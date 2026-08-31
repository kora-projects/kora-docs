---
description: "Explains Kora scheduling for the JDK and Quartz schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, graceful shutdown, and concurrency controls. Use when working with @ScheduleAtFixedRate, @ScheduleWithFixedDelay, @ScheduleOnce, @ScheduleWithCron, @ScheduleWithTrigger, @DisallowConcurrentExecution, @PersistJobDataAfterExecution, SchedulingJdkModule, SchedulingJdkExecutor, CronExpression, QuartzModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora scheduling for the JDK and Quartz schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, graceful shutdown, and concurrency controls; key triggers include @ScheduleAtFixedRate, @ScheduleWithFixedDelay, @ScheduleOnce, @ScheduleWithCron, @ScheduleWithTrigger, @DisallowConcurrentExecution, @PersistJobDataAfterExecution, SchedulingJdkModule, SchedulingJdkExecutor, CronExpression, QuartzModule."
---

Модуль планирования Kora позволяет запускать методы приложения по расписанию в декларативном стиле через аннотации.
Во время компиляции Kora генерирует компоненты задач и связывает их с выбранным механизмом планирования.

Доступны два варианта: планировщик `JDK` на основе `ScheduledExecutorService` и планировщик на основе `Quartz`.
Оба поддерживают `cron`-выражения.
Планировщик `JDK` закрывает периодические и `cron`-задачи внутри одного приложения без дополнительных зависимостей,
а `Quartz` добавляет пользовательские экземпляры `Trigger`, подключаемый `JobStore`, правила выполнения задач и диалект `cron` от Quartz с модификаторами `L`, `W` и `#`.

## JDK Scheduler { #native }

Планировщик `JDK` использует стандартный [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html), который поставляется вместе с `JDK`.

