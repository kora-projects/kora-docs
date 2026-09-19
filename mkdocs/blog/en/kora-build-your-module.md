---
title: How to Build Your Own First-Class Kora Framework Module
date: 2026-08-16
description: A step-by-step guide to building a first-class Kora Framework module with typed config, lifecycle, telemetry, and compile-time DI.
search:
  exclude: true
---
# How to Build Your Own First-Class Kora Module { #build-your-own }

**August 16, 2026**

The Kora Framework's claim that it is **built to be extended** is more interesting than the generic statement that developers can register custom components.

Almost every dependency-injection framework can put a third-party client into a container. If all you need is an Elasticsearch client, a NATS connection, a MinIO client, or an internal library object,
the basic problem is easy: construct it once and inject it.

A first-class framework module is a much higher bar.

A first-class Kora module should make an external technology behave as if it naturally belongs inside the framework. It should participate in typed configuration, compile-time dependency injection,
lifecycle, graceful shutdown, telemetry, testing, component replacement, and the same explicit application model used by Kora's built-in integrations.

The core pattern is:

```text
third-party library
        ↓
thin Kora integration module
        ↓
typed configuration
lifecycle
telemetry
DI factories
optional probes
        ↓
application graph
        ↓
business components
```

The module should not try to erase the external technology. If Elasticsearch already has a good Java API, application developers should still think in Elasticsearch concepts. If NATS exposes subjects,
subscriptions, JetStream, and acknowledgements, those concepts should remain visible. If MinIO is an S3-compatible object store, object-storage semantics should not be replaced by an arbitrary
framework DSL.

Kora's job is to provide the production glue:

```text
library stays library
Java/Kotlin stays Java/Kotlin
Kora supplies configuration, lifecycle, telemetry, and wiring
```

That is the right way to understand the framework's extensibility model.

## A Module Is More Than a Factory Method { #module-factory-method }

