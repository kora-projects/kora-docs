---
title: Advanced gRPC Client with Kora
summary: Master advanced gRPC client concepts including streaming patterns, connection management, and production-ready implementations
tags: grpc-client, protobuf, streaming, rpc, microservices, advanced
---

# Advanced gRPC Client with Kora

This advanced guide builds upon the [basic gRPC Client guide](grpc-client.md) to explore sophisticated gRPC client concepts including streaming patterns, connection management, and production-ready implementations. You'll learn how to implement server streaming, client streaming, and bidirectional streaming clients for complex real-world scenarios.

## What You'll Build

You'll build an advanced UserService gRPC client that demonstrates all streaming patterns:

- **Server Streaming Client**: Consume streaming user data for real-time dashboards
- **Client Streaming Client**: Send multiple user creation requests in batches
- **Bidirectional Streaming Client**: Real-time user updates with live synchronization
- **Advanced Connection Management**: Connection pooling, retry logic, and circuit breakers
- **Production Features**: Flow control, backpressure handling, and error recovery
- **Comprehensive Testing**: Unit tests and integration tests for streaming scenarios

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide
- Completed [basic gRPC Client guide](grpc-client.md)
- Running advanced gRPC server from the [gRPC Server Advanced guide](grpc-server-advanced.md)
- Basic understanding of [Protocol Buffers](https://developers.google.com/protocol-buffers)
- Familiarity with streaming concepts and reactive programming

## Prerequisites

!!! note "Required: Complete Basic gRPC Guides First"

    This advanced guide assumes you have completed both the **[basic gRPC Client guide](grpc-client.md)** and **[basic gRPC Server guide](grpc-server.md)**, and have a working unary RPC implementation. You should also have the **[advanced gRPC Server guide](grpc-server-advanced.md)** running as this client will connect to those advanced server operations.

    You should understand:
    - Basic gRPC concepts and Protocol Buffers
    - Unary RPC patterns (CreateUser, GetUser)
    - Kora's dependency injection system
    - Basic gRPC client configuration and connection management
    - Protocol buffer compilation and code generation

    If you haven't completed these guides yet, please do so first as this guide builds upon those foundational concepts.

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

**Client Implementation**: The client sends one request and processes multiple responses asynchronously.

### Client Streaming
**Client streaming** enables clients to send multiple requests to a server, which processes them and returns a single response. This pattern excels at:

- **Batch operations**: Bulk data uploads, batch processing
- **Real-time aggregation**: Collecting metrics, sensor data
- **Complex workflows**: Multi-step operations with intermediate feedback

**Protocol Buffer Syntax**:
```protobuf
rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);
```

**Client Implementation**: The client sends multiple requests and receives one final response.

### Bidirectional Streaming
**Bidirectional streaming** provides full-duplex communication where both client and server can send multiple messages independently. This advanced pattern supports:

- **Real-time collaboration**: Chat applications, collaborative editing
- **Complex workflows**: Interactive data processing, negotiation protocols
- **Event-driven systems**: Real-time event processing and responses

**Protocol Buffer Syntax**:
```protobuf
rpc UpdateUsers(stream UserUpdate) returns (stream UserResponse);
```

**Client Implementation**: Both client and server can send and receive multiple messages asynchronously.

## Step 1: Adding Server Streaming Client (GetAllUsers)

Server streaming allows a client to send a single request and receive multiple responses from the server. This pattern is ideal for scenarios where you need to consume a collection of data that might be large or where you want to process results progressively.

### Understanding Server Streaming Client

In server streaming:
- **Client sends**: One request message
- **Client receives**: Multiple response messages asynchronously
- **Use cases**: Real-time data feeds, large dataset consumption, progressive results processing

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
    ```

### Regenerate Protocol Buffer Code

After updating the proto file, regenerate the code:

```bash
# Regenerate protobuf classes
./gradlew generateProto

# Build the project
./gradlew build
```

### Implement Server Streaming Client

Now let's implement the client-side server streaming functionality:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/client/UserClientService.java`:

    ```java
    package ru.tinkoff.kora.example.client;

    import io.grpc.stub.StreamObserver;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.*;
    import ru.tinkoff.kora.grpc.client.GrpcClient;

    import java.util.List;
    import java.util.concurrent.CompletableFuture;
    import java.util.concurrent.CopyOnWriteArrayList;

    @Component
    public final class UserClientService {

        private static final Logger logger = LoggerFactory.getLogger(UserClientService.class);
        private final UserServiceGrpc.UserServiceBlockingStub blockingStub;
        private final UserServiceGrpc.UserServiceStub asyncStub;

        public UserClientService(
            @GrpcClient("userService") UserServiceGrpc.UserServiceBlockingStub blockingStub,
            @GrpcClient("userService") UserServiceGrpc.UserServiceStub asyncStub) {
            this.blockingStub = blockingStub;
            this.asyncStub = asyncStub;
        }

        // ...existing code...

        /**
         * Streams all users from the server using server streaming.
         * Returns a CompletableFuture that completes when streaming is finished.
         */
        public CompletableFuture<List<UserResponse>> streamAllUsers() {
            logger.info("Starting server streaming to get all users");

            CompletableFuture<List<UserResponse>> future = new CompletableFuture<>();
            List<UserResponse> users = new CopyOnWriteArrayList<>();

            // Create a StreamObserver to handle responses
            StreamObserver<UserResponse> responseObserver = new StreamObserver<>() {
                @Override
                public void onNext(UserResponse user) {
                    logger.info("Received user via streaming: id={}, name={}", user.getId(), user.getName());
                    users.add(user);
                }

                @Override
                public void onError(Throwable throwable) {
                    logger.error("Error during server streaming", throwable);
                    future.completeExceptionally(throwable);
                }

                @Override
                public void onCompleted() {
                    logger.info("Server streaming completed, received {} users", users.size());
                    future.complete(users);
                }
            };

            try {
                // Initiate the server streaming call
                asyncStub.getAllUsers(google.protobuf.Empty.getDefaultInstance(), responseObserver);
            } catch (Exception e) {
                logger.error("Failed to initiate server streaming", e);
                future.completeExceptionally(e);
            }

            return future;
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/client/UserClientService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.client

    import io.grpc.stub.StreamObserver
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.*
    import ru.tinkoff.kora.grpc.client.GrpcClient
    import java.util.concurrent.CompletableFuture
    import java.util.concurrent.CopyOnWriteArrayList

    @Component
    class UserClientService(
        @GrpcClient("userService")
        private val blockingStub: UserServiceGrpc.UserServiceBlockingStub,
        @GrpcClient("userService")
        private val asyncStub: UserServiceGrpc.UserServiceStub
    ) {

        private val logger = LoggerFactory.getLogger(UserClientService::class.java)

        // ...existing code...

        /**
         * Streams all users from the server using server streaming.
         * Returns a CompletableFuture that completes when streaming is finished.
         */
        fun streamAllUsers(): CompletableFuture<List<UserResponse>> {
            logger.info("Starting server streaming to get all users")

            val future = CompletableFuture<List<UserResponse>>()
            val users = CopyOnWriteArrayList<UserResponse>()

            // Create a StreamObserver to handle responses
            val responseObserver = object : StreamObserver<UserResponse> {
                override fun onNext(user: UserResponse) {
                    logger.info("Received user via streaming: id={}, name={}", user.id, user.name)
                    users.add(user)
                }

                override fun onError(throwable: Throwable) {
                    logger.error("Error during server streaming", throwable)
                    future.completeExceptionally(throwable)
                }

                override fun onCompleted() {
                    logger.info("Server streaming completed, received {} users", users.size)
                    future.complete(users)
                }
            }

            try {
                // Initiate the server streaming call
                asyncStub.getAllUsers(com.google.protobuf.Empty.getDefaultInstance(), responseObserver)
            } catch (e: Exception) {
                logger.error("Failed to initiate server streaming", e)
                future.completeExceptionally(e)
            }

            return future
        }
    }
    ```

### Key Concepts in Server Streaming Client

#### StreamObserver Pattern
- **`onNext(UserResponse)`**: Called for each message received from the server
- **`onError(Throwable)`**: Called when an error occurs during streaming
- **`onCompleted()`**: Called when the server finishes streaming

#### Asynchronous Processing
- **Non-blocking**: Client can continue processing while receiving data
- **Backpressure**: Natural backpressure through StreamObserver buffering
- **Resource Management**: Automatic cleanup when streaming completes

#### Error Handling
- **Network errors**: Connection failures, timeouts
- **Server errors**: gRPC status codes from the server
- **Processing errors**: Exceptions during message processing

## Step 2: Adding Client Streaming Client (CreateUsers)

Client streaming enables clients to send multiple requests to a server, which processes them and returns a single response. This pattern is ideal for batch operations and real-time data ingestion.

### Understanding Client Streaming Client

In client streaming:
- **Client sends**: Multiple request messages
- **Client receives**: One final response message
- **Use cases**: Batch operations, file uploads, real-time data ingestion

**Protocol Buffer Syntax**:
```protobuf
rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);
```

### Update Protocol Buffers for Client Streaming

Add the client streaming method and required message types:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/proto/user_service.proto`:

    ```protobuf
    // Service definition - contains all RPC methods
    service UserService {
      // ...existing code...

      // Client streaming: Send multiple user creation requests
      rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse) {}
    }

    // Message definitions - data structures for requests and responses
    // ...existing code...

    // Response message for batch user creation
    message CreateUsersResponse {
      int32 created_count = 1;
      repeated string created_ids = 2;
      repeated string errors = 3;
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/proto/user_service.proto`:

    ```protobuf
    // Service definition - contains all RPC methods
    service UserService {
      // ...existing code...

      // Client streaming: Send multiple user creation requests
      rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse) {}
    }

    // Message definitions - data structures for requests and responses
    // ...existing code...

    // Response message for batch user creation
    message CreateUsersResponse {
      int32 created_count = 1;
      repeated string created_ids = 2;
      repeated string errors = 3;
    }
    ```

### Regenerate and Implement Client Streaming

Regenerate the protobuf code and implement the client streaming functionality:

```bash
# Regenerate protobuf classes
./gradlew generateProto

