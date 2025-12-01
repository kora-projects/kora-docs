---
title: Messaging with Kafka
summary: Learn how to implement event-driven architecture with Apache Kafka for asynchronous processing and microservices communication
tags: kafka, messaging, event-driven, asynchronous, microservices, publish-subscribe
---

# Messaging with Kafka

This comprehensive guide demonstrates how to implement robust event-driven architecture using Apache Kafka with the Kora framework. You'll master the art of asynchronous messaging, enabling scalable microservices communication, event sourcing patterns, and real-time data processing.

## What is Apache Kafka?

**Apache Kafka** is a distributed event streaming platform designed for high-throughput, fault-tolerant, and scalable data streaming. Originally developed by LinkedIn and later open-sourced through the Apache Software Foundation, Kafka has become the de facto standard for event-driven architectures in modern enterprise systems.

### Core Kafka Concepts

- **Topics**: Named channels where messages are published and stored
- **Producers**: Applications that publish (send) messages to Kafka topics
- **Consumers**: Applications that subscribe to and process messages from topics
- **Brokers**: Kafka server instances that manage topic partitions and message storage
- **ZooKeeper/Kraft**: Metadata management for cluster coordination

### Key Capabilities

- **Durability**: Messages are persisted to disk and replicated across multiple brokers
- **Scalability**: Can handle millions of messages per second across distributed clusters
- **Fault Tolerance**: Automatic failover and data replication ensure high availability
- **Retention**: Configurable message retention policies for historical data access
- **Real-time Processing**: Low-latency message delivery for time-sensitive applications

## What is Event-Driven Architecture?

**Event-driven architecture (EDA)** is a software design paradigm where system components communicate through events rather than direct method calls or synchronous API invocations. Events represent significant occurrences or state changes within the system that other components might find interesting.

### Event Types

- **Domain Events**: Business-significant events (UserCreated, OrderPlaced, PaymentProcessed)
- **System Events**: Infrastructure-level events (ServiceStarted, DatabaseBackupCompleted)
- **Integration Events**: Cross-service communication events

### EDA Benefits

- **Loose Coupling**: Components don't need direct knowledge of each other
- **Scalability**: Services can be scaled independently based on event processing load
- **Fault Tolerance**: System remains operational even if some components fail
- **Asynchronous Processing**: Non-blocking operations improve system responsiveness
- **Auditability**: Complete event history provides system observability

## Messaging in Microservices Architecture

In microservices architectures, messaging serves as the nervous system that enables service-to-service communication without tight coupling. Kafka provides the backbone for this communication layer.

### Common Messaging Patterns

- **Publish-Subscribe**: One-to-many communication where multiple consumers can process the same event
- **Event Sourcing**: Storing application state as a sequence of events
- **CQRS (Command Query Responsibility Segregation)**: Separating read and write models with event synchronization
- **Saga Pattern**: Coordinating distributed transactions through event chains

### Use Cases in Enterprise Systems

- **Real-time Analytics**: Processing user behavior events for immediate insights
- **Data Pipeline Orchestration**: Moving data between systems with guaranteed delivery
- **Audit Logging**: Comprehensive event trails for compliance and debugging
- **Notification Systems**: Triggering alerts and communications based on business events
- **Cache Invalidation**: Updating distributed caches when data changes
- **Search Index Updates**: Keeping search engines synchronized with primary data stores

## Why Kafka with Kora?

The Kora framework provides first-class support for Kafka integration, offering:

- **Type-Safe APIs**: Compile-time safety for message serialization and deserialization
- **Dependency Injection**: Seamless integration with Kora's component system
- **Configuration Management**: HOCON-based configuration for different environments
- **Observability**: Built-in metrics, tracing, and logging for Kafka operations
- **Transactional Support**: Ensuring data consistency across databases and events

## When to Use Event-Driven Messaging

Choose Kafka messaging when you need:

- **Asynchronous Processing**: Operations that shouldn't block user requests
- **High Throughput**: Systems processing thousands of events per second
- **Data Durability**: Guaranteed message delivery and historical data access
- **Scalable Architecture**: Systems that need to grow without architectural changes
- **Real-time Processing**: Immediate reaction to business events
- **Decoupled Services**: Microservices that communicate without direct dependencies

This guide will transform your synchronous CRUD application into a sophisticated event-driven system, demonstrating enterprise-grade patterns used by companies like Netflix, Uber, and LinkedIn.

## What You'll Build

You'll enhance your existing HTTP API with:

- **Event Publishing**: Send domain events when data changes
- **Message Consumption**: Process events asynchronously in the background
- **Event-Driven Architecture**: Decouple services with message-based communication
- **JSON Serialization**: Structured event data with automatic serialization
- **Transactional Messaging**: Ensure data consistency across events and database
- **Comprehensive Testing**: Test publishers and consumers with Testcontainers

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- Docker (for Kafka and testing)
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide

## Prerequisites

!!! note "Required: Complete Basic Kora Setup"

    This guide assumes you have completed the **[Create Your First Kora App](../getting-started.md)** guide and have a working Kora project with basic HTTP server setup.

    If you haven't completed the basic guide yet, please do so first as this guide builds upon that foundation.

## Why Event-Driven Architecture?

**Traditional synchronous communication** has limitations:

- **Tight Coupling**: Services depend directly on each other
- **Scalability Issues**: Load spikes affect all dependent services
- **Error Propagation**: Failures cascade through the system
- **Real-time Constraints**: All operations must complete within request timeout

**Event-driven architecture with Kafka** solves these problems:

- **Loose Coupling**: Services communicate through events, not direct calls
- **Better Scalability**: Services can process events at their own pace
- **Fault Tolerance**: Failed services don't break the entire system
- **Asynchronous Processing**: Long-running tasks don't block user requests

In this step, you'll learn how to publish events to Kafka when your application data changes. We'll set up the infrastructure, create event DTOs, configure publishers, and integrate event publishing into your existing CRUD operations.

## Add Kafka Dependencies

First, add Kafka support to your existing Kora project:

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        // Kafka messaging
        implementation("ru.tinkoff.kora:kafka")

        // JSON serialization for events
        implementation("ru.tinkoff.kora:json-module")

        // Testcontainers for Kafka testing
        testImplementation("io.goodforgod:testcontainers-extensions-kafka:0.12.2")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        // Kafka messaging
        implementation("ru.tinkoff.kora:kafka")

        // JSON serialization for events
        implementation("ru.tinkoff.kora:json-module")

        // Testcontainers for Kafka testing
        testImplementation("io.goodforgod:testcontainers-extensions-kafka:0.12.2")
    }
    ```

## Update Application Module

Add the Kafka module to your application:

===! ":fontawesome-brands-java: `Java`"

    Update your `Application.java`:

    ```java
    @KoraApp
    public interface Application extends
            // ... existing modules ...
            KafkaModule,
            JsonModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update your `Application.kt`:

    ```kotlin
    @KoraApp
    interface Application :
            // ... existing modules ...
            KafkaModule,
            JsonModule
    ```

## Docker Setup for Local Development

Create `docker-compose.yml` in your project root for local Kafka development:

```yaml title="docker-compose.yml"
services:
  kafka:
    image: confluentinc/cp-kafka:7.7.1
    restart: unless-stopped
    ports:
      - '9092:9092'
      - '9093:9093'
    environment:
      KAFKA_CONFLUENT_SUPPORT_METRICS_ENABLE: "false"
      AUTO_CREATE_TOPICS: "true"
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_LOG4J_LOGGERS: org.apache.zookeeper=ERROR,org.kafka.zookeeper=ERROR,kafka.zookeeper=ERROR,org.apache.kafka=ERROR,kafka=ERROR,kafka.network=ERROR,kafka.cluster=ERROR,kafka.controller=ERROR,kafka.coordinator=INFO,kafka.log=ERROR,kafka.server=ERROR,state.change.logger=ERROR
      ZOOKEEPER_LOG4J_LOGGERS: org.apache.zookeeper=ERROR,org.kafka.zookeeper=ERROR,org.kafka.zookeeper.server=ERROR,kafka.zookeeper=ERROR,org.apache.kafka=ERROR
      KAFKA_KRAFT_MODE: "true"
      KAFKA_PROCESS_ROLES: controller,broker
      KAFKA_NODE_ID: 1
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@localhost:9093"
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,PLAINTEXT_DOCKER://kafka:29092,CONTROLLER://0.0.0.0:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_DOCKER:PLAINTEXT,CONTROLLER:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,PLAINTEXT_DOCKER://kafka:29092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      CLUSTER_ID: "kora-guide-cluster"
    healthcheck:
      test: nc -z localhost 9092 || exit 1
      interval: 3s
      timeout: 10s
      retries: 5
      start_period: 10s
```

Start Kafka for development:

```bash
docker-compose up -d kafka
```

# Kafka Producer

## Kafka Producer Configuration

Add Kafka producer configuration to your `application.conf`:

```hocon title="application.conf"
# ... existing configuration ...

kafka {
  producer {
    events {
      driverProperties {
        "bootstrap.servers": ${KAFKA_BOOTSTRAP}
        "acks": "all"
        "retries": 3
      }
      telemetry {
        logging.enabled = true
      }
    }
  }
}
```

## Creating Event DTOs

