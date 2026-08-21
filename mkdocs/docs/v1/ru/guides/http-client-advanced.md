---
search:
  exclude: true
title: Руководство по продвинутому HTTP-клиенту
summary: Extend the basic HTTP client guide with form and multipart bodies, custom request mapping, response-code-aware decoding, method interceptors, and API-key authorization
tags: http-client, advanced, form, multipart, interceptor, mapping, auth
---

# Руководство по продвинутому HTTP-клиенту { #advanced-http-client-guide }

В этом руководстве рассматриваются продвинутые шаблоны декларативного HTTP-клиента в Kora. Вы узнаете, как клиенты вызывают маршруты с формами, multipart и вспомогательным транспортом, как
пользовательские преобразователи тела задают форму нестандартных полезных нагрузок запроса и ответа, и как типизированные варианты ответа представляют разные HTTP-статусы. Вы также увидите, как перехватчики
уровня метода и уровня клиента добавляют сквозное поведение, например авторизацию по ключу API.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-advanced-app).

## Что вы создадите { #youll-build }

Вы расширите клиентское приложение и добавите:

- отдельный `DataApiClient`
- запросы `FormUrlEncoded` и `FormMultipart`
- пользовательский `HttpClientRequestMapper`
- декодирование с учетом кода ответа через `@ResponseCodeMapper`
- `HttpClientInterceptor` уровня метода
- общий для клиента перехватчик авторизации по ключу API
- отдельную агрегирующую конечную точку в `ClientTestController`, которая проверяет продвинутые маршруты данных

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- Docker Desktop или другая локальная Docker-среда для тестов на основе контейнеров
- текстовый редактор или среда разработки

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководства по HTTP-клиенту и продвинутому HTTP-серверу"

    Это руководство предполагает, что вы уже прошли **[Руководство по продвинутому HTTP-серверу](http-server-advanced.md)** и **[Руководство по HTTP-клиенту](http-client.md)**, а продвинутая серверная сторона уже предоставляет маршруты `DataController`.

    Если вы еще не прошли эти руководства, сначала сделайте это, потому что там уже разобран базовый поток HTTP-сервера/клиента, а это руководство сосредоточено только на продвинутом клиентском сопоставлении для маршрутов продвинутого сервера.

## Обзор { #overview }

