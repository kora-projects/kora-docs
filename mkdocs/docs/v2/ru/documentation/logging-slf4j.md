---
description: "Explains Kora SLF4J logging: obtaining a Logger, the logging.levels configuration and its runtime refresh, per-component telemetry logging, the Logback module with ConsoleTextRecordEncoder and KoraAsyncAppender, structured logs and the scoped MDC. Use when working with LoggingModule, LogbackModule, LoggingConfig, LoggingLevelApplier, StructuredArgument, MDC, KoraMdcConverter, telemetry.logging.enabled."
agent:
  use_when: "Use this file for Kora docs or implementation questions about SLF4J logging setup, logging.levels configuration and runtime refresh, per-component telemetry logging, Logback integration, alternative SLF4J implementations, structured log fields and MDC; key triggers include LoggingModule, LogbackModule, LoggingConfig, LoggingLevelApplier, LoggingLevelRefresher, ConsoleTextRecordEncoder, KoraAsyncAppender, KoraMdcConverter, KoraLoggingMarkerConverter, StructuredArgument, MDC, telemetry.logging.enabled."
---

Kora использует [`slf4j-api`](https://www.slf4j.org/) как общий фасад логирования во всем фреймворке.
`SLF4J` отделяет код приложения от конкретной реализации логирования, а в качестве основной реализации Kora предполагает использование [`Logback`](#logback).

Модуль логирования отвечает за получение `Logger` через стандартную фабрику `SLF4J`, управление уровнями логирования через конфигурацию Kora и передачу структурированных данных в записи логов.
Структурированные данные можно добавлять через `StructuredArgument`, `Marker`, пары ключ-значение `SLF4J` и `MDC`, чтобы они выводились вместе с обычным текстовым сообщением.

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

Уровни логирования описываются интерфейсом `LoggingConfig`, который отображается из секции `logging` [файла конфигурации](config.md).
В секции есть единственная карта `levels`, задающая уровень для `ROOT`, для пакета или для конкретного логгера:

===! ":material-code-json: `Hocon`"

    ```javascript
    logging {
      levels {  //(1)!
        "ROOT" = "WARN"
        "io.koraframework" = "INFO"
        "io.koraframework.http.server.common.HttpServer.request" = "DEBUG"
        "io.koraframework.example" = "INFO"
      }
    }
    ```

    1. Уровни логирования по имени логгера (по умолчанию: пустая карта, необязательно).

=== ":simple-yaml: `YAML`"

    ```yaml
    logging:
      levels: #(1)!
        "ROOT": "WARN"
        "io.koraframework": "INFO"
        "io.koraframework.http.server.common.HttpServer.request": "DEBUG"
        "io.koraframework.example": "INFO"
    ```

    1. Уровни логирования по имени логгера (по умолчанию: пустая карта, необязательно).

`levels` — плоская карта «имя логгера — уровень»: ключ является полным именем логгера, а значение — обычной строкой.

!!! warning "Имена логгеров в HOCON берите в кавычки"

    `HOCON` трактует ключ с точками без кавычек как путь и разворачивает его во вложенные объекты, поэтому `io.koraframework = "INFO"` превращается в объект `{ io { koraframework = "INFO" } }`.
    Вложенный объект не является строкой уровня, и отображение конфигурации падает с ошибкой о неожиданном типе значения.
    Всегда записывайте имена логгеров в кавычках — `"io.koraframework" = "INFO"`.
    В `YAML` ключ с точками и так остается литеральным, но кавычки делают оба формата одинаковыми.

!!! note

    Когда секция `logging` отсутствует, `levels` является пустой картой и Kora не применяет собственных уровней.
    Однако реализация [Logback](#logback) сбрасывает все логгеры при каждом (повторном) применении: `ROOT` нормализуется к `INFO`, а уровень каждого остального логгера очищается, чтобы он наследовался от родителя, после чего сверху применяются настроенные уровни.
    В результате значение `<root level="...">` из `logback.xml` при запуске фактически заменяется на `INFO`, если только уровень `ROOT` не задан в конфигурации.

### Обновление уровней во время работы { #levels-refresh }

Настроенные уровни применяются компонентом `LoggingLevelRefresher` — корневым компонентом, который при запуске сбрасывает все логгеры и применяет уровни из секции `logging` через `LoggingLevelApplier`.
Он повторно запускается при каждом обновлении конфигурации, поэтому когда активен [наблюдатель конфигурации](config.md#config-watcher), изменение уровня в файле конфигурации вступает в силу во время работы без перезапуска приложения.

Поскольку перед применением всегда выполняется сброс, удаленный из конфигурации уровень возвращается к наследуемому значению, а не остается на прежней настройке.

### Модули { #module }

Логирование запросов и ответов отдельных компонентов Kora является сигналом телеметрии этих компонентов и включается в их собственной секции конфигурации через `telemetry.logging.enabled`.
Это отдельная настройка от уровней логирования выше: `telemetry.logging.enabled` решает, порождает ли компонент записи логов вообще, а `logging.levels` — насколько эти записи подробны и проходят ли они фильтр по уровню.

По умолчанию логирование телеметрии **выключено для всех компонентов**, поэтому ниже приведена конфигурация для включения его у большинства из них:

===! ":material-code-json: `Hocon`"

    ```javascript
    jdbc.telemetry.logging.enabled = true //(1)!
    cassandra.telemetry.logging.enabled = true //(2)!
    grpcServer.telemetry.logging.enabled = true //(3)!
    httpServer.telemetry.logging.enabled = true //(4)!
    scheduling.telemetry.logging.enabled = true //(5)!
    resilient.telemetry.circuitBreaker.logging.enabled = true //(6)!
    grpcClient.SomeGrpcServiceName.telemetry.logging.enabled = true //(7)!
    soapClient.SomeSoapServiceName.telemetry.logging.enabled = true //(8)!
    SomePathToConfigHttpClient.telemetry.logging.enabled = true //(9)!
    kafka.consumer.SomeConsumerName.telemetry.logging.enabled = true //(10)!
    kafka.producer.SomePublisherName.telemetry.logging.enabled = true //(11)!
    ```

    1. Логирование запросов к базе данных [JDBC](database-jdbc.md) (по умолчанию: `false`).
    2. Логирование запросов к базе данных [Cassandra](database-cassandra.md) (по умолчанию: `false`).
    3. Логирование запросов [gRPC-сервера](grpc-server.md) (по умолчанию: `false`).
    4. Логирование запросов [HTTP-сервера](http-server.md) (по умолчанию: `false`).
    5. Логирование запусков [планировщика](scheduling.md) (по умолчанию: `false`).
    6. Логирование смены состояний [предохранителя](resilient.md); у `retry`, `timeout`, `fallback` и `rateLimiter` есть свои подсекции (по умолчанию: `false`).
    7. Логирование запросов [gRPC-клиента](grpc-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    8. Логирование запросов [SOAP-клиента](soap-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    9. Логирование запросов [HTTP-клиента](http-client.md), указывается для конкретного клиента по его собственному пути конфигурации (по умолчанию: `false`).
    10. Логирование Kafka-[потребителя](kafka.md#config-consumer), указывается для конкретного потребителя (по умолчанию: `false`).
    11. Логирование Kafka-[производителя](kafka.md#config-producer), указывается для конкретного производителя (по умолчанию: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    jdbc.telemetry.logging.enabled: true #(1)!
    cassandra.telemetry.logging.enabled: true #(2)!
    grpcServer.telemetry.logging.enabled: true #(3)!
    httpServer.telemetry.logging.enabled: true #(4)!
    scheduling.telemetry.logging.enabled: true #(5)!
    resilient.telemetry.circuitBreaker.logging.enabled: true #(6)!
    grpcClient.SomeGrpcServiceName.telemetry.logging.enabled: true #(7)!
    soapClient.SomeSoapServiceName.telemetry.logging.enabled: true #(8)!
    SomePathToConfigHttpClient.telemetry.logging.enabled: true #(9)!
    kafka.consumer.SomeConsumerName.telemetry.logging.enabled: true #(10)!
    kafka.producer.SomePublisherName.telemetry.logging.enabled: true #(11)!
    ```

    1. Логирование запросов к базе данных [JDBC](database-jdbc.md) (по умолчанию: `false`).
    2. Логирование запросов к базе данных [Cassandra](database-cassandra.md) (по умолчанию: `false`).
    3. Логирование запросов [gRPC-сервера](grpc-server.md) (по умолчанию: `false`).
    4. Логирование запросов [HTTP-сервера](http-server.md) (по умолчанию: `false`).
    5. Логирование запусков [планировщика](scheduling.md) (по умолчанию: `false`).
    6. Логирование смены состояний [предохранителя](resilient.md); у `retry`, `timeout`, `fallback` и `rateLimiter` есть свои подсекции (по умолчанию: `false`).
    7. Логирование запросов [gRPC-клиента](grpc-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    8. Логирование запросов [SOAP-клиента](soap-client.md), указывается для конкретного сервиса (по умолчанию: `false`).
    9. Логирование запросов [HTTP-клиента](http-client.md), указывается для конкретного клиента по его собственному пути конфигурации (по умолчанию: `false`).
    10. Логирование Kafka-[потребителя](kafka.md#config-consumer), указывается для конкретного потребителя (по умолчанию: `false`).
    11. Логирование Kafka-[производителя](kafka.md#config-producer), указывается для конкретного производителя (по умолчанию: `false`).

Компоненты пишут телеметрию через выделенные логгеры, названные по компоненту, а подробность вывода зависит от уровня этого логгера.
[HTTP-сервер](http-server.md) использует `io.koraframework.http.server.common.HttpServer.request` и `...HttpServer.response`: на `INFO` логируется операция, на `DEBUG` добавляются параметры запроса и заголовки, на `TRACE` — тело.
Пул базы данных использует `io.koraframework.database.<poolName>.query`, начинает логировать на `DEBUG` и добавляет текст `SQL` на `TRACE`.

!!! tip "Телеметрия включена, но ничего не логируется"

    Должны выполняться сразу два условия: `telemetry.logging.enabled = true` у компонента и достаточно низкий уровень в `levels` для логгера этого компонента.
    Пул базы данных, который логирует только на `DEBUG`, будет молчать при уровне `ROOT`, равном `INFO`.

Параметры логирования конкретных модулей описываются в документации этих модулей, например [HTTP сервер](http-server.md), [HTTP клиент](http-client.md), [gRPC-клиент](grpc-client.md).
Некоторые из них расширяют секцию логирования собственными ключами, например маскированием заголовков и параметров запроса у HTTP-сервера.

## Logback { #logback }

Модуль предоставляет реализацию логирования на основе [`Logback`](https://www.baeldung.com/logback), добавляет поддержку структурированных логов и позволяет управлять уровнями логирования через [файл конфигурации](config.md).

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:logging-logback"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LogbackModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:logging-logback")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LogbackModule
    ```

`LogbackModule` наследует `LoggingModule`, поэтому отдельная зависимость `logging-common` не требуется.

### Конфигурация { #configuration-2 }

`Logback` настраивается через `logback.xml`, а в конфигурации Kora обычно указываются только уровни логирования.
Пример `logback.xml`:

```xml
<configuration debug="false">
    <statusListener class="ch.qos.logback.core.status.NopStatusListener"/>

    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="io.koraframework.logging.logback.ConsoleTextRecordEncoder"/>
    </appender>

    <appender name="ASYNC" class="io.koraframework.logging.logback.KoraAsyncAppender">
        <appender-ref ref="STDOUT"/>
    </appender>

    <root level="WARN">
        <appender-ref ref="ASYNC"/>
    </root>
</configuration>
```

`KoraAsyncAppender` выполняет сразу две задачи.
Он передает запись рабочему потоку для асинхронной записи, а перед этим снимает все, что живет в текущей области видимости и иначе потерялось бы по дороге: значения Kora [`MDC`](#mdc) и текущий спан `OpenTelemetry`.
И то и другое сохраняется в `KoraLoggingEvent` — типе события, который понимают энкодер и конвертеры Kora.

!!! warning "Контекст Kora виден только благодаря KoraAsyncAppender"

    Значения Kora `MDC`, `traceId` и `spanId` читаются из `KoraLoggingEvent`.
    Цепочка аппендеров без `KoraAsyncAppender` порождает обычные события `Logback`, и эти поля просто не появляются в выводе.
    Оборачивайте реальный аппендер в `KoraAsyncAppender` даже тогда, когда асинхронная запись сама по себе не нужна.

### Формат записи лога { #record-format }

`ConsoleTextRecordEncoder` — единственный энкодер, поставляемый модулем.
Он формирует текстовую строку с добавленными структурированными полями, а не единый документ `JSON`, и складывается так:

- метка времени `yyyy-MM-dd HH:mm:ss.SSS` в `UTC`, уровень, имя потока в квадратных скобках и имя логгера;
- `traceId=... spanId=...`, если запись порождена внутри трассируемой операции;
- записи Kora `MDC` в виде `key=<json value>`;
- записи `MDC` из `SLF4J` в виде обычного `key=value`;
- отформатированное сообщение;
- по одной строке `fieldName={json}` с отступом табуляцией на каждое структурированное поле из маркеров, аргументов сообщения и пар ключ-значение `SLF4J`;
- стектрейс, если запись несет `Throwable`.

```text
2026-07-02 10:15:30.123 INFO  [kora-undertow-1] io.koraframework.example.SomeService - traceId=4bf92f3577b34da6a3ce929d0e0e4736 spanId=00f067aa0ba902b7 userId=42 user logged in
	role="admin"
```

Имя логгера выводится целиком и сокращается по пакетам только когда превышает 100 символов.

### Собственный шаблон { #custom-pattern }

Вместо `ConsoleTextRecordEncoder` можно использовать стандартный `PatternLayoutEncoder` вместе с конвертерами, которые отображают структурированные данные Kora.
`KoraMdcConverter` отображает `MDC` контекста Kora, а `KoraLoggingMarkerConverter` отображает маркер `StructuredArgument`; зарегистрируйте их как слова преобразования и сошлитесь на них в шаблоне:

```xml
<configuration>
    <conversionRule conversionWord="koraMdc" converterClass="io.koraframework.logging.logback.KoraMdcConverter"/>
    <conversionRule conversionWord="koraMarker" converterClass="io.koraframework.logging.logback.KoraLoggingMarkerConverter"/>

    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="ch.qos.logback.classic.encoder.PatternLayoutEncoder">
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} %-5level [%thread] %logger - %koraMdc%msg %koraMarker%n</pattern>
        </encoder>
    </appender>

    <appender name="ASYNC" class="io.koraframework.logging.logback.KoraAsyncAppender">
        <appender-ref ref="STDOUT"/>
    </appender>

    <root level="INFO">
        <appender-ref ref="ASYNC"/>
    </root>
</configuration>
```

`KoraMdcConverter` в первую очередь берет снимок `MDC`, который несет `KoraLoggingEvent`, и лишь в противном случае читает текущий привязанный `MDC` напрямую.
Такое чтение определено только внутри [области видимости `MDC`](#mdc-scope), и это еще одна причина держать `KoraAsyncAppender` перед аппендером с шаблоном: с ним записи, порожденные при инициализации графа или из shutdown hook, кодируются безопасно.

!!! note "Строка в логе не является контрактом запуска"

    Формулировки собственных стартовых сообщений Kora не входят в публичный контракт и меняются между версиями, а асинхронный аппендер под нагрузкой может потерять запись.
    Не ждите строку в логе, чтобы решить, что сервис поднялся — опрашивайте [пробу](probes.md) готовности по пути `/system/readiness`.

## Другая реализация { #other-implementation }

Kora использует [`slf4j-api`](https://www.slf4j.org/) как фасад логирования, поэтому можно подключить любую совместимую реализацию.
Базовый модуль добавляет общие компоненты для структурированных логов и управления уровнями логирования через [файл конфигурации](config.md).

### Подключение { #dependency-2 }

Требуется подключить общий модуль логирования:

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:logging-common"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:logging-common")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LoggingModule
    ```

### Использование { #usage-2 }

`LoggingModule` предоставляет компонент `LoggingConfig`, корневой компонент `LoggingLevelRefresher` и компонент `ILoggerFactory`, полученный из `LoggerFactory.getILoggerFactory()`.
`LoggingLevelApplier` он не предоставляет, поэтому собственная реализация должна дать его сама:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeLoggingLevelApplier implements LoggingLevelApplier {

        @Override
        public void apply(String logName, String logLevel) { //(1)!
            //...
        }

        @Override
        public void reset() { //(2)!
            //...
        }
    }
    ```

    1. Применяет уровень к логгеру с указанным именем; уровень приходит из карты `logging.levels` в том виде, в каком записан в конфигурации.
    2. Возвращает все логгеры в исходное состояние; вызывается перед каждым проходом применения, в том числе при обновлении конфигурации.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeLoggingLevelApplier : LoggingLevelApplier {

        override fun apply(logName: String, logLevel: String) { //(1)!
            //...
        }

        override fun reset() { //(2)!
            //...
        }
    }
    ```

    1. Применяет уровень к логгеру с указанным именем; уровень приходит из карты `logging.levels` в том виде, в каком записан в конфигурации.
    2. Возвращает все логгеры в исходное состояние; вызывается перед каждым проходом применения, в том числе при обновлении конфигурации.

Если приложение использует структурированные данные, собственная реализация также должна отображать `StructuredArgument`, `StructuredArgumentWriter` и Kora `MDC` — так же, как это делает [`ConsoleTextRecordEncoder`](#record-format) для `Logback`.

## Структурированные логи { #structured-logs }

Структурированные логи позволяют передавать в запись лога не только текст, но и именованные поля.
Такие поля удобны для средств сбора логов и могут использоваться для поиска, фильтрации и построения представлений.

Передать структурированные данные в запись лога можно тремя способами:

- через `Marker`;
- через параметр сообщения;
- через пару ключ-значение `SLF4J`.

Все три строятся из `io.koraframework.logging.common.arg.StructuredArgument`, а фабричные методы `marker` и `arg` принимают значения `String`, `Integer`, `Long`, `Boolean` и `Map<String, String>`.
Для любого другого типа передайте `JsonWriter<T>` или `StructuredArgumentWriter`.

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

### Пара ключ-значение { #key-value-pair }

Текучий построитель `SLF4J` прикрепляет именованное значение, не затрагивая ни сообщение, ни список маркеров.
`StructuredArgument.value` оборачивает писателя в `StructuredArgumentWriter`, который энкодер Kora отображает как структурированное поле — именно эту форму использует собственная телеметрия Kora:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    logger.atInfo()
        .addKeyValue("user", StructuredArgument.value(gen -> {
            gen.writeStartObject();
            gen.writeStringProperty("id", "42");
            gen.writeStringProperty("role", "admin");
            gen.writeEndObject();
        }))
        .log("user logged in");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    logger.atInfo()
        .addKeyValue("user", StructuredArgument.value { gen ->
            gen.writeStartObject()
            gen.writeStringProperty("id", "42")
            gen.writeStringProperty("role", "admin")
            gen.writeEndObject()
        })
        .log("user logged in")
    ```

### Сложный объект { #complex-object }

Для значений, которые не являются `String`, числом, `Boolean` или `Map<String, String>`, передайте `JsonWriter<T>` (тот же генерируемый для типа писатель [`@Json`](json.md)) или необработанную лямбду `StructuredArgumentWriter`, которая пишет значение поля напрямую в `JsonGenerator`.
Обе перегрузки предоставляют и `arg`, и `marker`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var parameter = StructuredArgument.arg("user", gen -> {
        gen.writeStartObject();
        gen.writeStringProperty("id", "42");
        gen.writeStringProperty("role", "admin");
        gen.writeEndObject();
    });
    logger.info("user logged in", parameter);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val parameter = StructuredArgument.arg("user") { gen ->
        gen.writeStartObject()
        gen.writeStringProperty("id", "42")
        gen.writeStringProperty("role", "admin")
        gen.writeEndObject()
    }
    logger.info("user logged in", parameter)
    ```

`JsonGenerator` здесь — тот же генератор `Jackson`, что используется во всей Kora, поэтому поля объекта пишутся через `writeStringProperty` / `writeNumberProperty`, а имена — через `writeName`.
Запись не объявляет проверяемых исключений, поэтому `try`/`catch` не нужен.

Перегрузка с `JsonWriter<T>` принимает значение и его писателя, а для `null` пишет `null`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private static final Logger logger = LoggerFactory.getLogger(SomeService.class);

        private final JsonWriter<User> userWriter;

        public SomeService(JsonWriter<User> userWriter) { //(1)!
            this.userWriter = userWriter;
        }

        public void handle(User user) {
            logger.info("user logged in", StructuredArgument.arg("user", user, userWriter));
        }
    }
    ```

    1. Писатель, сгенерированный для типа с аннотацией [`@Json`](json.md), является обычным компонентом графа и внедряется как зависимость.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(
        private val userWriter: JsonWriter<User>, //(1)!
    ) {

        fun handle(user: User) {
            logger.info("user logged in", StructuredArgument.arg("user", user, userWriter))
        }

        companion object {
            private val logger = LoggerFactory.getLogger(SomeService::class.java)
        }
    }
    ```

    1. Писатель, сгенерированный для типа с аннотацией [`@Json`](json.md), является обычным компонентом графа и внедряется как зависимость.

### Преобразователь аргумента { #argument-mapper }

`StructuredArgumentMapper<T>` — контракт, который превращает значение типа `T` в структурированное поле.
`LoggingModule` поставляет две реализации по умолчанию, построенные поверх существующего `JsonWriter<T>`:

- `JsonStructuredArgumentMapper` — пишет значение как `JSON`;
- `MaskedStructuredArgumentMapper` — пишет значение как `JSON`, заменяя поля, описанные в `MaskingRules`.

Обе объявлены как `@DefaultComponent`, поэтому собственный компонент `StructuredArgumentMapper<T>` для типа заменяет реализацию по умолчанию для этого типа.
Именно эти преобразователи использует аспект [`@Log`](logging-aspect.md) для сериализации аргументов и результатов методов, там же описаны правила маскирования.

### MDC { #mdc }

Структурированные данные можно прикрепить ко всем записям в рамках текущей области видимости с помощью класса `io.koraframework.logging.common.MDC`.
Значение будет добавляться в каждую запись лога, пока оно не будет удалено из `MDC`:

!!! warning "Импорт"

    Используйте `io.koraframework.logging.common.MDC`, а не `org.slf4j.MDC`.
    `MDC` из `SLF4J` — это thread-local со строками: Kora очищает его в начале каждого HTTP-запроса, он не следует за работой, переданной в другой поток, а его значения выводятся обычным текстом.
    Kora `MDC` живет в области видимости запроса, переносится через собственные передачи работы между потоками в Kora, а его значения выводятся как типизированный `JSON`.
    Декларативную альтернативу смотрите в [`@Mdc`](logging-aspect.md).

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

`put` принимает значения `String`, `Integer`, `Long` и `Boolean`, а также необработанный `StructuredArgumentWriter` для произвольного `JSON`; типизированные значения выводятся как их тип `JSON`, а не как текст, а значение `null` выводится как `null` в `JSON`:

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

### Область видимости MDC { #mdc-scope }

`MDC` не является глобальным thread-local: он привязан к области видимости, и `MDC.put` / `MDC.remove` / `MDC.get` работают только внутри нее.
Kora открывает такую область на каждой точке входа, которой владеет — запрос [HTTP-сервера](http-server.md), вызов [gRPC-сервера](grpc-server.md), запись [Kafka](kafka.md), запуск [планировщика](scheduling.md) — и каждая область начинается пустой, поэтому значения не утекают из одного запроса в следующий.
Когда Kora сама передает работу в другой поток, она заново привязывает `MDC` явно; например, слушатель Kafka получает `fork()` от `MDC` уровня опроса на каждую запись, поэтому значения отдельных записей остаются изолированными.

Код, который выполняется вне этих точек входа — инициализация графа, shutdown hook, задача в обычном `ExecutorService`, модульный тест — не имеет привязанного `MDC`, и вызов `MDC.put` там завершится ошибкой.
Для такого кода откройте область видимости явно:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ScopedValue.where(MDC.VALUE, new MDC()).run(() -> { //(1)!
        MDC.put("jobId", jobId);
        logger.info("job started");
    });
    ```

    1. `MDC.VALUE` — это `ScopedValue`, хранящий текущий `MDC`; привязка видна только в этом потоке внутри этого блока.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    ScopedValue.where(MDC.VALUE, MDC()).call<Unit, RuntimeException> { //(1)!
        MDC.put("jobId", jobId)
        logger.info("job started")
    }
    ```

    1. `MDC.VALUE` — это `ScopedValue`, хранящий текущий `MDC`. Используется `call`, а не `run`, потому что `run` разрешился бы в расширение стандартной библиотеки `Kotlin`, а не в метод носителя.

Из-за этой же привязки к области видимости [`KoraAsyncAppender`](#configuration-2) копирует `MDC` в момент добавления записи: у асинхронного рабочего потока собственной привязки нет, и именно скопированное в `KoraLoggingEvent` значение позже отображает энкодер.