# Build the project
./gradlew build
```

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/client/UserClientService.java`:

    ```java
    // ...existing code...

    /**
     * Creates multiple users using client streaming.
     * Sends multiple CreateUserRequest messages and receives one CreateUsersResponse.
     */
    public CompletableFuture<CreateUsersResponse> createUsersBatch(List<CreateUserRequest> userRequests) {
        logger.info("Starting client streaming to create {} users", userRequests.size());

        CompletableFuture<CreateUsersResponse> future = new CompletableFuture<>();

        // Create a StreamObserver to handle the response
        StreamObserver<CreateUsersResponse> responseObserver = new StreamObserver<>() {
            @Override
            public void onNext(CreateUsersResponse response) {
                logger.info("Batch creation completed: {} users created", response.getCreatedCount());
                future.complete(response);
            }

            @Override
            public void onError(Throwable throwable) {
                logger.error("Error during client streaming batch creation", throwable);
                future.completeExceptionally(throwable);
            }

            @Override
            public void onCompleted() {
                logger.debug("Client streaming response completed");
            }
        };

        // Initiate the client streaming call and get the request observer
        StreamObserver<CreateUserRequest> requestObserver = asyncStub.createUsers(responseObserver);

        try {
            // Send all user creation requests
            for (CreateUserRequest request : userRequests) {
                logger.debug("Sending user creation request: {}", request.getName());
                requestObserver.onNext(request);

                // Add small delay to simulate real-world batch processing
                Thread.sleep(10);
            }

            // Signal that we're done sending requests
            requestObserver.onCompleted();

        } catch (Exception e) {
            logger.error("Failed to send batch creation requests", e);
            requestObserver.onError(e);
            future.completeExceptionally(e);
        }

        return future;
    }

    // ...existing code...
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/client/UserClientService.kt`:

    ```kotlin
    // ...existing code...

    /**
     * Creates multiple users using client streaming.
     * Sends multiple CreateUserRequest messages and receives one CreateUsersResponse.
     */
    fun createUsersBatch(userRequests: List<CreateUserRequest>): CompletableFuture<CreateUsersResponse> {
        logger.info("Starting client streaming to create {} users", userRequests.size)

        val future = CompletableFuture<CreateUsersResponse>()

        // Create a StreamObserver to handle the response
        val responseObserver = object : StreamObserver<CreateUsersResponse> {
            override fun onNext(response: CreateUsersResponse) {
                logger.info("Batch creation completed: {} users created", response.createdCount)
                future.complete(response)
            }

            override fun onError(throwable: Throwable) {
                logger.error("Error during client streaming batch creation", throwable)
                future.completeExceptionally(throwable)
            }

            override fun onCompleted() {
                logger.debug("Client streaming response completed")
            }
        }

        // Initiate the client streaming call and get the request observer
        val requestObserver = asyncStub.createUsers(responseObserver)

        try {
            // Send all user creation requests
            for (request in userRequests) {
                logger.debug("Sending user creation request: {}", request.name)
                requestObserver.onNext(request)

                // Add small delay to simulate real-world batch processing
                Thread.sleep(10)
            }

            // Signal that we're done sending requests
            requestObserver.onCompleted()

        } catch (e: Exception) {
            logger.error("Failed to send batch creation requests", e)
            requestObserver.onError(e)
            future.completeExceptionally(e)
        }

        return future
    }

    // ...existing code...
    ```

