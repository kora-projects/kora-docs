---
title: Advanced gRPC Server with Kora
summary: Master advanced gRPC concepts including streaming patterns, interceptors, and production-ready implementations
tags: grpc-server, protobuf, streaming, rpc, microservices, advanced
---

# Advanced gRPC Server with Kora

This advanced guide builds upon the [basic gRPC Server guide](grpc-server.md) to explore sophisticated gRPC concepts including streaming patterns, custom interceptors, and production-ready implementations. You'll learn how to implement server streaming, client streaming, and bidirectional streaming for complex real-world scenarios.

## What You'll Build

You'll build an advanced UserService gRPC server that demonstrates all streaming patterns:

- **Server Streaming**: Stream all users to clients for real-time dashboards
- **Client Streaming**: Accept multiple user creation requests in batches
- **Bidirectional Streaming**: Real-time user updates with live synchronization
- **Advanced Interceptors**: Custom middleware for metrics, authentication, and rate limiting
- **Production Features**: Flow control, backpressure handling, and error recovery
- **Comprehensive Testing**: Unit tests and integration tests for streaming scenarios

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide
- Completed [basic gRPC Server guide](grpc-server.md)
- Basic understanding of [Protocol Buffers](https://developers.google.com/protocol-buffers)
- Familiarity with streaming concepts and reactive programming

## Prerequisites

!!! note "Required: Complete Basic gRPC Guide First"

    This advanced guide assumes you have completed the **[basic gRPC Server guide](grpc-server.md)** and have a working unary RPC implementation. You should understand:

    - Basic gRPC concepts and Protocol Buffers
    - Unary RPC patterns (CreateUser, GetUser)
    - Kora's dependency injection system
    - Basic gRPC server configuration and interceptors
    - Protocol buffer compilation and code generation

    If you haven't completed the basic guide yet, please do so first as this guide builds upon those foundational concepts.

## Understanding Streaming Patterns

While unary RPC provides simple request-response communication, streaming patterns enable more sophisticated data exchange scenarios essential for modern microservices.

### Server Streaming

**Server streaming** allows a client to send a single request and receive multiple responses from the server. This pattern is ideal for:

- **Real-time data feeds**: Stock prices, sensor readings, log monitoring
- **Large dataset pagination**: Breaking down large responses into manageable chunks
- **Progressive results**: Search results, computation progress, file downloads

**Protocol Buffer Syntax**:
```protobuf
rpc GetAllUsers(google.protobuf.Empty) returns (stream UserResponse);
```

**Use Cases**:
- Streaming user lists for admin dashboards
- Real-time notification feeds
- Progressive search results
- Log streaming for debugging

### Client Streaming

**Client streaming** enables clients to send multiple requests to a server, which processes them and returns a single response. This pattern excels at:

- **Batch operations**: Bulk data uploads, batch processing
- **Real-time aggregation**: Collecting metrics, sensor data
- **Complex workflows**: Multi-step operations with intermediate feedback

**Protocol Buffer Syntax**:
```protobuf
rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);
```

**Use Cases**:
- Bulk user creation
- File uploads in chunks
- Real-time data ingestion
- Batch processing workflows

### Bidirectional Streaming

**Bidirectional streaming** provides full-duplex communication where both client and server can send multiple messages independently. This advanced pattern supports:

- **Real-time collaboration**: Chat applications, collaborative editing
- **Complex workflows**: Interactive data processing, negotiation protocols
- **Event-driven systems**: Real-time event processing and responses

**Protocol Buffer Syntax**:
```protobuf
rpc UpdateUsers(stream UserUpdate) returns (stream UserResponse);
```

**Use Cases**:
- Real-time collaborative editing
- Interactive data analysis
- Live chat systems
- Real-time gaming

## Step 1: Adding Server Streaming (GetAllUsers)

Server streaming allows a client to send a single request and receive multiple responses from the server. This pattern is ideal for scenarios where you need to return a collection of data that might be large or where you want to stream results progressively.

### Understanding Server Streaming

In server streaming:
- **Client sends**: One request message
- **Server responds**: Multiple response messages
- **Use cases**: Real-time data feeds, large dataset pagination, progressive results

**Protocol Buffer Syntax**:
```protobuf
rpc GetAllUsers(google.protobuf.Empty) returns (stream UserResponse);
```

### Update Protocol Buffers

First, let's add the server streaming method to our proto file:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/proto/user_service.proto`:

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
      // ...existing code...

      // Server streaming: Stream all users to client
      rpc GetAllUsers(google.protobuf.Empty) returns (stream UserResponse) {}
    }

    // Message definitions - data structures for requests and responses

    // ...existing code...
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/proto/user_service.proto`:

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
      // ...existing code...

      // Server streaming: Stream all users to client
      rpc GetAllUsers(google.protobuf.Empty) returns (stream UserResponse) {}
    }

    // Message definitions - data structures for requests and responses

    // ...existing code...
    ```

### Update User Service

