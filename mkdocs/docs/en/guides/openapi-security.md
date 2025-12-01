---
title: Authentication & Security for APIs
summary: Learn how to add authentication and authorization to your OpenAPI-generated APIs using API keys and Basic auth
tags: authentication, authorization, security, api-keys, basic-auth, openapi
---

# Authentication & Security for APIs

This guide shows you how to add comprehensive authentication and authorization to your OpenAPI-generated APIs. You'll enhance the User API from the OpenAPI HTTP Server guide with multiple authentication schemes including API keys and Basic authentication, while maintaining contract-first development principles.

## What You'll Build

You'll add enterprise-grade security to your API by implementing:

- **API Key Authentication**: Simple key-based authentication for programmatic access
- **Basic Authentication**: Username/password authentication with configurable credentials
- **Role-Based Access Control**: Authorization based on user roles and permissions
- **Security-First API Design**: Authentication integrated into your OpenAPI contract

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [OpenAPI HTTP Server](../openapi-http-server.md) guide
- Environment variables for API credentials

## Prerequisites

!!! note "Required: Complete OpenAPI HTTP Server Guide"

    This guide assumes you have completed the **[OpenAPI HTTP Server](../openapi-http-server.md)** guide and have a working User API with generated endpoints.

    If you haven't completed the OpenAPI HTTP server guide yet, please do so first as this guide builds upon it.

## Why API Security Matters

**The Security-First Imperative**

APIs are the primary attack surface for modern applications. Without proper authentication and authorization:

- **Data Breaches**: Unauthorized access to sensitive user data
- **System Compromise**: Attackers can manipulate business logic
- **Compliance Violations**: Failure to meet regulatory requirements (GDPR, HIPAA, etc.)
- **Business Disruption**: DDoS attacks and resource exhaustion
- **Reputation Damage**: Security incidents erode user trust

**Contract-First Security**

Security should be designed into your API contract from day one:

1. **Authentication Schemes**: Define supported authentication methods in OpenAPI
2. **Authorization Scopes**: Specify required permissions for each endpoint
3. **Security Requirements**: Document security constraints in the specification
4. **Validation**: Ensure implementations match security specifications

## Step-by-Step Implementation

### Enhance Your OpenAPI Specification

First, update your OpenAPI specification to include comprehensive security schemes. Add this to your `user-api.yaml`:

```yaml
# ... existing paths and components ...

components:
  securitySchemes:
    apiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key authentication
    basicAuth:
      type: http
      scheme: basic
      description: Basic username/password authentication

  schemas:
    # ... existing schemas ...

    User:
      type: object
      properties:
        id:
          type: string
        username:
          type: string
        email:
          type: string
        roles:
          type: array
          items:
            type: string
            enum: [USER, ADMIN, MODERATOR]
        createdAt:
          type: string
          format: date-time
      required:
        - id
        - username
        - email

    LoginRequest:
      type: object
      properties:
        username:
          type: string
        password:
          type: string
      required:
        - username
        - password

    LoginResponse:
      type: object
      properties:
        token:
          type: string
          description: Access token
        refreshToken:
          type: string
          description: Refresh token
        expiresIn:
          type: integer
          description: Token expiration time in seconds
        user:
          $ref: '#/components/schemas/User'
      required:
        - token
        - expiresIn
        - user

# Global security requirement (all endpoints require authentication)
security:
  - apiKeyAuth: []
```

### Update Path Security Requirements

Add specific security requirements to your API paths:

```yaml
paths:
  /users:
    get:
      # Allow both authenticated users and API keys
      security:
        - apiKeyAuth: []
        - basicAuth: []
      # ... existing operation details ...

    post:
      # Require authentication for creating users
      security:
        - basicAuth: []
      # ... existing operation details ...

  /users/{userId}:
    get:
      # Basic read access
      security:
        - apiKeyAuth: []
        - basicAuth: []
      # ... existing operation details ...

    put:
      # Require authentication for updates
      security:
        - basicAuth: []
      # ... existing operation details ...

    delete:
      # Require authentication for deletion
      security:
        - basicAuth: []
      # ... existing operation details ...

  # Add authentication endpoints
  /auth/login:
    post:
      tags:
        - authentication
      summary: User login
      description: Authenticate user and return access tokens
      operationId: login
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
        '401':
          description: Invalid credentials
      # Login doesn't require authentication
      security: []

  /auth/refresh:
    post:
      tags:
        - authentication
      summary: Refresh access token
      description: Refresh expired access token using refresh token
      operationId: refreshToken
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                refreshToken:
                  type: string
              required:
                - refreshToken
      responses:
        '200':
          description: Token refreshed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
        '401':
          description: Invalid refresh token
      security: []
```

### Regenerate Your API Code

Update your Gradle build to regenerate the API with security support:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    // ... existing configuration ...

    def openApiGenerateUserApiServer = tasks.register("openApiGenerateUserApiServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/user-api.yaml"
        outputDir = "$buildDir/generated/openapi"
        def corePackage = "ru.tinkoff.kora.example.openapi.userapi"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode: "java-server",
        ]
    }
    sourceSets.main { java.srcDirs += openApiGenerateUserApiServer.get().outputDir }
    compileJava.dependsOn openApiGenerateUserApiServer
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    // ... existing configuration ...

    val openApiGenerateUserApiServer = tasks.register<org.openapitools.generator.gradle.plugin.tasks.GenerateTask>("openApiGenerateUserApiServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/user-api.yaml"
        outputDir = "$buildDir/generated/openapi"
        val corePackage = "ru.tinkoff.kora.example.openapi.userapi"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf(
            "mode" to "java-server"
        )
    }
    sourceSets.main { java.srcDirs(openApiGenerateUserApiServer.get().outputDir) }
    tasks.compileKotlin { dependsOn(openApiGenerateUserApiServer) }
    ```

Regenerate your API code:

```bash
./gradlew openApiGenerateUserApiServer
```

### Implement Authentication Services

Create services for user management and authentication:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/security/UserService.java`:

    ```java
    package ru.tinkoff.kora.example.security;

    import org.springframework.security.crypto.password.PasswordEncoder;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.openapi.userapi.model.User;

    import java.util.List;
    import java.util.Map;
    import java.util.concurrent.ConcurrentHashMap;

    @Component
    public final class UserService {

        private final PasswordEncoder passwordEncoder;
        private final Map<String, User> users = new ConcurrentHashMap<>();
        private final Map<String, String> passwords = new ConcurrentHashMap<>();

        public UserService(PasswordEncoder passwordEncoder) {
            this.passwordEncoder = passwordEncoder;
            // Create a default admin user for testing
            createUser("admin", "admin@example.com", "admin123", List.of("ADMIN", "USER"));
            createUser("user", "user@example.com", "user123", List.of("USER"));
        }

        public User authenticate(String username, String password) {
            String storedPassword = passwords.get(username);
            if (storedPassword != null && passwordEncoder.matches(password, storedPassword)) {
                return users.get(username);
            }
            return null;
        }

        public User findByUsername(String username) {
            return users.get(username);
        }

        public User findById(String userId) {
            return users.values().stream()
                    .filter(user -> user.getId().equals(userId))
                    .findFirst()
                    .orElse(null);
        }

        public List<User> findAll() {
            return List.copyOf(users.values());
        }

        public User createUser(String username, String email, String password, List<String> roles) {
            if (users.containsKey(username)) {
                throw new IllegalArgumentException("User already exists");
            }

            var user = new User()
                    .id(java.util.UUID.randomUUID().toString())
                    .username(username)
                    .email(email)
                    .roles(roles);

            users.put(username, user);
            passwords.put(username, passwordEncoder.encode(password));
            return user;
        }

        public void deleteUser(String username) {
            users.remove(username);
            passwords.remove(username);
        }
    }
    ```

    Create `src/main/java/ru/tinkoff/kora/example/security/AuthService.java`:

    ```java
    package ru.tinkoff.kora.example.security;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginRequest;
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginResponse;

    @Component
    public final class AuthService {

        private final UserService userService;

        public AuthService(UserService userService) {
            this.userService = userService;
        }

        public LoginResponse login(LoginRequest request) {
            var user = userService.authenticate(request.getUsername(), request.getPassword());
            if (user == null) {
                throw new SecurityException("Invalid credentials");
            }

            // For demo purposes, return user info without tokens
            // In production, implement proper session management
            return new LoginResponse()
                    .user(user);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/security/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.security

    import org.springframework.security.crypto.password.PasswordEncoder
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.openapi.userapi.model.User
    import java.util.concurrent.ConcurrentHashMap

    @Component
    class UserService(private val passwordEncoder: PasswordEncoder) {

        private val users = ConcurrentHashMap<String, User>()
        private val passwords = ConcurrentHashMap<String, String>()

        init {
            // Create default users for testing
            createUser("admin", "admin@example.com", "admin123", listOf("ADMIN", "USER"))
            createUser("user", "user@example.com", "user123", listOf("USER"))
        }

        fun authenticate(username: String, password: String): User? {
            val storedPassword = passwords[username]
            return if (storedPassword != null && passwordEncoder.matches(password, storedPassword)) {
                users[username]
            } else null
        }

        fun findByUsername(username: String): User? = users[username]

        fun findById(userId: String): User? = users.values.find { it.id == userId }

        fun findAll(): List<User> = users.values.toList()

        fun createUser(username: String, email: String, password: String, roles: List<String>): User {
            if (users.containsKey(username)) {
                throw IllegalArgumentException("User already exists")
            }

            val user = User().apply {
                id = java.util.UUID.randomUUID().toString()
                this.username = username
                this.email = email
                this.roles = roles
            }

            users[username] = user
            passwords[username] = passwordEncoder.encode(password)
            return user;
        }

        fun deleteUser(username: String) {
            users.remove(username)
            passwords.remove(username)
        }
    }
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/example/security/AuthService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.security

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginRequest
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginResponse

    @Component
    class AuthService(
        private val userService: UserService
    ) {

        fun login(request: LoginRequest): LoginResponse {
            val user = userService.authenticate(request.username, request.password)
                ?: throw SecurityException("Invalid credentials")

            // For demo purposes, return user info without tokens
            // In production, implement proper session management
            return LoginResponse().apply {
                this.user = user
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/security/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.security

    import org.springframework.security.crypto.password.PasswordEncoder
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.openapi.userapi.model.User
    import java.util.concurrent.ConcurrentHashMap

    @Component
    class UserService(private val passwordEncoder: PasswordEncoder) {

        private val users = ConcurrentHashMap<String, User>()
        private val passwords = ConcurrentHashMap<String, String>()

        init {
            // Create default users for testing
            createUser("admin", "admin@example.com", "admin123", listOf("ADMIN", "USER"))
            createUser("user", "user@example.com", "user123", listOf("USER"))
        }

        fun authenticate(username: String, password: String): User? {
            val storedPassword = passwords[username]
            return if (storedPassword != null && passwordEncoder.matches(password, storedPassword)) {
                users[username]
            } else null
        }

        fun findByUsername(username: String): User? = users[username]

        fun findById(userId: String): User? = users.values.find { it.id == userId }

        fun findAll(): List<User> = users.values.toList()

        fun createUser(username: String, email: String, password: String, roles: List<String>): User {
            if (users.containsKey(username)) {
                throw IllegalArgumentException("User already exists")
            }

            val user = User().apply {
                id = java.util.UUID.randomUUID().toString()
                this.username = username
                this.email = email
                this.roles = roles
            }

            users[username] = user
            passwords[username] = passwordEncoder.encode(password)
            return user
        }

        fun deleteUser(username: String) {
            users.remove(username)
            passwords.remove(username)
        }
    }
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/example/security/AuthService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.security

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginRequest
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginResponse

    @Component
    class AuthService(
        private val userService: UserService
    ) {

        fun login(request: LoginRequest): LoginResponse {
            val user = userService.authenticate(request.username, request.password)
                ?: throw SecurityException("Invalid credentials")

            // For demo purposes, return user info without tokens
            // In production, implement proper session management
            return LoginResponse().apply {
                this.user = user
            }
        }
    }
    ```

