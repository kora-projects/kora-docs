---
description: "Explains Kora scheduling for the JDK and Quartz schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, graceful shutdown, and concurrency controls. Use when working with @ScheduleAtFixedRate, @ScheduleWithFixedDelay, @ScheduleOnce, @ScheduleWithCron, @ScheduleWithTrigger, @DisallowConcurrentExecution, @PersistJobDataAfterExecution, SchedulingJdkModule, SchedulingJdkExecutor, CronExpression, QuartzModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora scheduling for the JDK and Quartz schedulers, fixed rate, fixed delay, one-shot and cron jobs, triggers, graceful shutdown, and concurrency controls; key triggers include @ScheduleAtFixedRate, @ScheduleWithFixedDelay, @ScheduleOnce, @ScheduleWithCron, @ScheduleWithTrigger, @DisallowConcurrentExecution, @PersistJobDataAfterExecution, SchedulingJdkModule, SchedulingJdkExecutor, CronExpression, QuartzModule."
---

The Kora scheduling module allows application methods to run on a schedule in a declarative style through annotations.
At compile time, Kora generates task components and connects them to the selected scheduling mechanism.

Two options are available: the `JDK` scheduler based on `ScheduledExecutorService`, and the scheduler based on `Quartz`.
Both support `cron` expressions.
The `JDK` scheduler covers periodic and `cron` tasks inside a single application without extra dependencies,
while `Quartz` adds custom `Trigger` instances, a pluggable `JobStore`, per-task execution rules, and the Quartz `cron` dialect with its `L`, `W` and `#` modifiers.

## JDK Scheduler { #native }

The `JDK` scheduler uses the standard [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) that comes with the `JDK`.

