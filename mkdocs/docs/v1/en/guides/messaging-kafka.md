---
search:
  exclude: true
title: Messaging with Kafka
summary: Extend the HTTP Server guide with asynchronous user creation using Kafka producer and consumer components in the same Kora application
tags: kafka, messaging, asynchronous, event-driven, producer, consumer
---

# Messaging with Kafka { #messaging-kafka }

This guide introduces event-driven messaging with Kora and Apache Kafka. It covers how producers publish domain events, how consumers process those events asynchronously, and how Kora wires Kafka
modules, JSON serializers, configuration, and lifecycle-managed listeners into the application graph. You will also see how an HTTP request can hand work off to Kafka while a consumer completes the
operation in the background.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-messaging-kafka-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-messaging-kafka-app).

## What You'll Build { #youll-build }

You will turn the existing user API into a small event-driven flow:

- the controller will accept `POST /users`
- it will generate the future user id
- it will publish `UserCreatedEvent` to Kafka
- it will return `202 Accepted` immediately
- a Kafka consumer in the same application will receive the event
- that consumer will create the user through the same service and repository stack

The rest of the API still behaves like the HTTP Server guide:

- `GET /users/{userId}`
- `GET /users`
- `PUT /users/{userId}`
- `DELETE /users/{userId}`

So the main change in this guide is not the whole application architecture. The main change is that **user creation becomes asynchronous**.

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- Docker for local Kafka and integration tests
- A text editor or IDE
- Completed [HTTP Server](http-server.md) guide

## Prerequisites { #prerequisites }

!!! note "Required: Complete HTTP Server First"

    This guide assumes you have completed **[HTTP Server](http-server.md)** and already have `UserController`, `UserService`, `UserRepository`, `InMemoryUserRepository`, `UserRequest`, and `UserResponse`.

    We will keep that familiar structure and evolve it instead of starting from scratch.

    If you haven't completed the HTTP server guide yet, do that first, because this guide changes the create-user flow while preserving the existing HTTP API and service structure.

## Overview { #overview }

This guide changes one part of the HTTP application from synchronous request-response behavior to event-driven behavior. Instead of completing user creation inside the HTTP request, the controller
publishes an event and returns quickly. A consumer receives that event later and performs the actual write.

That shift is small in code, but important architecturally. It introduces asynchronous work, eventual consistency, message serialization, consumer processing, and the need to keep business logic
reusable when the trigger is no longer only an HTTP request.

### What Is Event-Driven Architecture? { #event-driven-architecture }

Event-driven architecture is a design style where components communicate by publishing and consuming events. An event is a fact or request for work that other parts of the system can react to without
the producer calling them directly.

In a synchronous flow, the caller waits while every step finishes:

1. HTTP request arrives.
2. Controller calls service.
3. Service writes to repository.
4. Response returns only after the write is complete.

In an event-driven flow, part of the work moves behind a message boundary:

1. HTTP request arrives.
2. Controller publishes `UserCreatedEvent`.
3. Response returns with an accepted or future identifier.
4. Consumer receives the event.
5. Consumer calls the service and repository to complete the write.

That means the system becomes eventually consistent. A client may receive a response before the user is visible through `GET /users/{id}`. This is normal for asynchronous flows, but the API behavior,
tests, and troubleshooting section must make it explicit.

### Why Messaging Is Needed { #messaging-needed }

Messaging helps when doing all work inside one request becomes a poor fit:

- expensive work should not block the user-facing request
- several components need to react to the same business event
- producers and consumers should scale independently
- temporary consumer failure should not always break the entrypoint
- traffic spikes need buffering instead of immediate downstream pressure

Messaging is not a default replacement for simple method calls. It adds operational complexity: brokers, topics, serialization, retries, duplicate handling, lag, and ordering. Use it when the
decoupling or asynchronous behavior is worth that complexity.

### What Is Apache Kafka? { #apache-kafka }

