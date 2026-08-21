---
search:
  exclude: true
title: Трассировка с Kora
summary: Build focused OpenTelemetry tracing for a Kora HTTP service, including exporter configuration, manual spans, context propagation, Jaeger checks, and trace-aware troubleshooting.
tags: observability, tracing, opentelemetry, spans, tracer, jaeger, context
---

# Трассировка с Kora { #observability-tracing-kora }

Это руководство фокусируется только на трассировке. Вы добавите экспортер OpenTelemetry, настроите имя службы, создадите ручной спан вокруг бизнес-операции и проверите результат трассировки в Jaeger.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## Что вы создадите { #youll-build }

Вы добавите:

- `OpentelemetryHttpExporterModule`
- конфигурацию экспортера OTLP HTTP
- имя службы `guide-observability-app`
- `TracingService` с ручным спаном `user.create`
- интеграцию спана в `UserService`
- локальную проверку трассировки через Jaeger

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- Docker, если хотите локально запустить проверку по принципу черного ящика
- текстовый редактор или среда разработки
- пройденное [руководство по HTTP-серверу](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательная основа"

    Это руководство предполагает, что вы уже прошли **[руководство по HTTP-серверу](http-server.md)** и у вас уже есть HTTP-контроллеры, DTO, репозиторий, служба и конфигурация из того руководства.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что это руководство по наблюдаемости сохраняет тот же HTTP-интерфейс и накладывает поверх него телеметрию.

## Обзор { #overview }

Трассировка нужна, когда одного числа недостаточно. Метрика может сказать: "создание пользователя стало медленным". Но она не покажет, какой именно запрос был медленным, какие шаги он прошел и где потратилось время. Трассировка показывает путь одного конкретного запроса как цепочку связанных шагов.

Kora как фреймворк уже поставляет трассировку для основных поддерживаемых модулей из коробки. HTTP-серверы, клиенты, базы данных, обмен сообщениями и другие интеграции умеют отдавать базовые спаны в формате OpenTelemetry, когда подключены соответствующие модули телеметрии. Поэтому ручной спан в этом руководстве не заменяет встроенную трассировку Kora, а дополняет ее бизнес-шагом, который фреймворк не может вывести сам.

Представьте, что каждый запрос получает маленький билет с номером. Этот номер путешествует вместе с запросом через HTTP-слой, сервисы и дополнительные операции. Каждый важный шаг добавляет запись: "я начал работу", "я закончил работу", "у меня была ошибка". В конце вы видите не просто лог, а дерево выполнения запроса.

В этом руководстве используются такие инструменты:

- OpenTelemetry API дает типы `Tracer`, `Span` и `StatusCode`
- `OpentelemetryHttpExporterModule` подключает экспортер в граф Kora
- `OpentelemetryContext` связывает контекст OpenTelemetry с контекстом Kora
- Jaeger показывает результаты трассировки в локальном интерфейсе

OpenTelemetry можно воспринимать как общий язык трассировки. Приложение создает спаны, экспортер отправляет их наружу, а Jaeger или другой сборщик показывает их оператору. Kora помогает связать это с графом зависимостей и контекстом запроса.

### Модель трассировки { #trace-model }

Трассировка - это история одного запроса. Если пользователь вызывает `POST /users`, запись трассировки может содержать входящий HTTP-спан, спан `user.create`, возможно, спан обращения к базе или внешнему сервису. Все эти части связаны одним идентификатором трассировки.

Спан - это один шаг внутри трассировки. У спана есть имя, время начала, время окончания, статус и дополнительные данные. В этом руководстве спан называется `user.create`, потому что он описывает бизнес-шаг создания пользователя. Такое имя понятнее, чем название метода или класса.

Родительский контекст - это связь между шагами. Если спан `user.create` создается как дочерний от HTTP-запроса, Jaeger покажет его внутри общей записи трассировки. Если родительский контекст потерять, спан может стать отдельной записью трассировки, и вы не поймете, из какого запроса он появился.

Ошибка внутри спана должна быть записана явно. Поэтому код вызывает `span.recordException(e)` и выставляет `StatusCode.ERROR`. Это помогает отличить нормальный медленный запрос от запроса, который закончился исключением.

### Инструменты { #tools }

`OpentelemetryHttpExporterModule` добавляет в приложение отправку данных трассировки по OTLP HTTP. В конфигурации адрес `http://localhost:4318/v1/traces` указывает, куда экспортер отправляет собранные спаны. В локальном сценарии это Jaeger.

`Tracer` - это фабрика спанов. Компонент `TracingService` получает `Tracer` из графа Kora и создает спан через `tracer.spanBuilder("user.create")`. Сам `Tracer` не хранит бизнес-логику; он только помогает создавать измеряемые шаги.

`OpentelemetryContext` нужен, чтобы ручной спан стал частью текущего запроса. Kora использует свой `Context`, и контекст OpenTelemetry хранится внутри него. Поэтому код сначала берет `Context.current()`, затем `OpentelemetryContext.get(ctx)`, затем добавляет новый спан и восстанавливает прежнее состояние в `finally`.

Jaeger - это локальный инструмент просмотра трассировки. Он не нужен приложению для компиляции, но очень полезен для проверки. Вы создаете пользователя, открываете интерфейс Jaeger, выбираете `guide-observability-app` и смотрите, появился ли спан `user.create`.

### Граница спана { #span-boundary }

Спан должен описывать осмысленную работу. Не нужно создавать спан вокруг каждой строки, каждого `if` или каждого маленького преобразования DTO. Слишком много спанов превращает трассировку в шум.

Хорошая граница для ручного спана:

- начинается перед предметной операцией
- заканчивается после получения результата
- записывает исключение, если операция упала
- не содержит персональные данные в имени или атрибутах
- восстанавливает предыдущий контекст

В этом руководстве спан стоит вокруг создания пользователя. Это полезная точка, потому что она показывает, сколько заняла именно бизнес-операция, а не только HTTP-обработка. Если позже вы добавите базу данных или внешний сервис, трассировку можно будет расширить новыми дочерними спанами.

Практический результат такой: трассировка превращает один запрос в видимую цепочку действий. Метрики говорят "что-то стало медленным", а запись трассировки помогает открыть конкретный пример и увидеть, где именно это произошло.

## Зависимости { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        // ... существующие зависимости из руководства по HTTP-серверу ...

        implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        // ... существующие зависимости из руководства по HTTP-серверу ...

        implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    }
    ```

## Модули { #modules }

Подключите экспортер OpenTelemetry к графу приложения.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowHttpServerModule,
            OpentelemetryHttpExporterModule {  // <----- Подключили модуль

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowHttpServerModule,
        OpentelemetryHttpExporterModule  // <----- Подключили модуль
    ```

