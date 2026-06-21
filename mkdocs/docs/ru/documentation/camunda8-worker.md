---
description: "Explains Kora Camunda 8 Zeebe worker integration, worker configuration, job handling, variables, telemetry, and supported handler signatures. Use when working with @JobWorker, ZeebeClient, ActivatedJob, JobClient, Camunda8WorkerModule, Camunda8WorkerConfig."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Camunda 8 Zeebe worker integration, worker configuration, job handling, variables, telemetry, and supported handler signatures; key triggers include @JobWorker, ZeebeClient, ActivatedJob, JobClient, Camunda8WorkerModule, Camunda8WorkerConfig."
---

??? warning "Экспериментальный модуль"

    **Экспериментальный** модуль является полностью рабочим и протестированным, но требует дополнительной апробации и аналитики по использованию,
    по этой причине `API` может потенциально претерпеть незначительные изменения перед полной готовностью.

Модуль подключает клиент [Camunda 8 (Zeebe)](https://docs.camunda.io/docs/components/concepts/job-workers/) и создает
исполнителей заданий для внешнего оркестратора процессов. В `Kora` такой исполнитель объявляется обычным компонентом:
метод с аннотацией `@JobWorker` получает переменные процесса, выполняет работу и возвращает результат, который будет
передан обратно в `Zeebe`.

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:camunda-zeebe-worker"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ZeebeWorkerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:camunda-zeebe-worker")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ZeebeWorkerModule
    ```

## Конфигурация { #configuration }

Пример полной конфигурации клиента, описанной в классе `ZeebeClientConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `HOCON`"

    ```javascript
    zeebe {
        client {
            executionThreads = 2 //(1)!
            keepAlive = "45s" //(2)!
            tls = true //(3)!
            certificatePath = "/file/path/to/cert.crt" //(4)!
            initializationFailTimeout = "15s" //(5)!
            grpc {
                url = "grpc://localhost:8090" //(6)!
                ttl = "1h" //(7)!
                maxMessageSize = "4Mib" //(8)!
                retryPolicy {
                    enabled = true //(9)!
                    attempts = 5 //(10)!
                    delay = "100ms" //(11)!
                    delayMax = "5s" //(12)!
                    step = 3.0 //(13)!
                }
            }
            rest {
                url = "http://localhost:8080" //(14)!
            }
            deployment {
                resources = "classpath:bpm" //(15)!
                timeout = "45s" //(16)!
            }
            telemetry {
                logging {
                    enabled = false //(17)!
                }
                metrics {
                    enabled = true //(18)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(19)!
                    tags = { // (20)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(21)!
                    attributes = { // (22)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1.  Максимальное количество потоков для исполнителей заданий (по умолчанию: количество ядер процессора, но не меньше `2`)
    2.  Время без активности чтения перед отправкой проверки `KeepAlive` (по умолчанию: `45s`)
    3.  Использовать ли `TLS` при подключении (по умолчанию: `true`)
    4.  [Файловый путь](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/FileInputStream.html) до сертификата для подключения; если не указан, используется системный сертификат (по умолчанию не указано, необязательно)
    5.  Максимальное время ожидания проверки доступности топологии при запуске клиента (по умолчанию не указано, необязательно)
    6.  `URL` для подключения по `gRPC` (`обязательная`, по умолчанию не указано)
    7.  Время, в течение которого сообщение должно храниться на брокере при отправке по `gRPC` (по умолчанию: `1h`)
    8.  Максимальный размер входящего сообщения по `gRPC` (по умолчанию: `4Mib`)
    9.  Включена ли политика повторов для `gRPC`-соединения (по умолчанию: `true`)
    10. Количество попыток (по умолчанию: `5`)
    11. Начальная задержка между попытками (по умолчанию: `100ms`)
    12. Максимальная задержка между попытками (по умолчанию: `5s`)
    13. Коэффициент увеличения задержки между попытками (по умолчанию: `3.0`)
    14. `URL` для подключения к `REST`-адресу `Zeebe`; если указан, клиент предпочитает `REST` вместо `gRPC` для поддерживаемых операций (`обязательная` внутри необязательной секции `rest`, по умолчанию не указано)
    15. Пути для поиска ресурсов, которые будут загружены в оркестратор после запуска (по умолчанию: `[]`)
    16. Максимальное время ожидания загрузки ресурсов (по умолчанию: `45s`)
    17. Включает логирование модуля (по умолчанию: `false`)
    18. Включает метрики модуля (по умолчанию: `true`)
    19. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    20. Настройка тегов для метрик (по умолчанию: `{}`)
    21. Включает трассировку модуля (по умолчанию: `true`)
    22. Настройка атрибутов для трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      client:
        executionThreads: 2 #(1)!
        keepAlive: "45s" #(2)!
        tls: true #(3)!
        certificatePath: "/file/path/to/cert.crt" #(4)!
        initializationFailTimeout: "15s" #(5)!
        grpc:
          url: "grpc:#localhost:8090" //(6)!
          ttl: "1h" #(7)!
          maxMessageSize: "4Mib" #(8)!
          retryPolicy:
            enabled: true #(9)!
            attempts: 5 #(10)!
            delay: "100ms" #(11)!
            delayMax: "5s" #(12)!
            step: 3.0 #(13)!
        rest:
          url: "http://localhost:8080" #(14)!
        deployment:
          resources: "classpath:bpm" #(15)!
          timeout: "45s" #(16)!
        telemetry:
          logging:
            enabled: false #(17)!
          metrics:
            enabled: true #(18)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(19)!
            tags: #(20)!
              key1: "value1"
              key2: "value2"
          tracing:
            enabled: true #(21)!
            attributes: #(22)!
              key1: "value1"
              key2: "value2"
    ```

    1.  Максимальное количество потоков для исполнителей заданий (по умолчанию: количество ядер процессора, но не меньше `2`)
    2.  Время без активности чтения перед отправкой проверки `KeepAlive` (по умолчанию: `45s`)
    3.  Использовать ли `TLS` при подключении (по умолчанию: `true`)
    4.  [Файловый путь](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/FileInputStream.html) до сертификата для подключения; если не указан, используется системный сертификат (по умолчанию не указано, необязательно)
    5.  Максимальное время ожидания проверки доступности топологии при запуске клиента (по умолчанию не указано, необязательно)
    6.  `URL` для подключения по `gRPC` (`обязательная`, по умолчанию не указано)
    7.  Время, в течение которого сообщение должно храниться на брокере при отправке по `gRPC` (по умолчанию: `1h`)
    8.  Максимальный размер входящего сообщения по `gRPC` (по умолчанию: `4Mib`)
    9.  Включена ли политика повторов для `gRPC`-соединения (по умолчанию: `true`)
    10. Количество попыток (по умолчанию: `5`)
    11. Начальная задержка между попытками (по умолчанию: `100ms`)
    12. Максимальная задержка между попытками (по умолчанию: `5s`)
    13. Коэффициент увеличения задержки между попытками (по умолчанию: `3.0`)
    14. `URL` для подключения к `REST`-адресу `Zeebe`; если указан, клиент предпочитает `REST` вместо `gRPC` для поддерживаемых операций (`обязательная` внутри необязательной секции `rest`, по умолчанию не указано)
    15. Пути для поиска ресурсов, которые будут загружены в оркестратор после запуска (по умолчанию: `[]`)
    16. Максимальное время ожидания загрузки ресурсов (по умолчанию: `45s`)
    17. Включает логирование модуля (по умолчанию: `false`)
    18. Включает метрики модуля (по умолчанию: `true`)
    19. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    20. Настройка тегов для метрик (по умолчанию: `{}`)
    21. Включает трассировку модуля (по умолчанию: `true`)
    22. Настройка атрибутов для трассировки (по умолчанию: `{}`)

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#camunda-8-worker).

