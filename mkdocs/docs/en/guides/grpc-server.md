---
title: gRPC Server with Kora
summary: Build production-ready gRPC services with protocol buffers and unary RPC methods
tags: grpc-server, protobuf, rpc, microservices
---

# gRPC Server with Kora

This guide shows you how to build production-ready gRPC services using Kora's gRPC server module. You'll learn about protocol buffers, service definition, request/response handling, and advanced server configuration for microservices communication.

## Understanding gRPC and Protocol Buffers

### What is gRPC?

gRPC (gRPC Remote Procedure Call) is a modern, high-performance, open-source universal RPC framework developed by Google. It enables client and server applications to communicate transparently, and it supports multiple programming languages. gRPC is based on the HTTP/2 protocol and uses Protocol Buffers (Protobuf) as its interface definition language (IDL) and underlying message interchange format.

#### Key Features of gRPC:

- **Language Agnostic**: Supports multiple programming languages including Java, Go, Python, C++, Node.js, and more
- **Efficient Communication**: Uses HTTP/2 for transport, enabling features like multiplexing, flow control, and header compression
- **Strong Typing**: Uses Protocol Buffers for type-safe message definitions
- **Unary RPC Support**: Simple and reliable request-response communication pattern
- **Built-in Features**: Includes authentication, load balancing, and monitoring capabilities
- **Performance**: Significantly faster than REST APIs using JSON due to binary serialization and HTTP/2 efficiency

#### Why Use gRPC?

- **Microservices Communication**: Ideal for service-to-service communication in distributed systems
- **High Performance**: Binary serialization and HTTP/2 provide better performance than JSON over HTTP/1.1
- **Type Safety**: Compile-time guarantees prevent runtime errors from mismatched data structures
- **Code Generation**: Automatic generation of client and server code reduces boilerplate
- **Interoperability**: Works across different programming languages and platforms

### What are Protocol Buffers?

Protocol Buffers (Protobuf) is Google's language-neutral, platform-neutral, extensible mechanism for serializing structured data. It's similar to XML or JSON but smaller, faster, and simpler.

#### Key Characteristics:

- **Binary Format**: Uses efficient binary encoding instead of text-based formats like JSON or XML
- **Schema-Driven**: Requires a `.proto` file that defines the structure of your data
- **Code Generation**: Generates strongly-typed classes in your target language
- **Version Compatibility**: Supports forward and backward compatibility
- **Compact**: Typically 3-10 times smaller than equivalent JSON/XML
- **Fast**: 20-100 times faster to serialize/deserialize than JSON

#### Protobuf vs JSON Comparison:

| Aspect | Protocol Buffers | JSON |
|--------|------------------|------|
| **Size** | Compact binary | Verbose text |
| **Speed** | Very fast | Slower parsing |
| **Type Safety** | Strongly typed | Weakly typed |
| **Schema** | Required (.proto) | Optional |
| **Code Generation** | Automatic | Manual/Optional |
| **Compatibility** | Built-in | Manual handling |

#### Protobuf Syntax Basics:

```protobuf
syntax = "proto3";  // Use proto3 syntax

message Person {
  string name = 1;      // Field number 1
  int32 age = 2;        // Field number 2
  repeated string emails = 3;  // Repeated field
}

service PersonService {
  rpc GetPerson(GetPersonRequest) returns (Person) {}  // Unary RPC
}
```

### How gRPC and Protobuf Work Together

1. **Define Services**: Create `.proto` files defining your service interfaces and message types
2. **Code Generation**: Use protoc compiler to generate client and server code in your target language
3. **Implement Services**: Implement the generated service interfaces on the server
4. **Client Usage**: Use generated client stubs to call remote methods
5. **Communication**: Messages are serialized using Protobuf and transported over HTTP/2

### gRPC Architecture

```
┌─────────────┐          ┌─────────────┐
│   Client    │          │   Server    │
│             │          │             │
│ ┌─────────┐ │          │ ┌─────────┐ │
│ │ Stub    │◄┼─────────►│ │ Service │ │
│ │ (Auto-  │ │   gRPC   │ │ (Your   │ │
│ │ gen'd)  │ │          │ │ Impl)   │ │
│ └─────────┘ │          │ └─────────┘ │
└─────────────┘          └─────────────┘
       ▲                       ▲
       │                       │
┌─────────────┐          ┌─────────────┐
│ Protobuf    │          │ Protobuf    │
│ Messages    │          │ Messages    │
│ (Auto-gen'd)│          │ (Auto-gen'd)│
└─────────────┘          └─────────────┘
```

