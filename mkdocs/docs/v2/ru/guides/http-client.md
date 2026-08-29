---
search:
  exclude: true
title: Руководство по HTTP-клиенту
summary: Build a separate Kora application that calls the user endpoints from the HTTP Server guide with declarative synchronous clients
description: "Step-by-step declarative HTTP client for a Kora 2.0 service: the io.koraframework:http-client-ok artifact and OkHttpClientModule, a @HttpClient interface whose @HttpRoute methods bind @Path, @Query, @Header and @Cookie parameters and @Json request and response DTOs, HttpResponseEntity returns and a custom HttpClientResponseMapper, HttpClientResponseException on non-2xx answers, the httpClient.userApi url, requestTimeout and telemetry configuration next to httpServer.port and httpServer.system.port, and a @KoraAppTest check of the client against the running server application."
agent:
  use_when: "Use this file for questions about calling another service from Kora 2.0 with a declarative client: io.koraframework:http-client-ok, OkHttpClientModule, @HttpClient with a config path, @HttpRoute with HttpMethod, @Path, @Query, @Header, @Cookie, @Json bodies, HttpResponseEntity, writing an HttpClientResponseMapper for a type Kora has no ready mapper for, HttpClientResponseException and its code, headers and bytes, the httpClient.userApi.url and requestTimeout keys versus the transport-wide httpClient.connectTimeout, readTimeout and proxy, why suspend and CompletionStage client methods are rejected, and running the client and server applications side by side."
tags: http-client, http-server, declarative-client, okhttp, integration
---

# Руководство по HTTP-клиенту { #http-client-guide }

Это руководство знакомит с декларативными HTTP-клиентами в Kora. В нём разбирается, как аннотированные интерфейсы на Java и Kotlin описывают исходящие HTTP-вызовы, как JSON-тела запросов и ответов
преобразуются на границе клиента и как Kora связывает сгенерированную реализацию клиента с отдельным графом приложения. Вы также увидите, как клиентское приложение удерживает детали HTTP у транспортной
границы, чтобы остальной код оставался сосредоточен на сценариях использования.

HTTP-клиенты Kora **синхронные**. Декларативный метод отправляет запрос, дожидается ответа и сразу возвращает преобразованный результат. Здесь нет клиентских методов с `CompletionStage`, `Mono`, `Flux`
или `suspend`: параллелизм обеспечивают виртуальные потоки и структурированная многозадачность, а не тип возвращаемого значения.

===! ":fontawesome-brands-java: `Java`"

    Если хотите сверяться с готовым результатом по ходу дела, используйте рабочий пример: [Kora Java HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-app).

=== ":simple-kotlin: `Kotlin`"

    Если хотите сверяться с готовым результатом по ходу дела, используйте рабочий пример: [Kora Kotlin HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-app).

## Что вы создадите { #youll-build }

Вы создадите второе приложение Kora, которое:

- объявляет типизированный `UserApiClient`
- вызывает эндпоинты `/users` из руководства по HTTP-серверу
- предоставляет один сводный эндпоинт `POST /client/test-all-user-endpoints` для быстрой ручной проверки
- покрыт тестом JUnit 5, работающим против серверного приложения в контейнере

## Что понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+ (эталонные приложения используют Gradle Wrapper `9.5.1`)
- Docker Desktop или другое локальное окружение Docker для тестов с контейнерами
- Текстовый редактор или IDE
- Два терминала, если хотите запускать сервер и клиент вручную

Артефакты Kora собраны под Java 25, поэтому JDK, которым компилируется ваш код, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по HTTP-серверу"

    Это руководство предполагает, что вы прошли **[Руководство по HTTP-серверу](http-server.md)** и уже понимаете эндпоинты CRUD-API пользователей.

    Если руководство по HTTP-серверу ещё не пройдено, начните с него: здесь мы создаём отдельное клиентское приложение, которое обращается к уже существующему API.

## Обзор { #overview }

