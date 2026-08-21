---
description: "Explains Kora SLF4J logging setup, module log configuration, Logback integration, alternative implementations, structured logs, markers, parameters, and MDC. Use when working with LoggingModule, LogbackModule, LoggerFactory, StructuredArgument, Marker, MDC, loggingConfig."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora SLF4J logging setup, module log configuration, Logback integration, alternative implementations, structured logs, markers, parameters, and MDC; key triggers include LoggingModule, LogbackModule, LoggerFactory, StructuredArgument, Marker, MDC, loggingConfig."
---

Kora использует [`slf4j-api`](https://www.slf4j.org/) как общий фасад логирования во всем фреймворке.
`SLF4J` отделяет код приложения от конкретной реализации логирования, а в качестве основной реализации Kora предполагает использование [`Logback`](#logback).

Модуль логирования отвечает за получение `Logger` через стандартную фабрику `SLF4J`, управление уровнями логирования через конфигурацию Kora и передачу структурированных данных в записи логов.
Структурированные данные можно добавлять через `StructuredArgument`, `Marker` и `MDC`, чтобы они выводились вместе с обычным текстовым сообщением.

Пошаговый разбор перед справочным описанием смотрите в разделе [Наблюдаемость](../guides/observability.md).

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

Уровни логирования описываются классом `LoggingConfig`.
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

    1. Уровни логирования для `ROOT`, классов и пакетов (по умолчанию: не указано, необязательно).

=== ":simple-yaml: `YAML`"

    ```yaml
    logging:
      levels: #(1)!
        ROOT: "WARN"
        ru.tinkoff.kora: "INFO"
        ru.tinkoff.kora.http.server.common.telemetry: "INFO"
        ru.tinkoff.kora.http.client.common.telemetry.DefaultHttpClientTelemetry: "INFO"
    ```

    1. Уровни логирования для `ROOT`, классов и пакетов (по умолчанию: не указано, необязательно).

Ключ секции можно записать как `levels` или как `level` — оба варианта принимаются как псевдонимы.
Имена логгеров можно перечислять плоскими строками с точками (как выше) или как вложенный объект; Kora разворачивает вложенные объекты в имена логгеров с точками.
Имя логгера `ROOT` сопоставляется без учета регистра, поэтому `ROOT` и `root` эквивалентны.
Например, в поставляемых [примерах](https://github.com/kora-projects/kora-examples) используется псевдоним `level` в единственном числе с вложенным `root` в нижнем регистре:

```javascript
logging.level {
  "root": "WARN"
  "ru.tinkoff.kora": "INFO"
  "ru.tinkoff.kora.example": "INFO"
}
```

!!! note

    Когда секция `logging` отсутствует, Kora не применяет собственную карту уровней.
    Однако реализация [Logback](#logback) сбрасывает все логгеры при каждом (повторном) применении: `ROOT` нормализуется к `INFO`, а уровень каждого остального логгера очищается, чтобы он наследовался от родителя, после чего сверху применяются настроенные уровни.
    В результате значение `<root level="...">` из `logback.xml` при запуске фактически заменяется на `INFO`, если только уровень `ROOT` не задан в конфигурации.

### Обновление уровней во время работы { #levels-refresh }

Настроенные уровни применяются компонентом `LoggingLevelRefresher` — корневым компонентом, который при запуске сбрасывает все логгеры и заново применяет уровни из секции `logging` через `LoggingLevelApplier`.
Он повторно запускается при каждом обновлении конфигурации, поэтому когда активен [наблюдатель конфигурации](config.md#config-watcher), изменение уровня в файле конфигурации вступает в силу во время работы без перезапуска приложения.

Параметры логирования конкретных модулей описываются в документации этих модулей, например [HTTP сервер](http-server.md), [HTTP клиент](http-client.md), [gRPC-клиент](grpc-client.md).

### Модули { #module }

Включение и выключение логирования конкретных модулей задается в конфигурации самих модулей через `telemetry.logging.enabled`.

По умолчанию логирование **выключено для всех модулей**, поэтому ниже приведена конфигурация для включения логирования большинства модулей:

===! ":material-code-json: `Hocon`"

    ```javascript
    db.telemetry.logging.enabled = true //(1)!
    cassandra.telemetry.logging.enabled = true //(2)!
    grpcServer.telemetry.logging.enabled = true //(3)!
    httpServer.telemetry.logging.enabled = true //(4)!
    scheduling.telemetry.logging.enabled = true //(5)!
    grpcClient.SomeGrpcServiceName.telemetry.logging.enabled = true //(6)!
    soapClient.SomeSoapServiceName.telemetry.logging.enabled = true //(7)!
    SomePathToConfigHttpClient.telemetry.logging.enabled = true //(8)!
    SomePathToConfigKafkaConsumer.telemetry.logging.enabled = true //(9)!
    SomePathToConfigKafkaProducer.telemetry.logging.enabled = true //(10)!
    ```

    1. Логирование запросов к базе данных [JDBC](database-jdbc.md), `R2DBC` или `Vertx` (по умолчанию: `false`).
    2. Логирование запросов к базе данных [Cassandra](database-cassandra.md) (по умолчанию: `false`).
    3. Логирование запросов [gRPC-сервера](grpc-server.md) (по умолчанию: `false`).
    4. Логирование запросов [HTTP-сервера](http-server.md) (по умолчанию: `false`).
    5. Логирование запусков [планировщика](scheduling.md) (по умолчанию: `false`).
    6. Логирование запросов [gRPC-клиента](grpc-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    7. Логирование запросов [SOAP-клиента](soap-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    8. Логирование запросов [HTTP-клиента](http-client.md), указывается для конкретного клиента (по умолчанию: `false`).
    9. Логирование Kafka-[потребителя](kafka.md#config-consumer), указывается для конкретного потребителя (по умолчанию: `false`).
    10. Логирование Kafka-[производителя](kafka.md#config-producer), указывается для конкретного производителя (по умолчанию: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    db.telemetry.logging.enabled: true #(1)!
    cassandra.telemetry.logging.enabled: true #(2)!
    grpcServer.telemetry.logging.enabled: true #(3)!
    httpServer.telemetry.logging.enabled: true #(4)!
    scheduling.telemetry.logging.enabled: true #(5)!
    grpcClient.SomeGrpcServiceName.telemetry.logging.enabled: true #(6)!
    soapClient.SomeSoapServiceName.telemetry.logging.enabled: true #(7)!
    SomePathToConfigHttpClient.telemetry.logging.enabled: true #(8)!
    SomePathToConfigKafkaConsumer.telemetry.logging.enabled: true #(9)!
    SomePathToConfigKafkaProducer.telemetry.logging.enabled: true #(10)!
    ```

    1. Логирование запросов к базе данных [JDBC](database-jdbc.md), `R2DBC` или `Vertx` (по умолчанию: `false`).
    2. Логирование запросов к базе данных [Cassandra](database-cassandra.md) (по умолчанию: `false`).
    3. Логирование запросов [gRPC-сервера](grpc-server.md) (по умолчанию: `false`).
    4. Логирование запросов [HTTP-сервера](http-server.md) (по умолчанию: `false`).
    5. Логирование запусков [планировщика](scheduling.md) (по умолчанию: `false`).
    6. Логирование запросов [gRPC-клиента](grpc-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    7. Логирование запросов [SOAP-клиента](soap-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    8. Логирование запросов [HTTP-клиента](http-client.md), указывается для конкретного клиента (по умолчанию: `false`).
    9. Логирование Kafka-[потребителя](kafka.md#config-consumer), указывается для конкретного потребителя (по умолчанию: `false`).
    10. Логирование Kafka-[производителя](kafka.md#config-producer), указывается для конкретного производителя (по умолчанию: `false`).

## Logback { #logback }

Модуль предоставляет реализацию логирования на основе [`Logback`](https://www.baeldung.com/logback), добавляет поддержку структурированных логов и позволяет управлять уровнями логирования через [файл конфигурации](config.md).

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
Это единственный энкодер, поставляемый модулем: он формирует текст с добавленными структурированными полями, а не единый JSON-документ.
Запись выводится как обычная текстовая строка — `timestamp level [thread] logger - <mdc prefixes>message` — за которой, при наличии структурированных полей, следуют строки `fieldName={json}` с отступом табуляцией:

```text
2026-07-02 10:15:30.123 INFO  [main] r.t.k.example.SomeService - userId=42 user logged in
	role="admin"
```

`KoraAsyncAppender` используется для асинхронной записи логов: он сохраняет значения `MDC` из текущего контекста в `KoraLoggingEvent`, чтобы они не терялись при передаче записи в другой поток.

### Собственный шаблон { #custom-pattern }

Вместо `ConsoleTextRecordEncoder` можно использовать стандартный `PatternLayoutEncoder` вместе с конвертерами, которые отображают структурированные данные Kora.
`KoraMdcConverter` отображает `MDC` контекста Kora, а `KoraLoggingMarkerConverter` отображает маркер `StructuredArgument`; зарегистрируйте их как слова преобразования и сошлитесь на них в шаблоне:

```xml
<configuration>
    <conversionRule conversionWord="koraMdc" converterClass="ru.tinkoff.kora.logging.logback.KoraMdcConverter"/>
    <conversionRule conversionWord="koraMarker" converterClass="ru.tinkoff.kora.logging.logback.KoraLoggingMarkerConverter"/>

    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="ch.qos.logback.classic.encoder.PatternLayoutEncoder">
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} %-5level [%thread] %logger - %koraMdc%msg %koraMarker%n</pattern>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="STDOUT"/>
    </root>
</configuration>
```

## Другая реализация { #other-implementation }

Kora использует [`slf4j-api`](https://www.slf4j.org/) как фасад логирования, поэтому можно подключить любую совместимую реализацию.
Базовый модуль добавляет общие компоненты для структурированных логов и управления уровнями логирования через [файл конфигурации](config.md).

### Подключение { #dependency-2 }

Требуется подключить общий модуль логирования:

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

При использовании собственной реализации предоставьте компонент `LoggingLevelApplier`, который умеет применять уровень логирования для указанного `Logger` и сбрасывать уровни к их исходному состоянию.

Если приложение использует структурированные данные, собственная реализация также должна поддерживать запись `StructuredArgument`, `StructuredArgumentWriter` и `MDC`.

## Структурированные логи { #structured-logs }

Структурированные логи позволяют передавать в запись лога не только текст, но и именованные поля.
Такие поля удобны для средств сбора логов и могут использоваться для поиска, фильтрации и построения представлений.

Передать структурированные данные в запись лога можно двумя способами:

- через `Marker`;
- через параметр сообщения.

Методы `marker` и `arg` также принимают значения `Long`, `Integer`, `String`, `Boolean` и `Map<String, String>`.
Для более сложных объектов передайте свой `StructuredArgumentWriter` или `JsonWriter`.

### Marker { #marker }

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

### Сложный объект { #complex-object }

Для значений, которые не являются `String`, числом, `Boolean` или `Map<String, String>`, передайте `JsonWriter<T>` (тот же генерируемый для типа писатель [`@Json`](json.md)) или необработанную лямбду `StructuredArgumentWriter`, которая пишет значение поля напрямую в `JsonGenerator`.
Обе перегрузки предоставляют и `arg`, и `marker`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var parameter = StructuredArgument.arg("user", gen -> {
        gen.writeStartObject();
        gen.writeStringField("id", "42");
        gen.writeStringField("role", "admin");
        gen.writeEndObject();
    });
    logger.info("user logged in", parameter);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val parameter = StructuredArgument.arg("user") { gen ->
        gen.writeStartObject()
        gen.writeStringField("id", "42")
        gen.writeStringField("role", "admin")
        gen.writeEndObject()
    }
    logger.info("user logged in", parameter)
    ```

### MDC { #mdc }

Структурированные данные можно прикрепить ко всем записям в рамках текущего контекста с помощью класса `ru.tinkoff.kora.logging.common.MDC`.
Значение будет добавляться в каждую запись лога, пока оно не будет удалено из `MDC`:

!!! warning "Импорт"

    Используйте `ru.tinkoff.kora.logging.common.MDC`, а не `org.slf4j.MDC`. Kora хранит свой `MDC` внутри контекста Kora, а не в thread-local, поэтому значения, помещенные в `org.slf4j.MDC`, не отображаются энкодерами Kora и не распространяются через асинхронные границы. Декларативную альтернативу смотрите в [`@Mdc`](logging-aspect.md).

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

`put` принимает значения `String`, `Integer`, `Long` и `Boolean`, а также необработанный `StructuredArgumentWriter` для произвольного JSON; типизированные значения отображаются как их JSON-тип, а не как текст.
Также есть перегрузка `put(Context, key, value)` для записи в явно переданный контекст вместо текущего:

===! ":fontawesome-brands-java: `Java`"

    ```java
    MDC.put("userId", 42); //(1)!
    logger.info("user resolved");
    ```

    1. Отображается как JSON-число (`userId=42`), а не как строка.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    MDC.put("userId", 42) //(1)!
    logger.info("user resolved")
    ```

    1. Отображается как JSON-число (`userId=42`), а не как строка.

Поскольку `MDC` находится в контексте Kora, он распространяется через асинхронные и реактивные границы вместе с контекстом.

Если используется `AsyncAppender`, для корректной передачи параметров `MDC` используйте `ru.tinkoff.kora.logging.logback.KoraAsyncAppender`.
Он делает снимок `MDC` текущего контекста в момент добавления и передает делегату `ru.tinkoff.kora.logging.logback.KoraLoggingEvent`, поэтому структурированный `MDC` сохраняется при передаче записи в асинхронный рабочий поток.
