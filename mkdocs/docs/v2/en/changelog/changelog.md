---
seo_title: "Kora 2.0 Changelog: Release Notes"
seo_description: "Release notes for Kora 2.0: new features, breaking changes, fixes and migration notes for the Java and Kotlin backend framework."
keywords: ["Kora Framework", "Kora changelog", "Kora 2.0", "release notes", "migration guide"]
search:
  exclude: true
hide:
  - navigation
---

## 2.0.0.RC2

Refactorings:

- Quartz scheduling `scheduling.quartz.waitForJobComplete` replaced by `shutdownWait` (`30s` by default), Kora jobs are registered in the `kora` group (jobs of the `DEFAULT` group are moved automatically) and a persisted trigger is rescheduled only when its schedule, end time or CRON time zone changes
- Resilient `RateLimiter` default algorithm changed from fixed window to token bucket (`RateLimiterConfig.type` is `TOKEN_BUCKET`), set `type = FIXED_WINDOW` to keep the previous behavior
- HTTP server Undertow no longer applies `Configurer<HttpHandler>`, only `Configurer<Undertow.Builder>` and `Configurer<XnioWorker.Builder>` remain
- HTTP client and server `telemetry.logging.mask` config key removed, register a `MaskingStrategy` tagged `@Tag(HttpServerTelemetry.class)` / `@Tag(HttpClientTelemetry.class)` to change the replacement of masked values
- HTTP client Apache and JDK connect failures are thrown as `HttpClientConnectionException` instead of `HttpClientUnknownException` / `HttpClientTimeoutException`
- Telemetry metric names, tag keys, span names and span event names aligned with OpenTelemetry semantic conventions `1.44.0` across RPC, messaging, HTTP client, Redis, cache, Resilient, Camunda and database modules, existing dashboards and alerts must be updated
- Telemetry RPC `rpc.system` renamed to `rpc.system.name`, metrics `rpc.client.duration` / `rpc.server.duration` to `rpc.client.call.duration` / `rpc.server.call.duration`, gRPC `rpc.grpc.status_code` replaced with `rpc.response.status_code` holding the status name
- Telemetry Redis Lettuce metric `lettuce.command.completion.duration` renamed to `db.client.operation.duration`, cache counter `cache.ratio` to `cache.requests` with `cache.result` tag, HTTP client `http.route` replaced with `url.template`
- Telemetry tags and attributes are namespaced: `resilient.*`, `cache.operation` / `cache.origin`, `camunda.delegate`, `soap.fault.*`, Zeebe `job.*`, database span events `db.connection` / `db.statement` / `db.result`
- Logback `ConsoleTextRecordEncoder` moved to the `io.koraframework.logging.logback.text` package, update the encoder class in `logback.xml`
- OpenAPI generator client security interceptors add the `Basic ` / `Bearer ` prefix themselves, `HttpClientTokenProvider` must return the bare token

Refactorings (minor, usually no changes required):

- JDK scheduling jobs run on virtual threads, concurrency is limited by `scheduling.jdk.maxConcurrentExecutions` (unlimited by default) and running executions are interrupted after `scheduling.jdk.shutdownWait` on shutdown
- Scheduling JDK, Quartz and DB CRON expressions are validated at compile time, jobs declared with `config` got the `enabled` key and CRON jobs are evaluated in the time zone of an optional `ZoneId` component tagged with `SchedulingModule`
- HTTP server no longer sends the `Server: Kora` response header by default, set `httpServer.headerServerNameEnabled = true` to restore it
- Logback without `logback.xml` is configured by `KoraLogbackConfigurator`: the encoder is selected by `kora.logging.encoder` / `KORA_LOGGING_ENCODER` (`text`, `pretty`, `json`, `none`) and `java.util.logging` is bridged by default (`kora.logging.config.jul-bridge`)
- OpenAPI generator server security answers `403` instead of `401` when an authenticated principal lacks required scopes
- Redis `lettuce-core` updated to major version `7.8.0`

