---
search:
  exclude: true
title: Валидация с Kora
summary: Continue the HTTP Server guide and add body, path, and query validation with structured JSON validation errors
tags: validation, http-server, json, api
---

# Валидация с Kora { #validation-kora }

В этом руководстве рассматривается валидация запросов для HTTP API на Kora. Вы узнаете, как аннотации ограничений описывают допустимый вход, как `@Validate` включает сгенерированные валидаторы на
границах контроллера и как ошибки валидации превращаются в предсказуемые HTTP-ошибки. Вы также увидите, как валидация удерживает правила DTO рядом с данными, которые они защищают, оставляя код
сервисов и репозиториев сосредоточенным на поведении приложения.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-validation-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-validation-app).

## Что вы создадите { #youll-build }

Вы расширите существующий HTTP-сервер:

- валидацией тела запроса для `createUser` и `updateUser`
- валидацией path-параметра для `userId`
- валидацией query-параметров для `page`, `size` и `sort`
- AOP-валидацией методов через `@Validate`
- структурированными JSON-ответами для ошибок валидации

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- пройденное [руководство по HTTP-серверу](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательная основа"

    Это руководство предполагает, что вы уже прошли **[HTTP-сервер](http-server.md)** и у вас есть готовое CRUD-приложение с `UserController`, `UserService`, `UserRepository` и `InMemoryUserRepository`.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что валидация наиболее полезна, когда тело запроса, path-параметры, query-параметры и сервисный поток уже существуют.

## Обзор { #overview }

[Jakarta Bean Validation](https://jakarta.ee/specifications/bean-validation/) защищает границу между внешним вводом и поведением приложения. Контроллер может десериализовать JSON в DTO, но
десериализация доказывает только то, что полезная нагрузка имеет правильную общую форму. Она не доказывает, что email похож на email, имя не пустое, размер страницы находится в допустимых пределах или
path-параметр соответствует ожидаемому формату.

Без валидации приложение принимает плохой ввод и позволяет более глубоким слоям обнаруживать проблему позже. Обычно это приводит к более слабым ошибкам, большему количеству защитного кода в сервисах и
правилам данных, разбросанным по кодовой базе. С валидацией API может отклонить неправильный ввод рано и вернуть ответ, который явно относится к запросу клиента.

### Как валидация вписывается в HTTP API { #validation-fits-http-api }

В слоистом HTTP-приложении валидация обычно защищает границу, через которую внешний ввод попадает в систему.

Это значит:

- контроллер валидирует тела запросов, path-параметры и query-параметры
- сервис продолжает заниматься бизнес-логикой
- репозиторий продолжает заниматься хранением

Такое разделение полезно, потому что некорректный HTTP-ввод обычно нужно отклонить до того, как он попадет в более глубокие слои. Оно также делает правила валидации проще для поиска и понимания.

Kora поддерживает здесь два стиля:

- декларативную валидацию через аннотации вроде `@Valid` и `@Validate`
- императивное использование через компоненты валидации, описанные в [документации Kora по валидации](../documentation/validation.md)

В этом руководстве мы используем декларативный подход на основе контроллера, потому что он естественнее всего продолжает `http-server.md`.

### Валидация на границе { #validation-at-boundary }

Лучшее место для базовой валидации входа — граница API. Если некорректные данные отклоняются до попадания в сервисный слой, остальная часть приложения может работать с более сильными предположениями.
В этом руководстве валидация появляется в трех местах:

- DTO тела запроса, где можно ограничить поля вроде `name` и `email`
- path-параметры, где можно проверить значения маршрута вроде `userId`
- query-параметры, где можно ограничить ввод для постраничной выдачи и сортировки

Это не заменяет бизнес-валидацию. Правило DTO может сказать «email должен быть синтаксически корректным»; правило сервиса может сказать «этот email должен быть уникальным». Это разные слои валидации.

### Сгенерированная валидация и `@Validate` { #generated-validation-validate }

Полные правила генерации валидаторов, валидации классов и методов описаны в разделах [валидации класса](../documentation/validation.md#class-validation) и [валидации метода](../documentation/validation.md#method-validation).

Валидация Kora использует аннотации для описания ограничений и сгенерированный код для их применения. `@Validate` включает валидацию методов, а модуль валидации добавляет нужные компоненты графа.
Поскольку связка валидации генерируется, отсутствующие валидаторы или неподдерживаемые формы обнаруживаются во время сборки, а не только после того, как плохой запрос попадет в промышленную среду.

В этом руководстве также рассматривается сгенерированный AOP-код, чтобы вы могли увидеть, где валидация действительно выполняется. Это важно, потому что валидация — не магия, спрятанная внутри разбора
JSON. Это сгенерированная проверка границы вокруг методов контроллера.

Практический поток:

1. включить модуль валидации в графе Kora
2. добавить ограничения в DTO запросов
3. включить валидацию методов через `@Validate`
4. валидировать тело, path- и query-входы
5. изучить сгенерированную обертку валидации
6. сопоставить ошибки валидации со стабильным JSON-ответом

### Контракты ошибок { #error-contracts }

Ошибки валидации являются клиентскими ошибками, но клиентам нужно больше, чем сырое сообщение исключения. Полезный API возвращает предсказуемую форму ответа, которая говорит клиенту, какой ввод не
прошел проверку и почему. Финальная часть этого руководства добавляет JSON-контракт ошибки, чтобы ошибки валидации стали частью публичного HTTP-поведения, а не случайным выводом фреймворка.

## Зависимости { #dependencies }

Валидация в этом руководстве опирается на совместную работу нескольких модулей Kora:

- `validation-module` включает генерацию валидаторов и валидацию методов
- `http-server-undertow` открывает контроллер как HTTP-конечные точки
- `json-module` сериализует DTO запросов и ответов
- `config-hocon` и `logging-logback` дают стандартную настройку времени выполнения, используемую во всех руководствах

Подробнее смотрите в [документации Kora по валидации](../documentation/validation.md), [документации HTTP-сервера](../documentation/http-server.md) и [документации JSON](../documentation/json.md).

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies from http-server.md ...

        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("ru.tinkoff.kora:validation-module")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies from http-server.md ...

        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("ru.tinkoff.kora:validation-module")
    }
    ```

## Модули { #modules }

Перед тем как любые аннотации валидации смогут работать, графу приложения нужен `ValidationModule`.

На этом этапе мы включаем только сам модуль. Пользовательскую HTTP-обработку ошибок валидации добавим позже, когда фактический поток валидации уже будет понятен.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/ru/tinkoff/kora/guide/validation/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.validation;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.validation.module.ValidationModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            ValidationModule,  // <----- Подключили модуль
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/validation/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.validation

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.validation.module.ValidationModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        ValidationModule,  // <----- Подключили модуль
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Валидация модели { #model-validation }

Проще всего начать с того же тела запроса, которое уже используется в `createUser` и `updateUser`.

Это объектная валидация. Вместо того чтобы валидировать каждое JSON-поле прямо в методе контроллера, мы один раз описываем правила внутри `UserRequest`.

В этом руководстве:

- `name` должен присутствовать, не быть пустым и иметь разумный размер
- `email` должен присутствовать и соответствовать простому шаблону email

Так мы получаем хороший первый пример валидации DTO без изменения общего CRUD-проектирования из предыдущего руководства.

===! ":fontawesome-brands-java: `Java`"

    Создайте или обновите `src/main/java/ru/tinkoff/kora/guide/validation/dto/UserRequest.java`:

    ```java
    package ru.tinkoff.kora.guide.validation.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;
    import ru.tinkoff.kora.validation.common.annotation.NotBlank;
    import ru.tinkoff.kora.validation.common.annotation.Pattern;
    import ru.tinkoff.kora.validation.common.annotation.Size;

    @Json
    public record UserRequest(
        @NotBlank @Size(min = 2, max = 100) String name,
        @NotBlank @Pattern("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$") String email
    ) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте или обновите `src/main/kotlin/ru/tinkoff/kora/guide/validation/dto/UserRequest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.validation.dto

    import ru.tinkoff.kora.json.common.annotation.Json
    import ru.tinkoff.kora.validation.common.annotation.NotBlank
    import ru.tinkoff.kora.validation.common.annotation.Pattern
    import ru.tinkoff.kora.validation.common.annotation.Size

    @Json
    data class UserRequest(
        @field:NotBlank
        @field:Size(min = 2, max = 100)
        val name: String,
        @field:NotBlank
        @field:Pattern("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
        val email: String
    )
    ```

Обратите внимание, что на этом шаге мы только описали правила. Их еще нужно применить на границе контроллера, что мы и сделаем дальше.

## Валидация контроллера { #controller-validation }

Связка `@Valid` и `@Validate` опирается на правила [валидации класса](../documentation/validation.md#class-validation) и [валидации метода](../documentation/validation.md#method-validation).

Теперь мы связываем эти правила DTO с настоящими HTTP-конечными точками из `http-server.md`.

Здесь важнее всего две аннотации:

- `@Valid` говорит, что сложный объектный аргумент должен быть провалидирован с помощью сгенерированного валидатора для этого DTO
- `@Validate` включает валидацию уровня метода для самого метода контроллера

`@Validate` важна, потому что говорит Kora сгенерировать логику валидации вокруг вызова метода. `@Valid` важна, потому что говорит этой сгенерированной логике спуститься внутрь объекта `UserRequest` и
проверить его поля.

===! ":fontawesome-brands-java: `Java`"

    Обновите методы `POST` и `PUT` в `src/main/java/ru/tinkoff/kora/guide/validation/controller/UserController.java`:

    ```java
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    @Json
    @Validate
    public HttpResponseEntity<UserResponse> createUser(@Valid @Json UserRequest request) {
        UserResponse user = userService.createUser(request);
        return HttpResponseEntity.of(201, HttpHeaders.of(), user);
    }

    @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
    @Json
    @Validate
    public HttpResponseEntity<UserResponse> updateUser(
        @Path String userId,
        @Valid @Json UserRequest request) {
        UserResponse updated = userService.updateUser(userId, request);
        return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updated);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите те же методы в `src/main/kotlin/ru/tinkoff/kora/guide/validation/controller/UserController.kt`:

    ```kotlin
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    @Json
    @Validate
    open fun createUser(@Json @Valid request: UserRequest): HttpResponseEntity<UserResponse> {
        val user = userService.createUser(request)
        return HttpResponseEntity.of(201, HttpHeaders.of(), user)
    }

    @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
    @Json
    @Validate
    open fun updateUser(
        @Path userId: String,
        @Json @Valid request: UserRequest
    ): HttpResponseEntity<UserResponse> {
        val updated = userService.updateUser(userId, request)
        return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updated)
    }
    ```

На этом этапе:

- некорректный JSON по-прежнему падает во время разбора JSON
- корректный по форме JSON с недопустимыми значениями полей теперь падает во время валидации
- допустимый JSON продолжает попадать в тот же поток сервиса и репозитория, который вы уже построили раньше

После компиляции сгенерированный AOP-заместитель показывает, как `@Valid` делегирует работу в сгенерированный валидатор `UserRequest` до вызова метода контроллера:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-validation-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.java
    ```

    ```java
    private HttpResponseEntity<UserResponse> _createUser_AopProxy_ValidateMethodKoraAspect(UserRequest request) {
        var _argCtx = ValidationContext.builder().failFast(false).build();
        var _argViolations = new ArrayList<Violation>();

        if (request == null) {
            var _argCtx_request = _argCtx.addPath("request");
            _argViolations.add(_argCtx_request.violates("Parameter 'request' must be non null, but was null"));
        } else {
            var _argCtx_request = _argCtx.addPath("request");
            var _argValidatorResult_request_1 = validator6.validate(request, _argCtx_request);
            if (!_argValidatorResult_request_1.isEmpty()) {
                _argViolations.addAll(_argValidatorResult_request_1);
            }
        }

        if (!_argViolations.isEmpty()) {
            throw new ViolationException(_argViolations);
        }

        return super.createUser(request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-validation-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.kt
    ```

    ```kotlin
    private fun _createUser_AopProxy_ValidateMethodKoraAspect(request: UserRequest):
        HttpResponseEntity<UserResponse> {
      val _argsContext = ValidationContext.full()
      val _argsViolations = mutableListOf<Violation>()

      val _argsContext_request = _argsContext.addPath("request")
      _argsViolations.addAll(validator6.validate(request, _argsContext_request))

      if (_argsViolations.isNotEmpty()) {
        throw ViolationException(_argsViolations)
      }

      val _result = super.createUser(request)
      return _result
    }
    ```

Важная деталь в том, что `validator6.validate(request, ...)` выполняется до `super.createUser(request)`, поэтому недопустимые поля DTO никогда не попадают в тело контроллера.

### Path-параметры { #path-parameters }

Тела запросов — не единственный источник недопустимого ввода. Path-параметры тоже могут быть неверными.

В этом руководстве `userId` приходит из репозитория в памяти, который использует числовые строковые идентификаторы вроде `1`, `2` и `3`. Поэтому мы можем явно выразить это предположение в контроллере:

- `@NotBlank` отклоняет пустые идентификатор
- `@Pattern("^\\d+$")` говорит, что значение пути должно состоять только из цифр

Это валидация аргумента метода, а не валидация DTO. Она полезна, когда данные простые и не оправдывают создание отдельного объекта только ради валидации.

===! ":fontawesome-brands-java: `Java`"

    Обновите методы `GET`, `PUT` и `DELETE` в `src/main/java/ru/tinkoff/kora/guide/validation/controller/UserController.java`:

    ```java
    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    @Validate
    public UserResponse getUser(@Path @NotBlank @Pattern("^\\d+$") String userId) {
        return userService.getUser(userId)
            .orElseThrow(() -> HttpServerResponseException.of(404, "User not found"));
    }

    @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
    @Json
    @Validate
    public HttpResponseEntity<UserResponse> updateUser(
        @Path @NotBlank @Pattern("^\\d+$") String userId,
        @Valid @Json UserRequest request) {
        UserResponse updated = userService.updateUser(userId, request);
        return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updated);
    }

    @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
    @Validate
    public HttpServerResponse deleteUser(@Path @NotBlank @Pattern("^\\d+$") String userId) {
        userService.deleteUser(userId);
        return HttpServerResponse.of(204, HttpBody.empty());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите те же методы в `src/main/kotlin/ru/tinkoff/kora/guide/validation/controller/UserController.kt`:

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    @Validate
    open fun getUser(@Path @NotBlank @Pattern("^\\d+$") userId: String): UserResponse {
        return userService.getUser(userId)
            .orElseThrow { HttpServerResponseException.of(404, "User not found") }
    }

    @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
    @Json
    @Validate
    open fun updateUser(
        @Path @NotBlank @Pattern("^\\d+$") userId: String,
        @Json @Valid request: UserRequest
    ): HttpResponseEntity<UserResponse> {
        val updated = userService.updateUser(userId, request)
        return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updated)
    }

    @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
    @Validate
    open fun deleteUser(@Path @NotBlank @Pattern("^\\d+$") userId: String): HttpServerResponse {
        userService.deleteUser(userId)
        return HttpServerResponse.of(204, HttpBody.empty())
    }
    ```

Такая валидация особенно полезна для path-переменных, заголовков, файлы cookie и других простых параметров, которые естественно не живут внутри DTO запроса.

После компиляции сгенерированный заместитель показывает, как ограничения path-параметра становятся обычными вызовами валидаторов:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-validation-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.java
    ```

    ```java
    private UserResponse _getUser_AopProxy_ValidateMethodKoraAspect(String userId) {
        var _argCtx = ValidationContext.builder().failFast(false).build();
        var _argViolations = new ArrayList<Violation>();

        if (userId == null) {
            var _argCtx_userId = _argCtx.addPath("userId");
            _argViolations.add(_argCtx_userId.violates("Parameter 'userId' must be non null, but was null"));
        } else {
            var _argCtx_userId = _argCtx.addPath("userId");
            var _argConstResult_userId_1 = validator1.validate(userId, _argCtx_userId);
            if (!_argConstResult_userId_1.isEmpty()) {
                _argViolations.addAll(_argConstResult_userId_1);
            }
            var _argConstResult_userId_2 = validator2.validate(userId, _argCtx_userId);
            if (!_argConstResult_userId_2.isEmpty()) {
                _argViolations.addAll(_argConstResult_userId_2);
            }
        }

        if (!_argViolations.isEmpty()) {
            throw new ViolationException(_argViolations);
        }

        return super.getUser(userId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-validation-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.kt
    ```

    ```kotlin
    private fun _getUser_AopProxy_ValidateMethodKoraAspect(userId: String): UserResponse {
      val _argsContext = ValidationContext.full()
      val _argsViolations = mutableListOf<Violation>()

      val _argsContext_userId = _argsContext.addPath("userId")
      _argsViolations.addAll(validator1.validate(userId, _argsContext_userId))
      _argsViolations.addAll(validator2.validate(userId, _argsContext_userId))

      if (_argsViolations.isNotEmpty()) {
        throw ViolationException(_argsViolations)
      }

      val _result = super.getUser(userId)
      return _result
    }
    ```

Это делает границу метода видимой: Kora сначала валидирует `userId`, а затем делегирует вызов вашей исходной реализации `getUser(...)`.

### Query-параметры { #query-parameters }

Следующая распространенная цель валидации — строка запроса.

Наша конечная точка `GET /users` уже поддерживает постраничную выдачу и сортировку. Это делает ее хорошим местом для демонстрации валидации параметров метода для необязательных значений:

- `page` необязателен, но если присутствует, должен быть `0` или больше
- `size` необязателен, но если присутствует, должен оставаться в безопасном диапазоне
- `sort` необязателен, но если присутствует, должен быть одним из поддерживаемых полей сортировки

Такая валидация защищает API от неправильных запросов постраничной выдачи до запуска бизнес-логики или логики хранения.

===! ":fontawesome-brands-java: `Java`"

    Обновите `getUsers` в `src/main/java/ru/tinkoff/kora/guide/validation/controller/UserController.java`:

    ```java
    @HttpRoute(method = HttpMethod.GET, path = "/users")
    @Json
    @Validate
    public List<UserResponse> getUsers(
        @Nullable @Range(from = 0, to = 1_000) @Query("page") Integer page,
        @Nullable @Range(from = 1, to = 100) @Query("size") Integer size,
        @Nullable @Pattern("^(?i)(name|email|createdat)$") @Query("sort") String sort) {
        int pageNum = page == null ? 0 : page;
        int pageSize = size == null ? 10 : size;
        String sortBy = sort == null ? "name" : sort;
        return userService.getUsers(pageNum, pageSize, sortBy);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `getUsers` в `src/main/kotlin/ru/tinkoff/kora/guide/validation/controller/UserController.kt`:

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/users")
    @Json
    @Validate
    open fun getUsers(
        @Query("page") @Range(from = 0, to = 1_000) page: Int?,
        @Query("size") @Range(from = 1, to = 100) size: Int?,
        @Query("sort") @Pattern("^(?i)(name|email|createdat)$") sort: String?
    ): List<UserResponse> {
        val pageNum = page ?: 0
        val pageSize = size ?: 10
        val sortBy = sort ?: "name"
        return userService.getUsers(pageNum, pageSize, sortBy)
    }
    ```

После этого шага руководство покрывает три разные цели валидации в отдельных главах:

- сложные JSON-объекты
- простые path-параметры
- простые query-параметры

Такое разделение полезно, потому что каждый вид входа в настоящих API обычно развивается по-своему.

После компиляции сгенерированный заместитель показывает, что необязательные query-параметры валидируются только когда присутствуют:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-validation-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.java
    ```

    ```java
    private List<UserResponse> _getUsers_AopProxy_ValidateMethodKoraAspect(Integer page, Integer size, String sort) {
    var _argCtx = ValidationContext.builder().failFast(false).build();
    var _argViolations = new ArrayList<Violation>();

    if (page != null) {
        var _argCtx_page = _argCtx.addPath("page");
        var _argConstResult_page_1 = validator3.validate(page, _argCtx_page);
        if (!_argConstResult_page_1.isEmpty()) {
            _argViolations.addAll(_argConstResult_page_1);
        }
    }
    if (size != null) {
        var _argCtx_size = _argCtx.addPath("size");
        var _argConstResult_size_1 = validator4.validate(size, _argCtx_size);
        if (!_argConstResult_size_1.isEmpty()) {
            _argViolations.addAll(_argConstResult_size_1);
        }
    }
    if (sort != null) {
        var _argCtx_sort = _argCtx.addPath("sort");
        var _argConstResult_sort_1 = validator5.validate(sort, _argCtx_sort);
        if (!_argConstResult_sort_1.isEmpty()) {
            _argViolations.addAll(_argConstResult_sort_1);
        }
    }

    if (!_argViolations.isEmpty()) {
        throw new ViolationException(_argViolations);
    }

    return super.getUsers(page, size, sort);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-validation-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.kt
    ```

    ```kotlin
    private fun _getUsers_AopProxy_ValidateMethodKoraAspect(
      page: Int?,
      size: Int?,
      sort: String?,
    ): List<UserResponse> {
      val _argsContext = ValidationContext.full()
      val _argsViolations = mutableListOf<Violation>()

      if(page != null) {
        val _argsContext_page = _argsContext.addPath("page")
        _argsViolations.addAll(validator3.validate(page, _argsContext_page))
      }
      if(size != null) {
        val _argsContext_size = _argsContext.addPath("size")
        _argsViolations.addAll(validator4.validate(size, _argsContext_size))
      }
      if(sort != null) {
        val _argsContext_sort = _argsContext.addPath("sort")
        _argsViolations.addAll(validator5.validate(sort, _argsContext_sort))
      }

      if (_argsViolations.isNotEmpty()) {
        throw ViolationException(_argsViolations)
      }

      val _result = super.getUsers(page, size, sort)
      return _result
    }
    ```

Этот сгенерированный код точно объясняет необязательное поведение: `null` означает «параметр не передан», а присутствующее значение проверяется по своему ограничению.

## Сгенерированный код { #generated-code }

`@Validate` — это AOP-аннотация.

Это значит, что Kora не изменяет исходный файл вашего контроллера напрямую. Вместо этого она генерирует подкласс вокруг валидируемого компонента и помещает логику валидации в этот сгенерированный
класс. Ваш код по-прежнему выглядит простым, но сгенерированный заместитель выполняет проверки до того, как вызов попадет в тело метода.

Именно поэтому:

- валидируемые Java-классы не должны быть `final`
- валидируемые Kotlin-классы должны быть `open`
- валидируемые Kotlin-методы тоже должны быть `open`

После компиляции вы можете посмотреть сгенерированный исходник здесь:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-validation-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-validation-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.kt
    ```

Этот файл — самое простое место, где можно увидеть настоящий поток валидации. Вы увидите, что Kora:

- читает входящие аргументы метода
- валидирует простые параметры метода, например `userId`, `page`, `size` и `sort`
- валидирует вложенные объекты, например `UserRequest`
- выбрасывает `ViolationException`, когда правила нарушены
- вызывает исходный метод контроллера только если валидация успешна

В предыдущих главах сгенерированные фрагменты были показаны рядом с целью валидации, которая их породила: валидацией DTO тела, валидацией path-параметра и валидацией query-параметра. Важный урок везде
одинаков: валидация происходит до логики вашего контроллера, а вызов `super...` появляется только после сбора нарушений. Этот сгенерированный код также является хорошей целью отладки для
нейро-ассистентов, потому что он раскрывает конкретные валидаторы и имена параметров, которые Kora вывела из ваших аннотаций.

Это полезно, когда вы учитесь, отлаживаете или просто хотите подтвердить, что именно фреймворк сгенерировал для вас. Более широкие детали смотрите
в [документации Kora по валидации](../documentation/validation.md) и [документации по контейнеру](../documentation/container.md).

## Обработка ошибок валидации { #validation-errors }

Настройка HTTP-ответа здесь соединяет валидацию с общими правилами [обработки ошибок HTTP-сервера](../documentation/http-server.md#error-handling).

Пока валидация работает, но опыт HTTP-клиента все еще можно улучшить.

По умолчанию вы можете увидеть только ошибки уровня фреймворка. В настоящем API часто лучше возвращать стабильный JSON-контракт ошибки, который клиенты могут разобрать и отобразить.

Kora дает здесь гибкость. Можно определить такую обработку только для выбранных конечных точек или зарегистрировать ее глобально для всего HTTP-приложения. В этом руководстве используется глобальный
подход, потому что это самый простой способ сохранить все контроллеры единообразными.

Мы добавим:

- `ValidationErrorDetails` и `ValidationErrorResponse` как явные JSON DTO
- `ViolationExceptionHttpServerResponseMapper`, чтобы превращать `ViolationException` в этот DTO
- `ValidationHttpServerInterceptor`, чтобы применять это сопоставление в HTTP-конвейере

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/validation/dto/ValidationErrorDetails.java`:

    ```java
    package ru.tinkoff.kora.guide.validation.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record ValidationErrorDetails(String field, String message) {}
    ```

    Создайте `src/main/java/ru/tinkoff/kora/guide/validation/dto/ValidationErrorResponse.java`:

    ```java
    package ru.tinkoff.kora.guide.validation.dto;

    import java.util.List;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record ValidationErrorResponse(String code, String message, List<ValidationErrorDetails> errors) {

        public static ValidationErrorResponse of(List<ValidationErrorDetails> errors) {
            return new ValidationErrorResponse("VALIDATION_ERROR", "Validation failed", errors);
        }
    }
    ```

    Обновите `src/main/java/ru/tinkoff/kora/guide/validation/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.validation;

    import java.util.List;
    import java.util.stream.Collectors;
    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.guide.validation.dto.ValidationErrorDetails;
    import ru.tinkoff.kora.guide.validation.dto.ValidationErrorResponse;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerModule;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.common.JsonWriter;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.validation.common.Violation;
    import ru.tinkoff.kora.validation.module.ValidationModule;
    import ru.tinkoff.kora.validation.module.http.server.ValidationHttpServerInterceptor;
    import ru.tinkoff.kora.validation.module.http.server.ViolationExceptionHttpServerResponseMapper;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            ValidationModule,  // <----- Подключили модуль
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

        default ViolationExceptionHttpServerResponseMapper violationExceptionHttpServerResponseMapper(
                JsonWriter<ValidationErrorResponse> errorResponseJsonWriter) {
            return (request, exception) -> HttpServerResponse.of(
                    400,
                    HttpBody.json(errorResponseJsonWriter.toByteArrayUnchecked(
                            ValidationErrorResponse.of(toValidationErrors(exception.getViolations())))));
        }

        @Tag(HttpServerModule.class)
        default ValidationHttpServerInterceptor validationHttpServerInterceptor(
                ViolationExceptionHttpServerResponseMapper violationExceptionHttpServerResponseMapper) {
            return new ValidationHttpServerInterceptor(violationExceptionHttpServerResponseMapper);
        }

        private static List<ValidationErrorDetails> toValidationErrors(List<Violation> violations) {
            return violations.stream()
                    .map(violation -> new ValidationErrorDetails(normalizeField(violation), violation.message()))
                    .collect(Collectors.toList());
        }

        private static String normalizeField(Violation violation) {
            String fullPath = violation.path().full();
            int lastDot = fullPath.lastIndexOf('.');
            return lastDot >= 0 ? fullPath.substring(lastDot + 1) : fullPath;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/validation/dto/ValidationErrorDetails.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.validation.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class ValidationErrorDetails(
        val field: String,
        val message: String
    )
    ```

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/validation/dto/ValidationErrorResponse.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.validation.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class ValidationErrorResponse(
        val code: String,
        val message: String,
        val errors: List<ValidationErrorDetails>
    ) {
        companion object {
            fun of(errors: List<ValidationErrorDetails>): ValidationErrorResponse {
                return ValidationErrorResponse(
                    code = "VALIDATION_ERROR",
                    message = "Validation failed",
                    errors = errors
                )
            }
        }
    }
    ```

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/validation/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.validation

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.guide.validation.dto.ValidationErrorDetails
    import ru.tinkoff.kora.guide.validation.dto.ValidationErrorResponse
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerModule
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.common.JsonWriter
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.validation.common.Violation
    import ru.tinkoff.kora.validation.module.ValidationModule
    import ru.tinkoff.kora.validation.module.http.server.ValidationHttpServerInterceptor
    import ru.tinkoff.kora.validation.module.http.server.ViolationExceptionHttpServerResponseMapper

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        ValidationModule,  // <----- Подключили модуль
        UndertowHttpServerModule {

        fun violationExceptionHttpServerResponseMapper(
            errorResponseJsonWriter: JsonWriter<ValidationErrorResponse>
        ): ViolationExceptionHttpServerResponseMapper {
            return ViolationExceptionHttpServerResponseMapper { _, exception ->
                HttpServerResponse.of(
                    400,
                    HttpBody.json(
                        errorResponseJsonWriter.toByteArrayUnchecked(
                            ValidationErrorResponse.of(toValidationErrors(exception.violations))
                        )
                    )
                )
            }
        }

        @Tag(HttpServerModule::class)
        fun validationHttpServerInterceptor(
            violationExceptionHttpServerResponseMapper: ViolationExceptionHttpServerResponseMapper
        ): ValidationHttpServerInterceptor {
            return ValidationHttpServerInterceptor(violationExceptionHttpServerResponseMapper)
        }
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }

    private fun toValidationErrors(violations: List<Violation>): List<ValidationErrorDetails> {
        return violations.map { violation ->
            ValidationErrorDetails(normalizeField(violation), violation.message())
        }
    }

    private fun normalizeField(violation: Violation): String {
        val fullPath = violation.path().full()
        val lastDot = fullPath.lastIndexOf('.')
        return if (lastDot >= 0) fullPath.substring(lastDot + 1) else fullPath
    }
    ```

Важное разделение здесь такое:

- AOP-валидация решает, допустим ли вызов метода
- перехватчик и преобразователь решают, как HTTP-клиент увидит ошибку

## Запуск приложения { #run-app }

Используйте стандартный процесс запуска:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

## Проверка приложения { #check-app }

Корректный запрос `createUser`:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Некорректное тело запроса:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"","email":"broken-email"}'
```

Ожидаемая форма ответа:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "errors": [
    {
      "field": "name",
      "message": "Should be not blank"
    },
    {
      "field": "email",
      "message": "Should match RegEx ..."
    }
  ]
}
```

Некорректный path-параметр:

```bash
curl http://localhost:8080/users/abc
```

Ожидаемая форма ответа:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "errors": [
    {
      "field": "userId",
      "message": "Should match RegEx ..."
    }
  ]
}
```

Некорректные query-параметры:

```bash
curl "http://localhost:8080/users?page=-1&size=0&sort=nickname"
```

Ожидаемая форма ответа:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "errors": [
    {
      "field": "page",
      "message": "Should be in range ..."
    },
    {
      "field": "size",
      "message": "Should be in range ..."
    },
    {
      "field": "sort",
      "message": "Should match RegEx ..."
    }
  ]
}
```

## Лучшие практики { #best-practices }

- Добавляйте валидацию на границе контроллера, когда цель — защитить HTTP-ввод.
- Используйте валидацию DTO для структурированных JSON-тел и валидацию параметров метода для простых path- или query-значений.
- Держите `UserService` и `UserRepository` сосредоточенными на бизнес-логике и хранении, а не дублируйте там правила HTTP-ввода.
- Помните, что `@Validate` основана на AOP. В Java валидируемый класс не должен быть `final`. В Kotlin класс и валидируемые методы должны быть `open`.
- Когда ошибка валидации должна стать стабильным контрактом API, определяйте явный DTO ошибки вместо утечки сырых исключений фреймворка.
- В Kotlin продолжайте использовать `@field:` для аннотаций свойств, например `@field:NotBlank`, `@field:Size` и `@field:Pattern`.

## Итоги { #summary }

Вы постепенно расширили CRUD-приложение из `http-server.md` валидацией.

Сначала вы включили `ValidationModule` в графе приложения. Затем провалидировали тело `UserRequest`, используемое в `createUser` и `updateUser`. После этого провалидировали path-параметры `userId` и
query-параметры постраничной выдачи и сортировки в `getUsers`. Затем изучили сгенерированный AOP-исходник, чтобы увидеть, где на самом деле выполняется валидация методов. Наконец, вы ввели глобальную
стратегию сопоставления HTTP-ошибок валидации через `ViolationExceptionHttpServerResponseMapper` и `ValidationHttpServerInterceptor`.

## Ключевые понятия { #key-concepts }

- `ValidationModule` включает поддержку валидации Kora в графе приложения.
- `@Valid` валидирует вложенные объекты, например DTO запросов.
- `@Validate` включает валидацию аргументов метода и возвращаемого значения через сгенерированный AOP-код.
- Валидация DTO и валидация параметров метода решают разные задачи и часто используются вместе.
- `ViolationExceptionHttpServerResponseMapper` определяет, как ошибки валидации становятся HTTP-ответами.
- `ValidationHttpServerInterceptor` применяет этот преобразователь глобально в HTTP-конвейере.

## Устранение неполадок { #troubleshooting }

**Валидация не срабатывает:**

- Убедитесь, что `ValidationModule` включен в граф приложения.
- Убедитесь, что сам метод контроллера аннотирован `@Validate`.
- Для DTO запросов убедитесь, что параметр метода аннотирован `@Valid`.
- Помните, что `@Validate` работает через сгенерированный AOP-код. В Java валидируемый класс не должен быть `final`.
- В Kotlin валидируемый класс и валидируемые методы должны быть `open`.

**Я хочу увидеть, где валидация действительно происходит:**

- Запустите `./gradlew clean classes`.
- Откройте сгенерированный исходник:

  ```text
  guides/guide-validation-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.java
  guides/kotlin/guide-kotlin-validation-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.kt
  ```

- Изучите, как заместитель валидирует аргументы перед делегированием в исходный метод контроллера.

**HTTP возвращает исключение вместо JSON:**

- Убедитесь, что зарегистрированы и `ViolationExceptionHttpServerResponseMapper`, и `ValidationHttpServerInterceptor`.
- Убедитесь, что перехватчик помечен `@Tag(HttpServerModule.class)` в Java или `@Tag(HttpServerModule::class)` в Kotlin.

**Валидация кажется правильной, но конечная точка все равно возвращает 404:**

- Обычно это означает, что валидация прошла и запрос дошел до обычной логики приложения.
- Например, в этом руководстве `updateUser("999", ...)` все еще может вернуть `404 User not found`, потому что формат пути допустим, хотя пользователь не существует.

**Сборка Gradle зависает или блокирует файлы в Windows:**

- Запустите `./gradlew --stop` и повторите попытку.
- Если вы видите `AccessDeniedException` на кэшах Gradle или выходных каталогах сборки, закройте среда разработки или тестовые процессы, которые еще могут удерживать файловые дескрипторы.

## Что дальше? { #whats-next }

- [База данных JDBC](database-jdbc.md) или [База данных Cassandra](database-cassandra.md), чтобы сохранять провалидированные запросы.
- [Тестирование с JUnit](testing-junit.md), чтобы тестировать валидацию и сопоставление ошибок на уровне компонентов.
- [Тестирование как черный ящик](testing-black-box.md) после добавления хранения данных, чтобы валидацию можно было проверить через упакованное HTTP-приложение.
- [Шаблоны отказоустойчивости](resilient.md), чтобы добавить отказоустойчивость уровня сервиса вокруг провалидированных операций.

## Помощь { #help }

Если вы застряли:

- сравните с [Kora Java Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-validation-app) и [Kora Kotlin Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-validation-app)
- изучите [документацию по валидации](../documentation/validation.md)
- изучите [документацию HTTP-сервера](../documentation/http-server.md)
- изучите [документацию JSON](../documentation/json.md)