Add a method to retrieve all users for streaming:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.example.service;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.UserResponse;
    import ru.tinkoff.kora.example.UserStatus;

    import java.time.Instant;
    import java.util.List;
    import java.util.Map;
    import java.util.UUID;
    import java.util.concurrent.ConcurrentHashMap;

    @Component
    public final class UserService {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();

        // ...existing code...

        public List<UserResponse> getAllUsers() {
            return List.copyOf(users.values());
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/service/UserService.kt`:

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

        // ...existing code...

        fun getAllUsers(): List<UserResponse> {
            return users.values.toList()
        }
    }
    ```

### Update gRPC Handler

Add the server streaming implementation to the handler:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/grpc/UserServiceGrpcHandler.java`:

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

        // ...existing code...

        @Override
        public void getAllUsers(com.google.protobuf.Empty request, StreamObserver<UserResponse> responseObserver) {
            try {
                logger.info("Streaming all users");

                List<UserResponse> users = userService.getAllUsers();

                for (UserResponse user : users) {
                    // Check if client is still connected
                    if (responseObserver instanceof io.grpc.stub.ServerCallStreamObserver) {
                        io.grpc.stub.ServerCallStreamObserver<UserResponse> serverObserver =
                            (io.grpc.stub.ServerCallStreamObserver<UserResponse>) responseObserver;

                        // Check for client cancellation
                        if (serverObserver.isCancelled()) {
                            logger.info("Client cancelled streaming request");
                            return;
                        }
                    }

                    responseObserver.onNext(user);

                    // Simulate processing time and allow for backpressure
                    try {
                        Thread.sleep(50); // Reduced for demonstration
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        logger.warn("Streaming interrupted");
                        break;
                    }
                }

                responseObserver.onCompleted();
                logger.info("Streamed {} users successfully", users.size());

            } catch (Exception e) {
                logger.error("Error streaming users", e);
                responseObserver.onError(Status.INTERNAL
                    .withDescription("Failed to stream users")
                    .withCause(e)
                    .asRuntimeException());
            }
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/grpc/UserServiceGrpcHandler.kt`:

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

        // ...existing code...

        override fun getAllUsers(request: com.google.protobuf.Empty, responseObserver: StreamObserver<UserResponse>) {
            try {
                logger.info("Streaming all users")

                val users = userService.getAllUsers()

                for (user in users) {
                    // Check if client is still connected
                    if (responseObserver is io.grpc.stub.ServerCallStreamObserver<*>) {
                        val serverObserver = responseObserver as io.grpc.stub.ServerCallStreamObserver<UserResponse>

                        // Check for client cancellation
                        if (serverObserver.isCancelled) {
                            logger.info("Client cancelled streaming request")
                            return
                        }
                    }

                    responseObserver.onNext(user)

                    // Simulate processing time and allow for backpressure
                    try {
                        Thread.sleep(50) // Reduced for demonstration
                    } catch (e: InterruptedException) {
                        Thread.currentThread().interrupt()
                        logger.warn("Streaming interrupted")
                        break
                    }
                }

                responseObserver.onCompleted()
                logger.info("Streamed {} users successfully", users.size)

            } catch (e: Exception) {
                logger.error("Error streaming users", e)
                responseObserver.onError(Status.INTERNAL
                    .withDescription("Failed to stream users")
                    .withCause(e)
                    .asRuntimeException())
            }
        }
    }
    ```

### Test Server Streaming

Test the server streaming implementation:

```bash
# Generate updated protobuf classes
./gradlew generateProto

# Build and run
./gradlew build
./gradlew run
```

Test with grpcurl:

```bash
# Create some test users first
grpcurl -plaintext -d '{"name": "Alice", "email": "alice@example.com"}' \
  localhost:9090 ru.tinkoff.kora.example.UserService/CreateUser

grpcurl -plaintext -d '{"name": "Bob", "email": "bob@example.com"}' \
  localhost:9090 ru.tinkoff.kora.example.UserService/CreateUser

# Test server streaming
grpcurl -plaintext localhost:9090 ru.tinkoff.kora.example.UserService/GetAllUsers
```

## Step 2: Adding Client Streaming (CreateUsers)

Client streaming allows a client to send multiple requests to the server and receive a single response. This pattern is ideal for batch operations where you need to process multiple items and return a summary.

### Understanding Client Streaming

In client streaming:
- **Client sends**: Multiple request messages
- **Server responds**: One response message
- **Use cases**: Batch operations, file uploads, bulk data processing

**Protocol Buffer Syntax**:
```protobuf
rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);
```

### Update Protocol Buffers

Add the client streaming method and response message:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/proto/user_service.proto`:

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
      // ...existing code...

      // Client streaming: Accept multiple user creation requests
      rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse) {}
    }

    // Message definitions - data structures for requests and responses

    // ...existing code...

    // Response message for batch user creation
    message CreateUsersResponse {
      int32 created_count = 1;     // Number of users created
      repeated string user_ids = 2; // Array of created user IDs
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/proto/user_service.proto`:

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
      // ...existing code...

      // Client streaming: Accept multiple user creation requests
      rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse) {}
    }

    // Message definitions - data structures for requests and responses

    // ...existing code...

    // Response message for batch user creation
    message CreateUsersResponse {
      int32 created_count = 1;     // Number of users created
      repeated string user_ids = 2; // Array of created user IDs
    }
    ```

### Update User Service

Add a method to create multiple users in batch:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.example.service;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.UserResponse;
    import ru.tinkoff.kora.example.UserStatus;

    import java.time.Instant;
    import java.util.List;
    import java.util.Map;
    import java.util.UUID;
    import java.util.concurrent.ConcurrentHashMap;

    @Component
    public final class UserService {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();

        // ...existing code...

        /**
         * Creates multiple users in batch.
         * Returns a list of created user IDs.
         */
        public List<String> createUsers(List<CreateUserData> userDataList) {
            return userDataList.stream()
                .map(data -> {
                    UserResponse user = createUser(data.name(), data.email());
                    return user.getId();
                })
                .toList();
        }

        /**
         * Record for batch user creation data.
         */
        public record CreateUserData(String name, String email) {}
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/service/UserService.kt`:

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

        // ...existing code...

        /**
         * Creates multiple users in batch.
         * Returns a list of created user IDs.
         */
        fun createUsers(userDataList: List<CreateUserData>): List<String> {
            return userDataList.map { data ->
                val user = createUser(data.name, data.email)
                user.id
            }
        }

        /**
         * Data class for batch user creation.
         */
        data class CreateUserData(val name: String, val email: String)
    }
    ```

### Update gRPC Handler

Add the client streaming implementation to the handler:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/grpc/UserServiceGrpcHandler.java`:

    ```java
    package ru.tinkoff.kora.example.grpc;

    import io.grpc.Status;
    import io.grpc.stub.StreamObserver;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.service.UserService;
    import ru.tinkoff.kora.example.*;

    import java.util.ArrayList;
    import java.util.List;

    @Component
    public final class UserServiceGrpcHandler extends UserServiceGrpc.UserServiceImplBase {

        private static final Logger logger = LoggerFactory.getLogger(UserServiceGrpcHandler.class);
        private final UserService userService;

        public UserServiceGrpcHandler(UserService userService) {
            this.userService = userService;
        }

        // ...existing code...

        @Override
        public StreamObserver<CreateUserRequest> createUsers(StreamObserver<CreateUsersResponse> responseObserver) {
            return new StreamObserver<CreateUserRequest>() {
                private final List<UserService.CreateUserData> userDataList = new ArrayList<>();

                @Override
                public void onNext(CreateUserRequest request) {
                    logger.info("Received user creation request: name={}, email={}",
                        request.getName(), request.getEmail());

                    // Collect user data for batch processing
                    userDataList.add(new UserService.CreateUserData(
                        request.getName(),
                        request.getEmail()
                    ));
                }

                @Override
                public void onError(Throwable throwable) {
                    logger.error("Error in client streaming", throwable);
                    responseObserver.onError(Status.INTERNAL
                        .withDescription("Failed to process user creation stream")
                        .withCause(throwable)
                        .asRuntimeException());
                }

                @Override
                public void onCompleted() {
                    try {
                        logger.info("Processing batch creation of {} users", userDataList.size());

                        // Process all collected user data
                        List<String> createdUserIds = userService.createUsers(userDataList);

                        // Build response
                        CreateUsersResponse response = CreateUsersResponse.newBuilder()
                            .setCreatedCount(createdUserIds.size())
                            .addAllUserIds(createdUserIds)
                            .build();

                        responseObserver.onNext(response);
                        responseObserver.onCompleted();

                        logger.info("Successfully created {} users in batch", createdUserIds.size());

                    } catch (Exception e) {
                        logger.error("Error processing batch user creation", e);
                        responseObserver.onError(Status.INTERNAL
                            .withDescription("Failed to create users in batch")
                            .withCause(e)
                            .asRuntimeException());
                    }
                }
            };
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/grpc/UserServiceGrpcHandler.kt`:

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

        // ...existing code...

        override fun createUsers(responseObserver: StreamObserver<CreateUsersResponse>): StreamObserver<CreateUserRequest> {
            return object : StreamObserver<CreateUserRequest> {
                private val userDataList = mutableListOf<UserService.CreateUserData>()

                override fun onNext(request: CreateUserRequest) {
                    logger.info("Received user creation request: name={}, email={}",
                        request.name, request.email)

                    // Collect user data for batch processing
                    userDataList.add(UserService.CreateUserData(
                        request.name,
                        request.email
                    ))
                }

                override fun onError(throwable: Throwable) {
                    logger.error("Error in client streaming", throwable)
                    responseObserver.onError(Status.INTERNAL
                        .withDescription("Failed to process user creation stream")
                        .withCause(throwable)
                        .asRuntimeException())
                }

                override fun onCompleted() {
                    try {
                        logger.info("Processing batch creation of {} users", userDataList.size)

                        // Process all collected user data
                        val createdUserIds = userService.createUsers(userDataList)

                        // Build response
                        val response = CreateUsersResponse.newBuilder()
                            .setCreatedCount(createdUserIds.size)
                            .addAllUserIds(createdUserIds)
                            .build()

                        responseObserver.onNext(response)
                        responseObserver.onCompleted()

                        logger.info("Successfully created {} users in batch", createdUserIds.size)

                    } catch (e: Exception) {
                        logger.error("Error processing batch user creation", e)
                        responseObserver.onError(Status.INTERNAL
                            .withDescription("Failed to create users in batch")
                            .withCause(e)
                            .asRuntimeException())
                    }
                }
            }
        }
    }
    ```

### Test Client Streaming

Test the client streaming implementation:

```bash
# Generate updated protobuf classes
./gradlew generateProto

# Build and run
./gradlew build
./gradlew run
```

Test with grpcurl (send multiple requests):

```bash
# Test client streaming with multiple user creation requests
grpcurl -plaintext -d '{"name": "Charlie", "email": "charlie@example.com"}' \
  -d '{"name": "Diana", "email": "diana@example.com"}' \
  -d '{"name": "Eve", "email": "eve@example.com"}' \
  localhost:9090 ru.tinkoff.kora.example.UserService/CreateUsers
```

## Step 3: Adding Bidirectional Streaming (UpdateUsers)

Bidirectional streaming allows both client and server to send multiple messages asynchronously. This pattern is ideal for real-time communication scenarios where both sides need to exchange data continuously.

### Understanding Bidirectional Streaming

In bidirectional streaming:
- **Client sends**: Multiple request messages
- **Server sends**: Multiple response messages
- **Use cases**: Real-time chat, live updates, collaborative editing

**Protocol Buffer Syntax**:
```protobuf
rpc UpdateUsers(stream UserUpdate) returns (stream UserResponse);
```

### Update Protocol Buffers

Add the bidirectional streaming method and update message:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/proto/user_service.proto`:

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
      // ...existing code...

      // Bidirectional streaming: Real-time user updates
      rpc UpdateUsers(stream UserUpdate) returns (stream UserResponse) {}
    }

    // Message definitions - data structures for requests and responses

    // ...existing code...

    // Message for user update operations
    message UserUpdate {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/proto/user_service.proto`:

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
      // ...existing code...

      // Bidirectional streaming: Real-time user updates
      rpc UpdateUsers(stream UserUpdate) returns (stream UserResponse) {}
    }

    // Message definitions - data structures for requests and responses

    // ...existing code...

    // Message for user update operations
    message UserUpdate {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }
    ```

### Update User Service

Add a method to update user information:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.example.service;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.UserResponse;
    import ru.tinkoff.kora.example.UserStatus;

    import java.time.Instant;
    import java.util.List;
    import java.util.Map;
    import java.util.UUID;
    import java.util.concurrent.ConcurrentHashMap;

    @Component
    public final class UserService {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();

        // ...existing code...

        /**
         * Updates a user's information.
         * Returns the updated user or null if user doesn't exist.
         */
        public UserResponse updateUser(String userId, String name, String email) {
            UserResponse existingUser = users.get(userId);
            if (existingUser == null) {
                return null;
            }

            UserResponse updatedUser = existingUser.toBuilder()
                .setName(name)
                .setEmail(email)
                .build();

            users.put(userId, updatedUser);
            return updatedUser;
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/service/UserService.kt`:

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

        // ...existing code...

        /**
         * Updates a user's information.
         * Returns the updated user or null if user doesn't exist.
         */
        fun updateUser(userId: String, name: String, email: String): UserResponse? {
            val existingUser = users[userId] ?: return null

            val updatedUser = existingUser.toBuilder()
                .setName(name)
                .setEmail(email)
                .build()

            users[userId] = updatedUser
            return updatedUser
        }
    }
    ```

### Update gRPC Handler

Add the bidirectional streaming implementation to the handler:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/grpc/UserServiceGrpcHandler.java`:

    ```java
    package ru.tinkoff.kora.example.grpc;

    import io.grpc.Status;
    import io.grpc.stub.StreamObserver;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.service.UserService;
    import ru.tinkoff.kora.example.*;

    import java.util.ArrayList;
    import java.util.List;
    import java.util.concurrent.ExecutorService;
    import java.util.concurrent.Executors;

    @Component
    public final class UserServiceGrpcHandler extends UserServiceGrpc.UserServiceImplBase {

        private static final Logger logger = LoggerFactory.getLogger(UserServiceGrpcHandler.class);
        private final UserService userService;
        private final ExecutorService executor = Executors.newCachedThreadPool();

        public UserServiceGrpcHandler(UserService userService) {
            this.userService = userService;
        }

        // ...existing code...

        @Override
        public StreamObserver<UserUpdate> updateUsers(StreamObserver<UserResponse> responseObserver) {
            return new StreamObserver<UserUpdate>() {
                @Override
                public void onNext(UserUpdate update) {
                    executor.submit(() -> {
                        try {
                            logger.info("Processing user update: id={}, name={}, email={}",
                                update.getUserId(), update.getName(), update.getEmail());

                            UserResponse updatedUser = userService.updateUser(
                                update.getUserId(),
                                update.getName(),
                                update.getEmail()
                            );

                            if (updatedUser == null) {
                                logger.warn("User not found for update: {}", update.getUserId());
                                // For bidirectional streaming, we can choose to send an error or skip
                                // Here we skip silently, but you could send an error response
                                return;
                            }

                            // Send the updated user back to client
                            responseObserver.onNext(updatedUser);
                            logger.info("User updated successfully: id={}", updatedUser.getId());

                        } catch (Exception e) {
                            logger.error("Error updating user", e);
                            // In bidirectional streaming, errors can be sent back
                            responseObserver.onError(Status.INTERNAL
                                .withDescription("Failed to update user")
                                .withCause(e)
                                .asRuntimeException());
                        }
                    });
                }

                @Override
                public void onError(Throwable throwable) {
                    logger.error("Error in bidirectional streaming", throwable);
                    responseObserver.onError(Status.INTERNAL
                        .withDescription("Failed to process user update stream")
                        .withCause(throwable)
                        .asRuntimeException());
                }

                @Override
                public void onCompleted() {
                    logger.info("Bidirectional streaming completed");
                    responseObserver.onCompleted();
                }
            };
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/grpc/UserServiceGrpcHandler.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.grpc

    import io.grpc.Status
    import io.grpc.stub.StreamObserver
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.service.UserService
    import ru.tinkoff.kora.example.*
    import java.util.concurrent.Executors

    @Component
    class UserServiceGrpcHandler : UserServiceGrpc.UserServiceImplBase() {

        private val logger = LoggerFactory.getLogger(UserServiceGrpcHandler::class.java)
        private val userService: UserService
        private val executor = Executors.newCachedThreadPool()

        constructor(userService: UserService) {
            this.userService = userService;
        }

        // ...existing code...

        override fun updateUsers(responseObserver: StreamObserver<UserResponse>): StreamObserver<UserUpdate> {
            return object : StreamObserver<UserUpdate> {
                override fun onNext(update: UserUpdate) {
                    executor.submit {
                        try {
                            logger.info("Processing user update: id={}, name={}, email={}",
                                update.userId, update.name, update.email)

                            val updatedUser = userService.updateUser(
                                update.userId,
                                update.name,
                                update.email
                            )

                            if (updatedUser == null) {
                                logger.warn("User not found for update: {}", update.userId)
                                // For bidirectional streaming, we can choose to send an error or skip
                                // Here we skip silently, but you could send an error response
                                return@submit
                            }

                            // Send the updated user back to client
                            responseObserver.onNext(updatedUser)
                            logger.info("User updated successfully: id={}", updatedUser.id)

                        } catch (e: Exception) {
                            logger.error("Error updating user", e)
                            // In bidirectional streaming, errors can be sent back
                            responseObserver.onError(Status.INTERNAL
                                .withDescription("Failed to update user")
                                .withCause(e)
                                .asRuntimeException())
                        }
                    }
                }

                override fun onError(throwable: Throwable) {
                    logger.error("Error in bidirectional streaming", throwable)
                    responseObserver.onError(Status.INTERNAL
                        .withDescription("Failed to process user update stream")
                        .withCause(throwable)
                        .asRuntimeException())
                }

                override fun onCompleted() {
                    logger.info("Bidirectional streaming completed")
                    responseObserver.onCompleted()
                }
            }
        }
    }
    ```

### Test Bidirectional Streaming

Test the bidirectional streaming implementation:

```bash
# Generate updated protobuf classes
./gradlew generateProto

# Build and run
./gradlew build
./gradlew run
```

Test with grpcurl (bidirectional streaming requires a more complex setup):

```bash
# First create some users to update
grpcurl -plaintext -d '{"name": "Frank", "email": "frank@example.com"}' \
  localhost:9090 ru.tinkoff.kora.example.UserService/CreateUser

# Get the user ID from the response, then test bidirectional streaming
# Note: grpcurl has limited support for bidirectional streaming
# For full testing, you'd need a proper gRPC client
```

## Advanced Interceptors and Production Features

Now that you have all streaming patterns implemented, let's add advanced interceptors and production-ready features.

### Advanced Interceptor Patterns

### Streaming Message Design Best Practices

#### Server Streaming Messages
- **Chunking Strategy**: Break large responses into smaller chunks (1-10 items per message)
- **Metadata First**: Send metadata about the total size before streaming data
- **Progress Indicators**: Include progress information in streaming responses

#### Client Streaming Messages
- **Batch Size Limits**: Limit the number of messages a client can send in one stream
- **Validation**: Validate each message as it's received, not just at the end
- **Acknowledgment**: Send periodic acknowledgments for long-running streams

#### Bidirectional Streaming Messages
- **Message Ordering**: Use sequence numbers to maintain order
- **Heartbeat Messages**: Send periodic keep-alive messages
- **Flow Control**: Implement backpressure handling

## Testing Streaming RPCs

### Unit Testing with StreamRecorder

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/ru/tinkoff/kora/example/grpc/UserServiceGrpcHandlerTest.java`:

    ```java
    package ru.tinkoff.kora.example.grpc;

    import io.grpc.Status;
    import io.grpc.stub.StreamObserver;
    import org.junit.jupiter.api.BeforeEach;
    import org.junit.jupiter.api.Test;
    import ru.tinkoff.kora.example.service.UserService;
    import ru.tinkoff.kora.example.*;

    import java.util.List;

    import static org.assertj.core.api.Assertions.assertThat;

    class UserServiceGrpcHandlerTest {

        private UserServiceGrpcHandler handler;
        private UserService userService;

        @BeforeEach
        void setUp() {
            userService = new UserService();
            handler = new UserServiceGrpcHandler(userService);
        }

        @Test
        void testCreateUser() {
            // Given
            CreateUserRequest request = CreateUserRequest.newBuilder()
                .setName("Test User")
                .setEmail("test@example.com")
                .build();

            StreamRecorder<UserResponse> recorder = StreamRecorder.create();

            // When
            handler.createUser(request, recorder);

            // Then
            assertThat(recorder.getValues()).hasSize(1);
            UserResponse response = recorder.getValues().get(0);
            assertThat(response.getName()).isEqualTo("Test User");
            assertThat(response.getEmail()).isEqualTo("test@example.com");
            assertThat(response.getId()).isNotEmpty();
        }

        @Test
        void testGetAllUsersStreaming() {
            // Given - create some users first
            userService.createUser("User1", "user1@example.com");
            userService.createUser("User2", "user2@example.com");

            StreamRecorder<UserResponse> recorder = StreamRecorder.create();

            // When
            handler.getAllUsers(com.google.protobuf.Empty.getDefaultInstance(), recorder);

            // Then
            List<UserResponse> responses = recorder.getValues();
            assertThat(responses).hasSize(2);
            assertThat(responses.get(0).getName()).isEqualTo("User1");
            assertThat(responses.get(1).getName()).isEqualTo("User2");
        }

        @Test
        void testCreateUsersClientStreaming() {
            // Given
            StreamRecorder<CreateUsersResponse> recorder = StreamRecorder.create();
            StreamObserver<CreateUserRequest> requestObserver = handler.createUsers(recorder);

            // When - send multiple requests
            requestObserver.onNext(CreateUserRequest.newBuilder()
                .setName("Batch User 1")
                .setEmail("batch1@example.com")
                .build());
            requestObserver.onNext(CreateUserRequest.newBuilder()
                .setName("Batch User 2")
                .setEmail("batch2@example.com")
                .build());
            requestObserver.onCompleted();

            // Then
            List<CreateUsersResponse> responses = recorder.getValues();
            assertThat(responses).hasSize(1);
            CreateUsersResponse response = responses.get(0);
            assertThat(response.getCreatedCount()).isEqualTo(2);
            assertThat(response.getUserIdsList()).hasSize(2);
        }

        @Test
        void testUpdateUsersBidirectionalStreaming() {
            // Given - create a user to update
            UserResponse createdUser = userService.createUser("Original", "original@example.com");

            StreamRecorder<UserResponse> recorder = StreamRecorder.create();
            StreamObserver<UserUpdate> requestObserver = handler.updateUsers(recorder);

            // When - send update request
            requestObserver.onNext(UserUpdate.newBuilder()
                .setUserId(createdUser.getId())
                .setName("Updated Name")
                .setEmail("updated@example.com")
                .build());
            requestObserver.onCompleted();

            // Then - wait a bit for async processing
            try {
                Thread.sleep(100);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }

            List<UserResponse> responses = recorder.getValues();
            assertThat(responses).hasSize(1);
            UserResponse updatedUser = responses.get(0);
            assertThat(updatedUser.getName()).isEqualTo("Updated Name");
            assertThat(updatedUser.getEmail()).isEqualTo("updated@example.com");
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/ru/tinkoff/kora/example/grpc/UserServiceGrpcHandlerTest.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.grpc

    import io.grpc.stub.StreamObserver
    import org.junit.jupiter.api.BeforeEach
    import org.junit.jupiter.api.Test
    import ru.tinkoff.kora.example.service.UserService
    import ru.tinkoff.kora.example.*
    import kotlin.test.assertEquals
    import kotlin.test.assertNotNull

    class UserServiceGrpcHandlerTest {

        private lateinit var handler: UserServiceGrpcHandler
        private lateinit var userService: UserService

        @BeforeEach
        fun setUp() {
            userService = UserService()
            handler = UserServiceGrpcHandler(userService)
        }

        @Test
        fun testCreateUser() {
            // Given
            val request = CreateUserRequest.newBuilder()
                .setName("Test User")
                .setEmail("test@example.com")
                .build()

            val recorder = StreamRecorder.create<UserResponse>()

            // When
            handler.createUser(request, recorder)

            // Then
            assertEquals(1, recorder.values.size)
            val response = recorder.values[0]
            assertEquals("Test User", response.name)
            assertEquals("test@example.com", response.email)
            assertNotNull(response.id)
        }

        @Test
        fun testGetAllUsersStreaming() {
            // Given - create some users first
            userService.createUser("User1", "user1@example.com")
            userService.createUser("User2", "user2@example.com")

            val recorder = StreamRecorder.create<UserResponse>()

            // When
            handler.getAllUsers(com.google.protobuf.Empty.getDefaultInstance(), recorder)

            // Then
            val responses = recorder.values
            assertEquals(2, responses.size)
            assertEquals("User1", responses[0].name)
            assertEquals("User2", responses[1].name)
        }

        @Test
        fun testCreateUsersClientStreaming() {
            // Given
            val recorder = StreamRecorder.create<CreateUsersResponse>()
            val requestObserver = handler.createUsers(recorder)

            // When - send multiple requests
            requestObserver.onNext(CreateUserRequest.newBuilder()
                .setName("Batch User 1")
                .setEmail("batch1@example.com")
                .build())
            requestObserver.onNext(CreateUserRequest.newBuilder()
                .setName("Batch User 2")
                .setEmail("batch2@example.com")
                .build())
            requestObserver.onCompleted()

            // Then
            val responses = recorder.values
            assertEquals(1, responses.size)
            val response = responses[0]
            assertEquals(2, response.createdCount)
            assertEquals(2, response.userIdsList.size)
        }

        @Test
        fun testUpdateUsersBidirectionalStreaming() {
            // Given - create a user to update
            val createdUser = userService.createUser("Original", "original@example.com")

            val recorder = StreamRecorder.create<UserResponse>()
            val requestObserver = handler.updateUsers(recorder)

            // When - send update request
            requestObserver.onNext(UserUpdate.newBuilder()
                .setUserId(createdUser.id)
                .setName("Updated Name")
                .setEmail("updated@example.com")
                .build())
            requestObserver.onCompleted()

            // Then - wait a bit for async processing
            Thread.sleep(100)

            val responses = recorder.values
            assertEquals(1, responses.size)
            val updatedUser = responses[0]
            assertEquals("Updated Name", updatedUser.name)
            assertEquals("updated@example.com", updatedUser.email)
        }
    }
    ```

## Deployment and Production Considerations

### Health Checks and Monitoring

**gRPC Health Checks:**

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/grpc/GrpcHealthService.java`:

    ```java
    package ru.tinkoff.kora.example.grpc;

    import io.grpc.health.v1.HealthCheckResponse;
    import io.grpc.health.v1.HealthGrpc;
    import io.grpc.health.v1.HealthCheckRequest;
    import io.grpc.stub.StreamObserver;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.service.UserService;

    @Component
    public final class GrpcHealthService extends HealthGrpc.HealthImplBase {

        private final UserService userService;

        public GrpcHealthService(UserService userService) {
            this.userService = userService;
        }

        @Override
        public void check(HealthCheckRequest request, StreamObserver<HealthCheckResponse> responseObserver) {
            try {
                // Perform basic health checks
                // Check if user service is accessible
                userService.getAllUsers();

                // Check database connectivity if applicable
                // performDatabaseHealthCheck();

                HealthCheckResponse response = HealthCheckResponse.newBuilder()
                    .setStatus(HealthCheckResponse.ServingStatus.SERVING)
                    .build();

                responseObserver.onNext(response);
                responseObserver.onCompleted();

            } catch (Exception e) {
                HealthCheckResponse response = HealthCheckResponse.newBuilder()
                    .setStatus(HealthCheckResponse.ServingStatus.NOT_SERVING)
                    .build();

                responseObserver.onNext(response);
                responseObserver.onCompleted();
            }
        }

        @Override
        public void watch(HealthCheckRequest request, StreamObserver<HealthCheckResponse> responseObserver) {
            // For simplicity, just return current status
            // In production, you might want to stream health status changes
            check(request, responseObserver);
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/grpc/GrpcHealthService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.grpc

    import io.grpc.health.v1.HealthCheckRequest
    import io.grpc.health.v1.HealthCheckResponse
    import io.grpc.health.v1.HealthGrpc
    import io.grpc.stub.StreamObserver
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.service.UserService

    @Component
    class GrpcHealthService : HealthGrpc.HealthImplBase() {

        private val userService: UserService

        constructor(userService: UserService) {
            this.userService = userService
        }

        override fun check(request: HealthCheckRequest, responseObserver: StreamObserver<HealthCheckResponse>) {
            try {
                // Perform basic health checks
                // Check if user service is accessible
                userService.getAllUsers()

                // Check database connectivity if applicable
                // performDatabaseHealthCheck()

                val response = HealthCheckResponse.newBuilder()
                    .setStatus(HealthCheckResponse.ServingStatus.SERVING)
                    .build()

                responseObserver.onNext(response)
                responseObserver.onCompleted()

            } catch (e: Exception) {
                val response = HealthCheckResponse.newBuilder()
                    .setStatus(HealthCheckResponse.ServingStatus.NOT_SERVING)
                    .build()

                responseObserver.onNext(response)
                responseObserver.onCompleted()
            }
        }

        override fun watch(request: HealthCheckRequest, responseObserver: StreamObserver<HealthCheckResponse>) {
            // For simplicity, just return current status
            // In production, you might want to stream health status changes
            check(request, responseObserver)
        }
    }
    ```

### Security Considerations

**Authentication Interceptor:**

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/grpc/AuthenticationInterceptor.java`:

    ```java
    package ru.tinkoff.kora.example.grpc;

    import io.grpc.*;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;

    @Component
    public final class AuthenticationInterceptor implements ServerInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(AuthenticationInterceptor.class);
        private static final Metadata.Key<String> AUTH_TOKEN_KEY =
            Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER);

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                ServerCall<ReqT, RespT> call,
                Metadata headers,
                ServerCallHandler<ReqT, RespT> next) {

            String authToken = headers.get(AUTH_TOKEN_KEY);

            if (authToken == null || authToken.isEmpty()) {
                logger.warn("Missing authentication token for method: {}",
                    call.getMethodDescriptor().getFullMethodName());
                call.close(Status.UNAUTHENTICATED.withDescription("Authentication token required"),
                    new Metadata());
                return new ServerCall.Listener<ReqT>() {};
            }

            // Validate token (simplified - in production use proper JWT validation)
            if (!isValidToken(authToken)) {
                logger.warn("Invalid authentication token for method: {}",
                    call.getMethodDescriptor().getFullMethodName());
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid authentication token"),
                    new Metadata());
                return new ServerCall.Listener<ReqT>() {};
            }

            logger.debug("Authentication successful for method: {}",
                call.getMethodDescriptor().getFullMethodName());

            return next.startCall(call, headers);
        }

        private boolean isValidToken(String token) {
            // Simplified token validation - in production:
            // - Verify JWT signature
            // - Check expiration
            // - Validate claims
            // - Check against revocation list
            return token.startsWith("Bearer ") && token.length() > 20;
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/grpc/AuthenticationInterceptor.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.grpc

    import io.grpc.Metadata
    import io.grpc.ServerCall
    import io.grpc.ServerCallHandler
    import io.grpc.ServerInterceptor
    import io.grpc.Status
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component

    @Component
    class AuthenticationInterceptor : ServerInterceptor {

        private val logger = LoggerFactory.getLogger(AuthenticationInterceptor::class.java)
        private val AUTH_TOKEN_KEY = Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER)

        override fun <ReqT, RespT> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            val authToken = headers[AUTH_TOKEN_KEY]

            if (authToken.isNullOrEmpty()) {
                logger.warn("Missing authentication token for method: {}",
                    call.methodDescriptor.fullMethodName)
                call.close(Status.UNAUTHENTICATED.withDescription("Authentication token required"),
                    Metadata())
                return object : ServerCall.Listener<ReqT>() {}
            }

            // Validate token (simplified - in production use proper JWT validation)
            if (!isValidToken(authToken)) {
                logger.warn("Invalid authentication token for method: {}",
                    call.methodDescriptor.fullMethodName)
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid authentication token"),
                    Metadata())
                return object : ServerCall.Listener<ReqT>() {}
            }

            logger.debug("Authentication successful for method: {}",
                call.methodDescriptor.fullMethodName)

            return next.startCall(call, headers)
        }

        private fun isValidToken(token: String): Boolean {
            // Simplified token validation - in production:
            // - Verify JWT signature
            // - Check expiration
            // - Validate claims
            // - Check against revocation list
            return token.startsWith("Bearer ") && token.length > 20
        }
    }
    ```

### Rate Limiting Interceptor

**Rate Limiting Interceptor:**

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/grpc/RateLimitingInterceptor.java`:

    ```java
    package ru.tinkoff.kora.example.grpc;

    import io.grpc.*;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;

    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;

    @Component
    public final class RateLimitingInterceptor implements ServerInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(RateLimitingInterceptor.class);

        // Simple in-memory rate limiting (use Redis/external store in production)
        private final ConcurrentHashMap<String, AtomicLong> requestCounts = new ConcurrentHashMap<>();
        private final ConcurrentHashMap<String, Long> windowStartTimes = new ConcurrentHashMap<>();

        private static final long WINDOW_SIZE_MS = 60_000; // 1 minute
        private static final long MAX_REQUESTS_PER_WINDOW = 100; // Adjust based on your needs

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                ServerCall<ReqT, RespT> call,
                Metadata headers,
                ServerCallHandler<ReqT, RespT> next) {

            String clientId = getClientId(headers);
            String methodName = call.getMethodDescriptor().getFullMethodName();
            String key = clientId + ":" + methodName;

            long currentTime = System.currentTimeMillis();
            long windowStart = windowStartTimes.computeIfAbsent(key, k -> currentTime);

            // Reset window if expired
            if (currentTime - windowStart > WINDOW_SIZE_MS) {
                requestCounts.put(key, new AtomicLong(0));
                windowStartTimes.put(key, currentTime);
            }

            // Check rate limit
            long currentCount = requestCounts.computeIfAbsent(key, k -> new AtomicLong(0))
                .incrementAndGet();

            if (currentCount > MAX_REQUESTS_PER_WINDOW) {
                logger.warn("Rate limit exceeded for client: {}, method: {}", clientId, methodName);
                call.close(Status.RESOURCE_EXHAUSTED
                    .withDescription("Rate limit exceeded. Try again later."),
                    new Metadata());
                return new ServerCall.Listener<ReqT>() {};
            }

            return next.startCall(call, headers);
        }

        private String getClientId(Metadata headers) {
            // Extract client identifier from headers (IP, API key, etc.)
            // In production, use proper client identification
            String clientIp = headers.get(Metadata.Key.of("x-forwarded-for", Metadata.ASCII_STRING_MARSHALLER));
            return clientIp != null ? clientIp : "unknown";
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/grpc/RateLimitingInterceptor.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.grpc

    import io.grpc.Metadata
    import io.grpc.ServerCall
    import io.grpc.ServerCallHandler
    import io.grpc.ServerInterceptor
    import io.grpc.Status
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import java.util.concurrent.ConcurrentHashMap
    import java.util.concurrent.atomic.AtomicLong

    @Component
    class RateLimitingInterceptor : ServerInterceptor {

        private val logger = LoggerFactory.getLogger(RateLimitingInterceptor::class.java)

        // Simple in-memory rate limiting (use Redis/external store in production)
        private val requestCounts = ConcurrentHashMap<String, AtomicLong>()
        private val windowStartTimes = ConcurrentHashMap<String, Long>()

        private val WINDOW_SIZE_MS = 60_000L // 1 minute
        private val MAX_REQUESTS_PER_WINDOW = 100L // Adjust based on your needs

        override fun <ReqT, RespT> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            val clientId = getClientId(headers)
            val methodName = call.methodDescriptor.fullMethodName
            val key = "$clientId:$methodName"

            val currentTime = System.currentTimeMillis()
            val windowStart = windowStartTimes.computeIfAbsent(key) { currentTime }

            // Reset window if expired
            if (currentTime - windowStart > WINDOW_SIZE_MS) {
                requestCounts[key] = AtomicLong(0)
                windowStartTimes[key] = currentTime
            }

            // Check rate limit
            val currentCount = requestCounts.computeIfAbsent(key) { AtomicLong() }
                .incrementAndGet()

            if (currentCount > MAX_REQUESTS_PER_WINDOW) {
                logger.warn("Rate limit exceeded for client: {}, method: {}", clientId, methodName)
                call.close(Status.RESOURCE_EXHAUSTED
                    .withDescription("Rate limit exceeded. Try again later."),
                    Metadata())
                return object : ServerCall.Listener<ReqT>() {}
            }

            return next.startCall(call, headers)
        }

        private fun getClientId(headers: Metadata): String {
            // Extract client identifier from headers (IP, API key, etc.)
            // In production, use proper client identification
            val clientIp = headers[Metadata.Key.of("x-forwarded-for", Metadata.ASCII_STRING_MARSHALLER)]
            return clientIp ?: "unknown"
        }
    }
    ```

