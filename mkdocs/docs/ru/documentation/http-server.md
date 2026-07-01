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

Kora предоставляет тонкую настройку `HTTP`-сервера `Undertow` через два специализированных интерфейса конфигурации: `UndertowConfigurer` и `HttpHandlerConfigurer`.  
Они позволяют настраивать поведение сервера и конвейер обработки запросов, не жертвуя интеграцией с модульной архитектурой Kora.

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

Для указания, что тело является `JSON` и для него требуется автоматически создать и внедрить `JsonReader<T>`,
используется аннотация `@Json`:

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

Можно использовать `FormUrlEncoded` как тип аргумента тела [форма данных](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(FormUrlEncoded body) {
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
        fun helloWorld(body: FormUrlEncoded): String {
            return "Hello World"
        }
    }
    ```

##### Бинарная форма { #form-multipart }

Можно использовать `FormMultipart` как тип аргумента тела [бинарная форма](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(FormMultipart body) {
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
        fun helloWorld(body: FormMultipart): String {
            return "Hello World"
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
        @Mapping(RequestMapper::class)
        operator fun get(@Mapping(RequestMapper::class) context: UserContext): String {
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

Если предполагается отвечать в формате `JSON`, требуется использовать аннотацию `@Json` над методом.
Для типа ответа Kora найдет или создаст `JsonWriter<T>`:

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
            fun apply(ctx: Context, request: HttpServerRequest, result: HelloWorldResponse): HttpServerResponse {
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

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

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
    @Tag(HttpServerModule.class)
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
