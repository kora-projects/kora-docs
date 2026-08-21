---
search:
  exclude: true
title: Работа с JSON в Kora
summary: Learn how to handle JSON requests and responses in a Kora HTTP API with type-safe DTOs and sealed polymorphic responses
tags: json, http, api, serialization
---

# Работа с JSON в Kora { #working-json-kora }

Это руководство знакомит с отображением JSON-запросов и JSON-ответов в Kora. Оно показывает, как `@Json` выбирает JSON-преобразователи для HTTP-тел, как DTO запросов и ответов становятся
типизированной границей API, и как Kora генерирует код сериализации через обработку аннотаций. Также вы увидите, как JSON-отображение встраивается в граф зависимостей, который строится на этапе
компиляции и запускает приложение.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-json-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-json-app).

## Что вы создадите { #youll-build }

Вы соберете HTTP API, в котором JSON является основной формой обмена данными:

- разбор JSON-запроса для `POST /users`
- сериализация JSON-ответа для `GET /users`
- полиморфный JSON-ответ для `GET /users/{id}` с использованием sealed-типов
- типобезопасные DTO-контракты для моделей запроса и ответа

## Что потребуется { #youll-need }

- JDK 17 или новее
- Gradle 7+
- редактор кода или среда разработки
- пройденное руководство [Создание первого приложения на Kora](getting-started.md)

## Требования { #prerequisites }

!!! note "Требуется: базовая настройка Kora"

    Это руководство предполагает, что вы прошли **[Создание первого приложения на Kora](getting-started.md)** и имеете рабочий граф приложения Kora с базовым HTTP-сервером.

    Если вы еще не прошли начальное руководство, сделайте это сначала, потому что этот материал добавляет отображение JSON-запросов и JSON-ответов поверх уже готовой основы.

## Обзор { #overview }

[JSON](https://www.json.org/json-en.html) обычно становится первой настоящей границей данных в HTTP API. Простого строкового ответа достаточно, чтобы доказать, что сервер работает, но реальные
маршруты обмениваются структурированными объектами запросов и ответов. Это руководство показывает, как Kora превращает такие объекты в JSON, не заставляя код контроллера вручную разбирать или собирать
JSON-строки.

Важный сдвиг в мышлении такой: JSON становится транспортным представлением, а не самой моделью приложения. Код приложения должен работать с типизированными объектами, а фреймворк берет на себя то, как
эти объекты кодируются для передачи по сети.

### JSON-отображение в Kora { #json-mapping-kora }

Поддержка JSON в Kora основана на сгенерированных преобразователях. Когда вы добавляете JSON-модуль и помечаете HTTP-тела через `@Json`, Kora понимает, что тело запроса нужно десериализовать в Java-
или Kotlin-тип, а значение ответа нужно сериализовать обратно в JSON. Код преобразователей генерируется на этапе компиляции, поэтому отсутствующие или неподдерживаемые отображения обнаруживаются рано.

Это значит, что контроллер может работать с типизированными DTO:

- DTO запросов описывают, что принимает API
- DTO ответов описывают, что возвращает API
- сгенерированные JSON-преобразователи обрабатывают транспортное представление

### DTO как API-контракты { #dtos-api-contracts }

DTO — это не просто удобные классы. Это публичная форма вашего API. `UserRequest` говорит, какие поля должен отправить клиент, а `UserResponse` говорит, какие поля возвращает сервис. Явная граница
упрощает следующие руководства: правила проверки входных данных можно привязать к DTO, HTTP-маршруты могут переиспользовать их, а тесты могут проверять стабильную форму ответа.

### Типобезопасные результаты { #type-safe-results }

В этом руководстве также вводится sealed-модель результата. Sealed-результат полезен, когда одна операция может завершиться несколькими известными исходами, например успехом или ошибочным состоянием. Вместо
свободных словарей или исключений для каждой ветки код может выразить эти исходы как закрытый набор типов.

Главная идея: JSON-отображение должно поддерживать модель приложения, а не заменять ее. Код приложения работает с типизированными объектами запроса, ответа и результата; Kora обрабатывает
JSON-границу.

Практический порядок:

1. добавить JSON-модуль и поддержку обработки аннотаций
2. создать DTO запросов и ответов
3. пометить входные и выходные значения контроллера через `@Json`
4. позволить Kora сгенерировать JSON-преобразователи на этапе компиляции
5. использовать sealed-модель результата, чтобы исходы успеха и ошибки оставались типизированными

## Зависимости { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    Добавьте в `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:json-module")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:json-module")
    }
    ```

## Модули { #modules }

Обновите граф приложения, чтобы подключить поддержку JSON.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/ru/tinkoff/kora/guide/json/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.json;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,  // <----- Подключили модуль
            LogbackModule,
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/json/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,  // <----- Подключили модуль
        LogbackModule,
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## DTO { #dto }

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/json/dto/UserRequest.java`:

    ```java
    package ru.tinkoff.kora.guide.json.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    Создайте `src/main/java/ru/tinkoff/kora/guide/json/dto/UserResponse.java`:

    ```java
    package ru.tinkoff.kora.guide.json.dto;

    import java.time.LocalDateTime;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/json/dto/UserRequest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class UserRequest(
        val name: String,
        val email: String
    )
    ```

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/json/dto/UserResponse.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json.dto

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

Аннотировать сами DTO-классы нужно намеренно. Так вы говорите Kora сгенерировать средство чтения JSON и средство записи JSON для DTO во время обычной обработки аннотаций. Это помогает избежать
предупреждений о поздней генерации преобразователей, когда тот же тип позже используется через HTTP-тело, значение кеша, сообщение Kafka или другую JSON-границу.

После компиляции Kora сгенерирует средства чтения и записи JSON для этих DTO:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserRequest_JsonReader.java
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResponse_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserRequest_JsonReader.kt
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResponse_JsonWriter.kt
    ```

