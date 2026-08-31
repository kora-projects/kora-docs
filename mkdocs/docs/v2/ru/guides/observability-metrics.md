---
search:
  exclude: true
title: Метрики с Kora
summary: Build focused Micrometer metrics for a Kora HTTP service, including framework metrics, business counters, timers, private metrics endpoints, and practical verification.
description: "Step-by-step Micrometer metrics for a Kora HTTP service: the io.koraframework:micrometer-module dependency, MetricsModule and the injected MeterRegistry, the Prometheus scrape endpoint on httpServer.system.metricsPath, the telemetry.metrics.enabled flag that gates every component metric, slo histogram buckets and common tags, and a custom MetricsService with a Timer, a tagged Counter and a ConcurrentHashMap meter cache."
agent:
  use_when: "Use this file for questions about adding metrics to a Kora application step by step: io.koraframework:micrometer-module, MetricsModule, injecting MeterRegistry, Micrometer Counter and Timer, serviceLevelObjectives, tag cardinality, caching meters in a ConcurrentHashMap, the /metrics endpoint on httpServer.system.port, and why http_server_* metrics are missing until telemetry.metrics.enabled is set to true."
tags: observability, metrics, micrometer, meter-registry, counters, timers, monitoring
---

# Метрики с Kora { #observability-metrics-kora }

Это руководство фокусируется только на метриках. Вы возьмете приложение из руководства по HTTP-серверу и добавите к нему эксплуатационные и бизнес-метрики: модуль Micrometer, эндпоинт `/metrics`
на системном порту, собственный `MetricsService`, счетчик созданных пользователей и таймер операции создания.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## Что вы создадите { #youll-build }

Вы добавите:

- модуль `MetricsModule`
- эндпоинт `/metrics` на системном порту
- `telemetry.metrics.enabled = true` для HTTP-сервера, чтобы метрики компонентов действительно собирались
- собственный `MetricsService`
- таймер `user.creation.duration`
- счетчик `user.creation.total` с тегом `email.provider`
- практическую проверку, что метрики появляются после бизнес-операции

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Текстовый редактор или IDE
- Пройденное [руководство по HTTP-серверу](http-server.md)

Артефакты Kora 2.0 собраны под Java 25, поэтому JDK, которым компилируется приложение, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Необходимая база"

    Руководство предполагает, что вы прошли **[руководство по HTTP-серверу](http-server.md)** и у вас уже есть HTTP-контроллеры, DTO, репозиторий, сервис и конфигурация из того руководства.

    Если руководство по HTTP-серверу еще не пройдено, начните с него: это руководство по наблюдаемости сохраняет тот же HTTP-интерфейс и накладывает поверх него телеметрию.

## Обзор { #overview }

Метрики — это числа, которые приложение отдает наружу. Представьте табло рядом с сервисом: на нем видно, сколько запросов прошло, сколько пользователей создано, как долго выполнялись операции и сколько ресурсов сейчас занято. По одному числу обычно нельзя понять всю историю, но по набору чисел можно заметить, что приложение стало медленнее, начало чаще ошибаться или неожиданно выросло по нагрузке.

Kora как фреймворк уже умеет отдавать основные системные и модульные метрики. Когда вы подключаете нужные модули и включаете их метрики, Kora отдает метрики для поддерживаемых частей приложения: HTTP-серверов, клиентов, баз данных, обмена сообщениями, инфраструктуры времени выполнения и других интеграций. Эти сигналы отдаются в стандартной для наблюдаемости форме: имена и теги метрик следуют семантическим соглашениям OpenTelemetry, а эндпоинт опроса говорит в текстовом формате Prometheus.

Самая важная идея: метрики нужны не только фреймворку и не только инфраструктуре. Фреймворк может посчитать технические вещи, например HTTP-запросы или показатели времени выполнения. Но только ваш код знает предметный смысл события. Kora не может сама догадаться, что вызов `createUser()` означает создание пользователя, поэтому бизнес-метрику нужно поставить в сервисном слое.

В этом руководстве используются три основные сущности:

- `MetricsModule` создает реестр и контракт эндпоинта опроса Prometheus
- `MeterRegistry` — общая точка, через которую код приложения регистрирует собственные метрики
- Micrometer предоставляет типы метрик, например `Counter` и `Timer`

