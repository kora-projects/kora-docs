---
seo_title: "Планировщик Kora: cron, фиксированный интервал, Quartz и db-scheduler"
seo_description: "Справочник по планировщику Kora: JDK, Quartz и db-scheduler с хранением задач в базе, фиксированная частота и задержка, одноразовые и cron-задачи, корректное завершение."
keywords: ["Kora Framework", "фреймворк Kora", "планировщик Kora", "cron-задачи", "Quartz", "db-scheduler", "задачи по расписанию", "виртуальные потоки"]
description: "Explains Kora scheduling for the JDK, Quartz and db-scheduler schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, virtual-thread execution, persistent database jobs, graceful shutdown, and concurrency controls. Use when working with @ScheduleJdkAtFixedRate, @ScheduleJdkWithFixedDelay, @ScheduleJdkOnce, @ScheduleJdkWithCron, @ScheduleQuartzWithTrigger, @DisallowConcurrentExecution, @PersistJobDataAfterExecution, SchedulingJdkModule, SchedulingJdkExecutor, VirtualThreadSchedulingJdkExecutor, CronExpression, QuartzModule, DbSchedulerModule, DbSchedulerConfig, KoraDbScheduler, DbSchedulerJob."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora scheduling for the JDK, Quartz and db-scheduler schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, virtual-thread execution, persistent database jobs, graceful shutdown, and concurrency controls; key triggers include @ScheduleJdkAtFixedRate, @ScheduleJdkWithFixedDelay, @ScheduleJdkOnce, @ScheduleJdkWithCron, @ScheduleQuartzWithTrigger, @DisallowConcurrentExecution, @PersistJobDataAfterExecution, SchedulingJdkModule, SchedulingJdkExecutor, VirtualThreadSchedulingJdkExecutor, executionParallelism, CronExpression, QuartzModule, scheduling-db-scheduler, DbSchedulerModule, DbSchedulerConfig, KoraDbScheduler, DbSchedulerJob, Configurer<SchedulerBuilder>."
---

Модуль планирования Kora позволяет запускать методы приложения по расписанию в декларативном стиле через аннотации.
Во время компиляции Kora генерирует компоненты задач и связывает их с выбранным механизмом планирования.

