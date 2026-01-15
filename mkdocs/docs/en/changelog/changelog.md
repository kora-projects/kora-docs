---
search:
  exclude: true
hide:
  - navigation
---

## 1.2.7

Added:

- Allow `CompletableFuture<RecordMetadata>` and `Deferred<RecordMetadata>` results in `@KafkaPublisher` in Kotlin

### 1.2.6

Fixed:

- Fixed database repository query parameter name parsing
- Fixed Cache `GET_*` metrics for `Caffeine`
- Fixed correct usage of `KSType.toClassName` in KSP
- Improved `Swagger UI` bundle.js settings

### 1.2.5

Added:

- Added logging `@Mdc` annotation aspect
- Added OpenAPI generator HTTP client [multiple auth specification](https://swagger.io/docs/specification/v3_0/authentication/#using-multiple-authentication-types) support via [config option](../documentation/openapi-codegen.md#client)
- Added `ProgrammaticDriverConfigLoaderBuilder` to `CassandraConfigurer` config option
- Added Camunda BPMN Rest `CORS` support 
- Added Camunda BPMN engine virtual thread executor and `preconfigure` option
- Restored `OkHttpClient` option `retryOnConnectionFailure#true` by default 
- Improved annotation processing errors message output

Fixed:

- Fixed `suspend` function support in generated promised proxies in Kotlin
- Fixed `AbstractRedisCache#invalidateAll` proper behavior to evict only cache specific keys (slower performance)
- Fixed database query parameter substitution when prefix matched other parameter
- Fixed `@KafkaListener` generated factory handler missing `@Tag` annotation
- Fixed `Caffeine` cache tracing by disabling it cause useless 
- Fixed `AwsS3ObjectMeta` NPE when missing size response parameter
- Fixed config `Collection<T>` empty string value incorrectly treated not as empty collection 
- Fixed `@Mapping` should work with abstract class implementations
- Fixed OpenAPI generator `filterWithModel` for requests section
- Fixed OpenAPI HTTP Client auth parameter as argument extract name 
- Fixed Camunda REST request body reading for POST requests
- Fixed HTTP Client `@CodeMapper` signature matching for complex generic types
- Fixed `@Component` and `@Root` for HttpClient and Repository testing generated graph

### 1.2.4

Added:

- Added improved errors & hint output for `UnresolvedDependencyException` and other annotation processors
- Added OpenAPI generator `forceIncludeNonRequired` option
- Added config parsing of Duration based on Java `Duration` format

Fixed:

- Fixed Resilient `CircuitBreaker` incorrect release when ignored exceptions in `HALF_OPEN` state 
- Fixed HTTP Client encode space char in `@Path` param as `%20` symbol
- Fixed incorrect `@ScheduleWithCron` job `Quartz` execution at startup 
- Fixed OpenAPI generator `forceIncludeOptional` missing `@JsonInclude(ALWAYS)` for Kotlin 

### 1.2.3

Added: 

- Added `ConsumerRecordWrapper#unwrap` for accessing original record 

Fixed:

- Fixed `OkHttpClient` connection retry behavior disabled by default
- Fixed database name propagation in tracing
- Fixed `NPE` on `HttpServerResponseException.of` with empty message on throwable 
- Fixed Resilient module `Retry` incorrect behavior on `disabled` and `attemptMax=0` in Kotlin
- Fixed `HttpClientResponseMapper` resolution on `ResponseCodeMapper` annotation in Kotlin
- Fixed OpenAPI generator loop cause `StackOverFlow` when check models for server `Validation`
- Fixed OpenAPI generator config mapping `type+format` type support
- Fixed OpenAPI generator operation filter with filter models for `responses` and `requests` sections
- Fixed OpenAPI generator non-json mapper tag resolution in Java
- Reinforced Resilient `CircuitBreaker` & `Retry` & `Fallback` exception logging on `TRACE` level

### 1.2.2

Added:

- Added HTTP-server controller `@Tag` propagation support 
- Added `Redis` option `forceCluster` for single URI connection

Fixed:

- Fixed `Opentelemetry` gRPC exporter dependency for `OkHttp` client 
- Fixed OpenAPI generator `Form` generation for `byte[]` args 
- Fixed OpenAPI generator improve `discriminator` parent model 
- Fixed OpenAPI generator `Validation` for inner models 
- Fixed OpenAPI generator `Kotlin` nullable items
- Fixed `Undertow` HttpServer check for `Virtual Threads` enabled 
- Improved some exception messages, logging

### 1.2.1

Fixed:

- Fixed `JDBC` connection context shared when multiple DataSources registered
- Fixed `Tracing` missing `OK` status in most of the modules
- Fixed `OpentelemetryContext` NPE occurred for not Span context

## 1.2.0

Migration required:

- Update OpenAPI generator plugin to `7.14.0`
- If relying on `@JsonInclude(ALWAYS)` for `isNullable` and `NonRequired` fields in OpenAPI generator manually added in generator config `forceIncludeOptional = "true"` option

Added:

- Added virtual thread based executor for `Undertow` HTTP-server processing
- Added `@DisallowConcurrentExecution` and `@PersistJobDataAfterExecution` annotations for Quartz jobs
- Added `post-commit` and `post-rollback` callbacks for `JdbcConnectionFactory#inTx` method
- Added HTTP client `@Cookie` parameters support
- Added HTTP client processor should implement methods from super interfaces
- Added Kora `JUnit` mockito session & report unused stubbing
- Added OpenAPI generator behavior with remove `@JsonInclude(Always)` as default behavior since 1.1.13
- Added OpenAPI generator `forceIncludeOptional` option to add `@JsonInclude(Always)` for `isNullable` and `NonRequired` fields in the OpenAPI generator
- Added masking `Cookie/Set-Cookie` HTTP headers by default
- Added Redis Lettuce factory `LettuceConfigurator` for client
- Added Redis Lettuce metrics
- Added more data providing for `@KafkaProducer` telemetry
- Added HTTP client metric tags provider
- Added gRPC client metric tags provider
- Added Gradle incremental processing support
- Added Kotlin KSP incremental processing support
- Improved `@KafkaListener` & `@KafkaProducer` metrics
- Improved resilient `@CircuitBreaker` logging and metrics
- Updated all dependencies for their [up-to-date versions]((https://github.com/kora-projects/kora/pull/392/files#diff-697f70cdd88ba88fe77eebda60c7e143f6ad1286bca75017421e93ad84fb87df))

Fixed:

- Fixed `Cassandra` profiles should not require contact points in config
- Fixed `@Embedded` non-primitive field accessors
- Fixed OpenAPI generator failing `param:` annotation prefix for Kotlin
- Fixed OpenAPI generator `Form` generation for non-String fields
- Fixed method parameters preserve AOP annotations for generated classes
- Fixed JUnit tests concurrent multiple graph initialization `System Properties` conflict
- Fixed `@Validation` correct treating for `@NotNull` and `@Nullable` method signatures

### 1.1.31

Added:

- Added `@KafkaListener` skip record logic via [KafkaSkipRecordException](../documentation/kafka.md#exception-skipping)
- Added `Redis` cache `SSL` configuration options
- Added `OpentelemetryContext` methods for `getSpan` and `getTraceId`
- Added ability to post process `Cassandra` config with `CassandraConfigurer`
- Added OpenAPI HTTP-server generator `delegateMethodBodyMode` option
- Added OpenAPI generator `Javadoc` and improved code style for generated classes

Fixed:

- Fixed HTTP-client `JdkProxySelector` should not cache proxy IP address 
- Fixed `KafkaAssignConsumer` stopping topic polling on graph refresh
- Fixed support Json reader/writer generation for sealed hierarchies with `Nothing` as type variable in `Kotlin`
- Fixed OpenAPI generator `implicitHeaders` option extraction 
- Fixed `JUnit` testing complex `Wrapped<T>` support 

### 1.1.30

Added:

- Allow to set Map of system properties for `KoraConfigModification` in JUnit config
- Added improved gRPC Server & Client configuration
- Added gRPC Client result status for metrics

### 1.1.29

Added:

- Added `OpenAPI` generator `ImplicitHeaders` & `ImplicitHeadersRegex` options support
- Added enabled config option for all `resilient` components
- Added `Kafka` consumer metrics `KafkaClientMetrics` micrometer support
- Added Micrometer `gRPC` server tags provider

Fixed:

- Fixed `JDK HTTP-client` lazy evaluation for `content-type`
- Fixed `HTTP-client` body logging

### 1.1.28

Fixed:

- Fixed `Kotlin KSP` error message for unknown type during dependecy graph build

### 1.1.27

Added:

- Added `AWS S3 Client` contract `Head` interface support
- Added config support for `Map` with custom key declaration (`Enum`/`UUID`/etc)
- Added `JsonReader` unchecked read methods
- Added improved annotation processor graph resolution error output

Fixed:

- Fixed response stuck and loss `onComplete` signal for `JDK HTTP-client`
- Fixed `AWS S3 Client` method `objectMeta` implementation
- Fixed JDK HTTP-client `content-type` extraction
- Fixed JDBC repositories and Kotlin 2.0 compiler errors in syntax compatibility
- Fixed OpenAPI generator `@Valid` annotation generation for `Enum`
- Fixed Kafka Consumer Telemetry deprecated method library compatibility
- Fixed OpenAPI `FILTER` for complex hierarchy recursion scan
- Fixed OpenAPI generator some models missing property `override` for Kotlin
- Fixed `gRPC` server telemetry interceptor error handling

### 1.1.26

Added:

- Updated dependencies minor version

Fixed:

- Fixed resilient `CircuitBreaker` half open counter error introduced in [1.1.24](#1124)
- Fixed field order when mapping via `JsonObjectCodec`
- Fixed AOP support for default methods in AP processed interfaces (like `@HttpClient` interface)
- Fixed JSON processing for library `Enum` when invoked via extension
- Fixed JSON type propagation for sealed types when invoked via extension
- Fixed OpenAPI generator `Cookie` authorization for Kotlin HTTP-server
- Fixed OpenAPI generator model validation for Kotlin
- Fixed JUnit testing `Wrapped<T>` test component proper support and mocking

### 1.1.25

Added:

- Added more common default mappers for `Json` and `StringConverter`
- Added support for Kotlin properties in `@ConfigSource` interfaces 

Fixed:

- Fixed OpenAPI `Enum` field naming and translite field naming 
- Fixed OpenAPI field cyrillic translite naming
- Fixed OpenAPI option `filterWithModels` to work with complex hierarchy and recursion 
- Fixed support private functions and properties in `PromisedProxy` implementations 
- Fixed `JsonReader` generation for sealed interfaces

### 1.1.24

Added:

- Added OpenAPI `Enum` Cyrillic translite constants support 
- Added OpenAPI `Enum` constant SnakeCase additional naming 
- Added OpenAPI `filterWithModels` custom option for filtering models when `openapiNormalizer` [FILTER option](https://openapi-generator.tech/docs/customization/#available-filters) is specified
- Added OpenAPI `prefixPath` custom option for HTTP-server controllers generator
- Added OpenAPI Kotlin HTTP-server authorization optimizations
- Added more [tracing exporter](../documentation/tracing.md) configurable options 

Fixed:

- Fixed KSP generation of `JsonWriter` for Java classes 
- Fixed `CircuitBreaker` half-open proper error count 
- Fixed Redis Cache potential NPE for `putAsync` operation
- Fixed `KafkaConsumer` metric `report lag` proper value export
- Fixed OpenAPI discriminator field `JsonField` naming for child models
- Fixed OpenAPI discriminator for free Form error handling 
- Fixed OpenAPI management block in HTTP-server specified endpoints paths even if management endpoints are disabled

### 1.1.23

Added:

* Added pretty string write method to `JsonWriter`
* Added `maxConnectionAge` and `maxConnectionAgeGrace` config options to gRPC-server

Fixed:

* Fixed boolean value extraction in `DefaultServiceConfigConfigValueExtractor`
* Fixed `UndertowPrivateApiHandler` should write private api results on IO thread
* Fixed `JsonExtension` should not attempt to generate `JsonWriter`/`JsonReader` for non sealed interfaces
* Fixed Graph dependency adding hint message and match strategy
* Fixed HTTP `Interceptor` release should be called after dependent nodes released
* Fixed `CircuitBreakerConfig` error message
* Fixed `JDK` scheduling pool potential outOfThreads
* Fixed `JUnit` extension full graph only with mocked parts
* Fixed `JsonWriter`/`JsonReader` Kotlin generation field accessor check
* Fixed and reinforced JUnit parallel and `@Nested` tests proper execution

### 1.1.22

Fixed:

* Fixed `OpenAPI` generated model constructor, where discriminator with single value was a required construct argument in Java
* Fixed `OpenAPI` generated model field name with `enum array` type

### 1.1.21

Added:

* Added `Cache<K, Optional<T>>` cache signature support in Java
* Added database `Record/Data` class as self query parameter
* Added OpenAPI `additionalProperties` support for `nullable` and/or `non required` parameters
* Added `BigDecimal` parsing using `JsonReader<BigDecimal>` from dependency container and not static function
* Added optimized `HTTP Server` query and header retrieval
* Added optimized `Cassandra` mapper `List<T>` for empty values
* Added `CircuitBreaker` config on-start check reinforced
* Added ability to log slow initialized nodes in dependency container

Fixed:

* Fixed `HTTP Client` should check response codes in only `@Tag` annotated methods
* Fixed `S3Client` Kotlin generated constructor not been primary
* Fixed Database Kotlin `@Column` annotation name substitution in mapper
* Fixed OpenAPI parameter `Enum` variable naming
* Fixed `Wrapped<T>` generic support for Java dependency container
* Fixed `List<T>` and `Set<T>` correct query parameter parsing in `HTTP Server`
* Fixed `SoapClient` processing xml element `Wrapped<T>` for requests/responses
* Fixed `JdbcMappers` error handling when not provide mappers for `T?` entities in Kotlin
* Fixed `JUnit5` mock component sometimes not found in dependency container
* Fixed `HttpServerRequest#route` marked `nullable` when not matched with any controller
* Fixed generated `HTTP Client` should not use `this` to access static mappers
* Fixed generated `ConfigValueExtractor` contained unused fields

### 1.1.20

Added:

* Added `@EntityCassandra` annotation with processors
* Added more flexible way of gRPC component configuration
* Added warning in `@Json` extensions for non annotated types 
* Replaced deprecated OpenTelemetry `SemanticAttributes` usages 

Fixed:

* Fixed Cassandra `UDT` mappers for lists
* Fixed partially `T is not a sub type of the class/interface that contains` in Kotlin
* Fixed discriminators models in OpenAPI generator

### 1.1.19

Added:

* Added enriched HTTP-server parameter parsing API with `Set<T>` support
* Added more `Cassandra` default result mappers 
* Improved `ClientClassGenerator` error handling for Path/Query mismatch
* Added `ViolationExceptionHttpServerResponseMapper` context injection before execution
  
Fixed:

* Fixed Cache `Redis` multiple key get 
* Fixed `Cassandra` row mappers for primitive return types 
* Fixed `OpenAPI` generation discriminator enum naming 
* Fixed `Quartz` default properties values 
* Fixed Allow empty interfaces as targets of `@ConfigValueExtractor` targets 
* Fixed handling of `null` values for sealed interfaces in `JSON` parsing 
* Fixed `OpenAPI` parameter `typeMapping` for Java primitive types
* Fixed parameterized generic class to be discovered as final components 

### 1.1.18

Added:

* Added [Camunda Zeebe Worker](../documentation/camunda8-worker.md) **experimental** module
* Added Kotlin `suspend` database transaction extension methods
* Improved `OpenAPI` generated discriminator model contracts

Fixed:

* Fixed `Kafka` unused parameter in HandlerWrapper 
* Fixed `Kafka` transactional publisher sendOffsetsToTransaction method 
* Fixed `Quartz` scheduler default configuration for correct clustered behavior 
* Fixed `Wrapped` components  in `JUnit` for Mock/Spy/Replace operations
* Fixed minor dependency security updates 

### 1.1.17

Added:

* Added KafkaConsumer batch processing metric and other telemetry improvements
* Added Config boolean as native type

Fixed:

* Fixed gRPC client telemetry handling on request cancellation
* Fixed template generic components interface matching for graph processor
* Fixed HttpServer private release sleep removed
* Fixed ResourceConfigOrigin#description for improved config error

### 1.1.16

Added:

* Added new [HTTP-server config](../documentation/http-server.md#configuration) options

Fixed:

* Fixed JDBC `byte[]` type mapping
* Fixed `JdkScheduler` job await proper release 
* Fixed Quartz job registration potential NPE
* Fixed scheduling jobs refresh trigger whole scheduler refresh behavior 
* Improved Quartz job shutdown
* Updated dependencies minor version 

### 1.1.15

Fixed:

* Fixed HTTP Client tracing missing
* Fixed `QuartzModule` config method potential collision with jdk scheduling
* Fixed Jdk Scheduling job awaits graceful shutdown

### 1.1.14

Added:

* Added force shutdownNow when graceful shutdown fails for gRPC-server, KafkaListener, Scheduler

Fixed:

* Fixed Quartz config extractor missing

### 1.1.13

Added:

* Added [JsonNullable](../documentation/json.md#jsonnullable-wrapper) special type
* Added config parameter [KafkaConsumer](../documentation/kafka.md#configuration) that allows empty records after `poll()`
* Added OpenAPI [enableJsonNullable](../documentation/openapi-codegen.md#server) option support (**Changed default behavior**, now *nullable* and *non required* fields [Include.Always](../documentation/json.md#_9) default if `JsonNullable` is not enabled)
* Added Camunda Rest [OpenAPI](../documentation/camunda7-rest.md#configuration)
* Improved Camunda Rest Telemetry 
* Improved Graceful shutdown for HTTP Server, KafkaListener, gRPC Server, Schedulers

Fixed:

* Fixed OpenAPI Codegen `additionalContractAnnotations` without validation enabled
* Fixed KafkaConsumer RebalanceListener for topics config
* Fixed `HttpServerResponse` exceptions processing in blocking threads
* Fixed allow defaults methods in Kotlin KafkaProducer

### 1.1.12

Added:

* Added OpenAPI option to generate HTTP client authorization as [method argument](../documentation/openapi-codegen.md#client)
* Added `@KoraAppTest#modules` [parameter](../documentation/junit5.md#test)
* Added `@KoraApp` generate `@SubModule` if enabled to extend real graph in [other environments](../documentation/junit5.md#test-graph)
* Added `SOAP` telemetry tracing and logging

Fixed:

* Fixed HTTP Client introduced in `1.1.11` new telemetry config backward compatibility with older versions (actual for libraries with versions before `1.1.11`)
* Fixed Metrics missing tags for multiple modules
* Fixed Jdbc Kotlin `ResultSet.next()` check for optional params
* Fixed HTTP client operation logging enabled 
* Fixed tracing missing `ERROR` status code for multiple modules

### 1.1.11

Added:

* Added [HTTP Client/Server logging masking](../documentation/http-server.md#configuration)
* Added HTTP Client & Server metrics enriched
* Added OpenAPI additional contract annotations for HTTP client/server
* Added annotation processor for [JDBC result set mappers](../documentation/database-jdbc.md#entity)
* Added [Resilient Retry & Timeout](../documentation/resilient.md#retry) virtual thread support

Fixed:

* Fixed gRPC server/client metrics memory leak
* Fixed IntersectType Java generics component factory support
* Fixed QuartzJob exception and incorrect logging
* Fixed Enum config value string mapping
* Fixed JsonReader Set & Map types as Linked implementations
* Fixed Retry support zero attempts
* Fixed HttpClientRequestMapper String as plain text content-type

### 1.1.10

Added:

* Added Expose TypeSpec.Builder for aspects for end user
* Added support for `additionalModelTypeAnnotations` option in OpenAPI generator
* Added `@Deprecated` annotation for OpenAPI generated HTTP Client methods
* Added Date-Time `typeMapping` default values support in OpenAPI generator
* Added Cassandra improved metrics configs

Fixed:

* Fixed Undertow ByteBuffer leak
* Fixed OpenAPI CodegenModel required when non validated
* Fixed trace logging on HTTP client breaking `async-http-client`
* Fixed Cassandra nullable resultSet mapping in Kotlin
* Fixed nullability checks should check type use annotations in Java
* Fixed HTTP Server primitive type response in Java
* Fixed `LocalDate` type in JDBC repository in Kotlin

### 1.1.9

Added:

* Added [Camunda BPMN](../documentation/camunda7-bpmn.md) and [Camunda REST](../documentation/camunda7-rest.md) **experimental** module
* Added [multiple OpenAPI files](../documentation/openapi-management.md) support
* Added [ConsumerAwareRebalanceListener](../documentation/kafka.md#rebalance-events) support
* Added OpenAPI Client generated extra methods without optional parameters
* Added Kafka Listener [custom tag](../documentation/kafka.md#custom-tag) support
* Added more [Logging AOP](../documentation/logging-aspect.md#signatures) signatures support
* Enabled `Cassandra` driver metrics by default (see configuration)

Fixed:

* Fixed `GraphInterceptor` for components with AOP
* Fixed Cassandra metrics config
* Fixed Logging AOP exception handling
* Fixed JSON potential name collision 
* Fixed KSP missing external writer constructor
* Fixed Kafka Listener empty records telemetry recorded
* Fixed handling of event commit when processing record one by one in `@KafkaListener`
* Fixed error message if `@Batch` requests are not used correctly
* Fixed absence of `@Nullable` annotation when forming `@KoraSubmodule`
* Fixed HTTP Server `Content-Type` missing on exception with body
* Fixed OpenAPI non-string default values in schemas

### 1.1.8

Added:

* Added [S3 Client](../documentation/s3-client.md) **experimental** module 
* Added [Liquibase module](../documentation/database-migration.md#liquibase)
* Added configuration option to specify migration files to the [Flyway](../documentation/database-migration.md#flyway) module
* Added [Size type](../documentation/config.md#size)
* Added [gRPC server message size](../documentation/grpc-server.md#configuration) config option added
* Added more Javadoc

Fixed:

* Fixed HttpClientTelemetry log body that wasn't read till the end
* Fixed gRPC interceptor execution order
* Fixed Kafka Consumer record commit only after batch processed
* Fixed KafkaAssignConsumerContainer offset duration
* Fixed Openapi codegen mixing referenced oneOf fields in root type

### 1.1.7

Added:

* Added `@Tag` propagation for `@Repository`
* Added configuration of [OkHttp](../documentation/http-client.md#okhttp)

Fixed:

* Fixed JsonReader/JsonWriter for fields with symbol `$`
* Fixed requirement for `ReactorContextKt` in `CoroutineContextInjectInterceptor`
* Fixed NPE in GrpcServer metrics
* Fixed method argument `@Pattern` validation in Kotlin
* Fixed `Content-Type` propagation for [Response Entity](../documentation/http-server.md#response-entity)
* Fixed Kotlin alias collision for classes with same name
* Removed Prometheus JMX dependency

### 1.1.6

Fixed:

- Fixed Netty & gRPC [dependency bugs](https://github.com/grpc/grpc-java/issues/11284)

### 1.1.5

Added:

- Improved HTTP Client header required error message in OpenAPI Generator

Fixed:

- Fixed `CompletionFuture` signature for Cassandra repositories
- Fixed column nullability detection with any `@Nullable` annotation for Database Entities

### 1.1.4

Added:

- Added Database Record constructor parameters `@Nullable` support
- Added [Netty Transport](../documentation/netty.md) selection
- Added ability to [disable/enable](../documentation/config.md#config-watcher) Config Watcher
- Optimized generated OpenAPI HTTP server authorization

Fixed:

- Fixed ByteBufferPool factory available for private UndertowModule
- Fixed require `@NonNull` for CompletionStage signatures in Databases
- Fixed potential error handling for private API
- Fixed OpenAPI authorization interceptors potential name collision
- Fixed Async HTTP Client Netty transport dependencies
- Fixed Database tracing handling
- Fixed templated components should work with @Component
- Fixed Gradle compile warnings

### 1.1.3

Fixed:

- Fixed by replacing undertow byte buffer with our own to prevent thread leak
- Fixed OpenAPI `URI` type
- Fixed JDBC async signature (user `Executor` required)
- Fixed OpenAPI Server Cookie auth
- Updated dependencies with fix versions
- Undertow Xnio Executor tagged

### 1.1.2

Fixed:

- Fixed `@Retry` for CompletableFuture signature
- Fixed Cache AOP error handling 
- Fixed OpenAPI generator [primaryAuth](../documentation/openapi-codegen.md#client) property
- Fixed HttpClient telemetry passing Content-Length to underlying client 
- Fixed `Wrapped` support in JUnit5 testing

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
- Dependencies updated and synchronized across [all modules]((https://github.com/kora-projects/kora/pull/4/files#diff-d979b641bd0ea7c9da3fe113f9657636df1002652c75042cfe3b5203da064215))
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

First fully stabilized version with stable API.