Micrometer можно воспринимать как универсальный блокнот для чисел. Вы говорите ему: "вот счетчик с таким именем" или "вот таймер с таким именем", а дальше Micrometer хранит измерения в форме, которую могут читать системы мониторинга. Kora добавляет этот блокнот в граф приложения, чтобы компонент `MetricsService` мог получить `MeterRegistry` через конструктор.

### Модель сигнала { #signal-model }

Счетчик считает события. Он похож на механический счетчик на двери: каждый раз, когда событие произошло, значение увеличивается. В этом руководстве `user.creation.total` увеличивается после успешного создания пользователя и получает тег `email.provider`, извлеченный из домена email. Такой счетчик помогает отвечать на вопросы:

- сколько созданий пользователей было за последние пять минут
- не прекратилась ли внезапно бизнес-активность
- не изменилась ли частота операции после релиза
- какие email-провайдеры чаще всего встречаются у новых пользователей

Таймер измеряет длительность. Он похож на секундомер, который запускается вокруг операции, но сохраняет не одно значение, а набор измерений. По таймеру можно смотреть среднее время, максимумы, перцентили и количество измерений. В этом руководстве `user.creation.duration` показывает, сколько занимает создание пользователя.

Счетчик и таймер вместе дают более полезную картину, чем каждый по отдельности. Счетчик говорит "операция происходила", таймер говорит "операция занимала столько-то времени". Если счетчик растет, а таймер ухудшается, значит операция выполняется, но стала медленной. Если счетчик перестал расти, возможно, до этой операции вообще перестали доходить запросы.

### Инструменты { #tools }

`MetricsModule` — это Kora-модуль, который добавляет инфраструктуру метрик в приложение. После подключения `MeterRegistry` становится доступен как обычная зависимость графа. Это важно: метрики не создаются через глобальное состояние или случайные `static`-поля. Они живут в графе зависимостей так же, как репозиторий или HTTP-клиент.

`MeterRegistry` — это место регистрации. Когда `MetricsService` вызывает `Counter.builder(...).register(meterRegistry)`, он говорит: "создай или найди метрику с таким именем и описанием". После этого счетчик можно увеличивать, а таймер может записывать длительности. Конкретная реализация, которую собирает Kora, — это `PrometheusMeterRegistry`, поэтому все зарегистрированное через него доступно для опроса в текстовом формате Prometheus.

Эндпоинт `/metrics` — это окно, через которое внешний мониторинг читает накопленные значения. Его обслуживает системный HTTP-сервер, который по умолчанию слушает порт `8085`. Это не случайность: метрики могут раскрывать внутреннее устройство сервиса, поэтому обычные пользователи не должны получать их через публичный API на `8080`.

### Граница метрик { #metrics-boundary }

Хорошая бизнес-метрика ставится там, где есть бизнес-смысл. Для создания пользователя это `UserService`, а не HTTP-контроллер. Контроллер знает, что пришел HTTP-запрос. Сервис знает, что приложение действительно выполняет операцию создания.

В этом руководстве `MetricsService` оборачивает действие через `recordUserCreation()`. Такая форма удобна по трем причинам:

- имена метрик хранятся в одном компоненте
- сервисный метод остается читаемым
- таймер измеряет ровно тот кусок работы, который передан в него

Не нужно добавлять метрику на каждую строку кода. Метрики должны отвечать на вопросы, а не превращаться в шум. Если метрика не помогает принять решение, настроить оповещение или объяснить поведение сервиса, скорее всего, ее рано добавлять.

Еще один важный момент — теги. Теги полезны, когда нужно разделить измерения по стабильным категориям: статус операции, тип команды, имя клиента из небольшого фиксированного списка. Но теги опасны, если туда попадают идентификатор пользователя, полный email, исходный путь запроса или другие бесконечно разнообразные значения. Это называется высокой кардинальностью, и она быстро ломает хранение метрик.

Практический результат простой: подключаем Kora-модуль, включаем метрики у тех модулей, которые вам интересны, регистрируем понятные бизнес-метрики через `MeterRegistry` и проверяем их на системном эндпоинте `/metrics`. Так метрики становятся частью приложения, а не отдельной магией мониторинга.

## Зависимости { #dependencies }

Поддержка Micrometer живет в артефакте `micrometer-module`. Его версия приходит из платформы `io.koraframework:kora-bom`, поэтому в строке зависимости она не указывается.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation "io.koraframework:micrometer-module" //(1)!
    }
    ```

    1.  Модуль метрик Micrometer: создает `PrometheusMeterRegistry` и контракт опроса для системного сервера.

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation("io.koraframework:micrometer-module") //(1)!
    }
    ```

    1.  Модуль метрик Micrometer: создает `PrometheusMeterRegistry` и контракт опроса для системного сервера.

