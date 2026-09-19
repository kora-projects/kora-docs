---
search:
  exclude: true
hide:
  - navigation
---

## 2.0.0.RC1

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
