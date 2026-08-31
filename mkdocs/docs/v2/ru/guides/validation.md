---
search:
  exclude: true
title: Валидация с Kora
summary: Continue the HTTP Server guide and add body, path, and query validation with structured JSON validation errors
description: "Step-by-step request validation for a Kora 2.0 HTTP API: the io.koraframework:validation-module artifact and ValidationModule, Kora's own constraint annotations in io.koraframework.validation.common.annotation, @Valid on a record and on a parameter, @Validate for method argument and result validation, the generated $UserRequest_Validator and $UserController__AopProxy sources, ViolationException and Violation.path().full(), and a global ViolationExceptionHttpServerResponseMapper plus ValidationHttpServerInterceptor tagged with @Tag(HttpServer.class)."
agent:
  use_when: "Use this file for questions about validating HTTP input in a Kora 2.0 service: io.koraframework:validation-module, ValidationModule, the Kora constraint annotations (@NotBlank, @NotEmpty, @Pattern, @Size, @Range, @Min, @Max, @Positive, @Negative, @Digits, @OneOf, @UUID, @Uri, @Url, @Past, @Future, @AssertTrue, @AssertFalse), @Valid on types and parameters, @Validate and its failFast attribute, @ValidatedBy custom constraints, Validator and ValidatorFactory, ViolationException, Violation.path().full(), turning violations into HTTP 400 with ViolationExceptionHttpServerResponseMapper and ValidationHttpServerInterceptor bound with @Tag(HttpServer.class), and why Kora validation is not Jakarta Bean Validation."
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
- валидацией path-параметра `userId`
- валидацией query-параметров `page`, `size` и `sort`
- валидацией методов на основе AOP через `@Validate`
- структурированными JSON-ответами при ошибках валидации

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- текстовый редактор или среда разработки
- пройденное руководство [HTTP-сервер](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательная основа"

    Это руководство предполагает, что вы прошли **[HTTP-сервер](http-server.md)** и у вас уже есть готовое CRUD-приложение с `UserController`, `UserService`, `UserRepository` и `InMemoryUserRepository`.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что валидация полезнее всего тогда, когда тело запроса, path-параметры, query-параметры и поток сервиса уже существуют.

## Обзор { #overview }

Валидация защищает границу между внешним входом и поведением приложения. Контроллер может десериализовать JSON в DTO, но десериализация доказывает лишь то, что у полезной нагрузки правильная общая
форма. Она не доказывает, что email выглядит как email, что имя не пустое, что размер страницы в допустимых пределах или что path-параметр имеет ожидаемый формат.

Без валидации приложение принимает плохой вход и оставляет обнаружение проблемы более глубоким слоям. Обычно это дает менее внятные ошибки, более оборонительный код сервисов и правила данных,
разбросанные по всей кодовой базе. С валидацией API может отклонить неверный вход рано и вернуть ответ, который явно относится к запросу клиента.

!!! warning "Валидация Kora — это не Jakarta Bean Validation"

    Kora поставляет собственный API валидации в `io.koraframework.validation.common.annotation`. Имена аннотаций намеренно выглядят знакомо, но это собственные типы Kora, они обеспечиваются
    сгенерированным на этапе компиляции кодом, а не рефлексивным рантаймом, и они **не** взаимозаменяемы с `jakarta.validation.constraints`. Импорт одноименной Jakarta-аннотации дает класс, который
    компилируется и молча ничего не валидирует.

### Как валидация вписывается в HTTP API { #validation-fits-http-api }

В слоеном HTTP-приложении валидация обычно защищает границу, через которую внешний вход попадает в систему.

Это значит:

- контроллер валидирует тела запросов, path-параметры и query-параметры
- сервис продолжает заниматься бизнес-логикой
- репозиторий продолжает заниматься хранением

Такое разделение полезно, потому что неверный HTTP-вход обычно нужно отклонять до того, как он дойдет до более глубоких слоев. Оно же делает правила валидации проще для поиска и понимания.

Kora поддерживает здесь два стиля:

- декларативную валидацию через аннотации вроде `@Valid` и `@Validate`
- императивное использование через внедрение сгенерированного `Validator<T>` и самостоятельный вызов `validate(...)` или `validateAndThrow(...)`, как описано в [Ручной валидации](../documentation/validation.md#manual-validation)

В этом руководстве мы используем декларативный подход на контроллере, потому что он — самое естественное продолжение `http-server.md`.

### Валидация на границе { #validation-at-boundary }

Лучшее место для базовой валидации входа — граница API. Если неверные данные отклоняются до того, как дойдут до слоя сервиса, остальная часть приложения может работать с более сильными допущениями. В
этом руководстве валидация появляется в трех местах:

- DTO тела запроса, где можно ограничить поля вроде `name` и `email`
- path-параметры, где можно проверить значения маршрута вроде `userId`
- query-параметры, где можно ограничить вход постраничной выдачи и сортировки

Это не заменяет бизнес-валидацию. Правило DTO может сказать «email должен быть синтаксически корректным», а правило сервиса — «этот email должен быть уникальным». Это разные слои валидации.

### Аннотации ограничений { #constraint-annotations }

Набор заметно шире тех четырех ограничений, которые понадобились этому руководству. Все они живут в `io.koraframework.validation.common.annotation` и могут стоять на поле, методе или параметре метода:

| Группа     | Аннотации                                                                            |
|------------|--------------------------------------------------------------------------------------|
| Текст      | `@NotBlank`, `@Pattern`, `@Size`, `@OneOf`, `@UUID`, `@Uri`, `@Url`                   |
| Числа      | `@Min`, `@Max`, `@Range`, `@Positive`, `@PositiveOrZero`, `@Negative`, `@NegativeOrZero`, `@Digits` |
| Время      | `@Past`, `@PastOrPresent`, `@Future`, `@FutureOrPresent`                              |
| Логические | `@AssertTrue`, `@AssertFalse`                                                         |
| Коллекции  | `@NotEmpty`, `@Size`                                                                  |
| Структура  | `@Valid`, `@Validate`, `@ValidatedBy`                                                 |

`@Valid` и `@Validate` — не ограничения: `@Valid` говорит «спустись внутрь этого типа и примени его собственные правила», а `@Validate` включает валидацию методов. `@ValidatedBy` — точка расширения,
через которую вы строите собственное ограничение поверх своей `ValidatorFactory`. Полный справочник, включая точные сообщения о нарушениях для каждого ограничения, — в
[Аннотациях валидации](../documentation/validation.md#validation-annotations).

### Сгенерированная валидация и `@Validate` { #generated-validation-validate }

Полные правила для сгенерированных валидаторов, валидации классов и валидации методов описаны в [Валидации класса](../documentation/validation.md#class-validation) и [Валидации метода](../documentation/validation.md#method-validation).

Валидация Kora использует аннотации для описания ограничений и сгенерированный код для их применения. `@Valid` на типе генерирует реализацию `Validator<T>` для него, `@Validate` включает валидацию
методов, а модуль валидации добавляет необходимые компоненты графа. Поскольку обвязка валидации генерируется, отсутствующие валидаторы или неподдерживаемые формы обнаруживаются на этапе сборки, а не
только после того, как плохой запрос доберется до промышленной среды.

Это руководство также заглядывает в сгенерированный AOP-код, чтобы вы видели, где валидация действительно выполняется. Это важно, потому что валидация — не магия, спрятанная внутри разбора JSON. Это
сгенерированная граничная проверка вокруг методов контроллера.

Практический порядок такой:

1. включить модуль валидации в граф Kora
2. добавить ограничения в DTO запросов
3. включить валидацию методов через `@Validate`
4. провалидировать тело, path- и query-вход
5. изучить сгенерированную обертку валидации
6. отобразить ошибки валидации на стабильный JSON-ответ

### Контракты ошибок { #error-contracts }

Ошибки валидации — это клиентские ошибки, но клиентам нужно больше, чем сырое сообщение исключения. Полезный API возвращает предсказуемую форму ответа, которая говорит клиенту, какой вход не прошел и
почему. Последняя часть этого руководства добавляет JSON-контракт ошибок, чтобы ошибки валидации стали частью публичного HTTP-поведения, а не случайным выводом фреймворка.

## Зависимости { #dependencies }

Валидация в этом руководстве опирается на несколько совместно работающих модулей Kora:

- `validation-module` включает генерацию валидаторов, валидацию методов и HTTP-перехватчик, превращающий нарушения в ответы
- `http-server-undertow` публикует контроллер как HTTP-эндпоинты
- `json-common` сериализует DTO запросов и ответов
- `config-hocon` и `logging-logback` дают стандартную рантайм-обвязку, используемую во всех руководствах

Для более широкого контекста смотрите документацию Kora по [Валидации](../documentation/validation.md), [HTTP-серверу](../documentation/http-server.md)
и [JSON](../documentation/json.md).

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies from http-server.md ...

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")
        implementation("io.koraframework:validation-module")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies from http-server.md ...

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")
        implementation("io.koraframework:validation-module")
    }
    ```

Артефакт валидации один, а не два. `validation-module` приносит с собой `validation-common`, а генератор кода живет в артефакте `annotation-processors` / `symbol-processors`, который вы уже
подключили.

## Модули { #modules }

Прежде чем заработают любые аннотации валидации, графу приложения нужен `ValidationModule`.

На этом шаге мы включаем только сам модуль. Собственную HTTP-обработку ошибок валидации мы добавим позже, когда сам поток валидации уже станет понятен.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/io/koraframework/guide/validation/Application.java`:

    ```java
    package io.koraframework.guide.validation;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;
    import io.koraframework.validation.module.ValidationModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            ValidationModule,  // <----- Connected module
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/io/koraframework/guide/validation/Application.kt`:

    ```kotlin
    package io.koraframework.guide.validation

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule
    import io.koraframework.validation.module.ValidationModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        ValidationModule,  // <----- Connected module
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Валидация модели { #model-validation }

Проще всего начать с того же тела запроса, которое уже используют `createUser` и `updateUser`.

Это валидация объекта. Вместо того чтобы проверять каждое JSON-поле прямо в методе контроллера, мы описываем правила один раз внутри `UserRequest`.

В этом руководстве:

- `name` должно присутствовать, быть непустым и разумного размера
- `email` должен присутствовать и соответствовать простому шаблону email

Это дает хороший первый пример валидации DTO без изменения общего CRUD-дизайна из предыдущего руководства.

===! ":fontawesome-brands-java: `Java`"

    Создайте или обновите `src/main/java/io/koraframework/guide/validation/dto/UserRequest.java`:

    ```java
    package io.koraframework.guide.validation.dto;

    import io.koraframework.json.common.annotation.Json;
    import io.koraframework.validation.common.annotation.NotBlank;
    import io.koraframework.validation.common.annotation.Valid;
    import io.koraframework.validation.common.annotation.Pattern;
    import io.koraframework.validation.common.annotation.Size;

    @Json
    @Valid
    public record UserRequest(
        @NotBlank @Size(min = 2, max = 100) String name,
        @NotBlank @Pattern("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$") String email
    ) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте или обновите `src/main/kotlin/io/koraframework/guide/validation/dto/UserRequest.kt`:

    ```kotlin
    package io.koraframework.guide.validation.dto

    import io.koraframework.json.common.annotation.Json
    import io.koraframework.validation.common.annotation.NotBlank
    import io.koraframework.validation.common.annotation.Pattern
    import io.koraframework.validation.common.annotation.Size
    import io.koraframework.validation.common.annotation.Valid

    @Json
    @Valid
    data class UserRequest(
        @field:NotBlank
        @field:Size(min = 2, max = 100)
        val name: String,
        @field:NotBlank
        @field:Pattern("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
        val email: String
    )
    ```

Именно `@Valid` на самом типе заставляет обработчик аннотаций выпустить компонент `Validator<UserRequest>` с именем `$UserRequest_Validator`. Без него ограничения полей бездействуют: валидатор никто
не генерирует, и в графе нечего внедрить, чтобы их выполнить.

В Kotlin обязателен use-site target `@field:`. Голая `@NotBlank` на свойстве конструктора попадет на параметр конструктора, а не на поле, и обработчик ее не увидит.

Обратите внимание, что на этом шаге мы только описали правила. Их еще нужно применить на границе контроллера, чем мы и займемся дальше.

## Валидация контроллера { #controller-validation }

Связка `@Valid` и `@Validate` опирается на правила из [Валидации класса](../documentation/validation.md#class-validation) и [Валидации метода](../documentation/validation.md#method-validation).

Теперь мы подключаем эти правила DTO к настоящим HTTP-эндпоинтам из `http-server.md`.

Здесь важнее всего две аннотации:

- `@Valid` на параметре говорит, что аргумент-составной объект нужно провалидировать сгенерированным валидатором этого DTO
- `@Validate` включает валидацию на уровне самого метода контроллера

`@Validate` важна, потому что она велит Kora сгенерировать логику валидации вокруг вызова метода. `@Valid` важна, потому что она велит этой сгенерированной логике спуститься внутрь объекта
`UserRequest` и провалидировать его поля.

===! ":fontawesome-brands-java: `Java`"

    Обновите методы `POST` и `PUT` в `src/main/java/io/koraframework/guide/validation/controller/UserController.java`:

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

    Обновите те же методы в `src/main/kotlin/io/koraframework/guide/validation/controller/UserController.kt`:

    ```kotlin
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    @Json
    @Validate
    open fun createUser(@Valid @Json request: UserRequest): HttpResponseEntity<UserResponse> {
        val user = userService.createUser(request)
        return HttpResponseEntity.of(201, HttpHeaders.of(), user)
    }

    @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
    @Json
    @Validate
    open fun updateUser(
        @Path userId: String,
        @Valid @Json request: UserRequest
    ): HttpResponseEntity<UserResponse> {
        val updated = userService.updateUser(userId, request)
        return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updated)
    }
    ```

На этом этапе:

- некорректный JSON по-прежнему падает на этапе разбора JSON
- корректный JSON с неверными значениями полей теперь падает на этапе валидации
- корректный JSON продолжает идти в тот же поток сервиса и репозитория, который вы построили раньше

По умолчанию `@Validate` собирает все нарушения перед тем, как выбросить исключение. Если вы предпочитаете останавливаться на первом, используйте `@Validate(failFast = true)`: сгенерированный код тогда
выбрасывает исключение, как только не прошло одно ограничение, — это дешевле, но сообщает лишь об одной проблеме на запрос.

После компиляции сгенерированный AOP-прокси показывает, как `@Valid` делегирует сгенерированному валидатору `UserRequest` до вызова метода контроллера:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-validation-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/validation/controller/$UserController__AopProxy.java
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
    guides/kotlin/kora-kotlin-guide-validation-app/build/generated/ksp/main/kotlin/io/koraframework/guide/validation/controller/$UserController__AopProxy.kt
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

Важная деталь: `validator6.validate(request, ...)` выполняется до `super.createUser(request)`, поэтому неверные поля DTO никогда не доходят до тела вашего контроллера. `validator6` — это внедренный
`$UserRequest_Validator`; нумерация лишь отражает порядок, в котором прокси выделил поля валидаторов.

### Path-параметры { #path-parameters }

Тела запросов — не единственный источник неверного входа. Path-параметры тоже могут быть неправильными.

В этом руководстве `userId` приходит из репозитория в памяти, который использует числовые строковые идентификаторы вроде `1`, `2` и `3`. Так что это допущение можно выразить в контроллере явно:

- `@NotBlank` отклоняет пустые идентификаторы
- `@Pattern("^\\d+$")` говорит, что значение пути должно состоять только из цифр

Это валидация аргументов метода, а не DTO. Она полезна, когда данные простые и не оправдывают создание отдельного объекта только ради валидации.

===! ":fontawesome-brands-java: `Java`"

    Обновите методы `GET`, `PUT` и `DELETE` в `src/main/java/io/koraframework/guide/validation/controller/UserController.java`:

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

    Обновите те же методы в `src/main/kotlin/io/koraframework/guide/validation/controller/UserController.kt`:

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    @Validate
    open fun getUser(@Path @NotBlank @Pattern("^\\d+$") userId: String): UserResponse {
        return userService.getUser(userId)
            ?: throw HttpServerResponseException.of(404, "User not found")
    }

    @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
    @Json
    @Validate
    open fun updateUser(
        @Path @NotBlank @Pattern("^\\d+$") userId: String,
        @Valid @Json request: UserRequest
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

Ограничениям на параметрах не нужен target `@field:`, который понадобился свойствам DTO: здесь аннотация уже стоит на параметре, а это один из целевых элементов, объявленных каждым ограничением Kora.

Такая валидация особенно полезна для переменных пути, заголовков, cookie и других простых параметров, которым не место внутри DTO запроса.

После компиляции сгенерированный прокси показывает, как ограничения path-параметра превращаются в обычные вызовы валидаторов:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-validation-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/validation/controller/$UserController__AopProxy.java
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
    guides/kotlin/kora-kotlin-guide-validation-app/build/generated/ksp/main/kotlin/io/koraframework/guide/validation/controller/$UserController__AopProxy.kt
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

Это делает границу метода наглядной: Kora сначала валидирует `userId`, а затем делегирует вашей исходной реализации `getUser(...)`. Каждое ограничение становится отдельным вызовом `validate(...)`,
поэтому две аннотации на одном параметре дают `_argConstResult_userId_1` и `_argConstResult_userId_2`.

### Query-параметры { #query-parameters }

Следующая частая цель валидации — строка запроса.

Наш эндпоинт `GET /users` уже поддерживает постраничную выдачу и сортировку. Это делает его хорошим местом для демонстрации валидации параметров метода для необязательных значений:

- `page` необязателен, но если присутствует, должен быть не меньше `0`
- `size` необязателен, но если присутствует, должен оставаться в безопасном диапазоне
- `sort` необязателен, но если присутствует, должен быть одним из поддерживаемых полей сортировки

Такая валидация защищает API от неверных запросов постраничной выдачи до того, как выполнится любая бизнес-логика или логика хранения.

===! ":fontawesome-brands-java: `Java`"

    Обновите `getUsers` в `src/main/java/io/koraframework/guide/validation/controller/UserController.java`:

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

    Обновите `getUsers` в `src/main/kotlin/io/koraframework/guide/validation/controller/UserController.kt`:

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/users")
    @Json
    @Validate
    open fun getUsers(
        @Query("page") @Range(from = 0.0, to = 1_000.0) page: Int?,
        @Query("size") @Range(from = 1.0, to = 100.0) size: Int?,
        @Query("sort") @Pattern("^(?i)(name|email|createdat)$") sort: String?
    ): List<UserResponse> {
        val pageNum = page ?: 0
        val pageSize = size ?: 10
        val sortBy = sort ?: "name"
        return userService.getUsers(pageNum, pageSize, sortBy)
    }
    ```

`@Range` объявляет `from` и `to` как `double`. Java расширяет целочисленные литералы за вас, а Kotlin — нет, поэтому в версии на Kotlin написано `0.0` и `1_000.0`. У `@Range` есть еще атрибут
`boundary` (по умолчанию `INCLUSIVE_INCLUSIVE`, плюс три другие комбинации), когда границу нужно исключить.

Необязательными эти параметры делает допустимость `null`. В Java параметр помечен `@Nullable`, в Kotlin у него тип `Int?`. Сгенерированный код проверяет `null` перед валидацией, так что пропущенный
query-параметр никогда не становится нарушением.

После этого шага руководство охватывает три разные цели валидации в отдельных главах:

- составные JSON-объекты
- простые path-параметры
- простые query-параметры

Такое разделение полезно, потому что каждый вид входа в реальных API развивается по-своему.

После компиляции сгенерированный прокси показывает, что необязательные query-параметры валидируются только при наличии значения:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-validation-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/validation/controller/$UserController__AopProxy.java
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
    guides/kotlin/kora-kotlin-guide-validation-app/build/generated/ksp/main/kotlin/io/koraframework/guide/validation/controller/$UserController__AopProxy.kt
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

Этот сгенерированный код точно объясняет поведение с необязательными значениями: `null` означает «параметр не передан», а присутствующее значение проверяется своим ограничением.

## Сгенерированный код { #generated-code }

Валидация порождает два вида сгенерированных исходников, и их полезно различать.

`@Valid` на типе порождает **класс-валидатор**. Для `UserRequest` это `$UserRequest_Validator` — `Validator<UserRequest>`, опубликованный в графе. Это обычный компонент: его можно внедрить куда угодно
и вызвать `validate(value)` или `validateAndThrow(value)` вообще без участия AOP.

`@Validate` на методе порождает **AOP-прокси**. Kora не меняет исходник вашего контроллера напрямую. Вместо этого она генерирует класс-наследник вокруг валидируемого компонента и помещает логику
валидации в этот сгенерированный класс. Ваш код по-прежнему выглядит просто, но сгенерированный прокси выполняет проверки до того, как вызов дойдет до тела метода.

Именно поэтому:

- валидируемые Java-классы не должны быть `final`
- валидируемые Kotlin-классы должны быть `open`
- валидируемые Kotlin-методы тоже должны быть `open`

После компиляции сгенерированный исходник можно посмотреть здесь:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-validation-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/validation/controller/$UserController__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-validation-app/build/generated/ksp/main/kotlin/io/koraframework/guide/validation/controller/$UserController__AopProxy.kt
    ```

Этот файл — самое простое место, чтобы увидеть реальный поток валидации. Вы обнаружите, что Kora:

- читает входящие аргументы метода
- валидирует простые параметры метода вроде `userId`, `page`, `size` и `sort`
- валидирует вложенные объекты вроде `UserRequest`
- выбрасывает `ViolationException`, когда правила не выполнены
- вызывает ваш исходный метод контроллера только при успешной валидации

В предыдущих главах сгенерированные фрагменты показывались рядом с той целью валидации, которая их породила: валидация DTO тела, валидация path-параметров и валидация query-параметров. Урок во всех
случаях один: валидация происходит до логики вашего контроллера, а вызов `super...` появляется только после того, как нарушения собраны. Этот сгенерированный код — еще и хорошая цель для отладки
AI-ассистентами, потому что он раскрывает конкретные валидаторы и имена параметров, которые Kora вывела из ваших аннотаций.

Это помогает, когда вы учитесь, отлаживаете или просто хотите подтвердить, что именно фреймворк вам сгенерировал. Более широкие подробности — в документации Kora по
[Валидации](../documentation/validation.md) и [Контейнеру](../documentation/container.md).

## Обработка ошибок валидации { #validation-errors }

Настройка HTTP-ответа здесь связывает валидацию с общими правилами [обработки ошибок HTTP-сервера](../documentation/http-server.md#error-handling) и полностью описана в разделе
[HTTP-ответ валидации](../documentation/validation.md#validation-response-http).

Пока что валидация работает, но опыт HTTP-клиента можно улучшить.

`ValidationModule` уже добавляет `ValidationHttpServerInterceptor` как `@DefaultComponent`, и этот перехватчик уже превращает `ViolationException` в `400` с сообщением исключения. Чего он не делает —
так это не привязывает себя к серверу и не формирует машиночитаемое тело. В реальном API обычно лучше возвращать стабильный JSON-контракт ошибок, который клиенты могут разобрать и показать.

Kora дает здесь гибкость. Такую обработку можно определить только для выбранных эндпоинтов или зарегистрировать глобально для всего HTTP-приложения. В этом руководстве мы используем глобальный подход,
потому что так проще всего сохранить согласованность всех контроллеров.

Мы добавим:

- `ValidationErrorDetails` и `ValidationErrorResponse` как явные JSON-DTO
- `ViolationExceptionHttpServerResponseMapper`, чтобы превратить `ViolationException` в это DTO
- `ValidationHttpServerInterceptor` с меткой `@Tag(HttpServer.class)`, чтобы применить это отображение в HTTP-конвейере

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/validation/dto/ValidationErrorDetails.java`:

    ```java
    package io.koraframework.guide.validation.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record ValidationErrorDetails(String field, String message) {}
    ```

    Создайте `src/main/java/io/koraframework/guide/validation/dto/ValidationErrorResponse.java`:

    ```java
    package io.koraframework.guide.validation.dto;

    import java.util.List;
    import io.koraframework.json.common.annotation.Json;

    @Json
    public record ValidationErrorResponse(String code, String message, List<ValidationErrorDetails> errors) {

        public static ValidationErrorResponse of(List<ValidationErrorDetails> errors) {
            return new ValidationErrorResponse("VALIDATION_ERROR", "Validation failed", errors);
        }
    }
    ```

    Обновите `src/main/java/io/koraframework/guide/validation/Application.java`:

    ```java
    package io.koraframework.guide.validation;

    import java.util.List;
    import java.util.stream.Collectors;
    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.guide.validation.dto.ValidationErrorDetails;
    import io.koraframework.guide.validation.dto.ValidationErrorResponse;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.HttpServer;
    import io.koraframework.http.server.common.response.HttpServerResponse;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonWriter;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;
    import io.koraframework.validation.common.Violation;
    import io.koraframework.validation.module.ValidationModule;
    import io.koraframework.validation.module.http.server.ValidationHttpServerInterceptor;
    import io.koraframework.validation.module.http.server.ViolationExceptionHttpServerResponseMapper;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            ValidationModule,  // <----- Connected module
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

        default ViolationExceptionHttpServerResponseMapper violationExceptionHttpServerResponseMapper(
                JsonWriter<ValidationErrorResponse> errorResponseJsonWriter) {
            return (request, exception) -> HttpServerResponse.of(
                    400,
                    HttpBody.json(errorResponseJsonWriter.toByteArray(
                            ValidationErrorResponse.of(toValidationErrors(exception.getViolations())))));
        }

        @Tag(HttpServer.class)
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

    Создайте `src/main/kotlin/io/koraframework/guide/validation/dto/ValidationErrorDetails.kt`:

    ```kotlin
    package io.koraframework.guide.validation.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class ValidationErrorDetails(
        val field: String,
        val message: String
    )
    ```

    Создайте `src/main/kotlin/io/koraframework/guide/validation/dto/ValidationErrorResponse.kt`:

    ```kotlin
    package io.koraframework.guide.validation.dto

    import io.koraframework.json.common.annotation.Json

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

    Обновите `src/main/kotlin/io/koraframework/guide/validation/Application.kt`:

    ```kotlin
    package io.koraframework.guide.validation

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.common.annotation.Tag
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.guide.validation.dto.ValidationErrorDetails
    import io.koraframework.guide.validation.dto.ValidationErrorResponse
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.HttpServer
    import io.koraframework.http.server.common.response.HttpServerResponse
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonWriter
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule
    import io.koraframework.validation.common.Violation
    import io.koraframework.validation.module.ValidationModule
    import io.koraframework.validation.module.http.server.ValidationHttpServerInterceptor
    import io.koraframework.validation.module.http.server.ViolationExceptionHttpServerResponseMapper

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        ValidationModule,  // <----- Connected module
        UndertowPublicHttpServerModule {

        fun violationExceptionHttpServerResponseMapper(
            errorResponseJsonWriter: JsonWriter<ValidationErrorResponse>
        ): ViolationExceptionHttpServerResponseMapper {
            return ViolationExceptionHttpServerResponseMapper { _, exception ->
                HttpServerResponse.of(
                    400,
                    HttpBody.json(
                        errorResponseJsonWriter.toByteArray(
                            ValidationErrorResponse.of(toValidationErrors(exception.violations))
                        )
                    )
                )
            }
        }

        // the module default is untagged, so it is overridden only to bind the interceptor to the server;
        // 2.0 declares the mapper parameter as @Nullable, which Kotlin enforces on the override
        @Tag(HttpServer::class)
        override fun validationHttpServerInterceptor(
            violationExceptionHttpServerResponseMapper: ViolationExceptionHttpServerResponseMapper?
        ): ValidationHttpServerInterceptor {
            return ValidationHttpServerInterceptor(violationExceptionHttpServerResponseMapper)
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
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

В этой обвязке стоит выделить три детали.

Метка — это `HttpServer` из `io.koraframework.http.server.common`, маркер, по которому модуль Undertow собирает глобальные перехватчики. Непомеченный `ValidationHttpServerInterceptor` компилируется и
собирается нормально, но никогда не выполняется — ровно таков и собственный `@DefaultComponent` модуля: доступен, но ни к какому серверу не подключен.

`ViolationExceptionHttpServerResponseMapper` — функциональный интерфейс, возвращающий `@Nullable HttpServerResponse`. Возврат `null` из него — осознанный отказ от обработки этого запроса: перехватчик
откатывается к простому `400` с сообщением исключения.

`Violation.path().full()` дает полный точечный путь к неверному значению, например `request.email`. В этом примере он обрезается до последнего сегмента, чтобы в JSON попало `email`; оставьте полный
путь, если вашим клиентам нужно находить значение внутри вложенного объекта.

Важное разделение здесь такое:

- AOP-валидация решает, корректен ли вызов метода
- перехватчик и маппер решают, как сбой видит HTTP-клиент

## Запуск приложения { #run-app }

Используйте стандартный порядок из руководств:

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

- Добавляйте валидацию на границе контроллера, когда цель — защитить HTTP-вход.
- Используйте валидацию DTO для структурированных JSON-тел и валидацию параметров метода для простых path- или query-значений.
- Импортируйте ограничения из `io.koraframework.validation.common.annotation`, но не из `jakarta.validation.constraints`. Имена пересекаются, поведение — нет.
- Ставьте `@Valid` и на тип DTO, и на параметр: аннотация на типе генерирует валидатор, а аннотация на параметре его вызывает.
- Держите `UserService` и `UserRepository` сосредоточенными на бизнес-логике и хранении, а не дублируйте там правила HTTP-входа.
- Помните, что `@Validate` основана на AOP. В Java валидируемый класс не должен быть `final`. В Kotlin класс и валидируемые методы должны быть `open`.
- Когда ошибка валидации должна стать стабильным контрактом API, определите явное DTO ошибки вместо утечки сырых исключений фреймворка.
- В Kotlin продолжайте использовать `@field:` для аннотаций свойств вроде `@field:NotBlank`, `@field:Size` и `@field:Pattern`.

## Итоги { #summary }

Вы постепенно расширили CRUD-приложение из `http-server.md` валидацией.

Сначала вы включили `ValidationModule` в граф приложения. Затем провалидировали тело `UserRequest`, используемое `createUser` и `updateUser`. После этого провалидировали path-параметры `userId` и
query-параметры постраничной выдачи и сортировки в `getUsers`. Затем изучили сгенерированный AOP-исходник, чтобы увидеть, где на самом деле выполняется валидация методов. Наконец, вы ввели глобальную
стратегию отображения ошибок валидации с `ViolationExceptionHttpServerResponseMapper` и `ValidationHttpServerInterceptor` с меткой `@Tag(HttpServer.class)`.

## Ключевые понятия { #key-concepts }

- Валидация Kora — это собственный API Kora в `io.koraframework.validation.common.annotation`, генерируемый на этапе компиляции, а не Jakarta Bean Validation.
- `ValidationModule` включает поддержку валидации Kora в графе приложения.
- `@Valid` на типе генерирует `Validator<T>`; `@Valid` на параметре велит валидации метода его использовать.
- `@Validate` включает валидацию аргументов и результата метода через сгенерированный AOP-код, а `@Validate(failFast = true)` останавливается на первом нарушении.
- Валидация DTO и валидация параметров метода решают разные задачи и часто используются вместе.
- `ViolationExceptionHttpServerResponseMapper` определяет, как ошибки валидации становятся HTTP-ответами.
- `ValidationHttpServerInterceptor` применяет этот маппер глобально, но только когда он помечен `@Tag(HttpServer.class)`.

## Устранение неполадок { #troubleshooting }

**Валидация не срабатывает:**

- Убедитесь, что `ValidationModule` включен в граф приложения.
- Убедитесь, что сам метод контроллера помечен `@Validate`.
- Для DTO запросов убедитесь, что параметр метода помечен `@Valid`, а тип DTO — тоже `@Valid`.
- Проверьте импорты: `io.koraframework.validation.common.annotation.NotBlank`, а не `jakarta.validation.constraints.NotBlank`.
- Помните, что `@Validate` работает через сгенерированный AOP-код. В Java валидируемый класс не должен быть `final`.
- В Kotlin валидируемый класс и валидируемые методы должны быть `open`, а ограничениям свойств нужен target `@field:`.

**`Validator<UserRequest> not found` при сборке графа:**

- У типа DTO нет собственной `@Valid`. Только аннотация `@Valid` на типе заставляет обработчик выпустить `$UserRequest_Validator`.

**Хочу увидеть, где валидация выполняется на самом деле:**

- Выполните `./gradlew clean classes`.
- Откройте сгенерированный исходник по пути:

  ```text
  guides/java/kora-java-guide-validation-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/validation/controller/$UserController__AopProxy.java
  guides/kotlin/kora-kotlin-guide-validation-app/build/generated/ksp/main/kotlin/io/koraframework/guide/validation/controller/$UserController__AopProxy.kt
  ```

- Посмотрите, как прокси валидирует аргументы, прежде чем делегировать вашему исходному методу контроллера.

**HTTP возвращает простой текстовый 400 вместо JSON:**

- Это работает `ValidationHttpServerInterceptor` из модуля по умолчанию, без маппера. Убедитесь, что ваш собственный `ViolationExceptionHttpServerResponseMapper` зарегистрирован.
- Убедитесь, что перехватчик помечен `@Tag(HttpServer.class)` в Java или `@Tag(HttpServer::class)` в Kotlin. Без метки он никогда не подключается к серверу.

**Kotlin отказывается компилировать переопределение перехватчика:**

- `ValidationModule` объявляет параметр маппера как `@Nullable`, поэтому переопределение в Kotlin должно принимать `ViolationExceptionHttpServerResponseMapper?`.

**Kotlin отвергает `@Range(from = 0, to = 1_000)`:**

- `from` и `to` имеют тип `double`. Пишите `0.0` и `1_000.0`.

**Валидация выглядит корректной, но эндпоинт все равно возвращает 404:**

- Обычно это значит, что валидация прошла и запрос дошел до обычной логики приложения.
- Например, в этом руководстве `updateUser("999", ...)` может по-прежнему вернуть `404 User not found`, потому что формат пути корректен, хотя пользователя и не существует.

**Сборка Gradle зависает или блокирует файлы в Windows:**

- Выполните `./gradlew --stop` и повторите.
- Если видите `AccessDeniedException` на кешах Gradle или выходных каталогах сборки, закройте процессы IDE или тестов, которые могут держать файловые дескрипторы.

## Что дальше? { #whats-next }

- [База данных JDBC](database-jdbc.md) или [База данных Cassandra](database-cassandra.md), чтобы сохранять провалидированные запросы.
- [Тестирование с JUnit](testing-junit.md), чтобы протестировать валидацию и отображение ошибок на уровне компонентов.
- [Черноящичное тестирование](testing-black-box.md) после добавления хранения, чтобы валидацию можно было проверить через собранное HTTP-приложение.
- [Шаблоны отказоустойчивости](resilient.md), чтобы добавить отказоустойчивость на уровне сервиса вокруг провалидированных операций.

## Помощь { #help }

Если застряли:

- сравните с [Kora Java Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-validation-app) и [Kora Kotlin Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-validation-app)
- посмотрите [документацию по Валидации](../documentation/validation.md)
- посмотрите [документацию по HTTP-серверу](../documentation/http-server.md)
- посмотрите [документацию по JSON](../documentation/json.md)