## Конфигурация { #config }

Настройте экспортер OTLP HTTP. В локальном сценарии данные трассировки отправляются в Jaeger на порт `4318`.

```hocon title="src/main/resources/application.conf"
tracing {
  exporter {
    endpoint = "http://localhost:4318/v1/traces"
    exportTimeout = "5s"
    scheduleDelay = "1s"
    maxExportBatchSize = 512
    maxQueueSize = 2048
  }
  attributes {
    "service.name" = "guide-observability-app"
    "service.namespace" = "kora-guide"
  }
}
```

`service.name` особенно важен: именно по нему вы будете искать записи трассировки в интерфейсе. Если имя меняется между окружениями случайно, поиск становится неудобным.

## Сервис трассировки { #tracing-service }

Создайте компонент, который владеет ручным спаном. Он берет текущий контекст Kora, достает из него контекст OpenTelemetry, добавляет новый спан и восстанавливает прежний контекст в `finally`.

===! ":fontawesome-brands-java: `Java`"

    ```java
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

    ```kotlin
    @Component
    class TracingService(
        private val tracer: Tracer
    ) {
        fun <T> traceUserCreation(action: () -> T): T {
            val ctx = Context.current()
            val otctx = OpentelemetryContext.get(ctx)
            val span = tracer.spanBuilder("user.create")
                .setParent(otctx.context)
                .startSpan()

            OpentelemetryContext.set(ctx, otctx.add(span))
            try {
                val result = action()
                span.setStatus(StatusCode.OK)
                return result
            } catch (e: RuntimeException) {
                span.recordException(e)
                span.setStatus(StatusCode.ERROR, e.message ?: "error")
                throw e
            } finally {
                span.end()
                OpentelemetryContext.set(ctx, otctx)
            }
        }
    }
    ```

Не создавайте спан без родительского контекста, если работа идет внутри HTTP-запроса. Иначе бизнес-спан окажется отдельной записью трассировки и потеряет связь с входящим запросом.

## Интеграция сервиса { #service-integration }

Внедрите `TracingService` в `UserService` и оберните создание пользователя.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public UserResponse createUser(UserRequest request) {
        return tracingService.traceUserCreation(() -> {
            var generatedId = userRepository.save(request.name(), request.email());
            return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        });
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        return tracingService.traceUserCreation {
            val id = userRepository.save(request.name, request.email)
            UserResponse(id, request.name, request.email, LocalDateTime.now())
        }
    }
    ```

## Docker Compose { #docker-compose }

Запустите Jaeger с адресом OTLP HTTP:

```yaml title="docker-compose.yml"
services:
  jaeger:
    image: jaegertracing/all-in-one:1.57
    ports:
      - "16686:16686"
      - "4318:4318"
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
```

## Проверка приложения { #check-app }

Запустите Jaeger, приложение и создайте пользователя:

```bash
docker compose up -d

curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

Откройте [http://localhost:16686](http://localhost:16686), выберите службу `guide-observability-app` и найдите запись трассировки. Внутри нее должен быть спан `user.create`.

## Лучшие практики { #best-practices }

- Называйте спан по операции, а не по Java/Kotlin методу.
- Записывайте исключение и статус ошибки внутри спана.
- Не добавляйте в атрибуты персональные данные.
- Восстанавливайте прежний контекст после ручного спана.
- Держите `service.name` стабильным для окружения.

## Итоги { #summary }

Вы подключили экспортер OpenTelemetry, добавили ручной спан и проверили трассировку в Jaeger.

## Ключевые понятия { #key-concepts }

Tracer:
: объект для создания спана.

Span:
: измеряемый шаг внутри трассировки.

Распространение контекста:
: перенос связи между входящим запросом и вложенными операциями.

OTLP:
: протокол отправки телеметрии в сборщик.

## Устранение неполадок { #troubleshooting }

Трассировка не появляется:
: Проверьте адрес `http://localhost:4318/v1/traces` и доступность Jaeger.

Спан есть, но он отдельной записью трассировки:
: Проверьте `setParent(otctx.getContext())` и восстановление контекста.

В Jaeger нет нужной службы:
: Сверьте `tracing.attributes."service.name"`.

## Что дальше? { #whats-next }

- добавьте бизнес-метрики в [руководстве по метрикам](observability-metrics.md)
- добавьте проверки здоровья в [руководстве по пробам](observability-probes.md)
- сверяйтесь с [документацией по трассировке](../documentation/tracing.md)

## Помощь { #help }

- сравните код с готовыми Java и Kotlin приложениями наблюдаемости
- проверьте настройки экспортера в [документации по трассировке](../documentation/tracing.md)
