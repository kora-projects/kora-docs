---
description: "Explains Kora Camunda 8 Zeebe worker integration, worker configuration, job handling, variables, telemetry, and supported handler signatures. Use when working with @JobWorker, ZeebeClient, ActivatedJob, JobClient, Camunda8WorkerModule, Camunda8WorkerConfig."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Camunda 8 Zeebe worker integration, worker configuration, job handling, variables, telemetry, and supported handler signatures; key triggers include @JobWorker, ZeebeClient, ActivatedJob, JobClient, Camunda8WorkerModule, Camunda8WorkerConfig."
---

??? warning "Experimental module"

    The **experimental** module is fully working and tested, but requires additional validation and usage analytics.
    For this reason, its `API` may potentially undergo minor changes before becoming fully stable.

The module connects a [Camunda 8 (Zeebe)](https://docs.camunda.io/docs/components/concepts/job-workers/) client and
creates job workers for an external process orchestrator. In `Kora`, such a worker is declared as a regular component:
a method annotated with `@JobWorker` receives process variables, performs work, and returns a result that is sent back
to `Zeebe`.

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:camunda-zeebe-worker"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends ZeebeWorkerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:camunda-zeebe-worker")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : ZeebeWorkerModule
    ```

## Configuration { #configuration }

Example of a complete client configuration described in the `ZeebeClientConfig` class (example values or default values are specified):

===! ":material-code-json: `HOCON`"

    ```javascript
    zeebe {
        client {
            executionThreads = 2 //(1)!
            keepAlive = "45s" //(2)!
            tls = true //(3)!
            certificatePath = "/file/path/to/cert.crt" //(4)!
            initializationFailTimeout = "15s" //(5)!
            grpc {
                url = "grpc://localhost:8090" //(6)!
                ttl = "1h" //(7)!
                maxMessageSize = "4Mib" //(8)!
                retryPolicy {
                    enabled = true //(9)!
                    attempts = 5 //(10)!
                    delay = "100ms" //(11)!
                    delayMax = "5s" //(12)!
                    step = 3.0 //(13)!
                }
            }
            rest {
                url = "http://localhost:8080" //(14)!
            }
            deployment {
                resources = "classpath:bpm" //(15)!
                timeout = "45s" //(16)!
            }
            telemetry {
                logging {
                    enabled = false //(17)!
                }
                metrics {
                    enabled = true //(18)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(19)!
                    tags = { // (20)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(21)!
                    attributes = { // (22)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1. Maximum number of threads for job workers (default: number of CPU cores, but not less than `2`)
    2. Time without read activity before sending a `KeepAlive` check (default: `45s`)
    3. Whether to use `TLS` for the connection (default: `true`)
    4. [File path](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/FileInputStream.html) to the certificate for the connection; if not specified, the system certificate is used (default unspecified, optional)
    5. Maximum time to wait for topology availability check on client startup (default unspecified, optional)
    6. `URL` for connecting through `gRPC` (`required`, default unspecified)
    7. How long the message should be kept on the broker when sent through `gRPC` (default: `1h`)
    8. Maximum inbound message size for `gRPC` (default: `4Mib`)
    9. Whether the retry policy for the `gRPC` connection is enabled (default: `true`)
    10. Number of attempts (default: `5`)
    11. Initial delay between attempts (default: `100ms`)
    12. Maximum delay between attempts (default: `5s`)
    13. Delay multiplier between attempts (default: `3.0`)
    14. `URL` for connecting to the `Zeebe` `REST` address; if specified, the client prefers `REST` over `gRPC` for supported operations (`required` inside the optional `rest` section, default unspecified)
    15. Paths for searching resources that will be uploaded to the orchestrator after startup (default: `[]`)
    16. Maximum time to wait for resource upload (default: `45s`)
    17. Enables module logging (default: `false`)
    18. Enables module metrics (default: `true`)
    19. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    20. Configures tags for metrics (default: `{}`)
    21. Enables module tracing (default: `true`)
    22. Configures attributes for tracing (default: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      client:
        executionThreads: 2 #(1)!
        keepAlive: "45s" #(2)!
        tls: true #(3)!
        certificatePath: "/file/path/to/cert.crt" #(4)!
        initializationFailTimeout: "15s" #(5)!
        grpc:
          url: "grpc://localhost:8090" #(6)!
          ttl: "1h" #(7)!
          maxMessageSize: "4Mib" #(8)!
          retryPolicy:
            enabled: true #(9)!
            attempts: 5 #(10)!
            delay: "100ms" #(11)!
            delayMax: "5s" #(12)!
            step: 3.0 #(13)!
        rest:
          url: "http://localhost:8080" #(14)!
        deployment:
          resources: "classpath:bpm" #(15)!
          timeout: "45s" #(16)!
        telemetry:
          logging:
            enabled: false #(17)!
          metrics:
            enabled: true #(18)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(19)!
            tags: #(20)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(21)!
            attributes: #(22)!
              key1: value1
              key2: value2
    ```

    1. Maximum number of threads for job workers (default: number of CPU cores, but not less than `2`)
    2. Time without read activity before sending a `KeepAlive` check (default: `45s`)
    3. Whether to use `TLS` for the connection (default: `true`)
    4. [File path](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/FileInputStream.html) to the certificate for the connection; if not specified, the system certificate is used (default unspecified, optional)
    5. Maximum time to wait for topology availability check on client startup (default unspecified, optional)
    6. `URL` for connecting through `gRPC` (`required`, default unspecified)
    7. How long the message should be kept on the broker when sent through `gRPC` (default: `1h`)
    8. Maximum inbound message size for `gRPC` (default: `4Mib`)
    9. Whether the retry policy for the `gRPC` connection is enabled (default: `true`)
    10. Number of attempts (default: `5`)
    11. Initial delay between attempts (default: `100ms`)
    12. Maximum delay between attempts (default: `5s`)
    13. Delay multiplier between attempts (default: `3.0`)
    14. `URL` for connecting to the `Zeebe` `REST` address; if specified, the client prefers `REST` over `gRPC` for supported operations (`required` inside the optional `rest` section, default unspecified)
    15. Paths for searching resources that will be uploaded to the orchestrator after startup (default: `[]`)
    16. Maximum time to wait for resource upload (default: `45s`)
    17. Enables module logging (default: `false`)
    18. Enables module metrics (default: `true`)
    19. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    20. Configures tags for metrics (default: `{}`)
    21. Enables module tracing (default: `true`)
    22. Configures attributes for tracing (default: `{}`)

Module metrics are described in the [Metrics Reference](metrics.md#camunda-8-worker) section.

If `deployment.resources` contains paths, the module finds resources in `classpath:` during startup and uploads them to
`Zeebe`. Only paths with the `classpath:` prefix are supported, for example `classpath:bpm`; other locations are skipped.

### Client { #client }

The module creates a `ZeebeClient` component that can be injected into your own services when you need to manually start
processes, publish messages, or execute other `Zeebe` commands.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ProcessStarter {

        private final ZeebeClient client;

        public ProcessStarter(ZeebeClient client) {
            this.client = client;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ProcessStarter(private val client: ZeebeClient)
    ```

The client can be additionally configured with graph components: register a `CredentialsProvider` for authorization,
a `JsonMapper` for `ZeebeClient`, a `ScheduledExecutorService` for job workers, or a `ClientInterceptor` for the
`gRPC` channel.

## Worker { #worker }

Worker is a handler that can perform a specific job in a process.
When a process contains a job of the required type, `Zeebe` activates it and passes it to one of the workers.

### Configuration { #configuration-2 }

There is a default configuration that is applied to all workers on creation, and then named settings for a concrete
worker are applied on top of it by [worker type (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/).
To change settings for all workers at once, override the `default` section.
To change settings only for one worker, add a section with the type name specified in `@JobWorker`.
If the `zeebe.worker.job` section is not specified, the built-in default configuration is used.

Example of a complete worker configuration described in the `ZeebeWorkerConfig` class (example values or default values are specified):

===! ":material-code-json: `HOCON`"

    ```javascript
    zeebe {
        worker {
            job {
                default { //(1)!
                    enabled = true //(2)!
                    timeout = "15m" //(3)!
                    maxJobsActive = 32 //(4)!
                    requestTimeout = "15s" //(5)!
                    pollInterval = "100ms" //(6)!
                    tenantIds = [] //(7)!
                    streamEnabled = false //(8)!
                    streamTimeout = "15s" //(9)!
                    backoff {
                        minDelay = "100ms" //(11)!
                        maxDelay = "500ms" //(12)!
                        factor = 1.0 //(10)!
                        jitter = 1.1 //(13)!
                    }
                }
            }
        }
    }
    ```

    1. [Worker type (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) or the default settings name `default`
    2. Whether the worker is enabled (default: `true`)
    3. Maximum time for one job execution by the worker (default: `15m`)
    4. Maximum number of jobs that will be activated simultaneously for this worker; used to align job fetching speed with processing speed (`backpressure`) (default: `32`)
    5. Request timeout used for polling a new job by the worker (default: `15s`)
    6. Maximum interval between polling new jobs; if no jobs are activated after work is completed, the worker periodically polls the broker (default: `100ms`)
    7. `tenant` identifiers for which the worker can receive jobs (default: `[]`)
    8. Whether to use streaming together with polling for job activation (default: `false`)
    9. Maximum stream lifetime when streaming is enabled (default: `15s`)
    10. Minimum retry delay; due to `jitter`, the actual delay can be lower than this minimum (default: `100ms`)
    11. Maximum retry delay; due to `jitter`, the actual delay can exceed this value (default: `500ms`)
    12. Delay multiplication factor: the previous delay is multiplied by this value (default: `1.0`)
    13. `jitter` factor: the next delay is randomly changed within the `+/-` range of this factor (default: `1.1`)

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      worker:
        job:
          default: #(1)!
            enabled: true #(2)!
            timeout: "15m" #(3)!
            maxJobsActive: 32 #(4)!
            requestTimeout: "15s" #(5)!
            pollInterval: "100ms" #(6)!
            tenantIds: [] #(7)!
            streamEnabled: false #(8)!
            streamTimeout: "15s" #(9)!
            backoff:
              minDelay: "100ms" #(11)!
              maxDelay: "500ms" #(12)!
              factor: 1.0 #(10)!
              jitter: 1.1 #(13)!
    ```

    1. [Worker type (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) or the default settings name `default`
    2. Whether the worker is enabled (default: `true`)
    3. Maximum time for one job execution by the worker (default: `15m`)
    4. Maximum number of jobs that will be activated simultaneously for this worker; used to align job fetching speed with processing speed (`backpressure`) (default: `32`)
    5. Request timeout used for polling a new job by the worker (default: `15s`)
    6. Maximum interval between polling new jobs; if no jobs are activated after work is completed, the worker periodically polls the broker (default: `100ms`)
    7. `tenant` identifiers for which the worker can receive jobs (default: `[]`)
    8. Whether to use streaming together with polling for job activation (default: `false`)
    9. Maximum stream lifetime when streaming is enabled (default: `15s`)
    10. Minimum retry delay; due to `jitter`, the actual delay can be lower than this minimum (default: `100ms`)
    11. Maximum retry delay; due to `jitter`, the actual delay can exceed this value (default: `500ms`)
    12. Delay multiplication factor: the previous delay is multiplied by this value (default: `1.0`)
    13. `jitter` factor: the next delay is randomly changed within the `+/-` range of this factor (default: `1.1`)

### Declarative { #declarative }

You can declaratively create [workers](https://docs.camunda.io/docs/components/concepts/job-workers/) that perform work
within the `Zeebe` orchestrator.

The `@JobWorker` annotation specifies the [worker type (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/)
from the process. `Zeebe` uses this value to connect a job from a `BPMN` process with a handler in the application.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public void process() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process() {
            // do something
        }
    }
    ```

#### Parameter context { #parameter-context }

You can inject the job context as a method argument.
`JobContext` contains metadata of the current job, worker, and process.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public void process(JobContext context) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(context: JobContext) {
            // do something
        }
    }
    ```

#### Parameter variable { #parameter-variable }

You can inject [process variables](https://docs.camunda.io/docs/components/concepts/variables/) as method arguments.
A process variable is part of the process state and can be set on process start or as part of the worker result.

If at least one variable is specified through `@JobVariable`, the generated worker asks `Zeebe` only for those variables.
If `@JobVariable` is not used, the worker asks for all job variables.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public void process(@JobVariable("startId") String id) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(@JobVariable("startId") id: String) {
            // do something
        }
    }
    ```

You can specify the variable name explicitly in `@JobVariable`, or the method argument name will be used by default.

Since process variables are passed as `JSON`, the method argument can be a user type that has `JsonReader` and `JsonWriter`
available.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @Json
        public record User(String name, int code) { }

        @JobWorker("someJobType")
        public void process(@JobVariable User user) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        data class User(val name: String, val code: Int)

        @JobWorker("someJobType")
        fun process(@JobVariable user: User) {
            // do something
        }
    }
    ```

#### Parameter variables { #parameter-variables }

You can inject multiple [process variables](https://docs.camunda.io/docs/components/concepts/variables/) as one method
argument through `@JobVariables`. This argument represents all job variables as one `JSON` object.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @Json
        public record User(String name, int code) { }

        @Json
        public record UserContext(String startId, User user) { }

        @JobWorker("someJobType")
        public void process(@JobVariables UserContext userContext) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        data class User(val name: String, val code: Int)

        data class UserContext(val startId: String, val user: User)

        @JobWorker("someJobType")
        fun process(@JobVariables userContext: UserContext) {
            // do something
        }
    }
    ```

#### Result { #result }

You can not only execute work, but also return the result as variables to the process context.

The result can be returned as a `Map<String, Object>` that describes the `JSON` response structure.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public Map<String, Object> process() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(): Map<String, Any> {
            // do something
        }
    }
    ```

You can also return a named result as a single variable. This is equivalent to one key and value in a
`Map<String, Object>` object.

In this case, it is obligatory to specify the name of the variable in the `@JobVariable` annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @Json
        public record User(String name, int code) { }

        @JobVariable("user")
        @JobWorker("someJobType")
        public User process() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        data class User(val name: String, val code: Int)

        @JobVariable("user")
        @JobWorker("someJobType")
        fun process(): User {
            // do something
        }
    }
    ```

#### Errors { #errors }

If you need to complete execution with a process error, throw `JobWorkerException`.
The exception can contain an error code, message, and process variables if they are required.
This exception is converted to a `throwError` command for `Zeebe`.

If the handler throws another exception, the module converts it to `JobWorkerException` with the `INTERNAL` code.
Variable reading errors get the `DESERIALIZATION` code, result writing errors get the `SERIALIZATION` code, and
unexpected errors in a synchronous handler get the `UNEXPECTED` code.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public User process() {
            throw new JobWorkerException("DOESNT_WORK");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(): User {
            throw JobWorkerException("DOESNT_WORK")
        }
    }
    ```

### Imperative { #imperative }

You can also create lower-level workers and work directly with `ZeebeClient` contracts.
To do that, the component must implement the `KoraJobWorker` interface.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob implements KoraJobWorker {

        @Override
        public String type() {
            return "someJobType";
        }

        @Override
        public CompletionStage<FinalCommandStep<?>> handle(JobClient client, ActivatedJob job) {
            return CompletableFuture.completedFuture(client.newCompleteCommand(job));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob : KoraJobWorker {

        override fun type(): String = "someJobType"

        override fun handle(client: JobClient, job: ActivatedJob): CompletionStage<FinalCommandStep<*>> {
            return CompletableFuture.completedFuture(client.newCompleteCommand(job))
        }
    }
    ```

## Signatures { #signatures }

Available signatures for worker methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value or `Void`.
    If the result is `null` or `Optional.empty()`, the job is completed without adding variables.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (add [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `T?` or `Unit`.
    If the result is `null`, the job is completed without adding variables.

    - `myMethod(): T`
    - `myMethod(): Deferred<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (add [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