Start with a fictional library:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class SearchClient {
        public SearchClient(String endpoint, String apiKey) {
            // ...
        }

        public SearchResult search(SearchRequest request) {
            // ...
        }

        public void close() {
            // ...
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class SearchClient(endpoint: String, apiKey: String) {

        fun search(request: SearchRequest): SearchResult {
            // ...
        }

        fun close() {
            // ...
        }
    }
    ```

A naive module could be:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SearchModule {

        default SearchClient searchClient() {
            return new SearchClient(
                "https://search.internal",
                "secret"
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SearchModule {

        fun searchClient(): SearchClient {
            return SearchClient(
                "https://search.internal",
                "secret"
            )
        }
    }
    ```

Technically this integrates the client with DI. Operationally it is weak. The endpoint and secret are hard-coded, lifecycle is unmanaged, telemetry does not exist, multiple instances are impossible,
testing requires replacing implementation manually, and there is no explicit production contract.

A first-class integration should solve the real lifecycle of the technology rather than merely construction.

A useful baseline is:

```text
1. Configuration
2. Dependency injection
3. Lifecycle
4. Telemetry
5. Testability
```

Depending on the technology, a production module may also need:

```text
6. Probes
7. Multi-instance support
8. Graceful shutdown
9. Resilience hooks
10. Native-image support
11. Testing utilities
12. Generated adapters
```

Not every library needs every feature. A small stateless formatter may need only a factory. A NATS consumer integration needs significantly more. The module should model the actual operational nature
of the technology.

## Kora Modules Belong to the Compile-Time Graph { #kora-modules-belong }

Kora's dependency graph is validated largely during compilation. A module is therefore not merely a runtime registration hook. It becomes part of the same compile-time architecture as controllers,
repositories, clients, telemetry components, and other application dependencies.

Inside an application compilation unit, an interface annotated with `@Module` can provide factory methods:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SearchModule {

        default SearchService searchService(SearchClient client) {
            return new SearchService(client);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SearchModule {

        fun searchService(client: SearchClient): SearchService {
            return SearchService(client)
        }
    }
    ```

The parameters are graph dependencies. If `SearchClient` has no provider, or several ambiguous providers exist, Kora can reject the application before startup.

That matters for extension authors because they do not need to build their own container or runtime registry. They describe components and relationships; Kora compiles the structure.

## External Modules Are Connected Explicitly { #external-modules-connected }

For reusable modules shipped in a separate artifact, Kora's model is deliberately explicit. An application enables the external module through its `@KoraApp` interface rather than by classpath
scanning.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SearchClientModule {
        // reusable integration factories
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SearchClientModule {
        // reusable integration factories
    }
    ```

and in the service:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends SearchClientModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : SearchClientModule
    ```

This distinction is important.

Adding a JAR to the classpath does not automatically mean:

```text
initialize its client
start its threads
connect to its remote system
register all its components
```

The application says explicitly:

```text
I want this module in my graph.
```

That makes the `@KoraApp` interface an architectural manifest.

A service may read:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application
        extends JsonModule,
        JdbcDatabaseModule,
        SearchClientModule,
        NatsModule,
        MinioModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        JsonModule,
        JdbcDatabaseModule,
        SearchClientModule,
        NatsModule,
        MinioModule
    ```

An engineer can immediately see which infrastructure families are enabled. The compiler sees the same thing. An AI agent sees the same thing.

This is stronger than hidden auto-configuration.

## Start With a Thin Integration Boundary { #start-thin-integration }

The first design question is not "What framework abstraction can I invent?"

It is:

> What does the native library already do well, and what production integration does Kora need to add around it?

Suppose the external library already exposes a good `SearchClient`. The module may simply expose that client directly:

```text
application service
      ↓
SearchClient
      ↓
third-party library
```

Do not immediately add:

```text
KoraSearchTemplate
KoraSearchOperations
KoraSearchRepository
KoraSearchGateway
```

unless those abstractions solve recurring problems.

Framework integration and technology abstraction are different concerns.

Framework integration answers:

```text
How is it configured?
Who creates it?
Who closes it?
How is it observed?
How is it replaced in tests?
How do several instances coexist?
```

Technology abstraction answers:

```text
Should application code see the native library at all?
Should we expose domain-specific repositories?
Should we isolate vendor APIs?
```

The first is usually necessary.

The second is optional.

A first-class module should not force a large framework-specific API when the native library is already good.

## Step 1: Model Configuration as a Type { #step-1-model }

A production integration should usually begin with typed configuration.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public interface SearchConfig {

        URI endpoint();

        String apiKey();

        default Duration connectTimeout() {
            return Duration.ofSeconds(2);
        }

        default Duration requestTimeout() {
            return Duration.ofSeconds(5);
        }

        default int maxConnections() {
            return 50;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    interface SearchConfig {

        fun endpoint(): URI

        fun apiKey(): String

        fun connectTimeout(): Duration {
            return Duration.ofSeconds(2)
        }

        fun requestTimeout(): Duration {
            return Duration.ofSeconds(5)
        }

        fun maxConnections(): Int {
            return 50
        }
    }
    ```

Configuration may look like:

===! ":material-code-json: Hocon"

    ```hocon
    search {
        endpoint = "https://search.internal"
        apiKey = ${SEARCH_API_KEY}
        connectTimeout = "2s"
        requestTimeout = "5s"
        maxConnections = 50
    }
    ```

=== ":simple-yaml: YAML"

    ```yaml
    search:
        endpoint: "https://search.internal"
        apiKey: "${SEARCH_API_KEY}"
        connectTimeout: 2s
        requestTimeout: 5s
        maxConnections: 50
    ```

The configuration interface describes the shape and semantics of the module configuration.

For reusable library code, it is useful to keep the type itself independent from one rigid config path. The module factory can choose where that shape is mapped from.

That permits reuse such as:

```text
search.primary
search.analytics
```

without copying the same configuration model.

## Library Configuration Should Be Path-Agnostic { #library-configuration-path }

There are two separate contracts:

```text
configuration shape
configuration location
```

The type answers:

```text
Which values exist?
Which are required?
What are their Java types?
Which defaults apply?
```

The module factory answers:

```text
Where does this application store them?
```

This separation is particularly useful when a shared module is consumed by different projects or several named instances.

It also prevents the reusable integration from hard-coding one organization's configuration hierarchy.

## Avoid Raw Config Deep in the Module { #avoid-raw-config }

It is possible to inject raw configuration and repeatedly write:

===! ":fontawesome-brands-java: `Java`"

    ```java
    config.get("search.endpoint").asString();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    config.get("search.endpoint").asString()
    ```

but that weakens the module.

String paths spread through construction code. Defaults and validation scatter. Configuration becomes harder to test. Refresh behavior may unintentionally affect a larger part of the graph.

Prefer this structure:

```text
raw Config
   ↓
ConfigValueMapper<SearchConfig>
   ↓
SearchConfig
   ↓
all remaining module components
```

Raw configuration should usually stay at the edge.

Typed configuration becomes the real module contract.

## Configuration Is a Public API { #configuration-public-api }

Once a module is shared, its configuration is as important as its Java API.

Changing:

```yaml
search:
    endpoint:
```

to:

```yaml
search:
    url:
```

may be a breaking deployment change even if every Java class still compiles.

Defaults matter too. Changing a default timeout from five seconds to sixty seconds changes production behavior.

A first-class module should document and version:

```text
property names
types
units
defaults
required values
security-sensitive values
semantic meaning
```

Configuration is not an implementation detail.

## Defaults Should Be Safe for Production { #defaults-safe-production }

Avoid convenient but dangerous defaults such as:

```text
infinite timeout
unbounded pool
TLS verification disabled
automatic destructive resource creation
unlimited retry
```

Prefer bounded, explicit defaults:

```text
finite timeouts
bounded connections
secure TLS
conservative retry
predictable shutdown
```

A reusable module centralizes production behavior across many services. Bad defaults scale just as efficiently as good ones.

## Step 2: Construct the Client Through DI { #step-2-construct }

Once configuration exists, create the client using normal graph dependencies:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SearchClientModule {

        default SearchClient searchClient(SearchConfig config) {
            return new SearchClient(
                config.endpoint(),
                config.apiKey(),
                config.connectTimeout(),
                config.requestTimeout()
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SearchClientModule {

        fun searchClient(config: SearchConfig): SearchClient {
            return SearchClient(
                config.endpoint(),
                config.apiKey(),
                config.connectTimeout(),
                config.requestTimeout()
            )
        }
    }
    ```

Business components now depend on a normal type:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CatalogSearchService {

        private final SearchClient search;

        public CatalogSearchService(SearchClient search) {
            this.search = search;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CatalogSearchService(private val search: SearchClient)
    ```

No static registry.

No service locator.

No runtime lookup.

The dependency graph says exactly what the application requires.

## The Graph Should Expose Real Infrastructure Dependencies { #graph-expose-real }

Suppose the integration also needs:

```text
CredentialsProvider
SearchTelemetry
TLS configuration
HTTP transport
```

Make those dependencies visible:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default SearchClient searchClient(
        SearchConfig config,
        CredentialsProvider credentials,
        SearchTelemetry telemetry,
        SearchTransport transport
    ) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun searchClient(
        config: SearchConfig,
        credentials: CredentialsProvider,
        telemetry: SearchTelemetry,
        transport: SearchTransport
    ): SearchClient {
        // ...
    }
    ```

This gives Kora useful information.

The graph can validate completeness.

Tests can replace individual pieces.

Lifecycle ordering can follow real dependency relationships.

Generated wiring becomes readable.

Hidden global lookups destroy those advantages.

## Compile-Time DI Is a Module Author's Safety Net { #compile-time-di }

Assume your module requires:

```text
SearchConfig
SearchTelemetry
CredentialsProvider
```

If the application forgets the credentials provider, that should become a graph build error rather than a late runtime surprise.

This is one of the strongest reasons to implement infrastructure as real Kora modules.

The module author does not need custom startup validation for basic dependency existence and ambiguity. Kora already provides that structural check.

## Step 3: Treat Lifecycle as Part of the API { #step-3-treat }

Infrastructure clients often own resources:

```text
TCP connections
event-loop threads
worker pools
subscriptions
heartbeats
buffers
background refresh tasks
```

Creating the object is only half the problem.

The integration must answer:

```text
When is it ready?
Who starts it?
Who stops it?
Who closes network resources?
What happens during partial startup failure?
```

Kora has explicit component lifecycle semantics.

A component can implement:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface Lifecycle {
        void init() throws Exception;

        void release() throws Exception;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface Lifecycle {
        fun init()

        fun release()
    }
    ```

For external types that cannot implement Kora interfaces, a factory can attach lifecycle through a wrapper.

This is exactly what an integration layer is for: preserving the external API while connecting its resource lifecycle to the application graph.

## Use AutoCloseable When It Is Enough { #use-autocloseable-enough }

If the native client already implements `AutoCloseable`, do not invent a parallel lifecycle abstraction merely for consistency.

The graph can close owned resources during release.

Prefer native contracts when they correctly represent ownership.

A good Kora integration stays close to the underlying technology.

## Use Lifecycle When Startup Has Real Meaning { #use-lifecycle-startup }

A NATS integration may need to:

```text
connect
register subscriptions
initialize JetStream consumers
wait for dispatcher readiness
```

A MinIO client may need no meaningful initialization beyond construction.

An Elasticsearch transport may need to create connection resources but not perform a blocking cluster health call.

Do not force every module to perform network validation during startup simply because lifecycle exists.

Every mandatory remote call on startup increases time-to-readiness and makes deployments more sensitive to external failures.

The module should distinguish:

```text
object created
resource initialized
application ready
```

carefully.

## LifecycleWrapper Is Useful for Third-Party Objects { #lifecyclewrapper-useful-third }

A factory can conceptually return a wrapped client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default Wrapped<SearchClient> searchClient(SearchConfig config) {
        var client = createSearchClient(config);

        return new LifecycleWrapper<>(
            client,
            value -> {
                // optional initialization
            },
            SearchClient::close
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun searchClient(config: SearchConfig): Wrapped<SearchClient> {
        val client = createSearchClient(config)

        return LifecycleWrapper(
            client,
            {
                // optional initialization
            },
            SearchClient::close
        )
    }
    ```

The rest of the application still injects `SearchClient`.

Lifecycle remains an integration concern.

This is a strong pattern for adapting libraries that know nothing about Kora.

## Reverse Dependency Release Is Valuable { #reverse-dependency-release }

Suppose:

```text
SearchIndexer
depends on
SearchClient
```

During shutdown, the dependent component should stop first, then the client can close.

Kora releases graph components in reverse dependency order.

That means correct graph modeling produces sensible resource shutdown naturally.

This is another reason hidden dependencies are harmful: the graph cannot order resources it cannot see.

## Graceful Shutdown Defines Integration Quality { #graceful-shutdown-defines }

Messaging makes this especially obvious.

A NATS consumer module should think about:

```text
stop accepting new messages
finish or cancel in-flight handlers
flush publishes
drain subscriptions
close connection
```

The exact behavior depends on NATS and application policy.

But simply closing a socket immediately during every rollout is not enough for a serious integration.

A client can be perfectly correct during steady state and still be operationally poor if every deployment loses work.

First-class modules integrate shutdown semantics.

## Avoid Unnecessary Startup Work { #avoid-unnecessary-startup }

Kora initializes independent graph components in parallel where possible.

A custom module can easily erase that advantage by doing unrelated sequential work in one factory:

```text
connect
ping cluster
create resources
download schema
warm cache
load metadata
```

Separate mandatory initialization from optional warm-up.

Do not perform deployment/control-plane work during normal application startup unless it is essential.

Framework startup performance depends on module authors too.

## Step 4: Give the Module a Telemetry Contract { #step-4-give }

A production module should answer:

```text
How does an operator observe this technology?
```

At minimum, think about:

```text
logging
metrics
tracing
```

A useful design is a module-specific telemetry abstraction:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SearchTelemetry {

        Context create(SearchOperation operation);

        interface Context {
            void close(Throwable error);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SearchTelemetry {

        fun create(operation: SearchOperation): Context

        interface Context {
            fun close(error: Throwable?)
        }
    }
    ```

Then each operation follows one lifecycle:

```text
start observation
  ↓
execute native operation
  ↓
close with success or failure
```

This mirrors Kora's broader telemetry architecture: operation-specific context around real work.

## One Observation Context Is Better Than Three Independent Wrappers { #one-observation-context }

A weak implementation may manually do:

```text
logger.start
timer.start
span.start
operation
logger.end
timer.stop
span.end
```

in every method.

A better structure is:

```text
SearchTelemetry
  ├── logging
  ├── metrics
  └── tracing
```

and one operation context handles start/end symmetry.

This centralizes success/failure semantics and makes no-op telemetry cheap when disabled.

## Telemetry Should Describe the Native Technology { #telemetry-describe-native }

Useful Elasticsearch-style dimensions may include:

```text
operation=search
index=products
result=success
```

For NATS:

```text
operation=publish
subject=orders.created
```

For MinIO:

```text
operation=put_object
bucket=assets
```

Do not hide these behind framework-specific vocabulary if operators already understand the technology.

At the same time, cardinality must be controlled.

An object key is generally a terrible metric label.

A NATS subject may be safe if bounded, dangerous if generated dynamically.

An Elasticsearch index may be bounded in one architecture and unbounded in another.

Technology knowledge is still required.

## Metrics Need Bounded Dimensions { #metrics-bounded-dimensions }

Metrics are aggregation tools.

Good dimensions often include:

```text
operation
bounded resource name
result class
error category
```

Bad dimensions often include:

```text
request ID
user ID
object key
raw query
full exception message
```

A first-class module should choose safe defaults so consuming services do not have to rediscover cardinality rules independently.

## Traces Can Carry Richer Context { #traces-carry-richer }

Tracing can usually tolerate richer request-level metadata than metrics.

A search span can include:

```text
system=elasticsearch
operation=search
index=products
result.count=20
```

without adding the full query body.

A NATS publish span can include subject and payload size without copying message content.

A MinIO upload span can include bucket and size while avoiding sensitive keys.

Telemetry should be useful without becoming a data leak.

## Logs Should Capture Exceptional State, Not Every Success { #logs-capture-exceptional }

Useful module logs include:

```text
NATS reconnect started
NATS reconnect completed
Elasticsearch node marked unavailable
MinIO multipart upload aborted
credential refresh failed
```

A module usually does not need an INFO log for every successful request if metrics and tracing already cover steady-state behavior.

Structured logging should explain unusual decisions and state transitions.

## Reuse Kora's Existing Observability Stack { #reuse-kora-s }

A custom integration should normally depend on the application's existing metrics, tracing, and logging infrastructure rather than inventing another exporter stack.

That gives one service:

```text
one MeterRegistry
one OpenTelemetry setup
one logging convention
```

instead of a different monitoring system for every library.

This is what makes a custom module operationally feel like a built-in Kora integration.

## Follow Familiar Telemetry Configuration Conventions { #follow-familiar-telemetry }

If built-in Kora modules use concepts such as:

===! ":material-code-json: Hocon"

    ```hocon
    telemetry {
        logging {
            enabled = false
        }

        metrics {
            enabled = true
        }

        tracing {
            enabled = true
        }
    }
    ```

=== ":simple-yaml: YAML"

    ```yaml
    telemetry:
        logging:
            enabled: false

        metrics:
            enabled: true

        tracing:
            enabled: true
    ```

a custom module should strongly consider a similar shape.

For example:

===! ":material-code-json: Hocon"

    ```hocon
    search {
        endpoint = "https://search.internal"

        telemetry {
            logging {
                enabled = false
            }

            metrics {
                enabled = true
            }

            tracing {
                enabled = true
            }
        }
    }
    ```

=== ":simple-yaml: YAML"

    ```yaml
    search:
        endpoint: "https://search.internal"

        telemetry:
            logging:
                enabled: false

            metrics:
                enabled: true

            tracing:
                enabled: true
    ```

Developers already familiar with Kora will immediately understand it.

First-class means coherent with the framework, not merely compatible with it.

## Decide Whether to Expose the Native Client or a Thin Adapter { #decide-whether-expose }

There are two good designs.

### Native client as the component { #native-client-component }

```text
business service
  ↓
SearchClient
```

This is ideal when the third-party client already exposes useful hooks for transport, telemetry, or lifecycle.

### Thin instrumented adapter { #thin-instrumented-adapter }

```text
business service
  ↓
InstrumentedSearchClient
  ↓
SearchClient
```

This is useful when telemetry or policy cannot be attached cleanly to the native client.

The wrapper should earn its existence.

If it only renames:

===! ":fontawesome-brands-java: `Java`"

    ```java
    delegate.search(request);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    delegate.search(request)
    ```

it provides little value.

A useful wrapper should contribute something real:

```text
telemetry
mapping
policy
resource ownership
routing
stable internal API
```

## Concrete Search Module Architecture { #concrete-search-module }

A reasonable architecture might be:

```text
SearchConfig
    ↓
CredentialsProvider
    ↓
SearchTransport
    ↓
SearchTelemetry
    ↓
SearchClient
    ↓
CatalogSearchService
```

A typed configuration:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public interface SearchConfig {

        URI endpoint();

        String apiKey();

        default Duration connectTimeout() {
            return Duration.ofSeconds(2);
        }

        default Duration requestTimeout() {
            return Duration.ofSeconds(5);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    interface SearchConfig {

        fun endpoint(): URI

        fun apiKey(): String

        fun connectTimeout(): Duration {
            return Duration.ofSeconds(2)
        }

        fun requestTimeout(): Duration {
            return Duration.ofSeconds(5)
        }
    }
    ```

A simple telemetry adapter:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class InstrumentedSearchClient {

        private final SearchClient delegate;
        private final SearchTelemetry telemetry;

        public InstrumentedSearchClient(
            SearchClient delegate,
            SearchTelemetry telemetry
        ) {
            this.delegate = delegate;
            this.telemetry = telemetry;
        }

        public SearchResult search(SearchRequest request) {
            var ctx = telemetry.create(
                new SearchOperation("search", request.index())
            );

            try {
                var result = delegate.search(request);
                ctx.close(null);
                return result;
            } catch (Throwable e) {
                ctx.close(e);
                throw e;
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class InstrumentedSearchClient(
        private val delegate: SearchClient,
        private val telemetry: SearchTelemetry
    ) {

        fun search(request: SearchRequest): SearchResult {
            val ctx = telemetry.create(
                SearchOperation("search", request.index())
            )

            try {
                val result = delegate.search(request)
                ctx.close(null)
                return result
            } catch (e: Throwable) {
                ctx.close(e)
                throw e
            }
        }
    }
    ```

The application graph handles construction.

The business code sees a normal typed client.

## Keep Factory Methods Small { #keep-factory-methods }

Avoid a giant factory such as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default SearchEverything everything(
        Config config,
        MeterRegistry registry,
        OpenTelemetry telemetry,
        CredentialsProvider credentials,
        TlsFactory tls,
        Executor executor,
        ...
    ) {
        // hundreds of lines
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun everything(
        config: Config,
        registry: MeterRegistry,
        telemetry: OpenTelemetry,
        credentials: CredentialsProvider,
        tls: TlsFactory,
        executor: Executor,
        ...
    ): SearchEverything {
        // hundreds of lines
    }
    ```

Prefer smaller graph nodes:

```text
SearchConfig
  ↓
SearchCredentials
  ↓
SearchTransport
  ↓
SearchTelemetry
  ↓
SearchClient
```

Compile-time DI is good at assembling components.

Let Kora do that work rather than creating a private mini-container inside one method.

## Design Explicit Override Points { #design-explicit-override }

A shared module may provide:

```text
DefaultSearchTelemetry
DefaultCredentialsProvider
DefaultTransportFactory
```

but some applications will need replacements.

Good extension points often include:

```text
CredentialsProvider
TransportFactory
TelemetryFactory
ClientCustomizer
```

Do not expose every internal object as public API.

Expose stable boundaries where customization is genuinely useful.

This prevents forks without freezing implementation details.

## Replaceability Is Part of "Built to Be Extended" { #replaceability-part-built }

Extensibility is not only the ability to add new components.

It is also the ability to replace defaults.

A generic search module may use static API-key credentials by default while one production platform uses workload identity.

The module should allow that replacement through DI.

The same applies to telemetry, TLS, transport, and selected client construction behavior.

A first-class module is reusable because it provides strong defaults without being rigid.

## Multiple Instances Need Deliberate Design { #multiple-instances-deliberate }

Applications often outgrow the assumption of one global client.

Examples:

```text
primary search cluster
analytics search cluster

control-plane NATS
event-plane NATS

internal object storage
external object storage
```

Kora's tagging and factory-module patterns can represent several independently configured instances.

The module author should consciously choose whether multi-instance use is supported.

Do not accidentally make it impossible by hiding all state in one static singleton.

## Factory Modules Help Parameterized Integrations { #factory-modules-help }

Sometimes one reusable module implementation needs to be parameterized by configuration path or logical identity.

Conceptually:

```text
SearchFactoryModule("search.primary")
SearchFactoryModule("search.analytics")
```

can create two independent sets:

```text
SearchConfig
SearchTelemetry
SearchClient
```

with tags distinguishing them.

This is a powerful feature because custom infrastructure can use the same graph primitives Kora uses for its own parameterized modules.

Third-party integrations are not restricted to a weaker extension model.

## Tags Should Express Meaning { #tags-express-meaning }

Tags are appropriate when two components have the same type but different semantic roles:

```text
@PrimarySearch SearchClient
@AnalyticsSearch SearchClient
```

That communicates architecture.

Tags are less useful when added arbitrarily to repair poorly designed graph ambiguity.

A tag should tell the reader *why* the components differ.

## Elasticsearch: What a First-Class Module Needs { #elasticsearch-what-first }

A good Elasticsearch module should probably integrate:

```text
typed config
credentials
TLS
HTTP transport
native client
client/transport lifecycle
telemetry
optional health information
test support
```

A conceptual graph:

```text
ElasticsearchConfig
        ↓
CredentialsProvider
        ↓
Transport
        ↓
ElasticsearchClient
        ↓
SearchService
```

The native Elasticsearch API should remain visible unless the organization deliberately wants a stable internal abstraction.

Telemetry may be best attached at the transport level if the native client provides suitable hooks. Wrapping every high-level API call manually can be brittle.

The goal is to use native extension points where possible and add Kora integration around them.

## Do Not Double-Instrument Elasticsearch { #double-instrument-elasticsearch }

Modern clients and transports may already expose OpenTelemetry-compatible instrumentation.

If the native library already creates a useful client span and the Kora module creates an identical span around it, traces become noisy:

```text
search
  ↓
search
    ↓
HTTP request
```

Understand the library's observability model before adding another layer.

A first-class module composes with native instrumentation rather than blindly duplicating it.

## NATS: Lifecycle Is the Main Challenge { #nats-lifecycle-main }

A NATS integration may include:

```text
connection
reconnect state
JetStream context
subscriptions
dispatchers
message handlers
drain
flush
shutdown
```

A possible graph is:

```text
NatsConfig
   ↓
NatsConnection
   ├── NatsPublisher
   ├── JetStream
   └── NatsConsumerManager
          ↓
       handlers
```

Here lifecycle is much more important than simple construction.

The consumer manager may need to start subscriptions after the connection is ready and drain them before the connection closes.

Telemetry should cover publish operations and message processing.

A good integration should expose reconnect and consumer behavior operationally.

## Side-Effect Components May Need to Be Roots { #side-effect-components }

A consumer manager may exist only because its lifecycle starts subscriptions.

No other component necessarily injects it.

In a demand-driven dependency graph, such a component can disappear if nothing pulls it into the graph.

Infrastructure whose existence itself is application behavior may need to be marked as a root component.

Examples include:

```text
message consumer manager
background watcher
scheduler
subscription starter
```

Do not mark everything as root.

Use root status for components whose side effects are intentionally part of the running application.

## MinIO: Keep Object-Storage Semantics Visible { #minio-keep-object }

A MinIO module is usually closer to a client module.

Configuration may include:

```text
endpoint
access key
secret key
region
timeouts
TLS
```

Telemetry may describe:

```text
get_object
put_object
remove_object
stat_object
bucket
duration
payload size
result
```

Avoid metric dimensions such as raw object key.

Do not automatically create buckets during every application startup unless that is an explicit control-plane feature.

A service using MinIO for data-plane operations should not automatically require bucket-administration privileges.

## Separate Control Plane From Data Plane { #separate-control-plane }

This principle applies across technologies.

Examples of control-plane actions:

```text
create Elasticsearch index
install templates
create NATS stream
change retention
create object-storage bucket
```

Examples of data-plane actions:

```text
search
publish
consume
put object
get object
```

Application replicas commonly need the data plane.

They may not need administrative privileges.

A first-class module should avoid mixing deployment/setup work into every service startup unless the architecture explicitly requires it.

## Internal Library X Uses the Same Pattern { #internal-library-x }

Suppose a company owns:

```text
FraudModelClient
```

It needs typed configuration, TLS, credentials, telemetry, model refresh, and graceful shutdown.

A Kora module can expose:

```text
FraudModelConfig
FraudModelTelemetry
FraudModelClient
FraudModelModelWatcher
FraudModelProbe
```

The pattern is identical.

This is where framework modularity becomes organizationally valuable: company-specific infrastructure can participate in the same application model as built-in integrations.

## Keep the Public Module Surface Small { #keep-public-module }

Once several services depend on a module, every public type becomes a compatibility promise.

Expose only what consumers and extension authors genuinely need.

A useful shape may be:

```text
SearchModule
SearchConfig
SearchClient
SearchTelemetry
SearchTelemetryFactory
```

Implementation details should remain private.

This makes upgrades easier and keeps the module understandable.

## Separate Core Library From Kora Integration { #separate-core-library }

If you own library X, consider:

```text
library-core
library-kora
```

rather than forcing the core library itself to depend on Kora.

Then the core library can be used:

```text
inside Kora
outside Kora
in command-line utilities
in standalone tests
```

and the Kora module acts as a framework adapter.

This keeps responsibilities clean.

## Fine-Grained Dependencies Matter { #fine-grained-dependencies }

A custom module should depend only on the Kora capabilities it actually uses.

If a MinIO integration needs configuration and telemetry, it should not pull in HTTP server, database, Kafka, and unrelated modules.

Likewise optional testing utilities should not be production dependencies.

This follows Kora's broader principle:

```text
enable only what the service needs
```

A bloated integration can undermine the framework's modular runtime.

## Optional Features Should Be Actually Optional { #optional-features-actually }

Suppose tracing is disabled.

The module should be able to use a cheap no-op telemetry path instead of requiring unnecessary exporter behavior.

Suppose probes are not used.

The client should not start a background health checker merely because the integration supports one.

Optional features should not quietly pull large runtime subgraphs into every application.

## Probes Are a Policy Decision { #probes-policy-decision }

Should an unavailable Elasticsearch cluster make the application unready?

Sometimes yes.

Sometimes no.

A service that cannot perform any useful work without search may reasonably fail readiness.

A service that can fall back to PostgreSQL probably should not remove itself from traffic just because search is down.

A reusable module therefore should usually expose health information without imposing universal readiness or liveness semantics.

The application decides how dependency health maps to traffic admission.

## Do Not Turn Remote Dependency Failure Into Liveness Failure { #turn-remote-dependency }

Restarting an application rarely repairs an unavailable external service.

A NATS outage, Elasticsearch outage, or MinIO outage should not automatically cause every service replica to fail liveness and restart.

That can turn one infrastructure incident into a fleet-wide restart storm.

Probe design belongs to module architecture, not only framework configuration.

## Health Checks Must Be Cheap { #health-checks-cheap }

A probe should not run an expensive search or object upload every second from every Pod.

That creates production load from monitoring itself.

Prefer:

```text
native lightweight health endpoint
connection state
bounded ping
cached health state
```

depending on the technology.

Observability should not become an attack on the dependency.

## Configuration Refresh Needs a Deliberate Policy { #configuration-refresh-deliberate }

Kora can refresh affected graph components when configuration changes.

A module author should ask:

```text
Can this client be recreated safely?
Should consumers be recreated too?
Should some long-lived component observe the new client indirectly?
Does this change require a process restart?
```

Do not inherit refresh behavior accidentally.

External clients may own sockets, subscriptions, threads, or expensive state.

Configuration reload is powerful and should reflect resource semantics.

## Direct Dependencies and ValueOf Mean Different Lifecycle Coupling { #direct-dependencies-valueof }

A direct graph dependency means the consumer is lifecycle-coupled to the dependency.

An indirect `ValueOf<T>` dependency can let a long-lived component observe the current value without being rebuilt whenever that dependency changes.

This is useful for infrastructure that should remain running while one of its dependencies refreshes.

But do not use indirection simply to avoid a correct dependency relationship.

Use it when live replacement is a real architectural requirement.

## Testing Is Part of Module Design { #testing-part-module }

A first-class module should be testable at several levels.

### Module unit tests { #module-unit-tests }

Validate:

```text
config mapping
validation
telemetry classification
factory logic
error mapping
```

### Module integration tests { #module-integration-tests }

Use real infrastructure where protocol semantics matter:

```text
connect
authenticate
perform operation
observe telemetry
shutdown
```

### Consumer application tests { #consumer-application-tests }

Allow the application to replace the real client with a fake or test implementation.

Each level answers different questions.

## Component Replacement Is a Primary Test Seam { #component-replacement-primary }

A service test should be able to replace:

```text
SearchClient
```

with:

```text
FakeSearchClient
```

without starting Elasticsearch.

Then a separate integration suite exercises the real client module.

This is a healthy split:

```text
business tests
→ fake infrastructure

integration tests
→ real infrastructure
```

DI should make that easy.

If the module makes replacement difficult, its integration boundary is probably too rigid.

## Real Integration Tests Are Still Necessary { #real-integration-tests }

Mocks cannot prove:

```text
TLS behavior
authentication
protocol compatibility
Elasticsearch query semantics
NATS acknowledgement
MinIO multipart behavior
native retry
network timeout
shutdown
```

The module itself needs real integration coverage.

Testcontainers or equivalent disposable infrastructure is ideal where available.

Kora's fast graph startup helps make such tests practical.

## Test Lifecycle, Not Only Business Operations { #test-lifecycle-business }

A module test should verify more than:

```text
client.search() returns result
```

Also test:

```text
startup failure
partial startup cleanup
shutdown
repeated start/stop where relevant
in-flight operation handling
resource closure
```

Many integration bugs appear only during rolling deployment or partial failure.

First-class modules need lifecycle tests.

## Test Telemetry Semantics { #test-telemetry-semantics }

Verify:

```text
success metric emitted once
failure classification stable
span closes on exception
secrets are not logged
operation names remain bounded
```

Dashboards and alerts may depend on these contracts.

Telemetry is part of the module API.

## Failure Injection Matters { #failure-injection-matters }

Infrastructure modules should test:

```text
connection refused
authentication failure
timeout
remote server error
broker disconnect
invalid configuration
shutdown during work
```

and verify:

```text
error type
cleanup
telemetry
probe behavior
```

A module's production quality is defined heavily by its failure path.

## Startup Errors Should Be Actionable { #startup-errors-actionable }

If initialization fails, the error should tell the developer:

```text
which integration
which endpoint
which lifecycle phase
what underlying error occurred
```

Avoid vague wrapping such as:

```text
RuntimeException: init failed
```

Kora can show graph initialization failure, but the module should preserve enough detail to make the graph error useful.

## Partial Initialization Needs Cleanup { #partial-initialization-cleanup }

Consider:

```text
connection created
subscription A registered
subscription B fails
```

The integration must release A and the connection.

Lifecycle code that assumes startup always completes can leak resources.

Simple clients can use simple wrappers.

Complex subscription systems may deserve a dedicated manager with explicit state.

## Separate Managers When Responsibilities Differ { #separate-managers-responsibilities }

A NATS architecture may benefit from:

```text
NatsConnection
NatsConsumerManager
```

The connection owns transport.

The manager owns subscriptions and message-processing lifecycle.

During shutdown:

```text
consumer manager drains
  ↓
connection closes
```

The graph naturally represents this ordering.

Do not overload one component with unrelated responsibilities merely to minimize class count.

## Resource Ownership Must Be Explicit { #resource-ownership-explicit }

For every resource answer:

```text
Who creates it?
Who closes it?
Can it be shared?
Can the application provide its own?
```

For example:

```text
Search HTTP transport
  created by module
  owned by module
  closed by module

OpenTelemetry tracer
  created by application/platform
  injected into module
  not closed by module
```

A component should never close a shared dependency it does not own.

Ownership is part of lifecycle design.

## Avoid Hidden Thread Pools { #avoid-hidden-thread }

Third-party clients may create their own workers or event loops.

If the module supports multiple client instances, thread count can multiply unexpectedly.

Document important resource behavior.

Where safe and supported, allow shared executors or transports to be injected.

Do not hide expensive background resources behind a tiny-looking client factory.

## Threading Should Respect the Native Library { #threading-respect-native }

Some clients are synchronous.

Some are asynchronous.

Some manage their own event loops.

Kora 2's virtual-thread model means a synchronous blocking client can often remain synchronous without requiring a reactive wrapper.

Do not automatically add executors or asynchronous adapters for aesthetic consistency.

Thin integration means respecting the native execution model.

## Resilience Should Be Composable, Not Secretly Hard-Coded { #resilience-composable-secretly }

Should every search retry three times?

Should every object upload use a circuit breaker?

Should every NATS publish retry automatically?

There is no universal answer.

Prefer:

```text
native transport retry where appropriate
+
application/Kora resilience policy where semantically appropriate
```

rather than hiding aggressive behavior inside client construction.

A module should document native retry semantics so application-level retry does not accidentally multiply attempts.

## Retry Amplification Is Easy to Create { #retry-amplification-easy }

Suppose:

```text
native client retry = 3
Kora @Retry = 3
```

The system may perform up to nine attempts.

Under dependency failure, this can amplify load dramatically.

Module telemetry should make attempts and failures visible where possible.

Documentation should explain native behavior.

Framework integration should reduce surprises, not create them.

## Timeout Layers Need the Same Care { #timeout-layers-same }

A native request timeout and an outer Kora timeout are not necessarily the same.

For example:

```text
outer operation timeout = 2s
native client timeout = 10s
```

If cancellation is weak, the application may stop waiting while the underlying operation continues consuming resources.

A first-class module should document cancellation and timeout behavior of the underlying library.

Operational correctness depends on it.

## Security Configuration Should Be Explicit { #security-configuration-explicit }

Credentials should not be fetched from random environment variables inside deep implementation code.

Prefer a clear dependency:

```text
CredentialsProvider
```

or a typed secret configuration.

This allows applications to choose:

```text
static secret
Vault
cloud workload identity
rotating credentials
```

without changing business code.

Separating credential acquisition from client construction is an excellent extension seam.

## TLS Is Part of the Integration Contract { #tls-part-integration }

Serious modules need to consider:

```text
custom CA
client certificate
hostname verification
TLS protocol policy
```

Do not make insecure TLS the easy configuration.

If the organization has shared TLS components, integrate with them.

Otherwise expose clear typed options.

Security is not an afterthought to client construction.

## Never Leak Secrets Through Telemetry { #never-leak-secrets }

The module sees credentials and potentially sensitive request data.

It should prevent accidental logging of:

```text
API key
Authorization header
password
secret access key
signed URL
credential token
```

Masking belongs in the shared integration so each service does not reinvent it.

Centralized module code is a force multiplier for both good and bad security.

## Start With DI Before Building Code Generation { #start-di-building }

Kora uses annotation processors extensively, but a custom module does not automatically need one.

A sensible progression is:

```text
Phase 1:
module factories

Phase 2:
typed config + lifecycle

Phase 3:
telemetry + tests

Phase 4:
multi-instance support

Phase 5:
generation only if repetitive static contracts justify it
```

Do not build a processor merely because Kora itself has processors.

Use code generation when there is genuine compile-time structure worth generating.

## A First-Class Module Can Have Almost No Kora API at the Use Site { #first-class-module }

This is often the ideal result.

The module itself uses:

```text
modules
configuration mapping
lifecycle
telemetry
tags
```

but business code simply injects:

===! ":fontawesome-brands-java: `Java`"

    ```java
    SearchClient
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    SearchClient
    ```

and calls it.

That means framework integration succeeded without contaminating normal technology usage.

Kora is rich at the assembly boundary and thin in the runtime programming model.

## Compare Thin Integration With a Wrapper Stack { #compare-thin-integration }

An over-engineered integration may become:

```text
Your code
  ↓
KoraSearchRepositoryDSL
  ↓
KoraSearchTemplate
  ↓
KoraSearchOperations
  ↓
adapter
  ↓
Elasticsearch client
```

A thin integration prefers:

```text
Your code
  ↓
Elasticsearch client
```

plus Kora-managed construction and operations around it.

Add higher-level APIs only when they solve a real recurring problem.

Every additional abstraction creates upgrade and learning cost.

## Thin Modules Upgrade More Easily { #thin-modules-upgrade }

When the native client changes, a thin module mostly updates:

```text
construction
transport hooks
lifecycle
telemetry integration
```

A large framework-specific abstraction may need to translate many vendor features across versions.

Keeping semantic distance low reduces maintenance.

This is especially important for infrastructure libraries that evolve quickly.

## Versioning Policy Matters { #versioning-policy-matters }

A shared module should document:

```text
supported native client version
Kora compatibility
dependency-management assumptions
whether native client dependency is exposed
```

There is no one correct versioning scheme.

But the policy must be deliberate.

Too much flexibility can produce incompatible dependency combinations.

Too much pinning can block security updates.

## Dependency Conflicts Are Module Engineering { #dependency-conflicts-module }

Infrastructure clients frequently depend on:

```text
Netty
Jackson
OkHttp
protobuf
logging APIs
```

A reusable module must coexist with the wider Kora stack.

Avoid unnecessary shading or private copies of foundational libraries.

Align through dependency management where practical.

A first-class integration is not only API glue; it is also dependency hygiene.

## The Module's Telemetry Schema Is an API { #module-s-telemetry }

Changing a metric from:

```text
search.request.duration
```

to:

```text
search.operation.duration
```

may break dashboards.

Changing labels can break alert queries.

Changing span naming can break trace searches.

Telemetry compatibility matters once a module is widely deployed.

Version it deliberately.

## A Module Becomes an Organizational Platform Primitive { #module-becomes-organizational }

The first service can integrate library X locally.

The fifth service should probably not copy the same setup again.

A shared Kora module can centralize:

```text
construction
timeouts
TLS
credentials
telemetry
shutdown
dependency versions
testing support
```

Every service receives the accumulated infrastructure knowledge.

This is where modularity becomes an organizational scaling mechanism.

## Do Not Extract Shared Modules Too Early { #extract-shared-modules }

One service with one factory does not necessarily justify a platform artifact.

A useful evolution is:

```text
local integration
  ↓
second real consumer
  ↓
identify stable shared behavior
  ↓
extract reusable module
```

Premature infrastructure abstractions often freeze the wrong API.

Let real usage reveal the stable integration boundary.

## First-Class Does Not Mean Official { #first-class-mean }

A company module can be just as first-class as a Kora-maintained integration if it participates correctly in:

```text
graph
config
lifecycle
telemetry
testing
operations
```

That is the practical test of extensibility.

Users should not need modifications to Kora core to build production-grade integrations.

## The Compiler Is Part of the Extension Surface { #compiler-part-extension }

By declaring module factories and typed dependencies, custom integrations automatically benefit from Kora's compiler:

```text
missing dependency detection
ambiguity detection
cycle detection
generated wiring
```

The module author does not need a runtime bootstrap engine.

This is a powerful property.

The framework's compiler becomes infrastructure shared by the ecosystem.

## Generated Wiring Helps Debug Custom Modules { #generated-wiring-helps }

If an integration behaves strangely, developers can inspect generated application wiring and see:

```text
which factory created the client
which dependencies were injected
which implementation won
```

This is especially useful for organization-wide modules maintained by a platform team.

Consumers are not forced to trust invisible auto-configuration.

They can inspect what Kora built.

## AI Agents Benefit From Explicit Modules { #ai-agents-benefit }

An AI agent can follow:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends SearchClientModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : SearchClientModule
    ```

then inspect:

```text
SearchConfig
module factories
LifecycleWrapper
SearchTelemetry
generated graph
```

If the graph is incomplete, compilation provides precise feedback.

There is little classpath magic to infer.

This is exactly the kind of architecture that works well with agent-assisted infrastructure development.

## Strong Types Improve Both DI and AI { #strong-types-improve }

Avoid module APIs dominated by:

```text
Object
Map<String, Object>
generic context bags
```

when a stronger type exists.

Prefer:

```text
SearchConfig
SearchTelemetryFactory
SearchClient
CredentialsProvider
```

Strong contracts improve graph validation, IDE navigation, documentation, and AI reasoning.

Type quality directly affects infrastructure quality.

## Avoid Service-Locator APIs { #avoid-service-locator }

Kora supports advanced graph access for cases that genuinely need it.

Do not use it for ordinary construction.

Prefer:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default SearchClient searchClient(
        SearchConfig config,
        SearchTelemetry telemetry
    ) {
        ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun searchClient(
        config: SearchConfig,
        telemetry: SearchTelemetry
    ): SearchClient {
        ...
    }
    ```

to:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default SearchClient searchClient(Graph graph) {
        // dynamic lookups
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun searchClient(graph: Graph): SearchClient {
        // dynamic lookups
    }
    ```

Typed dependency parameters preserve compile-time validation.

Use graph lookup only when dynamic graph behavior is truly part of the problem.

## Avoid Building a Second Container Inside a Factory { #avoid-building-second }

If one module method contains complex conditional lookups, manual singleton caching, and dynamic construction, the module is recreating a DI container inside Kora.

Instead, express architecture as graph components where practical.

Let Kora resolve dependencies.

Factory methods should create values, not implement a hidden application framework.

## Optional Features Should Not Pull Unused Infrastructure { #optional-features-pull }

If the module supports:

```text
tracing
admin API
health checks
JetStream management
index provisioning
```

but an application needs only the base client, it should not initialize everything.

This applies Kora's own modularity principle recursively:

```text
use only what you need
```

A custom module should not become a monolith inside a modular framework.

## Split Large Integrations When Boundaries Become Real { #split-large-integrations }

A mature integration ecosystem may eventually have:

```text
kora-nats-core
kora-nats-jetstream
kora-nats-testing
```

or:

```text
kora-search-client
kora-search-admin
kora-search-testing
```

Do this only when the boundaries reduce dependencies or runtime behavior.

More Gradle modules are not automatically better modularity.

The split should correspond to meaningful capability boundaries.

## Testing Utilities Can Live Separately { #testing-utilities-live }

A production artifact should not need to depend on Testcontainers or large fake infrastructure.

Testing support can live in a dedicated artifact:

```text
SearchTestKit
NatsTestContainer
MinioFixture
FakeSearchClient
```

This preserves a clean production dependency graph while standardizing test setup for consumers.

## The Ideal Developer Experience { #ideal-developer-experience }

A consumer of a finished module should be able to do something close to:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends SearchClientModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : SearchClientModule
    ```

provide:

===! ":material-code-json: Hocon"

    ```hocon
    search {
        endpoint = "https://search.internal"
        apiKey = ${SEARCH_API_KEY}
    }
    ```

=== ":simple-yaml: YAML"

    ```yaml
    search:
        endpoint: "https://search.internal"
        apiKey: "${SEARCH_API_KEY}"
    ```

and inject:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ProductSearchService {

        private final SearchClient search;

        public ProductSearchService(SearchClient search) {
            this.search = search;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ProductSearchService(private val search: SearchClient)
    ```

The application developer should not manually:

```text
parse config
build transport
register shutdown hooks
construct metrics
create spans
mask credentials
close resources
```

The module owns those mechanics.

At the same time, if something goes wrong, the factories and generated graph remain inspectable.

That combination is the Kora ideal:

```text
easy default
+
explicit mechanism
```

## The Ideal Operator Experience { #ideal-operator-experience }

The operator should see the custom integration through the same tools as built-in Kora modules:

```text
operation metrics
distributed spans
structured errors
lifecycle logs
probe state where configured
```

There should not be a separate observability ecosystem simply because the client came from a third-party library.

First-class means operationally native too.

## The Ideal Platform-Team Experience { #ideal-platform-team }

A platform team should be able to publish:

```text
company-kora-elasticsearch
company-kora-nats
company-kora-minio
```

and know every service receives standardized:

```text
config
timeouts
TLS
credentials
telemetry
shutdown
test support
```

That is where the "Built to be extended" claim becomes strategically important.

Kora does not need every possible integration in its own repository if teams can create integrations that reach the same quality level using public framework primitives.

## Modularity Lets a Focused Framework Stay Focused { #modularity-lets-focused }

Kora deliberately avoids trying to wrap every technology behind one enormous framework abstraction.

That philosophy only works if extension is practical.

Otherwise every missing integration becomes a framework limitation.

A healthy model is:

```text
Kora core
provides application model

technology module
adapts library into that model

application
chooses module explicitly
```

The framework can remain focused while the ecosystem grows.

## Extension Quality Matters More Than Extension Count { #extension-quality-matters }

A framework with hundreds of integrations is not necessarily more extensible.

The important question is:

> Can a competent team build the next integration without fighting hidden framework internals?

Kora provides the raw materials:

```text
module factories
compile-time DI
typed config
lifecycle
wrappers
tags
root components
telemetry
testing
component replacement
```

If those are enough to build a production-quality integration, the extension model is healthy.

## A Good Module Should Become Boring { #good-module-become }

Once the module is finished, application developers should rarely think about its infrastructure mechanics.

They should inject the client and write business code.

Operators should get predictable telemetry.

Tests should replace the component cleanly.

Shutdown should release resources correctly.

Configuration should behave predictably.

Boring infrastructure is success.

## "Built to Be Extended" Means the Application Model Remains Open { #built-extended-means }

The deepest point is that Kora's own application model is available to extension authors.

You can use the same basic ideas:

```text
modules
factory methods
typed configuration
lifecycle
graph dependencies
tags
root components
telemetry
testing replacements
```

to build your own production integration.

You are not confined to a weak plugin API while framework-owned modules use privileged internal mechanisms.

That is what makes an integration capable of becoming first-class.

## A Practical Development Sequence { #practical-development-sequence }

When integrating a new library, a good progression is:

```text
1. Integrate it locally in one real service.
2. Understand native construction and ownership.
3. Extract typed configuration.
4. Move construction into DI factories.
5. Add lifecycle.
6. Add telemetry.
7. Add real integration tests.
8. Add consumer replacement seams.
9. Add multi-instance support only if needed.
10. Add code generation only if static repetition justifies it.
```

This keeps the module grounded in actual requirements.

Do not begin by designing the universal abstraction you hope to need someday.

## Measure the Module Under Real Load { #measure-module-real }

A custom integration can affect:

```text
startup time
readiness
memory
thread count
connection count
request latency
shutdown duration
```

Benchmark it.

Observe reconnect behavior.

Test dependency outages.

Measure telemetry overhead.

Check shutdown under load.

A module becomes first-class through production behavior, not through the presence of `@Module`.

## A Bad Module Can Erase Framework Advantages { #bad-module-erase }

If Kora reaches readiness quickly but your custom client spends fifteen seconds performing sequential cluster discovery, warming caches, and opening hundreds of connections, the application is still
slow.

The custom integration is now part of the framework path from the application's perspective.

Fast framework internals do not compensate for slow extension code.

Module authors need the same performance discipline as framework authors.

## Lifecycle and Telemetry Separate "Works" From "Operates" { #lifecycle-telemetry-separate }

A factory method makes a library work.

Typed configuration makes it deployable.

Lifecycle makes it safe to own.

Telemetry makes it operable.

Testing makes it maintainable.

Compile-time DI makes it structurally verifiable.

Together these properties make the integration first-class.

That is why the useful question is not:

> How do I put this client into Kora DI?

The better question is:

> What does this technology need in order to behave like a native production component of a Kora application?

## The Core Pattern { #core-pattern }

For most integrations, the architecture converges on:

```text
native library
     ↓
typed configuration
     ↓
factory / transport
     ↓
lifecycle-managed client
     ↓
telemetry adapter
     ↓
Kora application graph
     ↓
business code
```

Optional layers include:

```text
probe
resilience
multi-instance factory
test kit
generated adapters
```

The exact implementation changes with the technology.

The principles remain stable.

## Conclusion { #conclusion }

Kora's **Built to be extended** philosophy is not valuable because the framework allows one more annotation or one more factory method. It is valuable because the framework's own application model is
open enough for external integrations to become genuine peers of built-in modules.

A serious Kora module does more than instantiate a client.

It gives the technology a place in the compile-time dependency graph.

It maps deployment configuration into strong types.

It makes resource ownership and shutdown explicit.

It attaches logging, metrics, and tracing through the same operational stack used by the rest of the application.

It provides safe defaults and deliberate extension points.

It supports testing without forcing every service test to run real infrastructure.

It can expose health without confusing dependency failure with process liveness.

It can support several configured instances without global registries.

And it can do all of this while keeping the underlying technology recognizable.

A good Elasticsearch module should still feel like Elasticsearch.

A good NATS module should still feel like NATS.

A good MinIO module should still feel like S3-compatible object storage.

A good internal library module should still expose the concepts that library was built around.

Kora supplies the production glue:

```text
configuration
+
DI
+
lifecycle
+
telemetry
+
testing
```

not a replacement universe.

This is how a focused framework can remain small without becoming closed.

Kora does not need to integrate every possible library itself. It needs to expose the same architectural primitives strongly enough that teams can build their own integrations without workarounds.

The ideal final result is almost boring.

The application enables a module.

Configuration appears under a predictable section.

The graph constructs the client.

The client starts in the correct dependency order.

Operations emit the same metrics and traces as the rest of the service.

Shutdown releases resources in the correct order.

Tests replace the client when they need isolation and start real infrastructure when they need realism.

Business code simply injects the technology and uses it.

That is what a first-class module should feel like.

And that is the practical meaning of a framework being **built to be extended**.
