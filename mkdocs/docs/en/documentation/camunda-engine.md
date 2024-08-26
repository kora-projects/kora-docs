Module for connecting a BPMN process interpreter based on [Camunda 7](https://docs.camunda.org/manual/7.21/)

## Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:camunda-engine"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CamundaEngineModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:camunda-engine")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : CamundaEngineModule
    ```

Requires [JDBC module](database-jdbc.md) connection.

## Configuration

Example of the complete configuration described in the `CamundaEngineConfig` class (example values or default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda {
        engine {
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
            }
            parallelInitialization {
                enabled = true //(9)!
                validateIncompleteStatements = true //(10)!
            }
            licensePath = "camunda-licence.txt" //(11)!
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
    ```

    1. Minimum number of live threads in [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    2. Maximum number of threads in [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    3. Size of the task queue before tasks are thrown out of the [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) execution queue
    4. Maximum number of tasks in the [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) execution (default is the number of CPU cores multiplied by 2)
    5. Indeterminator tenant [load](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) resources (default is none)
    6. Name of [load](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) resources
    7. Flag that says that only modified resources should be loaded
    8. Paths to find BPMN/FORM/DMN resources that will be loaded into the engine after startup
    9. Whether to enable parallel loading, which slightly improves the engine startup speed
    10. Whether to check for incomplete engine configuration requests
    11. Path for the license file [Camunda 7](https://docs.camunda.org/manual/7.21/user-guide/license-use/)
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
        jobExecutor:
          corePoolSize = 5 #(1)!
          maxPoolSize = 25 #(2)!
          queueSize = 25 #(3)!
          maxJobsPerAcquisition = 2 #(4)!
        deployment:
          tenantId = "Camunda" #(5)!
          name = "KoraEngineAutoDeployment" #(6)!
          deployChangedOnly = true #(7)!
          resources = "classpath:bpm" #(8)!
        parallelInitialization:
          enabled = true #(9)!
          validateIncompleteStatements = true #(10)!
        licensePath = "camunda-licence.txt" #(11)!
        admin:
          id = "admin" #(12)!
          password = "admin" #(13)!
          firstname = "Ivan" #(14)!
          lastname = "Ivanov" #(15)!
          email = "admin@mail.ru" #(16)!
        telemetry:
          logging:
            enabled = false #(17)!
            stacktrace = true #(18)!
          metrics:
            enabled = true #(19)!
            slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(20)!
          engineTelemetryEnabled = false #(21)!
          tracing:
            enabled = true #(22)!
    ```

    1. Minimum number of live threads in [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    2. Maximum number of threads in [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    3. Size of the task queue before tasks are thrown out of the [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) execution queue
    4. Maximum number of tasks in the [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) execution (default is the number of CPU cores multiplied by 2)
    5. Indeterminator tenant [load](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) resources (default is none)
    6. Name of [load](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) resources
    7. Flag that says that only modified resources should be loaded
    8. Paths to find BPMN/FORM/DMN resources that will be loaded into the engine after startup
    9. Whether to enable parallel loading, which slightly improves the engine startup speed
    10. Whether to check for incomplete engine configuration requests
    11. Path for the license file [Camunda 7](https://docs.camunda.org/manual/7.21/user-guide/license-use/)
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

You can register with Camunda as your own [JavaDelegate](https://docs.camunda.org/manual/7.21/user-guide/process-engine/delegation-code/):

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

## Engine Configuration

It is possible to register arbitrary `ProcessEngineConfigurator` that allow up to [ProcessEngine](https://docs.camunda.org/manual/7.21/user-guide/process-engine/process-engine-bootstrapping/) configuration:

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

### Plugins

You can register arbitrary [Plugin](https://docs.camunda.org/manual/7.21/user-guide/process-engine/process-engine-plugins/) by providing them as components in a dependency container.
