---
title: "JWT Authentication with OpenAPI"
description: "Complete JWT authentication implementation for OpenAPI HTTP servers"
tags:
  - security
  - jwt
  - authentication
  - openapi
  - java
  - kotlin
---

# JWT Authentication with OpenAPI

This guide demonstrates how to implement complete JWT (JSON Web Token) authentication for your Kora OpenAPI HTTP server. It builds upon the [OpenAPI HTTP Server Guide](./openapi-http-server.md) and adds secure token-based authentication with access and refresh tokens.

## Prerequisites

Before starting this guide, ensure you have:

- ✅ Completed the [OpenAPI HTTP Server Guide](./openapi-http-server.md)
- ✅ Basic HTTP server with OpenAPI-generated endpoints
- ✅ User model and basic data structures

## Overview

This guide provides a complete JWT authentication system including:

- **Access tokens** for API authentication (15-minute expiration)
- **Refresh tokens** for seamless token renewal (7-day expiration)
- **Token-based security** for web and mobile applications
- **JWT claims** containing user identity and permissions
- **Comprehensive testing** and security best practices

> **⚠️ DEMO CODE WARNING**: This guide uses Java's built-in PBKDF2 for demonstration purposes with a high iteration count (100,000). **DO NOT use this implementation in production!** While PBKDF2 is secure, production applications should use established frameworks like Spring Security's BCryptPasswordEncoder or Argon2, which include additional security features and have been thoroughly audited.

## Dependencies

Add JWT dependencies to your `build.gradle`:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        // JWT Authentication
        implementation("io.jsonwebtoken:jjwt-api:0.12.3")
        runtimeOnly("io.jsonwebtoken:jjwt-impl:0.12.3")
        runtimeOnly("io.jsonwebtoken:jjwt-jackson:0.12.3")

        // Password encoding (DEMO ONLY - NOT SECURE FOR PRODUCTION!)
        // Using Java's built-in PBKDF2 for demonstration
        // In production, use Spring Security BCryptPasswordEncoder or Argon2
        // No external dependencies needed - uses java.security
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        // JWT Authentication
        implementation("io.jsonwebtoken:jjwt-api:0.12.3")
        runtimeOnly("io.jsonwebtoken:jjwt-impl:0.12.3")
        runtimeOnly("io.jsonwebtoken:jjwt-jackson:0.12.3")

        // Password encoding (DEMO ONLY - NOT SECURE FOR PRODUCTION!)
        // Using Java's built-in PBKDF2 for demonstration
        // In production, use Spring Security BCryptPasswordEncoder or Argon2
        // No external dependencies needed - uses java.security
    }
    ```

## Update OpenAPI Specification

This section defines the API contract for JWT authentication in your OpenAPI specification. The OpenAPI spec serves as the single source of truth for your API, documenting authentication requirements, request/response formats, and security schemes. By defining JWT Bearer authentication here, you're establishing a clear contract that:

- **Documents Authentication Requirements**: Specifies that certain endpoints require JWT Bearer tokens
- **Enables Code Generation**: The OpenAPI generator will create properly typed request/response models
- **Provides API Documentation**: Tools like Swagger UI can display authentication requirements
- **Ensures Consistency**: All API consumers understand the authentication format

The specification defines:
- **Bearer Authentication Scheme**: HTTP Bearer token authentication with JWT format
- **Login/Refresh Endpoints**: Clear API paths for token acquisition and renewal
- **Security Requirements**: Which endpoints require authentication and which don't
- **Response Models**: Structured responses containing tokens and user information

```yaml title="user-api.yaml"
# ... existing components ...

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    LoginResponse:
      type: object
      properties:
        token:
          type: string
          description: JWT access token
        refreshToken:
          type: string
          description: JWT refresh token for obtaining new access tokens
        expiresIn:
          type: integer
          description: Token expiration time in seconds
        user:
          $ref: '#/components/schemas/User'

# ... existing paths ...

paths:
  /auth/login:
    post:
      summary: User login with JWT token response
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                username:
                  type: string
                password:
                  type: string
      responses:
        '200':
          description: Successful login with JWT tokens
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
        '401':
          description: Invalid credentials

  /auth/refresh:
    post:
      summary: Refresh JWT access token
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                refreshToken:
                  type: string
                  description: The refresh token
      responses:
        '200':
          description: New JWT tokens
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
        '401':
          description: Invalid refresh token

# Apply JWT security globally
security:
  - bearerAuth: []

# Or apply to specific endpoints
paths:
  /users:
    get:
      security:
        - bearerAuth: []
      # ... rest of path config
