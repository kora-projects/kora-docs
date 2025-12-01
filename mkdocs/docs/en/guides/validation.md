---
title: Validation with Kora
summary: Learn how to add comprehensive input validation to your Kora APIs
tags: validation, api, security, data-integrity
---

# Validation with Kora

This guide shows you how to add robust input validation to your Kora applications using built-in validation annotations and constraints.

## What You'll Build

You'll enhance your existing API with:

- Request body validation with constraint annotations
- Parameter validation for method arguments
- Automatic validation error responses
- Type-safe validation rules
- Integration with existing JSON processing

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide

## Prerequisites

!!! note "Required: Complete Basic Kora Setup"

    This guide assumes you have completed the **[Create Your First Kora App](../getting-started.md)** guide and have a working Kora project with basic setup.

    If you haven't completed the basic guide yet, please do so first as this guide builds upon that foundation.

## Add Dependencies

Add the validation module dependency to your existing `build.gradle` or `build.gradle.kts`:

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:validation-module")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:validation-module")
    }
    ```

## Add Modules

Update your existing `Application.java` or `Application.kt` to include the `ValidationModule`:

===! ":fontawesome-brands-java: Java"

    Update `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.validation.module.ValidationModule;

    @KoraApp
    public interface Application extends
            UndertowHttpServerModule,
            JsonModule,
            ValidationModule,
            LogbackModule {  // Add this line
    }
    ```

=== ":simple-kotlin: Kotlin"

    Update `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.validation.module.ValidationModule

    @KoraApp
    interface Application :
        UndertowHttpServerModule,
        JsonModule,
        ValidationModule,
        LogbackModule  // Add this line
    ```

## Adding Validation to DTOs

Update your existing request DTOs to include validation constraints:

===! ":fontawesome-brands-java: Java"

    Update `src/main/java/ru/tinkoff/kora/example/dto/UserRequest.java`:

    ```java
    package ru.tinkoff.kora.example.dto;

    import ru.tinkoff.kora.validation.common.annotation.Valid;
    import ru.tinkoff.kora.validation.common.annotation.NotBlank;
    import ru.tinkoff.kora.validation.common.annotation.Size;

    @Valid
    public record UserRequest(
        @NotBlank String name,
        @Size(min = 3, max = 50) String email
    ) {}
    ```

=== ":simple-kotlin: Kotlin"

    Update `src/main/kotlin/ru/tinkoff/kora/example/dto/UserRequest.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.dto

    import ru.tinkoff.kora.validation.common.annotation.Valid
    import ru.tinkoff.kora.validation.common.annotation.NotBlank
    import ru.tinkoff.kora.validation.common.annotation.Size

    @Valid
    data class UserRequest(
        @NotBlank val name: String,
        @Size(min = 3, max = 50) val email: String
    )
    ```

## Understanding Validation Annotations

Kora provides two key validation annotations:

- **`@Valid`**: Validates the annotated element (field, parameter, or method return value)
- **`@Validate`**: Enables method-level validation for parameters and/or return values

### When to Use Each Annotation:

- **Parameter Validation**: Use `@Validate` on methods + `@Valid` on parameters (required for all methods with `@Valid` parameters)
- **Return Value Validation**: Use `@Validate` and `@Valid` on methods (not on type references)
- **Nested Object Validation**: Use `@Valid` on complex object fields

!!! note "Important"
    `@Valid` is only needed on method declarations for return value validation, not on generic type parameters like `List<@Valid UserResponse>`.

## Validating Controller Methods

Update your existing controller to use validation:

===! ":fontawesome-brands-java: Java"

    Update `src/main/java/ru/tinkoff/kora/example/UserController.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.http.server.common.annotation.HttpRoute;
    import ru.tinkoff.kora.json.common.annotation.Json;
    import ru.tinkoff.kora.validation.common.annotation.Valid;
    import ru.tinkoff.kora.validation.common.annotation.Validate;
    import ru.tinkoff.kora.validation.common.annotation.NotBlank;

    import java.time.LocalDateTime;
    import java.util.List;
    import java.util.Optional;
    import java.util.concurrent.CopyOnWriteArrayList;
    import java.util.concurrent.atomic.AtomicLong;

    @Component
    @HttpController
    public final class UserController {

        private final List<UserResponse> users = new CopyOnWriteArrayList<>();
        private final AtomicLong idGenerator = new AtomicLong(1);

        record UserRequest(@Valid String name, @Valid String email) {}
        record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        @Validate
        public UserResponse createUser(@Valid UserRequest request) {
            var id = String.valueOf(idGenerator.getAndIncrement());
            var user = new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
            users.add(user);
            return user;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        @Validate
        public Optional<UserResponse> getUser(@Valid @NotBlank String id) {
            return users.stream()
                .filter(user -> user.id().equals(id))
                .findFirst();
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        @Validate
        @Valid
        public List<UserResponse> getAllUsers() {
            return users;
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    Update `src/main/kotlin/ru/tinkoff/kora/example/UserController.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.http.server.common.annotation.HttpRoute
    import ru.tinkoff.kora.json.common.annotation.Json
    import ru.tinkoff.kora.validation.common.annotation.Valid
    import ru.tinkoff.kora.validation.common.annotation.Validate
    import ru.tinkoff.kora.validation.common.annotation.NotBlank

    import java.time.LocalDateTime
    import java.util.concurrent.CopyOnWriteArrayList
    import java.util.concurrent.atomic.AtomicLong

    @Component
    @HttpController
    class UserController {

        private val users = CopyOnWriteArrayList<UserResponse>()
        private val idGenerator = AtomicLong(1)

        data class UserRequest(@Valid val name: String, @Valid val email: String)
        data class UserResponse(val id: String, val name: String, val email: String, val createdAt: LocalDateTime)

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        @Validate
        fun createUser(@Valid request: UserRequest): UserResponse {
            val id = idGenerator.getAndIncrement().toString()
            val user = UserResponse(id, request.name, request.email, LocalDateTime.now())
            users.add(user)
            return user
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        @Validate
        fun getUser(@Valid @NotBlank id: String): UserResponse? {
            return users.find { it.id == id }
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        @Validate
        @Valid
        fun getAllUsers(): List<UserResponse> {
            return users
        }
    }
    ```

## Running the Application

```bash
./gradlew run
```

## Testing Validation

Test the validation by sending invalid requests:

### Valid Request (should succeed)

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

**Expected Response:**
```json
{
  "id": "1",
  "name": "John Doe",
  "email": "john@example.com",
  "createdAt": "2025-09-27T10:30:00"
}
```

### Invalid Request - Empty Name (should fail)

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "", "email": "john@example.com"}'
```

**Expected Response:**
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "errors": [
    {
      "field": "name",
      "message": "must not be blank"
    }
  ]
}
```

### Invalid Request - Invalid Email (should fail)

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "invalid-email"}'
```

**Expected Response:**
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "errors": [
    {
      "field": "email",
      "message": "size must be between 3 and 50"
    }
  ]
}
```

### Get All Users

```bash
curl http://localhost:8080/users
```

## Key Concepts Learned

### Validation Annotations
- **`@Valid`**: Enables validation for the annotated element
- **`@NotBlank`**: Ensures string is not null, empty, or whitespace-only
- **`@Size`**: Validates string length or collection size
- **`@Range`**: Validates numeric ranges
- **`@Pattern`**: Validates against regular expressions

### Validation Integration
- **Automatic validation**: Applied to `@Valid` parameters in controller methods
- **Error responses**: Structured validation error responses
- **Type safety**: Compile-time validation rule checking
- **Framework integration**: Works seamlessly with JSON processing

## What's Next?

- [Add Caching](../cache.md)
- [Add Security](../security.md)
- [Explore Testing Strategies](../testing.md)

## Help

If you encounter issues:

- Check the [Validation Module Documentation](../../documentation/validation.md)
- Check the [JSON Module Documentation](../../documentation/json.md)
- Check the [Validation Example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-validation)
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)

## Troubleshooting

### Validation Not Working
- Ensure `@Valid` annotation is present on controller method parameters
- Verify `ValidationModule` is included in Application interface
- Check that validation annotations are on the correct fields

### Unexpected Validation Errors
- Review validation constraints on your DTOs
- Check that request JSON matches the expected structure
- Verify Content-Type header is set to `application/json`

### Custom Validation Rules
- For complex validation logic, consider custom validator implementations
- Use `@Validate` annotation on methods that need custom validation
- Implement `Validator` interface for reusable validation rules