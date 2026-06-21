---
description: "Explains Kora scheduling for native and Quartz schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, shutdown, and concurrency controls. Use when working with @ScheduleAtFixedRate, @ScheduleWithFixedDelay, @ScheduleOnce, @ScheduleWithCron, @ScheduleWithTrigger, @DisallowConcurrentExecution, SchedulingModule, QuartzModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora scheduling for native and Quartz schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, shutdown, and concurrency controls; key triggers include @ScheduleAtFixedRate, @ScheduleWithFixedDelay, @ScheduleOnce, @ScheduleWithCron, @ScheduleWithTrigger, @DisallowConcurrentExecution, SchedulingModule, QuartzModule."
---

The Kora scheduling module allows application methods to run on a schedule in a declarative style through annotations.
At compile time, Kora generates task components and connects them to the selected scheduling mechanism.

Two options are available: the native scheduler based on `ScheduledExecutorService` from the `JDK`, and the scheduler based on `Quartz`.
The native option is suitable for simple periodic tasks inside one application, while `Quartz` is useful for `cron` expressions, custom `Trigger` instances, and additional task execution rules.

## Native Scheduler { #native }

The native scheduler uses the standard [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) that comes with the `JDK`.

Special annotations are used to create tasks through aspects, and they correspond to `ScheduledExecutorService` methods.
Annotation parameters match the parameters of the `scheduleAtFixedRate`, `scheduleWithFixedDelay`, and `schedule` methods.

All annotations have the `config` parameter.
If it is specified, parameter values are taken from the configuration at that path and have priority over annotation values.
The configuration of a specific task can also contain the `telemetry` section; its values override the common scheduler telemetry for that task.

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:scheduling-jdk"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends SchedulingJdkModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("ru.tinkoff.kora:scheduling-jdk")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : SchedulingJdkModule
    ```

### Configuration { #configuration }

Complete configuration example described by the `ScheduledExecutorServiceConfig` class with default values:

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

    1. Maximum number of threads in [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) (default: `2`)
    2. Time to wait for tasks to complete before scheduler shutdown during [graceful shutdown](container.md#component-lifecycle) (default: `30s`)
    3. Enables module logging (default: `false`)
    4. Enables module metrics (default: `true`)
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Configures metric tags (default: `{}`)
    7. Enables module tracing (default: `true`)
    8. Configures tracing attributes (default: `{}`)

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

    1. Maximum number of threads in [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) (default: `2`)
    2. Time to wait for tasks to complete before scheduler shutdown during [graceful shutdown](container.md#component-lifecycle) (default: `30s`)
    3. Enables module logging (default: `false`)
    4. Enables module metrics (default: `true`)
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Configures metric tags (default: `{}`)
    7. Enables module tracing (default: `true`)
    8. Configures tracing attributes (default: `{}`)

Module metrics are described in the [Metrics Reference](metrics.md#scheduling) section.

### Fixed Rate { #fixed-rate }

Scheduling with tasks started at a fixed time interval, regardless of whether the previous execution has completed.
This can lead to concurrent execution of several tasks.

For example, if the period is 10 seconds and each task execution takes 5 seconds,
the next task starts 5 seconds after the previous one completes.

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

#### Configuration { #configuration-2 }

Parameters can be passed through configuration; it has priority over annotation values:

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

Configuration file example:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        initialDelay = "50ms" //(1)!
        period = "50ms" //(2)!
    }
    ```

    1. Initial delay before the first task (default: `0ms`)
    2. Periodic interval between tasks (`required`, no default)

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      initialDelay: "50ms" #(1)!
      period: "50ms" #(2)!
    ```

    1. Initial delay before the first task (default: `0ms`)
    2. Periodic interval between tasks (`required`, no default)

### Fixed Delay { #fixed-delay }

The scheduler waits for a fixed time interval from the end of the previous task execution.
Multiple executions of the same task will not happen concurrently.

It does not matter how long the current execution takes:
the next task starts after the previous task completes and the configured delay passes.

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

#### Configuration { #configuration-3 }

Parameters can be passed through configuration; it has priority over annotation values:

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

Configuration file example:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        initialDelay = "50ms" //(1)!
        delay = "50ms" //(2)!
    }
    ```

    1. Initial delay before the first task (default: `0ms`)
    2. Periodic delay between tasks (`required`, no default)

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      initialDelay: "50ms" #(1)!
      delay: "50ms" #(2)!
    ```

    1. Initial delay before the first task (default: `0ms`)
    2. Periodic delay between tasks (`required`, no default)

### Once { #once }

Runs a task once after the configured time interval.

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

#### Configuration { #configuration-4 }

Parameters can be passed through configuration; it has priority over annotation values:

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

Configuration file example:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        delay = "50ms" //(1)!
    }
    ```

    1. Delay before the task (`required`, no default)

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      delay: "50ms" #(1)!
    ```

    1. Delay before the task (`required`, no default)

### Graceful Shutdown { #graceful-shutdown }

During [graceful shutdown](container.md#component-lifecycle), the native scheduler waits for tasks to complete for `scheduling.shutdownWait`.
If a task needs to stop earlier, check [Thread.currentThread().isInterrupted()](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#isInterrupted--) and stop the work manually.

## Quartz { #quartz }

The implementation based on the [Quartz](https://www.quartz-scheduler.org/) library is used for tasks with `cron` schedules, custom `Trigger` instances, and `Quartz` execution rules.

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:scheduling-quartz"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends QuartzModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("ru.tinkoff.kora:scheduling-quartz")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : QuartzModule
    ```

