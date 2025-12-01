---
title: gRPC Client with Kora
summary: Build gRPC clients to communicate with gRPC servers using protocol buffers and unary RPC methods
tags: grpc-client, protobuf, rpc, microservices
---

# gRPC Client with Kora

This guide shows you how to build gRPC clients using Kora's gRPC client module. You'll learn how to connect to gRPC servers, make unary RPC calls, handle responses, and implement robust client-side error handling for microservices communication.

## Understanding gRPC Clients

### What is a gRPC Client?

A gRPC client is an application that connects to and communicates with gRPC servers using the gRPC protocol. Clients use generated stub code to make remote procedure calls, sending requests and receiving responses in a type-safe manner.

#### Key Features of gRPC Clients:

- **Type-Safe Communication**: Generated client stubs ensure compile-time type safety
- **Multiple Languages**: Clients can be written in any language supported by gRPC
- **Efficient Transport**: Uses HTTP/2 for high-performance communication
- **Unary and Streaming**: Support for all gRPC communication patterns
- **Built-in Features**: Automatic retries, load balancing, and connection management

#### Why Use gRPC Clients?

- **Service Integration**: Connect microservices in distributed systems
- **High Performance**: Binary serialization and HTTP/2 provide excellent performance
- **Type Safety**: Compile-time guarantees prevent runtime errors
- **Code Generation**: Automatic generation of client code reduces boilerplate
- **Interoperability**: Works seamlessly across different programming languages

### Client-Server Architecture

```
┌─────────────────┐          ┌─────────────────┐
│     Client      │          │     Server      │
│                 │          │                 │
│ ┌─────────────┐ │          │ ┌─────────────┐ │
│ │  Service    │◄┼─────────►│ │   Handler   │ │
│ │  (Your      │ │   gRPC   │ │  (Server    │ │
│ │   Code)     │ │          │ │   Impl)     │ │
│ └─────────────┘ │          │ └─────────────┘ │
└─────────────────┘          └─────────────────┘
         ▲                           ▲
         │                           │
┌─────────────────┐          ┌─────────────────┐
│   Generated     │          │   Generated     │
│   Client        │          │   Server        │
│   Stubs         │          │   Stubs         │
│  (Auto-gen'd)   │          │  (Auto-gen'd)   │
└─────────────────┘          └─────────────────┘
```

This architecture enables seamless communication between client and server applications.

## What You'll Build

You'll build a UserService gRPC client that connects to the server created in the [gRPC Server guide](grpc-server.md):

