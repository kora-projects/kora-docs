Модуль предоставляет тонкий слой абстракции над библиотеками HTTP-сервера для создания обработчиков HTTP-запросов
с помощью аннотаций в декларативном стиле, так и в императивном стиле.

## Подключение

Пока что доступна реализация основанная на [Undertow](https://undertow.io/). 
Сервер поддерживает [штатное завершение](https://maxilect.ru/blog/pochemu-vazhen-graceful-shutdown-v-oblachnoy-srede-na-pr/).

===! ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:http-server-undertow"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends UndertowHttpServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:http-server-undertow")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : UndertowHttpServerModule
    ```

## Конфигурация

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
        shutdownWait = "100ms" //(9)!
        telemetry {
            logging {
                enabled = false //(10)!
                stacktrace = true //(11)!
            }
            metrics {
                enabled = true //(12)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(13)!
            }
            telemetry {
                enabled = true //(14)!
            }
        }
    }
    ```

    1.  Порт публичного сервера
    2.  Порт приватного сервера
    3.  Путь для получения [метрик](metrics.md) на приватном сервере
    4.  Путь для получения статуса [проб готовности](probes.md) на приватном сервере
    5.  Путь для получения статуса [проб жизнеспособности](probes.md) на приватном сервере
    6.  Игнорировать ли слэш в окончании пути, если включен то `/my/path` и `/my/path/` будут интерпритироваться одинакого, по умолчанию выключен
    7.  Количество потоков сервера, по умолчанию равен кол-во ядер процессора либо минимум `2`
    8.  Количество блокирующих потоков, по умолчанию равен кол-во ядер процессора умноженных на 2 либо минимум `2` потока
    9.  Время ожидания для выключения сервера в случае [штатного завершения](https://maxilect.ru/blog/pochemu-vazhen-graceful-shutdown-v-oblachnoy-srede-na-pr/)
    10.  Включает логгирование модуля (по умолчанию `false`)
    11.  Включает логгирование стэка вызовов в случае исключения
    12.  Включает метрики модуля (по умолчанию `true`)
    13.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    14.  Включает трассировку модуля (по умолчанию `true`)

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
      shutdownWait: "100ms" #(9)!
      telemetry:
        logging:
          enabled: false #(10)!
          stacktrace: true #(11)!
        metrics:
          enabled: true #(12)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(13)!
        telemetry:
          enabled: true #(14)!
    ```

    1.  Порт публичного сервера
    2.  Порт приватного сервера
    3.  Путь для получения [метрик](metrics.md) на приватном сервере
    4.  Путь для получения статуса [проб готовности](probes.md) на приватном сервере
    5.  Путь для получения статуса [проб жизнеспособности](probes.md) на приватном сервере
    6.  Игнорировать ли слэш в окончании пути, если включен то `/my/path` и `/my/path/` будут интерпритироваться одинакого, по умолчанию выключен
    7.  Количество потоков сервера, по умолчанию равен кол-во ядер процессора либо минимум `2`
    8.  Количество блокирующих потоков, по умолчанию равен кол-во ядер процессора умноженных на 2 либо минимум `2` потока
    9.  Время ожидания для выключения сервера в случае [штатного завершения](https://maxilect.ru/blog/pochemu-vazhen-graceful-shutdown-v-oblachnoy-srede-na-pr/)
    10.  Включает логгирование модуля (по умолчанию `false`)
    11.  Включает логгирование стэка вызовов в случае исключения
    12.  Включает метрики модуля (по умолчанию `true`)
    13.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    14.  Включает трассировку модуля (по умолчанию `true`)

## Контроллер декларативный

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
    4. Указывает тип HTTP метода обработчика
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
    4. Указывает тип HTTP метода обработчика
    5. Указывает путь метода обработчика

### Запрос

Секция описывает преобразования HTTP-запроса у контроллера.
Предлагается использовать специальные аннотации для указания параметров запроса.

#### Параметр пути

`@Path` — обозначает значение части пути запроса, сам параметр указывается в `{кавычках}` в пути
и имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.

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

#### Параметр запроса

`@Query` — значение параметра запроса, имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.

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

#### Заголовок запроса

`@Header` — значение [заголовка запроса](https://developer.mozilla.org/ru/docs/Web/HTTP/Headers), имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.

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

#### Тело запроса

Для указания тела запроса требуется использовать аргумент метода без специальных аннотации,
по умолчанию поддерживаются такие типы как `byte[]`, `ByteBuffer`, `String`.

##### Json

Для указания, что тело является Json и ему требуется автоматически создать такой читатель и внедрить его,
требуется использовать аннотацию `@Json`:

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

    1. Указывает что тело должно быть записано как Json

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

    1. Указывает что тело должно быть записано как Json

Требуется подключить модуль [Json](json.md).

##### Текстовая форма

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

##### Бинарная форма

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

#### Куки

`@Cookie` — значение [Cookie](https://developer.mozilla.org/ru/docs/Glossary/Cookie), имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.

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

#### Самописный параметр

В случае если требуется обрабатывать запрос отличным способом, то можно использовать специальный интерфейс `HttpServerRequestMapper`:

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

#### Обязательные параметры

===! ":fontawesome-brands-java: `Java`"

    По умолчанию все аргументы объявленные в методе являются **обязательными** (*NotNull*).

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все аргументы объявленные в методе которые не используют [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис считаются **обязательными** (*NotNull*).

#### Необязательные параметры

===! ":fontawesome-brands-java: `Java`"

    В случае если аргумент метода является необязательным, то есть может отсутствовать то,
    можно использовать аннотацию `@Nullable`:

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

    1.  Подойдет любая аннотация `@Nullable`, такие как `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использовать [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис и помечать такой параметр как Nullable:

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

### Ответ

По умолчанию можно использовать стандартные типы возвращаемых значений, 
такие как `byte[]`, `ByteBuffer`, `String` которые будут обработаны со статус кодом `200` и соответствующим заголовком типа ответа
либо `HttpServerResponse` где надо будет самостоятельно заполнить всю информацию об HTTP ответе.

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
                    HttpBody.plaintext(body) //(3)!
            ); 
        }
    }
    ```

    1. HTTP статус код ответа
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
                HttpBody.plaintext(body) //(3)!
            )
        }
    }
    ```

    1. HTTP статус код ответа
    2. Заголовки ответа
    3. Тело ответа