Если в `deployment.resources` указаны пути, модуль во время запуска найдет ресурсы в `classpath:` и загрузит их в
`Zeebe`. Поддерживаются только пути с префиксом `classpath:`, например `classpath:bpm`; другие расположения будут
пропущены.

### Клиент { #client }

Модуль создает компонент `ZeebeClient`, который можно внедрять в собственные сервисы, если нужно вручную запускать
процессы, публиковать сообщения или выполнять другие команды `Zeebe`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ProcessStarter {

        private final ZeebeClient client;

        public ProcessStarter(ZeebeClient client) {
            this.client = client;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ProcessStarter(private val client: ZeebeClient)
    ```

Клиент можно дополнительно настроить компонентами графа: зарегистрировать `CredentialsProvider` для авторизации,
`JsonMapper` для `ZeebeClient`, `ScheduledExecutorService` для исполнителей заданий или `ClientInterceptor` для
`gRPC`-канала.

## Исполнители { #worker }

Исполнитель — это обработчик, способный выполнять определенное задание в процессе.
Когда в процессе появляется задание нужного типа, `Zeebe` активирует его и передает одному из исполнителей.

### Конфигурация { #configuration-2 }

Существует конфигурация по умолчанию, которая применяется ко всем исполнителям при создании, а затем поверх нее
применяются именованные настройки конкретного исполнителя по [типу исполнителя (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/).
Чтобы изменить настройки сразу для всех исполнителей, переопределите секцию `default`.
Чтобы изменить настройки только одного исполнителя, добавьте секцию с именем его типа, указанного в `@JobWorker`.
Если секция `zeebe.worker.job` не указана, используется встроенная конфигурация по умолчанию.

Пример полной конфигурации исполнителя, описанной в классе `ZeebeWorkerConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `HOCON`"

    ```javascript
    zeebe {
        worker {
            job {
                default { //(1)!
                    enabled = true //(2)!
                    timeout = "15m" //(3)!
                    maxJobsActive = 32 //(4)!
                    requestTimeout = "15s" //(5)!
                    pollInterval = "100ms" //(6)!
                    tenantIds = [] //(7)!
                    streamEnabled = false //(8)!
                    streamTimeout = "15s" //(9)!
                    backoff {
                        minDelay = "100ms" //(11)!
                        maxDelay = "500ms" //(12)!
                        factor = 1.0 //(10)!
                        jitter = 1.1 //(13)!
                    }
                }
            }
        }
    }
    ```

    1.  [Тип исполнителя (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) или имя настроек по умолчанию `default`
    2.  Включить ли исполнителя (по умолчанию: `true`)
    3.  Максимальное время выполнения одного задания исполнителем (по умолчанию: `15m`)
    4.  Максимальное количество заданий, которые будут одновременно активированы для этого исполнителя; используется для согласования скорости получения заданий со скоростью их обработки (`backpressure`) (по умолчанию: `32`)
    5.  Ограничение времени запроса, который используется для опроса нового задания исполнителем (по умолчанию: `15s`)
    6.  Максимальный интервал между опросами новых заданий; если после завершения работы новые задания не активированы, исполнитель будет периодически опрашивать брокер (по умолчанию: `100ms`)
    7.  Идентификаторы `tenant`, для которых исполнитель может получать задания (по умолчанию: `[]`)
    8.  Использовать ли потоковую передачу вместе с опросом для активации заданий (по умолчанию: `false`)
    9.  Максимальное время жизни потока, если потоковая передача включена (по умолчанию: `15s`)
    10. Минимальная задержка повтора; из-за `jitter` фактическая задержка может оказаться ниже этого минимума (по умолчанию: `100ms`)
    11. Максимальная задержка повтора; из-за `jitter` фактическая задержка может превысить это значение (по умолчанию: `500ms`)
    12. Коэффициент умножения задержки: предыдущая задержка умножается на это значение (по умолчанию: `1.0`)
    13. Коэффициент `jitter`: следующая задержка случайно изменяется в диапазоне `+/-` этого коэффициента (по умолчанию: `1.1`)

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      worker:
        job:
          default: #(1)!
            enabled: true #(2)!
            timeout: "15m" #(3)!
            maxJobsActive: 32 #(4)!
            requestTimeout: "15s" #(5)!
            pollInterval: "100ms" #(6)!
            tenantIds: [] #(7)!
            streamEnabled: false #(8)!
            streamTimeout: "15s" #(9)!
            backoff:
              minDelay: "100ms" #(11)!
              maxDelay: "500ms" #(12)!
              factor: 1.0 #(10)!
              jitter: 1.1 #(13)!
    ```

    1.  [Тип исполнителя (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) или имя настроек по умолчанию `default`
    2.  Включить ли исполнителя (по умолчанию: `true`)
    3.  Максимальное время выполнения одного задания исполнителем (по умолчанию: `15m`)
    4.  Максимальное количество заданий, которые будут одновременно активированы для этого исполнителя; используется для согласования скорости получения заданий со скоростью их обработки (`backpressure`) (по умолчанию: `32`)
    5.  Ограничение времени запроса, который используется для опроса нового задания исполнителем (по умолчанию: `15s`)
    6.  Максимальный интервал между опросами новых заданий; если после завершения работы новые задания не активированы, исполнитель будет периодически опрашивать брокер (по умолчанию: `100ms`)
    7.  Идентификаторы `tenant`, для которых исполнитель может получать задания (по умолчанию: `[]`)
    8.  Использовать ли потоковую передачу вместе с опросом для активации заданий (по умолчанию: `false`)
    9.  Максимальное время жизни потока, если потоковая передача включена (по умолчанию: `15s`)
    10. Минимальная задержка повтора; из-за `jitter` фактическая задержка может оказаться ниже этого минимума (по умолчанию: `100ms`)
    11. Максимальная задержка повтора; из-за `jitter` фактическая задержка может превысить это значение (по умолчанию: `500ms`)
    12. Коэффициент умножения задержки: предыдущая задержка умножается на это значение (по умолчанию: `1.0`)
    13. Коэффициент `jitter`: следующая задержка случайно изменяется в диапазоне `+/-` этого коэффициента (по умолчанию: `1.1`)

### Декларативные { #declarative }

Можно декларативно создавать [исполнителей](https://docs.camunda.io/docs/components/concepts/job-workers/), которые будут
выполнять работу в рамках оркестратора `Zeebe`.

В аннотации `@JobWorker` указывается [тип исполнителя (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/)
из процесса. По этому значению `Zeebe` связывает задание из `BPMN`-процесса с обработчиком в приложении.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public void process() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process() {
            // do something
        }
    }
    ```

#### Параметр контекст { #parameter-context }

Можно внедрять контекст исполнения как аргумент метода.
`JobContext` содержит метаданные текущего задания, исполнителя и процесса.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public void process(JobContext context) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(context: JobContext) {
            // do something
        }
    }
    ```

#### Параметр переменная { #parameter-variable }

Можно внедрять [переменные процесса](https://docs.camunda.io/docs/components/concepts/variables/) как аргументы метода.
Переменная процесса является частью состояния процесса и может быть установлена при старте процесса или как часть результата исполнителя.

Если указана хотя бы одна переменная через `@JobVariable`, сгенерированный исполнитель будет запрашивать у `Zeebe`
только такие переменные. Если `@JobVariable` не используется, исполнитель запрашивает все переменные задания.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public void process(@JobVariable("startId") String id) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(@JobVariable("startId") id: String) {
            // do something
        }
    }
    ```

Можно указать имя переменной явно в `@JobVariable`, либо будет использовано имя аргумента метода по умолчанию.

Так как переменные процесса передаются как `JSON`, аргумент метода может быть пользовательским типом, для которого
доступны `JsonReader` и `JsonWriter`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @Json
        public record User(String name, int code) { }

        @JobWorker("someJobType")
        public void process(@JobVariable User user) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        data class User(val name: String, val code: Int)

        @JobWorker("someJobType")
        fun process(@JobVariable user: User) {
            // do something
        }
    }
    ```

#### Параметр переменные { #parameter-variables }

Можно внедрить сразу несколько [переменных процесса](https://docs.camunda.io/docs/components/concepts/variables/) одним
аргументом метода через `@JobVariables`. Такой аргумент представляет все переменные задания как один `JSON`-объект.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @Json
        public record User(String name, int code) { }

        @Json
        public record UserContext(String startId, User user) { }

        @JobWorker("someJobType")
        public void process(@JobVariables UserContext userContext) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        data class User(val name: String, val code: Int)

        data class UserContext(val startId: String, val user: User)

        @JobWorker("someJobType")
        fun process(@JobVariables userContext: UserContext) {
            // do something
        }
    }
    ```

#### Результат { #result }

Можно не только выполнять работу, но и возвращать результат как переменные в контекст процесса.

Результат можно возвращать как `Map<String, Object>`, который описывает структуру `JSON`-ответа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public Map<String, Object> process() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(): Map<String, Any> {
            // do something
        }
    }
    ```

Также можно возвращать именованный результат как одну переменную. Это аналог одного ключа и значения в объекте
`Map<String, Object>`.

В таком случае обязательно требуется указать имя переменной в аннотации `@JobVariable`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @Json
        public record User(String name, int code) { }

        @JobVariable("user")
        @JobWorker("someJobType")
        public User process() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        data class User(val name: String, val code: Int)

        @JobVariable("user")
        @JobWorker("someJobType")
        fun process(): User {
            // do something
        }
    }
    ```

