??? warning "Экспериментальный модуль"

    **Эксперементальный** модуль является полностью рабочим и протестированным, но требует дополнительной апробации и аналитики по использованию, 
    по этой причине API может потенциально притерпеть незначительные изменения перед полной готовностью.

Модуль для подключения клиента и создания исполнителей для внешнего оркестратора процессов [Camunda 8 (Zeebe)](https://docs.camunda.io/docs/components/concepts/job-workers/)

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:camunda-zeebe-worker"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ZeebeWorkerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:camunda-zeebe-worker")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ZeebeWorkerModule
    ```

## Конфигурация

Пример полной конфигурации клиента описанной в классе `ZeebeClientConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

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
                    stepFactor = 3.0 //(13)!
                }
            }
            http {
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
                }
                tracing {
                    enabled = true //(20)!
                }
            }
        }
    }
    ```

    1.  Максимальное количество потоков для исполнителей задач, по умолчанию равен кол-во ядер процессора либо минимум `2`
    2.  Время соединения без активности чтения перед отправкой `KeepAlive` проверки
    3.  Использовать ли TLS при подключении при соединении
    4.  [Файловый путь](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/FileInputStream.html) до файла сертификата который использовать при подключении, либо используется по умолчанию системный сертификат
    5.  Максимальное время ожидания инициализации запуска исполнителей при старте сервиса (по умолчанию отсутвует)
    6.  URL для подключения по gRPC
    7.  Время сколько сообщение должно буферизироваться на брокере по gRPC соединению
    8.  Максимальный размер сообщения по gRPC соединению
    9.  Включена ли политика повтора исполнения в случае ошибки соединения
    10. Количество попыток
    11. Задержка между попытками
    12. Максимальная длительность повторов
    13. Шаг коэфициент увеличения времени задержки между попытками
    14. URL для подключения по HTTP
    15. Пути для поиска ресурсов которые будут загружены в оркесратор после запуска
    16. Максимальное время ожидания загрузки ресурсов
    17. Включает логгирование модуля (по умолчанию `false`)
    18. Включает метрики модуля (по умолчанию `true`)
    19. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    20. Включает трассировку модуля (по умолчанию `true`)

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
            stepFactor: 3.0 #(13)!
        http:
          url: "http:#localhost:8080" //(14)!
        deployment:
          resources: "classpath:bpm" #(15)!
          timeout: "45s" #(16)!
        telemetry:
          logging:
            enabled: false #(17)!
          metrics:
            enabled: true #(18)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(19)!
          tracing:
            enabled: true #(20)!
    ```

    1.  Максимальное количество потоков для исполнителей задач
    2.  Время соединения без активности чтения перед отправкой `KeepAlive` проверки
    3.  Использовать ли TLS при подключении при соединении
    4.  [Файловый путь](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/FileInputStream.html) до файла сертификата который использовать при подключении, либо используется по умолчанию системный сертификат
    5.  Максимальное время ожидания инициализации запуска исполнителей при старте сервиса (по умолчанию отсутвует)
    6.  URL для подключения по gRPC
    7.  Время сколько сообщение должно буферизироваться на брокере по gRPC соединению
    8.  Максимальный размер сообщения по gRPC соединению
    9.  Включена ли политика повтора исполнения в случае ошибки соединения
    10. Количество попыток
    11. Задержка между попытками
    12. Максимальная длительность повторов
    13. Шаг коэфициент увеличения времени задержки между попытками
    14. URL для подключения по HTTP
    15. Пути для поиска ресурсов которые будут загружены в оркесратор после запуска
    16. Максимальное время ожидания загрузки ресурсов
    17. Включает логгирование модуля (по умолчанию `false`)
    18. Включает метрики модуля (по умолчанию `true`)
    19. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    20. Включает трассировку модуля (по умолчанию `true`)

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#camunda-8-worker).

## Исполнители

Исполнитель - это обработчик, способный выполнять определенное задание в процессе. 
Каждый раз, когда необходимо выполнить такое задание, оно представляется в виде задачи исполнителю.

### Конфигурация