This architecture provides type-safe, efficient communication between distributed services.

## What You'll Build

You'll build a UserService gRPC server with:

- **Protocol Buffer Definitions**: Define gRPC services and messages using .proto files
- **Unary RPC Methods**: Simple request-response operations for creating and retrieving users
- **Advanced Configuration**: Performance tuning, telemetry, and production features
- **Error Handling**: Proper gRPC status codes and error responses
- **Interceptors**: Custom request/response processing middleware

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide
- Basic understanding of [Protocol Buffers](https://developers.google.com/protocol-buffers)

## Prerequisites

!!! note "Required: Complete Basic Kora Setup"

    This guide assumes you have completed the **[Create Your First Kora App](../getting-started.md)** guide and have a working Kora project with basic setup.

    If you haven't completed the basic guide yet, please do so first as this guide builds upon that foundation.

## Add Dependencies

To build gRPC services with Kora, you need to add several key dependencies to your project. Each dependency serves a specific purpose in the gRPC ecosystem:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        // Kora gRPC Server Module - Core gRPC server implementation with dependency injection
        implementation("ru.tinkoff.kora:grpc-server")

        // gRPC Protobuf Support - Runtime support for Protocol Buffer serialization
        implementation("io.grpc:grpc-protobuf:1.62.2")

        // Java Annotations API - Required for annotation processing and runtime reflection
        implementation("javax.annotation:javax.annotation-api:1.3.2")
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        // Kora gRPC Server Module - Core gRPC server implementation with dependency injection
        implementation("ru.tinkoff.kora:grpc-server")

        // gRPC Protobuf Support - Runtime support for Protocol Buffer serialization
        implementation("io.grpc:grpc-protobuf:1.62.2")

        // Java Annotations API - Required for annotation processing and runtime reflection
        implementation("javax.annotation:javax.annotation-api:1.3.2")
    }
    ```

### Dependency Breakdown:

- **`ru.tinkoff.kora:grpc-server`**: The core Kora module that provides gRPC server functionality. This includes:
  - Server lifecycle management
  - Integration with Kora's dependency injection system
  - Automatic service registration
  - Configuration binding
  - Telemetry integration (metrics, tracing, logging)

- **`io.grpc:grpc-protobuf:1.62.2`**: The official gRPC Java library that provides:
  - Protocol Buffer message serialization/deserialization
  - gRPC stub generation and communication
  - HTTP/2 transport layer
  - Built-in interceptors and middleware support

- **`javax.annotation:javax.annotation-api:1.3.2`**: Provides standard Java annotations that are used by:
  - gRPC's annotation processing
  - Kora's component scanning
  - Runtime reflection operations

These dependencies work together to provide a complete gRPC server implementation that integrates seamlessly with Kora's application framework.

## Configure Protocol Buffers Plugin

The Protocol Buffers plugin for Gradle is essential for generating Java/Kotlin code from your `.proto` files. This plugin automates the code generation process and integrates it into your build lifecycle.

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    plugins {
        // ... existing plugins ...
        id "com.google.protobuf" version "0.9.4"
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.25.3" }
        plugins {
            grpc { artifact = "io.grpc:protoc-gen-grpc-java:1.62.2" }
        }
        generateProtoTasks {
            all()*.plugins { grpc {} }
        }
    }

    sourceSets {
        main.java {
            srcDirs "build/generated/source/proto/main/grpc"
            srcDirs "build/generated/source/proto/main/java"
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    import com.google.protobuf.gradle.id

    plugins {
        // ... existing plugins ...
        id("com.google.protobuf") version ("0.9.4")
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.25.3" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.62.2" }
        }
        generateProtoTasks {
            ofSourceSet("main").forEach { it.plugins { id("grpc") { } } }
        }
    }

    kotlin {
        sourceSets.main {
            kotlin.srcDir("build/generated/source/proto/main/grpc")
            kotlin.srcDir("build/generated/source/proto/main/java")
        }
    }
    ```

### Plugin Configuration Details:

#### Protobuf Plugin (`com.google.protobuf`)
- **Purpose**: Automates the compilation of `.proto` files into target language code
- **Version**: `0.9.4` - Latest stable version compatible with Gradle 7+
- **Functionality**: Downloads protoc compiler and plugins, manages code generation tasks

#### Protoc Compiler Configuration
- **`protoc.artifact`**: Specifies the Protocol Buffer compiler version (`3.25.3`)
- **Role**: The protoc compiler reads `.proto` files and generates language-specific code
- **Version Compatibility**: Must match the runtime gRPC version for optimal compatibility

#### gRPC Plugin Configuration
- **`grpc.artifact`**: Specifies the gRPC Java code generator version (`1.62.2`)
- **Generated Code**: Creates service base classes, client stubs, and server implementations
- **Integration**: Works with the protoc compiler to extend basic protobuf generation

#### Source Set Configuration
- **Java**: Adds generated directories to `main.java.srcDirs`
- **Kotlin**: Adds generated directories to `kotlin.srcDirs.main`
- **Purpose**: Makes generated code available for compilation and IDE recognition

#### Generated Code Locations:
- **`build/generated/source/proto/main/java`**: Protocol Buffer message classes
- **`build/generated/source/proto/main/grpc`**: gRPC service stubs and base classes

This configuration ensures that your `.proto` files are automatically compiled whenever you build your project, and the generated code is properly integrated into your source tree.

## Add Modules

