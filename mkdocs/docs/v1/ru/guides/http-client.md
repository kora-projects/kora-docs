---
search:
  exclude: true
title: Руководство по HTTP-клиенту
summary: Build a separate Kora application that calls the user endpoints from the HTTP Server guide with declarative clients
tags: http-client, http-server, declarative-client, integration
---

# Руководство по HTTP-клиенту { #http-client-guide }

Это руководство знакомит с декларативными HTTP-клиентами в Kora. В нем рассматривается, как аннотированные Java-интерфейсы описывают исходящие HTTP-вызовы, как JSON-тела запросов и ответов
преобразуются на границе клиента, и как Kora связывает сгенерированную реализацию клиента в отдельный граф приложения. Вы также увидите, как небольшая служба оборачивает транспортный клиент, чтобы код
приложения оставался сосредоточен на сценариях использования, а не на HTTP-деталях.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-app).

## Что вы создадите { #youll-build }

Вы создадите второе приложение Kora, которое:

- объявляет типизированный `UserApiClient`
- вызывает конечные точки `/users` из руководства по HTTP-серверу
- открывает одну агрегирующую конечную точку `POST /client/test-all-user-endpoints` для удобной ручной проверки
- также может тестироваться на контейнеризованной копии серверного приложения

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- Docker Desktop или другое локальное Docker-окружение для тестов на основе контейнеров
- текстовый редактор или среда разработки
- два терминала, если вы хотите запускать сервер и клиент вручную

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по HTTP-серверу"

    Это руководство предполагает, что вы уже прошли **[руководство по HTTP-серверу](http-server.md)** и понимаете конечные точки пользовательского CRUD API.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь создается отдельное клиентское приложение, которое вызывает уже существующий API.

## Обзор { #overview }