#### Ошибки { #errors }

Если требуется завершить исполнение ошибкой процесса, можно бросить `JobWorkerException`.
В исключении можно указать код ошибки, сообщение и переменные процесса, если они нужны.
Такое исключение будет преобразовано в команду `throwError` для `Zeebe`.

Если обработчик выбросит другое исключение, модуль преобразует его в `JobWorkerException` с кодом `INTERNAL`.
Ошибки чтения переменных получают код `DESERIALIZATION`, ошибки записи результата — `SERIALIZATION`, а неожиданные
ошибки в синхронном обработчике — `UNEXPECTED`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public User process() {
            throw new JobWorkerException("DOESNT_WORK");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(): User {
            throw JobWorkerException("DOESNT_WORK")
        }
    }
    ```

### Императивные { #imperative }

Можно также создавать более низкоуровневые исполнители и напрямую работать с контрактами `ZeebeClient`.
Для этого компонент должен реализовать интерфейс `KoraJobWorker`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob implements KoraJobWorker {

        @Override
        public String type() {
            return "someJobType";
        }

        @Override
        public CompletionStage<FinalCommandStep<?>> handle(JobClient client, ActivatedJob job) {
            return CompletableFuture.completedFuture(client.newCompleteCommand(job));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob : KoraJobWorker {

        override fun type(): String = "someJobType"

        override fun handle(client: JobClient, job: ActivatedJob): CompletionStage<FinalCommandStep<*>> {
            return CompletableFuture.completedFuture(client.newCompleteCommand(job))
        }
    }
    ```

## Сигнатуры { #signatures }

Доступные сигнатуры для методов исполнителя из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.
    Если результат равен `null` или `Optional.empty()`, задание будет завершено без добавления переменных.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.
    Если результат равен `null`, задание будет завершено без добавления переменных.

    - `myMethod(): T`
    - `myMethod(): Deferred<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
