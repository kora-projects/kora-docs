---
description: "Explains Kora Kafka consumers and producers, listener and publisher annotations, configuration, serialization, error handling, rebalance events, transactions, and telemetry tags. Use when working with @KafkaListener, @KafkaPublisher, @Topic, @Json, @Tag, KafkaModule, KafkaConsumer, KafkaProducer."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Kafka consumers and producers, listener and publisher annotations, configuration, serialization, error handling, rebalance events, transactions, and telemetry tags; key triggers include @KafkaListener, @KafkaPublisher, @Topic, @Json, @Tag, KafkaModule, KafkaConsumer, KafkaProducer, KafkaSkipRecordException."
---

The `Kafka` module provides declarative integration with [Apache Kafka](https://kafka.apache.org/): reading messages through
`@KafkaListener`, sending messages through `@KafkaPublisher`, serialization, deserialization, transactions, processing errors,
and telemetry.

`Apache Kafka` is a distributed event streaming platform. Applications write events to a `topic`, while other applications read
them through a `consumer group` or directly assigned partitions. Kora creates the required `Consumer` and `Producer` at compile time,
binds them to the dependency graph, and lets most of the contract be described through method signatures.

For a step-by-step walkthrough before the reference details, see [Kafka Messaging](../guides/messaging-kafka.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:kafka"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends KafkaModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:kafka")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : KafkaModule
    ```

## Consumer { #consumer }

`Consumer` reads records from a `topic` and passes them to an application method. Kora creates the consumer container,
calls `poll()`, applies deserialization, invokes the handler, and commits the offset unless the method signature requires
manual `Consumer` control.

Creating a `Consumer` requires using the `@KafkaListener` annotation over a method:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {
        
        @KafkaListener("kafka.someConsumer")
        void process(String key, String value) { 
            // my code
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {

        @KafkaListener("kafka.someConsumer")
        fun process(key: String, value: String) {
            // my code
        }
    }
    ```

The `@KafkaListener` annotation parameter points to the `Consumer` configuration path.

In case you need different behavior for different topics, it is possible to create several such containers,
each with its own individual configuration. It looks like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {
        
        @KafkaListener("kafka.someConsumer1")
        void processFirst(String key, String value) { 
            // some handler code
        }
        
        @KafkaListener("kafka.someConsumer2")
        void processSecond(String key, String value) {
            // some handler code
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {

        @KafkaListener("kafka.someConsumer1")
        fun processFirst(key: String, value: String) {
            // some handler code
        }

        @KafkaListener("kafka.someConsumer2")
        fun processSecond(key: String, value: String) {
            // some handler code
        }
    }
    ```

The value in the annotation indicates which part of the configuration file should be used.
Conceptually, it is similar to `@ConfigSource`: the annotation value selects the configuration branch for a specific container.

### Configuration { #config-consumer }

Configuration describes the settings of a particular `@KafkaListener` and an example for the configuration at path `kafka.someConsumer` is given below.

Example of the complete configuration described in the `KafkaListenerConfig` class (default or example values are specified):

In a real configuration, either `topics` or `topicsPattern` is usually specified.

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
        someConsumer {
            topics = ["topic1", "topic2"] //(1)!
            topicsPattern = "topic*" //(2)!
            partitions = ["0", "1"] //(3)!
            allowEmptyRecords = false //(4)!
            offset = "latest" //(5)!
            pollTimeout = "5s" //(6)!
            backoffTimeout = "15s" //(7)!
            partitionRefreshInterval = "1m" //(8)!
            threads = 1 //(9)!
            shutdownWait = "30s" //(10)!
            driverProperties { //(11)!
                "bootstrap.servers": "localhost:9093"
                "group.id": "my-group-id"
            }
            telemetry {
                logging {
                    enabled = false //(12)!
                }
                metrics {
                    enabled = true //(13)!
                    slo = [1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000] //(14)!
                    tags = { // (15)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(16)!
                    attributes = { // (17)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1.  List of `topic` values the `Consumer` subscribes to (not set by default, optional; either `topics` or `topicsPattern` must be specified)
    2.  `topic` pattern the `Consumer` subscribes to (not set by default, optional; either `topics` or `topicsPattern` must be specified)
    3.  List of partitions used only for consumer name construction when `group.id`, `topics`, and `topicsPattern` are not specified; partition assignment is controlled by the `assign` container (not set by default, optional)
    4.  Whether to process empty batches when the signature accepts `ConsumerRecords` (default: `false`)
    5.  Initial read position for the `assign` strategy when `group.id` is not specified (default: `latest`). Valid values:
        1. `earliest` - earliest available `offset`
        2. `latest` - latest available `offset`
        3. string in `Duration` format, for example `5m`, - shift back by the specified duration
    6.  Maximum time to wait for messages from a `topic` within one `poll()` call (default: `5s`)
    7.  Initial delay between unexpected processing errors; with repeated errors the delay increases up to `60s` (default: `15s`)
    8.  Partition list refresh period for the `assign` strategy (default: `1m`)
    9.  Number of threads the consumer starts on; if set to `0`, the consumer is not started (default: `1`)
    10. Time to wait for processing before stopping the consumer during [graceful shutdown](container.md#graceful-shutdown) (default: `30s`)
    11. Official `Kafka Consumer` `Properties`; see [Apache Kafka Consumer Configs](https://kafka.apache.org/documentation/#consumerconfigs) (`required`, not set by default)
    12. Enables module logging (default: `false`)
    13. Enables module metrics (default: `true`)
    14. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    15. Configures metric tags (default: `{}`)
    16. Enables module tracing (default: `true`)
    17. Configures tracing attributes (default: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someConsumer:
        topics: #(1)!
          - "topic1"
          - "topic2"
        topicsPattern: "topic*" #(2)!
        partitions: #(3)!
          - "0"
          - "1"
        allowEmptyRecords: false #(4)!
        offset: "latest" #(5)!
        pollTimeout: "5s" #(6)!
        backoffTimeout: "15s" #(7)!
        partitionRefreshInterval: "1m" #(8)!
        threads: 1 #(9)!
        shutdownWait: "30s" #(10)!
        driverProperties: #(11)!
          bootstrap.servers: "localhost:9093"
          group.id: "my-group-id"
        telemetry:
          logging:
            enabled: false #(12)!
          metrics:
            enabled: true #(13)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(14)!
            tags: #(15)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(16)!
            attributes: #(17)!
              key1: value1
              key2: value2
    ```

    1.  List of `topic` values the `Consumer` subscribes to (not set by default, optional; either `topics` or `topicsPattern` must be specified)
    2.  `topic` pattern the `Consumer` subscribes to (not set by default, optional; either `topics` or `topicsPattern` must be specified)
    3.  List of partitions used only for consumer name construction when `group.id`, `topics`, and `topicsPattern` are not specified; partition assignment is controlled by the `assign` container (not set by default, optional)
    4.  Whether to process empty batches when the signature accepts `ConsumerRecords` (default: `false`)
    5.  Initial read position for the `assign` strategy when `group.id` is not specified (default: `latest`). Valid values:
        1. `earliest` - earliest available `offset`
        2. `latest` - latest available `offset`
        3. string in `Duration` format, for example `5m`, - shift back by the specified duration
    6.  Maximum time to wait for messages from a `topic` within one `poll()` call (default: `5s`)
    7.  Initial delay between unexpected processing errors; with repeated errors the delay increases up to `60s` (default: `15s`)
    8.  Partition list refresh period for the `assign` strategy (default: `1m`)
    9.  Number of threads the consumer starts on; if set to `0`, the consumer is not started (default: `1`)
    10. Time to wait for processing before stopping the consumer during [graceful shutdown](container.md#graceful-shutdown) (default: `30s`)
    11. Official `Kafka Consumer` `Properties`; see [Apache Kafka Consumer Configs](https://kafka.apache.org/documentation/#consumerconfigs) (`required`, not set by default)
    12. Enables module logging (default: `false`)
    13. Enables module metrics (default: `true`)
    14. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    15. Configures metric tags (default: `{}`)
    16. Enables module tracing (default: `true`)
    17. Configures tracing attributes (default: `{}`)

Module metrics are described in the [Metrics Reference](metrics.md#kafka) section.

### Consume strategy { #consume-strategy }

`subscribe` strategy involves the use of [group.id](https://www.confluent.io/blog/configuring-apache-kafka-consumer-group-ids/),
to group the executors so that they do not duplicate the reading of records from their queue across multiple application instances.

Example of `subscribe` strategy configuration:

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
        someConsumer {
            topics: "first"
            driverProperties {
              "group.id": "my-group-id"
              "bootstrap.servers": "localhost:9093"
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someConsumer:
        topics: "first"
        driverProperties:
          "group.id": "my-group-id"
          "bootstrap.servers": "localhost:9093"
    ```

`assign` connection strategy implies that each instance of the application reads messages from the topic simultaneously with others,
i.e., messages are duplicated between all instances of the application within the topic.
This strategy is useful, for example, when all application replicas must receive the same message at once: to reset a local cache,
update local reference data, or handle a service event.
To use this strategy, simply **do not specify** `group.id` in the consumer configuration.
However, only one topic can be specified at a time in this strategy.

Example of `assign` strategy configuration:

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
        someConsumer {
            topics: "first"
            driverProperties {
              "bootstrap.servers": "localhost:9093"
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someConsumer:
        topics: "first"
        driverProperties:
          "bootstrap.servers": "localhost:9093"
    ```

### Signatures { #signatures }

Available signatures for out-of-the-box `Kafka Consumer` methods, where `K` refers to the key type and `V` to the message value type.
The generator supports three signature families: separate `key`/`value` arguments, a single `ConsumerRecord<K, V>`, or a whole `ConsumerRecords<K, V>` batch.
These families cannot be mixed in the same method.

#### Key and value { #key-value-signature }

A signature with separate arguments accepts `value`, optional `key`, optional `Headers`, optional `Consumer<K, V>`, and optional deserialization errors.
One user argument is treated as `value`; two user arguments are treated as `key` and `value` in that exact order.
If `key` is not declared, the key deserialization type is considered to be `byte[]`.

To handle deserialization errors, add `Exception`, `RecordKeyDeserializationException`, or `RecordValueDeserializationException`.
When such an argument is present, Kora passes the deserialization error to it, and the corresponding `key` or `value` is passed as `null`.
Without such an argument, the deserialization error is thrown from the handler, and the record is read again without committing the current offset.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.someConsumer")
    void process(K key, V value, Headers headers) {
        // some value handling work
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("kafka.someConsumer")
    fun process(key: K, value: V, headers: Headers) {
        // some value handling work
    }
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.someOtherConsumer")
    void process(@Nullable V value, @Nullable Exception exception) {
        if (exception != null) {
            // do deserialization handling work
        } else {
            // some value handling work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("kafka.someOtherConsumer")
    fun process(value: V?, exception: Exception?) {
        if (exception != null) {
            // do deserialization handling work
        } else {
            // some value handling work
        }
    }
    ```

#### Whole record { #record-signature }

A signature with `ConsumerRecord<K, V>` accepts one whole record, optional `Consumer<K, V>`, and optional deserialization errors:
`Exception`, `RecordKeyDeserializationException`, or `RecordValueDeserializationException`.
`Headers`, separate `key`/`value` arguments, and the telemetry context are not supported in this signature.

If error arguments are not declared, the deserialization error can be thrown when calling `record.key()` or `record.value()`.
If error arguments are declared, Kora calls `key()` and/or `value()` beforehand, catches the deserialization error, and passes it to the method.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.someConsumer")
    void process(ConsumerRecord<K, V> record) {
        try {
            var key = record.key();
            var value = record.value();

            // some value handling work
        } catch (RecordKeyDeserializationException e) {
            // do deserialization handling work
        } catch (RecordValueDeserializationException e) {
            // do deserialization handling work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("kafka.someConsumer")
    fun process(record: ConsumerRecord<K, V>) {
        try {
            val key = record.key()
            val value = record.value()

            // some value handling work
        } catch (e: RecordKeyDeserializationException) {
            // do deserialization handling work
        } catch (e: RecordValueDeserializationException) {
            // do deserialization handling work
        }
    }
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.someConsumer")
    void process(ConsumerRecord<K, V> record,
                 @Nullable RecordKeyDeserializationException keyException,
                 @Nullable RecordValueDeserializationException valueException) {
        if (keyException != null || valueException != null) {
            // do deserialization handling work
            return;
        }

        var key = record.key();
        var value = record.value();
        // some value handling work
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("kafka.someConsumer")
    fun process(
        record: ConsumerRecord<K, V>,
        keyException: RecordKeyDeserializationException?,
        valueException: RecordValueDeserializationException?,
    ) {
        if (keyException != null || valueException != null) {
            // do deserialization handling work
            return
        }

        val key = record.key()
        val value = record.value()
        // some value handling work
    }
    ```

#### Batch of records { #records-signature }

A signature with `ConsumerRecords<K, V>` accepts the whole batch of records from one `poll()`.
Together with it, only `Consumer<K, V>` and `KafkaConsumerRecordsTelemetryContext<K, V>` can be declared.
Separate `key`/`value` arguments, `Headers`, and deserialization error arguments are not supported in this signature; deserialization errors should be handled while iterating over records.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.someConsumer")
    void process(ConsumerRecords<K, V> records) {
        for (var record : records) {
            try {
                var key = record.key();
                var value = record.value();

                // some value handling work
            } catch (RecordKeyDeserializationException e) {
                // do deserialization handling work
            } catch (RecordValueDeserializationException e) {
                // do deserialization handling work
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("kafka.someConsumer")
    fun process(records: ConsumerRecords<K, V>) {
        for (record in records) {
            try {
                val key = record.key()
                val value = record.value()

                // some value handling work
            } catch (e: RecordKeyDeserializationException) {
                // do deserialization handling work
            } catch (e: RecordValueDeserializationException) {
                // do deserialization handling work
            }
        }
    }
    ```

#### Offset commit { #manual-commit }

If the signature does not declare a `Consumer<K, V>` argument, Kora commits the offset automatically: after each record for `key`/`value` and `ConsumerRecord<K, V>` signatures, or after the whole batch for `ConsumerRecords<K, V>`.
It does this by calling `commitSync()`.

If the signature declares a `Consumer<K, V>` argument, automatic offset commit is disabled, and the handler is fully responsible for calling `commitSync()` or `commitAsync()`.
This mode is useful when the offset should be committed only after an external operation, several records should be committed together, or the read position should be controlled manually.

In `subscribe` mode, a manual `commit` commits the offset inside the consumer group.
In `assign` mode, partitions are not coordinated through a consumer group, so it is usually more important to manage the position manually with `seek()`, `pause()`, and `resume()` instead of relying on a group offset commit.
If the handler fails before the manual commit, the record or batch will be read again according to the current consumer position.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.someConsumer")
    void process(ConsumerRecord<K, V> record, Consumer<K, V> consumer) {
        try {
            var key = record.key();
            var value = record.value();

            // some value handling work
        } catch (RecordKeyDeserializationException e) {
            // do deserialization handling work
        } catch (RecordValueDeserializationException e) {
            // do deserialization handling work
        } finally {
            consumer.commitSync();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("kafka.someConsumer")
    fun process(record: ConsumerRecord<K, V>, consumer: Consumer<K, V>) {
        try {
            val key = record.key()
            val value = record.value()

            // some value handling work
        } catch (e: RecordKeyDeserializationException) {
            // do deserialization handling work
        } catch (e: RecordValueDeserializationException) {
            // do deserialization handling work
        } finally {
            consumer.commitSync()
        }
    }
    ```

### Deserialization { #deserialization }

`Deserializer` is used to deserialize `ConsumerRecord` keys and values.
Kora provides `Deserializer` components for basic types: `String`, `UUID`, `byte[]`, `Bytes`, `ByteBuffer`, `Double`, `Float`,
`Integer`, `Long`, `Short`, and `Void`.

Tags are supported to better customize the `Deserializer`.
Tags can be set on parameter-key, parameter-value, as well as on parameters of type `ConsumerRecord` and `ConsumerRecords`.
These tags will be set on container dependencies.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {

        @KafkaListener("kafka.someConsumer1")
        void process1(@Tag(Sometag1.class) String key, @Tag(Sometag2.class) String value) {
            // some handler code
        }

        @KafkaListener("kafka.someConsumer2")
        void process2(ConsumerRecord<@Tag(Sometag1.class) String, @Tag(Sometag2.class) String> record) {
            // some handler code
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {
        @KafkaListener("kafka.someConsumer1")
        fun process1(@Tag(Sometag1::class) key: String, @Tag(Sometag2::class) value: String) {
            // some handler code
        }

        @KafkaListener("kafka.someConsumer2")
        fun process2(record: ConsumerRecord<@Tag(Sometag1::class) String, @Tag(Sometag2::class) String>) {
            // some handler code
        }
    }
    ```

If deserialization from `JSON` is required, use the `@Json` tag.
In this case, Kora uses `JsonReader<T>` and `JsonKafkaDeserializer<T>` from the [JSON](json.md) module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {

        @Json
        public record JsonEvent(String name, Integer code) {}

        @KafkaListener("kafka.someConsumer1")
        void process1(String key, @Json JsonEvent value) {
            // some handler code
        }

        @KafkaListener("kafka.someConsumer2")
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

        @KafkaListener("kafka.someConsumer1")
        fun process1(key: String, @Json value: JsonEvent) {
            // some handler code
        }

        @KafkaListener("kafka.someConsumer2")
        fun process2(record: ConsumerRecord<String, @Json JsonEvent>) {
            // some handler code
        }
    }
    ```

For non-key handlers, the default is `Deserializer<byte[]>` since it simply returns unhandled bytes.

### Exception handling { #exception-handling }

If the method labeled `@KafkaListener` throws an exception, Consumer will be restarted,
because there is no general solution on how to handle this and the developer **must** decide how to handle it.

#### Exception skipping { #exception-skipping }

If you need to skip processing a specific event (`ConsumerRecord`) during processing for business logic reasons,
you can throw a `KafkaSkipRecordException` by passing the actual exception to the constructor.
In this case, all metrics will be correctly accounted for and recorded, processing of the corresponding event will be skipped, and the next event will begin to be processed.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class SomeConsumer {

        @KafkaListener("kafka.someConsumer1")
        void process1(String key, String value) {
            if ("skip".equals(value)) {
                throw new KafkaSkipRecordException(new IllegalArgumentException("Want to skip!"))
            }
            // some handler code
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeConsumer {

        @KafkaListener("kafka.someConsumer1")
        fun process1(key: String, value: String) {
            if (value == "skip") {
                throw KafkaSkipRecordException(IllegalArgumentException("Want to skip!"))
            }
            // some handler code
        }
    }
    ```

If you want to implement your own skippable exceptions,
you can use the `SkippableRecordException` interface, which should be implemented in your exceptions.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class MyKafkaSkipRecordException extends RuntimeException implements SkippableRecordException {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class MyKafkaSkipRecordException : RuntimeException(), SkippableRecordException
    ```

#### Deserialization errors { #deserialization-errors }

If you use a signature with `ConsumerRecord` or `ConsumerRecords`, you will get a value deserialization exception at the moment of calling the `key` or `value` methods.
At that point, it is worth handling it in the way you want.

The following exceptions are thrown:

* ` `ru.tinkoff.kora.kafka.common.exceptions.RecordKeyDeserializationException`.
* `ru.tinkoff.kora.kafka.common.exceptions.RecordValueDeserializationException`.

From these exceptions, you can get a raw `ConsumerRecord<byte[], byte[]>`.

If you use a signature with unpacked `key`/`value`/`headers`, you can add `Exception`, `Throwable`, `RecordKeyDeserializationException`, `RecordKeyDeserializationException` with the last argument
or `RecordValueDeserializationException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {

        @KafkaListener("kafka.someConsumer")
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

        @KafkaListener("kafka.someConsumer")
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

### Custom tag { #custom-tag }

Automatic tag is created for the consumer by default, it can be viewed in the generated module at compile time.

If for some reason you need to override the consumer tag, you can set it as an argument to the `@KafkaListener` annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {

        @KafkaListener(value = "kafka.someConsumer", tag = ConsumerService.class)
        public void process(String value) {
          
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {

        @KafkaListener(value = "kafka.someConsumer", tag = ConsumerService::class)
        fun process(value: String) {

        }
    }
    ```

### Rebalance events { #rebalance-events }

You can listen and react to rebalance events with your implementation of the `ConsumerAwareRebalanceListener` interface,
it should be provided as a component by the consumer tag:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(SomeListenerProcessTag.class)
    @Component
    public final class SomeListener implements ConsumerAwareRebalanceListener {

        @Override
        public void onPartitionsRevoked(Consumer<?, ?> consumer, Collection<TopicPartition> partitions) {
            
        }

        @Override
        public void onPartitionsAssigned(Consumer<?, ?> consumer, Collection<TopicPartition> partitions) {

        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SomeListenerProcessTag::class)
    @Component
    class SomeListener : ConsumerAwareRebalanceListener {

        override fun onPartitionsRevoked(consumer: Consumer<*, *>, partitions: Collection<TopicPartition>) {
            
        }
        
        override fun onPartitionsAssigned(consumer: Consumer<*, *>, partitions: Collection<TopicPartition>) {
            
        }
    }
    ```

### Manual override { #manual-override }

Kora provides a small wrapper over `KafkaConsumer` that allows you to easily trigger the handling of incoming events.

The container constructor is as follows:

```java
public KafkaSubscribeConsumerContainer(KafkaListenerConfig config,
                                       Deserializer<K> keyDeserializer,
                                       Deserializer<V> valueDeserializer,
                                       BaseKafkaRecordsHandler<K, V> handler)
```

`BaseKafkaRecordsHandler<K,V>` is the basic functional interface of the handler:
```java
@FunctionalInterface
public interface BaseKafkaRecordsHandler<K, V> {
    void handle(ConsumerRecords<K, V> records, KafkaConsumer<K, V> consumer);
}
```

## Producer { #producer }

`Producer` sends records to a `topic`. Kora creates an implementation of the interface annotated with `@KafkaPublisher`,
selects a `Serializer` for the key and value, calls `KafkaProducer#send`, and connects sending with telemetry.

To create a `Producer`, use the `@KafkaPublisher` annotation on an interface.
To send messages to an arbitrary `topic`, declare a method with a `ProducerRecord` parameter:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {
          void send(ProducerRecord<String, String> record);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyPublisher {
        fun send(record: ProducerRecord<String, String>)
    }
    ```

The annotation parameter indicates the path to the producer configuration.

### Topic { #topic }

If typed methods are required for specific `topic` values, use the `@KafkaPublisher.Topic` annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        void send(String value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(value: String)
    } 
    ```

The annotation parameter indicates the path for the `topic` configuration.

### Configuration { #config-producer }

Configuration describes the settings of a particular `@KafkaPublisher`; below is an example for the `kafka.someProducer` configuration path.

Example of the complete configuration described in the `KafkaPublisherConfig` class (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
        someProducer {
            driverProperties { //(1)!
              "bootstrap.servers": "localhost:9093"
            }
            telemetry {
              logging {
                enabled = false //(2)!
              }
              metrics {
                enabled = true //(3)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(4)!
                tags = { //(5)!
                  "key1" = "value1"
                  "key2" = "value2"
                }
              }
              tracing {
                enabled = true //(6)!
                attributes = { //(7)!
                  "key1" = "value1"
                  "key2" = "value2"
                }
              }
            }
        }
    }
    ```

    1.  Official `Kafka Producer` `Properties`; see [Apache Kafka Producer Configs](https://kafka.apache.org/documentation/#producerconfigs) (`required`, not set by default)
    2.  Enables module logging (default: `false`)
    3.  Enables module metrics (default: `true`)
    4.  Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    5.  Configures metric tags (default: `{}`)
    6.  Enables module tracing (default: `true`)
    7.  Configures tracing attributes (default: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someProducer:
        driverProperties: #(1)!
          bootstrap.servers: "localhost:9093"
        telemetry:
          logging:
            enabled: true #(2)!
          metrics:
            enabled: true #(3)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(4)!
            tags: #(5)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(6)!
            attributes: #(7)!
              key1: value1
              key2: value2
    ```

    1.  Official `Kafka Producer` `Properties`; see [Apache Kafka Producer Configs](https://kafka.apache.org/documentation/#producerconfigs) (`required`, not set by default)
    2.  Enables module logging (default: `false`)
    3.  Enables module metrics (default: `true`)
    4.  Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    5.  Configures metric tags (default: `{}`)
    6.  Enables module tracing (default: `true`)
    7.  Configures tracing attributes (default: `{}`)

`topic` configuration describes the settings of a particular `@KafkaPublisher.Topic`; below is an example for the `kafka.someProducer.someTopic` configuration path.

Example of the complete configuration described in the `KafkaPublisherConfig.TopicConfig` class (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
      someProducer {
        someTopic {
          topic = "my-topic" //(1)!
          partition = 1 //(2)!
        }
      }
    }
    ```

    1. `topic` where the method sends data (`required`, not set by default)
    2. `topic` partition where the method sends data (not set by default, optional)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someProducer:
        someTopic:
          topic: "my-topic" #(1)!
          partition: 1 #(2)!
    ```

    1. `topic` where the method sends data (`required`, not set by default)
    2. `topic` partition where the method sends data (not set by default, optional)

### Serialization { #serialization }

`Serializer` is used to serialize `ProducerRecord` keys and values.
Kora provides `Serializer` components for basic types: `String`, `UUID`, `byte[]`, `Bytes`, `ByteBuffer`, `Double`, `Float`,
`Integer`, `Long`, `Short`, and `Void`.

To specify which `Serializer` to take from the container, tags can be used.
Tags should be set on `ProducerRecord` or `key`/`value` parameters of methods:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyKafkaProducer {

        void send(ProducerRecord<@Tag(MyTag1.class) String, @Tag(MyTag2.class) String> record);

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        void send(@Tag(MyTag1.class) String key, @Tag(MyTag2.class) String value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyKafkaProducer {

        fun send(record: ProducerRecord<@Tag(MyTag1::class) String, @Tag(MyTag2::class) String>)

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(@Tag(MyTag1::class) key: String, @Tag(MyTag2::class) value: String)
    }
    ```

If serialization to `JSON` is required, use the `@Json` tag.
In this case, Kora uses `JsonWriter<T>` and `JsonKafkaSerializer<T>` from the [JSON](json.md) module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyKafkaProducer {

        @Json
        record JsonEvent(String name, Integer code) {}

        void send(ProducerRecord<String, @Json JsonEvent> record);

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        void send(String key, @Json JsonEvent value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyKafkaProducer {

        @Json
        data class JsonEvent(val name: String, val code: Int)

        fun send(record: ProducerRecord<String, @Json JsonEvent>)

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(key: String, @Json value: JsonEvent)
    }
    ```

### Exception handling { #exception-handling-2 }

If a send error happens in a method annotated with `@KafkaPublisher.Topic` that does not return `Future<RecordMetadata>`,
`ru.tinkoff.kora.kafka.common.exceptions.KafkaPublishException` is thrown.
The original error from `KafkaProducer` is available in `cause`.

#### Serialization errors { #serialization-errors }

If a key or value serialization error happens in a method annotated with `@KafkaPublisher.Topic`,
`org.apache.kafka.common.errors.SerializationException` is thrown, just like with a direct `org.apache.kafka.clients.producer.Producer#send` call.

### Transactions { #transactions }

Messages can be sent to `Kafka` [within a transaction](https://www.confluent.io/blog/transactions-apache-kafka/).
For this, use the `@KafkaPublisher` annotation and extend `TransactionalPublisher`.

First, describe a regular `KafkaProducer`, and then use its type to create a transactional `Producer`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        void send(String key, String value);
    }

    @KafkaPublisher("kafka.someTransactionalProducer")
    public interface MyTransactionalPublisher extends TransactionalPublisher<MyPublisher> {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(key: String, value: String)
    }


    @KafkaPublisher("kafka.someTransactionalProducer")
    interface MyTransactionalPublisher : TransactionalPublisher<MyPublisher> 
    ```

Use `inTx` methods to send messages in a transaction: all messages inside the `lambda` are committed on successful execution
and aborted on error.

===! ":fontawesome-brands-java: `Java`"

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

It is also possible to manage the transaction manually through `begin()`:

===! ":fontawesome-brands-java: `Java`"

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

#### Configuration { #config-producer-tx }

`KafkaPublisherConfig.TransactionConfig` is used to configure `@KafkaPublisher` with the `TransactionalPublisher` interface:

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
        someTransactionalProducer {
            idPrefix = "kora-app-" //(1)!
            maxPoolSize = 10 //(2)!
            maxWaitTime = "10s" //(3)!
        }
    }
    ```

    1.  Transaction identifier prefix; a random `UUID` will be appended to it (default: `kora-app-`)
    2.  Maximum size of the transactional `Producer` pool (default: `10`)
    3.  Maximum time to wait for a free `Producer` from the pool (default: `10s`)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someTransactionalProducer:
        idPrefix: "kora-app-" #(1)!
        maxPoolSize: 10 #(2)!
        maxWaitTime: "10s" #(3)!
    ```

    1.  Transaction identifier prefix; a random `UUID` will be appended to it (default: `kora-app-`)
    2.  Maximum size of the transactional `Producer` pool (default: `10`)
    3.  Maximum time to wait for a free `Producer` from the pool (default: `10s`)

### Signatures { #signatures-3 }

Available signatures for out-of-the-box `Kafka Producer` methods, where `K` refers to the key type and `V` to the message value type.
The generator supports two signature families: sending a ready `ProducerRecord<K, V>` and sending through a method annotated with `@KafkaPublisher.Topic`.
These families cannot be mixed in the same method.

#### Ready `ProducerRecord` { #producer-record-signature }

A method with `ProducerRecord<K, V>` is used when the `topic`, partition, timestamp, or `Headers` should be set by the calling code.
Such a method cannot be annotated with `@KafkaPublisher.Topic`, because all send details are already contained in the `ProducerRecord`.
One `Callback` can be passed additionally.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {

        void send(ProducerRecord<K, V> record);

        void send(ProducerRecord<K, V> record, Callback callback);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyPublisher {

        fun send(record: ProducerRecord<K, V>)

        fun send(record: ProducerRecord<K, V>, callback: Callback)
    } 
    ```

#### Methods with `@KafkaPublisher.Topic` { #topic-signature }

A method with `key`, `value`, and `Headers` must be annotated with `@KafkaPublisher.Topic`.
One user argument is treated as `value`; two user arguments are treated as `key` and `value` in that exact order.
`Headers` and `Callback` can be declared additionally, but only one argument of each type is allowed.
If `Headers` is not passed, Kora creates empty headers.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        void send(V value);

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        void send(K key, V value);

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        void send(K key, V value, Headers headers);

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        void send(K key, V value, Headers headers, Callback callback);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(value: V)

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(key: K, value: V)

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(key: K, value: V, headers: Headers)

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(key: K, value: V, headers: Headers, callback: Callback)
    }
    ```

#### Send result { #publisher-result }

For a synchronous method, the return type can be `void`/`Unit` or `RecordMetadata`.
In this case, Kora calls `KafkaProducer#send`, waits for send completion through `Future#get()`, and only then returns control to the caller.

For asynchronous sending, the return type can be `Future<RecordMetadata>`, `CompletionStage<RecordMetadata>`, or `CompletableFuture<RecordMetadata>`.
In `Kotlin`, `suspend` methods and `Deferred<RecordMetadata>` are also supported.
If the signature contains a `Callback`, Kora first completes its own send telemetry and then calls the user `Callback`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        RecordMetadata send(V value);

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        Future<RecordMetadata> sendFuture(V value);

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        CompletionStage<RecordMetadata> sendStage(V value);

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        CompletableFuture<RecordMetadata> sendCompletableFuture(V value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(value: V): RecordMetadata

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        suspend fun sendSuspend(value: V): RecordMetadata

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(value: String): Future<RecordMetadata>

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(value: String): CompletionStage<RecordMetadata>

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(value: String): CompletableFuture<RecordMetadata>

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(value: String): Deferred<RecordMetadata>
    } 
    ```

Invalid combinations are: `ProducerRecord<K, V>` together with `@KafkaPublisher.Topic`, `ProducerRecord<K, V>` together with separate `key`/`value`/`Headers`, more than one `Headers`, more than one `Callback`, and a method with separate `key`/`value` without `@KafkaPublisher.Topic`.