## Summary

You've successfully built a comprehensive gRPC server with Kora that demonstrates all streaming patterns:

- **Unary RPC**: `CreateUser`, `GetUser` - Simple request-response
- **Server Streaming**: `GetAllUsers` - Stream multiple responses
- **Client Streaming**: `CreateUsers` - Process multiple requests
- **Bidirectional Streaming**: `UpdateUsers` - Real-time updates

**Key Features Implemented:**
- Production-ready error handling with proper gRPC Status codes
- Flow control and backpressure management
- Advanced interceptors (metrics, authentication, rate limiting)
- Comprehensive testing with StreamRecorder
- Health checks and monitoring
- Thread-safe concurrent data structures

**Production Considerations:**
- Use persistent storage instead of in-memory ConcurrentHashMap
- Implement proper authentication and authorization
- Add comprehensive monitoring and alerting
- Configure appropriate timeouts and resource limits
- Consider using gRPC-Gateway for REST API compatibility

This implementation showcases Kora's powerful dependency injection and component model while demonstrating best practices for building scalable gRPC services with streaming capabilities.

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

      // Server streaming: Stream all users to client
      rpc GetAllUsers(google.protobuf.Empty) returns (stream UserResponse) {}

      // Client streaming: Accept multiple user creation requests
      rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse) {}

      // Bidirectional streaming: Real-time user updates
      rpc UpdateUsers(stream UserUpdate) returns (stream UserResponse) {}
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

    // Response message for batch user creation
    message CreateUsersResponse {
      int32 created_count = 1;     // Number of users created
      repeated string user_ids = 2; // Array of created user IDs
    }

    // Message for user update operations
    message UserUpdate {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }

    // Enumeration for user status values
    enum UserStatus {
      ACTIVE = 0;     // Default value (first enum value should be 0)
      INACTIVE = 1;
      SUSPENDED = 2;
    }
    ```

### Streaming Message Design Best Practices

#### Server Streaming Messages
- **Chunk Size**: Balance between latency and throughput
- **Metadata**: Include progress indicators, sequence numbers
- **Termination**: Clear end-of-stream signaling

#### Client Streaming Messages
- **Batch Size**: Optimize for network efficiency
- **Acknowledgment**: Server feedback for reliability
- **Error Recovery**: Handle partial failures gracefully

#### Bidirectional Streaming Messages
- **Correlation IDs**: Match requests with responses
- **Flow Control**: Prevent resource exhaustion
- **State Management**: Handle connection interruptions

## Enhanced User Service Implementation

The UserService now supports all streaming operations with proper thread safety and resource management.

### Key Enhancements:

- **Thread-Safe Operations**: Concurrent access for streaming scenarios
- **Resource Management**: Proper cleanup and memory management
- **Streaming Support**: Methods for batch operations and real-time updates
- **Performance Optimization**: Efficient data structures for streaming

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.example.service;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.UserResponse;
    import ru.tinkoff.kora.example.UserStatus;

    import java.time.Instant;
    import java.util.List;
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

        /**
         * Returns an immutable list of all users.
         * Uses List.copyOf() to ensure immutability.
         */
        public List<UserResponse> getAllUsers() {
            return List.copyOf(users.values());
        }

        /**
         * Updates an existing user's information.
         * Only updates fields that are provided (non-null).
         * Returns null if the user doesn't exist.
         */
        public UserResponse updateUser(String userId, String name, String email) {
            UserResponse existingUser = users.get(userId);
            if (existingUser == null) {
                return null;
            }

            // Build updated user, preserving existing values for null fields
            UserResponse updatedUser = existingUser.toBuilder()
                .setName(name != null ? name : existingUser.getName())
                .setEmail(email != null ? email : existingUser.getEmail())
                .build();

            users.put(userId, updatedUser);
            return updatedUser;
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

        /**
         * Returns an immutable list of all users.
         * Uses toList() to create a new immutable list.
         */
        fun getAllUsers(): List<UserResponse> {
            return users.values.toList()
        }

        /**
         * Updates an existing user's information.
         * Only updates fields that are provided (non-null).
         * Returns null if the user doesn't exist.
         */
        fun updateUser(userId: String, name: String?, email: String?): UserResponse? {
            val existingUser = users[userId] ?: return null

            // Build updated user, preserving existing values for null fields
            val updatedUser = existingUser.toBuilder()
                .setName(name ?: existingUser.name)
                .setEmail(email ?: existingUser.email)
                .build()

            users[userId] = updatedUser
            return updatedUser
        }
    }
    ```

