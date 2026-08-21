---
description: "Explains Kora scheduling for native and Quartz schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, shutdown, and concurrency controls. Use when working with @ScheduleAtFixedRate, @ScheduleWithFixedDelay, @ScheduleOnce, @ScheduleWithCron, @ScheduleWithTrigger, @DisallowConcurrentExecution, SchedulingModule, QuartzModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora scheduling for native and Quartz schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, shutdown, and concurrency controls; key triggers include @ScheduleAtFixedRate, @ScheduleWithFixedDelay, @ScheduleOnce, @ScheduleWithCron, @ScheduleWithTrigger, @DisallowConcurrentExecution, SchedulingModule, QuartzModule."
---

Модуль планирования Kora позволяет запускать методы приложения по расписанию в декларативном стиле через аннотации.
Во время компиляции Kora генерирует компоненты задач и связывает их с выбранным механизмом планирования.

Доступны два варианта: собственный планировщик на основе `ScheduledExecutorService` из `JDK` и планировщик на основе `Quartz`.
Собственный вариант подходит для простых периодических задач внутри одного приложения, а `Quartz` полезен для `cron`-выражений, пользовательских экземпляров `Trigger` и дополнительных правил выполнения задач.

## Собственный планировщик { #native }

Собственный планировщик использует стандартный [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html), который поставляется вместе с `JDK`.

Для создания задач через аспекты используются специальные аннотации, соответствующие методам `ScheduledExecutorService`.
Параметры аннотаций совпадают с параметрами методов `scheduleAtFixedRate`, `scheduleWithFixedDelay` и `schedule`.

У всех аннотаций есть параметр `config`.
Если он указан, значения параметров берутся из конфигурации по этому пути и имеют приоритет над значениями из аннотации.
Конфигурация конкретной задачи также может содержать секцию `telemetry`, значения которой переопределяют общую телеметрию планировщика для этой задачи.

Методы, выполняемые по расписанию, должны удовлетворять следующим требованиям:

- Класс, в котором объявлен метод, должен быть компонентом в [графе зависимостей](container.md), например помеченным аннотацией `@Component`.
- Метод собственного планировщика не должен иметь аргументов (планировщик `Quartz` дополнительно допускает необязательный аргумент [JobExecutionContext](#job-context)).
- Возвращаемое значение метода игнорируется.
- В `Kotlin` метод не должен быть `suspend`-функцией.

!!! warning "Интервал обязателен"

    `@ScheduleAtFixedRate` требует `period`, а `@ScheduleWithFixedDelay` требует `delay`.
    Если не задан ни атрибут аннотации (его значение по умолчанию равно `0`), ни путь `config`, предоставляющий значение,
    компиляция завершается ошибкой `Either period() or config() annotation parameter must be provided`.

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:scheduling-jdk"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends SchedulingJdkModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("ru.tinkoff.kora:scheduling-jdk")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : SchedulingJdkModule
    ```

### Конфигурация { #configuration }

Полный пример конфигурации, описываемой классом `ScheduledExecutorServiceConfig`, со значениями по умолчанию:

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        threads = 2 //(1)!
        shutdownWait = "30s" //(2)!
        telemetry {
            logging {
                enabled = false //(3)!
            }
            metrics {
                enabled = true //(4)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(5)!
                tags = { // (6)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(7)!
                attributes = { // (8)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1. Максимальное количество потоков в [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) (по умолчанию: `2`)
    2. Время ожидания завершения задач перед остановкой планировщика при [плавной остановке](container.md#component-lifecycle) (по умолчанию: `30s`)
    3. Включает логирование модуля (по умолчанию: `false`)
    4. Включает метрики модуля (по умолчанию: `true`)
    5. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Настраивает теги метрик (по умолчанию: `{}`)
    7. Включает трассировку модуля (по умолчанию: `true`)
    8. Настраивает атрибуты трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      threads: 2 #(1)!
      shutdownWait: "30s" #(2)!
      telemetry:
        logging:
          enabled: false #(3)!
        metrics:
          enabled: true #(4)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(5)!
          tags: #(6)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(7)!
          attributes: #(8)!
            key1: value1
            key2: value2
    ```

    1. Максимальное количество потоков в [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) (по умолчанию: `2`)
    2. Время ожидания завершения задач перед остановкой планировщика при [плавной остановке](container.md#component-lifecycle) (по умолчанию: `30s`)
    3. Включает логирование модуля (по умолчанию: `false`)
    4. Включает метрики модуля (по умолчанию: `true`)
    5. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Настраивает теги метрик (по умолчанию: `{}`)
    7. Включает трассировку модуля (по умолчанию: `true`)
    8. Настраивает атрибуты трассировки (по умолчанию: `{}`)

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#scheduling).

Конфигурация конкретной задачи также может содержать собственную секцию `telemetry`, которая переопределяет общую для планировщика `scheduling.telemetry` только для этой задачи.
Незаданные значения берутся из общей конфигурации, поэтому достаточно указать только то, что должно отличаться:

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        jobs {
            fix-rate {
                period = "50ms"
                telemetry {
                    logging.enabled = true //(1)!
                    metrics.enabled = false //(2)!
                }
            }
        }
    }
    ```

    1. Переопределяет `scheduling.telemetry.logging.enabled` только для этой задачи
    2. Переопределяет `scheduling.telemetry.metrics.enabled` только для этой задачи

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        fix-rate:
          period: "50ms"
          telemetry:
            logging:
              enabled: true #(1)!
            metrics:
              enabled: false #(2)!
    ```

    1. Переопределяет `scheduling.telemetry.logging.enabled` только для этой задачи
    2. Переопределяет `scheduling.telemetry.metrics.enabled` только для этой задачи

Наблюдаемость задач по расписанию также можно настроить в коде, зарегистрировав компонент, реализующий
`SchedulingLoggerFactory`, `SchedulingMetricsFactory`, `SchedulingTracerFactory` или целиком `SchedulingTelemetryFactory`.

### Фиксированная частота { #fixed-rate }

Планирование с запуском задач через фиксированный интервал времени независимо от того, завершилось ли предыдущее выполнение.
Это может приводить к одновременному выполнению нескольких задач.

Например, если период равен 10 секундам, а каждое выполнение задачи занимает 5 секунд,
то следующая задача запускается через 5 секунд после завершения предыдущей.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleAtFixedRate(initialDelay = 50, period = 50, unit = ChronoUnit.MILLIS)
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleAtFixedRate(initialDelay = 50, period = 50, unit = ChronoUnit.MILLIS)
        fun schedule() {
            // do something
        }
    }
    ```

#### Конфигурация { #configuration-2 }

Параметры можно передавать через конфигурацию; конфигурация имеет приоритет над значениями из аннотации.
Путь `config` произвольный, но по соглашению вкладывается в секцию `scheduling`, чтобы параметры задачи
и её `telemetry` находились вместе (как в [проекте-примере](https://github.com/kora-projects/kora-examples), `scheduling.jobs.fix-rate`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleAtFixedRate(config = "scheduling.jobs.fix-rate")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleAtFixedRate(config = "scheduling.jobs.fix-rate")
        fun schedule() {
            // do something
        }
    }
    ```

Пример файла конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        jobs {
            fix-rate {
                initialDelay = "50ms" //(1)!
                period = "50ms" //(2)!
            }
        }
    }
    ```

    1. Начальная задержка перед первой задачей (по умолчанию: `0ms`)
    2. Периодический интервал между задачами (`обязательный`, без значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        fix-rate:
          initialDelay: "50ms" #(1)!
          period: "50ms" #(2)!
    ```

    1. Начальная задержка перед первой задачей (по умолчанию: `0ms`)
    2. Периодический интервал между задачами (`обязательный`, без значения по умолчанию)

### Фиксированная задержка { #fixed-delay }

Планировщик выдерживает фиксированный интервал времени от момента окончания предыдущего выполнения задачи.
Несколько выполнений одной и той же задачи не будут происходить одновременно.