[HTTP](https://www.rfc-editor.org/rfc/rfc9110)-клиент - это исходящая граница приложения. Он представляет API другой службы внутри вашей кодовой базы. Модель декларативного клиента Kora позволяет
описать этот удаленный API как Java- или Kotlin-интерфейс вместо ручной сборки URL, заголовков, тел запросов и логики разбора ответов.

Это похоже на то, как контроллер описывает входящий HTTP API, но направление обратное. Контроллер адаптирует входящие HTTP-запросы в вызовы приложения. Клиент адаптирует вызовы приложения в исходящие
HTTP-запросы.

### Декларативные клиенты { #declarative-clients }

Подробную модель декларативных клиентов, `@HttpClient`, маршрутов и конфигурации смотрите в разделе [декларативного HTTP-клиента](../documentation/http-client.md#client-declarative).

Декларативные клиенты используют ту же общую идею, что и серверные контроллеры, но в обратном направлении:

- аннотации методов описывают удаленный HTTP-метод и путь
- параметры становятся переменными пути, параметрами запроса или JSON-телами
- возвращаемые типы описывают ожидаемый ответ
- Kora создает реализацию во время компиляции

В результате получается типизированный клиент, который можно внедрять как любой другой компонент Kora.

### Транспортная граница и служба приложения { #transport-boundary-application-service }

Сгенерированные клиенты ориентированы на транспорт. Они знают, как вызывать HTTP-конечные точки, но не должны сами определять каждый сценарий использования приложения. В этом руководстве
сгенерированный клиент оборачивается небольшой службой, чтобы остальная часть приложения могла вызывать методы, соответствующие бизнес-намерению, а не сырым транспортным деталям.

Такая обертка также является правильным местом для обработки ошибок на уровне приложения, повторов в последующих руководствах или небольших преобразований между внешними DTO и внутренними моделями.

### Конфигурация и вызовы { #configuration-calls }

HTTP-клиенту также нужна конфигурация времени выполнения: базовый URL, тайм-ауты и другие транспортные настройки. Kora хранит эти настройки в конфигурации и связывает настроенный клиент с графом
зависимостей. Так код остается стабильным при локальной разработке, в тестах и в настоящих окружениях.

Практический ход такой:

1. описать удаленный API как аннотированный интерфейс
2. настроить цель клиента в HOCON
3. позволить Kora сгенерировать и внедрить реализацию
4. обернуть сгенерированный клиент в службу приложения
5. открыть локальные маршруты, которые выполняют исходящие вызовы

## Зависимости { #dependencies }

Клиентскому приложению нужны:

- зависимости HTTP-клиента, чтобы Kora могла генерировать и запускать декларативные клиенты
- зависимости HTTP-сервера, потому что это клиентское приложение все равно открывает собственную небольшую конечную точку для проверки

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    dependencies {
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-ok")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-ok")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

## Модули { #modules }

Мы используем:

- `HoconConfigModule` для `application.conf`
- `JsonModule` для сериализации запросов и ответов
- `LogbackModule` для журналов
- `OkHttpClientModule` для сгенерированных клиентов
- `UndertowHttpServerModule`, потому что это клиентское приложение открывает собственную конечную точку

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/Application.java"
    package ru.tinkoff.kora.guide.httpclient;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.client.ok.OkHttpClientModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            OkHttpClientModule,  // <----- Подключили модуль
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/Application.kt"
    package ru.tinkoff.kora.guide.httpclient

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.client.ok.OkHttpClientModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        OkHttpClientModule,  // <----- Подключили модуль
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## DTO-модели { #dto-models }

Первое понятие клиента вообще не является специфичным для клиента: клиенту по-прежнему нужны те же формы данных, которые сервер отправляет и получает.

Поэтому мы начинаем с переиспользования того же договора `UserRequest` и `UserResponse` из серверного руководства. Это сохраняет клиент и сервер согласованными и дает сгенерированному клиенту
типизированный интерфейс для работы.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/dto/UserRequest.java"
    package ru.tinkoff.kora.guide.httpclient.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/dto/UserResponse.java"
    package ru.tinkoff.kora.guide.httpclient.dto;

    import java.time.LocalDateTime;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/dto/UserRequest.kt"
    package ru.tinkoff.kora.guide.httpclient.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class UserRequest(val name: String, val email: String)
    ```

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/dto/UserResponse.kt"
    package ru.tinkoff.kora.guide.httpclient.dto

    import java.time.LocalDateTime
    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

## HTTP-клиент { #http-client }

Теперь мы описываем удаленный HTTP API как интерфейс.

Это ключевая абстракция руководства. Вместо написания императивного клиентского кода мы объявляем удаленный договор с помощью аннотаций:

- `@HttpClient`, чтобы пометить весь интерфейс как декларативный клиент
- `@HttpRoute`, чтобы описать удаленный метод и путь
- `@Path`, `@Query`, `@Header` и `@Cookie`, чтобы сопоставить отдельные аргументы
- `@Json`, чтобы указать, что для тела должны использоваться JSON-преобразователи

Этот интерфейс повторяет пользовательские конечные точки из `http-server.md`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/UserApiClient.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.guide.httpclient.dto.UserRequest;
    import ru.tinkoff.kora.guide.httpclient.dto.UserResponse;
    import ru.tinkoff.kora.http.client.common.annotation.HttpClient;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.HttpResponseEntity;
    import ru.tinkoff.kora.http.common.annotation.Cookie;
    import ru.tinkoff.kora.http.common.annotation.Header;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.common.annotation.Query;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @HttpClient(configPath = "httpClient.userApi")
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
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/UserApiClient.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import ru.tinkoff.kora.guide.httpclient.dto.UserRequest
    import ru.tinkoff.kora.guide.httpclient.dto.UserResponse
    import ru.tinkoff.kora.http.client.common.annotation.HttpClient
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.HttpResponseEntity
    import ru.tinkoff.kora.http.common.annotation.Cookie
    import ru.tinkoff.kora.http.common.annotation.Header
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.common.annotation.Query
    import ru.tinkoff.kora.json.common.annotation.Json

    @HttpClient(configPath = "httpClient.userApi")
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
    }
    ```

## Конфигурация { #config }

Это приложение является самостоятельной службой Kora, поэтому ему нужны собственные порты.

Мы будем использовать:

- `8080` для серверного приложения из `http-server.md`
- `8081` для открытого API клиентского приложения
- `8086` для закрытого API клиентского приложения
- `httpClient.userApi.url` как базовый URL для сгенерированного клиента

Полный справочник по конфигурации смотрите в разделах [HTTP-сервер](../documentation/http-server.md), [HTTP-клиент](../documentation/http-client.md)
и [Журналирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      userApiHttpPort = 8081 //(1)!
      privateApiHttpPort = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    httpClient {
      userApi {
        url = "http://localhost:8080" //(4)!
        url = ${?USER_API_URL} //(5)!
        requestTimeout = 10s //(6)!
      }
      telemetry.logging.enabled = true //(7)!
    }

    logging {
      levels {
        "ROOT": "INFO" //(8)!
        "ru.tinkoff.kora": "INFO" //(9)!
      }
    }
    ```

    1. Именованный открытый HTTP-порт, который использует локальная конечная точка руководства.
    2. Закрытый HTTP-порт по умолчанию, который используют пробы, метрики и управляющие конечные точки.
    3. Включает возможность для этого раздела конфигурации.
    4. Базовый URL, который использует настроенный клиент.
    5. Базовый URL, который использует настроенный клиент. Необязательное переопределение из `USER_API_URL`.
    6. Максимальное время, разрешенное для клиентского запроса.
    7. Включает возможность для этого раздела конфигурации.
    8. Уровень журналирования для `ROOT`.
    9. Уровень журналирования для `ru.tinkoff.kora`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      userApiHttpPort: 8081 #(1)!
      privateApiHttpPort: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    httpClient:
      userApi:
        url: ${?USER_API_URL:"http://localhost:8080"} #(4)!
        requestTimeout: 10s #(5)!
      telemetry:
        logging:
          enabled: true #(6)!
    logging:
      levels:
        ROOT: "INFO" #(7)!
        "ru.tinkoff.kora": "INFO" #(8)!
    ```

    1. Именованный открытый HTTP-порт, который использует локальная конечная точка руководства.
    2. Закрытый HTTP-порт по умолчанию, который используют пробы, метрики и управляющие конечные точки.
    3. Включает возможность для этого раздела конфигурации.
    4. Базовый URL, который использует настроенный клиент. Использует показанное значение по умолчанию и позволяет `USER_API_URL` переопределить его.
    5. Максимальное время, разрешенное для клиентского запроса.
    6. Включает возможность для этого раздела конфигурации.
    7. Уровень журналирования для `ROOT`.
    8. Уровень журналирования для `ru.tinkoff.kora`.

Необязательное переопределение `USER_API_URL` особенно полезно в тестах, где целевой сервер может работать внутри контейнера на случайно сопоставленном порту.

## Контроллер проверки { #check-controller }

Клиентскому приложению не нужно снова повторять весь сервер. Для этого у нас уже есть серверное приложение. Вместо этого мы открываем один небольшой контроллер, который выполняет полный сценарий через
сгенерированный клиент.

Это полезно по двум причинам:

- дает одну ручную конечную точку, которую можно вызвать во время обучения
- сохраняет сгенерированные клиентские интерфейсы главной темой руководства

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/controller/ClientTestController.java"
    package ru.tinkoff.kora.guide.httpclient.controller;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpclient.client.UserApiClient;
    import ru.tinkoff.kora.guide.httpclient.dto.UserRequest;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

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

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/controller/ClientTestController.kt"
    package ru.tinkoff.kora.guide.httpclient.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpclient.client.UserApiClient
    import ru.tinkoff.kora.guide.httpclient.dto.UserRequest
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

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

## Проверка приложения { #check-app }

Если вы хотите проверить сценарий вручную, запустите оба приложения в отдельных терминалах.

### Терминал 1: сервер { #terminal-1-server }

```bash
./gradlew clean classes
./gradlew run
```

Серверное приложение должно открыть свой открытый API на `http://localhost:8080`.

### Терминал 2: клиент { #terminal-2-client }

```bash
./gradlew clean classes
./gradlew run
```

Клиентское приложение должно открыть свой открытый API на `http://localhost:8081`.

### Клиентский сценарий { #client-scenario }

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

Ожидаемый результат: JSON-объект, где `allTestsPassed` равен `true`.

## Лучшие практики { #best-practices }

- Держите клиентские интерфейсы небольшими и организованными по областям удаленного API.
- Переиспользуйте DTO-договор из серверного руководства, где это возможно, чтобы клиент и сервер оставались согласованными.
- Предпочитайте `HttpResponseEntity<T>` только тогда, когда нужны коды статуса или заголовки; иначе возвращайте DTO напрямую.
- Используйте один небольшой агрегирующий контроллер для ручных учебных сценариев вместо повторного создания всего сервера внутри клиентского приложения.
- Добавляйте продвинутые возможности клиента только тогда, когда базовый договор уже легко понять.

## Итоги { #summary }

Вы создали самостоятельное клиентское приложение Kora, которое использует пользовательский API из руководства по HTTP-серверу.

По пути вы:

- переиспользовали серверный DTO-договор
- объявили `UserApiClient`, сгенерированный во время компиляции
- настроили удаленный базовый URL
- открыли одну агрегирующую конечную точку для удобной ручной проверки

## Ключевые понятия { #key-concepts }

- `@HttpClient(configPath = ...)` связывает декларативный клиент с конкретным разделом конфигурации
- `@HttpRoute`, `@Path`, `@Query`, `@Header` и `@Cookie` типобезопасно описывают удаленный договор
- `HttpResponseEntity<T>` полезен, когда нужны и тело, и HTTP-метаданные
- одного небольшого агрегирующего контроллера достаточно для базового учебного клиентского приложения

## Устранение неполадок { #troubleshooting }

**Клиент не может подключиться к серверу:**

- Убедитесь, что серверное приложение запущено на `8080` для ручных проверок
- Убедитесь, что `httpClient.userApi.url` указывает на настоящий URL сервера
- Если вы переопределяете `USER_API_URL`, убедитесь, что он все еще указывает на открытый API серверного приложения

**Сборка Gradle зависает или удерживает файловые блокировки в Windows:**

- Запустите `./gradlew --stop` и повторите попытку
- Если видите `AccessDeniedException` вокруг кеша Gradle или каталогов `build/`, закройте запущенные Java-процессы, терминалы или редакторы, которые все еще удерживают файловые дескрипторы

**Журналы телеметрии клиента слишком шумные:**

- Отключите или настройте `httpClient.telemetry.logging.enabled` в `application.conf`, когда закончите отладку

**Проверки готовности закрытого API не работают:**

- В этом руководстве `8086` используется как порт закрытого API клиентского приложения, чтобы он не пересекался с портами серверного приложения
- Стандартный путь готовности - `/system/readiness`
- Если меняете любое из этих значений, согласованно обновите стратегию ожидания и примечания по устранению неполадок

## Что дальше? { #whats-next }

- [Продвинутый HTTP-сервер](http-server-advanced.md), если хотите подготовить продвинутые серверные маршруты, которые используются в продвинутом руководстве по клиенту.
- [Продвинутый HTTP-клиент](http-client-advanced.md) после продвинутого HTTP-сервера, чтобы добавить формы, multipart, перехватчики, пользовательское преобразование и ручные низкоуровневые вызовы.
- [OpenAPI HTTP-сервер](openapi-http-server.md) перед [OpenAPI HTTP-клиентом](openapi-http-client.md), потому что сгенерированному клиенту нужен сгенерированный серверный договор.
- [Шаблоны устойчивости](resilient.md), чтобы сделать исходящие вызовы безопаснее при медленных или нестабильных службах.
- [Наблюдаемость](observability.md), чтобы трассировать и измерять вызовы между службами.

## Помощь { #help }

Если застряли:

- сравните с [Kora Java HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-app) и [Kora Kotlin HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-app)
- вернитесь к [HTTP-серверу](http-server.md) и запустите серверное приложение перед запуском клиента
- проверьте [документацию HTTP-клиента](../documentation/http-client.md)
- проверьте [документацию HTTP-сервера](../documentation/http-server.md)
