---
search:
  exclude: true
title: Validation with Kora
summary: Continue the HTTP Server guide and add body, path, and query validation with structured JSON validation errors
tags: validation, http-server, json, api
---

# Validation with Kora { #validation-kora }

This guide introduces request validation for Kora HTTP APIs. It covers how constraint annotations describe valid input, how `@Validate` activates generated validators at controller boundaries, and how
validation failures become predictable HTTP errors. You will also see how validation keeps DTO rules close to the data they protect while leaving service and repository code focused on application
behavior.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-validation-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-validation-app).

## What You'll Build { #youll-build }

You will extend the existing HTTP server with:

- request body validation for `createUser` and `updateUser`
- path parameter validation for `userId`
- query parameter validation for `page`, `size`, and `sort`
- AOP-based method validation with `@Validate`
- structured JSON responses for validation failures

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Completed [HTTP Server Guide](http-server.md)

## Prerequisites { #prerequisites }

!!! note "Required Foundation"

    This guide assumes you have completed **[HTTP Server](http-server.md)** and already have the finished CRUD application with `UserController`, `UserService`, `UserRepository`, and `InMemoryUserRepository`.

    If you haven't completed the HTTP server guide yet, do that first, because validation is most useful once the request body, path parameters, query parameters, and service flow already exist.

## Overview { #overview }

