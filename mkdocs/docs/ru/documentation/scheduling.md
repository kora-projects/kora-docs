Модуль для создания планировщиков в декларативном стиле с помощью аннотаций.

## Нативный

Создание планировщика с использованием стандартного [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) который поставляется с JVM.

Для создания планировщика через аспекты используются специальные аннотации которые по сути дублируются сигнатуры методов `ScheduledExecutorService`.
Параметры аннотаций соответствуют параметрам методов `scheduleAtFixedRate`, `scheduleWithFixedDelay`, `schedule` соответственно.

Так же все аннотации имеют аргумент `config` при наличии которого значения параметра возьмутся из конфигурации по указанному пути.

### Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:scheduling-jdk"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends SchedulingJdkModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:scheduling-jdk")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : SchedulingJdkModule
    ```

### Конфигурация

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
            }
            tracing {
                enabled = true //(6)!
            }
        }
    }
    ```

    1.  Максимальное кол-во потоков у [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html)
    2.  Время ожидания выполнения задач перед выключением планировщика в случае [штатного завершения](container.md#_24)
    3.  Включает логгирование модуля (по умолчанию `false`)
    4.  Включает метрики модуля (по умолчанию `true`)
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    6.  Включает трассировку модуля (по умолчанию `true`)

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
        telemetry:
          enabled: true #(6)!
    ```

    1.  Максимальное кол-во потоков у [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html)
    2.  Время ожидания выполнения задач перед выключением планировщика в случае [штатного завершения](container.md#_24)
    3.  Включает логгирование модуля (по умолчанию `false`)
    4.  Включает метрики модуля (по умолчанию `true`)
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    6.  Включает трассировку модуля (по умолчанию `true`)

### Фиксированный интервал

Планирование с запуском задач с фиксированными промежутками времени, независимо от того, завершилась ли предыдущая или нет
Такой подход может привести к одновременному выполнению нескольких задач.

Например, если период установлен в 10 секунд, а каждое выполнение задачи занимает 5 секунд,
то след задача запуститься через 5 секунд после выполнения предыдущей.

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

#### Конфигурация

Возможно передача параметров через конфигурацию, она имеет приоритет перед указанными в аннотации параметрами:

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

    1.  Начальный интервал задержки перед первой задачей
    2.  Переодический интервал между задачами

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      initialDelay: "50ms" #(1)!
      period: "50ms" #(2)!
    ```

    1.  Начальный интервал задержки перед первой задачей
    2.  Переодический интервал между задачами

### Фиксированная задержка

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

#### Конфигурация

Возможно передача параметров через конфигурацию, она имеет приоритет перед указанными в аннотации параметрами:

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

    1.  Начальный интервал задержки перед первой задачей
    2.  Переодический интервал задержки между задачами

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      initialDelay: "50ms" #(1)!
      delay: "50ms" #(2)!
    ```

    1.  Начальный интервал задержки перед первой задачей
    2.  Переодический интервал задержки между задачами

### Одноразовый

Запускает одиножды задачу через определенный фиксированный интервал времени.

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

#### Конфигурация

Возможно передача параметров через конфигурацию, она имеет приоритет перед указанными в аннотации параметрами:

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

    1.  Начальный интервал задержки перед задачей

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      delay: "50ms" #(1)!
    ```

    1.  Начальный интервал задержки перед задачей

### Штатное завершение

Если вы хотите предварительно завершить обработку при [штатном завершении](container.md#_24) сервиса не дожидаясь ее окончания, 
требуется проверять [Thread.currentThread().isInterrupted()](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#isInterrupted--) статус и прекращать работу самостоятельно.

## Quartz

Реализация на основе библиотеки [Quartz](https://www.baeldung.com/quartz) как планировщика для создания аспектов.

### Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:scheduling-quartz"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends QuartzModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:scheduling-quartz")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : QuartzModule
    ```

### Конфигурация

Конфигурация указывается как значения [Properties](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/configuration/) в формате ключ и значение:

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
            }
            tracing {
                enabled = true //(6)!
            }
        }
    }
    ```

    1.  Параметры настройки Quartz планировщика
    2.  Ожидать ли выполнения задач перед выключением планировщика в случае [штатного завершения](container.md#_24)
    3.  Включает логгирование модуля (по умолчанию `false`)
    4.  Включает метрики модуля (по умолчанию `true`)
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    6.  Включает трассировку модуля (по умолчанию `true`)

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
          slo: [ 3, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(5)!
        telemetry:
          enabled: true #(6)!
    ```

    1.  Параметры настройки Quartz планировщика
    2.  Ожидать ли выполнения задач перед выключением планировщика в случае [штатного завершения](container.md#_24)
    3.  Включает логгирование модуля (по умолчанию `false`)
    4.  Включает метрики модуля (по умолчанию `true`)
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    6.  Включает трассировку модуля (по умолчанию `true`)

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

### Крон

Использование [Cron](http://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html) выражений для запуска запланированных задач.

Запускает одиножды задачу через определенный фиксированный интервал времени.

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

    1. Cron выражение говорящее запускать задачу каждый час и каждый день

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

    1. Cron выражение говорящее запускать задачу каждый час и каждый день

#### Конфигурация

Возможно передача параметров через конфигурацию, она имеет приоритет перед указанными в аннотации параметрами:

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

    1. Cron выражение говорящее запускать задачу каждый час и каждый день

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      cron: "0 0 * * * * ?" #(1)!
    ```

    1. Cron выражение говорящее запускать задачу каждый час и каждый день

### Триггер

Предполагает создание собственного `триггера` на основе библиотеки Quartz и регистрация его в контейнере приложения с определенным тегом и последующее его использование через аннотацию.

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

    1. Тег триггера
    2. Тег триггера

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

        @ScheduleWithTrigger(@Tag(SomeService.class)) //(2)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Тег триггера
    2. Тег триггера
