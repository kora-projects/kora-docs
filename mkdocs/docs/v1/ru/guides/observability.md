---
search:
  exclude: true
title: Наблюдаемость и мониторинг с Kora
summary: Learn how to extend the HTTP Server guide with metrics, tracing, structured logging, and health probes
tags: observability, metrics, tracing, logging, health-checks, monitoring
---

# Наблюдаемость и мониторинг с Kora { #observability-monitoring-kora }

Это руководство знакомит с промышленно-ориентированной наблюдаемостью для приложений Kora. В нем рассматривается, как метрики, распределенная трассировка, структурированное журналирование и пробы
здоровья подключаются к графу приложения, как модули телеметрии инструментируют распространенные пути выполнения, и как управляющие конечные точки раскрывают эксплуатационное состояние. Вы также
увидите, как конфигурация наблюдаемости превращает локальное поведение в сигналы, которые могут потреблять системы мониторинга.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## Что вы создадите { #youll-build }

Вы расширите приложение HTTP-сервера:

- метриками Micrometer для событий фреймворка и бизнес-событий
- экспортом трассировок OpenTelemetry по HTTP
- журналированием запросов, обогащенным контекстом трассировки
- пробами живости и готовности на закрытом управляющем порту
- тестами, сфокусированными на наблюдаемости, которые проверяют метрики, пробы и поведение трассировки

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- Docker, если хотите локально запустить smoke-тест по принципу черного ящика
- текстовый редактор или среда разработки
- пройденное [руководство по HTTP-серверу](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательная основа"

    Это руководство предполагает, что вы уже прошли **[руководство по HTTP-серверу](http-server.md)** и у вас уже есть HTTP-контроллеры, DTO, репозиторий, служба и конфигурация из того руководства.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что это руководство по наблюдаемости сохраняет тот же HTTP-интерфейс и накладывает поверх него телеметрию.

## Обзор { #overview }

Наблюдаемость позволяет понимать работающую службу без догадок только по симптомам. Когда API становится медленнее, начинает периодически падать или работает в одном окружении, но не работает в
другом, вам нужны сигналы изнутри приложения, которые объясняют, что происходит.

Важный сдвиг в том, что наблюдаемость - это не отдельный режим отладки. Это часть договора времени выполнения промышленной службы. Служба должна раскрывать достаточно метрик, трассировок, журналов и
проб, чтобы операторы могли понять, здорова ли она и где происходят сбои.

### Три основных сигнала { #three-core-signals }

На практике наблюдаемость Kora строится вокруг трех взаимодополняющих сигналов:

- метрики [Micrometer](https://docs.micrometer.io/micrometer/reference/) показывают, как система ведет себя в совокупности с течением времени
- трассировки [OpenTelemetry](https://opentelemetry.io/docs/) показывают жизненный цикл одного запроса по цепочке вызовов
- пробы сообщают платформе, жив ли процесс и готов ли он принимать трафик

Метрики полезны, когда нужны тенденции, частоты и сигналы насыщения, а не подробности одного события. Kora использует Micrometer, поэтому приложение может публиковать в одном месте и метрики
фреймворка, и бизнес-метрики. В типичной службе вы увидите несколько категорий метрик:

- инфраструктурные метрики, например память JVM, CPU, потоки и использование на уровне процесса
- метрики HTTP-сервера, например число запросов, задержка, активные запросы и распределение кодов статуса
- метрики журналирования и времени выполнения, которые помогают объяснить внутреннюю активность
- пользовательские бизнес-метрики, например сколько пользователей создано и сколько времени заняла эта операция

Эти типы метрик отвечают на разные вопросы. Счетчики помогают отслеживать итоги и частоты, таймеры помогают измерять длительность и распределения задержек, а датчики помогают наблюдать значения,
которые со временем растут и уменьшаются. Вместе они позволяют замечать регрессии, настраивать оповещения о сбоях и понимать поведение системы до того, как пользователи начнут сообщать об инцидентах.

Трассировка решает другую задачу. Метрики могут показать, что запросы медленные, но не показывают, какой конкретный запрос был медленным и где было потрачено время. Распределенная трассировка следует
за одним запросом по приложению и прикрепляет trace идентификатор и span идентификатор к выполняемой работе. Это значительно упрощает сопоставление журналов, изучение потока запроса и понимание, где возникают задержки или
сбои, когда запрос проходит через несколько слоев или служб.

Пробы в первую очередь нужны для эксплуатации и оркестрации. Проба живости отвечает на вопрос "нужно ли перезапустить этот процесс?", а проба готовности отвечает "готов ли этот экземпляр обслуживать
трафик прямо сейчас?" Они критически важны для развертываний в стиле [Docker](https://docs.docker.com/) и [Kubernetes](https://kubernetes.io/docs/home/), потому что позволяют балансировщикам нагрузки
и оркестраторам не отправлять трафик на экземпляр, который еще прогревается или временно нездоров.

### Наблюдаемость в Kora { #observability-kora }

Kora подключает наблюдаемость через модули и конфигурацию. Компоненты фреймворка могут автоматически выдавать телеметрию, а прикладной код может добавлять пользовательские бизнес-сигналы там, где
фреймворк не может знать смысл предметной области.

Это руководство добавляет задачи наблюдаемости вокруг HTTP-приложения:

- `MetricsModule` включает метрики фреймворка и дает доступ к `MeterRegistry`
- `OpentelemetryHttpExporterModule` экспортирует трассировки в совместимый с OpenTelemetry коллектор
- `CustomReadinessProbe` и `ApplicationHealthProbe` питают `/system/readiness` и `/system/liveness`
- `MetricsService` записывает бизнес-метрики для создания пользователей
- тесты наблюдаемости становятся источником истины для управляющих конечных точек и журналирования с учетом трассировки

### Эксплуатационные границы { #operational-boundaries }

Конечные точки наблюдаемости обычно должны находиться на закрытом управляющем порту, а не на открытом бизнес-API. Такое разделение позволяет платформам, балансировщикам нагрузки и инструментам
мониторинга проверять здоровье службы, не раскрывая внутренние эксплуатационные детали обычным клиентам. Руководство разделяет поведение открытого API и управляющее поведение, чтобы форма времени
выполнения соответствовала промышленным ожиданиям.

Практический ход такой:

1. добавить модули метрик, трассировки, журналирования и проб
2. подключить модули наблюдаемости к графу Kora
3. добавить пользовательские пробы готовности и живости
4. записывать бизнес-метрики в коде службы
5. настроить управляющие конечные точки и экспорт телеметрии
6. проверить метрики, пробы и журналирование с учетом трассировки в тестах

## Зависимости { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    dependencies {
        // ... существующие зависимости из руководства по HTTP-серверу ...

        implementation("ru.tinkoff.kora:micrometer-module")
        implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... существующие зависимости из руководства по HTTP-серверу ...

        implementation("ru.tinkoff.kora:micrometer-module")
        implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    }
    ```

## Модули { #modules }

Добавьте модули наблюдаемости в тот же граф приложения, который вы создали в руководстве по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/ru/tinkoff/kora/guide/observability/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.observability;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.micrometer.module.MetricsModule;
    import ru.tinkoff.kora.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            MetricsModule,  // <----- Подключили модуль
            UndertowHttpServerModule,
            OpentelemetryHttpExporterModule {  // <----- Подключили модуль

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/observability/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.micrometer.module.MetricsModule
    import ru.tinkoff.kora.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        MetricsModule,  // <----- Подключили модуль
        UndertowHttpServerModule,
        OpentelemetryHttpExporterModule  // <----- Подключили модуль

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Конфигурация { #config }

Открытый API по-прежнему работает на `8080`, но все управляющие конечные точки в этом руководстве живут на закрытом порту `8085`.

Обновите `src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в разделах [HTTP-сервер](../documentation/http-server.md), [Трассировка](../documentation/tracing.md)
и [Журналирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      publicApiHttpPort = 8080 //(1)!
      privateApiHttpPort = 8085 //(2)!
      privateApiHttpMetricsPath = "/metrics" //(3)!
      privateApiHttpLivenessPath = "/system/liveness" //(4)!
      privateApiHttpReadinessPath = "/system/readiness" //(5)!
      telemetry.logging.enabled = true //(6)!
    }

    tracing {
      exporter {
        endpoint = "http://localhost:4318/v1/traces" //(7)!
      }
    }

    logging {
      levels {
        "ROOT" = "WARN" //(8)!
        "ru.tinkoff.kora" = "INFO" //(9)!
        "ru.tinkoff.kora.guide.observability" = "DEBUG" //(10)!
      }
    }
    ```

    1. Открытый HTTP-порт по умолчанию, который используется конечными точками приложения.
    2. Закрытый HTTP-порт по умолчанию, который используется пробами, метриками и управляющими конечными точками.
    3. Закрытый HTTP-путь по умолчанию, который открывает метрики.
    4. Закрытый HTTP-путь по умолчанию, который используется для пробы живости.
    5. Закрытый HTTP-путь по умолчанию, который используется для пробы готовности.
    6. Включает возможность для этого раздела конфигурации.
    7. Конечная точка экспортера телеметрии.
    8. Уровень журналирования для `ROOT`.
    9. Уровень журналирования для `ru.tinkoff.kora`.
    10. Уровень журналирования для `ru.tinkoff.kora.guide.observability`.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      publicApiHttpPort: 8080 #(1)!
      privateApiHttpPort: 8085 #(2)!
      privateApiHttpMetricsPath: "/metrics" #(3)!
      privateApiHttpLivenessPath: "/system/liveness" #(4)!
      privateApiHttpReadinessPath: "/system/readiness" #(5)!
      telemetry:
        logging:
          enabled: true #(6)!
    tracing:
      exporter:
        endpoint: "http://localhost:4318/v1/traces" #(7)!
    logging:
      levels:
        ROOT: "WARN" #(8)!
        "ru.tinkoff.kora": "INFO" #(9)!
        "ru.tinkoff.kora.guide.observability": "DEBUG" #(10)!
    ```

    1. Открытый HTTP-порт по умолчанию, который используется конечными точками приложения.
    2. Закрытый HTTP-порт по умолчанию, который используется пробами, метриками и управляющими конечными точками.
    3. Закрытый HTTP-путь по умолчанию, который открывает метрики.
    4. Закрытый HTTP-путь по умолчанию, который используется для пробы живости.
    5. Закрытый HTTP-путь по умолчанию, который используется для пробы готовности.
    6. Включает возможность для этого раздела конфигурации.
    7. Конечная точка экспортера телеметрии.
    8. Уровень журналирования для `ROOT`.
    9. Уровень журналирования для `ru.tinkoff.kora`.
    10. Уровень журналирования для `ru.tinkoff.kora.guide.observability`.

Почему это важно:

- `/metrics`, `/system/liveness` и `/system/readiness` намеренно изолированы от открытого API
- `telemetry.logging.enabled = true` позволяет HTTP-телеметрии обогащать журналы сведениями трассировки
- экспортер трассировки может отправлять интервалы в любой OTLP HTTP-коллектор; если локально ничего не запущено, приложение все равно стартует, а тесты все равно могут проверять связь журналов с
  трассировкой и управляющие конечные точки

## Метрики { #metrics }

Kora уже автоматически открывает многие метрики фреймворка. Добавляйте пользовательские метрики только для бизнес-событий, важных для вашего приложения.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/observability/service/MetricsService.java`:

    ```java
    package ru.tinkoff.kora.guide.observability.service;

    import io.micrometer.core.instrument.Counter;
    import io.micrometer.core.instrument.MeterRegistry;
    import io.micrometer.core.instrument.Timer;
    import java.util.concurrent.Callable;
    import ru.tinkoff.kora.common.Component;

    @Component
    public final class MetricsService {

        private final Counter userCreationCounter;
        private final Timer userCreationTimer;

        public MetricsService(MeterRegistry meterRegistry) {
            this.userCreationCounter = Counter.builder("user.creation.total")
                    .description("Total number of users created")
                    .register(meterRegistry);
            this.userCreationTimer = Timer.builder("user.creation.duration")
                    .description("Time taken to create users")
                    .register(meterRegistry);
        }

        public <T> T recordUserCreation(Callable<T> action) {
            this.userCreationCounter.increment();
            try {
                return this.userCreationTimer.recordCallable(action);
            } catch (RuntimeException e) {
                throw e;
            } catch (Exception e) {
                throw new IllegalStateException("Failed to record user creation metrics", e);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/observability/service/MetricsService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability.service

    import io.micrometer.core.instrument.Counter
    import io.micrometer.core.instrument.MeterRegistry
    import io.micrometer.core.instrument.Timer
    import ru.tinkoff.kora.common.Component
    import java.util.concurrent.Callable

    @Component
    class MetricsService(
        meterRegistry: MeterRegistry
    ) {
        private val userCreationCounter: Counter = Counter.builder("user.creation.total")
            .description("Total number of users created")
            .register(meterRegistry)

        private val userCreationTimer: Timer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .register(meterRegistry)

        fun <T> recordUserCreation(action: Callable<T>): T {
            userCreationCounter.increment()
            return try {
                userCreationTimer.recordCallable(action)
            } catch (e: RuntimeException) {
                throw e
            } catch (e: Exception) {
                throw IllegalStateException("Failed to record user creation metrics", e)
            }
        }
    }
    ```

## Сервис трассировки { #tracing-service }

Телеметрия фреймворка уже создает интервалы для поддерживаемых путей выполнения, например для обработки HTTP-запросов. Ручная трассировка нужна, когда вы хотите отметить бизнес-операцию внутри такого
запроса, назвать ее в терминах предметной области и привязать успех или ошибку именно к этой части работы.

В справочнике по трассировке этот шаблон разобран в разделе [Синхронная трассировка](../documentation/tracing.md#tracing-sync): внедрить `Tracer`, создать span с текущим контекстом как родителем,
поместить span в `OpentelemetryContext` и всегда завершать span в `finally`.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/observability/service/TracingService.java`:

    ```java
    package ru.tinkoff.kora.guide.observability.service;

    import io.opentelemetry.api.trace.StatusCode;
    import io.opentelemetry.api.trace.Tracer;
    import java.util.concurrent.Callable;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.opentelemetry.common.OpentelemetryContext;

    @Component
    public final class TracingService {

        private final Tracer tracer;

        public TracingService(Tracer tracer) {
            this.tracer = tracer;
        }

        public <T> T traceUserCreation(Callable<T> action) {
            var ctx = Context.current();
            var otctx = OpentelemetryContext.get(ctx);
            var span = tracer.spanBuilder("user.create")
                    .setParent(otctx.getContext())
                    .startSpan();

            OpentelemetryContext.set(ctx, otctx.add(span));
            try {
                var result = action.call();
                span.setStatus(StatusCode.OK);
                return result;
            } catch (RuntimeException e) {
                span.recordException(e);
                span.setStatus(StatusCode.ERROR, e.getMessage());
                throw e;
            } catch (Exception e) {
                span.recordException(e);
                span.setStatus(StatusCode.ERROR, e.getMessage());
                throw new IllegalStateException("Failed to trace user creation", e);
            } finally {
                span.end();
                OpentelemetryContext.set(ctx, otctx);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/observability/service/TracingService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability.service

    import io.opentelemetry.api.trace.StatusCode
    import io.opentelemetry.api.trace.Tracer
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.opentelemetry.common.OpentelemetryContext

    @Component
    class TracingService(
        private val tracer: Tracer
    ) {
        fun <T> traceUserCreation(action: () -> T): T {
            val ctx = Context.current()
            val otctx = OpentelemetryContext.get(ctx)
            val span = tracer.spanBuilder("user.create")
                .setParent(otctx.getContext())
                .startSpan()

            OpentelemetryContext.set(ctx, otctx.add(span))
            try {
                val result = action()
                span.setStatus(StatusCode.OK)
                return result
            } catch (e: RuntimeException) {
                span.recordException(e)
                span.setStatus(StatusCode.ERROR, e.message)
                throw e
            } finally {
                span.end()
                OpentelemetryContext.set(ctx, otctx)
            }
        }
    }
    ```

Этот span станет дочерним для текущего HTTP request span, когда операция выполняется во время обработки запроса. Если операция завершится ошибкой, span запишет исключение и будет экспортирован со
статусом ошибки.

## Интеграция трассировки { #tracing-integration }

Сохраните HTTP-договор из предыдущего руководства и добавьте наблюдаемость там, где происходит бизнес-действие.

В этом руководстве меняется только связывание конструктора `UserService` и `createUser()`. Остальные методы службы остаются такими же, как в руководстве по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/ru/tinkoff/kora/guide/observability/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.guide.observability.service;

    import java.time.LocalDateTime;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.observability.dto.UserRequest;
    import ru.tinkoff.kora.guide.observability.dto.UserResponse;
    import ru.tinkoff.kora.guide.observability.repository.UserRepository;

    @Component
    public final class UserService {

        private static final Logger logger = LoggerFactory.getLogger(UserService.class);

        private final UserRepository userRepository;
        private final MetricsService metricsService;
        private final TracingService tracingService;

        public UserService(UserRepository userRepository, MetricsService metricsService, TracingService tracingService) {
            this.userRepository = userRepository;
            this.metricsService = metricsService;
            this.tracingService = tracingService;
        }

        public UserResponse createUser(UserRequest request) {
            logger.info("Creating user with name={} and email={}", request.name(), request.email());
            return tracingService.traceUserCreation(() -> metricsService.recordUserCreation(() -> {
                var generatedId = userRepository.save(request.name(), request.email());
                var user = new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
                logger.info("Created user with id={}", generatedId);
                return user;
            }));
        }

        // getUser(), getUsers(), updateUser(), deleteUser(), and sorting logic
        // stay the same as in the HTTP server guide.
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/observability/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability.service

    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.observability.dto.UserRequest
    import ru.tinkoff.kora.guide.observability.dto.UserResponse
    import ru.tinkoff.kora.guide.observability.repository.UserRepository
    import java.time.LocalDateTime

    @Component
    class UserService(
        private val userRepository: UserRepository,
        private val metricsService: MetricsService,
        private val tracingService: TracingService
    ) {
        private val logger = LoggerFactory.getLogger(UserService::class.java)

        fun createUser(request: UserRequest): UserResponse {
            logger.info("Creating user with name={} and email={}", request.name, request.email)
            return tracingService.traceUserCreation {
                metricsService.recordUserCreation {
                    val generatedId = userRepository.save(request.name, request.email)
                    val user = UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
                    logger.info("Created user with id={}", generatedId)
                    user
                }
            }
        }

        // getUser(), getUsers(), updateUser(), deleteUser(), and sorting logic
        // stay the same as in the HTTP server guide.
    }
    ```

## Пробы { #probes }

Готовность должна стать здоровой после завершения запуска. Она не должна падать бесконечно.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/observability/health/CustomReadinessProbe.java`:

    ```java
    package ru.tinkoff.kora.guide.observability.health;

    import java.time.Duration;
    import java.time.Instant;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.readiness.ReadinessProbe;
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure;

    @Component
    public final class CustomReadinessProbe implements ReadinessProbe {

        private static final Duration WARMUP_PERIOD = Duration.ofMillis(500);

        private final Instant startedAt = Instant.now();

        @Override
        public ReadinessProbeFailure probe() {
            var readyAt = startedAt.plus(WARMUP_PERIOD);
            if (Instant.now().isBefore(readyAt)) {
                return new ReadinessProbeFailure("Service is warming up");
            }
            return null;
        }
    }
    ```

    Создайте `src/main/java/ru/tinkoff/kora/guide/observability/health/ApplicationHealthProbe.java`:

    ```java
    package ru.tinkoff.kora.guide.observability.health;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.liveness.LivenessProbe;
    import ru.tinkoff.kora.common.liveness.LivenessProbeFailure;

    @Component
    public final class ApplicationHealthProbe implements LivenessProbe {

        @Override
        public LivenessProbeFailure probe() {
            return null;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/observability/health/CustomReadinessProbe.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability.health

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.readiness.ReadinessProbe
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure
    import java.time.Duration
    import java.time.Instant

    @Component
    class CustomReadinessProbe : ReadinessProbe {
        private val startedAt = Instant.now()

        override fun probe(): ReadinessProbeFailure? {
            val readyAt = startedAt.plus(Duration.ofMillis(500))
            return if (Instant.now().isBefore(readyAt)) {
                ReadinessProbeFailure("Service is warming up")
            } else {
                null
            }
        }
    }
    ```

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/observability/health/ApplicationHealthProbe.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability.health

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.liveness.LivenessProbe
    import ru.tinkoff.kora.common.liveness.LivenessProbeFailure

    @Component
    class ApplicationHealthProbe : LivenessProbe {
        override fun probe(): LivenessProbeFailure? = null
    }
    ```

## Docker Compose { #docker-compose }

Если хотите локально изучить трассировки, запустите контейнер Jaeger all-in-one, который открывает и OTLP HTTP-точку приема, и пользовательский интерфейс Jaeger.

Создайте `docker-compose.yml` в каталоге модуля приложения:

```yaml
services:
    jaeger:
        image: jaegertracing/all-in-one:latest
        ports:
            - "16686:16686"
            - "4318:4318"
        environment:
            COLLECTOR_OTLP_ENABLED: "true"
```

Запустите Jaeger:

```bash
docker compose up -d
```

Затем:

- оставьте `tracing.exporter.endpoint = "http://localhost:4318/v1/traces"` в `application.conf`
- запустите приложение через `./gradlew run`
- отправьте несколько запросов на `http://localhost:8080/users`
- откройте [http://localhost:16686](http://localhost:16686) и найдите службу `guide-observability-app`

Остановите Jaeger, когда закончите:

```bash
docker compose down
```

Эта настройка необязательна, но это самый быстрый способ локально проверить, что интервалы экспортируются и что идентификаторы трассировки из журналов соответствуют трассировкам, видимым в
пользовательском интерфейсе.

## Проверка приложения { #check-app }

Используйте обычный поток Gradle для руководств времени выполнения:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

Когда приложение запущено, проверьте управляющие конечные точки на закрытом порту:

```bash
curl http://localhost:8085/system/liveness
curl http://localhost:8085/system/readiness
curl http://localhost:8085/metrics
```

Вы по-прежнему можете обращаться к открытому API на `8080`, например:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

## Лучшие практики { #best-practices }

- Держите бизнес-метрики в отдельной службе, чтобы контроллеры оставались сосредоточены на HTTP-задачах.
- Предпочитайте наблюдать бизнес-действия в слое службы, где встречаются журналы, метрики и контекст трассировки.
- Используйте ручные span для доменных операций, которые инструментация фреймворка не может точно назвать сама.
- Держите готовность легкой и временной. Проба готовности должна падать во время запуска или проверок зависимостей, а затем восстанавливаться.
- Открывайте здоровье и метрики только на закрытом порту `8085`.
- Рассматривайте тесты как источник истины для поведения наблюдаемости и держите их ограниченными тем, чему действительно учит руководство.

## Итоги { #summary }

Вы расширили приложение HTTP-сервера возможностями наблюдаемости Kora, не меняя договор открытого API. Теперь приложение открывает управляющие конечные точки на закрытом порту, записывает
бизнес-метрики для создания пользователей, создает ручной span `user.create`, выдает журналы с учетом трассировки и сообщает живость/готовность через пробы Kora.

## Ключевые понятия { #key-concepts }

- как `MetricsModule` включает метрики фреймворка и пользовательское использование `MeterRegistry`
- как `OpentelemetryHttpExporterModule` добавляет экспорт трассировок в граф приложения
- как внедренный `Tracer` и `OpentelemetryContext` создают ручной дочерний span для бизнес-операции
- почему управляющим конечным точкам место на закрытом порту
- как моделировать пробы живости и готовности с реалистичным поведением
- как проверять возможности наблюдаемости сфокусированными компонентными тестами и тестами по принципу черного ящика

## Устранение неполадок { #troubleshooting }

**`./gradlew clean` или `./gradlew test` зависает:**

Остановите демоны Gradle и повторите:

```bash
./gradlew --stop
./gradlew clean classes
./gradlew test
```

**Windows сообщает `AccessDeniedException` в кеше Gradle:**

Обычно это значит, что демон или другой процесс все еще удерживает файлы в каталогах `.gradle` или `build`. Запустите `./gradlew --stop`, закройте процессы среда разработки, которые могут блокировать файлы, и
повторите сборку.

**Readiness, Liveness или Metrics возвращает `404`:**

Проверьте, что используете закрытый порт `8085`, а не открытый порт `8080`, и что эти пути настроены:

Полный справочник по конфигурации смотрите в разделе [HTTP-сервер](../documentation/http-server.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    privateApiHttpMetricsPath = "/metrics" //(1)!
    privateApiHttpLivenessPath = "/system/liveness" //(2)!
    privateApiHttpReadinessPath = "/system/readiness" //(3)!
    ```

    1. Закрытый HTTP-путь по умолчанию, который открывает метрики.
    2. Закрытый HTTP-путь по умолчанию, который используется для пробы живости.
    3. Закрытый HTTP-путь по умолчанию, который используется для пробы готовности.

=== ":simple-yaml: `YAML`"

    ```yaml
    privateApiHttpMetricsPath: "/metrics" #(1)!
    privateApiHttpLivenessPath: "/system/liveness" #(2)!
    privateApiHttpReadinessPath: "/system/readiness" #(3)!
    ```

    1. Закрытый HTTP-путь по умолчанию, который открывает метрики.
    2. Закрытый HTTP-путь по умолчанию, который используется для пробы живости.
    3. Закрытый HTTP-путь по умолчанию, который используется для пробы готовности.

**Трассировки локально никуда не экспортируются:**

Это ожидаемо, если на `http://localhost:4318/v1/traces` не запущен OTLP-коллектор. Приложение и тесты все равно работают, но для просмотра экспортированных трассировок понадобится коллектор, например
Jaeger или OpenTelemetry Collector.

## Что дальше? { #whats-next }

- [Тестирование с JUnit](testing-junit.md), чтобы добавить сфокусированные компонентные тесты вокруг наблюдаемых компонентов.
- [База данных JDBC](database-jdbc.md) перед [руководством по тестированию как черный ящик](testing-black-box.md), потому что это руководство предполагает приложение на JDBC.
- [Сообщения с Kafka](messaging-kafka.md), чтобы наблюдать асинхронную обработку.
- [Шаблоны устойчивости](resilient.md), чтобы связать метрики и трассировки со сбоями, повторами и автоматическими выключателями.

## Помощь { #help }

Если что-то не совпадает с вашим локальным приложением:

- сравните с [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app) и [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app)
- вернитесь к [HTTP-серверу](http-server.md), чтобы свериться с формой базового API
- проверьте [документацию метрик](../documentation/metrics.md)
- проверьте [документацию трассировки](../documentation/tracing.md)
- проверьте [документацию журналирования](../documentation/logging-slf4j.md)
- проверьте [документацию проб](../documentation/probes.md)