[HTTP](https://www.rfc-editor.org/rfc/rfc9110)-клиент — это исходящая граница приложения. Он представляет API другого сервиса внутри вашей кодовой базы. Декларативная модель клиентов Kora позволяет
описать этот удалённый API как интерфейс на Java или Kotlin вместо ручной сборки URL, заголовков, тел запросов и логики разбора ответов.

Идея похожа на то, как контроллер описывает входящий HTTP-API, но направление обратное. Контроллер превращает входящие HTTP-запросы в вызовы приложения. Клиент превращает вызовы приложения в исходящие
HTTP-запросы.

### Декларативные клиенты { #declarative-clients }

Полное описание модели декларативных клиентов, `@HttpClient`, маршрутов и конфигурации смотрите в разделе [Декларативный HTTP-клиент](../documentation/http-client.md#client-declarative).

Декларативные клиенты используют ту же идею, что и контроллеры сервера, только в обратную сторону:

- аннотации метода описывают удалённый HTTP-метод и путь
- параметры становятся переменными пути, параметрами запроса, заголовками, куками или телом
- возвращаемые типы описывают ожидаемый ответ
- Kora генерирует реализацию во время компиляции

В результате получается типизированный клиент, который внедряется как любой другой компонент Kora. Ничего не разрешается через рефлексию во время выполнения: процессор аннотаций пишет обычный класс,
который собирает запрос и преобразует ответ.

### Транспортная граница и служба приложения { #transport-boundary-application-service }

Сгенерированные клиенты ориентированы на транспорт. Они знают, как вызвать HTTP-эндпоинты, но не должны сами описывать все сценарии приложения. Держите сгенерированный интерфейс близко к удалённому
контракту, а компоненты приложения пусть вызывают его так же, как любую другую зависимость.

Эта граница — правильное место и для обработки ошибок уровня приложения, и для аннотаций отказоустойчивости из последующих руководств, и для небольших преобразований между внешними DTO и внутренними
моделями.

### Конфигурация и вызовы { #configuration-calls }

HTTP-клиенту также нужна конфигурация времени выполнения: базовый URL, таймауты и настройки телеметрии. Kora хранит их в конфигурации и связывает настроенный клиент с графом зависимостей. Благодаря
этому код не меняется при переходе между локальной разработкой, тестами и реальными окружениями.

Практический порядок действий такой:

1. описать удалённый API как аннотированный интерфейс
2. настроить адрес клиента в HOCON
3. позволить Kora сгенерировать и внедрить реализацию
4. вызывать сгенерированный клиент из компонентов приложения
5. открыть локальные маршруты, которые задействуют исходящие вызовы

## Зависимости { #dependencies }

Клиентскому приложению нужны:

- транспорт HTTP-клиента, чтобы Kora могла сгенерировать и выполнять декларативные клиенты
- зависимости HTTP-сервера, потому что это клиентское приложение всё же предоставляет один собственный проверочный эндпоинт

В Kora 2.0 есть три транспорта, и ровно один из них должен присутствовать в classpath:

| Артефакт | Транспорт |
|---|---|
| `io.koraframework:http-client-ok` | [OkHttp](https://square.github.io/okhttp/) |
| `io.koraframework:http-client-apache` | [Apache HttpClient](https://hc.apache.org/) |
| `io.koraframework:http-client-jdk` | `java.net.http.HttpClient` из JDK |

В этом руководстве используется OkHttp.

Версии берутся из BOM `io.koraframework:kora-bom`, поэтому отдельные модули Kora объявляются без версии:

```properties title="gradle.properties"
koraVersion=2.0.0.RC1
junitVersion=6.1.3
```

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    configurations {
        koraBom
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testImplementation.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:$koraVersion")

        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:http-client-common"
        implementation "io.koraframework:http-client-ok"
        implementation "io.koraframework:http-server-undertow"
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:logging-logback"

        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
        testImplementation "org.testcontainers:testcontainers-junit-jupiter:2.0.5"
        testImplementation "org.testcontainers:testcontainers:2.0.5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:http-client-common")
        implementation("io.koraframework:http-client-ok")
        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
        testImplementation("org.testcontainers:testcontainers-junit-jupiter:2.0.5")
        testImplementation("org.testcontainers:testcontainers:2.0.5")
    }
    ```

Генерация кода для Java выполняется процессором аннотаций `io.koraframework:annotation-processors`, для Kotlin — KSP-процессором `io.koraframework:symbol-processors`. Без одного из них интерфейс
`@HttpClient` так и останется интерфейсом, и граф не найдёт для него реализацию.

## Модули { #modules }

Мы используем:

- `HoconConfigModule` для `application.conf`
- `JsonModule` для сериализации запросов и ответов
- `LogbackModule` для логов
- `OkHttpClientModule` как транспорт клиента
- `UndertowPublicHttpServerModule`, потому что это клиентское приложение предоставляет собственный эндпоинт

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/Application.java"
    package io.koraframework.guide.httpclient;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.client.ok.OkHttpClientModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            OkHttpClientModule,  // <----- Connected module
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/Application.kt"
    package io.koraframework.guide.httpclient

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.client.ok.OkHttpClientModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        OkHttpClientModule,  // <----- Connected module
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`OkHttpClientModule` добавляет в граф транспортный компонент `HttpClient`, а вместе с ним преобразователи запросов и ответов, на которые опирается любой сгенерированный клиент. Замена его на
`ApacheHttpClientModule` или `JdkHttpClientModule` меняет транспорт, не затрагивая ни одного интерфейса клиента.

## DTO-модели { #dto-models }

Первое понятие клиента вовсе не специфично для клиента: клиенту нужны те же структуры данных, которые сервер отправляет и принимает.

Поэтому начнём с повторного использования контракта `UserRequest` и `UserResponse` из руководства по серверу. Это держит клиент и сервер согласованными и даёт сгенерированному клиенту типизированный
интерфейс для работы.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/dto/UserRequest.java"
    package io.koraframework.guide.httpclient.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    ```java title="src/main/java/io/koraframework/guide/httpclient/dto/UserResponse.java"
    package io.koraframework.guide.httpclient.dto;

    import java.time.LocalDateTime;
    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/dto/UserRequest.kt"
    package io.koraframework.guide.httpclient.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserRequest(val name: String, val email: String)
    ```

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/dto/UserResponse.kt"
    package io.koraframework.guide.httpclient.dto

    import io.koraframework.json.common.annotation.Json
    import java.time.LocalDateTime

    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

`@Json` заставляет компилятор сгенерировать `JsonReader` и `JsonWriter` для каждого типа — именно эти компоненты сгенерированный клиент запрашивает у графа, когда метод или параметр помечен `@Json`.

## HTTP-клиент { #http-client }

Теперь опишем удалённый HTTP-API в виде интерфейса.

Это ключевая абстракция руководства. Вместо императивного клиентского кода мы объявляем удалённый контракт аннотациями:

- `@HttpClient` помечает весь интерфейс как декларативный клиент, а значением указывает путь конфигурации
- `@HttpRoute` описывает удалённый метод и путь
- `@Path`, `@Query`, `@Header` и `@Cookie` отображают отдельные аргументы
- `@Json` говорит, что для тела нужно использовать JSON-преобразователи

Этот интерфейс повторяет эндпоинты пользователей из `http-server.md`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/client/UserApiClient.java"
    package io.koraframework.guide.httpclient.client;

    import java.io.IOException;
    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpclient.dto.UserRequest;
    import io.koraframework.guide.httpclient.dto.UserResponse;
    import io.koraframework.http.client.common.annotation.HttpClient;
    import io.koraframework.http.client.common.response.HttpClientResponse;
    import io.koraframework.http.client.common.response.HttpClientResponseMapper;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.HttpResponseEntity;
    import io.koraframework.http.common.annotation.Cookie;
    import io.koraframework.http.common.annotation.Header;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.common.annotation.Query;
    import io.koraframework.json.common.annotation.Json;
    import org.jspecify.annotations.Nullable;

    @HttpClient("httpClient.userApi")
    public interface UserApiClient {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        HttpResponseEntity<UserResponse> createUser(
                @Json UserRequest request,
                @Nullable @Header("X-Request-ID") String requestId,
                @Nullable @Header("User-Agent") String userAgent,
                @Nullable @Cookie("sessionId") String sessionId);

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        UserResponse getUser(@Path String userId);

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        List<UserResponse> getUsers(
                @Nullable @Query("page") Integer page,
                @Nullable @Query("size") Integer size,
                @Nullable @Query("sort") String sort);

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        HttpResponseEntity<Void> deleteUser(@Path String userId);

        @Component
        final class VoidResponseMapper implements HttpClientResponseMapper<Void> {

            @Override
            public Void apply(HttpClientResponse response) throws IOException {
                try (var body = response.body()) {
                    body.asInputStream().readAllBytes();
                }
                return null;
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/client/UserApiClient.kt"
    package io.koraframework.guide.httpclient.client

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpclient.dto.UserRequest
    import io.koraframework.guide.httpclient.dto.UserResponse
    import io.koraframework.http.client.common.annotation.HttpClient
    import io.koraframework.http.client.common.response.HttpClientResponse
    import io.koraframework.http.client.common.response.HttpClientResponseMapper
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.HttpResponseEntity
    import io.koraframework.http.common.annotation.Cookie
    import io.koraframework.http.common.annotation.Header
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.common.annotation.Query
    import io.koraframework.json.common.annotation.Json

    @HttpClient("httpClient.userApi")
    interface UserApiClient {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(
            @Json request: UserRequest,
            @Header("X-Request-ID") requestId: String?,
            @Header("User-Agent") userAgent: String?,
            @Cookie("sessionId") sessionId: String?
        ): HttpResponseEntity<UserResponse>

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(@Path userId: String): UserResponse

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getUsers(
            @Query("page") page: Int?,
            @Query("size") size: Int?,
            @Query("sort") sort: String?
        ): List<UserResponse>

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        fun deleteUser(@Path userId: String): HttpResponseEntity<Void>

        @Component
        class VoidResponseMapper : HttpClientResponseMapper<Void> {

            override fun apply(response: HttpClientResponse): Void? {
                response.body().use { body ->
                    body.asInputStream().readAllBytes()
                }
                return null
            }
        }
    }
    ```

Несколько деталей этого интерфейса стоит разобрать не спеша.

**Путь конфигурации — это значение аннотации.** `@HttpClient("httpClient.userApi")` привязывает клиент к разделу конфигурации `httpClient.userApi`. Значение позиционное; у аннотации объявлены только
`value`, `telemetryTag` и `httpClientTag`. Если значение опустить, Kora выведет путь из имени интерфейса: `UserApiClient` превратится в `httpClient.userApiClient`.

**Nullable-параметры необязательны.** Заголовок, параметр запроса или кука с `@Nullable` просто не попадает в запрос, если аргумент равен `null`. В Kotlin тот же смысл несёт nullable-тип `String?`, и
аннотация не нужна. Ненулевой параметр записывается в запрос всегда.

**Методы синхронные.** `getUser` возвращает `UserResponse`, а не future. Kotlin-функции с `suspend` отклоняются символьным процессором с ошибкой компиляции, а Java-клиенты, возвращающие
`CompletionStage`, вызывают предупреждение `Method has async signature, this might not work correctly`. Пишите обычные блокирующие сигнатуры.

**Успех и ошибка разделены по статус-коду.** Для метода, возвращающего обычное тело, Kora преобразует ответ только при статусах `2xx`; любой другой статус приводит к `HttpClientResponseException`. Если
нужен сам статус-код, возвращайте `HttpResponseEntity<T>` — так делают `createUser` и `deleteUser`.

**Для `HttpResponseEntity<Void>` нужен собственный преобразователь.** Kora предоставляет готовые преобразователи ответа для `String`, `byte[]`, `ByteBuffer` и `HttpBodyInput`, а также шаблонную фабрику,
которая оборачивает любой `HttpClientResponseMapper<T>` в `HttpClientResponseMapper<HttpResponseEntity<T>>`. Встроенного преобразователя для `Void` нет, поэтому сборка графа для `deleteUser` упала бы с
`No component found for dependency:`, если бы приложение его не предоставило. `VoidResponseMapper` и есть этот компонент: он вычитывает тело и возвращает `null`, а обёртку в сущность делает сам
фреймворк. Обратите внимание: он зарегистрирован как `@Component` и **не** указывается через `@Mapping` — с `@Mapping` преобразователь должен был бы возвращать целиком `HttpResponseEntity<Void>`, а не
только полезную нагрузку.

!!! tip "Более простой вариант"

    Если статус-код ответа без тела вам не нужен, объявите `void deleteUser(@Path String userId)`. Методу с типом `void` преобразователь ответа не требуется вовсе, а статус вне `2xx` по-прежнему
    приведёт к `HttpClientResponseException`.

## Конфигурация { #config }

Это приложение — самостоятельный сервис Kora, поэтому ему нужны собственные порты.

Мы будем использовать:

- `8080` для серверного приложения из `http-server.md`
- `8081` для публичного HTTP-сервера клиентского приложения
- `8086` для системного HTTP-сервера клиентского приложения (пробы, метрики)
- `httpClient.userApi.url` как базовый URL для сгенерированного клиента

Полный справочник по конфигурации смотрите в разделах [HTTP-сервер](../documentation/http-server.md), [HTTP-клиент](../documentation/http-client.md) и [Логирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      port = 8081 //(1)!
      system.port = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    httpClient {
      userApi {
        url = "http://localhost:8080" //(4)!
        url = ${?USER_API_URL} //(5)!
        requestTimeout = 10s //(6)!
        telemetry.logging.enabled = true //(7)!
      }
    }

    logging {
      levels {
        "ROOT": "INFO" //(8)!
        "io.koraframework": "INFO" //(9)!
      }
    }
    ```

    1. Порт публичного HTTP-сервера, на котором работает локальный эндпоинт руководства (по умолчанию: `8080`).
    2. Порт системного HTTP-сервера для проб и метрик (по умолчанию: `8085`).
    3. Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4. Базовый URL, который использует настроенный клиент (обязательно, без значения по умолчанию).
    5. Необязательное переопределение базового URL из переменной окружения `USER_API_URL`.
    6. Максимальное время одного запроса клиента (опционально, без значения по умолчанию).
    7. Включает логирование запросов этого клиента (по умолчанию: `false`).
    8. Уровень логирования для `ROOT`.
    9. Уровень логирования для `io.koraframework`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      port: 8081 #(1)!
      system:
        port: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    httpClient:
      userApi:
        url: ${USER_API_URL:http://localhost:8080} #(4)!
        requestTimeout: 10s #(5)!
        telemetry:
          logging:
            enabled: true #(6)!
    logging:
      levels:
        ROOT: "INFO" #(7)!
        "io.koraframework": "INFO" #(8)!
    ```

    1. Порт публичного HTTP-сервера, на котором работает локальный эндпоинт руководства (по умолчанию: `8080`).
    2. Порт системного HTTP-сервера для проб и метрик (по умолчанию: `8085`).
    3. Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4. Базовый URL, который использует настроенный клиент (обязательно, без значения по умолчанию). Используется показанное значение, а `USER_API_URL` может его переопределить.
    5. Максимальное время одного запроса клиента (опционально, без значения по умолчанию).
    6. Включает логирование запросов этого клиента (по умолчанию: `false`).
    7. Уровень логирования для `ROOT`.
    8. Уровень логирования для `io.koraframework`.

Телеметрия относится к разделу конкретного клиента, а не к общему корню `httpClient`: декларативный клиент читает ровно то поддерево, которое названо в `@HttpClient`, поэтому на `UserApiClient` влияет
путь `httpClient.userApi.telemetry`. Общие настройки транспорта вроде `httpClient.connectTimeout`, `httpClient.readTimeout` и `httpClient.proxy` действительно живут в корне, потому что настраивают
общий транспорт.

Необязательное переопределение `USER_API_URL` особенно полезно в тестах, где целевой сервер может работать в контейнере на случайном пробрасываемом порту.

## Контроллер проверки { #check-controller }

Клиентскому приложению не нужно повторно воспроизводить весь сервер — для этого у нас уже есть серверное приложение. Вместо этого мы открываем один небольшой контроллер, который прогоняет полный
сценарий через сгенерированный клиент.

Это полезно по двум причинам:

- даёт один ручной эндпоинт, который можно дёрнуть в процессе обучения
- оставляет главным предметом руководства сами интерфейсы сгенерированного клиента

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/controller/ClientTestController.java"
    package io.koraframework.guide.httpclient.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpclient.client.UserApiClient;
    import io.koraframework.guide.httpclient.dto.UserRequest;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final UserApiClient userApiClient;

        public ClientTestController(UserApiClient userApiClient) {
            this.userApiClient = userApiClient;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        public TestResults testAllUserEndpoints() {
            try {
                var created = this.userApiClient.createUser(
                        new UserRequest("Client Demo User", "client-demo@example.com"),
                        "client-test-request",
                        "guide-http-client-app",
                        "client-test-session");

                boolean userCreated = created.code() == 201 && created.body() != null;
                var createdUser = created.body();
                var fetched = createdUser == null ? null : this.userApiClient.getUser(createdUser.id());
                boolean userFetched = fetched != null && createdUser != null && fetched.id().equals(createdUser.id());
                var users = this.userApiClient.getUsers(0, 10, "name");
                boolean usersListed = createdUser != null && users.stream().anyMatch(user -> user.id().equals(createdUser.id()));
                var deleteResult = createdUser == null ? null : this.userApiClient.deleteUser(createdUser.id());
                boolean userDeleted = deleteResult != null && deleteResult.code() == 204;

                boolean allTestsPassed = userCreated && userFetched && usersListed && userDeleted;
                return new TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, false, exception.getMessage());
            }
        }

        @Json
        public record TestResults(
                boolean userCreated,
                boolean userFetched,
                boolean usersListed,
                boolean userDeleted,
                boolean allTestsPassed,
                String error) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/controller/ClientTestController.kt"
    package io.koraframework.guide.httpclient.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpclient.client.UserApiClient
    import io.koraframework.guide.httpclient.dto.UserRequest
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val userApiClient: UserApiClient
    ) {
        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        fun testAllUserEndpoints(): TestResults {
            return try {
                val created = userApiClient.createUser(
                    UserRequest("Client Demo User", "client-demo@example.com"),
                    "client-test-request",
                    "guide-http-client-app",
                    "client-test-session"
                )

                val userCreated = created.code() == 201 && created.body() != null
                val createdUser = created.body()
                val fetched = createdUser?.let { userApiClient.getUser(it.id) }
                val userFetched = fetched != null && createdUser != null && fetched.id == createdUser.id
                val users = userApiClient.getUsers(0, 10, "name")
                val usersListed = createdUser != null && users.any { it.id == createdUser.id }
                val deleteResult = createdUser?.let { userApiClient.deleteUser(it.id) }
                val userDeleted = deleteResult != null && deleteResult.code() == 204

                val allTestsPassed = userCreated && userFetched && usersListed && userDeleted
                TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null)
            } catch (e: Exception) {
                TestResults(false, false, false, false, false, e.message)
            }
        }

        @Json
        data class TestResults(
            val userCreated: Boolean,
            val userFetched: Boolean,
            val usersListed: Boolean,
            val userDeleted: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

Обратите внимание, насколько обычно выглядит вызывающий код. Клиент синхронный, поэтому сценарий читается сверху вниз: создать, получить, перечислить, удалить. Единственная деталь, специфичная для
клиента, — `HttpResponseEntity`, который даёт доступ к `code()` и `body()`, когда важен статус-код.

## Проверка приложения { #check-app }

Если хотите проверить сценарий вручную, запустите оба приложения в отдельных терминалах.

### Терминал 1: сервер { #terminal-1-server }

```bash
./gradlew clean classes
./gradlew run
```

Серверное приложение должно отдавать публичный API по адресу `http://localhost:8080`.

### Терминал 2: клиент { #terminal-2-client }

```bash
./gradlew clean classes
./gradlew run
```

Клиентское приложение должно отдавать публичный API по адресу `http://localhost:8081`.

### Клиентский сценарий { #client-scenario }

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

Ожидаемый результат: JSON-объект, в котором `allTestsPassed` равно `true`.

### Тест с контейнером { #container-test }

Ручные проверки хороши на этапе обучения, но тот же сценарий несложно автоматизировать. `@KoraAppTest` поднимает граф клиентского приложения внутри JUnit 5, `@TestComponent` внедряет сгенерированный
клиент, а `KoraAppTestConfigModifier` направляет `USER_API_URL` на копию серверного приложения в контейнере.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/test/java/io/koraframework/guide/httpclient/HttpClientAppTest.java"
    package io.koraframework.guide.httpclient;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertNotNull;
    import static org.junit.jupiter.api.Assertions.assertThrows;

    import java.util.UUID;
    import org.junit.jupiter.api.Test;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;
    import io.koraframework.guide.httpclient.client.UserApiClient;
    import io.koraframework.guide.httpclient.dto.UserRequest;
    import io.koraframework.http.client.common.exception.HttpClientResponseException;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier;
    import io.koraframework.test.extension.junit5.KoraConfigModification;
    import io.koraframework.test.extension.junit5.TestComponent;

    @Testcontainers
    @KoraAppTest(Application.class)
    class HttpClientAppTest implements KoraAppTestConfigModifier {

        @Container
        static final AppContainer APP = new AppContainer();

        @TestComponent
        private UserApiClient userApiClient;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofResourceFile("application.conf")
                    .withSystemProperty("USER_API_URL", APP.getURI().toString());
        }

        @Test
        void createUserReturnsCreatedUser() {
            String unique = UUID.randomUUID().toString().substring(0, 8);

            var response = this.userApiClient.createUser(
                    new UserRequest("Client User " + unique, "client-" + unique + "@example.com"),
                    "request-1",
                    "test-agent",
                    "session-1");

            assertEquals(201, response.code());
            assertNotNull(response.body());
        }

        @Test
        void getMissingUserThrows() {
            assertThrows(HttpClientResponseException.class, () -> this.userApiClient.getUser("999999"));
        }

        @Test
        void deleteUserReturnsNoContent() {
            String unique = UUID.randomUUID().toString().substring(0, 8);
            var created = this.userApiClient.createUser(
                    new UserRequest("Delete Me " + unique, "delete-" + unique + "@example.com"),
                    "request-3",
                    "test-agent",
                    "session-3").body();

            var response = this.userApiClient.deleteUser(created.id());

            assertEquals(204, response.code());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/test/kotlin/io/koraframework/guide/httpclient/HttpClientAppTest.kt"
    package io.koraframework.guide.httpclient

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Assertions.assertThrows
    import org.junit.jupiter.api.Test
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers
    import io.koraframework.guide.httpclient.client.UserApiClient
    import io.koraframework.guide.httpclient.dto.UserRequest
    import io.koraframework.http.client.common.exception.HttpClientResponseException
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier
    import io.koraframework.test.extension.junit5.KoraConfigModification
    import io.koraframework.test.extension.junit5.TestComponent
    import java.util.UUID

    @Testcontainers
    @KoraAppTest(Application::class)
    class HttpClientAppTest : KoraAppTestConfigModifier {

        @TestComponent
        lateinit var userApiClient: UserApiClient

        override fun config(): KoraConfigModification =
            KoraConfigModification.ofResourceFile("application.conf")
                .withSystemProperty("USER_API_URL", APP.getURI().toString())

        @Test
        fun createUserReturnsCreatedUser() {
            val unique = UUID.randomUUID().toString().substring(0, 8)

            val response = userApiClient.createUser(
                UserRequest("Client User $unique", "client-$unique@example.com"),
                "request-1",
                "test-agent",
                "session-1"
            )

            assertEquals(201, response.code())
            assertNotNull(response.body())
        }

        @Test
        fun getMissingUserThrows() {
            assertThrows(HttpClientResponseException::class.java) { userApiClient.getUser("999999") }
        }

        @Test
        fun deleteUserReturnsNoContent() {
            val unique = UUID.randomUUID().toString().substring(0, 8)
            val created = userApiClient.createUser(
                UserRequest("Delete Me $unique", "delete-$unique@example.com"),
                "request-3",
                "test-agent",
                "session-3"
            ).body()!!

            val response = userApiClient.deleteUser(created.id)

            assertEquals(204, response.code())
        }

        companion object {
            @Container
            @JvmStatic
            val APP: AppContainer = AppContainer()
        }
    }
    ```

`AppContainer` — это обычный `GenericContainer` из Testcontainers: он собирает образ серверного приложения из `Dockerfile` руководства по серверу, публикует порты `8080` и `8085` и ждёт ответа
`/system/readiness` на системном порту перед запуском теста. Подробности работы с контейнерами разобраны в руководстве [Интеграционное тестирование](testing-integration.md).

## Лучшие практики { #best-practices }

- Держите интерфейсы клиентов небольшими и разбивайте их по областям удалённого API.
- По возможности переиспользуйте контракт DTO из руководства по серверу, чтобы клиент и сервер оставались согласованными.
- Возвращайте `HttpResponseEntity<T>` только тогда, когда нужны статус-коды или заголовки; в остальных случаях возвращайте DTO напрямую.
- Оставляйте методы клиента блокирующими. Если нужны параллельные вызовы, выполняйте блокирующие вызовы на виртуальных потоках или в структурированной области задач, а не меняйте тип результата.
- Давайте каждому клиенту собственный раздел конфигурации, чтобы таймауты и телеметрию можно было настраивать для каждого удалённого сервиса отдельно.
- Для учебных сценариев используйте один небольшой сводный контроллер вместо воспроизведения всего сервера внутри клиентского приложения.
- Добавляйте продвинутые возможности клиента только после того, как базовый контракт стал понятным.

## Итоги { #summary }

Вы создали самостоятельное клиентское приложение Kora, которое обращается к API пользователей из руководства по HTTP-серверу.

По ходу дела вы:

- переиспользовали контракт DTO сервера
- объявили `UserApiClient`, сгенерированный во время компиляции
- предоставили `HttpClientResponseMapper<Void>`, который нужен ответу без тела `HttpResponseEntity<Void>`
- настроили базовый URL, таймаут запроса и телеметрию клиента
- открыли один сводный эндпоинт для быстрой ручной проверки
- покрыли клиент тестом JUnit 5 против сервера в контейнере

## Ключевые понятия { #key-concepts }

- `@HttpClient("httpClient.userApi")` привязывает декларативный клиент к конкретному разделу конфигурации через позиционное значение
- `@HttpRoute`, `@Path`, `@Query`, `@Header` и `@Cookie` типобезопасно описывают удалённый контракт
- методы декларативного клиента синхронные и сразу возвращают преобразованный результат
- `HttpResponseEntity<T>` полезен, когда нужны и тело, и метаданные HTTP
- ответы вне `2xx` приводят к `HttpClientResponseException`, если метод не описывает их явно
- транспорт выбирается модулем (`OkHttpClientModule`, `ApacheHttpClientModule`, `JdkHttpClientModule`), а не интерфейсом клиента

## Устранение неполадок { #troubleshooting }

**Клиент не может подключиться к серверу:**

- Убедитесь, что серверное приложение работает на порту `8080` для ручных проверок
- Убедитесь, что `httpClient.userApi.url` указывает на реальный URL сервера
- Если вы переопределяете `USER_API_URL`, проверьте, что значение по-прежнему указывает на публичный API серверного приложения

**Сборка падает с `No component found for dependency:` и типом `HttpClientResponseMapper`:**

- Метод возвращает тип, для которого у Kora нет готового преобразователя. Добавьте `@Component`, реализующий `HttpClientResponseMapper<T>` для типа полезной нагрузки, как это делает `VoidResponseMapper` для `Void`
- Для JSON-нагрузок убедитесь, что DTO помечен `@Json`, а метод или параметр тоже помечен `@Json`

**Компиляция Kotlin падает с `Suspend methods are not supported by the HTTP client generator`:**

- Уберите `suspend` из метода клиента. HTTP-клиенты Kora блокирующие по замыслу

**Сборка Java печатает `Method has async signature, this might not work correctly`:**

- Метод возвращает `CompletionStage` или `Mono`. Замените тип на обычный синхронный

**Вызовы падают с `HttpClientResponseException`:**

- Удалённый сервис ответил статусом вне `2xx`. Методы `getCode()`, `getHeaders()` и `getBytes()` исключения содержат детали ответа
- Если статус вне `2xx` — нормальная часть контракта, возвращайте `HttpResponseEntity<T>` или описывайте обе ветки, как показано в [Продвинутом HTTP-клиенте](http-client-advanced.md#response-code-mapping)

**Сборка Gradle зависает или удерживает блокировки файлов в Windows:**

- Выполните `./gradlew --stop` и повторите
- Если появляется `AccessDeniedException` вокруг кеша Gradle или каталогов `build/`, закройте запущенные Java-процессы, терминалы и редакторы, которые ещё держат файловые дескрипторы

**Телеметрия клиента слишком шумная:**

- Отключите или настройте `httpClient.userApi.telemetry.logging.enabled` в `application.conf`, когда закончите отладку
- Чувствительные заголовки уже маскируются: `authorization`, `cookie` и `set-cookie` по умолчанию заменяются на `***`

**Системные эндпоинты не отвечают:**

- В этом руководстве системный HTTP-порт клиентского приложения — `8086`, чтобы он не пересекался с портами серверного приложения
- Стандартный путь готовности — `/system/readiness`, живости — `/system/liveness`
- Если меняете любое из значений, согласованно обновите стратегию ожидания и заметки по устранению неполадок

## Что дальше? { #whats-next }

- [Продвинутый HTTP-сервер](http-server-advanced.md), если хотите подготовить продвинутые серверные маршруты, которые использует руководство по продвинутому клиенту.
- [Продвинутый HTTP-клиент](http-client-advanced.md) после продвинутого HTTP-сервера — добавить формы, multipart, перехватчики, собственные преобразования и низкоуровневые вызовы вручную.
- [OpenAPI HTTP-сервер](openapi-http-server.md) перед [OpenAPI HTTP-клиентом](openapi-http-client.md), потому что сгенерированному клиенту нужен сгенерированный контракт сервера.
- [Шаблоны отказоустойчивости](resilient.md), чтобы сделать исходящие вызовы безопаснее при медленных или нестабильных сервисах.
- [Наблюдаемость](observability.md), чтобы трассировать и измерять вызовы между сервисами.

## Помощь { #help }

Если вы застряли:

- сравните с [Kora Java HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-app) и [Kora Kotlin HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-app)
- вернитесь к [HTTP-серверу](http-server.md) и запустите серверное приложение перед стартом клиента
- посмотрите [документацию по HTTP-клиенту](../documentation/http-client.md)
- посмотрите [документацию по HTTP-серверу](../documentation/http-server.md)