Special annotations from the `io.koraframework.scheduling.jdk.annotation` package are used to create tasks:
`@ScheduleAtFixedRate`, `@ScheduleWithFixedDelay`, `@ScheduleOnce` and `@ScheduleWithCron`.

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

    - `@ScheduleAtFixedRate` — `Either period() or config() annotation parameter must be provided`
    - `@ScheduleWithFixedDelay` and `@ScheduleOnce` — `Either delay() or config() annotation parameter must be provided`
    - `@ScheduleWithCron` — `Either value() or config() annotation parameter must be provided`

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

    1. Time the thread pool is given to finish its tasks before it is stopped forcibly during [graceful shutdown](container.md#component-lifecycle) (default: `30s`)
    2. Enables module logging (default: `false`)
    3. Enables module metrics (default: `false`)
    4. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    5. Configures metric tags (default: `{}`)
    6. Enables module tracing (default: `true`)
    7. Configures tracing attributes (default: `{}`)

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

    1. Time the thread pool is given to finish its tasks before it is stopped forcibly during [graceful shutdown](container.md#component-lifecycle) (default: `30s`)
    2. Enables module logging (default: `false`)
    3. Enables module metrics (default: `false`)
    4. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    5. Configures metric tags (default: `{}`)
    6. Enables module tracing (default: `true`)
    7. Configures tracing attributes (default: `{}`)

The thread pool is not configurable: Kora creates a `ScheduledThreadPoolExecutor` whose core size equals the number of scheduled jobs registered in the graph.
Its threads are named `kora-scheduler-N`, are not daemon threads, are released after 30 seconds of idling, and cancelled tasks are removed from the queue immediately.

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

### Cron { #jdk-cron }

The `JDK` scheduler runs `cron` tasks without any external scheduler.
Expressions are parsed and evaluated by the `CronExpression` class that ships with the `scheduling-jdk` artifact.

After every execution the job computes the next fire time from the current moment in the default time zone of the `JVM`
and schedules itself again, so a slow execution never causes a burst of catch-up runs.

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

    1. `cron` expression that runs the task every ten seconds

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

The expression is parsed when the dependency graph is built, not at compile time,
so an invalid expression fails application startup with an `IllegalArgumentException` describing the offending field.
If an expression can never fire again — for example a fixed year in the past — the job logs a warning and stops scheduling itself.

#### Configuration { #configuration-jdk-cron }

The expression can be passed through configuration; the configuration has priority over the annotation value:

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

During [graceful shutdown](container.md#component-lifecycle) components are released in reverse dependency order,
so every job is released before the executor it depends on.

Releasing a job waits for the execution that is in progress at that moment and then cancels the schedule without interrupting anything,
so no new execution is started and a job that never returns blocks the shutdown.
Afterwards the executor stops accepting work and waits up to `scheduling.jdk.shutdownWait` for the thread pool to drain;
when the wait expires the pool is stopped forcibly, running threads are interrupted, and
`SchedulingJdkExecutor failed completing graceful shutdown in ...` is logged.

Long-running tasks should therefore be written so that they finish on their own,
and may additionally check [Thread.currentThread().isInterrupted()](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html#isInterrupted()) to stop earlier.

### Programmatic Scheduling { #programmatic }

For scheduling tasks in imperative style, the `SchedulingJdkExecutor` component can be injected.
It wraps the same thread pool as the annotations and exposes the `scheduleAtFixedRate`, `scheduleWithFixedDelay` and `scheduleOnce` methods,
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

Tasks scheduled this way are plain `Runnable` instances: they share the pool with annotated jobs
but are not wrapped in scheduling telemetry and are not cancelled individually on shutdown.

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

    1. Whether to wait for tasks to complete before scheduler shutdown during [graceful shutdown](container.md#component-lifecycle) (default: `true`)
    2. `Quartz` scheduler configuration parameters, merged over the defaults below (optional)
    3. Enables module logging (default: `false`)
    4. Enables module metrics (default: `false`)
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Configures metric tags (default: `{}`)
    7. Enables module tracing (default: `true`)
    8. Configures tracing attributes (default: `{}`)

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

    1. Whether to wait for tasks to complete before scheduler shutdown during [graceful shutdown](container.md#component-lifecycle) (default: `true`)
    2. `Quartz` scheduler configuration parameters, merged over the defaults below (optional)
    3. Enables module logging (default: `false`)
    4. Enables module metrics (default: `false`)
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    6. Configures metric tags (default: `{}`)
    7. Enables module tracing (default: `true`)
    8. Configures tracing attributes (default: `{}`)

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
used to name the task, which is useful for identifying and replacing tasks, especially with clustered or persistent `JobStore` implementations.
When it is not set, the identity defaults to the fully qualified class name and method name of the task, for example `com.example.SomeService#schedule`:

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

!!! warning "Cron source is required"

    `@ScheduleWithCron` must get its expression either from `value()` or from `config()`.
    If neither is set, compilation fails with `Quartz @ScheduleWithCron on '...' has no cron source.`

#### Configuration { #configuration-6 }

Parameters can be passed through configuration; the configuration has priority over annotation values.
As with the `JDK` scheduler, the `config` path is arbitrary and by convention is nested under the `scheduling` section
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
and then pass that tag class to the `@ScheduleWithTrigger` annotation.

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

        @ScheduleWithTrigger(SomeService::class) //(2)!
        fun schedule() {
            // do something
        }
    }
    ```

    1. Tag used to register the `Trigger` in the dependency graph.
    2. The same tag used by the task to receive the `Trigger`.

`@ScheduleWithTrigger` has no `config` attribute: everything about the schedule is expressed by the `Trigger` component itself.

### Non-Concurrent Execution { #non-concurrent-execution }

The `@DisallowConcurrentExecution` annotation prevents concurrent execution of the same method by the `Quartz` scheduler.
It is the `Kora` counterpart of `org.quartz.DisallowConcurrentExecution` and is placed on a `@Schedule*`-annotated method;
placing the original `org.quartz.DisallowConcurrentExecution` on the enclosing class has the same effect for all its tasks.

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

During [graceful shutdown](container.md#component-lifecycle), the `scheduling.quartz.waitForJobComplete` option controls how the `Quartz` scheduler stops.
With `true` (default) it calls `scheduler.shutdown(true)` and blocks until running tasks finish; with `false` it stops without waiting.
As with the `JDK` scheduler, long-running tasks should still cooperatively check
[Thread.currentThread().isInterrupted()](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html#isInterrupted()) and stop the work manually.

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
