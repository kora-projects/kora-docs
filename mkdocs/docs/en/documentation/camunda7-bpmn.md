---
description: "Explains Kora Camunda 7 BPMN embedded process engine integration, deployment, worker components, configuration, and telemetry. Use when working with CamundaEngineBpmnModule, CamundaEngineBpmnConfig, ProcessEngine, JavaDelegate, @Component, Metrics Reference."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Camunda 7 BPMN embedded process engine integration, deployment, worker components, configuration, and telemetry; key triggers include CamundaEngineBpmnModule, CamundaEngineBpmnConfig, ProcessEngine, JavaDelegate, @Component, Metrics Reference."
---

??? warning "Experimental module"

    The **experimental** module is fully working and tested, but requires additional usage validation and analysis.
    Therefore, the `API` may receive minor changes before full readiness.

The module connects an embedded [Camunda 7](https://docs.camunda.org/manual/7.21/) engine for executing `BPMN` processes inside a Kora application.
It creates and configures `ProcessEngine`, connects it to a `JDBC` data source, registers delegates from the application graph, deploys `BPMN` / `FORM` / `DMN` resources from `classpath`, and adds execution telemetry.

To expose the `Camunda 7 REST API` and the `Cockpit` / `Admin` / `Tasklist` web applications over HTTP, use the separate [Camunda 7 REST module](camunda7-rest.md) alongside this one.

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:camunda-engine-bpmn"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CamundaEngineBpmnModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:camunda-engine-bpmn")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : CamundaEngineBpmnModule
    ```

The module requires the [JDBC module](database-jdbc.md).
By default, the main application `DataSource` is used, but you can provide a separate `DataSource` with the `@Tag(CamundaBpmn.class)` tag when needed.

## Configuration { #configuration }

Example of the complete configuration described by the `CamundaEngineBpmnConfig` class:

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
                        enabled = true //(20)!
                        slo = [1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000] //(21)!
                        tags = { //(22)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                    engineTelemetryEnabled = false //(23)!
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

    1.  Minimum number of permanently alive threads in [`JobExecutor`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (default: `5`).
    2.  Maximum number of threads in [`JobExecutor`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (default: `25`).
    3.  `JobExecutor` task queue size before new tasks are rejected (default: `25`).
    4.  Maximum number of jobs acquired by `JobExecutor` in one request (default: `Runtime.getRuntime().availableProcessors() * 2`).
    5.  Use [virtual threads](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html) as the `JobExecutor` base (default: `false`). When this option is enabled, pool and queue size settings are not used.
    6.  `tenant` identifier for resource [deployment](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) (default not specified, optional).
    7.  Resource [deployment](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) name (default: `KoraEngineAutoDeployment`).
    8.  Deploy only changed resources through `Camunda` duplicate filtering (default: `true`).
    9.  List of paths for finding `BPMN` / `FORM` / `DMN` resources (`required`, default not specified). Only paths with the `classpath:` prefix are supported.
    10. Delay before deploying resources to the engine (default not specified, optional).
    11. Enable parallel engine initialization (default: `true`).
    12. Validate incomplete engine statements during parallel initialization (default: `true`).
    13. `Camunda` administrator identifier (`required`, default not specified). The whole `admin` section is optional.
    14. `Camunda` administrator password (`required`, default not specified). The whole `admin` section is optional.
    15. `Camunda` administrator first name (default not specified, optional). If not specified, uppercase `id` is used.
    16. `Camunda` administrator last name (default not specified, optional). If not specified, uppercase `id` is used.
    17. `Camunda` administrator email address (default not specified, optional). If not specified, `<id>@localhost` is used.
    18. Enables module logging (default: `false`).
    19. Enables error stack trace logging (default: `true`).
    20. Enables module metrics (default: `true`).
    21. [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) configuration for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    22. Metric tags (default: `{}`).
    23. Enables built-in `Camunda` engine telemetry collection (default: `false`).
    24. Enables module tracing (default: `true`).
    25. Tracing attributes (default: `{}`).

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
              enabled: true #(20)!
              slo: [1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000] #(21)!
              tags: #(22)!
                key1: value1
                key2: value2
            engineTelemetryEnabled: false #(23)!
            tracing:
              enabled: true #(24)!
              attributes: #(25)!
                key1: value1
                key2: value2
    ```

    1.  Minimum number of permanently alive threads in [`JobExecutor`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (default: `5`).
    2.  Maximum number of threads in [`JobExecutor`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (default: `25`).
    3.  `JobExecutor` task queue size before new tasks are rejected (default: `25`).
    4.  Maximum number of jobs acquired by `JobExecutor` in one request (default: `Runtime.getRuntime().availableProcessors() * 2`).
    5.  Use [virtual threads](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html) as the `JobExecutor` base (default: `false`). When this option is enabled, pool and queue size settings are not used.
    6.  `tenant` identifier for resource [deployment](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) (default not specified, optional).
    7.  Resource [deployment](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) name (default: `KoraEngineAutoDeployment`).
    8.  Deploy only changed resources through `Camunda` duplicate filtering (default: `true`).
    9.  List of paths for finding `BPMN` / `FORM` / `DMN` resources (`required`, default not specified). Only paths with the `classpath:` prefix are supported.
    10. Delay before deploying resources to the engine (default not specified, optional).
    11. Enable parallel engine initialization (default: `true`).
    12. Validate incomplete engine statements during parallel initialization (default: `true`).
    13. `Camunda` administrator identifier (`required`, default not specified). The whole `admin` section is optional.
    14. `Camunda` administrator password (`required`, default not specified). The whole `admin` section is optional.
    15. `Camunda` administrator first name (default not specified, optional). If not specified, uppercase `id` is used.
    16. `Camunda` administrator last name (default not specified, optional). If not specified, uppercase `id` is used.
    17. `Camunda` administrator email address (default not specified, optional). If not specified, `<id>@localhost` is used.
    18. Enables module logging (default: `false`).
    19. Enables error stack trace logging (default: `true`).
    20. Enables module metrics (default: `true`).
    21. [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) configuration for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    22. Metric tags (default: `{}`).
    23. Enables built-in `Camunda` engine telemetry collection (default: `false`).
    24. Enables module tracing (default: `true`).
    25. Tracing attributes (default: `{}`).

The `deployment` section is optional: if it is not specified, the module does not automatically deploy resources.
If the section is specified, `resources` must contain at least one path.
Resources are searched recursively in `classpath`; unsupported paths without the `classpath:` prefix are skipped.

Module metrics are described in the [Metrics Reference](metrics.md#camunda-7-bpmn) section.

## Deployment { #deployment }

When the `deployment` section is present, the module automatically deploys process resources into the engine after it is created.
Resources are placed on the `classpath` (usually under `src/main/resources`) and referenced by the `resources` list:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda.engine.bpmn {
        deployment {
            resources = ["classpath:bpm"] //(1)!
        }
    }
    ```

    1.  At least one path is required when the `deployment` section is present. Only paths with the `classpath:` prefix are supported.

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      engine:
        bpmn:
          deployment:
            resources: #(1)!
              - "classpath:bpm"
    ```

    1.  At least one path is required when the `deployment` section is present. Only paths with the `classpath:` prefix are supported.

Given the following layout, the `classpath:bpm` path is scanned recursively and every supported resource under it is deployed:

```
src/main/resources/bpm/
├── approve.form
├── helloworld.bpmn
└── onboarding.bpmn
```

Deployment rules to keep in mind:

- Supported resource types are `BPMN` process models, `FORM` forms, and `DMN` decision tables.
- Only paths with the `classpath:` prefix are deployed. Any other path is skipped with a warning in the log.
- Paths are scanned **recursively**, so nested directories under the listed path are included.
- With `deployChangedOnly = true` (default) `Camunda` duplicate filtering is enabled, so only resources that changed since the previous deployment are redeployed.
- The optional `tenantId` binds the deployment to a specific `tenant`, and `delay` postpones the deployment for the configured duration after startup.
- The deployment is registered under the `name` (default `KoraEngineAutoDeployment`).
- If the whole `deployment` section is omitted, the module does not deploy any resources — you are expected to deploy them yourself through `RepositoryService`.

## Delegates { #applications }

`Camunda` can call application components as process delegates.
Regular [`JavaDelegate`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/delegation-code/) instances are registered in the context by the full class name (`canonicalName`) and by the short class name (`simpleName`).
Inside `execute(...)` you read and write process variables through `DelegateExecution`:

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

Because a `JavaDelegate` is registered by its short class name, a `serviceTask` in the `BPMN` model references it by `simpleName` through `camunda:delegateExpression`:

```xml
<bpmn:serviceTask id="Activity_0tusr5p" name="Score Customer"
                  camunda:delegateExpression="${ScoreCustomerDelegate}">
    <bpmn:incoming>Flow_score_in</bpmn:incoming>
    <bpmn:outgoing>Flow_score_out</bpmn:outgoing>
</bpmn:serviceTask>
```

Use `KoraDelegate` for an arbitrary delegate name.
The `key()` method returns `canonicalName` by default, but it can be overridden to specify the name used in `BPMN` expressions:

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

A delegate declared this way is referenced as `${myKey}` in `camunda:delegateExpression`, so the name used in the process model no longer depends on the class name.

Every delegate is wrapped by `KoraDelegateWrapperFactory` before it is called: it forks the current Kora `Context` for the delegate execution and applies module telemetry around `execute(...)`.
You can provide your own `KoraDelegateWrapperFactory` as a `@Component` to change this behavior.

## Engine Services { #engine-services }

The module provides standard `Camunda` services as dependency graph components:

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

These services can be injected into your components in the usual way.

## Starting and interacting with processes { #usage }

Inject `ProcessEngine` (or any of the engine services above) into your components to start and drive process instances.
A process is started by its `BPMN` process `id` through `RuntimeService`, and process definitions can be queried through `RepositoryService`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController("/camunda")
    public final class CamundaController {

        private final ProcessEngine processEngine;

        public CamundaController(ProcessEngine processEngine) {
            this.processEngine = processEngine;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/start/onboarding")
        public String startOnboarding() {
            String businessKey = UUID.randomUUID().toString();
            ProcessInstance instance = processEngine.getRuntimeService()
                .startProcessInstanceByKey("Onboarding", businessKey);
            return instance.getId();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController("/camunda")
    class CamundaController(private val processEngine: ProcessEngine) {

        @HttpRoute(method = HttpMethod.GET, path = "/start/onboarding")
        fun startOnboarding(): String {
            val businessKey = UUID.randomUUID().toString()
            val instance = processEngine.runtimeService
                .startProcessInstanceByKey("Onboarding", businessKey)
            return instance.id
        }
    }
    ```

A running process can be advanced from outside the engine as well: `RuntimeService.correlateMessage(...)` delivers a `BPMN` message event, and `TaskService` / `FormService` complete user tasks and submit forms:

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

## DataSource and transactions { #datasource }

The engine persists its state through a `JDBC` `DataSource`, so the [JDBC module](database-jdbc.md) is required.
By default the module reuses the main application `DataSource`, exposed to the engine under the `@Tag(CamundaBpmn.class)` tag.
To give the engine a dedicated data source, provide your own `DataSource` with that tag:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(CamundaBpmn.class)
    @Component
    public DataSource camundaDataSource(/* ... */) {
        return dataSource;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(CamundaBpmn::class)
    @Component
    fun camundaDataSource(/* ... */): DataSource {
        return dataSource
    }
    ```

The `CamundaEngineDataSource` component abstracts the engine's `DataSource` together with its `CamundaTransactionManager`.
The default implementation runs `JDBC` over the `@Tag(CamundaBpmn.class)` `DataSource`; you can override `CamundaEngineDataSource` as a `@Component` to fully control how the engine obtains connections and manages transactions.

A delegate that performs its own `JDBC` work can run it inside the engine transaction through `CamundaTransactionManager`.
`inContinueTx(...)` reuses the connection of the current engine transaction (opening a new one only if none is active), while `inNewTx(...)` always opens a new transaction; `currentConnection()` returns a handle to `commit()` / `rollback()` the current transaction:

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

## Job executor and readiness { #job-executor }

The engine runs asynchronous continuations and timers through a [`JobExecutor`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/).
The implementation is selected by the `jobExecutor.virtualThreadsEnabled` option: when `false` (default) a thread-pool executor is used and sized by `corePoolSize` / `maxPoolSize` / `queueSize` / `maxJobsPerAcquisition`; when `true` a [virtual-thread](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html) executor is used and the pool/queue sizes are ignored (see the [Configuration](#configuration) callouts).

The module automatically registers a [readiness probe](probes.md) that reports the application as `UP` only once the `JobExecutor` is active.
Until the job executor is activated the probe fails with `Camunda BPMN Engine JobExecutor is not active`, which keeps the application out of rotation while the engine is still starting.

## Admin user and Cockpit { #admin }

When the `admin` section is present, the module provisions a `Camunda` administrator user, ensures the `camunda-admin` group with full authorizations exists, and adds the user to it (see the [Configuration](#configuration) `admin` callouts).
This account is what you use to log into the `Cockpit` / `Admin` / `Tasklist` web applications served by the [Camunda 7 REST module](camunda7-rest.md).
If the `admin` section is omitted, no user is created.

## Engine Configuration { #engine-configuration }

For additional configuration, register a `ProcessEngineConfigurator` component.
The `prepare(...)` method is called before [ProcessEngine](https://docs.camunda.org/manual/7.21/user-guide/process-engine/process-engine-bootstrapping/) is created and receives `ProcessEngineConfiguration`; `setup(...)` is called after the engine is created:

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

## Plugins { #plugins }

You can register arbitrary [`ProcessEnginePlugin`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/process-engine-plugins/) by providing them as components in the Kora dependency container.
The module collects all such components and passes them to the engine configuration when creating `ProcessEngine`:

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

## Camunda version { #version }

The detected `Camunda` version is available as an injectable `CamundaVersion` component.
Its `version()` returns the version string reported by the `Camunda` package, and `isEnterprise()` returns `true` when an enterprise (`-ee`) distribution is on the classpath:

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

## Telemetry { #telemetry }

The module reports its own logging, metrics, and tracing for delegate executions through the `telemetry` configuration section.
Metrics are described in the [Metrics Reference](metrics.md#camunda-7-bpmn) section, and the `Context` fork performed by `KoraDelegateWrapperFactory` keeps this telemetry scoped to each delegate call.

Independently of the module telemetry, `telemetry.engineTelemetryEnabled` toggles `Camunda`'s own built-in telemetry collection (disabled by default).
