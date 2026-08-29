---
search:
  exclude: true
title: Трассировка с Kora
summary: Build focused OpenTelemetry tracing for a Kora HTTP service, including the OTLP exporter, KoraTracer business spans, trace context propagation, log correlation, and Jaeger verification.
description: "Step-by-step OpenTelemetry tracing for a Kora HTTP service: the io.koraframework:opentelemetry-tracing-exporter-http dependency, OpentelemetryHttpExporterModule, the tracing and tracing.exporter configuration sections, service.name resource attributes, business spans created with KoraTracer traceParent and traceNew, span attributes and error recording, ScopedValue-based trace context, traceId and spanId log correlation, and verifying a trace in Jaeger."
agent:
  use_when: "Use this file for questions about adding tracing to a Kora application step by step: io.koraframework:opentelemetry-tracing-exporter-http, OpentelemetryHttpExporterModule, OpentelemetryGrpcExporterModule, the tracing.exporter.endpoint setting, tracing.attributes with service.name, injecting KoraTracer, traceParent and traceNew, KoraTracer.TraceCallable in Kotlin, adding span attributes, why a manual span becomes a separate trace, why traceId is missing from logs, and running Jaeger locally to inspect a trace."
tags: observability, tracing, opentelemetry, spans, kora-tracer, jaeger, context
---

# Трассировка с Kora { #observability-tracing-kora }

Это руководство посвящено только трассировке. Вы возьмете приложение из руководства по HTTP-серверу и сделаете один запрос прослеживаемым от начала до конца: подключите экспортер OpenTelemetry,
зададите идентичность сервиса, добавите бизнес-спан через `KoraTracer` и прочитаете получившуюся трассировку в Jaeger.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## Что вы создадите { #youll-build }

Вы добавите:

- `OpentelemetryHttpExporterModule`
- секцию `tracing.exporter`, указывающую на локальный коллектор
- идентичность сервиса `guide-observability-app` в `tracing.attributes`
- бизнес-спан `user.create`, созданный через `KoraTracer`
- атрибуты спана и запись ошибок для этой операции
- `traceId` и `spanId` в каждой строке лога запроса
- трассировку, прочитанную в интерфейсе Jaeger

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Docker, чтобы запустить Jaeger локально
- Текстовый редактор или IDE
- Пройденное [Руководство по HTTP-серверу](http-server.md)

Артефакты Kora 2.0 собраны под Java 25, поэтому JDK, которым компилируется приложение, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Необходимая основа"

    Это руководство предполагает, что вы прошли **[Руководство по HTTP-серверу](http-server.md)** и у вас уже есть HTTP-контроллеры, DTO, репозиторий, сервис и конфигурация из него.

    Если руководство по HTTP-серверу еще не пройдено, начните с него: это руководство по наблюдаемости сохраняет тот же HTTP-слой и надстраивает телеметрию поверх него.

## Обзор { #overview }

Трассировка нужна тогда, когда одного числа уже мало. Метрика может сказать, что создание пользователя стало медленным. Она не скажет, *какой именно* запрос был медленным, через какие шаги он прошел и
куда на самом деле ушло время. Трассировка отвечает на это: она записывает путь одного конкретного запроса как цепочку связанных шагов с их длительностями.

