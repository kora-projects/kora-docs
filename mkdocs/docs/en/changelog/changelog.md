---
search:
    exclude: true
hide:
    - navigation
---

### 1.1.1

Fixed:

- Fixed Void results for HttpClient methods with code mappers
- Fixed `@Cacheable` AOP for Reactive contract
- Fixed HTTP Content-Length processing in implementation
- Fixed OpenApi Kotlin Nullable enum
- Fixed OpenAPI Kotlin empty class equals & hashCode 
- Fixed GraalVM ReactorContextHook#init() missing in runtime

## 1.1.0

Added:

- Added OpenTelemetry metrics [1.23](../documentation/metrics.md#standard) new standard
- Added GraalVM and GraalVM virtual threads support for most modules
- Dependencies updated and synchronized across all modules
- Component build message improved
- Lifecycle logging standardized

Fixed:

- Fixed unnecessary application graph node refreshes
- Fixed Missing `@Generated` annotations
- Fixed writing exception to closed Undertow connection should not ignore telemetry
- Fixed Resilient minor issues
- Fixed `HttpBody.contentLength` should be long
- Fixed AOP annotation processor crash without kora dependencies in compile unit
- Fixed `@ResponseCodeMapper` behaviour when only code defined
- Fixed Cassandra driver micrometer metrics

### 1.0.9

Added:

- Added [gRPC Server Reflection](https://github.com/grpc/grpc/blob/master/doc/server-reflection.md) support

Fixed:

- Fixed missing `@Generated` annotations (was affecting JaCoCo reports)

### 1.0.8

Added:

- Added database metrics error tag
- Added Cassandra driver metrics
- Added [Retry](../documentation/resilient.md#retry) contract for `CompletableStage` and AOP optimized for `CompletableStage`

Fixed:

- Fixed OpenAPI Generation codegen support for Java 21
- Fixed missing `Span.recordException` calls in telemetry
- Fixed HTTP Client telemetry with single packet responses as `InputStream`

### 1.0.7

Added:

- Support for `@Nested` tests
- Support for Cache AOP `CompletionStage<Optional<T>>` signature
- Support for Graph `AutoClosable` release stage
- Java Annotation Processor Logging improved

Fixed:

- Fixed OpenAPI Non Json `Content-Type` mapper generating
- Fixed OpenAPI `java-async-server` & `java-reactive-server` mode option
- Fixed Undertow `exchange already complete` error
- Fixed Cache Redis AOP for `Mono` contracts

### 1.0.6

Fixed:

- Fixed support for HTTP server/client metrics in deprecated OpenTelemetry standards

### 1.0.5

Added:

- Support improved for all [HTTP](../documentation/http-client.md) client configurations
- Partition label support in `messaging.kafka.consumer.lag` metric for KafkaProducer
- Support for HTTP server/client metrics and telemetry in new OpenTelemetry standards
- Support for interceptors for HTTP client/server in [OpenAPI generator](../documentation/openapi-codegen.md) using the `interceptors` option
- Support for `short` type for databases

Fixed:

- Fixed support for byte contracts when creating via [OpenAPI generator](../documentation/openapi-codegen.md)

### 1.0.4

Added:

- Support for [OkHttp](../documentation/http-client.md#okhttp) HTTP client implementation

Fixed:

- Fixed handling multiple reference values within a single value in a configuration file
- Fixed NPE in Kafka producer
- Fixed OpenTelemetry trace exporter over gRPC

### 1.0.3

Added:

- Support for Kafka Metrics to be compatible with OpenTelemetry semantic conventions
- Support for OpenTelemetry Trace exporter via [HTTP](../documentation/tracing.md)
- Support for Kafka Publisher return `CompletionStage` signature
- Support for optional parameters in canonical constructor for OpenAPI generated Kotlin models
- Support for Date & Time values in configuration
- Support for `Type Alias` annotations in Kotlin

Fixed:

- Fixed `CircuitBreaker` acquire bug in HalfOpen state
- Fixed dispatcher override on gRPC Server call removed
- Fixed preserving AOP annotations in for all framework generated classes

### 1.0.2

Added:

- Support for `HttpServerRequest` as a parameter in OpenAPI generated contracts
- Support for optional headers in response in OpenAPI generated contracts

Fixed:

- Fixed handling of repeated Cache annotations in Kotlin
- Fixed handling of Type Alias annotations in Kotlin
- Fixed missing `@Root` annotations in `@KoraSubmodule`

### 1.0.1

Added:

- HttpClient `@Query` and `@Header` parameter `Map` and `HttpHeaders` type support
- Scheduling `Quartz.properties` support by default
- Scheduling JDK config threads value support by default

Fixed:

- HttpServer `405` exception handling by interceptors fixed
- HttpServer missing HTTP parameters invokes interceptors fixed
- HttpServer interceptor exception handling hierarchy fixed
- Missing `@Generated` annotations fixed
- `@KoraSubmodule` missing `@Nullable` annotation fixed
- Logging Aspect primitive out parameter support fixed

# 1.0.0

First fully stable version.
