---
search:
  exclude: true
title: Advanced gRPC Server with Kora
summary: Extend a Kora gRPC server with streaming RPCs, server interceptors, API-key auth, and reflection
tags: grpc-server, protobuf, streaming, interceptors, reflection, authentication
---

# Advanced gRPC Server with Kora { #advanced-grpc-server-kora }

This guide introduces advanced gRPC server capabilities in Kora. It covers server streaming, client streaming, bidirectional streaming, service-level interceptors, metadata-based authorization, and
reflection for local tooling. You will also see how streaming handlers use observers and completion signals while unary services remain available in the same application graph.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-grpc-server-advanced-app).

## What You'll Build { #youll-build }

You will extend the gRPC server application with:

- a second protobuf service, `UserStreamingService`, separate from the unary CRUD service
- `GetAllUsers` as a server-streaming RPC
- `CreateUsers` as a client-streaming RPC
- `UpdateUsers` as a bidirectional-streaming RPC
- a Kora gRPC handler that uses observers, completion signals, and stream error handling
- a server-side logging interceptor
- metadata-based API-key authorization for the streaming service
- gRPC reflection enabled for local exploration with tools such as `grpcurl`

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Optional: `grpcurl` for reflection and manual streaming checks

## Prerequisites { #prerequisites }

!!! note "Required: Complete Base gRPC Server Guide"

    This guide assumes you have completed **[gRPC Server with Kora](grpc-server.md)** and **[HTTP Server Advanced](http-server-advanced.md)**, and already understand unary gRPC handlers, protobuf code generation, and the repository/service separation used across the guides.

    If you haven't completed the base gRPC server guide yet, do that first, because this guide keeps the unary service stable and adds streaming, reflection, interceptors, and metadata authorization around it.

## Overview { #overview }

The most important design choice in this guide is that we **do not overload the original unary service** with every advanced concept.

Instead:

- `UserService` stays the familiar unary CRUD service
- `UserStreamingService` becomes a separate advanced service in the `.proto` contract
- `UserStreamingServiceGrpcHandler` focuses only on streaming operations

That separation makes the guide easier to learn and mirrors a common production pattern: keep the basic synchronous API stable, and add specialized streaming APIs only where they actually help.

Kora still owns component wiring and lifecycle. gRPC owns the RPC protocol and generated service contracts. Your code sits between them: it implements generated service methods, injects ordinary Kora
components, and translates streaming callbacks into application behavior.

The advanced pieces in this guide have different responsibilities:

- streaming changes the shape and lifetime of an RPC call
- interceptors add cross-cutting behavior around calls
- reflection exposes service metadata to tools such as `grpcurl`
- metadata authorization reads request metadata before business logic runs

Those features are all transport-level concerns. They are important, but they should not force the repository or service layer to become aware of gRPC internals. The service layer should still talk in
application terms: users, requests, responses, and business rules. The gRPC handler is the adapter that turns generated protobuf messages and streaming callbacks into those application operations.

That separation matters more in streaming code than in unary code. A unary handler receives one request, calls a service method, and returns one response. A streaming handler owns a longer-lived
interaction:

- it can send several responses before completing
- it can receive several requests before producing a final answer
- it must decide when to call `onNext`, `onCompleted`, or `onError`
- it must keep cancellation, backpressure, and partial failure in mind

The guide keeps the implementation intentionally small, but the architecture mirrors production code: keep the stable unary API intact, add a separate streaming service, and place advanced gRPC
mechanics at the edge of the application.

### Why gRPC Streaming Exists { #grpc-streaming-exists }

Unary RPC is great when one request naturally produces one response.

But sometimes the transport itself should express a different conversation shape:

- one request, many responses
- many requests, one response
- many requests, many responses

That is exactly what streaming gives you.

### Server Streaming { #server-streaming }

The client sends one request, and the server sends back many messages.

This is useful when:

- you want to stream a large result set
- the client can start consuming results immediately
- the data naturally arrives as a sequence

### Client Streaming { #client-streaming }

The client sends many messages, and the server answers once at the end.

This is useful when:

- the client is batching operations
- the server should aggregate work before replying
- one summary response is more useful than many small acknowledgements

### Bidirectional Streaming { #bidirectional-streaming }

The client and server both exchange multiple messages on the same call.

This is useful when:

- the conversation is interactive
- updates should flow both ways
- one side should not wait for the other to finish sending everything first

## Immutable { #immutable }

