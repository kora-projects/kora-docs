---
search:
  exclude: true
title: Наблюдаемость и мониторинг с Kora
summary: Assemble metrics, tracing, structured logging, and health probes into one Kora application, and find the focused guide for each signal.
description: "The Kora observability hub: how metrics, tracing, logging and probes fit together in one application, which telemetry is on by default and which is not, the complete module graph with MetricsModule and OpentelemetryHttpExporterModule, the full httpServer.system, tracing and logging configuration, traceId correlation in log lines, the system port that serves /metrics and the probes, and links to the focused metrics, tracing and probes guides."
agent:
  use_when: "Use this file for questions about Kora observability as a whole: which of metrics, tracing, logging or probes to use for a problem, how they combine in one application, the complete @KoraApp graph with MetricsModule and OpentelemetryHttpExporterModule, why telemetry.metrics.enabled and telemetry.logging.enabled default to false while tracing defaults to true, the system HTTP port 8085 serving /metrics, /system/liveness and /system/readiness, correlating logs with traceId and spanId, and where each signal is taught step by step."
tags: observability, metrics, tracing, logging, health-checks, monitoring
---

# Наблюдаемость и мониторинг с Kora { #observability-monitoring-kora }

Это центральная страница по наблюдаемости в Kora. Она показывает, как четыре сигнала — метрики, трассировки, логи и пробы — складываются в одно работающее приложение, и указывает на отдельное
руководство, где каждый из них разбирается по шагам.

Читайте эту страницу, когда нужна общая картина: полный граф модулей, полная конфигурация и правила, общие для всех четырех сигналов. Читайте отдельные руководства, когда реализуете один из них.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## Что вы создадите { #youll-build }

Одно приложение, несущее все четыре сигнала:

- метрики Micrometer на `/metrics` — и фреймворка, и бизнеса
- трассировки OpenTelemetry, экспортируемые по `OTLP/HTTP`
- строки логов, несущие `traceId` и `spanId`
- пробы жизнеспособности и готовности на системном порту
- один системный порт, обслуживающий все эксплуатационные конечные точки
- тесты, проверяющие метрики, пробы и логи с контекстом трассировки

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Docker, чтобы запустить Jaeger и черноящичный тест локально
- Текстовый редактор или IDE
- Пройденное [Руководство по HTTP-серверу](http-server.md)

Артефакты Kora 2.0 собраны под Java 25, поэтому JDK, которым компилируется приложение, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Необходимая основа"

    Это руководство предполагает, что вы прошли **[Руководство по HTTP-серверу](http-server.md)** и у вас уже есть HTTP-контроллеры, DTO, репозиторий, сервис и конфигурация из него.

    Если руководство по HTTP-серверу еще не пройдено, начните с него: это руководство по наблюдаемости сохраняет тот же HTTP-слой и надстраивает телеметрию поверх него.

## Обзор { #overview }

Наблюдаемость — это то, что позволяет понимать работающий сервис, а не гадать по симптомам. Когда API становится медленнее, падает время от времени или работает в одном окружении и не работает в
другом, нужны сигналы изнутри приложения, объясняющие, что происходит на самом деле.

Сдвиг, который стоит совершить пораньше: наблюдаемость — это не режим отладки, который включают во время инцидента. Это часть рантайм-контракта продакшен-сервиса — к моменту, когда данные понадобятся,
они уже должны быть.

### Три основных сигнала { #three-core-signals }

Наблюдаемость Kora опирается на три сигнала плюс один эксплуатационный:

- **метрики** [Micrometer](https://docs.micrometer.io/micrometer/reference/) говорят, как система ведет себя в совокупности во времени
- **трассировки** [OpenTelemetry](https://opentelemetry.io/docs/) показывают жизненный цикл одного запроса по всей цепочке вызовов
- **логи** фиксируют, что сказал код, в привязке к породившей их трассировке
- **пробы** сообщают платформе, жив ли процесс и готов ли он к трафику

Метрики отвечают на вопросы о трендах, частотах и насыщении. Kora использует Micrometer, поэтому метрики фреймворка и бизнес-метрики попадают в один реестр: значения JVM и процесса, задержки и
распределение статусов HTTP-сервера, поведение базы данных и обмена сообщениями, плюс те счетчики и таймеры, которые вы регистрируете сами.

Трассировки отвечают на другой вопрос. Метрика может показать, что запросы медленные; она не покажет, *какой именно* запрос был медленным и куда ушло его время. Трассировка ведет один запрос через
приложение, привязывая к каждому шагу идентификаторы трассировки и спана, — именно это позволяет восстановить одно конкретное выполнение вместо усредненного.

Логи — самый старый сигнал, и они становятся куда полезнее с появлением трассировок, потому что каждая строка, выпущенная внутри трассируемой операции, несет идентификатор трассировки. Это ключ
соединения между «что сказал код» и «что делал запрос».

Пробы предназначены машинам, а не людям. Жизнеспособность отвечает на вопрос «нужно ли перезапустить процесс?», готовность — «должен ли этот экземпляр получать трафик прямо сейчас?», и
[Kubernetes](https://kubernetes.io/docs/home/) или балансировщик будут действовать по ответу, ни у кого не спрашивая.

### Выбор сигнала { #choosing-a-signal }

Четыре сигнала пересекаются достаточно, чтобы стоило понимать, какой на какой вопрос отвечает:

| Вопрос | Сигнал |
|--------|--------|
| Замедляется ли сервис за последний час? | метрики |
| Сколько пользователей создано сегодня? | метрики |
| Почему был медленным *вот этот конкретный* запрос? | трассировки |
| На каком шаге запрос упал? | трассировки |
| Что решил код и с какими значениями? | логи |
| Должен ли этот экземпляр получать трафик? | пробы |
| Нужно ли перезапустить этот процесс? | пробы |

Типичная ошибка — взять не тот сигнал: положить идентификатор пользователя с высокой кардинальностью в тег метрики, где он размножит временные ряды, пока система мониторинга не ляжет, хотя его место —
в атрибуте спана; или проверять базу данных в пробе жизнеспособности, где двухсекундная недоступность перезапустит весь парк, хотя ее место — в готовности или в
[CircuitBreaker](../documentation/resilient.md#circuitbreaker).

### Наблюдаемость в Kora { #observability-kora }

Kora связывает наблюдаемость через модули и конфигурацию. Компоненты фреймворка выпускают телеметрию сами, как только их модуль подключен и включен; код приложения добавляет бизнес-сигналы, которые
фреймворк назвать не может.

В собранном приложении:

- `MetricsModule` кладет в граф `MeterRegistry` и обеспечивает конечную точку `/metrics`
- `OpentelemetryHttpExporterModule` создает спаны, экспортирует их и предоставляет `KoraTracer`
- `LogbackModule` отрисовывает записи логов, включая идентификаторы трассировки
- `UndertowPublicHttpServerModule` обслуживает бизнес-API и, через наследуемый системный сервер, `/metrics` и обе пробы
- `MetricsService`, вызовы `KoraTracer` и компоненты проб несут специфичные для приложения части

### Эксплуатационные границы { #operational-boundaries }

Все эксплуатационные конечные точки живут на системном порту, а не на публичном. Бизнес-клиентам достается `8080`; Prometheus, kubelet и вашему агенту мониторинга — `8085`. Это разделение позволяет
открыть здоровье и метрики платформе, не открывая их интернету, и в Kora оно является поведением по умолчанию, а не тем, что нужно собирать самому.

## Отдельные руководства { #focused-guides }

У каждого сигнала есть собственное руководство с полным пошаговым разбором:

[Метрики с Kora](observability-metrics.md):
: Micrometer, `MeterRegistry`, счетчики и таймеры, границы гистограмм, кардинальность тегов и причина, по которой `/metrics` показывает только значения JVM, пока не включены метрики модулей.

[Трассировка с Kora](observability-tracing.md):
: Экспортер OTLP, идентичность сервиса, бизнес-спаны через `KoraTracer`, атрибуты спанов и ошибки, передача контекста трассировки и чтение трассировки в Jaeger.

[Пробы с Kora](observability-probes.md):
: Жизнеспособность и готовность, прогрев, агрегация нескольких проб, встроенные пробы фреймворка, контракт ответов и подключение в Kubernetes.

За справочными деталями по любому из них обращайтесь к [Метрикам](../documentation/metrics.md), [Трассировке](../documentation/tracing.md), [Пробам](../documentation/probes.md) и
[Логированию](../documentation/logging-slf4j.md).

## Зависимости { #dependencies }

Собранное приложение добавляет к сборке из руководства по HTTP-серверу два артефакта. Версии приходят из платформы `io.koraframework:kora-bom`.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation "io.koraframework:micrometer-module" //(1)!
        implementation "io.koraframework:opentelemetry-tracing-exporter-http" //(2)!
    }
    ```

    1.  Метрики Micrometer: `PrometheusMeterRegistry` и контракт сбора для системного сервера.
    2.  Экспортер спанов по `OTLP/HTTP`. Он транзитивно приносит базовую обвязку трассировки.

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation("io.koraframework:micrometer-module") //(1)!
        implementation("io.koraframework:opentelemetry-tracing-exporter-http") //(2)!
    }
    ```

    1.  Метрики Micrometer: `PrometheusMeterRegistry` и контракт сбора для системного сервера.
    2.  Экспортер спанов по `OTLP/HTTP`. Он транзитивно приносит базовую обвязку трассировки.

Логирование и пробы не добавляют ничего: `LogbackModule` пришел из руководства по HTTP-серверу, а интерфейсы проб приходят транзитивно в `io.koraframework:common`.

## Модули { #modules }

Полный граф приложения, несущего все четыре сигнала:

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
    import io.koraframework.micrometer.module.MetricsModule;
    import io.koraframework.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule, //(1)!
            MetricsModule, //(2)!
            UndertowPublicHttpServerModule, //(3)!
            OpentelemetryHttpExporterModule { //(4)!

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

    1.  Логирование, включая поля `traceId` и `spanId` в каждой строке внутри трассируемой операции.
    2.  Метрики: добавляет `MeterRegistry` и `MetricsScraper`, который системный сервер использует для `/metrics`.
    3.  Публичный HTTP-сервер; наследует системный сервер, отдающий `/metrics` и обе пробы.
    4.  Трассировка: создает спаны, экспортирует их по `OTLP/HTTP` и предоставляет `KoraTracer`.

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
    import io.koraframework.micrometer.module.MetricsModule
    import io.koraframework.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule, //(1)!
        MetricsModule, //(2)!
        UndertowPublicHttpServerModule, //(3)!
        OpentelemetryHttpExporterModule //(4)!

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

    1.  Логирование, включая поля `traceId` и `spanId` в каждой строке внутри трассируемой операции.
    2.  Метрики: добавляет `MeterRegistry` и `MetricsScraper`, который системный сервер использует для `/metrics`.
    3.  Публичный HTTP-сервер; наследует системный сервер, отдающий `/metrics` и обе пробы.
    4.  Трассировка: создает спаны, экспортирует их по `OTLP/HTTP` и предоставляет `KoraTracer`.

Отдельный управляющий модуль подключать не нужно. `UndertowPublicHttpServerModule` наследует `UndertowSystemHttpServerModule`, поэтому одно наследование дает два сервера: публичный на `httpServer.port`
и системный на `httpServer.system.port`, отвечающий на `/metrics`, `/system/liveness` и `/system/readiness`.

## Конфигурация { #config }

Полная конфигурация наблюдаемости для собранного приложения:

```hocon title="src/main/resources/application.conf"
httpServer {
  port = 8080 //(1)!
  system {
    port = 8085 //(2)!
    metricsPath = "/metrics" //(3)!
    livenessPath = "/system/liveness" //(4)!
    readinessPath = "/system/readiness" //(5)!
  }
  telemetry.logging.enabled = true //(6)!
  telemetry.metrics.enabled = true //(7)!
}

tracing {
  exporter {
    endpoint = "http://localhost:4318/v1/traces" //(8)!
    exportTimeout = "5s"
    scheduleDelay = "1s" //(9)!
    maxExportBatchSize = 512
    maxQueueSize = 2048
  }
  attributes { //(10)!
    "service.name" = "guide-observability-app"
    "service.namespace" = "kora-guide"
  }
}

logging {
  levels { //(11)!
    "ROOT": "WARN"
    "io.koraframework": "INFO"
    "io.koraframework.guide.observability": "DEBUG"
  }
}
```

1.  Публичный HTTP-порт для эндпоинтов приложения (по умолчанию: `8080`).
2.  Системный HTTP-порт, обслуживающий метрики и пробы (по умолчанию: `8085`).
3.  Путь сбора Prometheus на системном сервере (по умолчанию: `/metrics`).
4.  Путь жизнеспособности на системном сервере (по умолчанию: `/system/liveness`).
5.  Путь готовности на системном сервере (по умолчанию: `/system/readiness`).
6.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
7.  Включает сбор метрик публичного HTTP-сервера (по умолчанию: `false`).
8.  Адрес коллектора, куда экспортируются спаны (значения по умолчанию нет; без него ничего не экспортируется).
9.  Задержка накопления партии, уменьшенная относительно `2s` по умолчанию, чтобы локальные трассировки появлялись быстро.
10.  Идентичность сервиса, прикрепляемая к каждому экспортируемому спану (по умолчанию: `{}`).
11.  Уровни логирования по именам логгеров.

### Умолчания телеметрии { #telemetry-defaults }

!!! warning "Трассировка включена по умолчанию. Метрики и логирование — нет."

    `TelemetryConfig.TracingConfig#enabled` возвращает `true`, а `MetricsConfig#enabled` и `LoggingConfig#enabled` — оба `false`. Все модули Kora наследуют эти умолчания.

Эта асимметрия сбивает с толку, поэтому стоит сказать прямо. Приложение, подключившее `MetricsModule` и больше ничего, нормально стартует и отвечает на `/metrics` кодом `200` — но в теле будут только
значения JVM, процесса и `kora.up`. Не будет ни `http_server_request_duration_seconds`, ни `http_client_*`, ни `db_*`, и в логах не будет объяснения. Собственный `telemetry.metrics.enabled` модуля тоже
должен быть `true`.

С трассировкой все наоборот. Подключите модуль экспортера, задайте адрес — и спаны пойдут без дополнительных переключателей. Молча выключает трассировку как раз *отсутствующий* адрес: без
`tracing.exporter.endpoint` спаны по-прежнему создаются, а контекст по-прежнему передается, они просто никуда не отправляются — и об этом снова ничего не пишется в лог.

Собственные метрики, которые вы регистрируете через `MeterRegistry`, ничем из этого не затронуты. Они появляются, как только подключен `MetricsModule` и отработал код, потому что сам реестр всегда жив.
Флаг управляет только телеметрией модулей Kora.

Системный сервер — осознанное исключение в другую сторону: `SystemHttpServerConfig` переопределяет свою трассировку на `false`, поэтому оркестратор, опрашивающий готовность каждые несколько секунд, не
закапывает ваши настоящие трассировки.

## Логирование { #logging }

Именно конфигурация Logback из руководства по HTTP-серверу связывает логи с трассировками:

```xml title="src/main/resources/logback.xml"
<configuration debug="false">
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

`KoraAsyncAppender` захватывает текущий контекст спана в момент постановки события лога в очередь, а `ConsoleTextRecordEncoder` пишет `traceId=` и `spanId=` в строку всякий раз, когда этот захваченный
контекст валиден. Нужны оба аппендера: без асинхронного не будет захваченного контекста спана, а без энкодера он никогда не попадет в вывод.

Уровни берутся из секции конфигурации `logging.levels`, а не из этого файла, — именно это позволяет поднять уровень логгера в рантайме, не пересобирая образ.

## Сигналы вместе { #signals-together }

Когда подключены все четыре, одна бизнес-операция порождает все четыре сигнала сразу. Сервисный слой — то место, где они встречаются, потому что именно там живет доменный смысл:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        private static final Logger logger = LoggerFactory.getLogger(UserService.class);

        private final UserRepository userRepository;
        private final MetricsService metricsService;
        private final KoraTracer tracer;

        public UserService(UserRepository userRepository, MetricsService metricsService, KoraTracer tracer) {
            this.userRepository = userRepository;
            this.metricsService = metricsService;
            this.tracer = tracer;
        }

        public UserResponse createUser(UserRequest request) {
            return tracer.traceParent("user.create", span -> { //(1)!
                logger.info("Creating user with name={}", request.name()); //(2)!

                return metricsService.recordUserCreation(() -> { //(3)!
                    var generatedId = userRepository.save(request.name(), request.email());
                    span.setAttribute("user.id", generatedId); //(4)!
                    logger.info("Created user with id={}", generatedId);
                    return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
                });
            });
        }
    }
    ```

    1.  Трассировка: бизнес-спан, вложенный в спан HTTP-сервера.
    2.  Логирование: эта строка несет `traceId` и `spanId`, потому что находится внутри спана.
    3.  Метрики: счетчик и таймер операции.
    4.  Значение с высокой кардинальностью уместно на спане и было бы неуместно как тег метрики.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(
        private val userRepository: UserRepository,
        private val metricsService: MetricsService,
        private val tracer: KoraTracer
    ) {
        private val logger = LoggerFactory.getLogger(UserService::class.java)

        fun createUser(request: UserRequest): UserResponse {
            return tracer.traceParent("user.create", KoraTracer.TraceCallable<UserResponse, RuntimeException> { span -> //(1)!
                logger.info("Creating user with name={}", request.name) //(2)!

                metricsService.recordUserCreation { //(3)!
                    val id = userRepository.save(request.name, request.email)
                    span.setAttribute("user.id", id) //(4)!
                    logger.info("Created user with id={}", id)
                    UserResponse(id, request.name, request.email, LocalDateTime.now())
                }
            })
        }
    }
    ```

    1.  Трассировка: бизнес-спан, вложенный в спан HTTP-сервера.
    2.  Логирование: эта строка несет `traceId` и `spanId`, потому что находится внутри спана.
    3.  Метрики: счетчик и таймер операции.
    4.  Значение с высокой кардинальностью уместно на спане и было бы неуместно как тег метрики.

`MetricsService` — это небольшой компонент, который строится в [руководстве по метрикам](observability-metrics.md#metrics-service); пробы остаются в собственных компонентах, потому что им нечего делать
на пути запроса.

Один `POST /users` теперь оставляет за собой: инкремент `user.creation.total` и замер `user.creation.duration`, спан `user.create`, вложенный в HTTP-спан, две строки лога с тем же идентификатором
трассировки — и никаких изменений в пробах, что правильно, потому что создание пользователя ничего не говорит о том, должен ли экземпляр принимать трафик.

## Docker Compose { #docker-compose }

Jaeger принимает экспортируемые трассировки локально:

```yaml title="docker-compose.yml"
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686" #(1)!
      - "4318:4318" #(2)!
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
```

1.  Интерфейс Jaeger.
2.  Приемник `OTLP/HTTP` — тот порт, на который указывает `tracing.exporter.endpoint`.

## Проверка приложения { #check-app }

Поднимите коллектор и приложение:

```bash
docker compose up -d

./gradlew run
```

Задействуйте бизнес-API:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

Затем считайте все четыре сигнала обратно:

```bash
curl http://localhost:8085/metrics          # metrics
curl -i http://localhost:8085/system/liveness   # probes
curl -i http://localhost:8085/system/readiness
```

Трассировки — в интерфейсе Jaeger по адресу [http://localhost:16686](http://localhost:16686) под сервисом `guide-observability-app`, а логи — в собственном stdout приложения:

```text
09:41:12.508 INFO  [kora-undertow-4] i.k.g.o.service.UserService - traceId=4bf92f3577b34da6a3ce929d0e0e4736 spanId=00f067aa0ba902b7 Created user with id=1
```

`traceId` в этой строке — тот же идентификатор, который несет трассировка в Jaeger. В этом и состоит вся выгода от связывания сигналов между собой, а не по отдельности.

## Тестирование { #testing }

Наблюдаемость тестируема, и ее стоит тестировать — иначе сломанную пробу или пропавшую метрику обычно обнаруживают во время инцидента.

Внутри процесса внедрите нужные части и проверяйте их напрямую:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class ObservabilityAppTest {

        @TestComponent
        private UserService userService;
        @TestComponent
        private MeterRegistry meterRegistry; //(1)!

        @Test
        void userCreationUpdatesCustomMetrics() {
            userService.createUser(new UserRequest("Alice", "alice@example.com"));

            var counter = meterRegistry.find("user.creation.total").counter();
            assertNotNull(counter);
            assertEquals(1.0d, counter.count());
        }
    }
    ```

    1.  Реестр — обычный компонент графа, поэтому тест может прочитать метрики, зарегистрированные кодом.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class ObservabilityAppTest {

        @TestComponent
        lateinit var userService: UserService
        @TestComponent
        lateinit var meterRegistry: MeterRegistry //(1)!

        @Test
        fun userCreationUpdatesCustomMetrics() {
            userService.createUser(UserRequest("Alice", "alice@example.com"))

            val counter = meterRegistry.find("user.creation.total").counter()
            assertNotNull(counter)
            assertEquals(1.0, counter!!.count())
        }
    }
    ```

    1.  Реестр — обычный компонент графа, поэтому тест может прочитать метрики, зарегистрированные кодом.

В [черноящичном тесте](testing-black-box.md) дождитесь готовности для старта контейнера, а затем проверяйте системный порт: что `/metrics` содержит значения `http_server_*`, что обе пробы отвечают
`200` и что в stdout контейнера есть `traceId=`. Последняя проверка — самый дешевый регрессионный тест на «трассировка все еще подключена».

## Лучшие практики { #best-practices }

- Держите все эксплуатационные конечные точки на системном порту и вне публичного `Service`.
- Включайте телеметрию модулей осознанно — метрики и логирование выключены по умолчанию, трассировка включена.
- Наблюдайте за бизнес-операциями в сервисном слое, где встречаются логи, метрики и контекст трассировки.
- Держите значения с высокой кардинальностью в атрибутах спанов, а не в тегах метрик.
- В пробах проверяйте внутреннее состояние, а внешние зависимости — через [CircuitBreaker](../documentation/resilient.md#circuitbreaker).
- Задайте `service.name` и держите его стабильным для окружения.
- Не помещайте персональные данные ни в логи, ни в атрибуты спанов, ни в теги метрик.
- Проверяйте наблюдаемость в тестах: сигнал, который никто не проверяет, — это сигнал, который тихо исчезает.

## Итоги { #summary }

Вы собрали одно приложение, несущее все четыре сигнала: метрики Micrometer на системном порту, трассировки OpenTelemetry, экспортируемые по `OTLP/HTTP`, строки логов, связанные через `traceId`, и пробы
жизнеспособности и готовности — при неизменном контракте публичного API. У каждого сигнала есть отдельное руководство с той глубиной, в которую эта страница не заходит.

## Ключевые понятия { #key-concepts }

Метрики:
: агрегированные числа во времени — для трендов, частот и алертов.

Трассировка:
: путь одного запроса — чтобы найти, где потерялось время или корректность.

Связь с логами:
: `traceId` и `spanId` в строках логов, соединяющие то, что сказал код, с тем, что делал запрос.

Пробы:
: ответы о жизнеспособности и готовности, по которым действует платформа.

Системный порт:
: отдельный порт, обслуживающий `/metrics` и обе пробы в стороне от бизнес-API.

Умолчания телеметрии:
: трассировка включена, метрики и логирование выключены — по каждому модулю, пока не включите.

## Устранение неполадок { #troubleshooting }

`/metrics` отвечает `200`, но показывает только значения JVM:
: Задайте `<module>.telemetry.metrics.enabled = true`. Для каждого модуля значение по умолчанию — `false`.

`/metrics` отвечает `# Metric Scraper disabled`:
: `MetricsModule` не подключен, поэтому в графе нет `MetricsScraper`.

В коллектор трассировок ничего не приходит:
: Проверьте `tracing.exporter.endpoint`. Без него спаны создаются и передаются, но никогда не экспортируются, и молча.

В логах нет `traceId`:
: Строка была залогирована вне трассируемой операции, либо в `logback.xml` не используется `KoraAsyncAppender` с `ConsoleTextRecordEncoder`.

Любая эксплуатационная конечная точка отвечает `404`:
: Вы на публичном порту. Все они живут на `httpServer.system.port` (по умолчанию: `8085`).

Приложение перезапускается по кругу:
: В жизнеспособности проверяется внешняя зависимость. Перенесите ее в готовность.

Prometheus хранит огромное число рядов:
: У тега метрики неограниченное множество значений. Перенесите это значение в атрибут спана.

## Что дальше? { #whats-next }

- углубитесь в один сигнал в [Метриках](observability-metrics.md), [Трассировке](observability-tracing.md) или [Пробах](observability-probes.md)
- добавьте точечные компонентные тесты в [Тестировании с JUnit](testing-junit.md)
- проверьте собранное приложение целиком в [Черноящичном тестировании](testing-black-box.md)
- свяжите телеметрию с отказами, повторами и предохранителями в [Устойчивых паттернах](resilient.md)

## Помощь { #help }

- изучите готовые приложения по наблюдаемости на Java и Kotlin
- сверьтесь со справочными деталями в [Метриках](../documentation/metrics.md), [Трассировке](../documentation/tracing.md), [Пробах](../documentation/probes.md) и [Логировании](../documentation/logging-slf4j.md)
- вернитесь к [HTTP-серверу](http-server.md) за базовой формой API
