---
search:
  exclude: true
title: Работа с JSON в Kora
summary: Learn how to handle JSON requests and responses in a Kora HTTP API with type-safe DTOs and sealed polymorphic responses
description: "Step-by-step JSON request and response mapping for a Kora 2.0 HTTP API: the io.koraframework:json-common artifact, JsonModule, @Json on DTOs and on controller parameters and return values, compile-time generated JsonReader and JsonWriter classes, sealed polymorphic responses with @JsonDiscriminatorField and @JsonDiscriminatorValue, the nullable JsonReader.read contract, JsonWriter.toByteArray and toString, and reading the generated JSON sources."
agent:
  use_when: "Use this file for questions about handling JSON in a Kora 2.0 HTTP API: io.koraframework:json-common, JsonModule, @Json on records and data classes, @Json on @HttpRoute parameters and return values, generated $Type_JsonReader and $Type_JsonWriter sources, sealed responses with @JsonDiscriminatorField and @JsonDiscriminatorValue, JsonReader.read returning null, JsonWriter.toByteArray / toString / toPrettyString, StreamReadException parse errors, and why @Json belongs on the DTO type itself."
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

- JDK 25 или новее
- Gradle 9+
- Текстовый редактор или IDE
- Пройденное руководство [Создание первого приложения Kora](getting-started.md)

Артефакты Kora 2.0 собраны под Java 25, поэтому JDK, которым компилируется приложение, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Обязательно: базовая настройка Kora"

    Это руководство предполагает, что вы прошли **[Создание первого приложения Kora](getting-started.md)** и у вас есть рабочий граф приложения Kora с базовой настройкой HTTP-сервера.

    Если вы еще не проходили вводное руководство, начните с него: здесь мы добавляем отображение JSON-запросов и JSON-ответов поверх этой основы.

## Обзор { #overview }