Продвинутые [HTTP](https://www.rfc-editor.org/rfc/rfc9110)-клиенты появляются тогда, когда удаленный API — это не просто JSON CRUD. Некоторые сервисы предоставляют form-конечные точки,
multipart-загрузки, пользовательские форматы полезной нагрузки или контракты ответов, где разные коды состояния означают разные типизированные исходы. Хороший клиент должен явно моделировать эти
детали и не протаскивать низкоуровневый HTTP-код в остальные части приложения.

Ключевое проектное решение — держать продвинутую транспортную механику рядом со сгенерированным клиентом. Кодирование форм, построение multipart, пользовательское сопоставление, декодирование статусов
и заголовки авторизации — это задачи границы клиента, а не задачи бизнес-логики.

### HTTP-формы { #http-forms }

Декларативные клиенты Kora могут описывать несколько стилей HTTP-взаимодействия:

- параметры формы для запросов `application/x-www-form-urlencoded`
- multipart-части для вызовов в стиле загрузки файлов
- пользовательские преобразователи запросов для полезных нагрузок, которые не подходят под стандартную JSON-модель
- типизированное сопоставление ответов для API, где коды состояния несут доменный смысл

Главный принцип тот же, что в базовом руководстве по клиенту: сигнатура метода должна описывать удаленный контракт достаточно ясно, чтобы вызывающему коду не приходилось вручную строить запросы.

### Перехватчики клиента { #client-interceptors }

Клиентские перехватчики выполняются вокруг исходящих вызовов. Они полезны для сквозного транспортного поведения, например журналирования, идентификаторов корреляции, заголовков авторизации, ключей API
или метрик. Поскольку перехватчики живут на границе клиента, они помогают не дублировать один и тот же код заголовков или журналирования в каждом методе.

В этом руководстве перехватчики используются и для поведения уровня метода, и для переиспользуемой авторизации уровня клиента.

### Точечные изменения { #targeted-changes }

Продвинутые возможности клиента легко расползаются по приложению, если сгенерированный клиент используется напрямую везде. В этом руководстве вокруг клиента сохраняется сервисная обертка, чтобы
form-вызовы, multipart-вызовы, пользовательское декодирование и авторизация оставались рядом с транспортной границей. Остальная часть приложения может работать с более понятными методами и
типизированными результатами.

Практический поток:

1. добавить отдельный клиент для продвинутых маршрутов данных
2. декларативно вызвать form- и multipart-конечные точки
3. добавить пользовательский преобразователь запроса для одной формы полезной нагрузки
4. декодировать статусы ответа в типизированные результаты
5. подключить журналирование и авторизацию по ключу API через перехватчики

## Новый HTTP-клиент { #new-http-client }

Первая продвинутая концепция клиента все еще очень конкретна: вызвать дополнительные маршруты, введенные в `DataController`.

Мы держим эти вызовы в отдельном `DataApiClient`, чтобы транспортно-насыщенные примеры не загромождали более простой `UserApiClient`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/DataApiClient.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import java.nio.charset.StandardCharsets;
    import java.util.List;
    import ru.tinkoff.kora.http.client.common.annotation.HttpClient;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.form.FormMultipart;
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @HttpClient(configPath = "httpClient.dataApi")
    public interface DataApiClient {

        @HttpRoute(method = HttpMethod.POST, path = "/data/form")
        String processForm(FormUrlEncoded body);

        @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
        @Json
        UploadResponse processUpload(FormMultipart body);

        default UploadResponse sampleUpload() {
            return this.processUpload(new FormMultipart(List.of(
                    FormMultipart.data("field1", "some data content"),
                    FormMultipart.file("field2", "example1.txt", "text/plain", "some file content".getBytes(StandardCharsets.UTF_8)))));
        }

        @Json
        record UploadResponse(int fileCount, List<String> fileNames) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/DataApiClient.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import java.nio.charset.StandardCharsets
    import ru.tinkoff.kora.http.client.common.annotation.HttpClient
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.form.FormMultipart
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded
    import ru.tinkoff.kora.json.common.annotation.Json

    @HttpClient(configPath = "httpClient.dataApi")
    interface DataApiClient {

        @HttpRoute(method = HttpMethod.POST, path = "/data/form")
        fun processForm(body: FormUrlEncoded): String

        @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
        @Json
        fun processUpload(body: FormMultipart): UploadResponse

        fun sampleUpload(): UploadResponse {
            return processUpload(
                FormMultipart(
                    listOf(
                        FormMultipart.data("field1", "some data content"),
                        FormMultipart.file("field2", "example1.txt", "text/plain", "some file content".toByteArray(StandardCharsets.UTF_8))
                    )
                )
            )
        }

        @Json
        data class UploadResponse(val fileCount: Int, val fileNames: List<String>)
    }
    ```

Такое разделение помогает:

- `UserApiClient` остается сосредоточен на CRUD
- `DataApiClient` становится местом для продвинутых транспортных примеров
- базовое руководство остается простым для чтения

## Преобразователь параметра { #parameter-mapper }

Подробнее о преобразователях тела запроса клиента смотрите в разделе [тела запроса HTTP-клиента](../documentation/http-client.md#request-body).

Иногда тело запроса не должно использовать обычный поток JSON- или form-сопоставления. Удаленная конечная точка может ожидать очень конкретное текстовое или бинарное представление, а вы все равно
хотите моделировать вход своим типом.

Именно для этого нужен `HttpClientRequestMapper<T>`.

В этом руководстве используется небольшой пример:

- метод принимает `PlainTextGreetingBody`
- преобразователь превращает его в обычное текстовое HTTP-тело
- продвинутый сервер возвращает этот сопоставленный текст обратно

===! ":fontawesome-brands-java: `Java`"

    Добавьте эти части внутрь `DataApiClient.java`:

    ```java
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.common.Mapping;
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequestMapper;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.common.body.HttpBodyOutput;

    record PlainTextGreetingBody(String name) {}

    final class GreetingRequestMapper implements HttpClientRequestMapper<PlainTextGreetingBody> {

        @Override
        public HttpBodyOutput apply(Context ctx, PlainTextGreetingBody value) {
            return HttpBody.plaintext("Hello " + value.name());
        }
    }

    @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
    String processMappedRequest(@Mapping(GreetingRequestMapper.class) PlainTextGreetingBody body);
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте ту же идею в `DataApiClient.kt`:

    ```kotlin
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.common.Mapping
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequestMapper
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.common.body.HttpBodyOutput

    data class PlainTextGreetingBody(val name: String)

    class GreetingRequestMapper : HttpClientRequestMapper<PlainTextGreetingBody> {
        override fun apply(ctx: Context, value: PlainTextGreetingBody): HttpBodyOutput {
            return HttpBody.plaintext("Hello ${value.name}")
        }
    }

    @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
    fun processMappedRequest(@Mapping(GreetingRequestMapper::class) body: PlainTextGreetingBody): String
    ```

Это клиентский аналог преобразователей запросов, которые мы вводили в руководстве по продвинутому серверу: типизированный объект превращается в транспортное представление в одном ясном месте.

## Сопоставление по коду ответа { #response-code-mapping }

Стандартное поведение клиента часто рассматривает ответ как:

- успешное тело
- или исключение

Этого достаточно для многих API. Но иногда контракт намеренно говорит:

- `200` возвращает одну JSON-форму
- ответы не с `200` возвращают другую JSON-форму

Именно здесь полезен `@ResponseCodeMapper`.

В этом руководстве `GET /data/mapping-by-code/{code}` ведет себя так:

- `200` возвращает `{"message":"Hello from response mapper"}`
- другие коды возвращают `{"message":"Request failed with code <status>"}` через общий серверный `ErrorResponse`

Мы моделируем это как один sealed-тип результата.

===! ":fontawesome-brands-java: `Java`"

    Добавьте это внутрь `DataApiClient.java`:

    ```java
    import java.io.IOException;
    import ru.tinkoff.kora.guide.httpclient.client.DataApiClient.MappedResponse.Error;
    import ru.tinkoff.kora.guide.httpclient.client.DataApiClient.MappedResponse.Payload;
    import ru.tinkoff.kora.http.client.common.HttpClientDecoderException;
    import ru.tinkoff.kora.http.client.common.annotation.ResponseCodeMapper;
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse;
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponseMapper;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.json.common.JsonReader;

    sealed interface MappedResponse permits Payload, Error {

        @Json
        record Payload(String message) implements MappedResponse {}

        @Json
        record Error(int code, String message) implements MappedResponse {}

        @Json
        record ErrorPayload(String message) {}
    }

    final class MappedResponseSuccessMapper implements HttpClientResponseMapper<MappedResponse> {

        private final JsonReader<Payload> jsonReader;

        public MappedResponseSuccessMapper(JsonReader<Payload> jsonReader) {
            this.jsonReader = jsonReader;
        }

        @Override
        public MappedResponse apply(HttpClientResponse response) throws IOException, HttpClientDecoderException {
            try (var is = response.body().asInputStream()) {
                return this.jsonReader.read(is.readAllBytes());
            }
        }
    }

    final class MappedResponseErrorMapper implements HttpClientResponseMapper<MappedResponse> {

        private final JsonReader<MappedResponse.ErrorPayload> jsonReader;

        public MappedResponseErrorMapper(JsonReader<MappedResponse.ErrorPayload> jsonReader) {
            this.jsonReader = jsonReader;
        }

        @Override
        public MappedResponse apply(HttpClientResponse response) throws IOException, HttpClientDecoderException {
            try (var is = response.body().asInputStream()) {
                var payload = this.jsonReader.read(is.readAllBytes());
                return new Error(response.code(), payload.message());
            }
        }
    }

    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper.class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper.class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    MappedResponse getMappedByCode(@Path int code);
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте ту же идею в Kotlin:

    ```kotlin
    import java.io.IOException
    import ru.tinkoff.kora.http.client.common.HttpClientDecoderException
    import ru.tinkoff.kora.http.client.common.annotation.ResponseCodeMapper
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponseMapper
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.json.common.JsonReader

    sealed interface MappedResponse {

        @Json
        data class Payload(val message: String) : MappedResponse

        @Json
        data class Error(val code: Int, val message: String) : MappedResponse

        @Json
        data class ErrorPayload(val message: String)
    }

    class MappedResponseSuccessMapper(
        private val jsonReader: JsonReader<MappedResponse.Payload>
    ) : HttpClientResponseMapper<MappedResponse> {

        override fun apply(response: HttpClientResponse): MappedResponse {
            response.body().asInputStream().use { input ->
                return jsonReader.read(input.readAllBytes())
            }
        }
    }

    class MappedResponseErrorMapper(
        private val jsonReader: JsonReader<MappedResponse.ErrorPayload>
    ) : HttpClientResponseMapper<MappedResponse> {

        override fun apply(response: HttpClientResponse): MappedResponse {
            response.body().asInputStream().use { input ->
                val payload = jsonReader.read(input.readAllBytes())
                return MappedResponse.Error(response.code(), payload.message)
            }
        }
    }

    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper::class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper::class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    fun getMappedByCode(@Path code: Int): MappedResponse
    ```

Этот шаблон ценен тем, что транспортная логика, зависящая от кода состояния, остается рядом с методом клиента, а не просачивается в каждый вызывающий код.

Обратите внимание на маленькую, но важную деталь этой версии примера:

- JSON-тело ошибки содержит только `message`
- преобразователь берет `code` из фактической строки HTTP-статуса

Так формат ошибки на стороне сервера остается проще, но клиент все равно может предоставить более богатый типизированный результат.

## Перехватчик клиента { #client-interceptor }

Подробнее о перехватчиках клиента, их области действия и порядке выполнения смотрите в разделе [перехватчиков HTTP-клиента](../documentation/http-client.md#interceptors).

Следующая продвинутая концепция — перехватчик уровня метода.

Перехватчики полезны, когда нужно переиспользуемое поведение вокруг вызова, например:

- журналирование
- метрики
- пользовательская транспортная диагностика

Мы намеренно держим этот пример небольшим и применяем его только к `getMappedByCode()`.

===! ":fontawesome-brands-java: `Java`"

    Добавьте это внутрь `DataApiClient.java`:

    ```java
    import java.util.concurrent.CompletionStage;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.http.client.common.interceptor.HttpClientInterceptor;
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest;
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse;
    import ru.tinkoff.kora.http.common.annotation.InterceptWith;

    final class MethodLoggingInterceptor implements HttpClientInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(MethodLoggingInterceptor.class);

        @Override
        public CompletionStage<HttpClientResponse> processRequest(Context ctx, InterceptChain chain, HttpClientRequest request)
                throws Exception {
            logger.info("Advanced HTTP client interceptor invoked");
            return chain.process(ctx, request);
        }
    }

    @InterceptWith(MethodLoggingInterceptor.class)
    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper.class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper.class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    MappedResponse getMappedByCode(@Path int code);
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте ту же идею в Kotlin:

    ```kotlin
    import java.util.concurrent.CompletionStage
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.http.client.common.interceptor.HttpClientInterceptor
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse
    import ru.tinkoff.kora.http.common.annotation.InterceptWith

    class MethodLoggingInterceptor : HttpClientInterceptor {

        companion object {
            private val logger = LoggerFactory.getLogger(MethodLoggingInterceptor::class.java)
        }

        override fun processRequest(
            ctx: Context,
            chain: HttpClientInterceptor.InterceptChain,
            request: HttpClientRequest
        ): CompletionStage<HttpClientResponse> {
            logger.info("Advanced HTTP client interceptor invoked")
            return chain.process(ctx, request)
        }
    }

    @InterceptWith(MethodLoggingInterceptor::class)
    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper::class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper::class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    fun getMappedByCode(@Path code: Int): MappedResponse
    ```

Это хороший шаблон «локальное перед глобальным»: мы добавляем поведение только там, где оно действительно нужно примеру.

## Авторизация по ключу { #api-key }

Для более широкого описания авторизации на стороне HTTP-клиента смотрите раздел [авторизации](../documentation/http-client.md#authorization).

Руководство по продвинутому серверу защитило `DataController` простой проверкой ключа API в заголовке `Authorization`.

На этом этапе мы уже понимаем сами продвинутые маршруты, поэтому теперь имеет смысл добавить еще одну переиспользуемую клиентскую задачу: автоматическую авторизацию.

Мы не хотим, чтобы каждый вызывающий код вручную помнил об этом заголовке. Это как раз тот повторяющийся транспортный навык, которому место в перехватчике.

Создайте контракт конфигурации:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/ApiKeyAuthConfig.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface ApiKeyAuthConfig {
        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/ApiKeyAuthConfig.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface ApiKeyAuthConfig {
        fun value(): String
    }
    ```

Создайте перехватчик авторизации:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/ApiKeyAuthInterceptor.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import java.util.concurrent.CompletionStage;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.http.client.common.interceptor.HttpClientInterceptor;
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest;
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse;

    @Component
    public final class ApiKeyAuthInterceptor implements HttpClientInterceptor {

        private final ApiKeyAuthConfig config;

        public ApiKeyAuthInterceptor(ApiKeyAuthConfig config) {
            this.config = config;
        }

        @Override
        public CompletionStage<HttpClientResponse> processRequest(Context ctx, InterceptChain chain, HttpClientRequest request)
                throws Exception {
            var authorizedRequest = request.toBuilder()
                    .header("Authorization", this.config.value())
                    .build();
            return chain.process(ctx, authorizedRequest);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/ApiKeyAuthInterceptor.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import java.util.concurrent.CompletionStage
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.http.client.common.interceptor.HttpClientInterceptor
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse

    @Component
    class ApiKeyAuthInterceptor(
        private val config: ApiKeyAuthConfig
    ) : HttpClientInterceptor {

        override fun processRequest(
            ctx: Context,
            chain: HttpClientInterceptor.InterceptChain,
            request: HttpClientRequest
        ): CompletionStage<HttpClientResponse> {
            val authorizedRequest = request.toBuilder()
                .header("Authorization", config.value())
                .build()
            return chain.process(ctx, authorizedRequest)
        }
    }
    ```

Примените его к DataApiClient:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @InterceptWith(ApiKeyAuthInterceptor.class)
    @HttpClient(configPath = "httpClient.dataApi")
    public interface DataApiClient {
        // routes stay the same
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @InterceptWith(ApiKeyAuthInterceptor::class)
    @HttpClient(configPath = "httpClient.dataApi")
    interface DataApiClient {
        // routes stay the same
    }
    ```

Это очень распространенный сценарий использования перехватчика. Команды часто применяют тот же шаблон для:

- заголовков `Authorization`
- файлы cookie
- ключей API
- других метаданных запроса, которые всегда должны добавляться автоматически

Настройте ключ API:

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

Оба приложения могут использовать одно и то же локальное значение по умолчанию, а `HTTP_ADVANCED_API_KEY` сохраняет пример удобным для разных окружений.

## Императивный клиент { #imperative-client }

Декларативные интерфейсы `@HttpClient` — обычный стиль уровня приложения, но Kora также предоставляет базовый компонент `HttpClient`. Это полезно, когда нужно динамически построить запрос, применить
перехватчик вручную или отладить то, что декларативный клиент от вас скрывает.

Сначала добавьте небольшой контракт конфигурации для того же удаленного базового URL, который использует `DataApiClient`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/dataApiConfig.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("httpClient.dataApi")
    public interface dataApiConfig {
        String url();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/dataApiConfig.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("httpClient.dataApi")
    interface dataApiConfig {
        fun url(): String
    }
    ```

Теперь добавьте небольшой ручной клиент. Обратите внимание: он не кладет заголовок авторизации прямо в запрос. Он переиспользует тот же перехватчик авторизации через `this.httpClient.with(...)`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/ManualDataHttpClient.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import java.nio.charset.StandardCharsets;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.client.common.HttpClient;
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest;

    @Component
    public final class ManualDataHttpClient {

        private final HttpClient httpClient;
        private final dataApiConfig dataApiConfig;
        private final ApiKeyAuthInterceptor apiKeyAuthInterceptor;

        public ManualDataHttpClient(
                HttpClient httpClient,
                dataApiConfig dataApiConfig,
                ApiKeyAuthInterceptor apiKeyAuthInterceptor) {
            this.httpClient = httpClient;
            this.dataApiConfig = dataApiConfig;
            this.apiKeyAuthInterceptor = apiKeyAuthInterceptor;
        }

        public String pingManualHandler() {
            var request = HttpClientRequest.of("GET", this.dataApiConfig.url() + "/manual/data/ping")
                    .build();
            var response = this.httpClient.with(this.apiKeyAuthInterceptor)
                    .execute(request)
                    .toCompletableFuture()
                    .join();
            if (response.code() != 200) {
                throw new IllegalStateException("Manual HTTP call failed with status " + response.code());
            }
            try (var body = response.body().asInputStream()) {
                return new String(body.readAllBytes(), StandardCharsets.UTF_8);
            } catch (Exception exception) {
                throw new IllegalStateException("Failed to read manual HTTP response body", exception);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/ManualDataHttpClient.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import java.nio.charset.StandardCharsets
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.client.common.HttpClient
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest

    @Component
    class ManualDataHttpClient(
        private val httpClient: HttpClient,
        private val dataApiConfig: dataApiConfig,
        private val apiKeyAuthInterceptor: ApiKeyAuthInterceptor
    ) {

        fun pingManualHandler(): String {
            val request = HttpClientRequest.of("GET", dataApiConfig.url() + "/manual/data/ping")
                .build()
            val response = httpClient.with(apiKeyAuthInterceptor)
                .execute(request)
                .toCompletableFuture()
                .join()
            if (response.code() != 200) {
                throw IllegalStateException("Manual HTTP call failed with status ${response.code()}")
            }
            response.body().asInputStream().use { body ->
                return String(body.readAllBytes(), StandardCharsets.UTF_8)
            }
        }
    }
    ```

Этот пример намеренно небольшой, но он показывает три важные детали:

- `HttpClientRequest.of(...)` явно строит исходящий запрос
- `HttpClient.with(...)` возвращает клиент, украшенный перехватчиком
- `execute(...)` — это низкоуровневая операция за более высокоуровневыми декларативными клиентами

После компиляции сгенерированный граф приложения показывает, что Kora связывает базовый клиент, конфигурацию и перехватчик с ручным клиентом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    component57 = graphDraw.addNode0(_type_of_component57, new Class<?>[]{}, g -> new ManualDataHttpClient(
          g.get(ApplicationGraph.holder0.component29),
          g.get(ApplicationGraph.holder0.component36),
          g.get(ApplicationGraph.holder0.component42)
        ), List.of(), component29, component36, component42);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    component62 = graphDraw.addNode0(map["component62"],
      { ManualDataHttpClient(
        it.get(holder0.component34),
        it.get(holder0.component41),
        it.get(holder0.component47)
      ) },
      component34, component41, component47
    )
    ```

Этот сгенерированный граф — полезный источник истины, когда нужно подтвердить, какая реализация `HttpClient` и какие перехватчики действительно внедряются.

## Контроллер проверки { #check-controller }

Теперь мы связываем продвинутые возможности клиента в один агрегирующий сценарий, посвященный только маршрутам `DataController`.

В базовом руководстве уже есть ориентированная на пользователей агрегирующая конечная точка. Мы сохраняем это разделение:

- `testAllUserEndpoints()` относится к базовому руководству по клиенту
- `testAllDataEndpoints()` относится к этому продвинутому руководству

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/controller/ClientTestController.java"
    package ru.tinkoff.kora.guide.httpclient.controller;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpclient.client.DataApiClient;
    import ru.tinkoff.kora.guide.httpclient.client.ManualDataHttpClient;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final DataApiClient dataApiClient;
        private final ManualDataHttpClient manualDataHttpClient;

        public ClientTestController(DataApiClient dataApiClient, ManualDataHttpClient manualDataHttpClient) {
            this.dataApiClient = dataApiClient;
            this.manualDataHttpClient = manualDataHttpClient;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-data-endpoints")
        @Json
        public TestResults testAllDataEndpoints() {
            try {
                var formResult = this.dataApiClient.processForm(form("name", "John"));
                boolean formProcessed = "Hello World, John".equals(formResult);

                var uploadResult = this.dataApiClient.sampleUpload();
                boolean uploadProcessed = uploadResult.fileCount() == 2;

                var mappedRequestResult = this.dataApiClient.processMappedRequest(new DataApiClient.PlainTextGreetingBody("Client Mapper"));
                boolean customRequestMapped = "Received mapped body: Hello Client Mapper".equals(mappedRequestResult);

                var mappedSuccess = this.dataApiClient.getMappedByCode(200);
                var mappedFailure = this.dataApiClient.getMappedByCode(404);
                boolean responseMapped = mappedSuccess instanceof DataApiClient.MappedResponse.Payload payload
                        && "Hello from response mapper".equals(payload.message())
                        && mappedFailure instanceof DataApiClient.MappedResponse.Error error
                        && error.code() == 404
                        && "Request failed with code 404".equals(error.message());

                var manualPingResult = this.manualDataHttpClient.pingManualHandler();
                boolean manualHttpClientCallProcessed = "manual-data-pong".equals(manualPingResult);

                boolean allTestsPassed = formProcessed
                        && uploadProcessed
                        && customRequestMapped
                        && responseMapped
                        && manualHttpClientCallProcessed;
                return new TestResults(
                        formProcessed,
                        uploadProcessed,
                        customRequestMapped,
                        responseMapped,
                        manualHttpClientCallProcessed,
                        allTestsPassed,
                        null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, false, false, exception.getMessage());
            }
        }

        private static FormUrlEncoded form(String... keyValues) {
            FormUrlEncoded.FormPart[] parts = new FormUrlEncoded.FormPart[keyValues.length / 2];
            for (int i = 0; i < keyValues.length; i += 2) {
                parts[i / 2] = new FormUrlEncoded.FormPart(keyValues[i], keyValues[i + 1]);
            }
            return new FormUrlEncoded(parts);
        }

        @Json
        public record TestResults(
                boolean formProcessed,
                boolean uploadProcessed,
                boolean customRequestMapped,
                boolean responseMapped,
                boolean manualHttpClientCallProcessed,
                boolean allTestsPassed,
                String error) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/controller/ClientTestController.kt"
    package ru.tinkoff.kora.guide.httpclient.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpclient.client.DataApiClient
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val dataApiClient: DataApiClient
    ) {
        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-data-endpoints")
        @Json
        fun testAllDataEndpoints(): TestResults {
            return try {
                val formResult = dataApiClient.processForm(form("name", "John"))
                val formProcessed = formResult == "Hello World, John"

                val uploadResult = dataApiClient.sampleUpload()
                val uploadProcessed = uploadResult.fileCount == 2

                val mappedRequestResult = dataApiClient.processMappedRequest(DataApiClient.PlainTextGreetingBody("Client Mapper"))
                val customRequestMapped = mappedRequestResult == "Received mapped body: Hello Client Mapper"

                val mappedSuccess = dataApiClient.getMappedByCode(200)
                val mappedFailure = dataApiClient.getMappedByCode(404)
                val responseMapped =
                    mappedSuccess is DataApiClient.MappedResponse.Payload &&
                        mappedSuccess.message == "Hello from response mapper" &&
                        mappedFailure is DataApiClient.MappedResponse.Error &&
                        mappedFailure.code == 404 &&
                        mappedFailure.message == "Request failed with code 404"

                val allTestsPassed = formProcessed && uploadProcessed && customRequestMapped && responseMapped
                TestResults(
                    formProcessed,
                    uploadProcessed,
                    customRequestMapped,
                    responseMapped,
                    allTestsPassed,
                    null
                )
            } catch (e: Exception) {
                TestResults(false, false, false, false, false, e.message)
            }
        }

        private fun form(vararg keyValues: String): FormUrlEncoded {
            val parts = Array(keyValues.size / 2) { index ->
                FormUrlEncoded.FormPart(keyValues[index * 2], keyValues[index * 2 + 1])
            }
            return FormUrlEncoded(parts)
        }

        @Json
        data class TestResults(
            val formProcessed: Boolean,
            val uploadProcessed: Boolean,
            val customRequestMapped: Boolean,
            val responseMapped: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

## Проверка приложения { #check-app }

Запустите продвинутый сервер и продвинутый клиент в разных терминалах.

### Терминал 1: сервер { #terminal-1-server }

```bash
./gradlew clean classes
./gradlew run
```

Приложение продвинутого сервера должно слушать `http://localhost:8080`.

### Терминал 2: клиент { #terminal-2-client }

```bash
./gradlew clean classes
./gradlew run
```

Приложение продвинутого клиента должно слушать `http://localhost:8081`.

### Сценарий клиента { #client-scenario }

```bash
curl -X POST http://localhost:8081/client/test-all-data-endpoints
```

Ожидаемый результат: JSON-объект, где `allTestsPassed` равно `true`.

## Лучшие практики { #best-practices }

- Оставляйте базовое руководство по HTTP-клиенту сосредоточенным на самом простом JSON-first пути, а транспортно-насыщенные темы переносите в продвинутое продолжение.
- Используйте отдельные интерфейсы клиентов для разных областей удаленного API, когда это улучшает читаемость.
- Обращайтесь к `HttpClientRequestMapper` только тогда, когда встроенных стилей сопоставления недостаточно.
- Используйте `@ResponseCodeMapper`, когда декодирование с учетом кода состояния является частью контракта.
- Используйте перехватчики для повторяющегося транспортного поведения вроде журналирования или авторизации, а не повторяйте заголовки и шаблонный код вручную.

## Итоги { #summary }

Вы расширили базовое приложение HTTP-клиента:

- отдельным `DataApiClient`
- поддержкой form- и multipart-запросов
- пользовательским преобразователем запроса
- декодированием с учетом кода ответа
- перехватчиком уровня метода
- переиспользуемой авторизацией по ключу API

Результат отражает дух `http-server-advanced.md`: по одной продвинутой транспортной концепции за раз, и каждая вводится только после того, как более простой путь уже понятен.

## Ключевые понятия { #key-concepts }

- `FormUrlEncoded` и `FormMultipart` являются полноценными клиентскими типами тела в Kora
- `HttpClientRequestMapper<T>` позволяет контролировать, как тип превращается в тело HTTP-запроса
- `@ResponseCodeMapper` позволяет разным кодам состояния декодироваться в разные варианты одного типа результата
- `HttpClientInterceptor` хорошо подходит и для локального журналирования, и для общего поведения авторизации

## Устранение неполадок { #troubleshooting }

**Защищенные вызовы возвращают 403:**

- Проверьте, что сервер и клиент используют одно и то же значение ключа API.
- Проверьте переменную окружения `HTTP_ADVANCED_API_KEY` в обоих приложениях.
- Помните, что переменная окружения переопределяет локальное значение по умолчанию из `application.conf`.

**Form- или multipart-запросы не работают:**

- Убедитесь, что запущено приложение продвинутого сервера, а не только базовое серверное приложение.
- Проверьте, что `DataController` открыт на целевом сервере.

**Пользовательский преобразователь запроса не запускается:**

- Убедитесь, что параметр использует `@Mapping(...)`.
- Убедитесь, что преобразователь реализует `HttpClientRequestMapper<T>`.

**Сопоставление по коду ответа работает не так, как ожидалось:**

- Внимательно проверьте записи `@ResponseCodeMapper`.
- Помните, что `ResponseCodeMapper.DEFAULT` является запасным вариантом для всех неуказанных кодов.
- Убедитесь, что серверный маршрут возвращает JSON-форму, которую ваш преобразователь ожидает для каждой ветки.

**Журналирование перехватчика не появляется:**

- Проверьте `@InterceptWith(...)` на конкретном методе клиента.
- Убедитесь, что класс перехватчика реализует `HttpClientInterceptor`.

## Что дальше? { #whats-next }

- [HTTP-сервер OpenAPI](openapi-http-server.md), если вы еще не прошли путь сервера от контракта.
- [HTTP-клиент OpenAPI](openapi-http-client.md) после HTTP-сервера OpenAPI, чтобы увидеть, как генерация по контракту моделирует похожее транспортное поведение.
- [Шаблоны отказоустойчивости](resilient.md), чтобы защищать продвинутые исходящие вызовы повтором, временем ожидания, автоматическим выключателем и резервным ответом.
- [Наблюдаемость](observability.md), чтобы трассировать перехватчики, ручные вызовы `HttpClient` и сопоставленные ответы.

## Помощь { #help }

Если вы застряли:

- сравните с [Kora Java HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-advanced-app) и [Kora Kotlin HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-advanced-app)
- вернитесь к [HTTP-клиенту](http-client.md), чтобы вспомнить базовую форму декларативного клиента
- вернитесь к [Продвинутому HTTP-серверу](http-server-advanced.md), чтобы посмотреть серверные конечные точки, которые вызывает этот клиент
- проверьте [документацию HTTP-клиента](../documentation/http-client.md)
