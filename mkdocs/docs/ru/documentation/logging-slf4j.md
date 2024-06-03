Kora использует [slf4j-api](https://www.slf4j.org/) как движок для логирования в рамках всего фреймворка, 
предполагается что будет использоваться реализация на основе [Logback](#logback).

## Использование

Логеры требуется предоставлять посредствам фабрики [SLF4J](https://www.slf4j.org/manual.html#hello_world).

=== ":fontawesome-brands-java: `Java`"

    ```java
    Logger logger = LoggerFactory.getLogger(SomeService.class)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(SomeService::class.java);
    ```

## Конфигурация

Уровни логирования описанные в классе `LoggingConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    logging {
      levels {  //(1)!
        "ru.tinkoff.kora.http.server.common.telemetry": "INFO"
        "ru.tinkoff.kora.http.client.common.telemetry.DefaultHttpClientTelemetry": "INFO"
      }
    }
    ```

    1.  Указываются уровни логгирования для классов и пакетов

=== ":simple-yaml: `YAML`"

    ```yaml
    logging:
      levels: #(1)!
        ru.tinkoff.kora.http.server.common.telemetry: "INFO"
        ru.tinkoff.kora.http.client.common.telemetry.DefaultHttpClientTelemetry: "INFO"
    }
    ```

    1.  Указываются уровни логгирования для классов и пакетов

Параметры конфигурации сбора логов описываются в модулях в которых присутствует сбор логов, например [HTTP сервер](http-server.md), [HTTP клиент](http-client.md) и т.д.

### Модули

Включение и выключение логирования определенных модулей указывается в конфигурации самих модулей.

По умолчанию логирование **всех модулей выключено**, по этому для удобства тут указана отдельно конфигурация для включения логирования большинства модулей.

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

    1. База данных [JDBC](database-jdbc.md) / [R2DBC](database-jdbc.md) / [Vertx](database-vertx.md)
    2. База данных [Cassandra](database-cassandra.md)
    3. [gRPC сервер](grpc-server.md)
    4. [HTTP сервер](http-server.md)
    5. [Планировщик](scheduling.md)
    6. [gRPC клиент](grpc-client.md) (Указывается для конкретного сервиса)
    7. [SOAP клиент](soap-client.md) (Указывается для конкретного сервиса)
    8. [HTTP клиент](http-client.md) (Указывается для конкретного клиента)
    9. Kafka [потребитель](kafka.md#_3) (Указывается для конкретного потребителя)
    10. Kafka [продюсер](kafka.md#_11) (Указывается для конкретного продюсера)

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

    1. База данных [JDBC](database-jdbc.md) / [R2DBC](database-jdbc.md) / [Vertx](database-vertx.md)
    2. База данных [Cassandra](database-cassandra.md)
    3. [gRPC сервер](grpc-server.md)
    4. [HTTP сервер](http-server.md)
    5. [Планировщик](scheduling.md)
    6. [gRPC клиент](grpc-client.md) (Указывается для конкретного сервиса)
    7. [SOAP клиент](soap-client.md) (Указывается для конкретного сервиса)
    8. [HTTP клиент](http-client.md) (Указывается для конкретного клиента)
    9. Kafka [потребитель](kafka.md#_3) (Указывается для конкретного потребителя)
    10. Kafka [продюсер](kafka.md#_11) (Указывается для конкретного продюсера)

## Logback

Модуль предоставляет реализацию логирования на основе [Logback](https://www.baeldung.com/logback), добавляет поддержку структурированных логов и возможность конфигурации уровней логирования через [файл конфигурации](config.md).

### Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-logback"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LogbackModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:logging-logback")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LogbackModule
    ```

### Конфигурация

Предполагается что [настраиваться Logback](https://logback.qos.ch/manual/configuration.html) будет через `logback.xml`, а в конфигурации Kora указываться будут лишь уровни логирования, пример `logback.xml`:

```xml
<configuration debug="false">
    <statusListener class="ch.qos.logback.core.status.NopStatusListener" />
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

## Другая реализация

Kora использует [slf4j-api](https://www.slf4j.org/) как движок для логирования, можно подключить свою любую совместимую реализацию.
Базовый модуль добавляет поддержку структурированных логов и возможность конфигурации уровней логирования через [файл конфигурации](config.md).

### Подключение

Потребуется подключить общую реализацию логирования:

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-common"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:logging-common")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LoggingModule
    ```

### Использование

При использовании собственной реализации потребуется предоставить реализацию `LoggingLevelApplier` который бы реализовывал
установление уровня логирование и его сброс.

Также потребуется в реализации самостоятельно поддержать запись `StructuredArgument`, `StructuredArgumentWriter` и `MDC` если они будут использоваться.

## Структурированные логи

Передать структурированные данные в запись лога можно двумя способами через:

- Маркер
- Параметр

Методы маркера и параметра также принимают в качестве аргументов `Long`, `Integer`, `String`, `Boolean` и `Map<String, String>`.

### Маркер

Передать структурированные данные в лог можно через маркер:

=== ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var marker = StructuredArgument.marker("key", gen -> {
       gen.writeString("value");
    });
    logger.info(marker, "message");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val marker = StructuredArgument.marker("key") { it.writeString("value") }
    logger.info(marker, "message")
    ```

### Параметр

Передать структурированные данные в лог можно через параметры:

=== ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var parameter = StructuredArgument.arg("key", gen -> {
      gen.writeString("value");
    });
    log.info("message", parameter);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val parameter = StructuredArgument.arg("key") { it.writeString("value") }
    logger.info("message", parameter)
    ```

### MDC

Структурные данные можно прикреплять ко всем записям в рамках контекста с помощью класса `ru.tinkoff.kora.logging.common.MDC`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    MDC.put("key", gen -> gen.writeString("value"));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    MDC.put("key") { it.writeString("value") }
    ```

Если вы используете `AsyncAppender` для отправки логов, то для корректной передачи MDC параметров нужно воспользоваться `ru.tinkoff.kora.logging.logback.KoraAsyncAppender`,
который передаст делегату `ru.tinkoff.kora.logging.logback.KoraLoggingEvent`, содержащий, в том числе структурный MDC.
