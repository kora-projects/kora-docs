---
description: "Explains Kora Kafka consumers and producers, listener and publisher annotations, configuration, serialization, error handling, rebalance events, transactions, and telemetry. Use when working with @KafkaListener, @KafkaPublisher, @KafkaPublisher.Topic, @Json, @Tag, KafkaModule, KafkaListenerConfig, KafkaPublisherConfig, TransactionalPublisher."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Kafka consumers and producers, listener and publisher annotations, configuration, serialization, error handling, rebalance events, transactions, and telemetry; key triggers include @KafkaListener, @KafkaPublisher, @KafkaPublisher.Topic, @Json, @Tag, KafkaModule, KafkaListenerConfig, KafkaPublisherConfig, TransactionalPublisher, KafkaSkipRecordException, KafkaPublishException, RecordValueDeserializationException, ConsumerAwareRebalanceListener."
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
    annotationProcessor "io.koraframework:annotation-processors" //(1)!
    implementation "io.koraframework:kafka"
    ```

    1. Процессор аннотаций создает контейнеры потребителей и реализации продюсеров во время компиляции. Без него `@KafkaListener` и `@KafkaPublisher` ничего не создают, а сборка графа падает на отсутствующей зависимости.

    Модуль:
    ```java
    @KoraApp
    public interface Application extends KafkaModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(1)!
    implementation("io.koraframework:kafka")
    ```

    1. Процессор `KSP` создает контейнеры потребителей и реализации продюсеров во время компиляции. Без него `@KafkaListener` и `@KafkaPublisher` ничего не создают, а сборка графа падает на отсутствующей зависимости.

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : KafkaModule
    ```

Модуль построен поверх официального клиента `Apache Kafka` и напрямую использует его контракты `Consumer`, `Producer`,
`ConsumerRecord`, `ProducerRecord`, `Serializer` и `Deserializer`, поэтому любая настройка драйвера доступна через `driverProperties`.

## Потребитель { #consumer }

`Consumer` читает записи из `topic` и передает их в метод приложения. Kora сама создает контейнер потребителя,
вызывает `poll()`, применяет десериализацию, вызывает обработчик и выполняет фиксацию сдвига, если сигнатура метода
не требует ручного управления `Consumer`.

Для создания `Consumer` требуется использовать аннотацию `@KafkaListener` над методом:

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

Параметр аннотации `@KafkaListener` указывает на путь конфигурации `Consumer`.
Класс, в котором объявлен метод, сам должен быть компонентом графа — сгенерированный контейнер получает его как зависимость.

Если нужно разное поведение для разных топиков, можно создать несколько таких контейнеров,
каждый со своей собственной конфигурацией. Выглядит это так:

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

Значение в аннотации указывает, какая часть файла конфигурации будет использоваться.
Концептуально это похоже на `@ConfigSource`: значение аннотации выбирает ветку конфигурации для конкретного контейнера.

### Конфигурация { #config-consumer }

Конфигурация описывает настройки конкретного `@KafkaListener`, ниже приведен пример конфигурации по пути `kafka.someConsumer`.

