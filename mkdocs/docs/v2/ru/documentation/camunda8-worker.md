---
description: "Explains Kora Camunda 8 Zeebe worker integration, CamundaClient configuration, job handling, variables, telemetry, and supported handler signatures. Use when working with @JobWorker, @JobVariable, @JobVariables, CamundaClient, JobContext, KoraJobWorker, JobWorkerException, ZeebeWorkerModule, ZeebeClientConfig, ZeebeWorkerConfig."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Camunda 8 Zeebe worker integration, CamundaClient configuration, job handling, variables, telemetry, and supported handler signatures; key triggers include @JobWorker, @JobVariable, @JobVariables, CamundaClient, JobContext, KoraJobWorker, JobWorkerException, ZeebeWorkerModule, ZeebeClientConfig, ZeebeWorkerConfig."
---

??? warning "Экспериментальный модуль"

    **Экспериментальный** модуль является полностью рабочим и протестированным, но требует дополнительной апробации и аналитики по использованию,
    по этой причине его `API` может потенциально претерпеть незначительные изменения перед полной готовностью.

Модуль подключает клиент [Camunda 8 (Zeebe)](https://docs.camunda.io/docs/components/concepts/job-workers/) и создает
исполнителей заданий для внешнего оркестратора процессов. В `Kora` такой исполнитель объявляется обычным компонентом:
метод с аннотацией `@JobWorker` получает переменные процесса, выполняет работу и возвращает результат, который будет
передан обратно в `Zeebe`.

Модуль построен на клиенте `io.camunda:camunda-client-java`, поэтому тип клиента — `io.camunda.client.CamundaClient`,
а ответы его команд лежат в пакете `io.camunda.client.api.response`.

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework.experimental:camunda-zeebe-worker"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ZeebeWorkerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework.experimental:camunda-zeebe-worker")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ZeebeWorkerModule
    ```

## Конфигурация { #configuration }

Пример полной конфигурации клиента, описанной в классе `ZeebeClientConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    zeebe {
        client {
            executionThreads = 4 //(1)!
            keepAlive = "45s" //(2)!
            certificatePath = "/file/path/to/cert.crt" //(3)!
            initializationFailTimeout = "15s" //(4)!
            grpc {
                url = "http://localhost:26500" //(5)!
                ttl = "1h" //(6)!
                maxMessageSize = "4MiB" //(7)!
                retryPolicy {
                    enabled = true //(8)!
                    attempts = 5 //(9)!
                    delay = "100ms" //(10)!
                    delayMax = "5s" //(11)!
                    step = 3.0 //(12)!
                }
            }
            rest {
                url = "http://localhost:8080" //(13)!
            }
            deployment {
                resources = "classpath:bpm" //(14)!
                timeout = "45s" //(15)!
            }
            telemetry {
                logging {
                    enabled = false //(16)!
                }
                metrics {
                    enabled = false //(17)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(18)!
                    tags = { //(19)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(20)!
                    attributes = { //(21)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1. Максимальное количество потоков для исполнителей заданий (по умолчанию: удвоенное количество доступных процессоров, но не менее `2`)
    2. Время без активности чтения, после которого отправляется проверка `KeepAlive` (по умолчанию: `45s`)
    3. [Путь к файлу](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/io/FileInputStream.html) сертификата для соединения, если не указан — используется системный сертификат (опционально)
    4. Максимальное время ожидания проверки доступности топологии при старте клиента, если не указано — проверка не выполняется (опционально)
    5. `URL` шлюза `gRPC` у `Zeebe` (обязательный, без значения по умолчанию)
    6. Сколько времени сообщение хранится на брокере при отправке через `gRPC` (по умолчанию: `1h`)
    7. Максимальный размер входящего сообщения для `gRPC` (по умолчанию: `4MiB`)
    8. Включена ли политика повторных попыток для соединения `gRPC` (по умолчанию: `true`)
    9. Количество попыток (по умолчанию: `5`)
    10. Начальная задержка между попытками (по умолчанию: `100ms`)
    11. Максимальная задержка между попытками (по умолчанию: `5s`)
    12. Множитель задержки между попытками (по умолчанию: `3.0`)
    13. `URL` шлюза `REST` у `Zeebe` (обязательный, без значения по умолчанию)
    14. Пути поиска ресурсов, которые будут загружены в оркестратор после старта (по умолчанию: `[]`)
    15. Максимальное время ожидания загрузки ресурсов (по умолчанию: `45s`)
    16. Включает логгирование модуля (по умолчанию: `false`)
    17. Включает метрики модуля (по умолчанию: `false`)
    18. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    19. Настройка тегов для метрик (по умолчанию: `{}`)
    20. Включает трассировку модуля (по умолчанию: `true`)
    21. Настройка атрибутов для трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      client:
        executionThreads: 4 #(1)!
        keepAlive: "45s" #(2)!
        certificatePath: "/file/path/to/cert.crt" #(3)!
        initializationFailTimeout: "15s" #(4)!
        grpc:
          url: "http://localhost:26500" #(5)!
          ttl: "1h" #(6)!
          maxMessageSize: "4MiB" #(7)!
          retryPolicy:
            enabled: true #(8)!
            attempts: 5 #(9)!
            delay: "100ms" #(10)!
            delayMax: "5s" #(11)!
            step: 3.0 #(12)!
        rest:
          url: "http://localhost:8080" #(13)!
        deployment:
          resources: "classpath:bpm" #(14)!
          timeout: "45s" #(15)!
        telemetry:
          logging:
            enabled: false #(16)!
          metrics:
            enabled: false #(17)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(18)!
            tags: #(19)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(20)!
            attributes: #(21)!
              key1: value1
              key2: value2
    ```

    1. Максимальное количество потоков для исполнителей заданий (по умолчанию: удвоенное количество доступных процессоров, но не менее `2`)
    2. Время без активности чтения, после которого отправляется проверка `KeepAlive` (по умолчанию: `45s`)
    3. [Путь к файлу](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/io/FileInputStream.html) сертификата для соединения, если не указан — используется системный сертификат (опционально)
    4. Максимальное время ожидания проверки доступности топологии при старте клиента, если не указано — проверка не выполняется (опционально)
    5. `URL` шлюза `gRPC` у `Zeebe` (обязательный, без значения по умолчанию)
    6. Сколько времени сообщение хранится на брокере при отправке через `gRPC` (по умолчанию: `1h`)
    7. Максимальный размер входящего сообщения для `gRPC` (по умолчанию: `4MiB`)
    8. Включена ли политика повторных попыток для соединения `gRPC` (по умолчанию: `true`)
    9. Количество попыток (по умолчанию: `5`)
    10. Начальная задержка между попытками (по умолчанию: `100ms`)
    11. Максимальная задержка между попытками (по умолчанию: `5s`)
    12. Множитель задержки между попытками (по умолчанию: `3.0`)
    13. `URL` шлюза `REST` у `Zeebe` (обязательный, без значения по умолчанию)
    14. Пути поиска ресурсов, которые будут загружены в оркестратор после старта (по умолчанию: `[]`)
    15. Максимальное время ожидания загрузки ресурсов (по умолчанию: `45s`)
    16. Включает логгирование модуля (по умолчанию: `false`)
    17. Включает метрики модуля (по умолчанию: `false`)
    18. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    19. Настройка тегов для метрик (по умолчанию: `{}`)
    20. Включает трассировку модуля (по умолчанию: `true`)
    21. Настройка атрибутов для трассировки (по умолчанию: `{}`)

!!! warning "Оба адреса обязательны"

    Клиент всегда открывает канал `gRPC` и всегда читает адрес `REST`, поэтому `zeebe.client.grpc.url`
    и `zeebe.client.rest.url` должны быть указаны оба. Конфигурация, в которой присутствует только один
    из двух адресов, приводит к падению приложения на старте.

Схема соединения берется из `grpc.url`: `http` открывает канал без шифрования, `https` — канал с `TLS`.
Для самоподписанного сертификата укажите путь к нему в `certificatePath`, иначе используется системное хранилище доверия.
Порты `Zeebe` по умолчанию — `26500` для `gRPC` и `8080` для `REST`.

У канала `gRPC` есть собственная секция телеметрии `zeebe.client.grpc.telemetry` с теми же настройками, что и у любого
[gRPC клиента](grpc-client.md#configuration): она описывает транспортные вызовы к оркестратору, тогда как
`zeebe.client.telemetry` описывает работу самих исполнителей заданий.
Логи исполнителей пишутся в логгер `io.koraframework.camunda.zeebe.worker.<jobType>`, поэтому уровень логгирования можно
поднять для отдельного исполнителя; на уровне `DEBUG` в запись также попадают переменные задания.

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#camunda-8-worker).

### Развертывание ресурсов { #resource-deployment }

Если в `deployment.resources` указаны пути, модуль во время запуска находит ресурсы в `classpath` и развертывает их в
`Zeebe` через компонент `ZeebeResourceDeployment`. Развертываются как `BPMN`-процессы, так и `DMN`-решения, найденные в
настроенных расположениях. Поддерживаются только пути с префиксом `classpath:`, например `classpath:bpm`; другие
расположения логируются и пропускаются.

Разместите развертываемые ресурсы в соответствующей директории classpath:

```text
src/main/resources/
└── bpm/
    └── demo.bpmn
```

===! ":material-code-json: `Hocon`"

    ```javascript
    zeebe {
        client {
            deployment {
                resources = "classpath:bpm" //(1)!
            }
        }
    }
    ```

    1. Одно или несколько расположений в classpath для поиска `BPMN` / `DMN`-ресурсов (одно значение или список)

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      client:
        deployment:
          resources: "classpath:bpm" #(1)!
    ```

    1. Одно или несколько расположений в classpath для поиска `BPMN` / `DMN`-ресурсов (одно значение или список)

### Клиент { #client }

Модуль создает компонент `CamundaClient`, который можно внедрять в собственные сервисы, если нужно вручную запускать
процессы, публиковать сообщения или выполнять другие команды `Zeebe`.

Например, чтобы запустить новый экземпляр процесса:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ProcessStarter {

        private final CamundaClient client;

        public ProcessStarter(CamundaClient client) {
            this.client = client;
        }

        public void start() {
            ProcessInstanceEvent event = client.newCreateInstanceCommand()
                    .bpmnProcessId("demo") //(1)!
                    .latestVersion() //(2)!
                    .variables("{\"startId\":\"42\"}") //(3)!
                    .send()
                    .join(); //(4)!
        }
    }
    ```

    1. Идентификатор `BPMN`-процесса, который требуется запустить
    2. Запустить последнюю развернутую версию процесса
    3. Начальные переменные процесса в виде `JSON`-строки (также принимаются `Map` или объект с `@Json`)
    4. Отправить команду и дождаться подтверждения от `Zeebe` (`send()` возвращает `CamundaFuture`, который также является `CompletionStage`)

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ProcessStarter(private val client: CamundaClient) {

        fun start() {
            val event = client.newCreateInstanceCommand()
                .bpmnProcessId("demo") //(1)!
                .latestVersion() //(2)!
                .variables("""{"startId":"42"}""") //(3)!
                .send()
                .join() //(4)!
        }
    }
    ```

    1. Идентификатор `BPMN`-процесса, который требуется запустить
    2. Запустить последнюю развернутую версию процесса
    3. Начальные переменные процесса в виде `JSON`-строки (также принимаются `Map` или объект с `@Json`)
    4. Отправить команду и дождаться подтверждения от `Zeebe` (`send()` возвращает `CamundaFuture`, который также является `CompletionStage`)

Тот же клиент публикует сообщения (`client.newPublishMessageCommand()`), развертывает ресурсы
(`client.newDeployResourceCommand()`) и выполняет любые другие команды `Zeebe`.

#### Настройка клиента { #client-customization }

Поведение `CamundaClient` можно уточнить опциональными компонентами графа, которые модуль подхватывает автоматически:

* `CredentialsProvider` — авторизация в `Zeebe` (`Camunda 8 SaaS` либо self-managed с `OAuth`);
* `JsonMapper` — собственный маппер `JSON` (`io.camunda.client.api.JsonMapper`), который `CamundaClient` использует для (де)сериализации переменных;
* `ScheduledExecutorService` — исполнитель, который используют исполнители заданий;
* `ClientInterceptor` — каждый перехватчик `gRPC`, объявленный **без** `@Tag`, попадает на канал `Zeebe` вдобавок
  к собственному перехватчику телеметрии модуля. Поэтому перехватчики, относящиеся к другому клиенту, следует
  [помечать тегом своей службы](grpc-client.md#shared-interceptors), чтобы они не оказались на канале `Zeebe`.

Например, чтобы авторизоваться в `Camunda 8` через `OAuth`, предоставьте компонент `CredentialsProvider`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ZeebeAuthModule {

        default CredentialsProvider zeebeCredentialsProvider() {
            return CredentialsProvider.newCredentialsProviderBuilder()
                    .clientId("client-id")
                    .clientSecret("client-secret")
                    .audience("zeebe.camunda.io")
                    .authorizationServerUrl("https://login.cloud.camunda.io/oauth/token")
                    .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ZeebeAuthModule {

        fun zeebeCredentialsProvider(): CredentialsProvider =
            CredentialsProvider.newCredentialsProviderBuilder()
                .clientId("client-id")
                .clientSecret("client-secret")
                .audience("zeebe.camunda.io")
                .authorizationServerUrl("https://login.cloud.camunda.io/oauth/token")
                .build()
    }
    ```

## Исполнители { #worker }

Исполнитель — это обработчик, который может выполнять определенное задание в процессе.
Когда процесс содержит задание требуемого типа, `Zeebe` активирует его и передает одному из исполнителей.

### Конфигурация { #configuration-2 }

Существует конфигурация по умолчанию, которая применяется ко всем исполнителям при создании, а поверх нее применяются
именованные настройки конкретного исполнителя по [типу исполнителя (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/).
Чтобы поменять настройки сразу всем исполнителям, переопределите секцию `default`.
Чтобы поменять настройки только одному исполнителю, добавьте секцию с именем типа, указанного в `@JobWorker`.
Если секция `zeebe.worker.job` не указана, используется встроенная конфигурация по умолчанию.

Пример полной конфигурации исполнителя, описанной в классе `ZeebeWorkerConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    zeebe {
        worker {
            job {
                default { //(1)!
                    enabled = true //(2)!
                    name = "default" //(3)!
                    timeout = "15m" //(4)!
                    maxJobsActive = 32 //(5)!
                    requestTimeout = "15s" //(6)!
                    pollInterval = "100ms" //(7)!
                    tenantIds = [] //(8)!
                    streamEnabled = false //(9)!
                    streamTimeout = "15s" //(10)!
                    backoff {
                        minDelay = "100ms" //(11)!
                        maxDelay = "500ms" //(12)!
                        factor = 1.0 //(13)!
                        jitter = 1.1 //(14)!
                    }
                }
            }
        }
    }
    ```

    1. [Тип исполнителя (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) либо имя настроек по умолчанию `default`
    2. Включен ли исполнитель (по умолчанию: `true`)
    3. Имя, под которым исполнитель регистрируется на брокере (по умолчанию: `default`)
    4. Максимальное время выполнения одного задания исполнителем (по умолчанию: `15m`)
    5. Максимальное количество заданий, которые будут активированы для этого исполнителя одновременно, используется для согласования скорости получения и обработки заданий (`backpressure`) (по умолчанию: `32`)
    6. Таймаут запроса, используемый при опросе нового задания исполнителем (по умолчанию: `15s`)
    7. Максимальный интервал между опросами новых заданий: если после завершения работы задания не активированы, исполнитель периодически опрашивает брокер (по умолчанию: `100ms`)
    8. Идентификаторы `tenant`, по которым исполнитель может получать задания (по умолчанию: `[]`)
    9. Использовать ли потоковую передачу вместе с опросом для активации заданий (по умолчанию: `false`)
    10. Максимальное время жизни потока, когда включена потоковая передача (по умолчанию: `15s`)
    11. Минимальная задержка повтора, из-за `jitter` фактическая задержка может оказаться меньше этого минимума (по умолчанию: `100ms`)
    12. Максимальная задержка повтора, из-за `jitter` фактическая задержка может превысить это значение (по умолчанию: `500ms`)
    13. Множитель задержки: предыдущая задержка умножается на это значение (по умолчанию: `1.0`)
    14. Коэффициент `jitter`: следующая задержка случайно изменяется в диапазоне `+/-` этого коэффициента (по умолчанию: `1.1`)

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      worker:
        job:
          default: #(1)!
            enabled: true #(2)!
            name: "default" #(3)!
            timeout: "15m" #(4)!
            maxJobsActive: 32 #(5)!
            requestTimeout: "15s" #(6)!
            pollInterval: "100ms" #(7)!
            tenantIds: [] #(8)!
            streamEnabled: false #(9)!
            streamTimeout: "15s" #(10)!
            backoff:
              minDelay: "100ms" #(11)!
              maxDelay: "500ms" #(12)!
              factor: 1.0 #(13)!
              jitter: 1.1 #(14)!
    ```

    1. [Тип исполнителя (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) либо имя настроек по умолчанию `default`
    2. Включен ли исполнитель (по умолчанию: `true`)
    3. Имя, под которым исполнитель регистрируется на брокере (по умолчанию: `default`)
    4. Максимальное время выполнения одного задания исполнителем (по умолчанию: `15m`)
    5. Максимальное количество заданий, которые будут активированы для этого исполнителя одновременно, используется для согласования скорости получения и обработки заданий (`backpressure`) (по умолчанию: `32`)
    6. Таймаут запроса, используемый при опросе нового задания исполнителем (по умолчанию: `15s`)
    7. Максимальный интервал между опросами новых заданий: если после завершения работы задания не активированы, исполнитель периодически опрашивает брокер (по умолчанию: `100ms`)
    8. Идентификаторы `tenant`, по которым исполнитель может получать задания (по умолчанию: `[]`)
    9. Использовать ли потоковую передачу вместе с опросом для активации заданий (по умолчанию: `false`)
    10. Максимальное время жизни потока, когда включена потоковая передача (по умолчанию: `15s`)
    11. Минимальная задержка повтора, из-за `jitter` фактическая задержка может оказаться меньше этого минимума (по умолчанию: `100ms`)
    12. Максимальная задержка повтора, из-за `jitter` фактическая задержка может превысить это значение (по умолчанию: `500ms`)
    13. Множитель задержки: предыдущая задержка умножается на это значение (по умолчанию: `1.0`)
    14. Коэффициент `jitter`: следующая задержка случайно изменяется в диапазоне `+/-` этого коэффициента (по умолчанию: `1.1`)

Чтобы переопределить настройки одного исполнителя, добавьте секцию с ключом по [типу исполнителя (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/),
указанному в `@JobWorker`. Именованная секция накладывается поверх `default`, которая, в свою очередь, накладывается
поверх встроенных значений, поэтому в именованной секции достаточно перечислить только изменяемые ключи. Значение
`enabled = false` у именованного типа отключает только этот исполнитель.

===! ":material-code-json: `Hocon`"

    ```javascript
    zeebe {
        worker {
            job {
                foo { //(1)!
                    timeout = "30s"
                    maxJobsActive = 8
                }
                bar { //(2)!
                    enabled = false
                }
            }
        }
    }
    ```

    1. Переопределяет только `timeout` и `maxJobsActive` для исполнителя `@JobWorker("foo")`, остальные настройки берутся из `default`
    2. Отключает исполнитель `@JobWorker("bar")`, не затрагивая остальную конфигурацию

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      worker:
        job:
          foo: #(1)!
            timeout: "30s"
            maxJobsActive: 8
          bar: #(2)!
            enabled: false
    ```

    1. Переопределяет только `timeout` и `maxJobsActive` для исполнителя `@JobWorker("foo")`, остальные настройки берутся из `default`
    2. Отключает исполнитель `@JobWorker("bar")`, не затрагивая остальную конфигурацию

### Декларативные { #declarative }

Можно декларативно создавать [исполнителей](https://docs.camunda.io/docs/components/concepts/job-workers/), которые
выполняют работу в рамках оркестратора `Zeebe`.

Аннотация `@JobWorker` указывает [тип исполнителя (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/)
из процесса. `Zeebe` использует это значение, чтобы связать задание из `BPMN`-процесса с обработчиком в приложении.

К методам-исполнителям предъявляются следующие требования:

- Класс-владелец должен быть компонентом [графа зависимостей](container.md), например с аннотацией `@Component`.
- Метод не должен быть `private` — компиляция завершится ошибкой `@JobWorker method can't be private`.
- Метод может объявлять только параметры `@JobVariable`, `@JobVariables` и `JobContext` — любой другой тип параметра
  отклоняется на этапе компиляции. Исходные `JobClient` и `ActivatedJob` доступны только в [императивном](#imperative) исполнителе.
- Имя переменной (как аргумента, так и результата) должно состоять из букв и цифр, может содержать `_`, не должно
  начинаться с цифры и не должно совпадать с ключевым словом `FEEL`, например `if`, `then`, `else`, `for` или `not`.

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

Для каждого аннотированного метода Kora создает отдельный компонент `KoraJobWorker` и регистрирует его на брокере при старте.
Если несколько исполнителей объявляют один и тот же тип, регистрируются все они, а в лог пишется предупреждение.

#### Параметр контекст { #parameter-context }

Можно внедрить контекст задания как аргумент метода.
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

`JobContext` предоставляет следующие методы только для чтения:

| Метод                        | Описание                                                                             |
|------------------------------|--------------------------------------------------------------------------------------|
| `jobKey()`                   | Уникальный ключ активированного задания                                              |
| `jobName()`                  | Имя, под которым исполнитель зарегистрирован на брокере (настройка `name`)           |
| `jobType()`                  | Тип активированного задания, заданный в `BPMN`-процессе                              |
| `jobWorker()`                | Имя исполнителя, активировавшего задание на стороне брокера                          |
| `tenantId()`                 | Идентификатор `tenant`, которому принадлежит задание                                 |
| `processId()`                | Идентификатор `BPMN`-процесса                                                        |
| `processInstanceKey()`       | Ключ экземпляра процесса, которому принадлежит задание                               |
| `processDefinitionVersion()` | Версия развернутого определения процесса                                             |
| `processDefinitionKey()`     | Ключ развернутого определения процесса                                               |
| `elementId()`                | Идентификатор элемента `BPMN`, для которого создано задание                           |
| `elementInstanceKey()`       | Ключ экземпляра элемента `BPMN`                                                      |
| `headers()`                  | Пользовательские заголовки задания, заданные в модели `BPMN`                          |
| `retryCount()`               | Количество оставшихся повторов задания                                               |
| `deadline()`                 | Момент времени (`Instant`), до которого задание закреплено за исполнителем            |
| `deadlineAsMillis()`         | Тот же срок в миллисекундах эпохи                                                    |
| `variablesAsString()`        | Исходные переменные задания в виде `JSON`-строки                                     |

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public void process(JobContext context) {
            logger.info("Job {} of process {} at element {} with deadline {}",
                    context.jobType(), context.processInstanceKey(), context.elementId(), context.deadline());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(context: JobContext) {
            logger.info("Job {} of process {} at element {} with deadline {}",
                context.jobType(), context.processInstanceKey(), context.elementId(), context.deadline())
        }
    }
    ```

Контекст обрабатываемого задания на всё время вызова также привязан к
[scoped value](https://openjdk.org/jeps/506) `JobContext.VALUE`, поэтому код, вызванный из исполнителя, может прочитать
метаданные задания через `JobContext.VALUE.get()`, не прокидывая аргумент по стеку вызовов.

#### Параметр переменная { #parameter-variable }

Можно внедрять [переменные процесса](https://docs.camunda.io/docs/components/concepts/variables/) как аргументы метода.
Переменная процесса является частью состояния процесса и может быть задана при старте процесса или как часть результата исполнителя.

Если хотя бы одна переменная указана через `@JobVariable`, созданный исполнитель запрашивает у `Zeebe` только эти переменные.
Если `@JobVariable` не используется, исполнитель запрашивает все переменные задания.

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

Имя переменной можно указать явно в `@JobVariable`, иначе по умолчанию будет использовано имя аргумента метода.

По умолчанию аргумент-переменная обязателен: если процесс её не предоставил, задание завершится ошибкой.
Чтобы допустить отсутствующее или `null` значение, пометьте аргумент как допускающий `null` (`@Nullable` в `Java`, `T?` в `Kotlin`).

Так как переменные процесса передаются как `JSON`, аргументом метода может быть пользовательский тип,
для которого доступны `JsonReader` и `JsonWriter`.

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

        @Json
        data class User(val name: String, val code: Int)

        @JobWorker("someJobType")
        fun process(@JobVariable user: User) {
            // do something
        }
    }
    ```

#### Параметр переменные { #parameter-variables }

Можно внедрить сразу несколько [переменных процесса](https://docs.camunda.io/docs/components/concepts/variables/) одним
аргументом метода через `@JobVariables`. Такой аргумент представляет все переменные задания как один объект `JSON`.
В одном методе-исполнителе допускается только один аргумент `@JobVariables`.

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

        @Json
        data class User(val name: String, val code: Int)

        @Json
        data class UserContext(val startId: String, val user: User)

        @JobWorker("someJobType")
        fun process(@JobVariables userContext: UserContext) {
            // do something
        }
    }
    ```

#### Результат { #result }

Можно не только выполнять работу, но и возвращать результат в виде переменных в контекст процесса.

Результат может возвращаться как `Map<String, Object>`, который описывает структуру `JSON`-ответа.

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

Можно также вернуть именованный результат одной переменной. Это эквивалентно одному ключу и значению в объекте
`Map<String, Object>`.

В этом случае имя переменной обязательно указывается в аннотации `@JobVariable`:

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

        @Json
        data class User(val name: String, val code: Int)

        @JobVariable("user")
        @JobWorker("someJobType")
        fun process(): User {
            // do something
        }
    }
    ```

#### Ошибки { #errors }

Если требуется завершить выполнение ошибкой процесса, выбросьте `JobWorkerException` из пакета
`io.koraframework.camunda.zeebe.worker.exception`.
Исключение может содержать код ошибки, сообщение и переменные процесса, если они нужны.
Такое исключение преобразуется в команду `throwError` для `Zeebe`: `getCode()`, сообщение и `getVariables()` исключения
отправляются как код ошибки, сообщение об ошибке и переменные команды, а модель `BPMN` решает, как обработать ошибку,
например через граничное событие ошибки.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public User process() {
            throw new JobWorkerException("DOESNT_WORK"); //(1)!
        }
    }
    ```

    1. Дополнительные конструкторы принимают сообщение/причину и `Map<String, Object>` переменных, которые будут приложены к команде `throwError`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(): User {
            throw JobWorkerException("DOESNT_WORK") //(1)!
        }
    }
    ```

    1. Дополнительные конструкторы принимают сообщение/причину и `Map<String, Any>` переменных, которые будут приложены к команде `throwError`

Любое другое исключение считается технической ошибкой, а не ошибкой процесса: модуль оборачивает его в
`JobWorkerException` с одним из встроенных кодов ниже и пропускает дальше. Задание при этом помечается на брокере как
неуспешное и активируется повторно согласно настройкам `backoff` исполнителя, пока не закончатся повторы и не будет
создан инцидент.

| Код             | Когда используется                                                                                  |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `SERIALIZATION` | Результат исполнителя не удалось записать в переменные процесса                                     |
| `UNEXPECTED`    | Любая другая ошибка метода-исполнителя, включая переменную задания, которую не удалось прочитать в аргумент |

### Императивные { #imperative }

Можно также создавать исполнителей более низкого уровня и работать напрямую с контрактами `CamundaClient`.
Для этого компонент должен реализовывать интерфейс `KoraJobWorker`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob implements KoraJobWorker {

        @Override
        public String type() {
            return "someJobType";
        }

        @Override
        public List<String> fetchVariables() {
            return List.of("startId"); //(1)!
        }

        @Override
        public FinalCommandStep<?> handle(JobClient client, ActivatedJob job) {
            return client.newCompleteCommand(job); //(2)!
        }
    }
    ```

    1. Из `Zeebe` будут запрошены только эти переменные, пустой список (значение по умолчанию) запрашивает **все** переменные
    2. Возвращенную команду модуль отправляет сам после того, как зафиксирует телеметрию вызова

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob : KoraJobWorker {

        override fun type(): String = "someJobType"

        override fun fetchVariables(): List<String> = listOf("startId") //(1)!

        override fun handle(client: JobClient, job: ActivatedJob): FinalCommandStep<*> {
            return client.newCompleteCommand(job) //(2)!
        }
    }
    ```

    1. Из `Zeebe` будут запрошены только эти переменные, пустой список (значение по умолчанию) запрашивает **все** переменные
    2. Возвращенную команду модуль отправляет сам после того, как зафиксирует телеметрию вызова

Метод `fetchVariables()` — императивный аналог `@JobVariable`: он определяет, какие переменные процесса `Zeebe` отправит
вместе с заданием. По умолчанию он возвращает пустой список, что означает получение всех переменных; непустой список
ограничивает передаваемые данные только этими переменными. В отличие от декларативных исполнителей, `handle` получает
исходные `JobClient` и `ActivatedJob` и сам решает, какая команда завершит задание: `client.newCompleteCommand(job)`
завершает его успешно, а `client.newThrowErrorCommand(job).errorCode("DOESNT_WORK").errorMessage("...")` поднимает
ошибку `BPMN`. Исключение, выброшенное из `handle`, наоборот, помечает задание как неуспешное, и брокер активирует его
повторно согласно настройкам `backoff`.

## Сигнатуры { #signatures }

Доступные сигнатуры для методов-исполнителей из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения либо `void`.
    Если результат равен `null` или `Optional.empty()`, задание завершается без добавления переменных.

    - `void myMethod()`
    - `T myMethod()`
    - `Optional<T> myMethod()`

    Асинхронные сигнатуры не поддерживаются: возвращаемые типы `CompletionStage`, `Future` и `Publisher` / `Mono`
    отклоняются на этапе компиляции с ошибкой `Async invocation is not supported`.

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, это может быть `T`, `T?` либо `Unit`.
    Если результат равен `null`, задание завершается без добавления переменных.

    - `myMethod()`
    - `myMethod(): T`
    - `myMethod(): T?`

    Асинхронные сигнатуры не поддерживаются: `suspend`-функции и возвращаемые типы `Deferred`, `Mono`, `Flux`
    и `CompletionStage` отклоняются на этапе компиляции.