```

Regenerate your API code:

```bash
./gradlew openApiGenerateUserApiServer
```

## Implement User Management

Create services for user management and authentication:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/security/UserService.java`:

    ```java
    package ru.tinkoff.kora.example.security;

    import org.springframework.security.crypto.password.PasswordEncoder;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.openapi.userapi.model.User;

    import java.util.List;
    import java.util.concurrent.ConcurrentHashMap;

    @Component
    public final class UserService {

        private final PasswordEncoderComponent passwordEncoder;
        private final ConcurrentHashMap<String, User> users = new ConcurrentHashMap<>();
        private final ConcurrentHashMap<String, String> passwords = new ConcurrentHashMap<>();

        public UserService(PasswordEncoderComponent passwordEncoder) {
            this.passwordEncoder = passwordEncoder;
            // Create default users for testing
            createUser("admin", "admin@example.com", "admin123", List.of("ADMIN", "USER"));
            createUser("user", "user@example.com", "user123", List.of("USER"));
        }

        public User authenticate(String username, String password) {
            var storedPassword = passwords.get(username);
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

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/security/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.security

    import org.springframework.security.crypto.password.PasswordEncoder
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.openapi.userapi.model.User
    import java.util.concurrent.ConcurrentHashMap

    @Component
    class UserService(private val passwordEncoder: PasswordEncoderComponent) {

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

## Implement JWT Authentication Service

Create a JWT authentication service that extends the basic authentication with token management:

===! ":fontawesome-brands-java: `Java`"

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

            return new LoginResponse().user(user);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/security/AuthService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.security

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginRequest
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginResponse

    @Component
    class AuthService(private val userService: UserService) {

        fun login(request: LoginRequest): LoginResponse {
            val user = userService.authenticate(request.username, request.password)
                ?: throw SecurityException("Invalid credentials")

            return LoginResponse().apply {
                this.user = user
            }
        }
    }
    ```

## Implement JWT Service

This section implements the core JWT token management functionality that powers your authentication system. The JWT service handles the cryptographic operations for creating, validating, and extracting information from JSON Web Tokens. This is the security foundation of your application because it:

- **Generates Secure Tokens**: Creates cryptographically signed JWTs with user claims and expiration
- **Validates Token Integrity**: Verifies token signatures and prevents tampering
- **Manages Token Lifecycle**: Handles both access tokens (short-lived) and refresh tokens (long-lived)
- **Extracts User Context**: Parses token claims to reconstruct user identity and permissions
- **Implements Security Best Practices**: Uses proper key management and secure algorithms

The service provides:
- **Access Token Generation**: Short-lived tokens (15 minutes) for API authentication
- **Refresh Token Generation**: Long-lived tokens (7 days) for seamless token renewal
- **Token Validation**: Cryptographic verification of token signatures and claims
- **User Extraction**: Converting token claims back to user objects for authorization
- **Configuration Management**: Externalized secrets and expiration settings