Не имеет значения, сколько длится текущее выполнение:
следующая задача запускается после того, как предыдущая задача завершилась и прошла настроенная задержка.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithFixedDelay(initialDelay = 50, delay = 50, unit = ChronoUnit.MILLIS)
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleWithFixedDelay(initialDelay = 50, delay = 50, unit = ChronoUnit.MILLIS)
        fun schedule() {
            // do something
        }
    }
    ```

#### Конфигурация { #configuration-3 }

Параметры можно передавать через конфигурацию; она имеет приоритет над значениями из аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithFixedDelay(config = "scheduling.jobs.fix-delay")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleWithFixedDelay(config = "scheduling.jobs.fix-delay")
        fun schedule() {
            // do something
        }
    }
    ```

Пример файла конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        jobs {
            fix-delay {
                initialDelay = "50ms" //(1)!
                delay = "50ms" //(2)!
            }
        }
    }
    ```

    1. Начальная задержка перед первой задачей (по умолчанию: `0ms`)
    2. Периодическая задержка между задачами (`обязательный`, без значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        fix-delay:
          initialDelay: "50ms" #(1)!
          delay: "50ms" #(2)!
    ```

    1. Начальная задержка перед первой задачей (по умолчанию: `0ms`)
    2. Периодическая задержка между задачами (`обязательный`, без значения по умолчанию)

### Однократно { #once }

Запускает задачу один раз через настроенный интервал времени.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleOnce(delay = 50, unit = ChronoUnit.MILLIS)
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleOnce(delay = 50, unit = ChronoUnit.MILLIS)
        fun schedule() {
            // do something
        }
    }
    ```

#### Конфигурация { #configuration-4 }

Параметры можно передавать через конфигурацию; она имеет приоритет над значениями из аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleOnce(config = "scheduling.jobs.once")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleOnce(config = "scheduling.jobs.once")
        fun schedule() {
            // do something
        }
    }
    ```

Пример файла конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        jobs {
            once {
                delay = "50ms" //(1)!
            }
        }
    }
    ```

    1. Задержка перед задачей (`обязательный`, без значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        once:
          delay: "50ms" #(1)!
    ```

    1. Задержка перед задачей (`обязательный`, без значения по умолчанию)

### Плавная остановка { #graceful-shutdown }

