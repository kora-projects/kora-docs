---
search:
  exclude: true
title: Руководство по HTTP-серверу
summary: Learn how to build your first Kora HTTP API step by step, from one controller method to a full CRUD service
tags: http-server, rest-api, json, routing, beginner
---

# Руководство по HTTP-серверу { #http-server-guide }

Это руководство знакомит с основным процессом создания HTTP API в Kora. В нем разбирается, как `@HttpController` и `@HttpRoute` превращают методы Java в HTTP-конечные точки, как `@Json`, `@Path`
и `@Query`
связывают запросы с типизированным кодом приложения, и как явные API ответов и исключений дают каждому маршруту понятное HTTP-поведение. Вы также увидите, как граф зависимостей Kora, собираемый во
время компиляции, соединяет
контроллеры, прикладные сервисы, репозитории, преобразователи JSON, конфигурацию и сервер Undertow в одно запускаемое приложение.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-server-app).

## Что вы создадите { #youll-build }

К концу руководства у вас будут:

- `UserController` с CRUD-маршрутами
- DTO запросов и ответов
- хранящий данные в памяти `UserRepository`
- `UserService`, который содержит прикладную логику
- публичный API на порту `8080`
- приватный API управления на порту `8085`

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- пройденное руководство [JSON Processing with Kora](json.md)

## Требования { #prerequisites }

!!! note "Обязательная основа"

    Это руководство предполагает, что вы прошли **[JSON Processing with Kora](json.md)** и у вас есть рабочий проект Kora с доступным сопоставлением JSON DTO.

    Если вы еще не прошли руководство по JSON, сначала сделайте это, потому что оно уже опирается на начальное руководство и дает этому HTTP API нужные шаблоны сериализации JSON.

## Обзор { #overview }

HTTP-серверы Kora строятся вокруг простой идеи: обычные методы могут стать HTTP-конечными точками, когда их транспортный контракт объявлен явно. Вы пишете классы контроллеров, аннотируете маршруты и
параметры, а Kora во время компиляции генерирует код обработки запросов.

Это означает, что HTTP API в Kora строится не на низкоуровневом разборе запросов. Он строится на типизированных сигнатурах методов и аннотациях, которые описывают, как HTTP-данные сопоставляются с
кодом приложения.

### Контроллеры как транспортные адаптеры { #controllers-transport-adapters }

Контроллер — это HTTP-граница приложения. Он должен понимать маршруты, тела запросов, переменные пути, параметры строки запроса, коды состояния и заголовки. Он не должен навсегда становиться местом,
где живет каждое правило хранения или бизнес-правило. Именно поэтому это руководство постепенно разделяет ответственности контроллера, сервиса и репозитория.

Аннотации Kora описывают, как HTTP-данные входят в методы контроллера и выходят из них:

- `@HttpController` помечает класс как HTTP-контроллер
- `@HttpRoute` объявляет HTTP-метод и путь
- `@Json` сопоставляет JSON-тела запросов и ответов
- `@Path` сопоставляет заполнители маршрута с параметрами метода
- `@Query` сопоставляет значения строки запроса с параметрами метода

### Явное HTTP-поведение { #explicit-http-behavior }

Простые методы могут возвращать DTO напрямую, но настоящим API часто нужно больше контроля. `HttpResponseEntity<T>` позволяет маршруту вернуть тело с конкретным кодом состояния или
заголовками. `HttpServerResponse` полезен для ответов без JSON-тела, например `204 No Content`. `HttpServerResponseException` дает прямой способ завершить запрос понятной HTTP-ошибкой.

Эти типы сохраняют HTTP-поведение видимым в контроллере, а не прячут коды состояния внутри не относящегося к этому сервисного кода.

### Слои приложения { #application-layers }

Руководство начинается с одного метода контроллера, затем вводит хранение данных и прикладную логику как отдельные ответственности. Репозиторий отвечает за доступ к данным. Сервис отвечает за
прикладное поведение. Контроллер отвечает за HTTP-представление. Это разделение намеренно небольшое, но именно такую форму позже переиспользуют руководства по базам данных, проверке данных,
кешированию, устойчивости и наблюдаемости.

Практический путь такой:

1. добавить модули HTTP-сервера и JSON
2. создать DTO запросов и ответов
3. открыть первый JSON-маршрут
4. добавить сопоставление параметров пути и строки запроса
5. ввести слои репозитория и сервиса
6. возвращать явные статусы, заголовки и HTTP-ошибки

## Зависимости { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

