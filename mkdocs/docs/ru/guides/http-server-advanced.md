---
search:
  exclude: true
title: Руководство по продвинутому HTTP-серверу
summary: Extend the basic Kora HTTP server with request context mapping, additional body formats, controller interceptors, consistent error responses, and simple API-key authorization
tags: http-server, advanced, interceptors, request-mapping, auth, forms
---

# Руководство по продвинутому HTTP-серверу { #advanced-http-server-guide }

В этом руководстве рассматриваются продвинутые возможности HTTP-сервера в Kora. Вы узнаете, как контекст запроса, тела форм, multipart-загрузки, перехватчики контроллеров, глобальная обработка ошибок
и простая авторизация по ключу API встраиваются вокруг той же структуры контроллер-сервис, которая используется в базовых API. Вы также увидите, как эти транспортные задачи остаются явными на
HTTP-границе, не заставляя хранение данных или прикладную логику знать о низкоуровневой обработке запросов.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-server-advanced-app).

## Что вы создадите { #youll-build }

Вы расширите сервер:

- типизированным `RequestContextMapper`
- `DataController` для форм, multipart-загрузок и вспомогательных маршрутов для руководства по продвинутому клиенту
- `LoggingInterceptor` уровня контроллера
- общим `ErrorResponse`
- глобальным `ExceptionHandler`
- простой проверкой `Authorization: ApiKey ...` для `DataController`

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- пройденное [руководство по HTTP-серверу](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по HTTP-серверу"

    Это руководство предполагает, что вы уже прошли **[Руководство по HTTP-серверу](http-server.md)** и у вас есть рабочее CRUD-приложение с `Application`, `UserController`, `UserService`, `UserRepository` и `InMemoryUserRepository`.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь тот же API расширяется продвинутым сопоставлением запросов, перехватчиками, обработкой ошибок и авторизацией.

## Обзор { #overview }

Базовые CRUD-маршруты с [JSON](https://www.json.org/json-en.html) покрывают самый частый сценарий HTTP, но поверхность [HTTP](https://www.rfc-editor.org/rfc/rfc9110) шире, чем JSON-тела и
path-переменные. Настоящим API часто нужны более богатое сопоставление запросов, переиспользуемое поведение вокруг маршрутов, единообразные ответы об ошибках и легкие проверки безопасности на
транспортной границе.

Руководство по продвинутому серверу сохраняет ту же модель приложения и расширяет только HTTP-край. Это отражает промышленный код: сервису и репозиторию не должно быть важно, пришел ли запрос из JSON,
формы, multipart-загрузки или маршрута, защищенного перехватчиком.

### Формы запросов за пределами JSON { #request-forms-beyond-json }

Не каждый HTTP-запрос является JSON-документом. Некоторые конечные точки получают поля форм, загруженные файлы, сырые тела, заголовки или метаданные запроса. Kora позволяет методам контроллера
объявлять эти входные данные как типизированные параметры, поэтому сигнатура метода по-прежнему описывает транспортный контракт.

Это руководство расширяет обработку запросов:

- контекстом запроса для метаданных, которые относятся к текущему HTTP-запросу
- полями формы для классических потоков `application/x-www-form-urlencoded`
- multipart-частями для конечных точек в стиле загрузки файлов
- вспомогательными маршрутами, которые показывают пользовательское сопоставление и управление ответом

### Сквозное HTTP-поведение { #cross-cutting-http-behavior }

Некоторое поведение должно применяться вокруг маршрутов, а не внутри тела каждого метода. Для этого в HTTP-сервере используются перехватчики. Они могут наблюдать или изменять обработку запроса до и
после выполнения метода контроллера. Это делает их подходящими для журналирования, легкой авторизации, обогащения запроса или других политик транспортного уровня.

Важная граница в том, что перехватчики должны оставаться сосредоточенными на HTTP-задачах. Они не должны становиться скрытым сервисным слоем.

### Границы ошибок и авторизации { #error-authorization-boundaries }

Когда API растут, непоследовательные ошибки становятся болезненными для клиентов. Общий обработчик исключений дает ошибкам предсказуемую форму ответа. Простая авторизация по ключу API показывает еще
одну распространенную транспортную границу: область контроллера можно защитить до запуска бизнес-логики, а сервисы и репозитории останутся неосведомленными о заголовках и метаданных авторизации.

К концу этого руководства слой HTTP-сервера должен ощущаться как нечто большее, чем аннотации маршрутов: это место, где координируются сопоставление запросов, формирование ответов, перехват, обработка
ошибок и простая авторизация.

Практический поток:

1. добавить преобразователь контекста запроса для одного маршрута
2. добавить обработку форм и multipart в отдельный контроллер
3. ввести перехватчики контроллеров
4. централизовать ответы об ошибках через обработчик исключений
5. защитить одну область контроллера простым ключом API

## Собственный преобразователь { #custom-mapper }

Подробные правила для пользовательских параметров маршрута и `HttpServerRequestMapper<T>` смотрите в разделе [самописных параметров HTTP-сервера](../documentation/http-server.md#custom-parameter).

Иногда маршруту нужно больше, чем JSON-тело или path-переменная. Ему также могут понадобиться метаданные запроса, например:

- идентификатор запроса из заголовков
- user agent
- идентификатор сессии из файлов cookie

Можно передавать все эти значения как отдельные параметры метода, но когда они концептуально относятся друг к другу, типизированный объект проще читать и проще развивать позже.

Для этого нужен `HttpServerRequestMapper<T>`. Он позволяет вывести один типизированный параметр из сырого HTTP-запроса.

Создайте `RequestContextMapper`:

===! ":fontawesome-brands-java: `Java`"

    Добавьте эти вложенные типы внутрь `UserController.java`:

    ```java
    public record RequestContext(String requestId, String userAgent, String sessionId) {}

    public static final class RequestContextMapper implements HttpServerRequestMapper<RequestContext> {

        @Override
        public RequestContext apply(HttpServerRequest request) {
            String sessionId = request.cookies().stream()
                    .filter(cookie -> "sessionId".equals(cookie.name()))
                    .map(cookie -> cookie.value())
                    .findFirst()
                    .orElse(null);

            return new RequestContext(
                    request.headers().getFirst("X-Request-ID"),
                    request.headers().getFirst("User-Agent"),
                    sessionId);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте ту же идею в `UserController.kt`:

    ```kotlin
    data class RequestContext(
        val requestId: String?,
        val userAgent: String?,
        val sessionId: String?
    )

    class RequestContextMapper : HttpServerRequestMapper<RequestContext> {
        override fun apply(request: HttpServerRequest): RequestContext {
            val sessionId = request.cookies()
                .firstOrNull { it.name() == "sessionId" }
                ?.value()

            return RequestContext(
                request.headers().getFirst("X-Request-ID"),
                request.headers().getFirst("User-Agent"),
                sessionId
            )
        }
    }
    ```

Используйте его в `createUser()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    @Json
    public HttpResponseEntity<UserResponse> createUser(
            @Json UserRequest request,
            @Mapping(RequestContextMapper.class) RequestContext context) {
        System.out.printf(
                "Creating user with request ID: %s, user agent: %s, session ID: %s%n",
                context.requestId(), context.userAgent(), context.sessionId());

        UserResponse user = userService.createUser(request);
        return HttpResponseEntity.of(201, HttpHeaders.of(), user);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    @Json
    fun createUser(
        @Json request: UserRequest,
        @Mapping(RequestContextMapper::class) context: RequestContext
    ): HttpResponseEntity<UserResponse> {
        println(
            "Creating user with request ID: ${context.requestId}, " +
                "user agent: ${context.userAgent}, session ID: ${context.sessionId}"
        )

        val user = userService.createUser(request)
        return HttpResponseEntity.of(201, HttpHeaders.of(), user)
    }
    ```

Почему эта абстракция полезна:

- `HttpServerRequestMapper<T>` позволяет создать любой типизированный объект из запроса
- `@Mapping(...)` говорит Kora использовать этот преобразователь для одного конкретного параметра
- сигнатура маршрута остается компактной, даже когда маршруту нужно несколько значений, полученных из запроса

Часто это лучше подходит, чем бесконечно расширять сигнатуры методов контроллера.

## Новый контроллер { #new-controller }

Полная модель тел запросов, JSON, форм и multipart описана в разделе [тела запроса HTTP-сервера](../documentation/http-server.md#request-body).

Следующая продвинутая тема — тела запросов, которые не являются JSON.

Пока базовое руководство использовало только JSON DTO. Настоящим HTTP API также часто нужны:

- `application/x-www-form-urlencoded`
- `multipart/form-data`

Что это за форматы:

- `application/x-www-form-urlencoded` — классический формат браузерных форм. Очень типичный пример — обычная форма создания учетной записи на сайте, где браузер отправляет небольшой набор текстовых
  полей.
- `multipart/form-data` — формат, который используется, когда запрос разделен на именованные части, особенно когда присутствуют файлы или бинарное содержимое.

Можно думать о них так:

- используйте `form-url-encoded`, когда тело в основном является небольшим набором текстовых полей
- используйте multipart, когда тело состоит из именованных частей и часть этих частей может быть файлами

Даже в JSON-first системах эти форматы все еще часто встречаются:

- браузерные административные инструменты
- старые интеграции
- конечные точки загрузки
- поставщики webhook

`DataController` помогает, потому что мы намеренно держим эти маршруты вне `UserController`:

- `UserController` остается сосредоточен на пользовательском CRUD
- `DataController` становится транспортной площадкой для альтернативных форматов HTTP-тела

Так бизнес-ориентированный контроллер остается проще для чтения.

Создайте `DataController`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataController.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    import java.util.List;
    import java.util.stream.Collectors;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.common.form.FormMultipart;
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class DataController {

        @HttpRoute(method = HttpMethod.POST, path = "/data/form")
        public String processForm(FormUrlEncoded formBody) {
            var namePart = formBody.get("name");
            var name = namePart == null || namePart.values().isEmpty() ? "World" : namePart.values().get(0);
            return "Hello World, " + name;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
        @Json
        public UploadResponse processUpload(FormMultipart multipart) {
            List<String> fileNames = multipart.parts().stream()
                    .map(FormMultipart.FormPart::name)
                    .sorted()
                    .collect(Collectors.toList());
            return new UploadResponse(fileNames.size(), fileNames);
        }

        @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
        public String processMappedRequest(String body) {
            return "Received mapped body: " + body;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
        @Json
        public Payload mappingByCode(@Path int code) {
            if (code == 200) {
                return new Payload("Hello from response mapper");
            }
            throw HttpServerResponseException.of(code, "Request failed with code " + code);
        }

        @Json
        public record Payload(String message) {}

        @Json
        public record UploadResponse(int fileCount, List<String> fileNames) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataController.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.common.form.FormMultipart
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class DataController {

        @HttpRoute(method = HttpMethod.POST, path = "/data/form")
        fun processForm(formBody: FormUrlEncoded): String {
            val name = formBody.get("name")?.values()?.firstOrNull() ?: "World"
            return "Hello World, $name"
        }

        @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
        @Json
        fun processUpload(multipart: FormMultipart): UploadResponse {
            val fileNames = multipart.parts().map { it.name() }.sorted()
            return UploadResponse(fileNames.size, fileNames)
        }

        @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
        fun processMappedRequest(body: String): String {
            return "Received mapped body: $body"
        }

        @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
        @Json
        fun mappingByCode(@Path code: Int): Payload {
            if (code == 200) {
                return Payload("Hello from response mapper")
            }
            throw HttpServerResponseException.of(code, "Request failed with code $code")
        }
    }

    @Json
    data class Payload(val message: String)

    @Json
    data class UploadResponse(val fileCount: Int, val fileNames: List<String>)
    ```

Вспомогательные маршруты внизу намеренно маленькие. Они существуют, чтобы следующее руководство, [Руководство по продвинутому HTTP-клиенту](http-client-advanced.md), могло показать:

- пользовательское сопоставление запроса на `POST /data/mapping-request`
- декодирование по конкретному коду ответа на `GET /data/mapping-by-code/{code}`

Успешная ветка возвращает маленький `Payload(message)`. Ветка ошибки выбрасывает `HttpServerResponseException`, а глобальный `ExceptionHandler` превращает это в общий
JSON-контракт `ErrorResponse(message)` для ответов не с 200.

## Перехватчик логгирования { #logging-interceptor }

Подробнее о локальных и глобальных перехватчиках HTTP-сервера смотрите в разделе [перехватчиков](../documentation/http-server.md#interceptors).

Следующая тема — перехватчики.

Перехватчик полезен, когда нужно переиспользуемое поведение вокруг обработки запросов, например:

- журналирование
- измерение времени
- метрики
- проверки безопасности
- пользовательская сквозная транспортная логика

Важный проектный вопрос — область действия.

Иногда поведение нужно для всего сервера. Иногда оно нужно только вокруг одного контроллера или одной группы маршрутов. Здесь мы начинаем с более узкого и безопасного случая: перехватчика уровня
контроллера.

Создайте `LoggingInterceptor`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/LoggingInterceptor.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    import java.util.concurrent.CompletionStage;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor;
    import ru.tinkoff.kora.http.server.common.HttpServerRequest;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;

    @Component
    public final class LoggingInterceptor implements HttpServerInterceptor {

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain)
                throws Exception {
            long started = System.nanoTime();
            return chain.process(context, request).whenComplete((response, throwable) -> {
                long durationMs = (System.nanoTime() - started) / 1_000_000;
                int statusCode = response != null ? response.code() : 500;
                System.out.printf("Request: %s %s -> %d (%d ms)%n", request.method(), request.path(), statusCode, durationMs);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/LoggingInterceptor.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    import java.util.concurrent.CompletionStage
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor
    import ru.tinkoff.kora.http.server.common.HttpServerRequest
    import ru.tinkoff.kora.http.server.common.HttpServerResponse

    @Component
    class LoggingInterceptor : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            val started = System.nanoTime()
            return chain.process(context, request).whenComplete { response, _ ->
                val durationMs = (System.nanoTime() - started) / 1_000_000
                val statusCode = response?.code() ?: 500
                println("Request: ${request.method()} ${request.path()} -> $statusCode (${durationMs} ms)")
            }
        }
    }
    ```

Примените его только к `UserController`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    @InterceptWith(LoggingInterceptor.class)
    public final class UserController {
        // existing routes stay the same
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    @InterceptWith(LoggingInterceptor::class)
    class UserController(
        private val userService: UserService
    ) {
        // existing routes stay the same
    }
    ```

Это хороший пример того, почему перехватчики с областью действия контроллера полезны:

- они сохраняют поведение переиспользуемым
- но не влияют на несвязанные контроллеры
- и их часто легче понимать, чем сразу делать поведение глобальным

## Перехватчик ошибок { #error-interceptor }

Полные варианты обработки исключений и сопоставления ошибок описаны в разделе [обработки ошибок HTTP-сервера](../documentation/http-server.md#error-handling).

Теперь мы переходим от поведения, локального для контроллера, к поведению всего сервера.

Обработка ошибок — классический случай, где команды часто хотят более сильного контроля:

- одна и та же JSON-форма для всех ошибок
- одно место для перевода исключений в HTTP-ответы
- меньше повторяющейся логики форматирования ошибок в контроллерах

Именно поэтому общий `ErrorResponse` и глобальный `ExceptionHandler` являются распространенными шаблонами.

Создайте `ErrorResponse`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/dto/ErrorResponse.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record ErrorResponse(String message) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/dto/ErrorResponse.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class ErrorResponse(
        val message: String
    )
    ```

Создайте небольшое исключение для намеренно запрещенного имени формы:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/RestrictedFormNameException.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    public final class RestrictedFormNameException extends RuntimeException {

        public RestrictedFormNameException(String name) {
            super("Form name '" + name + "' is restricted");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/RestrictedFormNameException.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    class RestrictedFormNameException(name: String) :
        RuntimeException("Form name '$name' is restricted")
    ```

Теперь обновите маршрут формы, чтобы у нового исключения был конкретный источник:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.POST, path = "/data/form")
    public String processForm(FormUrlEncoded formBody) {
        var namePart = formBody.get("name");
        var name = namePart == null || namePart.values().isEmpty() ? "World" : namePart.values().get(0);
        if ("admin".equalsIgnoreCase(name)) {
            throw new RestrictedFormNameException(name);
        }
        return "Hello World, " + name;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.POST, path = "/data/form")
    fun processForm(formBody: FormUrlEncoded): String {
        val name = formBody.get("name")?.values()?.firstOrNull() ?: "World"
        if (name.equals("admin", ignoreCase = true)) {
            throw RestrictedFormNameException(name)
        }
        return "Hello World, $name"
    }
    ```

Создайте глобальный `ExceptionHandler`:

Kora позволяет применить перехватчик ко всему HTTP-серверу, если пометить его тегом `HttpServerModule`. Именно это делает перехватчик глобальным, а не локальным для контроллера.

Перехватчик зависит от `JsonWriter<ErrorResponse>`, поэтому он всегда может сериализовать одно и то же типизированное тело ошибки, а не собирать отдельные строки вручную. Так транспортный контракт
ошибок остается явным и единообразным.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/ExceptionHandler.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    import java.util.concurrent.CompletionException;
    import java.util.concurrent.CompletionStage;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.httpserver.advanced.dto.ErrorResponse;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor;
    import ru.tinkoff.kora.http.server.common.HttpServerModule;
    import ru.tinkoff.kora.http.server.common.HttpServerRequest;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.json.common.JsonWriter;

    @Tag(HttpServerModule.class)
    @Component
    public final class ExceptionHandler implements HttpServerInterceptor {

        private final JsonWriter<ErrorResponse> errorJsonWriter;

        public ExceptionHandler(JsonWriter<ErrorResponse> errorJsonWriter) {
            this.errorJsonWriter = errorJsonWriter;
        }

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain)
                throws Exception {
            return chain.process(context, request).exceptionally(throwable -> {
                Throwable cause = unwrap(throwable);
                if (cause instanceof RestrictedFormNameException restrictedFormNameException) {
                    return jsonResponse(400, restrictedFormNameException.getMessage());
                }
                if (cause instanceof HttpServerResponseException responseException) {
                    return jsonResponse(responseException.code(), responseException.getMessage());
                }
                if (cause instanceof IllegalArgumentException) {
                    return jsonResponse(400, "Invalid request parameters");
                }
                if (cause instanceof SecurityException) {
                    return jsonResponse(403, cause.getMessage() != null ? cause.getMessage() : "Access denied");
                }
                return jsonResponse(500, "An unexpected error occurred");
            });
        }

        private HttpServerResponse jsonResponse(int statusCode, String message) {
            return HttpServerResponse.of(statusCode, HttpBody.json(this.errorJsonWriter.toByteArrayUnchecked(new ErrorResponse(message))));
        }

        private static Throwable unwrap(Throwable throwable) {
            Throwable current = throwable;
            while (current instanceof CompletionException && current.getCause() != null) {
                current = current.getCause();
            }
            return current;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/ExceptionHandler.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    import java.util.concurrent.CompletionException
    import java.util.concurrent.CompletionStage
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.httpserver.advanced.dto.ErrorResponse
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor
    import ru.tinkoff.kora.http.server.common.HttpServerModule
    import ru.tinkoff.kora.http.server.common.HttpServerRequest
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    import ru.tinkoff.kora.json.common.JsonWriter

    @Tag(HttpServerModule::class)
    @Component
    class ExceptionHandler(
        private val errorJsonWriter: JsonWriter<ErrorResponse>
    ) : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            return chain.process(context, request).exceptionally { throwable ->
                val cause = unwrap(throwable)
                when (cause) {
                    is RestrictedFormNameException -> jsonResponse(400, cause.message ?: "Restricted form name")
                    is HttpServerResponseException -> jsonResponse(cause.code(), cause.message ?: "HTTP error")
                    is IllegalArgumentException -> jsonResponse(400, "Invalid request parameters")
                    is SecurityException -> jsonResponse(403, cause.message ?: "Access denied")
                    else -> jsonResponse(500, "An unexpected error occurred")
                }
            }
        }

        private fun jsonResponse(statusCode: Int, message: String): HttpServerResponse {
            return HttpServerResponse.of(statusCode, HttpBody.json(errorJsonWriter.toByteArrayUnchecked(ErrorResponse(message))))
        }

        private fun unwrap(throwable: Throwable): Throwable {
            var current = throwable
            while (current is CompletionException && current.cause != null) {
                current = current.cause!!
            }
            return current
        }
    }
    ```

Оставьте обычный поиск пользователя локальным для `UserController`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    public UserResponse getUser(@Path String userId) {
        return userService.getUser(userId)
                .orElseThrow(() -> HttpServerResponseException.of(404, "User not found"));
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    fun getUser(@Path userId: String): UserResponse {
        return userService.getUser(userId)
            .orElseThrow { HttpServerResponseException.of(404, "User not found") }
    }
    ```

Это полезное разделение:

- маршрут формы выбрасывает пользовательскую прикладную ошибку только для нового продвинутого поведения
- обычные HTTP-ошибки состояния по-прежнему могут использовать `HttpServerResponseException`
- один перехватчик переводит обе формы в один и тот же вид ответа
- весь API теперь возвращает одну форму `ErrorResponse`

## Авторизация по ключу { #api-key }

Эта секция использует перехватчик как транспортную границу; общие правила применения перехватчиков описаны в [документации HTTP-сервера](../documentation/http-server.md#interceptors).

Последний шаг вводит небольшой механизм безопасности.

Мы не защищаем все приложение. Мы защищаем только `DataController`, потому что это хорошее изолированное место, где можно показать шаблон, не усложняя основной CRUD-поток.

Идея намеренно простая:

- ожидаемый ключ API живет в конфигурации
- значение может приходить из `HTTP_ADVANCED_API_KEY`
- перехватчик читает заголовок `Authorization`
- если значение не совпадает, перехватчик выбрасывает `SecurityException`
- глобальный `ExceptionHandler` превращает это в JSON-ответ `403`

Это не попытка показать промышленную аутентификацию. Это легкий учебный пример, который показывает, как перехватчики Kora и конфигурация могут работать вместе для проверок, похожих на авторизацию.

Создайте контракт `DataApiAuthConfig`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataApiAuthConfig.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface DataApiAuthConfig {
        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataApiAuthConfig.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface DataApiAuthConfig {
        fun value(): String
    }
    ```

Создайте `DataApiAuthInterceptor`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataApiAuthInterceptor.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    import java.util.concurrent.CompletionStage;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor;
    import ru.tinkoff.kora.http.server.common.HttpServerRequest;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;

    @Component
    public final class DataApiAuthInterceptor implements HttpServerInterceptor {

        private final DataApiAuthConfig config;

        public DataApiAuthInterceptor(DataApiAuthConfig config) {
            this.config = config;
        }

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain)
                throws Exception {
            var authorization = request.headers().getFirst("authorization");
            if (!this.config.value().equals(authorization)) {
                throw new SecurityException("Invalid API key");
            }
            return chain.process(context, request);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataApiAuthInterceptor.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    import java.util.concurrent.CompletionStage
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor
    import ru.tinkoff.kora.http.server.common.HttpServerRequest
    import ru.tinkoff.kora.http.server.common.HttpServerResponse

    @Component
    class DataApiAuthInterceptor(
        private val config: DataApiAuthConfig
    ) : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            val authorization = request.headers().getFirst("authorization")
            if (config.value() != authorization) {
                throw SecurityException("Invalid API key")
            }
            return chain.process(context, request)
        }
    }
    ```

Примените его к `DataController`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    @InterceptWith(DataApiAuthInterceptor.class)
    public final class DataController {
        // routes stay the same
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    @InterceptWith(DataApiAuthInterceptor::class)
    class DataController {
        // routes stay the same
    }
    ```

Настройте ключ API:

Добавьте значение авторизации в `application.conf`:

Полное описание настроек смотрите в разделе [Конфигурация](../documentation/config.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    auth {
      apiKey {
        value = "MySecuredApiKey" //(1)!
        value = ${?HTTP_ADVANCED_API_KEY} //(2)!
      }
    }
    ```

    1. Настроенное значение, которое использует компонент руководства.
    2. Настроенное значение, которое использует компонент руководства. Необязательное переопределение через `HTTP_ADVANCED_API_KEY`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    auth:
      apiKey:
        value: ${?HTTP_ADVANCED_API_KEY:"MySecuredApiKey"} #(1)!
    ```

    1. Настроенное значение, которое использует компонент руководства. Использует показанное значение по умолчанию и позволяет `HTTP_ADVANCED_API_KEY` переопределить его.

Локальное значение по умолчанию упрощает запуск руководства, а переопределение через переменную окружения показывает дружественный к промышленной среде шаблон.

## Сгенерированный код { #generated-code }

Декларативные HTTP-контроллеры Kora компилируются в компоненты `HttpServerRequestHandler`.

После запуска:

```bash
./gradlew clean classes
```

изучите сгенерированный модуль:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-http-server-advanced-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataControllerModule.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-http-server-advanced-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataControllerModule.kt
    ```

Например, сгенерированный обработчик для конечной точки формы выглядит так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default HttpServerRequestHandler post_data_form(DataController _controller,
        HttpServerRequestMapper<FormUrlEncoded> formBodyHttpRequestMapper,
        HttpServerResponseMapper<String> _responseMapper,
        BlockingRequestExecutor _executor,
        DataApiAuthInterceptor _interceptor1) {
      return HttpServerRequestHandlerImpl.of("POST", "/data/form", (_ctx, _request) -> {
        try {
          return _interceptor1.intercept(_ctx, _request, (_ctx_1, _request1) -> {
            return _executor.execute(_ctx, () -> {
              final FormUrlEncoded formBody = formBodyHttpRequestMapper.apply(_request1);
              var _result = _controller.processForm(formBody);
              return _responseMapper.apply(_ctx, _request, _result);
            });
          });
        } catch (Exception _e) {
          return CompletableFuture.failedFuture(_e);
        }
      });
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    public fun post_data_form(
      _controller: DataController,
      _formBodyMapper: HttpServerRequestMapper<FormUrlEncoded>,
      _responseMapper: HttpServerResponseMapper<String>,
      _executor: BlockingRequestExecutor,
    ): HttpServerRequestHandler = HttpServerRequestHandlerImpl.of("POST", "/data/form") { _ctx, _request ->
      try {
        _executor.execute(_ctx) {
          val formBody = (_formBodyMapper as HttpServerRequestMapper<FormUrlEncoded?>).apply(_request)
            ?: throw HttpServerResponseException.of(400, "Parameter formBody is not nullable, but got null from mapper")
          val _result = _controller.processForm(formBody)
          return@execute _responseMapper.apply(_ctx, _request, _result)
        }
      } catch (_e: Exception) {
        if (_e is HttpServerResponse) {
          CompletableFuture.failedFuture(_e)
        } else {
          CompletableFuture.failedFuture(HttpServerResponseException.of(400, _e))
        }
      }
    }
    ```

Этот сгенерированный код является мостом между удобным методом контроллера и низкоуровневым конвейером HTTP-сервера:

- `HttpServerRequestHandlerImpl.of(...)` регистрирует метод маршрута и путь
- `HttpServerRequestMapper<FormUrlEncoded>` читает тело запроса
- `DataApiAuthInterceptor` оборачивает маршрут
- `BlockingRequestExecutor` безопасно выполняет блокирующий метод контроллера
- `HttpServerResponseMapper<String>` превращает возвращаемое значение в HTTP-ответ

Это сильный прием отладки и для разработчиков, и для ИИ-помощников: когда поведение маршрута непонятно, сгенерированные исходники показывают точный конвейер запроса, который Kora собрала из аннотаций.

## Императивный контроллер { #imperative-controller }

Для большинства прикладных конечных точек стоит использовать декларативные контроллеры, потому что их проще читать и тестировать. Kora также разрешает низкоуровневый императивный стиль
через `HttpServerRequestHandler`; он полезен, когда нужен прямой контроль над конвейером запроса или когда вы хотите понять, во что компилируются сгенерированные контроллеры.

Добавьте этот ручной обработчик в `Application.java`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/Application.java"
    package ru.tinkoff.kora.guide.httpserver.advanced;

    import java.util.concurrent.CompletableFuture;
    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.guide.httpserver.advanced.controller.DataApiAuthConfig;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandler;
    import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandlerImpl;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowHttpServerModule {  // <----- Подключили модуль

        default HttpServerRequestHandler manualDataPingHandler(DataApiAuthConfig authConfig) {
            return HttpServerRequestHandlerImpl.get("/manual/data/ping", (context, request) -> {
                var authorization = request.headers().getFirst("authorization");
                if (!authConfig.value().equals(authorization)) {
                    return CompletableFuture.completedFuture(
                            HttpServerResponse.of(403, HttpBody.plaintext("Invalid API key")));
                }
                return CompletableFuture.completedFuture(
                        HttpServerResponse.of(200, HttpBody.plaintext("manual-data-pong")));
            });
        }

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/Application.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.guide.httpserver.advanced.controller.DataApiAuthConfig
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandler
    import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandlerImpl
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import java.util.concurrent.CompletableFuture

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowHttpServerModule {  // <----- Подключили модуль

        fun manualDataPingHandler(authConfig: DataApiAuthConfig): HttpServerRequestHandler {
            return HttpServerRequestHandlerImpl.get("/manual/data/ping") { _, request ->
                val authorization = request.headers().getFirst("authorization")
                if (authConfig.value() != authorization) {
                    CompletableFuture.completedFuture(HttpServerResponse.of(403, HttpBody.plaintext("Invalid API key")))
                } else {
                    CompletableFuture.completedFuture(HttpServerResponse.of(200, HttpBody.plaintext("manual-data-pong")))
                }
            }
        }
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Метод напрямую возвращает обработчик фреймворка:

- `HttpServerRequestHandlerImpl.get(...)` регистрирует `GET /manual/data/ping`
- лямбда получает `Context` и `HttpServerRequest`
- обработчик вручную читает заголовок `Authorization`
- метод возвращает `CompletionStage<HttpServerResponse>` через `CompletableFuture.completedFuture(...)`

После компиляции сгенерированный граф приложения подключает этот обработчик как еще один HTTP-маршрут:

===! ":fontawesome-brands-java: `Java`"

    ```java
    component44 = graphDraw.addNode0(_type_of_component44, new Class<?>[]{}, g -> impl.manualDataPingHandler(
          g.get(ApplicationGraph.holder0.component29)
        ), List.of(), component29);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    component28 = graphDraw.addNode0(map["component28"],
      arrayOf(),
      { impl.manualDataPingHandler(
        it.get(holder0.component27)
      ) },
      listOf(),
      component27
    )
    ```

Важное отличие в том, что декларативные контроллеры генерируют `HttpServerRequestHandler` за вас, а императивный стиль позволяет предоставить этот обработчик самостоятельно.

## Проверка приложения { #check-app }

```
./gradlew clean classes
./gradlew test
./gradlew run
```

Попробуйте более насыщенный запрос `createUser` с метаданными запроса:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-123" \
  -H "User-Agent: curl-test" \
  -H "Cookie: sessionId=session-42" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

Затем вызовите защищенные маршруты `DataController` с ключом API:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Authorization: MySecuredApiKey" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Ivan"

curl -X POST http://localhost:8080/data/upload \
  -H "Authorization: MySecuredApiKey" \
  -F "file=@README.md"

curl http://localhost:8080/manual/data/ping \
  -H "Authorization: MySecuredApiKey"
```

Если заголовок `Authorization` отсутствует или указан неверно, маршрут должен вернуть `403` с общим телом `ErrorResponse`.

## Лучшие практики { #best-practices }

- Вводите продвинутые HTTP-концепции по одной, а не смешивайте их с первым примером сервера.
- Используйте `HttpServerRequestMapper`, когда несколько значений запроса относятся к одному типизированному понятию.
- Держите маршруты, завязанные на транспорт, в отдельном контроллере, чтобы бизнес-контроллеры оставались сфокусированными.
- Предпочитайте перехватчики уровня контроллера, прежде чем делать поведение глобальным.
- Используйте глобальный перехватчик только для поведения, которое действительно должно влиять на весь HTTP-сервер.
- Используйте императивный `HttpServerRequestHandler` умеренно, когда прямое управление запросом и ответом понятнее аннотаций.
- Даже в учебных приложениях помещайте простые секреты за переопределения через переменные окружения.

## Итоги { #summary }

Вы расширили базовый HTTP-сервер Kora следующими возможностями:

- типизированным `RequestContextMapper`
- `DataController` для форм, многочастных загрузок и продвинутых вспомогательных маршрутов клиента
- перехватчиком уровня контроллера `LoggingInterceptor`
- общим `ErrorResponse`
- глобальным `ExceptionHandler`
- простой авторизацией по ключу API на `DataController`
- ручной конечной точкой `HttpServerRequestHandler`, которая показывает низкоуровневый API маршрутов

## Что вы изучили { #you-learned }

- пользовательское отображение запросов через `HttpServerRequestMapper` и `@Mapping`
- дополнительные форматы тела через `FormUrlEncoded` и `FormMultipart`
- перехватчики уровня контроллера через `@InterceptWith`
- глобальные перехватчики через `@Tag(HttpServerModule.class)`
- простая авторизация по заголовку через перехватчик и конфигурацию
- императивная регистрация маршрутов через `HttpServerRequestHandlerImpl`

## Устранение неполадок { #troubleshooting }

**`RequestContextMapper` не используется:**

- Проверьте, что параметр аннотирован `@Mapping(...)`.
- Убедитесь, что отображатель реализует `HttpServerRequestMapper<T>`.

**Multipart-запрос не работает:**

- Убедитесь, что клиент отправляет `multipart/form-data`.
- Проверьте, что имена загружаемых частей совпадают с тем, что обрабатывает контроллер.

**Журналирование уровня контроллера не появляется:**

- Проверьте `@InterceptWith(LoggingInterceptor.class)` или `@InterceptWith(LoggingInterceptor::class)` на контроллере.
- Убедитесь, что сам перехватчик является компонентом.

**Глобальный обработчик исключений не запускается:**

- Проверьте `@Tag(HttpServerModule.class)` на перехватчике.
- Убедитесь, что класс также аннотирован `@Component`.

**Защищенные маршруты `DataController` возвращают 403:**

- Проверьте значение заголовка `Authorization`.
- Убедитесь, что оно совпадает с `auth.apiKey.value`.
- Если вы используете `HTTP_ADVANCED_API_KEY`, помните, что он переопределяет локальное значение по умолчанию.

## Что дальше? { #whats-next }

- [Хранение файлов в S3](s3.md), чтобы развить модель многочастных запросов и продвинутой обработки HTTP-запросов.
- [HTTP-клиент](http-client.md), если вы еще не собирали клиентское приложение.
- [Продвинутый HTTP-клиент](http-client-advanced.md) после HTTP-клиента, чтобы вызвать эти более насыщенные конечные точки из другого приложения Kora.
- [OpenAPI HTTP-сервер](openapi-http-server.md) перед [Продвинутый OpenAPI HTTP-сервер](openapi-http-server-advanced.md), потому что продвинутое руководство по OpenAPI требует обе ветки.
- [Наблюдаемость](observability.md), чтобы наблюдать за продвинутыми отображениями запросов, перехватчиками и обработкой ошибок.

## Помощь { #help }

Если вы застряли:

- сравните с [Kora Java HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-advanced-app) и [Kora Kotlin HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-server-advanced-app)
- вернитесь к [HTTP-сервер](http-server.md) для базового потока контроллер-сервис-репозиторий
- проверьте [документацию HTTP-сервера](../documentation/http-server.md)
- проверьте [документацию контейнера](../documentation/container.md)
