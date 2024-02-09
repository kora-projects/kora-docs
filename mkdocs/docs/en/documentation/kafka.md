Module for creating declarative [Apache Kafka](https://kafka.apache.org/) `Consumer` and `Producer` using annotations.

## Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:kafka"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends KafkaModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:kafka")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : KafkaModule
    ```

## Consumer

Descriptions of working with [Kafka Consumer](https://docs.confluent.io/platform/current/clients/consumer.html)

Creating a `Consumer` requires using the `@KafkaListener` annotation over a method:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {
        
        @KafkaListener("path.to.config")
        void process(String key, String value) { 
            // my code
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {

        @KafkaListener("path.to.config")
        fun process(key: String, value: String) {
            // my code
        }
    }
    ```

The `@KafkaListener` annotation parameter points to the `Consumer` configuration path.

In case you need different behavior for different topics, it is possible to create several such containers,
each with its own individual configuration. It looks like this:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {
        
        @KafkaListener("path.to.first.config")
        void processFirst(String key, String value) { 
            // some handler code
        }
        
        @KafkaListener("path.to.second.config")
        void processSecond(String key, String value) {
            // some handler code
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {

        @KafkaListener("path.to.first.config")
        fun processFirst(key: String, value: String) {
            // some handler code
        }

        @KafkaListener("path.to.second.config")
        fun processSecond(key: String, value: String) {
            // some handler code
        }
    }
    ```

The value in the annotation indicates from which part of the configuration file the settings should be taken. As far as getting the configuration is concerned - works similarly to `@ConfigSource`

### Configuration

The configuration describes the settings of a particular `@KafkaListener` and is described in the `KafkaListenerConfig` class,
below is an example for the configuration at path `path.to.config`:

===! ":material-code-json: `Hocon`"

    ```javascript
    path {
        to {
            config {
                topics = [ "topic1", "topic2" ] //(1)!
                topicsPattern = "topic*" //(2)!
                partitions = [ "1", "2" ] //(3)!
                offset = "latest" //(4)!
                pollTimeout = "5s" //(5)!
                backoffTimeout = "15s" //(6)!
                partitionRefreshInterval = "1m" //(7)!
                threads = 1 //(8)!
                driverProperties { //(9)!
                    "bootstrap.servers": "localhost:9093"
                    "group.id": "my-group-id"
                }
                telemetry {
                    logging {
                        enabled = true //(10)!
                    }
                    metrics {
                        enabled = true //(11)!
                        slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(12)!
                    }
                    telemetry {
                        enabled = true //(13)!
                    }
                }
            }
        }
    }
    ```

    1. Specifies the topics to which Consumer will subscribe (or specify `topicsPattern`)
    2. Specifies the pattern of topics to which the Consumer will subscribe (or `topics` is specified).
    3. Specifies the partitions of topics to be subscribed to
    4. Specifies which position in the topics the Consumer should use. Valid values are `earliest` - go to the earliest available offset, `latest` - go to the latest available offset, string in `Duration` format, e.g. `5m` - shift back a certain time.
    5. Maximal waiting time for messages from a topic within one call
    6. Maximum waiting time between unexpected exceptions during processing
    7. Time interval within which it is required to update partitions in case of `assign` method
    8. Additional telemetry attributes
    9. *Properties* from the official kafka client, documentation on them can be found at [link](https://kafka.apache.org/documentation/#consumerconfigs)
    10. Enables module logging
    11. Enables module metrics
    12. Configuring [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    13. Enables module tracing

=== ":simple-yaml: `YAML`"

    ```yaml
    path:
      to:
        config:
          topics: #(1)!
            - "topic1"
            - "topic2"
          topicsPattern: "topic*" #(2)!
          partitions: #(3)!
            - "1"
            - "2"
          offset: "latest" #(4)!
          pollTimeout: "5s" #(5)!
          backoffTimeout: "15s" #(6)!
          partitionRefreshInterval: "1m" #(7)!
          threads: 1 #(8)!
          driverProperties: #(9)!
            bootstrap.servers: "localhost:9093"
            group.id: "my-group-id"
          telemetry:
            logging:
              enabled: true #(10)!
            metrics:
              enabled: true #(11)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(12)!
            telemetry:
              enabled: true #(13)!
    ```

    1. Specifies the topics to which Consumer will subscribe (or specify `topicsPattern`)
    2. Specifies the pattern of topics to which the Consumer will subscribe (or `topics` is specified).
    3. Specifies the partitions of topics to be subscribed to
    4. Specifies which position in the topics the Consumer should use. Valid values are `earliest` - go to the earliest available offset, `latest` - go to the latest available offset, string in `Duration` format, e.g. `5m` - shift back a certain time.
    5. Maximal waiting time for messages from a topic within one call
    6. Maximum waiting time between unexpected exceptions during processing
    7. Time interval within which it is required to update partitions in case of `assign` method
    8. Additional telemetry attributes
    9. *Properties* from the official kafka client, documentation on them can be found at [link](https://kafka.apache.org/documentation/#consumerconfigs)
    10. Enables module logging
    11. Enables module metrics
    12. Configuring [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    13. Enables module tracing

Configuration example for connecting to topics without a group.
In this example, Consumer will be connected to all partitions in the topiq and the offset is shifted back 10 minutes.
In case of connection without `group.id`, only 1 topic can be specified:

===! ":material-code-json: `Hocon`"

    ```javascript
    path {
        to {
            config {
                pollTimeout: "3s"
                topics: "first"
                driverProperties {
                    "bootstrap.servers": "localhost:9093"
                }
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    path:
      to:
        config:
          pollTimeout: "3s"
          topics: "first,second,third"
          driverProperties:
            "bootstrap.servers": "localhost:9093"
    ```

### Signatures

Accepts `value` and `key` (optional) and `headers` (optional) from `ConsumerRecord`, after all events are processed, `commitSync()` is called:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("path.to.config")
    void process(String key, String value, Headers headers) {
        // some handler code
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("path.to.config")
    fun process(key: String, value: String, headers: Headers) {
        // some handler code
    }
    ```

Accepts `ConsumerRecord`/`ConsumerRecords`, once all `ConsumerRecords` have been processed, `commitSync()` is called:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("path.to.config")
    void process(ConsumerRecord<String, String> record) {
        // some handler code
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("path.to.config")
    fun process(record: ConsumerRecord<String, String>) {
        // some handler code
    }
    ```

Accepts `ConsumerRecord`/`ConsumerRecords` and `Consumer`.
As in the previous case, `commit` must be called manually.
Called for each `ConsumerRecord` obtained by calling `poll()`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("path.to.config")
    void process(ConsumerRecord<String, String> record, Consumer<String, String> consumer) {
        // some handler code
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("path.to.config")
    fun process(record: ConsumerRecord<String, String>, consumer: Consumer<String, String>) {
        // some handler code
    }
    ```

### Deserialization

`Deserializer` - used to deserialize `ConsumerRecord` keys and values.

Tags are supported to better customize the `Deserializer`.
Tags can be set on parameter-key, parameter-value, as well as on parameters of type `ConsumerRecord` and `ConsumerRecords`.
These tags will be set on container dependencies.

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {

        @KafkaListener("path.to.config1")
        void process1(@Tag(Sometag1.class) String key, @Tag(Sometag2.class) String value) {
            // some handler code
        }

        @KafkaListener("path.to.config2")
        void process2(ConsumerRecord<@Tag(Sometag1.class) String, @Tag(Sometag2.class) String> record) {
            // some handler code
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {
        @KafkaListener("path.to.config1")
        fun process1(@Tag(Sometag1::class) key: String, @Tag(Sometag2::class) value: String) {
            // some handler code
        }

        @KafkaListener("path.to.config2")
        fun process2(record: ConsumerRecord<@Tag(Sometag1::class) String, @Tag(Sometag2::class) String>) {
            // some handler code
        }
    }
    ```

In case deserialization from `Json` is required, the `@Json` tag can be used:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {

        @Json
        public record JsonEvent(String name, Integer code) {}

        @KafkaListener("path.to.config1")
        void process1(String key, @Json JsonEvent value) {
            // some handler code
        }

        @KafkaListener("path.to.config2")
        void process2(ConsumerRecord<String, @Json JsonEvent> record) {
            // some handler code
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {

        @Json
        data class JsonEvent(val name: String, val code: Int)

        @KafkaListener("path.to.config1")
        fun process1(key: String, @Json value: JsonEvent) {
            // some handler code
        }

        @KafkaListener("path.to.config2")
        fun process2(record: ConsumerRecord<String, @Json JsonEvent>) {
            // some handler code
        }
    }
    ```

For non-key handlers, the default is `Deserializer<byte[]>` since it simply returns unhandled bytes.

### Exception handling

If the method labeled `@KafkaListener` throws an exception, Consumer will be restarted,
because there is no general solution on how to handle this and the developer **must** decide how to handle it.

#### Deserialization errors

If you use a signature with `ConsumerRecord` or `ConsumerRecords`, you will get a value deserialization exception at the moment of calling the `key` or `value` methods.
At that point, it is worth handling it in the way you want.

The following exceptions are thrown:

* ` `ru.tinkoff.kora.kafka.common.exceptions.RecordKeyDeserializationException`.
* `ru.tinkoff.kora.kafka.common.exceptions.RecordValueDeserializationException`.

From these exceptions, you can get a raw `ConsumerRecord<byte[], byte[]>`.

If you use a signature with unpacked `key`/`value`/`headers`, you can add `Exception`, `Throwable`, `RecordKeyDeserializationException`, `RecordKeyDeserializationException` with the last argument
or `RecordValueDeserializationException`.

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {

        @KafkaListener("path.to.config")
        public void process(@Nullable String key, @Nullable String value, @Nullable Exception exception) {
            if (exception != null) {
                // handle exception
            } else {
                // handle key/value
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {

        @KafkaListener("path.to.config")
        fun process(key: String?, value: String?, exception: Exception?) {
            if (exception != null) {
                // handle exception
            } else {
                // handle key/value
            }
        }
    }
    ```

Note that all arguments become optional, meaning we expect to either have a key and value or an exception.

### Manual override

Kora provides a small wrapper over `KafkaConsumer` that allows you to easily trigger the handling of incoming events.

The container constructor is as follows:

```java
public KafkaSubscribeConsumerContainer(KafkaListenerConfig config,
                                       Deserializer<K> keyDeserializer,
                                       Deserializer<V> valueDeserializer,
                                       BaseKafkaRecordsHandler<K, V> handler) {
    this.factory = new KafkaConsumerFactory<>(config);
    this.handler = handler;
    this.keyDeserializer = keyDeserializer;
    this.valueDeserializer = valueDeserializer;
    this.config = config;
}
```

`BaseKafkaRecordsHandler<K,V>` is the basic functional interface of the handler:
```java
@FunctionalInterface
public interface BaseKafkaRecordsHandler<K, V> {
    void handle(ConsumerRecords<K, V> records, KafkaConsumer<K, V> consumer);
}
```

## Producer

Descriptions of working with [Kafka Producer](https://docs.confluent.io/platform/current/clients/producer.html)

Assume to use the `@KafkaPublisher` annotation on the interface to create `Kafka Producer`,
in order to send messages to any topic it is supposed to create a method with the signature `ProducerRecord`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyPublisher {
          void send(ProducerRecord<String, String> record);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyPublisher {
        fun send(record: ProducerRecord<String, String>)
    }
    ```

The annotation parameter indicates the path to the configuration.

### Topic

In case it is required to use typed contracts for specific topics, the `@KafkaPublisher.Topic` annotation is supposed to be used
to create such contracts:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        void send(String value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        fun send(value: String)
    } 
    ```

The annotation parameter indicates the path for the configuration of the topic.

### Configuration

`KafkaPublisherConfig` is used to configure `@KafkaPublisher`, and
`KafkaPublisherConfig.TopicConfig` is used for the `@KafkaPublisher.Topic` configuration:

===! ":material-code-json: `Hocon`"

    ```javascript
    path {
        to {
            config {
                driverProperties { //(1)!
                    "bootstrap.servers": "localhost:9093"
                }
                telemetry {
                    logging {
                        enabled = true //(2)!
                    }
                    metrics {
                        enabled = true //(3)!
                        slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(4)!
                    }
                    telemetry {
                        enabled = true //(5)!
                    }
                }
            }

            topic { //(6)!
                config {
                    topic = "my-topic" //(7)!
                    partition = 1 //(8)!
                }
            }
        }
    }
    ```

    1. *Properties* from the official kafka client, documentation on them can be found at [link](https://kafka.apache.org/documentation/#producerconfigs)
    2. Enables module logging
    3. Enables module metrics
    4. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    5. Enables module tracing
    6. Configuration of `@KafkaPublisher.Topic`.
    7. Which topic the method will send data to
    8. Which partition of the topic the method will send data (optional)

=== ":simple-yaml: `YAML`"

    ```yaml
    path:
      to:
        config:
          driverProperties: #(1)!
            bootstrap.servers: "localhost:9093"
          telemetry:
            logging:
              enabled: true #(2)!
            metrics:
              enabled: true #(3)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(4)!
            telemetry:
              enabled: true #(5)!
        
        topic: #(6)!
          config:
            topic: "my-topic" #(7)!
            partition: 1 #(8)!
    ```

    1. *Properties* from the official kafka client, documentation on them can be found at [link](https://kafka.apache.org/documentation/#producerconfigs)
    2. Enables module logging
    3. Enables module metrics
    4. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    5. Enables module tracing
    6. Configuration of `@KafkaPublisher.Topic`.
    7. Which topic the method will send data to
    8. Which partition of the topic the method will send data (optional)

### Signatures

Allows `value` and `key` (optional) and `headers` (optional) to be sent from `ProducerRecord`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        void send(String key, String value, Headers headers);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        fun send(key: String, value: String, headers: Headers)
    } 
    ```

Can be received as the result of a `RecordMetadata` operation:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        RecordMetadata send(String value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        fun send(value: String): RecordMetadata
    } 
    ```

Can be obtained as the result of a `Future<RecordMetadata>` or `CompletionStage<RecordMetadata>` operation:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        Future<RecordMetadata> send(String value);

        @KafkaPublisher.Topic("path.to.topic.config")
        CompletionStage<RecordMetadata> sendStage(V value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        fun send(value: String): Future<RecordMetadata>
    } 
    ```

It is possible to send `ProducerRecord` with or without `Callback` and combine the response with the examples above:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyPublisher {

          void send(ProducerRecord<String, String> record, Callback callback);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyPublisher {

        fun send(record: ProducerRecord<String, String>, callback: Callback)
    }
    ```

### Serialization

In order to specify which `Serializer` to take from a container, there is an option to use tags.
Tags should be set on `ProducerRecord` or `key`/`value` parameters of methods:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyKafkaProducer {

        void send(ProducerRecord<@Tag(MyTag1.class) String, @Tag(MyTag2.class) String> record);

        @KafkaPublisher.Topic("path.to.topic.config")
        void send(@Tag(MyTag1.class) String key, @Tag(MyTag2.class) String value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyKafkaProducer {

        fun send(record: ProducerRecord<@Tag(MyTag1::class) String, @Tag(MyTag2::class) String>)

        @KafkaPublisher.Topic("path.to.topic.config")
        fun send(@Tag(MyTag1::class) key: String, @Tag(MyTag2::class) value: String)
    }
    ```

If you want to serialize as Json, you should use `@Json` annotation:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyKafkaProducer {

        @Json
        record JsonEvent(String name, Integer code) {}

        void send(ProducerRecord<String, @Json JsonEvent> record);

        @KafkaPublisher.Topic("path.to.topic.config")
        void send(String key, @Json JsonEvent value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyKafkaProducer {

        @Json
        data class JsonEvent(val name: String, val code: Int)

        fun send(record: ProducerRecord<String, @Json JsonEvent>)

        @KafkaPublisher.Topic("path.to.topic.config")
        fun send(key: String, @Json value: JsonEvent)
    }
    ```

### Exception handling

In case of a submission error in a method annotated `@Topic` and which does not return `Future<RecordMetadata>` a `ru.tinkoff.kora.kafka.kora.kafka.common.exceptions.KafkaPublishException` will be thrown.
where in `cause` will lie the actual error from `KafkaProducer`.

#### Serialization errors

In case of a key/value serialization error in a method annotated with `@Topic`, `org.apache.kafka.common.errors.SerializationException` will be thrown
similar to what would happen in the case of `org.apache.kafka.kafka.clients.producer.Producer#send`.

### Transactions

It is possible to send a message to Kafka in [within a transaction](https://www.confluent.io/blog/transactions-apache-kafka/), this is supposed to use the
`@KafkaPublisher` annotation to create such a `KafkaProducer`.

It is required to first create a regular `KafkaProducer` and then use it to create a transactional Producer:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        void send(String key, String value);
    }

    @KafkaPublisher("path.to.transactional.config")
    public interface MyTransactionalPublisher extends TransactionalPublisher<MyPublisher> {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        fun send(key: String, value: String)
    }


    @KafkaPublisher("path.to.transactional.config")
    interface MyTransactionalPublisher : TransactionalPublisher<MyPublisher> 
    ```

It is expected to use `inTx` methods to send such messages, all messages within Lambda will be applied if it is successful and canceled if it fails.

=== ":fontawesome-brands-java: `Java`"

    ```java
    transactionalPublisher.inTx(producer -> {
        producer.send("username1");
        producer.send("username2");
    });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    transactionalPublisher.inTx(TransactionalConsumer {
        it.send("key1", "value1")
        it.send("key2", "value2")
    })
    ```

It is also possible to manually perform all manipulations with `KafkaProducer`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    // commit will be called on try-with-resources close
    try (var transaction = transactionalPublisher.begin()) {
        transaction.producer().send(record);
        if (somethingBad) {
            transaction.abort();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // commit will be called on try-with-resources close
    transactionalPublisher.begin().use { 
        it.producer().send(record)
        if (somethingBad) {
            it.abort()
        }
    }
    ```

#### Configuration

`KafkaPublisherConfig.TransactionConfig` is used to configure `@KafkaPublisher` with the `TransactionalPublisher` interface:

===! ":material-code-json: `Hocon`"

    ```javascript
    path {
        to {
            transactional {
                config {
                    idPrefix = "kafka-app-" //(1)!
                    maxPoolSize = 10 //(2)!
                    maxWaitTime = "10s" //(3)!
                }
            }
        }
    }
    ```

    1. Transaction identifier prefix
    2. Connection set size for transactions
    3. Maximum transaction waiting time

=== ":simple-yaml: `YAML`"

    ```yaml
    path:
      to:
        transactional:
          config:
            idPrefix: "kafka-app-" #(1)!
            maxPoolSize: 10 #(2)!
            maxWaitTime: "10s" #(3)!
    ```

    1. Transaction identifier prefix
    2. Connection set size for transactions
    3. Maximum transaction waiting time