This service is critical for security - any vulnerability here could compromise your entire authentication system.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/security/JwtService.java`:

    ```java
    package ru.tinkoff.kora.example.security;

    import io.jsonwebtoken.Claims;
    import io.jsonwebtoken.Jwts;
    import io.jsonwebtoken.security.Keys;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.config.common.ConfigSource;
    import ru.tinkoff.kora.example.openapi.userapi.model.User;

    import javax.crypto.SecretKey;
    import java.time.Instant;
    import java.time.temporal.ChronoUnit;
    import java.util.Date;
    import java.util.HashMap;
    import java.util.List;
    import java.util.Map;

    @Component
    public final class JwtService {

        private final SecretKey accessTokenKey;
        private final SecretKey refreshTokenKey;
        private final long accessTokenExpirationMinutes;
        private final long refreshTokenExpirationDays;

        public JwtService(@ConfigSource("jwt") JwtConfig config) {
            this.accessTokenKey = Keys.hmacShaKeyFor(config.accessTokenSecret().getBytes());
            this.refreshTokenKey = Keys.hmacShaKeyFor(config.refreshTokenSecret().getBytes());
            this.accessTokenExpirationMinutes = config.accessTokenExpirationMinutes();
            this.refreshTokenExpirationDays = config.refreshTokenExpirationDays();
        }

        public String generateAccessToken(User user) {
            Map<String, Object> claims = new HashMap<>();
            claims.put("userId", user.getId());
            claims.put("username", user.getUsername());
            claims.put("email", user.getEmail());
            claims.put("roles", user.getRoles());

            return Jwts.builder()
                    .claims(claims)
                    .subject(user.getUsername())
                    .issuedAt(new Date())
                    .expiration(Date.from(Instant.now().plus(accessTokenExpirationMinutes, ChronoUnit.MINUTES)))
                    .signWith(accessTokenKey)
                    .compact();
        }

        public String generateRefreshToken(User user) {
            return Jwts.builder()
                    .subject(user.getUsername())
                    .issuedAt(new Date())
                    .expiration(Date.from(Instant.now().plus(refreshTokenExpirationDays, ChronoUnit.DAYS)))
                    .signWith(refreshTokenKey)
                    .compact();
        }

        public Claims validateAccessToken(String token) {
            return Jwts.parser()
                    .verifyWith(accessTokenKey)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
        }

        public Claims validateRefreshToken(String token) {
            return Jwts.parser()
                    .verifyWith(refreshTokenKey)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
        }

        public User extractUserFromToken(String token) {
            Claims claims = validateAccessToken(token);
            return new User()
                    .id(claims.get("userId", String.class))
                    .username(claims.getSubject())
                    .email(claims.get("email", String.class))
                    .roles((List<String>) claims.get("roles"));
        }

        @ConfigSource("jwt")
        public interface JwtConfig {
            String accessTokenSecret();
            String refreshTokenSecret();
            long accessTokenExpirationMinutes(); // default 15
            long refreshTokenExpirationDays(); // default 7
        }
    }
    ```

    Create `src/main/java/ru/tinkoff/kora/example/security/UserPrincipal.java`:

    ```java
    package ru.tinkoff.kora.example.security;

    import ru.tinkoff.kora.common.Principal;
    import ru.tinkoff.kora.example.openapi.userapi.model.User;

    import java.util.Collection;
    import java.util.List;

    public record UserPrincipal(User user) implements Principal {

        @Override
        public String name() {
            return user.getUsername();
        }

        public String userId() {
            return user.getId();
        }

        public List<String> roles() {
            return user.getRoles();
        }

        public boolean hasRole(String role) {
            return roles().contains(role);
        }

        public boolean hasAnyRole(String... roles) {
            return List.of(roles).stream().anyMatch(this::hasRole);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/security/JwtService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.security

    import io.jsonwebtoken.Claims
    import io.jsonwebtoken.Jwts
    import io.jsonwebtoken.security.Keys
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.config.common.ConfigSource
    import ru.tinkoff.kora.example.openapi.userapi.model.User
    import java.time.Instant
    import java.time.temporal.ChronoUnit
    import java.util.*
    import javax.crypto.SecretKey

    @Component
    class JwtService(
        @ConfigSource("jwt") private val config: JwtConfig
    ) {

        private val accessTokenKey: SecretKey = Keys.hmacShaKeyFor(config.accessTokenSecret().toByteArray())
        private val refreshTokenKey: SecretKey = Keys.hmacShaKeyFor(config.refreshTokenSecret().toByteArray())

        fun generateAccessToken(user: User): String {
            val claims = mapOf(
                "userId" to user.id,
                "username" to user.username,
                "email" to user.email,
                "roles" to user.roles
            )

            return Jwts.builder()
                .claims(claims)
                .subject(user.username)
                .issuedAt(Date())
                .expiration(Date.from(Instant.now().plus(config.accessTokenExpirationMinutes, ChronoUnit.MINUTES)))
                .signWith(accessTokenKey)
                .compact()
        }

        fun generateRefreshToken(user: User): String {
            return Jwts.builder()
                .subject(user.username)
                .issuedAt(Date())
                .expiration(Date.from(Instant.now().plus(config.refreshTokenExpirationDays, ChronoUnit.DAYS)))
                .signWith(refreshTokenKey)
                .compact()
        }

        fun validateAccessToken(token: String): Claims {
            return Jwts.parser()
                .verifyWith(accessTokenKey)
                .build()
                .parseSignedClaims(token)
                .payload
        }

        fun validateRefreshToken(token: String): Claims {
            return Jwts.parser()
                .verifyWith(refreshTokenKey)
                .build()
                .parseSignedClaims(token)
                .payload
        }

        fun extractUserFromToken(token: String): User {
            val claims = validateAccessToken(token)
            return User().apply {
                id = claims["userId"] as String
                username = claims.subject
                email = claims["email"] as String
                roles = claims["roles"] as List<String>
            }
        }

        @ConfigSource("jwt")
        interface JwtConfig {
            fun accessTokenSecret(): String
            fun refreshTokenSecret(): String
            fun accessTokenExpirationMinutes(): Long // default 15
            fun refreshTokenExpirationDays(): Long // default 7
        }
    }
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/example/security/UserPrincipal.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.security

    import ru.tinkoff.kora.common.Principal
    import ru.tinkoff.kora.example.openapi.userapi.model.User

    data class UserPrincipal(val user: User) : Principal {

        override fun name(): String = user.username

        val userId: String
            get() = user.id

        val roles: List<String>
            get() = user.roles

        fun hasRole(role: String): Boolean = roles.contains(role)

        fun hasAnyRole(vararg roles: String): Boolean = roles.any { this.roles.contains(it) }
    }
    ```

## Update Authentication Services

This section bridges your basic authentication with JWT token management, transforming your AuthService from a simple credential validator into a complete authentication orchestrator. The updated service becomes the central hub that coordinates user authentication, token generation, and token refresh operations - essentially the "conductor" of your authentication symphony.

The AuthService now serves as the critical integration point that:

- **Authenticates User Credentials**: Validates username/password combinations against your user store
- **Orchestrates Token Generation**: Coordinates with JwtService to create both access and refresh tokens upon successful login
- **Manages Token Lifecycle**: Handles refresh token validation and generates new token pairs for seamless user experience
- **Provides Unified API**: Offers a clean interface for login and token refresh operations that your HTTP endpoints can consume
- **Implements Security Boundaries**: Enforces authentication rules and throws appropriate security exceptions for invalid credentials

This service is the operational heart of your JWT authentication system - it connects user authentication with token management, ensuring that every login produces valid tokens and every token refresh maintains security integrity. Without this orchestration layer, your JWT tokens would be just cryptographic artifacts without meaningful user context.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/security/AuthService.java`:

    ```java
    package ru.tinkoff.kora.example.security;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginRequest;
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginResponse;

    @Component
    public final class AuthService {

        private final UserService userService;
        private final JwtService jwtService;

        public AuthService(UserService userService, JwtService jwtService) {
            this.userService = userService;
            this.jwtService = jwtService;
        }

        public LoginResponse login(LoginRequest request) {
            var user = userService.authenticate(request.getUsername(), request.getPassword());
            if (user == null) {
                throw new SecurityException("Invalid credentials");
            }

            var accessToken = jwtService.generateAccessToken(user);
            var refreshToken = jwtService.generateRefreshToken(user);

            return new LoginResponse()
                    .token(accessToken)
                    .refreshToken(refreshToken)
                    .expiresIn(15 * 60) // 15 minutes
                    .user(user);
        }

        public LoginResponse refreshToken(String refreshToken) {
            try {
                var claims = jwtService.validateRefreshToken(refreshToken);
                var username = claims.getSubject();
                var user = userService.findByUsername(username);

                if (user == null) {
                    throw new SecurityException("User not found");
                }

                var newAccessToken = jwtService.generateAccessToken(user);
                var newRefreshToken = jwtService.generateRefreshToken(user);

                return new LoginResponse()
                        .token(newAccessToken)
                        .refreshToken(newRefreshToken)
                        .expiresIn(15 * 60)
                        .user(user);
            } catch (Exception e) {
                throw new SecurityException("Invalid refresh token");
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/security/AuthService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.security

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginRequest
    import ru.tinkoff.kora.example.openapi.userapi.model.LoginResponse

    @Component
    class AuthService(
        private val userService: UserService,
        private val jwtService: JwtService
    ) {

        fun login(request: LoginRequest): LoginResponse {
            val user = userService.authenticate(request.username, request.password)
                ?: throw SecurityException("Invalid credentials")

            val accessToken = jwtService.generateAccessToken(user)
            val refreshToken = jwtService.generateRefreshToken(user)

            return LoginResponse().apply {
                token = accessToken
                this.refreshToken = refreshToken
                expiresIn = 15 * 60 // 15 minutes
                this.user = user
            }
        }

        fun refreshToken(refreshToken: String): LoginResponse {
            return try {
                val claims = jwtService.validateRefreshToken(refreshToken)
                val username = claims.subject
                val user = userService.findByUsername(username)
                    ?: throw SecurityException("User not found")

                val newAccessToken = jwtService.generateAccessToken(user)
                val newRefreshToken = jwtService.generateRefreshToken(user)

                LoginResponse().apply {
                    token = newAccessToken
                    this.refreshToken = newRefreshToken
                    expiresIn = 15 * 60
                    this.user = user
                }
            } catch (e: Exception) {
                throw SecurityException("Invalid refresh token")
            }
        }
    }
    ```

## Implement Password Encoder

This section implements the cryptographic foundation of your authentication system as a dedicated Kora component - a secure password encoder that protects user credentials. The password encoder is the critical security component that transforms plain-text passwords into cryptographically secure hashes that cannot be reversed, making it the first line of defense against credential theft.

By implementing it as a `@Component` class, you get several architectural benefits:
- **Dependency Injection**: The component can be injected wherever password encoding is needed
- **Testability**: The encoder can be easily mocked or tested in isolation
- **Reusability**: The same encoder instance is shared across your application
- **Configuration**: Future enhancements can add configuration injection if needed

The password encoder serves several crucial security functions:

- **One-Way Hashing**: Converts passwords into irreversible hashes using PBKDF2 (Password-Based Key Derivation Function 2) with HMAC-SHA256
- **Salt Generation**: Creates unique random salts for each password to prevent rainbow table attacks
- **Work Factor Control**: Uses 100,000 iterations to make brute-force attacks computationally expensive
- **Constant-Time Comparison**: Prevents timing attacks by comparing hashes in constant time regardless of password length
- **Secure Storage Format**: Combines salt and hash in a Base64-encoded format for safe database storage

The implementation uses Java's built-in cryptographic functions (no external dependencies) and follows security best practices:
- **PBKDF2WithHmacSHA256**: Industry-standard key derivation function
- **256-bit Output**: Provides sufficient cryptographic strength
- **16-byte Salt**: Random salt generation prevents pre-computed attacks
- **High Iteration Count**: Makes password cracking prohibitively expensive
- **Exception Handling**: Graceful failure handling for cryptographic operations

This encoder is the foundation that makes your JWT authentication secure - without it, even the most sophisticated token system would be vulnerable to credential compromise.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/security/PasswordEncoderComponent.java`:

    ```java
    package ru.tinkoff.kora.example.security;

    import org.springframework.security.crypto.password.PasswordEncoder;
    import ru.tinkoff.kora.common.Component;

    import javax.crypto.SecretKeyFactory;
    import javax.crypto.spec.PBEKeySpec;
    import java.security.NoSuchAlgorithmException;
    import java.security.SecureRandom;
    import java.security.spec.InvalidKeySpecException;
    import java.security.spec.KeySpec;
    import java.util.Base64;

    @Component
    public final class PasswordEncoderComponent implements PasswordEncoder {

        private static final int ITERATIONS = 100000; // High iteration count for demo
        private static final int KEY_LENGTH = 256; // 256-bit key
        private final SecureRandom random = new SecureRandom();

        @Override
        public String encode(CharSequence rawPassword) {
            try {
                // Generate a unique random salt for this password
                byte[] salt = new byte[16];
                random.nextBytes(salt);

                // Create PBKDF2 specification with password, salt, iterations, and key length
                KeySpec spec = new PBEKeySpec(rawPassword.toString().toCharArray(), salt, ITERATIONS, KEY_LENGTH);

                // Use PBKDF2 with HMAC-SHA256 for key derivation
                SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");

                // Generate the cryptographic hash
                byte[] hash = factory.generateSecret(spec).getEncoded();

                // Store salt and hash together in format: salt:hash (Base64 encoded)
                return Base64.getEncoder().encodeToString(salt) + ":" +
                       Base64.getEncoder().encodeToString(hash);
            } catch (NoSuchAlgorithmException | InvalidKeySpecException e) {
                throw new RuntimeException("Error encoding password", e);
            }
        }

        @Override
        public boolean matches(CharSequence rawPassword, String encodedPassword) {
            try {
                // Split the stored format into salt and hash components
                String[] parts = encodedPassword.split(":");
                if (parts.length != 2) return false;

                // Decode the Base64-encoded salt and hash
                byte[] salt = Base64.getDecoder().decode(parts[0]);
                byte[] storedHash = Base64.getDecoder().decode(parts[1]);

                // Recreate the same PBKDF2 specification used during encoding
                KeySpec spec = new PBEKeySpec(rawPassword.toString().toCharArray(), salt, ITERATIONS, KEY_LENGTH);
                SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");

                // Generate hash for the provided password using the same salt
                byte[] computedHash = factory.generateSecret(spec).getEncoded();

                // Compare hashes in constant time to prevent timing attacks
                return constantTimeEquals(storedHash, computedHash);
            } catch (Exception e) {
                return false;
            }
        }

        /**
         * Compares two byte arrays in constant time to prevent timing attacks.
         * This ensures that password verification takes the same amount of time
         * regardless of how many bytes match, preventing attackers from gaining
         * information about partial password matches.
         */
        private boolean constantTimeEquals(byte[] a, byte[] b) {
            if (a.length != b.length) return false;
            int result = 0;
            for (int i = 0; i < a.length; i++) {
                result |= a[i] ^ b[i]; // XOR operation - result is 0 only if bytes are identical
            }
            return result == 0;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/security/PasswordEncoderComponent.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.security

    import org.springframework.security.crypto.password.PasswordEncoder
    import ru.tinkoff.kora.common.Component
    import java.security.SecureRandom
    import java.security.spec.KeySpec
    import javax.crypto.SecretKeyFactory
    import javax.crypto.spec.PBEKeySpec

    @Component
    class PasswordEncoderComponent : PasswordEncoder {

        private val ITERATIONS = 100000 // High iteration count for demo
        private val KEY_LENGTH = 256 // 256-bit key
        private val random = SecureRandom()

        override fun encode(rawPassword: CharSequence): String {
            try {
                // Generate a unique random salt for this password
                val salt = ByteArray(16)
                random.nextBytes(salt)

                // Create PBKDF2 specification with password, salt, iterations, and key length
                val spec: KeySpec = PBEKeySpec(rawPassword.toString().toCharArray(), salt, ITERATIONS, KEY_LENGTH)

                // Use PBKDF2 with HMAC-SHA256 for key derivation
                val factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")

                // Generate the cryptographic hash
                val hash = factory.generateSecret(spec).encoded

                // Store salt and hash together in format: salt:hash (Base64 encoded)
                return Base64.getEncoder().encodeToString(salt) + ":" +
                       Base64.getEncoder().encodeToString(hash)
            } catch (e: Exception) {
                throw RuntimeException("Error encoding password", e)
            }
        }

        override fun matches(rawPassword: CharSequence, encodedPassword: String): Boolean {
            return try {
                // Split the stored format into salt and hash components
                val parts = encodedPassword.split(":")
                if (parts.size != 2) return false

                // Decode the Base64-encoded salt and hash
                val salt = Base64.getDecoder().decode(parts[0])
                val storedHash = Base64.getDecoder().decode(parts[1])

                // Recreate the same PBKDF2 specification used during encoding
                val spec: KeySpec = PBEKeySpec(rawPassword.toString().toCharArray(), salt, ITERATIONS, KEY_LENGTH)
                val factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")

                // Generate hash for the provided password using the same salt
                val computedHash = factory.generateSecret(spec).encoded

                // Compare hashes in constant time to prevent timing attacks
                constantTimeEquals(storedHash, computedHash)
            } catch (e: Exception) {
                false
            }
        }

        /**
         * Compares two byte arrays in constant time to prevent timing attacks.
         * This ensures that password verification takes the same amount of time
         * regardless of how many bytes match, preventing attackers from gaining
         * information about partial password matches.
         */
        private fun constantTimeEquals(a: ByteArray, b: ByteArray): Boolean {
            if (a.size != b.size) return false
            var result = 0
            for (i in a.indices) {
                result = result or (a[i].toInt() xor b[i].toInt()) // XOR operation - result is 0 only if bytes are identical
            }
            return result == 0
        }
    }
    ```

## Configure JWT Authentication

Update your Application class to configure JWT authentication:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.common.Principal;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.example.openapi.userapi.api.ApiSecurity;
    import ru.tinkoff.kora.example.security.JwtService;
    import ru.tinkoff.kora.example.security.UserPrincipal;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.http.server.common.auth.HttpServerPrincipalExtractor;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.validation.module.ValidationModule;
    import ru.tinkoff.kora.validation.module.http.server.ViolationExceptionHttpServerResponseMapper;

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

        // JWT Bearer token authentication
        @Tag(ApiSecurity.BearerAuth.class)
        default HttpServerPrincipalExtractor<Principal> bearerHttpServerPrincipalExtractor(JwtService jwtService) {
            return (request, token) -> {
                try {
                    var user = jwtService.extractUserFromToken(token);
                    return CompletableFuture.completedFuture(new UserPrincipal(user));
                } catch (Exception e) {
                    throw new SecurityException("Invalid JWT token");
                }
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.common.Principal
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.example.openapi.userapi.api.ApiSecurity
    import ru.tinkoff.kora.example.security.JwtService
    import ru.tinkoff.kora.example.security.UserPrincipal
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

        // JWT Bearer token authentication
        @Tag(ApiSecurity.BearerAuth::class)
        fun bearerHttpServerPrincipalExtractor(jwtService: JwtService): HttpServerPrincipalExtractor<Principal> {
            return HttpServerPrincipalExtractor { request, token ->
                try {
                    val user = jwtService.extractUserFromToken(token)
                    CompletableFuture.completedFuture(UserPrincipal(user))
                } catch (e: Exception) {
                    throw SecurityException("Invalid JWT token")
                }
            }
        }
    }
    ```

## Update User API Delegate

Add JWT token refresh endpoint to your UserApiDelegate:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/UserApiDelegate.java`:

    ```java
    // ... existing code ...

    @Override
    public UserApiResponses.LoginApiResponse login(LoginRequest request) {
        try {
            var response = authService.login(request);
            return new UserApiResponses.LoginApiResponse.Login200ApiResponse(response);
        } catch (SecurityException e) {
            return new UserApiResponses.LoginApiResponse.Login401ApiResponse();
        }
    }

    @Override
    public UserApiResponses.RefreshTokenApiResponse refreshToken(Object request) {
        // Extract refresh token from request body
        if (!(request instanceof Map<?, ?> map) || !map.containsKey("refreshToken")) {
            return new UserApiResponses.RefreshTokenApiResponse.RefreshToken400ApiResponse();
        }

        var refreshToken = (String) map.get("refreshToken");
        try {
            var response = authService.refreshToken(refreshToken);
            return new UserApiResponses.RefreshTokenApiResponse.RefreshToken200ApiResponse(response);
        } catch (SecurityException e) {
            return new UserApiResponses.RefreshTokenApiResponse.RefreshToken401ApiResponse();
        }
    }

    // ... rest of existing code ...
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/UserApiDelegate.kt`:

    ```kotlin
    // ... existing code ...

    override fun login(request: LoginRequest): UserApiResponses.LoginApiResponse {
        return try {
            val response = authService.login(request)
            UserApiResponses.LoginApiResponse.Login200ApiResponse(response)
        } catch (e: SecurityException) {
            UserApiResponses.LoginApiResponse.Login401ApiResponse()
        }
    }

    override fun refreshToken(request: Any): UserApiResponses.RefreshTokenApiResponse {
        val map = request as? Map<*, *> ?: return UserApiResponses.RefreshTokenApiResponse.RefreshToken400ApiResponse()
        val refreshToken = map["refreshToken"] as? String ?: return UserApiResponses.RefreshTokenApiResponse.RefreshToken400ApiResponse()

        return try {
            val response = authService.refreshToken(refreshToken)
            UserApiResponses.RefreshTokenApiResponse.RefreshToken200ApiResponse(response)
        } catch (e: SecurityException) {
            UserApiResponses.RefreshTokenApiResponse.RefreshToken401ApiResponse()
        }
    }

    // ... rest of existing code ...
    ```

## JWT Configuration

Add JWT configuration to your `application.conf`:

```hocon
# ... existing configuration ...

# JWT Configuration
jwt {
  accessTokenSecret = "your-super-secret-access-token-key-that-is-at-least-256-bits-long"
  refreshTokenSecret = "your-super-secret-refresh-token-key-that-is-at-least-256-bits-long"
  accessTokenExpirationMinutes = 15
  refreshTokenExpirationDays = 7
}

# HTTP Server Configuration
httpServer {
  publicApiHttpPort = 8080
}
```

## Test JWT Authentication

Create comprehensive tests for JWT functionality:

===! ":fontawesome-brands-java: `Java`"

    Update `src/test/java/ru/tinkoff/kora/example/UserApiAuthenticationTest.java`:

    ```java
    // ... existing imports and test setup ...

    @Test
    void testJwtLoginSuccess(AuthService authService) {
        var request = new LoginRequest()
                .username("admin")
                .password("admin123");

        var response = authService.login(request);

        assertNotNull(response);
        assertNotNull(response.getToken());
        assertNotNull(response.getRefreshToken());
        assertEquals(900, response.getExpiresIn()); // 15 minutes
        assertNotNull(response.getUser());
        assertEquals("admin", response.getUser().getUsername());
    }

    @Test
    void testJwtTokenRefresh(AuthService authService) {
        // First login to get tokens
        var loginRequest = new LoginRequest()
                .username("admin")
                .password("admin123");
        var loginResponse = authService.login(loginRequest);

        // Then refresh the token
        var refreshResponse = authService.refreshToken(loginResponse.getRefreshToken());

        assertNotNull(refreshResponse);
        assertNotNull(refreshResponse.getToken());
        assertNotNull(refreshResponse.getRefreshToken());
        assertNotEquals(loginResponse.getToken(), refreshResponse.getToken()); // New access token
        assertNotEquals(loginResponse.getRefreshToken(), refreshResponse.getRefreshToken()); // New refresh token
    }

    @Test
    void testJwtInvalidRefreshToken(AuthService authService) {
        assertThrows(SecurityException.class, () -> authService.refreshToken("invalid-token"));
    }

    @KoraConfigModifier
    static KoraConfigModifier jwtConfigModifier() {
        return config -> config
            .put("jwt.accessTokenSecret", "test-access-token-secret-key-that-is-long-enough-for-hmac")
            .put("jwt.refreshTokenSecret", "test-refresh-token-secret-key-that-is-long-enough-for-hmac")
            .put("jwt.accessTokenExpirationMinutes", 15)
            .put("jwt.refreshTokenExpirationDays", 7);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/test/kotlin/ru/tinkoff/kora/example/UserApiAuthenticationTest.kt`:

    ```kotlin
    // ... existing imports and test setup ...

    @Test
    fun testJwtLoginSuccess(authService: AuthService) {
        val request = LoginRequest().apply {
            username = "admin"
            password = "admin123"
        }

        val response = authService.login(request)

        assertNotNull(response)
        assertNotNull(response.token)
        assertNotNull(response.refreshToken)
        assertEquals(900, response.expiresIn) // 15 minutes
        assertNotNull(response.user)
        assertEquals("admin", response.user.username)
    }

    @Test
    fun testJwtTokenRefresh(authService: AuthService) {
        // First login to get tokens
        val loginRequest = LoginRequest().apply {
            username = "admin"
            password = "admin123"
        }
        val loginResponse = authService.login(loginRequest)

        // Then refresh the token
        val refreshResponse = authService.refreshToken(loginResponse.refreshToken)

        assertNotNull(refreshResponse)
        assertNotNull(refreshResponse.token)
        assertNotNull(refreshResponse.refreshToken)
        assertNotEquals(loginResponse.token, refreshResponse.token) // New access token
        assertNotEquals(loginResponse.refreshToken, refreshResponse.refreshToken) // New refresh token
    }

    @Test
    fun testJwtInvalidRefreshToken(authService: AuthService) {
        org.junit.jupiter.api.assertThrows<SecurityException> {
            authService.refreshToken("invalid-token")
        }
    }

    @KoraConfigModifier
    fun jwtConfigModifier(): KoraConfigModifier {
        return KoraConfigModifier { config ->
            config.put("jwt.accessTokenSecret", "test-access-token-secret-key-that-is-long-enough-for-hmac")
            config.put("jwt.refreshTokenSecret", "test-refresh-token-secret-key-that-is-long-enough-for-hmac")
            config.put("jwt.accessTokenExpirationMinutes", 15)
            config.put("jwt.refreshTokenExpirationDays", 7)
        }
    }
    ```

Run your JWT tests:

```bash
./gradlew test --tests "*AuthenticationTest*"
```

## Testing JWT Authentication

### Test JWT Bearer Authentication

```bash
# 1. Login to get JWT token
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 2. Use the token to access protected endpoints
curl -X GET http://localhost:8080/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

### Test JWT Token Refresh

```bash
# Refresh an expired access token
curl -X POST http://localhost:8080/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refreshToken": "your-refresh-token-here"}'
```

## JWT Security Best Practices

### Token Security
- **Strong secrets**: Use 256+ bit keys for HMAC-SHA256
- **Short-lived access tokens**: 15 minutes expiration
- **Secure refresh tokens**: 7+ days with rotation
- **Token validation**: Verify signatures on every request

### Implementation Security
- **Secure storage**: Never store tokens in localStorage (use httpOnly cookies)
- **HTTPS only**: Always use encrypted connections
- **Token blacklisting**: Implement for logout/compromised tokens
- **Rate limiting**: Prevent token brute force attacks

### Advanced JWT Features

**Custom Claims**: Add application-specific data to tokens:

```java
public String generateAccessToken(User user) {
    Map<String, Object> claims = new HashMap<>();
    claims.put("userId", user.getId());
    claims.put("username", user.getUsername());
    claims.put("email", user.getEmail());
    claims.put("roles", user.getRoles());
    claims.put("permissions", getUserPermissions(user)); // Custom claim

    return Jwts.builder()
            .claims(claims)
            .subject(user.getUsername())
            .issuedAt(new Date())
            .expiration(Date.from(Instant.now().plus(accessTokenExpirationMinutes, ChronoUnit.MINUTES)))
            .signWith(accessTokenKey)
            .compact();
}
```

**Token Blacklisting**: Implement token revocation:

```java
@Component
public class TokenBlacklistService {
    private final Set<String> blacklistedTokens = ConcurrentHashMap.newKeySet();

    public void blacklistToken(String token) {
        blacklistedTokens.add(token);
    }

    public boolean isTokenBlacklisted(String token) {
        return blacklistedTokens.contains(token);
    }
}
```

## Next Steps

Now that you have a complete JWT authentication system, consider these enhancements:

- **Token persistence**: Store refresh tokens securely in database
- **Multi-factor authentication**: Add 2FA to login flow
- **Social login**: Integrate Google/GitHub OAuth with JWT
- **Microservices**: Use JWT for service-to-service authentication
- **Token introspection**: Implement token validation endpoints
- **Role-based access control**: Implement fine-grained permissions
- **Audit logging**: Track authentication events
- **Token blacklisting**: Implement comprehensive token revocation

Your JWT authentication system is now production-ready with secure token management, user authentication, and protected API endpoints! 🔐