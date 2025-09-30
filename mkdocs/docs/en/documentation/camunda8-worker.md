??? warning "Experimental module"

    **Experimental** module is fully working and tested, but requires additional approbation and usage analytics, 
    for this reason, API may potentially undergo minor changes before fully stable.

Module for connecting a client and creating workers for an external process orchestrator [Camunda 8 (Zeebe)](https://docs.camunda.io/docs/components/concepts/job-workers/)

## Dependency

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

## Configuration

Example of a complete client configuration described in the `ZeebeClientConfig` class (example values or default values are specified):

===! ":material-code-json: `Hocon`"

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
                    stepFactor = 3.0 //(13)!
                }
            }
            http {
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
                }
                tracing {
                    enabled = true //(20)!
                }
            }
        }
    }
    ```

    1. Maximum number of threads for task workers, by default equal to the number of CPU cores or minimum `2`.
    2. Connection time without reading activity before sending `KeepAlive` check
    3. Whether to use TLS when connecting on a connection
    4. [File path](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/FileInputStream.html) to the certificate file to use when connecting, or use the default system certificate
    5. Maximum time to wait for initialization of workers to start when the service starts (default is none)
    6. URL for connection via gRPC
    7. Time for how long the message should be buffered at the broker over gRPC connection
    8. Maximum message size over gRPC connection
    9. Whether the policy of execution repeat in case of connection error is enabled
    10. Number of attempts
    11. Delay between attempts
    12. maximum duration of retries
    13. Step coefficient for increasing the delay time between attempts
    14. URL for HTTP connection
    15. Paths to find resources that will be loaded into the orchestrator after startup
    16. Maximum time to wait for resources to be loaded
    17. Enables module logging (default is `false`)
    18. Enables module metrics (default `true`)
    19. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    20. Enables module tracing (default `true`)

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
          url: "grpc:#localhost:8090" //(6)!
          ttl: "1h" #(7)!
          maxMessageSize: "4Mib" #(8)!
          retryPolicy:
            enabled: true #(9)!
            attempts: 5 #(10)!
            delay: "100ms" #(11)!
            delayMax: "5s" #(12)!
            stepFactor: 3.0 #(13)!
        http:
          url: "http:#localhost:8080" //(14)!
        deployment:
          resources: "classpath:bpm" #(15)!
          timeout: "45s" #(16)!
        telemetry:
          logging:
            enabled: false #(17)!
          metrics:
            enabled: true #(18)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(19)!
          tracing:
            enabled: true #(20)!
    ```

    1. Maximum number of threads for task workers, by default equal to the number of CPU cores or minimum `2`.
    2. Connection time without reading activity before sending `KeepAlive` check
    3. Whether to use TLS when connecting on a connection
    4. [File path](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/FileInputStream.html) to the certificate file to use when connecting, or use the default system certificate
    5. Maximum time to wait for initialization of workers to start when the service starts (default is none)
    6. URL for connection via gRPC
    7. Time for how long the message should be buffered at the broker over gRPC connection
    8. Maximum message size over gRPC connection
    9. Whether the policy of execution repeat in case of connection error is enabled
    10. Number of attempts
    11. Delay between attempts
    12. maximum duration of retries
    13. Step coefficient for increasing the delay time between attempts
    14. URL for HTTP connection
    15. Paths to find resources that will be loaded into the orchestrator after startup
    16. Maximum time to wait for resources to be loaded
    17. Enables module logging (default is `false`)
    18. Enables module metrics (default `true`)
    19. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    20. Enables module tracing (default `true`)

## Worker

Worker is a handler that can perform a specific job in a process.
Each time such a job needs to be performed, it is polled by worker.

### Configuration