### Key Concepts in Client Streaming Client

#### Request StreamObserver
- **`onNext(CreateUserRequest)`**: Send each request to the server
- **`onCompleted()`**: Signal end of request stream
- **`onError(Throwable)`**: Handle errors during sending

#### Response Handling
- **Single Response**: Only one response message expected
- **Batch Results**: Contains summary of all operations
- **Error Aggregation**: Collects errors from individual operations

#### Flow Control
- **Backpressure**: Server can signal when to slow down
- **Cancellation**: Can cancel the operation mid-stream
- **Timeouts**: Configurable timeouts for long-running operations

## Step 3: Adding Bidirectional Streaming Client (UpdateUsers)

Bidirectional streaming provides full-duplex communication where both client and server can send multiple messages independently. This advanced pattern supports real-time collaboration and complex interactive workflows.

### Understanding Bidirectional Streaming Client

In bidirectional streaming:
- **Client sends**: Multiple request messages asynchronously
- **Client receives**: Multiple response messages asynchronously
- **Use cases**: Real-time collaboration, interactive data processing, live chat

**Protocol Buffer Syntax**:
```protobuf
rpc UpdateUsers(stream UserUpdate) returns (stream UserResponse);
```

### Update Protocol Buffers for Bidirectional Streaming

Add the bidirectional streaming method and required message types:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/proto/user_service.proto`:

    ```protobuf
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
      UpdateOperation operation = 2;
      UserUpdateData data = 3;
    }

    // Enumeration for update operations
    enum UpdateOperation {
      UPDATE_NAME = 0;
      UPDATE_EMAIL = 1;
      UPDATE_STATUS = 2;
    }

    // Data payload for user updates
    message UserUpdateData {
      optional string name = 1;
      optional string email = 2;
      optional UserStatus status = 3;
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/proto/user_service.proto`:

    ```protobuf
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
      UpdateOperation operation = 2;
      UserUpdateData data = 3;
    }

    // Enumeration for update operations
    enum UpdateOperation {
      UPDATE_NAME = 0;
      UPDATE_EMAIL = 1;
      UPDATE_STATUS = 2;
    }

    // Data payload for user updates
    message UserUpdateData {
      optional string name = 1;
      optional string email = 2;
      optional UserStatus status = 3;
    }
    ```

### Implement Bidirectional Streaming Client

Regenerate the protobuf code and implement the bidirectional streaming functionality:

```bash
# Regenerate protobuf classes
./gradlew generateProto