- **Protocol Buffer Integration**: Use the same .proto files as the server
- **Unary RPC Calls**: Make simple request-response calls to create and retrieve users
- **Client Service Layer**: Clean abstraction layer for gRPC communication
- **Error Handling**: Proper handling of gRPC status codes and network errors
- **Configuration**: Connection management and client-side configuration

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide
- Running gRPC server from the [gRPC Server guide](grpc-server.md)
- Basic understanding of [Protocol Buffers](https://developers.google.com/protocol-buffers)

## Prerequisites

!!! note "Required: Complete gRPC Server Guide First"

    This guide assumes you have completed the **[gRPC Server guide](grpc-server.md)** and have a running gRPC server. The client will connect to the UserService server you built in that guide.

    If you haven't completed the server guide yet, please do so first as this client guide depends on having a running server to connect to.

## Add Dependencies

To build gRPC clients with Kora, you need to add several key dependencies to your project. Each dependency serves a specific purpose in the gRPC client ecosystem:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        // Kora gRPC Client Module - Core gRPC client implementation with dependency injection
        implementation("ru.tinkoff.kora:grpc-client")

        // gRPC Protobuf Support - Runtime support for Protocol Buffer serialization
        implementation("io.grpc:grpc-protobuf:1.62.2")

        // gRPC Netty Transport - High-performance transport layer for clients
        implementation("io.grpc:grpc-netty:1.62.2")

        // Java Annotations API - Required for annotation processing and runtime reflection
        implementation("javax.annotation:javax.annotation-api:1.3.2")
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        // Kora gRPC Client Module - Core gRPC client implementation with dependency injection
        implementation("ru.tinkoff.kora:grpc-client")

        // gRPC Protobuf Support - Runtime support for Protocol Buffer serialization
        implementation("io.grpc:grpc-protobuf:1.62.2")

        // gRPC Netty Transport - High-performance transport layer for clients
        implementation("io.grpc:grpc-netty:1.62.2")

        // Java Annotations API - Required for annotation processing and runtime reflection
        implementation("javax.annotation:javax.annotation-api:1.3.2")
    }
    ```

### Dependency Breakdown:

- **`ru.tinkoff.kora:grpc-client`**: The core Kora module that provides gRPC client functionality. This includes:
  - Client lifecycle management
  - Integration with Kora's dependency injection system
  - Automatic stub creation and management
  - Configuration binding
  - Telemetry integration (metrics, tracing, logging)

- **`io.grpc:grpc-protobuf:1.62.2`**: The official gRPC Java library that provides:
  - Protocol Buffer message serialization/deserialization
  - gRPC stub generation and communication
  - HTTP/2 transport layer
  - Built-in interceptors and middleware support

- **`io.grpc:grpc-netty:1.62.2`**: Netty-based transport implementation that provides:
  - High-performance HTTP/2 transport
  - Connection pooling and management
  - TLS/SSL support
  - Advanced networking features

- **`javax.annotation:javax.annotation-api:1.3.2`**: Provides standard Java annotations that are used by:
  - gRPC's annotation processing
  - Kora's component scanning
  - Runtime reflection operations

These dependencies work together to provide a complete gRPC client implementation that integrates seamlessly with Kora's application framework.

## Configure Protocol Buffers Plugin

The Protocol Buffers plugin for Gradle is essential for generating Java/Kotlin client code from your `.proto` files. This plugin automates the code generation process and integrates it into your build lifecycle.

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
- **`build/generated/source/proto/main/grpc`**: gRPC service stubs and client classes

This configuration ensures that your `.proto` files are automatically compiled whenever you build your project, and the generated code is properly integrated into your source tree.

## Add Modules

Update your Application interface to include the GrpcClientModule:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.grpc.client.GrpcClientModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            GrpcClientModule,
            LogbackModule {
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.grpc.client.GrpcClientModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        GrpcClientModule,
        LogbackModule
    ```

## Define Protocol Buffers

Protocol Buffers are the core of gRPC communication - they define your service interfaces, message structures, and data types. For the client, you'll use the same `.proto` file that defines the server interface.

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

!!! note "Shared Protocol Buffers"

    Since you're building a client to connect to the server from the [gRPC Server guide](grpc-server.md), you'll use the same `user_service.proto` file that defines the server interface. This ensures type-safe communication between client and server.

===! ":fontawesome-brands-java: `Java`"

    Copy `src/main/proto/user_service.proto` from your server project:

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

    Copy `src/main/proto/user_service.proto` from your server project:

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
- **`UserServiceGrpc.UserServiceBlockingStub`**: Synchronous client for unary calls
- **`UserServiceGrpc.UserServiceStub`**: Asynchronous client for streaming calls
- **`UserServiceGrpc.UserServiceFutureStub`**: Future-based client for unary calls

### Best Practices for Protocol Buffers:

1. **Field Numbers**: Never change field numbers once assigned (breaks compatibility)
2. **Package Naming**: Use reverse domain notation (e.g., `com.example.service`)
3. **Message Naming**: Use PascalCase for message names
4. **Field Naming**: Use snake_case for field names (converts to camelCase in generated code)
5. **Versioning**: Use package names or service names for versioning, not field changes
6. **Documentation**: Add comments to services and messages for API documentation

This `.proto` file serves as your API contract and ensures type-safe communication between client and server.

## Configure gRPC Client

Configure your gRPC client connection in `application.conf`:

```hocon
grpcClient {
  userService {
    host = "localhost"
    port = 9090
    maxMessageSize = "4MiB"
    enableRetry = true
    telemetry {
      logging.enabled = true
    }
  }
}
```

### Client Configuration Options:

- **`host`**: The hostname or IP address of the gRPC server
- **`port`**: The port number the gRPC server is listening on
- **`maxMessageSize`**: Maximum size of individual messages (default: "4MiB")
- **`enableRetry`**: Enables automatic retry logic for failed requests
- **`telemetry.logging.enabled`**: Enables structured logging for gRPC calls

