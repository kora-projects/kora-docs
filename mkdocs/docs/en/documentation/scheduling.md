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

Scheduled methods must satisfy the following requirements:

- The enclosing class must be a component in the [dependency graph](container.md), for example annotated with `@Component`.
- The native scheduler method must have no arguments (the `Quartz` scheduler additionally allows an optional [JobExecutionContext](#job-context) argument).
- The method return value is ignored.
- In `Kotlin` the method must not be a `suspend` function.

!!! warning "Interval is required"

    `@ScheduleAtFixedRate` requires `period` and `@ScheduleWithFixedDelay` requires `delay`.
    If neither the annotation attribute (its default is `0`) nor a `config` path providing the value is set,
    compilation fails with `Either period() or config() annotation parameter must be provided`.

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

A specific task configuration may also contain its own `telemetry` section, which overrides the scheduler-wide `scheduling.telemetry` for that task only.
Unset values fall back to the common configuration, so it is enough to specify only what should differ:

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

    1. Overrides `scheduling.telemetry.logging.enabled` for this task only
    2. Overrides `scheduling.telemetry.metrics.enabled` for this task only

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

    1. Overrides `scheduling.telemetry.logging.enabled` for this task only
    2. Overrides `scheduling.telemetry.metrics.enabled` for this task only

Observability of scheduled tasks can also be customized in code by registering a component that implements
`SchedulingLoggerFactory`, `SchedulingMetricsFactory`, `SchedulingTracerFactory`, or the whole `SchedulingTelemetryFactory`.

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

Parameters can be passed through configuration; the configuration has priority over annotation values.
The `config` path is arbitrary, but by convention it is nested under the `scheduling` section so that a task's
parameters and its `telemetry` live together (as in the [example project](https://github.com/kora-projects/kora-examples), `scheduling.jobs.fix-rate`):

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

Configuration file example:

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

    1. Initial delay before the first task (default: `0ms`)
    2. Periodic interval between tasks (`required`, no default)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        fix-rate:
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

Configuration file example:

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

    1. Initial delay before the first task (default: `0ms`)
    2. Periodic delay between tasks (`required`, no default)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        fix-delay:
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

Configuration file example:

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

    1. Delay before the task (`required`, no default)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        once:
          delay: "50ms" #(1)!
    ```

    1. Delay before the task (`required`, no default)

### Graceful Shutdown { #graceful-shutdown }

During [graceful shutdown](container.md#component-lifecycle), the native scheduler waits for tasks to complete for `scheduling.shutdownWait`.
If a task needs to stop earlier, check [Thread.currentThread().isInterrupted()](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#isInterrupted--) and stop the work manually.

### Programmatic Scheduling { #programmatic }

For scheduling tasks in imperative style, the `JdkSchedulingExecutor` component can be injected.
It wraps the same `ScheduledExecutorService` as the annotations and exposes the `scheduleAtFixedRate`, `scheduleWithFixedDelay`, and `schedule` methods:

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

A `Quartz` expression has six required fields and an optional seventh year field, separated by spaces:

| Field        | Allowed values      | Required |
|--------------|---------------------|----------|
| Seconds      | `0-59`              | yes      |
| Minutes      | `0-59`              | yes      |
| Hours        | `0-23`              | yes      |
| Day of month | `1-31`              | yes      |
| Month        | `1-12` or `JAN-DEC` | yes      |
| Day of week  | `1-7` or `SUN-SAT`  | yes      |
| Year         | empty, `1970-2099`  | no       |

Besides plain numbers, ranges (`8-10`), lists (`6,19`), and steps (`0/30`), the following special characters are supported:

| Character | Meaning                                                                                          |
|-----------|--------------------------------------------------------------------------------------------------|
| `*`       | All values of the field (for example `*` in the minute field means "every minute")               |
| `?`       | No specific value, used in the day-of-month or day-of-week field when the other one is specified |
| `L`       | Last (last day of the month, or last given weekday of the month)                                 |
| `W`       | Nearest weekday to the given day of month                                                        |
| `#`       | The N-th given weekday of the month, for example `5#2` is the second Friday                       |

Expression examples:

| Expression          | Meaning                                     |
|---------------------|---------------------------------------------|
| `0 0 * * * ?`       | The top of every hour of every day          |
| `*/10 * * * * ?`    | Every ten seconds                           |
| `0 0 8-10 * * ?`    | 8, 9 and 10 o'clock of every day            |
| `0 0/30 8-10 * * ?` | 8:00, 8:30, 9:00, 9:30, 10:00 and 10:30     |
| `0 0 0 L * ?`       | Last day of the month at midnight           |
| `0 0 0 1W * ?`      | First weekday of the month at midnight      |
| `0 0 0 ? * 5#2`     | The second Friday of the month at midnight  |

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

    1. `cron` expression that runs the task every second

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

    1. `cron` expression that runs the task every second

The `identity` attribute sets the [Quartz Trigger identity](https://www.quartz-scheduler.org/api/2.3.0/org/quartz/TriggerBuilder.html)
used to name the task, which is useful for identifying and replacing tasks, especially with clustered or persistent `JobStore` implementations:

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

    1. `cron` expression that runs the task at the top of every hour, registered under the trigger identity `my-hourly-job`

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

    1. `cron` expression that runs the task at the top of every hour, registered under the trigger identity `my-hourly-job`

#### Configuration { #configuration-6 }

Parameters can be passed through configuration; the configuration has priority over annotation values.
As with the native scheduler, the `config` path is arbitrary and by convention is nested under the `scheduling` section
(as in the [example project](https://github.com/kora-projects/kora-examples), `scheduling.jobs.quartz`):

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

Configuration example:

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

    1. `cron` expression that runs the task every second (`required`, no default)

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        quartz:
          cron: "* * * ? * * *" #(1)!
    ```

    1. `cron` expression that runs the task every second (`required`, no default)

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
It is the `Kora` counterpart of `org.quartz.DisallowConcurrentExecution` and can be placed on any `@Schedule*`-annotated method.

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

### Job Context { #job-context }

A `Quartz` scheduled method may optionally declare a single `org.quartz.JobExecutionContext` argument.
When it is present, `Kora` passes the current execution context to the method; when it is absent, the method is called with no arguments.
The context gives access to the task's `org.quartz.JobDataMap`, which is the way to read and write state associated with the task:

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

### Persisting Job Data { #persistent-execution }

The `@PersistJobDataAfterExecution` annotation tells `Quartz` to store the updated `org.quartz.JobDataMap` back after task execution,
so that the changes made through the [JobExecutionContext](#job-context) are visible in the next execution.

It is recommended to use it together with `@DisallowConcurrentExecution`
to avoid data storage conflicts during concurrent task execution.

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

    1. The updated value is persisted after execution and available in the next run

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

    1. The updated value is persisted after execution and available in the next run

### Graceful Shutdown { #graceful-shutdown-quartz }

During [graceful shutdown](container.md#component-lifecycle), the `scheduling.waitForJobComplete` option controls how the `Quartz` scheduler stops.
With `true` (default) it calls `scheduler.shutdown(true)` and blocks until running tasks finish; with `false` it stops without waiting.
As with the native scheduler, long-running tasks should still cooperatively check
[Thread.currentThread().isInterrupted()](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#isInterrupted--) and stop the work manually.

### Scheduler { #scheduler }

The underlying `org.quartz.Scheduler` is registered as a component and can be injected for advanced scenarios,
such as registering tasks programmatically or inspecting the scheduler state:

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