Сгенерированное средство чтения запроса проверяет JSON-токены и обязательные поля до создания записи:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static String read_name(JsonParser __parser, int[] __receivedFields) throws IOException {
        var __token = __parser.nextToken();
        __receivedFields[0] = __receivedFields[0] | (1 << 0);
        if (__token == JsonToken.VALUE_STRING) {
            return __parser.getText();
        } else {
            throw new JsonParseException(__parser, "Expecting [VALUE_STRING] token for field 'name', got " + __token);
        }
    }

    return new UserRequest(name, email);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private fun read_name(__parser: JsonParser, __receivedFields: IntArray): String {
      val __token = __parser.nextToken()
      __receivedFields[0] = __receivedFields[0] or (1 shl 0)
      if (__token == JsonToken.VALUE_STRING) {
        return __parser.text
      }
      throw JsonParseException(__parser, "Expecting [VALUE_STRING] token for field 'name', got " + __token)
    }

    return UserRequest(name!!, email!!)
    ```

Сгенерированное средство записи ответа записывает ровно те поля DTO, которые формируют контракт HTTP-ответа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    _gen.writeStartObject(_object);
    if (_object.id() != null) {
        _gen.writeFieldName(_id_optimized_field_name);
        _gen.writeString(_object.id());
    }
    if (_object.createdAt() != null) {
        _gen.writeFieldName(_createdAt_optimized_field_name);
        createdAtWriter.write(_gen, _object.createdAt());
    }
    _gen.writeEndObject();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    _gen.writeStartObject(_object)
    _object.id.let {
      _gen.writeFieldName(_id_optimized_field_name)
      _gen.writeString(it)
    }
    _object.createdAt.let {
      _gen.writeFieldName(_createdAt_optimized_field_name)
      createdAtWriter.write(_gen, it)
    }
    _gen.writeEndObject()
    ```

Это первое место, где `@Json` становится конкретным: DTO запросов получают сгенерированные средства чтения, DTO ответов получают сгенерированные средства записи, а неподдерживаемые формы падают на
этапе компиляции вместо того, чтобы обнаруживаться через рефлексию во время выполнения.

