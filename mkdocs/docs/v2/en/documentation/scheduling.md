---
seo_title: "Kora Scheduling: Cron, Fixed Rate, Quartz and db-scheduler Jobs"
seo_description: "Reference for Kora scheduling: JDK, Quartz and database-backed db-scheduler jobs, fixed rate, fixed delay, one-shot and cron jobs, triggers, graceful shutdown."
keywords: ["Kora Framework", "Kora scheduling", "cron jobs Java", "Quartz", "db-scheduler", "scheduled tasks", "@ScheduleJdkAtFixedRate", "virtual threads"]
description: "Explains Kora scheduling for the JDK, Quartz and db-scheduler schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, virtual-thread execution, persistent database jobs, graceful shutdown, and concurrency controls. Use when working with @ScheduleJdkAtFixedRate, @ScheduleJdkWithFixedDelay, @ScheduleJdkOnce, @ScheduleJdkWithCron, @ScheduleQuartzWithTrigger, @DisallowConcurrentExecution, @PersistJobDataAfterExecution, SchedulingJdkModule, SchedulingJdkExecutor, VirtualThreadSchedulingJdkExecutor, CronExpression, QuartzModule, DbSchedulerModule, DbSchedulerConfig, KoraDbScheduler, DbSchedulerJob."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora scheduling for the JDK, Quartz and db-scheduler schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, virtual-thread execution, persistent database jobs, graceful shutdown, and concurrency controls; key triggers include @ScheduleJdkAtFixedRate, @ScheduleJdkWithFixedDelay, @ScheduleJdkOnce, @ScheduleJdkWithCron, @ScheduleQuartzWithTrigger, @DisallowConcurrentExecution, @PersistJobDataAfterExecution, SchedulingJdkModule, SchedulingJdkExecutor, VirtualThreadSchedulingJdkExecutor, executionParallelism, CronExpression, QuartzModule, scheduling-db-scheduler, DbSchedulerModule, DbSchedulerConfig, KoraDbScheduler, DbSchedulerJob, Configurer<SchedulerBuilder>."
---

The Kora scheduling module allows application methods to run on a schedule in a declarative style through annotations.
At compile time, Kora generates task components and connects them to the selected scheduling mechanism.