# Build the project
./gradlew build
```

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/client/UserClientService.java`:

    ```java
    // ...existing code...

    /**
     * Performs real-time user updates using bidirectional streaming.
     * Can send multiple update requests and receive multiple responses asynchronously.
     */
    public StreamObserver<UserUpdate> startUserUpdates(StreamObserver<UserResponse> responseHandler) {
        logger.info("Starting bidirectional streaming for user updates");

        // Create a StreamObserver to handle responses from server
        StreamObserver<UserResponse> serverResponseObserver = new StreamObserver<>() {
            @Override
            public void onNext(UserResponse user) {
                logger.info("Received updated user: id={}, name={}, status={}",
                    user.getId(), user.getName(), user.getStatus());
                responseHandler.onNext(user);
            }

            @Override
            public void onError(Throwable throwable) {
                logger.error("Error in bidirectional streaming", throwable);
                responseHandler.onError(throwable);
            }

            @Override
            public void onCompleted() {
                logger.info("Bidirectional streaming completed");
                responseHandler.onCompleted();
            }
        };

        // Initiate bidirectional streaming and return the request observer
        return asyncStub.updateUsers(serverResponseObserver);
    }

    // ...existing code...
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/client/UserClientService.kt`:

    ```kotlin
    // ...existing code...

    /**
     * Performs real-time user updates using bidirectional streaming.
     * Can send multiple update requests and receive multiple responses asynchronously.
     */
    fun startUserUpdates(responseHandler: StreamObserver<UserResponse>): StreamObserver<UserUpdate> {
        logger.info("Starting bidirectional streaming for user updates")

        // Create a StreamObserver to handle responses from server
        val serverResponseObserver = object : StreamObserver<UserResponse> {
            override fun onNext(user: UserResponse) {
                logger.info("Received updated user: id={}, name={}, status={}",
                    user.id, user.name, user.status)
                responseHandler.onNext(user)
            }

            override fun onError(throwable: Throwable) {
                logger.error("Error in bidirectional streaming", throwable)
                responseHandler.onError(throwable)
            }

            override fun onCompleted() {
                logger.info("Bidirectional streaming completed")
                responseHandler.onCompleted()
            }
        }

        // Initiate bidirectional streaming and return the request observer
        return asyncStub.updateUsers(serverResponseObserver)
    }

    // ...existing code...
    ```

