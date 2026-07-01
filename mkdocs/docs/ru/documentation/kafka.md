---
description: "Explains Kora Kafka consumers and producers, listener and publisher annotations, configuration, serialization, error handling, rebalance events, transactions, and telemetry tags. Use when working with @KafkaListener, @KafkaPublisher, @Topic, @Json, @Tag, KafkaModule, KafkaConsumer, KafkaProducer."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Kafka consumers and producers, listener and publisher annotations, configuration, serialization, error handling, rebalance events, transactions, and telemetry tags; key triggers include @KafkaListener, @KafkaPublisher, @Topic, @Json, @Tag, KafkaModule, KafkaConsumer, KafkaProducer, KafkaSkipRecordException."
---

Модуль `Kafka` предоставляет декларативную интеграцию с [Apache Kafka](https://kafka.apache.org/): чтение сообщений через
`@KafkaListener`, отправку сообщений через `@KafkaPublisher`, работу с сериализацией, десериализацией, транзакциями,
ошибками обработки и телеметрией.

`Apache Kafka` — это распределенная платформа потоковой передачи событий. Приложения записывают события в `topic`,
а другие приложения читают их через `consumer group` или напрямую назначенные разделы. Kora создает нужные `Consumer`
и `Producer` во время компиляции, связывает их с графом зависимостей и позволяет описывать большую часть контракта
через сигнатуры методов.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Kafka](../guides/messaging-kafka.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:kafka"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends KafkaModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:kafka")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : KafkaModule
    ```

## Потребитель { #consumer }

`Consumer` читает записи из `topic` и передает их в метод приложения. Kora сама создает контейнер потребителя,
вызывает `poll()`, применяет десериализацию, вызывает обработчик и выполняет фиксацию сдвига, если сигнатура метода
не требует ручного управления `Consumer`.

Для создания `Consumer` требуется использовать аннотацию `@KafkaListener` над методом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class SomeConsumer {
        
        @KafkaListener("kafka.someConsumer")
        void process(String key, String value) { 
            // my code
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeConsumer {

        @KafkaListener("kafka.someConsumer")
        fun process(key: String, value: String) {
            // my code
        }
    }
    ```

Параметр аннотации `@KafkaListener` указывает на путь к конфигурации `Consumer`.