[Apache Kafka](https://kafka.apache.org/documentation/) is a distributed event streaming platform. It stores events in named topics, lets producers append records to those topics, and lets consumers
read records at their own pace. Kafka is commonly used as a durable backbone for event-driven systems because it is built for high throughput, retention, replay, and horizontal scaling.

At a practical level, Kafka gives applications a durable place to publish facts about what happened and lets other components react to those facts later.

#### Core Kafka Concepts { #core-kafka-concepts }

- Topic: a named stream of records
- Producer: application code that writes records to a topic
- Consumer: application code that reads records from a topic
- Consumer group: a group of consumers that share work for a topic
- Broker: a Kafka server that stores topic data and serves producers and consumers
- Record key and value: the data sent to Kafka, often serialized from typed application objects

Kafka is not a database replacement. Your main application state still belongs in the database or repository layer. Kafka is the transport that moves business events between components and services.

### Messaging in Services { #messaging-services }

In microservices architectures, messaging often acts as a coordination layer between independently deployed components. Instead of one service knowing every downstream API and waiting for every
response, it can publish events that other services consume.

Common patterns include:

- Publish-subscribe: one event can be consumed by one or many subscribers
- Event sourcing: application state is reconstructed from stored events
- CQRS: write-side changes publish events that update one or more read models
- Saga pattern: distributed workflows coordinate through a sequence of events

This guide uses the smallest useful version of that idea. The producer and consumer live in the same application so the guide can focus on the messaging model before splitting the flow across several
services.

### Kafka and Kora { #kora-kafka }

Kora's Kafka modules wire producers and consumers into the application graph. Configuration describes brokers, topics, consumer groups, and serialization. JSON serializers keep event payloads typed,
while lifecycle-managed consumers start with the application and process records in the background.

The important boundary stays the same as in the HTTP guide:

- the controller handles HTTP input and publishes an event
- the producer is the outbound messaging adapter
- the consumer is the inbound messaging adapter
- the service still owns application behavior
- the repository still owns storage

The practical flow is:

1. add Kafka modules and dependencies
2. introduce `UserCreatedEvent`
3. publish the event from `createUser()`
4. add a Kafka consumer for that event
5. route consumer work back through the service and repository
6. configure Kafka for local development and tests

## Dependencies { #dependencies }

First, add Kafka support to the project you already built in the HTTP Server guide.

===! ":fontawesome-brands-java: `Java`"

    Add these dependencies to `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        implementation("ru.tinkoff.kora:kafka")
        implementation("ru.tinkoff.kora:json-module")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add these dependencies to `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        implementation("ru.tinkoff.kora:kafka")
        implementation("ru.tinkoff.kora:json-module")
    }
    ```

Kafka support in Kora comes from `KafkaModule`, and JSON support is important because we want to send structured event objects instead of raw strings.

## Modules { #modules }

Now extend your application with Kafka support.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/Application.java"
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowHttpServerModule,
            JsonModule,
            KafkaModule,  // <----- Connected module
            LogbackModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/Application.kt"
    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowHttpServerModule,
        JsonModule,
        KafkaModule,  // <----- Connected module
        LogbackModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

At this point nothing publishes or consumes yet. We are only enabling the framework modules that will generate producer and consumer components for us.

## Events { #events }

In the HTTP Server guide, `createUser()` returned the created user immediately because the write happened in the same request.

Here we want a different contract:

- the controller accepts the request
- it generates the future id
- it publishes an event
- it returns that id immediately

So we need two new DTOs:

- `UserCreatedEvent` for Kafka
- `UserAcceptedResponse` for the HTTP response

This is not only a DTO change. It is also a change in how the application thinks about work.

In a synchronous CRUD application, the request thread usually performs everything before the HTTP response is returned. That is often a good starting point, but it becomes much less attractive when
creating a user also requires other slow or fragile operations such as:

- calling external identity providers
- provisioning data in another platform
- sending emails or notifications
- updating search indexes
- pushing data into analytics systems
- triggering workflows in other services

If all of that work happens inside the request, the endpoint becomes slower and more fragile. A single slow downstream integration can make the user wait much longer than expected, and a failure in
one dependency can break the whole request path.

Publishing an event and processing it later can be a better design because:

- the HTTP request can finish quickly
- the long-running work moves out of the request thread
- processing can fail or retry independently
- the processing logic can later live in another application without changing the event contract

That is exactly what we are modeling in this guide.

For simplicity, the producer and consumer still live in the same application. Conceptually, though, you should think of this as a small simulation of a larger event-driven system:

- the controller accepts the command
- Kafka carries the event
- the consumer performs the actual creation work later

So even though the guide uses one application, the architecture is the same kind of architecture teams use when one service publishes an event and another service consumes it.

Add `UserCreatedEvent`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedEvent.java"
    @Json
    public record UserCreatedEvent(
            String id,
            String name,
            String email,
            LocalDateTime createdAt
    ) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedEvent.kt"
    @Json
    data class UserCreatedEvent(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

This is the payload that Kafka will carry from the producer to the consumer.

Add `UserAcceptedResponse`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/dto/UserAcceptedResponse.java"
    @Json
    public record UserAcceptedResponse(String id) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/dto/UserAcceptedResponse.kt"
    @Json
    data class UserAcceptedResponse(val id: String)
    ```