Three options are available: the `JDK` scheduler based on the standard library, the scheduler based on `Quartz`,
and the [DB Scheduler](#db-scheduler) based on the `db-scheduler` library. All of them support `cron` expressions.
The `JDK` scheduler covers periodic and `cron` tasks inside a single application without extra dependencies,
`Quartz` adds custom `Trigger` instances, a pluggable `JobStore`, per-task execution rules, and the Quartz `cron` dialect with its `L`, `W` and `#` modifiers,
and the `DB Scheduler` keeps task state in a database table, so tasks survive restarts and are coordinated between application instances.

Each scheduler has its own annotations: `io.koraframework.scheduling.jdk.annotation.ScheduleJdk*`, `io.koraframework.scheduling.quartz.annotation.ScheduleQuartz*`, and `io.koraframework.scheduling.db.scheduler.annotation.ScheduleDb*`. Jobs with a `config` path support `enabled = false`; persistent schedulers also unschedule a disabled job at startup.
Generated jobs inherit `@Conditional` from the component that declares the scheduled method, so a failed condition keeps the job out of the graph.

## JDK Scheduler { #native }

The `JDK` scheduler is built on the `JDK` standard library and follows the [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) model:
a single timer thread tracks when tasks are due, and every execution runs on its own [virtual thread](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html).

Special annotations from the `io.koraframework.scheduling.jdk.annotation` package are used to create tasks:
`@ScheduleJdkAtFixedRate`, `@ScheduleJdkWithFixedDelay`, `@ScheduleJdkOnce` and `@ScheduleJdkWithCron`.

All annotations have the `config` parameter.
If it is specified, parameter values are taken from the configuration at that path and have priority over annotation values.
The configuration of a specific task can also contain the `telemetry` section; its values override the common scheduler telemetry for that task.

Scheduled methods must satisfy the following requirements:

- The enclosing class must be a component in the [dependency graph](container.md), for example annotated with `@Component`.
- The `JDK` scheduler method must have no arguments (the `Quartz` scheduler additionally allows an optional [JobExecutionContext](#job-context) argument).
- The method return value is ignored.
- In `Kotlin` the method must be a member function of a class and must not be a `suspend` function.

!!! warning "Schedule parameter is required"

    Every `JDK` annotation needs a schedule either from its own attributes or from a `config` path.
    If neither is present, compilation fails:

    - `@ScheduleJdkAtFixedRate` — `Either period() or config() annotation parameter must be provided`
    - `@ScheduleJdkWithFixedDelay` and `@ScheduleJdkOnce` — `Either delay() or config() annotation parameter must be provided`
    - `@ScheduleJdkWithCron` — `Either value() or config() annotation parameter must be provided`

    The default value of `period()` and `delay()` is `0`, which counts as "not provided".

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:scheduling-jdk"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends SchedulingJdkModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("io.koraframework:scheduling-jdk")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : SchedulingJdkModule
    ```

### Configuration { #configuration }

Scheduler options are described by the `SchedulingJdkConfig` class and live in the `scheduling.jdk` section,
telemetry options are shared by both schedulers and live in the `scheduling.telemetry` section:

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

    1. Time the executor is given to finish running executions before they are interrupted during [graceful shutdown](#graceful-shutdown) (default: `30s`)
    2. Maximum number of job executions running at the same time across all jobs; executions above the limit wait in a queue (default: unlimited, `Integer.MAX_VALUE`)
    3. Enables module logging (default: `false`)
    4. Enables module metrics (default: `false`)
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Configures metric tags (default: `{}`)
    7. Enables module tracing (default: `true`)
    8. Configures tracing attributes (default: `{}`)

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

    1. Time the executor is given to finish running executions before they are interrupted during [graceful shutdown](#graceful-shutdown) (default: `30s`)
    2. Maximum number of job executions running at the same time across all jobs; executions above the limit wait in a queue (default: unlimited, `Integer.MAX_VALUE`)
    3. Enables module logging (default: `false`)
    4. Enables module metrics (default: `false`)
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Configures metric tags (default: `{}`)
    7. Enables module tracing (default: `true`)
    8. Configures tracing attributes (default: `{}`)

The default `SchedulingJdkExecutor` is `VirtualThreadSchedulingJdkExecutor`.
It keeps a single non-daemon platform thread named `kora-jdk-scheduler-timer` that only tracks fire times,
and starts every job execution on a new virtual thread named `kora-jdk-scheduler-job-N`, so jobs do not occupy platform threads while they wait for I/O.
Executions of the same job never overlap, and the number of executions running at once across all jobs is limited by `scheduling.jdk.executionParallelism`.
The executor is registered as a `@DefaultComponent`, so registering your own `SchedulingJdkExecutor` component replaces it.

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

Observability of scheduled tasks can also be customized in code.
Registering a component that extends `DefaultSchedulingLoggerFactory` or `DefaultSchedulingMetricsFactory` changes how jobs are logged or measured,
and registering a `SchedulingTelemetryFactory` component replaces the default implementation entirely.

### Fixed Rate { #fixed-rate }

Scheduling with tasks started at a fixed time interval measured between the starts of consecutive executions.

If an execution takes longer than the period, the next one starts as soon as the previous one finishes:
executions of the same task never overlap, they only start late.

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

#### Configuration { #configuration-2 }

Parameters can be passed through configuration; the configuration has priority over annotation values.
The `config` path is arbitrary, but by convention it is nested under the `scheduling` section so that a task's
parameters and its `telemetry` live together (as in the [example project](https://github.com/kora-projects/kora-examples), `scheduling.jobs.fix-rate`):

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

If the annotation already provides `period` and `initialDelay`, the values from the annotation become the defaults of the generated
configuration and the configuration only has to override what should differ.

### Fixed Delay { #fixed-delay }

The scheduler waits for a fixed time interval from the end of the previous task execution.
Multiple executions of the same task will not happen concurrently.

It does not matter how long the current execution takes:
the next task starts after the previous task completes and the configured delay passes.

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

#### Configuration { #configuration-3 }

Parameters can be passed through configuration; it has priority over annotation values:

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

#### Configuration { #configuration-4 }

Parameters can be passed through configuration; it has priority over annotation values:

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

### Cron { #jdk-cron }

The `JDK` scheduler runs `cron` tasks without any external scheduler.
Expressions are parsed and evaluated by the `CronExpression` class that ships with the `scheduling-jdk` artifact.

After every execution the job computes the next fire time from the current moment in the time zone of a `ZoneId` component tagged `@Tag(SchedulingModule.class)`, or the default time zone of the `JVM` when no such component exists,
and schedules itself again, so a slow execution never causes a burst of catch-up runs.

Daylight saving time transitions are evaluated in chronological order:
a local time that does not exist because the clock jumps forward is skipped rather than shifted,
and a local time that occurs twice because the clock jumps back fires at both occurrences.

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

    1. `cron` expression that runs the task every ten seconds

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

    1. `cron` expression that runs the task every ten seconds

#### Expression Format { #jdk-cron-format }

An expression may contain five, six or seven space-separated fields.
The five-field form omits the seconds field and is evaluated with `0` seconds:

| Field        | Allowed values                | Required                      |
|--------------|-------------------------------|-------------------------------|
| Seconds      | `0-59`                        | in the six- and seven-field form |
| Minutes      | `0-59`                        | yes                           |
| Hours        | `0-23`                        | yes                           |
| Day of month | `1-31`                        | yes                           |
| Month        | `1-12` or `JAN-DEC`           | yes                           |
| Day of week  | `1-7` or `SUN-SAT`            | yes                           |
| Year         | empty or `1970-2099`          | no                            |

In the day-of-week field `1` is Sunday and `7` is Saturday; `0` is also accepted as Sunday.
When the year field is omitted, all years from `1970` through `2099` are allowed.

Besides plain numbers the following special characters are supported:

| Character | Meaning                                                                                                        |
|-----------|----------------------------------------------------------------------------------------------------------------|
| `*`       | All values of the field (for example `*` in the minute field means "every minute")                             |
| `?`       | No specific value, allowed only in the day-of-month, day-of-week and year fields, where it is equivalent to `*` |
| `,`       | List of values, for example `6,19` in the hour field                                                           |
| `-`       | Inclusive range, for example `MON-FRI` or `9-17`                                                               |
| `/`       | Step, for example `*/10` in the seconds field or `5/10`                                                        |

The day-of-month and day-of-week fields are combined with a logical `AND`, so `0 0 9-17 * * MON-FRI` fires on weekdays only.

Expression examples:

| Expression                | Meaning                                                     |
|---------------------------|-------------------------------------------------------------|
| `0 * * * * *`             | The top of every minute                                     |
| `*/10 * * * * *`          | Every ten seconds                                           |
| `0 0 * * * ?`             | The top of every hour                                       |
| `0 0 6,19 * * ?`          | 6:00 and 19:00 every day                                    |
| `0 0/30 8-10 * * ?`       | Every 30 minutes from 8:00 through 10:30 every day          |
| `0 0 9-17 ? * MON-FRI`    | Every hour from 9:00 through 17:00 on weekdays              |
| `*/15 9-17 * * MON-FRI`   | Five-field form: every 15 minutes from 9:00 through 17:00 on weekdays |
| `0 0 0 25 DEC ?`          | Every Christmas Day at midnight                             |
| `0 0 0 29 FEB ?`          | Every leap day at midnight                                  |
| `0 0 0 1 JAN ? 2027`      | January 1, 2027 at midnight                                 |

!!! warning "Quartz modifiers are not supported"

    The `JDK` evaluator rejects the Quartz-specific `L`, `W`, `#` and `C` modifiers with
    `Cron field doesn't support L, W, # or C modifiers`.
    Expressions that need them must run on the [Quartz](#quartz) scheduler.

Literal annotation expressions are checked by the Java or Kotlin processor at compile time. An expression supplied through configuration is parsed when the graph is built; an invalid configured expression fails startup.
If an expression can never fire again — for example a fixed year in the past — the job logs a warning and stops scheduling itself.

#### Configuration { #configuration-jdk-cron }

The expression can be passed through configuration; the configuration has priority over the annotation value:

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

The configuration path accepts either an object with the `cron` key and an optional `telemetry` section, or a plain string with the expression:

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

    1. `cron` expression that runs the task every ten seconds (`required`, no default)
    2. Short form: the value of the `config` path itself is the `cron` expression

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        cron:
          cron: "*/10 * * * * *" #(1)!
        cron-short: "*/10 * * * * *" #(2)!
    ```

    1. `cron` expression that runs the task every ten seconds (`required`, no default)
    2. Short form: the value of the `config` path itself is the `cron` expression

When the annotation also carries an expression, that expression becomes the default of the generated configuration,
so the configuration path may be absent entirely and is only needed to override the schedule.

### Graceful Shutdown { #graceful-shutdown }

During [graceful shutdown](container.md#component-lifecycle) components are released in reverse dependency order.
Jobs depend on the executor, while the executor does not depend on jobs, so every job is released before the executor.

Releasing a job cancels its schedule without interrupting anything and without waiting:
no new execution of that job is started, and an execution that is already running keeps running.
Afterwards the executor stops accepting work, cancels the remaining periodic tasks, and waits up to `scheduling.jdk.shutdownWait`
for the running executions to finish; the same deadline covers one-shot tasks that are still pending in the timer.
When the wait expires, the remaining tasks are cancelled, running executions are interrupted, and
`SchedulingJdkExecutor failed completing graceful shutdown in ...` is logged, so a job that never returns delays the shutdown by at most `shutdownWait`.

Long-running tasks should therefore be written so that they finish on their own,
and may additionally check [Thread.currentThread().isInterrupted()](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html#isInterrupted()) to stop earlier.

### Programmatic Scheduling { #programmatic }

For scheduling tasks in imperative style, the `SchedulingJdkExecutor` component can be injected.
It is the same executor that runs annotated jobs and exposes the `scheduleAtFixedRate`, `scheduleWithFixedDelay` and `scheduleOnce` methods,
each returning a `ScheduledFuture`:

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

Tasks scheduled this way are plain `Runnable` instances: they run on virtual threads and count toward `scheduling.jdk.executionParallelism` together with annotated jobs,
but are not wrapped in scheduling telemetry.
Executions of the same periodic task never overlap, a `period` or `delay` that is not positive fails with `IllegalArgumentException`,
and scheduling after the executor was released fails with `RejectedExecutionException`.
Periodic tasks are cancelled when the executor is released, and pending one-shot tasks are subject to the same `shutdownWait` as described in [Graceful Shutdown](#graceful-shutdown).

## Quartz { #quartz }

The implementation based on the [Quartz](https://www.quartz-scheduler.org/) library is used for tasks with custom `Trigger` instances,
Quartz execution rules, and the Quartz `cron` dialect.

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:scheduling-quartz"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends QuartzModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("io.koraframework:scheduling-quartz")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : QuartzModule
    ```

### Configuration { #configuration-5 }

`Quartz` itself is configured with [Properties](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/configuration/) values in key-value format
under the `scheduling.quartz.properties` section.
Kora settings for graceful shutdown live in `scheduling.quartz`, and telemetry is shared with the `JDK` scheduler in the `scheduling.telemetry` section.

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

    1. Wait for running jobs before interrupting them during [graceful shutdown](#graceful-shutdown-quartz) (default: `30s`)
    2. Whether to remove [orphaned jobs](#persistent-job-store) from the persistent job store on scheduler startup (default: `false`)
    3. Compare the trigger start time when reconciling persisted jobs (default: `false`); the end time is always compared
    4. `Quartz` scheduler configuration parameters, merged over the defaults below (optional)
    5. Enables module logging (default: `false`)
    6. Enables module metrics (default: `false`)
    7. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    8. Configures metric tags (default: `{}`)
    9. Enables module tracing (default: `true`)
    10. Configures tracing attributes (default: `{}`)

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

    1. Wait for running jobs before interrupting them during [graceful shutdown](#graceful-shutdown-quartz) (default: `30s`)
    2. Whether to remove [orphaned jobs](#persistent-job-store) from the persistent job store on scheduler startup (default: `false`)
    3. Compare the trigger start time when reconciling persisted jobs (default: `false`); the end time is always compared
    4. `Quartz` scheduler configuration parameters, merged over the defaults below (optional)
    5. Enables module logging (default: `false`)
    6. Enables module metrics (default: `false`)
    7. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    8. Configures metric tags (default: `{}`)
    9. Enables module tracing (default: `true`)
    10. Configures tracing attributes (default: `{}`)

Defaults are read from the `org/quartz/quartz.properties` resource shipped with the `Quartz` library and are then adjusted by Kora.
Any key present in `scheduling.quartz.properties` wins over both.

??? abstract "Properties set by Kora"

    ```properties
    org.quartz.scheduler.instanceName: kora-quartz-scheduler
    org.quartz.scheduler.instanceId: AUTO
    ```

The configuration of a specific `cron` task can also contain the `telemetry` section; its values override the common scheduler telemetry for that task,
exactly as described for the [JDK scheduler](#configuration).

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

        @ScheduleQuartzWithCron("* * * ? * * *") //(1)!
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

        @ScheduleQuartzWithCron("* * * ? * * *") //(1)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. `cron` expression that runs the task every second

The `identity` attribute sets the [Quartz Trigger identity](https://www.quartz-scheduler.org/api/2.3.0/org/quartz/TriggerBuilder.html)
used to name the task, which is useful for identifying and replacing tasks, especially with clustered or persistent `JobStore` implementations.
When it is not set, the identity defaults to the fully qualified class name and method name of the task, for example `com.example.SomeService#schedule`:

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

    1. `cron` expression that runs the task at the top of every hour, registered under the trigger identity `my-hourly-job`

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

    1. `cron` expression that runs the task at the top of every hour, registered under the trigger identity `my-hourly-job`

!!! warning "Cron source is required"

    `@ScheduleQuartzWithCron` must get its expression either from `value()` or from `config()`.
    If neither is set, compilation fails with `Quartz @ScheduleQuartzWithCron on '...' has no cron source.`

#### Configuration { #configuration-6 }

Parameters can be passed through configuration; the configuration has priority over annotation values.
As with the `JDK` scheduler, the `config` path is arbitrary and by convention is nested under the `scheduling` section
(as in the [example project](https://github.com/kora-projects/kora-examples), `scheduling.jobs.quartz`):

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

The configuration path accepts either an object with the `cron` key and an optional `telemetry` section, or a plain string with the expression:

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

    1. `cron` expression that runs the task every second (`required`, no default)
    2. Short form: the value of the `config` path itself is the `cron` expression

=== ":simple-yaml: `YAML`"

    ```yaml
    scheduling:
      jobs:
        quartz:
          cron: "* * * ? * * *" #(1)!
        quartz-short: "* * * ? * * *" #(2)!
    ```

    1. `cron` expression that runs the task every second (`required`, no default)
    2. Short form: the value of the `config` path itself is the `cron` expression

### Trigger { #trigger }

For a custom schedule, you can create a `Trigger` from the `Quartz` library, register it in the dependency graph with a tag,
and then pass that tag class to the `@ScheduleQuartzWithTrigger` annotation.

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

        @ScheduleQuartzWithTrigger(SomeService::class) //(2)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Tag used to register the `Trigger` in the dependency graph.
    2. The same tag used by the task to receive the `Trigger`.

`@ScheduleQuartzWithTrigger` has no `config` attribute: everything about the schedule is expressed by the `Trigger` component itself.

### Non-Concurrent Execution { #non-concurrent-execution }

The `@DisallowConcurrentExecution` annotation prevents concurrent execution of the same method by the `Quartz` scheduler.
It is the `Kora` counterpart of `org.quartz.DisallowConcurrentExecution` and is placed on a `@Schedule*`-annotated method;
placing the original `org.quartz.DisallowConcurrentExecution` on the enclosing class has the same effect for all its tasks.

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

### Job Context { #job-context }

A `Quartz` scheduled method may optionally declare a single `org.quartz.JobExecutionContext` argument.
When it is present, `Kora` passes the current execution context to the method; when it is absent, the method is called with no arguments.
The context gives access to the task's `org.quartz.JobDataMap`, which is the way to read and write state associated with the task:

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
        @ScheduleQuartzWithCron(config = "scheduling.jobs.quartz")
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
        @ScheduleQuartzWithCron(config = "scheduling.jobs.quartz")
        fun schedule(context: JobExecutionContext) {
            val data = context.jobDetail.jobDataMap
            val counter = if (data.containsKey("counter")) data.getInt("counter") else 0
            data.put("counter", counter + 1) //(1)!
        }
    }
    ```

    1. The updated value is persisted after execution and available in the next run

### Graceful Shutdown { #graceful-shutdown-quartz }

During [graceful shutdown](container.md#component-lifecycle), `scheduling.quartz.shutdownWait` defaults to `30s`. Quartz stops firing triggers and waits up to this duration for running jobs. It then interrupts unfinished jobs and waits up to the same duration again, so shutdown can take twice the configured wait. Set `0s` to interrupt immediately. Long-running jobs should respond to interruption.

### Persistent Job Store { #persistent-job-store }

With a persistent `JobStore` (for example, `org.quartz.impl.jdbcjobstore.JobStoreTX`), jobs and triggers outlive the application,
so on every startup and graph refresh Kora reconciles the stored state with the tasks present in the application graph.
Two options control this reconciliation:

- `scheduling.quartz.cleanupOrphanedJobs` (default: `false`) removes from the store, on scheduler startup, every job that is no longer registered in the application graph,
  for example after a class with `@ScheduleQuartzWithCron` was deleted or renamed.
  When disabled, such orphaned jobs remain in the store and `Quartz` logs `JobPersistenceException: Couldn't retrieve job because a required class was not found`
  on every startup while its misfire handler retries them.
- `scheduling.quartz.compareStartTime` (default: `false`) also compares a persisted trigger's start time. By default, a trigger is rescheduled when its schedule or end time changes; its start time is ignored because Quartz defaults it to the moment the trigger is built. Enable this only for fixed `startAt()` values.

!!! warning "Enable `cleanupOrphanedJobs` with caution"

    Cleanup removes Kora-managed jobs absent from the current application graph; jobs added directly to `org.quartz.Scheduler` are kept. Use a dedicated store for one application. Applications sharing a store, or different versions during a rolling deployment, can remove one another's Kora jobs.

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

Every declared task is registered as a durable `JobDetail` whose identity is the canonical name of the generated job class.
Registration is repeated when the dependency graph is refreshed: triggers whose definition changed are rescheduled,
and triggers that no longer exist are removed.

## DB Scheduler { #db-scheduler }

The implementation based on the [db-scheduler](https://github.com/kagkarlsson/db-scheduler) library keeps task state in a database table.
Scheduled executions survive application restarts, and application instances that share the table coordinate through it,
so every execution is picked by one instance only. A task is identified in the table by its name, which is why task names must stay stable between deployments.

Tasks are created with annotations from the `io.koraframework.scheduling.db.scheduler.annotation` package:
`@ScheduleDbWithCron`, `@ScheduleDbWithFixedDelay` and `@ScheduleDbOnce`.
Their names distinguish them from the [JDK scheduler](#native) annotations.
The method requirements are the same as for the `JDK` scheduler: the method belongs to a component, has no arguments, and in `Kotlin` is a non-`suspend` member function.

Every annotation has the `name` and `config` attributes:

- `name` sets the task name stored in the table; when empty, the default is `CanonicalClassName#methodName`, for example `com.example.SomeService#schedule`.
- `config` sets a configuration path whose values have priority over annotation values, as for the [JDK scheduler](#configuration-2).
  It may also contain `enabled` and a `telemetry` section. The task name comes only from the annotation.

### Dependency { #dependency-3 }

The module requires a `javax.sql.DataSource` component in the graph, for example the one provided by the [JDBC](database-jdbc.md) module.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:scheduling-db-scheduler"
    implementation "io.koraframework:database-jdbc"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends DbSchedulerModule, JdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("io.koraframework:scheduling-db-scheduler")
    implementation("io.koraframework:database-jdbc")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : DbSchedulerModule, JdbcDatabaseModule
    ```

The scheduler itself is the `KoraDbScheduler` component. `DbSchedulerModule` marks it as a [root component](container.md#root-component), so it starts with the application.

### Configuration { #configuration-7 }

Scheduler options are described by the `DbSchedulerConfig` class and live in the `scheduling.dbScheduler` section,
telemetry is shared with the other schedulers in the `scheduling.telemetry` section described for the [JDK scheduler](#configuration):

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

    1. Creates the table on startup when it does not exist, see [Database Table](#db-scheduler-table) (default: `false`)
    2. Name of the table used by the scheduler (default: `kora_scheduling_db_scheduler_jobs`)
    3. Maximum number of task executions running at the same time; it is passed to `db-scheduler` as its thread count and limits the virtual threads that run executions (default: `10`)
    4. Time the scheduler waits for running executions during [graceful shutdown](#graceful-shutdown-db-scheduler), passed to `db-scheduler` as `shutdownMaxWait` (default: `30s`)
    5. Polling strategy: `FETCH` or `LOCK_AND_FETCH` (default: `FETCH`)
    6. How many due executions are prefetched relative to `executionParallelism`: `DEFAULT` keeps the `db-scheduler` defaults, `BOUNDED` keeps the local backlog close to `executionParallelism`, `BUFFERED` keeps a larger buffer to reduce idle gaps between polls (default: `DEFAULT`)
    7. Delay between polls of the table for due executions (default: `10s`)

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

    1. Creates the table on startup when it does not exist, see [Database Table](#db-scheduler-table) (default: `false`)
    2. Name of the table used by the scheduler (default: `kora_scheduling_db_scheduler_jobs`)
    3. Maximum number of task executions running at the same time; it is passed to `db-scheduler` as its thread count and limits the virtual threads that run executions (default: `10`)
    4. Time the scheduler waits for running executions during [graceful shutdown](#graceful-shutdown-db-scheduler), passed to `db-scheduler` as `shutdownMaxWait` (default: `30s`)
    5. Polling strategy: `FETCH` or `LOCK_AND_FETCH` (default: `FETCH`)
    6. How many due executions are prefetched relative to `executionParallelism`: `DEFAULT` keeps the `db-scheduler` defaults, `BOUNDED` keeps the local backlog close to `executionParallelism`, `BUFFERED` keeps a larger buffer to reduce idle gaps between polls (default: `DEFAULT`)
    7. Delay between polls of the table for due executions (default: `10s`)

Task executions run on virtual threads named `kora-db-scheduler-N`.
Module metrics are the same as for the other schedulers and are described in the [Metrics Reference](metrics.md#scheduling) section.

### Database Table { #db-scheduler-table }

`db-scheduler` needs its table before startup. The module includes SQL schemas for PostgreSQL, MySQL, MariaDB, Microsoft SQL Server, Oracle and HSQLDB at
`db/kora/scheduling-db-scheduler/schema/<database>.sql`, and a Liquibase changelog at
`db/kora/scheduling-db-scheduler/liquibase/changelog.yaml`.
The default table is `kora_scheduling_db_scheduler_jobs`; its primary key and indexes use the same prefix.
For Flyway, copy the SQL for your database into your application's next free migration version. The module does not ship a versioned Flyway migration because its version could collide with application migrations.
For Liquibase, include the bundled changelog in your master changelog.
If you change `scheduling.dbScheduler.tableName`, rename the table and constraints in a copied SQL script.

With `tableInitialize = true`, the module creates the configured table at startup if absent, using the bundled schema for the detected database. The default is `false`; manage production schema with your migration tool when you need controlled migrations.

### Cron { #db-scheduler-cron }

Runs a task by a `cron` expression.
The expression is evaluated by the `CronSchedule` class of `db-scheduler`, not by the `JDK` scheduler's [CronExpression](#jdk-cron-format):
it uses the Spring 5.3 `cron` format with six fields, starting with seconds, and the tagged scheduling `ZoneId` or the default time zone of the `JVM`,
see the [db-scheduler documentation](https://github.com/kagkarlsson/db-scheduler) for details.
This dialect accepts `@yearly`, `@monthly`, `@weekly`, `@daily` and `@hourly`. A single `-` disables a configured cron job and removes its scheduled execution at startup. Literal expressions are validated during Java/Kotlin processing; configured expressions are validated when the graph starts.

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

    1. `cron` expression that runs the task every ten seconds, stored in the table under the task name `some-cron`

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

    1. `cron` expression that runs the task every ten seconds, stored in the table under the task name `some-cron`

If neither `value` nor `config` is set, compilation fails with `Either value() or config() annotation parameter must be provided`.
The `config` path accepts either an object with `cron`, `enabled` and `telemetry`, or a plain string with the expression. Set the task name with the annotation's `name` parameter.
When the annotation also carries an expression, the configuration path may be absent entirely.

### Fixed Delay { #db-scheduler-fixed-delay }

Runs a task repeatedly, waiting for a fixed time interval after the previous execution completes.
`initialDelay` delays the first execution (default: `0`).

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

If neither `delay` nor `config` is set, compilation fails with `Either delay() or config() annotation parameter must be provided`.

### Once { #db-scheduler-once }

Runs a task once after the configured delay.
The execution is created when the scheduler starts, unless one with the same name is already stored in the table,
and is removed from the table after it completes. A failed execution is removed as well: there are no retries.

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

If neither `delay` nor `config` is set, compilation fails with `Either delay() or config() annotation parameter must be provided`.

### Configuration { #configuration-8 }

Parameters of every annotation can be passed through configuration; the configuration has priority over annotation values:

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

Configuration file example:

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

    1. `cron` expression (`required`, no default)
    2. Delay before the first execution (default: `0ms`)
    3. Delay after an execution completes before the next one (`required`, no default)
    4. Delay before the single execution (`required`, no default)

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

    1. `cron` expression (`required`, no default)
    2. Delay before the first execution (default: `0ms`)
    3. Delay after an execution completes before the next one (`required`, no default)
    4. Delay before the single execution (`required`, no default)

If the annotation already provides the value, it becomes the default of the generated configuration and the configuration only has to override what should differ.

### Customization { #db-scheduler-customization }

The scheduler uses the `DataSource` tagged `@Tag(KoraDbScheduler.class)`; by default it is the application `DataSource`,
so registering a `DataSource` component with this tag moves the scheduler to another database.

The `db-scheduler` `SchedulerBuilder` can be adjusted before the scheduler is built by registering a `Configurer<SchedulerBuilder>` component
(`io.koraframework.common.Configurer`); it is applied after the settings from `DbSchedulerConfig`, so it can also override them:

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

Any component implementing `DbSchedulerJob` is registered in the scheduler together with the annotated tasks.
Implement it manually when a task needs `db-scheduler` APIs directly, such as custom task data or completion handling.
Such a task is not wrapped in scheduling telemetry:

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

`KoraDbScheduler` wraps the `db-scheduler` `com.github.kagkarlsson.scheduler.Scheduler`,
so the `Scheduler` itself can be injected, for example to schedule new instances of a task or to inspect scheduled executions.

### Graceful Shutdown { #graceful-shutdown-db-scheduler }

During [graceful shutdown](container.md#component-lifecycle) `KoraDbScheduler` stops the `db-scheduler` scheduler,
which stops picking new executions and waits up to `scheduling.dbScheduler.shutdownWait` for the running executions to finish.
When the wait expires, running executions are interrupted and the scheduler waits up to `shutdownWait` once more.
As with the other schedulers, long-running tasks should finish on their own
or check [Thread.currentThread().isInterrupted()](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html#isInterrupted()).