Update your Application interface to include the GrpcServerModule:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.grpc.server.GrpcServerModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            GrpcServerModule,
            LogbackModule {
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.grpc.server.GrpcServerModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        GrpcServerModule,
        LogbackModule
    ```

## Define Protocol Buffers

Protocol Buffers are the core of gRPC services - they define your service interfaces, message structures, and data types. The `.proto` file serves as the single source of truth for your API contract, from which all client and server code is generated.

### Key Concepts in Protocol Buffers:

#### Service Definition
- **`service`**: Defines a gRPC service containing one or more RPC methods
- **`rpc`**: Defines a remote procedure call with request/response types

#### Message Types
- **`message`**: Defines structured data with typed fields
- **Field Numbers**: Unique identifiers for each field (1-536,870,911)
- **Field Types**: Primitive types (string, int32, bool) or custom messages
- **`repeated`**: Indicates an array/list of values
- **`enum`**: Defines enumerated types with integer values

#### Unary RPC Pattern
- **Unary**: `rpc Method(Request) returns (Response)` - Single request, single response
- **Simple and Reliable**: Most common pattern for basic CRUD operations
- **Synchronous**: Client waits for server response before continuing

#### Standard Imports
- **`google/protobuf/timestamp.proto`**: For timestamp fields
- **`google/protobuf/empty.proto`**: For methods that don't need request/response data

### Proto File Structure:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/proto/user_service.proto`:

    ```protobuf
    // Protocol Buffer syntax version (proto3 is recommended for new services)
    syntax = "proto3";

    // Package declaration - maps to Java/Kotlin package
    package ru.tinkoff.kora.example;

    // Import standard Google protobuf types
    import "google/protobuf/timestamp.proto";
    import "google/protobuf/empty.proto";

    // Service definition - contains all RPC methods
    service UserService {
      // Unary RPC: Simple request-response pattern
      rpc CreateUser(CreateUserRequest) returns (UserResponse) {}

      // Unary RPC: Retrieve single user by ID
      rpc GetUser(GetUserRequest) returns (UserResponse) {}
    }

    // Message definitions - data structures for requests and responses

    // Request message for creating a user
    message CreateUserRequest {
      string name = 1;   // Field number 1
      string email = 2;  // Field number 2
    }

    // Request message for retrieving a user
    message GetUserRequest {
      string user_id = 1;
    }

    // Response message containing user data
    message UserResponse {
      string id = 1;
      string name = 2;
      string email = 3;
      google.protobuf.Timestamp created_at = 4;  // Uses imported timestamp type
      UserStatus status = 5;  // Uses custom enum
    }

    // Enumeration for user status values
    enum UserStatus {
      ACTIVE = 0;     // Default value (first enum value should be 0)
      INACTIVE = 1;
      SUSPENDED = 2;
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/proto/user_service.proto`:

    ```protobuf
    // Protocol Buffer syntax version (proto3 is recommended for new services)
    syntax = "proto3";

    // Package declaration - maps to Java/Kotlin package
    package ru.tinkoff.kora.example;

    // Import standard Google protobuf types
    import "google/protobuf/timestamp.proto";
    import "google/protobuf/empty.proto";

    // Service definition - contains all RPC methods
    service UserService {
      // Unary RPC: Simple request-response pattern
      rpc CreateUser(CreateUserRequest) returns (UserResponse) {}

      // Unary RPC: Retrieve single user by ID
      rpc GetUser(GetUserRequest) returns (UserResponse) {}
    }

    // Message definitions - data structures for requests and responses

    // Request message for creating a user
    message CreateUserRequest {
      string name = 1;   // Field number 1
      string email = 2;  // Field number 2
    }

    // Request message for retrieving a user
    message GetUserRequest {
      string user_id = 1;
    }

    // Response message containing user data
    message UserResponse {
      string id = 1;
      string name = 2;
      string email = 3;
      google.protobuf.Timestamp created_at = 4;  // Uses imported timestamp type
      UserStatus status = 5;  // Uses custom enum
    }

    // Enumeration for user status values
    enum UserStatus {
      ACTIVE = 0;     // Default value (first enum value should be 0)
      INACTIVE = 1;
      SUSPENDED = 2;
    }
    ```

### Generated Code Structure:

When you run `./gradlew generateProto`, the following classes are generated:

#### Message Classes (in `build/generated/source/proto/main/java`):
- **`UserServiceOuterClass.java`**: Contains all message builders and parsers
- **`CreateUserRequest`**: Builder pattern for creating request messages
- **`UserResponse`**: Strongly-typed user data structure
- **`UserStatus`**: Enum with proper constants

#### Service Classes (in `build/generated/source/proto/main/grpc`):
- **`UserServiceGrpc.java`**: Contains service base classes and client stubs
- **`UserServiceImplBase`**: Abstract base class for server implementations
- **Client stubs**: For calling the service from clients

### Best Practices for Protocol Buffers:

1. **Field Numbers**: Never change field numbers once assigned (breaks compatibility)
2. **Package Naming**: Use reverse domain notation (e.g., `com.example.service`)
3. **Message Naming**: Use PascalCase for message names
4. **Field Naming**: Use snake_case for field names (converts to camelCase in generated code)
5. **Versioning**: Use package names or service names for versioning, not field changes
6. **Documentation**: Add comments to services and messages for API documentation

This `.proto` file serves as your API contract and ensures type safety across all gRPC clients and servers.

## Create User Service Implementation

The UserService is your business logic layer that handles user operations. This service is annotated with `@Component` to be automatically registered with Kora's dependency injection system. It provides the core functionality that your gRPC handlers will use.

### Key Design Patterns:

- **@Component Annotation**: Registers the service as a managed bean in Kora's DI container
- **Thread-Safe Storage**: Uses `ConcurrentHashMap` for safe concurrent access
- **Immutable Responses**: Protocol Buffer messages are immutable once built
- **Builder Pattern**: Uses generated builders for constructing complex messages
- **Null Safety**: Proper null checking and optional field handling

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.example.service;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.UserResponse;
    import ru.tinkoff.kora.example.UserStatus;

    import java.time.Instant;
    import java.util.Map;
    import java.util.UUID;
    import java.util.concurrent.ConcurrentHashMap;

    @Component
    public final class UserService {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();

        /**
         * Creates a new user with the given name and email.
         * Generates a unique ID and timestamp for the user.
         */
        public UserResponse createUser(String name, String email) {
            String id = UUID.randomUUID().toString();

            // Build the UserResponse using the generated builder
            UserResponse user = UserResponse.newBuilder()
                .setId(id)
                .setName(name)
                .setEmail(email)
                .setCreatedAt(com.google.protobuf.Timestamp.newBuilder()
                    .setSeconds(Instant.now().getEpochSecond())
                    .build())
                .setStatus(UserStatus.ACTIVE)
                .build();

            users.put(id, user);
            return user;
        }

        /**
         * Retrieves a user by their unique ID.
         * Returns null if the user doesn't exist.
         */
        public UserResponse getUser(String userId) {
            return users.get(userId);
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.service

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.UserResponse
    import ru.tinkoff.kora.example.UserStatus
    import java.time.Instant
    import java.util.UUID
    import java.util.concurrent.ConcurrentHashMap

    @Component
    class UserService {

        private val users = ConcurrentHashMap<String, UserResponse>()

        /**
         * Creates a new user with the given name and email.
         * Generates a unique ID and timestamp for the user.
         */
        fun createUser(name: String, email: String): UserResponse {
            val id = UUID.randomUUID().toString()

            // Build the UserResponse using the generated builder
            val user = UserResponse.newBuilder()
                .setId(id)
                .setName(name)
                .setEmail(email)
                .setCreatedAt(com.google.protobuf.Timestamp.newBuilder()
                    .setSeconds(Instant.now().epochSecond)
                    .build())
                .setStatus(UserStatus.ACTIVE)
                .build()

            users[id] = user
            return user
        }

        /**
         * Retrieves a user by their unique ID.
         * Returns null if the user doesn't exist.
         */
        fun getUser(userId: String): UserResponse? {
            return users[userId]
        }
    }
    ```

### Service Implementation Details:

#### Thread Safety
- **ConcurrentHashMap**: Provides thread-safe operations for concurrent access
- **Immutable Returns**: `List.copyOf()` and `toList()` create immutable snapshots
- **Atomic Operations**: User creation and updates are atomic operations

#### Protocol Buffer Integration
- **Generated Builders**: Uses `UserResponse.newBuilder()` for constructing messages
- **Timestamp Handling**: Converts `Instant` to protobuf `Timestamp`
- **Enum Usage**: Uses generated `UserStatus` enum values
- **Null Handling**: Properly handles optional fields in updates

#### Business Logic Separation
- **Pure Business Logic**: Contains only domain logic, no gRPC concerns
- **Testable**: Can be unit tested independently of gRPC layer
- **Reusable**: Could be used by REST APIs, GraphQL, or other interfaces

This service layer provides a clean separation between your business logic and the gRPC transport layer, making your code more maintainable and testable.

## Create gRPC Service Handler

The gRPC service handler is where your business logic meets the gRPC protocol. It extends the generated `UserServiceGrpc.UserServiceImplBase` class and implements each RPC method defined in your `.proto` file. The handler is annotated with `@Component` for automatic dependency injection.

### Key Concepts:

- **@Component Annotation**: Registers the handler with Kora's DI container
- **Unary RPC Pattern**: Simple request-response communication
- **Error Handling**: Uses gRPC Status codes for proper error propagation
- **Logging**: Comprehensive logging for debugging and monitoring
- **StreamObserver**: Handles request/response flow for unary operations

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/grpc/UserServiceGrpcHandler.java`:

    ```java
    package ru.tinkoff.kora.example.grpc;

    import io.grpc.Status;
    import io.grpc.stub.StreamObserver;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.service.UserService;
    import ru.tinkoff.kora.example.*;

    @Component
    public final class UserServiceGrpcHandler extends UserServiceGrpc.UserServiceImplBase {

        private static final Logger logger = LoggerFactory.getLogger(UserServiceGrpcHandler.class);
        private final UserService userService;

        public UserServiceGrpcHandler(UserService userService) {
            this.userService = userService;
        }

        @Override
        public void createUser(CreateUserRequest request, StreamObserver<UserResponse> responseObserver) {
            try {
                logger.info("Creating user: name={}, email={}", request.getName(), request.getEmail());

                UserResponse user = userService.createUser(request.getName(), request.getEmail());

                responseObserver.onNext(user);
                responseObserver.onCompleted();

                logger.info("User created successfully: id={}", user.getId());

            } catch (Exception e) {
                logger.error("Error creating user", e);
                responseObserver.onError(Status.INTERNAL
                    .withDescription("Failed to create user")
                    .withCause(e)
                    .asRuntimeException());
            }
        }

        @Override
        public void getUser(GetUserRequest request, StreamObserver<UserResponse> responseObserver) {
            try {
                logger.info("Getting user: id={}", request.getUserId());

                UserResponse user = userService.getUser(request.getUserId());

                if (user == null) {
                    responseObserver.onError(Status.NOT_FOUND
                        .withDescription("User not found: " + request.getUserId())
                        .asRuntimeException());
                    return;
                }

                responseObserver.onNext(user);
                responseObserver.onCompleted();

                logger.info("User retrieved successfully: id={}", user.getId());

            } catch (Exception e) {
                logger.error("Error getting user", e);
                responseObserver.onError(Status.INTERNAL
                    .withDescription("Failed to get user")
                    .withCause(e)
                    .asRuntimeException());
            }
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/grpc/UserServiceGrpcHandler.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.grpc

    import io.grpc.Status
    import io.grpc.stub.StreamObserver
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.service.UserService
    import ru.tinkoff.kora.example.*

    @Component
    class UserServiceGrpcHandler : UserServiceGrpc.UserServiceImplBase() {

        private val logger = LoggerFactory.getLogger(UserServiceGrpcHandler::class.java)
        private val userService: UserService

        constructor(userService: UserService) {
            this.userService = userService;
        }

        override fun createUser(request: CreateUserRequest, responseObserver: StreamObserver<UserResponse>) {
            try {
                logger.info("Creating user: name={}, email={}", request.name, request.email)

                val user = userService.createUser(request.name, request.email)

                responseObserver.onNext(user)
                responseObserver.onCompleted()

                logger.info("User created successfully: id={}", user.id)

            } catch (e: Exception) {
                logger.error("Error creating user", e)
                responseObserver.onError(Status.INTERNAL
                    .withDescription("Failed to create user")
                    .withCause(e)
                    .asRuntimeException())
            }
        }

        override fun getUser(request: GetUserRequest, responseObserver: StreamObserver<UserResponse>) {
            try {
                logger.info("Getting user: id={}", request.userId)

                val user = userService.getUser(request.userId)

                if (user == null) {
                    responseObserver.onError(Status.NOT_FOUND
                        .withDescription("User not found: " + request.userId)
                        .asRuntimeException())
                    return
                }

                responseObserver.onNext(user)
                responseObserver.onCompleted()

                logger.info("User retrieved successfully: id={}", user.id)

            } catch (e: Exception) {
                logger.error("Error getting user", e)
                responseObserver.onError(Status.INTERNAL
                    .withDescription("Failed to get user")
                    .withCause(e)
                    .asRuntimeException())
            }
        }
    }
    ```

### Handler Implementation Details:

#### Unary RPC Methods (`createUser`, `getUser`)
- **Simple Pattern**: Single request, single response
- **Error Handling**: Check for null results and throw appropriate gRPC status codes
- **Logging**: Track request parameters and results

This handler bridges your business logic with the gRPC protocol, maintaining clean error handling and logging for unary RPC operations.

## Create and Inject a Simple Interceptor

!!! warning "Educational Purpose Only"

    **This custom logging interceptor is provided for learning purposes only.** Kora provides comprehensive telemetry and logging capabilities out-of-the-box for gRPC servers, including:

    - **Automatic Request/Response Logging**: All gRPC calls are automatically logged with structured information
    - **Performance Metrics**: Built-in timing, throughput, and error rate monitoring
    - **Distributed Tracing**: Integrated tracing with OpenTelemetry support
    - **Health Checks**: Automatic health monitoring and metrics collection
    - **Structured Logging**: Consistent log formatting across all gRPC services

    **In production applications, you typically do not need to implement custom logging interceptors** as Kora handles all observability concerns automatically through its telemetry module.

gRPC interceptors allow you to intercept and modify gRPC calls, enabling cross-cutting concerns like logging, authentication, metrics collection, and request/response modification. In Kora, interceptors are managed components that can be easily injected and configured.

### What is a gRPC Interceptor?

An interceptor is middleware that sits between the client and server, allowing you to:
- **Log Requests/Responses**: Track all gRPC calls with detailed information
- **Add Authentication**: Validate tokens or credentials on each request
- **Collect Metrics**: Measure response times, error rates, and throughput
- **Modify Messages**: Transform requests or responses
- **Handle Errors**: Implement custom error handling logic
- **Add Headers**: Inject custom metadata into requests/responses

### Creating a Simple Logging Interceptor (Educational Example)

The `@Component` annotation registers the interceptor with Kora's dependency injection system. Kora automatically discovers and applies all `ServerInterceptor` components to the gRPC server.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/grpc/LoggingInterceptor.java`:

    ```java
    package ru.tinkoff.kora.example.grpc;

    import io.grpc.Metadata;
    import io.grpc.ServerCall;
    import io.grpc.ServerCallHandler;
    import io.grpc.ServerInterceptor;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;

    @Component
    public final class LoggingInterceptor implements ServerInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(LoggingInterceptor.class);

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                ServerCall<ReqT, RespT> call,
                Metadata headers,
                ServerCallHandler<ReqT, RespT> next) {

            // Log the incoming request
            logger.info("Incoming gRPC request: method={}, headers={}",
                call.getMethodDescriptor().getFullMethodName(),
                headers);

            // Continue with the normal call flow (no completion interception needed for this example)
            return next.startCall(call, headers);
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/grpc/LoggingInterceptor.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.grpc

    import io.grpc.Metadata
    import io.grpc.ServerCall
    import io.grpc.ServerCallHandler
    import io.grpc.ServerInterceptor
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component

    @Component
    class LoggingInterceptor : ServerInterceptor {

        private val logger = LoggerFactory.getLogger(LoggingInterceptor::class.java)

        override fun <ReqT, RespT> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {

            // Log the incoming request
            logger.info("Incoming gRPC request: method={}, headers={}",
                call.methodDescriptor.fullMethodName,
                headers)

            // Continue with the normal call flow (no completion interception needed for this example)
            return next.startCall(call, headers)
        }
    }
    ```

### How the Interceptor Works

#### Key Components:
- **`ServerInterceptor`**: Interface for intercepting server-side gRPC calls
- **`interceptCall()`**: Main interception method called for each gRPC request
- **`ServerCall`**: Represents the gRPC call
- **`ServerCallHandler`**: Provides access to the next handler in the chain

#### Simple Interception Flow:
1. **Request Arrival**: `interceptCall()` is invoked when a gRPC request arrives
2. **Logging**: Log the incoming request details (method name, headers)
3. **Delegation**: Call `next.startCall()` to continue with normal processing

## Configure gRPC Server

Configure your gRPC server in `application.conf`:

```hocon
grpcServer {
  port = 9090
  maxMessageSize = "4MiB"
  reflectionEnabled = true
  telemetry {
    logging.enabled = true
  }
}
```

### Server Configuration Options:

- **`port`**: The port number the gRPC server will listen on (default: 9090)
- **`maxMessageSize`**: Maximum size of individual messages (default: "4MiB")
- **`reflectionEnabled`**: Enables gRPC server reflection for service discovery
- **`telemetry.logging.enabled`**: Enables structured logging for gRPC calls

## gRPC Server Reflection

gRPC Server Reflection is a powerful feature that allows clients to discover and interact with gRPC services dynamically at runtime, without needing pre-compiled stubs or `.proto` files.

### What is Server Reflection?

Server Reflection provides a way for gRPC clients to:
- **Discover Available Services**: Query the server for all exposed gRPC services
- **Inspect Service Methods**: Get detailed information about RPC methods and their signatures
- **Dynamic Client Generation**: Create clients on-the-fly without code generation
- **API Exploration**: Use tools like `grpcurl` and `grpcui` for testing and debugging

### How Server Reflection Works

When `reflectionEnabled = true`, the server exposes a special reflection service that clients can query using the `grpc.reflection.v1alpha.ServerReflection` service. This service provides:

1. **Service Discovery**: Lists all available gRPC services on the server
2. **Method Inspection**: Returns method signatures, input/output types
3. **Type Information**: Provides detailed protobuf message definitions
4. **File Descriptor Sets**: Returns compiled protobuf descriptors

### Configuration

```hocon
grpcServer {
  reflectionEnabled = true  // Enable server reflection
}
```

### Usage Examples

#### Using grpcurl for Service Discovery

```bash
# List all available services
grpcurl -plaintext localhost:9090 list

# Get service methods
grpcurl -plaintext localhost:9090 list ru.tinkoff.kora.example.UserService

# Get method details
grpcurl -plaintext localhost:9090 describe ru.tinkoff.kora.example.UserService
```

#### Using grpcui for Web Interface

```bash
# Start web UI for service exploration
grpcui -plaintext localhost:9090
```

This opens a web interface at `http://localhost:1030` where you can:
- Browse all available services
- View method signatures
- Make test calls with a web form
- See request/response examples

#### Programmatic Reflection

```java
// Create a reflection client
ServerReflectionStub reflectionStub = ServerReflectionGrpc.newStub(channel);

// Query for services
reflectionStub.serverReflectionInfo(new StreamObserver<ServerReflectionResponse>() {
    @Override
    public void onNext(ServerReflectionResponse response) {
        // Process reflection response
        ListServiceResponse listResponse = response.getListServicesResponse();
        for (ServiceResponse service : listResponse.getServiceList()) {
            System.out.println("Service: " + service.getName());
        }
    }
    // ... other callbacks
});
```

### When to Use Server Reflection

**✅ Recommended For:**
- **Development & Testing**: Easy service exploration and testing
- **API Gateways**: Dynamic service discovery and routing
- **Debugging Tools**: Building gRPC debugging and monitoring tools
- **Generic Clients**: Applications that need to work with multiple services

**❌ Not Recommended For:**
- **Production APIs**: Adds overhead and security considerations
- **Performance-Critical Services**: Reflection has runtime performance cost
- **Security-Sensitive Environments**: May expose service metadata

### Security Considerations

- **Information Disclosure**: Reflection exposes service and method names
- **Production Deployment**: Consider disabling in production or protecting with authentication
- **Network Security**: Ensure reflection endpoints are not exposed to untrusted networks

### Performance Impact

- **Memory Usage**: Reflection service increases memory footprint
- **CPU Overhead**: Processing reflection requests adds computational cost
- **Startup Time**: Slightly increases server startup time

### Best Practices

1. **Environment-Specific**: Enable only in development/testing environments
2. **Authentication**: Protect reflection endpoints when enabled in production
3. **Monitoring**: Monitor reflection usage and performance impact
4. **Documentation**: Document which environments have reflection enabled

Server Reflection is an invaluable tool for development and testing, but should be used judiciously in production environments due to security and performance considerations.

## Build and Run

Generate protobuf classes and run the application:

```bash
# Generate protobuf classes
./gradlew generateProto

# Build the application
./gradlew build

# Run the application
./gradlew run
```

## Test the gRPC Service

Test your gRPC service using grpcurl or a gRPC client:

### Test Unary RPC (Create User)

```bash
grpcurl -plaintext -d '{"name": "John Doe", "email": "john@example.com"}' \
  localhost:9090 ru.tinkoff.kora.example.UserService/CreateUser
```

### Test Unary RPC (Get User)

```bash
grpcurl -plaintext -d '{"user_id": "user-id-here"}' \
  localhost:9090 ru.tinkoff.kora.example.UserService/GetUser
```

## Key Concepts Learned

### Protocol Buffers
- **`.proto` files**: Define service interfaces and message structures
- **Code generation**: Automatic generation of client and server code
- **Type safety**: Compile-time guarantees for message structures
- **Language agnostic**: Services can be consumed from any language

### gRPC Service Patterns
- **Unary RPC**: Simple request-response pattern for basic CRUD operations
- **Reliable Communication**: Synchronous pattern with guaranteed delivery
- **Performance**: Optimized for low-latency, high-throughput scenarios

### Error Handling
- **gRPC Status codes**: Standardized error codes (NOT_FOUND, INTERNAL, etc.)
- **Status descriptions**: Human-readable error messages
- **Exception handling**: Proper error propagation and logging

### Kora gRPC Integration
- **@Component annotation**: Registers service handlers with dependency injection
- **Automatic wiring**: Generated clients and servers are automatically configured
- **Telemetry integration**: Built-in metrics, tracing, and logging support

## What's Next?

- [Master Advanced gRPC Streaming](grpc-server-advanced.md)
- [Add Database Integration](../database-jdbc.md)
- [Add Observability & Monitoring](../observability.md)
- [Create gRPC Client](../grpc-client.md)
- [Add Validation](../validation.md)

## Help

If you encounter issues:

- Check the [gRPC Server Documentation](../../documentation/grpc-server.md)
- Verify protobuf compilation: `./gradlew generateProto`
- Check the [gRPC Server Example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-grpc-server)
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)</content>
<parameter name="filePath">c:\Users\Anton\IdeaProjects\kora\agents-md\kora-docs\mkdocs\docs\en\guides\grpc-server.md