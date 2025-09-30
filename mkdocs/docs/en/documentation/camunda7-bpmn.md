??? warning "Experimental module"

    **Experimental** module is fully working and tested, but requires additional approbation and usage analytics, 
    for this reason, API may potentially undergo minor changes before fully stable.

Module for connecting a BPMN process workflow engine based on [Camunda 7](https://docs.camunda.org/manual/7.21/)

## Dependency

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

Requires [JDBC module](database-jdbc.md) connection.

## Configuration

Example of the complete configuration described in the `CamundaEngineBpmnConfig` class (example values or default values are specified):

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
                }
                deployment {
                    tenantId = "Camunda" //(5)!
                    name = "KoraEngineAutoDeployment" //(6)!
                    deployChangedOnly = true //(7)!
                    resources = "classpath:bpm" //(8)!
                    delay = "1m" //(9)!
                }
                parallelInitialization {
                    enabled = true //(10)!
                    validateIncompleteStatements = true //(11)!
                }
                admin {
                    id = "admin" //(12)!
                    password = "admin" //(13)!
                    firstname = "Ivan" //(14)!
                    lastname = "Ivanov" //(15)!
                    email = "admin@mail.ru" //(16)!
                }
                telemetry {
                    logging {
                        enabled = false //(17)!
                        stacktrace = true //(18)!
                    }
                    metrics {
                        enabled = true //(19)!
                        slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(20)!
                    }
                    engineTelemetryEnabled = false //(21)!
                    tracing {
                        enabled = true //(22)!
                    }
                }
            }
        }
    }
    ```

    1. Minimum number of live threads in [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    2. Maximum number of threads in [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    3. Size of the task queue before tasks are thrown out of the [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) execution queue
    4. Maximum number of tasks in the [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) execution (default is the number of CPU cores multiplied by 2)
    5. Indeterminator tenant [load](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) resources (default is none)
    6. Name of [load](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) resources
    7. Flag that says that only modified resources should be loaded
    8. Paths to find BPMN/FORM/DMN resources that will be loaded into the engine after startup
    9. Delay before deploying new resources to engine
    10. Whether to enable parallel loading, which slightly improves the engine startup speed
    11. Whether to check for incomplete engine configuration requests
    12. Camunda administrator identifier (optional)
    13. Camunda Administrator Password (optional)
    14. Camunda Administrator Name (optional)
    15. Last name of Camunda administrator (optional)
    16. Email of the Camunda administrator (optional)
    17. Enables module logging (default is `false`)
    18. Enables error stack logging (default is `true`)
    19. Enables module metrics (default `true`)
    20. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    21. Enables collection of engine metrics/telemetry (default is `false`)
    22. Enables module tracing (default `true`)

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
          deployment:
            tenantId: "Camunda" #(5)!
            name: "KoraEngineAutoDeployment" #(6)!
            deployChangedOnly: true #(7)!
            resources: "classpath:bpm" #(8)!
            delay: "1m" #(9)!
          parallelInitialization:
            enabled: true #(10)!
            validateIncompleteStatements: true #(11)!
          admin:
            id: "admin" #(12)!
            password: "admin" #(13)!
            firstname: "Ivan" #(14)!
            lastname: "Ivanov" #(15)!
            email: "admin@mail.ru" #(16)!
          telemetry:
            logging:
              enabled: false #(17)!
              stacktrace: true #(18)!
            metrics:
              enabled: true #(19)!
              slo: [ 0, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(20)!
            engineTelemetryEnabled: false #(21)!
            tracing:
              enabled: true #(22)!
    ```

    1. Minimum number of live threads in [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    2. Maximum number of threads in [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    3. Size of the task queue before tasks are thrown out of the [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) execution queue
    4. Maximum number of tasks in the [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) execution (default is the number of CPU cores multiplied by 2)
    5. Indeterminator tenant [load](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) resources (default is none)
    6. Name of [load](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) resources
    7. Flag that says that only modified resources should be loaded
    8. Paths to find BPMN/FORM/DMN resources that will be loaded into the engine after startup
    9. Delay before deploying new resources to engine
    10. Whether to enable parallel loading, which slightly improves the engine startup speed
    11. Whether to check for incomplete engine configuration requests
    12. Camunda administrator identifier (optional)
    13. Camunda Administrator Password (optional)
    14. Camunda Administrator Name (optional)
    15. Last name of Camunda administrator (optional)
    16. Email of the Camunda administrator (optional)
    17. Enables module logging (default is `false`)
    18. Enables error stack logging (default is `true`)
    19. Enables module metrics (default `true`)
    20. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    21. Enables collection of engine metrics/telemetry (default is `false`)
    22. Enables module tracing (default `true`)

## Applications

You can register in Camunda user [JavaDelegate](https://docs.camunda.org/manual/7.21/user-guide/process-engine/delegation-code/)
which will be registered in the context by their full class name (`canonicalName`) and by their simplified class name (`simpleName`):

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

        fun execute(delegateExecution: DelegateExecution) {

        }
    }
    ```

You can also register specialized `KoraDelegate`, which allow, in addition to standard naming, to register an executor with an arbitrary name in context via the `key()` method:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SimpleDelegate implements KoraDelegate {

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

        fun key() = "myKey"

        fun execute(delegateExecution: DelegateExecution) {

        }
    }
    ```

## Engine configuration

It is possible to register user `ProcessEngineConfigurator` that allow configuring [ProcessEngine](https://docs.camunda.org/manual/7.21/user-guide/process-engine/process-engine-bootstrapping/):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SimpleProcessEngineConfigurator implements ProcessEngineConfigurator {

        @Override
        public void setup(ProcessEngine engine) {

        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SimpleProcessEngineConfigurator : ProcessEngineConfigurator {

        fun setup(engine: ProcessEngine) {
        
        }
    }
    ```

## Plugins

You can register arbitrary [Plugin](https://docs.camunda.org/manual/7.21/user-guide/process-engine/process-engine-plugins/) by providing them as components in a dependency container.