Основные параметры конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
        someConsumer {
            topics = ["topic1", "topic2"] //(1)!
            offset = "latest" //(2)!
            pollTimeout = "5s" //(3)!
            threads = 1 //(4)!
            driverProperties { //(5)!
                "bootstrap.servers": "localhost:9093"
                "group.id": "my-group-id"
            }
        }
    }
    ```

    1.  Список `topic` на которые подписывается потребитель (`обязательно` указать либо `topics`, либо `topicsPattern`)
    2.  Начальная позиция чтения (по умолчанию: `latest`). Допустимые значения: `earliest`, `latest` или сдвиг во времени (например `5m`)
    3.  Максимальное время ожидания сообщений (по умолчанию: `5s`)
    4.  Количество потоков потребителя (по умолчанию: `1`)
    5.  Официальные `Properties` для `Kafka Consumer` (`обязательное`, без значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someConsumer:
        topics:
          - "topic1"
          - "topic2" #(1)!
        offset: "latest" #(2)!
        pollTimeout: "5s" #(3)!
        threads: 1 #(4)!
        driverProperties: #(5)!
          "bootstrap.servers": "localhost:9093"
          "group.id": "my-group-id"
    ```

    1.  Список `topic` на которые подписывается потребитель (`обязательно` указать либо `topics`, либо `topicsPattern`)
    2.  Начальная позиция чтения (по умолчанию: `latest`). Допустимые значения: `earliest`, `latest` или сдвиг во времени (например `5m`)
    3.  Максимальное время ожидания сообщений (по умолчанию: `5s`)
    4.  Количество потоков потребителя (по умолчанию: `1`)
    5.  Официальные `Properties` для `Kafka Consumer` (`обязательное`, без значения по умолчанию)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классе `KafkaListenerConfig` (указаны значения по умолчанию либо примерные значения):

    В реальной конфигурации обычно указывается либо `topics`, либо `topicsPattern`.

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
                initializationFailTimeout = "30s" //(10)!
                driverProperties { //(11)!
                    "bootstrap.servers": "localhost:9093"
                    "group.id": "my-group-id"
                }
                telemetry {
                    logging {
                        enabled = false //(12)!
                    }
                    metrics {
                        enabled = false //(13)!
                        driverMetrics = false //(14)!
                        slo = [1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000] //(15)!
                        tags = { //(16)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                    tracing {
                        enabled = true //(17)!
                        attributes = { //(18)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                }
            }
        }
        ```

        1.  Список `topic` на которые подписывается `Consumer` (по умолчанию отсутствует, опционально; должен быть указан либо `topics`, либо `topicsPattern`)
        2.  Шаблон `topic` на которые подписывается `Consumer` (по умолчанию отсутствует, опционально; должен быть указан либо `topics`, либо `topicsPattern`)
            Поддерживается только стратегией `subscribe`; стратегия `assign` отвергает его при старте и требует явного списка `topics`.
        3.  Обрабатывать ли пустые пачки, когда сигнатура принимает `ConsumerRecords` (по умолчанию: `false`)
            Если `false` и `ConsumerRecords` пустой (нет сообщений), метод потребителя не будет вызван.
            Если `true`, метод будет вызван с пустым `ConsumerRecords` (полезно для периодических проверок).
        4.  Начальная позиция чтения для стратегии `assign`, когда `group.id` не указан (по умолчанию: `latest`). Допустимые значения:
            1. `earliest` - самый ранний доступный `offset`
            2. `latest` - самый поздний доступный `offset`
            3. строка в формате `Duration`, например `5m`, - сдвиг назад на указанную длительность
               Формат: число + единица (ms, s, m, h, d). Примеры: `5m` = 5 минут назад, `1h` = 1 час назад.
        5.  Максимальное время ожидания сообщений из `topic` в рамках одного вызова `poll()` (по умолчанию: `5s`)
        6.  Начальная задержка между непредвиденными ошибками обработки; при повторяющихся ошибках задержка удваивается вплоть до `60s` (по умолчанию: `15s`)
            Если потребитель выбрасывает непредвиденное исключение (не `KafkaSkipRecordException`),
            Kora перезапустит потребителя с задержкой `backoffTimeout`, чтобы избежать циклических ошибок.
        7.  Период обновления списка разделов для стратегии `assign` (по умолчанию: `1m`)
        8.  Количество потоков, на которых запускается потребитель; при значении `0` потребитель не запускается (по умолчанию: `1`)
        9.  Время ожидания обработки перед остановкой потребителя при [штатном завершении](container.md#graceful-shutdown) (по умолчанию: `30s`)
        10. Максимальное время ожидания при старте приложения, пока каждый поток потребителя не выполнит первый `poll()` (по умолчанию отсутствует, опционально)
            Если время истекло, старт приложения завершается ошибкой. Если параметр не указан, потребитель подключается в фоне и недоступный брокер не блокирует старт.
        11. Официальные `Properties` для `Kafka Consumer`, смотрите [Apache Kafka Consumer Configs](https://kafka.apache.org/documentation/#consumerconfigs) (`обязательное`, по умолчанию отсутствует)
        12. Включает логирование модуля (по умолчанию: `false`)
        13. Включает метрики модуля (по умолчанию: `false`)
        14. Регистрирует метрики драйвера `Apache Kafka` у используемого `KafkaConsumer` в `MeterRegistry` (по умолчанию: `false`)
        15. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        16. Настройка тегов метрик (по умолчанию: `{}`)
        17. Включает трассировку модуля (по умолчанию: `true`)
        18. Настройка атрибутов трассировки (по умолчанию: `{}`)

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
            initializationFailTimeout: "30s" #(10)!
            driverProperties: #(11)!
              bootstrap.servers: "localhost:9093"
              group.id: "my-group-id"
            telemetry:
              logging:
                enabled: false #(12)!
              metrics:
                enabled: false #(13)!
                driverMetrics: false #(14)!
                slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(15)!
                tags: #(16)!
                  key1: value1
                  key2: value2
              tracing:
                enabled: true #(17)!
                attributes: #(18)!
                  key1: value1
                  key2: value2
        ```

        1.  Список `topic` на которые подписывается `Consumer` (по умолчанию отсутствует, опционально; должен быть указан либо `topics`, либо `topicsPattern`)
        2.  Шаблон `topic` на которые подписывается `Consumer` (по умолчанию отсутствует, опционально; должен быть указан либо `topics`, либо `topicsPattern`)
            Поддерживается только стратегией `subscribe`; стратегия `assign` отвергает его при старте и требует явного списка `topics`.
        3.  Обрабатывать ли пустые пачки, когда сигнатура принимает `ConsumerRecords` (по умолчанию: `false`)
            Если `false` и `ConsumerRecords` пустой (нет сообщений), метод потребителя не будет вызван.
            Если `true`, метод будет вызван с пустым `ConsumerRecords` (полезно для периодических проверок).
        4.  Начальная позиция чтения для стратегии `assign`, когда `group.id` не указан (по умолчанию: `latest`). Допустимые значения:
            1. `earliest` - самый ранний доступный `offset`
            2. `latest` - самый поздний доступный `offset`
            3. строка в формате `Duration`, например `5m`, - сдвиг назад на указанную длительность
               Формат: число + единица (ms, s, m, h, d). Примеры: `5m` = 5 минут назад, `1h` = 1 час назад.
        5.  Максимальное время ожидания сообщений из `topic` в рамках одного вызова `poll()` (по умолчанию: `5s`)
        6.  Начальная задержка между непредвиденными ошибками обработки; при повторяющихся ошибках задержка удваивается вплоть до `60s` (по умолчанию: `15s`)
            Если потребитель выбрасывает непредвиденное исключение (не `KafkaSkipRecordException`),
            Kora перезапустит потребителя с задержкой `backoffTimeout`, чтобы избежать циклических ошибок.
        7.  Период обновления списка разделов для стратегии `assign` (по умолчанию: `1m`)
        8.  Количество потоков, на которых запускается потребитель; при значении `0` потребитель не запускается (по умолчанию: `1`)
        9.  Время ожидания обработки перед остановкой потребителя при [штатном завершении](container.md#graceful-shutdown) (по умолчанию: `30s`)
        10. Максимальное время ожидания при старте приложения, пока каждый поток потребителя не выполнит первый `poll()` (по умолчанию отсутствует, опционально)
            Если время истекло, старт приложения завершается ошибкой. Если параметр не указан, потребитель подключается в фоне и недоступный брокер не блокирует старт.
        11. Официальные `Properties` для `Kafka Consumer`, смотрите [Apache Kafka Consumer Configs](https://kafka.apache.org/documentation/#consumerconfigs) (`обязательное`, по умолчанию отсутствует)
        12. Включает логирование модуля (по умолчанию: `false`)
        13. Включает метрики модуля (по умолчанию: `false`)
        14. Регистрирует метрики драйвера `Apache Kafka` у используемого `KafkaConsumer` в `MeterRegistry` (по умолчанию: `false`)
        15. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        16. Настройка тегов метрик (по умолчанию: `{}`)
        17. Включает трассировку модуля (по умолчанию: `true`)
        18. Настройка атрибутов трассировки (по умолчанию: `{}`)

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#kafka).

### Стратегия подключения { #consume-strategy }

Стратегия `subscribe` используется, когда в `driverProperties` указан [group.id](https://www.confluent.io/blog/configuring-apache-kafka-consumer-group-ids/).
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

Стратегия `assign` используется, когда в `driverProperties` **не** указан `group.id`.
В этом режиме каждый экземпляр приложения сам назначает себе разделы указанных топиков, поэтому одни и те же записи
читаются каждым экземпляром независимо. Такая стратегия полезна, когда одно и то же сообщение должны получить все реплики
приложения: например, для сброса локального кеша, обновления справочников в памяти или доставки служебного события
каждому экземпляру приложения.

Стратегия `assign` требует явного списка `topics` и не поддерживает `topicsPattern`.
Список разделов обновляется каждые `partitionRefreshInterval` и распределяется между `threads` потребителями,
а начальная позиция чтения управляется параметром `offset`.

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

### Сигнатуры { #signatures }

Доступные сигнатуры для методов `Kafka Consumer` из коробки, где `K` — тип ключа, а `V` — тип значения сообщения.
Генератор поддерживает три семейства сигнатур: отдельные аргументы `key`/`value`, одно событие `ConsumerRecord<K, V>`
или целая пачка `ConsumerRecords<K, V>`. Смешивать эти семейства в одном методе нельзя.

Обработчики синхронные: поток цикла опроса вызывает метод и ждет его завершения, прежде чем выполнить следующий `poll()`.
В `Kotlin` слушатель может быть объявлен `suspend`; сгенерированный обработчик тогда выполняет его через `runBlocking`
в том же потоке цикла опроса, то есть поток потребителя все равно занят на все время обработки.

#### Ключ и значение { #key-value-signature }

Сигнатура с отдельными аргументами принимает `value`, необязательный `key`, необязательные `Headers`, необязательный `Consumer<K, V>` и необязательные ошибки чтения.
Один пользовательский аргумент считается `value`, два пользовательских аргумента считаются `key` и `value` именно в таком порядке.
Если `key` не указан, тип ключа для десериализации считается `byte[]`.

Для обработки ошибки чтения можно добавить `Exception`, `Throwable`, `RecordKeyDeserializationException` или `RecordValueDeserializationException`.
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

#### Событие целиком { #record-signature }

Сигнатура с `ConsumerRecord<K, V>` принимает одно событие целиком, необязательный `Consumer<K, V>` и необязательные ошибки чтения:
`Exception`, `Throwable`, `RecordKeyDeserializationException` или `RecordValueDeserializationException`.
`Headers` и отдельные `key`/`value` в такой сигнатуре не поддерживаются, потому что `ConsumerRecord` уже содержит их.

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
Вместе с ней можно объявить только `Consumer<K, V>`.
Отдельные `key`/`value`, `Headers` и аргументы ошибок чтения в такой сигнатуре не поддерживаются — ошибки десериализации
обрабатываются при обходе событий.

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

Если в сигнатуре нет аргумента `Consumer<K, V>`, Kora фиксирует сдвиг автоматически: после каждого события для сигнатур
`key`/`value` и `ConsumerRecord<K, V>` либо после всей пачки для `ConsumerRecords<K, V>`.

Автоматическая фиксация выполняется только тогда, когда драйвер не делает этого сам.
Если `enable.auto.commit` не указан в `driverProperties`, Kora принудительно выставляет его в `false` и фиксирует сдвиги сама.
Если `enable.auto.commit` явно выставлен в `true`, сдвигами управляет драйвер, и Kora ничего не фиксирует.

Если в сигнатуре объявлен аргумент `Consumer<K, V>`, автоматическая фиксация сдвига отключается, и обработчик полностью
отвечает за вызов `commitSync()` или `commitAsync()`. Этот режим полезен, когда сдвиг нужно фиксировать только после
внешней операции, фиксировать несколько событий вместе или управлять позицией чтения вручную.

В режиме `subscribe` ручной `commit` фиксирует сдвиг внутри группы потребителей.
В режиме `assign` разделы не координируются через группу потребителей, поэтому обычно важнее управлять позицией вручную
через `seek()`, `pause()` и `resume()`, а не полагаться на групповую фиксацию сдвига.
Если обработчик упадет до ручной фиксации, событие или пачка будут вычитаны повторно согласно текущей позиции потребителя.

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

### Десериализация { #deserialization }

`Deserializer` используется для десериализации ключей и значений `ConsumerRecord`.
Kora предоставляет компоненты `Deserializer` для базовых типов: `String`, `UUID`, `byte[]`, `Bytes`, `ByteBuffer`,
`Double`, `Float`, `Integer`, `Long`, `Short` и `Void`.

Для более точной настройки `Deserializer` поддерживаются теги.
Теги можно установить на параметре-ключе, параметре-значении, а также на параметрах типа `ConsumerRecord` и `ConsumerRecords`.
Эти теги будут установлены на зависимостях контейнера.

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

Если требуется десериализация из `JSON`, используйте тег `@Json`.
В этом случае Kora использует `JsonReader<T>` и `JsonKafkaDeserializer<T>` из модуля [JSON](json.md):

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

Если ключ в обработчике не объявлен, по умолчанию используется `Deserializer<byte[]>`, который просто возвращает необработанные байты.

### Пользовательский десериализатор { #custom-deserializer }

Если требуется своя десериализация, можно реализовать собственный `Deserializer`.

**Вариант 1: десериализатор по умолчанию для типа**

Если предоставить `Deserializer<T>` как компонент без тега, он будет использоваться всеми потребителями этого типа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public static class MyEventDeserializer implements Deserializer<MyEvent> {

        private final JsonReader<MyEvent> reader;

        public MyEventDeserializer(JsonReader<MyEvent> reader) {
            this.reader = reader;
        }

        @Override
        public MyEvent deserialize(String topic, byte[] data) {
            return reader.read(data);
        }
    }

    @Component
    final class SomeConsumer {

        @KafkaListener("kafka.someConsumer")
        void process(MyEvent value) { // Uses MyEventDeserializer
            // event handling
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyEventDeserializer(
        private val reader: JsonReader<MyEvent>
    ) : Deserializer<MyEvent> {

        override fun deserialize(topic: String, data: ByteArray): MyEvent {
            return requireNotNull(reader.read(data)) { "Empty payload in topic $topic" }
        }
    }

    @Component
    class SomeConsumer {

        @KafkaListener("kafka.someConsumer")
        fun process(value: MyEvent) { // Uses MyEventDeserializer
            // event handling
        }
    }
    ```

`JsonReader<T>.read(byte[])` выбрасывает непроверяемое `JacksonException` на некорректном теле сообщения и возвращает `null`
для пустого тела, поэтому в `Kotlin` результат нужно развернуть через `requireNotNull`, прежде чем вернуть его как non-null тип.

**Вариант 2: точечный десериализатор для конкретного потребителя**

Если нужна разная десериализация для разных потребителей одного и того же типа, используйте теги:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class SomeConsumer {

        @Json
        public record MyEvent(String username, int code) {}

        @Tag(MyEvent.class)
        @Component
        public static class MyDeserializer implements Deserializer<MyEvent> {

            private final JsonReader<MyEvent> reader;

            public MyDeserializer(JsonReader<MyEvent> reader) {
                this.reader = reader;
            }

            @Override
            public MyEvent deserialize(String topic, byte[] data) {
                return reader.read(data);
            }
        }

        @KafkaListener("kafka.someConsumer")
        void process(@Tag(MyEvent.class) MyEvent value) {
            // event handling
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeConsumer {

        @Json
        data class MyEvent(val username: String, val code: Int)

        @Tag(MyEvent::class)
        @Component
        class MyDeserializer(
            private val reader: JsonReader<MyEvent>
        ) : Deserializer<MyEvent> {

            override fun deserialize(topic: String, data: ByteArray): MyEvent {
                return requireNotNull(reader.read(data)) { "Empty payload in topic $topic" }
            }
        }

        @KafkaListener("kafka.someConsumer")
        fun process(@Tag(MyEvent::class) value: MyEvent) {
            // event handling
        }
    }
    ```

### Обработка исключений { #exception-handling }

Если метод, помеченный `@KafkaListener`, выбросит исключение, цикл опроса прерывается и `Consumer` перезапускается
через `backoffTimeout`, потому что общего решения, как это обрабатывать, не существует, и разработчик **обязан**
решить это сам. При повторяющихся ошибках задержка удваивается вплоть до `60s`, поэтому постоянно падающий обработчик
не нагружает брокер.

#### Пропуск обработки { #exception-skipping }

Если по причинам бизнес-логики требуется пропустить обработку конкретного события (`ConsumerRecord`),
можно выбросить `KafkaSkipRecordException`, передав в конструктор исходное исключение.
В этом случае все метрики будут корректно учтены и записаны, обработка соответствующего события будет пропущена,
и начнется обработка следующего события.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class SomeConsumer {

        @KafkaListener("kafka.someConsumer1")
        void process1(String key, String value) {
            if ("skip".equals(value)) {
                throw new KafkaSkipRecordException(new IllegalArgumentException("Want to skip!"));
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

Если требуется реализовать собственные пропускаемые исключения,
можно использовать интерфейс `SkippableRecordException`, который следует реализовать в своих исключениях.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class MyKafkaSkipRecordException extends RuntimeException implements SkippableRecordException {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class MyKafkaSkipRecordException : RuntimeException(), SkippableRecordException
    ```

Пропуск работает только для сигнатур с одним событием: сигнатура с пачкой получает весь `ConsumerRecords` и сама решает, какие события пропустить.

#### Ошибки десериализации { #deserialization-errors }

Если используется сигнатура с `ConsumerRecord` или `ConsumerRecords`, исключение десериализации возникнет в момент
вызова методов `key` или `value`. Именно там его и стоит обработать нужным образом.

Выбрасываются следующие исключения:

* `io.koraframework.kafka.common.exceptions.RecordKeyDeserializationException`.
* `io.koraframework.kafka.common.exceptions.RecordValueDeserializationException`.

Оба наследуют `org.apache.kafka.common.errors.SerializationException`.
Из этих исключений можно получить исходный `ConsumerRecord<byte[], byte[]>` методом `getRecord()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    final class ConsumerService {

        @KafkaListener("kafka.someConsumer")
        public void process(ConsumerRecord<String, String> record) {
            try {
                var key = record.key();
                var value = record.value();
                // some value handling work
            } catch (RecordKeyDeserializationException e) {
                ConsumerRecord<byte[], byte[]> rawRecord = e.getRecord();
                // Handle raw record (log, send to DLQ, etc.)
            } catch (RecordValueDeserializationException e) {
                ConsumerRecord<byte[], byte[]> rawRecord = e.getRecord();
                // Handle raw record (log, send to DLQ, etc.)
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ConsumerService {

        @KafkaListener("kafka.someConsumer")
        fun process(record: ConsumerRecord<String, String>) {
            try {
                val key = record.key()
                val value = record.value()
                // some value handling work
            } catch (e: RecordKeyDeserializationException) {
                val rawRecord = e.record
                // Handle raw record (log, send to DLQ, etc.)
            } catch (e: RecordValueDeserializationException) {
                val rawRecord = e.record
                // Handle raw record (log, send to DLQ, etc.)
            }
        }
    }
    ```

Если используется сигнатура с распакованными `key`/`value`/`headers`, последним аргументом можно добавить `Exception`,
`Throwable`, `RecordKeyDeserializationException` или `RecordValueDeserializationException`.

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

Обратите внимание, что все аргументы становятся необязательными: ожидается либо пара ключ и значение, либо исключение.
Если не удалось десериализовать и ключ, и значение, а объявлен один аргумент `Exception`, будет передана ошибка ключа.

### Пользовательский тег { #custom-tag }

По умолчанию для потребителя создается автоматический тег с именем `<ListenerClass>Module.<ListenerClass><Method>Tag`,
его можно увидеть в сгенерированном модуле во время компиляции.

Если по каким-то причинам требуется переопределить тег потребителя, его можно задать аргументом аннотации `@KafkaListener`:

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

Тег проставляется на сгенерированный `KafkaListenerConfig`, обработчик и зависимость контейнера от слушателя ребалансировки,
то есть это ровно тот тег, под которым нужно регистрировать `ConsumerAwareRebalanceListener`.

### События ребалансировки { #rebalance-events }

Слушать и реагировать на события ребалансировки можно своей реализацией интерфейса `ConsumerAwareRebalanceListener`,
которую следует предоставить как компонент под тегом потребителя:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(SomeListenerProcessTag.class)
    @Component
    public final class SomeListener implements ConsumerAwareRebalanceListener {

        @Override
        public void onPartitionsRevoked(Consumer<?, ?> consumer, Collection<TopicPartition> partitions) {
            // Called before partitions are revoked from this consumer.
            // Use this to commit offsets or cleanup state.
        }

        @Override
        public void onPartitionsAssigned(Consumer<?, ?> consumer, Collection<TopicPartition> partitions) {
            // Called when partitions are assigned to this consumer.
            // Use this to initialize state for assigned partitions.
        }

        @Override
        public void onPartitionsLost(Consumer<?, ?> consumer, Collection<TopicPartition> partitions) {
            // Called when partitions are lost (e.g., consumer failure, group rebalance).
            // Unlike onPartitionsRevoked, this is called when the consumer is no longer
            // part of the group and cannot commit offsets.
            // Use this to cleanup local state for lost partitions.
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SomeListenerProcessTag::class)
    @Component
    class SomeListener : ConsumerAwareRebalanceListener {

        override fun onPartitionsRevoked(consumer: Consumer<*, *>, partitions: Collection<TopicPartition>) {
            // Called before partitions are revoked from this consumer.
            // Use this to commit offsets or cleanup state.
        }

        override fun onPartitionsAssigned(consumer: Consumer<*, *>, partitions: Collection<TopicPartition>) {
            // Called when partitions are assigned to this consumer.
            // Use this to initialize state for assigned partitions.
        }

        override fun onPartitionsLost(consumer: Consumer<*, *>, partitions: Collection<TopicPartition>) {
            // Called when partitions are lost (e.g., consumer failure, group rebalance).
            // Unlike onPartitionsRevoked, this is called when the consumer is no longer
            // part of the group and cannot commit offsets.
            // Use this to cleanup local state for lost partitions.
        }
    }
    ```

У `onPartitionsLost` есть реализация по умолчанию, делегирующая в `onPartitionsRevoked`, поэтому переопределять его нужно
только тогда, когда потерянные разделы требуют иной обработки, чем отозванные.

События ребалансировки существуют только в стратегии `subscribe`: контейнер `assign` управляет разделами сам и никогда не обращается к слушателю.

### Ручное управление { #manual-override }

Kora предоставляет небольшую обертку над `KafkaConsumer`, которая позволяет самостоятельно запускать обработку входящих событий.
Оба контейнера реализуют `GeneratedListener`, поэтому участвуют в жизненном цикле графа приложения как любой сгенерированный контейнер.

Конструктор контейнера `subscribe` выглядит так:

```java
public KafkaSubscribeConsumerContainer(String listenerConfig,
                                       String listenerImpl,
                                       KafkaListenerConfig config,
                                       Deserializer<K> keyDeserializer,
                                       Deserializer<V> valueDeserializer,
                                       BaseKafkaRecordsHandler<K, V> handler,
                                       KafkaConsumerTelemetry telemetry,
                                       @Nullable ConsumerAwareRebalanceListener rebalanceListener)
```

Конструктор контейнера `assign` выглядит так:

```java
public KafkaAssignConsumerContainer(String listenerConfig,
                                    String listenerImpl,
                                    KafkaListenerConfig config,
                                    Deserializer<K> keyDeserializer,
                                    Deserializer<V> valueDeserializer,
                                    KafkaConsumerTelemetry telemetry,
                                    BaseKafkaRecordsHandler<K, V> handler)
```

`listenerConfig` — это путь конфигурации, используемый в телеметрии, а `listenerImpl` — имя логгера слушателя.

`BaseKafkaRecordsHandler<K,V>` — базовый функциональный интерфейс обработчика:
```java
@FunctionalInterface
public interface BaseKafkaRecordsHandler<K, V> {

    void handle(KafkaConsumerPollObservation observation,
                ConsumerRecords<K, V> records,
                Consumer<K, V> consumer,
                boolean commitAllowed);
}
```

`commitAllowed` сообщает, оставляет ли драйвер управление сдвигами обработчику, то есть отключен ли `enable.auto.commit`.
Готовые обертки для обработки по одному событию и по пачке доступны в `HandlerWrapper`.

### Телеметрия { #telemetry-consumer }

Kafka использует контракт телеметрии для логирования, метрик и трассировки сообщений.
Конфигурация телеметрии (секция `telemetry { logging / metrics / tracing }`) описана в разделе [Конфигурация](#config-consumer).

`KafkaConsumerTelemetryFactory` создает `KafkaConsumerTelemetry` для каждого слушателя по пути конфигурации слушателя,
имени класса слушателя, `driverProperties` и `KafkaConsumerTelemetryConfig`.
`KafkaConsumerTelemetry` открывает `KafkaConsumerPollObservation` на каждый вызов `poll()`, порождает от него
`KafkaConsumerRecordObservation` на каждое событие и сообщает отставание потребителя по разделам:

```java
public interface KafkaConsumerTelemetry {

    MeterRegistry meterRegistry();

    KafkaConsumerPollObservation observePoll();

    void reportLag(TopicPartition partition, long lag);
}
```

Каждое наблюдение закрывается по завершении обработки, а наблюдение события несет топик, раздел, сдвиг и длительность обработки.

Реализация по умолчанию — `DefaultKafkaConsumerTelemetryFactory`, зарегистрированная в `KafkaModule` как `@DefaultComponent`.
Она полностью отключается, когда логирование, метрики и трассировка выключены, а иначе собирает включенные части из:

- `DefaultKafkaConsumerLoggerFactory` создает логгер, который пишет начало и конец опроса и обработки сообщений;
- `DefaultKafkaConsumerMetricsFactory` создает измерители длительности пачки, длительности события и отставания.

Обе фабрики внедряются в `KafkaModule` как необязательные зависимости, поэтому собственный `@Component`-наследник любой из них
заменяет только эту часть телеметрии по умолчанию. Собственный компонент `KafkaConsumerTelemetryFactory` заменяет телеметрию целиком.

Метрики и трассировка описаны в разделе [Справочник метрик](metrics.md#kafka).

## Продюсер { #producer }

`Producer` отправляет записи в `topic`. Kora создает реализацию интерфейса, помеченного `@KafkaPublisher`,
подбирает `Serializer` для ключа и значения, вызывает `KafkaProducer#send` и связывает отправку с телеметрией.

Для создания `Producer` используйте аннотацию `@KafkaPublisher` над интерфейсом.
Чтобы отправлять сообщения в произвольный `topic`, объявите метод с параметром `ProducerRecord`:

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

Параметр аннотации указывает путь к конфигурации продюсера.

### Топик { #topic }

Если нужны типизированные методы для конкретных `topic`, используйте аннотацию `@KafkaPublisher.Topic`:

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

Параметр аннотации указывает путь конфигурации `topic`.
Путь, начинающийся с `.`, разрешается относительно пути конфигурации `@KafkaPublisher`, поэтому
`@KafkaPublisher.Topic(".someTopic")` у продюсера, настроенного по пути `kafka.someProducer`, читает `kafka.someProducer.someTopic`.

### Конфигурация { #config-producer }

Конфигурация описывает настройки конкретного `@KafkaPublisher`, ниже приведен пример конфигурации по пути `kafka.someProducer`.

Основные параметры конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    kafka {
        someProducer {
            driverProperties { //(1)!
              "bootstrap.servers": "localhost:9093"
            }
        }
    }
    ```

    1.  Официальные `Properties` для `Kafka Producer` (`обязательное`, без значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someProducer:
        driverProperties: #(1)!
          "bootstrap.servers": "localhost:9093"
    ```

    1.  Официальные `Properties` для `Kafka Producer` (`обязательное`, без значения по умолчанию)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классе `KafkaPublisherConfig` (указаны значения по умолчанию либо примерные значения):

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
                    enabled = false //(3)!
                    driverMetrics = false //(4)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(5)!
                    tags = { //(6)!
                      "key1" = "value1"
                      "key2" = "value2"
                    }
                  }
                  tracing {
                    enabled = true //(7)!
                    attributes = { //(8)!
                      "key1" = "value1"
                      "key2" = "value2"
                    }
                  }
                }
            }
        }
        ```

        1.  Официальные `Properties` для `Kafka Producer`, смотрите [Apache Kafka Producer Configs](https://kafka.apache.org/documentation/#producerconfigs) (`обязательное`, по умолчанию отсутствует)
        2.  Включает логирование модуля (по умолчанию: `false`)
        3.  Включает метрики модуля (по умолчанию: `false`)
        4.  Регистрирует метрики драйвера `Apache Kafka` у используемого `KafkaProducer` в `MeterRegistry` (по умолчанию: `false`)
        5.  Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        6.  Настройка тегов метрик (по умолчанию: `{}`)
        7.  Включает трассировку модуля (по умолчанию: `true`)
        8.  Настройка атрибутов трассировки (по умолчанию: `{}`)

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
                enabled: false #(3)!
                driverMetrics: false #(4)!
                slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(5)!
                tags: #(6)!
                  key1: value1
                  key2: value2
              tracing:
                enabled: true #(7)!
                attributes: #(8)!
                  key1: value1
                  key2: value2
        ```

        1.  Официальные `Properties` для `Kafka Producer`, смотрите [Apache Kafka Producer Configs](https://kafka.apache.org/documentation/#producerconfigs) (`обязательное`, по умолчанию отсутствует)
        2.  Включает логирование модуля (по умолчанию: `false`)
        3.  Включает метрики модуля (по умолчанию: `false`)
        4.  Регистрирует метрики драйвера `Apache Kafka` у используемого `KafkaProducer` в `MeterRegistry` (по умолчанию: `false`)
        5.  Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        6.  Настройка тегов метрик (по умолчанию: `{}`)
        7.  Включает трассировку модуля (по умолчанию: `true`)
        8.  Настройка атрибутов трассировки (по умолчанию: `{}`)

Конфигурация `topic` описывает настройки конкретного `@KafkaPublisher.Topic`, ниже приведен пример конфигурации по пути `kafka.someProducer.someTopic`.

Пример полной конфигурации, описанной в классе `KafkaPublisherConfig.TopicConfig` (указаны значения по умолчанию либо примерные значения):

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

    1. `topic` в который метод отправляет данные (`обязательное`, по умолчанию отсутствует)
    2. Раздел `topic` в который метод отправляет данные (по умолчанию отсутствует, опционально)
        Если указан, все сообщения будут отправляться в указанный раздел.
        Если не указан, используется стандартное партиционирование Kafka (по ключу или случайное).

=== ":simple-yaml: `YAML`"

    ```yaml
    kafka:
      someProducer:
        someTopic:
          topic: "my-topic" #(1)!
          partition: 1 #(2)!
    ```

    1. `topic` в который метод отправляет данные (`обязательное`, по умолчанию отсутствует)
    2. Раздел `topic` в который метод отправляет данные (по умолчанию отсутствует, опционально)
        Если указан, все сообщения будут отправляться в указанный раздел.
        Если не указан, используется стандартное партиционирование Kafka (по ключу или случайное).

### Сигнатуры { #signatures-producer }

Доступные сигнатуры для методов `Kafka Producer` из коробки, где `K` — тип ключа, а `V` — тип значения сообщения.
Генератор поддерживает два семейства сигнатур: отправку готового `ProducerRecord<K, V>` и отправку через метод,
помеченный `@KafkaPublisher.Topic`. Смешивать эти семейства в одном методе нельзя.

#### Готовое событие { #producer-record-signature }

Метод с `ProducerRecord<K, V>` используется, когда `topic`, раздел, время или `Headers` задает вызывающий код.
Такой метод нельзя помечать `@KafkaPublisher.Topic`, потому что все детали отправки уже содержатся в `ProducerRecord`.
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

#### Методы по топику { #topic-signature }

Метод с `key`, `value` и `Headers` должен быть помечен `@KafkaPublisher.Topic`.
Один пользовательский аргумент считается `value`, два пользовательских аргумента считаются `key` и `value` именно в таком порядке.
Дополнительно можно объявить `Headers` и `Callback`, но не более одного аргумента каждого типа.
Если `Headers` не переданы, Kora создает пустые заголовки.

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

Для синхронного метода возвращаемым типом может быть `void`/`Unit` или `RecordMetadata`.
В этом случае Kora вызывает `KafkaProducer#send`, дожидается завершения отправки через `Future#get()`
и только затем возвращает управление вызывающему коду.

Для асинхронной отправки возвращаемым типом может быть `Future<RecordMetadata>`, `CompletionStage<RecordMetadata>`
или `CompletableFuture<RecordMetadata>`. В `Kotlin` также поддерживаются `suspend`-методы и `Deferred<RecordMetadata>`.
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
        fun sendFuture(value: V): Future<RecordMetadata>

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun sendStage(value: V): CompletionStage<RecordMetadata>

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun sendCompletableFuture(value: V): CompletableFuture<RecordMetadata>

        @KafkaPublisher.Topic("kafka.someProducer.someTopic")
        fun sendDeferred(value: V): Deferred<RecordMetadata>
    }
    ```

Недопустимые комбинации: `ProducerRecord<K, V>` вместе с `@KafkaPublisher.Topic`, `ProducerRecord<K, V>` вместе с отдельными `key`/`value`/`Headers`, более одного `Headers`, более одного `Callback`, а также метод с отдельными `key`/`value` без `@KafkaPublisher.Topic`.

### Сериализация { #serialization }

`Serializer` используется для сериализации ключей и значений `ProducerRecord`.
Kora предоставляет компоненты `Serializer` для базовых типов: `String`, `UUID`, `byte[]`, `Bytes`, `ByteBuffer`,
`Double`, `Float`, `Integer`, `Long`, `Short` и `Void`.

Чтобы указать, какой `Serializer` брать из контейнера, можно использовать теги.
Теги следует ставить на параметры `ProducerRecord` или `key`/`value` методов:

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

Если требуется сериализация в `JSON`, используйте тег `@Json`.
В этом случае Kora использует `JsonWriter<T>` и `JsonKafkaSerializer<T>` из модуля [JSON](json.md):

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

### Сериализаторы и десериализаторы по умолчанию { #default-serializers }

`KafkaModule` автоматически предоставляет сериализаторы и десериализаторы для базовых типов через `KafkaSerializersModule` и `KafkaDeserializersModule`.

Они предоставляются как компоненты `@DefaultComponent` **без тегов** и используются по умолчанию для всех потребителей и продюсеров соответствующих типов.
Поскольку это компоненты по умолчанию, собственный `Serializer<T>`/`Deserializer<T>` без тега для того же типа переопределяет их без конфликта.

**Поддерживаемые типы из коробки:**

| Тип | Сериализатор | Десериализатор |
|------|------------|--------------|
| `String` | `StringSerializer` | `StringDeserializer` |
| `byte[]` | `ByteArraySerializer` | `ByteArrayDeserializer` |
| `ByteBuffer` | `ByteBufferSerializer` | `ByteBufferDeserializer` |
| `Bytes` | `BytesSerializer` | `BytesDeserializer` |
| `UUID` | `UUIDSerializer` | `UUIDDeserializer` |
| `Integer` | `IntegerSerializer` | `IntegerDeserializer` |
| `Long` | `LongSerializer` | `LongDeserializer` |
| `Short` | `ShortSerializer` | `ShortDeserializer` |
| `Double` | `DoubleSerializer` | `DoubleDeserializer` |
| `Float` | `FloatSerializer` | `FloatDeserializer` |
| `Void` | `VoidSerializer` | `VoidDeserializer` |

Дополнительно под тегом `@Json` предоставляются `JsonKafkaSerializer<T>` и `JsonKafkaDeserializer<T>` для любого типа, у которого есть сгенерированный `JsonWriter<T>`/`JsonReader<T>`.

Чтобы использовать их, достаточно указать тип в методе продюсера или потребителя:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {
        @KafkaPublisher.Topic("kafka.someProducer.topic")
        void send(UUID key, String value);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyPublisher {
        @KafkaPublisher.Topic("kafka.someProducer.topic")
        fun send(key: UUID, value: String)
    }
    ```

### Пользовательский сериализатор { #custom-serializer }

Если требуется своя сериализация, можно реализовать собственный `Serializer`.

**Вариант 1: сериализатор по умолчанию для типа**

Если предоставить `Serializer<T>` как компонент без тега, он будет использоваться всеми продюсерами этого типа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public static class MyEventSerializer implements Serializer<MyEvent> {

        private final JsonWriter<MyEvent> writer;

        public MyEventSerializer(JsonWriter<MyEvent> writer) {
            this.writer = writer;
        }

        @Override
        public byte[] serialize(String topic, MyEvent data) {
            return writer.toByteArray(data);
        }
    }

    @KafkaPublisher("kafka.someProducer")
    public interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.topic")
        void send(MyEvent value); // Uses MyEventSerializer
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyEventSerializer(
        private val writer: JsonWriter<MyEvent>
    ) : Serializer<MyEvent> {

        override fun serialize(topic: String, data: MyEvent): ByteArray {
            return writer.toByteArray(data)
        }
    }

    @KafkaPublisher("kafka.someProducer")
    interface MyPublisher {

        @KafkaPublisher.Topic("kafka.someProducer.topic")
        fun send(value: MyEvent) // Uses MyEventSerializer
    }
    ```

`JsonWriter<T>.toByteArray(T)` выбрасывает непроверяемое `JacksonException`, поэтому обрабатывать проверяемые исключения в маппере не требуется.

**Вариант 2: точечный сериализатор для конкретного продюсера**

Если нужна разная сериализация для разных продюсеров одного и того же типа, используйте теги:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaPublisher("kafka.someProducer")
    public interface MyKafkaProducer {

        @Json
        record MyEvent(String username, int code) {}

        @Tag(MyEvent.class)
        @Component
        class MySerializer implements Serializer<MyEvent> {

            private final JsonWriter<MyEvent> writer;

            public MySerializer(JsonWriter<MyEvent> writer) {
                this.writer = writer;
            }

            @Override
            public byte[] serialize(String topic, MyEvent data) {
                return writer.toByteArray(data);
            }
        }

        void send(ProducerRecord<String, @Tag(MyEvent.class) MyEvent> record);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaPublisher("kafka.someProducer")
    interface MyKafkaProducer {

        @Json
        data class MyEvent(val username: String, val code: Int)

        @Tag(MyEvent::class)
        @Component
        class MySerializer(
            private val writer: JsonWriter<MyEvent>
        ) : Serializer<MyEvent> {

            override fun serialize(topic: String, data: MyEvent): ByteArray {
                return writer.toByteArray(data)
            }
        }

        fun send(record: ProducerRecord<String, @Tag(MyEvent::class) MyEvent>)
    }
    ```

### Обработка исключений { #exception-handling-producer }

Если ошибка отправки происходит в методе, возвращающем `void`/`Unit` или `RecordMetadata`,
выбрасывается `io.koraframework.kafka.common.exceptions.KafkaPublishException`.
Он наследует `org.apache.kafka.common.KafkaException`, а исходная ошибка от `KafkaProducer` доступна через `getCause()`.
`RuntimeException`, пришедший от драйвера, пробрасывается как есть, без оборачивания.

Методы, возвращающие `Future<RecordMetadata>`, `CompletionStage<RecordMetadata>` или `CompletableFuture<RecordMetadata>`,
не выбрасывают исключение — ошибка отправки завершает возвращенный future исключительно.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    class SomeService {

        private final MyPublisher publisher;

        public SomeService(MyPublisher publisher) {
            this.publisher = publisher;
        }

        void sendMessage() {
            try {
                publisher.send("key", "value");
            } catch (KafkaPublishException e) {
                // Handle the failed send (log, retry, etc.)
                var cause = e.getCause();
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(
        private val publisher: MyPublisher
    ) {

        fun sendMessage() {
            try {
                publisher.send("key", "value")
            } catch (e: KafkaPublishException) {
                // Handle the failed send (log, retry, etc.)
                val cause = e.cause
            }
        }
    }
    ```

#### Ошибки сериализации { #serialization-errors }

Если ошибка сериализации ключа или значения происходит в методе, помеченном `@KafkaPublisher.Topic`,
выбрасывается `org.apache.kafka.common.errors.SerializationException` — так же, как при прямом вызове `org.apache.kafka.clients.producer.Producer#send`.
Сериализация выполняется до передачи записи драйверу, поэтому такая ошибка не оборачивается в `KafkaPublishException`.

### Транзакции { #transactions }

Сообщения можно отправлять в `Kafka` [в рамках транзакции](https://www.confluent.io/blog/transactions-apache-kafka/).
Для этого используется аннотация `@KafkaPublisher` и наследование `TransactionalPublisher`.

Сначала описывается обычный `KafkaProducer`, а затем его тип используется для создания транзакционного `Producer`:

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

Транзакционный продюсер переиспользует `driverProperties` делегата и переопределяет только `transactional.id`,
поэтому подключение к брокеру настраивается один раз — по пути конфигурации продюсера-делегата.

Для отправки сообщений в транзакции используйте методы `inTx`: все сообщения внутри `lambda` фиксируются при успешном
выполнении и отменяются при ошибке.

===! ":fontawesome-brands-java: `Java`"

    ```java
    transactionalPublisher.inTx(publisher -> {
        publisher.send("key1", "value1");
        publisher.send("key2", "value2");
    });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    transactionalPublisher.inTx(TransactionalConsumer<MyPublisher, RuntimeException> { publisher ->
        publisher.send("key1", "value1")
        publisher.send("key2", "value2")
    })
    ```

В `Kotlin` методы `inTx` и `withTx` перегружены для колбэка с возвращаемым значением и без него, поэтому лямбду
приходится оборачивать в явно типизированный `SAM`-конструктор, чтобы компилятор выбрал нужную перегрузку.

Транзакцией можно управлять и вручную через `begin()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // commit will be called on try-with-resources close
    try (var transaction = transactionalPublisher.begin()) {
        transaction.publisher().send("key1", "value1");
        if (somethingBad) {
            transaction.abort();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // commit will be called on use close
    transactionalPublisher.begin().use {
        it.publisher().send("key1", "value1")
        if (somethingBad) {
            it.abort()
        }
    }
    ```

#### Конфигурация { #config-producer-tx }

`KafkaPublisherConfig.TransactionConfig` используется для настройки `@KafkaPublisher` с интерфейсом `TransactionalPublisher`:

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

    1.  Префикс идентификатора транзакции, к которому будет добавлен случайный `UUID` (по умолчанию: `kora-app-`)
        Формат: `{idPrefix}-{uuid}`. Пример: `my-transaction-550e8400-e29b-41d4-a716-446655440000`.
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

    1.  Префикс идентификатора транзакции, к которому будет добавлен случайный `UUID` (по умолчанию: `kora-app-`)
        Формат: `{idPrefix}-{uuid}`. Пример: `my-transaction-550e8400-e29b-41d4-a716-446655440000`.
    2.  Максимальный размер пула транзакционных `Producer` (по умолчанию: `10`)
    3.  Максимальное время ожидания свободного `Producer` из пула (по умолчанию: `10s`)

Когда пул исчерпан, `begin()` ждет свободный `Producer` до `maxWaitTime`, а затем выбрасывает
`org.apache.kafka.common.errors.TimeoutException`.

### Продвинутое использование транзакций { #advanced-transactions }

#### Интерфейс Transaction { #transaction-interface }

Метод `begin()` возвращает объект `Transaction<P>`, дающий расширенные возможности управления транзакцией:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try (var tx = transactionalPublisher.begin()) {
        // Sending messages
        tx.publisher().send("key1", "value1");
        tx.publisher().send("key2", "value2");

        // Commit consumer offsets within the transaction (exactly-once semantics)
        Map<TopicPartition, OffsetAndMetadata> offsets = ...;
        ConsumerGroupMetadata groupMetadata = ...;
        tx.sendOffsetsToTransaction(offsets, groupMetadata);

        // Explicit flush to guarantee sending before commit
        tx.flush();

        // commit() is called automatically on try-with-resources close
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    transactionalPublisher.begin().use { tx ->
        // Sending messages
        tx.publisher().send("key1", "value1")
        tx.publisher().send("key2", "value2")

        // Commit consumer offsets within the transaction (exactly-once semantics)
        val offsets: Map<TopicPartition, OffsetAndMetadata> = ...
        val groupMetadata: ConsumerGroupMetadata = ...
        tx.sendOffsetsToTransaction(offsets, groupMetadata)

        // Explicit flush to guarantee sending before commit
        tx.flush()

        // commit() is called automatically on use close
    }
    ```

**Методы `Transaction<P>`:**

| Метод | Описание |
|--------|-------------|
| `publisher()` | Возвращает типизированный продюсер для отправки сообщений |
| `producer()` | Возвращает исходный `Producer<byte[], byte[]>` для низкоуровневых операций |
| `sendOffsetsToTransaction(offsets, groupMetadata)` | Фиксирует сдвиги потребителя в той же транзакции |
| `flush()` | Гарантирует отправку всех сообщений до фиксации |
| `abort()` | Отменяет транзакцию |
| `abort(cause)` | Отменяет транзакцию с указанной причиной |
| `close()` | Закрывает транзакцию (фиксирует, если не было отмены) |

Типичный exactly-once конвейер читает событие, отправляет результат и сдвиг потребителя в одной транзакции
и поэтому вообще не фиксирует сдвиг через `Consumer`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class TransactionalPipelineListener {

        private final MyTransactionalPublisher publisher;

        public TransactionalPipelineListener(MyTransactionalPublisher publisher) {
            this.publisher = publisher;
        }

        @KafkaListener("kafka.someConsumer")
        public void process(ConsumerRecord<String, String> record, Consumer<String, String> consumer) {
            publisher.withTx(transaction -> {
                transaction.publisher().send("processed:" + record.value());
                transaction.sendOffsetsToTransaction(
                    Map.of(new TopicPartition(record.topic(), record.partition()), new OffsetAndMetadata(record.offset() + 1)),
                    consumer.groupMetadata()
                );
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class TransactionalPipelineListener(private val publisher: MyTransactionalPublisher) {

        @KafkaListener("kafka.someConsumer")
        fun process(record: ConsumerRecord<String, String>, consumer: Consumer<String, String>) {
            publisher.begin().use { transaction ->
                transaction.publisher().send("processed:${record.value()}")
                transaction.sendOffsetsToTransaction(
                    mapOf(TopicPartition(record.topic(), record.partition()) to OffsetAndMetadata(record.offset() + 1)),
                    consumer.groupMetadata()
                )
            }
        }
    }
    ```

Такой потребитель должен читать с `isolation.level = read_committed` и `enable.auto.commit = false`,
иначе отмененные транзакции станут видны либо сдвиг зафиксируется вне транзакции.

#### Методы транзакций { #tx-methods }

`TransactionalPublisher` предоставляет 4 метода для работы с транзакциями:

| Метод | Передает в колбэк | Возвращает значение |
|--------|-------------------|---------------|
| `inTx(TransactionalConsumer)` | `P publisher` | `void` |
| `inTx(TransactionalFunction)` | `P publisher` | `R` |
| `withTx(TransactionConsumer)` | `Transaction<P> tx` | `void` |
| `withTx(TransactionFunction)` | `Transaction<P> tx` | `R` |

Любое исключение из колбэка отменяет транзакцию и пробрасывается вызывающему коду.

**Пример с возвращаемым значением:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    // inTx with return value
    Long messageId = transactionalPublisher.inTx(publisher -> {
        publisher.send("key", "value");
        return System.currentTimeMillis();
    });

    // withTx with Transaction access
    transactionalPublisher.withTx(tx -> {
        tx.publisher().send("key", "value");
        tx.sendOffsetsToTransaction(offsets, groupMetadata);
        tx.flush(); // Explicit flush
    });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // inTx with return value
    val messageId = transactionalPublisher.inTx(TransactionalFunction<MyPublisher, RuntimeException, Long> { publisher ->
        publisher.send("key", "value")
        System.currentTimeMillis()
    })

    // withTx with Transaction access
    transactionalPublisher.withTx(TransactionConsumer<MyPublisher, RuntimeException> { tx ->
        tx.publisher().send("key", "value")
        tx.sendOffsetsToTransaction(offsets, groupMetadata)
        tx.flush() // Explicit flush
    })
    ```

### Телеметрия { #telemetry-producer }

Kafka использует контракт телеметрии для логирования, метрик и трассировки сообщений.
Конфигурация телеметрии (секция `telemetry { logging / metrics / tracing }`) описана в разделе [Конфигурация](#config-producer).

`KafkaPublisherTelemetryFactory` создает `KafkaPublisherTelemetry` для каждого продюсера по пути конфигурации продюсера,
имени интерфейса продюсера, `KafkaPublisherTelemetryConfig` и `driverProperties`.
`KafkaPublisherTelemetry` открывает наблюдение на каждую отправку и на каждую транзакцию:

```java
public interface KafkaPublisherTelemetry {

    MeterRegistry meterRegistry();

    KafkaPublisherTransactionObservation observeTx();

    KafkaPublisherRecordObservation observeSend(String topic);
}
```

`KafkaPublisherRecordObservation` также реализует `org.apache.kafka.clients.producer.Callback`, поэтому драйвер завершает
его сразу после подтверждения записи брокером; наблюдение несет топик, раздел, сдвиг и длительность отправки.
`KafkaPublisherTransactionObservation` фиксирует отправленные в транзакцию сдвиги, коммиты и откаты.

Реализация по умолчанию — `DefaultKafkaPublisherTelemetryFactory`, зарегистрированная в `KafkaModule` как `@DefaultComponent`.
Она объединяет `DefaultKafkaPublisherLoggerFactory` для логирования и `DefaultKafkaPublisherMetricsFactory` для метрик,
обе внедряются как необязательные зависимости, поэтому любую из них можно заменить собственным `@Component`-наследником.
Собственный компонент `KafkaPublisherTelemetryFactory` заменяет телеметрию целиком.

Метрики и трассировка описаны в разделе [Справочник метрик](metrics.md#kafka).