Returning only the future id is important for the tutorial narrative. It makes the asynchronous contract visible to the reader: the user is not guaranteed to exist yet at the exact
moment `POST /users` returns.

## Producer { #kafka-producer }

For details on generated Kafka producers, topic configuration, and error handling, see [Producer](../documentation/kafka.md#producer).

Now we need a producer component that can publish `UserCreatedEvent`.

Kora generates producer implementations from annotated interfaces, so we only declare the contract.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedPublisher.java"
    @KafkaPublisher("kafka.producer.user-created")
    public interface UserCreatedPublisher {

        @Topic("kafka.producer.user-created-topic")
        void send(@Json UserCreatedEvent event);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedPublisher.kt"
    @KafkaPublisher("kafka.producer.user-created")
    interface UserCreatedPublisher {

        @Topic("kafka.producer.user-created-topic")
        fun send(@Json event: UserCreatedEvent)
    }
    ```

What is happening here:

- `@KafkaPublisher(...)` tells Kora to generate a Kafka producer component
- `@Topic(...)` points to the named topic configuration in `application.conf`
- `@Json` tells Kora to serialize the event as JSON before sending it to Kafka

This is similar in spirit to Kora HTTP clients: you describe the contract, and Kora generates the implementation.

### Publish events { #publish-events }

This is the most important step in the guide.

In the HTTP Server guide, `createUser()` delegated to the service and immediately wrote to the repository. Now we will change only this part of the controller. The other HTTP operations still stay
close to the original CRUD example.

Update only the constructor dependencies and the `createUser()` method. The other endpoints stay the same as in the HTTP Server guide, so we do not repeat them here.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/controller/UserController.java"
    @Component
    @HttpController
    public final class UserController {

        private final UserCreatedPublisher userCreatedPublisher;
        private final UserService userService;

        public UserController(UserCreatedPublisher userCreatedPublisher, UserService userService) {
            this.userCreatedPublisher = userCreatedPublisher;
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public HttpResponseEntity<UserAcceptedResponse> createUser(@Json UserRequest request) {
            var userId = UUID.randomUUID().toString();
            var event = new UserCreatedEvent(userId, request.name(), request.email(), LocalDateTime.now());
            this.userCreatedPublisher.send(event);
            return HttpResponseEntity.of(202, HttpHeaders.of(), new UserAcceptedResponse(userId));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/controller/UserController.kt"
    @Component
    @HttpController
    class UserController(
        private val userCreatedPublisher: UserCreatedPublisher,
        private val userService: UserService
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): HttpResponseEntity<UserAcceptedResponse> {
            val userId = UUID.randomUUID().toString()
            val event = UserCreatedEvent(userId, request.name, request.email, LocalDateTime.now())
            userCreatedPublisher.send(event)
            return HttpResponseEntity.of(202, HttpHeaders.of(), UserAcceptedResponse(userId))
        }
    }
    ```

What changed conceptually:

- `createUser()` no longer persists directly
- the controller now plays the role of command entry point
- it returns `202 Accepted` instead of `201 Created`
- the returned id is the id the future user will have after the event is processed

That is why this guide is a good introduction to messaging. The same business action still exists, but the timing changes.

## Service layer { #service-layer }

We still want this example to feel like a continuation of the HTTP Server guide, so we keep the same layers:

- controller
- service
- repository

The only difference is that user creation now enters the system through Kafka.

Because the consumer receives a fully prepared event with id and timestamp, the repository saves a ready `UserResponse` object instead of generating the id itself.

Again, we only show the parts that actually changed compared with the HTTP Server guide.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/repository/UserRepository.java"
    public interface UserRepository {

        void save(UserResponse user);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/repository/UserRepository.kt"
    interface UserRepository {

        fun save(user: UserResponse)
    }
    ```

The in-memory repository changes only in its `save(...)` method, because it now stores a fully prepared user object:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/repository/InMemoryUserRepository.java"
    @Component
    public final class InMemoryUserRepository implements UserRepository {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();

        @Override
        public void save(UserResponse user) {
            this.users.put(user.id(), user);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/repository/InMemoryUserRepository.kt"
    @Component
    class InMemoryUserRepository : UserRepository {

        private val users = ConcurrentHashMap<String, UserResponse>()

        override fun save(user: UserResponse) {
            users[user.id] = user
        }
    }
    ```

The service also changes only where the Kafka consumer needs a new entrypoint. Everything else in the class stays the same as in the HTTP Server guide.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/service/UserService.java"
    @Component
    public final class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        public void createUser(UserCreatedEvent event) {
            this.userRepository.save(new UserResponse(event.id(), event.name(), event.email(), event.createdAt()));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/service/UserService.kt"
    @Component
    class UserService(
        private val userRepository: UserRepository
    ) {

        fun createUser(event: UserCreatedEvent) {
            userRepository.save(UserResponse(event.id, event.name, event.email, event.createdAt))
        }
    }
    ```

This keeps the guide grounded. The reader is still working with the same `UserService` and `UserRepository` ideas they already learned in the HTTP Server guide.

## Consumer { #kafka-consumer }

For more on `@KafkaListener`, subscription strategies, deserialization, and failures, see [Consume strategy](../documentation/kafka.md#consume-strategy), [Deserialization](../documentation/kafka.md#deserialization), and [Exception handling](../documentation/kafka.md#exception-handling).

Now we can connect the other side of the flow.

The producer already publishes `UserCreatedEvent`. The consumer will listen to that topic and delegate back into the service layer.

At first, a Kafka listener can look as simple as this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.consumer.user-created")
    public void process(@Json UserCreatedEvent event) {
        this.userService.createUser(event);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("kafka.consumer.user-created")
    fun process(@Json event: UserCreatedEvent) {
        userService.createUser(event)
    }
    ```

That is a good first mental model: Kora deserializes the message and passes the event object to your method.

### Events processing { #events-processing }

For real applications, it is often useful to also receive a possible deserialization or mapping error. That is the final form used in this guide:

Here again, we only show the consumer class itself because that is the class being introduced in this step.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedConsumer.java"
    @Component
    public final class UserCreatedConsumer {

        private static final Logger logger = LoggerFactory.getLogger(UserCreatedConsumer.class);

        private final UserService userService;

        public UserCreatedConsumer(UserService userService) {
            this.userService = userService;
        }

        @KafkaListener("kafka.consumer.user-created")
        public void process(@Json @Nullable UserCreatedEvent event, @Nullable Exception exception) {
            if (exception != null) {
                logger.warn("Failed to consume user creation event", exception);
                return;
            }
            if (event == null) {
                logger.warn("Received null user creation event without exception");
                return;
            }
            logger.info("Consuming user creation event for user {}", event.id());
            this.userService.createUser(event);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedConsumer.kt"
    @Component
    class UserCreatedConsumer(
        private val userService: UserService
    ) {

        private val logger = LoggerFactory.getLogger(UserCreatedConsumer::class.java)

        @KafkaListener("kafka.consumer.user-created")
        fun process(@Json event: UserCreatedEvent?, exception: Exception?) {
            if (exception != null) {
                logger.warn("Failed to consume user creation event", exception)
                return
            }
            if (event == null) {
                logger.warn("Received null user creation event without exception")
                return
            }
            logger.info("Consuming user creation event for user {}", event.id)
            userService.createUser(event)
        }
    }
    ```

Why this is useful:

- if deserialization fails, Kora can pass the error to your listener
- your business code can separate “valid event” from “message could not be read”
- the guide can show both the simple shape and the more defensive production-style shape

This is also a nice symmetry with the HTTP guides: the controller is still the entry point for the HTTP command, but now the consumer becomes the entry point for the asynchronous processing stage.

## Configuration { #configuration }

Now wire the producer and consumer to the same topic.

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [Kafka](../documentation/kafka.md) and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    kafka {
      producer {
        user-created {
          driverProperties {
            "bootstrap.servers": ${?KAFKA_BOOTSTRAP} //(1)!
          }
          telemetry.logging.enabled = true //(2)!
        }

        user-created-topic {
          topic = "user-created-events" //(3)!
        }
      }

      consumer {
        user-created {
          topics = "user-created-events" //(4)!
          pollTimeout = 250ms //(5)!
          driverProperties {
            "bootstrap.servers": ${?KAFKA_BOOTSTRAP} //(6)!
            "group.id": "guide-messaging-kafka-app" //(7)!
            "auto.offset.reset" = "earliest" //(8)!
            "enable.auto.commit" = true //(9)!
          }
          telemetry.logging.enabled = true //(10)!
        }
      }
    }
    ```

    1. Kafka bootstrap servers used by producer or consumer clients. Optional override from `KAFKA_BOOTSTRAP`.
    2. Enables the feature for this configuration section.
    3. Topic or channel name used by the component.
    4. Value for `kafka.consumer.user-created.topics`.
    5. Value for `kafka.consumer.user-created.pollTimeout`.
    6. Kafka bootstrap servers used by producer or consumer clients. Optional override from `KAFKA_BOOTSTRAP`.
    7. Value for `kafka.consumer.user-created.driverProperties.group.id`.
    8. Value for `kafka.consumer.user-created.driverProperties.auto.offset.reset`.
    9. Value for `kafka.consumer.user-created.driverProperties.enable.auto.commit`.
    10. Enables the feature for this configuration section.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    kafka:
      producer:
        user-created:
          driverProperties:
            "bootstrap.servers": ${?KAFKA_BOOTSTRAP} #(1)!
          telemetry:
            logging:
              enabled: true #(2)!
        user-created-topic:
          topic: "user-created-events" #(3)!
      consumer:
        user-created:
          topics: "user-created-events" #(4)!
          pollTimeout: 250ms #(5)!
          driverProperties:
            "bootstrap.servers": ${?KAFKA_BOOTSTRAP} #(6)!
            "group.id": "guide-messaging-kafka-app" #(7)!
            "auto.offset.reset": "earliest" #(8)!
            "enable.auto.commit": true #(9)!
          telemetry:
            logging:
              enabled: true #(10)!
    ```

    1. Kafka bootstrap servers used by producer or consumer clients. Optional override from `KAFKA_BOOTSTRAP`.
    2. Enables the feature for this configuration section.
    3. Topic or channel name used by the component.
    4. Value for `kafka.consumer.user-created.topics`.
    5. Value for `kafka.consumer.user-created.pollTimeout`.
    6. Kafka bootstrap servers used by producer or consumer clients. Optional override from `KAFKA_BOOTSTRAP`.
    7. Value for `kafka.consumer.user-created.driverProperties.group.id`.
    8. Value for `kafka.consumer.user-created.driverProperties.auto.offset.reset`.
    9. Value for `kafka.consumer.user-created.driverProperties.enable.auto.commit`.
    10. Enables the feature for this configuration section.

What this configuration does:

- defines one producer named `user-created`
- defines one consumer named `user-created`
- points both of them to the same Kafka topic
- enables simple logging telemetry so you can see the flow while learning

## Docker Compose { #docker-compose }

For local development, start Kafka with Docker.

Create `docker-compose.yml` in the application module directory:

```yaml title="docker-compose.yml"
services:
  kafka:
    image: apache/kafka-native:4.1.0
    restart: unless-stopped
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      CLUSTER_ID: "4L6g3nShT-eMCtK--X86sw"
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: "broker,controller"
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@kafka:9093"
      KAFKA_LISTENERS: "PLAINTEXT://:9092,CONTROLLER://:9093"
      KAFKA_ADVERTISED_LISTENERS: "PLAINTEXT://localhost:9092"
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: "PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT"
      KAFKA_INTER_BROKER_LISTENER_NAME: "PLAINTEXT"
      KAFKA_CONTROLLER_LISTENER_NAMES: "CONTROLLER"
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
```

## Run Application { #run-app }

Start Kafka:

```bash
docker compose up -d kafka
```

Then run the application:

```bash
./gradlew run
```

## Check Application { #check-app }

Create a user:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

You should get a response like:

```json
{
    "id": "9f6f1d43-8e2c-41ce-a7c1-f1d4d92a7982"
}
```

Notice what happened:

- the HTTP request returned immediately
- the response does not contain the whole created user
- the user id is already known
- the real write happens when the Kafka consumer processes the event

Now fetch the user:

```bash
curl http://localhost:8080/users/9f6f1d43-8e2c-41ce-a7c1-f1d4d92a7982
```

Depending on timing, there may be a short gap before the user becomes visible. That gap is the whole point of the guide: the creation pipeline is asynchronous now.

## Best Practices { #best-practices }

- Keep event DTOs focused on business meaning. `UserCreatedEvent` should represent a fact, not an HTTP request shape.
- Treat consumer code as another application boundary. Validate and log carefully.
- Make consumers idempotent when possible. In real systems, the same event may be delivered more than once.
- Keep the HTTP contract honest. Returning `202 Accepted` is better than pretending the write already finished.
- Reuse your existing service and repository layers when it keeps the design simple. Kafka should change the flow, not force needless rewrites.

## Summary { #summary }

You extended the HTTP Server guide with a first event-driven workflow:

- `POST /users` now publishes `UserCreatedEvent`
- the controller returns `202 Accepted` with the future user id
- a Kafka consumer receives that event
- the consumer creates the user through `UserService`
- the rest of the CRUD API still looks familiar

That makes this guide a gentle introduction to asynchronous messaging. The application still feels like the same CRUD service, but one important operation now happens through Kafka.

## Key Concepts { #key-concepts }

- Kafka lets you move work out of the HTTP request path
- producers publish events, consumers process them later
- `202 Accepted` is a natural HTTP status for asynchronous creation
- Kora can generate Kafka producers from interfaces
- Kafka listeners can evolve from a simple event-only signature to a more defensive `event + exception` form
- event-driven architecture can build on top of the same service and repository layers you already know

## Troubleshooting { #troubleshooting }

**`POST /users` returns an id but `GET /users/{id}` still returns 404:**

That usually means the event was published but not consumed yet, or the consumer failed to process it.

Check:

- Kafka is running
- the topic name is the same for producer and consumer
- application logs show the consumer processing the event

**Consumer never receives the event:**

Check:

- `kafka.producer.user-created-topic.topic`
- `kafka.consumer.user-created.topics`
- `KAFKA_BOOTSTRAP`

Both producer and consumer must point to the same broker and the same topic.

**Deserialization errors in the consumer:**

If JSON cannot be read correctly, the listener may receive `exception != null`.

That is why the final consumer signature in this guide accepts both:

- `@Json @Nullable UserCreatedEvent event`
- `@Nullable Exception exception`

This gives you a place to log or react to mapping failures explicitly.

## What's Next? { #whats-next }

- [Resilient Patterns](resilient.md) to add retries, circuit breakers, and fallbacks around operations that publish or consume events.
- [Observability](observability.md) to monitor producers, consumers, lag-sensitive behavior, and asynchronous failures.
- [Caching](cache.md) when event-driven writes need fast read paths.
- [Database JDBC](database-jdbc.md) before black-box testing if you want the JDBC-backed end-to-end test path.

## Help { #help }

If you encounter issues:

- compare with [Kora Java Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-messaging-kafka-app) and [Kora Kotlin Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-messaging-kafka-app)
- revisit [HTTP Server](http-server.md) for the synchronous API baseline
- check the [Kafka documentation](../documentation/kafka.md)
- check the [JSON documentation](../documentation/json.md) for event payload mapping
