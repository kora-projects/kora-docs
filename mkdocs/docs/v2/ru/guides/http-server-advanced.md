---
search:
  exclude: true
title: Руководство по продвинутому HTTP-серверу
summary: Extend the basic Kora HTTP server with request context mapping, additional body formats, controller interceptors, consistent error responses, and simple API-key authorization
description: "Advanced Kora HTTP server topics: HttpServerRequestMapper with @Mapping for typed request context, FormUrlEncoded and FormMultipart bodies, controller interceptors with @InterceptWith, global interceptors tagged @Tag(HttpServer.class), a shared JSON error contract built on JsonWriter.toByteArray, API-key authorization from @ConfigSource, the generated controller module, imperative HttpServerRequestHandlerImpl routes and parallel work inside a synchronous handler."
agent:
  use_when: "Use this file for questions about advanced Kora HTTP server work: HttpServerRequestMapper and @Mapping, FormUrlEncoded and FormMultipart request bodies, @InterceptWith controller and method interceptors, global interceptors registered with @Tag(HttpServer.class), HttpServerInterceptor.InterceptChain.process, turning exceptions into a shared JSON ErrorResponse, API-key checks from @ConfigSource, reading the generated *ControllerModule sources, imperative HttpServerRequestHandlerImpl handlers, and why suspend or CompletionStage controller methods are rejected."
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
- контроллером `DataController` для форм, multipart-загрузок и вспомогательных маршрутов продвинутого руководства по клиенту
- перехватчиком уровня контроллера `LoggingInterceptor`
- общим `ErrorResponse`
- глобальным `ExceptionHandler`
- простой проверкой `Authorization: ApiKey ...` для `DataController`

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Текстовый редактор или IDE
- Пройденное [Руководство по HTTP-серверу](http-server.md)

## Требования { #prerequisites }

!!! note "Необходимо: пройти руководство по HTTP-серверу"

    Руководство предполагает, что вы прошли **[Руководство по HTTP-серверу](http-server.md)** и у вас есть рабочее CRUD-приложение с `Application`, `UserController`, `UserService`, `UserRepository` и `InMemoryUserRepository`.

    Если руководство по HTTP-серверу еще не пройдено, начните с него: здесь тот же API расширяется продвинутым маппингом запросов, перехватчиками, обработкой ошибок и авторизацией.

## Обзор { #overview }