Существует конфигурация по умолчанию, которая применяется ко всем исполнителям при создании
и затем применяются именованные настройки конкретного исполнителя ([по типу исполнителя `Type`](https://docs.camunda.io/docs/components/concepts/job-workers/)) 
для переопределения настроек по умолчанию.
Можно изменить настройки по умолчанию для всех прерывателей одновременно изменив конфигурацию по умолчанию (`default`).

Пример полной конфигурации исполнителя описан в классе `ZeebeWorkerConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

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
                        jitter = 1.3 //(13)!
                    }
                }
            }
        }
    }
    ```

    1.  [Тип обработчика (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) или имя настроек по умолчанию (`default`)
    2.  Включить ли исполнителя
    3.  Максимальное время выполнения одной задачи исполнителем
    4.  Максимальное количество задач, которые будут одновременно активированы только для этого исполнителя. Это используется для управления скорость работы производителя данных для согласования со скоростью работы исполнителя (`backpressure`)
    5.  Ограничение времени запроса используемого для опроса нового задания исполнителем
    6.  Максимальный интервал между опросами новых задач. Рабочий автоматически пытается всегда активировать новые задания после завершения работы. Если ни одно задание не может быть активировано после завершения, исполнитель будет периодически опрашивать новые задания
    7.  Указывает индетификаторы тенантов, которые могут владеть любыми сущностями (например, определением процесса, экземплярами процесса и т. д.), полученными в результате выполнения этой команды
    8.  Если установлено значение «включено», рабочий будет использовать сочетание потоковой передачи и опроса для активации заданий
    9.  Если потоковая передача включена, устанавливает максимальное время жизни для данного потока
    10.  Устанавливает минимальную задержку повтора. Обратите внимание, что из-за `jitter` задержка повтора может оказаться ниже этого минимума
    11.  Устанавливает максимальную задержку повтора. Обратите внимание, что `jitter` может превысить эту максимальную задержку
    12.  Устанавливает коэффициент умножения задержки. Предыдущая задержка умножается на этот коэффициент
    13.  Устанавливает коэффициент джиттера. Следующая задержка изменяется случайным образом в диапазоне +/- этого коэффициента. 
        Например, если следующая задержка рассчитывается как 1 с, а `jitter` равен 0,1, то фактическая следующая задержка может быть где-то между 0,9 и 1,1 с

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
              jitter: 1.3 #(13)!
    ```

    1.  [Тип обработчика (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) или имя настроек по умолчанию (`default`)
    2.  Включить ли исполнителя
    3.  Максимальное время выполнения одной задачи исполнителем
    4.  Максимальное количество задач, которые будут одновременно активированы только для этого исполнителя. Это используется для управления скорость работы производителя данных для согласования со скоростью работы исполнителя (`backpressure`)
    5.  Ограничение времени запроса используемого для опроса нового задания исполнителем
    6.  Максимальный интервал между опросами новых задач. Рабочий автоматически пытается всегда активировать новые задания после завершения работы. Если ни одно задание не может быть активировано после завершения, исполнитель будет периодически опрашивать новые задания
    7.  Указывает индетификаторы тенантов, которые могут владеть любыми сущностями (например, определением процесса, экземплярами процесса и т. д.), полученными в результате выполнения этой команды
    8.  Если установлено значение «включено», рабочий будет использовать сочетание потоковой передачи и опроса для активации заданий
    9.  Если потоковая передача включена, устанавливает максимальное время жизни для данного потока
    10.  Устанавливает минимальную задержку повтора. Обратите внимание, что из-за `jitter` задержка повтора может оказаться ниже этого минимума
    11.  Устанавливает максимальную задержку повтора. Обратите внимание, что `jitter` может превысить эту максимальную задержку
    12.  Устанавливает коэффициент умножения задержки. Предыдущая задержка умножается на этот коэффициент
    13.  Устанавливает коэффициент джиттера. Следующая задержка изменяется случайным образом в диапазоне +/- этого коэффициента. 
        Например, если следующая задержка рассчитывается как 1 с, а `jitter` равен 0,1, то фактическая следующая задержка может быть где-то между 0,9 и 1,1 с

### Декларативные

Можно создавать декларативно [исполнителей](https://docs.camunda.io/docs/components/concepts/job-workers/) которые будут выполнять работу в рамках Zeebe оркестратора.

В аннотации `JobWorker` указывается значение [типа исполнителя (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) в рамках процесса.

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

#### Параметр контекст

Можно внедрять контекст исполнения как аргумент метода,
контекст исполнения имеет метаданные задачи, исполнителя и процесса доступные для текущей задачи, которая на исполнении.

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

#### Параметр переменная

Можно внедрять [переменные процесса](https://docs.camunda.io/docs/components/concepts/variables/) как аргументы метода,
переменная процесса является частью состояния процесса и может быть установлена на старте или как часть результата исполнителя.

Важно, если указана хоть одна именованная переменная, то только эти переменные будут переданы на получение из оркестратора.

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

Можно указать имя переменной из контекста, либо будет использовано имя аргумента метода по умолчанию.

Так как все переменные процесса обязаны быть JSON объектами, 
то аргумент метода может представлять собой также любое отображение JSON объекта.

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

#### Параметр переменные

Можно внедрить сразу несколько [переменных процесса](https://docs.camunda.io/docs/components/concepts/variables/) как аргумент метода,
как один объект, который представляет собой JSON объекты в состоянии процесса.

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

#### Результат

Можно не просто выполнять работу, но и возвращать результат выполнения работы как переменную в контекст процесса.

Результат можно возвращать как `Map<String, Object>` описывающую структуру JSON ответа.

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

Так и возвращать сразу именованный результат как одну переменную, 
что будет аналогом одного ключа и значения в `Map<String, Object>` объекте.

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

#### Ошибки

В случае если требуется завершить исполнение ошибкой, можно бросить исключение `JobWorkerException` где можно указать,
как код ошибки, так и сообщение и переменные процесса если того требуется.

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

### Императивные

Можно также создавать более низкоуровневые исполнители и напрямую работать с контрактами `ZeebeClient` и его интерфейсом.

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
            return client.newCompleteCommand(job);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob : KoraJobWorker {

        fun type(): String = "someJobType"

        fun handle(client: JobClient, job: ActivatedJob): CompletionStage<FinalCommandStep<*>> {
            return client.newCompleteCommand(job)
        }
    }
    ```

## Сигнатуры

Доступные сигнатуры для методов репозитория из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `myMethod(): Deferred<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
