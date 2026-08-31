---
search:
  exclude: true
title: Руководство по продвинутому HTTP-клиенту
summary: Extend the basic HTTP client guide with form and multipart bodies, custom request mapping, response-code-aware decoding, method and client interceptors, API-key authorization and imperative calls
description: "Advanced declarative HTTP client patterns for Kora 2.0: FormUrlEncoded and FormMultipart request bodies built from FormPart values, a custom HttpClientRequestMapper attached with @Mapping, @ResponseCodeMapper with ResponseCodeMapper.DEFAULT and per-status HttpClientResponseMapper implementations, HttpClientInterceptor applied through @InterceptWith for method logging and API-key authorization backed by @ConfigSource and @ConfigMapper, per-operation settings from HttpClientOperationConfig, and the imperative HttpClient with HttpClientRequest.of and a closeable HttpClientResponse."
agent:
  use_when: "Use this file for questions about non-trivial Kora 2.0 HTTP client calls: sending FormUrlEncoded or FormMultipart bodies with FormPart, writing an HttpClientRequestMapper and binding it with @Mapping, decoding different status codes into typed variants with @ResponseCodeMapper and ResponseCodeMapper.DEFAULT, HttpClientDecoderException raised inside a mapper, HttpClientInterceptor with @InterceptWith on a method or the whole interface, adding an API-key header from an @ConfigSource or @ConfigMapper value, per-operation keys such as httpClient.dataApi.getMappedByCode.requestTimeout and HttpClientOperationConfig, and building requests by hand with HttpClientRequest.of, HttpClient.with and HttpClient.execute."
tags: http-client, advanced, form, multipart, interceptor, mapping, auth, imperative
---

# Руководство по продвинутому HTTP-клиенту { #advanced-http-client-guide }

В этом руководстве разбираются продвинутые приёмы работы с декларативными HTTP-клиентами Kora. Вы узнаете, как клиенты вызывают маршруты с формами, multipart и вспомогательным транспортом, как
собственные преобразователи тела задают форму нестандартных полезных нагрузок запроса и ответа и как типизированные варианты ответа представляют разные HTTP-статусы. Вы также увидите, как перехватчики
уровня метода и уровня клиента добавляют сквозное поведение вроде авторизации по API-ключу и как спуститься к императивному `HttpClient`, когда запрос нужно собрать вручную.

Всё на этой странице остаётся синхронным. Перехватчик возвращает `HttpClientResponse`, `HttpClient.execute(...)` возвращает `HttpClientResponse`, а преобразователи работают с уже полученным ответом.
В контракте клиента нет ни колбэков, ни future, ни корутин.