## Advanced gRPC Service Handler

The enhanced handler now implements all streaming patterns with proper resource management and error handling.

### Streaming Implementation Patterns:

#### Server Streaming Implementation
- **Iterator Pattern**: Process and stream results progressively
- **Backpressure Handling**: Respect client's consumption rate
- **Resource Cleanup**: Ensure proper resource management
- **Error Propagation**: Handle errors during streaming

#### Client Streaming Implementation
- **Stateful Processing**: Accumulate client requests
- **Batch Optimization**: Process requests efficiently
- **Partial Failure Handling**: Handle individual request failures
- **Atomic Operations**: Ensure consistency in batch operations

#### Bidirectional Streaming Implementation
- **Independent Streams**: Handle request/response streams separately
- **Correlation Management**: Match requests with responses
- **Flow Control**: Prevent resource exhaustion
- **Real-time Processing**: Immediate response to client requests

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

    import java.util.ArrayList;
    import java.util.List;

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

        @Override
        public void getAllUsers(com.google.protobuf.Empty request, StreamObserver<UserResponse> responseObserver) {
            try {
                logger.info("Streaming all users");

                List<UserResponse> users = userService.getAllUsers();

                for (UserResponse user : users) {
                    // Check if client is still connected
                    if (responseObserver instanceof io.grpc.stub.ServerCallStreamObserver) {
                        io.grpc.stub.ServerCallStreamObserver<UserResponse> serverObserver =
                            (io.grpc.stub.ServerCallStreamObserver<UserResponse>) responseObserver;

                        // Check for client cancellation
                        if (serverObserver.isCancelled()) {
                            logger.info("Client cancelled streaming request");
                            return;
                        }
                    }

                    responseObserver.onNext(user);

                    // Simulate processing time and allow for backpressure
                    try {
                        Thread.sleep(50); // Reduced for demonstration
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        logger.warn("Streaming interrupted");
                        break;
                    }
                }

                responseObserver.onCompleted();
                logger.info("Streamed {} users successfully", users.size());

            } catch (Exception e) {
                logger.error("Error streaming users", e);
                responseObserver.onError(Status.INTERNAL
                    .withDescription("Failed to stream users")
                    .withCause(e)
                    .asRuntimeException());
            }
        }

        @Override
        public StreamObserver<CreateUserRequest> createUsers(StreamObserver<CreateUsersResponse> responseObserver) {
            return new StreamObserver<CreateUserRequest>() {
                private final List<String> createdUserIds = new ArrayList<>();
                private final List<String> failedRequests = new ArrayList<>();
                private int requestCount = 0;

                @Override
                public void onNext(CreateUserRequest request) {
                    try {
                        requestCount++;
                        logger.info("Processing user creation request {}: name={}, email={}",
                            requestCount, request.getName(), request.getEmail());

                        UserResponse user = userService.createUser(request.getName(), request.getEmail());
                        createdUserIds.add(user.getId());

                        logger.info("User created in stream: id={}", user.getId());

                    } catch (Exception e) {
                        logger.error("Error processing user {} in stream", requestCount, e);
                        failedRequests.add("Request " + requestCount + ": " + e.getMessage());
                        // Continue processing other requests
                    }
                }

                @Override
                public void onError(Throwable throwable) {
                    logger.error("Client streaming error", throwable);
                    responseObserver.onError(Status.INTERNAL
                        .withDescription("Client streaming failed")
                        .withCause(throwable)
                        .asRuntimeException());
                }

                @Override
                public void onCompleted() {
                    try {
                        logger.info("Client streaming completed, created {} users, {} failed",
                            createdUserIds.size(), failedRequests.size());

                        CreateUsersResponse response = CreateUsersResponse.newBuilder()
                            .setCreatedCount(createdUserIds.size())
                            .addAllUserIds(createdUserIds)
                            .build();

                        responseObserver.onNext(response);
                        responseObserver.onCompleted();

                        if (!failedRequests.isEmpty()) {
                            logger.warn("Some requests failed: {}", String.join("; ", failedRequests));
                        }

                    } catch (Exception e) {
                        logger.error("Error completing client streaming", e);
                        responseObserver.onError(Status.INTERNAL
                            .withDescription("Failed to complete user creation streaming")
                            .withCause(e)
                            .asRuntimeException());
                    }
                }
            };
        }

        @Override
        public StreamObserver<UserUpdate> updateUsers(StreamObserver<UserResponse> responseObserver) {
            return new StreamObserver<UserUpdate>() {
                @Override
                public void onNext(UserUpdate update) {
                    try {
                        logger.info("Processing user update: id={}, name={}, email={}",
                            update.getUserId(), update.getName(), update.getEmail());

                        UserResponse updatedUser = userService.updateUser(
                            update.getUserId(),
                            update.getName(),
                            update.getEmail()
                        );

                        if (updatedUser == null) {
                            logger.warn("User not found for update: id={}", update.getUserId());
                            responseObserver.onError(Status.NOT_FOUND
                                .withDescription("User not found: " + update.getUserId())
                                .asRuntimeException());
                            return;
                        }

                        responseObserver.onNext(updatedUser);
                        logger.info("User updated in bidirectional stream: id={}", updatedUser.getId());

                    } catch (Exception e) {
                        logger.error("Error processing user update in stream", e);
                        responseObserver.onError(Status.INTERNAL
                            .withDescription("Failed to process user update")
                            .withCause(e)
                    .asRuntimeException());
                    }
                }

                @Override
                public void onError(Throwable throwable) {
                    logger.error("Bidirectional streaming error", throwable);
                    responseObserver.onError(Status.INTERNAL
                        .withDescription("Bidirectional streaming failed")
                        .withCause(throwable)
                        .asRuntimeException());
                }

                @Override
                public void onCompleted() {
                    logger.info("Bidirectional streaming completed");
                    responseObserver.onCompleted();
                }
            };
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

        override fun getAllUsers(request: com.google.protobuf.Empty, responseObserver: StreamObserver<UserResponse>) {
            try {
                logger.info("Streaming all users")

                val users = userService.getAllUsers()

                for (user in users) {
                    // Check if client is still connected
                    if (responseObserver is io.grpc.stub.ServerCallStreamObserver<*>) {
                        val serverObserver = responseObserver as io.grpc.stub.ServerCallStreamObserver<UserResponse>

                        // Check for client cancellation
                        if (serverObserver.isCancelled) {
                            logger.info("Client cancelled streaming request")
                            return
                        }
                    }

                    responseObserver.onNext(user)

                    // Simulate processing time and allow for backpressure
                    try {
                        Thread.sleep(50) // Reduced for demonstration
                    } catch (e: InterruptedException) {
                        Thread.currentThread().interrupt()
                        logger.warn("Streaming interrupted")
                        break
                    }
                }

                responseObserver.onCompleted()
                logger.info("Streamed {} users successfully", users.size)

            } catch (e: Exception) {
                logger.error("Error streaming users", e)
                responseObserver.onError(Status.INTERNAL
                    .withDescription("Failed to stream users")
                    .withCause(e)
                    .asRuntimeException())
            }
        }

        override fun createUsers(responseObserver: StreamObserver<CreateUsersResponse>): StreamObserver<CreateUserRequest> {
            return object : StreamObserver<CreateUserRequest> {
                private val createdUserIds = mutableListOf<String>()
                private val failedRequests = mutableListOf<String>()
                private var requestCount = 0

                override fun onNext(request: CreateUserRequest) {
                    try {
                        requestCount++
                        logger.info("Processing user creation request {}: name={}, email={}",
                            requestCount, request.name, request.email)

                        val user = userService.createUser(request.name, request.email)
                        createdUserIds.add(user.id)

                        logger.info("User created in stream: id={}", user.id)

                    } catch (e: Exception) {
                        logger.error("Error processing user {} in stream", requestCount, e)
                        failedRequests.add("Request $requestCount: ${e.message}")
                        // Continue processing other requests
                    }
                }

                override fun onError(throwable: Throwable) {
                    logger.error("Client streaming error", throwable)
                    responseObserver.onError(Status.INTERNAL
                        .withDescription("Client streaming failed")
                        .withCause(throwable)
                        .asRuntimeException())
                }

                override fun onCompleted() {
                    try {
                        logger.info("Client streaming completed, created {} users, {} failed",
                            createdUserIds.size, failedRequests.size)

                        val response = CreateUsersResponse.newBuilder()
                            .setCreatedCount(createdUserIds.size)
                            .addAllUserIds(createdUserIds)
                            .build()

                        responseObserver.onNext(response)
                        responseObserver.onCompleted()

                        if (failedRequests.isNotEmpty()) {
                            logger.warn("Some requests failed: {}", failedRequests.joinToString("; "))
                        }

                    } catch (e: Exception) {
                        logger.error("Error completing client streaming", e)
                        responseObserver.onError(Status.INTERNAL
                            .withDescription("Failed to complete user creation streaming")
                            .withCause(e)
                            .asRuntimeException())
                    }
                }
            }
        }

        override fun updateUsers(responseObserver: StreamObserver<UserResponse>): StreamObserver<UserUpdate> {
            return object : StreamObserver<UserUpdate> {
                override fun onNext(update: UserUpdate) {
                    try {
                        logger.info("Processing user update: id={}, name={}, email={}",
                            update.userId, update.name, update.email)

                        val updatedUser = userService.updateUser(
                            update.userId,
                            update.name,
                            update.email
                        )

                        if (updatedUser == null) {
                            logger.warn("User not found for update: id={}", update.userId)
                            responseObserver.onError(Status.NOT_FOUND
                                .withDescription("User not found: " + update.userId)
                                .asRuntimeException())
                            return
                        }

                        responseObserver.onNext(updatedUser)
                        logger.info("User updated in bidirectional stream: id={}", updatedUser.id)

                    } catch (e: Exception) {
                        logger.error("Error processing user update in stream", e)
                        responseObserver.onError(Status.INTERNAL
                            .withDescription("Failed to process user update")
                            .withCause(e)
                            .asRuntimeException())
                    }
                }

                override fun onError(throwable: Throwable) {
                    logger.error("Bidirectional streaming error", throwable)
                    responseObserver.onError(Status.INTERNAL
                        .withDescription("Bidirectional streaming failed")
                        .withCause(throwable)
                        .asRuntimeException())
                }

                override fun onCompleted() {
                    logger.info("Bidirectional streaming completed")
                    responseObserver.onCompleted()
                }
            }
        }
    }
    ```

## Advanced Streaming Patterns and Best Practices

### Server Streaming Best Practices

#### Flow Control and Backpressure
- **Client-Driven Pace**: Respect client's consumption rate
- **Buffering Strategy**: Balance memory usage with throughput
- **Cancellation Handling**: Properly handle client disconnection

#### Performance Optimization
- **Chunk Size**: Optimize message size for network efficiency
- **Parallel Processing**: Process data in parallel when possible
- **Resource Management**: Clean up resources promptly

#### Error Handling
- **Partial Failures**: Handle errors mid-stream gracefully
- **Recovery Strategies**: Implement retry mechanisms
- **Client Notification**: Inform clients of stream termination reasons

### Client Streaming Best Practices

#### Batch Processing
- **Optimal Batch Size**: Balance latency with throughput
- **Transaction Boundaries**: Define clear batch boundaries
- **Progress Feedback**: Provide progress updates to clients

#### Error Recovery
- **Partial Success**: Handle scenarios where some requests succeed
- **Retry Logic**: Implement intelligent retry strategies
- **State Management**: Maintain state across retries

#### Resource Management
- **Memory Limits**: Prevent memory exhaustion from large batches
- **Timeout Handling**: Implement appropriate timeouts
- **Connection Management**: Handle connection failures gracefully

### Bidirectional Streaming Best Practices

#### State Synchronization
- **Correlation IDs**: Match requests with responses
- **Sequence Numbers**: Maintain message ordering
- **State Recovery**: Handle connection interruptions

#### Flow Control
- **Rate Limiting**: Prevent resource exhaustion
- **Buffer Management**: Manage message queues effectively
- **Load Balancing**: Distribute load across instances

#### Real-time Considerations
- **Latency Requirements**: Meet real-time latency expectations
- **Message Ordering**: Ensure proper message sequencing
- **Duplicate Handling**: Handle duplicate messages gracefully

## Advanced Interceptor Patterns

### Authentication and Authorization Interceptor

```java
@Component
public class AuthInterceptor implements ServerInterceptor {

