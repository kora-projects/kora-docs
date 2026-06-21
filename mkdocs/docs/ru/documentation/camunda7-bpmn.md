---
description: "Explains Kora Camunda 7 BPMN embedded process engine integration, deployment, worker components, configuration, and telemetry. Use when working with CamundaEngineBpmnModule, CamundaEngineConfig, ProcessEngine, JavaDelegate, @Component, Metrics Reference."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Camunda 7 BPMN embedded process engine integration, deployment, worker components, configuration, and telemetry; key triggers include CamundaEngineBpmnModule, CamundaEngineConfig, ProcessEngine, JavaDelegate, @Component, Metrics Reference."
---

??? warning "Экспериментальный модуль"

    **Экспериментальный** модуль является полностью рабочим и протестированным, но требует дополнительной апробации и аналитики по использованию.
    Поэтому `API` может получить незначительные изменения до полной готовности.

Модуль подключает встроенный движок [Camunda 7](https://docs.camunda.org/manual/7.21/) для выполнения `BPMN`-процессов внутри приложения Kora.
Он создает и настраивает `ProcessEngine`, связывает его с `JDBC`-источником данных, регистрирует исполнителей из графа приложения, загружает `BPMN` / `FORM` / `DMN`-ресурсы из `classpath` и добавляет телеметрию выполнения.

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:camunda-engine-bpmn"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CamundaEngineBpmnModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:camunda-engine-bpmn")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CamundaEngineBpmnModule
    ```

Модуль требует подключения [JDBC-модуля](database-jdbc.md).
По умолчанию используется основной `DataSource` приложения, но при необходимости можно предоставить отдельный `DataSource` с тегом `@Tag(CamundaBpmn.class)`.

## Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `CamundaEngineBpmnConfig`:

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

    1.  Минимальное количество постоянно живых потоков в [`JobExecutor`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (по умолчанию: `5`).
    2.  Максимальное количество потоков в [`JobExecutor`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (по умолчанию: `25`).
    3.  Размер очереди задач `JobExecutor` перед отклонением новых задач (по умолчанию: `25`).
    4.  Максимальное количество задач, получаемых `JobExecutor` за один запрос (по умолчанию: `Runtime.getRuntime().availableProcessors() * 2`).
    5.  Использовать [виртуальные потоки](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html) как основу `JobExecutor` (по умолчанию: `false`). При включении этой опции настройки размера пула и очереди не используются.
    6.  Идентификатор `tenant` для [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию не указано, необязательно).
    7.  Имя [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию: `KoraEngineAutoDeployment`).
    8.  Загружать только измененные ресурсы через фильтрацию дублей `Camunda` (по умолчанию: `true`).
    9.  Список путей для поиска `BPMN` / `FORM` / `DMN`-ресурсов (`обязательная`, по умолчанию не указано). Поддерживаются только пути с префиксом `classpath:`.
    10. Задержка перед загрузкой ресурсов в движок (по умолчанию не указано, необязательно).
    11. Включить параллельную инициализацию движка (по умолчанию: `true`).
    12. Проверять незавершенные настройки движка при параллельной инициализации (по умолчанию: `true`).
    13. Идентификатор администратора `Camunda` (`обязательная`, по умолчанию не указано). Секция `admin` целиком необязательна.
    14. Пароль администратора `Camunda` (`обязательная`, по умолчанию не указано). Секция `admin` целиком необязательна.
    15. Имя администратора `Camunda` (по умолчанию не указано, необязательно). Если не указано, используется `id` в верхнем регистре.
    16. Фамилия администратора `Camunda` (по умолчанию не указано, необязательно). Если не указано, используется `id` в верхнем регистре.
    17. Адрес электронной почты администратора `Camunda` (по умолчанию не указано, необязательно). Если не указано, используется `<id>@localhost`.
    18. Включает логирование модуля (по умолчанию: `false`).
    19. Включает логирование стека ошибки (по умолчанию: `true`).
    20. Включает метрики модуля (по умолчанию: `true`).
    21. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    22. Теги метрик (по умолчанию: `{}`).
    23. Включает сбор встроенной телеметрии движка `Camunda` (по умолчанию: `false`).
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

    1.  Минимальное количество постоянно живых потоков в [`JobExecutor`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (по умолчанию: `5`).
    2.  Максимальное количество потоков в [`JobExecutor`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/the-job-executor/) (по умолчанию: `25`).
    3.  Размер очереди задач `JobExecutor` перед отклонением новых задач (по умолчанию: `25`).
    4.  Максимальное количество задач, получаемых `JobExecutor` за один запрос (по умолчанию: `Runtime.getRuntime().availableProcessors() * 2`).
    5.  Использовать [виртуальные потоки](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html) как основу `JobExecutor` (по умолчанию: `false`). При включении этой опции настройки размера пула и очереди не используются.
    6.  Идентификатор `tenant` для [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию не указано, необязательно).
    7.  Имя [загрузки](https://docs.camunda.org/javadoc/camunda-bpm-platform/7.21/org/camunda/bpm/engine/repository/DeploymentBuilder.html) ресурсов (по умолчанию: `KoraEngineAutoDeployment`).
    8.  Загружать только измененные ресурсы через фильтрацию дублей `Camunda` (по умолчанию: `true`).
    9.  Список путей для поиска `BPMN` / `FORM` / `DMN`-ресурсов (`обязательная`, по умолчанию не указано). Поддерживаются только пути с префиксом `classpath:`.
    10. Задержка перед загрузкой ресурсов в движок (по умолчанию не указано, необязательно).
    11. Включить параллельную инициализацию движка (по умолчанию: `true`).
    12. Проверять незавершенные настройки движка при параллельной инициализации (по умолчанию: `true`).
    13. Идентификатор администратора `Camunda` (`обязательная`, по умолчанию не указано). Секция `admin` целиком необязательна.
    14. Пароль администратора `Camunda` (`обязательная`, по умолчанию не указано). Секция `admin` целиком необязательна.
    15. Имя администратора `Camunda` (по умолчанию не указано, необязательно). Если не указано, используется `id` в верхнем регистре.
    16. Фамилия администратора `Camunda` (по умолчанию не указано, необязательно). Если не указано, используется `id` в верхнем регистре.
    17. Адрес электронной почты администратора `Camunda` (по умолчанию не указано, необязательно). Если не указано, используется `<id>@localhost`.
    18. Включает логирование модуля (по умолчанию: `false`).
    19. Включает логирование стека ошибки (по умолчанию: `true`).
    20. Включает метрики модуля (по умолчанию: `true`).
    21. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    22. Теги метрик (по умолчанию: `{}`).
    23. Включает сбор встроенной телеметрии движка `Camunda` (по умолчанию: `false`).
    24. Включает трассировку модуля (по умолчанию: `true`).
    25. Атрибуты трассировки (по умолчанию: `{}`).

Секция `deployment` необязательна: если она не задана, модуль не выполняет автоматическую загрузку ресурсов.
Если секция задана, `resources` должен содержать хотя бы один путь.
Ресурсы ищутся рекурсивно в `classpath`; неподдерживаемые пути без префикса `classpath:` пропускаются.

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#camunda-7-bpmn).

## Исполнители { #applications }

`Camunda` может вызывать компоненты приложения как исполнителей процесса.
Обычные [`JavaDelegate`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/delegation-code/) регистрируются в контексте по полному имени класса (`canonicalName`) и по короткому имени класса (`simpleName`):

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

Для произвольного имени исполнителя можно использовать `KoraDelegate`.
Метод `key()` по умолчанию возвращает `canonicalName`, но его можно переопределить и указать имя, которое будет использоваться в `BPMN`-выражениях:

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

Исполнители оборачиваются `KoraDelegateWrapperFactory`, поэтому для их вызовов применяется контекст Kora и телеметрия модуля.

## Сервисы движка { #engine-services }

Модуль предоставляет стандартные сервисы `Camunda` как компоненты графа зависимостей:

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

Эти сервисы можно внедрять в свои компоненты обычным способом.

## Донастройка { #engine-configuration }

Для дополнительной настройки можно зарегистрировать компонент `ProcessEngineConfigurator`.
Метод `prepare(...)` вызывается до создания [ProcessEngine](https://docs.camunda.org/manual/7.21/user-guide/process-engine/process-engine-bootstrapping/) и получает `ProcessEngineConfiguration`, а `setup(...)` вызывается после создания движка:

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

## Плагины { #plugins }

Можно регистрировать произвольные [`ProcessEnginePlugin`](https://docs.camunda.org/manual/7.21/user-guide/process-engine/process-engine-plugins/), предоставляя их как компоненты в контейнер зависимостей Kora.
Модуль передает все такие компоненты в конфигурацию движка при создании `ProcessEngine`.