Added:

- Added OpenAPI generator `typeMappings` for `date-time` are applied, so generated types change for projects that declare such mapping
- Added OpenAPI status-code range responses (`4XX`, `5XX`) for Java and Kotlin clients and servers
- Added OpenAPI client successful response mode with typed error exceptions
- Added Resilient `Retry` and `CircuitBreaker` non-registered exceptions
- Added distributed Resilient `RateLimiter` and `RetryBudget`
- Added pluggable telemetry attributes and metric tags providers with enable switch
- Added HTTP telemetry masking for headers, queries and structured bodies
- Added Kafka telemetry masking with `TRACE` consumer payload logging
- Added gRPC telemetry masking with tagged strategies
- Added Scheduling DB module
- Added PostgreSQL JDBC database module
- Added `keepAlive` parameter for `KoraApplication#run`
- Added `Either#fold` to map either side into a single result
- Added KSP symbol processors console logging like in Java annotation processors, level is set by the `koraLogLevel` option
- Added Camunda REST optional API authentication with pluggable `CamundaRestAuthenticationProvider`

Improved:

- Optimized Undertow request processing with fewer allocations and NIO response body writes
- Improved JSON reader parse-error messages
- Improved JDK scheduling to use virtual threads for jobs
- Improved dependency graph errors in AP and KSP with readable signatures, exact source of the problem and concrete fixes
- Improved server startup log message to report the listening port
- Updated dependencies versions

Fixed:

- Fixed OpenAPI generator multipart form mapping and parsing
- Fixed OpenAPI generator free-form map schemas should resolve to `Object`
- Fixed OpenAPI generator `date-time` should honour `typeMappings`
- Fixed OpenAPI generator spec text with `%` or `$` breaking code generation
- Fixed OpenAPI generator array or map of inline enum should be generated as a collection of the enum instead of a single enum value
- Fixed OpenAPI generator client `Authorization` header should carry its auth scheme
- Fixed OpenAPI generator client and server security should support `openIdConnect` schemes
- Fixed OpenAPI generator server validation annotations should match the contract
- Fixed HTTP client response body decoding failures should be wrapped
- Fixed HTTP client transport integration for JDK and Apache clients
- Fixed HTTP client connect failures should map to `HttpClientConnectionException` for Apache and JDK clients
- Fixed HTTP client connection error log should be written to and controlled by the response logger
- Fixed HTTP client JDK `httpClient.readTimeout` should be applied to requests
- Fixed HTTP server Undertow should serve requests with the handler replaced by a refresh
- Fixed HTTP server request duration metric should carry `http.response.status_code`
- Fixed HTTP cookie parser should keep trailing `=` in cookie values
- Fixed Kafka KSP listener with `Headers` and deserialization exception argument
- Fixed telemetry Kafka and JMS spans should be named `<operation> <destination>`, JMS consumer metric `messaging.receive.duration` renamed to `messaging.process.duration`
- Fixed database mapping of empty embedded
- Fixed database `snake_case` column names in Kotlin symbol processor
- Fixed database JDBC result set mapper of an array type crashing the Java annotation processor
- Fixed database JDBC post-commit and post-rollback actions should run once and for their own transaction
- Removed unreachable coroutine code paths from the Kotlin repository generators
- Fixed validation constraint factory argument order in Kotlin symbol processor
- Fixed KSP graph interceptor tagged with `Tag.Any` should intercept components of any tag
- Fixed KSP graph interceptor should apply only to components of exactly its intercepted type as in the Java processor
- Fixed KSP generated Kotlin sources producing compiler warnings
- Fixed MapStruct `@Tag` on a `@Mapper` should be honored when injecting the mapper in Java and Kotlin
- Fixed `GraphCondition.and` should return `Matched` when all conditions matched
- Fixed `@KoraApp` condition components should be ordered after their last dependency
- Fixed `@KoraApp` circular dependency going through `All<T>` should be reported as a cycle
- Fixed `@KoraApp` component factory returning type check reinforced
- Fixed `@KoraApp` generated submodule should declare AOP proxy method declarations
- Fixed `@Nullable` dependency on a `@Conditional` component should receive `null` when the condition fails
- Fixed `@Conditional` nodes should work in a subgraph and a copy of the graph draw
- Fixed condition-failed `@Conditional` nodes breaking `@KoraAppTest`
- Fixed application init and release time should be logged in milliseconds
- Fixed graph refresh should not recreate independent nodes
- Fixed graph node read from a factory may not be initialized yet
- Fixed graph refresh that creates nothing logging a bogus `IllegalArgumentException`
- Fixed graph refresh should survive an `equals` that throws
- Fixed config watcher refreshing the graph on every check after the first config change
- Fixed JDK scheduling executor should not depend on jobs
- Fixed scheduling job should keep its class and method in logs when its telemetry is disabled
- Fixed scheduling job of a `@Conditional` component should exist under the same condition
- Fixed `Caffeine` cache metrics registered twice
- Fixed S3 client issues on strict S3-compatible servers
- Fixed S3 client `@S3.Head` and `S3Client.headObject` should pass `HeadObjectArgs` to the request, `@S3.Head` accepts `HeadObjectResult?` in KSP
- Fixed Logback `KoraMdcConverter` should render nothing instead of failing outside an MDC scope
- Fixed Logback `KoraAsyncAppender` discarding threshold should be based on log level
- Fixed logging `@Mask` should generate masking rules in Java projects
- Fixed JSON deprecated `JsonParser.getText()` replaced with `getString()`
- Fixed GraalVM native-image `reflect-config.json` and `resource-config.json` across modules
- Fixed deprecated usages, Javadoc and annotation processors isolation usage