[JSON](https://www.json.org/json-en.html) обычно становится первой настоящей границей данных в HTTP API. Строкового ответа достаточно, чтобы убедиться в работоспособности сервера, но реальные эндпоинты
обмениваются структурированными объектами запроса и ответа. Это руководство показывает, как Kora превращает такие объекты в JSON, не заставляя код контроллера вручную разбирать или собирать JSON-строки.

Важный сдвиг в мышлении: JSON — это транспортное представление, а не сама модель приложения. Код приложения должен работать с типизированными объектами, а фреймворк отвечает за то, как эти объекты
кодируются при передаче.

### JSON-отображение в Kora { #json-mapping-kora }

Поддержка JSON в Kora построена на генерируемых преобразователях. Когда вы подключаете JSON-модуль и помечаете HTTP-тела аннотацией `@Json`, Kora знает, что тело запроса нужно десериализовать в тип
Java или Kotlin, а значение ответа — сериализовать обратно в JSON. Код преобразователя генерируется на этапе компиляции, поэтому отсутствующие или неподдерживаемые отображения обнаруживаются рано.

Генерация создает два контракта на тип — `JsonReader<T>` и `JsonWriter<T>`, и оба они являются обычными компонентами графа зависимостей без тегов. Ничего не ищется через
рефлексию во время выполнения, а нижележащий потоковый слой — это [Jackson](https://github.com/FasterXML/jackson) в форме `tools.jackson.core`.

Это значит, что контроллер может работать с типизированными DTO:

- DTO запроса описывают, что API принимает
- DTO ответа описывают, что API возвращает
- сгенерированные JSON-преобразователи отвечают за транспортное представление

### DTO как API-контракты { #dtos-api-contracts }

DTO — это не просто вспомогательные классы. Это публичная форма вашего API. `UserRequest` говорит, какие поля обязан прислать клиент, а `UserResponse` — какие поля возвращает сервис. Явно
обозначенная граница упрощает последующие руководства: валидация может навешивать правила на DTO, HTTP-маршруты могут переиспользовать их, а тесты — проверять стабильную форму ответа.

По умолчанию каждое объявленное поле обязательно. Поле становится необязательным, когда оно помечено как допускающее `null` — аннотацией `@Nullable` из [JSpecify](https://jspecify.dev/) в Java или
nullable-типом в Kotlin. Отсутствие обязательного поля прерывает чтение с `StreamReadException`, где перечислены имена полей, — так некорректный запрос клиента превращается в `400`, а не в `null`
где-то в глубине кода приложения.

### Типобезопасные результаты { #type-safe-results }

Это руководство также вводит sealed-модель результата. Sealed-результат полезен, когда одна операция может привести к нескольким известным исходам, например успеху или ошибочному состоянию. Вместо
того чтобы возвращать произвольные словари или бросать исключения на каждую ветку, код может выразить эти исходы замкнутым набором типов.

Главная мысль: JSON-отображение должно поддерживать вашу модель приложения, а не подменять ее. Код приложения работает с типизированными объектами запроса, ответа и результата; Kora берет на себя
границу JSON.

Практический порядок действий:

1. подключить JSON-модуль и поддержку обработчика аннотаций
2. создать DTO запроса и ответа
3. пометить входы и выходы контроллера аннотацией `@Json`
4. дать Kora сгенерировать JSON-преобразователи на этапе компиляции
5. использовать sealed-модель результата, чтобы успешный и ошибочный исходы оставались типизированными

## Зависимости { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    Добавьте в блок `dependencies` в `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation "io.koraframework:json-common"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в блок `dependencies` в `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:json-common")
    }
    ```

Версия артефакта берется из платформы `io.koraframework:kora-bom`, которую приложение уже импортирует, поэтому указывать версию здесь не нужно. `json-common` приносит контракты `JsonReader` и
`JsonWriter` вместе со встроенными кодеками; читатели и писатели для ваших собственных типов создает обработчик аннотаций Kora (`annotation-processors` для Java, `symbol-processors` для Kotlin),
который уже подключен во вводном руководстве.

## Модули { #modules }

Обновите граф приложения, чтобы включить поддержку JSON.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/io/koraframework/guide/json/Application.java`:

    ```java
    package io.koraframework.guide.json;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,  // <----- Connected module
            LogbackModule,
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/io/koraframework/guide/json/Application.kt`:

    ```kotlin
    package io.koraframework.guide.json

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,  // <----- Connected module
        LogbackModule,
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`JsonModule` предоставляет кодеки по умолчанию для стандартных типов — чисел, строк, булевых значений, `UUID`, типов `java.time`, коллекций и словарей. Кодеки для ваших собственных типов приходят от
обработчика аннотаций, и оба набора объединяются графом.

## DTO { #dto }

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/json/dto/UserRequest.java`:

    ```java
    package io.koraframework.guide.json.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    Создайте `src/main/java/io/koraframework/guide/json/dto/UserResponse.java`:

    ```java
    package io.koraframework.guide.json.dto;

    import java.time.LocalDateTime;
    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/json/dto/UserRequest.kt`:

    ```kotlin
    package io.koraframework.guide.json.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserRequest(
        val name: String,
        val email: String
    )
    ```

    Создайте `src/main/kotlin/io/koraframework/guide/json/dto/UserResponse.kt`:

    ```kotlin
    package io.koraframework.guide.json.dto

    import java.time.LocalDateTime
    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

Аннотировать сами классы DTO — осознанное решение. Так Kora генерирует JSON-читатель и JSON-писатель для DTO во время обычной обработки аннотаций, и это избавляет от генерации преобразователей на
поздней фазе, когда тот же тип позже используется как HTTP-тело, значение кэша, полезная нагрузка Kafka или другая JSON-граница.

После компиляции Kora генерирует JSON-читатели и JSON-писатели для этих DTO:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserRequest_JsonReader.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResponse_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserRequest_JsonReader.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResponse_JsonWriter.kt
    ```

Сгенерированный читатель запроса проверяет JSON-токены и обязательные поля до создания записи:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static String read_name(JsonParser __parser, int[] __receivedFields) {
      var __token = __parser.nextToken();
      __receivedFields[0] = __receivedFields[0] | (1 << 0);
      if (__token == JsonToken.VALUE_STRING) {
        return __parser.getText();
      } else {
        throw new StreamReadException(__parser, "Expecting [VALUE_STRING] token for field 'name', got " + __token);
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
      throw StreamReadException(__parser, "Expecting [VALUE_STRING] token for field 'name', got " + __token)
    }

    return UserRequest(
      name!!,
      email!!,
    )
    ```

Оба поля `UserRequest` обязательны, поэтому читатель ведет битовую маску полученных полей и сообщает обо всех отсутствующих полях сразу:

```text
Some of required json fields were not received: name(name) email(email)
```

Сгенерированный писатель ответа пишет ровно те поля DTO, которые образуют контракт HTTP-ответа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    _gen.writeStartObject(_object);
    if (_object.id() != null) {
      _gen.writeName(_id_optimized_field_name);
      _gen.writeString(_object.id());
    }
    if (_object.createdAt() != null) {
      _gen.writeName(_createdAt_optimized_field_name);
      createdAtWriter.write(_gen, _object.createdAt());
    }
    _gen.writeEndObject();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    _gen.writeStartObject(_object)
    _object.id.let {
      _gen.writeName(_id_optimized_field_name)
      _gen.writeString(it)
    }
    _object.createdAt.let {
      _gen.writeName(_createdAt_optimized_field_name)
      createdAtWriter.write(_gen, it)
    }
    _gen.writeEndObject()
    ```

Обратите внимание, что `createdAt` не пишется на месте: сгенерированный писатель принимает `JsonWriter<LocalDateTime>` как зависимость конструктора и делегирует ему. Этот делегат приходит из
`JsonModule` — вот почему модуль обязан быть подключен к графу, и почему смена представления типа-значения сводится к замене одного компонента, а не к правке каждого DTO.

Именно здесь `@Json` становится конкретным: DTO запросов получают сгенерированные читатели, DTO ответов — сгенерированные писатели, а неподдерживаемые формы падают на этапе компиляции, а не
обнаруживаются через рефлексию во время выполнения.

## Сервис { #service }

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/json/service/UserService.java`:

    ```java
    package io.koraframework.guide.json.service;

    import java.time.LocalDateTime;
    import java.util.List;
    import java.util.Map;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.json.dto.UserRequest;
    import io.koraframework.guide.json.dto.UserResponse;
    import io.koraframework.guide.json.dto.UserResult;

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

    Создайте `src/main/kotlin/io/koraframework/guide/json/service/UserService.kt`:

    ```kotlin
    package io.koraframework.guide.json.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.json.dto.UserRequest
    import io.koraframework.guide.json.dto.UserResponse
    import io.koraframework.guide.json.dto.UserResult
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

Сервис работает только с типизированными объектами. Он никогда не видит ни `JsonParser`, ни `JsonGenerator`, ни JSON-строку — именно это разделение и выстраивает данное руководство.

## Sealed-модель ответа { #sealed-response-model }

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/json/dto/UserResult.java`:

    ```java
    package io.koraframework.guide.json.dto;

    import io.koraframework.json.common.annotation.Json;
    import io.koraframework.json.common.annotation.JsonDiscriminatorField;
    import io.koraframework.json.common.annotation.JsonDiscriminatorValue;

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

    Создайте `src/main/kotlin/io/koraframework/guide/json/dto/UserResult.kt`:

    ```kotlin
    package io.koraframework.guide.json.dto

    import io.koraframework.json.common.annotation.Json
    import io.koraframework.json.common.annotation.JsonDiscriminatorField
    import io.koraframework.json.common.annotation.JsonDiscriminatorValue

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

Здесь дискриминатор одновременно является настоящим полем каждого подтипа, поэтому он пишется как обычное свойство и в полезной нагрузке не появляется синтетического ключа. Это сознательный выбор:
дискриминатор не обязан существовать в модели, но когда он есть, одно и то же значение определяет и форму JSON, и ветки `when`/`switch` в коде приложения.

После компиляции сгенерированные sealed-читатель и sealed-писатель показывают, как Kora использует поле-дискриминатор:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_JsonReader.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_JsonReader.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_JsonWriter.kt
    ```

Писатель выбирает конкретный подтип по типу времени выполнения:

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

Читатель выполняет обратную операцию, считывая дискриминатор `status`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var bufferingParser = new BufferingJsonParser(__parser);
    var discriminator = DiscriminatorHelper.readStringDiscriminator(bufferingParser, "status");
    if (discriminator == null) throw new StreamReadException(__parser, "Discriminator required, but not provided, expected one of: [OK, ERROR]");
    var bufferedParser = JsonParserSequence.createFlattened(false, bufferingParser.reset(), __parser);
    bufferedParser.nextToken();
    return switch(discriminator) {
      case "OK" -> userSuccessReader.read(bufferedParser);
      case "ERROR" -> userErrorReader.read(bufferedParser);
      default -> throw new StreamReadException(__parser, "Unknown discriminator: '" + discriminator + "'");
    };
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val bufferingParser = BufferingJsonParser(__parser)
    val discriminator = DiscriminatorHelper.readStringDiscriminator(bufferingParser, "status")
    if (discriminator == null) throw StreamReadException(__parser, "Discriminator required, but not provided, expected one of: [ERROR, OK]")
    val bufferedParser = JsonParserSequence.createFlattened(false, bufferingParser.reset(), __parser)
    bufferedParser.nextToken()
    return when(discriminator) {
      "ERROR" -> userErrorReader.read(bufferedParser)
      "OK" -> userSuccessReader.read(bufferedParser)
      else -> throw StreamReadException(__parser, "Unknown discriminator")
    }
    ```

`BufferingJsonParser` в этом коде и делает дискриминатор независимым от позиции: Kora буферизует токены, прочитанные в поисках `status`, а затем воспроизводит их для читателя подтипа. Поэтому клиент
может прислать `status` последним, и полезная нагрузка все равно будет разобрана.

Если полезная нагрузка законно может не содержать дискриминатор, задайте запасное значение через атрибут `defaultValue` аннотации `@JsonDiscriminatorField`, вместо того чтобы позволять чтению падать.

Этот сгенерированный код объясняет полиморфный JSON без догадок: `@JsonDiscriminatorField("status")` превращается в настоящий поиск дискриминатора, а у каждого подтипа есть собственные сгенерированные
читатель и писатель.

## Контроллер { #controller }

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/json/controller/UserController.java`:

    ```java
    package io.koraframework.guide.json.controller;

    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.json.dto.UserRequest;
    import io.koraframework.guide.json.dto.UserResponse;
    import io.koraframework.guide.json.dto.UserResult;
    import io.koraframework.guide.json.service.UserService;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

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

    Создайте `src/main/kotlin/io/koraframework/guide/json/controller/UserController.kt`:

    ```kotlin
    package io.koraframework.guide.json.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.json.dto.UserRequest
    import io.koraframework.guide.json.dto.UserResponse
    import io.koraframework.guide.json.dto.UserResult
    import io.koraframework.guide.json.service.UserService
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

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

`@Json` выступает здесь в двух разных ролях. На параметре она выбирает преобразователь JSON-тела запроса, на методе — преобразователь JSON-тела ответа. `getAllUsers` возвращает `List<UserResponse>` и
не требует дополнительных объявлений, потому что `JsonModule` предоставляет `JsonWriter<List<T>>`, который сочетается со сгенерированным `JsonWriter<UserResponse>`.

## Сгенерированный JSON-код { #json-code }

`@Json` — это генерация кода на этапе компиляции, а не рефлексия во время выполнения.

После выполнения:

```bash
./gradlew clean classes
```

изучите сгенерированные JSON-читатели и JSON-писатели:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserRequest_JsonReader.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResponse_JsonWriter.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_JsonReader.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_JsonWriter.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_UserSuccess_JsonWriter.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_Status_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserRequest_JsonReader.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResponse_JsonWriter.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_JsonReader.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_JsonWriter.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_UserSuccess_JsonWriter.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_Status_JsonWriter.kt
    ```

Обратите внимание: читатель и писатель генерируются для каждого `@Json`-типа в иерархии, включая вложенный enum `Status` и каждый sealed-подтип. Контроллер запрашивает только `JsonWriter<UserResult>`,
а остальное собирает граф.

Главы про DTO и sealed-ответ показывали сгенерированные фрагменты рядом с моделью, из которой они получены. Сгенерированные JSON-классы также отлично подходят как контекст для ИИ-ассистентов: они
показывают точные имена полей, значения дискриминатора, обработку `null` и отображение подтипов, которые Kora скомпилировала из ваших DTO.

## Чтение и запись JSON напрямую { #read-write-directly }

HTTP-слой использует сгенерированные кодеки за вас, но те же компоненты можно внедрить где угодно — в потребителя Kafka, в задачу миграции или в тест. Запросите `JsonReader<T>` или `JsonWriter<T>` по
типу и используйте их напрямую.

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.json.service;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.json.dto.UserRequest;
    import io.koraframework.json.common.JsonReader;
    import io.koraframework.json.common.JsonWriter;

    @Component
    public final class UserCodec {

        private final JsonReader<UserRequest> reader;
        private final JsonWriter<UserRequest> writer;

        public UserCodec(JsonReader<UserRequest> reader, JsonWriter<UserRequest> writer) {
            this.reader = reader;
            this.writer = writer;
        }

        public byte[] encode(UserRequest request) {
            return this.writer.toByteArray(request); //(1)!
        }

        public UserRequest decode(byte[] payload) {
            UserRequest request = this.reader.read(payload); //(2)!
            if (request == null) {
                throw new IllegalArgumentException("Expected a user request, but got JSON null");
            }
            return request;
        }
    }
    ```

    1.  `toByteArray(...)`, `toString(...)` и `toPrettyString(...)` не объявляют проверяемое исключение, поэтому `try`/`catch` не требуется. Некорректное значение приводит к непроверяемому `JacksonException`.
    2.  `read(...)` помечен `@Nullable`: JSON-документ, состоящий из литерала `null`, декодируется в `null`, а не в объект.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.json.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.json.dto.UserRequest
    import io.koraframework.json.common.JsonReader
    import io.koraframework.json.common.JsonWriter

    @Component
    class UserCodec(
        private val reader: JsonReader<UserRequest>,
        private val writer: JsonWriter<UserRequest>
    ) {

        fun encode(request: UserRequest): ByteArray = writer.toByteArray(request) //(1)!

        fun decode(payload: ByteArray): UserRequest =
            requireNotNull(reader.read(payload)) { "Expected a user request, but got JSON null" } //(2)!
    }
    ```

    1.  `toByteArray(...)`, `toString(...)` и `toPrettyString(...)` не объявляют проверяемое исключение, поэтому `try`/`catch` не требуется. Некорректное значение приводит к непроверяемому `JacksonException`.
    2.  `read(...)` возвращает `UserRequest?`, поэтому Kotlin заставляет решить, что означает JSON-документ `null`. `requireNotNull(...)` превращает это в понятную ошибку.

Оба контракта также принимают `String`, `InputStream` и срез `byte[]`, поэтому один и тот же компонент подходит и для полезной нагрузки в памяти, и для потока.

???+ warning "Внимание"

    Об ошибке разбора сигнализирует `StreamReadException`, наследник непроверяемого `JacksonException`. Обрабатывать его никто не заставляет, поэтому решите явно, где именно нужно ловить некорректную
    полезную нагрузку. Внутри HTTP-маршрута Kora уже делает это за вас и отвечает `400`.

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

Приложение слушает порт `8080` по умолчанию, потому что ничто в `application.conf` не переопределяет `httpServer.port`.

## Проверка приложения { #check-app }

Создание пользователя:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

```json
{"id":"1","name":"John Doe","email":"john@example.com","createdAt":"2026-01-15T10:30:00.123"}
```

Получение всех пользователей:

```bash
curl http://localhost:8080/users
```

```json
[{"id":"1","name":"John Doe","email":"john@example.com","createdAt":"2026-01-15T10:30:00.123"}]
```

Получение пользователя по идентификатору (успех):

```bash
curl http://localhost:8080/users/1
```

```json
{"status":"OK","user":{"id":"1","name":"John Doe","email":"john@example.com","createdAt":"2026-01-15T10:30:00.123"}}
```

Получение пользователя по идентификатору (не найден):

```bash
curl http://localhost:8080/users/999
```

```json
{"status":"ERROR","message":"User not found with id: 999"}
```

Оба ответа приходят из одного маршрута и одного возвращаемого типа. Поле `status` сообщает клиенту, какую ветку sealed-иерархии он получил.

Отправьте запрос без обязательного поля, чтобы увидеть сгенерированную проверку:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe"}'
```

Чтение падает еще до входа в метод контроллера, и сервер отвечает `400`.

## Лучшие практики { #best-practices }

- Держите DTO запросов и ответов простыми и неизменяемыми.
- Используйте sealed-ответы, когда исходы эндпоинта имеют разную форму полезной нагрузки.
- Держите бизнес-логику в слое сервиса, а не в методах контроллера.
- Используйте генерируемое на этапе компиляции JSON-отображение (`@Json`) вместо ручного разбора.
- Ставьте `@Json` на классы DTO запросов и ответов, которые сериализуются или десериализуются как JSON, а не только на параметры и возвращаемые значения контроллера.
- Помечайте поле как допускающее `null` только тогда, когда API действительно разрешает его отсутствие; все остальное остается обязательным и падает сразу.
- Изучайте сгенерированные читатели и писатели, когда форма JSON или полиморфное декодирование неочевидны.

## Итоги { #summary }

Вы реализовали обработку JSON-запросов и JSON-ответов в Kora с помощью:

- API-контрактов на основе DTO
- автоматического JSON-отображения
- полиморфных sealed JSON-ответов с полем-дискриминатором
- сгенерированных JSON-читателей и JSON-писателей для DTO и контрактов sealed-ответа

## Ключевые понятия { #key-concepts }

- `json-common` включает обработку JSON в HTTP-приложениях Kora, а `JsonModule` поставляет кодеки для стандартных типов.
- `@Json` отвечает за десериализацию запроса и сериализацию ответа и регистрирует сгенерированные кодеки в графе как обычные компоненты без тегов.
- Каждое объявленное поле обязательно, если оно не допускает `null`; отсутствие обязательного поля прерывает чтение с `StreamReadException`.
- Sealed-типы с `@JsonDiscriminatorField` и `@JsonDiscriminatorValue` дают типобезопасные полиморфные ответы API.
- `JsonReader<T>.read(...)` может вернуть `null`, а `JsonWriter<T>.toByteArray(...)` и `toString(...)` не требуют обработки проверяемых исключений.
- Сгенерированный JSON-код показывает точное поведение сериализации и десериализации.

## Устранение неполадок { #troubleshooting }

**Тело запроса не десериализуется**

- Убедитесь, что `io.koraframework:json-common` добавлен в зависимости, а `JsonModule` подключен к интерфейсу `@KoraApp`.
- Убедитесь, что параметр запроса в контроллере помечен аннотацией `@Json`.

**Сборка падает из-за отсутствующего компонента `JsonReader` или `JsonWriter`**

- Поставьте `@Json` на сам тип DTO, а не только на сигнатуру контроллера.
- Проверьте, что обработчик Kora подключен: `annotationProcessor "io.koraframework:annotation-processors"` для Java, `ksp("io.koraframework:symbol-processors")` для Kotlin.

**Запрос падает с `Some of required json fields were not received`**

- Перечисленные поля объявлены не допускающими `null`. Либо присылайте их, либо сделайте необязательными через `@Nullable` в Java или nullable-тип в Kotlin.

**Полиморфный ответ сериализуется не так, как ожидалось**

- Проверьте `@JsonDiscriminatorField` на sealed-типе.
- Проверьте, что у каждого подтипа есть `@JsonDiscriminatorValue`.
- Для входящей полезной нагрузки без дискриминатора задайте `@JsonDiscriminatorField(value = "status", defaultValue = "OK")`.

**HTTP-маршруты не находятся**

- Проверьте аннотации `@HttpController` и `@HttpRoute`.
- Проверьте шаблоны путей (`/users`, `/users/{id}`) и HTTP-методы.

## Что дальше? { #whats-next }

- [Создание HTTP-сервера](http-server.md), чтобы применить эти паттерны JSON-DTO в полноценном CRUD API.
- [Валидация](validation.md) после HTTP-сервера, так как валидация опирается на готовый поток контроллер/сервис/репозиторий.
- [База данных JDBC](database-jdbc.md) или [База данных Cassandra](database-cassandra.md) после HTTP-сервера, когда будете готовы заменить репозиторий в памяти.
- [OpenAPI HTTP-сервер](openapi-http-server.md) после HTTP-сервера, чтобы сравнить написанные вручную JSON-DTO с транспортными моделями, сгенерированными из контракта.

## Помощь { #help }

Если возникли сложности:

- сравните с [Kora Java JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-json-app) и [Kora Kotlin JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-json-app)
- посмотрите [документацию по JSON](../documentation/json.md)
- посмотрите [документацию по HTTP-серверу](../documentation/http-server.md)
- посмотрите [пример JSON](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-json)
