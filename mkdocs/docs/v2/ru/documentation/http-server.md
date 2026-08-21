---
description: "Explains Kora HTTP server, declarative and imperative controllers, routing, request and response mapping, interceptors, error handling, and Undertow configuration. Use when working with @HttpController, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora HTTP server, declarative and imperative controllers, routing, request and response mapping, interceptors, error handling, and Undertow configuration; key triggers include @HttpController, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith, HttpServerModule, UndertowHttpServerModule."
---

Модуль `HTTP-сервера` описывает входящую HTTP-границу приложения: прием запроса, разбор параметров, чтение тела,
выбор обработчика, формирование ответа, телеметрию и перехватчики. В Kora можно описывать контроллеры декларативно
через `@HttpController` и `@HttpRoute` как тонкий слой абстракции, либо регистрировать обработчики императивно через `HttpServerRequestHandler`.

Декларативный подход подходит для большинства API: сигнатура метода описывает HTTP-контракт, а Kora во время компиляции
создает обработчик. Императивный подход полезен для низкоуровневых
или динамических маршрутов, где запрос удобнее обрабатывать вручную.

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
    implementation "ru.tinkoff.kora:http-server-undertow"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends UndertowHttpServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:http-server-undertow")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : UndertowHttpServerModule
    ```

## Конфигурация { #configuration }

Основные параметры конфигурации HTTP-сервера:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        publicApiHttpPort = 8080 //(1)!
        privateApiHttpPort = 8085 //(2)!
        virtualThreadsEnabled = false //(3)!
        maxRequestBodySize = "256MiB" //(4)!
    }
    ```

    1.  Порт публичного `HTTP`-сервера (по умолчанию: `8080`)
    2.  Порт служебного `HTTP`-сервера (по умолчанию: `8085`)
    3.  Включает виртуальные потоки для блокирующей обработки запросов вместо пула `blockingThreads`, требует `Java 21+` (по умолчанию: `false`)
    4.  Максимально допустимый размер тела входящего запроса (по умолчанию: `256MiB`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      publicApiHttpPort: 8080 #(1)!
      privateApiHttpPort: 8085 #(2)!
      virtualThreadsEnabled: false #(3)!
      maxRequestBodySize: "256MiB" #(4)!
    ```

    1.  Порт публичного `HTTP`-сервера (по умолчанию: `8080`)
    2.  Порт служебного `HTTP`-сервера (по умолчанию: `8085`)
    3.  Включает виртуальные потоки для блокирующей обработки запросов вместо пула `blockingThreads`, требует `Java 21+` (по умолчанию: `false`)
    4.  Максимально допустимый размер тела входящего запроса (по умолчанию: `256MiB`)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классе `HttpServerConfig` (указаны примеры значений или значения по умолчанию):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpServer {
            publicApiHttpPort = 8080 //(1)!
            privateApiHttpPort = 8085 //(2)!
            privateApiHttpMetricsPath = "/metrics" //(3)!
            privateApiHttpReadinessPath = "/system/readiness" //(4)!
            privateApiHttpLivenessPath = "/system/liveness" //(5)!
            ignoreTrailingSlash = false //(6)!
            ioThreads = 2 //(7)!
            blockingThreads = 2 //(8)!
            shutdownWait = "30s" //(9)!
            threadKeepAliveTimeout = "60s" //(10)!
            socketReadTimeout = "0s" //(11)!
            socketWriteTimeout = "0s" //(12)!
            socketKeepAliveEnabled = false //(13)!
            virtualThreadsEnabled = false //(14)!
            maxRequestBodySize = "256MiB" //(15)!
            telemetry {
                logging {
                    enabled = false //(16)!
                    stacktrace = true //(17)!
                    mask = "***" //(18)!
                    maskQueries = [ ] //(19)!
                    maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(20)!
                    pathTemplate = true //(21)!
                }
                metrics {
                    enabled = true //(22)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(23)!
                    tags = { // (24)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(25)!
                    attributes = { // (26)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1.  Порт публичного `HTTP`-сервера (по умолчанию: `8080`)
        2.  Порт служебного `HTTP`-сервера (по умолчанию: `8085`)
        3.  Путь для получения [метрик](metrics.md) на служебном сервере (по умолчанию: `/metrics`)
        4.  Путь для получения статуса [проб готовности](probes.md) на служебном сервере (по умолчанию: `/system/readiness`)
        5.  Путь для получения статуса [проб жизнеспособности](probes.md) на служебном сервере (по умолчанию: `/system/liveness`)
        6.  Игнорировать ли завершающий `/` в пути: если включено, `/my/path` и `/my/path/` будут считаться одним маршрутом (по умолчанию: `false`)
        7.  Количество потоков сетевого ввода-вывода (по умолчанию: количество доступных процессоров, но не меньше `2`)
        8.  Количество потоков для блокирующей обработки запросов (по умолчанию: `min(max(доступные процессоры, 2) * 8, 200)`)
        9.  Время ожидания обработки перед выключением сервера при [штатном завершении](container.md#component-lifecycle) (по умолчанию: `30s`)
        10.  Максимальное время жизни потока обработчика запроса без работы (по умолчанию: `60s`)
        11.  Максимальное время ожидания чтения данных из сокета или соединения; `0s` отключает тайм-аут (по умолчанию: `0s`)
        12.  Максимальное время ожидания записи данных в сокет или соединение; `0s` отключает тайм-аут (по умолчанию: `0s`)
        13.  Включать ли `TCP keep-alive` для сокета или соединения (по умолчанию: `false`)
        14.  Включает виртуальные потоки для блокирующей обработки запросов вместо пула `blockingThreads`, требует `Java 21+` (по умолчанию: `false`)
        15.  Максимально допустимый размер тела входящего запроса (по умолчанию: `256MiB`)
        16.  Включает логирование модуля (по умолчанию: `false`)
        17.  Включает логирование стека вызовов при исключении (по умолчанию: `true`)
        18.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
        19.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
        20.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
        21.  Использовать ли шаблон пути запроса при логировании; если не указано, шаблон используется всегда, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указано, необязательно)
        22.  Включает метрики модуля (по умолчанию: `true`)
        23.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        24.  Настройка тегов для метрик (по умолчанию: `{}`)
        25.  Включает трассировку модуля (по умолчанию: `true`)
        26.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpServer:
          publicApiHttpPort: 8080 #(1)!
          privateApiHttpPort: 8085 #(2)!
          privateApiHttpMetricsPath: "/metrics" #(3)!
          privateApiHttpReadinessPath: "/system/readiness" #(4)!
          privateApiHttpLivenessPath: "/system/liveness" #(5)!
          ignoreTrailingSlash: false #(6)!
          ioThreads: 2 #(7)!
          blockingThreads: 2 #(8)!
          shutdownWait: "30s" #(9)!
          threadKeepAliveTimeout: "60s" #(10)!
          socketReadTimeout: "0s" #(11)!
          socketWriteTimeout: "0s" #(12)!
          socketKeepAliveEnabled: false #(13)!
          virtualThreadsEnabled: false #(14)!
          maxRequestBodySize: "256MiB" #(15)!
          telemetry:
            logging:
              enabled: false #(16)!
              stacktrace: true #(17)!
              mask: "***" #(18)!
              maskQueries: [ ] #(19)!
              maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(20)!
              pathTemplate: true #(21)!
            metrics:
              enabled: true #(22)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(23)!
              tags: #(24)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(25)!
              attributes: #(26)!
                key1: value1
                key2: value2
        ```

        1.  Порт публичного `HTTP`-сервера (по умолчанию: `8080`)
        2.  Порт служебного `HTTP`-сервера (по умолчанию: `8085`)
        3.  Путь для получения [метрик](metrics.md) на служебном сервере (по умолчанию: `/metrics`)
        4.  Путь для получения статуса [проб готовности](probes.md) на служебном сервере (по умолчанию: `/system/readiness`)
        5.  Путь для получения статуса [проб жизнеспособности](probes.md) на служебном сервере (по умолчанию: `/system/liveness`)
        6.  Игнорировать ли завершающий `/` в пути: если включено, `/my/path` и `/my/path/` будут считаться одним маршрутом (по умолчанию: `false`)
        7.  Количество потоков сетевого ввода-вывода (по умолчанию: количество доступных процессоров, но не меньше `2`)
        8.  Количество потоков для блокирующей обработки запросов (по умолчанию: `min(max(доступные процессоры, 2) * 8, 200)`)
        9.  Время ожидания обработки перед выключением сервера при [штатном завершении](container.md#component-lifecycle) (по умолчанию: `30s`)
        10.  Максимальное время жизни потока обработчика запроса без работы (по умолчанию: `60s`)
        11.  Максимальное время ожидания чтения данных из сокета или соединения; `0s` отключает тайм-аут (по умолчанию: `0s`)
        12.  Максимальное время ожидания записи данных в сокет или соединение; `0s` отключает тайм-аут (по умолчанию: `0s`)
        13.  Включать ли `TCP keep-alive` для сокета или соединения (по умолчанию: `false`)
        14.  Включает виртуальные потоки для блокирующей обработки запросов вместо пула `blockingThreads`, требует `Java 21+` (по умолчанию: `false`)
        15.  Максимально допустимый размер тела входящего запроса (по умолчанию: `256MiB`)
        16.  Включает логирование модуля (по умолчанию: `false`)
        17.  Включает логирование стека вызовов при исключении (по умолчанию: `true`)
        18.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
        19.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
        20.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
        21.  Использовать ли шаблон пути запроса при логировании; если не указано, шаблон используется всегда, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указано, необязательно)
        22.  Включает метрики модуля (по умолчанию: `true`)
        23.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        24.  Настройка тегов для метрик (по умолчанию: `{}`)
        25.  Включает трассировку модуля (по умолчанию: `true`)
        26.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#http-server).

### Публичный и приватный API { #public-private-api }

Модуль запускает **два** независимых HTTP-сервера:

* **Публичный API** на `publicApiHttpPort` (по умолчанию `8080`) — обслуживает все ваши маршруты `@HttpController` и императивные обработчики. Это порт, к которому обращаются клиенты.
* **Приватный API** на `privateApiHttpPort` (по умолчанию `8085`) — обслуживает служебные эндпоинты, которые не должны быть доступны извне: [метрики](metrics.md) (`privateApiHttpMetricsPath`, по умолчанию `/metrics`), а также пробы [readiness](probes.md) и [liveness](probes.md) (`privateApiHttpReadinessPath` / `privateApiHttpLivenessPath`, по умолчанию `/system/readiness` и `/system/liveness`).

Разделение портов позволяет публиковать через ingress/балансировщик только публичный порт, оставляя метрики и пробы доступными только из внутренней сети или оркестратора (например Kubernetes). Приватные эндпоинты предоставляются соответствующими модулями ([Метрики](metrics.md), [Пробы](probes.md)) — регистрировать их вручную не нужно.

### Низкоуровневая настройка сервера { #undertow-configurer }

Для низкоуровневой настройки, которую не покрывает конфигурация выше, Kora предоставляет две точки расширения, специфичные для `Undertow`. Предоставьте любую из них как компонент, и Kora применит её при построении сервера.

`UndertowConfigurer` даёт прямой доступ к `Undertow.Builder` (настройки worker/буферов, слушатели, опции сокетов и другие серверные опции):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeUndertowConfigurer implements UndertowConfigurer {

        @Override
        public Undertow.Builder configure(Undertow.Builder builder) {
            return builder.setServerOption(UndertowOptions.ENABLE_HTTP2, true);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeUndertowConfigurer : UndertowConfigurer {

        override fun configure(builder: Undertow.Builder): Undertow.Builder {
            return builder.setServerOption(UndertowOptions.ENABLE_HTTP2, true)
        }
    }
    ```

`HttpHandlerConfigurer` оборачивает корневой `HttpHandler` — это подходящее место для сквозного поведения на уровне «сырого» `Undertow` (например, обернуть каждый запрос в дополнительный обработчик до того, как отработает маршрутизация Kora):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeHandlerConfigurer implements HttpHandlerConfigurer {

        @Override
        public HttpHandler configure(HttpHandler handler) {
            return exchange -> {
                // пользовательская логика до маршрутизации Kora
                handler.handleRequest(exchange);
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeHandlerConfigurer : HttpHandlerConfigurer {

        override fun configure(handler: HttpHandler): HttpHandler {
            return HttpHandler { exchange ->
                // пользовательская логика до маршрутизации Kora
                handler.handleRequest(exchange)
            }
        }
    }
    ```

Для всего, что можно выразить параметрами [Конфигурации](#configuration) и [перехватчиками](#interceptors), используйте их; к этим интерфейсам прибегайте только для поведения, действительно специфичного для `Undertow`.

## Контроллер декларативный { #somecontroller-declarative }

Для создания контроллера следует использовать `@HttpController` аннотацию, а для его регистрации как зависимость `@Component`.
Аннотация `@HttpRoute` отвечает за указания пути и метода HTTP для конкретного метода обработчика.

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

    1. Указывает что класс является компонентом и его требуется зарегистрировать в контейнере приложения
    2. Указывает что класс является контроллером и содержит HTTP-обработчики
    3. Указывает что метод является обработчиком пути в контроллере
    4. Указывает тип `HTTP`-метода обработчика
    5. Указывает путь метода обработчика

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

    1. Указывает что класс является компонентом и его требуется зарегистрировать в контейнере приложения
    2. Указывает что класс является контроллером и содержит HTTP-обработчики
    3. Указывает что метод является обработчиком пути в контроллере
    4. Указывает тип `HTTP`-метода обработчика
    5. Указывает путь метода обработчика

### Маршрутизация { #routing }

`@HttpRoute` сопоставляет запрос по его `method` ([HTTP-метод](https://developer.mozilla.org/ru/docs/Web/HTTP/Methods) из `HttpMethod`) и `path`.
`path` — это шаблон, который должен начинаться с `/` и может содержать один или несколько сегментов `{name}` — каждый является [параметром пути](#path-parameter), связываемым через `@Path`:

* `/users` — статический путь
* `/users/{id}` — один параметр пути
* `/users/{userId}/orders/{orderId}` — несколько параметров пути, в том числе в середине пути

Параметр пути всегда соответствует ровно одному сегменту пути; значение никогда не охватывает `/`.

**Завершающий слеш.** По умолчанию сопоставление точное, поэтому `/users` и `/users/` — это **разные** маршруты: запрос к `/users/` при маршруте `/users` вернёт `404`.
Чтобы считать их одним маршрутом, включите `httpServer.ignoreTrailingSlash` (см. [Конфигурация](#configuration)):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        ignoreTrailingSlash = true
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      ignoreTrailingSlash: true
    ```

**Сопоставление метода.** Путь, обслуживаемый методом без подходящего маршрута, вернёт `405 Method Not Allowed`; неизвестный путь вернёт `404 Not Found`.
Сопоставленный шаблон доступен во время выполнения как `HttpServerRequest.route()` и используется как метка пути с низкой кардинальностью в метриках и трассировке (см. [Телеметрия](#telemetry)).

### Запрос { #request }

Раздел описывает преобразование `HTTP`-запроса в аргументы метода контроллера.
Для частей запроса используются специальные аннотации, а тело запроса передается аргументом без такой аннотации.

#### Преобразование параметров из строки { #string-parameter-reader }

Значения из пути, параметров запроса, заголовков и `cookie` приходят как строки.
Для преобразования строки в нужный тип Kora использует `StringParameterReader<T>`:

```java
public interface StringParameterReader<T> {
    T read(String string);
}
```

`StringParameterReader<T>` ищется как компонент графа по точному типу параметра. Если параметр объявлен как `List<T>` или `Set<T>`,
преобразователь применяется к каждому значению отдельно.

Из коробки поддерживаются `String`, `Boolean`, `Integer`, `Long`, `Float`, `Double`, `UUID`, `BigInteger`, `BigDecimal`,
`Duration`, `LocalDate`, `LocalTime`, `LocalDateTime`, `OffsetTime`, `OffsetDateTime`, `ZonedDateTime` и `enum`.
Для `enum` по умолчанию используется имя значения через `Enum.name()`. Если значение невозможно преобразовать, запрос завершается
ответом `400` через `HttpServerResponseException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserId(long value) {}

    @Module
    public interface UserIdModule {

        default StringParameterReader<UserId> userIdStringParameterReader() {
            return StringParameterReader.of(
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

        fun userIdStringParameterReader(): StringParameterReader<UserId> {
            return StringParameterReader.of(
                { value -> UserId(value.toLong()) },
                { value -> "Invalid user id: $value" }
            )
        }
    }
    ```

После регистрации преобразователя пользовательский тип можно использовать в параметрах контроллера:

```java
@HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
public User get(@Path("id") UserId id) {
    return userService.get(id);
}
```

#### Параметр пути { #path-parameter }

`@Path` — обозначает значение части пути запроса, сам параметр указывается в `{кавычках}` в пути
и имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.
Значение преобразуется через `StringParameterReader<T>`, поэтому можно использовать как встроенные типы, так и пользовательские.

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

#### Параметр запроса { #query-parameter }

`@Query` — значение параметра запроса, имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.
Поддерживаются одиночные значения, `List<T>` и `Set<T>`. Для `List<T>` сохраняются все значения параметра,
для `Set<T>` повторяющиеся значения удаляются с сохранением порядка первого появления.

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

#### Заголовок запроса { #request-header }

`@Header` — значение [заголовка запроса](https://developer.mozilla.org/ru/docs/Web/HTTP/Headers), имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.
Поддерживаются одиночные значения, `List<T>` и `Set<T>`.
Для `List<T>` и `Set<T>` используются все значения заголовка.

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
        operator fun helloWorld(
            @Header("headerName") headerValue: String,
            @Header("headerNameList") headerValues: List<String>
        ): String {
            return "Hello World";
        }
    }
    ```

#### Тело запроса { #request-body }

Для указания тела запроса требуется использовать аргумент метода без специальных аннотаций.
По умолчанию поддерживаются `byte[]`, `ByteBuffer`, `String`, `FormUrlEncoded`, `FormMultipart` и пользовательские типы через `HttpServerRequestMapper<T>`.

##### JSON { #json }

Для указания, что тело является `JSON` и для него требуется внедрить `JsonReader<T>`, используется аннотация `@Json`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public record Request(String name) {}

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Json Request body) { //(1)!
            return "Hello World";
        }
    }
    ```

    1. Указывает что тело должно быть прочитано как `JSON`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        data class Request(val name: String)

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(@Json body: Request): String { //(1)!
            return "Hello World"
        }
    }
    ```

    1. Указывает что тело должно быть прочитано как `JSON`

Требуется подключить модуль [JSON](json.md).

##### Текстовая форма { #form-urlencoded }

Объявите аргумент `FormUrlEncoded` (из `ru.tinkoff.kora.http.common.form`), чтобы принять запрос с типом содержимого
`application/x-www-form-urlencoded` ([форма данных](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1)).
Аннотации `@Json` или `@Mapping` не требуются — для этого типа в Kora есть встроенный reader.

`FormUrlEncoded` итерируем и предоставляет:

* `get(String name)` — возвращает `FormUrlEncoded.FormPart` с таким именем, либо `null`
* `FormPart.name()` — имя поля
* `FormPart.values()` — все значения поля (поле может повторяться в форме)

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/form/encoded")
        public String handle(FormUrlEncoded body) {
            FormUrlEncoded.FormPart name = body.get("name"); //(1)!
            String firstName = (name != null) ? name.values().get(0) : null;
            return "Hello " + firstName;
        }
    }
    ```

    1. Читает поле `name` из отправленной формы

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/form/encoded")
        fun handle(body: FormUrlEncoded): String {
            val name = body.get("name") //(1)!
            val firstName = name?.values()?.firstOrNull()
            return "Hello $firstName"
        }
    }
    ```

    1. Читает поле `name` из отправленной формы

##### Бинарная форма { #form-multipart }

Объявите аргумент `FormMultipart` (из `ru.tinkoff.kora.http.common.form`), чтобы принять запрос `multipart/form-data`
([бинарная форма](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2)), обычно используется для загрузки файлов.
Аннотации `@Json` или `@Mapping` не требуются.

`FormMultipart.parts()` возвращает список частей, где каждая `FormMultipart.FormPart` — один из sealed-подтипов:

* `MultipartData` — текстовое поле: `name()`, `content()` (`String`)
* `MultipartFile` — файл, загруженный в память: `name()`, `fileName()`, `contentType()`, `content()` (`byte[]`)
* `MultipartFileStream` — потоковый файл: `name()`, `fileName()`, `contentType()`, `content()` (`Flow.Publisher<ByteBuffer>`)

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/form/multipart")
        public String handle(FormMultipart body) {
            for (FormMultipart.FormPart part : body.parts()) {
                if (part instanceof FormMultipart.FormPart.MultipartData data) { //(1)!
                    String value = data.content();
                } else if (part instanceof FormMultipart.FormPart.MultipartFile file) { //(2)!
                    String fileName = file.fileName();
                    String contentType = file.contentType();
                    byte[] content = file.content();
                }
            }
            return "OK";
        }
    }
    ```

    1. Текстовое поле формы
    2. Файл, загруженный в форме

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/form/multipart")
        fun handle(body: FormMultipart): String {
            for (part in body.parts()) {
                when (part) {
                    is FormMultipart.FormPart.MultipartData -> { //(1)!
                        val value = part.content()
                    }
                    is FormMultipart.FormPart.MultipartFile -> { //(2)!
                        val fileName = part.fileName()
                        val contentType = part.contentType()
                        val content = part.content()
                    }
                    else -> {}
                }
            }
            return "OK"
        }
    }
    ```

#### Куки { #cookie }

`@Cookie` — значение [Cookie](https://developer.mozilla.org/ru/docs/Glossary/Cookie), имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.
Можно получить значение как `String`, как тип `Cookie` с именем, значением и атрибутами, либо как другой тип через `StringParameterReader<T>`.

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
        operator fun helloWorld(
            @Cookie("cookieName") cookieValue: String
        ): String {
            return "Hello World";
        }
    }
    ```

#### Пользовательский параметр { #custom-parameter }

Если требуется собрать аргумент метода из запроса вручную, можно использовать специальный интерфейс `HttpServerRequestMapper<T>`.
Такой подход удобен для пользовательского контекста, авторизации, сложной проверки заголовков или нескольких частей запроса сразу:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public record UserContext(String userId, String traceId) {}

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

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class MapperRequestController {

        data class UserContext(val userId: String, val traceId: String)

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

#### Обязательные параметры { #required-parameters }

===! ":fontawesome-brands-java: `Java`"

    По умолчанию все аргументы, объявленные в методе, являются **обязательными**.
    Если обязательное значение отсутствует в запросе, Kora вернет ответ `400`.

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все аргументы метода, которые не используют синтаксис [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html),
    считаются **обязательными**. Если обязательное значение отсутствует в запросе, Kora вернет ответ `400`.

#### Необязательные параметры { #optional-parameters }

===! ":fontawesome-brands-java: `Java`"

    Если аргумент метода является необязательным, то есть может отсутствовать в запросе,
    можно использовать аннотацию `@Nullable` или `Optional<T>` для одиночных значений:

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

    1.  Подойдет любая аннотация `@Nullable`, например `javax.annotation.Nullable`, `jakarta.annotation.Nullable` или `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использовать синтаксис [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) и помечать такой параметр как необязательный:

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

По умолчанию можно использовать стандартные типы возвращаемых значений: `byte[]`, `ByteBuffer`, `String`.
Они будут обработаны со статусом `200` и соответствующим заголовком типа ответа.

Если нужно вручную указать статус, заголовки или тело, метод может вернуть `HttpServerResponse`.
Основной контракт `HttpServerResponse` состоит из кода ответа, заголовков и необязательного тела:

```java
public interface HttpServerResponse {
    int code();
    MutableHttpHeaders headers();
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

    1. Код состояния `HTTP`-ответа
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

    1. Код состояния `HTTP`-ответа
    2. Заголовки ответа
    3. Тело ответа

#### JSON { #json-2 }

Если предполагается отвечать в формате `JSON` и для него требуется обработчик с `JsonWriter<T>`, для этого требуется использовать аннотацию `@Json` над методом.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public record Response(String greeting) {}

        @Json //(1)!
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public Response helloWorld() {
            return new Response("Hello World");
        }
    }
    ```

    1. Указывает что ответ должен быть в формате `JSON`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        data class Response(val greeting: String)

        @Json //(1)!
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): Response {
            return Response("Hello World")
        }
    }
    ```

    1. Указывает что ответ должен быть в формате `JSON`

Требуется подключить модуль [JSON](json.md).

#### Сущность ответа { #response-entity }

Если требуется вернуть тело, заголовки и код состояния ответа вместе,
используется `HttpResponseEntity<T>` — обертка над телом ответа.

Ниже показан пример, аналогичный примеру `JSON`, вместе с оберткой `HttpResponseEntity`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

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

        data class Response(val greeting: String)

        @Json
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): HttpResponseEntity<Response> {
            return HttpResponseEntity.of(200, HttpHeaders.of("myHeader", "12345"), Response("Hello World"));
        }
    }
    ```

#### Ответ исключение { #respond-exception }

Если требуется прервать обработку и сразу вернуть ошибку, можно бросить `HttpServerResponseException`.
Это одновременно исключение и `HttpServerResponse`, поэтому его можно выбросить из контроллера, сервиса или преобразователя параметра.

Фабричные методы `HttpServerResponseException.of(...)` позволяют указать код состояния, текст ответа, причину и заголовки.
Тело ответа будет записано как `text/plain; charset=utf-8`.

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

Если требуется сформировать ответ нестандартным способом, можно использовать специальный интерфейс `HttpServerResponseMapper<T>`.
Он получает `Context`, исходный `HttpServerRequest` и результат метода контроллера, а возвращает готовый `HttpServerResponse`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public record HelloWorldResponse(String greeting, String name) {}

        public static final class ResponseMapper implements HttpServerResponseMapper<HelloWorldResponse> {

            @Override
            public HttpServerResponse apply(Context ctx, HttpServerRequest request, HelloWorldResponse result) {
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

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        data class HelloWorldResponse(val greeting: String, val name: String)

        class ResponseMapper : HttpServerResponseMapper<HelloWorldResponse> {
            override fun apply(ctx: Context, request: HttpServerRequest, result: HelloWorldResponse): HttpServerResponse {
                return HttpServerResponse.of(200, HttpBody.plaintext(result.greeting + " - " + result.name))
            }
        }

        @Mapping(ResponseMapper::class)
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): HelloWorldResponse {
            return HelloWorldResponse("Hello World", "Bob")
        }
    }
    ```

### Сигнатуры { #signatures }

Доступные сигнатуры для методов декларативного HTTP обработчика из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения. Это может быть тип тела (`void`, `String`, `byte[]`, тип с `@Json` и т.д.),
    [`HttpResponseEntity<T>`](#response-entity) для указания также статуса и заголовков, либо полный [`HttpServerResponse`](#response).

    - `T myMethod()` — **блокирующая**: обработчик выполняется на потоке из пула `blockingThreads` (либо на виртуальном потоке при `virtualThreadsEnabled`, см. [Конфигурация](#configuration))
    - `CompletionStage<T> myMethod()` — **неблокирующая**: обработчик выполняется на I/O-потоке и не должен его блокировать; см. [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` — **неблокирующая** через [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

    Результат `null` (или `void`) даёт пустое тело со статусом `200`, если только тип возврата не `HttpServerResponse` / `HttpResponseEntity`, которые несут собственный статус.

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения — тип тела, [`HttpResponseEntity<T>`](#response-entity) или полный [`HttpServerResponse`](#response).

    - `myMethod(): T` — **блокирующая**: обработчик выполняется на потоке из пула `blockingThreads` (либо на виртуальном потоке при `virtualThreadsEnabled`, см. [Конфигурация](#configuration))
    - `suspend myMethod(): T` — **неблокирующая** [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

    Nullable-тип возврата (`T?`) допустим для обработчиков, которые могут вернуть пустое тело `200`.

Выбирайте блокирующую сигнатуру, когда обработчик вызывает блокирующий код (JDBC, блокирующие клиенты); неблокирующую — только когда вся цепочка вызова неблокирующая, иначе вы застопорите I/O-потоки.

## Перехватчики { #interceptors }

Можно создавать перехватчики для изменения поведения или добавления общей логики вокруг обработки запроса.
Для этого используется интерфейс `HttpServerInterceptor`:

```java
public interface HttpServerInterceptor {
    CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain) throws Exception;

    interface InterceptChain {
        CompletionStage<HttpServerResponse> process(Context ctx, HttpServerRequest request) throws Exception;
    }
}
```

Перехватчик получает текущий `Context`, `HttpServerRequest` и цепочку дальнейшей обработки.
Чтобы передать запрос дальше, нужно вызвать `chain.process(context, request)`. Если перехватчик возвращает ответ сам,
обработчик контроллера дальше не вызывается.

Перехватчики можно использовать на:

- Конкретных методах контроллера
- Контроллере целиком
- Всех контроллерах сразу: для этого компонент перехватчика должен быть зарегистрирован с тегом `@Tag(HttpServerModule.class)`;
  таких глобальных перехватчиков может быть несколько

**Порядок выполнения:**

Перехватчики, объявленные через `@InterceptWith`, выполняются в порядке объявления (сверху вниз): перехватчики уровня
контроллера оборачивают перехватчики уровня метода, а в пределах одной цели порядок соответствует порядку аннотаций. Каждый
перехватчик может изменить запрос перед `chain.process(...)`, прервать цепочку, вернув ответ без её вызова, либо обработать
результат/исключение после.

Глобальные перехватчики, зарегистрированные через `@Tag(HttpServerModule.class)`, **не имеют гарантированного порядка между собой**.
Если требуется строгий порядок между глобальными обработчиками (например, авторизация должна выполняться до обработки ошибок),
не регистрируйте несколько глобальных перехватчиков — реализуйте **один** глобальный перехватчик, который вызывает нужные
шаги в требуемом порядке внутри себя.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public static final class MethodInterceptor implements HttpServerInterceptor {

            @Override
            public CompletionStage<HttpServerResponse> intercept(Context context, 
                                                                 HttpServerRequest request, 
                                                                 InterceptChain chain) throws Exception {
                return chain.process(context, request);
            }
        }

        @InterceptWith(MethodInterceptor.class)
        @HttpRoute(method = HttpMethod.POST, path = "/intercepted")
        public String helloWorld() {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        class MethodInterceptor : HttpServerInterceptor {

            override fun intercept(
                context: Context,
                request: HttpServerRequest,
                chain: HttpServerInterceptor.InterceptChain
            ): CompletionStage<HttpServerResponse> {
                return chain.process(context, request)
            }
        }

        @InterceptWith(MethodInterceptor::class)
        @HttpRoute(method = HttpMethod.POST, path = "/intercepted")
        fun helloWorld(): String {
            return "Hello World"
        }
    }
    ```

### Обработка ошибок { #error-handling }

Обработка ошибок на уровне всех `HTTP`-ответов может быть реализована через перехватчик.
Ниже представлен простой пример такого перехватчика.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(HttpServerModule.class)
    @Component
    public final class ErrorInterceptor implements HttpServerInterceptor {

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, 
                                                             HttpServerRequest request, 
                                                             InterceptChain chain) throws Exception {
            return chain.process(context, request).exceptionally(e -> {
                if(e instanceof CompletionException) {
                    e = e.getCause();
                }
                if (e instanceof HttpServerResponseException ex) {
                    return ex;
                }

                var body = HttpBody.plaintext(e.getMessage());
                if (e instanceof IllegalArgumentException) {
                    return HttpServerResponse.of(400, body);
                } else if (e instanceof TimeoutException) {
                    return HttpServerResponse.of(408, body);
                } else {
                    return HttpServerResponse.of(500, body);
                }
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(HttpServerModule::class)
    @Component
    class ErrorInterceptor : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            return chain.process(context, request).exceptionally { e ->
                val error = if (e is CompletionException) e.cause!! else e
                if (error is HttpServerResponseException) {
                    return@exceptionally error
                }

                val body = HttpBody.plaintext(error.message)
                when (error) {
                    is IllegalArgumentException -> HttpServerResponse.of(400, body)
                    is TimeoutException -> HttpServerResponse.of(408, body)
                    else -> HttpServerResponse.of(500, body)
                }
            }
        }
    }
    ```

## Контроллер императивный { #somecontroller-imperative }

Для создания контроллера следует реализовать `HttpServerRequestHandler.HandlerFunction` интерфейс,
а затем зарегистрировать его в обработчике `HttpServerRequestHandler`.

Ниже показан пример по обработке всех описанных декларативных параметров запроса из примеров выше:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        default HttpServerRequestHandler someHttpHandler() {
            return HttpServerRequestHandlerImpl.of(HttpMethod.POST, //(1)!
                                                   "/hello/{world}", //(2)!
                                                   (context, request) -> {
                var path = RequestHandlerUtils.parseStringPathParameter(request, "world");
                var query = RequestHandlerUtils.parseOptionalStringQueryParameter(request, "query");
                var queries = RequestHandlerUtils.parseOptionalStringListQueryParameter(request, "Queries");
                var header = RequestHandlerUtils.parseOptionalStringHeaderParameter(request, "header");
                var headers = RequestHandlerUtils.parseOptionalStringListHeaderParameter(request, "Headers");
                return CompletableFuture.completedFuture(HttpServerResponse.of(200, HttpBody.plaintext("Hello World")));
            });
        }
    }
    ```

    1. Указывает тип `HTTP`-метода обработчика
    2. Указывает путь метода обработчика

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {

        fun someHttpHandler(): HttpServerRequestHandler? {
            return HttpServerRequestHandlerImpl.of(
                HttpMethod.POST, //(1)!
                "/hello/{world}" //(2)!
            ) { context: Context, request: HttpServerRequest ->
                val path = RequestHandlerUtils.parseStringPathParameter(request, "world")
                val query = RequestHandlerUtils.parseOptionalStringQueryParameter(request, "query")
                val queries = RequestHandlerUtils.parseOptionalStringListQueryParameter(request, "Queries")
                val header = RequestHandlerUtils.parseOptionalStringHeaderParameter(request, "header")
                val headers = RequestHandlerUtils.parseOptionalStringListHeaderParameter(request, "Headers")
                CompletableFuture.completedFuture(HttpServerResponse.of(200, HttpBody.plaintext("Hello World")))
            }
        }
    }
    ```

    1. Указывает тип `HTTP`-метода обработчика
    2. Указывает путь метода обработчика

## Авторизация { #authorization }

Kora предоставляет механизм извлечения контекста авторизации из HTTP запроса через интерфейс `HttpServerPrincipalExtractor`.
Этот интерфейс позволяет реализовать любую схему аутентификации: [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/).

### Принцип работы { #how-it-works }

`HttpServerPrincipalExtractor<T>` извлекает токен из запроса (обычно из заголовка `Authorization`) и возвращает объект `Principal`.
Полученный `Principal` сохраняется в `Context` запроса и может быть получен в любом месте обработки запроса через `Principal.current()`.

```java
public interface HttpServerPrincipalExtractor<T extends Principal> {
    CompletionStage<T> extract(HttpServerRequest request, @Nullable String value);
}
```

Где:

- `request` — текущий HTTP запрос, из которого можно извлечь дополнительные данные (заголовки, параметры)
- `value` — значение токена, извлеченное из заголовка `Authorization` (или другого источника)
- `T extends Principal` — тип контекста авторизации, который будет сохранен в `Context`

### Пользовательский Principal { #custom-principal }

Пользователь может создать простой принципал для API при необходимости, с полями или без них:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record ApiPrincipal(String client) implements Principal {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class ApiPrincipal(val client: String) : Principal
    ```

Для передачи дополнительной информации об авторизации (userId, роли, scope) создайте собственную реализацию `Principal`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserContext(String userId, List<String> roles) implements Principal {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserContext(val userId: String, val roles: List<String>) : Principal
    ```

Если требуется работа с scope (областями видимости), используйте интерфейс `PrincipalWithScopes`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record ScopedUser(String userId, Collection<String> scopes) implements PrincipalWithScopes {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class ScopedUser(val userId: String, val scopes: Collection<String>) : PrincipalWithScopes
    ```

### Базовый пример { #basic-example }

Простой пример извлечения API ключа из заголовка `Authorization`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface AuthModule {

        @ConfigSource("auth.apiKey")
        interface ApiKeyAuthConfig {
            String value();
        }

        default HttpServerPrincipalExtractor<Principal> apiKeyExtractor(ApiKeyAuthConfig config) {
            return (request, value) -> {
                if (value == null || !config.value().equals(value)) {
                    return CompletableFuture.failedFuture(
                        new IllegalAccessException("Invalid API key")
                    );
                }
                return CompletableFuture.completedFuture(new ApiPrincipal("api-client"));
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface AuthModule {

        @ConfigSource("auth.apiKey")
        interface ApiKeyAuthConfig {
            fun value(): String
        }

        fun apiKeyExtractor(config: ApiKeyAuthConfig): HttpServerPrincipalExtractor<Principal> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || config.value() != value) {
                    return@HttpServerPrincipalExtractor CompletableFuture.failedFuture(
                        IllegalAccessException("Invalid API key")
                    )
                }
                CompletableFuture.completedFuture(ApiPrincipal("api-client"))
            }
        }
    }
    ```

### Bearer токен { #bearer }

Пример извлечения Bearer токена с пользовательской реализацией `Principal`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface BearerAuthModule {

        default HttpServerPrincipalExtractor<UserContext> bearerExtractor(TokenValidator validator) {
            return (request, value) -> {
                if (value == null || !value.startsWith("Bearer ")) {
                    return CompletableFuture.failedFuture(
                        new IllegalAccessException("No Bearer token")
                    );
                }
                
                String token = value.substring(7);
                return validator.validate(token)
                    .thenApply(userData -> new UserContext(userData.userId(), userData.roles()));
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface BearerAuthModule {

        fun bearerExtractor(validator: TokenValidator): HttpServerPrincipalExtractor<UserContext> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || !value.startsWith("Bearer ")) {
                    return CompletableFuture.failedFuture(
                        IllegalAccessException("No Bearer token")
                    )
                }
                
                val token = value.substring(7)
                validator.validate(token)
                    .thenApply { userData ->
                        UserContext(userData.userId, userData.roles)
                    }
            }
        }
    }
    ```

### Получение Principal { #getting-principal }

Получить текущий контекст авторизации можно в любом месте обработки запроса:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public class SecureController {

        @HttpRoute(method = HttpMethod.GET, path = "/secure")
        public String getSecureData() {
            Principal principal = Principal.current();
            if (principal instanceof UserContext user) {
                return "Hello, user: " + user.userId();
            }
            throw new SecurityException("Not authenticated");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SecureController {

        @HttpRoute(method = HttpMethod.GET, path = "/secure")
        fun getSecureData(): String {
            val principal = Principal.current()
            return if (principal is UserContext) {
                "Hello, user: ${principal.userId}"
            } else {
                throw SecurityException("Not authenticated")
            }
        }
    }
    ```

### OAuth2 { #oauth2 }

Для OAuth2 авторизации создайте `HttpServerPrincipalExtractor`, который проверяет токен через OAuth2 provider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface OAuth2Module {

        default HttpServerPrincipalExtractor<ScopedUser> oauth2Extractor(OAuth2Client oauth2Client) {
            return (request, value) -> {
                if (value == null || !value.startsWith("Bearer ")) {
                    return CompletableFuture.failedFuture(
                        new IllegalAccessException("No OAuth2 token")
                    );
                }
                
                String token = value.substring(7);
                return oauth2Client.introspect(token)
                    .thenApply(introspection -> 
                        new ScopedUser(
                            introspection.subject(),
                            introspection.scopes()
                        )
                    );
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface OAuth2Module {

        fun oauth2Extractor(oauth2Client: OAuth2Client): HttpServerPrincipalExtractor<ScopedUser> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || !value.startsWith("Bearer ")) {
                    return CompletableFuture.failedFuture(
                        IllegalAccessException("No OAuth2 token")
                    )
                }
                
                val token = value.substring(7)
                oauth2Client.introspect(token)
                    .thenApply { introspection ->
                        ScopedUser(introspection.subject, introspection.scopes)
                    }
            }
        }
    }
    ```

#### Проверка scope { #scope-check }

Для проверки scope можно создать перехватчик, который проверяет `PrincipalWithScopes`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ScopeCheckingInterceptor implements HttpServerInterceptor {

        private final String requiredScope;

        public ScopeCheckingInterceptor(@ConfigSource("auth.requiredScope") String requiredScope) {
            this.requiredScope = requiredScope;
        }

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, 
                                                             HttpServerRequest request, 
                                                             InterceptChain chain) {
            Principal principal = Principal.current(context);
            if (principal instanceof PrincipalWithScopes scoped) {
                if (!scoped.scopes().contains(requiredScope)) {
                    return CompletableFuture.failedFuture(
                        HttpServerResponseException.of(403, "Insufficient scope")
                    );
                }
            } else {
                return CompletableFuture.failedFuture(
                    HttpServerResponseException.of(403, "No scopes available")
                );
            }
            
            return chain.process(context, request);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ScopeCheckingInterceptor(
        @ConfigSource("auth.requiredScope") private val requiredScope: String
    ) : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            val principal = Principal.current(context)
            if (principal is PrincipalWithScopes) {
                if (!principal.scopes.contains(requiredScope)) {
                    return CompletableFuture.failedFuture(
                        HttpServerResponseException.of(403, "Insufficient scope")
                    )
                }
            } else {
                return CompletableFuture.failedFuture(
                    HttpServerResponseException.of(403, "No scopes available")
                )
            }
            
            return chain.process(context, request)
        }
    }
    ```

### OpenAPI интеграция { #openapi }

При использовании Kora OpenAPI Generator авторизация настраивается автоматически на основе спецификации OpenAPI.
Генератор создает:

1. Интерфейс `ApiSecurity` с классами-маркерами для каждого типа авторизации
2. `HttpServerInterceptor` для каждого security scheme
3. Требует предоставить `HttpServerPrincipalExtractor` с соответствующим `@Tag`

Пример из [kora-examples](https://github.com/kora-projects/kora-examples):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowHttpServerModule,
            JsonModule {

        @Tag(ApiSecurity.ApiKeyAuth.class)
        default HttpServerPrincipalExtractor<Principal> apiKeyExtractor(DataApiAuthConfig config) {
            return (request, value) -> {
                if (value == null || !config.value().equals(value)) {
                    throw new SecurityException("Invalid API key");
                }
                return CompletableFuture.completedFuture(
                    new DataApiPrincipal("data-api-client")
                );
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
        UndertowHttpServerModule,
        JsonModule {

        @Tag(ApiSecurity.ApiKeyAuth::class)
        fun apiKeyExtractor(config: DataApiAuthConfig): HttpServerPrincipalExtractor<Principal> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || config.value() != value) {
                    throw SecurityException("Invalid API key")
                }
                CompletableFuture.completedFuture(
                    DataApiPrincipal("data-api-client")
                )
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

### Обработка ошибок { #error-handling }

Если `HttpServerPrincipalExtractor` выбрасывает исключение или возвращает `null`, запрос отклоняется с кодом `403 Forbidden`.
Для кастомной обработки ошибок авторизации используйте перехватчик:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(HttpServerModule.class)
    @Component
    public final class AuthErrorInterceptor implements HttpServerInterceptor {

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, 
                                                             HttpServerRequest request, 
                                                             InterceptChain chain) {
            return chain.process(context, request).exceptionally(e -> {
                if (e instanceof CompletionException) {
                    e = e.getCause();
                }
                if (e instanceof IllegalAccessException) {
                    return HttpServerResponse.of(401, HttpBody.plaintext("Unauthorized: " + e.getMessage()));
                }
                if (e instanceof SecurityException) {
                    return HttpServerResponse.of(403, HttpBody.plaintext("Forbidden: " + e.getMessage()));
                }
                throw new CompletionException(e);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(HttpServerModule::class)
    @Component
    class AuthErrorInterceptor : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            return chain.process(context, request).exceptionally { e ->
                val error = if (e is CompletionException) e.cause!! else e
                when (error) {
                    is IllegalAccessException -> 
                        HttpServerResponse.of(401, HttpBody.plaintext("Unauthorized: ${error.message}"))
                    is SecurityException -> 
                        HttpServerResponse.of(403, HttpBody.plaintext("Forbidden: ${error.message}"))
                    else -> throw CompletionException(error)
                }
            }
        }
    }
    ```

## Телеметрия { #telemetry }

HTTP Server использует контракт телеметрии для логирования, метрик и трассировки запросов.
Конфигурация телеметрии (секция `telemetry { logging / metrics / tracing }`) описана в разделе [Конфигурация](#configuration).
Точки расширения находятся в `ru.tinkoff.kora.http.server.common.telemetry`.

Для каждого HTTP-запроса создаётся `HttpServerTelemetry.HttpServerTelemetryContext`, который закрывается по завершении обработки запроса.
Запрос описывается через параметры обработчика телеметрии, включая метод, путь, статус ответа и длительность.

Фабрика по умолчанию `DefaultHttpServerTelemetryFactory` объединяет три фабрики:
- `HttpServerLoggerFactory` строит `HttpServerLogger` для логирования начала/конца обработки запроса;
- `HttpServerMetricsFactory` строит `HttpServerMetrics` для записи метрик запросов;
- `HttpServerTracerFactory` строит `HttpServerTracer` для распределённой трассировки.

Метрики и трассировка описаны в разделе [Справочник метрик](metrics.md#http-server).

### Логирование { #telemetry-logging }

Логирование сервера пишется через `SLF4J` под логгером `ru.tinkoff.kora.http.server.common.HttpServer`. Включение логирования в конфигурации
(`httpServer.telemetry.logging.enabled = true`) активирует телеметрию, но **что именно** пишется, определяется уровнем логирования этого логгера,
поэтому детализацией вы управляете из вашего фреймворка логирования (`logback` и т.д.) без перезапуска с другой конфигурацией:

| Уровень лога | Что логируется |
|--------------|----------------|
| `INFO`  | Строка начала и конца запроса: метод, шаблон пути, статус ответа, код результата и длительность |
| `DEBUG` | Дополнительно **заголовки** запроса и ответа |
| `TRACE` | Дополнительно полный (нешаблонизированный) путь запроса |

Следующие поля конфигурации формируют вывод (полный список см. в [Конфигурации](#configuration)):

* `pathTemplate` — при `true` (по умолчанию) логируется шаблон маршрута с низкой кардинальностью (`/users/{id}`) и используется как метка метрик/трассировки вместо разрешённого пути (`/users/42`); на `TRACE` логируется разрешённый путь
* `maskHeaders` — имена заголовков, значения которых заменяются на `mask` (по умолчанию маскируются `authorization`, `cookie`, `set-cookie`)
* `maskQueries` — имена query-параметров, значения которых заменяются на `mask`
* `mask` — строка замены (по умолчанию `***`)
* `stacktrace` — при `true` (по умолчанию) логирует стектрейс исключения при ошибке обработки запроса

Пример конфигурации `logback`, включающей логирование заголовков сервера:

```xml
<logger name="ru.tinkoff.kora.http.server.common.HttpServer" level="DEBUG"/>
```

### Свой логгер { #telemetry-custom-logger }

Чтобы полностью управлять форматом или назначением лога, предоставьте свой компонент `HttpServerLoggerFactory` (или `HttpServerLogger`) — он заменит
фабрику по умолчанию `Slf4jHttpServerLoggerFactory`. То же касается метрик (`HttpServerMetricsFactory`) и трассировки (`HttpServerTracerFactory`):
предоставление любого из этих компонентов переопределяет соответствующую реализацию по умолчанию, остальные сохраняют реализацию по умолчанию.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyHttpServerLoggerFactory implements HttpServerLoggerFactory {

        @Override
        public HttpServerLogger get(HttpServerLoggerConfig logging) {
            return new MyHttpServerLogger(); //(1)!
        }
    }
    ```

    1. Ваша реализация `HttpServerLogger`, управляющая тем, что и как логировать

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyHttpServerLoggerFactory : HttpServerLoggerFactory {

        override fun get(logging: HttpServerLoggerConfig): HttpServerLogger {
            return MyHttpServerLogger() //(1)!
        }
    }
    ```

    1. Ваша реализация `HttpServerLogger`, управляющая тем, что и как логировать