Create event classes to represent your domain events:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/com/example/event/UserEvent.java`:

    ```java
    package com.example.event;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserEvent(
            String eventType,
            String userId,
            String username,
            String email,
            long timestamp
    ) {
        public static UserEvent created(String userId, String username, String email) {
            return new UserEvent("USER_CREATED", userId, username, email, System.currentTimeMillis());
        }

        public static UserEvent updated(String userId, String username, String email) {
            return new UserEvent("USER_UPDATED", userId, username, email, System.currentTimeMillis());
        }

        public static UserEvent deleted(String userId, String username, String email) {
            return new UserEvent("USER_DELETED", userId, username, email, System.currentTimeMillis());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/com/example/event/UserEvent.kt`:

    ```kotlin
    package com.example.event;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    data class UserEvent(
        val eventType: String,
        val userId: String,
        val username: String,
        val email: String,
        val timestamp: Long
    ) {
        companion object {
            fun created(userId: String, username: String, email: String) = UserEvent(
                "USER_CREATED", userId, username, email, System.currentTimeMillis()
            )

            fun updated(userId: String, username: String, email: String) = UserEvent(
                "USER_UPDATED", userId, username, email, System.currentTimeMillis()
            )

            fun deleted(userId: String, username: String, email: String) = UserEvent(
                "USER_DELETED", userId, username, email, System.currentTimeMillis()
            )
        }
    }
    ```

## Creating Event Publishers

Create a publisher interface for sending events:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/com/example/publisher/UserEventPublisher.java`:

    ```java
    package com.example.publisher;

    import com.example.event.UserEvent;
    import ru.tinkoff.kora.kafka.common.annotation.KafkaPublisher;
    import ru.tinkoff.kora.kafka.common.annotation.KafkaPublisher.Topic;

    @KafkaPublisher("kafka.producer.events")
    public interface UserEventPublisher {

        @Topic("kafka.producer.events.user-topic")
        void publish(UserEvent event);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/com/example/publisher/UserEventPublisher.kt`:

    ```kotlin
    package com.example.publisher

    import com.example.event.UserEvent
    import ru.tinkoff.kora.kafka.common.annotation.KafkaPublisher
    import ru.tinkoff.kora.kafka.common.annotation.KafkaPublisher.Topic

    @KafkaPublisher("kafka.producer.events")
    interface UserEventPublisher {

        @Topic("kafka.producer.events.user-topic")
        fun publish(event: UserEvent)
    }
    ```

## Configure Topics

Add topic configuration to `application.conf`:

```hocon title="application.conf"
kafka {
  # ... existing configuration ...

  producer {
    events {
      # ... existing producer config ...

      user-topic {
        topic = "user-events"
      }
    }
  }
}
```

## Integrating Events with CRUD Operations

Update your existing service to publish events when data changes:

===! ":fontawesome-brands-java: `Java`"

    Update your `UserService.java`:

    ```java
    @Component
    public final class UserService {
        private final UserRepository userRepository;
        private final UserEventPublisher eventPublisher;

        public UserService(UserRepository userRepository, UserEventPublisher eventPublisher) {
            this.userRepository = userRepository;
            this.eventPublisher = eventPublisher;
        }

        public UserResponse createUser(UserRequest request) {
            var user = userRepository.save(request);
            // Publish event after successful creation
            eventPublisher.publish(UserEvent.created(user.id(), user.name(), user.email()));
            return user;
        }

        public Optional<UserResponse> updateUser(String id, UserRequest request) {
            return userRepository.findById(id)
                    .map(existing -> {
                        var updated = userRepository.save(request);
                        // Publish event after successful update
                        eventPublisher.publish(UserEvent.updated(updated.id(), updated.name(), updated.email()));
                        return updated;
                    });
        }

        public boolean deleteUser(String id) {
            return userRepository.findById(id)
                    .map(user -> {
                        var deleted = userRepository.deleteById(id);
                        if (deleted) {
                            // Publish event after successful deletion
                            eventPublisher.publish(UserEvent.deleted(user.id(), user.name(), user.email()));
                        }
                        return deleted;
                    })
                    .orElse(false);
        }

        // ... other methods remain unchanged ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update your `UserService.kt`:

    ```kotlin
    @Component
    class UserService(
        private val userRepository: UserRepository,
        private val eventPublisher: UserEventPublisher
    ) {

        fun createUser(request: UserRequest): UserResponse {
            val user = userRepository.save(request)
            // Publish event after successful creation
            eventPublisher.publish(UserEvent.created(user.id, user.name, user.email))
            return user
        }

        fun updateUser(id: String, request: UserRequest): UserResponse? {
            return userRepository.findById(id)?.let { existing ->
                val updated = userRepository.save(request)
                // Publish event after successful update
                eventPublisher.publish(UserEvent.updated(updated.id, updated.name, updated.email))
                updated
            }
        }

        fun deleteUser(id: String): Boolean {
            return userRepository.findById(id)?.let { user ->
                val deleted = userRepository.deleteById(id)
                if (deleted) {
                    // Publish event after successful deletion
                    eventPublisher.publish(UserEvent.deleted(user.id, user.name, user.email))
                }
                deleted
            } ?: false
        }

        // ... other methods remain unchanged ...
    }
    ```

## Testing Event Publishing

Create tests for your event publishing:

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/com/example/publisher/UserEventPublisherTest.java`:

    ```java
    package com.example.publisher;

    import com.example.event.UserEvent;
    import io.goodforgod.testcontainers.extensions.kafka.ConnectionKafka;
    import io.goodforgod.testcontainers.extensions.kafka.KafkaConnection;
    import io.goodforgod.testcontainers.extensions.kafka.TestcontainersKafka;
    import io.goodforgod.testcontainers.extensions.kafka.Topics;
    import org.json.JSONObject;
    import org.junit.jupiter.api.Test;
    import com.example.Application;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier;
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification;
    import ru.tinkoff.kora.test.extension.junit5.TestComponent;

    @TestcontainersKafka(mode = PER_RUN, topics = @Topics("user-events"))
    @KoraAppTest(Application.class)
    class UserEventPublisherTest implements KoraAppTestConfigModifier {

        @ConnectionKafka
        private KafkaConnection connection;

        @TestComponent
        private UserEventPublisher publisher;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty(
                "KAFKA_BOOTSTRAP", connection.params().bootstrapServers()
            );
        }

        @Test
        void shouldPublishUserCreatedEvent() {
            // Given
            var consumer = connection.subscribe("user-events");
            var event = UserEvent.created("user-123", "john", "john@example.com");

            // When
            publisher.publish(event);

            // Then
            var records = consumer.consume(1);
            assertEquals(1, records.size());

            var record = records.get(0);
            var jsonEvent = new JSONObject(record.value());
            assertEquals("USER_CREATED", jsonEvent.getString("eventType"));
            assertEquals("user-123", jsonEvent.getString("userId"));
            assertEquals("john", jsonEvent.getString("username"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/com/example/publisher/UserEventPublisherTest.kt`:

    ```kotlin
    package com.example.publisher

    import com.example.event.UserEvent
    import io.goodforgod.testcontainers.extensions.kafka.ConnectionKafka
    import io.goodforgod.testcontainers.extensions.kafka.KafkaConnection
    import io.goodforgod.testcontainers.extensions.kafka.TestcontainersKafka
    import io.goodforgod.testcontainers.extensions.kafka.Topics
    import org.json.JSONObject
    import org.junit.jupiter.api.Test
    import com.example.Application
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification
    import ru.tinkoff.kora.test.extension.junit5.TestComponent

    @TestcontainersKafka(mode = PER_RUN, topics = @Topics(["user-events"]))
    @KoraAppTest(Application::class)
    class UserEventPublisherTest : KoraAppTestConfigModifier {

        @ConnectionKafka
        private lateinit var connection: KafkaConnection

        @TestComponent
        private lateinit var publisher: UserEventPublisher

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofSystemProperty(
                "KAFKA_BOOTSTRAP", connection.params().bootstrapServers()
            )
        }

        @Test
        fun `should publish user created event`() {
            // Given
            val consumer = connection.subscribe("user-events")
            val event = UserEvent.created("user-123", "john", "john@example.com")

            // When
            publisher.publish(event)

            // Then
            val records = consumer.consume(1)
            assertEquals(1, records.size)

            val record = records[0]
            val jsonEvent = JSONObject(record.value())
            assertEquals("USER_CREATED", jsonEvent.getString("eventType"))
            assertEquals("user-123", jsonEvent.getString("userId"))
            assertEquals("john", jsonEvent.getString("username"))
        }
    }
    ```

## Testing the Integration

Test that your CRUD operations now publish events:

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/com/example/UserServiceEventIntegrationTest.java`:

    ```java
    package com.example;

    import com.example.dto.UserRequest;
    import io.goodforgod.testcontainers.extensions.kafka.ConnectionKafka;
    import io.goodforgod.testcontainers.extensions.kafka.KafkaConnection;
    import io.goodforgod.testcontainers.extensions.kafka.TestcontainersKafka;
    import io.goodforgod.testcontainers.extensions.kafka.Topics;
    import org.json.JSONObject;
    import org.junit.jupiter.api.Test;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier;
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification;
    import ru.tinkoff.kora.test.extension.junit5.TestComponent;

    @TestcontainersKafka(mode = PER_RUN, topics = @Topics("user-events"))
    @KoraAppTest(Application.class)
    class UserServiceEventIntegrationTest implements KoraAppTestConfigModifier {

        @ConnectionKafka
        private KafkaConnection connection;

        @TestComponent
        private UserService userService;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification
                .ofSystemProperty("KAFKA_BOOTSTRAP", connection.params().bootstrapServers())
                .withSystemProperty("POSTGRES_JDBC_URL", "jdbc:h2:mem:test")
                .withSystemProperty("POSTGRES_USER", "sa")
                .withSystemProperty("POSTGRES_PASS", "");
        }

        @Test
        void createUser_ShouldPublishEvent() {
            // Given
            var consumer = connection.subscribe("user-events");
            var request = new UserRequest("John", "john@example.com");

            // When
            var result = userService.createUser(request);

            // Then
            assertNotNull(result);
            var records = consumer.consume(1);
            assertEquals(1, records.size());

            var event = new JSONObject(records.get(0).value());
            assertEquals("USER_CREATED", event.getString("eventType"));
            assertEquals(result.name(), event.getString("username"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/com/example/UserServiceEventIntegrationTest.kt`:

    ```kotlin
    package com.example

    import com.example.dto.UserRequest
    import io.goodforgod.testcontainers.extensions.kafka.ConnectionKafka
    import io.goodforgod.testcontainers.extensions.kafka.KafkaConnection
    import io.goodforgod.testcontainers.extensions.kafka.TestcontainersKafka
    import io.goodforgod.testcontainers.extensions.kafka.Topics
    import org.json.JSONObject
    import org.junit.jupiter.api.Test
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification
    import ru.tinkoff.kora.test.extension.junit5.TestComponent

    @TestcontainersKafka(mode = PER_RUN, topics = @Topics(["user-events"]))
    @KoraAppTest(Application::class)
    class UserServiceEventIntegrationTest : KoraAppTestConfigModifier {

        @ConnectionKafka
        private lateinit var connection: KafkaConnection

        @TestComponent
        private lateinit var userService: UserService

        override fun config(): KoraConfigModification {
            return KoraConfigModification
                .ofSystemProperty("KAFKA_BOOTSTRAP", connection.params().bootstrapServers())
                .withSystemProperty("POSTGRES_JDBC_URL", "jdbc:h2:mem:test")
                .withSystemProperty("POSTGRES_USER", "sa")
                .withSystemProperty("POSTGRES_PASS", "")
        }

        @Test
        fun `createUser should publish event`() {
            // Given
            val consumer = connection.subscribe("user-events")
            val request = UserRequest("John", "john@example.com")

            // When
            val result = userService.createUser(request)

            // Then
            assertNotNull(result)
            val records = consumer.consume(1)
            assertEquals(1, records.size)

            val event = JSONObject(records[0].value())
            assertEquals("USER_CREATED", event.getString("eventType"))
            assertEquals(result.name, event.getString("username"))
        }
    }
    ```

## Running and testing

Test your event publishing setup:

```bash
# Start Kafka
docker-compose up -d kafka

# Run your application
./gradlew run

# In another terminal, test event publishing
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Check Kafka logs to see events being published
docker-compose logs kafka
```

Run the publisher tests:

```bash
./gradlew test --tests "*UserEventPublisherTest*"
./gradlew test --tests "*UserServiceEventIntegrationTest*"
```

---

# Kafka Consumer

Now that you can publish events, let's learn how to consume and process them asynchronously. In this step, we'll create consumers that listen for events and process them in the background.

## Add Consumer Configuration

Add consumer configuration to your `application.conf`:

```hocon title="application.conf"
kafka {
  # ... existing configuration ...

  consumer {
    events {
      topics = ["user-events"]
      driverProperties {
        "bootstrap.servers": ${KAFKA_BOOTSTRAP}
        "group.id": "kora-guide-consumer"
        "auto.offset.reset": "latest"
        "enable.auto.commit": true
      }
      telemetry {
        logging.enabled = true
        metrics.enabled = true
        tracing.enabled = true
      }
    }
  }
}
```

## Creating Event Consumers

Create a consumer to handle user events asynchronously:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/com/example/consumer/UserEventConsumer.java`:

    ```java
    package com.example.consumer;

    import com.example.event.UserEvent;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.kafka.common.annotation.KafkaListener;

    @Component
    public class UserEventConsumer {
        private static final Logger logger = LoggerFactory.getLogger(UserEventConsumer.class);

        @KafkaListener("kafka.consumer.events")
        void process(UserEvent event) {
            logger.info("Processing user event: {} for user {}", event.eventType(), event.username());

            // Process the event asynchronously
            switch (event.eventType()) {
                case "USER_CREATED" -> handleUserCreated(event);
                case "USER_UPDATED" -> handleUserUpdated(event);
                case "USER_DELETED" -> handleUserDeleted(event);
                default -> logger.warn("Unknown event type: {}", event.eventType());
            }
        }

        private void handleUserCreated(UserEvent event) {
            logger.info("🎉 New user created: {} ({})", event.username(), event.email());
            // Here you could:
            // - Send welcome email
            // - Create user profile in analytics system
            // - Send notification to admin
            // - Update search index
        }

        private void handleUserUpdated(UserEvent event) {
            logger.info("📝 User updated: {} ({})", event.username(), event.email());
            // Here you could:
            // - Update search index
            // - Send change notification
            // - Update analytics profile
        }

        private void handleUserDeleted(UserEvent event) {
            logger.info("🗑️ User deleted: {} ({})", event.username(), event.email());
            // Here you could:
            // - Clean up user data from external systems
            // - Send goodbye email
            // - Archive user analytics data
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/com/example/consumer/UserEventConsumer.kt`:

    ```kotlin
    package com.example.consumer

    import com.example.event.UserEvent
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.kafka.common.annotation.KafkaListener

    @Component
    class UserEventConsumer {
        private val logger = LoggerFactory.getLogger(UserEventConsumer::class.java)

        @KafkaListener("kafka.consumer.events")
        fun process(event: UserEvent) {
            logger.info("Processing user event: {} for user {}", event.eventType, event.username)

            // Process the event asynchronously
            when (event.eventType) {
                "USER_CREATED" -> handleUserCreated(event)
                "USER_UPDATED" -> handleUserUpdated(event)
                "USER_DELETED" -> handleUserDeleted(event)
                else -> logger.warn("Unknown event type: {}", event.eventType)
            }
        }

        private fun handleUserCreated(event: UserEvent) {
            logger.info("🎉 New user created: {} ({})", event.username, event.email)
            // Here you could:
            // - Send welcome email
            // - Create user profile in analytics system
            // - Send notification to admin
            // - Update search index
        }

        private fun handleUserUpdated(event: UserEvent) {
            logger.info("📝 User updated: {} ({})", event.username, event.email)
            // Here you could:
            // - Update search index
            // - Send change notification
            // - Update analytics profile
        }

        private fun handleUserDeleted(event: UserEvent) {
            logger.info("🗑️ User deleted: {} ({})", event.username, event.email)
            // Here you could:
            // - Clean up user data from external systems
            // - Send goodbye email
            // - Archive user analytics data
        }
    }
    ```

## Testing Event Consumption

Create tests for your event consumers:

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/com/example/consumer/UserEventConsumerTest.java`:

    ```java
    package com.example.consumer;

    import com.example.event.UserEvent;
    import io.goodforgod.testcontainers.extensions.kafka.ConnectionKafka;
    import io.goodforgod.testcontainers.extensions.kafka.KafkaConnection;
    import io.goodforgod.testcontainers.extensions.kafka.TestcontainersKafka;
    import io.goodforgod.testcontainers.extensions.kafka.Topics;
    import org.junit.jupiter.api.Test;
    import com.example.Application;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier;
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification;

    @TestcontainersKafka(mode = PER_RUN, topics = @Topics("user-events"))
    @KoraAppTest(Application.class)
    class UserEventConsumerTest implements KoraAppTestConfigModifier {

        @ConnectionKafka
        private KafkaConnection connection;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty(
                "KAFKA_BOOTSTRAP", connection.params().bootstrapServers()
            );
        }

        @Test
        void shouldConsumeUserEvents() throws InterruptedException {
            // Given
            var producer = connection.producer("user-events");
            var event = UserEvent.created("user-123", "john", "john@example.com");

            // When
            producer.send(event);

            // Then - Consumer should process the event
            // Wait a bit for async processing
            Thread.sleep(1000);

            // In a real test, you might verify side effects like:
            // - Email service was called
            // - Database was updated
            // - External API was invoked
            // For now, we just verify the consumer doesn't crash
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/com/example/consumer/UserEventConsumerTest.kt`:

    ```kotlin
    package com.example.consumer

    import com.example.event.UserEvent
    import io.goodforgod.testcontainers.extensions.kafka.ConnectionKafka
    import io.goodforgod.testcontainers.extensions.kafka.KafkaConnection
    import io.goodforgod.testcontainers.extensions.kafka.TestcontainersKafka
    import io.goodforgod.testcontainers.extensions.kafka.Topics
    import org.junit.jupiter.api.Test
    import com.example.Application
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification

    @TestcontainersKafka(mode = PER_RUN, topics = @Topics(["user-events"]))
    @KoraAppTest(Application::class)
    class UserEventConsumerTest : KoraAppTestConfigModifier {

        @ConnectionKafka
        private lateinit var connection: KafkaConnection

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty(
                "KAFKA_BOOTSTRAP", connection.params().bootstrapServers()
            );
        }

        @Test
        fun `should consume user events`() {
            // Given
            val producer = connection.subscribe("user-events")
            val event = UserEvent.created("user-123", "john", "john@example.com")

            // When
            producer.send(event)

            // Then - Consumer should process the event
            // Wait a bit for async processing
            Thread.sleep(1000)

            // In a real test, you might verify side effects like:
            // - Email service was called
            // - Database was updated
            // - External API was invoked
            // For now, we just verify the consumer doesn't crash
        }
    }
    ```

## Running Step 2

Test your complete event-driven system:

```bash
# Start Kafka
docker-compose up -d kafka

# Run your application
./gradlew run

# In another terminal, create a user (this will publish an event)
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Check application logs to see event processing
# You should see consumer logs like:
# "🎉 New user created: John Doe (john@example.com)"
```

Run all tests:

```bash
./gradlew test
```

## Advanced Patterns

### Transactional Publishing

For data consistency between database and events:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.producer.transactional")
    public interface TransactionalEventPublisher extends TransactionalPublisher<TransactionalEventPublisher.EventPublisher> {

        @KafkaPublisher("kafka.producer.events")
        interface EventPublisher {
            @Topic("kafka.producer.events.user-topic")
            void publish(UserEvent event);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.producer.transactional")
    interface TransactionalEventPublisher : TransactionalPublisher<TransactionalEventPublisher.EventPublisher> {

        @KafkaPublisher("kafka.producer.events")
        interface EventPublisher {
            @Topic("kafka.producer.events.user-topic")
            fun publish(event: UserEvent)
        }
    }
    ```

### Manual Commit for Fine Control

For advanced error handling:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.consumer.manual")
    void process(UserEvent event, Consumer<String, String> consumer) {
        try {
            // Process event
            processEvent(event);
            // Manual commit on success
            consumer.commitSync();
        } catch (Exception e) {
            // Handle error - don't commit, message will be retried
            logger.error("Failed to process event", e);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("kafka.consumer.manual")
    fun process(event: UserEvent, consumer: Consumer<String, String>) {
        try {
            // Process event
            processEvent(event)
            // Manual commit on success
            consumer.commitSync()
        } catch (e: Exception) {
            // Handle error - don't commit, message will be retried
            logger.error("Failed to process event", e)
        }
    }
    ```

## Monitoring and Observability

Kora automatically provides metrics and tracing for Kafka operations. View them at your configured endpoints.

## Best Practices

### Event Design
- Use descriptive event names (UserCreated, OrderPlaced)
- Include all relevant data in events
- Use event versioning for schema evolution
- Keep events immutable

### Consumer Patterns
- Make consumers idempotent (handle duplicate events)
- Use dead letter topics for failed messages
- Implement proper error handling and logging
- Monitor consumer lag and throughput

### Testing Strategies
- Test publishers and consumers separately
- Use Testcontainers for integration tests
- Test error scenarios and edge cases
- Verify event data integrity

## Summary

You've successfully implemented event-driven architecture with Kafka:

- **Step 1 - Publishing**: Send domain events when data changes
- **Step 2 - Consuming**: Process events asynchronously in the background
- **Event-Driven Architecture**: Decouple services with message-based communication
- **JSON Serialization**: Structured event data with automatic serialization
- **Transactional Messaging**: Ensure data consistency across events and database
- **Comprehensive Testing**: Test all components with Testcontainers

## Key Concepts Learned

### Event-Driven Architecture
- **Domain Events**: Represent business facts as immutable events
- **Publish-Subscribe**: Decouple producers and consumers
- **Asynchronous Processing**: Handle operations without blocking

### Kafka Integration
- **Publishers**: Send messages with type-safe interfaces
- **Consumers**: Process messages with automatic serialization
- **Configuration**: Flexible setup for different environments

### Testing Strategies
- **Testcontainers**: Realistic testing with Docker containers
- **Publisher Tests**: Verify events are sent correctly
- **Consumer Tests**: Ensure events are processed properly

## Next Steps

Continue your event-driven journey:

- **Advanced Kafka**: Explore transactional messaging and exactly-once delivery
- **Event Sourcing**: Build applications around event streams
- **CQRS**: Separate read and write models with events
- **Microservices**: Use events for service communication

## Troubleshooting

### Connection Issues
- Verify Kafka is running: `docker-compose ps`
- Check bootstrap servers configuration
- Ensure network connectivity between containers

### Serialization Errors
- Verify `@Json` annotations on event classes
- Check JSON field mappings
- Validate event data types

### Consumer Not Processing
- Check topic names match between producer and consumer
- Verify consumer group configuration
- Check logs for deserialization errors

### Testcontainers Issues
- Ensure Docker is running and accessible
- Check Testcontainers version compatibility
- Verify network configuration for container communication

## What You'll Build

You'll enhance your existing HTTP API with:

- **Event Publishing**: Send domain events when data changes
- **Message Consumption**: Process events asynchronously in the background
- **Event-Driven Architecture**: Decouple services with message-based communication
- **JSON Serialization**: Structured event data with automatic serialization
- **Transactional Messaging**: Ensure data consistency across events and database
- **Comprehensive Testing**: Test publishers and consumers with Testcontainers

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- Docker (for Kafka and testing)
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide

## Prerequisites

!!! note "Required: Complete Basic Kora Setup"

    This guide assumes you have completed the **[Create Your First Kora App](../getting-started.md)** guide and have a working Kora project with basic HTTP server setup.

    If you haven't completed the basic guide yet, please do so first as this guide builds upon that foundation.

## Why Event-Driven Architecture?

**Traditional synchronous communication** has limitations:

- **Tight Coupling**: Services depend directly on each other
- **Scalability Issues**: Load spikes affect all dependent services
- **Error Propagation**: Failures cascade through the system
- **Real-time Constraints**: All operations must complete within request timeout

**Event-driven architecture with Kafka** solves these problems:

- **Loose Coupling**: Services communicate through events, not direct calls
- **Better Scalability**: Services can process events at their own pace
- **Fault Tolerance**: Failed services don't break the entire system
- **Asynchronous Processing**: Long-running tasks don't block user requests

## Add Kafka Dependencies

First, add Kafka support to your existing Kora project:

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        // Kafka messaging
        implementation("ru.tinkoff.kora:kafka")

        // JSON serialization for events
        implementation("ru.tinkoff.kora:json-module")

        // Testcontainers for Kafka testing
        testImplementation("io.goodforgod:testcontainers-extensions-kafka:0.12.2")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        // Kafka messaging
        implementation("ru.tinkoff.kora:kafka")

        // JSON serialization for events
        implementation("ru.tinkoff.kora:json-module")

        // Testcontainers for Kafka testing
        testImplementation("io.goodforgod:testcontainers-extensions-kafka:0.12.2")
    }
    ```

## Update Application Module

Add the Kafka module to your application:

===! ":fontawesome-brands-java: `Java`"

    Update your `Application.java`:

    ```java
    @KoraApp
    public interface Application extends
            // ... existing modules ...
            KafkaModule,
            JsonModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update your `Application.kt`:

    ```kotlin
    @KoraApp
    interface Application :
            // ... existing modules ...
            KafkaModule,
            JsonModule
    ```

## Docker Setup for Local Development

Create `docker-compose.yml` in your project root for local Kafka development:

```yaml title="docker-compose.yml"
services:
  kafka:
    image: confluentinc/cp-kafka:7.7.1
    restart: unless-stopped
    ports:
      - '9092:9092'
      - '9093:9093'
    environment:
      KAFKA_CONFLUENT_SUPPORT_METRICS_ENABLE: "false"
      AUTO_CREATE_TOPICS: "true"
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_LOG4J_LOGGERS: org.apache.zookeeper=ERROR,org.kafka.zookeeper=ERROR,kafka.zookeeper=ERROR,org.apache.kafka=ERROR,kafka=ERROR,kafka.network=ERROR,kafka.cluster=ERROR,kafka.controller=ERROR,kafka.coordinator=INFO,kafka.log=ERROR,kafka.server=ERROR,state.change.logger=ERROR
      ZOOKEEPER_LOG4J_LOGGERS: org.apache.zookeeper=ERROR,org.kafka.zookeeper=ERROR,org.kafka.zookeeper.server=ERROR,kafka.zookeeper=ERROR,org.apache.kafka=ERROR
      KAFKA_KRAFT_MODE: "true"
      KAFKA_PROCESS_ROLES: controller,broker
      KAFKA_NODE_ID: 1
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@localhost:9093"
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,PLAINTEXT_DOCKER://kafka:29092,CONTROLLER://0.0.0.0:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_DOCKER:PLAINTEXT,CONTROLLER:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,PLAINTEXT_DOCKER://kafka:29092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      CLUSTER_ID: "kora-guide-cluster"
    healthcheck:
      test: nc -z localhost 9092 || exit 1
      interval: 3s
      timeout: 10s
      retries: 5
      start_period: 10s

# Uncomment to run your application in Docker alongside Kafka
#  app:
#    image: kora-kafka-guide
#    build: .
#    ports:
#      - '8080:8080'
#    environment:
#      KAFKA_BOOTSTRAP: kafka:29092
#    depends_on:
#      kafka:
#        condition: service_healthy
```

Start Kafka for development:

```bash
docker-compose up -d kafka
```

## Kafka Configuration

Add Kafka configuration to your `application.conf`:

```hocon title="application.conf"
# ... existing configuration ...

kafka {
  producer {
    events {
      driverProperties {
        "bootstrap.servers": ${KAFKA_BOOTSTRAP}
        "acks": "all"
        "retries": 3
      }
      telemetry {
        logging.enabled = true
        metrics.enabled = true
        tracing.enabled = true
      }
    }
  }

  consumer {
    events {
      topics = ["user-events", "task-events"]
      driverProperties {
        "bootstrap.servers": ${KAFKA_BOOTSTRAP}
        "group.id": "kora-guide-consumer"
        "auto.offset.reset": "latest"
        "enable.auto.commit": true
      }
      telemetry {
        logging.enabled = true
        metrics.enabled = true
        tracing.enabled = true
      }
    }
  }
}
```

## Publishing Events

Create event DTOs and publishers for your domain events.

### Event DTOs

Create event classes for your domain:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/com/example/event/UserEvent.java`:

    ```java
    package com.example.event;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserEvent(
            String eventType,
            String userId,
            String username,
            String email,
            long timestamp
    ) {
        public static UserEvent created(String userId, String username, String email) {
            return new UserEvent("USER_CREATED", userId, username, email, System.currentTimeMillis());
        }

        public static UserEvent updated(String userId, String username, String email) {
            return new UserEvent("USER_UPDATED", userId, username, email, System.currentTimeMillis());
        }

        public static UserEvent deleted(String userId, String username, String email) {
            return new UserEvent("USER_DELETED", userId, username, email, System.currentTimeMillis());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/com/example/event/UserEvent.kt`:

    ```kotlin
    package com.example.event

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class UserEvent(
        val eventType: String,
        val userId: String,
        val username: String,
        val email: String,
        val timestamp: Long
    ) {
        companion object {
            fun created(userId: String, username: String, email: String) = UserEvent(
                "USER_CREATED", userId, username, email, System.currentTimeMillis()
            )

            fun updated(userId: String, username: String, email: String) = UserEvent(
                "USER_UPDATED", userId, username, email, System.currentTimeMillis()
            )

            fun deleted(userId: String, username: String, email: String) = UserEvent(
                "USER_DELETED", userId, username, email, System.currentTimeMillis()
            )
        }
    }
    ```

### Event Publisher

Create a publisher interface for sending events:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/com/example/publisher/UserEventPublisher.java`:

    ```java
    package com.example.publisher;

    import com.example.event.UserEvent;
    import ru.tinkoff.kora.kafka.common.annotation.KafkaPublisher;
    import ru.tinkoff.kora.kafka.common.annotation.KafkaPublisher.Topic;

    @KafkaPublisher("kafka.producer.events")
    public interface UserEventPublisher {

        @Topic("kafka.producer.events.user-topic")
        void publish(UserEvent event);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/com/example/publisher/UserEventPublisher.kt`:

    ```kotlin
    package com.example.publisher

    import com.example.event.UserEvent
    import ru.tinkoff.kora.kafka.common.annotation.KafkaPublisher
    import ru.tinkoff.kora.kafka.common.annotation.KafkaPublisher.Topic

    @KafkaPublisher("kafka.producer.events")
    interface UserEventPublisher {

        @Topic("kafka.producer.events.user-topic")
        fun publish(event: UserEvent)
    }
    ```

### Update Topic Configuration

Add topic configuration to `application.conf`:

```hocon title="application.conf"
kafka {
  # ... existing configuration ...

  producer {
    events {
      # ... existing producer config ...

      user-topic {
        topic = "user-events"
      }
    }
  }
}
```

## Consuming Events

Create consumers to process events asynchronously.

### Event Consumer

Create a consumer to handle user events:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/com/example/consumer/UserEventConsumer.java`:

    ```java
    package com.example.consumer;

    import com.example.event.UserEvent;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.kafka.common.annotation.KafkaListener;

    @Component
    public class UserEventConsumer {
        private static final Logger logger = LoggerFactory.getLogger(UserEventConsumer.class);

        @KafkaListener("kafka.consumer.events")
        void process(UserEvent event) {
            logger.info("Processing user event: {} for user {}", event.eventType(), event.username());

            // Process the event (e.g., send notifications, update search index, etc.)
            switch (event.eventType()) {
                case "USER_CREATED" -> handleUserCreated(event);
                case "USER_UPDATED" -> handleUserUpdated(event);
                case "USER_DELETED" -> handleUserDeleted(event);
                default -> logger.warn("Unknown event type: {}", event.eventType());
            }
        }

        private void handleUserCreated(UserEvent event) {
            logger.info("User created: {} ({})", event.username(), event.email());
            // Send welcome email, create notification, etc.
        }

        private void handleUserUpdated(UserEvent event) {
            logger.info("User updated: {} ({})", event.username(), event.email());
            // Update search index, send notification, etc.
        }

        private void handleUserDeleted(UserEvent event) {
            logger.info("User deleted: {} ({})", event.username(), event.email());
            // Clean up user data, send goodbye email, etc.
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/com/example/consumer/UserEventConsumer.kt`:

    ```kotlin
    package com.example.consumer

    import com.example.event.UserEvent
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.kafka.common.annotation.KafkaListener

    @Component
    class UserEventConsumer {
        private val logger = LoggerFactory.getLogger(UserEventConsumer::class.java)

        @KafkaListener("kafka.consumer.events")
        fun process(event: UserEvent) {
            logger.info("Processing user event: {} for user {}", event.eventType, event.username)

            // Process the event (e.g., send notifications, update search index, etc.)
            when (event.eventType) {
                "USER_CREATED" -> handleUserCreated(event)
                "USER_UPDATED" -> handleUserUpdated(event)
                "USER_DELETED" -> handleUserDeleted(event)
                else -> logger.warn("Unknown event type: {}", event.eventType)
            }
        }

        private fun handleUserCreated(event: UserEvent) {
            logger.info("User created: {} ({})", event.username, event.email)
            // Send welcome email, create notification, etc.
        }

        private fun handleUserUpdated(event: UserEvent) {
            logger.info("User updated: {} ({})", event.username, event.email)
            // Update search index, send notification, etc.
        }

        private fun handleUserDeleted(event: UserEvent) {
            logger.info("User deleted: {} ({})", event.username, event.email)
            // Clean up user data, send goodbye email, etc.
        }
    }
    ```

## Integrating with Your CRUD Application

Update your existing service to publish events when data changes.

### Update User Service

Modify your user service to publish events:

===! ":fontawesome-brands-java: `Java`"

    Update your `UserService.java`:

    ```java
    @Component
    public final class UserService {
        private final UserRepository userRepository;
        private final UserEventPublisher eventPublisher;

        public UserService(UserRepository userRepository, UserEventPublisher eventPublisher) {
            this.userRepository = userRepository;
            this.eventPublisher = eventPublisher;
        }

        public UserResponse createUser(UserRequest request) {
            var user = userRepository.save(request);
            // Publish event after successful creation
            eventPublisher.publish(UserEvent.created(user.id(), user.name(), user.email()));
            return user;
        }

        public Optional<UserResponse> updateUser(String id, UserRequest request) {
            return userRepository.findById(id)
                    .map(existing -> {
                        var updated = userRepository.save(request);
                        // Publish event after successful update
                        eventPublisher.publish(UserEvent.updated(updated.id(), updated.name(), updated.email()));
                        return updated;
                    });
        }

        public boolean deleteUser(String id) {
            return userRepository.findById(id)
                    .map(user -> {
                        var deleted = userRepository.deleteById(id);
                        if (deleted) {
                            // Publish event after successful deletion
                            eventPublisher.publish(UserEvent.deleted(user.id(), user.name(), user.email()));
                        }
                        return deleted;
                    })
                    .orElse(false);
        }

        // ... other methods remain unchanged ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update your `UserService.kt`:

    ```kotlin
    @Component
    class UserService(
        private val userRepository: UserRepository,
        private val eventPublisher: UserEventPublisher
    ) {

        fun createUser(request: UserRequest): UserResponse {
            val user = userRepository.save(request)
            // Publish event after successful creation
            eventPublisher.publish(UserEvent.created(user.id, user.name, user.email))
            return user
        }

        fun updateUser(id: String, request: UserRequest): UserResponse? {
            return userRepository.findById(id)?.let { existing ->
                val updated = userRepository.save(request)
                // Publish event after successful update
                eventPublisher.publish(UserEvent.updated(updated.id, updated.name, updated.email))
                updated
            }
        }

        fun deleteUser(id: String): Boolean {
            return userRepository.findById(id)?.let { user ->
                val deleted = userRepository.deleteById(id)
                if (deleted) {
                    // Publish event after successful deletion
                    eventPublisher.publish(UserEvent.deleted(user.id, user.name, user.email))
                }
                deleted
            } ?: false
        }

        // ... other methods remain unchanged ...
    }
    ```

## Testing Your Events

Create comprehensive tests for your event-driven system.

### Publisher Tests

Test your event publishing:

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/com/example/publisher/UserEventPublisherTest.java`:

    ```java
    package com.example.publisher;

    import com.example.event.UserEvent;
    import io.goodforgod.testcontainers.extensions.kafka.ConnectionKafka;
    import io.goodforgod.testcontainers.extensions.kafka.KafkaConnection;
    import io.goodforgod.testcontainers.extensions.kafka.TestcontainersKafka;
    import io.goodforgod.testcontainers.extensions.kafka.Topics;
    import org.json.JSONObject;
    import org.junit.jupiter.api.Test;
    import com.example.Application;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier;
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification;
    import ru.tinkoff.kora.test.extension.junit5.TestComponent;

    @TestcontainersKafka(mode = PER_RUN, topics = @Topics("user-events"))
    @KoraAppTest(Application.class)
    class UserEventPublisherTest implements KoraAppTestConfigModifier {

        @ConnectionKafka
        private KafkaConnection connection;

        @TestComponent
        private UserEventPublisher publisher;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty(
                "KAFKA_BOOTSTRAP", connection.params().bootstrapServers()
            );
        }

        @Test
        void shouldPublishUserCreatedEvent() {
            // Given
            var consumer = connection.subscribe("user-events");
            var event = UserEvent.created("user-123", "john", "john@example.com");

            // When
            publisher.publish(event);

            // Then
            var records = consumer.consume(1);
            assertEquals(1, records.size());

            var record = records.get(0);
            var jsonEvent = new JSONObject(record.value());
            assertEquals("USER_CREATED", jsonEvent.getString("eventType"));
            assertEquals("user-123", jsonEvent.getString("userId"));
            assertEquals("john", jsonEvent.getString("username"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/com/example/publisher/UserEventPublisherTest.kt`:

    ```kotlin
    package com.example.publisher

    import com.example.event.UserEvent
    import io.goodforgod.testcontainers.extensions.kafka.ConnectionKafka
    import io.goodforgod.testcontainers.extensions.kafka.KafkaConnection
    import io.goodforgod.testcontainers.extensions.kafka.TestcontainersKafka
    import io.goodforgod.testcontainers.extensions.kafka.Topics
    import org.json.JSONObject
    import org.junit.jupiter.api.Test
    import com.example.Application
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification
    import ru.tinkoff.kora.test.extension.junit5.TestComponent

    @TestcontainersKafka(mode = PER_RUN, topics = @Topics(["user-events"]))
    @KoraAppTest(Application::class)
    class UserEventPublisherTest : KoraAppTestConfigModifier {

        @ConnectionKafka
        private lateinit var connection: KafkaConnection

        @TestComponent
        private lateinit var publisher: UserEventPublisher

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofSystemProperty(
                "KAFKA_BOOTSTRAP", connection.params().bootstrapServers()
            )
        }

        @Test
        fun `should publish user created event`() {
            // Given
            val consumer = connection.subscribe("user-events")
            val event = UserEvent.created("user-123", "john", "john@example.com")

            // When
            publisher.publish(event)

            // Then
            val records = consumer.consume(1)
            assertEquals(1, records.size)

            val record = records[0]
            val jsonEvent = JSONObject(record.value())
            assertEquals("USER_CREATED", jsonEvent.getString("eventType"))
            assertEquals("user-123", jsonEvent.getString("userId"))
            assertEquals("john", jsonEvent.getString("username"))
        }
    }
    ```

### Consumer Tests

Test your event consumption:

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/com/example/consumer/UserEventConsumerTest.java`:

    ```java
    package com.example.consumer;

    import com.example.event.UserEvent;
    import io.goodforgod.testcontainers.extensions.kafka.ConnectionKafka;
    import io.goodforgod.testcontainers.extensions.kafka.KafkaConnection;
    import io.goodforgod.testcontainers.extensions.kafka.TestcontainersKafka;
    import io.goodforgod.testcontainers.extensions.kafka.Topics;
    import org.junit.jupiter.api.Test;
    import com.example.Application;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier;
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification;

    @TestcontainersKafka(mode = PER_RUN, topics = @Topics("user-events"))
    @KoraAppTest(Application.class)
    class UserEventConsumerTest implements KoraAppTestConfigModifier {

        @ConnectionKafka
        private KafkaConnection connection;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty(
                "KAFKA_BOOTSTRAP", connection.params().bootstrapServers()
            );
        }

        @Test
        void shouldConsumeUserEvents() throws InterruptedException {
            // Given
            var producer = connection.producer("user-events");
            var event = UserEvent.created("user-123", "john", "john@example.com");

            // When
            producer.send(event);

            // Then - Consumer should process the event
            // Wait a bit for async processing
            Thread.sleep(1000);

            // Verify event was processed (check logs or mock dependencies)
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/com/example/consumer/UserEventConsumerTest.kt`:

    ```kotlin
    package com.example.consumer

    import com.example.event.UserEvent
    import io.goodforgod.testcontainers.extensions.kafka.ConnectionKafka
    import io.goodforgod.testcontainers.extensions.kafka.KafkaConnection
    import io.goodforgod.testcontainers.extensions.kafka.TestcontainersKafka
    import io.goodforgod.testcontainers.extensions.kafka.Topics
    import org.junit.jupiter.api.Test
    import com.example.Application
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification

    @TestcontainersKafka(mode = PER_RUN, topics = @Topics(["user-events"]))
    @KoraAppTest(Application::class)
    class UserEventConsumerTest : KoraAppTestConfigModifier {

        @ConnectionKafka
        private lateinit var connection: KafkaConnection

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofSystemProperty(
                "KAFKA_BOOTSTRAP", connection.params().bootstrapServers()
            )
        }

        @Test
        fun `should consume user events`() {
            // Given
            val producer = connection.producer("user-events")
            val event = UserEvent.created("user-123", "john", "john@example.com")

            // When
            producer.send(event)

            // Then - Consumer should process the event
            // Wait a bit for async processing
            Thread.sleep(1000)

            // Verify event was processed (check logs or mock dependencies)
        }
    }
    ```

## Running and Testing

Start your application with Kafka:

```bash
# Start Kafka
docker-compose up -d kafka

# Run your application
./gradlew run

# In another terminal, test the events
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

Run the tests:

```bash
./gradlew test
```

## Advanced Patterns

### Transactional Publishing

For data consistency between database and events:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.producer.transactional")
    public interface TransactionalEventPublisher extends TransactionalPublisher<TransactionalEventPublisher.EventPublisher> {

        @KafkaPublisher("kafka.producer.events")
        interface EventPublisher {
            @Topic("kafka.producer.events.user-topic")
            void publish(UserEvent event);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.producer.transactional")
    interface TransactionalEventPublisher : TransactionalPublisher<TransactionalEventPublisher.EventPublisher> {

        @KafkaPublisher("kafka.producer.events")
        interface EventPublisher {
            @Topic("kafka.producer.events.user-topic")
            fun publish(event: UserEvent)
        }
    }
    ```

### Manual Commit for Fine Control

For advanced error handling:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.consumer.manual")
    void process(UserEvent event, Consumer<String, String> consumer) {
        try {
            // Process event
            processEvent(event);
            // Manual commit on success
            consumer.commitSync();
        } catch (Exception e) {
            // Handle error - don't commit, message will be retried
            logger.error("Failed to process event", e);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("kafka.consumer.manual")
    fun process(event: UserEvent, consumer: Consumer<String, String>) {
        try {
            // Process event
            processEvent(event)
            // Manual commit on success
            consumer.commitSync()
        } catch (e: Exception) {
            // Handle error - don't commit, message will be retried
            logger.error("Failed to process event", e)
        }
    }
    ```

## Monitoring and Observability

Kora automatically provides metrics and tracing for Kafka operations. View them at your configured endpoints.

## Best Practices

### Event Design
- Use descriptive event names (UserCreated, OrderPlaced)
- Include all relevant data in events
- Use event versioning for schema evolution
- Keep events immutable

### Consumer Patterns
- Make consumers idempotent (handle duplicate events)
- Use dead letter topics for failed messages
- Implement proper error handling and logging
- Monitor consumer lag and throughput

### Testing Strategies
- Test publishers and consumers separately
- Use Testcontainers for integration tests
- Test error scenarios and edge cases
- Verify event data integrity

## Summary

You've successfully implemented event-driven architecture with Kafka:

- **Event Publishing**: Send domain events when data changes
- **Asynchronous Processing**: Handle events in the background
- **Loose Coupling**: Services communicate through events
- **Scalability**: Process events at your own pace
- **Comprehensive Testing**: Test all components with Testcontainers

## Key Concepts Learned

### Event-Driven Architecture
- **Domain Events**: Represent business facts as immutable events
- **Publish-Subscribe**: Decouple producers and consumers
- **Asynchronous Processing**: Handle operations without blocking

### Kafka Integration
- **Publishers**: Send messages with type-safe interfaces
- **Consumers**: Process messages with automatic serialization
- **Configuration**: Flexible setup for different environments

### Testing Strategies
- **Testcontainers**: Realistic testing with Docker containers
- **Publisher Tests**: Verify events are sent correctly
- **Consumer Tests**: Ensure events are processed properly

## Next Steps

Continue your event-driven journey:

- **Advanced Kafka**: Explore transactional messaging and exactly-once delivery
- **Event Sourcing**: Build applications around event streams
- **CQRS**: Separate read and write models with events
- **Microservices**: Use events for service communication

## Troubleshooting

### Connection Issues
- Verify Kafka is running: `docker-compose ps`
- Check bootstrap servers configuration
- Ensure network connectivity between containers

### Serialization Errors
- Verify `@Json` annotations on event classes
- Check JSON field mappings
- Validate event data types

### Consumer Not Processing
- Check topic names match between producer and consumer
- Verify consumer group configuration
- Check logs for deserialization errors

### Testcontainers Issues
- Ensure Docker is running and accessible
- Check Testcontainers version compatibility
- Verify network configuration for container communication