## Модули { #modules }

Добавьте `MetricsModule` в граф приложения рядом с модулями, которые вы уже подключили в руководстве по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            MetricsModule,  // <----- Connected module
            UndertowPublicHttpServerModule {

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
        MetricsModule,  // <----- Connected module
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`MetricsModule` находится в пакете `io.koraframework.micrometer.module`. Он добавляет в граф `MeterRegistry`, привязывает к нему стандартные измерители JVM и процесса и предоставляет контракт
`MetricsScraper`, через который системный сервер отвечает на `/metrics`. `UndertowPublicHttpServerModule` наследует `UndertowSystemHttpServerModule`, поэтому эндпоинт опроса уже разведен по
маршрутам — отдельный управляющий модуль подключать не нужно.

## Конфигурация { #config }

Публичный API остается на `8080`, а все эксплуатационные эндпоинты живут на системном порту `8085`.

Полный справочник конфигурации смотрите в разделах [Метрики](../documentation/metrics.md#configuration) и [HTTP-сервер](../documentation/http-server.md#system-server).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system {
        port = 8085 //(2)!
        metricsPath = "/metrics" //(3)!
      }
      telemetry.metrics.enabled = true //(4)!
    }
    ```

    1.  Публичный HTTP-порт для эндпоинтов приложения (по умолчанию: `8080`).
    2.  Системный HTTP-порт, который отдает метрики и пробы (по умолчанию: `8085`).
    3.  Путь эндпоинта опроса Prometheus на системном сервере (по умолчанию: `/metrics`).
    4.  Включает сбор метрик для публичного HTTP-сервера (по умолчанию: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
        metricsPath: "/metrics" #(3)!
      telemetry:
        metrics:
          enabled: true #(4)!
    ```

    1.  Публичный HTTP-порт для эндпоинтов приложения (по умолчанию: `8080`).
    2.  Системный HTTP-порт, который отдает метрики и пробы (по умолчанию: `8085`).
    3.  Путь эндпоинта опроса Prometheus на системном сервере (по умолчанию: `/metrics`).
    4.  Включает сбор метрик для публичного HTTP-сервера (по умолчанию: `false`).

Такой разнос важен для рабочего окружения: бизнес-клиенты не должны видеть внутренние метрики, а Prometheus, Kubernetes или другой агент мониторинга должен иметь стабильный путь для опроса.

### Включение метрик модулей { #module-metrics }

!!! warning "Метрики компонентов выключены, пока вы их не включите"

    `TelemetryConfig.MetricsConfig#enabled` возвращает `false`, и это значение наследует каждый модуль Kora. Приложение, в котором подключен только `MetricsModule`, стартует нормально и отвечает на
    `/metrics` кодом `200`, но в теле ответа будут лишь значения JVM, процесса и `kora.up`. Никаких `http_server_request_duration_seconds`, `http_client_*` или `db_*` — и ничего в логе, что подсказало бы причину.

Это самый частый способ молча получить пустую панель мониторинга, поэтому стоит разобраться с правилом, которое за этим стоит. Модуль сообщает метрики только тогда, когда выполнены **оба** условия:

- `MetricsModule` подключен, поэтому в графе есть `MeterRegistry`
- у самого модуля `telemetry.metrics.enabled` равно `true`

Если не выполнено хотя бы одно, модуль переходит на `Noop`-фабрику метрик: ни один `Meter` не создается, поэтому в реестре потом нечему пропадать. Это же способ заглушить шумную интеграцию, не
убирая сам модуль.

Блок телеметрии всегда вложен в секцию конфигурации того модуля, которому принадлежит, поэтому метрики включаются там же, где настраивается модуль:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer.telemetry.metrics.enabled = true //(1)!
    httpClient.telemetry.metrics.enabled = true //(2)!
    jdbc.telemetry.metrics.enabled = true //(3)!
    ```

    1.  Метрики публичного HTTP-сервера: длительность запроса и число активных запросов.
    2.  Метрики, общие для декларативных HTTP-клиентов.
    3.  Метрики источника данных JDBC и его пула соединений.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      telemetry:
        metrics:
          enabled: true #(1)!
    httpClient:
      telemetry:
        metrics:
          enabled: true #(2)!
    jdbc:
      telemetry:
        metrics:
          enabled: true #(3)!
    ```

    1.  Метрики публичного HTTP-сервера: длительность запроса и число активных запросов.
    2.  Метрики, общие для декларативных HTTP-клиентов.
    3.  Метрики источника данных JDBC и его пула соединений.