### Configuration { #configuration-5 }

`Quartz` configuration is specified as [Properties](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/configuration/) values in key-value format.
Kora settings for graceful shutdown and telemetry are configured in the `scheduling` section.
The configuration of a specific `cron` task can also contain the `telemetry` section; its values override the common scheduler telemetry for that task.

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

    1. `Quartz` scheduler configuration parameters (by default, properties from `quartz.properties` below are used)
    2. Whether to wait for tasks to complete before scheduler shutdown during [graceful shutdown](container.md#component-lifecycle) (default: `true`)
    3. Enables module logging (default: `false`)
    4. Enables module metrics (default: `true`)
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Configures metric tags (default: `{}`)
    7. Enables module tracing (default: `true`)
    8. Configures tracing attributes (default: `{}`)

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

    1. `Quartz` scheduler configuration parameters (by default, properties from `quartz.properties` below are used)
    2. Whether to wait for tasks to complete before scheduler shutdown during [graceful shutdown](container.md#component-lifecycle) (default: `true`)
    3. Enables module logging (default: `false`)
    4. Enables module metrics (default: `true`)
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Configures metric tags (default: `{}`)
    7. Enables module tracing (default: `true`)
    8. Configures tracing attributes (default: `{}`)

Default settings are used from:

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

[`cron` expressions](http://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html) are used to run scheduled tasks.

`Quartz` uses a format with six required fields and one optional year field: seconds, minutes, hours, day of month, month, day of week, and year.

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

    1. `cron` expression that runs the task every hour every day

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

    1. `cron` expression that runs the task every hour every day

#### Configuration { #configuration-6 }

Parameters can be passed through configuration; it has priority over annotation values:

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

Configuration example:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        cron = "0 0 * * * * ?" //(1)!
    }
    ```

    1. `cron` expression that runs the task every hour every day (`required`, no default)

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      cron: "0 0 * * * * ?" #(1)!
    ```

    1. `cron` expression that runs the task every hour every day (`required`, no default)

### Trigger { #trigger }

For a custom schedule, you can create a `Trigger` from the `Quartz` library, register it in the dependency graph with a tag, and then use this tag in the `@ScheduleWithTrigger` annotation.

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

    1. Tag used to register the `Trigger` in the dependency graph.
    2. The same tag used by the task to receive the `Trigger`.

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

    1. Tag used to register the `Trigger` in the dependency graph.
    2. The same tag used by the task to receive the `Trigger`.

### Non-Concurrent Execution { #non-concurrent-execution }

The `@DisallowConcurrentExecution` annotation prevents concurrent execution of the same method by the `Quartz` scheduler.

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

### Persisting Job Data { #persistent-execution }

The `@PersistJobDataAfterExecution` annotation tells `Quartz` to save the updated `org.quartz.JobDataMap` state after task execution.

It is recommended to use it together with `@DisallowConcurrentExecution`
to avoid data storage conflicts during concurrent task execution.

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