## Сервис { #service }

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/json/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.guide.json.service;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.json.dto.UserRequest;
    import ru.tinkoff.kora.guide.json.dto.UserResponse;
    import ru.tinkoff.kora.guide.json.dto.UserResult;

    import java.time.LocalDateTime;
    import java.util.List;
    import java.util.Map;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;

    @Component
    public final class UserService {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();
        private final AtomicLong idGenerator = new AtomicLong(1);

        public UserResponse createUser(UserRequest request) {
            String id = String.valueOf(idGenerator.getAndIncrement());
            UserResponse user = new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
            users.put(id, user);
            return user;
        }

        public List<UserResponse> getAllUsers() {
            return users.values().stream().toList();
        }

        public UserResult getUser(String id) {
            UserResponse user = users.get(id);
            if (user != null) {
                return new UserResult.UserSuccess(UserResult.Status.OK, user);
            }
            return new UserResult.UserError(UserResult.Status.ERROR, "User not found with id: " + id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/json/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json.service

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.json.dto.UserRequest
    import ru.tinkoff.kora.guide.json.dto.UserResponse
    import ru.tinkoff.kora.guide.json.dto.UserResult
    import java.time.LocalDateTime
    import java.util.concurrent.ConcurrentHashMap
    import java.util.concurrent.atomic.AtomicLong

    @Component
    class UserService {

        private val users = ConcurrentHashMap<String, UserResponse>()
        private val idGenerator = AtomicLong(1)

        fun createUser(request: UserRequest): UserResponse {
            val id = idGenerator.getAndIncrement().toString()
            val user = UserResponse(
                id = id,
                name = request.name,
                email = request.email,
                createdAt = LocalDateTime.now()
            )
            users[id] = user
            return user
        }

        fun getAllUsers(): List<UserResponse> = users.values.toList()

        fun getUser(id: String): UserResult {
            val user = users[id]
            return if (user != null) {
                UserResult.UserSuccess(UserResult.Status.OK, user)
            } else {
                UserResult.UserError(UserResult.Status.ERROR, "User not found with id: $id")
            }
        }
    }
    ```

## Sealed-модель ответа { #sealed-response-model }

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/json/dto/UserResult.java`:

    ```java
    package ru.tinkoff.kora.guide.json.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorField;
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorValue;

    @Json
    @JsonDiscriminatorField("status")
    public sealed interface UserResult permits UserResult.UserSuccess, UserResult.UserError {

        @Json
        enum Status {
            OK,
            ERROR
        }

        Status status();

        @Json
        @JsonDiscriminatorValue("OK")
        record UserSuccess(Status status, UserResponse user) implements UserResult {}

        @Json
        @JsonDiscriminatorValue("ERROR")
        record UserError(Status status, String message) implements UserResult {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/json/dto/UserResult.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json.dto

    import ru.tinkoff.kora.json.common.annotation.Json
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorField
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorValue

    @Json
    @JsonDiscriminatorField("status")
    sealed interface UserResult {

        @Json
        enum class Status {
            OK,
            ERROR
        }

        val status: Status

        @Json
        @JsonDiscriminatorValue("OK")
        data class UserSuccess(
            override val status: Status,
            val user: UserResponse
        ) : UserResult

        @Json
        @JsonDiscriminatorValue("ERROR")
        data class UserError(
            override val status: Status,
            val message: String
        ) : UserResult
    }
    ```

После компиляции сгенерированные средства чтения и записи для sealed-типа показывают, как Kora использует поле-дискриминатор:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonReader.java
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonReader.kt
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonWriter.kt
    ```

Средство записи выбирает конкретный подтип по Java-типу:

===! ":fontawesome-brands-java: `Java`"

    ```java
    if (_object == null) {
        _gen.writeNull();
    } else if (_object instanceof UserResult.UserSuccess _o) {
        userSuccessWriter.write(_gen, _o);
    } else if (_object instanceof UserResult.UserError _o) {
        userErrorWriter.write(_gen, _o);
    } else {
        throw new IllegalStateException("Unsupported class");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    when (_object) {
      null -> _gen.writeNull()
      is UserResult.UserError -> userErrorWriter.write(_gen, _object)
      is UserResult.UserSuccess -> userSuccessWriter.write(_gen, _object)
    }
    ```

Средство чтения выполняет обратную операцию: читает дискриминатор `status`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    var discriminator = DiscriminatorHelper.readStringDiscriminator(bufferingParser, "status");
    if (discriminator == null) {
        throw new JsonParseException(__parser, "Discriminator required, but not provided");
    }
    return switch(discriminator) {
        case "OK" -> userSuccessReader.read(bufferedParser);
        case "ERROR" -> userErrorReader.read(bufferedParser);
        default -> throw new JsonParseException(__parser, "Unknown discriminator: '" + discriminator + "'");
    };
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val discriminator = DiscriminatorHelper.readStringDiscriminator(bufferingParser, "status")
    if (discriminator == null) throw JsonParseException(__parser, "Discriminator required, but not provided")
    return when(discriminator) {
      "ERROR" -> userErrorReader.read(bufferedParser)
      "OK" -> userSuccessReader.read(bufferedParser)
      else -> throw JsonParseException(__parser, "Unknown discriminator")
    }
    ```

Этот сгенерированный код объясняет полиморфный JSON без догадок: `@JsonDiscriminatorField("status")` превращается в настоящий поиск дискриминатора, а каждый подтип получает собственные сгенерированные
средства чтения и записи.

## Контроллер { #controller }

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/json/controller/UserController.java`:

    ```java
    package ru.tinkoff.kora.guide.json.controller;

    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.json.dto.UserRequest;
    import ru.tinkoff.kora.guide.json.dto.UserResponse;
    import ru.tinkoff.kora.guide.json.dto.UserResult;
    import ru.tinkoff.kora.guide.json.service.UserService;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class UserController {

        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(@Json UserRequest request) {
            return userService.createUser(request);
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        public List<UserResponse> getAllUsers() {
            return userService.getAllUsers();
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        public UserResult getUser(@Path String id) {
            return userService.getUser(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/json/controller/UserController.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.json.dto.UserRequest
    import ru.tinkoff.kora.guide.json.dto.UserResponse
    import ru.tinkoff.kora.guide.json.dto.UserResult
    import ru.tinkoff.kora.guide.json.service.UserService
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class UserController(
        private val userService: UserService
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): UserResponse {
            return userService.createUser(request)
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getAllUsers(): List<UserResponse> {
            return userService.getAllUsers()
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        fun getUser(@Path id: String): UserResult {
            return userService.getUser(id)
        }
    }
    ```

## Сгенерированный JSON-код { #json-code }

`@Json` — это генерация кода на этапе компиляции, а не рефлексия во время выполнения.

После запуска:

```bash
./gradlew clean classes
```

посмотрите сгенерированные средства чтения и записи JSON:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserRequest_JsonReader.java
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResponse_JsonWriter.java
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonReader.java
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserRequest_JsonReader.kt
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResponse_JsonWriter.kt
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonReader.kt
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonWriter.kt
    ```

Главы про DTO и sealed-ответы показывали сгенерированные фрагменты рядом с моделью, которая их породила. Сгенерированные JSON-классы также дают отличный контекст для нейро-ассистентов: в них видны точные
имена полей, значения дискриминатора, обработка `null` и отображение подтипов, которые Kora скомпилировала из ваших DTO.

## Запуск приложения { #run-app }

Сначала проверьте компиляцию и тесты:

```bash
./gradlew clean classes
./gradlew test
```

Затем запустите приложение:

```bash
./gradlew run
```

## Проверка приложения { #check-app }

Создайте пользователя:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Получите всех пользователей:

```bash
curl http://localhost:8080/users
```

Получите пользователя по идентификатору, когда он найден:

```bash
curl http://localhost:8080/users/1
```

Получите пользователя по идентификатору, когда он не найден:

```bash
curl http://localhost:8080/users/999
```

## Лучшие практики { #best-practices }

- Держите DTO запросов и ответов простыми и неизменяемыми.
- Используйте sealed-ответы, когда исходы маршрута имеют разные формы полезной нагрузки.
- Держите бизнес-логику в сервисном слое, а не в методах контроллера.
- Используйте сгенерированное JSON-отображение на этапе компиляции (`@Json`) вместо ручного разбора.
- Ставьте `@Json` на классы DTO запросов и ответов, которые сериализуются или десериализуются как JSON, а не только на параметры и возвращаемые значения контроллера.
- Изучайте сгенерированные средства чтения и записи, когда форма JSON или полиморфное декодирование непонятны.

## Итоги { #summary }

Вы реализовали обработку JSON-запросов и JSON-ответов в Kora с:

- API-контрактами на основе DTO
- автоматическим JSON-отображением
- полиморфными sealed JSON-ответами с полем-дискриминатором
- сгенерированными средствами чтения и записи JSON для DTO и sealed-контрактов ответа

## Ключевые понятия { #key-concepts }

- `json-module` включает обработку JSON в HTTP-приложениях Kora.
- `@Json` обрабатывает десериализацию запроса и сериализацию ответа.
- Sealed-типы с `@JsonDiscriminatorField` и `@JsonDiscriminatorValue` дают типобезопасные полиморфные API-ответы.
- Сгенерированные JSON-исходники показывают точное поведение сериализации и десериализации.

## Устранение неполадок { #troubleshooting }

**Тело запроса не десериализуется**

- Проверьте, что `json-module` добавлен в зависимости.
- Проверьте, что параметр запроса в контроллере помечен `@Json`.

**Полиморфный ответ сериализуется не так, как ожидалось**

- Проверьте `@JsonDiscriminatorField` на sealed-типе.
- Проверьте, что у каждого подтипа есть `@JsonDiscriminatorValue`.

**HTTP-маршруты не найдены**

- Проверьте аннотации `@HttpController` и `@HttpRoute`.
- Проверьте шаблоны путей (`/users`, `/users/{id}`) и HTTP-методы.

## Что дальше? { #whats-next }

- [Создание HTTP-сервера](http-server.md), чтобы использовать эти шаблоны JSON DTO в полноценном CRUD API.
- [Валидация](validation.md) после HTTP-сервера, потому что проверка входных данных предполагает завершенный поток контроллер/сервис/репозиторий для CRUD.
- [База данных JDBC](database-jdbc.md) или [База данных Cassandra](database-cassandra.md) после HTTP-сервера, когда вы будете готовы заменить репозиторий в памяти.
- [OpenAPI HTTP-сервер](openapi-http-server.md) после HTTP-сервера, чтобы сравнить написанные вручную JSON DTO с транспортными моделями, сгенерированными из контракта.

## Помощь { #help }

Если возникли проблемы:

- сравните с [Kora Java JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-json-app) и [Kora Kotlin JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-json-app)
- проверьте [документацию JSON](../documentation/json.md)
- проверьте [документацию HTTP-сервера](../documentation/http-server.md)
- проверьте [пример HTTP-сервер](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-server)
