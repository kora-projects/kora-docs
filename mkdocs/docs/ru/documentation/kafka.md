Модуль для создания декларативных [Apache Kafka](https://kafka.apache.org/) `Consumer` и `Producer` с помощью аннотаций.

## Подключение

===! ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:kafka"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends KafkaModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:kafka")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : KafkaModule
    ```

## Потребитель

Описания работы с [Kafka Consumer](https://docs.confluent.io/platform/current/clients/consumer.html)

Для создания `Consumer` требуется использовать аннотацию `@KafkaListener` над методом:

===! ":fontawesome-brands-java: `Java`"

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

Параметр аннотации `@KafkaListener` указывает на путь к конфигурации `Consumer`'а.

В случае, если нужно разное поведение для разных топиков, существует возможность создавать несколько подобных контейнеров, 
каждый со своим индивидуальным конфигом. Выглядит это так:

===! ":fontawesome-brands-java: `Java`"

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

Значение в аннотации указывает, из какой части файла конфигурации нужно брать настройки. В том, что касается получения конфигурации — работает аналогично `@ConfigSource`

### Конфигурация

Конфигурация описывает настройки конкретного `@KafkaListener` и ниже указан пример для конфигурации по пути `path.to.config`.

Пример полной конфигурации, описанной в классе `KafkaListenerConfig` (указаны примеры значений или значения по умолчанию):

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
              enabled = false //(10)!
            }
            metrics {
              enabled = true //(11)!
              slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(12)!
            }
            tracing {
              enabled = true //(13)!
            }
          }
        }
      }
    }
    ```

    1.  Указываются топики на которые будет подписан Consumer (**обязательный** либо указывается `topicsPattern`)
    2.  Указываются паттерн топиков на которые будет подписан Consumer (**обязательный** либо указывается `topics`)
    3.  Указываются партиции топиков на которые требуется подписаться
    4.  Работает только если не указан `group.id`. Определяет стратегнию какую позицию в топике должен использовать Consumer. Допустимые значение:
        1. `earliest` - самый ранний доступный offset
        2. `latest` - последний доступный offset
        3. Строка в формате `Duration` (например `5m`) - сдвиг на определённое время назад
    5.  Максиимальное время ожидания сообщений из топика в рамках одного вызова
    6.  Максимальное время ожидания между неожиданными исключениями во время обработки
    7.  Временной интервал в рамках которого требуется делать обновление партиций в случае `assign` метода 
    8.  Количество потоков на которых будет запущен потребитель для параллельной обработки (если будет равен 0 то ни один потребитель не будет запущен вообще)
    9.  *Properties* из официального клиента кафки, документацию по ним можно посмотреть по [ссылке](https://kafka.apache.org/documentation/#consumerconfigs) (**обязательный**)
    10.  Включает логгирование модуля (по умолчанию `false`)
    11.  Включает метрики модуля (по умолчанию `true`)
    12.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    13.  Включает трассировку модуля (по умолчанию `true`)

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
              enabled: false #(10)!
            metrics:
              enabled: true #(11)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(12)!
            telemetry:
              enabled: true #(13)!
    ```

    1.  Указываются топики на которые будет подписан Consumer (**обязательный** либо указывается `topicsPattern`)
    2.  Указываются паттерн топиков на которые будет подписан Consumer (**обязательный** либо указывается `topics`)
    3.  Указываются партиции топиков на которые требуется подписаться
    4.  Работает только если не указан `group.id`. Определяет стратегнию какую позицию в топике должен использовать Consumer. Допустимые значение:
        1. `earliest` - самый ранний доступный offset
        2. `latest` - последний доступный offset
        3. Строка в формате `Duration` (например `5m`) - сдвиг на определённое время назад
    5.  Максиимальное время ожидания сообщений из топика в рамках одного вызова
    6.  Максимальное время ожидания между неожиданными исключениями во время обработки
    7.  Временной интервал в рамках которого требуется делать обновление партиций в случае `assign` метода 
    8.  Количество потоков на которых будет запущен потребитель для параллельной обработки (если будет равен 0 то ни один потребитель не будет запущен вообще)
    9.  *Properties* из официального клиента кафки, документацию по ним можно посмотреть по [ссылке](https://kafka.apache.org/documentation/#consumerconfigs) (**обязательный**)
    10.  Включает логгирование модуля (по умолчанию `false`)
    11.  Включает метрики модуля (по умолчанию `true`)
    12.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    13.  Включает трассировку модуля (по умолчанию `true`)

### Стратегия подключения

`subscribe` стратегия подразумевает использование [group.id](https://medium.com/@kirill.sereda/kafka-%D0%B4%D0%BB%D1%8F-%D1%81%D0%B0%D0%BC%D1%8B%D1%85-%D0%BC%D0%B0%D0%BB%D0%B5%D0%BD%D1%8C%D0%BA%D0%B8%D1%85-f42864cb1bfb),
чтобы объединить исполнителей в группы и они не дублировали вычитывание записей из своего очереди в рамках нескольких экземпляров приложений.

В случае же если надо чтобы каждый экземпляр приложения читал сообщения из топика одновременно с другими, предполагается использовать `assign` стратегию,
для этого надо просто **не указывать** `group.id` в конфигурации потребителя, но в такой стратегии можно указать одновременно лишь 1 топик.

Пример конфигурации `assign` стратегии:

===! ":material-code-json: `Hocon`"

    ```javascript
    path {
      to {
        config {
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
          topics: "first"
          driverProperties:
            "bootstrap.servers": "localhost:9093"
    ```

### Десериализация

`Deserializer` - используется для десериализации ключей и значений `ConsumerRecord`.

Для более точной настройки `Deserializer` поддерживаются теги.
Теги можно установить на параметре-ключе, параметре-значении, а так же на параметрах типа `ConsumerRecord` и `ConsumerRecords`.
Эти теги будут установлены на зависимостях контейнера.

===! ":fontawesome-brands-java: `Java`"

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

В случае если требуется десериализация из `Json`, то можно использовать тег `@Json`:

===! ":fontawesome-brands-java: `Java`"

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
    }
    ```

Для обработчиков, не использующих ключ, по умолчанию используется `Deserializer<byte[]>` т.к. он просто возвращает не обработанные байты.

### Обработка исключений

Если метод помеченный `@KafkaListener` выбросит исключение, то Consumer будет перезапущен,
потому что нет общего решения, как реагировать на это и разработчик **должен** сам решить как эту ситуацию обрабатывать.

#### Ошибки десериализации

Если вы используете сигнатуру с `ConsumerRecord` или `ConsumerRecords`, то вы получите исключение десериализации значения в момент вызова методов `key` или `value`.
В этот момент стоит его обработать нужным вам образом.

Выбрасываются следующие исключения:

* `ru.tinkoff.kora.kafka.common.exceptions.RecordKeyDeserializationException`
* `ru.tinkoff.kora.kafka.common.exceptions.RecordValueDeserializationException`

Из этих исключений можно получить сырой `ConsumerRecord<byte[], byte[]>`.

Если вы используете сигнатуру с распакованными `key`/`value`/`headers`, то можно добавить последним аргументом `Exception`, `Throwable`, `RecordKeyDeserializationException`
или `RecordValueDeserializationException`.

===! ":fontawesome-brands-java: `Java`"

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

Обратите внимание, что все аргументы становятся необязательными, то есть мы ожидаем что у нас либо будут ключ и значение, либо исключение.

### Пользовательский тег

По умолчанию для потребителя создается автоматический тег по которому происходит внедрение, его можно посмотреть в созданном модуле на этапе компиляции.

Если по каким-то причинам вам требуется переопределить тег потребителя, можно задать его как аргумент аннотации `@KafkaListener`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {

        @KafkaListener(value = "path.to.config", tag = ConsumerService.class)
        public void process(String value) {
          
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {

        @KafkaListener(value = "path.to.config", tag = ConsumerService::class)
        fun process(value: String) {

        }
    }
    ```

### События ребалансировки

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

### Ручное управление

Kora предоставляет небольшую обёртку над `KafkaConsumer`, позволяющую легко запустить обработку входящих событий.

Конструктор контейнера выглядит следующим образом:

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

`BaseKafkaRecordsHandler<K,V>` это базовый функциональный интерфейс обработчика:
```java
@FunctionalInterface
public interface BaseKafkaRecordsHandler<K, V> {
    void handle(ConsumerRecords<K, V> records, KafkaConsumer<K, V> consumer);
}
```

### Сигнатуры

Доступные сигнатуры для методов Kafka потребителя из коробки, где под `K` подразумевается тип ключа и под `V` тип значения сообщения.

Позволяет принимать `value` (обязательный), `key` (опционально), `Headers` (опционально) от `ConsumerRecord`,
`Exception` (опционально) в случае ошибки сериализации/соединения и после обработки всех событий вызывается `commitSync()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("path.to.config")
    void process(K key, V value, Headers headers) {
        // some handler code
    }

    @KafkaListener("path.to.other.config")
    void process(@Nullable V value, @Nullable Exception exception) {
        // some handler code
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("path.to.config")
    fun process(key: K, value: V, headers: Headers) {
        // some handler code
    }

    @KafkaListener("path.to.other.config")
    fun process(value: V?, exception: Exception?) {
        // some handler code
    }
    ```

Принимает `ConsumerRecord`/`ConsumerRecords` и `KafkaConsumerRecordsTelemetryContext`/`KafkaConsumerRecordTelemetryContext` (опционально) после обработки вызывается `commitSync()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("path.to.config")
    void process(ConsumerRecord<K, V> record) {
        // some handler code
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("path.to.config")
    fun process(record: ConsumerRecord<K, V>) {
        // some handler code
    }
    ```

Принимает `ConsumerRecord`/`ConsumerRecords` и `Consumer`.
Вызывается для каждого `ConsumerRecord` полученного при вызове `poll()`:

В данном случае `commit` нужно **вызывать вручную**.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("path.to.config")
    void process(ConsumerRecord<K, V> record, Consumer<K, V> consumer) {
        // some handler code
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("path.to.config")
    fun process(record: ConsumerRecord<K, V>, consumer: Consumer<K, V>) {
        // some handler code
    }
    ```

## Продюсер

Описания работы с [Kafka Producer](https://docs.confluent.io/platform/current/clients/producer.html)

Предполагается использовать аннотацию `@KafkaPublisher` на интерфейсе для создания `Kafka Producer`,
для того чтобы отправлять сообщения в любой топик предполагается создание метода с сигнатурой `ProducerRecord`:

===! ":fontawesome-brands-java: `Java`"

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

Параметр аннотации указывает на путь до конфигурации.

### Топик

В случае если требуется использовать типизированные контракты на определенные топики то предполагается использование аннотации `@KafkaPublisher.Topic`
для создания таких контрактов:

===! ":fontawesome-brands-java: `Java`"

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

Параметр аннотации указывает на путь для конфигурации топика.

### Конфигурация

Конфигурация описывает настройки конкретного `@KafkaPublisher` и ниже указан пример для конфигурации по пути `path.to.config`.

Пример полной конфигурации, описанной в классе `KafkaPublisherConfig` (указаны примеры значений или значения по умолчанию):

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
              enabled = false //(2)!
            }
            metrics {
              enabled = true //(3)!
              slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(4)!
            }
            tracing {
              enabled = true //(5)!
            }
          }
        }
      }
    }
    ```

    1.  *Properties* из официального клиента кафки, документацию по ним можно посмотреть по [ссылке](https://kafka.apache.org/documentation/#producerconfigs) (**обязательный**)
    2.  Включает логгирование модуля (по умолчанию `false`)
    3.  Включает метрики модуля (по умолчанию `true`)
    4.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    5.  Включает трассировку модуля (по умолчанию `true`)

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
    ```

    1.  *Properties* из официального клиента кафки, документацию по ним можно посмотреть по [ссылке](https://kafka.apache.org/documentation/#producerconfigs) (**обязательный**)
    2.  Включает логгирование модуля (по умолчанию `false`)
    3.  Включает метрики модуля (по умолчанию `true`)
    4.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    5.  Включает трассировку модуля (по умолчанию `true`)

Конфигурация топика описывает настройки конкретного `@KafkaPublisher.Topic` и ниже указан пример для конфигурации по пути `path.to.topic.config`.

Пример полной конфигурации, описанной в классе `KafkaPublisherConfig.TopicConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    path {
      to {
        topic {
          config {
            topic = "my-topic" //(2)!
            partition = 1 //(3)!
          }
        }
      }
    }
    ```

    1.  В какой топик метод будет отправлять данные (**обязательный**)
    2.  В какой partition топика метод будет отправлять данные (по умолчанию отсутвует)

=== ":simple-yaml: `YAML`"

    ```yaml
    path:
      to:
        topic:
          config:
            topic: "my-topic" #(1)!
            partition: 1 #(1)!
    ```

    1.  В какой топик метод будет отправлять данные (**обязательный**)
    2.  В какой partition топика метод будет отправлять данные (по умолчанию отсутвует)

### Сериализация

Для уточнения какой `Serializer` взять из контейнера есть возможность использовать теги.
Теги необходимо устанавливать на параметры `ProducerRecord` или `key`/`value` методов:

===! ":fontawesome-brands-java: `Java`"

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

В случае если хочется сериализовать как Json то следует использовать `@Json` аннотацию:

===! ":fontawesome-brands-java: `Java`"

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

### Обработка исключений

В случае ошибки отправки методе проаннотированным `@Topic` и который не возвращает `Future<RecordMetadata>` будет выброшено `ru.tinkoff.kora.kafka.common.exceptions.KafkaPublishException`
где в `cause` будет лежать реальная ошибка из `KafkaProducer`.

#### Ошибки сериализации

В случае ошибки сериализации ключа/значения в методе проаннотированным `@Topic` будет выброшено `org.apache.kafka.common.errors.SerializationException`
аналогично как это было бы в случае `org.apache.kafka.clients.producer.Producer#send`

### Транзакции

Возможно отправлять сообщение в Kafka в [рамках транзакции](https://www.confluent.io/blog/transactions-apache-kafka/), для этого предполагается использовать
аннотацию `@KafkaPublisher` для создания такого `KafkaProducer`.

Требуется сначала создать обычного `KafkaProducer` а затем его использовать для создания транзакционного Producer'а:

===! ":fontawesome-brands-java: `Java`"

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


Предполагается использовать методы `inTx` для отправки таких сообщений, все сообщения в рамках Lambda будут применены в случае успешного ее выполнения и отменены в случае ошибки.

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

Также возможно в ручную произвести все манипуляции с `KafkaProducer`:

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

#### Конфигурация

`KafkaPublisherConfig.TransactionConfig` используется для конфигурации `@KafkaPublisher` с интерфейсом `TransactionalPublisher`:

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

    1.  Префикс индетификатора транзакций
    2.  Размер набора соединений для транзакций
    3.  Максимальное время ожидания транзакции

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

    1.  Префикс индетификатора транзакций
    2.  Размер набора соединений для транзакций
    3.  Максимальное время ожидания транзакции

### Сигнатуры

Доступные сигнатуры для методов Kafka продюсера из коробки, где под `K` подразумевается тип ключа и под `V` тип значения сообщения.

Позволяет отправлять `value` и `key` (опционально) и `headers` (опционально) от `ProducerRecord`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        void send(K key, V value, Headers headers);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        fun send(key: K, value: V, headers: Headers)
    } 
    ```


===! ":fontawesome-brands-java: `Java`"

    Можно получать как результат операции `RecordMetadata` либо `Future<RecordMetadata>`:

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        RecordMetadata send(V value);

        @KafkaPublisher.Topic("path.to.topic.config")
        Future<RecordMetadata> sendFuture(V value);

        @KafkaPublisher.Topic("path.to.topic.config")
        CompletionStage<RecordMetadata> sendStage(V value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Можно получать как результат операции `RecordMetadata` и иметь модификатор `suspend`:

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyPublisher {

        @KafkaPublisher.Topic("path.to.topic.config")
        fun send(value: V): RecordMetadata

        @KafkaPublisher.Topic("path.to.topic.config")
        suspend fun sendSuspend(value: V): RecordMetadata
    } 
    ```

Возможна отправка `ProducerRecord` и `Callback` (опционально) и комбинировать сигнатуры ответа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("path.to.config")
    public interface MyPublisher {

          void send(ProducerRecord<K, V> record, Callback callback);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("path.to.config")
    interface MyPublisher {

        fun send(record: ProducerRecord<K, V>, callback: Callback)
    }
    ```
