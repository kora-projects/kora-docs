---
description: "Explains Kora scheduling for native and Quartz schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, shutdown, and concurrency controls. Use when working with @ScheduleAtFixedRate, @ScheduleWithFixedDelay, @ScheduleOnce, @ScheduleWithCron, @ScheduleWithTrigger, @DisallowConcurrentExecution, SchedulingModule, QuartzModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora scheduling for native and Quartz schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, shutdown, and concurrency controls; key triggers include @ScheduleAtFixedRate, @ScheduleWithFixedDelay, @ScheduleOnce, @ScheduleWithCron, @ScheduleWithTrigger, @DisallowConcurrentExecution, SchedulingModule, QuartzModule."
---

Модуль планирования задач Kora позволяет запускать методы приложения по расписанию в декларативном стиле через аннотации.
Kora на этапе компиляции генерирует компоненты задач и подключает их к выбранному механизму планирования.

Доступны два варианта: встроенный планировщик на основе `ScheduledExecutorService` из `JDK` и планировщик на основе `Quartz`.
Встроенный вариант подходит для простых периодических задач внутри одного приложения, а `Quartz` нужен для `cron`-выражений, собственных `Trigger` и дополнительных правил выполнения задач.

## Встроенный планировщик { #native }

Встроенный планировщик использует стандартный [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html), который поставляется вместе с `JDK`.

Для создания задач через аспекты используются специальные аннотации, которые соответствуют методам `ScheduledExecutorService`.
Параметры аннотаций соответствуют параметрам методов `scheduleAtFixedRate`, `scheduleWithFixedDelay`, `schedule` соответственно.

Все аннотации имеют параметр `config`.
Если он указан, значения параметров берутся из конфигурации по этому пути и имеют приоритет над значениями в аннотации.
В конфигурации конкретной задачи также можно указать секцию `telemetry`; ее значения переопределят общую телеметрию планировщика для этой задачи.

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

Пример полной конфигурации, описанной в классе `ScheduledExecutorServiceConfig` (указаны значения по умолчанию):

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

    1.  Максимальное количество потоков у [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) (по умолчанию: `2`)
    2.  Время ожидания выполнения задач перед выключением планировщика при [штатном завершении](container.md#component-lifecycle) (по умолчанию: `30s`)
    3.  Включает логирование модуля (по умолчанию: `false`)
    4.  Включает метрики модуля (по умолчанию: `true`)
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6.  Настройка тегов для метрик (по умолчанию: `{}`)
    7.  Включает трассировку модуля (по умолчанию: `true`)
    8.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  Максимальное количество потоков у [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) (по умолчанию: `2`)
    2.  Время ожидания выполнения задач перед выключением планировщика при [штатном завершении](container.md#component-lifecycle) (по умолчанию: `30s`)
    3.  Включает логирование модуля (по умолчанию: `false`)
    4.  Включает метрики модуля (по умолчанию: `true`)
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6.  Настройка тегов для метрик (по умолчанию: `{}`)
    7.  Включает трассировку модуля (по умолчанию: `true`)
    8.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#scheduling).

### Фиксированный интервал { #fixed-rate }

Планирование с запуском задач через фиксированный интервал времени, независимо от того, завершилось ли предыдущее выполнение.
Такой подход может привести к одновременному выполнению нескольких задач.

Например, если период установлен в 10 секунд, а каждое выполнение задачи занимает 5 секунд,
то следующая задача запустится через 5 секунд после завершения предыдущей.

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

Параметры можно передать через конфигурацию, она имеет приоритет над значениями в аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleAtFixedRate(config = "job")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleAtFixedRate(config = "job")
        fun schedule() {
            // do something
        }
    }
    ```

Пример конфигурации через файл:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        initialDelay = "50ms" //(1)!
        period = "50ms" //(2)!
    }
    ```

    1.  Начальный интервал задержки перед первой задачей (по умолчанию: `0ms`)
    2.  Периодический интервал между задачами (`обязательная`, по умолчанию не указано)

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      initialDelay: "50ms" #(1)!
      period: "50ms" #(2)!
    ```

    1.  Начальный интервал задержки перед первой задачей (по умолчанию: `0ms`)
    2.  Периодический интервал между задачами (`обязательная`, по умолчанию не указано)

### Фиксированная задержка { #fixed-delay }

Планировщик ожидает фиксированный промежуток времени от окончания предыдущего исполнения задачи.
Выполнения нескольких задач не будет происходить одновременно.

Не имеет значения, сколько времени занимает текущее исполнение,
следующая задача запустится после завершения предыдущей задачи и заданного промежутка ожидания.

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

Параметры можно передать через конфигурацию, она имеет приоритет над значениями в аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithFixedDelay(config = "job")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleWithFixedDelay(config = "job")
        fun schedule() {
            // do something
        }
    }
    ```

Пример конфигурации через файл:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        initialDelay = "50ms" //(1)!
        delay = "50ms" //(2)!
    }
    ```

    1.  Начальный интервал задержки перед первой задачей (по умолчанию: `0ms`)
    2.  Периодический интервал задержки между задачами (`обязательная`, по умолчанию не указано)

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      initialDelay: "50ms" #(1)!
      delay: "50ms" #(2)!
    ```

    1.  Начальный интервал задержки перед первой задачей (по умолчанию: `0ms`)
    2.  Периодический интервал задержки между задачами (`обязательная`, по умолчанию не указано)