Before adding anything new, keep in mind what does **not** change:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`
- unary `UserServiceGrpcHandler`

That is intentional. Advanced features should extend the application, not force you to rewrite the basic path you already trust.

## Protobuf API { #protobuf-api }

Now extend the contract by adding a second service instead of mixing everything into the original one.

??? example "Protobuf contract"

    ```protobuf title="src/main/proto/user_service.proto"
    syntax = "proto3";
    
    package ru.tinkoff.kora.guide.grpcserver.advanced;
    option java_multiple_files = true;
    
    import "google/protobuf/empty.proto";
    import "google/protobuf/timestamp.proto";
    
    service UserService {
      rpc CreateUser(CreateUserRequest) returns (UserResponse) {}
      rpc GetUser(GetUserRequest) returns (UserResponse) {}
      rpc GetUsers(GetUsersRequest) returns (GetUsersResponse) {}
      rpc UpdateUser(UpdateUserRequestUnary) returns (UserResponse) {}
      rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty) {}
    }
    
    service UserStreamingService {
      rpc GetAllUsers(google.protobuf.Empty) returns (stream UserResponse) {}
      rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse) {}
      rpc UpdateUsers(stream UpdateUserRequest) returns (stream UserResponse) {}
    }
    
    message CreateUserRequest {
      string name = 1;
      string email = 2;
    }
    
    message GetUserRequest {
      string user_id = 1;
    }
    
    message GetUsersRequest {
      int32 page = 1;
      int32 size = 2;
      string sort = 3;
    }
    
    message GetUsersResponse {
      repeated UserResponse users = 1;
    }
    
    message UpdateUserRequestUnary {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }
    
    message DeleteUserRequest {
      string user_id = 1;
    }
    
    message UpdateUserRequest {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }
    
    message CreateUsersResponse {
      int32 created_count = 1;
      repeated string user_ids = 2;
    }
    
    message UserResponse {
      string id = 1;
      string name = 2;
      string email = 3;
      google.protobuf.Timestamp created_at = 4;
    }
    ```

This shape is important for teaching:

- `UserService` still looks like the HTTP CRUD API
- `UserStreamingService` becomes the clearly advanced part

## Streaming Service { #streaming-service }

Just like we split the transport contract, we also split the application logic.

The advanced module introduces:

- `UserStreamingService`

This service owns the logic behind:

- returning all users for server streaming
- creating many users for client streaming
- updating users for bidirectional streaming

That keeps the original `UserService` close to the HTTP guide and prevents it from turning into a transport-specific god class.

## Streaming Handler { #streaming-handler }

Now connect the generated streaming service to the new application service.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/UserStreamingServiceGrpcHandler.java"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc;

    import com.google.protobuf.Empty;
    import com.google.protobuf.Timestamp;
    import io.grpc.Status;
    import io.grpc.StatusRuntimeException;
    import io.grpc.stub.StreamObserver;
    import java.time.ZoneOffset;
    import java.util.ArrayList;
    import java.util.List;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUsersResponse;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UpdateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc;
    import ru.tinkoff.kora.guide.grpcserver.advanced.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.service.UserStreamingService;

    @Component
    public final class UserStreamingServiceGrpcHandler extends UserStreamingServiceGrpc.UserStreamingServiceImplBase {

        private static final Logger logger = LoggerFactory.getLogger(UserStreamingServiceGrpcHandler.class);

        private final UserStreamingService userStreamingService;

        public UserStreamingServiceGrpcHandler(UserStreamingService userStreamingService) {
            this.userStreamingService = userStreamingService;
        }

        @Override
        public void getAllUsers(Empty request, StreamObserver<UserResponse> responseObserver) {
            try {
                for (var user : userStreamingService.getAllUsers()) {
                    responseObserver.onNext(toGrpcUser(user));
                }
                responseObserver.onCompleted();
            } catch (Exception e) {
                responseObserver.onError(Status.INTERNAL.withDescription("Failed to stream users").withCause(e).asRuntimeException());
            }
        }

        @Override
        public StreamObserver<CreateUserRequest> createUsers(StreamObserver<CreateUsersResponse> responseObserver) {
            return new StreamObserver<>() {
                private final List<UserRequest> requests = new ArrayList<>();

                @Override
                public void onNext(CreateUserRequest value) {
                    requests.add(new UserRequest(value.getName(), value.getEmail()));
                }

                @Override
                public void onError(Throwable t) {
                    logger.error("Client streaming failed", t);
                    responseObserver.onError(t);
                }

                @Override
                public void onCompleted() {
                    try {
                        var createdUsers = userStreamingService.createUsers(requests);
                        responseObserver.onNext(CreateUsersResponse.newBuilder()
                                .setCreatedCount(createdUsers.size())
                                .addAllUserIds(createdUsers.stream().map(ru.tinkoff.kora.guide.grpcserver.advanced.dto.UserResponse::id).toList())
                                .build());
                        responseObserver.onCompleted();
                    } catch (Exception e) {
                        responseObserver.onError(Status.INTERNAL.withDescription("Failed to create users").withCause(e).asRuntimeException());
                    }
                }
            };
        }

        @Override
        public StreamObserver<UpdateUserRequest> updateUsers(StreamObserver<UserResponse> responseObserver) {
            return new StreamObserver<>() {
                @Override
                public void onNext(UpdateUserRequest value) {
                    try {
                        var user = userStreamingService.tryUpdateUser(value.getUserId(), new UserRequest(value.getName(), value.getEmail()))
                                .orElseThrow(() -> Status.NOT_FOUND.withDescription("User not found: " + value.getUserId()).asRuntimeException());
                        responseObserver.onNext(toGrpcUser(user));
                    } catch (StatusRuntimeException e) {
                        responseObserver.onError(e);
                    }
                }

                @Override
                public void onError(Throwable t) {
                    logger.error("Bidirectional streaming failed", t);
                    responseObserver.onError(t);
                }

                @Override
                public void onCompleted() {
                    responseObserver.onCompleted();
                }
            };
        }

        private UserResponse toGrpcUser(ru.tinkoff.kora.guide.grpcserver.advanced.dto.UserResponse user) {
            return UserResponse.newBuilder()
                    .setId(user.id())
                    .setName(user.name())
                    .setEmail(user.email())
                    .setCreatedAt(Timestamp.newBuilder()
                            .setSeconds(user.createdAt().toEpochSecond(ZoneOffset.UTC))
                            .setNanos(user.createdAt().getNano())
                            .build())
                    .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/UserStreamingServiceGrpcHandler.kt"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc

    import com.google.protobuf.Empty
    import io.grpc.Status
    import io.grpc.StatusRuntimeException
    import io.grpc.stub.StreamObserver
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUsersResponse
    import ru.tinkoff.kora.guide.grpcserver.advanced.UpdateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc
    import ru.tinkoff.kora.guide.grpcserver.advanced.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.service.UserStreamingService

    @Component
    class UserStreamingServiceGrpcHandler(
        private val userStreamingService: UserStreamingService
    ) : UserStreamingServiceGrpc.UserStreamingServiceImplBase() {

        private val logger = LoggerFactory.getLogger(UserStreamingServiceGrpcHandler::class.java)

        override fun getAllUsers(
            request: Empty,
            responseObserver: StreamObserver<ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse>
        ) {
            try {
                userStreamingService.getAllUsers().forEach { responseObserver.onNext(it.toGrpcUser()) }
                responseObserver.onCompleted()
            } catch (e: Exception) {
                responseObserver.onError(
                    Status.INTERNAL.withDescription("Failed to stream users").withCause(e).asRuntimeException()
                )
            }
        }

        override fun createUsers(responseObserver: StreamObserver<CreateUsersResponse>): StreamObserver<CreateUserRequest> {
            return object : StreamObserver<CreateUserRequest> {
                private val requests = mutableListOf<UserRequest>()

                override fun onNext(value: CreateUserRequest) {
                    requests += UserRequest(value.name, value.email)
                }

                override fun onError(t: Throwable) {
                    logger.error("Client streaming failed", t)
                    responseObserver.onError(t)
                }

                override fun onCompleted() {
                    try {
                        val createdUsers = userStreamingService.createUsers(requests)
                        responseObserver.onNext(
                            CreateUsersResponse.newBuilder()
                                .setCreatedCount(createdUsers.size)
                                .addAllUserIds(createdUsers.map { it.id })
                                .build()
                        )
                        responseObserver.onCompleted()
                    } catch (e: Exception) {
                        responseObserver.onError(
                            Status.INTERNAL.withDescription("Failed to create users").withCause(e).asRuntimeException()
                        )
                    }
                }
            }
        }

        override fun updateUsers(responseObserver: StreamObserver<ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse>): StreamObserver<UpdateUserRequest> {
            return object : StreamObserver<UpdateUserRequest> {
                override fun onNext(value: UpdateUserRequest) {
                    try {
                        val user = userStreamingService.tryUpdateUser(value.userId, UserRequest(value.name, value.email))
                            ?: throw Status.NOT_FOUND.withDescription("User not found: ${value.userId}")
                                .asRuntimeException()
                        responseObserver.onNext(user.toGrpcUser())
                    } catch (e: StatusRuntimeException) {
                        responseObserver.onError(e)
                    }
                }

                override fun onError(t: Throwable) {
                    logger.error("Bidirectional streaming failed", t)
                    responseObserver.onError(t)
                }

                override fun onCompleted() {
                    responseObserver.onCompleted()
                }
            }
        }
    }
    ```