На собственные метрики, которые ваш код регистрирует через `MeterRegistry`, этот флаг не влияет. `user.creation.total` появится, как только подключен `MetricsModule` и код отработал, потому что сам
реестр всегда живой. Флаг управляет только телеметрией модулей Kora.

### Корзины гистограммы и общие теги { #slo-and-tags }

В том же блоке `telemetry.metrics` есть еще две настройки, которые определяют, что именно сообщает модуль:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      telemetry.metrics {
        enabled = true //(1)!
        slo = ["1ms", "10ms", "50ms", "100ms", "500ms", "1s", "5s"] //(2)!
        tags { //(3)!
          "deployment.environment" = "stage"
        }
      }
    }
    ```

    1.  Включает сбор метрик для модуля (по умолчанию: `false`).
    2.  Корзины гистограммы для метрик `Timer` этого модуля, список длительностей (по умолчанию: 14 корзин от `1ms` до `90000ms`).
    3.  Дополнительные теги, добавляемые к каждой метрике, которую сообщает модуль (по умолчанию: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      telemetry:
        metrics:
          enabled: true #(1)!
          slo: [ "1ms", "10ms", "50ms", "100ms", "500ms", "1s", "5s" ] #(2)!
          tags: #(3)!
            "deployment.environment": "stage"
    ```

    1.  Включает сбор метрик для модуля (по умолчанию: `false`).
    2.  Корзины гистограммы для метрик `Timer` этого модуля, список длительностей (по умолчанию: 14 корзин от `1ms` до `90000ms`).
    3.  Дополнительные теги, добавляемые к каждой метрике, которую сообщает модуль (по умолчанию: `{}`).

Длительность в `slo` несет свою единицу измерения (`"1ms"`, `"250ms"`, `"1s"`), а голое число читается как миллисекунды, поэтому `slo = [1, 10, 50]` и `slo = ["1ms", "10ms", "50ms"]` описывают один и тот же список.
Эти два ключа действуют только на метрики, которые сообщает сам модуль. Собственный таймер, который вы сейчас напишете, получает свои корзины из построителя Micrometer — об этом следующий раздел.

## Сервис метрик { #metrics-service }

Создавайте `MetricsService` постепенно. Сначала добавьте простую метрику длительности, затем счетчик, а потом усложните счетчик тегом email-провайдера.

### Таймер { #timer }