Для создания задач используются специальные аннотации из пакета `io.koraframework.scheduling.jdk.annotation`:
`@ScheduleAtFixedRate`, `@ScheduleWithFixedDelay`, `@ScheduleOnce` и `@ScheduleWithCron`.

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

    - `@ScheduleAtFixedRate` — `Either period() or config() annotation parameter must be provided`
    - `@ScheduleWithFixedDelay` и `@ScheduleOnce` — `Either delay() or config() annotation parameter must be provided`
    - `@ScheduleWithCron` — `Either value() or config() annotation parameter must be provided`

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
        }
        telemetry {
            logging {
                enabled = false //(2)!
            }
            metrics {
                enabled = false //(3)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(4)!
                tags = { //(5)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(6)!
                attributes = { //(7)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1. Время, которое даётся пулу потоков на завершение задач перед принудительной остановкой при [плавной остановке](container.md#component-lifecycle) (по умолчанию: `30s`)
    2. Включает логирование модуля (по умолчанию: `false`)
    3. Включает метрики модуля (по умолчанию: `false`)
    4. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    5. Настройка тегов метрик (по умолчанию: `{}`)
    6. Включает трассировку модуля (по умолчанию: `true`)
    7. Настройка атрибутов трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jdk:
        shutdownWait: "30s" #(1)!
      telemetry:
        logging:
          enabled: false #(2)!
        metrics:
          enabled: false #(3)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(4)!
          tags: #(5)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(6)!
          attributes: #(7)!
            key1: value1
            key2: value2
    ```

    1. Время, которое даётся пулу потоков на завершение задач перед принудительной остановкой при [плавной остановке](container.md#component-lifecycle) (по умолчанию: `30s`)
    2. Включает логирование модуля (по умолчанию: `false`)
    3. Включает метрики модуля (по умолчанию: `false`)
    4. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    5. Настройка тегов метрик (по умолчанию: `{}`)
    6. Включает трассировку модуля (по умолчанию: `true`)
    7. Настройка атрибутов трассировки (по умолчанию: `{}`)

Пул потоков не конфигурируется: Kora создаёт `ScheduledThreadPoolExecutor`, размер ядра которого равен количеству задач, зарегистрированных в графе.
Его потоки называются `kora-scheduler-N`, не являются демонами, освобождаются после 30 секунд простоя, а отменённые задачи сразу удаляются из очереди.

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

Параметры можно передавать через конфигурацию, она имеет приоритет над значениями из аннотации.
Путь `config` произвольный, но по соглашению он вкладывается в секцию `scheduling`, чтобы параметры задачи
и её `telemetry` находились рядом (как в [проекте с примерами](https://github.com/kora-projects/kora-examples), `scheduling.jobs.fix-rate`):

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

Параметры можно передавать через конфигурацию, она имеет приоритет над значениями из аннотации:

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

Параметры можно передавать через конфигурацию, она имеет приоритет над значениями из аннотации:

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

После каждого выполнения задача вычисляет следующее время запуска от текущего момента в часовом поясе `JVM` по умолчанию
и планирует себя заново, поэтому долгое выполнение никогда не приводит к серии догоняющих запусков.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithCron("*/10 * * * * *") //(1)!
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

        @ScheduleWithCron("*/10 * * * * *") //(1)!
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

Выражение разбирается при построении графа зависимостей, а не во время компиляции,
поэтому некорректное выражение приводит к падению запуска приложения с `IllegalArgumentException` и указанием проблемного поля.
Если выражение больше никогда не может сработать — например, задан год в прошлом, — задача пишет предупреждение в лог и прекращает планировать себя.

#### Конфигурация { #configuration-jdk-cron }

Выражение можно передавать через конфигурацию, она имеет приоритет над значением из аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithCron(config = "scheduling.jobs.cron")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleWithCron(config = "scheduling.jobs.cron")
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

При [плавной остановке](container.md#component-lifecycle) компоненты освобождаются в обратном порядке зависимостей,
поэтому каждая задача освобождается раньше исполнителя, от которого она зависит.

Освобождение задачи дожидается выполнения, идущего в этот момент, и затем отменяет расписание, никого не прерывая,
поэтому новое выполнение не начинается, а задача, которая никогда не возвращает управление, блокирует остановку.
После этого исполнитель перестаёт принимать работу и ждёт завершения пула потоков не дольше `scheduling.jdk.shutdownWait`;
по истечении ожидания пул останавливается принудительно, работающие потоки прерываются, а в лог пишется
`SchedulingJdkExecutor failed completing graceful shutdown in ...`.

Поэтому долгие задачи следует писать так, чтобы они завершались сами,
и дополнительно можно проверять [Thread.currentThread().isInterrupted()](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html#isInterrupted()), чтобы остановиться раньше.

### Программное планирование { #programmatic }

Для планирования задач в императивном стиле можно внедрить компонент `SchedulingJdkExecutor`.
Он оборачивает тот же пул потоков, что и аннотации, и предоставляет методы `scheduleAtFixedRate`, `scheduleWithFixedDelay` и `scheduleOnce`,
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

Задачи, запланированные таким образом, являются обычными `Runnable`: они делят пул с задачами из аннотаций,
но не оборачиваются в телеметрию планировщика и не отменяются по отдельности при остановке.

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
            waitForJobComplete = true //(1)!
            properties { //(2)!
                "org.quartz.threadPool.threadCount" = "10"
            }
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

    1. Ожидать ли завершения задач перед остановкой планировщика при [плавной остановке](container.md#component-lifecycle) (по умолчанию: `true`)
    2. Параметры конфигурации планировщика `Quartz`, накладываемые поверх значений по умолчанию ниже (опционально)
    3. Включает логирование модуля (по умолчанию: `false`)
    4. Включает метрики модуля (по умолчанию: `false`)
    5. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Настройка тегов метрик (по умолчанию: `{}`)
    7. Включает трассировку модуля (по умолчанию: `true`)
    8. Настройка атрибутов трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      quartz:
        waitForJobComplete: true #(1)!
        properties: #(2)!
          org.quartz.threadPool.threadCount: "10"
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

    1. Ожидать ли завершения задач перед остановкой планировщика при [плавной остановке](container.md#component-lifecycle) (по умолчанию: `true`)
    2. Параметры конфигурации планировщика `Quartz`, накладываемые поверх значений по умолчанию ниже (опционально)
    3. Включает логирование модуля (по умолчанию: `false`)
    4. Включает метрики модуля (по умолчанию: `false`)
    5. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Настройка тегов метрик (по умолчанию: `{}`)
    7. Включает трассировку модуля (по умолчанию: `true`)
    8. Настройка атрибутов трассировки (по умолчанию: `{}`)

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

        @ScheduleWithCron("* * * ? * * *") //(1)!
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

        @ScheduleWithCron("* * * ? * * *") //(1)!
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

        @ScheduleWithCron(value = "0 0 * * * ?", identity = "my-hourly-job") //(1)!
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

        @ScheduleWithCron(value = "0 0 * * * ?", identity = "my-hourly-job") //(1)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Выражение `cron`, запускающее задачу в начале каждого часа, зарегистрированное под идентификатором триггера `my-hourly-job`

!!! warning "Источник cron обязателен"

    `@ScheduleWithCron` должна получить выражение либо из `value()`, либо из `config()`.
    Если не задано ни то, ни другое, компиляция завершается ошибкой `Quartz @ScheduleWithCron on '...' has no cron source.`

#### Конфигурация { #configuration-6 }

Параметры можно передавать через конфигурацию, она имеет приоритет над значениями из аннотации.
Как и для планировщика `JDK`, путь `config` произвольный и по соглашению вкладывается в секцию `scheduling`
(как в [проекте с примерами](https://github.com/kora-projects/kora-examples), `scheduling.jobs.quartz`):

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
и затем передать класс этого тега в аннотацию `@ScheduleWithTrigger`.

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

        @ScheduleWithTrigger(SomeService.class) //(2)!
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

        @ScheduleWithTrigger(SomeService::class) //(2)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Тег, с которым `Trigger` регистрируется в графе зависимостей.
    2. Тот же тег, по которому задача получает `Trigger`.

У `@ScheduleWithTrigger` нет атрибута `config`: всё расписание выражается самим компонентом `Trigger`.

### Неконкурентное выполнение { #non-concurrent-execution }

Аннотация `@DisallowConcurrentExecution` запрещает одновременное выполнение одного и того же метода планировщиком `Quartz`.
Это аналог `org.quartz.DisallowConcurrentExecution` в `Kora`, он ставится на метод, помеченный `@Schedule*`;
исходная аннотация `org.quartz.DisallowConcurrentExecution` на классе даёт тот же эффект для всех его задач.

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

Метод задачи `Quartz` может опционально объявить единственный аргумент типа `org.quartz.JobExecutionContext`.
Если он присутствует, `Kora` передаёт в метод текущий контекст выполнения; если отсутствует, метод вызывается без аргументов.
Контекст даёт доступ к `org.quartz.JobDataMap` задачи — это способ читать и записывать состояние, связанное с задачей:

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
        @ScheduleWithCron(config = "scheduling.jobs.quartz")
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
        @ScheduleWithCron(config = "scheduling.jobs.quartz")
        fun schedule(context: JobExecutionContext) {
            val data = context.jobDetail.jobDataMap
            val counter = if (data.containsKey("counter")) data.getInt("counter") else 0
            data.put("counter", counter + 1) //(1)!
        }
    }
    ```

    1. Обновлённое значение сохраняется после выполнения и доступно в следующем запуске

### Плавная остановка { #graceful-shutdown-quartz }

При [плавной остановке](container.md#component-lifecycle) опция `scheduling.quartz.waitForJobComplete` определяет, как останавливается планировщик `Quartz`.
При значении `true` (по умолчанию) вызывается `scheduler.shutdown(true)` и остановка блокируется до завершения выполняющихся задач; при `false` планировщик останавливается без ожидания.
Как и в случае планировщика `JDK`, долгие задачи всё равно должны кооперативно проверять
[Thread.currentThread().isInterrupted()](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html#isInterrupted()) и завершать работу самостоятельно.

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
