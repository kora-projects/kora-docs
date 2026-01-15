Модуль для создания декларативных [Apache Kafka](https://kafka.apache.org/) `Consumer` и `Producer` с помощью аннотаций.

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:kafka"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends KafkaModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
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
    final class SomeConsumer {
        
        @KafkaListener("kafka.someConsume")
        void process(String key, String value) { 
            // my code
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeConsumer {

        @KafkaListener("kafka.someConsume")
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

Значение в аннотации указывает, из какой части файла конфигурации нужно брать настройки. В том, что касается получения конфигурации — работает аналогично `@ConfigSource`

### Конфигурация

Конфигурация описывает настройки конкретного `@KafkaListener` и ниже указан пример для конфигурации по пути `kafka.someConsumer`.

Пример полной конфигурации, описанной в классе `KafkaListenerConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
        someConsumer {
            topics = ["topic1", "topic2"] //(1)!
            topicsPattern = "topic*" //(2)!
            allowEmptyRecords = false //(3)!
            offset = "latest" //(4)!
            pollTimeout = "5s" //(5)!
            backoffTimeout = "15s" //(6)!
            partitionRefreshInterval = "1m" //(7)!
            threads = 1 //(8)!
            shutdownWait = "30s" //(9)!
            driverProperties { //(10)!
                "bootstrap.servers": "localhost:9093"
                "group.id": "my-group-id"
            }
            telemetry {
                logging {
                    enabled = false //(11)!
                }
                metrics {
                    enabled = true //(12)!
                    slo = [1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000] //(12)!
                }
                tracing {
                    enabled = true //(14)!
                }
            }
        }
    }
    ```

    1.  Указываются топики на которые будет подписан Consumer (**обязательный** либо указывается `topicsPattern`)
    2.  Указываются паттерн топиков на которые будет подписан Consumer (**обязательный** либо указывается `topics`)
    3.  Обрабатывать ли пустые записи в случае если сигнатура принимает `ConsumerRecords`
    4.  Работает только если не указан `group.id`. Определяет стратегнию какую позицию в топике должен использовать Consumer. Допустимые значение:
        1. `earliest` - самый ранний доступный offset
        2. `latest` - последний доступный offset
        3. Строка в формате `Duration` (например `5m`) - сдвиг на определённое время назад
    5.  Максиимальное время ожидания сообщений из топика в рамках одного вызова
    6.  Максимальное время ожидания между неожиданными исключениями во время обработки
    7.  Временной интервал в рамках которого требуется делать обновление партиций в случае `assign` метода 
    8.  Количество потоков на которых будет запущен потребитель для параллельной обработки (если будет равен 0 то ни один потребитель не будет запущен вообще)
    9. Время ожидания обработки перед выключением потребителя в случае [штатного завершения](container.md#_24)
    10.  *Properties* из официального клиента кафки, документацию по ним можно посмотреть по [ссылке](https://kafka.apache.org/documentation/#consumerconfigs) (**обязательный**)
    11. Включает логгирование модуля (по умолчанию `false`)
    12. Включает метрики модуля (по умолчанию `true`)
    13. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    14. Включает трассировку модуля (по умолчанию `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someConsumer:
        topics: #(1)!
          - "topic1"
          - "topic2"
        topicsPattern: "topic*" #(2)!
        allowEmptyRecords: false #(3)!
        offset: "latest" #(4)!
        pollTimeout: "5s" #(5)!
        backoffTimeout: "15s" #(6)!
        partitionRefreshInterval: "1m" #(7)!
        threads: 1 #(8)!
        shutdownWait: "30s" #(9)!
        driverProperties: #(10)!
          bootstrap.servers: "localhost:9093"
          group.id: "my-group-id"
        telemetry:
          logging:
            enabled: false #(11)!
          metrics:
            enabled: true #(12)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(12)!
          telemetry:
            enabled: true #(14)!
    ```

    1.  Указываются топики на которые будет подписан Consumer (**обязательный** либо указывается `topicsPattern`)
    2.  Указываются паттерн топиков на которые будет подписан Consumer (**обязательный** либо указывается `topics`)
    3.  Обрабатывать ли пустые записи в случае если сигнатура принимает `ConsumerRecords`
    4.  Работает только если не указан `group.id`. Определяет стратегнию какую позицию в топике должен использовать Consumer. Допустимые значение:
        1. `earliest` - самый ранний доступный offset
        2. `latest` - последний доступный offset
        3. Строка в формате `Duration` (например `5m`) - сдвиг на определённое время назад
    5.  Максиимальное время ожидания сообщений из топика в рамках одного вызова
    6.  Максимальное время ожидания между неожиданными исключениями во время обработки
    7.  Временной интервал в рамках которого требуется делать обновление партиций в случае `assign` метода 
    8.  Количество потоков на которых будет запущен потребитель для параллельной обработки (если будет равен 0 то ни один потребитель не будет запущен вообще)
    9. Время ожидания обработки перед выключением потребителя в случае [штатного завершения](container.md#_24)
    10.  *Properties* из официального клиента кафки, документацию по ним можно посмотреть по [ссылке](https://kafka.apache.org/documentation/#consumerconfigs) (**обязательный**)
    11. Включает логгирование модуля (по умолчанию `false`)
    12. Включает метрики модуля (по умолчанию `true`)
    13. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    14. Включает трассировку модуля (по умолчанию `true`)

### Стратегия подключения

`subscribe` стратегия подразумевает использование [group.id](https://medium.com/@kirill.sereda/kafka-%D0%B4%D0%BB%D1%8F-%D1%81%D0%B0%D0%BC%D1%8B%D1%85-%D0%BC%D0%B0%D0%BB%D0%B5%D0%BD%D1%8C%D0%BA%D0%B8%D1%85-f42864cb1bfb),
чтобы объединить исполнителей в группы и они не дублировали вычитывание записей из своей очереди в рамках нескольких экземпляров приложений.

Пример конфигурации `subscribe` стратегии:

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

`assign` стратегия подключения подразумевает, что каждый экземпляр приложения читает сообщения из топика одновременно с другими,
то есть сообщения дублируются между всеми экземплярами приложения в рамках топика.
Для использования такой стратегии надо просто **не указывать** `group.id` в конфигурации потребителя, 
но в такой стратегии можно указать одновременно лишь 1 топик.

Пример конфигурации `assign` стратегии:

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

### Десериализация

`Deserializer` - используется для десериализации ключей и значений `ConsumerRecord`.

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

В случае если требуется десериализация из `Json`, то можно использовать тег `@Json`:

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

Для потребителей, не использующих ключ, по умолчанию используется `Deserializer<byte[]>` т.к. он просто возвращает не обработанные байты.

### Обработка исключений

Если метод помеченный `@KafkaListener` выбросит исключение, то Consumer будет перезапущен,
потому что нет общего решения, как реагировать на это и разработчик **должен** сам решить как эту ситуацию обрабатывать.

#### Пропуск обработки

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

#### Ошибки десериализации

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

### Пользовательский тег

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
                                       BaseKafkaRecordsHandler<K, V> handler)
```

`BaseKafkaRecordsHandler<K,V>` это базовый функциональный интерфейс потребителя:
```java
@FunctionalInterface
public interface BaseKafkaRecordsHandler<K, V> {
    void handle(ConsumerRecords<K, V> records, KafkaConsumer<K, V> consumer);
}
```

### Сигнатуры

Доступные сигнатуры для методов Kafka потребителя из коробки, где под `K` подразумевается тип ключа и под `V` тип значения сообщения.

Работа потребителя начинается с вызова `poll()` для пачки `ConsumerRecords<K, V>`, каждое событие по аргументам передается в потребителя.
Потребитель может принимать `value` (обязательный), `key` (опциональный), `Headers` (опциональный) аргумент от `ConsumerRecord<K, V>`,
после обработки **каждого** события вызывается `commitSync()`.

Учитывайте что при использовании такой сигнатуры в случае ошибки чтения ключа/значения потребитель уйдет 
в бесконечный цикл повторных вычитываний без фиксации текущего сдвига по топику.

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

Рекомендуется дополнительно использовать в потребителе аргумент `Exception` (опциональный), 
который будет сигнализировать о случаях ошибки чтения ключа/значения.

Учитывайте что в таком случае все значения становятся опциональными, т.к. может вернуться либо результат, либо ошибка.

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

Возможно также принимать аргументом `ConsumerRecord<K, V>`, в таком случае ошибка чтения ключа/значения 
может быть выброшена при обращении к методам `key()`/`value()` у события.

Работа потребителя начинается с вызова `poll()` для пачки `ConsumerRecords<K, V>` и передаёт каждое событие `ConsumerRecord<K, V>` по отдельности в потребителя.
Потребитель принимает `ConsumerRecord` и `KafkaConsumerRecordsTelemetryContext`/`KafkaConsumerRecordTelemetryContext` (опционально)
и после обработки **каждого** события вызывается `commitSync()`:

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

Возможно также принимать аргументом `ConsumerRecords<K, V>` и обрабатывать всю пачку самостоятельно.

Вызывается `poll()` для пачки `ConsumerRecords<K, V>` и передаёт всю пачку событий в потребитель.
Потребитель принимает `ConsumerRecords` и `KafkaConsumerRecordsTelemetryContext`/`KafkaConsumerRecordTelemetryContext` (опционально)
и после обработки **всей пачки** событий вызывается `commitSync()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.someConsumer")
    void process(ConsumerRecords<K, V> record) {
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
    fun process(record: ConsumerRecords<K, V>) {
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

Можно также контролировать самостоятельно, как и когда вызывать фиксацию сдвига по топику у потребителя.
Такая сигнатура доступна как для одного события, так и для пачки событий.

В случае если аргументом принимается `Consumer<K, V>`, то `commit` всегда нужно **вызывать самостоятельно**.

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
            consumer.commitSync()
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

## Продюсер

Описания работы с [Kafka Producer](https://docs.confluent.io/platform/current/clients/producer.html)

Предполагается использовать аннотацию `@KafkaPublisher` на интерфейсе для создания `Kafka Producer`,
для того чтобы отправлять сообщения в любой топик предполагается создание метода с сигнатурой `ProducerRecord`:

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

### Топик

В случае если требуется использовать типизированные контракты на определенные топики 
то предполагается использование аннотации `@KafkaPublisher.Topic` для создания таких контрактов:

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

Параметр аннотации указывает на путь для конфигурации топика.

### Конфигурация

Конфигурация описывает настройки конкретного `@KafkaPublisher` и ниже указан пример для конфигурации по пути `kafka.someConsumer`.

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
              }
              tracing {
                enabled = true //(5)!
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
          telemetry:
            enabled: true #(5)!
    ```

    1.  *Properties* из официального клиента кафки, документацию по ним можно посмотреть по [ссылке](https://kafka.apache.org/documentation/#producerconfigs) (**обязательный**)
    2.  Включает логгирование модуля (по умолчанию `false`)
    3.  Включает метрики модуля (по умолчанию `true`)
    4.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    5.  Включает трассировку модуля (по умолчанию `true`)

Конфигурация топика описывает настройки конкретного `@KafkaPublisher.Topic` и ниже указан пример для конфигурации по пути `kafka.someProducer.someTopic`.

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

    1.  В какой топик метод будет отправлять данные (**обязательный**)
    2.  В какой partition топика метод будет отправлять данные (по умолчанию отсутвует)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someProducer:
        someTopic:
          topic: "my-topic" #(1)!
          partition: 1 #(2)!
    ```

    1.  В какой топик метод будет отправлять данные (**обязательный**)
    2.  В какой partition топика метод будет отправлять данные (по умолчанию отсутвует)

### Сериализация

Для уточнения какой `Serializer` взять из контейнера есть возможность использовать теги.
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

В случае если хочется сериализовать как Json то следует использовать `@Json` аннотацию:

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

### Обработка исключений

В случае ошибки отправки методе проаннотированным `@Topic` и который не возвращает `Future<RecordMetadata>` будет выброшено `ru.tinkoff.kora.kafka.common.exceptions.KafkaPublishException`
где в `cause` будет лежать реальная ошибка из `KafkaProducer`.

#### Ошибки сериализации

В случае ошибки сериализации ключа/значения в методе проаннотированным `@Topic` будет выброшено `org.apache.kafka.common.errors.SerializationException`
аналогично как это было бы в случае `org.apache.kafka.clients.producer.Producer#send`

### Транзакции

Возможно отправлять сообщение в Kafka в [рамках транзакции](https://www.confluent.io/blog/transactions-apache-kafka/), для этого предполагается использовать
аннотацию `@KafkaPublisher` и наследование интерфейса `TransactionalPublisher` для создания такого `KafkaProducer`.

Требуется сначала создать обычного `KafkaProducer` а затем его использовать для создания транзакционного Producer'а:

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

Также возможно вручную произвести все манипуляции с `KafkaProducer`:

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
    kafka {
        someTransactionalProducer {
            idPrefix = "kafka-app-" //(1)!
            maxPoolSize = 10 //(2)!
            maxWaitTime = "10s" //(3)!
        }
    }
    ```

    1.  Префикс индетификатора транзакций
    2.  Размер набора соединений для транзакций
    3.  Максимальное время ожидания транзакции

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someTransactionalProducer:
        idPrefix: "kafka-app-" #(1)!
        maxPoolSize: 10 #(2)!
        maxWaitTime: "10s" #(3)!
    ```

    1.  Префикс индетификатора транзакций
    2.  Размер набора соединений для транзакций
    3.  Максимальное время ожидания транзакции

### Сигнатуры

Доступные сигнатуры для методов Kafka продюсера из коробки, где под `K` подразумевается тип ключа и под `V` тип значения сообщения.

Позволяет отправлять `value` (обязательный) и `key` (опциональный) и `headers` (опциональный) от `ProducerRecord`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        void send(K key, V value, Headers headers);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun send(key: K, value: V, headers: Headers)
    } 
    ```

===! ":fontawesome-brands-java: `Java`"

    Можно получать как результат операции `RecordMetadata` либо `Future<RecordMetadata>` либо `CompletionStage<RecordMetadata>`:

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        RecordMetadata send(V value);

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        Future<RecordMetadata> sendFuture(V value);

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        CompletionStage<RecordMetadata> sendStage(V value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Можно получать как результат операции `RecordMetadata` либо иметь модификатор `suspend` либо `Future<RecordMetadata>` либо `CompletionStage<RecordMetadata>` либо `Deferred<RecordMetadata>`:

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
        fun send(value: String): Deferred<RecordMetadata>
    } 
    ```

Возможна отправка `ProducerRecord` и `Callback` (опционально) и комбинировать сигнатуры ответа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {

          void send(ProducerRecord<K, V> record, Callback callback);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyPublisher {

        fun send(record: ProducerRecord<K, V>, callback: Callback)
    }
    ```