Начните с `MeterRegistry` и одного общего `Timer`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MetricsService {

        private final MeterRegistry meterRegistry;
        private final Timer userCreationTimer;

        public MetricsService(MeterRegistry meterRegistry) {
            this.meterRegistry = meterRegistry;
            this.userCreationTimer = Timer.builder("user.creation.duration")
                    .description("Time taken to create users")
                    .register(meterRegistry);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MetricsService(
        private val meterRegistry: MeterRegistry
    ) {
        private val userCreationTimer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .register(meterRegistry)
    }
    ```

`MeterRegistry` — это место, где регистрируются метрики. `Timer` измеряет длительность создания пользователя. Он общий для всех email-провайдеров, потому что время операции нас интересует как единый сигнал: сколько в целом занимает создание пользователя.

#### Корзины длительности { #duration-buckets }

Метрика длительности нужна не только для среднего значения. В рабочем окружении обычно важнее вопросы вроде "сколько операций быстрее 100 ms?", "не ухудшился ли 95-й перцентиль?" или "пора ли сработать оповещению, потому что слишком много запросов вышло за целевую задержку?". Для этого Micrometer может отдавать измерения по корзинам через целевые уровни обслуживания.

Обновите таймер и добавьте несколько практичных границ задержки:

===! ":fontawesome-brands-java: `Java`"

    ```java
    this.userCreationTimer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .serviceLevelObjectives(
                    Duration.ofMillis(50),
                    Duration.ofMillis(100),
                    Duration.ofMillis(250),
                    Duration.ofMillis(500))
            .register(meterRegistry);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val userCreationTimer = Timer.builder("user.creation.duration")
        .description("Time taken to create users")
        .serviceLevelObjectives(
            Duration.ofMillis(50),
            Duration.ofMillis(100),
            Duration.ofMillis(250),
            Duration.ofMillis(500),
        )
        .register(meterRegistry)
    ```

Эти значения не универсальны. Это пример бизнес-ориентиров задержки: 50 ms — отлично, 100 ms — здоровое значение, 250 ms уже стоит наблюдать, а 500 ms для такой небольшой операции выглядит как явный сигнал тревоги. Выбирайте границы под свой сервис.

Это аналог ключа `telemetry.metrics.slo` для собственных метрик: когда Kora регистрирует таймеры своих модулей, она передает настроенные длительности ровно в тот же метод построителя `serviceLevelObjectives(...)`.

### Обертка операции { #operation-wrapper }

Теперь добавьте простую обертку без `email`. Она только измеряет длительность и возвращает результат операции:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public <T> T recordUserCreation(Callable<T> action) {
        try {
            return this.userCreationTimer.recordCallable(action);
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("Failed to record user creation metrics", e);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun <T> recordUserCreation(action: Callable<T>): T {
        return try {
            userCreationTimer.recordCallable(action)
        } catch (e: RuntimeException) {
            throw e
        } catch (e: Exception) {
            throw IllegalStateException("Failed to record user creation metrics", e)
        }
    }
    ```

На этом шаге метрика отвечает только на вопрос "сколько длилась операция?". Если операция падает, исключение уходит наружу как раньше. Метрики не должны менять бизнес-поведение.

### Счетчик { #counter }

Теперь добавьте вторую метрику: счетчик успешных созданий пользователя. Простой счетчик ответил бы только на вопрос "сколько пользователей создано?". Но часто хочется чуть больше контекста, например какие email-провайдеры чаще встречаются у новых пользователей.

Для этого нужны теги. Тег — это короткая стабильная метка, которая добавляется к метрике. Например, одна и та же метрика `user.creation.total` может иметь разные значения тега `email.provider`: `gmail.com`, `example.com`, `company.org`.

Тег должен быть стабильным и иметь ограниченное число вариантов. Хорошие значения тега обычно похожи на маршрут, провайдера, статус, результат или операцию. Плохие значения — полный email, идентификатор пользователя, идентификатор запроса, исходный путь запроса и другие данные, которые могут расти почти без ограничения.

Фреймворковые метрики Kora следуют тому же правилу. Таймер HTTP-сервера `http.server.request.duration` размечен тегами `server.name`, `server.port`, `http.request.method`, `http.route`, `url.scheme`, `server.address` и `error.type` — каждый из них берется из небольшого предсказуемого набора. Шаблон маршрута вроде `/users/{id}` безопасен, а исходный путь вроде `/users/128734` создавал бы новый ряд для каждого пользователя — именно поэтому Kora сообщает шаблон, а если маршрут не совпал, подставляет `UNKNOWN_ROUTE`. Домен после `@` устроен так же: он не раскрывает конкретного пользователя и хорошо подходит для группировки.

#### Динамический тег { #dynamic-tag }

Теперь создайте счетчик с тегом `email.provider`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private Counter userCreationCounter(String emailProvider) {
        return Counter.builder("user.creation.total")
                .description("Total number of users created")
                .tag("email.provider", emailProvider)
                .register(this.meterRegistry);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private fun userCreationCounter(emailProvider: String): Counter {
        return Counter.builder("user.creation.total")
            .description("Total number of users created")
            .tag("email.provider", emailProvider)
            .register(meterRegistry)
    }
    ```

Теперь система мониторинга сможет показать не только общее число созданий, но и группы по провайдеру. После запросов с `alice@example.com` и `bob@gmail.com` вы увидите отдельные ряды для `example.com` и `gmail.com`.

Для этого научите сервис получать провайдера из `email`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static String emailProvider(String email) {
        int at = email.indexOf('@');
        if (at < 0 || at == email.length() - 1) {
            return "unknown";
        }
        return email.substring(at + 1).toLowerCase(Locale.ROOT);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private fun emailProvider(email: String): String {
        val provider = email.substringAfter('@', missingDelimiterValue = "")
        return provider.ifBlank { "unknown" }.lowercase()
    }
    ```

Если email некорректный или домен отсутствует, возвращаем `unknown`. Это лучше, чем создавать пустой тег или падать внутри кода метрики.

#### Кеширование метрик { #metric-caching }

Есть еще один прием для рабочего окружения, который стоит взять из внутренних метрик Kora: не пересобирать один и тот же измеритель с тегами на каждый запрос. Если у метрики нет динамических тегов, лучший вариант — создать ее один раз в конструкторе и хранить как `final` поле, как `userCreationTimer`. Тогда на горячем пути запроса код только вызывает `record(...)` или `increment()`, а вся сборка измерителя уже завершена при создании компонента.

С динамическими тегами ситуация другая. Значение `email.provider` известно только во время обработки конкретного пользователя, поэтому одного общего `final Counter` недостаточно: для `gmail.com`, `example.com` и `company.org` нужны разные временные ряды одной метрики. Но это все равно не значит, что счетчик надо собирать заново на каждый запрос. Правильная форма — создать счетчик один раз для каждого нового провайдера и дальше переиспользовать его.

Внутри Micrometer измеритель определяется именем и полным набором тегов. Когда код вызывает `Counter.builder(...).tag(...).register(meterRegistry)`, Micrometer собирает идентификатор измерителя, проверяет реестр и возвращает уже существующий измеритель или регистрирует новый. Даже если реестр умеет не плодить дубликаты, вызов построителя на каждом запросе все равно заново создает построитель, описание, теги и проходит путь регистрации. Это лишняя работа на самом горячем участке приложения.

Именно поэтому Kora собирает ключ из стабильных значений тегов, регистрирует измеритель один раз через `computeIfAbsent` и дальше только обновляет уже зарегистрированную метрику. В ее метриках HTTP-сервера ключом служит запись из метода, шаблона маршрута, схемы, хоста и типа ошибки — ровно для этого. В нашем бизнес-примере ключ проще: только `email.provider`.

Сделайте то же самое для `email.provider`. Добавьте небольшой кеш счетчиков:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private final ConcurrentHashMap<String, Counter> userCreationCounters = new ConcurrentHashMap<>();

    private Counter userCreationCounter(String emailProvider) {
        return this.userCreationCounters.computeIfAbsent(emailProvider, provider ->
                Counter.builder("user.creation.total")
                        .description("Total number of users created")
                        .tag("email.provider", provider)
                        .register(this.meterRegistry));
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val userCreationCounters = ConcurrentHashMap<String, Counter>()

    private fun userCreationCounter(emailProvider: String): Counter {
        return userCreationCounters.computeIfAbsent(emailProvider) { provider ->
            Counter.builder("user.creation.total")
                .description("Total number of users created")
                .tag("email.provider", provider)
                .register(meterRegistry)
        }
    }
    ```

Метрика все еще создается лениво: счетчик для `gmail.com` появится только тогда, когда пройдет успешная операция с Gmail-адресом. После этого тот же счетчик будет переиспользоваться. На следующих запросах с `gmail.com` `computeIfAbsent` просто вернет уже зарегистрированный `Counter`, и код сразу вызовет `increment()`.

Такой кеш нужен не для каждого измерителя. Если набор тегов фиксированный, держите измеритель как поле сервиса. Кеш нужен там, где тег появляется из данных времени выполнения, но эти данные остаются низкокардинальными и пригодными для группировки. Так граница тега остается видимой, лишняя работа построителя и регистрации не повторяется на каждом вызове, а код остается похожим на подход Kora к ее собственным HTTP-метрикам.

### Финальная обертка операции { #final-wrapper }

Последний шаг — обновить обертку операции. Теперь она принимает `email`, измеряет длительность через таймер, а после успешного выполнения увеличивает счетчик с тегом.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public <T> T recordUserCreation(String email, Callable<T> action) {
        try {
            var result = this.userCreationTimer.recordCallable(action);
            this.userCreationCounter(emailProvider(email)).increment();
            return result;
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("Failed to record user creation metrics", e);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun <T> recordUserCreation(email: String, action: Callable<T>): T {
        return try {
            val result = userCreationTimer.recordCallable(action)
            userCreationCounter(emailProvider(email)).increment()
            result
        } catch (e: RuntimeException) {
            throw e
        } catch (e: Exception) {
            throw IllegalStateException("Failed to record user creation metrics", e)
        }
    }
    ```

Порядок важен: счетчик увеличивается только после успешной операции. Так `user.creation.total` считает созданных пользователей, а не любые попытки вызвать метод.

### Итоговый сервис { #complete-service }

Итоговый компонент остается небольшим, и у каждой части теперь ясная задача:

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/observability/service/MetricsService.java`:

    ```java
    package io.koraframework.guide.observability.service;

    import io.koraframework.common.annotation.Component;
    import io.micrometer.core.instrument.Counter;
    import io.micrometer.core.instrument.MeterRegistry;
    import io.micrometer.core.instrument.Timer;
    import java.time.Duration;
    import java.util.Locale;
    import java.util.concurrent.Callable;
    import java.util.concurrent.ConcurrentHashMap;

    @Component
    public final class MetricsService {

        private final MeterRegistry meterRegistry;
        private final Timer userCreationTimer;
        private final ConcurrentHashMap<String, Counter> userCreationCounters = new ConcurrentHashMap<>();

        public MetricsService(MeterRegistry meterRegistry) {
            this.meterRegistry = meterRegistry;
            this.userCreationTimer = Timer.builder("user.creation.duration")
                    .description("Time taken to create users")
                    .serviceLevelObjectives(
                            Duration.ofMillis(50),
                            Duration.ofMillis(100),
                            Duration.ofMillis(250),
                            Duration.ofMillis(500))
                    .register(meterRegistry);
        }

        public <T> T recordUserCreation(String email, Callable<T> action) {
            try {
                var result = this.userCreationTimer.recordCallable(action);
                this.userCreationCounter(emailProvider(email)).increment();
                return result;
            } catch (RuntimeException e) {
                throw e;
            } catch (Exception e) {
                throw new IllegalStateException("Failed to record user creation metrics", e);
            }
        }

        private Counter userCreationCounter(String emailProvider) {
            return this.userCreationCounters.computeIfAbsent(emailProvider, provider ->
                    Counter.builder("user.creation.total")
                            .description("Total number of users created")
                            .tag("email.provider", provider)
                            .register(this.meterRegistry));
        }

        private static String emailProvider(String email) {
            int at = email.indexOf('@');
            if (at < 0 || at == email.length() - 1) {
                return "unknown";
            }
            return email.substring(at + 1).toLowerCase(Locale.ROOT);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/observability/service/MetricsService.kt`:

    ```kotlin
    package io.koraframework.guide.observability.service

    import io.koraframework.common.annotation.Component
    import io.micrometer.core.instrument.Counter
    import io.micrometer.core.instrument.MeterRegistry
    import io.micrometer.core.instrument.Timer
    import java.time.Duration
    import java.util.concurrent.Callable
    import java.util.concurrent.ConcurrentHashMap

    @Component
    class MetricsService(
        private val meterRegistry: MeterRegistry
    ) {
        private val userCreationTimer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .serviceLevelObjectives(
                Duration.ofMillis(50),
                Duration.ofMillis(100),
                Duration.ofMillis(250),
                Duration.ofMillis(500),
            )
            .register(meterRegistry)
        private val userCreationCounters = ConcurrentHashMap<String, Counter>()

        fun <T> recordUserCreation(email: String, action: Callable<T>): T {
            return try {
                val result = userCreationTimer.recordCallable(action)
                userCreationCounter(emailProvider(email)).increment()
                result
            } catch (e: RuntimeException) {
                throw e
            } catch (e: Exception) {
                throw IllegalStateException("Failed to record user creation metrics", e)
            }
        }

        private fun userCreationCounter(emailProvider: String): Counter {
            return userCreationCounters.computeIfAbsent(emailProvider) { provider ->
                Counter.builder("user.creation.total")
                    .description("Total number of users created")
                    .tag("email.provider", provider)
                    .register(meterRegistry)
            }
        }

        private fun emailProvider(email: String): String {
            val provider = email.substringAfter('@', missingDelimiterValue = "")
            return provider.ifBlank { "unknown" }.lowercase()
        }
    }
    ```

## Интеграция сервиса { #service-integration }

Внедрите `MetricsService` в `UserService` и оберните создание пользователя. Email передается в метрики отдельно, потому что именно из него `MetricsService` извлекает тег провайдера.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public UserResponse createUser(UserRequest request) {
        return metricsService.recordUserCreation(request.email(), () -> {
            var generatedId = userRepository.save(request.name(), request.email());
            return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        });
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        return metricsService.recordUserCreation(request.email) {
            val id = userRepository.save(request.name, request.email)
            UserResponse(id, request.name, request.email, LocalDateTime.now())
        }
    }
    ```

Размещайте бизнес-метрики на уровне сервиса, а не контроллера. Контроллер знает HTTP-форму запроса, а сервис знает, произошла ли предметная операция. Метод при этом остается синхронным — именно
поэтому обернуть его в таймер так просто: нет колбэка, который завершится уже после возврата из `recordCallable`.

## Проверка приложения { #check-app }

Запустите приложение, создайте двух пользователей с разными email-доменами и посмотрите метрики:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'

curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob","email":"bob@gmail.com"}'

curl http://localhost:8085/metrics
```

Экспозиция Prometheus переписывает имена измерителей: точки становятся подчеркиваниями, а `Timer` получает суффикс единицы измерения `_seconds`. Поэтому в выводе должны быть
`user_creation_duration_seconds_count`, `user_creation_duration_seconds_sum`, ряды `user_creation_duration_seconds_bucket`, порожденные целевыми уровнями обслуживания, и `user_creation_total`.
У счетчика также должны быть видны значения тега провайдера вроде `example.com` и `gmail.com`, а имя тега нормализуется до `email_provider`.

Если бизнес-метрик нет, проверьте, что `MetricsModule` подключен, что код доходит до `recordUserCreation()` и что `curl` обращается к системному порту `8085`.

Если же бизнес-метрики есть, а фреймворковых вроде `http_server_request_duration_seconds` нет, это поведение по умолчанию из раздела [Включение метрик модулей](#module-metrics):
`httpServer.telemetry.metrics.enabled` все еще `false`. Эндпоинт в этом состоянии продолжает отвечать `200`, поэтому симптом — пустая панель мониторинга, а не ошибка.

## Лучшие практики { #best-practices }

- Начинайте с небольшого числа бизнес-метрик, которые отвечают на реальные эксплуатационные вопросы.
- Включайте `telemetry.metrics.enabled` для тех модулей, за которыми действительно хотите наблюдать, и оставляйте его выключенным для шумных.
- Не добавляйте теги с идентификаторами пользователей, полными email, исходными путями запросов или другими значениями высокой кардинальности.
- Нормализуйте теги: `gmail.com` лучше, чем полный `bob@gmail.com`.
- Держите имена метрик стабильными: панели мониторинга и оповещения зависят от них.
- Регистрируйте измеритель один раз и переиспользуйте его; кешируйте измерители с тегами по низкокардинальному ключу.
- Измеряйте фактическую операцию, а не подготовку DTO.
- Держите `/metrics` на системном порту.

## Итоги { #summary }

Вы добавили Micrometer, включили метрики HTTP-сервера, вынесли `/metrics` на системный порт, измерили длительность создания пользователя и посчитали успешные создания с тегом email-провайдера.

## Ключевые понятия { #key-concepts }

Counter:
: считает количество событий и может разделять их по стабильным тегам.

Timer:
: измеряет длительность и распределение времени выполнения.

Tag:
: стабильная метка для группировки рядов метрик.

MeterRegistry:
: зависимость графа Kora, через которую регистрируются собственные измерители.

`telemetry.metrics.enabled`:
: переключатель на каждый модуль, который решает, сообщает ли модуль Kora метрики вообще.

Системный порт:
: отдельный порт для эксплуатационных эндпоинтов, например `/metrics` и проб.

## Устранение неполадок { #troubleshooting }

Метрика не появилась:
: Убедитесь, что операция реально была вызвана после старта приложения.

`/metrics` отвечает `200`, но там только значения JVM:
: Установите `<module>.telemetry.metrics.enabled = true` для тех модулей, за которыми хотите наблюдать.

`/metrics` отвечает `# Metric Scraper disabled`:
: `MetricsModule` не подключен, поэтому в графе нет `MetricsScraper`.

`/metrics` недоступен:
: Проверьте `httpServer.system.port` и `httpServer.system.metricsPath`.

Слишком много рядов в мониторинге:
: Уберите теги с динамическими значениями.

## Что дальше? { #whats-next }

- добавьте трассировку в [руководстве по трассировке с Kora](observability-tracing.md)
- добавьте проверки живости и готовности в [руководстве по пробам с Kora](observability-probes.md)
- соберите все сигналы в одном приложении в [руководстве по наблюдаемости и мониторингу с Kora](observability.md)
- сравните детали с [документацией по метрикам](../documentation/metrics.md)

## Помощь { #help }

- посмотрите готовые Java- и Kotlin-приложения observability
- ищите имена и теги метрик модулей в [справочнике метрик](../documentation/metrics.md#metrics-reference)
- сверяйте имена модулей с [документацией по метрикам](../documentation/metrics.md)