### Configure Authentication Extractors

Update your Application class to configure authentication extractors:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
    import org.springframework.security.crypto.password.PasswordEncoder;
    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.common.Principal;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.example.openapi.userapi.api.ApiSecurity;
    import ru.tinkoff.kora.example.security.UserPrincipal;
    import ru.tinkoff.kora.example.security.UserService;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.http.server.common.auth.HttpServerPrincipalExtractor;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.validation.module.ValidationModule;
    import ru.tinkoff.kora.validation.module.http.server.ViolationExceptionHttpServerResponseMapper;

    import java.util.List;
    import java.util.concurrent.CompletableFuture;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            ValidationModule,
            JsonModule,
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

        default ViolationExceptionHttpServerResponseMapper customViolationExceptionHttpServerResponseMapper() {
            return (request, exception) -> HttpServerResponseException.of(400, exception.getMessage());
        }

        // Password encoder for user authentication
        default PasswordEncoder passwordEncoder() {
            return new BCryptPasswordEncoder();
        }

        // API Key authentication
        @Tag(ApiSecurity.ApiKeyAuth.class)
        default HttpServerPrincipalExtractor<Principal> apiKeyHttpServerPrincipalExtractor(SecurityConfig config) {
            return (request, apiKey) -> {
                // Validate API key against configured value
                if (apiKey == null || apiKey.trim().isEmpty() || !apiKey.equals(config.apiKey())) {
                    throw new SecurityException("Invalid API key");
                }
                // Create a service principal for API key authentication
                var serviceUser = new ru.tinkoff.kora.example.openapi.userapi.model.User()
                        .id("service-" + apiKey.hashCode())
                        .username("service-user")
                        .email("service@example.com")
                        .roles(List.of("SERVICE"));
                return CompletableFuture.completedFuture(new UserPrincipal(serviceUser));
            };
        }

        // Basic authentication
        @Tag(ApiSecurity.BasicAuth.class)
        default HttpServerPrincipalExtractor<Principal> basicHttpServerPrincipalExtractor(UserService userService, SecurityConfig config) {
            return (request, credentials) -> {
                // credentials format: "username:password" (base64 decoded)
                var parts = credentials.split(":", 2);
                if (parts.length != 2) {
                    throw new SecurityException("Invalid basic auth format");
                }

                // Check against configured admin credentials
                if (parts[0].equals(config.adminUsername()) && parts[1].equals(config.adminPassword())) {
                    var adminUser = new ru.tinkoff.kora.example.openapi.userapi.model.User()
                            .id("admin-user")
                            .username(config.adminUsername())
                            .email("admin@example.com")
                            .roles(List.of("ADMIN", "USER"));
                    return CompletableFuture.completedFuture(new UserPrincipal(adminUser));
                }

                // Check against user service for regular users
                var user = userService.authenticate(parts[0], parts[1]);
                if (user == null) {
                    throw new SecurityException("Invalid credentials");
                }

                return CompletableFuture.completedFuture(new UserPrincipal(user));
            };
        }

        @ConfigSource("security")
        public interface SecurityConfig {
            String apiKey();
            String adminUsername();
            String adminPassword();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder
    import org.springframework.security.crypto.password.PasswordEncoder
    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.common.Principal
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.example.openapi.userapi.api.ApiSecurity
    import ru.tinkoff.kora.example.security.UserPrincipal
    import ru.tinkoff.kora.example.security.UserService
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    import ru.tinkoff.kora.http.server.common.auth.HttpServerPrincipalExtractor
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.validation.module.ValidationModule
    import ru.tinkoff.kora.validation.module.http.server.ViolationExceptionHttpServerResponseMapper
    import java.util.concurrent.CompletableFuture

    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        ValidationModule,
        JsonModule,
        UndertowHttpServerModule {

        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                KoraApplication.run(ApplicationGraph::graph)
            }
        }

        fun customViolationExceptionHttpServerResponseMapper(): ViolationExceptionHttpServerResponseMapper {
            return ViolationExceptionHttpServerResponseMapper { request, exception ->
                HttpServerResponseException.of(400, exception.message ?: "Validation error")
            }
        }

        // Password encoder for user authentication
        fun passwordEncoder(): PasswordEncoder = BCryptPasswordEncoder()

        // API Key authentication
        @Tag(ApiSecurity.ApiKeyAuth::class)
        fun apiKeyHttpServerPrincipalExtractor(config: SecurityConfig): HttpServerPrincipalExtractor<Principal> {
            return HttpServerPrincipalExtractor { request, apiKey ->
                if (apiKey.isNullOrBlank() || apiKey != config.apiKey()) {
                    throw SecurityException("Invalid API key")
                }
                // Create a service principal for API key authentication
                val serviceUser = ru.tinkoff.kora.example.openapi.userapi.model.User().apply {
                    id = "service-${apiKey.hashCode()}"
                    username = "service-user"
                    email = "service@example.com"
                    roles = listOf("SERVICE")
                }
                CompletableFuture.completedFuture(UserPrincipal(serviceUser))
            }
        }

        // Basic authentication
        @Tag(ApiSecurity.BasicAuth::class)
        fun basicHttpServerPrincipalExtractor(userService: UserService, config: SecurityConfig): HttpServerPrincipalExtractor<Principal> {
            return HttpServerPrincipalExtractor { request, credentials ->
                val parts = credentials.split(":", limit = 2)
                if (parts.size != 2) {
                    throw SecurityException("Invalid basic auth format")
                }

                // Check against configured admin credentials
                if (parts[0] == config.adminUsername() && parts[1] == config.adminPassword()) {
                    val adminUser = ru.tinkoff.kora.example.openapi.userapi.model.User().apply {
                        id = "admin-user"
                        this.username = config.adminUsername()
                        email = "admin@example.com"
                        roles = listOf("ADMIN", "USER")
                    }
                    return@HttpServerPrincipalExtractor CompletableFuture.completedFuture(UserPrincipal(adminUser))
                }

                val user = userService.authenticate(parts[0], parts[1])
                    ?: throw SecurityException("Invalid credentials")

                CompletableFuture.completedFuture(UserPrincipal(user))
            }
        }

        @ConfigSource("security")
        interface SecurityConfig {
            fun apiKey(): String
            fun adminUsername(): String
            fun adminPassword(): String
        }
    }
    ```

### Update Your User Delegate

Update your UserApiDelegate to include authentication endpoints and authorization checks:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/UserApiDelegate.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Principal;
    import ru.tinkoff.kora.example.openapi.userapi.api.UserApiDelegate;
    import ru.tinkoff.kora.example.openapi.userapi.api.UserApiResponses;
    import ru.tinkoff.kora.example.openapi.userapi.model.*;
    import ru.tinkoff.kora.example.security.AuthService;
    import ru.tinkoff.kora.example.security.UserPrincipal;
    import ru.tinkoff.kora.example.security.UserService;

    import java.util.List;
    import java.util.Map;
    import java.util.concurrent.ConcurrentHashMap;

    @Component
    public final class UserApiDelegate implements UserApiDelegate {

        private final UserService userService;
        private final AuthService authService;
        private final Map<String, User> userStorage = new ConcurrentHashMap<>();

        public UserApiDelegate(UserService userService, AuthService authService) {
            this.userService = userService;
            this.authService = authService;
        }

        @Override
        public UserApiResponses.GetUsersApiResponse getUsers(Principal principal, Integer page, Integer size, String sort) {
            // Check if user has permission to list users
            if (!(principal instanceof UserPrincipal userPrincipal)) {
                return new UserApiResponses.GetUsersApiResponse.GetUsers403ApiResponse();
            }

            var users = userService.findAll();
            return new UserApiResponses.GetUsersApiResponse.GetUsers200ApiResponse(users);
        }

        @Override
        public UserApiResponses.CreateUserApiResponse createUser(Principal principal, UserRequest request) {
            // Check if user has permission to create users
            if (!(principal instanceof UserPrincipal userPrincipal)) {
                return new UserApiResponses.CreateUserApiResponse.CreateUser403ApiResponse();
            }

            if (!userPrincipal.hasAnyRole("ADMIN", "USER")) {
                return new UserApiResponses.CreateUserApiResponse.CreateUser403ApiResponse();
            }

            try {
                var user = userService.createUser(
                    request.getName(),
                    request.getEmail(),
                    "defaultPassword", // In production, generate secure password
                    List.of("USER")
                );
                return new UserApiResponses.CreateUserApiResponse.CreateUser201ApiResponse(user);
            } catch (IllegalArgumentException e) {
                return new UserApiResponses.CreateUserApiResponse.CreateUser400ApiResponse();
            }
        }

        @Override
        public UserApiResponses.GetUserApiResponse getUser(Principal principal, String userId) {
            if (!(principal instanceof UserPrincipal userPrincipal)) {
                return new UserApiResponses.GetUserApiResponse.GetUser403ApiResponse();
            }

            var user = userService.findById(userId);
            if (user == null) {
                return new UserApiResponses.GetUserApiResponse.GetUser404ApiResponse();
            }

            return new UserApiResponses.GetUserApiResponse.GetUser200ApiResponse(user);
        }

        @Override
        public UserApiResponses.UpdateUserApiResponse updateUser(Principal principal, String userId, UserRequest request) {
            if (!(principal instanceof UserPrincipal userPrincipal)) {
                return new UserApiResponses.UpdateUserApiResponse.UpdateUser403ApiResponse();
            }

            // Users can only update themselves, admins can update anyone
            if (!userPrincipal.userId().equals(userId) && !userPrincipal.hasRole("ADMIN")) {
                return new UserApiResponses.UpdateUserApiResponse.UpdateUser403ApiResponse();
            }

            var existingUser = userService.findById(userId);
            if (existingUser == null) {
                return new UserApiResponses.UpdateUserApiResponse.UpdateUser404ApiResponse();
            }

            // Update user logic here
            // For demo, we'll just return the existing user
            return new UserApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse(existingUser);
        }

        @Override
        public UserApiResponses.DeleteUserApiResponse deleteUser(Principal principal, String userId) {
            if (!(principal instanceof UserPrincipal userPrincipal)) {
                return new UserApiResponses.DeleteUserApiResponse.DeleteUser403ApiResponse();
            }

            // Only admins can delete users
            if (!userPrincipal.hasRole("ADMIN")) {
                return new UserApiResponses.DeleteUserApiResponse.DeleteUser403ApiResponse();
            }

            var user = userService.findById(userId);
            if (user == null) {
                return new UserApiResponses.DeleteUserApiResponse.DeleteUser404ApiResponse();
            }

            userService.deleteUser(user.getUsername());
            return new UserApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse();
        }

        @Override
        public UserApiResponses.LoginApiResponse login(LoginRequest request) {
            try {
                var response = authService.login(request);
                return new UserApiResponses.LoginApiResponse.Login200ApiResponse(response);
            } catch (SecurityException e) {
                return new UserApiResponses.LoginApiResponse.Login401ApiResponse();
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/UserApiDelegate.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Principal
    import ru.tinkoff.kora.example.openapi.userapi.api.UserApiDelegate
    import ru.tinkoff.kora.example.openapi.userapi.api.UserApiResponses
    import ru.tinkoff.kora.example.openapi.userapi.model.*
    import ru.tinkoff.kora.example.security.AuthService
    import ru.tinkoff.kora.example.security.UserPrincipal
    import ru.tinkoff.kora.example.security.UserService
    import java.util.concurrent.ConcurrentHashMap

    @Component
    class UserApiDelegate(
        private val userService: UserService,
        private val authService: AuthService
    ) : UserApiDelegate {

        override fun getUsers(principal: Principal, page: Int?, size: Int?, sort: String?): UserApiResponses.GetUsersApiResponse {
            if (principal !is UserPrincipal) {
                return UserApiResponses.GetUsersApiResponse.GetUsers403ApiResponse()
            }

            val users = userService.findAll()
            return UserApiResponses.GetUsersApiResponse.GetUsers200ApiResponse(users)
        }

        override fun createUser(principal: Principal, request: UserRequest): UserApiResponses.CreateUserApiResponse {
            if (principal !is UserPrincipal) {
                return UserApiResponses.CreateUserApiResponse.CreateUser403ApiResponse()
            }

            if (!principal.hasAnyRole("ADMIN", "USER")) {
                return UserApiResponses.CreateUserApiResponse.CreateUser403ApiResponse()
            }

            return try {
                val user = userService.createUser(
                    request.name,
                    request.email,
                    "defaultPassword", // In production, generate secure password
                    listOf("USER")
                )
                UserApiResponses.CreateUserApiResponse.CreateUser201ApiResponse(user)
            } catch (e: IllegalArgumentException) {
                UserApiResponses.CreateUserApiResponse.CreateUser400ApiResponse()
            }
        }

        override fun getUser(principal: Principal, userId: String): UserApiResponses.GetUserApiResponse {
            if (principal !is UserPrincipal) {
                return UserApiResponses.GetUserApiResponse.GetUser403ApiResponse()
            }

            val user = userService.findById(userId)
                ?: return UserApiResponses.GetUserApiResponse.GetUser404ApiResponse()

            return UserApiResponses.GetUserApiResponse.GetUser200ApiResponse(user)
        }

        override fun updateUser(principal: Principal, userId: String, request: UserRequest): UserApiResponses.UpdateUserApiResponse {
            if (principal !is UserPrincipal) {
                return UserApiResponses.UpdateUserApiResponse.UpdateUser403ApiResponse()
            }

            // Users can only update themselves, admins can update anyone
            if (principal.userId != userId && !principal.hasRole("ADMIN")) {
                return UserApiResponses.UpdateUserApiResponse.UpdateUser403ApiResponse()
            }

            val existingUser = userService.findById(userId)
                ?: return UserApiResponses.UpdateUserApiResponse.UpdateUser404ApiResponse()

            // Update user logic here
            return UserApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse(existingUser)
        }

        override fun deleteUser(principal: Principal, userId: String): UserApiResponses.DeleteUserApiResponse {
            if (principal !is UserPrincipal) {
                return UserApiResponses.DeleteUserApiResponse.DeleteUser403ApiResponse()
            }

            // Only admins can delete users
            if (!principal.hasRole("ADMIN")) {
                return UserApiResponses.DeleteUserApiResponse.DeleteUser403ApiResponse()
            }

            val user = userService.findById(userId)
                ?: return UserApiResponses.DeleteUserApiResponse.DeleteUser404ApiResponse()

            userService.deleteUser(user.username)
            return UserApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse()
        }

        override fun login(request: LoginRequest): UserApiResponses.LoginApiResponse {
            return try {
                val response = authService.login(request)
                UserApiResponses.LoginApiResponse.Login200ApiResponse(response)
            } catch (e: SecurityException) {
                UserApiResponses.LoginApiResponse.Login401ApiResponse()
            }
        }
    }
    ```