### 2.0.0.RC1

Migration required:

- Telemetry has been standardized across all modules (HTTP client & server, Database, gRPC, Kafka, Cache, SOAP, JMS, Scheduling, Camunda, Zeebe, Resilient) — config keys, metrics and tracing are now aligned to unified conventions
- SOAP client migrated to `CXF 4.2.2` with Jakarta-only support
- Netty module refactored with `io_uring` (`URING`) transport support
- OpenAPI generator `interceptors` option is superseded by the `extensions` option
- OpenAPI `RapiDoc` replaced with `Scalar` (with response caching)
- Resilient contracts reinforced and simplified

Added:

- Added class-module support via `@FactoryModule` and `Tag.Factory`
- Added factory modules for server, client, database, Redis, S3, Flyway and Liquibase components
- Added `@DefaultComponent` support for `@Component` classes
- Added Resilient module `RateLimiter` metrics and advanced `CircuitBreaker` implementations
- Added `@Retry` support for `KoraRetryBudget`, `jitter` and `backoff`
- Added HTTP Client `Apache` module
- Added HTTP client typed `Either<T, E>` response mapping
- Added `KoraTracer` wrapper with parent, root and linked span modes
- Added JDK `CRON` scheduling support
- Added structured log JSON masking with generated metadata
- Added more validation annotations and default validators, plus config validation for mappers and sources
- Added JSON discriminator defaults with missing-field fallback compatibility
- Added database macros: `@Column` type use, method argument macros, aliases and one-to-many mapping
- Added OpenAPI generator `extensions` option as successor for `interceptors`
- Added OpenAPI security fallback modes with anonymous access
- Added OpenAPI single `clientConfig` path as default behavior and shared client interface for same model with different status codes
- Added async cache modes with shared executor and cache enablement config with disabled no-op behavior
- Added `Caffeine` cache telemetry with Redis-aligned contracts and `RedisCache#putExpireAfterWrite` contracts
- Added S3 AWS client module
- Added `Swagger UI` upgrade with `OAuth2` redirect page support
- Added `ConfigWatcher` tracking of `HOCON` include files
- Added gRPC `ManagedChannel` connection establishment during initialization

Improved:

- Improved HTTP server route matching with a performant hybrid implementation
- Optimized HTTP header and server parameter handling
- Improved DI diagnostics with readable AP and KSP error guidance
- Enriched runtime and JUnit exception messages
- Improved telemetry no-op metrics with a shared zero-allocation registry
- Reinforced dependency management and `kora-bom`
- Reinforced GraalVM native-image configuration across modules

Fixed:

- Fixed AOP generated proxies should be registered with supertype in graph
- Fixed AOP proxy generation for no-op method aspects and parent-interface AOP for HTTP client & repository
- Fixed OpenAPI generator reserved words per target language and Kotlin reliefs
- Fixed OpenAPI generator NPE for `Valid` nullable annotation and restored enum `fromValue` factory
- Fixed OpenAPI generator multipart `byte`/file handling and `nameMapping` option
- Fixed OpenAPI security tags with scheme-based names for Java and Kotlin clients & servers
- Fixed config value extractors for interfaces with default methods and config watcher dependency
- Fixed numerous GraalVM native-image reflection registrations (Undertow, JDBC, Kafka, gRPC, Caffeine, Micrometer)
- Fixed a number of backported issues from the `1.2.x` line (Kafka, Cassandra, HTTP, cache, logging, JUnit)

### 2.0.0.alpha6

Added:

- Added `RateLimiter` feature for the resilient module

Fixed:

- Fixed conditional components should work with `All<T>`
- Fixed `HttpClientParameterWriter` package placement

### 2.0.0.alpha5

Migration required:

- Root package and Maven group id changed to `io.koraframework`

Added:

- Enriched `Flyway` config
- Added support for Kotlin `data` class default values in configs
- Added HTTP client and server response entity mappers for JSON bodies
- Added conditional graph elements

Improved:

- Standardized, refactored and simplified HTTP API contracts
- Sped up graph resolution with a simple class name to component cache
- Simplified Kora app graph processor structures
- Updated `kafka-clients` to `4.2.0`

Fixed:

- Fixed HTTP spans should follow the OpenTelemetry status specification
- Fixed SQL parameter regex to handle `=` without spaces for repositories
- Added `MAX_ENTITY_SIZE` Undertow option in HTTP server config
- Fixed `ConfigValueExtractor` handling of `null` values
- Fixed enum naming in the OpenAPI generator
- Fixed validation `module-info` exports
- Fixed HTTP client `Map<String, List<String>>` generation
- Removed exact-match component wiring from the graph

### 2.0.0.alpha4

Fixed:

- Fixed private API config tags
- Removed automatic declaration of dependencies with final classes

### 2.0.0.alpha3

Added:

- Restored support of anonymous enums in OpenAPI contracts

Fixed:

- Fixed HTTP client telemetry should honor the config `logging.enabled` flag
- Polished private API implementation

### 2.0.0.alpha2

Added:

- Added `@Module` on generated S3 client modules
- Allowed `Deferred` results in KSP-generated Kafka publishers

Fixed:

- Fixed `@KoraApp` processor to run without kora libs in classpath
- Fixed database telemetry should not require a tracer
- Fixed OpenAPI generator to generate the responses class with `public` modifier

### 2.0.0.alpha1

Migration required:

- `@Tag` annotation now takes a single class instead of a class array
- Jakarta annotations replaced with `JSpecify`
- Replaced `grpc-netty` with `grpc-okhttp`
- Updated Kotlin to `2.3.0` and JUnit to `6.0.1`

Added:

- Added generic `Configurer<T>` class to use in different integrations

Improved:

- Improved support of OpenAPI nullable fields
- `@Json` annotated classes now use `@Mapping` for custom readers/writers
- Codegen now uses `@Nullable` on types, not on elements
- Moved json-module components to mappers modules

Fixed:

- Fixed correct usage of `KSType.toClassName`
- Fixed database repository method parameter detection in query
- Removed `VirtualThreadExecutorHolder` as no longer needed