## Модули { #modules }

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/ru/tinkoff/kora/guide/httpserver/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.httpserver;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowHttpServerModule {  // <----- Подключили модуль

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/httpserver/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.httpserver

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowHttpServerModule  // <----- Подключили модуль

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## DTO { #dto }

Прежде чем добавлять маршруты, нам нужны формы данных, которые мы хотим принимать и возвращать.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/httpserver/dto/UserRequest.java`:

    ```java
    package ru.tinkoff.kora.guide.httpserver.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    Создайте `src/main/java/ru/tinkoff/kora/guide/httpserver/dto/UserResponse.java`:

    ```java
    package ru.tinkoff.kora.guide.httpserver.dto;

    import java.time.LocalDateTime;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/httpserver/dto/UserRequest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.httpserver.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class UserRequest(
        val name: String,
        val email: String
    )
    ```

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/httpserver/dto/UserResponse.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.httpserver.dto

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

`UserRequest` представляет входящий JSON от клиента.

`UserResponse` представляет JSON, который ваш API отправляет обратно.

Начинать с DTO удобно, потому что сигнатура контроллера уже получает устойчивые именованные типы вместо безымянных словарей или сырых строк.

## Создание пользователя { #create-user }

Теперь создадим первый контроллер и первый маршрут. На этом этапе мы **пока не будем** ничего сохранять. Цель этого шага — понять, как Kora сопоставляет HTTP-запрос с методом контроллера.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/httpserver/controller/UserController.java`:

    ```java
    package ru.tinkoff.kora.guide.httpserver.controller;

    import java.time.LocalDateTime;
    import java.util.UUID;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest;
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

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

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/httpserver/controller/UserController.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.httpserver.controller

    import java.time.LocalDateTime
    import java.util.UUID
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

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
  Этот класс содержит HTTP-маршруты. Kora сканирует его и генерирует связку HTTP-обработчиков.

- `@HttpRoute(method = HttpMethod.POST, path = "/users")`
  Этот метод должен обрабатывать `POST /users`.

- `@Json` на методе
  Kora должна использовать преобразователь данных со специальной меткой `@Json`, чтобы сериализовать возвращаемое значение в JSON.

- `@Json` на параметре
  Kora должна использовать преобразователь данных со специальной меткой `@Json`, чтобы десериализовать тело запроса из JSON в `UserRequest`.

На этом этапе маршрут уже ощущается как настоящий API, но он еще ничего не запоминает. Каждый вызов создает новый объект ответа и сразу возвращает его.

Попробуйте:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

## Получение пользователя { #get-user }

Следующий естественный маршрут — `getUser`. Но как только мы добавляем его, мы сталкиваемся с важным вопросом проектирования: где живут пользователи после того, как `createUser` вернул ответ?

Пока мы добавим маршрут и намеренно вернем `404`, чтобы показать, что контроллер уже умеет выражать сбой на уровне HTTP.

===! ":fontawesome-brands-java: `Java`"

    Обновите `UserController.java`:

    ```java
    package ru.tinkoff.kora.guide.httpserver.controller;

    import java.time.LocalDateTime;
    import java.util.UUID;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest;
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

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
            throw HttpServerResponseException.of(404, "User not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `UserController.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.httpserver.controller

    import java.time.LocalDateTime
    import java.util.UUID
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

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
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

Здесь появляются две новые идеи:

- `@Path String userId`
  Kora берет часть `{userId}` из пути маршрута и передает ее в метод.

- `HttpServerResponseException`
  Это простой способ сказать: «этот запрос должен завершиться такой HTTP-ошибкой».

Этот шаг намеренно неполный. Теперь у нас достаточно поведения контроллера, чтобы увидеть, зачем нужна отдельная абстракция хранения.

## Репозиторий пользователей { #user-repository }

Теперь добавим слой репозитория. Репозиторий отвечает за сохранение и получение данных. В этом руководстве мы используем хранящую данные в памяти карту, потому что так пример проще запускать, но сама
абстракция
позже позволит нам перейти на настоящую базу данных.

Сначала нам нужны только две операции:

- сохранить пользователя
- получить пользователя по идентификатору

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/httpserver/repository/UserRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.httpserver.repository;

    import java.util.Optional;
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse;

    public interface UserRepository {

        String save(String name, String email);

        Optional<UserResponse> findById(String id);
    }
    ```

    Создайте `src/main/java/ru/tinkoff/kora/guide/httpserver/repository/InMemoryUserRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.httpserver.repository;

    import java.time.LocalDateTime;
    import java.util.Map;
    import java.util.Optional;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse;

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

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/httpserver/repository/UserRepository.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.httpserver.repository

    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse

    interface UserRepository {
        fun save(name: String, email: String): String
        fun findById(id: String): UserResponse?
    }
    ```

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/httpserver/repository/InMemoryUserRepository.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.httpserver.repository

    import java.time.LocalDateTime
    import java.util.concurrent.ConcurrentHashMap
    import java.util.concurrent.atomic.AtomicLong
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse

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

Репозиторий ничего не знает об HTTP. Он знает только, как сохранять и загружать данные пользователей. Такое разделение важно, потому что задачи хранения и задачи HTTP меняются по разным причинам.

## Контроллер к репозиторию { #controller-repository }

Теперь, когда у нас есть хранилище, можно вернуться к контроллеру и заставить `createUser` и `getUser` действительно работать вместе.

===! ":fontawesome-brands-java: `Java`"

    Обновите `UserController.java`:

    ```java
    package ru.tinkoff.kora.guide.httpserver.controller;

    import java.util.Optional;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest;
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse;
    import ru.tinkoff.kora.guide.httpserver.repository.UserRepository;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

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
                    .orElseThrow(() -> HttpServerResponseException.of(404, "User not found"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `UserController.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.httpserver.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse
    import ru.tinkoff.kora.guide.httpserver.repository.UserRepository
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

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
                ?: throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

Это первый момент, когда API становится сохраняющим состояние. Теперь можно вызвать `createUser`, получить идентификатор и затем использовать этот идентификатор в `getUser`.

## CRUD репозиторий { #crud-repository }

API уже работает для создания и получения. Прежде чем добавлять новые HTTP-маршруты, сначала сделаем абстракцию хранения способной выполнить полный CRUD-поток:

- получить список пользователей
- обновлять пользователей
- удалять пользователей

Так репозиторий остается сосредоточенным только на операциях хранения. Контроллер начнет использовать эти операции в следующем разделе, после того как мы введем сервисный слой между
HTTP-маршрутизацией и хранением.

===! ":fontawesome-brands-java: `Java`"

    Расширьте `UserRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.httpserver.repository;

    import java.util.List;
    import java.util.Optional;
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse;

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
    package ru.tinkoff.kora.guide.httpserver.repository;

    import java.time.LocalDateTime;
    import java.util.ArrayList;
    import java.util.List;
    import java.util.Map;
    import java.util.Optional;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse;

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
    package ru.tinkoff.kora.guide.httpserver.repository

    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse

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
    package ru.tinkoff.kora.guide.httpserver.repository

    import java.time.LocalDateTime
    import java.util.concurrent.ConcurrentHashMap
    import java.util.concurrent.atomic.AtomicLong
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse

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
            val current = users[id] ?: return false
            users[id] = UserResponse(id, name, email, current.createdAt)
            return true
        }

        override fun deleteById(id: String): Boolean = users.remove(id) != null
    }
    ```

На этом этапе репозиторий умеет хранить, выводить список, обновлять и удалять пользователей, но HTTP API все еще открывает только маршруты из предыдущего раздела. Дальше мы добавим сервисный слой и
затем подключим полное CRUD-поведение к контроллеру.

## Сервисный слой { #service-layer }

Во многих приложениях контроллер считается слоем представления, а сервисный слой содержит прикладную логику. Это особенно часто встречается в приложениях в стиле MVC и в сервисах, которые позже
обрастают правилами, интеграциями и точками переиспользования.

Теперь в репозитории есть все операции хранения, которые нужны API. Сервисный слой превращает эти операции в прикладное поведение:

- создает пользователей из DTO запросов
- сортирует и разбивает список в памяти на страницы
- сопоставляет результаты обновления и удаления из репозитория с бизнес-ошибками

После этого контроллер может оставаться сосредоточенным на HTTP-маршрутизации, привязке запросов, кодах ответов и заголовках.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/httpserver/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.guide.httpserver.service;

    import java.time.LocalDateTime;
    import java.util.Comparator;
    import java.util.List;
    import java.util.Optional;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest;
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse;
    import ru.tinkoff.kora.guide.httpserver.repository.UserRepository;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;

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
                throw HttpServerResponseException.of(404, "User not found");
            }
            return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
        }

        public void deleteUser(String id) {
            boolean deleted = userRepository.deleteById(id);
            if (!deleted) {
                throw HttpServerResponseException.of(404, "User not found");
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

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/httpserver/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.httpserver.service

    import java.time.LocalDateTime
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse
    import ru.tinkoff.kora.guide.httpserver.repository.UserRepository
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException

    @Component
    class UserService(
        private val userRepository: UserRepository
    ) {

        fun createUser(request: UserRequest): UserResponse {
            val generatedId = userRepository.save(request.name, request.email)
            return UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
        }

        fun getUser(id: String): UserResponse? = userRepository.findById(id)

        fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> {
            return userRepository.findAll()
                .sortedWith(getComparator(sort))
                .drop(page * size)
                .take(size)
        }

        fun updateUser(id: String, request: UserRequest): UserResponse {
            val updated = userRepository.update(id, request.name, request.email)
            if (!updated) {
                throw HttpServerResponseException.of(404, "User not found")
            }
            return UserResponse(id, request.name, request.email, LocalDateTime.now())
        }

        fun deleteUser(id: String) {
            val deleted = userRepository.deleteById(id)
            if (!deleted) {
                throw HttpServerResponseException.of(404, "User not found")
            }
        }

        private fun getComparator(sort: String): Comparator<UserResponse> {
            return when (sort.lowercase()) {
                "name" -> compareBy(UserResponse::name)
                "email" -> compareBy(UserResponse::email)
                "createdat" -> compareBy(UserResponse::createdAt)
                else -> compareBy(UserResponse::name)
            }
        }
    }
    ```

## Контроллер и сервис { #controller-service }

Теперь контроллер может открыть полный CRUD API, не владея хранением данных или прикладной логикой. Он принимает HTTP-запросы, привязывает параметры маршрута и строки запроса, делегирует
работу `UserService` и выбирает форму HTTP-ответа для каждого маршрута.

Этот шаг также добавляет оставшиеся HTTP-специфичные части:

- `@Query` сопоставляет значения строки запроса, например `?page=0&size=10&sort=name`, с параметрами контроллера
- `@Nullable` помечает необязательные параметры строки запроса
- `HttpResponseEntity<T>` возвращает JSON-тело вместе с явным кодом состояния или заголовками
- `HttpServerResponse` возвращает ответы без JSON-тела, например `204 No Content`

===! ":fontawesome-brands-java: `Java`"

    Перепишите `UserController.java`, чтобы он делегировал работу сервису:

    ```java
    package ru.tinkoff.kora.guide.httpserver.controller;

    import jakarta.annotation.Nullable;
    import java.time.Instant;
    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest;
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse;
    import ru.tinkoff.kora.guide.httpserver.service.UserService;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.HttpResponseEntity;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.common.annotation.Query;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.common.header.HttpHeaders;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

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
                    .orElseThrow(() -> HttpServerResponseException.of(404, "User not found"));
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

    Перепишите `UserController.kt`, чтобы он делегировал работу сервису:

    ```kotlin
    package ru.tinkoff.kora.guide.httpserver.controller

    import jakarta.annotation.Nullable
    import java.time.Instant
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse
    import ru.tinkoff.kora.guide.httpserver.service.UserService
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.HttpResponseEntity
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.common.annotation.Query
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.common.header.HttpHeaders
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class UserController(
        private val userService: UserService
    ) {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(@Path userId: String): UserResponse {
            return userService.getUser(userId)
                ?: throw HttpServerResponseException.of(404, "User not found")
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getUsers(
            @Nullable @Query("page") page: Int?,
            @Nullable @Query("size") size: Int?,
            @Nullable @Query("sort") sort: String?
        ): List<UserResponse> {
            val pageNum = page ?: 0
            val pageSize = size ?: 10
            val sortBy = sort ?: "name"
            return userService.getUsers(pageNum, pageSize, sortBy)
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): HttpResponseEntity<UserResponse> {
            val user = userService.createUser(request)
            return HttpResponseEntity.of(201, HttpHeaders.of(), user)
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
        @Json
        fun updateUser(@Path userId: String, @Json request: UserRequest): HttpResponseEntity<UserResponse> {
            val updated = userService.updateUser(userId, request)
            return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updated)
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        fun deleteUser(@Path userId: String): HttpServerResponse {
            userService.deleteUser(userId)
            return HttpServerResponse.of(204, HttpBody.empty())
        }
    }
    ```

Это финальная структура, которую использует запускаемое сопровождающее приложение. Поведение не изменилось, но архитектура стала чище:

- контроллер = HTTP-представление
- репозиторий = абстракция хранения
- сервис = прикладная логика

## Конфигурация { #config }

Теперь, когда структура приложения готова, можно подключить саму конфигурацию HTTP-сервера.

Создайте или обновите `src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [HTTP-сервер](../documentation/http-server.md) и [журналирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      publicApiHttpPort = 8080 //(1)!
      privateApiHttpPort = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    logging {
      levels {
        "ROOT": "WARN" //(4)!
        "ru.tinkoff.kora": "INFO" //(5)!
      }
    }
    ```

    1. Публичный HTTP-порт по умолчанию, используемый конечными точками приложения.
    2. Приватный HTTP-порт по умолчанию, используемый пробами, метриками и конечными точками управления.
    3. Включает возможность для этого раздела конфигурации.
    4. Уровень логирования для `ROOT`.
    5. Уровень логирования для `ru.tinkoff.kora`.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      publicApiHttpPort: 8080 #(1)!
      privateApiHttpPort: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    logging:
      levels:
        ROOT: "WARN" #(4)!
        "ru.tinkoff.kora": "INFO" #(5)!
    ```

    1. Публичный HTTP-порт по умолчанию, используемый конечными точками приложения.
    2. Приватный HTTP-порт по умолчанию, используемый пробами, метриками и конечными точками управления.
    3. Включает возможность для этого раздела конфигурации.
    4. Уровень логирования для `ROOT`.
    5. Уровень логирования для `ru.tinkoff.kora`.

Это дает два порта:

- `8080` для основного API приложения
- `8085` для конечных точек управления, таких как готовность и живучесть

Такое разделение полезно в настоящих системах, потому что проверки состояния и эксплуатационные конечные точки обычно держат отдельно от публичного бизнес-трафика.

## Проверка приложения { #check-app }

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

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

Проверки приватного API:

```bash
curl http://localhost:8085/system/readiness
curl http://localhost:8085/system/liveness
```

## Лучшие практики { #best-practices }

- Держите методы контроллера тонкими, когда проект перерастает простые обработчики.
- Используйте репозитории для задач хранения, а сервисы — для прикладной логики.
- Используйте `HttpResponseEntity`, когда нужны явные коды состояния или заголовки.
- Выбрасывайте `HttpServerResponseException`, когда контроллеру или сервису нужно показать чистую HTTP-ошибку.

## Итоги { #summary }

Вы постепенно построили HTTP API на Kora:

- сначала один маршрут без постоянного хранения
- затем второй маршрут, который показал необходимость хранилища
- затем абстракцию репозитория с реализацией в памяти
- затем контракт репозитория, расширенный до полного CRUD
- и наконец сервисный слой плюс маршруты контроллера, которые открывают полный API

## Ключевые понятия { #key-concepts }

- HTTP-маршрутизация Kora с `@HttpRoute`
- сопоставление JSON-запросов и JSON-ответов через `@Json`
- сопоставление запросов через `@Path` и `@Query`
- управление ответами через `HttpResponseEntity`
- сигнализация HTTP-ошибок через `HttpServerResponseException`
- разные ответственности контроллера, репозитория и сервиса

## Устранение неполадок { #troubleshooting }

**Сервер не запускается:**

- Проверьте доступность портов `8080` и `8085`.
- Убедитесь, что `Application` включает `UndertowHttpServerModule` и `HoconConfigModule`.

**`getUser` всегда возвращает 404:**

- Проверьте, что `createUser` и `getUser` уже подключены к слою репозитория.
- Убедитесь, что вызываете `getUser` с идентификатором, который действительно вернул `createUser`.

**Необязательные параметры строки запроса обрабатываются неправильно:**

- В Java используйте nullable-обертки с `@Nullable @Query`, например `Integer` и `String`.
- Избегайте `Optional<T>` в параметрах строки запроса контроллера.

**Сборка зависает или неожиданно падает:**

- Выполните `./gradlew --stop`, затем повторите.

## Что дальше? { #whats-next }

- [JSON Processing](json.md), чтобы сделать сопоставление DTO HTTP-запросов и ответов явным.
- [Валидация](validation.md), чтобы добавить проверки на границе того же HTTP API.
- [База данных JDBC](database-jdbc.md) или [База данных Cassandra](database-cassandra.md), чтобы заменить репозиторий в памяти настоящим постоянным хранением.
- [Продвинутый HTTP-сервер](http-server-advanced.md), когда базовая CRUD-форма станет понятной.
- [HTTP-клиент](http-client.md), когда вы захотите, чтобы другое приложение Kora вызывало этот API.

## Помощь { #help }

Если вы столкнулись с проблемами:

- сравните с [Kora Java HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-app) и [Kora Kotlin HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-server-app)
- проверьте [документацию HTTP-сервера](../documentation/http-server.md)
- проверьте [документацию JSON](../documentation/json.md)
- проверьте [примеры Kora](../examples/kora-examples.md)
