---
search:
  exclude: true
title: Validation with Kora
summary: Continue the HTTP Server guide and add body, path, and query validation with structured JSON validation errors
description: "Step-by-step request validation for a Kora 2.0 HTTP API: the io.koraframework:validation-module artifact and ValidationModule, Kora's own constraint annotations in io.koraframework.validation.common.annotation, @Valid on a record and on a parameter, @Validate for method argument and result validation, the generated $UserRequest_Validator and $UserController__AopProxy sources, ViolationException and Violation.path().full(), and a global ViolationExceptionHttpServerResponseMapper plus ValidationHttpServerInterceptor tagged with @Tag(HttpServer.class)."
agent:
  use_when: "Use this file for questions about validating HTTP input in a Kora 2.0 service: io.koraframework:validation-module, ValidationModule, the Kora constraint annotations (@NotBlank, @NotEmpty, @Pattern, @Size, @Range, @Min, @Max, @Positive, @Negative, @Digits, @OneOf, @UUID, @Uri, @Url, @Past, @Future, @AssertTrue, @AssertFalse), @Valid on types and parameters, @Validate and its failFast attribute, @ValidatedBy custom constraints, Validator and ValidatorFactory, ViolationException, Violation.path().full(), turning violations into HTTP 400 with ViolationExceptionHttpServerResponseMapper and ValidationHttpServerInterceptor bound with @Tag(HttpServer.class), and why Kora validation is not Jakarta Bean Validation."
tags: validation, http-server, json, api
---

# Validation with Kora { #validation-kora }

This guide introduces request validation for Kora HTTP APIs. It covers how constraint annotations describe valid input, how `@Validate` activates generated validators at controller boundaries, and how
validation failures become predictable HTTP errors. You will also see how validation keeps DTO rules close to the data they protect while leaving service and repository code focused on application
behavior.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-validation-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-validation-app).

## What You'll Build { #youll-build }

You will extend the existing HTTP server with:

- request body validation for `createUser` and `updateUser`
- path parameter validation for `userId`
- query parameter validation for `page`, `size`, and `sort`
- AOP-based method validation with `@Validate`
- structured JSON responses for validation failures

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+
- A text editor or IDE
- Completed [HTTP Server Guide](http-server.md)

## Prerequisites { #prerequisites }

!!! note "Required Foundation"

    This guide assumes you have completed **[HTTP Server](http-server.md)** and already have the finished CRUD application with `UserController`, `UserService`, `UserRepository`, and `InMemoryUserRepository`.

    If you haven't completed the HTTP server guide yet, do that first, because validation is most useful once the request body, path parameters, query parameters, and service flow already exist.

## Overview { #overview }

Validation protects the boundary between external input and application behavior. A controller can deserialize JSON into a DTO, but deserialization only proves that the payload has the right general
shape. It does not prove that an email looks like an email, a name is not blank, a page size is within limits, or a path parameter follows the expected format.

Without validation, the application accepts bad input and lets deeper layers discover the problem later. That usually produces weaker errors, more defensive service code, and data rules that are
scattered across the codebase. With validation, the API can reject invalid input early and return a response that clearly belongs to the client request.

!!! warning "Kora validation is not Jakarta Bean Validation"

    Kora ships its own validation API in `io.koraframework.validation.common.annotation`. The annotation names deliberately look familiar, but they are Kora's own types, they are enforced by
    compile-time generated code rather than by a reflective runtime, and they are **not** interchangeable with `jakarta.validation.constraints`. Importing the Jakarta annotation of the same name
    produces a class that compiles and silently validates nothing.

### How Validation Fits into an HTTP API { #validation-fits-http-api }

In a layered HTTP application, validation usually protects the boundary where outside input enters the system.

That means:

- the controller validates request bodies, path parameters, and query parameters
- the service keeps focusing on business logic
- the repository keeps focusing on storage

This separation is useful because invalid HTTP input should usually be rejected before it reaches deeper layers. It also keeps validation rules easier to discover and reason about.

Kora supports two styles here:

- declarative validation through annotations such as `@Valid` and `@Validate`
- imperative usage by injecting a generated `Validator<T>` and calling `validate(...)` or `validateAndThrow(...)` yourself, as described in [Manual validation](../documentation/validation.md#manual-validation)

In this guide we use the declarative controller-based approach because it is the most natural continuation of `http-server.md`.

### Validation at the Boundary { #validation-at-boundary }

The best place for basic input validation is the API boundary. If invalid data is rejected before it reaches the service layer, the rest of the application can work with stronger assumptions. In this
guide, validation appears in three places:

- request body DTOs, where fields such as `name` and `email` can be constrained
- path parameters, where route values such as `userId` can be checked
- query parameters, where pagination and sorting input can be limited

This does not replace business validation. A DTO rule can say "email must be syntactically valid"; a service rule might say "this email must be unique". Those are different layers of validation.

### Constraint Annotations { #constraint-annotations }

The set is considerably wider than the four constraints this guide happens to need. Every one of them lives in `io.koraframework.validation.common.annotation` and can be placed on a field, a method, or
a method parameter:

| Group      | Annotations                                                                          |
|------------|--------------------------------------------------------------------------------------|
| Text       | `@NotBlank`, `@Pattern`, `@Size`, `@OneOf`, `@UUID`, `@Uri`, `@Url`                   |
| Numeric    | `@Min`, `@Max`, `@Range`, `@Positive`, `@PositiveOrZero`, `@Negative`, `@NegativeOrZero`, `@Digits` |
| Temporal   | `@Past`, `@PastOrPresent`, `@Future`, `@FutureOrPresent`                              |
| Boolean    | `@AssertTrue`, `@AssertFalse`                                                         |
| Collection | `@NotEmpty`, `@Size`                                                                  |
| Structural | `@Valid`, `@Validate`, `@ValidatedBy`                                                 |

`@Valid` and `@Validate` are not constraints: `@Valid` says "descend into this type and apply its own rules", and `@Validate` turns on method validation. `@ValidatedBy` is the extension point you use to
build a custom constraint on top of your own `ValidatorFactory`. The full reference, including the exact violation messages each constraint produces, is in
[Validation annotations](../documentation/validation.md#validation-annotations).

### Generated Validation and `@Validate` { #generated-validation-validate }

The full rules for generated validators, class validation, and method validation are covered in [Class validation](../documentation/validation.md#class-validation) and [Method validation](../documentation/validation.md#method-validation).

Kora validation uses annotations to describe constraints and generated code to enforce them. `@Valid` on a type generates a `Validator<T>` implementation for it, `@Validate` activates method
validation, and the validation module contributes the required graph components. Because validation wiring is generated, missing validators or unsupported shapes are found during build time rather
than discovered only after a bad request reaches production.

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

- `validation-module` enables validator generation, method validation, and the HTTP interceptor that turns violations into responses
- `http-server-undertow` exposes the controller as HTTP endpoints
- `json-common` serializes request and response DTOs
- `config-hocon` and `logging-logback` provide the standard runtime setup used across the guides

For more background, see the Kora [Validation documentation](../documentation/validation.md), [HTTP Server documentation](../documentation/http-server.md)
and [JSON documentation](../documentation/json.md).

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

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

    Update `build.gradle.kts`:

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

There is one artifact for validation, not two. `validation-module` brings `validation-common` with it, and the code generator lives in the `annotation-processors` / `symbol-processors` artifact you
already apply.

## Modules { #modules }

Before any validation annotations can work, the application graph needs `ValidationModule`.

At this point we only enable the module itself. We will add custom HTTP handling for validation failures later, after the actual validation flow is already clear.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/io/koraframework/guide/validation/Application.java`:

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

    Update `src/main/kotlin/io/koraframework/guide/validation/Application.kt`:

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

## Model Validation { #model-validation }

The easiest place to start is the same request body already used by `createUser` and `updateUser`.

This is object validation. Instead of validating each JSON field directly on the controller method, we describe the rules once inside `UserRequest`.

In this guide:

- `name` must be present, not blank, and reasonably sized
- `email` must be present and match a simple email pattern

That gives us a good first example of DTO validation without changing the overall CRUD design from the previous guide.

===! ":fontawesome-brands-java: `Java`"

    Create or update `src/main/java/io/koraframework/guide/validation/dto/UserRequest.java`:

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

    Create or update `src/main/kotlin/io/koraframework/guide/validation/dto/UserRequest.kt`:

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

The `@Valid` on the type itself is what makes the annotation processor emit a `Validator<UserRequest>` component named `$UserRequest_Validator`. Without it the field constraints are inert: nothing
generates a validator, and nothing in the graph can be injected to run them.

In Kotlin the `@field:` use-site target is required. A bare `@NotBlank` on a constructor property lands on the constructor parameter, not on the backing field, and the processor will not see it.

Notice that at this step we only described the rules. They still need to be applied at the controller boundary, which we do next.

## Controller Validation { #controller-validation }

The `@Valid` plus `@Validate` combination relies on the rules from [Class validation](../documentation/validation.md#class-validation) and [Method validation](../documentation/validation.md#method-validation).

Now we connect those DTO rules to the real HTTP endpoints from `http-server.md`.

This is where two annotations matter most:

- `@Valid` on a parameter says that the complex object argument should be validated using the generated validator for that DTO
- `@Validate` turns on method-level validation for the controller method itself

`@Validate` is important because it tells Kora to generate validation logic around the method call. `@Valid` is important because it tells that generated logic to descend into the `UserRequest` object
and validate its fields.

===! ":fontawesome-brands-java: `Java`"

    Update the `POST` and `PUT` methods in `src/main/java/io/koraframework/guide/validation/controller/UserController.java`:

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

    Update the same methods in `src/main/kotlin/io/koraframework/guide/validation/controller/UserController.kt`:

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

At this point:

- malformed JSON still fails at JSON parsing time
- well-formed JSON with invalid field values now fails at validation time
- valid JSON continues into the same service and repository flow you already built earlier

By default `@Validate` collects every violation before throwing. If you would rather stop at the first one, use `@Validate(failFast = true)`: the generated code then throws as soon as a single
constraint fails, which is cheaper but reports only one problem per request.

After compilation, the generated AOP proxy shows how `@Valid` delegates into the generated `UserRequest` validator before the controller method is called:

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

The important detail is that `validator6.validate(request, ...)` runs before `super.createUser(request)`, so invalid DTO fields never reach your controller body. `validator6` is the injected
`$UserRequest_Validator`; the numbering is just the order in which the proxy allocated its validator fields.

### Path Parameters { #path-parameters }

Request bodies are not the only source of invalid input. Path parameters can also be wrong.

In this guide, `userId` comes from an in-memory repository that uses numeric string identifiers such as `1`, `2`, and `3`. So we can express that assumption explicitly in the controller:

- `@NotBlank` rejects empty IDs
- `@Pattern("^\\d+$")` says the path value must contain only digits

This is method-argument validation rather than DTO validation. It is useful when the data is simple and does not justify creating a separate object just for validation.

===! ":fontawesome-brands-java: `Java`"

    Update the `GET`, `PUT`, and `DELETE` methods in `src/main/java/io/koraframework/guide/validation/controller/UserController.java`:

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

    Update the same methods in `src/main/kotlin/io/koraframework/guide/validation/controller/UserController.kt`:

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

Parameter constraints do not need the `@field:` target that DTO properties needed: here the annotation is already on a parameter, which is one of the targets every Kora constraint declares.

This kind of validation is especially useful for path variables, headers, cookies, and other simple parameters that do not naturally live inside a request DTO.

After compilation, the generated proxy shows how path parameter constraints become ordinary validator calls:

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

This makes the method boundary visible: Kora validates `userId` first, then delegates to your original `getUser(...)` implementation. Each constraint becomes its own `validate(...)` call, which is why
two annotations on one parameter produce `_argConstResult_userId_1` and `_argConstResult_userId_2`.

### Query Parameters { #query-parameters }

The next common validation target is the query string.

Our `GET /users` endpoint already supports pagination and sorting. That makes it a good place to demonstrate method parameter validation for optional values:

- `page` is optional, but if present it must be `0` or greater
- `size` is optional, but if present it must stay in a safe range
- `sort` is optional, but if present it must be one of the supported sort fields

This kind of validation protects the API from invalid paging requests before any business logic or storage logic runs.

===! ":fontawesome-brands-java: `Java`"

    Update `getUsers` in `src/main/java/io/koraframework/guide/validation/controller/UserController.java`:

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

    Update `getUsers` in `src/main/kotlin/io/koraframework/guide/validation/controller/UserController.kt`:

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

`@Range` declares `from` and `to` as `double`. Java widens the integer literals for you, but Kotlin does not, which is why the Kotlin version writes `0.0` and `1_000.0`. `@Range` also accepts a
`boundary` attribute (`INCLUSIVE_INCLUSIVE` by default, plus the three other combinations) when an endpoint should be excluded.

Nullability is what makes these parameters optional. In Java the parameter is marked `@Nullable`; in Kotlin the type is `Int?`. The generated code checks for `null` before validating, so an omitted
query parameter is never a violation.

After this step, the guide now covers three different validation targets in separate chapters:

- complex JSON objects
- simple path parameters
- simple query parameters

That separation is useful because each kind of input tends to evolve differently in real APIs.

After compilation, the generated proxy shows that optional query parameters are validated only when present:

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

That generated code explains the optional behavior precisely: null means "parameter omitted", while a present value is checked against its constraint.

## Generated Code { #generated-code }

Validation produces two kinds of generated source, and it helps to keep them apart.

`@Valid` on a type produces a **validator class**. For `UserRequest` that is `$UserRequest_Validator`, a `Validator<UserRequest>` published into the graph. It is an ordinary component: you can inject it
anywhere and call `validate(value)` or `validateAndThrow(value)` without any AOP involved.

`@Validate` on a method produces an **AOP proxy**. Kora does not modify your controller source file directly. Instead, it generates a subclass around the validated component and puts the validation
logic into that generated class. Your code still looks simple, but the generated proxy performs the checks before the call reaches your method body.

This is why:

- validated Java classes must not be `final`
- validated Kotlin classes must be `open`
- validated Kotlin methods must also be `open`

After compilation you can inspect the generated source here:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-validation-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/validation/controller/$UserController__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-validation-app/build/generated/ksp/main/kotlin/io/koraframework/guide/validation/controller/$UserController__AopProxy.kt
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

The HTTP response setup here connects validation with the general [HTTP Server error handling](../documentation/http-server.md#error-handling) rules, and is described in full under
[Validation HTTP response](../documentation/validation.md#validation-response-http).

So far validation works, but the HTTP client experience can still be improved.

`ValidationModule` already contributes a `ValidationHttpServerInterceptor` as a `@DefaultComponent`, and that interceptor already turns a `ViolationException` into a `400` carrying the exception
message. What it does not do is bind itself to the server or produce a machine-readable body. In a real API it is usually better to return a stable JSON error contract that clients can parse and
display.

Kora gives you flexibility here. You can define such handling only for selected endpoints, or register it globally for the whole HTTP application. In this guide we use the global approach because it
is the easiest way to keep every controller consistent.

We will add:

- `ValidationErrorDetails` and `ValidationErrorResponse` as explicit JSON DTOs
- `ViolationExceptionHttpServerResponseMapper` to turn `ViolationException` into that DTO
- `ValidationHttpServerInterceptor`, tagged with `@Tag(HttpServer.class)`, to apply that mapping in the HTTP pipeline

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/validation/dto/ValidationErrorDetails.java`:

    ```java
    package io.koraframework.guide.validation.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record ValidationErrorDetails(String field, String message) {}
    ```

    Create `src/main/java/io/koraframework/guide/validation/dto/ValidationErrorResponse.java`:

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

    Update `src/main/java/io/koraframework/guide/validation/Application.java`:

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

    Create `src/main/kotlin/io/koraframework/guide/validation/dto/ValidationErrorDetails.kt`:

    ```kotlin
    package io.koraframework.guide.validation.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class ValidationErrorDetails(
        val field: String,
        val message: String
    )
    ```

    Create `src/main/kotlin/io/koraframework/guide/validation/dto/ValidationErrorResponse.kt`:

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

    Update `src/main/kotlin/io/koraframework/guide/validation/Application.kt`:

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

Three details in that wiring are worth calling out.

The tag is `HttpServer`, from `io.koraframework.http.server.common` — the marker the Undertow module uses to collect global interceptors. An untagged `ValidationHttpServerInterceptor` compiles and
builds fine but never runs, which is exactly what the module's own `@DefaultComponent` is: available, but not attached to any server.

`ViolationExceptionHttpServerResponseMapper` is a functional interface returning a `@Nullable HttpServerResponse`. Returning `null` from it is a deliberate opt-out for that request: the interceptor
falls back to its plain `400` with the exception message.

`Violation.path().full()` gives the full dotted path of the failing value, such as `request.email`. This example trims it to the last segment so the JSON reports `email`; keep the full path instead if
your clients need to locate a value inside a nested object.

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
- Import constraints from `io.koraframework.validation.common.annotation`, never from `jakarta.validation.constraints`. The names overlap; the behavior does not.
- Put `@Valid` on the DTO type as well as on the parameter: the type-level annotation is what generates the validator, and the parameter-level one is what invokes it.
- Keep `UserService` and `UserRepository` focused on business logic and storage instead of duplicating HTTP input rules there.
- Remember that `@Validate` is AOP-based. In Java the validated class must not be `final`. In Kotlin the class and validated methods must be `open`.
- When a validation failure should become a stable API contract, define an explicit error DTO instead of leaking raw framework exceptions.
- In Kotlin, keep using `@field:` for property annotations such as `@field:NotBlank`, `@field:Size`, and `@field:Pattern`.

## Summary { #summary }

You extended the CRUD application from `http-server.md` with validation in a gradual way.

First, you enabled `ValidationModule` in the application graph. Then you validated the `UserRequest` body used by `createUser` and `updateUser`. After that, you validated `userId` path parameters and
the pagination and sorting query parameters on `getUsers`. Then you inspected the generated AOP source to see where method validation really runs. Finally, you introduced a global HTTP validation
error mapping strategy with `ViolationExceptionHttpServerResponseMapper` and a `ValidationHttpServerInterceptor` tagged with `@Tag(HttpServer.class)`.

## Key Concepts { #key-concepts }

- Kora validation is Kora's own API in `io.koraframework.validation.common.annotation`, generated at compile time, not Jakarta Bean Validation.
- `ValidationModule` enables Kora validation support in the application graph.
- `@Valid` on a type generates a `Validator<T>`; `@Valid` on a parameter tells method validation to use it.
- `@Validate` enables method argument and return value validation through generated AOP code, and `@Validate(failFast = true)` stops at the first violation.
- DTO validation and method parameter validation solve different problems and are often used together.
- `ViolationExceptionHttpServerResponseMapper` defines how validation failures become HTTP responses.
- `ValidationHttpServerInterceptor` applies that mapper globally, but only when it is tagged with `@Tag(HttpServer.class)`.

## Troubleshooting { #troubleshooting }

**Validation does not trigger:**

- Make sure `ValidationModule` is included in the application graph.
- Make sure the controller method itself is annotated with `@Validate`.
- For request DTOs, make sure the method parameter is annotated with `@Valid` and the DTO type is annotated with `@Valid` too.
- Check the imports: `io.koraframework.validation.common.annotation.NotBlank`, not `jakarta.validation.constraints.NotBlank`.
- Remember that `@Validate` works through generated AOP code. In Java, the validated class must not be `final`.
- In Kotlin, the validated class and validated methods must be `open`, and property constraints need the `@field:` target.

**`Validator<UserRequest> not found` when building the graph:**

- The DTO type is missing its own `@Valid`. Only a type-level `@Valid` makes the processor emit `$UserRequest_Validator`.

**I want to see where validation really happens:**

- Run `./gradlew clean classes`.
- Open the generated source under:

  ```text
  guides/java/kora-java-guide-validation-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/validation/controller/$UserController__AopProxy.java
  guides/kotlin/kora-kotlin-guide-validation-app/build/generated/ksp/main/kotlin/io/koraframework/guide/validation/controller/$UserController__AopProxy.kt
  ```

- Inspect how the proxy validates arguments before delegating to your original controller method.

**HTTP returns a plain text 400 instead of JSON:**

- That is the module's default `ValidationHttpServerInterceptor` with no mapper. Make sure your own `ViolationExceptionHttpServerResponseMapper` is registered.
- Make sure the interceptor is tagged with `@Tag(HttpServer.class)` in Java or `@Tag(HttpServer::class)` in Kotlin. Without the tag it is never attached to the server.

**Kotlin refuses to compile the interceptor override:**

- `ValidationModule` declares the mapper parameter as `@Nullable`, so the Kotlin override must accept `ViolationExceptionHttpServerResponseMapper?`.

**Kotlin rejects `@Range(from = 0, to = 1_000)`:**

- `from` and `to` are `double`. Write `0.0` and `1_000.0`.

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

- compare with [Kora Java Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-validation-app) and [Kora Kotlin Validation App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-validation-app)
- review the [Validation documentation](../documentation/validation.md)
- review the [HTTP Server documentation](../documentation/http-server.md)
- review the [JSON documentation](../documentation/json.md)