===! ":fontawesome-brands-java: `Java`"

    Если хотите сверяться с готовым результатом по ходу дела, используйте рабочий пример: [Kora Java HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    Если хотите сверяться с готовым результатом по ходу дела, используйте рабочий пример: [Kora Kotlin HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-advanced-app).

## Что вы создадите { #youll-build }

Вы расширите клиентское приложение:

- отдельным `DataApiClient`
- запросами `FormUrlEncoded` и `FormMultipart`
- собственным `HttpClientRequestMapper`
- разбором ответа с учётом статус-кода через `@ResponseCodeMapper`
- перехватчиком `HttpClientInterceptor` уровня метода
- перехватчиком авторизации по API-ключу для всего клиента
- императивным вызовом через базовый `HttpClient` с переиспользованием сгенерированной конфигурации клиента
- отдельным сводным эндпоинтом в `ClientTestController`, который задействует продвинутые маршруты данных

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+ (эталонные приложения используют Gradle Wrapper `9.5.1`)
- Docker Desktop или другое локальное окружение Docker для тестов с контейнерами
- Текстовый редактор или IDE

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководства по HTTP-клиенту и продвинутому HTTP-серверу"

    Это руководство предполагает, что вы прошли **[Руководство по продвинутому HTTP-серверу](http-server-advanced.md)** и **[Руководство по HTTP-клиенту](http-client.md)**, и что продвинутая серверная часть уже предоставляет маршруты `DataController`.

    Если эти руководства ещё не пройдены, начните с них: там уже разобран базовый поток HTTP-сервера и клиента, а здесь мы сосредоточены только на продвинутых преобразованиях клиента для продвинутых серверных маршрутов.

## Обзор { #overview }

Продвинутые [HTTP](https://www.rfc-editor.org/rfc/rfc9110)-клиенты появляются, когда удалённый API — это не просто JSON-CRUD. Одни сервисы предоставляют эндпоинты форм, другие — multipart-загрузки,
собственные форматы полезной нагрузки или контракты, где разные статус-коды означают разные типизированные результаты. Хороший клиент должен описывать эти детали явно, не протаскивая низкоуровневый
HTTP-код в остальную часть приложения.

Ключевое проектное решение — держать продвинутую транспортную механику рядом со сгенерированным клиентом. Кодирование форм, сборка multipart, собственные преобразования, разбор статусов и заголовки
авторизации — это задачи границы клиента, а не бизнес-логики.

### HTTP-формы { #http-forms }

Декларативные клиенты Kora умеют описывать несколько стилей взаимодействия по HTTP:

- параметры формы для запросов `application/x-www-form-urlencoded`
- multipart-части для вызовов с загрузкой файлов
- собственные преобразователи запроса для полезных нагрузок, которые не укладываются в стандартную JSON-модель
- типизированное преобразование ответа для API, где статус-коды несут доменный смысл

Основной принцип тот же, что и в базовом руководстве по клиенту: сигнатура метода должна описывать удалённый контракт достаточно чётко, чтобы вызывающему коду не пришлось собирать запрос вручную.

### Перехватчики клиента { #client-interceptors }

Перехватчики клиента выполняются вокруг исходящих вызовов. Они полезны для сквозного транспортного поведения: логирования, идентификаторов корреляции, заголовков аутентификации, API-ключей или метрик.
Поскольку перехватчики живут на границе клиента, они избавляют от дублирования одного и того же кода с заголовками или логированием в каждом методе.

Перехватчик реализует один синхронный метод — `HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request)`. Он может переписать запрос, вызвать `chain.process(request)`,
изучить ответ и даже вовсе пропустить вызов. Перехватчики, объявленные на интерфейсе, выполняются раньше перехватчиков, объявленных на методе.

В этом руководстве перехватчики используются и для поведения уровня метода, и для переиспользуемой авторизации уровня клиента.

### Точечные изменения { #targeted-changes }

Продвинутые возможности клиента легко расползаются по приложению, если сгенерированный клиент используется напрямую повсюду. В этом руководстве транспортно-нагруженные части остаются внутри интерфейса
клиента, поэтому вызовы форм, multipart, собственные преобразования и авторизация остаются у транспортной границы. Остальная часть приложения работает с более понятными методами и типизированными
результатами.

Практический порядок действий такой:

1. добавить отдельный клиент для продвинутых маршрутов данных
2. декларативно вызывать эндпоинты форм и multipart
3. добавить собственный преобразователь запроса для одной формы полезной нагрузки
4. разобрать статусы ответа в типизированные результаты
5. подключить логирование и авторизацию по API-ключу через перехватчики
6. обратиться к императивному `HttpClient` там, где декларативная модель не подходит

## Новый HTTP-клиент { #new-http-client }

Первое продвинутое понятие всё ещё вполне конкретно: вызвать дополнительные маршруты, добавленные `DataController`.

Мы держим эти вызовы в отдельном `DataApiClient`, чтобы транспортно-нагруженные примеры не загромождали более простой `UserApiClient`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/client/DataApiClient.java"
    package io.koraframework.guide.httpclient.client;

    import java.nio.charset.StandardCharsets;
    import java.util.List;
    import io.koraframework.http.client.common.annotation.HttpClient;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.form.FormMultipart;
    import io.koraframework.http.common.form.FormUrlEncoded;
    import io.koraframework.json.common.annotation.Json;

    @HttpClient("httpClient.dataApi")
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

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/client/DataApiClient.kt"
    package io.koraframework.guide.httpclient.client

    import io.koraframework.http.client.common.annotation.HttpClient
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.form.FormMultipart
    import io.koraframework.http.common.form.FormUrlEncoded
    import io.koraframework.json.common.annotation.Json
    import java.nio.charset.StandardCharsets

    @HttpClient("httpClient.dataApi")
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
                        FormMultipart.file(
                            "field2",
                            "example1.txt",
                            "text/plain",
                            "some file content".toByteArray(StandardCharsets.UTF_8)
                        )
                    )
                )
            )
        }

        @Json
        data class UploadResponse(val fileCount: Int, val fileNames: List<String>)
    }
    ```

Такое разделение помогает:

- `UserApiClient` остаётся сосредоточенным на CRUD
- `DataApiClient` становится домом для продвинутых транспортных примеров
- базовое руководство остаётся простым для чтения

Основную работу здесь делают два типа тела, и оба живут в `io.koraframework.http.common.form`:

- `FormUrlEncoded` хранит записи `FormPart(name, values)` и кодируется как `application/x-www-form-urlencoded`
- `FormMultipart` хранит список частей, созданных через `FormMultipart.data(...)` для обычных полей и `FormMultipart.file(...)` для файловых частей, и кодируется как `multipart/form-data`

Ни одному из них не нужен `@Mapping`: Kora поставляет преобразователи запроса для обоих. `sampleUpload()` — обычный default-метод интерфейса, поэтому он не маршрут, а удобная обёртка, которая собирает
multipart-тело и делегирует в `processUpload`. Default-методы также пропускаются, когда Kora генерирует конфигурацию по методам, поэтому лишних ключей конфигурации от них не появляется.

Клиенту нужен собственный раздел конфигурации, названный в значении `@HttpClient`:

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpClient {
      dataApi {
        url = "http://localhost:8080" //(1)!
        url = ${?DATA_API_URL} //(2)!
        requestTimeout = 10s //(3)!
        telemetry.logging.enabled = true //(4)!
        getMappedByCode.requestTimeout = 2s //(5)!
      }
    }
    ```

    1. Базовый URL продвинутого серверного приложения (обязательно, без значения по умолчанию).
    2. Необязательное переопределение базового URL из переменной окружения `DATA_API_URL`.
    3. Максимальное время одного запроса клиента (опционально, без значения по умолчанию).
    4. Включает логирование запросов этого клиента (по умолчанию: `false`).
    5. Переопределение для конкретной операции: у каждого метода клиента есть собственный блок конфигурации, названный по имени метода.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpClient:
      dataApi:
        url: ${DATA_API_URL:http://localhost:8080} #(1)!
        requestTimeout: 10s #(2)!
        telemetry:
          logging:
            enabled: true #(3)!
        getMappedByCode:
          requestTimeout: 2s #(4)!
    ```

    1. Базовый URL продвинутого серверного приложения (обязательно, без значения по умолчанию). Используется показанное значение, а `DATA_API_URL` может его переопределить.
    2. Максимальное время одного запроса клиента (опционально, без значения по умолчанию).
    3. Включает логирование запросов этого клиента (по умолчанию: `false`).
    4. Переопределение для конкретной операции: у каждого метода клиента есть собственный блок конфигурации, названный по имени метода.

## Преобразователь параметра { #parameter-mapper }

Подробнее о преобразователях тела запроса читайте в разделе [Тело запроса HTTP-клиента](../documentation/http-client.md#request-body).

Иногда тело запроса не должно проходить обычный путь JSON- или form-преобразования. Удалённый эндпоинт может ожидать очень конкретное текстовое или бинарное представление, а вы всё равно хотите
моделировать вход собственным типом.

Для этого и нужен `HttpClientRequestMapper<T>`. У него один метод — `HttpBodyOutput apply(T value)`, а `HttpBody` предоставляет фабрики для привычных представлений: `HttpBody.plaintext(...)`,
`HttpBody.json(...)`, `HttpBody.octetStream(...)` и `HttpBody.of(contentType, bytes)`.

В этом руководстве используется небольшой пример:

- метод принимает `PlainTextGreetingBody`
- преобразователь превращает его в текстовое тело HTTP
- продвинутый сервер возвращает этот преобразованный текст обратно

===! ":fontawesome-brands-java: `Java`"

    Добавьте эти части внутрь `DataApiClient.java`:

    ```java
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Mapping;
    import io.koraframework.http.client.common.request.HttpClientRequestMapper;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.common.body.HttpBodyOutput;

    @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
    String processMappedRequest(@Mapping(GreetingRequestMapper.class) PlainTextGreetingBody body);

    record PlainTextGreetingBody(String name) {}

    @Component
    final class GreetingRequestMapper implements HttpClientRequestMapper<PlainTextGreetingBody> {

        @Override
        public HttpBodyOutput apply(PlainTextGreetingBody value) {
            return HttpBody.plaintext("Hello " + value.name());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте то же самое в `DataApiClient.kt`:

    ```kotlin
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Mapping
    import io.koraframework.http.client.common.request.HttpClientRequestMapper
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.common.body.HttpBodyOutput

    @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
    fun processMappedRequest(@Mapping(GreetingRequestMapper::class) body: PlainTextGreetingBody): String

    data class PlainTextGreetingBody(val name: String)

    @Component
    class GreetingRequestMapper : HttpClientRequestMapper<PlainTextGreetingBody> {

        override fun apply(value: PlainTextGreetingBody): HttpBodyOutput {
            return HttpBody.plaintext("Hello ${value.name}")
        }
    }
    ```

Обратите внимание на `@Component` у преобразователя. Преобразователь запроса, указанный в `@Mapping`, всегда берётся из графа зависимостей — сгенерированный клиент получает его аргументом конструктора,
— поэтому он должен быть компонентом графа даже без собственных зависимостей. То же правило действует для любого перехватчика, указанного в `@InterceptWith`.

Это клиентский аналог преобразователей запроса, представленных в руководстве по продвинутому серверу: типизированный объект превращается в транспортное представление в одном понятном месте.

## Сопоставление по коду ответа { #response-code-mapping }

По умолчанию клиент трактует ответ как одно из двух:

- успешное тело — для статусов `2xx`
- либо `HttpClientResponseException` — для всего остального

Для многих API этого достаточно. Но иногда контракт намеренно говорит:

- `200` возвращает одну форму JSON
- ответы, отличные от `200`, возвращают другую форму JSON

Вот здесь и пригождается `@ResponseCodeMapper`. Аннотация повторяемая, принимает конкретный статус-код и `HttpClientResponseMapper` для него, а `ResponseCodeMapper.DEFAULT` покрывает все статусы, не
перечисленные явно. Если указан хотя бы один `@ResponseCodeMapper`, сгенерированный клиент переключается по статус-коду вместо того, чтобы бросать исключение на не-`2xx`.

В этом руководстве `GET /data/mapping-by-code/{code}` ведёт себя так:

- `200` возвращает `{"message":"Hello from response mapper"}`
- другие коды возвращают `{"message":"Request failed with code <status>"}` через общую серверную полезную нагрузку ошибки

Мы моделируем это одним запечатанным типом результата.

===! ":fontawesome-brands-java: `Java`"

    Добавьте это внутрь `DataApiClient.java`:

    ```java
    import java.io.IOException;
    import io.koraframework.http.client.common.annotation.ResponseCodeMapper;
    import io.koraframework.http.client.common.exception.HttpClientDecoderException;
    import io.koraframework.http.client.common.response.HttpClientResponse;
    import io.koraframework.http.client.common.response.HttpClientResponseMapper;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.json.common.JsonReader;

    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper.class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper.class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    MappedResponse getMappedByCode(@Path int code);

    sealed interface MappedResponse permits MappedResponse.Payload, MappedResponse.Error {

        @Json
        record Payload(String message) implements MappedResponse {}

        @Json
        record Error(int code, String message) implements MappedResponse {}

        @Json
        record ErrorPayload(String message) {}
    }

    @Component
    final class MappedResponseSuccessMapper implements HttpClientResponseMapper<MappedResponse> {

        private final JsonReader<MappedResponse.Payload> jsonReader;

        public MappedResponseSuccessMapper(JsonReader<MappedResponse.Payload> jsonReader) {
            this.jsonReader = jsonReader;
        }

        @Override
        public MappedResponse apply(HttpClientResponse response) throws IOException, HttpClientDecoderException {
            try (var is = response.body().asInputStream()) {
                return this.jsonReader.read(is.readAllBytes());
            }
        }
    }

    @Component
    final class MappedResponseErrorMapper implements HttpClientResponseMapper<MappedResponse> {

        private final JsonReader<MappedResponse.ErrorPayload> jsonReader;

        public MappedResponseErrorMapper(JsonReader<MappedResponse.ErrorPayload> jsonReader) {
            this.jsonReader = jsonReader;
        }

        @Override
        public MappedResponse apply(HttpClientResponse response) throws IOException, HttpClientDecoderException {
            try (var is = response.body().asInputStream()) {
                var payload = this.jsonReader.read(is.readAllBytes());
                return new MappedResponse.Error(response.code(), payload.message());
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте то же самое на Kotlin:

    ```kotlin
    import io.koraframework.http.client.common.annotation.ResponseCodeMapper
    import io.koraframework.http.client.common.exception.HttpClientDecoderException
    import io.koraframework.http.client.common.response.HttpClientResponse
    import io.koraframework.http.client.common.response.HttpClientResponseMapper
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.json.common.JsonReader
    import java.io.IOException

    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper::class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper::class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    fun getMappedByCode(@Path code: Int): MappedResponse

    sealed interface MappedResponse {

        @Json
        data class Payload(val message: String) : MappedResponse

        @Json
        data class Error(val code: Int, val message: String) : MappedResponse

        @Json
        data class ErrorPayload(val message: String)
    }

    @Component
    class MappedResponseSuccessMapper(
        private val jsonReader: JsonReader<MappedResponse.Payload>
    ) : HttpClientResponseMapper<MappedResponse> {

        @Throws(IOException::class, HttpClientDecoderException::class)
        override fun apply(response: HttpClientResponse): MappedResponse {
            response.body().asInputStream().use { input ->
                return requireNotNull(jsonReader.read(input.readAllBytes())) { "Empty success payload" }
            }
        }
    }

    @Component
    class MappedResponseErrorMapper(
        private val jsonReader: JsonReader<MappedResponse.ErrorPayload>
    ) : HttpClientResponseMapper<MappedResponse> {

        @Throws(IOException::class, HttpClientDecoderException::class)
        override fun apply(response: HttpClientResponse): MappedResponse {
            response.body().asInputStream().use { input ->
                val payload = requireNotNull(jsonReader.read(input.readAllBytes())) { "Empty error payload" }
                return MappedResponse.Error(response.code(), payload.message)
            }
        }
    }
    ```

Этот приём ценен тем, что логика, зависящая от статус-кода, остаётся рядом с методом клиента и не протекает в каждый вызывающий код.

Обратите внимание на несколько деталей этого варианта примера:

- оба преобразователя принимают `JsonReader` в конструкторе, поэтому оба должны быть `@Component`
- JSON-тело ошибки содержит только `message`
- `code` преобразователь берёт из реальной строки статуса HTTP
- всё, что бросает преобразователь, сгенерированный клиент оборачивает в `HttpClientDecoderException`

Это позволяет держать серверный формат ошибки проще, но всё равно отдавать клиенту более богатый типизированный результат.

!!! tip "Два исхода без собственных преобразователей"

    Когда нужно только «полезная нагрузка успеха или полезная нагрузка ошибки» и обе в JSON, `Either<T, E>` — более лёгкий вариант: метод, возвращающий `Either<Payload, ErrorPayload>`, преобразует
    любой статус-код без исключений, а с `@Json` Kora строит оба преобразователя сама. Смотрите [Either](../documentation/http-client.md#either).

## Перехватчик клиента { #client-interceptor }

Подробнее о перехватчиках клиента, их области действия и порядке выполнения читайте в разделе [Перехватчики HTTP-клиента](../documentation/http-client.md#interceptors).

Следующее продвинутое понятие — перехватчик уровня метода.

Перехватчики полезны, когда нужно переиспользуемое поведение вокруг вызова:

- логирование
- метрики
- собственная транспортная диагностика

Этот пример намеренно небольшой и применяется только к `getMappedByCode()`.

===! ":fontawesome-brands-java: `Java`"

    Добавьте это внутрь `DataApiClient.java`:

    ```java
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import io.koraframework.http.client.common.interceptor.HttpClientInterceptor;
    import io.koraframework.http.client.common.request.HttpClientRequest;
    import io.koraframework.http.common.annotation.InterceptWith;

    @InterceptWith(MethodLoggingInterceptor.class)
    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper.class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper.class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    MappedResponse getMappedByCode(@Path int code);

    @Component
    final class MethodLoggingInterceptor implements HttpClientInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(MethodLoggingInterceptor.class);

        @Override
        public HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request) throws Exception {
            logger.info("Advanced HTTP client interceptor invoked");
            return chain.process(request);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте то же самое на Kotlin:

    ```kotlin
    import org.slf4j.LoggerFactory
    import io.koraframework.http.client.common.interceptor.HttpClientInterceptor
    import io.koraframework.http.client.common.request.HttpClientRequest
    import io.koraframework.http.common.annotation.InterceptWith

    @InterceptWith(MethodLoggingInterceptor::class)
    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper::class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper::class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    fun getMappedByCode(@Path code: Int): MappedResponse

    @Component
    class MethodLoggingInterceptor : HttpClientInterceptor {

        private val logger = LoggerFactory.getLogger(MethodLoggingInterceptor::class.java)

        override fun processRequest(chain: HttpClientInterceptor.InterceptChain, request: HttpClientRequest): HttpClientResponse {
            logger.info("Advanced HTTP client interceptor invoked")
            return chain.process(request)
        }
    }
    ```

Это хороший приём «сначала локально, потом глобально»: поведение добавляется только там, где оно действительно нужно примеру.

Сигнатуру стоит разобрать внимательно. `processRequest` принимает сначала цепочку, затем запрос, и сразу возвращает ответ:

- чтобы изменить исходящий запрос, пересоберите его через `request.toBuilder()` и передайте новый экземпляр в `chain.process(...)`
- чтобы изучить или заменить ответ, работайте со значением, которое вернул `chain.process(...)`
- чтобы прервать вызов, верните ответ, вовсе не обращаясь к цепочке

## Авторизация по ключу { #api-key }

Более широкая модель авторизации HTTP-клиента описана в разделе [Авторизация](../documentation/http-client.md#authorization).

В руководстве по продвинутому серверу `DataController` был защищён простой проверкой API-ключа в заголовке `Authorization`.

Продвинутые маршруты мы уже разобрали, так что теперь самое время добавить ещё одну переиспользуемую заботу клиента — автоматическую авторизацию.

Мы не хотим, чтобы каждый вызывающий код помнил об этом заголовке. Это ровно то повторяющееся транспортное правило, которому место в перехватчике.

Создайте контракт конфигурации:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/client/ApiKeyAuthConfig.java"
    package io.koraframework.guide.httpclient.client;

    import io.koraframework.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface ApiKeyAuthConfig {

        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/client/ApiKeyAuthConfig.kt"
    package io.koraframework.guide.httpclient.client

    import io.koraframework.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface ApiKeyAuthConfig {

        fun value(): String
    }
    ```

Создайте перехватчик авторизации:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/client/ApiKeyAuthInterceptor.java"
    package io.koraframework.guide.httpclient.client;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.client.common.interceptor.HttpClientInterceptor;
    import io.koraframework.http.client.common.request.HttpClientRequest;
    import io.koraframework.http.client.common.response.HttpClientResponse;

    @Component
    public final class ApiKeyAuthInterceptor implements HttpClientInterceptor {

        private final ApiKeyAuthConfig config;

        public ApiKeyAuthInterceptor(ApiKeyAuthConfig config) {
            this.config = config;
        }

        @Override
        public HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request) throws Exception {
            var authorizedRequest = request.toBuilder()
                    .header("Authorization", this.config.value())
                    .build();
            return chain.process(authorizedRequest);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/client/ApiKeyAuthInterceptor.kt"
    package io.koraframework.guide.httpclient.client

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.client.common.interceptor.HttpClientInterceptor
    import io.koraframework.http.client.common.request.HttpClientRequest
    import io.koraframework.http.client.common.response.HttpClientResponse

    @Component
    class ApiKeyAuthInterceptor(
        private val config: ApiKeyAuthConfig
    ) : HttpClientInterceptor {

        override fun processRequest(chain: HttpClientInterceptor.InterceptChain, request: HttpClientRequest): HttpClientResponse {
            val authorizedRequest = request.toBuilder()
                .header("Authorization", config.value())
                .build()
            return chain.process(authorizedRequest)
        }
    }
    ```

Примените его ко всему клиенту, чтобы авторизован был каждый маршрут:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @InterceptWith(ApiKeyAuthInterceptor.class)
    @HttpClient("httpClient.dataApi")
    public interface DataApiClient {
        // routes stay the same
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @InterceptWith(ApiKeyAuthInterceptor::class)
    @HttpClient("httpClient.dataApi")
    interface DataApiClient {
        // routes stay the same
    }
    ```

Перехватчики, объявленные на интерфейсе, выполняются для каждого маршрута и **раньше** любого перехватчика, объявленного на отдельном методе. Поэтому для `getMappedByCode()` порядок такой: сначала
`ApiKeyAuthInterceptor`, затем `MethodLoggingInterceptor`, затем сам транспортный вызов.

Это очень распространённый сценарий использования перехватчиков. Команды применяют тот же приём для:

- заголовков `Authorization`
- кук
- API-ключей
- других метаданных запроса, которые всегда нужно добавлять автоматически

В `io.koraframework.http.client.common.interceptor` Kora поставляет и готовые перехватчики для стандартных схем, так что собственный класс нужен только для нестандартной схемы:

- `BasicAuthHttpClientInterceptor` — отправляет `Authorization: Basic ...` из логина и пароля либо из `HttpClientTokenProvider`
- `BearerAuthHttpClientInterceptor` — отправляет `Authorization: Bearer ...` из статического токена либо из `HttpClientTokenProvider`
- `ApiKeyHttpClientInterceptor` — отправляет API-ключ как заголовок, параметр запроса или куку; место выбирается через `ApiKeyLocation.{HEADER,QUERY,COOKIE}`

Настройте API-ключ:

Полный справочник по конфигурации смотрите в разделе [Конфигурация](../documentation/config.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    auth {
      apiKey {
        value = "MySecuredApiKey" //(1)!
        value = ${?HTTP_ADVANCED_API_KEY} //(2)!
      }
    }
    ```

    1. Локальное значение API-ключа по умолчанию, используемое в руководстве (обязательно, без значения по умолчанию).
    2. Необязательное переопределение API-ключа из переменной окружения `HTTP_ADVANCED_API_KEY`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    auth:
      apiKey:
        value: ${HTTP_ADVANCED_API_KEY:MySecuredApiKey} #(1)!
    ```

    1. API-ключ, используемый в руководстве (обязательно, без значения по умолчанию). Используется показанное значение, а `HTTP_ADVANCED_API_KEY` может его переопределить.

Оба приложения могут использовать одно и то же локальное значение по умолчанию, а `HTTP_ADVANCED_API_KEY` делает пример удобным для разных окружений. Телеметрия клиента по умолчанию маскирует заголовок
`authorization`, поэтому ключ не утекает в логи.

## Императивный клиент { #imperative-client }

Декларативные интерфейсы `@HttpClient` — обычный стиль на уровне приложения, но Kora предоставляет и базовый компонент `HttpClient`. Он полезен, когда запрос нужно собрать динамически, применить
перехватчик вручную или разобраться, что именно скрывает декларативный клиент.

Дублировать конфигурацию клиента для этого не нужно. Для каждого интерфейса `@HttpClient` процессор генерирует интерфейс конфигурации с именем `$<ИмяИнтерфейса>_Config` и модуль, который привязывает его
к настроенному пути; этот интерфейс — обычный компонент графа, который можно внедрить:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public interface $DataApiClient_Config extends DeclarativeHttpClientConfig {

        @Override
        HttpClientTelemetryConfig telemetry();

        HttpClientOperationConfig processForm();

        HttpClientOperationConfig processUpload();

        HttpClientOperationConfig processMappedRequest();

        HttpClientOperationConfig getMappedByCode();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    interface `$DataApiClient_Config` : DeclarativeHttpClientConfig {

        override fun telemetry(): HttpClientTelemetryConfig

        fun processForm(): HttpClientOperationConfig

        fun processUpload(): HttpClientOperationConfig

        fun processMappedRequest(): HttpClientOperationConfig

        fun getMappedByCode(): HttpClientOperationConfig
    }
    ```

`DeclarativeHttpClientConfig` даёт `url()`, `requestTimeout()` и `telemetry()`, а каждый абстрактный метод клиента добавляет один блок `HttpClientOperationConfig`. Именно поэтому
`httpClient.dataApi.getMappedByCode.requestTimeout` из конфигурации выше — валидный ключ, и именно поэтому default-методы вроде `sampleUpload()` там никогда не появляются.

Теперь добавим небольшой ручной клиент. Обратите внимание, что заголовок авторизации он не проставляет напрямую, а переиспользует тот же перехватчик через `this.httpClient.with(...)`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/client/ManualDataHttpClient.java"
    package io.koraframework.guide.httpclient.client;

    import java.nio.charset.StandardCharsets;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.client.common.HttpClient;
    import io.koraframework.http.client.common.request.HttpClientRequest;

    @Component
    public final class ManualDataHttpClient {

        private final HttpClient httpClient;
        private final $DataApiClient_Config dataApiConfig;
        private final ApiKeyAuthInterceptor apiKeyAuthInterceptor;

        public ManualDataHttpClient(HttpClient httpClient,
                                    $DataApiClient_Config dataApiConfig,
                                    ApiKeyAuthInterceptor apiKeyAuthInterceptor) {
            this.httpClient = httpClient;
            this.dataApiConfig = dataApiConfig;
            this.apiKeyAuthInterceptor = apiKeyAuthInterceptor;
        }

        public String pingManualHandler() {
            var request = HttpClientRequest.of("GET", this.dataApiConfig.url() + "/manual/data/ping")
                    .build();
            var response = this.httpClient.with(this.apiKeyAuthInterceptor).execute(request);
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

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/client/ManualDataHttpClient.kt"
    package io.koraframework.guide.httpclient.client

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.client.common.HttpClient
    import io.koraframework.http.client.common.request.HttpClientRequest
    import java.nio.charset.StandardCharsets

    @Component
    class ManualDataHttpClient(
        private val httpClient: HttpClient,
        private val dataApiConfig: `$DataApiClient_Config`,
        private val apiKeyAuthInterceptor: ApiKeyAuthInterceptor
    ) {

        fun pingManualHandler(): String {
            val request = HttpClientRequest.of("GET", dataApiConfig.url() + "/manual/data/ping")
                .build()
            val response = httpClient.with(apiKeyAuthInterceptor).execute(request)
            if (response.code() != 200) {
                throw IllegalStateException("Manual HTTP call failed with status ${response.code()}")
            }
            response.body().asInputStream().use { body ->
                return String(body.readAllBytes(), StandardCharsets.UTF_8)
            }
        }
    }
    ```

Пример намеренно небольшой, но он показывает четыре важные детали:

- `HttpClientRequest.of(method, uriTemplate)` возвращает `HttpClientRequestBuilder`; есть и сокращения вроде `HttpClientRequest.get(...)`, `.post(...)` и `.delete(...)`
- у построителя есть `pathParam`, `queryParam`, `header`, `body` и `requestTimeout`, а `request.toBuilder()` создаёт изменённую копию существующего запроса
- `HttpClient.with(...)` возвращает клиент, обёрнутый перехватчиком, так что авторизация остаётся в одном месте
- `execute(...)` — низкоуровневая синхронная операция, лежащая в основе любого декларативного клиента; она возвращает `HttpClientResponse`, тело которого нужно прочитать до закрытия

В отличие от декларативного метода, императивный клиент не переводит статус-коды за вас: здесь ничто не бросает `HttpClientResponseException`, поэтому проверка `response.code()` — ваша задача.

## Контроллер проверки { #check-controller }

Теперь свяжем продвинутые возможности клиента в один сводный сценарий, посвящённый только маршрутам `DataController`.

В базовом руководстве уже есть сводный эндпоинт для пользователей. Мы сохраняем это разделение:

- `testAllUserEndpoints()` относится к базовому руководству по клиенту
- `testAllDataEndpoints()` относится к этому продвинутому руководству

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/controller/ClientTestController.java"
    package io.koraframework.guide.httpclient.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpclient.client.DataApiClient;
    import io.koraframework.guide.httpclient.client.ManualDataHttpClient;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.form.FormUrlEncoded;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

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

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/controller/ClientTestController.kt"
    package io.koraframework.guide.httpclient.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpclient.client.DataApiClient
    import io.koraframework.guide.httpclient.client.ManualDataHttpClient
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.form.FormUrlEncoded
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val dataApiClient: DataApiClient,
        private val manualDataHttpClient: ManualDataHttpClient
    ) {
        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-data-endpoints")
        @Json
        fun testAllDataEndpoints(): TestResults {
            return try {
                val formResult = dataApiClient.processForm(form("name", "John"))
                val formProcessed = formResult == "Hello World, John"

                val uploadResult = dataApiClient.sampleUpload()
                val uploadProcessed = uploadResult.fileCount == 2

                val mappedRequestResult =
                    dataApiClient.processMappedRequest(DataApiClient.PlainTextGreetingBody("Client Mapper"))
                val customRequestMapped = mappedRequestResult == "Received mapped body: Hello Client Mapper"

                val mappedSuccess = dataApiClient.getMappedByCode(200)
                val mappedFailure = dataApiClient.getMappedByCode(404)
                val responseMapped =
                    mappedSuccess is DataApiClient.MappedResponse.Payload &&
                            mappedSuccess.message == "Hello from response mapper" &&
                            mappedFailure is DataApiClient.MappedResponse.Error &&
                            mappedFailure.code == 404 &&
                            mappedFailure.message == "Request failed with code 404"

                val manualPingResult = manualDataHttpClient.pingManualHandler()
                val manualHttpClientCallProcessed = manualPingResult == "manual-data-pong"

                val allTestsPassed = formProcessed &&
                        uploadProcessed &&
                        customRequestMapped &&
                        responseMapped &&
                        manualHttpClientCallProcessed
                TestResults(
                    formProcessed,
                    uploadProcessed,
                    customRequestMapped,
                    responseMapped,
                    manualHttpClientCallProcessed,
                    allTestsPassed,
                    null
                )
            } catch (e: Exception) {
                TestResults(false, false, false, false, false, false, e.message)
            }
        }

        private fun form(vararg keyValues: String): FormUrlEncoded {
            val parts = Array(keyValues.size / 2) { index ->
                FormUrlEncoded.FormPart(keyValues[index * 2], keyValues[index * 2 + 1])
            }
            return FormUrlEncoded(*parts)
        }

        @Json
        data class TestResults(
            val formProcessed: Boolean,
            val uploadProcessed: Boolean,
            val customRequestMapped: Boolean,
            val responseMapped: Boolean,
            val manualHttpClientCallProcessed: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

## Проверка приложения { #check-app }

Запустите продвинутый сервер и продвинутый клиент в отдельных терминалах.

### Терминал 1: сервер { #terminal-1-server }

```bash
./gradlew clean classes
./gradlew run
```

Продвинутое серверное приложение должно слушать `http://localhost:8080`.

### Терминал 2: клиент { #terminal-2-client }

```bash
./gradlew clean classes
./gradlew run
```

Продвинутое клиентское приложение должно слушать `http://localhost:8081`.

### Сценарий клиента { #client-scenario }

```bash
curl -X POST http://localhost:8081/client/test-all-data-endpoints
```

Ожидаемый результат: JSON-объект, в котором `allTestsPassed` равно `true`.

Тот же сценарий автоматизируется ровно так же, как в базовом руководстве: поднимите продвинутое серверное приложение в контейнере, направьте на него `DATA_API_URL` через `KoraAppTestConfigModifier` и
внедрите `DataApiClient` и `ManualDataHttpClient` через `@TestComponent`. Смотрите [Тест с контейнером](http-client.md#container-test).

## Лучшие практики { #best-practices }

- Держите базовое руководство по HTTP-клиенту сосредоточенным на простейшем JSON-первом пути, а транспортно-нагруженные темы выносите в продвинутое продолжение.
- Используйте отдельные интерфейсы клиентов для разных областей удалённого API, когда это улучшает читаемость.
- Беритесь за `HttpClientRequestMapper` только тогда, когда встроенных стилей преобразования недостаточно.
- Используйте `@ResponseCodeMapper`, когда разбор с учётом статус-кода — часть контракта, и `Either<T, E>`, когда достаточно простого разделения на успех и ошибку.
- Используйте перехватчики для повторяющегося транспортного поведения вроде логирования или авторизации вместо ручного дублирования заголовков и шаблонного кода.
- Для стандартных схем предпочитайте встроенные `BasicAuthHttpClientInterceptor`, `BearerAuthHttpClientInterceptor` и `ApiKeyHttpClientInterceptor`.
- Оставляйте императивный `HttpClient` для действительно динамических запросов и помните, что сам он не бросает `HttpClientResponseException`.

## Итоги { #summary }

Вы расширили базовое клиентское приложение HTTP:

- отдельным `DataApiClient`
- поддержкой запросов с формами и multipart
- собственным преобразователем запроса
- разбором ответа с учётом статус-кода
- перехватчиком уровня метода
- переиспользуемой авторизацией по API-ключу
- императивным вызовом, который переиспользует сгенерированную конфигурацию клиента и перехватчик авторизации

Результат повторяет дух `http-server-advanced.md`: по одному продвинутому транспортному понятию за раз, и каждое вводится только после того, как более простой путь уже понятен.

## Ключевые понятия { #key-concepts }

- `FormUrlEncoded` и `FormMultipart` — полноценные типы тела на стороне клиента Kora, и им не нужен собственный преобразователь
- `HttpClientRequestMapper<T>` превращает тип в тело HTTP-запроса через `HttpBodyOutput apply(T value)`
- `@ResponseCodeMapper` позволяет разным статус-кодам разбираться в разные варианты одного типа результата, а `ResponseCodeMapper.DEFAULT` служит запасным вариантом
- `HttpClientInterceptor.processRequest(chain, request)` синхронный, а перехватчики уровня интерфейса выполняются раньше перехватчиков уровня метода
- преобразователи и перехватчики, указанные в `@Mapping` и `@InterceptWith`, — аргументы конструктора сгенерированного клиента, поэтому они должны быть компонентами графа
- `$<Client>_Config` генерируется для каждого декларативного клиента, и его можно внедрить везде, где нужна конфигурация клиента

## Устранение неполадок { #troubleshooting }

**Защищённые вызовы возвращают 403:**

- Проверьте, что сервер и клиент используют одно и то же значение API-ключа.
- Проверьте переменную окружения `HTTP_ADVANCED_API_KEY` в обоих приложениях.
- Помните, что переменная окружения переопределяет локальное значение по умолчанию из `application.conf`.

**Запросы с формами или multipart не работают:**

- Убедитесь, что запущено продвинутое серверное приложение, а не только базовое.
- Проверьте, что `DataController` доступен на целевом сервере.
- Не добавляйте `@Json` к параметру типа `FormUrlEncoded` или `FormMultipart` — у этих типов уже есть собственные преобразователи запроса.

**Сборка падает с `No component found for dependency:` и типом преобразователя или перехватчика:**

- Добавьте `@Component` классу, указанному в `@Mapping` или `@InterceptWith`. Сгенерированный клиент получает оба аргументами конструктора, поэтому они должны быть в графе даже без собственных
  зависимостей.

**Собственный преобразователь запроса не срабатывает:**

- Убедитесь, что у параметра указан `@Mapping(...)`.
- Убедитесь, что преобразователь реализует `HttpClientRequestMapper<T>` ровно для типа параметра.

**Сопоставление по коду ответа ведёт себя не так, как ожидалось:**

- Внимательно проверьте записи `@ResponseCodeMapper`.
- Помните, что `ResponseCodeMapper.DEFAULT` — запасной вариант для всех неперечисленных кодов, и что без записи `DEFAULT` неперечисленный код приводит к `HttpClientResponseException`.
- Убедитесь, что серверный маршрут возвращает для каждой ветки ту форму JSON, которую ожидает ваш преобразователь.
- Исключение, брошенное внутри преобразователя, всплывает как `HttpClientDecoderException`, поэтому смотрите на причину.

**Логи перехватчика не появляются:**

- Проверьте `@InterceptWith(...)` на нужном методе клиента или на интерфейсе.
- Убедитесь, что класс перехватчика реализует `HttpClientInterceptor` и помечен `@Component`.

**Императивный вызов зависает или возвращает пустое тело:**

- Читайте тело до закрытия ответа: `HttpClientResponse` реализует `Closeable`, а тело не буферизуется за вас.
- Задавайте таймаут через `HttpClientRequest.of(...).requestTimeout(...)`, если удалённый сервис может отвечать медленно.

## Что дальше? { #whats-next }

- [OpenAPI HTTP-сервер](openapi-http-server.md), если вы ещё не прошли путь contract-first для сервера.
- [OpenAPI HTTP-клиент](openapi-http-client.md) после OpenAPI HTTP-сервера — посмотреть, как генерация по контракту моделирует похожее транспортное поведение.
- [Шаблоны отказоустойчивости](resilient.md), чтобы защитить продвинутые исходящие вызовы повтором, таймаутом, предохранителем и запасным сценарием.
- [Наблюдаемость](observability.md), чтобы трассировать перехватчики, ручные вызовы `HttpClient` и преобразованные ответы.

## Помощь { #help }

Если вы застряли:

- сравните с [Kora Java HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-advanced-app) и [Kora Kotlin HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-advanced-app)
- вернитесь к [HTTP-клиенту](http-client.md) за базовой формой декларативного клиента
- вернитесь к [Продвинутому HTTP-серверу](http-server-advanced.md) за серверными эндпоинтами, которые вызывает этот клиент
- посмотрите [документацию по HTTP-клиенту](../documentation/http-client.md)