Kora трассирует поддерживаемые модули за вас. HTTP-сервер и клиент, база данных, `Kafka`, gRPC-сервер и клиент и другие подсистемы создают собственные спаны через свою телеметрию, а контекст
трассировки передается между сервисами по стандарту [W3C Trace Context](https://www.w3.org/TR/trace-context/). Ручной спан из этого руководства не заменяет эту инструментацию — он добавляет тот
единственный шаг, о котором фреймворк не может догадаться сам: бизнес-смысл операции.

Представьте, что каждому входящему запросу выдают талончик с номером. Номер едет вместе с запросом через HTTP-слой, в сервисы и дальше во все, что они вызывают. Каждый важный шаг делает на талончике
запись: «я начал», «я закончил», «я упал здесь». В итоге вы получаете дерево выполнения, а не россыпь строк лога.

### Модель трассировки { #trace-model }

**Трассировка** (trace) — это история одного запроса. Когда клиент вызывает `POST /users`, трассировка содержит входящий спан HTTP-сервера, спан `user.create`, который вы сейчас добавите, а позже,
возможно, спаны базы данных или исходящих HTTP-вызовов. Все части этой истории связаны одним идентификатором трассировки.

**Спан** (span) — это один шаг внутри трассировки. У него есть имя, время начала и окончания, статус и необязательные атрибуты. Спан в этом руководстве называется `user.create`, потому что это имя
бизнес-шага. Оно лучше имени класса или метода, который реализует его сегодня, потому что бизнес-шаг переживет рефакторинг.

**Родитель** (parent) — это то, что связывает шаги между собой. Если `user.create` создан дочерним к спану HTTP-сервера, Jaeger покажет его вложенным в ту же трассировку. Если родитель потерян, спан
начинает собственную трассировку, и понять, какой запрос его породил, уже невозможно.

**Ошибки** нужно класть на спан осознанно. Завершенный спан — это еще не успешный спан: именно запись исключения и установка статуса ошибки отличают «этот запрос просто был медленным» от «этот запрос
упал».

### Инструменты { #tools }

`OpentelemetryHttpExporterModule` добавляет в граф приложения экспорт спанов по `OTLP/HTTP`. Его конфигурация говорит, куда уходят собранные спаны; локально это Jaeger на порту `4318`. Для коллекторов,
которые говорят по `OTLP/gRPC`, есть парный `OpentelemetryGrpcExporterModule` — подключать нужно ровно один из двух.

`KoraTracer` — это компонент, который вы внедряете, чтобы создать бизнес-спан. Он строит спан, делает его текущим контекстом на время вызова, выставляет статус, записывает исключение, если оно вылетело,
и завершает спан. Один вызов, никакой ручной бухгалтерии.

**Контекст трассировки** переносится через `ScopedValue`, а не через thread local. Kora регистрирует собственную реализацию `ContextStorage` для OpenTelemetry, поэтому
`io.opentelemetry.context.Context.current()` и `io.opentelemetry.api.trace.Span.current()` возвращают правильные значения в любом месте трассируемой операции, включая виртуальные потоки.

**Jaeger** — это локальный просмотрщик трассировок. Он не нужен для сборки и запуска приложения, но именно им вы проверяете результат: создаете пользователя, открываете интерфейс, выбираете сервис и
ищете спан.

### Границы спана { #span-boundary }

Спан должен описывать работу, которую есть смысл измерять. Не оборачивайте в него каждую строку, каждое ветвление и каждое преобразование DTO — избыток спанов превращает трассировку в шум, а каждый
спан стоит памяти и трафика на экспорт.

Хороший ручной спан:

- начинается перед доменной операцией и заканчивается после появления ее результата
- назван по операции, а не по методу, который ее реализует
- несет несколько атрибутов с низкой кардинальностью, помогающих фильтровать
- записывает исключение, когда операция падает
- не содержит персональных данных ни в имени, ни в атрибутах

В этом руководстве спан оборачивает создание пользователя. Это полезно, потому что отделяет бизнес-операцию от HTTP-обработки вокруг нее: если в трассировке спан HTTP занимает 200 мс, а `user.create` —
4 мс, значит время ушло куда-то еще, и трассировка подсказывает, где искать дальше.

## Зависимости { #dependencies }

Экспорт по `OTLP/HTTP` живет в артефакте `opentelemetry-tracing-exporter-http`. Его версия приходит из платформы `io.koraframework:kora-bom`, поэтому в строке зависимости она не указывается.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation "io.koraframework:opentelemetry-tracing-exporter-http" //(1)!
    }
    ```

    1.  Экспортер спанов по `OTLP/HTTP`. Он транзитивно приносит базовую обвязку трассировки, поэтому отдельная зависимость не нужна.

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation("io.koraframework:opentelemetry-tracing-exporter-http") //(1)!
    }
    ```

    1.  Экспортер спанов по `OTLP/HTTP`. Он транзитивно приносит базовую обвязку трассировки, поэтому отдельная зависимость не нужна.

Модуль `OTLP/HTTP` отправляет спаны через HTTP-клиент `JDK` и не тянет `OkHttp` в приложение. Если ваш коллектор принимает `OTLP/gRPC`, замените артефакт на
`io.koraframework:opentelemetry-tracing-exporter-grpc`, а модуль — на `OpentelemetryGrpcExporterModule`: у обоих экспортеров одинаковая структура конфигурации, поэтому больше в этом руководстве ничего
не меняется.

## Модули { #modules }