### Key Concepts in Bidirectional Streaming Client

#### Independent Streams
- **Request Stream**: Client can send updates at any time
- **Response Stream**: Server can send responses at any time
- **Full Duplex**: Both streams operate independently

#### Real-time Communication
- **Live Updates**: Immediate response to changes
- **State Synchronization**: Keep client and server in sync
- **Interactive Workflows**: Complex multi-step operations

#### Resource Management
- **Connection Lifecycle**: Long-lived connections for real-time features
- **Cleanup**: Proper stream closure and resource cleanup
- **Error Recovery**: Handle network interruptions gracefully

## Step 4: Advanced Client Application

Create an advanced client application that demonstrates all streaming patterns:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/client/UserClientApplication.java`:

    ```java
    package ru.tinkoff.kora.example.client;

    import io.grpc.stub.StreamObserver;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Root;
    import ru.tinkoff.kora.example.*;

    import java.util.Arrays;
    import java.util.List;
    import java.util.concurrent.CompletableFuture;

    @Root
    public final class UserClientApplication {

        private static final Logger logger = LoggerFactory.getLogger(UserClientApplication.class);
        private final UserClientService userClientService;

        public UserClientApplication(UserClientService userClientService) {
            this.userClientService = userClientService;
        }

        /**
         * Demonstrates all advanced gRPC client operations.
         */
        public void runAdvancedClientDemo() {
            logger.info("Starting advanced gRPC client demo...");

            try {
                // 1. Server Streaming Demo
                demonstrateServerStreaming();

                // 2. Client Streaming Demo
                demonstrateClientStreaming();

                // 3. Bidirectional Streaming Demo
                demonstrateBidirectionalStreaming();

                logger.info("Advanced gRPC client demo completed successfully!");

            } catch (Exception e) {
                logger.error("Error during advanced client demo", e);
            }
        }

        private void demonstrateServerStreaming() throws Exception {
            logger.info("=== Demonstrating Server Streaming ===");

            // Stream all users from server
            CompletableFuture<List<UserResponse>> future = userClientService.streamAllUsers();
            List<UserResponse> users = future.get(); // Wait for completion

            logger.info("Server streaming demo completed: received {} users", users.size());
        }

        private void demonstrateClientStreaming() throws Exception {
            logger.info("=== Demonstrating Client Streaming ===");

            // Create batch of users
            List<CreateUserRequest> batchRequests = Arrays.asList(
                CreateUserRequest.newBuilder().setName("Alice Johnson").setEmail("alice@example.com").build(),
                CreateUserRequest.newBuilder().setName("Bob Smith").setEmail("bob@example.com").build(),
                CreateUserRequest.newBuilder().setName("Carol Williams").setEmail("carol@example.com").build()
            );

            // Send batch creation request
            CompletableFuture<CreateUsersResponse> future = userClientService.createUsersBatch(batchRequests);
            CreateUsersResponse response = future.get(); // Wait for completion

            logger.info("Client streaming demo completed: created {} users", response.getCreatedCount());
        }

        private void demonstrateBidirectionalStreaming() throws Exception {
            logger.info("=== Demonstrating Bidirectional Streaming ===");

            // Create a response handler for the bidirectional stream
            StreamObserver<UserResponse> responseHandler = new StreamObserver<>() {
                @Override
                public void onNext(UserResponse user) {
                    logger.info("Bidirectional response: Updated user {} - {}", user.getId(), user.getName());
                }

                @Override
                public void onError(Throwable throwable) {
                    logger.error("Bidirectional streaming error", throwable);
                }

                @Override
                public void onCompleted() {
                    logger.info("Bidirectional streaming finished");
                }
            };

            // Start bidirectional streaming
            StreamObserver<UserUpdate> requestObserver = userClientService.startUserUpdates(responseHandler);

            // Send some update requests
            List<UserUpdate> updates = Arrays.asList(
                createUserUpdate("user-1", UpdateOperation.UPDATE_NAME,
                    UserUpdateData.newBuilder().setName("Updated Alice").build()),
                createUserUpdate("user-2", UpdateOperation.UPDATE_EMAIL,
                    UserUpdateData.newBuilder().setEmail("updated.bob@example.com").build())
            );

            for (UserUpdate update : updates) {
                logger.info("Sending update: {} for user {}", update.getOperation(), update.getUserId());
                requestObserver.onNext(update);
                Thread.sleep(100); // Small delay between updates
            }

            // Complete the request stream
            requestObserver.onCompleted();

            // Wait a bit for responses
            Thread.sleep(1000);

            logger.info("Bidirectional streaming demo completed");
        }

        private UserUpdate createUserUpdate(String userId, UpdateOperation operation, UserUpdateData data) {
            return UserUpdate.newBuilder()
                .setUserId(userId)
                .setOperation(operation)
                .setData(data)
                .build();
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/client/UserClientApplication.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.client

    import io.grpc.stub.StreamObserver
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Root
    import ru.tinkoff.kora.example.*
    import java.util.concurrent.CompletableFuture

    @Root
    class UserClientApplication(
        private val userClientService: UserClientService
    ) {

        private val logger = LoggerFactory.getLogger(UserClientApplication::class.java)

        /**
         * Demonstrates all advanced gRPC client operations.
         */
        fun runAdvancedClientDemo() {
            logger.info("Starting advanced gRPC client demo...")

            try {
                // 1. Server Streaming Demo
                demonstrateServerStreaming()

                // 2. Client Streaming Demo
                demonstrateClientStreaming()

                // 3. Bidirectional Streaming Demo
                demonstrateBidirectionalStreaming()

                logger.info("Advanced gRPC client demo completed successfully!")

            } catch (e: Exception) {
                logger.error("Error during advanced client demo", e)
            }
        }

        private fun demonstrateServerStreaming() {
            logger.info("=== Demonstrating Server Streaming ===")

            // Stream all users from server
            val future = userClientService.streamAllUsers()
            val users = future.get() // Wait for completion

            logger.info("Server streaming demo completed: received {} users", users.size)
        }

        private fun demonstrateClientStreaming() {
            logger.info("=== Demonstrating Client Streaming ===")

            // Create batch of users
            val batchRequests = listOf(
                CreateUserRequest.newBuilder().setName("Alice Johnson").setEmail("alice@example.com").build(),
                CreateUserRequest.newBuilder().setName("Bob Smith").setEmail("bob@example.com").build(),
                CreateUserRequest.newBuilder().setName("Carol Williams").setEmail("carol@example.com").build()
            )

            // Send batch creation request
            val future = userClientService.createUsersBatch(batchRequests)
            val response = future.get() // Wait for completion

            logger.info("Client streaming demo completed: created {} users", response.createdCount)
        }

        private fun demonstrateBidirectionalStreaming() {
            logger.info("=== Demonstrating Bidirectional Streaming ===")

            // Create a response handler for the bidirectional stream
            val responseHandler = object : StreamObserver<UserResponse> {
                override fun onNext(user: UserResponse) {
                    logger.info("Bidirectional response: Updated user {} - {}", user.id, user.name)
                }

                override fun onError(throwable: Throwable) {
                    logger.error("Bidirectional streaming error", throwable)
                }

                override fun onCompleted() {
                    logger.info("Bidirectional streaming finished")
                }
            }

            // Start bidirectional streaming
            val requestObserver = userClientService.startUserUpdates(responseHandler)

            // Send some update requests
            val updates = listOf(
                createUserUpdate("user-1", UpdateOperation.UPDATE_NAME,
                    UserUpdateData.newBuilder().setName("Updated Alice").build()),
                createUserUpdate("user-2", UpdateOperation.UPDATE_EMAIL,
                    UserUpdateData.newBuilder().setEmail("updated.bob@example.com").build())
            )

            for (update in updates) {
                logger.info("Sending update: {} for user {}", update.operation, update.userId)
                requestObserver.onNext(update)
                Thread.sleep(100) // Small delay between updates
            }

            // Complete the request stream
            requestObserver.onCompleted()

            // Wait a bit for responses
            Thread.sleep(1000)

            logger.info("Bidirectional streaming demo completed")
        }

        private fun createUserUpdate(userId: String, operation: UpdateOperation, data: UserUpdateData): UserUpdate {
            return UserUpdate.newBuilder()
                .setUserId(userId)
                .setOperation(operation)
                .setData(data)
                .build()
        }
    }
    ```

## Build and Run Advanced Client

Generate protobuf classes and run the advanced client application:

```bash
# Generate protobuf classes
./gradlew generateProto

# Build the client application
./gradlew build

# Run the client application
./gradlew run
```

## Test the Advanced gRPC Client

Test your advanced gRPC client by ensuring the advanced server is running and then running the client demo:

### Prerequisites for Testing

1. **Start the Advanced gRPC Server**: Make sure the advanced server from the [gRPC Server Advanced guide](grpc-server-advanced.md) is running on `localhost:9090`
2. **Verify Server Health**: Test that the server is responding:

```bash
# Test server connectivity
grpcurl -plaintext localhost:9090 ru.tinkoff.kora.example.UserService/GetAllUsers
```

### Run Advanced Client Demo

Once the advanced server is running, you can run the client demo:

```bash
# Run the client application
./gradlew run
```

The client will demonstrate:
1. **Server Streaming**: Stream all users from the server
2. **Client Streaming**: Create multiple users in a batch
3. **Bidirectional Streaming**: Perform real-time user updates

### Expected Output

```
INFO  UserClientApplication - Starting advanced gRPC client demo...
INFO  UserClientApplication - === Demonstrating Server Streaming ===
INFO  UserClientService - Starting server streaming to get all users
INFO  UserClientService - Received user via streaming: id=user-1, name=John Doe
INFO  UserClientService - Received user via streaming: id=user-2, name=Jane Smith
INFO  UserClientService - Server streaming completed, received 2 users
INFO  UserClientApplication - Server streaming demo completed: received 2 users
INFO  UserClientApplication - === Demonstrating Client Streaming ===
INFO  UserClientService - Starting client streaming to create 3 users
INFO  UserClientService - Batch creation completed: 3 users created
INFO  UserClientApplication - Client streaming demo completed: created 3 users
INFO  UserClientApplication - === Demonstrating Bidirectional Streaming ===
INFO  UserClientService - Starting bidirectional streaming for user updates
INFO  UserClientService - Received updated user: id=user-1, name=Updated Alice, status=ACTIVE
INFO  UserClientService - Received updated user: id=user-2, name=Bob Smith, status=ACTIVE
INFO  UserClientApplication - Bidirectional streaming demo completed
INFO  UserClientApplication - Advanced gRPC client demo completed successfully!
```

## Key Concepts Learned

### Advanced Streaming Patterns

#### Server Streaming Client
- **Asynchronous Consumption**: Process streaming data as it arrives
- **Memory Management**: Handle large datasets efficiently
- **Real-time Processing**: React to streaming data immediately

#### Client Streaming Client
- **Batch Operations**: Send multiple related requests efficiently
- **Flow Control**: Manage request pacing and server load
- **Aggregated Responses**: Handle summary responses for batch operations

#### Bidirectional Streaming Client
- **Full Duplex Communication**: Independent request and response streams
- **Real-time Collaboration**: Support for live, interactive workflows
- **State Synchronization**: Maintain consistency between client and server

### Production Considerations

#### Connection Management
- **Connection Pooling**: Reuse connections for better performance
- **Health Checks**: Monitor connection health and reconnect when needed
- **Load Balancing**: Distribute requests across multiple server instances

#### Error Handling and Recovery
- **Retry Logic**: Automatic retry for transient failures
- **Circuit Breakers**: Prevent cascading failures
- **Graceful Degradation**: Continue operating when some features fail

#### Performance Optimization
- **Message Batching**: Reduce network overhead with larger messages
- **Compression**: Enable message compression for large payloads
- **Keep-alive**: Maintain long-lived connections for streaming

## What's Next?

- [gRPC Interceptors and Middleware](grpc-interceptors.md)
- [Service Discovery and Load Balancing](service-discovery.md)
- [Circuit Breaker Pattern](resilience.md)
- [Distributed Tracing](observability-tracing.md)
- [gRPC Performance Tuning](grpc-performance.md)

## Help

If you encounter issues:

- Check the [gRPC Client Documentation](../../documentation/grpc-client.md)
- Verify the advanced server from [gRPC Server Advanced guide](grpc-server-advanced.md) is running
- Check client configuration in `application.conf`
- Test server connectivity with grpcurl
- Review streaming patterns and error handling
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)