This one class demonstrates all three streaming shapes:

- `getAllUsers()` shows server streaming
- `createUsers()` shows client streaming
- `updateUsers()` shows bidirectional streaming

## Server Interceptor { #server-interceptor }

For more on server-side gRPC interceptors and how they are wired, see [gRPC Server: Interceptors](../documentation/grpc-server.md#interceptors).

Interceptors are the gRPC equivalent of transport middleware. They are a good place for concerns that should stay outside business logic:

- logging
- auth
- tracing
- rate limiting

The advanced module introduces a simple logging interceptor:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/LoggingInterceptor.java"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc;

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
            logger.info("Incoming gRPC request: method={}", call.getMethodDescriptor().getFullMethodName());
            return next.startCall(call, headers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/LoggingInterceptor.kt"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc

    import io.grpc.Metadata
    import io.grpc.ServerCall
    import io.grpc.ServerCallHandler
    import io.grpc.ServerInterceptor
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component

    @Component
    class LoggingInterceptor : ServerInterceptor {

        private val logger = LoggerFactory.getLogger(LoggingInterceptor::class.java)

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            logger.info("Incoming gRPC request: method={}", call.methodDescriptor.fullMethodName)
            return next.startCall(call, headers)
        }
    }
    ```

This interceptor lives only in the advanced module, so the basic guide stays focused on first principles.

## Server Reflection { #server-reflection }

Reflection is useful in development because it lets tools inspect the gRPC server without manually wiring a pre-generated client first.

In Kora, enabling it is just configuration:

For the full configuration reference, see [gRPC Server](../documentation/grpc-server.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    grpcServer {
      port = 8092 //(1)!
      reflectionEnabled = true //(2)!
      telemetry.logging.enabled = true //(3)!
    }
    ```

    1. Network port used by this server.
    2. Enables gRPC reflection for tools such as grpcurl.
    3. Enables the feature for this configuration section.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    grpcServer:
      port: 8092 #(1)!
      reflectionEnabled: true #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    ```

    1. Network port used by this server.
    2. Enables gRPC reflection for tools such as grpcurl.
    3. Enables the feature for this configuration section.

Why this matters:

- `grpcurl` can discover services more easily
- local debugging gets simpler
- the advanced guide can show a more tooling-friendly server setup

## API Key Authorization { #api-key }

The advanced module also introduces a server-side auth interceptor, but only for the streaming service.

That is important pedagogically:

- unary CRUD stays easy to understand
- the protected area is clearly limited to the advanced API

Configuration:

For the full configuration reference, see [Configuration](../documentation/config.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    auth.apiKey.value = ${?GRPC_STREAMING_API_KEY} //(1)!
    ```

    1. Configured value consumed by the guide component. Optional override from `GRPC_STREAMING_API_KEY`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    auth:
      apiKey:
        value: ${?GRPC_STREAMING_API_KEY} #(1)!
    ```

    1. Configured value consumed by the guide component. Optional override from `GRPC_STREAMING_API_KEY`.

Interceptor:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/UserStreamingAuthInterceptor.java"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc;

    import io.grpc.Metadata;
    import io.grpc.ServerCall;
    import io.grpc.ServerCallHandler;
    import io.grpc.ServerInterceptor;
    import io.grpc.Status;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Component
    public final class UserStreamingAuthInterceptor implements ServerInterceptor {

        private static final Metadata.Key<String> AUTHORIZATION_HEADER =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER);

        private final UserStreamingAuthConfig config;

        public UserStreamingAuthInterceptor(UserStreamingAuthConfig config) {
            this.config = config;
        }

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                ServerCall<ReqT, RespT> call,
                Metadata headers,
                ServerCallHandler<ReqT, RespT> next) {
            if (!UserStreamingServiceGrpc.SERVICE_NAME.equals(call.getMethodDescriptor().getServiceName())) {
                return next.startCall(call, headers);
            }

            var authorization = headers.get(AUTHORIZATION_HEADER);
            if (!this.config.value().equals(authorization)) {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), new Metadata());
                return new ServerCall.Listener<>() {};
            }

            return next.startCall(call, headers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/UserStreamingAuthInterceptor.kt"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc

    import io.grpc.*
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc

    @Component
    class UserStreamingAuthInterceptor(
        private val config: UserStreamingAuthConfig
    ) : ServerInterceptor {

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            if (UserStreamingServiceGrpc.SERVICE_NAME != call.methodDescriptor.serviceName) {
                return next.startCall(call, headers)
            }

            val authorization = headers.get(AUTHORIZATION_HEADER)
            if (config.value() != authorization) {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), Metadata())
                return object : ServerCall.Listener<ReqT>() {}
            }
            return next.startCall(call, headers)
        }

        companion object {
            private val AUTHORIZATION_HEADER: Metadata.Key<String> =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER)
        }
    }
    ```

This is the gRPC counterpart of the protected advanced endpoints we introduced in the HTTP advanced guide.

## Run Application { #run-app }

Compile:

```bash
./gradlew clean classes
```

Run:

```bash
$env:GRPC_STREAMING_API_KEY="test-api-key"
./gradlew run
```

Now the unary service is available on port `8092`, and the streaming service additionally expects:

- metadata header `authorization`
- value equal to `GRPC_STREAMING_API_KEY`

## Testing { #testing }

Run the module tests with:

```bash
./gradlew test
```

The companion app tests:

- unary CRUD
- server streaming
- client streaming
- bidirectional streaming
- unauthorized access to the protected streaming service

## Best Practices { #best-practices }

- Keep advanced streaming methods in a separate service when that improves clarity.
- Do not force every feature into one giant protobuf service.
- Keep unary CRUD stable while adding more advanced transport patterns around it.
- Use interceptors for cross-cutting transport concerns, not for business logic.
- Scope authorization narrowly when you can; not every method must be protected the same way.
- Turn on reflection in development-oriented modules where tooling support helps.
- Annotate handwritten DTOs with `@Json` only when they cross an HTTP/JSON boundary; generated protobuf messages do not need JSON annotations.

## Summary { #summary }

In this guide you kept the original unary gRPC service intact and added a second, clearly advanced streaming service on top of it.

That gave you a cleaner architecture and a better teaching flow:

- base service for familiar CRUD
- separate streaming service for advanced gRPC patterns
- interceptors, reflection, and auth only where they add real value

## Key Concepts { #key-concepts }

- why streaming deserves its own service boundary in many cases
- how server, client, and bidirectional streaming look in generated gRPC handlers
- how server interceptors work in Kora gRPC applications
- how to protect a service with metadata-based API-key auth
- how reflection helps local exploration and debugging

## Troubleshooting { #troubleshooting }

**Streaming methods are not generated:**

Regenerate sources with `./gradlew clean classes` after editing the `.proto` file and check that the streaming service is in the same source set.

**Protected calls are always rejected:**

Make sure `GRPC_STREAMING_API_KEY` is set and that the client sends the `authorization` metadata header expected by the interceptor.

**Reflection does not work:**

Verify `grpcServer.reflectionEnabled = true` in `application.conf` and include the gRPC services dependency in the build.

## What's Next? { #whats-next }

- [HTTP Client](http-client.md) if you have not completed it yet.
- [gRPC Client](grpc-client.md) if you want to revisit the unary client baseline first.
- [Advanced gRPC Client](grpc-client-advanced.md) after gRPC Client, to consume the streaming service and metadata-protected calls.
- [Observability](observability.md) to monitor streaming RPCs, interceptors, and server behavior.
- [Resilient Patterns](resilient.md) to protect clients that call advanced gRPC services.

## Help { #help }

If something does not work:

- compare with [Kora Java gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-advanced-app) and [Kora Kotlin gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-grpc-server-advanced-app)
- check the [gRPC Server documentation](../documentation/grpc-server.md)
- verify that you regenerated sources after changing the `.proto` contract
- make sure `GRPC_STREAMING_API_KEY` is set before testing protected calls