#### Json

В случае если предполагается отвечать в формате Json, то требуется использовать аннотацию `@Json` над методом:

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

    1. Указывает что ответ должен быть в формате Json

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

    1. Указывает что ответ должен быть в формате Json

Требуется подключить модуль [Json](json.md).

#### Сущность ответа

Если предполагается читать тело и получить также заголовки и статус код ответа,
то предполагается использовать `HttpResponseEntity`, это обертка над телом ответа.

Ниже показан пример аналогичный примеру Json вместе с оберткой `HttpResponseEntity`:

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

#### Ответ исключение

Если требуется отвечать ошибкой, то можно использовать `HttpServerResponseException` для того чтобы бросать исключение.

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

#### Самописное

В случае если требуется чтение ответа отличным способом, то можно использовать специальный интерфейс `HttpServerResponseMapper`:

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

### Сигнатуры

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

## Перехватчики

Можно создавать перехватчики для изменения поведения либо создания дополнительного поведения используя класс `HttpServerInterceptor`.
Перехватчики можно накладывать:

- На конкретные методы контроллера
- На весь класс контроллер целиком
- На все классы контроллеры одновременно (требуется использовать `@Tag(HttpServerModule.class)` над классом перехватчиком)

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public static final class MethodInterceptor implements HttpServerInterceptor {

            @Override
            public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain) throws Exception {
                return chain.process(context, request).exceptionally(e -> {
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
                return chain.process(context, request).exceptionally { e ->
                    val body = HttpBody.plaintext(e.message)
                    when (e) {
                        is HttpServerResponseException -> e
                        is IllegalArgumentException -> HttpServerResponse.of(400, body)
                        is TimeoutException -> HttpServerResponse.of(408, body)
                        else -> HttpServerResponse.of(500, body)
                    }
                }
            }
        }

        @InterceptWith(MethodInterceptor::class)
        @HttpRoute(method = HttpMethod.POST, path = "/intercepted")
        fun helloWorld(): String {
            return "Hello World"
        }
    }
    ```

## Контроллер императивный

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

    1. Указывает тип HTTP метода обработчика
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

    1. Указывает тип HTTP метода обработчика
    2. Указывает путь метода обработчика
