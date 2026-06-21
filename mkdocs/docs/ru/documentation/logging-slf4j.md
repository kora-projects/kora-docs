---
description: "Explains Kora SLF4J logging setup, module log configuration, Logback integration, alternative implementations, structured logs, markers, parameters, and MDC. Use when working with Slf4jModule, LogbackModule, LoggerFactory, StructuredArgument, Marker, MDC, loggingConfig."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora SLF4J logging setup, module log configuration, Logback integration, alternative implementations, structured logs, markers, parameters, and MDC; key triggers include Slf4jModule, LogbackModule, LoggerFactory, StructuredArgument, Marker, MDC, loggingConfig."
---

Kora использует [`slf4j-api`](https://www.slf4j.org/) как общий фасад логирования во всем фреймворке.
`SLF4J` отделяет код приложения от конкретной реализации логирования, а в качестве основной реализации в Kora предполагается [`Logback`](#logback).

Модуль логирования отвечает за получение `Logger` через стандартную фабрику `SLF4J`, управление уровнями логирования через конфигурацию Kora и передачу структурированных данных в записи логов.
Структурированные данные можно добавлять через `StructuredArgument`, `Marker` и `MDC`, чтобы они попадали в вывод вместе с обычным текстовым сообщением.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Наблюдаемость](../guides/observability.md).

## Использование { #usage }

`Logger` создается через фабрику [`SLF4J`](https://www.slf4j.org/manual.html#hello_world):

===! ":fontawesome-brands-java: `Java`"

    ```java
    Logger logger = LoggerFactory.getLogger(SomeService.class);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(SomeService::class.java)
    ```

## Конфигурация { #configuration }

Уровни логирования описываются в классе `LoggingConfig`.
Конфигурация задает уровень для `ROOT`, пакета или конкретного класса:

===! ":material-code-json: `Hocon`"

    ```javascript
    logging {
      levels {  //(1)!
        "ROOT": "WARN"
        "ru.tinkoff.kora": "INFO"
        "ru.tinkoff.kora.http.server.common.telemetry": "INFO"
        "ru.tinkoff.kora.http.client.common.telemetry.DefaultHttpClientTelemetry": "INFO"
      }
    }
    ```

    1. Уровни логирования для `ROOT`, классов и пакетов (по умолчанию не указано, необязательно).

=== ":simple-yaml: `YAML`"

    ```yaml
    logging:
      levels: #(1)!
        ROOT: "WARN"
        ru.tinkoff.kora: "INFO"
        ru.tinkoff.kora.http.server.common.telemetry: "INFO"
        ru.tinkoff.kora.http.client.common.telemetry.DefaultHttpClientTelemetry: "INFO"
    ```

    1. Уровни логирования для `ROOT`, классов и пакетов (по умолчанию не указано, необязательно).

Если секция `logging` не указана, Kora не переопределяет уровни логирования через свою конфигурацию.

Параметры логирования конкретных модулей описываются в документации этих модулей, например [HTTP сервер](http-server.md), [HTTP клиент](http-client.md), [gRPC-клиент](grpc-client.md).

### Модули { #module }

Включение и выключение логирования определенных модулей указывается в конфигурации самих модулей через `telemetry.logging.enabled`.

По умолчанию логирование **всех модулей выключено**, поэтому ниже приведена конфигурация для включения логирования большинства модулей:

===! ":material-code-json: `Hocon`"

    ```javascript
    db.telemetry.logging.enabled = true //(1)!
    cassandra.telemetry.logging.enabled = true //(2)!
    grpcServer.telemetry.logging.enabled = true //(3)!
    httpServer.telemetry.logging.enabled = true //(4)!
    scheduling.telemetry.logging.enabled = true //(5)!
    grpcClient.ИмяСервисаGrpc.telemetry.logging.enabled = true //(6)!
    soapClient.ИмяСервисаSoap.telemetry.logging.enabled = true //(7)!
    ПутьДоКонфигурацииHttpКлиента.telemetry.logging.enabled = true //(8)!
    ПутьДоКонфигурацииKafkaПотребителя.telemetry.logging.enabled = true //(9)!
    ПутьДоКонфигурацииKafkaПродюсера.telemetry.logging.enabled = true //(10)!
    ```

    1. Логирование запросов к базе данных [JDBC](database-jdbc.md), `R2DBC` или `Vertx` (по умолчанию: `false`).
    2. Логирование запросов к базе данных [Cassandra](database-cassandra.md) (по умолчанию: `false`).
    3. Логирование запросов [gRPC-сервера](grpc-server.md) (по умолчанию: `false`).
    4. Логирование запросов [HTTP-сервера](http-server.md) (по умолчанию: `false`).
    5. Логирование запусков [планировщика](scheduling.md) (по умолчанию: `false`).
    6. Логирование запросов [gRPC-клиента](grpc-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    7. Логирование запросов [SOAP-клиента](soap-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    8. Логирование запросов [HTTP-клиента](http-client.md), указывается для конкретного клиента (по умолчанию: `false`).
    9. Логирование Kafka-[потребителя](kafka.md#configuration), указывается для конкретного потребителя (по умолчанию: `false`).
    10. Логирование Kafka-[продюсера](kafka.md#manual-override), указывается для конкретного продюсера (по умолчанию: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    db.telemetry.logging.enabled: true #(1)!
    cassandra.telemetry.logging.enabled: true #(2)!
    grpcServer.telemetry.logging.enabled: true #(3)!
    httpServer.telemetry.logging.enabled: true #(4)!
    scheduling.telemetry.logging.enabled: true #(5)!
    grpcClient.ИмяСервисаGrpc.telemetry.logging.enabled: true #(6)!
    soapClient.ИмяСервисаSoap.telemetry.logging.enabled: true #(7)!
    ПутьДоКонфигурацииHttpКлиента.telemetry.logging.enabled: true #(8)!
    ПутьДоКонфигурацииKafkaПотребителя.telemetry.logging.enabled: true #(9)!
    ПутьДоКонфигурацииKafkaПродюсера.telemetry.logging.enabled: true #(10)!
    ```

    1. Логирование запросов к базе данных [JDBC](database-jdbc.md), `R2DBC` или `Vertx` (по умолчанию: `false`).
    2. Логирование запросов к базе данных [Cassandra](database-cassandra.md) (по умолчанию: `false`).
    3. Логирование запросов [gRPC-сервера](grpc-server.md) (по умолчанию: `false`).
    4. Логирование запросов [HTTP-сервера](http-server.md) (по умолчанию: `false`).
    5. Логирование запусков [планировщика](scheduling.md) (по умолчанию: `false`).
    6. Логирование запросов [gRPC-клиента](grpc-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    7. Логирование запросов [SOAP-клиента](soap-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    8. Логирование запросов [HTTP-клиента](http-client.md), указывается для конкретного клиента (по умолчанию: `false`).
    9. Логирование Kafka-[потребителя](kafka.md#configuration), указывается для конкретного потребителя (по умолчанию: `false`).
    10. Логирование Kafka-[продюсера](kafka.md#manual-override), указывается для конкретного продюсера (по умолчанию: `false`).

## Logback { #logback }

Модуль предоставляет реализацию логирования на основе [`Logback`](https://www.baeldung.com/logback), добавляет поддержку структурированных логов и возможность управлять уровнями логирования через [файл конфигурации](config.md).

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-logback"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LogbackModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:logging-logback")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LogbackModule
    ```

### Конфигурация { #configuration-2 }

`Logback` настраивается через `logback.xml`, а в конфигурации Kora обычно указываются только уровни логирования.
Пример `logback.xml`:

```xml
<configuration debug="false">
    <statusListener class="ch.qos.logback.core.status.NopStatusListener"/>

    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="ru.tinkoff.kora.logging.logback.ConsoleTextRecordEncoder"/>
    </appender>

    <appender name="ASYNC" class="ru.tinkoff.kora.logging.logback.KoraAsyncAppender">
        <appender-ref ref="STDOUT"/>
    </appender>

    <root level="WARN">
        <appender-ref ref="ASYNC"/>
    </root>
</configuration>
```

`ConsoleTextRecordEncoder` выводит текстовую запись лога и добавляет к ней структурированные данные из `StructuredArgument`, `Marker`, пар ключ-значение `SLF4J` и `MDC`.
`KoraAsyncAppender` нужен для асинхронной записи логов: он сохраняет значения `MDC` из текущего контекста в `KoraLoggingEvent`, чтобы они не терялись при передаче записи в другой поток.

## Другая реализация { #other-implementation }

Kora использует [`slf4j-api`](https://www.slf4j.org/) как фасад логирования, поэтому можно подключить любую совместимую реализацию.
Базовый модуль добавляет общие компоненты для структурированных логов и управления уровнями логирования через [файл конфигурации](config.md).

### Подключение { #dependency-2 }

Потребуется подключить общий модуль логирования:

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-common"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:logging-common")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LoggingModule
    ```

### Использование { #usage-2 }

При использовании собственной реализации потребуется предоставить компонент `LoggingLevelApplier`, который умеет применять уровень логирования для указанного `Logger` и сбрасывать уровни к исходному состоянию.

Если в приложении используются структурированные данные, в собственной реализации также нужно самостоятельно поддержать запись `StructuredArgument`, `StructuredArgumentWriter` и `MDC`.

## Структурированные логи { #structured-logs }

Структурированные логи позволяют передавать в запись лога не только текст, но и именованные поля.
Такие поля удобно читать средствами сбора логов и использовать для поиска, фильтрации и построения представлений.

Передать структурированные данные в запись лога можно двумя способами:

- через `Marker`;
- через параметр сообщения.

Методы `marker` и `arg` также принимают значения типов `Long`, `Integer`, `String`, `Boolean` и `Map<String, String>`.
Для более сложных объектов можно передать свой `StructuredArgumentWriter` или `JsonWriter`.

### Маркер { #marker }

`Marker` добавляет структурированное поле к записи лога и не занимает место параметра в текстовом сообщении:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var marker = StructuredArgument.marker("key", "value");
    logger.info(marker, "message");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val marker = StructuredArgument.marker("key", "value")
    logger.info(marker, "message")
    ```

### Параметр { #parameter }

Параметр сообщения добавляет структурированное поле через обычный массив аргументов `SLF4J`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var parameter = StructuredArgument.arg("key", "value");
    logger.info("message", parameter);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val parameter = StructuredArgument.arg("key", "value")
    logger.info("message", parameter)
    ```

### MDC { #mdc }

Структурированные данные можно прикреплять ко всем записям в рамках текущего контекста с помощью класса `ru.tinkoff.kora.logging.common.MDC`.
Значение будет попадать в каждую запись лога, пока оно не удалено из `MDC`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    MDC.put("key", "value");
    try {
        logger.info("message");
    } finally {
        MDC.remove("key");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    MDC.put("key", "value")
    try {
        logger.info("message")
    } finally {
        MDC.remove("key")
    }
    ```

Если используется `AsyncAppender`, для корректной передачи параметров `MDC` нужно использовать `ru.tinkoff.kora.logging.logback.KoraAsyncAppender`.
Он передает делегату `ru.tinkoff.kora.logging.logback.KoraLoggingEvent`, который содержит в том числе структурированный `MDC`.
