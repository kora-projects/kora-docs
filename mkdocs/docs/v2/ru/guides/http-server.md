---
search:
  exclude: true
title: Руководство по HTTP-серверу
summary: Learn how to build your first Kora HTTP API step by step, from one controller method to a full CRUD service
description: "Step-by-step Kora HTTP API: the io.koraframework:http-server-undertow module, UndertowPublicHttpServerModule, @HttpController and @HttpRoute routes, @Json request and response bodies, @Path and @Query binding, HttpResponseEntity and HttpServerResponse, HttpServerResponseException errors, a controller-service-repository split and the httpServer.port / httpServer.system.port configuration."
agent:
  use_when: "Use this file for questions about building a Kora REST API step by step: @HttpController, @HttpRoute, @Path, @Query, @Json DTOs, HttpResponseEntity, HttpServerResponse, HttpServerResponseException, UndertowPublicHttpServerModule, io.koraframework:http-server-undertow and json-common dependencies, httpServer.port and httpServer.system.port, readiness and liveness probes, and splitting a controller from a service and a repository."
tags: http-server, rest-api, json, routing, beginner
---

# Руководство по HTTP-серверу { #http-server-guide }

Это руководство знакомит с основным процессом создания HTTP API в Kora. В нем разбирается, как `@HttpController` и `@HttpRoute` превращают обычные методы в HTTP-конечные точки, как `@Json`, `@Path`
и `@Query` связывают запросы с типизированным кодом приложения, и как явные API ответов и исключений дают каждому маршруту понятное HTTP-поведение. Вы также увидите, как граф зависимостей Kora,
собираемый во время компиляции, соединяет контроллеры, прикладные сервисы, репозитории, преобразователи JSON, конфигурацию и сервер Undertow в одно запускаемое приложение.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-server-app).

## Что вы создадите { #youll-build }

К концу руководства у вас будет:

- `UserController` с CRUD-маршрутами
- DTO запроса и ответа
- `UserRepository` в памяти
- `UserService` с прикладной логикой
- публичный API на порту `8080`
- системный API на порту `8085`

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Текстовый редактор или IDE
- Пройденное руководство [Работа с JSON в Kora](json.md)

Артефакты Kora 2.0 собраны под Java 25, поэтому JDK, которым компилируется приложение, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Необходимая база"

    Руководство предполагает, что вы прошли **[Работа с JSON в Kora](json.md)** и у вас есть рабочий проект Kora с настроенным маппингом JSON-DTO.

    Если руководство по JSON еще не пройдено, начните с него: оно уже опирается на вводное руководство и дает этому HTTP API нужные приемы сериализации JSON.

## Обзор { #overview }

