---
description: "Explains Kora Camunda 8 Zeebe worker integration, CamundaClient configuration, job handling, variables, telemetry, and supported handler signatures. Use when working with @JobWorker, @JobVariable, @JobVariables, CamundaClient, JobContext, KoraJobWorker, JobWorkerException, ZeebeWorkerModule, ZeebeClientConfig, ZeebeWorkerConfig."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Camunda 8 Zeebe worker integration, CamundaClient configuration, job handling, variables, telemetry, and supported handler signatures; key triggers include @JobWorker, @JobVariable, @JobVariables, CamundaClient, JobContext, KoraJobWorker, JobWorkerException, ZeebeWorkerModule, ZeebeClientConfig, ZeebeWorkerConfig."
---

??? warning "Experimental module"

    The **experimental** module is fully working and tested, but requires additional validation and usage analytics.
    For this reason, its `API` may potentially undergo minor changes before becoming fully stable.

The module connects a [Camunda 8 (Zeebe)](https://docs.camunda.io/docs/components/concepts/job-workers/) client and
creates job workers for an external process orchestrator. In `Kora`, such a worker is declared as a regular component:
a method annotated with `@JobWorker` receives process variables, performs work, and returns a result that is sent back
to `Zeebe`.

The module is built on the `io.camunda:camunda-client-java` client, so the client type is `io.camunda.client.CamundaClient`
and its command responses live in the `io.camunda.client.api.response` package.

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework.experimental:camunda-zeebe-worker"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends ZeebeWorkerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework.experimental:camunda-zeebe-worker")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : ZeebeWorkerModule
    ```

## Configuration { #configuration }

Example of a complete client configuration described in the `ZeebeClientConfig` class (example values or default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    zeebe {
        client {
            executionThreads = 4 //(1)!
            keepAlive = "45s" //(2)!
            certificatePath = "/file/path/to/cert.crt" //(3)!
            initializationFailTimeout = "15s" //(4)!
            grpc {
                url = "http://localhost:26500" //(5)!
                ttl = "1h" //(6)!
                maxMessageSize = "4MiB" //(7)!
                retryPolicy {
                    enabled = true //(8)!
                    attempts = 5 //(9)!
                    delay = "100ms" //(10)!
                    delayMax = "5s" //(11)!
                    step = 3.0 //(12)!
                }
            }
            rest {
                url = "http://localhost:8080" //(13)!
            }
            deployment {
                resources = "classpath:bpm" //(14)!
                timeout = "45s" //(15)!
            }
            telemetry {
                logging {
                    enabled = false //(16)!
                }
                metrics {
                    enabled = false //(17)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(18)!
                    tags = { //(19)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(20)!
                    attributes = { //(21)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1. Maximum number of threads for job workers (default: twice the number of available processors, but not less than `2`)
    2. Time without read activity before sending a `KeepAlive` check (default: `45s`)
    3. [File path](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/io/FileInputStream.html) to the certificate for the connection; if not specified, the system certificate is used (optional)
    4. Maximum time to wait for the topology availability check on client startup; if not specified, the check is skipped (optional)
    5. `URL` of the `Zeebe` `gRPC` gateway (required, no default)
    6. How long the message should be kept on the broker when sent through `gRPC` (default: `1h`)
    7. Maximum inbound message size for `gRPC` (default: `4MiB`)
    8. Whether the retry policy for the `gRPC` connection is enabled (default: `true`)
    9. Number of attempts (default: `5`)
    10. Initial delay between attempts (default: `100ms`)
    11. Maximum delay between attempts (default: `5s`)
    12. Delay multiplier between attempts (default: `3.0`)
    13. `URL` of the `Zeebe` `REST` gateway (required, no default)
    14. Paths for searching resources that will be uploaded to the orchestrator after startup (default: `[]`)
    15. Maximum time to wait for resource upload (default: `45s`)
    16. Enables module logging (default: `false`)
    17. Enables module metrics (default: `false`)
    18. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    19. Configures tags for metrics (default: `{}`)
    20. Enables module tracing (default: `true`)
    21. Configures attributes for tracing (default: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      client:
        executionThreads: 4 #(1)!
        keepAlive: "45s" #(2)!
        certificatePath: "/file/path/to/cert.crt" #(3)!
        initializationFailTimeout: "15s" #(4)!
        grpc:
          url: "http://localhost:26500" #(5)!
          ttl: "1h" #(6)!
          maxMessageSize: "4MiB" #(7)!
          retryPolicy:
            enabled: true #(8)!
            attempts: 5 #(9)!
            delay: "100ms" #(10)!
            delayMax: "5s" #(11)!
            step: 3.0 #(12)!
        rest:
          url: "http://localhost:8080" #(13)!
        deployment:
          resources: "classpath:bpm" #(14)!
          timeout: "45s" #(15)!
        telemetry:
          logging:
            enabled: false #(16)!
          metrics:
            enabled: false #(17)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(18)!
            tags: #(19)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(20)!
            attributes: #(21)!
              key1: value1
              key2: value2
    ```

    1. Maximum number of threads for job workers (default: twice the number of available processors, but not less than `2`)
    2. Time without read activity before sending a `KeepAlive` check (default: `45s`)
    3. [File path](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/io/FileInputStream.html) to the certificate for the connection; if not specified, the system certificate is used (optional)
    4. Maximum time to wait for the topology availability check on client startup; if not specified, the check is skipped (optional)
    5. `URL` of the `Zeebe` `gRPC` gateway (required, no default)
    6. How long the message should be kept on the broker when sent through `gRPC` (default: `1h`)
    7. Maximum inbound message size for `gRPC` (default: `4MiB`)
    8. Whether the retry policy for the `gRPC` connection is enabled (default: `true`)
    9. Number of attempts (default: `5`)
    10. Initial delay between attempts (default: `100ms`)
    11. Maximum delay between attempts (default: `5s`)
    12. Delay multiplier between attempts (default: `3.0`)
    13. `URL` of the `Zeebe` `REST` gateway (required, no default)
    14. Paths for searching resources that will be uploaded to the orchestrator after startup (default: `[]`)
    15. Maximum time to wait for resource upload (default: `45s`)
    16. Enables module logging (default: `false`)
    17. Enables module metrics (default: `false`)
    18. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    19. Configures tags for metrics (default: `{}`)
    20. Enables module tracing (default: `true`)
    21. Configures attributes for tracing (default: `{}`)