В случае, если нужно разное поведение для разных `topic`, существует возможность создавать несколько подобных контейнеров,
каждый со своей конфигурацией. Выглядит это так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class SomeConsumer {
        
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
    class SomeConsumer {

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

Значение в аннотации указывает, из какой части файла конфигурации нужно брать настройки.
По смыслу это похоже на `@ConfigSource`: путь в аннотации выбирает ветку конфигурации для конкретного контейнера.

### Конфигурация { #config-consumer }

Конфигурация описывает настройки конкретного `@KafkaListener` и ниже указан пример для конфигурации по пути `kafka.someConsumer`.

Пример полной конфигурации, описанной в классе `KafkaListenerConfig` (указаны примеры значений или значения по умолчанию):

В реальной конфигурации обычно указывается либо `topics`, либо `topicsPattern`.

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

    1.  Список `topic`, на которые будет подписан `Consumer` (по умолчанию не указано, необязательно; требуется указать `topics` или `topicsPattern`)
    2.  Шаблон `topic`, на которые будет подписан `Consumer` (по умолчанию не указано, необязательно; требуется указать `topics` или `topicsPattern`)
    3.  Список разделов, который используется только при формировании имени потребителя, если не указаны `group.id`, `topics` и `topicsPattern`; назначением разделов управляет контейнер `assign` (по умолчанию не указано, необязательно)
    4.  Обрабатывать ли пустые пачки записей, если сигнатура принимает `ConsumerRecords` (по умолчанию: `false`)
    5.  Начальная позиция чтения для стратегии `assign`, когда не указан `group.id` (по умолчанию: `latest`). Допустимые значения:
        1. `earliest` - самый ранний доступный `offset`
        2. `latest` - последний доступный `offset`
        3. строка в формате `Duration`, например `5m`, - сдвиг на указанное время назад
    6.  Максимальное время ожидания сообщений из `topic` в рамках одного вызова `poll()` (по умолчанию: `5s`)
    7.  Начальное время ожидания между неожиданными исключениями во время обработки; при повторных ошибках задержка увеличивается до `60s` (по умолчанию: `15s`)
    8.  Период обновления списка разделов для стратегии `assign` (по умолчанию: `1m`)
    9.  Количество потоков, на которых будет запущен потребитель; если указать `0`, потребитель не будет запущен (по умолчанию: `1`)
    10. Время ожидания обработки перед выключением потребителя при [штатном завершении](container.md#component-lifecycle) (по умолчанию: `30s`)
    11. `Properties` официального `Kafka Consumer`; документация по ним доступна в [Apache Kafka Consumer Configs](https://kafka.apache.org/documentation/#consumerconfigs) (`обязательная`, по умолчанию не указано)
    12. Включает логирование модуля (по умолчанию: `false`)
    13. Включает метрики модуля (по умолчанию: `true`)
    14. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    15. Настройка тегов для метрик (по умолчанию: `{}`)
    16. Включает трассировку модуля (по умолчанию: `true`)
    17. Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  Список `topic`, на которые будет подписан `Consumer` (по умолчанию не указано, необязательно; требуется указать `topics` или `topicsPattern`)
    2.  Шаблон `topic`, на которые будет подписан `Consumer` (по умолчанию не указано, необязательно; требуется указать `topics` или `topicsPattern`)
    3.  Список разделов, который используется только при формировании имени потребителя, если не указаны `group.id`, `topics` и `topicsPattern`; назначением разделов управляет контейнер `assign` (по умолчанию не указано, необязательно)
    4.  Обрабатывать ли пустые пачки записей, если сигнатура принимает `ConsumerRecords` (по умолчанию: `false`)
    5.  Начальная позиция чтения для стратегии `assign`, когда не указан `group.id` (по умолчанию: `latest`). Допустимые значения:
        1. `earliest` - самый ранний доступный `offset`
        2. `latest` - последний доступный `offset`
        3. строка в формате `Duration`, например `5m`, - сдвиг на указанное время назад
    6.  Максимальное время ожидания сообщений из `topic` в рамках одного вызова `poll()` (по умолчанию: `5s`)
    7.  Начальное время ожидания между неожиданными исключениями во время обработки; при повторных ошибках задержка увеличивается до `60s` (по умолчанию: `15s`)
    8.  Период обновления списка разделов для стратегии `assign` (по умолчанию: `1m`)
    9.  Количество потоков, на которых будет запущен потребитель; если указать `0`, потребитель не будет запущен (по умолчанию: `1`)
    10. Время ожидания обработки перед выключением потребителя при [штатном завершении](container.md#component-lifecycle) (по умолчанию: `30s`)
    11. `Properties` официального `Kafka Consumer`; документация по ним доступна в [Apache Kafka Consumer Configs](https://kafka.apache.org/documentation/#consumerconfigs) (`обязательная`, по умолчанию не указано)
    12. Включает логирование модуля (по умолчанию: `false`)
    13. Включает метрики модуля (по умолчанию: `true`)
    14. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    15. Настройка тегов для метрик (по умолчанию: `{}`)
    16. Включает трассировку модуля (по умолчанию: `true`)
    17. Настройка атрибутов для трассировки (по умолчанию: `{}`)

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#kafka).

### Стратегия подключения { #consume-strategy }

Стратегия `subscribe` используется, когда в `driverProperties` указан `group.id`.
В этом режиме экземпляры приложения входят в одну `consumer group`, а `Kafka` распределяет разделы между ними так,
чтобы разные экземпляры не обрабатывали одни и те же записи одновременно.

Пример конфигурации `subscribe` стратегии:

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
        someConsumer {
            topics = ["first"]
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
        topics:
          - "first"
        driverProperties:
          "group.id": "my-group-id"
          "bootstrap.servers": "localhost:9093"
    ```

Стратегия `assign` используется, когда в `driverProperties` не указан `group.id`.
В этом режиме каждый экземпляр приложения сам назначает себе разделы выбранного `topic`, поэтому сообщения могут читаться
каждым экземпляром приложения независимо. В такой стратегии можно указать только один `topic`, а начальная позиция чтения
управляется параметром `offset`.

Такая стратегия полезна, когда одно и то же сообщение должны получить все реплики приложения: например, для сброса локального
кеша, обновления справочников в памяти или доставки служебного события каждому экземпляру приложения.

Пример конфигурации `assign` стратегии:

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
        someConsumer {
            topics = ["first"]
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
        topics:
          - "first"
        driverProperties:
          "bootstrap.servers": "localhost:9093"
    ```

### Десериализация { #deserialization }

`Deserializer` используется для десериализации ключей и значений `ConsumerRecord`.
Kora предоставляет компоненты `Deserializer` для базовых типов: `String`, `UUID`, `byte[]`, `Bytes`, `ByteBuffer`,
`Double`, `Float`, `Integer`, `Long`, `Short` и `Void`.

Для более точной настройки `Deserializer` поддерживаются теги.
Теги можно установить на параметре-ключе, параметре-значении, а так же на параметрах типа `ConsumerRecord` и `ConsumerRecords`.
Эти теги будут установлены на зависимостях контейнера.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class SomeConsumer {

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
    class SomeConsumer {
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

Если требуется десериализация из `JSON`, можно использовать тег `@Json`.
В таком случае Kora использует `JsonReader<T>` и `JsonKafkaDeserializer<T>` из модуля [JSON](json.md):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class SomeConsumer {

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
    class SomeConsumer {

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

Для потребителей, не использующих ключ, по умолчанию используется `Deserializer<byte[]>`, так как он возвращает необработанные байты.

### Обработка исключений { #exception-handling }

Если метод помеченный `@KafkaListener` выбросит исключение, то Consumer будет перезапущен,
потому что нет общего решения, как реагировать на это и разработчик **должен** сам решить как эту ситуацию обрабатывать.

#### Пропуск обработки { #exception-skipping }

В случае когда требуется пропустить обработку **конкретного события** (`ConsumerRecord`) в процессе обработки по причинам бизнес-логики, 
можно выбросить исключение `KafkaSkipRecordException` передав в конструктор реальное исключение.
В таком случае все метрики будут корректно учтены и записаны, обработка соответствующего события будет пропущена и начнется обрабатываться следующее событие.

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

В случае если хочется реализовать свои пропускаемые исключения, 
то можно использовать `SkippableRecordException` интерфейс который следует реализовать в своих исключениях.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class MyKafkaSkipRecordException extends RuntimeException implements SkippableRecordException {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class MyKafkaSkipRecordException : RuntimeException(), SkippableRecordException
    ```

#### Ошибки десериализации { #deserialization-errors }

Если вы используете сигнатуру с `ConsumerRecord` или `ConsumerRecords`, 
то вы получите исключение десериализации значения в момент вызова методов `key()` или `value()` у события.
В этот момент стоит его обработать нужным вам образом.

Выбрасываются следующие исключения:

* `ru.tinkoff.kora.kafka.common.exceptions.RecordKeyDeserializationException`
* `ru.tinkoff.kora.kafka.common.exceptions.RecordValueDeserializationException`

Из этих исключений можно получить сырой `ConsumerRecord<byte[], byte[]>`.

Если вы используете сигнатуру с распакованными `key`/`value`/`headers`, 
то можно добавить последним аргументом `Exception`, `Throwable`, `RecordKeyDeserializationException` или `RecordValueDeserializationException`,
для обработки таких ошибок.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class SomeConsumer {

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
    class SomeConsumer {

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

Обратите внимание, что все аргументы становятся необязательными, то есть мы ожидаем что у нас либо будут ключ и значение, либо исключение.

### Пользовательский тег { #custom-tag }

По умолчанию для потребителя создается автоматический тег по которому происходит внедрение, его можно посмотреть в созданном модуле на этапе компиляции.

Если по каким-то причинам вам требуется переопределить тег потребителя, можно задать его как аргумент аннотации `@KafkaListener`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class SomeConsumer {

        @KafkaListener(value = "kafka.someConsumer", tag = SomeConsumer.class)
        public void process(String value) {
          
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeConsumer {

        @KafkaListener(value = "kafka.someConsumer", tag = SomeConsumer::class)
        fun process(value: String) {

        }
    }
    ```

### События ребалансировки { #rebalance-events }

Можно слушать и реагировать на события ребалансировки с помощью свой реализации интерфейса `ConsumerAwareRebalanceListener`,
его следует предоставить как компонент по тегу потребителя:

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

### Ручное управление { #manual-override }

Kora предоставляет небольшую обёртку над `KafkaConsumer`, позволяющую легко запустить обработку входящих событий.

Конструктор контейнера выглядит следующим образом:

```java
public KafkaSubscribeConsumerContainer(KafkaListenerConfig config,
                                       Deserializer<K> keyDeserializer,
                                       Deserializer<V> valueDeserializer,
                                       BaseKafkaRecordsHandler<K, V> handler)
```

`BaseKafkaRecordsHandler<K,V>` это базовый функциональный интерфейс потребителя:
```java
@FunctionalInterface
public interface BaseKafkaRecordsHandler<K, V> {
    void handle(ConsumerRecords<K, V> records, KafkaConsumer<K, V> consumer);
}
```

### Сигнатуры { #signatures }

Доступные сигнатуры для методов `Kafka Consumer` из коробки, где под `K` подразумевается тип ключа, а под `V` тип значения сообщения.
Генератор поддерживает три семейства сигнатур: отдельные `key`/`value`, один `ConsumerRecord<K, V>` или всю пачку `ConsumerRecords<K, V>`.
Эти семейства нельзя смешивать между собой в одном методе.

#### Ключ и значение { #key-value-signature }

Сигнатура с отдельными аргументами принимает `value`, необязательный `key`, необязательные `Headers`, необязательный `Consumer<K, V>` и необязательные ошибки чтения.
Один пользовательский аргумент считается `value`, два пользовательских аргумента считаются `key` и `value` именно в таком порядке.
Если `key` не указан, тип ключа для десериализации считается `byte[]`.

Для обработки ошибки чтения можно добавить `Exception`, `RecordKeyDeserializationException` или `RecordValueDeserializationException`.
Если такой аргумент есть, Kora передаст в него ошибку чтения, а значение соответствующего `key` или `value` будет `null`.
Без такого аргумента ошибка чтения будет выброшена из обработчика, и событие будет вычитано повторно без фиксации текущего сдвига.

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
        if(exception != null) {
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
        if(exception != null) {
            // do deserialization handling work
        } else {
            // some value handling work
        }
    }
    ```

#### Событие целиком { #record-signature }

Сигнатура с `ConsumerRecord<K, V>` принимает одно событие целиком, необязательный `Consumer<K, V>` и необязательные ошибки чтения:
`Exception`, `RecordKeyDeserializationException` или `RecordValueDeserializationException`.
`Headers`, отдельные `key`/`value` и контекст телеметрии в такой сигнатуре не поддерживаются.

Если аргументы ошибок не указаны, ошибка чтения может быть выброшена при обращении к `record.key()` или `record.value()`.
Если аргументы ошибок указаны, Kora заранее вызовет `key()` и/или `value()`, поймает ошибку чтения и передаст ее в метод.

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

#### Пачка событий { #records-signature }

Сигнатура с `ConsumerRecords<K, V>` принимает всю пачку событий из одного `poll()`.
Вместе с ней можно указать только `Consumer<K, V>` и `KafkaConsumerRecordsTelemetryContext<K, V>`.
Отдельные `key`/`value`, `Headers` и аргументы ошибок чтения в такой сигнатуре не поддерживаются; ошибки чтения нужно обрабатывать при обходе событий.

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

#### Фиксация сдвига { #manual-commit }

Если в сигнатуре нет аргумента `Consumer<K, V>`, Kora фиксирует сдвиг самостоятельно: после каждого события для сигнатур `key`/`value` и `ConsumerRecord<K, V>`, либо после всей пачки для `ConsumerRecords<K, V>`.
Для этого вызывается `commitSync()`.

Если в сигнатуре есть аргумент `Consumer<K, V>`, автоматическая фиксация сдвига отключается, и обработчик полностью отвечает за вызов `commitSync()` или `commitAsync()`.
Такой режим нужен, когда нужно зафиксировать сдвиг только после внешней операции, зафиксировать несколько событий вместе или вручную управлять позицией чтения.

В режиме `subscribe` ручной `commit` фиксирует сдвиг внутри группы потребителей.
В режиме `assign` нет распределения разделов через группу потребителей, поэтому обычно важнее вручную управлять позицией через `seek()`, `pause()` и `resume()`, а не рассчитывать на групповую фиксацию сдвига.
Если обработчик завершился с ошибкой до ручной фиксации, событие или пачка будут вычитаны повторно согласно текущей позиции потребителя.

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

## Продюсер { #producer }

`Producer` отправляет записи в `topic`. Kora создает реализацию интерфейса, помеченного `@KafkaPublisher`,
подбирает `Serializer` для ключа и значения, вызывает `KafkaProducer#send` и связывает отправку с телеметрией.

Для создания `Producer` используется аннотация `@KafkaPublisher` на интерфейсе.
Чтобы отправлять сообщения в произвольный `topic`, можно объявить метод с параметром `ProducerRecord`:

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

Параметр аннотации указывает на путь до конфигурации продюсера.

### Топик { #topic }

Если требуется использовать типизированные методы для конкретных `topic`, используется аннотация `@KafkaPublisher.Topic`:

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

Параметр аннотации указывает на путь для конфигурации `topic`.

### Конфигурация { #config-producer }

Конфигурация описывает настройки конкретного `@KafkaPublisher`; ниже указан пример для конфигурации по пути `kafka.someProducer`.

Пример полной конфигурации, описанной в классе `KafkaPublisherConfig` (указаны примеры значений или значения по умолчанию):

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
                tags = { // (5)!
                  "key1" = "value1"
                  "key2" = "value2"
                }
              }
              tracing {
                enabled = true //(6)!
                attributes = { // (7)!
                  "key1" = "value1"
                  "key2" = "value2"
                }
              }
            }
        }
    }
    ```

    1.  `Properties` официального `Kafka Producer`; документация по ним доступна в [Apache Kafka Producer Configs](https://kafka.apache.org/documentation/#producerconfigs) (`обязательная`, по умолчанию не указано)
    2.  Включает логирование модуля (по умолчанию: `false`)
    3.  Включает метрики модуля (по умолчанию: `true`)
    4.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    5.  Настройка тегов для метрик (по умолчанию: `{}`)
    6.  Включает трассировку модуля (по умолчанию: `true`)
    7.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someProducer:
        driverProperties: #(1)!
          bootstrap.servers: "localhost:9093"
        telemetry:
          logging:
            enabled: false #(2)!
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

    1.  `Properties` официального `Kafka Producer`; документация по ним доступна в [Apache Kafka Producer Configs](https://kafka.apache.org/documentation/#producerconfigs) (`обязательная`, по умолчанию не указано)
    2.  Включает логирование модуля (по умолчанию: `false`)
    3.  Включает метрики модуля (по умолчанию: `true`)
    4.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    5.  Настройка тегов для метрик (по умолчанию: `{}`)
    6.  Включает трассировку модуля (по умолчанию: `true`)
    7.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

Конфигурация `topic` описывает настройки конкретного `@KafkaPublisher.Topic`; ниже указан пример для конфигурации по пути `kafka.someProducer.someTopic`.

Пример полной конфигурации, описанной в классе `KafkaPublisherConfig.TopicConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  `topic`, в который метод будет отправлять данные (`обязательная`, по умолчанию не указано)
    2.  Раздел `topic`, в который метод будет отправлять данные (по умолчанию не указано, необязательно)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someProducer:
        someTopic:
          topic: "my-topic" #(1)!
          partition: 1 #(2)!
    ```

    1.  `topic`, в который метод будет отправлять данные (`обязательная`, по умолчанию не указано)
    2.  Раздел `topic`, в который метод будет отправлять данные (по умолчанию не указано, необязательно)

### Сериализация { #serialization }

`Serializer` используется для сериализации ключей и значений `ProducerRecord`.
Kora предоставляет компоненты `Serializer` для базовых типов: `String`, `UUID`, `byte[]`, `Bytes`, `ByteBuffer`,
`Double`, `Float`, `Integer`, `Long`, `Short` и `Void`.

Для уточнения, какой `Serializer` взять из контейнера, можно использовать теги.
Теги необходимо устанавливать на параметры `ProducerRecord` или `key`/`value` методов:

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

Если требуется сериализация в `JSON`, используется тег `@Json`.
В таком случае Kora использует `JsonWriter<T>` и `JsonKafkaSerializer<T>` из модуля [JSON](json.md):

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

### Обработка исключений { #exception-handling-2 }

В случае ошибки отправки в методе, помеченном `@KafkaPublisher.Topic`, который не возвращает `Future<RecordMetadata>`,
будет выброшено `ru.tinkoff.kora.kafka.common.exceptions.KafkaPublishException`.
Исходная ошибка из `KafkaProducer` будет доступна в `cause`.

#### Ошибки сериализации { #serialization-errors }

В случае ошибки сериализации ключа или значения в методе, помеченном `@KafkaPublisher.Topic`,
будет выброшено `org.apache.kafka.common.errors.SerializationException`, как и при прямом вызове `org.apache.kafka.clients.producer.Producer#send`.

### Транзакции { #transactions }

Можно отправлять сообщения в `Kafka` в [рамках транзакции](https://www.confluent.io/blog/transactions-apache-kafka/).
Для этого используется аннотация `@KafkaPublisher` и наследование от `TransactionalPublisher`.

Сначала требуется описать обычный `KafkaProducer`, а затем использовать его тип для создания транзакционного `Producer`:

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


Для отправки в транзакции используются методы `inTx`: все сообщения внутри `lambda` будут подтверждены при успешном выполнении
и отменены при ошибке.

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

Также можно вручную управлять транзакцией через `begin()`:

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

#### Конфигурация { #config-producer-tx }

`KafkaPublisherConfig.TransactionConfig` используется для конфигурации `@KafkaPublisher` с интерфейсом `TransactionalPublisher`:

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

    1.  Префикс идентификатора транзакций; к нему будет добавлен случайный `UUID` (по умолчанию: `kora-app-`)
    2.  Максимальный размер пула транзакционных `Producer` (по умолчанию: `10`)
    3.  Максимальное время ожидания свободного `Producer` из пула (по умолчанию: `10s`)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someTransactionalProducer:
        idPrefix: "kora-app-" #(1)!
        maxPoolSize: 10 #(2)!
        maxWaitTime: "10s" #(3)!
    ```

    1.  Префикс идентификатора транзакций; к нему будет добавлен случайный `UUID` (по умолчанию: `kora-app-`)
    2.  Максимальный размер пула транзакционных `Producer` (по умолчанию: `10`)
    3.  Максимальное время ожидания свободного `Producer` из пула (по умолчанию: `10s`)

### Сигнатуры { #signatures-3 }

Доступные сигнатуры для методов `Kafka Producer` из коробки, где под `K` подразумевается тип ключа, а под `V` тип значения сообщения.
Генератор поддерживает два семейства сигнатур: отправку готового `ProducerRecord<K, V>` и отправку через метод с `@KafkaPublisher.Topic`.
Эти семейства нельзя смешивать между собой в одном методе.

#### Готовый `ProducerRecord` { #producer-record-signature }

Метод с `ProducerRecord<K, V>` используется, когда `topic`, раздел, время создания или `Headers` нужно задать на стороне вызывающего кода.
Такой метод нельзя помечать `@KafkaPublisher.Topic`, потому что все сведения об отправке уже находятся в самом `ProducerRecord`.
Дополнительно можно передать один `Callback`.

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

#### Методы с `@KafkaPublisher.Topic` { #topic-signature }

Метод с `key`, `value` и `Headers` должен быть помечен `@KafkaPublisher.Topic`.
Один пользовательский аргумент считается `value`, два пользовательских аргумента считаются `key` и `value` именно в таком порядке.
`Headers` и `Callback` можно указать дополнительно, но не больше одного аргумента каждого типа.
Если `Headers` не переданы, Kora создаст пустые заголовки.

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

#### Результат отправки { #publisher-result }

Для синхронного метода можно вернуть `void`/`Unit` или `RecordMetadata`.
В таком случае Kora вызывает `KafkaProducer#send`, ожидает завершения отправки через `Future#get()` и только после этого возвращает управление вызывающему коду.

Для асинхронной отправки можно вернуть `Future<RecordMetadata>`, `CompletionStage<RecordMetadata>` или `CompletableFuture<RecordMetadata>`.
В `Kotlin` дополнительно поддерживаются `suspend`-методы и `Deferred<RecordMetadata>`.
Если в сигнатуре есть `Callback`, Kora сначала завершает собственную телеметрию отправки, а затем вызывает пользовательский `Callback`.

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

Недопустимые сочетания: `ProducerRecord<K, V>` вместе с `@KafkaPublisher.Topic`, `ProducerRecord<K, V>` вместе с отдельными `key`/`value`/`Headers`, больше одного `Headers`, больше одного `Callback`, а также метод с отдельными `key`/`value` без `@KafkaPublisher.Topic`.