Базовые CRUD-маршруты на [JSON](https://www.json.org/json-en.html) закрывают самый частый сценарий HTTP, но у [HTTP](https://www.rfc-editor.org/rfc/rfc9110) поверхность шире, чем JSON-тела и
переменные пути. Реальным API часто нужны более богатый маппинг запросов, переиспользуемое поведение вокруг маршрутов, единообразные ответы об ошибках и легковесные проверки безопасности на границе
транспорта.

Продвинутое руководство сохраняет ту же модель приложения и расширяет только HTTP-край. Это отражает продуктовый код: сервис и репозиторий не должны знать, пришел ли запрос из JSON, формы,
multipart-загрузки или маршрута, защищенного перехватчиком.

### Формы запросов за пределами JSON { #request-forms-beyond-json }

Не каждый HTTP-запрос — это JSON-документ. Некоторые эндпоинты получают поля форм, загруженные файлы, «сырые» тела, заголовки или метаданные запроса. Kora позволяет методам контроллера объявлять такие
входные данные типизированными параметрами, так что сигнатура метода по-прежнему описывает транспортный контракт.

Это руководство расширяет обработку запросов:

- контекстом запроса для метаданных текущего HTTP-запроса
- полями формы для классических потоков `application/x-www-form-urlencoded`
- multipart-частями для эндпоинтов загрузки файлов
- вспомогательными маршрутами, которые демонстрируют собственный маппинг и контроль ответа

### Сквозное HTTP-поведение { #cross-cutting-http-behavior }

Часть поведения должна применяться вокруг маршрутов, а не внутри тела каждого метода. Для этого в HTTP-сервере есть перехватчики. Они могут наблюдать или изменять обработку запроса до и после вызова
метода контроллера. Это делает их подходящими для логирования, легковесной авторизации, обогащения запроса и другой транспортной политики.

Поскольку обработка синхронная, перехватчик — это обычный вызов метода вокруг остальной цепочки: он вызывает `chain.process(request)`, получает `HttpServerResponse` и может обернуть вызов
в `try/catch/finally`. В контракте нет ни колбэков, ни `CompletionStage`, ни `suspend`-функций.

Важная граница в том, что перехватчики должны оставаться в рамках HTTP-задач. Они не должны превращаться в скрытый сервисный слой.

### Границы ошибок и авторизации { #error-authorization-boundaries }

По мере роста API несогласованные ошибки становятся болезненными для клиентов. Общий обработчик исключений придает отказам предсказуемую форму ответа. Простая авторизация по ключу API показывает
другую типичную транспортную границу: область контроллера можно защитить до запуска бизнес-логики, а сервисы и репозитории останутся в неведении о заголовках и метаданных авторизации.

К концу руководства слой HTTP-сервера должен восприниматься шире, чем аннотации маршрутов: это место, где согласованы маппинг запроса, формирование ответа, перехват, обработка ошибок и простая
авторизация.

Практический порядок такой:

1. добавить преобразователь контекста запроса для одного маршрута
2. добавить обработку форм и multipart в отдельном контроллере
3. ввести перехватчики уровня контроллера
4. централизовать ответы об ошибках через обработчик исключений
5. защитить одну область контроллера простым ключом API

## Собственный преобразователь { #custom-mapper }

Полные правила для пользовательских параметров маршрута и `HttpServerRequestMapper<T>` — в разделе [Пользовательский параметр HTTP-сервера](../documentation/http-server.md#custom-parameter).

Иногда маршруту нужно больше, чем JSON-тело или переменная пути. Ему могут потребоваться метаданные запроса:

- идентификатор запроса из заголовков
- user agent
- идентификатор сессии из cookie

Можно передавать все эти значения отдельными параметрами метода, но как только они логически относятся к одному целому, типизированный объект читается лучше и проще развивается дальше.

Именно для этого существует `HttpServerRequestMapper<T>`. Он позволяет получить один типизированный параметр из «сырого» HTTP-запроса. Интерфейс лежит в `io.koraframework.http.server.common.request`
и содержит единственный синхронный метод `T apply(HttpServerRequest request)`.

Преобразователь, указанный в `@Mapping`, **не** создается сгенерированным модулем контроллера — он запрашивается из графа зависимостей. Поэтому класс преобразователя помечен `@Component`, даже если
у него нет собственных зависимостей в конструкторе.

Создайте `RequestContextMapper`:

===! ":fontawesome-brands-java: `Java`"

    Добавьте эти вложенные типы в `UserController.java` вместе с импортами `org.jspecify.annotations.Nullable`, `io.koraframework.http.common.cookie.Cookie`,
    `io.koraframework.http.server.common.request.HttpServerRequest` и `io.koraframework.http.server.common.request.HttpServerRequestMapper`:

    ```java
    public record RequestContext(@Nullable String requestId, @Nullable String userAgent, @Nullable String sessionId) {}

    @Component
    public static final class RequestContextMapper implements HttpServerRequestMapper<RequestContext> {

        @Override
        public RequestContext apply(HttpServerRequest request) {
            String sessionId = request.cookies().stream()
                    .filter(cookie -> "sessionId".equals(cookie.name()))
                    .map(Cookie::value)
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

    Добавьте ту же идею в `UserController.kt` вместе с импортами `io.koraframework.http.server.common.request.HttpServerRequest` и
    `io.koraframework.http.server.common.request.HttpServerRequestMapper`:

    ```kotlin
    data class RequestContext(
        val requestId: String?,
        val userAgent: String?,
        val sessionId: String?
    )

    @Component
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

Чем полезна эта абстракция:

- `HttpServerRequestMapper<T>` позволяет собрать из запроса любой типизированный объект
- `@Mapping(...)` из `io.koraframework.common.annotation` говорит Kora использовать этот преобразователь для конкретного параметра
- сигнатура маршрута остается компактной, даже когда маршруту нужно несколько значений, выведенных из запроса

Часто это лучше, чем бесконечно растить список параметров метода контроллера.

Исключение, брошенное преобразователем, превращается в ответ `400`, если только само исключение не является `HttpServerResponse`, так что преобразователь — еще и удобное место, чтобы отклонить
некорректный запрос с точным кодом статуса.

## Новый контроллер { #new-controller }

Полная модель тела запроса для JSON, форм и multipart описана в разделе [Тело запроса HTTP-сервера](../documentation/http-server.md#request-body).

Следующая продвинутая тема — тела запросов, которые не являются JSON.

До сих пор базовое руководство использовало только JSON-DTO. Реальным HTTP API также часто нужны:

- `application/x-www-form-urlencoded`
- `multipart/form-data`

Что это за форматы:

- `application/x-www-form-urlencoded` — классический браузерный формат формы. Типичный пример — обычная форма создания аккаунта на сайте, где браузер отправляет небольшой набор текстовых полей.
- `multipart/form-data` — формат, когда запрос разбит на именованные части, особенно если в них есть файлы или бинарный контент.

Ориентироваться можно так:

- form-url-encoded — когда тело по сути является небольшим набором текстовых полей
- multipart — когда тело состоит из именованных частей и некоторые из них могут быть файлами

Даже в JSON-ориентированных системах эти форматы встречаются часто:

- админки в браузере
- легаси-интеграции
- эндпоинты загрузки
- провайдеры вебхуков

И `FormUrlEncoded`, и `FormMultipart` лежат в `io.koraframework.http.common.form`, а преобразователи запроса для них Kora уже предоставляет, поэтому методу контроллера достаточно объявить параметр.

`DataController` помогает тем, что мы намеренно держим такие маршруты вне `UserController`:

- `UserController` остается сосредоточен на CRUD пользователей
- `DataController` становится транспортной песочницей для альтернативных форматов тела HTTP

Так контроллер с бизнес-смыслом читается легче.

Создайте `DataController`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpserver/advanced/controller/DataController.java"
    package io.koraframework.guide.httpserver.advanced.controller;

    import java.util.List;
    import java.util.stream.Collectors;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.common.form.FormMultipart;
    import io.koraframework.http.common.form.FormUrlEncoded;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.json.common.annotation.Json;

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

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpserver/advanced/controller/DataController.kt"
    package io.koraframework.guide.httpserver.advanced.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.common.form.FormMultipart
    import io.koraframework.http.common.form.FormUrlEncoded
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.json.common.annotation.Json

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

`FormUrlEncoded.get(name)` возвращает nullable-`FormPart` со списком значений, а `FormMultipart.parts()` возвращает запечатанную иерархию `FormPart`, где часть — это либо данные, либо файл, либо
поток файла; поэтому маршрут загрузки читает здесь только `name()`.

Вспомогательные маршруты внизу намеренно крошечные. Они существуют, чтобы следующее руководство, [Продвинутый HTTP-клиент](http-client-advanced.md), могло показать:

- собственный маппинг запроса на `POST /data/mapping-request`
- декодирование в зависимости от кода ответа на `GET /data/mapping-by-code/{code}`

Успешная ветка возвращает маленький `Payload(message)`. Ветка ошибки бросает `HttpServerResponseException`, а глобальный `ExceptionHandler` превращает его в общий JSON-контракт `ErrorResponse(message)`
для ответов, отличных от 200.

## Перехватчик логгирования { #logging-interceptor }

Подробнее о локальных и глобальных перехватчиках HTTP-сервера — в разделе [Перехватчики HTTP-сервера](../documentation/http-server.md#interceptors).

Следующая тема — перехватчики.

Перехватчик полезен, когда нужно переиспользуемое поведение вокруг обработки запроса, например:

- логирование
- замер времени
- метрики
- проверки безопасности
- собственная сквозная транспортная логика

Главный вопрос проектирования — область действия.

Иногда поведение нужно для всего сервера. Иногда — только вокруг одного контроллера или группы маршрутов. Начнем с более узкого и безопасного случая: перехватчика уровня контроллера.

Создайте `LoggingInterceptor`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpserver/advanced/controller/LoggingInterceptor.java"
    package io.koraframework.guide.httpserver.advanced.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.server.common.interceptor.HttpServerInterceptor;
    import io.koraframework.http.server.common.request.HttpServerRequest;
    import io.koraframework.http.server.common.response.HttpServerResponse;

    @Component
    public final class LoggingInterceptor implements HttpServerInterceptor {

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
            long started = System.nanoTime();
            int statusCode = 500;
            try {
                var response = chain.process(request);
                statusCode = response.code();
                return response;
            } finally {
                long durationMs = (System.nanoTime() - started) / 1_000_000;
                System.out.printf("Request: %s %s -> %d (%d ms)%n", request.method(), request.path(), statusCode, durationMs);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpserver/advanced/controller/LoggingInterceptor.kt"
    package io.koraframework.guide.httpserver.advanced.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.server.common.interceptor.HttpServerInterceptor
    import io.koraframework.http.server.common.request.HttpServerRequest
    import io.koraframework.http.server.common.response.HttpServerResponse

    @Component
    class LoggingInterceptor : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            val started = System.nanoTime()
            var statusCode = 500
            try {
                val response = chain.process(request)
                statusCode = response.code()
                return response
            } finally {
                val durationMs = (System.nanoTime() - started) / 1_000_000
                println("Request: ${request.method()} ${request.path()} -> $statusCode ($durationMs ms)")
            }
        }
    }
    ```

Контракт перехватчика — один синхронный метод:

- `intercept(request, chain)` получает входящий запрос и оставшуюся цепочку
- `chain.process(request)` выполняет остальные перехватчики и метод контроллера и возвращает ответ
- возврат без вызова `chain.process(...)` замыкает маршрут
- исключение, возникшее глубже в цепочке, просто пробрасывается, поэтому `try/finally` достаточно, чтобы строка лога писалась всегда

Начальное значение `statusCode = 500` — это то, что попадет в лог, если цепочка бросила исключение: в этом случае `chain.process(request)` не возвращает значения, а блок `finally` все равно выполняется.

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

`@InterceptWith` живет в `io.koraframework.http.common.annotation`. Аннотация повторяемая и может стоять на классе контроллера или на отдельном методе-маршруте; перехватчики, объявленные на классе,
выполняются раньше объявленных на методе. Как и `@Mapping`, она ссылается на класс, который Kora разрешает из графа, поэтому `LoggingInterceptor` должен быть `@Component`.

Это хороший пример того, чем полезны перехватчики уровня контроллера:

- поведение остается переиспользуемым
- но не затрагивает посторонние контроллеры
- и о нем обычно проще рассуждать, чем сразу делать поведение глобальным

## Перехватчик ошибок { #error-interceptor }

Полный набор вариантов сопоставления исключений и ошибок описан в разделе [Обработка ошибок HTTP-сервера](../documentation/http-server.md#error-handling).

Теперь переходим от поведения уровня контроллера к поведению уровня всего сервера.

Обработка ошибок — классический случай, когда командам нужен более строгий контроль:

- одинаковая форма JSON для всех ошибок
- одно место, где исключения переводятся в HTTP-ответы
- меньше повторяющейся логики форматирования ошибок в контроллерах

Поэтому общий `ErrorResponse` и глобальный `ExceptionHandler` — распространенные паттерны.

Создайте `ErrorResponse`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpserver/advanced/dto/ErrorResponse.java"
    package io.koraframework.guide.httpserver.advanced.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record ErrorResponse(String message) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpserver/advanced/dto/ErrorResponse.kt"
    package io.koraframework.guide.httpserver.advanced.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class ErrorResponse(
        val message: String
    )
    ```

Создайте небольшое исключение для намеренно запрещенного имени в форме:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpserver/advanced/controller/RestrictedFormNameException.java"
    package io.koraframework.guide.httpserver.advanced.controller;

    public final class RestrictedFormNameException extends RuntimeException {

        public RestrictedFormNameException(String name) {
            super("Form name '" + name + "' is restricted");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpserver/advanced/controller/RestrictedFormNameException.kt"
    package io.koraframework.guide.httpserver.advanced.controller

    class RestrictedFormNameException(name: String) : RuntimeException("Form name '$name' is restricted")
    ```

Теперь обновите маршрут формы, чтобы у нового исключения появился конкретный источник:

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

Kora собирает глобальные перехватчики по тегу `@Tag(HttpServer.class)`: `HttpServerModule` объявляет зависимость роутера как `@Tag(HttpServer.class) All<HttpServerInterceptor> interceptors`. Именно
этот тег, и только он, делает перехватчик глобальным, а не привязанным к контроллеру. `HttpServer` импортируется из `io.koraframework.http.server.common`.

Так как обработка синхронная, обработчик — это обычный `try/catch` вокруг `chain.process(request)`. Перехватчик зависит от `JsonWriter<ErrorResponse>`, поэтому всегда может сериализовать одно и то же
типизированное тело ошибки вместо ручной сборки строк. Эта зависимость в конструкторе — еще и причина, по которой класс обязан быть компонентом графа.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpserver/advanced/controller/ExceptionHandler.java"
    package io.koraframework.guide.httpserver.advanced.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.httpserver.advanced.dto.ErrorResponse;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.HttpServer;
    import io.koraframework.http.server.common.interceptor.HttpServerInterceptor;
    import io.koraframework.http.server.common.request.HttpServerRequest;
    import io.koraframework.http.server.common.response.HttpServerResponse;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.json.common.JsonWriter;

    @Tag(HttpServer.class)
    @Component
    public final class ExceptionHandler implements HttpServerInterceptor {

        private final JsonWriter<ErrorResponse> errorJsonWriter;

        public ExceptionHandler(JsonWriter<ErrorResponse> errorJsonWriter) {
            this.errorJsonWriter = errorJsonWriter;
        }

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) {
            try {
                return chain.process(request);
            } catch (RestrictedFormNameException e) {
                return jsonResponse(400, e.getMessage());
            } catch (HttpServerResponseException e) {
                return jsonResponse(e.code(), e.getMessage());
            } catch (IllegalArgumentException e) {
                return jsonResponse(400, "Invalid request parameters");
            } catch (SecurityException e) {
                return jsonResponse(403, e.getMessage() != null ? e.getMessage() : "Access denied");
            } catch (Exception e) {
                return jsonResponse(500, "An unexpected error occurred");
            }
        }

        private HttpServerResponse jsonResponse(int statusCode, String message) {
            return HttpServerResponse.of(statusCode, HttpBody.json(this.errorJsonWriter.toByteArray(new ErrorResponse(message))));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpserver/advanced/controller/ExceptionHandler.kt"
    package io.koraframework.guide.httpserver.advanced.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.httpserver.advanced.dto.ErrorResponse
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.HttpServer
    import io.koraframework.http.server.common.interceptor.HttpServerInterceptor
    import io.koraframework.http.server.common.request.HttpServerRequest
    import io.koraframework.http.server.common.response.HttpServerResponse
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.json.common.JsonWriter

    @Tag(HttpServer::class)
    @Component
    class ExceptionHandler(
        private val errorJsonWriter: JsonWriter<ErrorResponse>
    ) : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            return try {
                chain.process(request)
            } catch (e: RestrictedFormNameException) {
                jsonResponse(400, e.message ?: "Restricted form name")
            } catch (e: HttpServerResponseException) {
                jsonResponse(e.code(), e.message ?: "HTTP error")
            } catch (e: IllegalArgumentException) {
                jsonResponse(400, "Invalid request parameters")
            } catch (e: SecurityException) {
                jsonResponse(403, e.message ?: "Access denied")
            } catch (e: Exception) {
                jsonResponse(500, "An unexpected error occurred")
            }
        }

        private fun jsonResponse(statusCode: Int, message: String): HttpServerResponse {
            return HttpServerResponse.of(
                statusCode,
                HttpBody.json(errorJsonWriter.toByteArray(ErrorResponse(message)))
            )
        }
    }
    ```

`JsonWriter.toByteArray(...)` не объявляет проверяемых исключений, поэтому обработчику не нужна отдельная ветка `IOException` вокруг сериализации.

???+ warning "Глобальным его делает именно тег"

    Глобальный перехватчик публичного сервера регистрирует только `@Tag(HttpServer.class)` / `@Tag(HttpServer::class)`. Любой другой тег компилируется, но перехватчик просто никогда не вызывается,
    и контракт ошибок тихо исчезает. Чтобы перехватывать все запросы **системного** сервера, используйте тег `@SystemApi`. Если глобальных перехватчиков несколько, они применяются в детерминированном
    порядке, отсортированном по простому имени класса перехватчика.

Оставьте обычный поиск пользователя локальным для `UserController`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    public UserResponse getUser(@Path String userId) {
        return userService.getUser(userId)
                .orElseThrow(() -> HttpServerResponseException.of(404, "User not found: " + userId));
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    fun getUser(@Path userId: String): UserResponse =
        userService.getUser(userId) ?: throw HttpServerResponseException.of(404, "User not found: $userId")
    ```

Это полезное разделение:

- маршрут формы бросает собственную прикладную ошибку только ради нового продвинутого поведения
- обычные отказы по HTTP-статусу по-прежнему используют `HttpServerResponseException`
- один перехватчик переводит обе формы в одинаковую форму ответа
- весь API теперь возвращает одинаковую форму `ErrorResponse`

Глобальный перехватчик также оборачивает ответы `404` и `405`, которые формирует сам роутер, и ошибки разбора параметров, на которые Kora отвечает `400` еще до вызова метода контроллера. Именно это
делает его настоящим контрактом ошибок, а не удобством отдельного контроллера.

## Авторизация по ключу { #api-key }

В этом разделе перехватчик выступает транспортной границей; общие правила перехватчиков описаны в [документации по HTTP-серверу](../documentation/http-server.md#interceptors).

Последний шаг вводит небольшой механизм безопасности.

Мы защищаем не все приложение, а только `DataController`, потому что это удачное изолированное место, чтобы показать паттерн, не усложняя основной CRUD-поток.

Идея намеренно проста:

- ожидаемый ключ API живет в конфигурации
- значение может приходить из `HTTP_ADVANCED_API_KEY`
- перехватчик читает заголовок `Authorization`
- если значение не совпало, перехватчик бросает `SecurityException`
- глобальный `ExceptionHandler` превращает это в JSON-ответ `403`

Это не претендует на аутентификацию промышленного уровня. Это легковесный учебный пример того, как перехватчики Kora и конфигурация работают вместе для проверок вроде авторизации. Про авторизацию на
основе `Principal` и `HttpServerPrincipalExtractor` см. [Авторизация HTTP-сервера](../documentation/http-server.md#authorization).

Создайте контракт `DataApiAuthConfig`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpserver/advanced/controller/DataApiAuthConfig.java"
    package io.koraframework.guide.httpserver.advanced.controller;

    import io.koraframework.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface DataApiAuthConfig {

        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpserver/advanced/controller/DataApiAuthConfig.kt"
    package io.koraframework.guide.httpserver.advanced.controller

    import io.koraframework.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface DataApiAuthConfig {
        fun value(): String
    }
    ```

Создайте `DataApiAuthInterceptor`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpserver/advanced/controller/DataApiAuthInterceptor.java"
    package io.koraframework.guide.httpserver.advanced.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.server.common.interceptor.HttpServerInterceptor;
    import io.koraframework.http.server.common.request.HttpServerRequest;
    import io.koraframework.http.server.common.response.HttpServerResponse;

    @Component
    public final class DataApiAuthInterceptor implements HttpServerInterceptor {

        private final DataApiAuthConfig config;

        public DataApiAuthInterceptor(DataApiAuthConfig config) {
            this.config = config;
        }

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
            var authorization = request.headers().getFirst("authorization");
            if (!this.config.value().equals(authorization)) {
                throw new SecurityException("Invalid API key");
            }
            return chain.process(request);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpserver/advanced/controller/DataApiAuthInterceptor.kt"
    package io.koraframework.guide.httpserver.advanced.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.server.common.interceptor.HttpServerInterceptor
    import io.koraframework.http.server.common.request.HttpServerRequest
    import io.koraframework.http.server.common.response.HttpServerResponse

    @Component
    class DataApiAuthInterceptor(
        private val config: DataApiAuthConfig
    ) : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            val authorization = request.headers().getFirst("authorization")
            if (config.value() != authorization) {
                throw SecurityException("Invalid API key")
            }
            return chain.process(request)
        }
    }
    ```

Имена заголовков сопоставляются в `HttpHeaders` без учета регистра, поэтому `"authorization"` совпадет и с заголовком `Authorization:`, отправленным клиентом.

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

Добавьте значение авторизации в `application.conf`.

Полный справочник по конфигурации — в разделе [Конфигурация](../documentation/config.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    auth {
      apiKey {
        value = "MySecuredApiKey" //(1)!
        value = ${?HTTP_ADVANCED_API_KEY} //(2)!
      }
    }
    ```

    1.  Локальное значение по умолчанию, используемое, когда переменная окружения не задана.
    2.  Необязательное переопределение из `HTTP_ADVANCED_API_KEY`. В HOCON значение по умолчанию выражается двойным присваиванием ключа: второе присваивание пропускается, если переменной нет.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    auth:
      apiKey:
        value: ${HTTP_ADVANCED_API_KEY:MySecuredApiKey} #(1)!
    ```

    1.  Читает `HTTP_ADVANCED_API_KEY` и откатывается к показанному значению по умолчанию. Не пишите `${?VAR:default}`: с `?` весь текст `VAR:default` считается именем ссылки, и ключ не разрешается ни во что.

Локальное значение по умолчанию упрощает запуск руководства, а переопределение через переменную окружения показывает пригодный для продакшена подход.

## Блокирующая и параллельная работа { #blocking-parallel }

HTTP-обработчики Kora синхронны, и это осознанное проектное решение, а не ограничение. Undertow отправляет каждый запрос на виртуальный поток до того, как сгенерированный обработчик вызовет метод
контроллера, поэтому блокирующий ввод-вывод внутри маршрута нормален: запрос в JDBC, HTTP-вызов в другой сервис или чтение файла не занимают платформенный поток.

Процессоры проверяют этот контракт во время компиляции:

===! ":fontawesome-brands-java: `Java`"

    Маршрут, возвращающий `CompletionStage<T>`, `Future<T>` или реактивный `Publisher<T>`, компилируется, но аннотационный процессор выдает предупреждение, а значение трактуется как обычный результат,
    которому нужен собственный преобразователь ответа:

    ```text
    Method return type is CompletionStage<T> which is unsupported and has no meaning
    ```

    Возвращайте само значение. Если одному запросу действительно нужны два независимых вызова одновременно, распараллельте их внутри обработчика и дождитесь результата перед возвратом:

    ```java
    @HttpRoute(method = HttpMethod.GET, path = "/data/summary")
    @Json
    public Payload summary() throws Exception {
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) { //(1)!
            var first = executor.submit(() -> remoteA.load());
            var second = executor.submit(() -> remoteB.load()); //(2)!
            return new Payload(first.get() + " / " + second.get()); //(3)!
        }
    }
    ```

    1.  Один короткоживущий executor на запрос; `close()` дожидается отправленных задач.
    2.  Оба вызова стартуют сразу и выполняются на своих виртуальных потоках.
    3.  Обработчик блокируется здесь и возвращает обычное значение, поэтому контракт маршрута остается синхронным.

=== ":simple-kotlin: `Kotlin`"

    Маршрут с `suspend` отклоняется символьным процессором сразу:

    ```text
    HTTP server controller method is invalid:
      test

    Problem:
      Suspend methods are not supported by the HTTP server controller generator.

    Fix:
      Remove suspend from the controller method.
    ```

    Возвращайте само значение. Если одному запросу действительно нужны два независимых вызова одновременно, распараллельте их внутри обработчика и дождитесь результата перед возвратом:

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/data/summary")
    @Json
    fun summary(): Payload {
        Executors.newVirtualThreadPerTaskExecutor().use { executor -> //(1)!
            val first = executor.submit<String> { remoteA.load() }
            val second = executor.submit<String> { remoteB.load() } //(2)!
            return Payload("${first.get()} / ${second.get()}") //(3)!
        }
    }
    ```

    1.  Один короткоживущий executor на запрос; `close()` дожидается отправленных задач.
    2.  Оба вызова стартуют сразу и выполняются на своих виртуальных потоках.
    3.  Обработчик блокируется здесь и возвращает обычное значение, поэтому контракт маршрута остается синхронным.

То же правило действует для перехватчиков и для реализаций `HttpServerRequestMapper` / `HttpServerResponseMapper`: все они возвращают результат напрямую.

Полное сообщение компилятора про `suspend` дополнительно предлагает структурную конкурентность через `StructuredTaskScope` для такой параллельной работы, но это preview-API, которому нужен
`--enable-preview` на тулчейне JDK 25. Показанному выше executor'у preview-флаг не нужен, поэтому руководство использует именно его.

## Сгенерированный код { #generated-code }

Декларативные HTTP-контроллеры Kora компилируются в компоненты `HttpServerRequestHandler`.

После выполнения:

```bash
./gradlew clean classes
```

посмотрите сгенерированный модуль:

===! ":fontawesome-brands-java: `Java`"

    ```text
    build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/httpserver/advanced/controller/DataControllerModule.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    build/generated/ksp/main/kotlin/io/koraframework/guide/httpserver/advanced/controller/DataControllerModule.kt
    ```

Например, сгенерированный обработчик эндпоинта формы выглядит так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Generated("io.koraframework.http.server.annotation.processor.ControllerModuleGenerator")
    @Module
    public interface DataControllerModule {

      default HttpServerRequestHandler post_data_form(DataController _controller,
          HttpServerRequestMapper<FormUrlEncoded> formBodyHttpRequestMapper,
          HttpServerResponseMapper<String> _responseMapper,
          DataApiAuthInterceptor _interceptor1) {
        return HttpServerRequestHandlerImpl.of("POST", "/data/form", (_request) -> {
          return _interceptor1.intercept(_request, (_request1) -> {
            final FormUrlEncoded formBody;
            try {
              formBody = formBodyHttpRequestMapper.apply(_request1);
            } catch (Exception _e) {
              if (_e instanceof HttpServerResponse) throw _e;
              throw HttpServerResponseException.of(400, _e);
            }
            var _result = _controller.processForm(formBody);
            return _responseMapper.apply(_request, _result);
          });
        });
      }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Generated("io.koraframework.http.server.symbol.procesor.HttpControllerProcessor")
    @Module
    public interface DataControllerModule {

      public fun post_data_form(
        _controller: DataController,
        _formBodyMapper: HttpServerRequestMapper<FormUrlEncoded>,
        _responseMapper: HttpServerResponseMapper<String>,
        _interceptor1: DataApiAuthInterceptor,
      ): HttpServerRequestHandler {
        return HttpServerRequestHandlerImpl.of("POST", "/data/form") { _request ->
          _interceptor1.intercept(_request) process@{ _request1 ->
            val formBody = try {
              (_formBodyMapper as HttpServerRequestMapper<FormUrlEncoded?>).apply(_request1)
            } catch (_e: Exception) {
              if (_e is HttpServerResponse) {
                throw _e
              }
              throw HttpServerResponseException.of(400, _e)
            }
            if (formBody == null) {
              throw HttpServerResponseException.of(400, "Parameter formBody is not nullable, but got null from mapper")
            }
            val _result = _controller.processForm(formBody)
            return@process _responseMapper.apply(_request, _result)
          }
        }
      }
    }
    ```

Этот сгенерированный код — мост между удобным методом контроллера и низкоуровневым конвейером HTTP-сервера:

- `HttpServerRequestHandlerImpl.of(...)` регистрирует метод и путь маршрута, а имя сгенерированного метода выводится из них
- `HttpServerRequestMapper<FormUrlEncoded>` читает тело запроса и внедряется из графа
- `DataApiAuthInterceptor` оборачивает маршрут, а `chain.process(request)` — это вложенная лямбда
- `HttpServerResponseMapper<String>` превращает возвращаемое значение в HTTP-ответ
- сбой преобразователя превращается в `400`, если исключение само не является `HttpServerResponse`

Обратите внимание, чего здесь *нет*: ни переключения на executor, ни `CompletableFuture`, ни колбэков. Обработчик выполняется сверху вниз на том виртуальном потоке, который Undertow выделил запросу.

Это сильный прием отладки и для разработчиков, и для ИИ-ассистентов: когда поведение маршрута непонятно, сгенерированные исходники показывают точный конвейер запроса, который Kora собрала из аннотаций.

## Императивный контроллер { #imperative-controller }

Большинство эндпоинтов приложения должны использовать декларативные контроллеры — их проще читать и тестировать. Kora также допускает более низкоуровневый императивный стиль через
`HttpServerRequestHandler`, который полезен, когда нужен прямой контроль над конвейером запроса или хочется понять, во что компилируются декларативные контроллеры.

`HttpServerRequestHandlerImpl` лежит в `io.koraframework.http.server.common.request` и предлагает по фабрике на каждый HTTP-метод (`get`, `post`, `put`, `delete`, ...) плюс общий `of(method, route,
handler)`. Обработчик — это `HandlerFunction`: он принимает `HttpServerRequest` и возвращает `HttpServerResponse`.

Добавьте этот ручной обработчик в `Application.java` или `Application.kt`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpserver/advanced/Application.java"
    package io.koraframework.guide.httpserver.advanced;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.guide.httpserver.advanced.controller.DataApiAuthConfig;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.request.HttpServerRequestHandler;
    import io.koraframework.http.server.common.request.HttpServerRequestHandlerImpl;
    import io.koraframework.http.server.common.response.HttpServerResponse;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule {  // <----- Connected module

        default HttpServerRequestHandler manualDataPingHandler(DataApiAuthConfig authConfig) {
            return HttpServerRequestHandlerImpl.get("/manual/data/ping", request -> {
                var authorization = request.headers().getFirst("authorization");
                if (!authConfig.value().equals(authorization)) {
                    return HttpServerResponse.of(403, HttpBody.plaintext("Invalid API key"));
                }
                return HttpServerResponse.of(200, HttpBody.plaintext("manual-data-pong"));
            });
        }

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpserver/advanced/Application.kt"
    package io.koraframework.guide.httpserver.advanced

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.guide.httpserver.advanced.controller.DataApiAuthConfig
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.request.HttpServerRequestHandler
    import io.koraframework.http.server.common.request.HttpServerRequestHandlerImpl
    import io.koraframework.http.server.common.response.HttpServerResponse
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule {  // <----- Connected module

        fun manualDataPingHandler(authConfig: DataApiAuthConfig): HttpServerRequestHandler {
            return HttpServerRequestHandlerImpl.get("/manual/data/ping") { request ->
                val authorization = request.headers().getFirst("authorization")
                if (authConfig.value() != authorization) {
                    HttpServerResponse.of(403, HttpBody.plaintext("Invalid API key"))
                } else {
                    HttpServerResponse.of(200, HttpBody.plaintext("manual-data-pong"))
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
- лямбда получает `HttpServerRequest` и возвращает `HttpServerResponse`
- обработчик читает заголовок `Authorization` вручную
- поскольку метод объявлен на интерфейсе `@KoraApp`, его результат становится компонентом графа, и роутер подхватывает его через `All<HttpServerRequestHandler>`
- глобальные перехватчики вроде `ExceptionHandler` по-прежнему оборачивают этот маршрут, потому что их применяет роутер, а не сгенерированный модуль контроллера

После компиляции сгенерированный граф приложения подключает этот обработчик как еще один узел. Номера компонентов зависят от того, сколько компонентов вносят подключенные модули, поэтому в вашей
сборке они будут другими:

===! ":fontawesome-brands-java: `Java`"

    ```java
    component44 = graphDraw.addNode(_type_of_component44,
        null,
        null,
        List.of(component29),
        List.of(component29),
        List.of(),
        g -> impl.manualDataPingHandler(
          g.get(ApplicationGraph.holder0.component29)
        ));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    component28 = graphDraw.addNode(map["component28"],
      null,
      null,
      listOf(component27),
      listOf(component27),
      listOf(),
      { impl.manualDataPingHandler(
        it.get(holder0.component27)
      ) }
    )
    ```

Важное различие в том, что декларативные контроллеры генерируют `HttpServerRequestHandler` за вас, а императивный стиль позволяет предоставить этот обработчик самостоятельно.

## Проверка приложения { #check-app }

```
./gradlew clean classes
./gradlew test
./gradlew run
```

Попробуйте расширенный запрос `createUser` с метаданными:

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

Если заголовок `Authorization` отсутствует или неверен, маршрут должен вернуть `403` с общим телом `ErrorResponse`. Запрещенное имя в форме дает ту же форму ответа с кодом `400`:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Authorization: MySecuredApiKey" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=admin"
# Expected output: {"message":"Form name 'admin' is restricted"}
```

## Лучшие практики { #best-practices }

- Вводите продвинутые HTTP-возможности по одной, а не смешивайте их в первом же примере сервера.
- Используйте `HttpServerRequestMapper`, когда несколько значений запроса относятся к одному типизированному понятию.
- Держите транспортно-специфичные маршруты в отдельном контроллере, чтобы бизнес-контроллеры оставались сфокусированными.
- Предпочитайте перехватчики уровня контроллера, прежде чем делать поведение глобальным.
- Используйте глобальный перехватчик только для поведения, которое действительно должно затрагивать весь HTTP-сервер, и всегда помечайте его `@Tag(HttpServer.class)`.
- Покрывайте глобальный перехватчик тестом: неверный тег компилируется без ошибок и молча отключает его.
- Используйте императивный `HttpServerRequestHandler` умеренно — когда прямой контроль запроса и ответа понятнее аннотаций.
- Прячьте даже простые секреты за переопределением из переменных окружения, в том числе в учебных приложениях.

## Итоги { #summary }

Вы расширили базовый HTTP-сервер Kora:

- типизированным `RequestContextMapper`
- контроллером `DataController` для форм, multipart-загрузок и вспомогательных маршрутов продвинутого клиента
- перехватчиком уровня контроллера `LoggingInterceptor`
- общим `ErrorResponse`
- глобальным `ExceptionHandler`
- простым слоем авторизации по ключу API для `DataController`
- ручным эндпоинтом `HttpServerRequestHandler`, показывающим низкоуровневый API маршрутов

## Что вы изучили { #you-learned }

- собственный маппинг запроса через `HttpServerRequestMapper` и `@Mapping`
- дополнительные форматы тела через `FormUrlEncoded` и `FormMultipart`
- перехватчики уровня контроллера через `@InterceptWith`
- глобальные перехватчики через `@Tag(HttpServer.class)`
- простую авторизацию по заголовку через перехватчик и конфигурацию
- императивную регистрацию маршрута через `HttpServerRequestHandlerImpl`
- почему методы контроллера, перехватчики и преобразователи синхронны и как при этом выполнять работу параллельно

## Устранение неполадок { #troubleshooting }

**RequestContextMapper не используется:**

- Проверьте, что параметр помечен `@Mapping(...)`.
- Убедитесь, что преобразователь реализует `HttpServerRequestMapper<T>`.

**Компиляция падает с `No component found for dependency` и именем преобразователя или перехватчика:**

- Класс, указанный в `@Mapping` или `@InterceptWith`, разрешается из графа и никогда не создается сгенерированным модулем. Добавьте ему `@Component`.

**Multipart-запрос не работает:**

- Убедитесь, что клиент отправляет `multipart/form-data`.
- Проверьте, что имена загружаемых частей соответствуют тому, что обрабатывает контроллер.

**Логирование уровня контроллера не появляется:**

- Проверьте `@InterceptWith(LoggingInterceptor.class)` или `@InterceptWith(LoggingInterceptor::class)` на контроллере.
- Убедитесь, что сам перехватчик является компонентом.

**Глобальный обработчик исключений не срабатывает:**

- Проверьте `@Tag(HttpServer.class)` на перехватчике. Любой другой тег компилируется, но роутер его не собирает.
- Убедитесь, что класс также помечен `@Component`.

**Защищенные маршруты DataController возвращают 403:**

- Проверьте значение заголовка `Authorization`.
- Убедитесь, что оно совпадает с `auth.apiKey.value`.
- Если используете `HTTP_ADVANCED_API_KEY`, помните, что она переопределяет локальное значение по умолчанию.

**Ключ API из YAML не разрешается ни во что:**

- `${?VAR:default}` — недопустимая комбинация: с `?` весь текст `VAR:default` становится именем ссылки. Используйте `${VAR:default}`.

**Сборка Kotlin падает с `Suspend methods are not supported by the HTTP server controller generator`:**

- Уберите `suspend` из метода контроллера и возвращайте значение напрямую.

## Что дальше? { #whats-next }

- [Хранение файлов в S3](s3.md) — чтобы развить модель multipart и продвинутой обработки HTTP-запросов.
- [HTTP-клиент](http-client.md) — если клиентское приложение еще не построено.
- [Продвинутый HTTP-клиент](http-client-advanced.md) — после HTTP-клиента, чтобы вызывать эти более сложные эндпоинты из другого приложения Kora.
- [OpenAPI HTTP-сервер](openapi-http-server.md) перед [Продвинутым OpenAPI HTTP-сервером](openapi-http-server-advanced.md), потому что продвинутое руководство по OpenAPI требует обеих веток.
- [Наблюдаемость](observability.md) — чтобы мониторить продвинутые маппинги запросов, перехватчики и обработку ошибок.

## Помощь { #help }

Если застряли:

- сравните с [Kora Java HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-advanced-app) и [Kora Kotlin HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-server-advanced-app)
- перечитайте [HTTP-сервер](http-server.md) про базовый поток контроллер-сервис-репозиторий
- посмотрите [документацию по HTTP-серверу](../documentation/http-server.md)
- посмотрите [документацию по контейнеру](../documentation/container.md)