[Jakarta Bean Validation](https://jakarta.ee/specifications/bean-validation/) protects the boundary between external input and application behavior. A controller can deserialize JSON into a DTO, but
deserialization only proves that the payload has the right general shape. It does not prove that an email looks like an email, a name is not blank, a page size is within limits, or a path parameter
follows the expected format.

Without validation, the application accepts bad input and lets deeper layers discover the problem later. That usually produces weaker errors, more defensive service code, and data rules that are
scattered across the codebase. With validation, the API can reject invalid input early and return a response that clearly belongs to the client request.

### How Validation Fits into an HTTP API { #validation-fits-http-api }

In a layered HTTP application, validation usually protects the boundary where outside input enters the system.

That means:

- the controller validates request bodies, path parameters, and query parameters
- the service keeps focusing on business logic
- the repository keeps focusing on storage

This separation is useful because invalid HTTP input should usually be rejected before it reaches deeper layers. It also keeps validation rules easier to discover and reason about.

Kora supports two styles here:

- declarative validation through annotations such as `@Valid` and `@Validate`
- imperative usage through validation components described in the Kora [Validation documentation](../documentation/validation.md)

In this guide we use the declarative controller-based approach because it is the most natural continuation of `http-server.md`.

### Validation at the Boundary { #validation-at-boundary }

The best place for basic input validation is the API boundary. If invalid data is rejected before it reaches the service layer, the rest of the application can work with stronger assumptions. In this
guide, validation appears in three places:

- request body DTOs, where fields such as `name` and `email` can be constrained
- path parameters, where route values such as `userId` can be checked
- query parameters, where pagination and sorting input can be limited

This does not replace business validation. A DTO rule can say "email must be syntactically valid"; a service rule might say "this email must be unique". Those are different layers of validation.

### Generated Validation and `@Validate` { #generated-validation-validate }

The full rules for generated validators, class validation, and method validation are covered in [Class validation](../documentation/validation.md#class-validation) and [Method validation](../documentation/validation.md#method-validation).

Kora validation uses annotations to describe constraints and generated code to enforce them. `@Validate` activates method validation, and the validation module contributes the required graph
components. Because validation wiring is generated, missing validators or unsupported shapes are found during build time rather than discovered only after a bad request reaches production.

This guide also looks at generated AOP code so you can see where validation actually runs. That matters because validation is not magic hidden inside JSON parsing. It is a generated boundary check
around controller methods.

The practical flow is:

1. enable the validation module in the Kora graph
2. add constraints to request DTOs
3. activate method validation with `@Validate`
4. validate body, path, and query inputs
5. inspect the generated validation wrapper
6. map validation failures to a stable JSON error response

### Error Contracts { #error-contracts }

Validation failures are client errors, but clients need more than a raw exception message. A useful API returns a predictable response shape that tells the client which input failed and why. The final
part of this guide adds a JSON error contract so validation failures become part of the public HTTP behavior instead of accidental framework output.

## Dependencies { #dependencies }

Validation in this guide relies on a few Kora modules working together:

- `validation-module` enables validator generation and method validation
- `http-server-undertow` exposes the controller as HTTP endpoints
- `json-module` serializes request and response DTOs
- `config-hocon` and `logging-logback` provide the standard runtime setup used across the guides

For more background, see the Kora [Validation documentation](../documentation/validation.md), [HTTP Server documentation](../documentation/http-server.md)
and [JSON documentation](../documentation/json.md).

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

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

    Update `build.gradle.kts`:

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

## Modules { #modules }

Before any validation annotations can work, the application graph needs `ValidationModule`.

At this point we only enable the module itself. We will add custom HTTP handling for validation failures later, after the actual validation flow is already clear.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/guide/validation/Application.java`:

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
            ValidationModule,  // <----- Connected module
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/guide/validation/Application.kt`:

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
        ValidationModule,  // <----- Connected module
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Model Validation { #model-validation }

The easiest place to start is the same request body already used by `createUser` and `updateUser`.

This is object validation. Instead of validating each JSON field directly on the controller method, we describe the rules once inside `UserRequest`.

In this guide:

- `name` must be present, not blank, and reasonably sized
- `email` must be present and match a simple email pattern

That gives us a good first example of DTO validation without changing the overall CRUD design from the previous guide.

===! ":fontawesome-brands-java: `Java`"

    Create or update `src/main/java/ru/tinkoff/kora/guide/validation/dto/UserRequest.java`:

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

    Create or update `src/main/kotlin/ru/tinkoff/kora/guide/validation/dto/UserRequest.kt`:

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

Notice that at this step we only described the rules. They still need to be applied at the controller boundary, which we do next.

## Controller Validation { #controller-validation }

The `@Valid` plus `@Validate` combination relies on the rules from [Class validation](../documentation/validation.md#class-validation) and [Method validation](../documentation/validation.md#method-validation).

Now we connect those DTO rules to the real HTTP endpoints from `http-server.md`.

This is where two annotations matter most:

- `@Valid` says that the complex object argument should be validated using the generated validator for that DTO
- `@Validate` turns on method-level validation for the controller method itself

`@Validate` is important because it tells Kora to generate validation logic around the method call. `@Valid` is important because it tells that generated logic to descend into the `UserRequest` object
and validate its fields.

===! ":fontawesome-brands-java: `Java`"

    Update the `POST` and `PUT` methods in `src/main/java/ru/tinkoff/kora/guide/validation/controller/UserController.java`:

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

    Update the same methods in `src/main/kotlin/ru/tinkoff/kora/guide/validation/controller/UserController.kt`:

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

At this point:

- malformed JSON still fails at JSON parsing time
- well-formed JSON with invalid field values now fails at validation time
- valid JSON continues into the same service and repository flow you already built earlier

After compilation, the generated AOP proxy shows how `@Valid` delegates into the generated `UserRequest` validator before the controller method is called:

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

The important detail is that `validator6.validate(request, ...)` runs before `super.createUser(request)`, so invalid DTO fields never reach your controller body.

### Path Parameters { #path-parameters }

Request bodies are not the only source of invalid input. Path parameters can also be wrong.

In this guide, `userId` comes from an in-memory repository that uses numeric string identifiers such as `1`, `2`, and `3`. So we can express that assumption explicitly in the controller:

- `@NotBlank` rejects empty IDs
- `@Pattern("^\\d+$")` says the path value must contain only digits

This is method-argument validation rather than DTO validation. It is useful when the data is simple and does not justify creating a separate object just for validation.

===! ":fontawesome-brands-java: `Java`"

    Update the `GET`, `PUT`, and `DELETE` methods in `src/main/java/ru/tinkoff/kora/guide/validation/controller/UserController.java`:

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

    Update the same methods in `src/main/kotlin/ru/tinkoff/kora/guide/validation/controller/UserController.kt`:

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

This kind of validation is especially useful for path variables, headers, cookies, and other simple parameters that do not naturally live inside a request DTO.

After compilation, the generated proxy shows how path parameter constraints become ordinary validator calls:

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

This makes the method boundary visible: Kora validates `userId` first, then delegates to your original `getUser(...)` implementation.

### Query Parameters { #query-parameters }

The next common validation target is the query string.

Our `GET /users` endpoint already supports pagination and sorting. That makes it a good place to demonstrate method parameter validation for optional values:

- `page` is optional, but if present it must be `0` or greater
- `size` is optional, but if present it must stay in a safe range
- `sort` is optional, but if present it must be one of the supported sort fields

This kind of validation protects the API from invalid paging requests before any business logic or storage logic runs.

===! ":fontawesome-brands-java: `Java`"

    Update `getUsers` in `src/main/java/ru/tinkoff/kora/guide/validation/controller/UserController.java`:

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

    Update `getUsers` in `src/main/kotlin/ru/tinkoff/kora/guide/validation/controller/UserController.kt`:

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

After this step, the guide now covers three different validation targets in separate chapters:

- complex JSON objects
- simple path parameters
- simple query parameters

That separation is useful because each kind of input tends to evolve differently in real APIs.

After compilation, the generated proxy shows that optional query parameters are validated only when present:

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

That generated code explains the optional behavior precisely: null means "parameter omitted", while a present value is checked against its constraint.

## Generated Code { #generated-code }

`@Validate` is an AOP annotation.

That means Kora does not modify your controller source file directly. Instead, it generates a subclass around the validated component and puts the validation logic into that generated class. Your code
still looks simple, but the generated proxy performs the checks before the call reaches your method body.

This is why:

- validated Java classes must not be `final`
- validated Kotlin classes must be `open`
- validated Kotlin methods must also be `open`

After compilation you can inspect the generated source here:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-validation-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-validation-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.kt
    ```

That file is the easiest place to see the real validation flow. You will find that Kora:

- reads the incoming method arguments
- validates simple method parameters such as `userId`, `page`, `size`, and `sort`
- validates nested objects such as `UserRequest`
- throws `ViolationException` when the rules fail
- calls your original controller method only if validation succeeds

The previous chapters showed the generated fragments next to the validation target that produced them: body DTO validation, path parameter validation, and query parameter validation. The important
lesson is the same in each case: validation happens before your controller logic, and the call to `super...` appears only after violations have been collected. That generated code is also a good
debugging target for AI assistants, because it exposes the concrete validators and parameter names that Kora derived from your annotations.

This is helpful when you are learning, debugging, or simply want to confirm what the framework generated for you. For broader details, see the
Kora [Validation documentation](../documentation/validation.md) and [Container documentation](../documentation/container.md).

## Validation Error Handling { #validation-errors }

The HTTP response setup here connects validation with the general [HTTP Server error handling](../documentation/http-server.md#error-handling) rules.

So far validation works, but the HTTP client experience can still be improved.

By default, you may only see framework-level failures. In a real API it is often better to return a stable JSON error contract that clients can parse and display.

Kora gives you flexibility here. You can define such handling only for selected endpoints, or register it globally for the whole HTTP application. In this guide we use the global approach because it
is the easiest way to keep every controller consistent.

We will add:

- `ValidationErrorDetails` and `ValidationErrorResponse` as explicit JSON DTOs
- `ViolationExceptionHttpServerResponseMapper` to turn `ViolationException` into that DTO
- `ValidationHttpServerInterceptor` to apply that mapping in the HTTP pipeline

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/validation/dto/ValidationErrorDetails.java`:

    ```java
    package ru.tinkoff.kora.guide.validation.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record ValidationErrorDetails(String field, String message) {}
    ```

    Create `src/main/java/ru/tinkoff/kora/guide/validation/dto/ValidationErrorResponse.java`:

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

    Update `src/main/java/ru/tinkoff/kora/guide/validation/Application.java`:

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
            ValidationModule,  // <----- Connected module
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

    Create `src/main/kotlin/ru/tinkoff/kora/guide/validation/dto/ValidationErrorDetails.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.validation.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class ValidationErrorDetails(
        val field: String,
        val message: String
    )
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/guide/validation/dto/ValidationErrorResponse.kt`:

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

    Update `src/main/kotlin/ru/tinkoff/kora/guide/validation/Application.kt`:

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
        ValidationModule,  // <----- Connected module
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

The important split here is:

- AOP validation decides whether the method call is valid
- the interceptor and mapper decide how the HTTP client sees the failure

## Run Application { #run-app }

Use the standard guide flow:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

## Check Application { #check-app }

Valid `createUser` request:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Invalid request body:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"","email":"broken-email"}'
```

Expected response shape:

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

Invalid path parameter:

```bash
curl http://localhost:8080/users/abc
```

Expected response shape:

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

Invalid query parameters:

```bash
curl "http://localhost:8080/users?page=-1&size=0&sort=nickname"
```

Expected response shape:

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

## Best Practices { #best-practices }

- Add validation at the controller boundary when the goal is to protect HTTP input.
- Use DTO validation for structured JSON bodies and method parameter validation for simple path or query values.
- Keep `UserService` and `UserRepository` focused on business logic and storage instead of duplicating HTTP input rules there.
- Remember that `@Validate` is AOP-based. In Java the validated class must not be `final`. In Kotlin the class and validated methods must be `open`.
- When a validation failure should become a stable API contract, define an explicit error DTO instead of leaking raw framework exceptions.
- In Kotlin, keep using `@field:` for property annotations such as `@field:NotBlank`, `@field:Size`, and `@field:Pattern`.

## Summary { #summary }

You extended the CRUD application from `http-server.md` with validation in a gradual way.

First, you enabled `ValidationModule` in the application graph. Then you validated the `UserRequest` body used by `createUser` and `updateUser`. After that, you validated `userId` path parameters and
the pagination and sorting query parameters on `getUsers`. Then you inspected the generated AOP source to see where method validation really runs. Finally, you introduced a global HTTP validation
error mapping strategy with `ViolationExceptionHttpServerResponseMapper` and `ValidationHttpServerInterceptor`.

## Key Concepts { #key-concepts }

- `ValidationModule` enables Kora validation support in the application graph.
- `@Valid` validates nested objects such as request DTOs.
- `@Validate` enables method argument and return value validation through generated AOP code.
- DTO validation and method parameter validation solve different problems and are often used together.
- `ViolationExceptionHttpServerResponseMapper` defines how validation failures become HTTP responses.
- `ValidationHttpServerInterceptor` applies that mapper globally in the HTTP pipeline.

## Troubleshooting { #troubleshooting }

**Validation does not trigger:**

- Make sure `ValidationModule` is included in the application graph.
- Make sure the controller method itself is annotated with `@Validate`.
- For request DTOs, make sure the method parameter is annotated with `@Valid`.
- Remember that `@Validate` works through generated AOP code. In Java, the validated class must not be `final`.
- In Kotlin, the validated class and validated methods must be `open`.

**I want to see where validation really happens:**

- Run `./gradlew clean classes`.
- Open the generated source under:

  ```text
  guides/guide-validation-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.java
  guides/kotlin/guide-kotlin-validation-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/validation/controller/$UserController__AopProxy.kt
  ```

- Inspect how the proxy validates arguments before delegating to your original controller method.

**HTTP returns an exception instead of JSON:**

- Make sure both `ViolationExceptionHttpServerResponseMapper` and `ValidationHttpServerInterceptor` are registered.
- Make sure the interceptor is tagged with `@Tag(HttpServerModule.class)` in Java or `@Tag(HttpServerModule::class)` in Kotlin.

**Validation seems correct, but the endpoint still returns 404:**

- That usually means validation passed and the request reached your normal application logic.
- In this guide, for example, `updateUser("999", ...)` can still return `404 User not found` because the path format is valid even though the user does not exist.

**Gradle build hangs or locks files on Windows:**

- Run `./gradlew --stop` and retry.
- If you see `AccessDeniedException` on Gradle caches or build outputs, close IDE or test processes that may still hold file handles.

## What's Next? { #whats-next }

- [Database JDBC](database-jdbc.md) or [Cassandra Database](database-cassandra.md) to persist validated requests.
- [Testing with JUnit](testing-junit.md) to test validation and error mapping at the component level.
- [Black Box Testing](testing-black-box.md) after persistence is added, so validation can be checked through the packaged HTTP app.
- [Resilient Patterns](resilient.md) to add service-level fault-tolerance around validated operations.

## Help { #help }

If you get stuck:

- compare with [Kora Java Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-validation-app) and [Kora Kotlin Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-validation-app)
- review the [Validation documentation](../documentation/validation.md)
- review the [HTTP Server documentation](../documentation/http-server.md)
- review the [JSON documentation](../documentation/json.md)
