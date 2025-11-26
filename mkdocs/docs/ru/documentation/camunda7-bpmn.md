??? warning "Экспериментальный модуль"

    **Эксперементальный** модуль является полностью рабочим и протестированным, но требует дополнительной апробации и аналитики по использованию, 
    по этой причине API может потенциально притерпеть незначительные изменения перед полной готовностью.

Модуль для подключения оркестратора BPMN процессов на основе [Camunda 7](https://docs.camunda.org/manual/7.21/)

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:camunda-engine-bpmn"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CamundaEngineBpmnModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
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
                    virtualThreadsEnabled = true //(5)!
                }
                deployment {
                    tenantId = "Camunda" //(6)!
                    name = "KoraEngineAutoDeployment" //(7)!
                    deployChangedOnly = true //(8)!
                    resources = "classpath:bpm" //(9)!
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
                        slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(21)!
                    }
                    engineTelemetryEnabled = false //(22)!
                    tracing {
                        enabled = true //(23)!
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
    5.  Использовать ли [виртуальные потоки](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html) в как основу JobExecutor, все предыдущие опции не имеют значения в случае включения виртуальных потоков
    6.  Индетефикатор тенант [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию отсутсвует)
    7.  Имя [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов
    8.  Флаг который говорит что следует загружать только измененные ресурсы
    9.  Пути для поиска BPMN/FORM/DMN ресурсов которые будут загружены в оркестратор после запуска
    10.  Задержда перед тем как начать загрузку новых ресурсов в оркестратор
    11.  Включить ли параллельную загрузку которая слегка улучшает скорость запуска оркестратора
    12.  Проверять ли не полные запросы настройки оркестратора
    13.  Индетификатор администратора Camunda (необязательный)
    14.  Пароль администратора Camunda (необязательный)
    15.  Имя администратора Camunda (необязательный)
    16.  Фамилия администратора Camunda (необязательный)
    17.  Email администратора Camunda (необязательный)
    18.  Включает логгирование модуля (по умолчанию `false`)
    19.  Включает логгирование стека ошибки (по умолчанию `true`)
    20.  Включает метрики модуля (по умолчанию `true`)
    21.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    22.  Включает сбор метрик/телеметрии оркестратора (по умолчанию `false`)
    23.  Включает трассировку модуля (по умолчанию `true`)

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
            virtualThreadsEnabled: true #(5)!
          deployment:
            tenantId: "Camunda" #(6)!
            name: "KoraEngineAutoDeployment" #(7)!
            deployChangedOnly: true #(8)!
            resources: "classpath:bpm" #(9)!
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
              slo: [ 0, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(21)!
            engineTelemetryEnabled: false #(22)!
            tracing:
              enabled: true #(23)!
    ```

    1.  Минимальное количество живых потоков в [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    2.  Максимальное кличество потоков в [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    3.  Размер очереди задачи перед тем как задачи будут выброшены из очереди выполнения [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/)
    4.  Максимальное количество задач в выполнении [JobExecutor](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (по умолчанию равно кол-во ядер процессора умноженных на 2)
    5.  Использовать ли [виртуальные потоки](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html) в как основу JobExecutor, все предыдущие опции не имеют значения в случае включения виртуальных потоков
    6.  Индетефикатор тенант [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию отсутсвует)
    7.  Имя [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов
    8.  Флаг который говорит что следует загружать только измененные ресурсы
    9.  Пути для поиска BPMN/FORM/DMN ресурсов которые будут загружены в оркестратор после запуска
    10.  Задержда перед тем как начать загрузку новых ресурсов в оркестратор
    11.  Включить ли параллельную загрузку которая слегка улучшает скорость запуска оркестратора
    12.  Проверять ли не полные запросы настройки оркестратора
    13.  Индетификатор администратора Camunda (необязательный)
    14.  Пароль администратора Camunda (необязательный)
    15.  Имя администратора Camunda (необязательный)
    16.  Фамилия администратора Camunda (необязательный)
    17.  Email администратора Camunda (необязательный)
    18.  Включает логгирование модуля (по умолчанию `false`)
    19.  Включает логгирование стека ошибки (по умолчанию `true`)
    20.  Включает метрики модуля (по умолчанию `true`)
    21.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    22.  Включает сбор метрик/телеметрии оркестратора (по умолчанию `false`)
    23.  Включает трассировку модуля (по умолчанию `true`)

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