### Update Configuration

Add security configuration to your `application.conf`:

```hocon
# ... existing configuration ...

# Security Configuration
security {
  apiKey = ${?API_KEY}
  adminUsername = ${?ADMIN_USERNAME}
  adminPassword = ${?ADMIN_PASSWORD}
}

# HTTP Server Configuration
httpServer {
  publicApiHttpPort = 8080
}
```

Set the environment variables before running your application:

```bash
export API_KEY="your-secure-api-key-here"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="secure-admin-password"
```

### Test Your Secure API

Create comprehensive tests for your authentication system:

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/ru/tinkoff/kora/example/UserApiAuthenticationTest.java`:

    ```java
    package ru.tinkoff.kora.example;

    import org.junit.jupiter.api.Test;
    import org.mockserver.client.MockServerClient;
    import org.mockserver.model.HttpRequest;
    import org.mockserver.model.HttpResponse;
    import org.testcontainers.containers.MockServerContainer;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginRequest;
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginResponse;
    import ru.tinkoff.kora.example.security.AuthService;
    import ru.tinkoff.kora.test.KoraAppTest;
    import ru.tinkoff.kora.test.KoraConfigModifier;

    import java.util.Base64;

    import static org.junit.jupiter.api.Assertions.*;

    @Testcontainers
    @KoraAppTest(Application.class)
    public class UserApiAuthenticationTest {

        @Test
        void testLoginSuccess(AuthService authService) {
            var request = new LoginRequest()
                    .username("admin")
                    .password("admin123");

            var response = authService.login(request);

            assertNotNull(response);
            assertNotNull(response.getUser());
            assertEquals("admin", response.getUser().getUsername());
        }

        @Test
        void testLoginFailure(AuthService authService) {
            var request = new LoginRequest()
                    .username("admin")
                    .password("wrongpassword");

            assertThrows(SecurityException.class, () -> authService.login(request));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/ru/tinkoff/kora/example/UserApiAuthenticationTest.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import org.junit.jupiter.api.Test
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginRequest
    import ru.tinkoff.kora.example.security.AuthService
    import ru.tinkoff.kora.test.KoraAppTest
    import ru.tinkoff.kora.test.KoraConfigModifier
    import kotlin.test.assertEquals
    import kotlin.test.assertNotEquals
    import kotlin.test.assertNotNull

    @KoraAppTest(Application::class)
    class UserApiAuthenticationTest {

        @Test
        fun testLoginSuccess(authService: AuthService) {
            val request = LoginRequest().apply {
                username = "admin"
                password = "admin123"
            }

            val response = authService.login(request)

            assertNotNull(response)
            assertNotNull(response.user)
            assertEquals("admin", response.user.username)
        }

        @Test
        fun testLoginFailure(authService: AuthService) {
            val request = LoginRequest().apply {
                username = "admin"
                password = "wrongpassword"
            }

            org.junit.jupiter.api.assertThrows<SecurityException> {
                authService.login(request)
            }
        }
    }
    ```

Run your authentication tests:

```bash
./gradlew test --tests UserApiAuthenticationTest
```

## Testing Different Authentication Methods

### Test API Key Authentication

```bash
# Use API key in header
curl -X GET http://localhost:8080/users \
  -H "X-API-Key: your-api-key-here"
```

### Test Basic Authentication

```bash
# Use basic auth with configured admin credentials
curl -X GET http://localhost:8080/users \
  -u "admin:secure-admin-password"
```

### Test User Authentication

```bash
# Use basic auth with regular user credentials
curl -X GET http://localhost:8080/users \
  -u "user:user123"
```

## Key Security Concepts Learned

### Authentication vs Authorization
- **Authentication**: Verifying user identity (who they are)
- **Authorization**: Controlling access to resources (what they can do)

### Multiple Authentication Schemes
- **API keys** for service-to-service communication
- **Basic auth** for simple username/password scenarios
- **Configuration-based credentials** for secure credential management

### Security-First API Design
- **Contract-driven security** in OpenAPI specifications
- **Principle of least privilege** with role-based access
- **Defense in depth** with multiple security layers
- **Secure defaults** requiring explicit authentication

## Next Steps

Continue your security journey:

- **JWT Token Authentication**: Add JSON Web Token support for stateless authentication
- **API Rate Limiting**: Prevent abuse with request throttling
- **Audit Logging**: Track security events and user actions
- **Security Headers**: CORS, CSP, HSTS, and other HTTP security headers
- **Data Encryption**: Encrypt sensitive data at rest and in transit

## Security Best Practices

### API Key Management
- Generate cryptographically secure API keys
- Implement key rotation and revocation
- Rate limit by API key
- Audit API key usage

### Authentication Architecture
- Separate authentication from business logic
- Use dependency injection for security components
- Implement proper error handling for security failures
- Log security events for monitoring

This guide establishes a solid foundation for API security while maintaining the contract-first development approach that makes Kora powerful and maintainable! 🔐