    private final JwtService jwtService;
    private final PermissionService permissionService;

    public AuthInterceptor(JwtService jwtService, PermissionService permissionService) {
        this.jwtService = jwtService;
        this.permissionService = permissionService;
    }

    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
            ServerCall<ReqT, RespT> call, Metadata headers, ServerCallHandler<ReqT, RespT> next) {

        try {
            // Extract and validate JWT token
            String authHeader = headers.get(Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER));
            if (authHeader == null || !authHeader.startsWith("Bearer ")) {
                call.close(Status.UNAUTHENTICATED.withDescription("Missing or invalid authorization header"),
                          new Metadata());
                return new ServerCall.Listener<ReqT>() {};
            }

            String token = authHeader.substring(7); // Remove "Bearer " prefix
            UserPrincipal principal = jwtService.validateToken(token);

            // Check permissions for this method
            String methodName = call.getMethodDescriptor().getFullMethodName();
            if (!permissionService.hasPermission(principal, methodName)) {
                call.close(Status.PERMISSION_DENIED.withDescription("Insufficient permissions"),
                          new Metadata());
                return new ServerCall.Listener<ReqT>() {};
            }

            // Add user context to call attributes
            Context context = Context.current().withValue(USER_PRINCIPAL_KEY, principal);
            return Contexts.interceptCall(context, call, headers, next);

        } catch (JwtException e) {
            call.close(Status.UNAUTHENTICATED.withDescription("Invalid token"), new Metadata());
            return new ServerCall.Listener<ReqT>() {};
        }
    }
}
```

## Testing Advanced Streaming Scenarios

### Server Streaming Tests

```java
@Test
void testGetAllUsersStreaming() {
    // Create test users
    userService.createUser("Alice", "alice@example.com");
    userService.createUser("Bob", "bob@example.com");

    // Test streaming
    StreamRecorder<UserResponse> recorder = StreamRecorder.create();
    userServiceGrpcHandler.getAllUsers(Empty.getDefaultInstance(), recorder);

    List<UserResponse> responses = recorder.getValues();
    assertThat(responses).hasSize(2);
    assertThat(responses.get(0).getName()).isEqualTo("Alice");
    assertThat(responses.get(1).getName()).isEqualTo("Bob");
}
```

### Client Streaming Tests

```java
@Test
void testCreateUsersStreaming() {
    // Create streaming observer
    StreamRecorder<CreateUsersResponse> responseRecorder = StreamRecorder.create();
    StreamObserver<CreateUserRequest> requestObserver =
        userServiceGrpcHandler.createUsers(responseRecorder);

    // Send multiple requests
    requestObserver.onNext(CreateUserRequest.newBuilder()
        .setName("Alice").setEmail("alice@example.com").build());
    requestObserver.onNext(CreateUserRequest.newBuilder()
        .setName("Bob").setEmail("bob@example.com").build());
    requestObserver.onCompleted();

    // Verify response
    List<CreateUsersResponse> responses = responseRecorder.getValues();
    assertThat(responses).hasSize(1);
    assertThat(responses.get(0).getCreatedCount()).isEqualTo(2);
    assertThat(responses.get(0).getUserIdsList()).hasSize(2);
}
```

### Bidirectional Streaming Tests

```java
@Test
void testUpdateUsersBidirectionalStreaming() {
    // Create test user
    UserResponse user = userService.createUser("Alice", "alice@example.com");

    // Create streaming observers
    StreamRecorder<UserResponse> responseRecorder = StreamRecorder.create();
    StreamObserver<UserUpdate> requestObserver =
        userServiceGrpcHandler.updateUsers(responseRecorder);

    // Send update request
    requestObserver.onNext(UserUpdate.newBuilder()
        .setUserId(user.getId())
        .setName("Alice Updated")
        .build());
    requestObserver.onCompleted();

    // Verify response
    List<UserResponse> responses = responseRecorder.getValues();
    assertThat(responses).hasSize(1);
    assertThat(responses.get(0).getName()).isEqualTo("Alice Updated");
}
```

## Production Deployment Considerations

### Resource Management

#### Memory Optimization
- **Stream Buffering**: Configure appropriate buffer sizes
- **Object Pooling**: Reuse objects to reduce GC pressure
- **Connection Limits**: Set maximum concurrent streams

#### Performance Tuning
- **Thread Pools**: Configure appropriate thread pool sizes
- **Queue Management**: Handle request queuing properly
- **CPU Optimization**: Optimize for CPU-bound vs I/O-bound operations

### Monitoring and Observability

#### Key Metrics to Monitor
- **Stream Duration**: Monitor streaming operation times
- **Throughput**: Track messages per second
- **Error Rates**: Monitor streaming error rates
- **Resource Usage**: Track memory and CPU usage

#### Logging Best Practices
- **Structured Logging**: Use structured logs for streaming operations
- **Correlation IDs**: Track requests across stream boundaries
- **Performance Logging**: Log performance metrics

### Security Considerations

#### Transport Security
- **TLS Configuration**: Ensure proper TLS setup
- **Certificate Management**: Handle certificate rotation
- **Client Authentication**: Implement mutual TLS when needed

#### Authorization
- **Fine-grained Access**: Implement method-level authorization
- **Data Filtering**: Filter data based on user permissions
- **Audit Logging**: Log access for compliance

## Key Concepts Learned

### Advanced Protocol Buffers
- **Streaming Patterns**: Server, client, and bidirectional streaming
- **Message Design**: Optimizing messages for streaming scenarios
- **Schema Evolution**: Managing changes in streaming APIs

### Streaming Implementation
- **Flow Control**: Managing backpressure and resource usage
- **Error Handling**: Handling errors in streaming contexts
- **State Management**: Maintaining state across streaming operations

### Production Patterns
- **Resource Management**: Optimizing memory and CPU usage
- **Monitoring**: Comprehensive monitoring of streaming operations
- **Security**: Securing streaming APIs

### Interceptor Patterns
- **Authentication**: Securing streaming endpoints
- **Rate Limiting**: Protecting against abuse
- **Metrics Collection**: Monitoring streaming performance

## What's Next?

- [Deploy to Kubernetes](deployment-kubernetes.md)
- [Implement Circuit Breaker Pattern](resilience.md)
- [Add Distributed Tracing](observability-tracing.md)
- [Scale with Service Mesh](service-mesh.md)
- [Implement Event-Driven Architecture](event-driven.md)

## Help

If you encounter issues:

- Check the [gRPC Server Documentation](../../documentation/grpc-server.md)
- Verify protobuf compilation: `./gradlew generateProto`
- Check the [gRPC Server Example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-grpc-server)
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)