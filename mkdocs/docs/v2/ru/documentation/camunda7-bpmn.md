---
description: "Explains Kora Camunda 7 BPMN embedded process engine integration, resource deployment, delegates, engine services, transactions, configuration, and telemetry. Use when working with CamundaEngineBpmnModule, CamundaEngineBpmnConfig, ProcessEngine, JavaDelegate, KoraDelegate, CamundaTransactionManager, ProcessEngineConfigurator, Metrics Reference."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the Kora Camunda 7 BPMN embedded process engine, resource deployment, delegates, engine services, transactions, configuration, and telemetry; key triggers include CamundaEngineBpmnModule, CamundaEngineBpmnConfig, ProcessEngine, JavaDelegate, KoraDelegate, CamundaEngineDataSource, CamundaTransactionManager, ProcessEngineConfigurator, CamundaVersion, Metrics Reference."
---

??? warning "Экспериментальный модуль"

    **Экспериментальный** модуль является полностью рабочим и протестированным, но требует дополнительной апробации и аналитики по использованию.
    Поэтому `API` может получить незначительные изменения до полной готовности.

???+ warning "Camunda 7 устарела"

    `CamundaEngineBpmnModule` помечен как `@Deprecated`, потому что [Camunda 7 достигла конца жизненного цикла](https://camunda.com/blog/2025/02/camunda-7-enterprise-end-of-life-extension/).
    Модуль по-прежнему работает и поставляется, но новых возможностей для него не планируется.
    Для новых сервисов рассмотрите [Camunda 8](camunda8-worker.md) или движок [Operaton](https://operaton.org/) — форк Camunda 7, развиваемый сообществом.

Модуль подключает встроенный движок [Camunda 7](https://docs.camunda.org/manual/7.24/) для выполнения `BPMN`-процессов внутри приложения Kora.
Он создает и настраивает `ProcessEngine`, связывает его с `JDBC`-источником данных, регистрирует исполнителей из графа приложения, загружает `BPMN` / `FORM` / `DMN`-ресурсы из `classpath` и добавляет телеметрию выполнения.

Чтобы предоставить `Camunda 7 REST API` по HTTP, используйте вместе с этим модулем отдельный [модуль Camunda 7 REST](camunda7-rest.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework.experimental:camunda-engine-bpmn"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CamundaEngineBpmnModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework.experimental:camunda-engine-bpmn")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CamundaEngineBpmnModule
    ```

Модуль требует подключения [модуля JDBC](database-jdbc.md).
По умолчанию используется основной `DataSource` приложения, но при необходимости можно предоставить отдельный `DataSource` с тегом `@Tag(CamundaBpmn.class)`.

## Конфигурация { #configuration }

Пример полной конфигурации, описанной в интерфейсе `CamundaEngineBpmnConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda {
        engine {
            bpmn {
                jobExecutor {
                    corePoolSize = 5 //(1)!
                    maxPoolSize = 25 //(2)!
                    queueSize = 25 //(3)!
                    maxJobsPerAcquisition = 2 //(4)!
                    virtualThreadsEnabled = false //(5)!
                }
                deployment {
                    tenantId = "Camunda" //(6)!
                    name = "KoraEngineAutoDeployment" //(7)!
                    deployChangedOnly = true //(8)!
                    resources = ["classpath:bpm"] //(9)!
                    delay = "1m" //(10)!
                }
                parallelInitialization {
                    enabled = true //(11)!
                    validateIncompleteStatements = true //(12)!
                }
                admin {
                    id = "admin" //(13)!
                    password = "admin" //(14)!
                    firstname = "Ivan" //(15)!
                    lastname = "Ivanov" //(16)!
                    email = "admin@mail.ru" //(17)!
                }
                telemetry {
                    logging {
                        enabled = false //(18)!
                        stacktrace = true //(19)!
                    }
                    metrics {
                        enabled = false //(20)!
                        engineMetrics = false //(21)!
                        slo = [1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000] //(22)!
                        tags = { //(23)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                    tracing {
                        enabled = true //(24)!
                        attributes = { //(25)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                }
            }
        }
    }
    ```

    1.  Минимальное количество постоянно живущих потоков в [`JobExecutor`](https://docs.camunda.org/manual/7.24/user-guide/process-engine/the-job-executor/) (по умолчанию: `5`).
    2.  Максимальное количество потоков в [`JobExecutor`](https://docs.camunda.org/manual/7.24/user-guide/process-engine/the-job-executor/) (по умолчанию: `25`).
    3.  Размер очереди задач `JobExecutor`, при превышении которого новые задачи отклоняются (по умолчанию: `25`).
    4.  Максимальное количество задач, забираемых `JobExecutor` за один запрос (по умолчанию: `Runtime.getRuntime().availableProcessors() * 2`).
    5.  Использовать [виртуальные потоки](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html) в качестве основы `JobExecutor` (по умолчанию: `false`). При включении этой опции настройки размера пула и очереди не используются.
    6.  Идентификатор `tenant` для [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.24/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию не указан, опционально).
    7.  Имя [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.24/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию: `KoraEngineAutoDeployment`).
    8.  Загружать только измененные ресурсы за счет фильтрации дубликатов в `Camunda` (по умолчанию: `true`).
    9.  Список путей для поиска `BPMN` / `FORM` / `DMN`-ресурсов (`обязательный`, по умолчанию не указан). Поддерживаются только пути с префиксом `classpath:`.
    10. Задержка перед загрузкой ресурсов в движок (по умолчанию не указана, опционально).
    11. Включить параллельную инициализацию движка (по умолчанию: `true`).
    12. Проверять незавершенные выражения движка при параллельной инициализации (по умолчанию: `true`).
    13. Идентификатор администратора `Camunda` (`обязательный`, по умолчанию не указан). Вся секция `admin` является опциональной.
    14. Пароль администратора `Camunda` (`обязательный`, по умолчанию не указан). Вся секция `admin` является опциональной.
    15. Имя администратора `Camunda` (по умолчанию не указано, опционально). Если не указано, используется `id` в верхнем регистре.
    16. Фамилия администратора `Camunda` (по умолчанию не указана, опционально). Если не указана, используется `id` в верхнем регистре.
    17. Адрес электронной почты администратора `Camunda` (по умолчанию не указан, опционально). Если не указан, используется `<id>@localhost`.
    18. Включает логирование модуля (по умолчанию: `false`).
    19. Включает логирование стек-трейса ошибок (по умолчанию: `true`).
    20. Включает метрики модуля (по умолчанию: `false`).
    21. Включает собственные метрики движка и задач `Camunda`, которые накапливаются в таблицах ее базы данных (по умолчанию: `false`).
    22. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    23. Теги метрик (по умолчанию: `{}`).
    24. Включает трассировку модуля (по умолчанию: `true`).
    25. Атрибуты трассировки (по умолчанию: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      engine:
        bpmn:
          jobExecutor:
            corePoolSize: 5 #(1)!
            maxPoolSize: 25 #(2)!
            queueSize: 25 #(3)!
            maxJobsPerAcquisition: 2 #(4)!
            virtualThreadsEnabled: false #(5)!
          deployment:
            tenantId: "Camunda" #(6)!
            name: "KoraEngineAutoDeployment" #(7)!
            deployChangedOnly: true #(8)!
            resources: #(9)!
              - "classpath:bpm"
            delay: "1m" #(10)!
          parallelInitialization:
            enabled: true #(11)!
            validateIncompleteStatements: true #(12)!
          admin:
            id: "admin" #(13)!
            password: "admin" #(14)!
            firstname: "Ivan" #(15)!
            lastname: "Ivanov" #(16)!
            email: "admin@mail.ru" #(17)!
          telemetry:
            logging:
              enabled: false #(18)!
              stacktrace: true #(19)!
            metrics:
              enabled: false #(20)!
              engineMetrics: false #(21)!
              slo: [1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000] #(22)!
              tags: #(23)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(24)!
              attributes: #(25)!
                key1: value1
                key2: value2
    ```

    1.  Минимальное количество постоянно живущих потоков в [`JobExecutor`](https://docs.camunda.org/manual/7.24/user-guide/process-engine/the-job-executor/) (по умолчанию: `5`).
    2.  Максимальное количество потоков в [`JobExecutor`](https://docs.camunda.org/manual/7.24/user-guide/process-engine/the-job-executor/) (по умолчанию: `25`).
    3.  Размер очереди задач `JobExecutor`, при превышении которого новые задачи отклоняются (по умолчанию: `25`).
    4.  Максимальное количество задач, забираемых `JobExecutor` за один запрос (по умолчанию: `Runtime.getRuntime().availableProcessors() * 2`).
    5.  Использовать [виртуальные потоки](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html) в качестве основы `JobExecutor` (по умолчанию: `false`). При включении этой опции настройки размера пула и очереди не используются.
    6.  Идентификатор `tenant` для [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.24/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию не указан, опционально).
    7.  Имя [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.24/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию: `KoraEngineAutoDeployment`).
    8.  Загружать только измененные ресурсы за счет фильтрации дубликатов в `Camunda` (по умолчанию: `true`).
    9.  Список путей для поиска `BPMN` / `FORM` / `DMN`-ресурсов (`обязательный`, по умолчанию не указан). Поддерживаются только пути с префиксом `classpath:`.
    10. Задержка перед загрузкой ресурсов в движок (по умолчанию не указана, опционально).
    11. Включить параллельную инициализацию движка (по умолчанию: `true`).
    12. Проверять незавершенные выражения движка при параллельной инициализации (по умолчанию: `true`).
    13. Идентификатор администратора `Camunda` (`обязательный`, по умолчанию не указан). Вся секция `admin` является опциональной.
    14. Пароль администратора `Camunda` (`обязательный`, по умолчанию не указан). Вся секция `admin` является опциональной.
    15. Имя администратора `Camunda` (по умолчанию не указано, опционально). Если не указано, используется `id` в верхнем регистре.
    16. Фамилия администратора `Camunda` (по умолчанию не указана, опционально). Если не указана, используется `id` в верхнем регистре.
    17. Адрес электронной почты администратора `Camunda` (по умолчанию не указан, опционально). Если не указан, используется `<id>@localhost`.
    18. Включает логирование модуля (по умолчанию: `false`).
    19. Включает логирование стек-трейса ошибок (по умолчанию: `true`).
    20. Включает метрики модуля (по умолчанию: `false`).
    21. Включает собственные метрики движка и задач `Camunda`, которые накапливаются в таблицах ее базы данных (по умолчанию: `false`).
    22. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    23. Теги метрик (по умолчанию: `{}`).
    24. Включает трассировку модуля (по умолчанию: `true`).
    25. Атрибуты трассировки (по умолчанию: `{}`).

Секция `deployment` является опциональной: если она не указана, модуль не выполняет автоматическую загрузку ресурсов.
Если секция указана, `resources` должна содержать хотя бы один путь.
Ресурсы ищутся рекурсивно в `classpath`; неподдерживаемые пути без префикса `classpath:` пропускаются.

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#camunda-7-bpmn).

## Загрузка ресурсов { #deployment }

Когда секция `deployment` присутствует, модуль автоматически загружает ресурсы процессов в движок после его создания.
Ресурсы размещаются в `classpath` (обычно в каталоге `src/main/resources`) и указываются в списке `resources`:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda.engine.bpmn {
        deployment {
            resources = ["classpath:bpm"] //(1)!
        }
    }
    ```

    1.  Когда секция `deployment` присутствует, требуется хотя бы один путь. Поддерживаются только пути с префиксом `classpath:`.

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      engine:
        bpmn:
          deployment:
            resources: #(1)!
              - "classpath:bpm"
    ```

    1.  Когда секция `deployment` присутствует, требуется хотя бы один путь. Поддерживаются только пути с префиксом `classpath:`.

При следующей структуре каталогов путь `classpath:bpm` сканируется рекурсивно, и каждый поддерживаемый ресурс внутри него загружается:

```
src/main/resources/bpm/
├── approve.form
├── helloworld.bpmn
└── onboarding.bpmn
```

Правила загрузки, которые стоит учитывать:

- Поддерживаемые типы ресурсов — модели процессов `BPMN`, формы `FORM` и таблицы решений `DMN`. Кейс-модели `CMMN` этой интеграцией не поддерживаются: движок собирается без `CMMN`, а запросы кейсов всегда возвращают пустой результат.
- Загружаются только пути с префиксом `classpath:`. Любой другой путь пропускается с предупреждением в логе.
- Пути сканируются **рекурсивно**, поэтому вложенные каталоги внутри указанного пути также включаются.
- Ресурсы находятся как в распакованных каталогах, так и внутри `JAR`-файлов, поэтому путь `classpath:bpm` продолжает работать и в собранном дистрибутиве.
- При `deployChangedOnly = true` (по умолчанию) включается фильтрация дубликатов `Camunda`, поэтому повторно загружаются только ресурсы, изменившиеся с момента предыдущей загрузки.
- Опциональный `tenantId` привязывает загрузку к конкретному `tenant`, а `delay` откладывает загрузку на заданное время после старта.
- Загрузка регистрируется под именем `name` (по умолчанию `KoraEngineAutoDeployment`).
- Если вся секция `deployment` опущена, модуль не загружает никакие ресурсы — предполагается, что вы загружаете их самостоятельно через `RepositoryService`.

## Исполнители { #applications }

`Camunda` может вызывать компоненты приложения в качестве исполнителей процесса.
Обычные компоненты [`JavaDelegate`](https://docs.camunda.org/manual/7.24/user-guide/process-engine/delegation-code/) регистрируются в контексте выражений движка по полному имени класса (`canonicalName`) и по короткому имени класса (`simpleName`).
Внутри `execute(...)` вы читаете и записываете переменные процесса через `DelegateExecution`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ScoreCustomerDelegate implements JavaDelegate {

        private static final Logger logger = LoggerFactory.getLogger(ScoreCustomerDelegate.class);

        @Override
        public void execute(DelegateExecution execution) {
            int scoring = ThreadLocalRandom.current().nextInt(1, 100);
            logger.info("Scored {} with result {}.", execution.getBusinessKey(), scoring);
            execution.setVariable("result", scoring);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ScoreCustomerDelegate : JavaDelegate {

        private val logger = LoggerFactory.getLogger(ScoreCustomerDelegate::class.java)

        override fun execute(execution: DelegateExecution) {
            val scoring = ThreadLocalRandom.current().nextInt(1, 100)
            logger.info("Scored {} with result {}.", execution.businessKey, scoring)
            execution.setVariable("result", scoring)
        }
    }
    ```

Поскольку `JavaDelegate` регистрируется по короткому имени класса, `serviceTask` в модели `BPMN` ссылается на него по `simpleName` через `camunda:delegateExpression`:

```xml
<bpmn:serviceTask id="Activity_0tusr5p" name="Score Customer"
                  camunda:delegateExpression="${ScoreCustomerDelegate}">
    <bpmn:incoming>Flow_score_in</bpmn:incoming>
    <bpmn:outgoing>Flow_score_out</bpmn:outgoing>
</bpmn:serviceTask>
```

Используйте `KoraDelegate` для произвольного имени исполнителя.
Метод `key()` по умолчанию возвращает `canonicalName`, но его можно переопределить, чтобы задать имя, используемое в выражениях `BPMN`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SimpleDelegate implements KoraDelegate {

        @Override
        public String key() {
            return "myKey";
        }

        @Override
        public void execute(DelegateExecution delegateExecution) throws Exception {

        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SimpleKoraDelegate : KoraDelegate {

        override fun key(): String = "myKey"

        override fun execute(delegateExecution: DelegateExecution) {

        }
    }
    ```

На объявленный таким образом исполнитель ссылаются как `${myKey}` в `camunda:delegateExpression`, поэтому имя, используемое в модели процесса, больше не зависит от имени класса.
Для `KoraDelegate` продолжают работать и `simpleName`, и `canonicalName`, так что переопределение `key()` лишь добавляет еще одно имя.

Эти же имена доступны в скриптовых задачах и скриптовых выражениях `BPMN`, потому что модуль регистрирует свой реестр исполнителей как скриптовый `Resolver` `Camunda`.
Кроме того, исполнитель разрешается и через `camunda:class` по полному имени класса: модуль устанавливает `ArtifactFactory`, который возвращает компонент из графа вместо создания нового объекта, поэтому `camunda:class="com.example.ScoreCustomerDelegate"` вызывает именно компонент из контейнера со всеми внедренными зависимостями.

Каждый исполнитель перед вызовом оборачивается фабрикой `KoraDelegateWrapperFactory`: она открывает новую область логирования `MDC` и телеметрическое наблюдение модуля вокруг `execute(...)`.
Вы можете предоставить собственную `KoraDelegateWrapperFactory` в виде `@Component`, чтобы изменить это поведение.

## Сервисы движка { #engine-services }

Модуль предоставляет стандартные сервисы `Camunda` в виде компонентов графа зависимостей:

- `RuntimeService`
- `RepositoryService`
- `ManagementService`
- `AuthorizationService`
- `DecisionService`
- `ExternalTaskService`
- `FilterService`
- `FormService`
- `TaskService`
- `HistoryService`
- `IdentityService`

Эти сервисы можно внедрять в ваши компоненты обычным образом, как и сам `ProcessEngine`.

## Запуск процессов и взаимодействие с ними { #usage }

Внедрите `ProcessEngine` (или любой из перечисленных выше сервисов движка) в свои компоненты, чтобы запускать процессы и управлять их экземплярами.
Процесс запускается по `id` процесса `BPMN` через `RuntimeService`, а определения процессов можно запрашивать через `RepositoryService`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController("/camunda")
    public final class CamundaController {

        @Json
        public record CamundaProcess(String instanceId, String businessKey) {}

        private final ProcessEngine processEngine;

        public CamundaController(ProcessEngine processEngine) {
            this.processEngine = processEngine;
        }

        @Json
        @HttpRoute(method = HttpMethod.GET, path = "/start/onboarding")
        public HttpResponseEntity<CamundaProcess> startOnboarding() {
            String businessKey = UUID.randomUUID().toString();
            ProcessInstance instance = processEngine.getRuntimeService()
                .startProcessInstanceByKey("Onboarding", businessKey);
            return HttpResponseEntity.of(200, new CamundaProcess(instance.getId(), businessKey));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController("/camunda")
    class CamundaController(private val processEngine: ProcessEngine) {

        @Json
        data class CamundaProcess(val instanceId: String, val businessKey: String)

        @Json
        @HttpRoute(method = HttpMethod.GET, path = "/start/onboarding")
        fun startOnboarding(): HttpResponseEntity<CamundaProcess> {
            val businessKey = UUID.randomUUID().toString()
            val instance = processEngine.runtimeService
                .startProcessInstanceByKey("Onboarding", businessKey)
            return HttpResponseEntity.of(200, CamundaProcess(instance.id, businessKey))
        }
    }
    ```

Запущенный процесс можно продвигать и извне движка: `RuntimeService.correlateMessage(...)` доставляет событие-сообщение `BPMN`, а `TaskService` / `FormService` завершают пользовательские задачи и отправляют формы:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController("/camunda/process/onboarding")
    public final class OnboardingController {

        private final FormService formService;
        private final TaskService taskService;
        private final RuntimeService runtimeService;

        public OnboardingController(FormService formService, TaskService taskService, RuntimeService runtimeService) {
            this.formService = formService;
            this.taskService = taskService;
            this.runtimeService = runtimeService;
        }

        @HttpRoute(path = "/cancel/{businessKey}", method = HttpMethod.GET)
        public String customerCancellation(@Path String businessKey) {
            runtimeService.correlateMessage("MessageCustomerCancellation", businessKey);
            return "Cancelled: " + businessKey;
        }

        @HttpRoute(path = "/order/{businessKey}", method = HttpMethod.GET)
        public String customerOrder(@Path String businessKey) {
            Task task = taskService.createTaskQuery().processInstanceBusinessKey(businessKey).active().singleResult();
            formService.submitTaskForm(task.getId(), Map.of("approved", true));
            return "Approved: " + businessKey;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController("/camunda/process/onboarding")
    class OnboardingController(
        private val formService: FormService,
        private val taskService: TaskService,
        private val runtimeService: RuntimeService
    ) {

        @HttpRoute(path = "/cancel/{businessKey}", method = HttpMethod.GET)
        fun customerCancellation(@Path businessKey: String): String {
            runtimeService.correlateMessage("MessageCustomerCancellation", businessKey)
            return "Cancelled: $businessKey"
        }

        @HttpRoute(path = "/order/{businessKey}", method = HttpMethod.GET)
        fun customerOrder(@Path businessKey: String): String {
            val task = taskService.createTaskQuery().processInstanceBusinessKey(businessKey).active().singleResult()
            formService.submitTaskForm(task.id, mapOf("approved" to true))
            return "Approved: $businessKey"
        }
    }
    ```

## Источник данных и транзакции { #datasource }

Движок сохраняет свое состояние через `JDBC`-`DataSource`, поэтому [модуль JDBC](database-jdbc.md) обязателен.
По умолчанию модуль переиспользует основной `DataSource` приложения, предоставляемый движку под тегом `@Tag(CamundaBpmn.class)`.
Чтобы выделить движку отдельный источник данных, предоставьте собственный `DataSource` с этим тегом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface CamundaDataSourceModule {

        @Tag(CamundaBpmn.class)
        default DataSource camundaDataSource(/* ... */) {
            return dataSource;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface CamundaDataSourceModule {

        @Tag(CamundaBpmn::class)
        fun camundaDataSource(/* ... */): DataSource {
            return dataSource
        }
    }
    ```

Компонент `CamundaEngineDataSource` абстрагирует `DataSource` движка вместе с его `CamundaTransactionManager`.
Реализация по умолчанию выполняет `JDBC` через `DataSource` с тегом `@Tag(CamundaBpmn.class)`; вы можете переопределить `CamundaEngineDataSource` как `@Component`, чтобы полностью контролировать, как движок получает соединения и управляет транзакциями.

Поскольку движок работает с внешним управлением транзакциями, каждая команда движка выполняется внутри транзакции, открытой `CamundaTransactionManager`.
Исполнитель, выполняющий собственную `JDBC`-работу, может присоединиться к этой транзакции вместо открытия второй.
`inContinueTx(...)` переиспользует соединение текущей транзакции движка (открывая новую только если активной нет), тогда как `inNewTx(...)` всегда открывает новую транзакцию; `currentConnection()` возвращает дескриптор для `commit()` / `rollback()` текущей транзакции:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class AuditDelegate implements JavaDelegate {

        private final CamundaTransactionManager transactionManager;

        public AuditDelegate(CamundaTransactionManager transactionManager) {
            this.transactionManager = transactionManager;
        }

        @Override
        public void execute(DelegateExecution execution) {
            transactionManager.inContinueTx(() -> {
                // JDBC work sharing the engine transaction
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class AuditDelegate(private val transactionManager: CamundaTransactionManager) : JavaDelegate {

        override fun execute(execution: DelegateExecution) {
            transactionManager.inContinueTx(Runnable {
                // JDBC work sharing the engine transaction
            })
        }
    }
    ```

Ошибка `JDBC`-операции сообщается как `UncheckedSqlException`.

## Исполнитель задач и готовность { #job-executor }

Движок выполняет асинхронные продолжения и таймеры через [`JobExecutor`](https://docs.camunda.org/manual/7.24/user-guide/process-engine/the-job-executor/).
Реализация выбирается опцией `jobExecutor.virtualThreadsEnabled`: при `false` (по умолчанию) используется исполнитель на пуле потоков с именами потоков `camunda-worker-N` и размерами, задаваемыми `corePoolSize` / `maxPoolSize` / `queueSize` / `maxJobsPerAcquisition`; при `true` используется исполнитель на [виртуальных потоках](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html) с именами потоков `camunda-job-executor-N`, а размеры пула и очереди игнорируются (см. пояснения в разделе [Конфигурация](#configuration)).

Модуль автоматически регистрирует [пробу готовности](probes.md), которая сообщает о приложении как `UP` только после того, как `JobExecutor` становится активным.
Пока исполнитель задач не активирован, проба падает с сообщением `Camunda BPMN Engine JobExecutor is not active`, что удерживает приложение вне ротации, пока движок еще запускается.

При `parallelInitialization.enabled = true` (по умолчанию) движок стартует в два этапа: на первом этапе движок собирается с сокращенным набором выражений `MyBatis`, чтобы приложение запускалось быстрее, а на втором этапе добавляются оставшиеся выражения и параллельно с остальными конфигураторами активируется `JobExecutor`.
Значение `parallelInitialization.enabled = false` собирает движок в один этап.

## Пользователь-администратор { #admin }

Когда секция `admin` присутствует, модуль создает пользователя-администратора `Camunda`, гарантирует существование группы `camunda-admin` с полными правами и добавляет в нее пользователя (см. пояснения `admin` в разделе [Конфигурация](#configuration)).
Эта учетная запись хранится в сервисе идентификации движка, поэтому она аутентифицируется в [Camunda 7 REST API](camunda7-rest.md) и в любом внешнем веб-приложении `Camunda`, работающем с той же базой данных.
Если секция `admin` опущена, пользователь не создается; если пользователь с указанным `id` уже существует, ничего не изменяется.

## Конфигурация движка { #engine-configuration }

Для дополнительной настройки зарегистрируйте компонент `ProcessEngineConfigurator`.
Метод `prepare(...)` вызывается до создания [ProcessEngine](https://docs.camunda.org/manual/7.24/user-guide/process-engine/process-engine-bootstrapping/) и получает `ProcessEngineConfiguration`; метод `setup(...)` вызывается после создания движка:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SimpleProcessEngineConfigurator implements ProcessEngineConfigurator {

        @Override
        public void prepare(ProcessEngineConfiguration configuration) {

        }

        @Override
        public void setup(ProcessEngine engine) throws Exception {

        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SimpleProcessEngineConfigurator : ProcessEngineConfigurator {

        override fun prepare(configuration: ProcessEngineConfiguration) {

        }

        override fun setup(engine: ProcessEngine) {

        }
    }
    ```

Все вызовы `setup(...)` выполняются параллельно на виртуальных потоках, поэтому конфигуратор не должен полагаться на порядок выполнения других конфигураторов.
Сам модуль через этот же механизм добавляет конфигуратор пользователя-администратора, конфигуратор загрузки ресурсов и конфигуратор второго этапа инициализации.

Всю `ProcessEngineConfiguration` тоже можно заменить: она предоставляется как `@DefaultComponent`, поэтому регистрация собственного компонента `ProcessEngineConfiguration` имеет приоритет над `KoraProcessEngineConfiguration` из модуля.

## Плагины { #plugins }

Вы можете зарегистрировать произвольные [`ProcessEnginePlugin`](https://docs.camunda.org/manual/7.24/user-guide/process-engine/process-engine-plugins/), предоставив их в качестве компонентов в контейнере зависимостей Kora.
Модуль собирает все такие компоненты и передает их в конфигурацию движка при создании `ProcessEngine`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SimpleProcessEnginePlugin implements ProcessEnginePlugin {

        @Override
        public void preInit(ProcessEngineConfigurationImpl configuration) {

        }

        @Override
        public void postInit(ProcessEngineConfigurationImpl configuration) {

        }

        @Override
        public void postProcessEngineBuild(ProcessEngine engine) {

        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SimpleProcessEnginePlugin : ProcessEnginePlugin {

        override fun preInit(configuration: ProcessEngineConfigurationImpl) {

        }

        override fun postInit(configuration: ProcessEngineConfigurationImpl) {

        }

        override fun postProcessEngineBuild(engine: ProcessEngine) {

        }
    }
    ```

## Версия Camunda { #version }

Определенная версия `Camunda` доступна как внедряемый компонент `CamundaVersion`.
Его `version()` возвращает строку версии, сообщаемую пакетом `Camunda`, а `isEnterprise()` возвращает `true`, когда в classpath присутствует enterprise-дистрибутив (`-ee`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class VersionPrinter {

        public VersionPrinter(CamundaVersion version) {
            if (version.isEnterprise()) {
                // enterprise-only behavior
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class VersionPrinter(version: CamundaVersion) {

        init {
            if (version.isEnterprise()) {
                // enterprise-only behavior
            }
        }
    }
    ```

## Тестирование { #testing }

Для [компонентных тестов](junit5.md) движок можно заменить на in-memory, чтобы не требовалась внешняя база данных.
Компонент `ProcessEngineConfiguration` заменяется на `StandaloneInMemProcessEngineConfiguration`, который сохраняет предоставленные Kora менеджер выражений, фабрику артефактов, генератор идентификаторов, исполнитель задач и скриптовый резолвер, поэтому исполнители из графа по-прежнему разрешаются как обычно:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class InMemoryProcessEngineConfiguration extends StandaloneInMemProcessEngineConfiguration {

        public InMemoryProcessEngineConfiguration(KoraAppGraph graph) {
            setDatabaseSchemaUpdate(ProcessEngineConfiguration.DB_SCHEMA_UPDATE_CREATE_DROP);
            setJdbcUrl("jdbc:h2:mem:camunda;DB_CLOSE_ON_EXIT=FALSE");
            setAuthorizationEnabled(false);
            setJobExecutorActivate(true);
            setExpressionManager(graph.getFirst(JuelExpressionManager.class));
            setArtifactFactory(graph.getFirst(ArtifactFactory.class));
            setIdGenerator(graph.getFirst(IdGenerator.class));
            setJobExecutor(graph.getFirst(JobExecutor.class));
            if (getResolverFactories() == null) {
                setResolverFactories(new ArrayList<>());
            }
            getResolverFactories().add(graph.getFirst(KoraResolverFactory.class));
        }
    }

    @KoraAppTest(Application.class)
    class ProcessTests implements KoraAppTestGraphModifier, KoraAppTestConfigModifier {

        @Mock
        @TestComponent
        private CamundaEngineDataSource mockDataSource;
        @TestComponent
        private ProcessEngine processEngine;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                camunda.engine.bpmn {
                  deployment.resources = "classpath:bpm"
                }
                """);
        }

        @Override
        public KoraGraphModification graph() {
            return KoraGraphModification.create()
                .replaceComponent(ProcessEngineConfiguration.class, InMemoryProcessEngineConfiguration::new);
        }

        @Test
        void processStarted() {
            var instance = processEngine.getRuntimeService()
                .startProcessInstanceByKey("Onboarding", UUID.randomUUID().toString());
            assertNotNull(instance.getId());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class InMemoryProcessEngineConfiguration(graph: KoraAppGraph) : StandaloneInMemProcessEngineConfiguration() {

        init {
            databaseSchemaUpdate = ProcessEngineConfiguration.DB_SCHEMA_UPDATE_CREATE_DROP
            jdbcUrl = "jdbc:h2:mem:camunda;DB_CLOSE_ON_EXIT=FALSE"
            authorizationEnabled = false
            isJobExecutorActivate = true
            expressionManager = graph.getFirst(JuelExpressionManager::class.java)
            artifactFactory = graph.getFirst(ArtifactFactory::class.java)
            idGenerator = graph.getFirst(IdGenerator::class.java)
            jobExecutor = graph.getFirst(JobExecutor::class.java)
            if (resolverFactories == null) {
                resolverFactories = ArrayList()
            }
            resolverFactories.add(graph.getFirst(KoraResolverFactory::class.java))
        }
    }

    @KoraAppTest(Application::class)
    class ProcessTests : KoraAppTestGraphModifier, KoraAppTestConfigModifier {

        @Mock
        @TestComponent
        lateinit var mockDataSource: CamundaEngineDataSource

        @TestComponent
        lateinit var processEngine: ProcessEngine

        override fun config(): KoraConfigModification = KoraConfigModification.ofString(
            """
            camunda.engine.bpmn {
              deployment.resources = "classpath:bpm"
            }
            """.trimIndent()
        )

        override fun graph(): KoraGraphModification = KoraGraphModification.create()
            .replaceComponent(ProcessEngineConfiguration::class.java, ::InMemoryProcessEngineConfiguration)

        @Test
        fun processStarted() {
            val instance = processEngine.runtimeService
                .startProcessInstanceByKey("Onboarding", UUID.randomUUID().toString())
            assertNotNull(instance.id)
        }
    }
    ```

Мок `CamundaEngineDataSource` не дает реальному `DataSource` приложения попасть в тестовый граф, а любой исполнитель можно замокать через `@Mock` `@TestComponent`, чтобы проверить, что процесс до него дошел.

## Телеметрия { #telemetry }

Модуль сообщает собственные логирование, метрики и трассировку для выполнения исполнителей через секцию конфигурации `telemetry`.

Логирование пишется в логгер, названный по классу исполнителя, и создает событие `Camunda BPMN Engine started` перед вызовом и событие `Camunda BPMN Engine finished delegate execution` (или `... failed delegate execution`) после него, со структурированными полями `processBusinessKey`, `processInstanceId`, `activityId`, `activityName`, `eventName`, `businessKey` и временем обработки.

Трассировка создает на каждый вызов исполнителя span `Camunda Delegate <canonicalName>` с атрибутами `eventName`, `processBusinessKey` и `processInstanceId`.
Метрики описаны в разделе [Справочник метрик](metrics.md#camunda-7-bpmn), а область `MDC`, открываемая `KoraDelegateWrapperFactory`, ограничивает эту телеметрию рамками каждого вызова исполнителя.

Чтобы изменить состав отправляемых данных, зарегистрируйте как `@Component` собственного наследника `DefaultCamundaEngineLoggerFactory` или `DefaultCamundaEngineMetricsFactory`; вся `CamundaEngineTelemetryFactory` предоставляется через `@DefaultComponent` и также может быть заменена.

Независимо от телеметрии модуля, `telemetry.metrics.engineMetrics` переключает собственные метрики движка и задач `Camunda`, которые движок накапливает в своих таблицах базы данных (по умолчанию отключены).
