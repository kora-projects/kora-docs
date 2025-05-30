A module for creating declarative-style planners using annotations.

===! ":fontawesome-brands-java: `Java`"

    When applying aspects, class must not be `final`

=== ":simple-kotlin: `Kotlin`"

    When applying aspects, class must be `open`

## Native

Creating a scheduler using the standard [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html) that comes with the JVM.

In order to create a scheduler via aspects, special annotations are used that essentially duplicate the `ScheduledExecutorService` method signatures.
The parameters of the annotations correspond to the parameters of the methods `scheduleAtFixedRate`, `schedule`, `scheduleWithFixedDelay` respectively.

Also all annotations have the `config` argument, if it is present, the parameter values will be taken from the configuration on the specified path.

### Dependency

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
    ```groovy
    implementation("ru.tinkoff.kora:scheduling-jdk")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : SchedulingJdkModule
    ```

### Configuration

Example of the complete configuration described in the `ScheduledExecutorServiceConfig` class (default values are specified):

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

    1. Maximum number of threads in [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html)
    2. Time to wait for jobs to complete before shutting down the scheduler in case of [graceful shutdown](container.md#graceful-shutdown)
    3. Enables module logging (default `false`)
    4. Enables module metrics (default `true`)
    5. Configuring [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    6. Enables module tracing (default `true`)

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

    1. Maximum number of threads in [ScheduledExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html)
    2. Time to wait for jobs to complete before shutting down the scheduler in case of [graceful shutdown](container.md#graceful-shutdown)
    3. Enables module logging (default `false`)
    4. Enables module metrics (default `true`)
    5. Configuring [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    6. Enables module tracing (default `true`)

### Fixed rate

Scheduling with tasks running at fixed time intervals, regardless of whether the previous task has completed or not
This can lead to simultaneous execution of several tasks.

For example, if the period is set to 10 seconds, and each task execution takes 5 seconds,
next task execution will start 5 seconds after the previous one completed.

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

#### Configuration

It is possible to transfer parameters via configuration, it has priority over the parameters specified in the annotation:

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

SomeService of configuration via a config file:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        initialDelay = "50ms" //(1)!
        period = "50ms" //(2)!
    }
    ```

    1.  Initial delay interval before the first task
    2.  Intermittent interval between tasks

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      initialDelay: "50ms" #(1)!
      period: "50ms" #(2)!
    ```

    1.  Initial delay interval before the first task
    2.  Intermittent interval between tasks

### Fixed delay

The scheduler waits for a fixed period of time from the end of the previous task execution.
Multiple tasks will not be executed simultaneously.

It does not matter how long the current execution takes,
the next task will start after the previous task is finished and the specified waiting interval.

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

#### Configuration

It is possible to transfer parameters via configuration, it has priority over the parameters specified in the annotation:

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

SomeService of configuration via a config file:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        initialDelay = "50ms" //(1)!
        delay = "50ms" //(2)!
    }
    ```

    1.  Initial delay interval before the first task
    2.  Intermittent delay interval between tasks

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      initialDelay: "50ms" #(1)!
      delay: "50ms" #(2)!
    ```

    1.  Initial delay interval before the first task
    2.  Intermittent delay interval between tasks

### Once

Runs a single task at a certain fixed time interval.

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

#### Configuration

It is possible to transfer parameters via configuration, it has priority over the parameters specified in the annotation:

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

SomeService of configuration via a config file:

===! ":material-code-json: `Hocon`"

    ```javascript
    job {
        delay = "50ms" //(1)!
    }
    ```

    1.  Initial delay interval before the task

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      delay: "50ms" #(1)!
    ```

    1.  Initial delay interval before the task

### Graceful Shutdown

If you want to pre-terminate processing on a scheduled service termination without waiting for the service to end,
you need to check [Thread.currentThread().isInterrupted()](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#isInterrupted--) status and terminate the service yourself.

## Quartz

A library-based implementation of [Quartz](https://www.baeldung.com/quartz) as a scheduler for creating aspects.

### Dependency

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
    ```groovy
    implementation("ru.tinkoff.kora:scheduling-quartz")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : QuartzModule
    ```

### Configuration

Configuration is specified as [Properties](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/configuration/) values in key and value format:

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

    1. Quartz scheduler configuration parameters
    2. Whether to wait for jobs to complete before shutting down scheduler in case of [graceful shutdown](container.md#graceful-shutdown)
    3. Enables module logging (default `false`)
    4. Enables module metrics (default `true`)
    5. Configuring [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    6. Enables module tracing (default `true`)

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

    1. Quartz scheduler configuration parameters
    2. Whether to wait for jobs to complete before shutting down scheduler in case of [graceful shutdown](container.md#graceful-shutdown)
    3. Enables module logging (default `false`)
    4. Enables module metrics (default `true`)
    5. Configuring [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    6. Enables module tracing (default `true`)

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

### Cron

Usage [Cron](http://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html) expressions to run scheduled tasks.

Starts a single task at a certain fixed time interval.

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

    1. Cron expression saying to run a task every hour and every day

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

    1. Cron expression saying to run a task every hour and every day

#### Configuration

It is possible to transfer parameters via configuration, it has priority over the parameters specified in the annotation:

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

    1. Cron expression saying to run a task every hour and every day

=== ":simple-yaml: `YAML`"

    ```yaml
    job:
      cron: "0 0 * * * * ?" #(1)!
    ```

    1. Cron expression saying to run a task every hour and every day

### Trigger

This involves creating your custom `trigger` based on the Quartz library and registering it in the application dependency container with a specific tag and then using it via annotation.

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

    1. Trigger tag
    2. Trigger tag

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

    1. Trigger tag
    2. Trigger tag
