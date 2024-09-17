??? warning "Экспериментальный модуль"

    **Эксперементальный** модуль является полностью рабочим и протестированным, но не гарантирует полностью стабилизированный API и может
    притерпеть какие либо незначительные изменения перед полной готовностью.

Модуль для подключения интерпретатора BPMN процессов на основе [Camunda 7](https://docs.camunda.org/manual/7.21/)

## Подключение

===! ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:camunda-engine-bpmn"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CamundaEngineBpmnModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:camunda-engine-bpmn")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CamundaEngineBpmnModule
    ```

Требует подключения [JDBC модуля](database-jdbc.md).

## Конфигурация

Пример полной конфигурации, описанной в классе `CamundaEngineBpmnConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  Минимальное количество живых потоков в [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    2.  Максимальное кличество потоков в [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    3.  Размер очереди задачи перед тем как задачи будут выброшены из очереди выполнения [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    4.  Максимальное количество задач в выполнении [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (по умолчанию равно кол-во ядер процессора умноженных на 2)
    5.  Индетефикатор тенант [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию отсутсвует)
    6.  Имя [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов
    7.  Флаг который говорит что следует загружать только измененные ресурсы
    8.  Пути для поиска BPMN/FORM/DMN ресурсов которые будут загружены в движок после запуска
    9.  Задержда перед тем как начать загрузку новых ресурсов в движок
    10.  Включить ли параллельную загрузку которая слегка улучшает скорость запуска движка
    11.  Проверять ли не полные запросы настройки движка
    12.  Индетификатор администратора Camunda (необязательный)
    13.  Пароль администратора Camunda (необязательный)
    14.  Имя администратора Camunda (необязательный)
    15.  Фамилия администратора Camunda (необязательный)
    16.  Email администратора Camunda (необязательный)
    17.  Включает логгирование модуля (по умолчанию `false`)
    18.  Включает логгирование стека ошибки (по умолчанию `true`)
    19.  Включает метрики модуля (по умолчанию `true`)
    20.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    21.  Включает сбор метрик/телеметрии движка (по умолчанию `false`)
    22.  Включает трассировку модуля (по умолчанию `true`)

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

    1.  Минимальное количество живых потоков в [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    2.  Максимальное кличество потоков в [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    3.  Размер очереди задачи перед тем как задачи будут выброшены из очереди выполнения [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    4.  Максимальное количество задач в выполнении [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (по умолчанию равно кол-во ядер процессора умноженных на 2)
    5.  Индетефикатор тенант [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию отсутсвует)
    6.  Имя [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов
    7.  Флаг который говорит что следует загружать только измененные ресурсы
    8.  Пути для поиска BPMN/FORM/DMN ресурсов которые будут загружены в движок после запуска
    9.  Задержда перед тем как начать загрузку новых ресурсов в движок
    10.  Включить ли параллельную загрузку которая слегка улучшает скорость запуска движка
    11.  Проверять ли не полные запросы настройки движка
    12.  Индетификатор администратора Camunda (необязательный)
    13.  Пароль администратора Camunda (необязательный)
    14.  Имя администратора Camunda (необязательный)
    15.  Фамилия администратора Camunda (необязательный)
    16.  Email администратора Camunda (необязательный)
    17.  Включает логгирование модуля (по умолчанию `false`)
    18.  Включает логгирование стека ошибки (по умолчанию `true`)
    19.  Включает метрики модуля (по умолчанию `true`)
    20.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    21.  Включает сбор метрик/телеметрии движка (по умолчанию `false`)
    22.  Включает трассировку модуля (по умолчанию `true`)

## Исполнители

Регистрировать в Camunda можно как свои [JavaDelegate](https://docs.camunda.org/manual/7.21/user-guide/process-engine/delegation-code/),
которые будут зарегистрированы в контексте по своему полному имени класса (`canonicalName`) так и по упрощенному имени класса (`simpleName`):

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

Так и специализированные `KoraDelegate`, которые позволяют помимо стандартных именований регистрировать исполнителя с помощью произвольного имени в контексте по средствам метода `key()`:

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

## Донастройка

Можно регистрировать произвольные `ProcessEngineConfigurator` которые позволяют донастраивать [ProcessEngine](https://docs.camunda.org/manual/7.21/user-guide/process-engine/process-engine-bootstrapping/):

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

## Плагины

Можно регистрировать произвольные [Plugin](https://docs.camunda.org/manual/7.21/user-guide/process-engine/process-engine-plugins/) предоставляя их как компоненты в контейнер зависимостей.