!!! warning "Both addresses are required"

    The client always opens a `gRPC` channel and always reads the `REST` address, so `zeebe.client.grpc.url`
    and `zeebe.client.rest.url` must both be present. A configuration that declares only one of the two
    fails on application startup.

The connection scheme is taken from `grpc.url`: `http` opens a plaintext channel, `https` opens a `TLS` channel.
For a self-signed certificate, point `certificatePath` at the certificate file; otherwise the system trust store is used.
The default `Zeebe` ports are `26500` for `gRPC` and `8080` for `REST`.

The `gRPC` channel has its own telemetry section `zeebe.client.grpc.telemetry` with the same options as any
[gRPC client](grpc-client.md#configuration); it describes the transport calls to the orchestrator, while
`zeebe.client.telemetry` describes the job workers themselves.
Job worker logs are written to the `io.koraframework.camunda.zeebe.worker.<jobType>` logger, so log levels can be raised
for a single worker; at the `DEBUG` level the log record also contains the job variables.

Module metrics are described in the [Metrics Reference](metrics.md#camunda-8-worker) section.

### Resource deployment { #resource-deployment }

If `deployment.resources` contains paths, the module finds resources on the classpath during startup and deploys them to
`Zeebe` through the `ZeebeResourceDeployment` component. Both `BPMN` processes and `DMN` decisions found under the
configured locations are deployed. Only paths with the `classpath:` prefix are supported, for example `classpath:bpm`;
other locations are logged and skipped.

Put the deployable resources under the corresponding classpath directory:

```text
src/main/resources/
└── bpm/
    └── demo.bpmn
```

===! ":material-code-json: `Hocon`"

    ```javascript
    zeebe {
        client {
            deployment {
                resources = "classpath:bpm" //(1)!
            }
        }
    }
    ```

    1. One or more classpath locations to scan for `BPMN` / `DMN` resources (a single value or a list)

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      client:
        deployment:
          resources: "classpath:bpm" #(1)!
    ```

    1. One or more classpath locations to scan for `BPMN` / `DMN` resources (a single value or a list)

### Client { #client }

The module creates a `CamundaClient` component that can be injected into your own services when you need to manually start
processes, publish messages, or execute other `Zeebe` commands.

For example, to start a new process instance:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ProcessStarter {

        private final CamundaClient client;

        public ProcessStarter(CamundaClient client) {
            this.client = client;
        }

        public void start() {
            ProcessInstanceEvent event = client.newCreateInstanceCommand()
                    .bpmnProcessId("demo") //(1)!
                    .latestVersion() //(2)!
                    .variables("{\"startId\":\"42\"}") //(3)!
                    .send()
                    .join(); //(4)!
        }
    }
    ```

    1. `BPMN` process identifier of the process to start
    2. Start the latest deployed version of the process
    3. Initial process variables as a `JSON` string (a `Map` or a `@Json` object are also accepted)
    4. Send the command and block until `Zeebe` acknowledges it (`send()` returns a `CamundaFuture`, which is also a `CompletionStage`)

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ProcessStarter(private val client: CamundaClient) {

        fun start() {
            val event = client.newCreateInstanceCommand()
                .bpmnProcessId("demo") //(1)!
                .latestVersion() //(2)!
                .variables("""{"startId":"42"}""") //(3)!
                .send()
                .join() //(4)!
        }
    }
    ```

    1. `BPMN` process identifier of the process to start
    2. Start the latest deployed version of the process
    3. Initial process variables as a `JSON` string (a `Map` or a `@Json` object are also accepted)
    4. Send the command and block until `Zeebe` acknowledges it (`send()` returns a `CamundaFuture`, which is also a `CompletionStage`)

The same client publishes messages (`client.newPublishMessageCommand()`), deploys resources
(`client.newDeployResourceCommand()`), and executes any other `Zeebe` command.

#### Client customization { #client-customization }

The `CamundaClient` can be tuned with optional graph components that the module picks up automatically:

* `CredentialsProvider` — authorization for `Zeebe` (`Camunda 8 SaaS` or self-managed with `OAuth`);
* `JsonMapper` — custom `JSON` mapper (`io.camunda.client.api.JsonMapper`) used by `CamundaClient` for variable (de)serialization;
* `ScheduledExecutorService` — executor used by job workers;
* `ClientInterceptor` — every `gRPC` interceptor declared **without** a `@Tag` is collected and applied to the `Zeebe` channel,
  in addition to the module's own telemetry interceptor. Interceptors that belong to another client must therefore be
  [tagged with their service](grpc-client.md#shared-interceptors) so that they do not end up on the `Zeebe` channel.

For example, to authenticate against `Camunda 8` with `OAuth`, provide a `CredentialsProvider` bean:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ZeebeAuthModule {

        default CredentialsProvider zeebeCredentialsProvider() {
            return CredentialsProvider.newCredentialsProviderBuilder()
                    .clientId("client-id")
                    .clientSecret("client-secret")
                    .audience("zeebe.camunda.io")
                    .authorizationServerUrl("https://login.cloud.camunda.io/oauth/token")
                    .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ZeebeAuthModule {

        fun zeebeCredentialsProvider(): CredentialsProvider =
            CredentialsProvider.newCredentialsProviderBuilder()
                .clientId("client-id")
                .clientSecret("client-secret")
                .audience("zeebe.camunda.io")
                .authorizationServerUrl("https://login.cloud.camunda.io/oauth/token")
                .build()
    }
    ```

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

===! ":material-code-json: `Hocon`"

    ```javascript
    zeebe {
        worker {
            job {
                default { //(1)!
                    enabled = true //(2)!
                    name = "default" //(3)!
                    timeout = "15m" //(4)!
                    maxJobsActive = 32 //(5)!
                    requestTimeout = "15s" //(6)!
                    pollInterval = "100ms" //(7)!
                    tenantIds = [] //(8)!
                    streamEnabled = false //(9)!
                    streamTimeout = "15s" //(10)!
                    backoff {
                        minDelay = "100ms" //(11)!
                        maxDelay = "500ms" //(12)!
                        factor = 1.0 //(13)!
                        jitter = 1.1 //(14)!
                    }
                }
            }
        }
    }
    ```

    1. [Worker type (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) or the default settings name `default`
    2. Whether the worker is enabled (default: `true`)
    3. Name the worker is registered under on the broker (default: `default`)
    4. Maximum time for one job execution by the worker (default: `15m`)
    5. Maximum number of jobs that will be activated simultaneously for this worker; used to align job fetching speed with processing speed (`backpressure`) (default: `32`)
    6. Request timeout used for polling a new job by the worker (default: `15s`)
    7. Maximum interval between polling new jobs; if no jobs are activated after work is completed, the worker periodically polls the broker (default: `100ms`)
    8. `tenant` identifiers for which the worker can receive jobs (default: `[]`)
    9. Whether to use streaming together with polling for job activation (default: `false`)
    10. Maximum stream lifetime when streaming is enabled (default: `15s`)
    11. Minimum retry delay; due to `jitter`, the actual delay can be lower than this minimum (default: `100ms`)
    12. Maximum retry delay; due to `jitter`, the actual delay can exceed this value (default: `500ms`)
    13. Delay multiplication factor: the previous delay is multiplied by this value (default: `1.0`)
    14. `jitter` factor: the next delay is randomly changed within the `+/-` range of this factor (default: `1.1`)

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      worker:
        job:
          default: #(1)!
            enabled: true #(2)!
            name: "default" #(3)!
            timeout: "15m" #(4)!
            maxJobsActive: 32 #(5)!
            requestTimeout: "15s" #(6)!
            pollInterval: "100ms" #(7)!
            tenantIds: [] #(8)!
            streamEnabled: false #(9)!
            streamTimeout: "15s" #(10)!
            backoff:
              minDelay: "100ms" #(11)!
              maxDelay: "500ms" #(12)!
              factor: 1.0 #(13)!
              jitter: 1.1 #(14)!
    ```

    1. [Worker type (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/) or the default settings name `default`
    2. Whether the worker is enabled (default: `true`)
    3. Name the worker is registered under on the broker (default: `default`)
    4. Maximum time for one job execution by the worker (default: `15m`)
    5. Maximum number of jobs that will be activated simultaneously for this worker; used to align job fetching speed with processing speed (`backpressure`) (default: `32`)
    6. Request timeout used for polling a new job by the worker (default: `15s`)
    7. Maximum interval between polling new jobs; if no jobs are activated after work is completed, the worker periodically polls the broker (default: `100ms`)
    8. `tenant` identifiers for which the worker can receive jobs (default: `[]`)
    9. Whether to use streaming together with polling for job activation (default: `false`)
    10. Maximum stream lifetime when streaming is enabled (default: `15s`)
    11. Minimum retry delay; due to `jitter`, the actual delay can be lower than this minimum (default: `100ms`)
    12. Maximum retry delay; due to `jitter`, the actual delay can exceed this value (default: `500ms`)
    13. Delay multiplication factor: the previous delay is multiplied by this value (default: `1.0`)
    14. `jitter` factor: the next delay is randomly changed within the `+/-` range of this factor (default: `1.1`)

To override settings for a single worker, add a section keyed by the [worker type (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/)
declared in `@JobWorker`. A named section is merged over `default`, which in turn is merged over the built-in defaults,
so a named section only needs to list the keys it changes. Setting `enabled = false` on a named type disables just that
one worker.

===! ":material-code-json: `Hocon`"

    ```javascript
    zeebe {
        worker {
            job {
                foo { //(1)!
                    timeout = "30s"
                    maxJobsActive = 8
                }
                bar { //(2)!
                    enabled = false
                }
            }
        }
    }
    ```

    1. Overrides only `timeout` and `maxJobsActive` for the `@JobWorker("foo")` worker; all other settings come from `default`
    2. Disables the `@JobWorker("bar")` worker while leaving the rest of the configuration untouched

=== ":simple-yaml: `YAML`"

    ```yaml
    zeebe:
      worker:
        job:
          foo: #(1)!
            timeout: "30s"
            maxJobsActive: 8
          bar: #(2)!
            enabled: false
    ```

    1. Overrides only `timeout` and `maxJobsActive` for the `@JobWorker("foo")` worker; all other settings come from `default`
    2. Disables the `@JobWorker("bar")` worker while leaving the rest of the configuration untouched

### Declarative { #declarative }

You can declaratively create [workers](https://docs.camunda.io/docs/components/concepts/job-workers/) that perform work
within the `Zeebe` orchestrator.

The `@JobWorker` annotation specifies the [worker type (`Type`)](https://docs.camunda.io/docs/components/concepts/job-workers/)
from the process. `Zeebe` uses this value to connect a job from a `BPMN` process with a handler in the application.

Worker methods must satisfy the following requirements:

- The enclosing class must be a component in the [dependency graph](container.md), for example annotated with `@Component`.
- The method must not be `private` — compilation fails with `@JobWorker method can't be private`.
- The method may only declare `@JobVariable`, `@JobVariables`, and `JobContext` parameters — any other parameter type
  is rejected at compile time. The raw `JobClient` and `ActivatedJob` are available only in the [imperative](#imperative) worker.
- A variable name (both for arguments and for the result) must be alphanumeric, may contain `_`, must not start with
  a digit, and must not be a `FEEL` keyword such as `if`, `then`, `else`, `for` or `not`.

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

For each annotated method Kora generates a separate `KoraJobWorker` component and registers it on the broker at startup.
If several workers declare the same type, all of them are registered and a warning is written to the log.

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

`JobContext` exposes the following read-only accessors:

| Method                       | Description                                                                          |
|------------------------------|--------------------------------------------------------------------------------------|
| `jobKey()`                   | Unique key of the activated job                                                      |
| `jobName()`                  | Name the worker is registered under on the broker (the `name` configuration option)  |
| `jobType()`                  | Job type of the activated job as defined in the `BPMN` process                       |
| `jobWorker()`                | Name of the worker that activated the job on the broker side                         |
| `tenantId()`                 | Tenant identifier the job belongs to                                                 |
| `processId()`                | `BPMN` process identifier                                                             |
| `processInstanceKey()`       | Key of the process instance the job belongs to                                       |
| `processDefinitionVersion()` | Version of the deployed process definition                                           |
| `processDefinitionKey()`     | Key of the deployed process definition                                               |
| `elementId()`                | Identifier of the `BPMN` element the job was created for                              |
| `elementInstanceKey()`       | Key of the `BPMN` element instance                                                   |
| `headers()`                  | Custom headers defined on the job in the `BPMN` model                                |
| `retryCount()`               | Number of remaining retries for the job                                              |
| `deadline()`                 | Moment (`Instant`) until which the job is exclusively assigned to the worker         |
| `deadlineAsMillis()`         | Same deadline expressed as epoch milliseconds                                        |
| `variablesAsString()`        | Raw job variables as a `JSON` string                                                 |

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public void process(JobContext context) {
            logger.info("Job {} of process {} at element {} with deadline {}",
                    context.jobType(), context.processInstanceKey(), context.elementId(), context.deadline());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(context: JobContext) {
            logger.info("Job {} of process {} at element {} with deadline {}",
                context.jobType(), context.processInstanceKey(), context.elementId(), context.deadline())
        }
    }
    ```

The context of the job being handled is also bound to the `JobContext.VALUE`
[scoped value](https://openjdk.org/jeps/506) for the whole duration of the call, so code that is called from a worker can
read the job metadata through `JobContext.VALUE.get()` without passing the argument down the call stack.

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

A variable argument is required by default: if the process does not provide it, the job fails.
Mark the argument as nullable (`@Nullable` in `Java`, `T?` in `Kotlin`) to accept a missing or `null` variable.

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

        @Json
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
Only one `@JobVariables` argument is allowed per worker method.

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

        @Json
        data class User(val name: String, val code: Int)

        @Json
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

        @Json
        data class User(val name: String, val code: Int)

        @JobVariable("user")
        @JobWorker("someJobType")
        fun process(): User {
            // do something
        }
    }
    ```

#### Errors { #errors }

If you need to complete execution with a process error, throw `JobWorkerException` from the
`io.koraframework.camunda.zeebe.worker.exception` package.
The exception can contain an error code, message, and process variables if they are required.
This exception is converted to a `throwError` command for `Zeebe`: the `getCode()`, message, and `getVariables()`
of the exception are sent as the error code, error message, and variables of the command, and the `BPMN` model decides
how to handle the error, for example through a boundary error event.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeJob {

        @JobWorker("someJobType")
        public User process() {
            throw new JobWorkerException("DOESNT_WORK"); //(1)!
        }
    }
    ```

    1. Additional overloads accept a message/cause and a `Map<String, Object>` of variables to attach to the `throwError` command

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob {

        @JobWorker("someJobType")
        fun process(): User {
            throw JobWorkerException("DOESNT_WORK") //(1)!
        }
    }
    ```

    1. Additional overloads accept a message/cause and a `Map<String, Any>` of variables to attach to the `throwError` command

Any other exception is a technical failure rather than a process error: the module wraps it into a `JobWorkerException`
with one of the built-in codes below and lets it propagate. The job is then failed on the broker and reactivated
according to the worker `backoff` settings until the retries are exhausted and an incident is created.

| Code            | When it is used                                                                                     |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `SERIALIZATION` | The worker result could not be written into process variables                                       |
| `UNEXPECTED`    | Any other error from the worker method, including a job variable that could not be read into an argument |

### Imperative { #imperative }

You can also create lower-level workers and work directly with `CamundaClient` contracts.
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
        public List<String> fetchVariables() {
            return List.of("startId"); //(1)!
        }

        @Override
        public FinalCommandStep<?> handle(JobClient client, ActivatedJob job) {
            return client.newCompleteCommand(job); //(2)!
        }
    }
    ```

    1. Only these variables are fetched from `Zeebe`; return an empty list (the default) to fetch **all** variables
    2. The returned command is sent by the module after the telemetry of the call is recorded

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeJob : KoraJobWorker {

        override fun type(): String = "someJobType"

        override fun fetchVariables(): List<String> = listOf("startId") //(1)!

        override fun handle(client: JobClient, job: ActivatedJob): FinalCommandStep<*> {
            return client.newCompleteCommand(job) //(2)!
        }
    }
    ```

    1. Only these variables are fetched from `Zeebe`; return an empty list (the default) to fetch **all** variables
    2. The returned command is sent by the module after the telemetry of the call is recorded

The `fetchVariables()` method is the imperative analogue of `@JobVariable`: it controls which process variables `Zeebe`
sends with the job. By default it returns an empty list, which fetches all variables; returning a non-empty list limits
the payload to just those variables. Unlike declarative workers, `handle` receives the raw `JobClient` and `ActivatedJob`
and decides itself which command finishes the job — `client.newCompleteCommand(job)` to complete it, or
`client.newThrowErrorCommand(job).errorCode("DOESNT_WORK").errorMessage("...")` to raise a `BPMN` error.
An exception thrown out of `handle` fails the job instead, and the broker reactivates it according to the `backoff` settings.

## Signatures { #signatures }

Available signatures for worker methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value or `void`.
    If the result is `null` or `Optional.empty()`, the job is completed without adding variables.

    - `void myMethod()`
    - `T myMethod()`
    - `Optional<T> myMethod()`

    Asynchronous signatures are not supported: `CompletionStage`, `Future` and `Publisher` / `Mono` return types are
    rejected at compile time with `Async invocation is not supported`.

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `T`, `T?` or `Unit`.
    If the result is `null`, the job is completed without adding variables.

    - `myMethod()`
    - `myMethod(): T`
    - `myMethod(): T?`

    Asynchronous signatures are not supported: `suspend` functions and `Deferred`, `Mono`, `Flux` and `CompletionStage`
    return types are rejected at compile time.