Добавьте модуль экспортера в граф приложения рядом с модулями из руководства по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/io/koraframework/guide/observability/Application.java`:

    ```java
    package io.koraframework.guide.observability;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;
    import io.koraframework.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule,
            OpentelemetryHttpExporterModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/io/koraframework/guide/observability/Application.kt`:

    ```kotlin
    package io.koraframework.guide.observability

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule
    import io.koraframework.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule,
        OpentelemetryHttpExporterModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`OpentelemetryHttpExporterModule` наследует `OpentelemetryTracingModule`, который и кладет в граф `TracerProvider`, `Tracer` и `KoraTracer`. Поэтому подключения одного модуля экспортера достаточно и
для создания спанов, и для их отправки.

## Конфигурация { #config }

Трассировка описывается двумя секциями: `tracing` — про сам сервис, и `tracing.exporter` — про транспорт, который увозит спаны наружу.

Полный справочник по конфигурации — в [Трассировке](../documentation/tracing.md#configuration).

===! ":material-code-json: `Hocon`"

    ```javascript
    tracing {
      exporter {
        endpoint = "http://localhost:4318/v1/traces" //(1)!
        exportTimeout = "5s" //(2)!
        scheduleDelay = "1s" //(3)!
        maxExportBatchSize = 512 //(4)!
        maxQueueSize = 2048 //(5)!
      }
      attributes { //(6)!
        "service.name" = "guide-observability-app"
        "service.namespace" = "kora-guide"
      }
    }
    ```

    1.  Адрес коллектора, куда экспортируются спаны. Для `OTLP/HTTP` путь `/v1/traces` является частью URL (значения по умолчанию нет).
    2.  Максимальное время ожидания отправки данных экспортером (по умолчанию: `3s`).
    3.  Задержка между отправками накопленных спанов в коллектор (по умолчанию: `2s`).
    4.  Максимальное число спанов в одной партии экспорта (по умолчанию: `512`).
    5.  Максимальный размер очереди спанов, ожидающих отправки (по умолчанию: `2048`).
    6.  Атрибуты `OpenTelemetry Resource`, добавляемые к каждому экспортируемому спану сервиса (по умолчанию: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    tracing:
      exporter:
        endpoint: "http://localhost:4318/v1/traces" #(1)!
        exportTimeout: "5s" #(2)!
        scheduleDelay: "1s" #(3)!
        maxExportBatchSize: 512 #(4)!
        maxQueueSize: 2048 #(5)!
      attributes: #(6)!
        "service.name": "guide-observability-app"
        "service.namespace": "kora-guide"
    ```

    1.  Адрес коллектора, куда экспортируются спаны. Для `OTLP/HTTP` путь `/v1/traces` является частью URL (значения по умолчанию нет).
    2.  Максимальное время ожидания отправки данных экспортером (по умолчанию: `3s`).
    3.  Задержка между отправками накопленных спанов в коллектор (по умолчанию: `2s`).
    4.  Максимальное число спанов в одной партии экспорта (по умолчанию: `512`).
    5.  Максимальный размер очереди спанов, ожидающих отправки (по умолчанию: `2048`).
    6.  Атрибуты `OpenTelemetry Resource`, добавляемые к каждому экспортируемому спану сервиса (по умолчанию: `{}`).

`service.name` заслуживает отдельного внимания, потому что именно по нему вы вообще что-то найдете. Секция `tracing.attributes` по умолчанию пуста, поэтому сервис, который ее пропустил, экспортирует
спаны без идентичности и выглядит в коллекторе как безымянный источник. Задайте хотя бы имя, а если у вас несколько связанных сервисов — то и пространство имен.

`scheduleDelay = "1s"` — осознанный выбор для локального руководства: значение по умолчанию `2s` вполне подходит для продакшена, но ощущается как зависание, когда вы создали пользователя и тут же
обновляете интерфейс Jaeger.

### Переключатели трассировки { #tracing-switches }

!!! note "Трассировка включена по умолчанию, метрики и логирование — нет"

    `OpentelemetryTracingConfig#enabled` возвращает `true`, и то же самое делает `TelemetryConfig.TracingConfig#enabled` для каждого модуля. Это противоположно телеметрии метрик и логирования, которая
    выключена, пока вы ее не включите. Если вы подключили модуль экспортера и задали адрес, спаны пойдут без каких-либо дополнительных переключателей.

Выключить трассировку могут две независимые вещи:

===! ":material-code-json: `Hocon`"

    ```javascript
    tracing.enabled = false //(1)!
    httpServer.telemetry.tracing.enabled = false //(2)!
    ```

    1.  Глобальный переключатель. Kora ставит no-op `TracerProvider`, поэтому спаны не записываются нигде (по умолчанию: `true`).
    2.  Переключатель уровня модуля. Публичный HTTP-сервер перестает создавать собственные спаны (по умолчанию: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    tracing:
      enabled: false #(1)!
    httpServer:
      telemetry:
        tracing:
          enabled: false #(2)!
    ```

    1.  Глобальный переключатель. Kora ставит no-op `TracerProvider`, поэтому спаны не записываются нигде (по умолчанию: `true`).
    2.  Переключатель уровня модуля. Публичный HTTP-сервер перестает создавать собственные спаны (по умолчанию: `true`).

Есть еще одна деталь, о которой стоит знать: если `tracing.exporter.endpoint` не задан вовсе, ни экспортер, ни обработчик спанов не создаются. Приложение при этом стартует, спаны по-прежнему создаются,
а контекст трассировки по-прежнему передается — они просто никуда не отправляются. Это ровно то поведение, которое нужно в модульном тесте, и именно поэтому забытый адрес не дает никакого сообщения об
ошибке.

Системный HTTP-сервер — осознанное исключение из правила «трассировка включена»: `SystemHttpServerConfig` переопределяет свою трассировку на `false`, поэтому опрос `/system/readiness` оркестратором
каждые несколько секунд не закапывает ваши настоящие трассировки.

## Бизнес-спан { #business-span }

Телеметрия фреймворка уже создала спан для входящего `POST /users`. Чего она знать не может — что именно этот запрос означает в вашей предметной области «создать пользователя». Это и есть спан, который
вы добавляете руками.

### KoraTracer { #kora-tracer }

Внедрите `KoraTracer` в `UserService` и оберните логику создания. `traceParent` вкладывает новый спан в текущий активный — в спан HTTP-сервера, — поэтому в результате получается одна трассировка, а не
две.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        private final UserRepository userRepository;
        private final KoraTracer tracer;

        public UserService(UserRepository userRepository, KoraTracer tracer) {
            this.userRepository = userRepository;
            this.tracer = tracer;
        }

        public UserResponse createUser(UserRequest request) {
            return tracer.traceParent("user.create", span -> { //(1)!
                var generatedId = userRepository.save(request.name(), request.email());
                return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
            });
        }
    }
    ```

    1.  Спан создается, делается текущим, завершается и получает статус силами `KoraTracer` — в лямбде остается только бизнес-логика.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(
        private val userRepository: UserRepository,
        private val tracer: KoraTracer
    ) {

        fun createUser(request: UserRequest): UserResponse {
            return tracer.traceParent("user.create", KoraTracer.TraceCallable<UserResponse, RuntimeException> { span -> //(1)!
                val id = userRepository.save(request.name, request.email)
                UserResponse(id, request.name, request.email, LocalDateTime.now())
            })
        }
    }
    ```

    1.  `traceParent` перегружен для `TraceCallable` и `TraceRunnable`, а `Kotlin` не может сам выбрать между двумя функциональными интерфейсами — передайте явный SAM-конструктор.

`KoraTracer` дает три точки входа:

- `traceParent(name, …)` — спан, вложенный в текущий активный. Это то, что нужно внутри запроса.
- `traceNew(name, …)` — корневой спан, начинающий собственную трассировку. Используйте его для работы, которая действительно не является частью входящего запроса, например для фоновой задачи.
- `tracer()` — нижележащий `io.opentelemetry.api.trace.Tracer` для случаев, которые два предыдущих метода не покрывают.

Каждый из них принимает либо `TraceCallable`, который возвращает значение, либо `TraceRunnable`, который не возвращает. Оба отдают вам созданный `Span`.

### Атрибуты спана { #span-attributes }

`Span`, переданный в лямбду, — это место, где вы записываете, чем именно это выполнение отличается от предыдущего. Атрибуты нужны для фильтрации и группировки в интерфейсе трассировок, поэтому держите
их значения ограниченными.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public UserResponse createUser(UserRequest request) {
        return tracer.traceParent("user.create", span -> {
            span.setAttribute("user.email.provider", emailProvider(request.email())); //(1)!

            var generatedId = userRepository.save(request.name(), request.email());
            span.setAttribute("user.id", generatedId); //(2)!

            return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        });
    }

    private static String emailProvider(String email) {
        var at = email.lastIndexOf('@');
        return at < 0 ? "unknown" : email.substring(at + 1);
    }
    ```

    1.  Атрибут с низкой кардинальностью: полезен для фильтрации, число различных значений ограничено.
    2.  Атрибут с высокой кардинальностью на спане допустим — в отличие от метрики, он не создает новый временной ряд.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        return tracer.traceParent("user.create", KoraTracer.TraceCallable<UserResponse, RuntimeException> { span ->
            span.setAttribute("user.email.provider", emailProvider(request.email)) //(1)!

            val id = userRepository.save(request.name, request.email)
            span.setAttribute("user.id", id) //(2)!

            UserResponse(id, request.name, request.email, LocalDateTime.now())
        })
    }

    private fun emailProvider(email: String): String =
        email.substringAfterLast('@', "unknown")
    ```

    1.  Атрибут с низкой кардинальностью: полезен для фильтрации, число различных значений ограничено.
    2.  Атрибут с высокой кардинальностью на спане допустим — в отличие от метрики, он не создает новый временной ряд.

Это настоящая разница между двумя сигналами. У [метрики](observability-metrics.md#metric-caching) тег с неограниченным множеством значений умножает число хранимых временных рядов и рано или поздно
уронит систему мониторинга. На спане идентификатор — это просто поле одного записанного события, поэтому `user.id` здесь уместен, а на счетчике был бы неуместен.

Чего нельзя класть на спан ни в том, ни в другом случае — так это персональных данных. Сам адрес почты, полное имя, токен — все это попадет в коллектор, будет проиндексировано и станет доступно любому,
у кого есть доступ к интерфейсу трассировок. Провайдер почты отвечает на вопрос «не ломаются ли регистрации через Gmail?», не сохраняя при этом сам адрес.

### Ошибки в спане { #span-errors }

Чтобы записать сбой, `try`/`catch` не нужен. Если лямбда бросает исключение, `KoraTracer` записывает его на спан, ставит статус `ERROR` с сообщением исключения, завершает спан и пробрасывает исключение
дальше. При нормальном возврате он ставит `OK`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public void deleteUser(String id) {
        tracer.traceParent("user.delete", span -> { //(1)!
            span.setAttribute("user.id", id);
            if (!userRepository.deleteById(id)) {
                throw HttpServerResponseException.of(404, "User not found"); //(2)!
            }
        });
    }
    ```

    1.  Лямбда ничего не возвращает, поэтому выбирается перегрузка `TraceRunnable`.
    2.  Исключение записывается на спан и пробрасывается дальше — `404` доходит до клиента без изменений.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun deleteUser(id: String) {
        tracer.traceParent("user.delete", KoraTracer.TraceRunnable<RuntimeException> { span -> //(1)!
            span.setAttribute("user.id", id)
            if (!userRepository.deleteById(id)) {
                throw HttpServerResponseException.of(404, "User not found") //(2)!
            }
        })
    }
    ```

    1.  Ничего не возвращается, значит это перегрузка `TraceRunnable` — снова с явным SAM-конструктором.
    2.  Исключение записывается на спан и пробрасывается дальше — `404` доходит до клиента без изменений.

Трассировка никогда не проглатывает исключение. Она фиксирует его по дороге и дает ему дойти до HTTP-слоя, который превращает его в тот ответ, который в итоге получает клиент.

### Когда KoraTracer недостаточно { #manual-span }

`KoraTracer` покрывает самый распространенный случай. Когда нужно то, чего он не дает, — конкретный `SpanKind`, ссылка на другую трассировку, спан, живущий дольше вызова, — стройте спан из `Tracer` и
привязывайте контекст сами.

===! ":fontawesome-brands-java: `Java`"

    ```java
    var span = tracer.tracer().spanBuilder("user.create")
            .setSpanKind(SpanKind.INTERNAL)
            .setParent(io.opentelemetry.context.Context.current())
            .startSpan();

    return ScopedValue.where(OpentelemetryContext.VALUE, io.opentelemetry.context.Context.current().with(span)) //(1)!
            .call(() -> {
                try {
                    var result = doWork();
                    span.setStatus(StatusCode.OK);
                    return result;
                } catch (Exception e) {
                    span.recordException(e);
                    span.setStatus(StatusCode.ERROR, e.getMessage());
                    throw e;
                } finally {
                    span.end(); //(2)!
                }
            });
    ```

    1.  Привязка `ScopedValue` — это и есть способ сделать контекст текущим. `Context#makeCurrent()` в Kora намеренно бросает `IllegalStateException`.
    2.  Спан, который не завершили, не будет экспортирован — отсюда `finally`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val span = tracer.tracer().spanBuilder("user.create")
        .setSpanKind(SpanKind.INTERNAL)
        .setParent(io.opentelemetry.context.Context.current())
        .startSpan()

    val carrier = ScopedValue.where( //(1)!
        OpentelemetryContext.VALUE,
        io.opentelemetry.context.Context.current().with(span)
    )
    return carrier.call<UserResponse, RuntimeException> {
        try {
            val result = doWork()
            span.setStatus(StatusCode.OK)
            result
        } catch (e: Exception) {
            span.recordException(e)
            span.setStatus(StatusCode.ERROR, e.message)
            throw e
        } finally {
            span.end() //(2)!
        }
    }
    ```

    1.  Привязка `ScopedValue` — это и есть способ сделать контекст текущим. `Context#makeCurrent()` в Kora намеренно бросает `IllegalStateException`.
    2.  Спан, который не завершили, не будет экспортирован — отсюда `finally`.

`ScopedValue` виден только внутри той динамической области, которая его связала, поэтому передача работы в другой поток теряет контекст трассировки. Если вы отправляете задачу в executor, захватите
`io.opentelemetry.context.Context.current()` в вызывающем потоке и заново привяжите его в рабочем — смотрите [Асинхронную трассировку](../documentation/tracing.md#async-tracing).

## Связь с логами { #log-correlation }

Самый быстро окупающийся результат подключения трассировки — это не интерфейс трассировок, а то, что в строках лога появляется идентификатор трассировки.

`KoraAsyncAppender` захватывает текущий контекст спана в момент постановки события в очередь, а `ConsoleTextRecordEncoder` пишет `traceId=` и `spanId=` в строку всякий раз, когда этот контекст валиден.
Конфигурация Logback из руководства по HTTP-серверу уже содержит оба:

```xml title="src/main/resources/logback.xml"
<appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="io.koraframework.logging.logback.ConsoleTextRecordEncoder"/>
</appender>

<appender name="ASYNC" class="io.koraframework.logging.logback.KoraAsyncAppender">
    <appender-ref ref="STDOUT"/>
</appender>
```

Залогируйте строку внутри трассируемой операции — и она получит идентификаторы автоматически:

```text
09:41:12.508 INFO  [kora-undertow-4] i.k.g.o.service.UserService - traceId=4bf92f3577b34da6a3ce929d0e0e4736 spanId=00f067aa0ba902b7 Created user with id=1
```

Ничего не нужно класть в `MDC` или убирать оттуда ради этого — идентификаторы трассировки через него не идут. Строки, залогированные вне трассируемой операции, просто не содержат этих полей.

Это и есть мост между двумя сигналами. Вы находите упавший запрос в логах, копируете его `traceId`, вставляете в Jaeger и видите весь запрос целиком; или находите медленную трассировку и ищете ее
идентификатор в логах, чтобы прочитать, что код говорил в этот момент.

## Docker Compose { #docker-compose }

Запустите Jaeger с включенным приемником `OTLP/HTTP`:

```yaml title="docker-compose.yml"
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686" #(1)!
      - "4318:4318" #(2)!
    environment:
      COLLECTOR_OTLP_ENABLED: "true" #(3)!
```

1.  Интерфейс Jaeger.
2.  Приемник `OTLP/HTTP` — тот порт, на который указывает `tracing.exporter.endpoint`.
3.  Включает приемники `OTLP` в образе all-in-one.

## Проверка приложения { #check-app }

Запустите Jaeger, поднимите приложение и создайте пользователя:

```bash
docker compose up -d

./gradlew run
```

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

Посмотрите в лог приложения строку, подтверждающую, что запрос был протрассирован:

```text
09:41:12.508 INFO  [kora-undertow-4] i.k.g.o.service.UserService - traceId=4bf92f3577b34da6a3ce929d0e0e4736 spanId=00f067aa0ba902b7 Created user with id=1
```

Затем откройте [http://localhost:16686](http://localhost:16686), выберите сервис `guide-observability-app` и нажмите **Find Traces**. Дайте ему секунду-другую — спаны уходят из приложения партиями
каждые `scheduleDelay`.

Откройте трассировку: вы должны увидеть спан HTTP-сервера с вложенным в него `user.create`, несущим атрибуты `user.email.provider` и `user.id`, которые вы задали. Эта вложенность и есть весь смысл — она
доказывает, что ручной спан нашел своего родителя.

## Лучшие практики { #best-practices }

- Называйте спаны по операциям, а не по методам Java или Kotlin, которые их реализуют.
- Предпочитайте `KoraTracer` ручной возне со спанами; спускайтесь к «сырому» `Tracer` только ради того, чего он не покрывает.
- Внутри запроса используйте `traceParent`, а `traceNew` — только для работы, которая действительно начинает собственную трассировку.
- Давайте исключениям проходить сквозь спан, а не ловите и перебрасывайте их вручную.
- Не помещайте персональные данные в имена и атрибуты спанов.
- Задайте `service.name` и держите его стабильным для окружения.
- Атрибуты спана могут иметь высокую кардинальность, теги метрик — нет.

## Итоги { #summary }

Вы подключили экспортер `OTLP/HTTP`, задали идентичность сервиса, добавили спан `user.create` через `KoraTracer` вместе с атрибутами и записью ошибок, увидели `traceId` в логах и прочитали готовую
трассировку в Jaeger.

## Ключевые понятия { #key-concepts }

Трассировка:
: полная история одного запроса, общая для всех входящих в нее спанов.

Спан:
: один измеренный шаг внутри трассировки — с именем, временем, статусом и атрибутами.

`KoraTracer`:
: внедряемый компонент, который создает бизнес-спан и берет на себя его статус, ошибки и время жизни.

Родительский контекст:
: то, что делает ручной спан частью входящего запроса, а не отдельной трассировкой.

Атрибуты ресурса:
: `tracing.attributes` — идентичность сервиса, прикрепляемая к каждому экспортируемому спану.

OTLP:
: протокол, по которому спаны уезжают в коллектор, через `HTTP` или `gRPC`.

## Устранение неполадок { #troubleshooting }

В Jaeger ничего не приходит:
: Проверьте, что задан `tracing.exporter.endpoint`. Без адреса спаны создаются и передаются, но никогда не экспортируются, и в лог об этом ничего не пишется.

Ничего не приходит, а адрес задан:
: Убедитесь, что Jaeger запущен с `COLLECTOR_OTLP_ENABLED=true` и что URL содержит путь `/v1/traces`.

Трассировка появляется только спустя время:
: Это `tracing.exporter.scheduleDelay` копит спаны партиями (по умолчанию: `2s`).

Сервиса нет в выпадающем списке Jaeger:
: Задайте `tracing.attributes."service.name"`. Без него спаны экспортируются без идентичности сервиса.

`user.create` показывается отдельной трассировкой:
: Где-то потерян родительский контекст. Используйте `traceParent`, а не `traceNew`, и проверьте, не ушла ли работа в другой поток без переноса контекста.

Спанов нет вообще:
: Проверьте `tracing.enabled` и `<module>.telemetry.tracing.enabled` у самого модуля. Оба по умолчанию `true`, поэтому выключить их мог только явный `false`.

В логах нет `traceId`:
: Строка была залогирована вне трассируемой операции, либо в `logback.xml` не используется `KoraAsyncAppender` с `ConsoleTextRecordEncoder`.

## Что дальше? { #whats-next }

- добавьте бизнес-метрики в [Метриках с Kora](observability-metrics.md)
- добавьте проверки жизнеспособности и готовности в [Пробах с Kora](observability-probes.md)
- соберите все сигналы в одном приложении в [Наблюдаемости и мониторинге с Kora](observability.md)
- сверьтесь с деталями в [документации по трассировке](../documentation/tracing.md)

## Помощь { #help }

- изучите готовые приложения по наблюдаемости на Java и Kotlin
- проверьте настройки экспортера и семплирования в [документации по трассировке](../documentation/tracing.md)
- посмотрите, как идентификаторы трассировки попадают в строку лога, в [документации по логированию](../documentation/logging-slf4j.md#logback)