There is a default configuration that is applied to all workers at creation
and then the named worker-specific settings ([by `Type`](https://docs.camunda.io/docs/components/concepts/job-workers/)) are then applied overriding the default settings.
You can change the default settings for all interrupters at the same time by changing the default configuration (`default`).

Example of a complete worker configuration is described in the `ZeebebeWorkerConfig` class (example values or default values are specified):

===! ":material-code-json: `Hocon`"

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
                        jitter = 1.3 //(13)!
                    }
                }
            }
        }
    }
    ```

    1. [Worker (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) or the name of the default settings (`default`)
    2. Whether to include an worker
    3. Maximum time for an worker to complete a single task
    4. The maximum number of tasks that will be activated simultaneously for this worker only. This is used to control the speed of the data producer to match the speed of the worker (`backpressure`)
    5. Limitation on the query time used to poll a new task by the worker
    6. Maximum interval between polling of new tasks. The worker automatically tries to always activate new tasks after the job is finished. If no task can be activated after completion, the performer will poll new tasks periodically
    7. Specifies the tenant identifiers that can own any entities (e.g., process definition, process instances, etc.) resulting from the execution of this command
    8. If set to enabled, the worker will use a combination of streaming and polling to activate jobs
    9. If streaming is enabled, sets the maximum lifetime for this thread
    10. Sets the minimum repetition delay. Note that due to `jitter`, the repeat delay may be lower than this minimum    
    11. Sets the maximum repeat delay. Note that `jitter` may exceed this maximum delay
    12. Sets the delay multiplication factor. The previous delay is multiplied by this factor
    13. Sets the jitter coefficient. The next delay is varied randomly within the range +/- of this coefficient. 
        For example, if the next delay is calculated as 1s and `jitter` is 0.1, the actual next delay may be somewhere between 0.9 and 1.1s

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
              jitter: 1.3 #(13)!
    ```

    1. [Worker (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) or the name of the default settings (`default`)
    2. Whether to include an worker
    3. Maximum time for an worker to complete a single task
    4. The maximum number of tasks that will be activated simultaneously for this worker only. This is used to control the speed of the data producer to match the speed of the worker (`backpressure`)
    5. Limitation on the query time used to poll a new task by the worker
    6. Maximum interval between polling of new tasks. The worker automatically tries to always activate new tasks after the job is finished. If no task can be activated after completion, the performer will poll new tasks periodically
    7. Specifies the tenant identifiers that can own any entities (e.g., process definition, process instances, etc.) resulting from the execution of this command
    8. If set to enabled, the worker will use a combination of streaming and polling to activate jobs
    9. If streaming is enabled, sets the maximum lifetime for this thread
    10. Sets the minimum repetition delay. Note that due to `jitter`, the repeat delay may be lower than this minimum    
    11. Sets the maximum repeat delay. Note that `jitter` may exceed this maximum delay
    12. Sets the delay multiplication factor. The previous delay is multiplied by this factor
    13. Sets the jitter coefficient. The next delay is varied randomly within the range +/- of this coefficient. 
        For example, if the next delay is calculated as 1s and `jitter` is 0.1, the actual next delay may be somewhere between 0.9 and 1.1s

### Declarative

You can create declaratively [JobWorkers](https://docs.camunda.io/docs/components/concepts/job-workers/) that will perform work within the Zeebe orchestrator.

`JobWorker` annotation specifies the value of the [worker type (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) within the process.

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

#### Parameter context

You can embed the job context as a method argument.
Job Context has task, worker and process metadata available for the current task being executed.

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

#### Parameter variable

You can embed [process variables](https://docs.camunda.io/docs/components/concepts/variables/) as method arguments,
a process variable is part of the process state and can be set on start or as part of the worker result.

Importantly, if any named variables are specified, only those variables will be passed to receive from the orchestrator.

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

You can specify a variable name from context, or the default method argument name will be used.

Since all process variables are required to be JSON objects,
the method argument can also be any mapping of a JSON object.

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

#### Parameter variables

You can embed multiple [process variables](https://docs.camunda.io/docs/components/concepts/variables/) at once as a method argument,
as a single object that represents JSON objects in the process state.

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

#### Result

You can also execute a job with some result of the job execution and pass it as a variable to process context.

The result can be returned as a `Map<String, Object>` describing the JSON structure of the response.

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

Or return the named result as a single variable at once,
which will be analogous to a single key and value in a `Map<String, Object>` object.

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

#### Errors

In case you need to terminate execution with an error, you can throw a `JobWorkerException` exception where you can specify,
both the error code and the message and process variables if required.

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

### Imperative.

You can also create more low-level workers and work directly with `ZeebeClient` contracts and its interface.

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
            return client.newCompleteCommand(job);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob : KoraJobWorker {

        fun type(): String = "someJobType"

        fun handle(client: JobClient, job: ActivatedJob): CompletionStage<FinalCommandStep<*>> {
            return client.newCompleteCommand(job)
        }
    }
    ```

## Signatures

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value or `Void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (add [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `T?` or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): Deferred<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (add [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