Доступны три варианта: планировщик `JDK` на основе стандартной библиотеки, планировщик на основе `Quartz`
и [DB Scheduler](#db-scheduler) на основе библиотеки `db-scheduler`. Все они поддерживают `cron`-выражения.
Планировщик `JDK` закрывает периодические и `cron`-задачи внутри одного приложения без дополнительных зависимостей,
`Quartz` добавляет пользовательские экземпляры `Trigger`, подключаемый `JobStore`, правила выполнения задач и диалект `cron` от Quartz с модификаторами `L`, `W` и `#`,
а `DB Scheduler` хранит состояние задач в таблице базы данных, поэтому задачи переживают перезапуски и согласуются между экземплярами приложения.


У каждого планировщика свои аннотации: `io.koraframework.scheduling.jdk.annotation.ScheduleJdk*`, `io.koraframework.scheduling.quartz.annotation.ScheduleQuartz*` и `io.koraframework.scheduling.db.scheduler.annotation.ScheduleDb*`. Для задач с путём `config` доступно `enabled = false`; постоянные планировщики также снимают отключённую задачу с расписания при старте.
Сгенерированные задачи наследуют `@Conditional` компонента, где объявлен метод: если условие не выполнено, задача не попадает в граф.

## JDK Scheduler { #native }

Планировщик `JDK` построен на стандартной библиотеке `JDK` и следует модели [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html):
один поток-таймер отслеживает, когда задачи должны сработать, а каждое выполнение идёт в собственном [виртуальном потоке](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html).

Для создания задач используются специальные аннотации из пакета `io.koraframework.scheduling.jdk.annotation`:
`@ScheduleJdkAtFixedRate`, `@ScheduleJdkWithFixedDelay`, `@ScheduleJdkOnce` и `@ScheduleJdkWithCron`.

У всех аннотаций есть параметр `config`.
Если он указан, значения параметров берутся из конфигурации по этому пути и имеют приоритет над значениями из аннотации.
Конфигурация конкретной задачи также может содержать секцию `telemetry`, значения которой переопределяют общую телеметрию планировщика для этой задачи.

Методы, выполняемые по расписанию, должны удовлетворять следующим требованиям:

- Класс, в котором объявлен метод, должен быть компонентом в [графе зависимостей](container.md), например помеченным аннотацией `@Component`.
- Метод планировщика `JDK` не должен иметь аргументов (планировщик `Quartz` дополнительно допускает необязательный аргумент [JobExecutionContext](#job-context)).
- Возвращаемое значение метода игнорируется.
- В `Kotlin` метод должен быть функцией-членом класса и не должен быть `suspend`-функцией.

!!! warning "Параметр расписания обязателен"

    Каждой аннотации `JDK` требуется расписание — либо из её собственных атрибутов, либо по пути `config`.
    Если не задано ни то, ни другое, компиляция завершается ошибкой:

    - `@ScheduleJdkAtFixedRate` — `Either period() or config() annotation parameter must be provided`
    - `@ScheduleJdkWithFixedDelay` и `@ScheduleJdkOnce` — `Either delay() or config() annotation parameter must be provided`
    - `@ScheduleJdkWithCron` — `Either value() or config() annotation parameter must be provided`

    Значение по умолчанию у `period()` и `delay()` равно `0`, и оно считается незаданным.

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:scheduling-jdk"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends SchedulingJdkModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("io.koraframework:scheduling-jdk")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : SchedulingJdkModule
    ```

### Конфигурация { #configuration }

Параметры планировщика описываются классом `SchedulingJdkConfig` и располагаются в секции `scheduling.jdk`,
параметры телеметрии общие для обоих планировщиков и располагаются в секции `scheduling.telemetry`:

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        jdk {
            shutdownWait = "30s" //(1)!
            executionParallelism = 10 //(2)!
        }
        telemetry {
            logging {
                enabled = false //(3)!
            }
            metrics {
                enabled = false //(4)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(5)!
                tags = { //(6)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(7)!
                attributes = { //(8)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1. Время, которое даётся исполнителю на завершение идущих выполнений перед их прерыванием при [плавной остановке](#graceful-shutdown) (по умолчанию: `30s`)
    2. Максимальное число выполнений, идущих одновременно по всем задачам; выполнения сверх лимита ждут в очереди (по умолчанию: без ограничения, `Integer.MAX_VALUE`)
    3. Включает логирование модуля (по умолчанию: `false`)
    4. Включает метрики модуля (по умолчанию: `false`)
    5. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Настройка тегов метрик (по умолчанию: `{}`)
    7. Включает трассировку модуля (по умолчанию: `true`)
    8. Настройка атрибутов трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jdk:
        shutdownWait: "30s" #(1)!
        executionParallelism: 10 #(2)!
      telemetry:
        logging:
          enabled: false #(3)!
        metrics:
          enabled: false #(4)!
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

    1. Время, которое даётся исполнителю на завершение идущих выполнений перед их прерыванием при [плавной остановке](#graceful-shutdown) (по умолчанию: `30s`)
    2. Максимальное число выполнений, идущих одновременно по всем задачам; выполнения сверх лимита ждут в очереди (по умолчанию: без ограничения, `Integer.MAX_VALUE`)
    3. Включает логирование модуля (по умолчанию: `false`)
    4. Включает метрики модуля (по умолчанию: `false`)
    5. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Настройка тегов метрик (по умолчанию: `{}`)
    7. Включает трассировку модуля (по умолчанию: `true`)
    8. Настройка атрибутов трассировки (по умолчанию: `{}`)

По умолчанию `SchedulingJdkExecutor` — это `VirtualThreadSchedulingJdkExecutor`.
Он держит один платформенный поток `kora-jdk-scheduler-timer`, который не является демоном и только отслеживает время срабатывания,
а каждое выполнение задачи запускает в новом виртуальном потоке `kora-jdk-scheduler-job-N`, поэтому задачи не занимают платформенные потоки, пока ждут ввода-вывода.
Выполнения одной задачи никогда не пересекаются, а число выполнений, идущих одновременно по всем задачам, ограничено `scheduling.jdk.executionParallelism`.
Исполнитель зарегистрирован как `@DefaultComponent`, поэтому собственный компонент `SchedulingJdkExecutor` его заменяет.

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#scheduling).

Конфигурация конкретной задачи также может содержать собственную секцию `telemetry`, которая переопределяет общую `scheduling.telemetry` только для этой задачи.
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

Наблюдаемость задач можно настроить и в коде.
Регистрация компонента, наследующего `DefaultSchedulingLoggerFactory` или `DefaultSchedulingMetricsFactory`, меняет способ логирования или сбора метрик задач,
а регистрация компонента `SchedulingTelemetryFactory` полностью заменяет реализацию по умолчанию.

### Фиксированная частота { #fixed-rate }

Планирование, при котором интервал отсчитывается между началами соседних выполнений задачи.

Если выполнение длится дольше периода, следующее начнётся сразу после завершения предыдущего:
выполнения одной и той же задачи никогда не накладываются друг на друга, они лишь запускаются с опозданием.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleJdkAtFixedRate(initialDelay = 50, period = 50, unit = ChronoUnit.MILLIS)
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleJdkAtFixedRate(initialDelay = 50, period = 50, unit = ChronoUnit.MILLIS)
        fun schedule() {
            // do something
        }
    }
    ```

#### Конфигурация { #configuration-2 }

Параметры можно передавать через конфигурацию, она имеет приоритет над значениями из аннотации.
Путь `config` произвольный, но по соглашению он вкладывается в секцию `scheduling`, чтобы параметры задачи
и её `telemetry` находились рядом (как в [проекте с примерами](https://github.com/kora-projects/kora-examples), `scheduling.jobs.fix-rate`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleJdkAtFixedRate(config = "scheduling.jobs.fix-rate")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleJdkAtFixedRate(config = "scheduling.jobs.fix-rate")
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
    2. Периодичный интервал между задачами (`обязательный`, нет значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        fix-rate:
          initialDelay: "50ms" #(1)!
          period: "50ms" #(2)!
    ```

    1. Начальная задержка перед первой задачей (по умолчанию: `0ms`)
    2. Периодичный интервал между задачами (`обязательный`, нет значения по умолчанию)

Если аннотация уже задаёт `period` и `initialDelay`, эти значения становятся значениями по умолчанию сгенерированной конфигурации,
и в конфигурации достаточно переопределить только то, что должно отличаться.

### Фиксированная задержка { #fixed-delay }

Планировщик выдерживает фиксированный интервал от момента завершения предыдущего выполнения задачи.
Несколько выполнений одной и той же задачи не будут происходить одновременно.

Неважно, сколько длится текущее выполнение:
следующая задача начнётся после завершения предыдущей и истечения настроенной задержки.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleJdkWithFixedDelay(initialDelay = 50, delay = 50, unit = ChronoUnit.MILLIS)
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleJdkWithFixedDelay(initialDelay = 50, delay = 50, unit = ChronoUnit.MILLIS)
        fun schedule() {
            // do something
        }
    }
    ```

#### Конфигурация { #configuration-3 }

Параметры можно передавать через конфигурацию, она имеет приоритет над значениями из аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleJdkWithFixedDelay(config = "scheduling.jobs.fix-delay")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleJdkWithFixedDelay(config = "scheduling.jobs.fix-delay")
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
    2. Периодичная задержка между задачами (`обязательный`, нет значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        fix-delay:
          initialDelay: "50ms" #(1)!
          delay: "50ms" #(2)!
    ```

    1. Начальная задержка перед первой задачей (по умолчанию: `0ms`)
    2. Периодичная задержка между задачами (`обязательный`, нет значения по умолчанию)

### Однократно { #once }

Однократный запуск задачи по истечении настроенного интервала времени.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleJdkOnce(delay = 50, unit = ChronoUnit.MILLIS)
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleJdkOnce(delay = 50, unit = ChronoUnit.MILLIS)
        fun schedule() {
            // do something
        }
    }
    ```

#### Конфигурация { #configuration-4 }

Параметры можно передавать через конфигурацию, она имеет приоритет над значениями из аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleJdkOnce(config = "scheduling.jobs.once")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleJdkOnce(config = "scheduling.jobs.once")
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

    1. Задержка перед задачей (`обязательный`, нет значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        once:
          delay: "50ms" #(1)!
    ```

    1. Задержка перед задачей (`обязательный`, нет значения по умолчанию)

### Cron { #jdk-cron }

Планировщик `JDK` выполняет `cron`-задачи без внешнего планировщика.
Выражения разбираются и вычисляются классом `CronExpression`, который поставляется в артефакте `scheduling-jdk`.

После каждого выполнения задача вычисляет следующее время запуска от текущего момента в часовом поясе компонента `ZoneId` с тегом `@Tag(SchedulingModule.class)` или в часовом поясе `JVM` по умолчанию, если такого компонента нет,
и планирует себя заново, поэтому долгое выполнение никогда не приводит к серии догоняющих запусков.

Переходы на летнее и зимнее время обрабатываются в хронологическом порядке:
локальное время, которого не существует из-за перевода часов вперёд, пропускается, а не сдвигается,
а локальное время, которое повторяется из-за перевода часов назад, срабатывает при обоих вхождениях.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleJdkWithCron("*/10 * * * * *") //(1)!
        void schedule() {
            // do something
        }
    }
    ```

    1. Выражение `cron`, запускающее задачу каждые десять секунд

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleJdkWithCron("*/10 * * * * *") //(1)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Выражение `cron`, запускающее задачу каждые десять секунд

#### Формат выражения { #jdk-cron-format }

Выражение может содержать пять, шесть или семь полей, разделённых пробелами.
Форма из пяти полей не содержит поля секунд и вычисляется с `0` секунд:

| Поле          | Допустимые значения           | Обязательное                     |
|---------------|-------------------------------|----------------------------------|
| Секунды       | `0-59`                        | в форме из шести и семи полей    |
| Минуты        | `0-59`                        | да                               |
| Часы          | `0-23`                        | да                               |
| День месяца   | `1-31`                        | да                               |
| Месяц         | `1-12` или `JAN-DEC`          | да                               |
| День недели   | `1-7` или `SUN-SAT`           | да                               |
| Год           | пусто или `1970-2099`         | нет                              |

В поле дня недели `1` — это воскресенье, а `7` — суббота; `0` также принимается как воскресенье.
Если поле года опущено, разрешены все годы с `1970` по `2099`.

Помимо обычных чисел поддерживаются следующие специальные символы:

| Символ | Значение                                                                                                               |
|--------|------------------------------------------------------------------------------------------------------------------------|
| `*`    | Все значения поля (например, `*` в поле минут означает «каждую минуту»)                                                |
| `?`    | Отсутствие конкретного значения, допустимо только в полях дня месяца, дня недели и года, где эквивалентно `*`           |
| `,`    | Перечисление значений, например `6,19` в поле часов                                                                     |
| `-`    | Включающий диапазон, например `MON-FRI` или `9-17`                                                                      |
| `/`    | Шаг, например `*/10` в поле секунд или `5/10`                                                                           |

Поля дня месяца и дня недели объединяются логическим `AND`, поэтому `0 0 9-17 * * MON-FRI` срабатывает только по будням.

Примеры выражений:

| Выражение                 | Значение                                                    |
|---------------------------|-------------------------------------------------------------|
| `0 * * * * *`             | В начале каждой минуты                                      |
| `*/10 * * * * *`          | Каждые десять секунд                                        |
| `0 0 * * * ?`             | В начале каждого часа                                       |
| `0 0 6,19 * * ?`          | В 6:00 и 19:00 каждый день                                  |
| `0 0/30 8-10 * * ?`       | Каждые 30 минут с 8:00 по 10:30 каждый день                 |
| `0 0 9-17 ? * MON-FRI`    | Каждый час с 9:00 по 17:00 по будням                        |
| `*/15 9-17 * * MON-FRI`   | Форма из пяти полей: каждые 15 минут с 9:00 по 17:00 по будням |
| `0 0 0 25 DEC ?`          | Каждое Рождество в полночь                                  |
| `0 0 0 29 FEB ?`          | Каждый високосный день в полночь                            |
| `0 0 0 1 JAN ? 2027`      | 1 января 2027 года в полночь                                |

!!! warning "Модификаторы Quartz не поддерживаются"

    Вычислитель `JDK` отклоняет специфичные для Quartz модификаторы `L`, `W`, `#` и `C` с ошибкой
    `Cron field doesn't support L, W, # or C modifiers`.
    Выражения, которым они нужны, должны выполняться на планировщике [Quartz](#quartz).

Буквальное выражение в аннотации проверяется Java- или Kotlin-процессором при компиляции. Выражение из конфигурации разбирается при построении графа; неверное значение в конфигурации приводит к ошибке запуска.
Если выражение больше никогда не может сработать — например, задан год в прошлом, — задача пишет предупреждение в лог и прекращает планировать себя.

#### Конфигурация { #configuration-jdk-cron }

Выражение можно передавать через конфигурацию, она имеет приоритет над значением из аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleJdkWithCron(config = "scheduling.jobs.cron")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleJdkWithCron(config = "scheduling.jobs.cron")
        fun schedule() {
            // do something
        }
    }
    ```

Путь конфигурации принимает либо объект с ключом `cron` и необязательной секцией `telemetry`, либо обычную строку с выражением:

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        jobs {
            cron {
                cron = "*/10 * * * * *" //(1)!
            }
            cron-short = "*/10 * * * * *" //(2)!
        }
    }
    ```

    1. Выражение `cron`, запускающее задачу каждые десять секунд (`обязательный`, нет значения по умолчанию)
    2. Краткая форма: значение самого пути `config` является выражением `cron`

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        cron:
          cron: "*/10 * * * * *" #(1)!
        cron-short: "*/10 * * * * *" #(2)!
    ```

    1. Выражение `cron`, запускающее задачу каждые десять секунд (`обязательный`, нет значения по умолчанию)
    2. Краткая форма: значение самого пути `config` является выражением `cron`

Если выражение указано и в аннотации, оно становится значением по умолчанию сгенерированной конфигурации,
поэтому путь конфигурации может отсутствовать полностью и нужен только для переопределения расписания.

### Плавная остановка { #graceful-shutdown }

При [плавной остановке](container.md#component-lifecycle) компоненты освобождаются в обратном порядке зависимостей.
Задачи зависят от исполнителя, а исполнитель от задач не зависит, поэтому каждая задача освобождается раньше исполнителя.

Освобождение задачи отменяет её расписание, никого не прерывая и ничего не дожидаясь:
новое выполнение этой задачи не начинается, а уже идущее выполнение продолжается.
После этого исполнитель перестаёт принимать работу, отменяет оставшиеся периодические задачи и ждёт завершения идущих выполнений не дольше `scheduling.jdk.shutdownWait`;
тот же срок распространяется на одноразовые задачи, которые ещё ожидают в таймере.
По истечении ожидания оставшиеся задачи отменяются, идущие выполнения прерываются, а в лог пишется
`SchedulingJdkExecutor failed completing graceful shutdown in ...`, поэтому задача, которая никогда не возвращает управление, задерживает остановку не более чем на `shutdownWait`.

Поэтому долгие задачи следует писать так, чтобы они завершались сами,
и дополнительно можно проверять [Thread.currentThread().isInterrupted()](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html#isInterrupted()), чтобы остановиться раньше.

### Программное планирование { #programmatic }

Для планирования задач в императивном стиле можно внедрить компонент `SchedulingJdkExecutor`.
Это тот же исполнитель, который выполняет задачи из аннотаций; он предоставляет методы `scheduleAtFixedRate`, `scheduleWithFixedDelay` и `scheduleOnce`,
каждый из которых возвращает `ScheduledFuture`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        private final SchedulingJdkExecutor executor;

        public SomeService(SchedulingJdkExecutor executor) {
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
    class SomeService(private val executor: SchedulingJdkExecutor) {

        fun start() {
            executor.scheduleAtFixedRate({
                // do something
            }, 50, 50, TimeUnit.MILLISECONDS)
        }
    }
    ```

Задачи, запланированные таким образом, являются обычными `Runnable`: они выполняются в виртуальных потоках и вместе с задачами из аннотаций учитываются в `scheduling.jdk.executionParallelism`,
но не оборачиваются в телеметрию планировщика.
Выполнения одной периодической задачи никогда не пересекаются, неположительные `period` или `delay` приводят к `IllegalArgumentException`,
а планирование после освобождения исполнителя — к `RejectedExecutionException`.
Периодические задачи отменяются при освобождении исполнителя, а ожидающие одноразовые задачи подчиняются тому же `shutdownWait`, как описано в разделе [Плавная остановка](#graceful-shutdown).

## DB Scheduler { #db-scheduler }

Реализация на основе библиотеки [db-scheduler](https://github.com/kagkarlsson/db-scheduler) хранит состояние задач в таблице базы данных.
Запланированные выполнения переживают перезапуск приложения, а экземпляры приложения, использующие общую таблицу, согласуются через неё,
поэтому каждое выполнение забирает только один экземпляр. Задача определяется в таблице своим именем, поэтому имена задач должны оставаться стабильными между развёртываниями.

Задачи создаются аннотациями из пакета `io.koraframework.scheduling.db.scheduler.annotation`:
`@ScheduleDbWithCron`, `@ScheduleDbWithFixedDelay` и `@ScheduleDbOnce`.
Их имена отличаются от аннотаций [планировщика JDK](#native).
Требования к методу те же, что и для планировщика `JDK`: метод принадлежит компоненту, не имеет аргументов, а в `Kotlin` является функцией-членом класса без `suspend`.

У всех аннотаций есть параметры `name` и `config`:

- `name` задаёт имя задачи в таблице; если оно пустое, используется `CanonicalClassName#methodName`, например `com.example.SomeService#schedule`.
- `config` задаёт путь конфигурации, значения которой имеют приоритет над значениями аннотации, как и у [планировщика JDK](#configuration-2).
  Она также может содержать `enabled` и секцию `telemetry`. Имя задачи задаётся только аннотацией.

### Подключение { #dependency-3 }

Модулю нужен компонент `javax.sql.DataSource` в графе, например предоставляемый модулем [JDBC](database-jdbc.md).

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:scheduling-db-scheduler"
    implementation "io.koraframework:database-jdbc"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends DbSchedulerModule, JdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("io.koraframework:scheduling-db-scheduler")
    implementation("io.koraframework:database-jdbc")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : DbSchedulerModule, JdbcDatabaseModule
    ```

Сам планировщик — это компонент `KoraDbScheduler`. `DbSchedulerModule` помечает его как [корневой компонент](container.md#root-component), поэтому он запускается вместе с приложением.

### Конфигурация { #configuration-7 }

Параметры планировщика описываются классом `DbSchedulerConfig` и находятся в секции `scheduling.dbScheduler`,
телеметрия общая с остальными планировщиками и находится в секции `scheduling.telemetry`, описанной для [планировщика JDK](#configuration):

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        dbScheduler {
            tableInitialize = false //(1)!
            tableName = "kora_scheduling_db_scheduler_jobs" //(2)!
            executionParallelism = 10 //(3)!
            shutdownWait = "30s" //(4)!
            polling {
                strategy = "FETCH" //(5)!
                prefetchMode = "DEFAULT" //(6)!
                interval = "10s" //(7)!
            }
        }
    }
    ```

    1. Создаёт таблицу при старте, если её нет, см. [Таблица в базе данных](#db-scheduler-table) (по умолчанию: `false`)
    2. Имя таблицы, которую использует планировщик (по умолчанию: `kora_scheduling_db_scheduler_jobs`)
    3. Максимальное число выполнений задач, идущих одновременно; передаётся в `db-scheduler` как число потоков и ограничивает виртуальные потоки, в которых идут выполнения (по умолчанию: `10`)
    4. Время, которое планировщик ждёт идущие выполнения при [плавной остановке](#graceful-shutdown-db-scheduler); передаётся в `db-scheduler` как `shutdownMaxWait` (по умолчанию: `30s`)
    5. Стратегия опроса: `FETCH` или `LOCK_AND_FETCH` (по умолчанию: `FETCH`)
    6. Сколько готовых к запуску выполнений забирается заранее относительно `executionParallelism`: `DEFAULT` сохраняет значения по умолчанию `db-scheduler`, `BOUNDED` держит локальную очередь близкой к `executionParallelism`, `BUFFERED` держит больший запас, чтобы сократить простои между опросами (по умолчанию: `DEFAULT`)
    7. Интервал между опросами таблицы на готовые к запуску выполнения (по умолчанию: `10s`)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      dbScheduler:
        tableInitialize: false #(1)!
        tableName: "kora_scheduling_db_scheduler_jobs" #(2)!
        executionParallelism: 10 #(3)!
        shutdownWait: "30s" #(4)!
        polling:
          strategy: "FETCH" #(5)!
          prefetchMode: "DEFAULT" #(6)!
          interval: "10s" #(7)!
    ```

    1. Создаёт таблицу при старте, если её нет, см. [Таблица в базе данных](#db-scheduler-table) (по умолчанию: `false`)
    2. Имя таблицы, которую использует планировщик (по умолчанию: `kora_scheduling_db_scheduler_jobs`)
    3. Максимальное число выполнений задач, идущих одновременно; передаётся в `db-scheduler` как число потоков и ограничивает виртуальные потоки, в которых идут выполнения (по умолчанию: `10`)
    4. Время, которое планировщик ждёт идущие выполнения при [плавной остановке](#graceful-shutdown-db-scheduler); передаётся в `db-scheduler` как `shutdownMaxWait` (по умолчанию: `30s`)
    5. Стратегия опроса: `FETCH` или `LOCK_AND_FETCH` (по умолчанию: `FETCH`)
    6. Сколько готовых к запуску выполнений забирается заранее относительно `executionParallelism`: `DEFAULT` сохраняет значения по умолчанию `db-scheduler`, `BOUNDED` держит локальную очередь близкой к `executionParallelism`, `BUFFERED` держит больший запас, чтобы сократить простои между опросами (по умолчанию: `DEFAULT`)
    7. Интервал между опросами таблицы на готовые к запуску выполнения (по умолчанию: `10s`)

Выполнения задач идут в виртуальных потоках `kora-db-scheduler-N`.
Метрики модуля те же, что и у остальных планировщиков, и описаны в разделе [Справочник метрик](metrics.md#scheduling).

### Таблица в базе данных { #db-scheduler-table }

Таблица `db-scheduler` должна существовать до запуска. Модуль содержит SQL-схемы для PostgreSQL, MySQL, MariaDB, Microsoft SQL Server, Oracle и HSQLDB по пути
`db/kora/scheduling-db-scheduler/schema/<database>.sql`, а также changelog Liquibase:
`db/kora/scheduling-db-scheduler/liquibase/changelog.yaml`.
Таблица по умолчанию — `kora_scheduling_db_scheduler_jobs`; первичный ключ и индексы имеют тот же префикс.
Для Flyway скопируйте SQL нужной базы в следующую свободную версию миграции приложения. Модуль не поставляет версионированную миграцию Flyway: её версия могла бы конфликтовать с миграциями приложения.
Для Liquibase подключите поставляемый changelog к основному changelog.
При изменении `scheduling.dbScheduler.tableName` переименуйте таблицу и ограничения в скопированном SQL-файле.

При `tableInitialize = true` модуль создаёт указанную таблицу при старте, если её ещё нет, используя схему для обнаруженной базы данных. Значение по умолчанию — `false`; в продакшене используйте инструмент миграций, если нужен управляемый процесс обновления схемы.

### Cron { #db-scheduler-cron }

Запускает задачу по `cron`-выражению.
Выражение вычисляет класс `CronSchedule` из `db-scheduler`, а не [CronExpression](#jdk-cron-format) планировщика `JDK`:
он использует формат `cron` Spring 5.3 из шести полей, начиная с секунд, и тегированный `ZoneId` планировщика или часовой пояс `JVM` по умолчанию,
подробности описаны в [документации db-scheduler](https://github.com/kagkarlsson/db-scheduler).
Этот диалект принимает `@yearly`, `@monthly`, `@weekly`, `@daily` и `@hourly`. Одиночное `-` выключает настроенную cron-задачу и удаляет её запланированное выполнение при старте. Буквальные выражения проверяются при обработке Java/Kotlin; значения из конфигурации — при запуске графа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleDbWithCron(value = "*/10 * * * * *", name = "some-cron") //(1)!
        void schedule() {
            // do something
        }
    }
    ```

    1. `cron`-выражение, которое запускает задачу каждые десять секунд; задача хранится в таблице под именем `some-cron`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleDbWithCron(value = "*/10 * * * * *", name = "some-cron") //(1)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. `cron`-выражение, которое запускает задачу каждые десять секунд; задача хранится в таблице под именем `some-cron`

Если не заданы ни `value`, ни `config`, компиляция завершается ошибкой `Either value() or config() annotation parameter must be provided`.
Путь `config` принимает либо объект с ключами `cron`, `enabled` и `telemetry`, либо просто строку с выражением. Имя задачи задаётся параметром `name` аннотации.
Если выражение указано и в аннотации, путь конфигурации может отсутствовать полностью.

### Фиксированная задержка { #db-scheduler-fixed-delay }

Запускает задачу многократно, выдерживая фиксированный интервал после завершения предыдущего выполнения.
`initialDelay` откладывает первое выполнение (по умолчанию: `0`).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleDbWithFixedDelay(initialDelay = 5, delay = 30, unit = ChronoUnit.SECONDS)
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleDbWithFixedDelay(initialDelay = 5, delay = 30, unit = ChronoUnit.SECONDS)
        fun schedule() {
            // do something
        }
    }
    ```

Если не заданы ни `delay`, ни `config`, компиляция завершается ошибкой `Either delay() or config() annotation parameter must be provided`.

### Однократный запуск { #db-scheduler-once }

Запускает задачу один раз после заданной задержки.
Выполнение создаётся при старте планировщика, если в таблице ещё нет выполнения с тем же именем,
и удаляется из таблицы после завершения. Неудачное выполнение тоже удаляется: повторов нет.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleDbOnce(delay = 30, unit = ChronoUnit.SECONDS)
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleDbOnce(delay = 30, unit = ChronoUnit.SECONDS)
        fun schedule() {
            // do something
        }
    }
    ```

Если не заданы ни `delay`, ни `config`, компиляция завершается ошибкой `Either delay() or config() annotation parameter must be provided`.

### Конфигурация { #configuration-8 }

Параметры любой аннотации можно передать через конфигурацию; она имеет приоритет над значениями из аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleDbWithCron(config = "scheduling.jobs.db-cron")
        void cron() {
            // do something
        }

        @ScheduleDbWithFixedDelay(config = "scheduling.jobs.db-delay")
        void fixedDelay() {
            // do something
        }

        @ScheduleDbOnce(config = "scheduling.jobs.db-once")
        void once() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleDbWithCron(config = "scheduling.jobs.db-cron")
        fun cron() {
            // do something
        }

        @ScheduleDbWithFixedDelay(config = "scheduling.jobs.db-delay")
        fun fixedDelay() {
            // do something
        }

        @ScheduleDbOnce(config = "scheduling.jobs.db-once")
        fun once() {
            // do something
        }
    }
    ```

Пример файла конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        jobs {
            db-cron {
                cron = "*/10 * * * * *" //(1)!
            }
            db-delay {
                initialDelay = "5s" //(2)!
                delay = "30s" //(3)!
            }
            db-once {
                delay = "30s" //(4)!
            }
        }
    }
    ```

    1. `cron`-выражение (`обязательный`, нет значения по умолчанию)
    2. Задержка перед первым выполнением (по умолчанию: `0ms`)
    3. Задержка после завершения выполнения перед следующим (`обязательный`, нет значения по умолчанию)
    4. Задержка перед единственным выполнением (`обязательный`, нет значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        db-cron:
          cron: "*/10 * * * * *" #(1)!
        db-delay:
          initialDelay: "5s" #(2)!
          delay: "30s" #(3)!
        db-once:
          delay: "30s" #(4)!
    ```

    1. `cron`-выражение (`обязательный`, нет значения по умолчанию)
    2. Задержка перед первым выполнением (по умолчанию: `0ms`)
    3. Задержка после завершения выполнения перед следующим (`обязательный`, нет значения по умолчанию)
    4. Задержка перед единственным выполнением (`обязательный`, нет значения по умолчанию)

Если значение уже задано в аннотации, оно становится значением по умолчанию сгенерированной конфигурации, и в конфигурации достаточно переопределить только то, что должно отличаться.

### Настройка { #db-scheduler-customization }

Планировщик использует `DataSource` с тегом `@Tag(KoraDbScheduler.class)`; по умолчанию это `DataSource` приложения,
поэтому регистрация компонента `DataSource` с этим тегом переносит планировщик в другую базу данных.

`SchedulerBuilder` из `db-scheduler` можно донастроить перед созданием планировщика, зарегистрировав компонент `Configurer<SchedulerBuilder>`
(`io.koraframework.common.Configurer`); он применяется после настроек из `DbSchedulerConfig`, поэтому может их и переопределить:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MySchedulerConfigurer implements Configurer<SchedulerBuilder> {

        @Override
        public SchedulerBuilder configure(SchedulerBuilder builder) {
            return builder.pollingInterval(Duration.ofSeconds(1));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MySchedulerConfigurer : Configurer<SchedulerBuilder> {

        override fun configure(builder: SchedulerBuilder): SchedulerBuilder {
            return builder.pollingInterval(Duration.ofSeconds(1))
        }
    }
    ```

Любой компонент, реализующий `DbSchedulerJob`, регистрируется в планировщике вместе с задачами из аннотаций.
Реализуйте его вручную, когда задаче нужны API `db-scheduler` напрямую, например собственные данные задачи или обработка завершения.
Такая задача не оборачивается в телеметрию планировщика:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ReportJob implements DbSchedulerJob {

        private final RecurringTask<Void> task = Tasks.recurring("report", FixedDelay.of(Duration.ofMinutes(5)))
            .execute((instance, context) -> {
                // do something
            });

        @Override
        public Task<?> task() {
            return task;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ReportJob : DbSchedulerJob {

        private val task: RecurringTask<Void> = Tasks.recurring("report", FixedDelay.of(Duration.ofMinutes(5)))
            .execute { _, _ ->
                // do something
            }

        override fun task(): Task<*> = task
    }
    ```

`KoraDbScheduler` оборачивает `com.github.kagkarlsson.scheduler.Scheduler` из `db-scheduler`,
поэтому можно внедрить и сам `Scheduler`, например чтобы планировать новые экземпляры задачи или просматривать запланированные выполнения.

### Плавная остановка { #graceful-shutdown-db-scheduler }

При [плавной остановке](container.md#component-lifecycle) `KoraDbScheduler` останавливает планировщик `db-scheduler`,
который перестаёт брать новые выполнения и ждёт завершения идущих выполнений не дольше `scheduling.dbScheduler.shutdownWait`.
По истечении ожидания идущие выполнения прерываются, и планировщик ждёт ещё не дольше `shutdownWait`.
Как и в случае остальных планировщиков, долгие задачи должны завершаться сами
или проверять [Thread.currentThread().isInterrupted()](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html#isInterrupted()).

## Quartz { #quartz }

Реализация на основе библиотеки [Quartz](https://www.quartz-scheduler.org/) используется для задач с пользовательскими экземплярами `Trigger`,
правилами выполнения `Quartz` и диалектом `cron` от Quartz.

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:scheduling-quartz"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends QuartzModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("io.koraframework:scheduling-quartz")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : QuartzModule
    ```

### Конфигурация { #configuration-5 }

Сам `Quartz` настраивается значениями [Properties](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/configuration/) в формате «ключ-значение»
в секции `scheduling.quartz.properties`.
Настройки Kora для плавной остановки находятся в `scheduling.quartz`, а телеметрия общая с планировщиком `JDK` и находится в секции `scheduling.telemetry`.

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        quartz {
            shutdownWait = "30s" //(1)!
            cleanupOrphanedJobs = false //(2)!
            compareStartTime = false //(3)!
            properties { //(4)!
                "org.quartz.threadPool.threadCount" = "10"
            }
        }
        telemetry {
            logging {
                enabled = false //(5)!
            }
            metrics {
                enabled = false //(6)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(7)!
                tags = { //(8)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(9)!
                attributes = { //(10)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1. Время ожидания работающих задач до их прерывания при [плавной остановке](#graceful-shutdown-quartz) (по умолчанию: `30s`)
    2. Удалять ли [осиротевшие задачи](#persistent-job-store) из постоянного хранилища при старте планировщика (по умолчанию: `false`)
    3. Сравнивать время начала триггера при сверке сохранённых задач (по умолчанию: `false`); время окончания сравнивается всегда
    4. Параметры конфигурации планировщика `Quartz`, накладываемые поверх значений по умолчанию ниже (опционально)
    5. Включает логирование модуля (по умолчанию: `false`)
    6. Включает метрики модуля (по умолчанию: `false`)
    7. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    8. Настройка тегов метрик (по умолчанию: `{}`)
    9. Включает трассировку модуля (по умолчанию: `true`)
    10. Настройка атрибутов трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      quartz:
        shutdownWait: "30s" #(1)!
        cleanupOrphanedJobs: false #(2)!
        compareStartTime: false #(3)!
        properties: #(4)!
          org.quartz.threadPool.threadCount: "10"
      telemetry:
        logging:
          enabled: false #(5)!
        metrics:
          enabled: false #(6)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(7)!
          tags: #(8)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(9)!
          attributes: #(10)!
            key1: value1
            key2: value2
    ```

    1. Время ожидания работающих задач до их прерывания при [плавной остановке](#graceful-shutdown-quartz) (по умолчанию: `30s`)
    2. Удалять ли [осиротевшие задачи](#persistent-job-store) из постоянного хранилища при старте планировщика (по умолчанию: `false`)
    3. Сравнивать время начала триггера при сверке сохранённых задач (по умолчанию: `false`); время окончания сравнивается всегда
    4. Параметры конфигурации планировщика `Quartz`, накладываемые поверх значений по умолчанию ниже (опционально)
    5. Включает логирование модуля (по умолчанию: `false`)
    6. Включает метрики модуля (по умолчанию: `false`)
    7. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    8. Настройка тегов метрик (по умолчанию: `{}`)
    9. Включает трассировку модуля (по умолчанию: `true`)
    10. Настройка атрибутов трассировки (по умолчанию: `{}`)

Значения по умолчанию считываются из ресурса `org/quartz/quartz.properties`, поставляемого с библиотекой `Quartz`, и затем корректируются Kora.
Любой ключ, присутствующий в `scheduling.quartz.properties`, имеет приоритет над обоими источниками.

??? abstract "Свойства, задаваемые Kora"

    ```properties
    org.quartz.scheduler.instanceName: kora-quartz-scheduler
    org.quartz.scheduler.instanceId: AUTO
    ```

Конфигурация конкретной `cron`-задачи также может содержать секцию `telemetry`, значения которой переопределяют общую телеметрию планировщика для этой задачи,
ровно так же, как описано для [планировщика JDK](#configuration).

### Cron { #cron }

Для запуска задач по расписанию используются [`cron`-выражения](http://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html).

Выражение `Quartz` состоит из шести обязательных полей и необязательного седьмого поля года, разделённых пробелами:

| Поле          | Допустимые значения    | Обязательное |
|---------------|------------------------|--------------|
| Секунды       | `0-59`                 | да           |
| Минуты        | `0-59`                 | да           |
| Часы          | `0-23`                 | да           |
| День месяца   | `1-31`                 | да           |
| Месяц         | `1-12` или `JAN-DEC`   | да           |
| День недели   | `1-7` или `SUN-SAT`    | да           |
| Год           | пусто, `1970-2099`     | нет          |

Помимо обычных чисел, диапазонов (`8-10`), перечислений (`6,19`) и шагов (`0/30`) поддерживаются следующие специальные символы:

| Символ | Значение                                                                                                     |
|--------|--------------------------------------------------------------------------------------------------------------|
| `*`    | Все значения поля (например, `*` в поле минут означает «каждую минуту»)                                      |
| `?`    | Отсутствие конкретного значения, используется в поле дня месяца или дня недели, когда задано другое из них    |
| `L`    | Последний (последний день месяца или последний указанный день недели в месяце)                               |
| `W`    | Ближайший рабочий день к указанному дню месяца                                                                |
| `#`    | N-й указанный день недели в месяце, например `5#2` — вторая пятница                                          |

Примеры выражений:

| Выражение           | Значение                                    |
|---------------------|---------------------------------------------|
| `0 0 * * * ?`       | В начале каждого часа каждого дня           |
| `*/10 * * * * ?`    | Каждые десять секунд                        |
| `0 0 8-10 * * ?`    | В 8, 9 и 10 часов каждый день               |
| `0 0/30 8-10 * * ?` | В 8:00, 8:30, 9:00, 9:30, 10:00 и 10:30     |
| `0 0 0 L * ?`       | В последний день месяца в полночь           |
| `0 0 0 1W * ?`      | В первый рабочий день месяца в полночь      |
| `0 0 0 ? * 5#2`     | Во вторую пятницу месяца в полночь          |

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleQuartzWithCron("* * * ? * * *") //(1)!
        void schedule() {
            // do something
        }
    }
    ```

    1. Выражение `cron`, запускающее задачу каждую секунду

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleQuartzWithCron("* * * ? * * *") //(1)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Выражение `cron`, запускающее задачу каждую секунду

Атрибут `identity` задаёт [идентификатор Quartz Trigger](https://www.quartz-scheduler.org/api/2.3.0/org/quartz/TriggerBuilder.html),
которым именуется задача — это полезно для идентификации и замены задач, особенно с кластерными или персистентными реализациями `JobStore`.
Если он не задан, идентификатором становится полное имя класса и имя метода задачи, например `com.example.SomeService#schedule`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleQuartzWithCron(value = "0 0 * * * ?", identity = "my-hourly-job") //(1)!
        void schedule() {
            // do something
        }
    }
    ```

    1. Выражение `cron`, запускающее задачу в начале каждого часа, зарегистрированное под идентификатором триггера `my-hourly-job`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleQuartzWithCron(value = "0 0 * * * ?", identity = "my-hourly-job") //(1)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Выражение `cron`, запускающее задачу в начале каждого часа, зарегистрированное под идентификатором триггера `my-hourly-job`

!!! warning "Источник cron обязателен"

    `@ScheduleQuartzWithCron` должна получить выражение либо из `value()`, либо из `config()`.
    Если не задано ни то, ни другое, компиляция завершается ошибкой `Quartz @ScheduleQuartzWithCron on '...' has no cron source.`

#### Конфигурация { #configuration-6 }

Параметры можно передавать через конфигурацию, она имеет приоритет над значениями из аннотации.
Как и для планировщика `JDK`, путь `config` произвольный и по соглашению вкладывается в секцию `scheduling`
(как в [проекте с примерами](https://github.com/kora-projects/kora-examples), `scheduling.jobs.quartz`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleQuartzWithCron(config = "scheduling.jobs.quartz")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleQuartzWithCron(config = "scheduling.jobs.quartz")
        fun schedule() {
            // do something
        }
    }
    ```

Путь конфигурации принимает либо объект с ключом `cron` и необязательной секцией `telemetry`, либо обычную строку с выражением:

===! ":material-code-json: `Hocon`"

    ```javascript
    scheduling {
        jobs {
            quartz {
                cron = "* * * ? * * *" //(1)!
            }
            quartz-short = "* * * ? * * *" //(2)!
        }
    }
    ```

    1. Выражение `cron`, запускающее задачу каждую секунду (`обязательный`, нет значения по умолчанию)
    2. Краткая форма: значение самого пути `config` является выражением `cron`

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        quartz:
          cron: "* * * ? * * *" #(1)!
        quartz-short: "* * * ? * * *" #(2)!
    ```

    1. Выражение `cron`, запускающее задачу каждую секунду (`обязательный`, нет значения по умолчанию)
    2. Краткая форма: значение самого пути `config` является выражением `cron`

### Trigger { #trigger }

Для собственного расписания можно создать `Trigger` из библиотеки `Quartz`, зарегистрировать его в графе зависимостей с тегом
и затем передать класс этого тега в аннотацию `@ScheduleQuartzWithTrigger`.

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

        @ScheduleQuartzWithTrigger(SomeService.class) //(2)!
        void schedule() {
            // do something
        }
    }
    ```

    1. Тег, с которым `Trigger` регистрируется в графе зависимостей.
    2. Тот же тег, по которому задача получает `Trigger`.

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

        @ScheduleQuartzWithTrigger(SomeService::class) //(2)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Тег, с которым `Trigger` регистрируется в графе зависимостей.
    2. Тот же тег, по которому задача получает `Trigger`.

У `@ScheduleQuartzWithTrigger` нет атрибута `config`: всё расписание выражается самим компонентом `Trigger`.

### Неконкурентное выполнение { #non-concurrent-execution }

Аннотация `@DisallowConcurrentExecution` запрещает одновременное выполнение одного и того же метода планировщиком `Quartz`.
Это аналог `org.quartz.DisallowConcurrentExecution` в `Kora`, он ставится на метод, помеченный `@Schedule*`;
исходная аннотация `org.quartz.DisallowConcurrentExecution` на классе даёт тот же эффект для всех его задач.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @DisallowConcurrentExecution
        @ScheduleQuartzWithCron(config = "scheduling.jobs.quartz")
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
        @ScheduleQuartzWithCron(config = "scheduling.jobs.quartz")
        fun schedule() {
            // do something
        }
    }
    ```

### Контекст задачи { #job-context }

Метод задачи `Quartz` может опционально объявить единственный аргумент типа `org.quartz.JobExecutionContext`.
Если он присутствует, `Kora` передаёт в метод текущий контекст выполнения; если отсутствует, метод вызывается без аргументов.
Контекст даёт доступ к `org.quartz.JobDataMap` задачи — это способ читать и записывать состояние, связанное с задачей:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleQuartzWithCron(config = "scheduling.jobs.quartz")
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

        @ScheduleQuartzWithCron(config = "scheduling.jobs.quartz")
        fun schedule(context: JobExecutionContext) {
            val data = context.jobDetail.jobDataMap
            val counter = if (data.containsKey("counter")) data.getInt("counter") else 0
            data.put("counter", counter + 1)
        }
    }
    ```

### Сохранение данных задачи { #persistent-execution }

Аннотация `@PersistJobDataAfterExecution` указывает `Quartz` сохранить обновлённый `org.quartz.JobDataMap` после выполнения задачи,
чтобы изменения, сделанные через [JobExecutionContext](#job-context), были видны в следующем выполнении.

Её рекомендуется использовать вместе с `@DisallowConcurrentExecution`,
чтобы избежать конфликтов хранения данных при одновременном выполнении задачи.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @DisallowConcurrentExecution
        @PersistJobDataAfterExecution
        @ScheduleQuartzWithCron(config = "scheduling.jobs.quartz")
        void schedule(JobExecutionContext context) {
            JobDataMap data = context.getJobDetail().getJobDataMap();
            int counter = data.containsKey("counter") ? data.getInt("counter") : 0;
            data.put("counter", counter + 1); //(1)!
        }
    }
    ```

    1. Обновлённое значение сохраняется после выполнения и доступно в следующем запуске

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @DisallowConcurrentExecution
        @PersistJobDataAfterExecution
        @ScheduleQuartzWithCron(config = "scheduling.jobs.quartz")
        fun schedule(context: JobExecutionContext) {
            val data = context.jobDetail.jobDataMap
            val counter = if (data.containsKey("counter")) data.getInt("counter") else 0
            data.put("counter", counter + 1) //(1)!
        }
    }
    ```

    1. Обновлённое значение сохраняется после выполнения и доступно в следующем запуске

### Плавная остановка { #graceful-shutdown-quartz }

При [плавной остановке](container.md#component-lifecycle) `scheduling.quartz.shutdownWait` по умолчанию равен `30s`. Quartz прекращает запуск новых задач, ждёт работающие задачи не дольше указанного времени, прерывает оставшиеся и ждёт ещё столько же. Поэтому остановка может занять вдвое больше заданного времени. Значение `0s` прерывает задачи сразу. Долгие задачи должны обрабатывать прерывание.

### Постоянное хранилище задач { #persistent-job-store }

При постоянном `JobStore` (например, `org.quartz.impl.jdbcjobstore.JobStoreTX`) задачи и триггеры переживают перезапуск приложения,
поэтому при каждом старте и обновлении графа Kora сверяет сохранённое состояние с задачами, присутствующими в графе приложения.
Этой сверкой управляют два параметра:

- `scheduling.quartz.cleanupOrphanedJobs` (по умолчанию: `false`) при старте планировщика удаляет из хранилища все задачи, которые больше не зарегистрированы в графе приложения,
  например после удаления или переименования класса с `@ScheduleQuartzWithCron`.
  При выключенном значении такие «осиротевшие» задачи остаются в хранилище, и `Quartz` при каждом старте логирует
  `JobPersistenceException: Couldn't retrieve job because a required class was not found`, пока их повторно обрабатывает обработчик misfire.
- `scheduling.quartz.compareStartTime` (по умолчанию: `false`) дополнительно сравнивает время начала сохранённого триггера. По умолчанию перепланирование происходит при изменении расписания или времени окончания; время начала игнорируется, поскольку Quartz задаёт его в момент создания триггера. Включайте опцию только для фиксированных значений `startAt()`.

!!! warning "Включайте `cleanupOrphanedJobs` с осторожностью"

    Очистка удаляет управляемые Kora задачи, отсутствующие в текущем графе; задачи, добавленные напрямую через `org.quartz.Scheduler`, остаются. Используйте отдельное хранилище для одного приложения. Приложения с общим хранилищем или разные версии при поэтапном развёртывании могут удалить задачи Kora друг друга.

### Scheduler { #scheduler }

Нижележащий `org.quartz.Scheduler` зарегистрирован как компонент и может быть внедрён для продвинутых сценариев,
таких как программная регистрация задач или анализ состояния планировщика:

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

Каждая объявленная задача регистрируется как durable `JobDetail`, идентификатором которого является каноническое имя сгенерированного класса задачи.
Регистрация повторяется при обновлении графа зависимостей: триггеры с изменившимся определением перепланируются,
а триггеры, которых больше нет, удаляются.