HTTP-серверы Kora ([HTTP](https://www.rfc-editor.org/rfc/rfc9110)) построены на простой идее: обычные методы становятся HTTP-конечными точками, если их транспортный контракт описан явно. Вы пишете
классы-контроллеры, размечаете маршруты и параметры аннотациями, а Kora генерирует код обработки запроса во время компиляции.

Это значит, что HTTP API в Kora строится не из низкоуровневого разбора запроса, а из типизированных сигнатур методов и аннотаций, которые описывают, как HTTP-данные отображаются на код приложения.

### Контроллеры как транспортные адаптеры { #controllers-transport-adapters }

Контроллер — это HTTP-граница приложения. Он должен разбираться в маршрутах, телах запросов, переменных пути, параметрах строки запроса, кодах статуса и заголовках. Он не должен навсегда становиться
местом, где живут все правила хранения и бизнес-логики. Поэтому руководство постепенно разделяет ответственность контроллера, сервиса и репозитория.

Аннотации Kora описывают, как HTTP-данные попадают в методы контроллера и выходят из них:

- `@HttpController` помечает класс как HTTP-контроллер
- `@HttpRoute` объявляет HTTP-метод и путь
- `@Json` связывает JSON-тела запроса и ответа
- `@Path` отображает плейсхолдеры маршрута в параметры метода
- `@Query` отображает значения строки запроса в параметры метода

Обработка запросов **синхронная**. Undertow отправляет каждый запрос на виртуальный поток до того, как сгенерированный обработчик вызовет ваш метод, поэтому метод контроллера может свободно
блокироваться: он возвращает результат напрямую и никогда не возвращает `CompletionStage`, `Mono`/`Flux` или `suspend`-функцию.

### Явное HTTP-поведение { #explicit-http-behavior }

Простые методы могут возвращать DTO напрямую, но реальным API часто нужен больший контроль. `HttpResponseEntity<T>` позволяет вернуть тело вместе с конкретным кодом статуса или заголовками.
`HttpServerResponse` удобен для ответов без JSON-тела, например `204 No Content`. `HttpServerResponseException` дает прямой способ завершить запрос понятной HTTP-ошибкой.

Эти типы оставляют HTTP-поведение видимым в контроллере, а не прячут коды статуса внутри посторонней логики сервисов.

### Слои приложения { #application-layers }

Руководство начинается с одного метода контроллера, а затем выделяет хранение и прикладную логику в отдельные обязанности. Репозиторий владеет доступом к данным. Сервис владеет прикладным поведением.
Контроллер владеет HTTP-представлением. Разделение намеренно небольшое, но это та же форма, которую переиспользуют последующие руководства по базам данных, валидации, кэшированию, отказоустойчивости
и наблюдаемости.

Практический порядок такой:

1. подключить модули HTTP-сервера и JSON
2. создать DTO запроса и ответа
3. открыть первый JSON-маршрут
4. добавить маппинг параметров пути и строки запроса
5. ввести слои репозитория и сервиса
6. возвращать явные статусы, заголовки и HTTP-ошибки

## Зависимости { #dependencies }

HTTP-сервер живет в модуле `http-server-undertow`, а поддержка JSON — в `json-common`. Оба модуля относятся к Kora, поэтому их версии берутся из платформы `io.koraframework:kora-bom`, а не пишутся
в каждой строке.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    dependencies {
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1") //(1)!

        annotationProcessor "io.koraframework:annotation-processors" //(2)!

        implementation "io.koraframework:config-hocon" //(3)!
        implementation "io.koraframework:http-server-undertow" //(4)!
        implementation "io.koraframework:json-common" //(5)!
        implementation "io.koraframework:logging-logback" //(6)!
    }
    ```

    1.  Kora BOM: согласует версии всех модулей Kora и библиотек, от которых зависит Kora.
    2.  Аннотационный процессор Kora: генерирует граф приложения, модули контроллеров и JSON-читатели/писатели во время компиляции.
    3.  Чтение конфигурации HOCON из `application.conf`.
    4.  Транспорт HTTP-сервера Undertow.
    5.  Инфраструктура JSON времени компиляции.
    6.  Реализация логирования Logback, встроенная в граф Kora.

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1")) //(1)!

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

        implementation("io.koraframework:config-hocon") //(3)!
        implementation("io.koraframework:http-server-undertow") //(4)!
        implementation("io.koraframework:json-common") //(5)!
        implementation("io.koraframework:logging-logback") //(6)!
    }
    ```

    1.  Kora BOM: согласует версии всех модулей Kora и библиотек, от которых зависит Kora.
    2.  KSP-процессор Kora: генерирует граф приложения, модули контроллеров и JSON-читатели/писатели во время компиляции.
    3.  Чтение конфигурации HOCON из `application.conf`.
    4.  Транспорт HTTP-сервера Undertow.
    5.  Инфраструктура JSON времени компиляции.
    6.  Реализация логирования Logback, встроенная в граф Kora.

## Модули { #modules }

`UndertowPublicHttpServerModule` — модуль, который нужно подключить приложению с бизнес-эндпоинтами. Он наследует `UndertowSystemHttpServerModule`, поэтому одно наследование дает сразу два сервера
в одном процессе: публичный на `httpServer.port` и системный на `httpServer.system.port`, который отвечает на запросы readiness, liveness и метрик.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/io/koraframework/guide/httpserver/Application.java`:

    ```java
    package io.koraframework.guide.httpserver;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/io/koraframework/guide/httpserver/Application.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## DTO { #dto }

Прежде чем добавлять маршрут, нужно описать формы данных, которые мы хотим принимать и возвращать.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/httpserver/dto/UserRequest.java`:

    ```java
    package io.koraframework.guide.httpserver.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    Создайте `src/main/java/io/koraframework/guide/httpserver/dto/UserResponse.java`:

    ```java
    package io.koraframework.guide.httpserver.dto;

    import java.time.LocalDateTime;
    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/httpserver/dto/UserRequest.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserRequest(
        val name: String,
        val email: String
    )
    ```

    Создайте `src/main/kotlin/io/koraframework/guide/httpserver/dto/UserResponse.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.dto

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

`UserRequest` описывает входящий JSON от клиента.

`UserResponse` описывает JSON, который ваш API отдает обратно.

Начинать с DTO удобно: сигнатура контроллера сразу получает стабильные именованные типы вместо безымянных словарей и «сырых» строк.

## Создание пользователя { #create-user }

Теперь создадим первый контроллер и первый маршрут. На этом шаге мы **ничего** не сохраняем. Цель — понять, как Kora отображает HTTP-запрос на метод контроллера.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/httpserver/controller/UserController.java`:

    ```java
    package io.koraframework.guide.httpserver.controller;

    import java.time.LocalDateTime;
    import java.util.UUID;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(@Json UserRequest request) {
            System.out.printf("Received createUser request: name=%s, email=%s%n", request.name(), request.email());
            return new UserResponse(
                    UUID.randomUUID().toString(),
                    request.name(),
                    request.email(),
                    LocalDateTime.now());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/httpserver/controller/UserController.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json
    import java.time.LocalDateTime
    import java.util.UUID

    @Component
    @HttpController
    class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): UserResponse {
            println("Received createUser request: name=${request.name}, email=${request.email}")
            return UserResponse(
                UUID.randomUUID().toString(),
                request.name,
                request.email,
                LocalDateTime.now()
            )
        }
    }
    ```

Разберем, что здесь происходит:

- `@Component`
  Kora должна создать этот класс и поместить его в граф зависимостей.

- `@HttpController`
  Класс содержит HTTP-маршруты. Kora сканирует его и генерирует обвязку HTTP-обработчиков.

- `@HttpRoute(method = HttpMethod.POST, path = "/users")`
  Метод обрабатывает `POST /users`. В `HttpMethod` лежат стандартные имена HTTP-методов в виде строковых констант.

- `@Json` на методе
  Kora использует преобразователь данных со специальным тегом `@Json`, чтобы сериализовать возвращаемое значение в JSON.

- `@Json` на параметре
  Kora использует преобразователь данных со специальным тегом `@Json`, чтобы десериализовать тело запроса из JSON в `UserRequest`.

На этом этапе маршрут уже похож на настоящий API, но он ничего не запоминает. Каждый вызов создает новый объект ответа и сразу его возвращает.

Проверьте:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

## Получение пользователя { #get-user }

Следующий естественный маршрут — `getUser`. Но как только мы его добавляем, возникает важный вопрос проектирования: где живут пользователи после того, как `createUser` вернул ответ?

Пока что добавим маршрут и намеренно вернем `404`, чтобы показать, что контроллер уже умеет выражать отказ на уровне HTTP.

===! ":fontawesome-brands-java: `Java`"

    Обновите `UserController.java`:

    ```java
    package io.koraframework.guide.httpserver.controller;

    import java.time.LocalDateTime;
    import java.util.UUID;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(@Json UserRequest request) {
            System.out.printf("Received createUser request: name=%s, email=%s%n", request.name(), request.email());
            return new UserResponse(
                    UUID.randomUUID().toString(),
                    request.name(),
                    request.email(),
                    LocalDateTime.now());
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        public UserResponse getUser(@Path String userId) {
            throw HttpServerResponseException.of(404, "User not found: " + userId);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `UserController.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.json.common.annotation.Json
    import java.time.LocalDateTime
    import java.util.UUID

    @Component
    @HttpController
    class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): UserResponse {
            println("Received createUser request: name=${request.name}, email=${request.email}")
            return UserResponse(
                UUID.randomUUID().toString(),
                request.name,
                request.email,
                LocalDateTime.now()
            )
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(@Path userId: String): UserResponse {
            throw HttpServerResponseException.of(404, "User not found: $userId")
        }
    }
    ```

Здесь появляются две новые идеи:

- `@Path String userId`
  Kora берет часть `{userId}` из пути маршрута и передает ее в метод.

- `HttpServerResponseException`
  Простой способ сказать «этот запрос должен завершиться такой HTTP-ошибкой». Само исключение является `HttpServerResponse`, поэтому сервер пишет его статус и тело без дополнительного преобразования.

Шаг намеренно неполный. Теперь поведения контроллера достаточно, чтобы увидеть, зачем нужна отдельная абстракция хранения.

## Репозиторий пользователей { #user-repository }

Теперь добавим слой репозитория. Репозиторий отвечает за сохранение и получение данных. В этом руководстве используется словарь в памяти — так пример проще запускать, — но сама абстракция позже
позволит перейти на настоящую базу данных.

Сначала нужны всего две операции:

- сохранить пользователя
- получить пользователя по ID

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/httpserver/repository/UserRepository.java`:

    ```java
    package io.koraframework.guide.httpserver.repository;

    import java.util.Optional;
    import io.koraframework.guide.httpserver.dto.UserResponse;

    public interface UserRepository {

        String save(String name, String email);

        Optional<UserResponse> findById(String id);
    }
    ```

    Создайте `src/main/java/io/koraframework/guide/httpserver/repository/InMemoryUserRepository.java`:

    ```java
    package io.koraframework.guide.httpserver.repository;

    import java.time.LocalDateTime;
    import java.util.Map;
    import java.util.Optional;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserResponse;

    @Component
    public final class InMemoryUserRepository implements UserRepository {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();
        private final AtomicLong idGenerator = new AtomicLong(1);

        @Override
        public String save(String name, String email) {
            String id = String.valueOf(idGenerator.getAndIncrement());
            users.put(id, new UserResponse(id, name, email, LocalDateTime.now()));
            return id;
        }

        @Override
        public Optional<UserResponse> findById(String id) {
            return Optional.ofNullable(users.get(id));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/httpserver/repository/UserRepository.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.repository

    import io.koraframework.guide.httpserver.dto.UserResponse

    interface UserRepository {
        fun save(name: String, email: String): String
        fun findById(id: String): UserResponse?
    }
    ```

    Создайте `src/main/kotlin/io/koraframework/guide/httpserver/repository/InMemoryUserRepository.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.repository

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserResponse
    import java.time.LocalDateTime
    import java.util.concurrent.ConcurrentHashMap
    import java.util.concurrent.atomic.AtomicLong

    @Component
    class InMemoryUserRepository : UserRepository {

        private val users = ConcurrentHashMap<String, UserResponse>()
        private val idGenerator = AtomicLong(1)

        override fun save(name: String, email: String): String {
            val id = idGenerator.getAndIncrement().toString()
            users[id] = UserResponse(id, name, email, LocalDateTime.now())
            return id
        }

        override fun findById(id: String): UserResponse? = users[id]
    }
    ```

Репозиторий ничего не знает про HTTP. Он умеет только сохранять и загружать данные пользователя. Это разделение важно, потому что задачи хранения и задачи HTTP меняются по разным причинам.

Поскольку каждый запрос выполняется на своем виртуальном потоке, хранилище в памяти — это разделяемое состояние: `ConcurrentHashMap` и `AtomicLong` выбраны намеренно вместо небезопасных аналогов.

## Контроллер к репозиторию { #controller-repository }

Теперь, когда есть хранилище, вернемся к контроллеру и заставим `createUser` и `getUser` работать вместе.

===! ":fontawesome-brands-java: `Java`"

    Обновите `UserController.java`:

    ```java
    package io.koraframework.guide.httpserver.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.guide.httpserver.repository.UserRepository;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class UserController {

        private final UserRepository userRepository;

        public UserController(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(@Json UserRequest request) {
            String id = userRepository.save(request.name(), request.email());
            return userRepository.findById(id)
                    .orElseThrow(() -> new IllegalStateException("Saved user not found"));
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        public UserResponse getUser(@Path String userId) {
            return userRepository.findById(userId)
                    .orElseThrow(() -> HttpServerResponseException.of(404, "User not found: " + userId));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `UserController.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.guide.httpserver.repository.UserRepository
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.json.common.annotation.Json

    @Component
    @HttpController
    class UserController(
        private val userRepository: UserRepository
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): UserResponse {
            val id = userRepository.save(request.name, request.email)
            return userRepository.findById(id)
                ?: error("Saved user not found")
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(@Path userId: String): UserResponse {
            return userRepository.findById(userId)
                ?: throw HttpServerResponseException.of(404, "User not found: $userId")
        }
    }
    ```

Это первый момент, когда API становится stateful. Теперь можно вызвать `createUser`, получить ID и использовать его в `getUser`.

`UserRepository` — интерфейс, а `InMemoryUserRepository` — реализующий его `@Component`. Контроллер запрашивает в конструкторе интерфейс, и Kora разрешает это ребро графа во время компиляции: если бы
реализации не было, сборка упала бы с `No component found for dependency`, а не в рантайме.

## CRUD репозиторий { #crud-repository }

API уже умеет создавать и получать. Прежде чем добавлять новые HTTP-маршруты, сделаем абстракцию хранения способной на полный CRUD:

- список пользователей
- обновление пользователей
- удаление пользователей

Так репозиторий остается сосредоточен только на операциях хранения. Контроллер начнет использовать эти операции в следующем разделе, после того как между HTTP-маршрутизацией и хранением появится
сервисный слой.

===! ":fontawesome-brands-java: `Java`"

    Расширьте `UserRepository.java`:

    ```java
    package io.koraframework.guide.httpserver.repository;

    import java.util.List;
    import java.util.Optional;
    import io.koraframework.guide.httpserver.dto.UserResponse;

    public interface UserRepository {

        List<UserResponse> findAll();

        Optional<UserResponse> findById(String id);

        String save(String name, String email);

        boolean update(String id, String name, String email);

        boolean deleteById(String id);
    }
    ```

    Расширьте `InMemoryUserRepository.java`:

    ```java
    package io.koraframework.guide.httpserver.repository;

    import java.time.LocalDateTime;
    import java.util.ArrayList;
    import java.util.List;
    import java.util.Map;
    import java.util.Optional;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserResponse;

    @Component
    public final class InMemoryUserRepository implements UserRepository {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();
        private final AtomicLong idGenerator = new AtomicLong(1);

        @Override
        public List<UserResponse> findAll() {
            return new ArrayList<>(users.values());
        }

        @Override
        public Optional<UserResponse> findById(String id) {
            return Optional.ofNullable(users.get(id));
        }

        @Override
        public String save(String name, String email) {
            String id = String.valueOf(idGenerator.getAndIncrement());
            users.put(id, new UserResponse(id, name, email, LocalDateTime.now()));
            return id;
        }

        @Override
        public boolean update(String id, String name, String email) {
            return users.computeIfPresent(id,
                    (k, v) -> new UserResponse(k, name, email, v.createdAt())) != null;
        }

        @Override
        public boolean deleteById(String id) {
            return users.remove(id) != null;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Расширьте `UserRepository.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.repository

    import io.koraframework.guide.httpserver.dto.UserResponse

    interface UserRepository {
        fun findAll(): List<UserResponse>
        fun findById(id: String): UserResponse?
        fun save(name: String, email: String): String
        fun update(id: String, name: String, email: String): Boolean
        fun deleteById(id: String): Boolean
    }
    ```

    Расширьте `InMemoryUserRepository.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.repository

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserResponse
    import java.time.LocalDateTime
    import java.util.concurrent.ConcurrentHashMap
    import java.util.concurrent.atomic.AtomicLong

    @Component
    class InMemoryUserRepository : UserRepository {

        private val users = ConcurrentHashMap<String, UserResponse>()
        private val idGenerator = AtomicLong(1)

        override fun findAll(): List<UserResponse> = users.values.toList()

        override fun findById(id: String): UserResponse? = users[id]

        override fun save(name: String, email: String): String {
            val id = idGenerator.getAndIncrement().toString()
            users[id] = UserResponse(id, name, email, LocalDateTime.now())
            return id
        }

        override fun update(id: String, name: String, email: String): Boolean {
            return users.computeIfPresent(id) { key, current -> UserResponse(key, name, email, current.createdAt) } != null
        }

        override fun deleteById(id: String): Boolean = users.remove(id) != null
    }
    ```

На этом этапе репозиторий умеет сохранять, перечислять, обновлять и удалять пользователей, но HTTP API по-прежнему открывает только маршруты из предыдущего раздела. Дальше добавим сервисный слой,
а затем подключим к контроллеру полное CRUD-поведение.

## Сервисный слой { #service-layer }

Во многих приложениях контроллер считают слоем представления, а прикладная логика живет в сервисном слое. Это особенно характерно для приложений в стиле MVC и для сервисов, которые со временем
обрастают правилами, интеграциями и точками переиспользования.

В репозитории уже есть все операции хранения, нужные API. Сервисный слой превращает их в прикладное поведение:

- создает пользователей из DTO запроса
- сортирует и разбивает на страницы список из памяти
- превращает результаты обновления и удаления в бизнес-ошибки

После этого контроллер может сосредоточиться на HTTP-маршрутизации, связывании запроса, кодах ответа и заголовках.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/httpserver/service/UserService.java`:

    ```java
    package io.koraframework.guide.httpserver.service;

    import java.time.LocalDateTime;
    import java.util.Comparator;
    import java.util.List;
    import java.util.Optional;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.guide.httpserver.repository.UserRepository;
    import io.koraframework.http.server.common.response.HttpServerResponseException;

    @Component
    public final class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        public UserResponse createUser(UserRequest request) {
            var generatedId = userRepository.save(request.name(), request.email());
            return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        }

        public Optional<UserResponse> getUser(String id) {
            return userRepository.findById(id);
        }

        public List<UserResponse> getUsers(int page, int size, String sort) {
            return userRepository.findAll().stream()
                    .sorted(getComparator(sort))
                    .skip((long) page * size)
                    .limit(size)
                    .toList();
        }

        public UserResponse updateUser(String id, UserRequest request) {
            boolean updated = userRepository.update(id, request.name(), request.email());
            if (!updated) {
                throw HttpServerResponseException.of(404, "User not found: " + id);
            }
            return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
        }

        public void deleteUser(String id) {
            boolean deleted = userRepository.deleteById(id);
            if (!deleted) {
                throw HttpServerResponseException.of(404, "User not found: " + id);
            }
        }

        private Comparator<UserResponse> getComparator(String sort) {
            return switch (sort.toLowerCase()) {
                case "name" -> Comparator.comparing(UserResponse::name);
                case "email" -> Comparator.comparing(UserResponse::email);
                case "createdat" -> Comparator.comparing(UserResponse::createdAt);
                default -> Comparator.comparing(UserResponse::name);
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/httpserver/service/UserService.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.guide.httpserver.repository.UserRepository
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import java.time.LocalDateTime

    @Component
    class UserService(
        private val userRepository: UserRepository
    ) {

        fun createUser(request: UserRequest): UserResponse {
            val generatedId = userRepository.save(request.name, request.email)
            return UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
        }

        fun getUser(id: String): UserResponse? = userRepository.findById(id)

        fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> =
            userRepository.findAll()
                .sortedWith(getComparator(sort))
                .drop(page * size)
                .take(size)

        fun updateUser(id: String, request: UserRequest): UserResponse {
            if (!userRepository.update(id, request.name, request.email)) {
                throw HttpServerResponseException.of(404, "User not found: $id")
            }
            return UserResponse(id, request.name, request.email, LocalDateTime.now())
        }

        fun deleteUser(id: String) {
            if (!userRepository.deleteById(id)) {
                throw HttpServerResponseException.of(404, "User not found: $id")
            }
        }

        private fun getComparator(sort: String): Comparator<UserResponse> = when (sort.lowercase()) {
            "name" -> compareBy { it.name }
            "email" -> compareBy { it.email }
            "createdat" -> compareBy { it.createdAt }
            else -> compareBy { it.name }
        }
    }
    ```

`UserService` бросает `HttpServerResponseException` для «не найдено», чтобы руководство оставалось коротким. В более крупном приложении сервис обычно бросал бы доменное исключение, а один глобальный
перехватчик переводил бы его в HTTP-статус — именно это строит следующее руководство [Продвинутый HTTP-сервер](http-server-advanced.md).

## Контроллер и сервис { #controller-service }

Теперь контроллер может открыть полный CRUD API, не владея ни хранением, ни прикладной логикой. Он принимает HTTP-запросы, связывает параметры маршрута и строки запроса, делегирует работу
`UserService` и выбирает форму HTTP-ответа для каждого маршрута.

На этом шаге добавляются оставшиеся HTTP-специфичные элементы:

- `@Query` отображает значения строки запроса вида `?page=0&size=10&sort=name` в параметры контроллера
- nullable-тип параметра помечает необязательный параметр строки запроса
- `HttpResponseEntity<T>` возвращает JSON-тело вместе с явным кодом статуса или заголовками
- `HttpServerResponse` возвращает ответы без JSON-тела, например `204 No Content`

В Java необязательные параметры помечаются JSpecify-аннотацией `@Nullable` из `org.jspecify.annotations`; в Kotlin достаточно `?` в типе параметра, никакой аннотации не нужно. Параметр `@Query`,
который не является ни nullable, ни `Optional`, считается обязательным, и запрос без него получает `400` еще до вызова метода контроллера.

===! ":fontawesome-brands-java: `Java`"

    Перепишите `UserController.java` так, чтобы он делегировал работу сервису:

    ```java
    package io.koraframework.guide.httpserver.controller;

    import org.jspecify.annotations.Nullable;
    import java.time.Instant;
    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.guide.httpserver.service.UserService;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.HttpResponseEntity;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.common.annotation.Query;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.common.header.HttpHeaders;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponse;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class UserController {

        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        public UserResponse getUser(@Path String userId) {
            return userService.getUser(userId)
                    .orElseThrow(() -> HttpServerResponseException.of(404, "User not found: " + userId));
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        public List<UserResponse> getUsers(
                @Nullable @Query("page") Integer page,
                @Nullable @Query("size") Integer size,
                @Nullable @Query("sort") String sort) {
            int pageNum = page == null ? 0 : page;
            int pageSize = size == null ? 10 : size;
            String sortBy = sort == null ? "name" : sort;
            return userService.getUsers(pageNum, pageSize, sortBy);
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public HttpResponseEntity<UserResponse> createUser(@Json UserRequest request) {
            UserResponse user = userService.createUser(request);
            return HttpResponseEntity.of(201, HttpHeaders.of(), user);
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
        @Json
        public HttpResponseEntity<UserResponse> updateUser(@Path String userId, @Json UserRequest request) {
            UserResponse updated = userService.updateUser(userId, request);
            return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updated);
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        public HttpServerResponse deleteUser(@Path String userId) {
            userService.deleteUser(userId);
            return HttpServerResponse.of(204, HttpBody.empty());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Перепишите `UserController.kt` так, чтобы он делегировал работу сервису:

    ```kotlin
    package io.koraframework.guide.httpserver.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.guide.httpserver.service.UserService
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.HttpResponseEntity
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.common.annotation.Query
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.common.header.HttpHeaders
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponse
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.json.common.annotation.Json
    import java.time.Instant

    @Component
    @HttpController
    class UserController(
        private val userService: UserService
    ) {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(@Path userId: String): UserResponse =
            userService.getUser(userId) ?: throw HttpServerResponseException.of(404, "User not found: $userId")

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getUsers(
            @Query("page") page: Int?,
            @Query("size") size: Int?,
            @Query("sort") sort: String?
        ): List<UserResponse> =
            userService.getUsers(page ?: 0, size ?: 10, sort ?: "name")

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): HttpResponseEntity<UserResponse> =
            HttpResponseEntity.of(201, HttpHeaders.of(), userService.createUser(request))

        @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
        @Json
        fun updateUser(@Path userId: String, @Json request: UserRequest): HttpResponseEntity<UserResponse> =
            HttpResponseEntity.of(
                200,
                HttpHeaders.of("X-Updated-At", Instant.now().toString()),
                userService.updateUser(userId, request)
            )

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        fun deleteUser(@Path userId: String): HttpServerResponse {
            userService.deleteUser(userId)
            return HttpServerResponse.of(204, HttpBody.empty())
        }
    }
    ```

Это финальная структура, которую использует готовое приложение-спутник. Поведение не изменилось, но архитектура стала чище:

- контроллер = HTTP-представление
- репозиторий = абстракция хранения
- сервис = прикладная логика

Обратите внимание, как тип возвращаемого значения каждого маршрута определяет, какой преобразователь Kora ищет во время компиляции:

- `UserResponse` и `List<UserResponse>` с `@Json` требуют `JsonWriter` для типа, который генерирует `@Json` на DTO
- `HttpResponseEntity<UserResponse>` переиспользует тот же JSON-писатель и добавляет сверху код статуса и заголовки
- `HttpServerResponse` возвращается как есть и вообще не нуждается в преобразователе

## Конфигурация { #config }

Теперь, когда структура приложения на месте, можно настроить сам HTTP-сервер.

Создайте или обновите `src/main/resources/application.conf`:

Полный справочник по конфигурации — в [HTTP-сервере](../documentation/http-server.md#configuration) и [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system.port = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    logging {
      levels {
        "ROOT": "WARN" //(4)!
        "io.koraframework": "INFO" //(5)!
      }
    }
    ```

    1.  Публичный HTTP-порт для эндпоинтов приложения (по умолчанию: `8080`).
    2.  Системный HTTP-порт для проб, метрик и служебных эндпоинтов (по умолчанию: `8085`).
    3.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4.  Уровень логирования корневого логгера.
    5.  Уровень логирования логгеров фреймворка Kora.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    logging:
      levels:
        ROOT: "WARN" #(4)!
        "io.koraframework": "INFO" #(5)!
    ```

    1.  Публичный HTTP-порт для эндпоинтов приложения (по умолчанию: `8080`).
    2.  Системный HTTP-порт для проб, метрик и служебных эндпоинтов (по умолчанию: `8085`).
    3.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4.  Уровень логирования корневого логгера.
    5.  Уровень логирования логгеров фреймворка Kora.

Так вы получаете два порта:

- `8080` — основной API приложения
- `8085` — системные эндпоинты, такие как readiness и liveness

Такое разделение полезно в реальных системах, потому что проверки здоровья и эксплуатационные эндпоинты обычно отделяют от публичного бизнес-трафика. Оба ключа уже имеют эти значения по умолчанию,
поэтому приложение запускается и вовсе без `application.conf`; файл становится нужен, как только требуется перенести порт, поднять уровень логирования или прочитать значение из переменной окружения.

## Проверка приложения { #check-app }

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

`classes` — осмысленная первая проверка в Kora: она запускает аннотационный процессор или KSP, генерирует модуль контроллера и граф приложения и падает во время компиляции, если маршрут или
зависимость не удается связать.

Проверки публичного API:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

curl http://localhost:8080/users/1
curl "http://localhost:8080/users?page=0&size=10&sort=name"

curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "email": "updated@example.com"}'

curl -X DELETE http://localhost:8080/users/1
```

Проверки системного API:

```bash
curl http://localhost:8085/system/readiness
# Expected output: OK
curl http://localhost:8085/system/liveness
# Expected output: OK
```

## Лучшие практики { #best-practices }

- Держите методы контроллера тонкими, как только проект выходит за рамки тривиальных обработчиков.
- Используйте репозитории для задач хранения, а сервисы — для прикладной логики.
- Используйте `HttpResponseEntity`, когда нужны явные коды статуса или заголовки.
- Бросайте `HttpServerResponseException`, когда контроллеру или сервису нужно вернуть чистую HTTP-ошибку.
- Держите методы контроллера синхронными и позволяйте виртуальным потокам Undertow нести блокирующую работу.
- Защищайте любое состояние, разделяемое между запросами, потому что параллельные запросы выполняются на разных потоках.

## Итоги { #summary }

Вы построили HTTP API на Kora постепенно:

- сначала один маршрут без хранения
- затем второй маршрут, который показал необходимость хранилища
- затем абстракцию репозитория с реализацией в памяти
- затем контракт репозитория, расширенный до полного CRUD
- и, наконец, сервисный слой и маршруты контроллера, открывающие полный API

## Ключевые понятия { #key-concepts }

- маршрутизация HTTP в Kora через `@HttpRoute`
- маппинг JSON запроса и ответа через `@Json`
- связывание запроса через `@Path` и `@Query`
- контроль ответа через `HttpResponseEntity`
- сигнализация HTTP-ошибок через `HttpServerResponseException`
- разные обязанности контроллера, репозитория и сервиса
- один процесс, два HTTP-сервера: публичный и системный

## Устранение неполадок { #troubleshooting }

**Сервер не стартует:**

- Проверьте доступность портов `8080` и `8085`.
- Убедитесь, что `Application` подключает `UndertowPublicHttpServerModule` и `HoconConfigModule`.

**Компиляция падает с `No component found for dependency`:**

- Типа, указанного в сообщении, нет в графе. Добавьте `@Component` его реализации или предоставьте его методом модуля.
- Частый случай — забытый `@Component` на `InMemoryUserRepository` или `UserService`.

**Компиляция падает с `JsonWriter<T> was not found`:**

- DTO, возвращаемое маршрутом, не помечено `@Json`, поэтому писатель для него не сгенерирован.

**`getUser` всегда возвращает 404:**

- Проверьте, что `createUser` и `getUser` уже связаны со слоем репозитория.
- Убедитесь, что вызываете `getUser` с тем ID, который реально вернул `createUser`.

**Необязательные параметры строки запроса обрабатываются неверно:**

- В Java используйте nullable-обертки с `@Nullable @Query`, например `Integer` и `String`, и импортируйте `@Nullable` из `org.jspecify.annotations`.
- В Kotlin объявляйте тип параметра nullable, например `page: Int?`.
- Отсутствующий обязательный параметр строки запроса получает `400` еще до вызова метода.

**Сборка Kotlin падает с `Suspend methods are not supported by the HTTP server controller generator`:**

- Уберите `suspend` из метода контроллера. HTTP-обработчики Kora синхронные и уже выполняются на виртуальном потоке.

**Сборка зависает или падает неожиданно:**

- Выполните `./gradlew --stop` и повторите.

## Что дальше? { #whats-next }

- [Работа с JSON](json.md) — чтобы маппинг DTO запроса и ответа стал явным.
- [Валидация](validation.md) — чтобы добавить проверки на границе того же HTTP API.
- [База данных JDBC](database-jdbc.md) или [База данных Cassandra](database-cassandra.md) — чтобы заменить репозиторий в памяти настоящим хранилищем.
- [Продвинутый HTTP-сервер](http-server-advanced.md) — когда базовая форма CRUD станет привычной.
- [HTTP-клиент](http-client.md) — когда захочется вызывать этот API из другого приложения Kora.

## Помощь { #help }

Если возникли сложности:

- сравните с [Kora Java HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-app) и [Kora Kotlin HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-server-app)
- посмотрите [документацию по HTTP-серверу](../documentation/http-server.md)
- посмотрите [документацию по JSON](../documentation/json.md)