### Одноразовый { #once }

Запускает задачу один раз через заданный интервал времени.

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

Параметры можно передать через конфигурацию, она имеет приоритет над значениями в аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleOnce(config = "job")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleOnce(config = "job")
        fun schedule() {
            // do something
        }
    }
    ```

Пример конфигурации через файл:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        delay = "50ms" //(1)!
    }
    ```

    1.  Интервал задержки перед задачей (`обязательная`, по умолчанию не указано)

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      delay: "50ms" #(1)!
    ```

    1.  Интервал задержки перед задачей (`обязательная`, по умолчанию не указано)

### Штатное завершение { #graceful-shutdown }

При [штатном завершении](container.md#component-lifecycle) встроенный планировщик ожидает завершения задач в течение `scheduling.shutdownWait`.
Если задачу нужно завершить раньше, проверяйте статус [Thread.currentThread().isInterrupted()](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#isInterrupted--) и прекращайте работу самостоятельно.

## Quartz { #quartz }

Реализация на основе библиотеки [Quartz](https://www.quartz-scheduler.org/) используется для задач с `cron`-расписанием, собственными `Trigger` и правилами выполнения `Quartz`.

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

Конфигурация `Quartz` указывается как значения [Properties](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/configuration/) в формате ключ-значение.
Настройки Kora для штатного завершения и телеметрии задаются в секции `scheduling`.
В конфигурации конкретной `cron`-задачи также можно указать секцию `telemetry`; ее значения переопределят общую телеметрию планировщика для этой задачи.

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

    1.  Параметры настройки планировщика `Quartz` (по умолчанию используются свойства из `quartz.properties` ниже)
    2.  Ожидать ли выполнения задач перед выключением планировщика при [штатном завершении](container.md#component-lifecycle) (по умолчанию: `true`)
    3.  Включает логирование модуля (по умолчанию: `false`)
    4.  Включает метрики модуля (по умолчанию: `true`)
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6.  Настройка тегов для метрик (по умолчанию: `{}`)
    7.  Включает трассировку модуля (по умолчанию: `true`)
    8.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  Параметры настройки планировщика `Quartz` (по умолчанию используются свойства из `quartz.properties` ниже)
    2.  Ожидать ли выполнения задач перед выключением планировщика при [штатном завершении](container.md#component-lifecycle) (по умолчанию: `true`)
    3.  Включает логирование модуля (по умолчанию: `false`)
    4.  Включает метрики модуля (по умолчанию: `true`)
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6.  Настройка тегов для метрик (по умолчанию: `{}`)
    7.  Включает трассировку модуля (по умолчанию: `true`)
    8.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

По умолчанию используются настройки из:

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

### Крон { #cron }

Использование [`cron`-выражений](http://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html) для запуска запланированных задач.

`Quartz` использует формат из шести обязательных полей и одного необязательного поля года: секунды, минуты, часы, день месяца, месяц, день недели и год.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithCron("0 0 * * * * ?") //(1)!
        void schedule() {
            // do something
        }
    }
    ```

    1. `cron`-выражение, которое запускает задачу каждый час каждый день

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleWithCron("0 0 * * * * ?") //(1)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. `cron`-выражение, которое запускает задачу каждый час каждый день

#### Конфигурация { #configuration-6 }

Параметры можно передать через конфигурацию, она имеет приоритет над значениями в аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @ScheduleWithCron(config = "job")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @ScheduleWithCron(config = "job")
        fun schedule() {
            // do something
        }
    }
    ```

Пример конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        cron = "0 0 * * * * ?" //(1)!
    }
    ```

    1. `cron`-выражение, которое запускает задачу каждый час каждый день (`обязательная`, по умолчанию не указано)

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      cron: "0 0 * * * * ?" #(1)!
    ```

    1. `cron`-выражение, которое запускает задачу каждый час каждый день (`обязательная`, по умолчанию не указано)

### Триггер { #trigger }

Для собственного расписания можно создать `Trigger` из библиотеки `Quartz`, зарегистрировать его в графе зависимостей с тегом и затем использовать этот тег в аннотации `@ScheduleWithTrigger`.

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

    1. Тег, по которому `Trigger` регистрируется в графе зависимостей.
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

        @ScheduleWithTrigger(@Tag(SomeService::class)) //(2)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Тег, по которому `Trigger` регистрируется в графе зависимостей.
    2. Тот же тег, по которому задача получает `Trigger`.

### Неконкурентный запуск { #non-concurrent-execution }

Аннотация `@DisallowConcurrentExecution` запрещает параллельное выполнение одного и того же метода планировщиком `Quartz`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @DisallowConcurrentExecution
        @ScheduleWithCron(config = "job")
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
        @ScheduleWithCron(config = "job")
        fun schedule() {
            // do something
        }
    }
    ```

### Сохранение данных задачи { #persistent-execution }

Аннотация `@PersistJobDataAfterExecution` указывает `Quartz`, что после выполнения задачи нужно сохранить обновленное состояние `org.quartz.JobDataMap`.

Рекомендуется использовать совместно с аннотацией `@DisallowConcurrentExecution`,
чтобы избежать конфликтов при сохранении данных во время одновременного выполнения задач.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @PersistJobDataAfterExecution
        @ScheduleWithCron(config = "job")
        void schedule() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @PersistJobDataAfterExecution
        @ScheduleWithCron(config = "job")
        fun schedule() {
            // do something
        }
    }
    ```