## Create User Client Service

The UserClientService is your client-side service layer that handles communication with the gRPC server. This service is annotated with `@Component` to be automatically registered with Kora's dependency injection system. It provides a clean abstraction over the raw gRPC calls.

### Key Design Patterns:

- **@Component Annotation**: Registers the service as a managed bean in Kora's DI container
- **Blocking Stub Usage**: Uses synchronous client stubs for unary RPC calls
- **Exception Handling**: Proper handling of gRPC status codes and network errors
- **Resource Management**: Automatic connection management through Kora
- **Builder Pattern**: Uses generated builders for constructing complex messages

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/client/UserClientService.java`:

    ```java
    package ru.tinkoff.kora.example.client;

    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.*;
    import ru.tinkoff.kora.grpc.client.GrpcClient;

    @Component
    public final class UserClientService {

        private static final Logger logger = LoggerFactory.getLogger(UserClientService.class);
        private final UserServiceGrpc.UserServiceBlockingStub userServiceStub;

        public UserClientService(@GrpcClient("userService") UserServiceGrpc.UserServiceBlockingStub userServiceStub) {
            this.userServiceStub = userServiceStub;
        }

        /**
         * Creates a new user by calling the gRPC server.
         * Returns the created user information.
         */
        public UserResponse createUser(String name, String email) {
            logger.info("Creating user via gRPC: name={}, email={}", name, email);

            // Build the request message
            CreateUserRequest request = CreateUserRequest.newBuilder()
                .setName(name)
                .setEmail(email)
                .build();

            try {
                // Make the gRPC call
                UserResponse response = userServiceStub.createUser(request);
                logger.info("User created successfully: id={}", response.getId());
                return response;

            } catch (Exception e) {
                logger.error("Failed to create user via gRPC", e);
                throw new RuntimeException("Failed to create user", e);
            }
        }

        /**
         * Retrieves a user by ID by calling the gRPC server.
         * Returns the user information or null if not found.
         */
        public UserResponse getUser(String userId) {
            logger.info("Getting user via gRPC: id={}", userId);

            // Build the request message
            GetUserRequest request = GetUserRequest.newBuilder()
                .setUserId(userId)
                .build();

            try {
                // Make the gRPC call
                UserResponse response = userServiceStub.getUser(request);
                logger.info("User retrieved successfully: id={}", response.getId());
                return response;

            } catch (io.grpc.StatusRuntimeException e) {
                if (e.getStatus().getCode() == io.grpc.Status.Code.NOT_FOUND) {
                    logger.info("User not found: id={}", userId);
                    return null;
                }
                logger.error("Failed to get user via gRPC", e);
                throw new RuntimeException("Failed to get user", e);
            } catch (Exception e) {
                logger.error("Failed to get user via gRPC", e);
                throw new RuntimeException("Failed to get user", e);
            }
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/client/UserClientService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.client

    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.*
    import ru.tinkoff.kora.grpc.client.GrpcClient

    @Component
    class UserClientService(
        @GrpcClient("userService")
        private val userServiceStub: UserServiceGrpc.UserServiceBlockingStub
    ) {

        private val logger = LoggerFactory.getLogger(UserClientService::class.java)

        /**
         * Creates a new user by calling the gRPC server.
         * Returns the created user information.
         */
        fun createUser(name: String, email: String): UserResponse {
            logger.info("Creating user via gRPC: name={}, email={}", name, email)

            // Build the request message
            val request = CreateUserRequest.newBuilder()
                .setName(name)
                .setEmail(email)
                .build()

            try {
                // Make the gRPC call
                val response = userServiceStub.createUser(request)
                logger.info("User created successfully: id={}", response.id)
                return response

            } catch (e: Exception) {
                logger.error("Failed to create user via gRPC", e)
                throw RuntimeException("Failed to create user", e)
            }
        }

        /**
         * Retrieves a user by ID by calling the gRPC server.
         * Returns the user information or null if not found.
         */
        fun getUser(userId: String): UserResponse? {
            logger.info("Getting user via gRPC: id={}", userId)

            // Build the request message
            val request = GetUserRequest.newBuilder()
                .setUserId(userId)
                .build()

            try {
                // Make the gRPC call
                val response = userServiceStub.getUser(request)
                logger.info("User retrieved successfully: id={}", response.id)
                return response

            } catch (e: io.grpc.StatusRuntimeException) {
                if (e.status.code == io.grpc.Status.Code.NOT_FOUND) {
                    logger.info("User not found: id={}", userId)
                    return null
                }
                logger.error("Failed to get user via gRPC", e)
                throw RuntimeException("Failed to get user", e)
            } catch (e: Exception) {
                logger.error("Failed to get user via gRPC", e)
                throw RuntimeException("Failed to get user", e)
            }
        }
    }
    ```

### Service Implementation Details:

#### @GrpcClient Annotation
- **`@GrpcClient("userService")`**: Injects a configured gRPC client stub
- **Configuration Reference**: Refers to the `grpcClient.userService` configuration block
- **Type Safety**: Ensures the correct stub type is injected

#### Blocking Stub Usage
- **`UserServiceBlockingStub`**: Synchronous client for unary RPC calls
- **Simple API**: Direct method calls that block until response
- **Exception Handling**: Throws `StatusRuntimeException` for gRPC errors

#### Error Handling
- **StatusRuntimeException**: Specific exception type for gRPC status codes
- **NOT_FOUND Handling**: Graceful handling of missing resources
- **Generic Exceptions**: Catch-all for network and other errors

#### Protocol Buffer Integration
- **Generated Builders**: Uses `CreateUserRequest.newBuilder()` for requests
- **Type Safety**: Compile-time guarantees for message structures
- **Null Safety**: Proper handling of optional fields

This client service provides a clean, testable abstraction over the raw gRPC communication, making it easy to integrate gRPC calls into your application logic.

## Create Client Application

Create a simple application that demonstrates using the UserClientService to interact with the gRPC server:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/client/UserClientApplication.java`:

    ```java
    package ru.tinkoff.kora.example.client;

    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Root;
    import ru.tinkoff.kora.example.UserResponse;

    @Root
    public final class UserClientApplication {

        private static final Logger logger = LoggerFactory.getLogger(UserClientApplication.class);
        private final UserClientService userClientService;

        public UserClientApplication(UserClientService userClientService) {
            this.userClientService = userClientService;
        }

        /**
         * Demonstrates gRPC client operations.
         * This method can be called to test the client functionality.
         */
        public void runClientDemo() {
            logger.info("Starting gRPC client demo...");

            try {
                // Create a new user
                logger.info("Creating a new user...");
                UserResponse createdUser = userClientService.createUser("John Doe", "john.doe@example.com");
                logger.info("Created user: {} (ID: {})", createdUser.getName(), createdUser.getId());

                // Retrieve the user
                logger.info("Retrieving the user...");
                UserResponse retrievedUser = userClientService.getUser(createdUser.getId());
                if (retrievedUser != null) {
                    logger.info("Retrieved user: {} (ID: {})", retrievedUser.getName(), retrievedUser.getId());
                } else {
                    logger.warn("User not found!");
                }

                // Try to get a non-existent user
                logger.info("Trying to retrieve non-existent user...");
                UserResponse notFoundUser = userClientService.getUser("non-existent-id");
                if (notFoundUser == null) {
                    logger.info("Correctly returned null for non-existent user");
                }

                logger.info("gRPC client demo completed successfully!");

            } catch (Exception e) {
                logger.error("Error during client demo", e);
            }
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/client/UserClientApplication.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.client

    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Root
    import ru.tinkoff.kora.example.UserResponse

    @Root
    class UserClientApplication(
        private val userClientService: UserClientService
    ) {

        private val logger = LoggerFactory.getLogger(UserClientApplication::class.java)

        /**
         * Demonstrates gRPC client operations.
         * This method can be called to test the client functionality.
         */
        fun runClientDemo() {
            logger.info("Starting gRPC client demo...")

            try {
                // Create a new user
                logger.info("Creating a new user...")
                val createdUser = userClientService.createUser("John Doe", "john.doe@example.com")
                logger.info("Created user: {} (ID: {})", createdUser.name, createdUser.id)

                // Retrieve the user
                logger.info("Retrieving the user...")
                val retrievedUser = userClientService.getUser(createdUser.id)
                if (retrievedUser != null) {
                    logger.info("Retrieved user: {} (ID: {})", retrievedUser.name, retrievedUser.id)
                } else {
                    logger.warn("User not found!")
                }

                // Try to get a non-existent user
                logger.info("Trying to retrieve non-existent user...")
                val notFoundUser = userClientService.getUser("non-existent-id")
                if (notFoundUser == null) {
                    logger.info("Correctly returned null for non-existent user")
                }

                logger.info("gRPC client demo completed successfully!")

            } catch (e: Exception) {
                logger.error("Error during client demo", e)
            }
        }
    }
    ```

## Build and Run

Generate protobuf classes and run the client application:

```bash
# Generate protobuf classes
./gradlew generateProto

# Build the client application
./gradlew build

# Run the client application
./gradlew run
```

## Test the gRPC Client

Test your gRPC client by ensuring the server is running and then running the client demo:

### Prerequisites for Testing

1. **Start the gRPC Server**: Make sure the server from the [gRPC Server guide](grpc-server.md) is running on `localhost:9090`
2. **Verify Server Health**: Test that the server is responding using grpcurl:

```bash
# Test server connectivity
grpcurl -plaintext localhost:9090 ru.tinkoff.kora.example.UserService/CreateUser \
  -d '{"name": "Test User", "email": "test@example.com"}'
```

### Run Client Demo

Once the server is running, you can run the client demo:

```bash
# Run the client application
./gradlew run
```

The client will:
1. Create a new user via gRPC
2. Retrieve the created user
3. Attempt to retrieve a non-existent user (should return null)

### Expected Output

```
INFO  UserClientApplication - Starting gRPC client demo...
INFO  UserClientApplication - Creating a new user...
INFO  UserClientService - Creating user via gRPC: name=John Doe, email=john.doe@example.com
INFO  UserClientService - User created successfully: id=550e8400-e29b-41d4-a716-446655440000
INFO  UserClientApplication - Created user: John Doe (ID: 550e8400-e29b-41d4-a716-446655440000)
INFO  UserClientApplication - Retrieving the user...
INFO  UserClientService - Getting user via gRPC: id=550e8400-e29b-41d4-a716-446655440000
INFO  UserClientService - User retrieved successfully: id=550e8400-e29b-41d4-a716-446655440000
INFO  UserClientApplication - Retrieved user: John Doe (ID: 550e8400-e29b-41d4-a716-446655440000)
INFO  UserClientApplication - Trying to retrieve non-existent user...
INFO  UserClientService - User not found: id=non-existent-id
INFO  UserClientApplication - Correctly returned null for non-existent user
INFO  UserClientApplication - gRPC client demo completed successfully!
```

## Key Concepts Learned

### gRPC Client Architecture
- **Client Stubs**: Generated code for type-safe RPC communication
- **Blocking vs Async**: Different stub types for various use cases
- **Connection Management**: Automatic connection pooling and lifecycle management

### Protocol Buffers in Clients
- **Shared Schema**: Same .proto files used by both client and server
- **Type Safety**: Compile-time guarantees across service boundaries
- **Version Compatibility**: Forward and backward compatibility support

### Error Handling
- **Status Codes**: gRPC status codes for different error conditions
- **Network Errors**: Handling connection failures and timeouts
- **Business Logic Errors**: Translating gRPC errors to application exceptions

### Configuration
- **Client Configuration**: Connection parameters and behavior settings
- **Service Discovery**: How clients locate and connect to servers
- **Load Balancing**: Distributing requests across multiple server instances

## What's Next?

- [Advanced gRPC Client Patterns](grpc-client-advanced.md)
- [gRPC Streaming Clients](grpc-client-streaming.md)
- [Service Discovery and Load Balancing](service-discovery.md)
- [Circuit Breaker Pattern](resilience.md)
- [Distributed Tracing](observability-tracing.md)

## Help

If you encounter issues:

- Check the [gRPC Client Documentation](../../documentation/grpc-client.md)
- Verify the server from [gRPC Server guide](grpc-server.md) is running
- Check client configuration in `application.conf`
- Test server connectivity with grpcurl
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)