Во время [плавной остановки](container.md#component-lifecycle) собственный планировщик ожидает завершения задач в течение `scheduling.shutdownWait`.
Если задачу нужно остановить раньше, проверяйте [Thread.currentThread().isInterrupted()](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#isInterrupted--) и останавливайте работу вручную.

### Программное планирование { #programmatic }

Для планирования задач в императивном стиле можно внедрить компонент `JdkSchedulingExecutor`.
Он оборачивает тот же `ScheduledExecutorService`, что и аннотации, и предоставляет методы `scheduleAtFixedRate`, `scheduleWithFixedDelay` и `schedule`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        private final JdkSchedulingExecutor executor;

        public SomeService(JdkSchedulingExecutor executor) {
            this.executor = executor;
        }

        public void start() {
            executor.scheduleAtFixedRate(() -> {
                // do something
            }, 50, 50, TimeUnit.MILLISECONDS);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val executor: JdkSchedulingExecutor) {

        fun start() {
            executor.scheduleAtFixedRate({
                // do something
            }, 50, 50, TimeUnit.MILLISECONDS)
        }
    }
    ```

## Quartz { #quartz }

Реализация на основе библиотеки [Quartz](https://www.quartz-scheduler.org/) используется для задач с расписанием по `cron`, пользовательских экземпляров `Trigger` и правил выполнения `Quartz`.

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:scheduling-quartz"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends QuartzModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("ru.tinkoff.kora:scheduling-quartz")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : QuartzModule
    ```

### Конфигурация { #configuration-5 }

Конфигурация `Quartz` задаётся значениями [Properties](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/configuration/) в формате ключ-значение.
Настройки Kora для плавной остановки и телеметрии задаются в секции `scheduling`.
Конфигурация конкретной `cron`-задачи также может содержать секцию `telemetry`, значения которой переопределяют общую телеметрию планировщика для этой задачи.

===! ":material-code-json: `Hocon`"

    ```javascript
    quartz { //(1)!
        "org.quartz.threadPool.threadCount" = "10"
    }
    scheduling {
        waitForJobComplete = true //(2)!
        telemetry {
            logging {
                enabled = false //(3)!
            }
            metrics {
                enabled = true //(4)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(5)!
                tags = { // (6)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(7)!
                attributes = { // (8)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1. Параметры конфигурации планировщика `Quartz` (по умолчанию используются свойства из `quartz.properties` ниже)
    2. Ожидать ли завершения задач перед остановкой планировщика при [плавной остановке](container.md#component-lifecycle) (по умолчанию: `true`)
    3. Включает логирование модуля (по умолчанию: `false`)
    4. Включает метрики модуля (по умолчанию: `true`)
    5. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Настраивает теги метрик (по умолчанию: `{}`)
    7. Включает трассировку модуля (по умолчанию: `true`)
    8. Настраивает атрибуты трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    quartz: #(1)!
      org.quartz.threadPool.threadCount: "10"
    scheduling:
      waitForJobComplete: true #(2)!
      telemetry:
        logging:
          enabled: false #(3)!
        metrics:
          enabled: true #(4)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(5)!
          tags: #(6)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(7)!
          attributes: #(8)!
            key1: value1
            key2: value2
    ```

    1. Параметры конфигурации планировщика `Quartz` (по умолчанию используются свойства из `quartz.properties` ниже)
    2. Ожидать ли завершения задач перед остановкой планировщика при [плавной остановке](container.md#component-lifecycle) (по умолчанию: `true`)
    3. Включает логирование модуля (по умолчанию: `false`)
    4. Включает метрики модуля (по умолчанию: `true`)
    5. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Настраивает теги метрик (по умолчанию: `{}`)
    7. Включает трассировку модуля (по умолчанию: `true`)
    8. Настраивает атрибуты трассировки (по умолчанию: `{}`)

Настройки по умолчанию используются из:

??? abstract "quartz.properties"

    ```properties
    org.quartz.scheduler.instanceName: DefaultQuartzScheduler
    org.quartz.scheduler.rmi.export: false
    org.quartz.scheduler.rmi.proxy: false
    org.quartz.scheduler.wrapJobExecutionInUserTransaction: false

    org.quartz.threadPool.class: org.quartz.simpl.SimpleThreadPool
    org.quartz.threadPool.threadCount: 10
    org.quartz.threadPool.threadPriority: 5
    org.quartz.threadPool.threadsInheritContextClassLoaderOfInitializingThread: true

    org.quartz.jobStore.misfireThreshold: 60000

    org.quartz.jobStore.class: org.quartz.simpl.RAMJobStore
    ```

### Cron { #cron }

Для запуска задач по расписанию используются [`cron`-выражения](http://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html).

Выражение `Quartz` состоит из шести обязательных полей и необязательного седьмого поля года, разделённых пробелами:

| Поле         | Допустимые значения  | Обязательное |
|--------------|----------------------|--------------|
| Секунды      | `0-59`               | да           |
| Минуты       | `0-59`               | да           |
| Часы         | `0-23`               | да           |
| День месяца  | `1-31`               | да           |
| Месяц        | `1-12` или `JAN-DEC` | да           |
| День недели  | `1-7` или `SUN-SAT`  | да           |
| Год          | пусто, `1970-2099`   | нет          |

Помимо обычных чисел, диапазонов (`8-10`), списков (`6,19`) и шагов (`0/30`), поддерживаются следующие специальные символы:

| Символ | Значение                                                                                           |
|--------|----------------------------------------------------------------------------------------------------|
| `*`    | Все значения поля (например, `*` в поле минут означает «каждую минуту»)                             |
| `?`    | Без конкретного значения, используется в поле дня месяца или дня недели, когда указано другое из них |
| `L`    | Последний (последний день месяца или последний указанный день недели в месяце)                      |
| `W`    | Ближайший будний день к указанному дню месяца                                                       |
| `#`    | N-й указанный день недели в месяце, например `5#2` — это вторая пятница                             |

Примеры выражений:

| Выражение           | Значение                                    |
|---------------------|---------------------------------------------|
| `0 0 * * * ?`       | В начале каждого часа каждого дня           |
| `*/10 * * * * ?`    | Каждые десять секунд                        |
| `0 0 8-10 * * ?`    | В 8, 9 и 10 часов каждого дня               |
| `0 0/30 8-10 * * ?` | В 8:00, 8:30, 9:00, 9:30, 10:00 и 10:30     |
| `0 0 0 L * ?`       | В последний день месяца в полночь           |
| `0 0 0 1W * ?`      | В первый будний день месяца в полночь       |
| `0 0 0 ? * 5#2`     | Во вторую пятницу месяца в полночь          |

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithCron("* * * ? * * *") //(1)!
        void schedule() {
            // do something
        }
    }
    ```

    1. `cron`-выражение, которое запускает задачу каждую секунду

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleWithCron("* * * ? * * *") //(1)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. `cron`-выражение, которое запускает задачу каждую секунду

Атрибут `identity` задаёт [идентичность Quartz Trigger](https://www.quartz-scheduler.org/api/2.3.0/org/quartz/TriggerBuilder.html),
используемую для именования задачи, что полезно для идентификации и замены задач, особенно с кластерными или персистентными реализациями `JobStore`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithCron(value = "0 0 * * * ?", identity = "my-hourly-job") //(1)!
        void schedule() {
            // do something
        }
    }
    ```

    1. `cron`-выражение, которое запускает задачу в начале каждого часа, зарегистрированное под идентичностью триггера `my-hourly-job`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleWithCron(value = "0 0 * * * ?", identity = "my-hourly-job") //(1)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. `cron`-выражение, которое запускает задачу в начале каждого часа, зарегистрированное под идентичностью триггера `my-hourly-job`

#### Конфигурация { #configuration-6 }

Параметры можно передавать через конфигурацию; конфигурация имеет приоритет над значениями из аннотации.
Как и в случае собственного планировщика, путь `config` произвольный и по соглашению вкладывается в секцию `scheduling`
(как в [проекте-примере](https://github.com/kora-projects/kora-examples), `scheduling.jobs.quartz`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithCron(config = "scheduling.jobs.quartz")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleWithCron(config = "scheduling.jobs.quartz")
        fun schedule() {
            // do something
        }
    }
    ```

Пример конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        jobs {
            quartz {
                cron = "* * * ? * * *" //(1)!
            }
        }
    }
    ```

    1. `cron`-выражение, которое запускает задачу каждую секунду (`обязательный`, без значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        quartz:
          cron: "* * * ? * * *" #(1)!
    ```

    1. `cron`-выражение, которое запускает задачу каждую секунду (`обязательный`, без значения по умолчанию)

### Trigger { #trigger }

Для пользовательского расписания можно создать `Trigger` из библиотеки `Quartz`, зарегистрировать его в графе зависимостей с тегом, а затем использовать этот тег в аннотации `@ScheduleWithTrigger`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends QuartzModule {

        @Tag(SomeService.class) //(1)!
        default Trigger myTrigger() {
            return TriggerBuilder.newTrigger()
                    .withIdentity("myTrigger")
                    .startNow()
                    .withSchedule(SimpleScheduleBuilder.simpleSchedule()
                            .withIntervalInMilliseconds(50)
                            .repeatForever())
                    .build();
        }
    }

    @Component
    public class SomeService {

        @ScheduleWithTrigger(@Tag(SomeService.class)) //(2)!
        void schedule() {
            // do something
        }
    }
    ```

    1. Тег, используемый для регистрации `Trigger` в графе зависимостей.
    2. Тот же тег, используемый задачей для получения `Trigger`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : QuartzModule {

        @Tag(SomeService::class) //(1)!
        fun myTrigger(): Trigger {
            return TriggerBuilder.newTrigger()
                .withIdentity("myTrigger")
                .startNow()
                .withSchedule(
                    SimpleScheduleBuilder.simpleSchedule()
                        .withIntervalInMilliseconds(50)
                        .repeatForever()
                )
            .build()
        }
    }

    @Component
    class SomeService {

        @ScheduleWithTrigger(@Tag(SomeService::class)) //(2)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Тег, используемый для регистрации `Trigger` в графе зависимостей.
    2. Тот же тег, используемый задачей для получения `Trigger`.

### Неконкурентное выполнение { #non-concurrent-execution }

Аннотация `@DisallowConcurrentExecution` предотвращает одновременное выполнение одного и того же метода планировщиком `Quartz`.
Это аналог `org.quartz.DisallowConcurrentExecution` в `Kora`, который можно разместить на любом методе, помеченном `@Schedule*`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @DisallowConcurrentExecution
        @ScheduleWithCron(config = "scheduling.jobs.quartz")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @DisallowConcurrentExecution
        @ScheduleWithCron(config = "scheduling.jobs.quartz")
        fun schedule() {
            // do something
        }
    }
    ```

### Контекст задачи { #job-context }

Метод, выполняемый по расписанию `Quartz`, может опционально объявить единственный аргумент `org.quartz.JobExecutionContext`.
Если он присутствует, `Kora` передаёт методу текущий контекст выполнения; если отсутствует, метод вызывается без аргументов.
Контекст даёт доступ к `org.quartz.JobDataMap` задачи, что является способом чтения и записи состояния, связанного с задачей:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithCron(config = "scheduling.jobs.quartz")
        void schedule(JobExecutionContext context) {
            JobDataMap data = context.getJobDetail().getJobDataMap();
            int counter = data.containsKey("counter") ? data.getInt("counter") : 0;
            data.put("counter", counter + 1);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleWithCron(config = "scheduling.jobs.quartz")
        fun schedule(context: JobExecutionContext) {
            val data = context.jobDetail.jobDataMap
            val counter = if (data.containsKey("counter")) data.getInt("counter") else 0
            data.put("counter", counter + 1)
        }
    }
    ```

### Сохранение данных задачи { #persistent-execution }

Аннотация `@PersistJobDataAfterExecution` указывает `Quartz` сохранять обновлённый `org.quartz.JobDataMap` после выполнения задачи,
чтобы изменения, внесённые через [JobExecutionContext](#job-context), были видны при следующем выполнении.

Её рекомендуется использовать вместе с `@DisallowConcurrentExecution`,
чтобы избежать конфликтов при сохранении данных во время одновременного выполнения задачи.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @DisallowConcurrentExecution
        @PersistJobDataAfterExecution
        @ScheduleWithCron(config = "scheduling.jobs.quartz")
        void schedule(JobExecutionContext context) {
            JobDataMap data = context.getJobDetail().getJobDataMap();
            int counter = data.containsKey("counter") ? data.getInt("counter") : 0;
            data.put("counter", counter + 1); //(1)!
        }
    }
    ```

    1. Обновлённое значение сохраняется после выполнения и доступно при следующем запуске

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @DisallowConcurrentExecution
        @PersistJobDataAfterExecution
        @ScheduleWithCron(config = "scheduling.jobs.quartz")
        fun schedule(context: JobExecutionContext) {
            val data = context.jobDetail.jobDataMap
            val counter = if (data.containsKey("counter")) data.getInt("counter") else 0
            data.put("counter", counter + 1) //(1)!
        }
    }
    ```

    1. Обновлённое значение сохраняется после выполнения и доступно при следующем запуске

### Плавная остановка { #graceful-shutdown-quartz }

Во время [плавной остановки](container.md#component-lifecycle) параметр `scheduling.waitForJobComplete` управляет тем, как останавливается планировщик `Quartz`.
При `true` (по умолчанию) он вызывает `scheduler.shutdown(true)` и блокируется до завершения выполняющихся задач; при `false` он останавливается без ожидания.
Как и в случае собственного планировщика, длительно выполняющиеся задачи всё же должны кооперативно проверять
[Thread.currentThread().isInterrupted()](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#isInterrupted--) и останавливать работу вручную.

### Scheduler { #scheduler }

Лежащий в основе `org.quartz.Scheduler` регистрируется как компонент и может быть внедрён для продвинутых сценариев,
таких как программная регистрация задач или инспекция состояния планировщика:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        private final Scheduler scheduler;

        public SomeService(Scheduler scheduler) {
            this.scheduler = scheduler;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val scheduler: Scheduler)
    ```
