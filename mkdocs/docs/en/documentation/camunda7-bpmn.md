---
description: "Explains Kora Camunda 7 BPMN embedded process engine integration, deployment, worker components, configuration, and telemetry. Use when working with CamundaEngineBpmnModule, CamundaEngineConfig, ProcessEngine, JavaDelegate, @Component, Metrics Reference."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Camunda 7 BPMN embedded process engine integration, deployment, worker components, configuration, and telemetry; key triggers include CamundaEngineBpmnModule, CamundaEngineConfig, ProcessEngine, JavaDelegate, @Component, Metrics Reference."
---

??? warning "Experimental module"

    The **experimental** module is fully working and tested, but requires additional usage validation and analysis.
    Therefore, the `API` may receive minor changes before full readiness.

The module connects an embedded [Camunda 7](https://docs.camunda.org/manual/7.21/) engine for executing `BPMN` processes inside a Kora application.
It creates and configures `ProcessEngine`, connects it to a `JDBC` data source, registers delegates from the application graph, deploys `BPMN` / `FORM` / `DMN` resources from `classpath`, and adds execution telemetry.

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

## Delegates { #applications }

`Camunda` can call application components as process delegates.
Regular [`JavaDelegate`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/delegation-code/) instances are registered in the context by the full class name (`canonicalName`) and by the short class name (`simpleName`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SimpleDelegate implements JavaDelegate {

        @Override
        public void execute(DelegateExecution delegateExecution) throws Exception {

        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SimpleKoraDelegate : JavaDelegate {

        override fun execute(delegateExecution: DelegateExecution) {

        }
    }
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

Delegates are wrapped by `KoraDelegateWrapperFactory`, so Kora context and module telemetry are applied to their calls.

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
The module passes all such components to the engine configuration when creating `ProcessEngine`.
