---
description: "Explains Kora Cassandra repositories, Cassandra driver configuration, execution profiles, entity and UDT mapping, manual CQL queries, and repository signatures. Use when working with @Repository, @Query, @EntityCassandra, @Table, @Id, @Column, @UDT, CassandraDatabaseModule, CassandraExecutor."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Cassandra repositories, Cassandra driver configuration, execution profiles, entity and UDT mapping, manual CQL queries via CassandraQuery, and repository signatures; key triggers include @Repository, @Query, @EntityCassandra, @Table, @Id, @Column, @UDT, @CassandraProfile, CassandraDatabaseModule, CassandraRepository, CassandraExecutor, CassandraSession."
---

Module provides a repository implementation for the [Cassandra](https://cassandra.apache.org/_/cassandra-basics.html) database
on top of the [Cassandra Java driver](https://docs.datastax.com/en/developer/java-driver/4.17/) (`org.apache.cassandra:java-driver-core` version `4.19.3`, brought in by the module transitively).
`Cassandra` is a distributed column-oriented database where queries are written in `CQL`, and the data model is usually designed around specific read scenarios.
In Kora, the Cassandra module provides declarative repositories on top of `CqlSession`: the application writes `CQL` queries in `@Query`, and Kora generates query preparation, parameter binding, and result mapping code at compile time.

Common rules for entities, `@Repository`, `@Query`, macros, batch queries, and the `@Table`, `@Column`, `@Id`, `@Embedded` annotations are described in the [common database section](database-common.md).
This document covers the Cassandra-specific parts: driver connection, `CqlSession` configuration, execution profiles, `UDT`, mappers, and supported method signatures.

For a step-by-step walkthrough before the reference details, see [Cassandra Database](../guides/database-cassandra.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:database-cassandra"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CassandraDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:database-cassandra")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : CassandraDatabaseModule
    ```

`CassandraDatabaseModule` extends `CassandraMapperModule`, so the standard row, column, and parameter mappers come with it.
The module registers a `CassandraSession` component that owns the driver `CqlSession`: it is opened when the application graph starts and closed on shutdown.
`CassandraSession` is a `Wrapped<CqlSession>`, so the raw `CqlSession` can also be injected into any component directly.

## Configuration { #configuration }

Configuration is read from the `cassandra` section and described by the `CassandraConfig` interface.
At minimum, `basic.contactPoints` must be specified. Other parameters are optional or passed to the driver only when explicitly configured.

Simple configuration example:

===! ":material-code-json: `Hocon`"

    ```javascript
    cassandra {
        basic {
            contactPoints = "127.0.0.1:9042, 127.0.0.2:9042" //(1)!
            dc = "datacenter1"  //(2)!
            sessionKeyspace = "test-db" //(3)!
            request {
                timeout = "5s" //(4)!
            }
        }
        auth {
            login = "username" //(5)!
            password = "password" //(6)!
        }
    }
    ```

    1. `Cassandra` node addresses for connecting to the database (`required`, no default)
    2. `Cassandra` datacenter name (not specified by default, optional)
    3. `keyspace` name for the connection (not specified by default, optional)
    4. Query execution timeout for the connection (not specified by default, optional)
    5. Username for the connection (not specified by default, optional)
    6. Password for the connection (not specified by default, optional)

=== ":simple-yaml: `YAML`"

    ```yaml
    cassandra:
      basic:
        contactPoints: "127.0.0.1:9042, 127.0.0.2:9042" #(1)!
        dc: "datacenter1" #(2)!
        sessionKeyspace: "test-db" #(3)!
        request:
          timeout: "5s" #(4)!
      auth:
        login: "username" #(5)!
        password: "password" #(6)!
    ```

    1. `Cassandra` node addresses for connecting to the database (`required`, no default)
    2. `Cassandra` datacenter name (not specified by default, optional)
    3. `keyspace` name for the connection (not specified by default, optional)
    4. Query execution timeout for the connection (not specified by default, optional)
    5. Username for the connection (not specified by default, optional)
    6. Password for the connection (not specified by default, optional)

??? abstract "Full configuration example"

    Full configuration with example values. Parameter descriptions are shared by the `HOCON` and `YAML` examples.

    ===! ":material-code-json: `Hocon`"

        ```javascript
        cassandra {
            auth {
                login = "username" //(1)!
                password = "password" //(2)!
            }

            basic {
                contactPoints = [ "127.0.0.1:9042", "127.0.0.2:9042" ] //(3)!
                sessionName = "some-session-name" //(4)!
                dc = "datacenter1" //(5)!
                sessionKeyspace = "test-db" //(6)!

                loadBalancingPolicy.slowReplicaAvoidance = true //(7)!
                cloud.secureConnectBundle = "/location/of/secure/connect/bundle" //(8)!
                request {
                    timeout = "5s" //(9)!
                    consistency = "LOCAL_ONE" //(10)!
                    pageSize = 5000 //(11)!
                    serialConsistency = "LOCAL_SERIAL" //(12)!
                    defaultIdempotence = false //(13)!
                }
            }

            advanced {
                sessionLeak.threshold = 4 //(14)!
                connection {
                    connectTimeout = "10s" //(15)!
                    initQueryTimeout = "10s" //(16)!
                    setKeyspaceTimeout = "10s" //(17)!
                    maxRequestsPerConnection = 1024 //(18)!
                    maxOrphanRequests = 256 //(19)!
                    warnOnInitError = true //(20)!
                    pool {
                        localSize = 10 //(21)!
                        remoteSize = 10 //(22)!
                    }
                }
                reconnectOnInit = false //(23)!
                reconnectionPolicy {
                    baseDelay = "1s" //(24)!
                    maxDelay = "60s" //(25)!
                }
                loadBalancingPolicy.dcFailover {
                    maxNodesPerRemoveDc = 1 //(26)!
                    allowForLocalConsistencyLevels = false //(27)!
                }
                sslEngineFactory {
                    cipherSuites = [ "TLS_RSA_WITH_AES_128_CBC_SHA", "TLS_RSA_WITH_AES_256_CBC_SHA" ] //(28)!
                    hostnameValidation = true //(29)!
                    keystorePath = "/path/to/client.keystore" //(30)!
                    keystorePassword = "password" //(31)!
                    truststorePath = "/path/to/client.truststore" //(32)!
                    truststorePassword = "password" //(33)!
                }
                timestampGenerator {
                    forceJavaClock = false //(34)!
                    driftWarning.threshold = "1s" //(35)!
                    driftWarning.interval = "10s" //(36)!
                }
                protocol {
                    version = "V4" //(37)!
                    compression = "lz4" //(38)!
                    maxFrameLength = 268435456 //(39)!
                }
                request {
                    warnIfSetKeyspace = true //(40)!
                    trace {
                        attempts = 5 //(41)!
                        interval = "1ms" //(42)!
                        consistency = "ONE" //(43)!
                    }
                    logWarnings = true //(44)!
                }
                metrics {
                    idGenerator {
                        name = "TaggingMetricIdGenerator" //(45)!
                        prefix = "my-app" //(46)!
                    }
                    node {
                        enabled = [ "bytes-sent", "bytes-received", "open-connections" ] //(47)!
                        cqlMessages {
                            lowestLatency = "1ms" //(48)!
                            highestLatency = "90s" //(49)!
                            significantDigits = 1 //(50)!
                            refreshInterval = "10s" //(51)!
                            slo = [ 1, 10, 50, 100, 200, 500, 1000 ] //(52)!
                        }
                    }
                    session {
                        enabled = [ "connected-nodes", "cql-requests", "cql-client-timeouts" ] //(53)!
                        cqlRequests {
                            lowestLatency = "1ms" //(54)!
                            highestLatency = "90s" //(55)!
                            significantDigits = 1 //(56)!
                            refreshInterval = "10s" //(57)!
                            slo = [ 1, 10, 50, 100, 200, 500, 1000 ] //(58)!
                        }
                        throttlingDelay {
                            lowestLatency = "1ms" //(59)!
                            highestLatency = "90s" //(60)!
                            significantDigits = 1 //(61)!
                            refreshInterval = "10s" //(62)!
                            slo = [ 1, 10, 50, 100, 200, 500, 1000 ] //(63)!
                        }
                    }
                    publishPercentileHistogram = false //(64)!
                }
                socket {
                    tcpNoDelay = true //(65)!
                    keepAlive = false //(66)!
                    reuseAddress = true //(67)!
                    lingerInterval = 0 //(68)!
                    receiveBufferSize = 65535 //(69)!
                    sendBufferSize = 65535 //(70)!
                }
                heartbeat {
                    interval = "30s" //(71)!
                    timeout = "2m" //(72)!
                }
                metadata {
                    schema {
                        enabled = true //(73)!
                        requestTimeout = "20s" //(74)!
                        requestPageSize = 20 //(75)!
                        refreshedKeyspaces = [ "ks1", "ks2" ] //(76)!
                        debouncer.window = "1s" //(77)!
                        debouncer.maxEvents = 20 //(78)!
                    }
                    topologyEventDebouncer.window = "1s" //(79)!
                    topologyEventDebouncer.maxEvents = 20 //(80)!
                    tokenMapEnabled = true //(81)!
                }
                controlConnection {
                    timeout = "10s" //(82)!
                    schemaAgreement {
                        interval = "200ms" //(83)!
                        timeout = "10s" //(84)!
                        warnOnFailure = true //(85)!
                    }
                }
                preparedStatements {
                    prepareOnAllNodes = true //(86)!
                    reprepareOnUp {
                        enabled = true //(87)!
                        checkSystemTable = false //(88)!
                        maxStatements = 0 //(89)!
                        maxParallelism = 100 //(90)!
                        timeout = "20s" //(91)!
                    }
                    preparedCache.weakValues = false //(92)!
                }
                netty {
                    ioGroup.size = 0 //(93)!
                    ioGroup.shutdown {
                        quietPeriod = 2 //(94)!
                        timeout = 15 //(95)!
                        unit = "SECONDS" //(96)!
                    }
                    adminGroup.size = 2 //(97)!
                    adminGroup.shutdown {
                        quietPeriod = 2 //(98)!
                        timeout = 15 //(99)!
                        unit = "SECONDS" //(100)!
                    }
                    timer.tickDuration = "100ms" //(101)!
                    timer.ticksPerWheel = 2048 //(102)!
                    daemon = false //(103)!
                }
                coalescer.rescheduleInterval = "10ms" //(104)!
                resolveContactPoints = false //(105)!
                throttler {
                    throttlerClass = "ConcurrencyLimitingRequestThrottler" //(106)!
                    maxConcurrentRequests = 1024 //(107)!
                    maxRequestsPerSecond = 10000 //(108)!
                    maxQueueSize = 10000 //(109)!
                    drainInterval = "1ms" //(110)!
                }
            }

            profiles {
                someProfile {
                    basic.request.timeout = "10s" //(111)!
                    basic.request.consistency = "LOCAL_QUORUM" //(112)!
                    advanced.request.trace.attempts = 3 //(113)!
                    advanced.request.trace.consistency = "ONE" //(114)!
                }
            }

            telemetry {
                logging.enabled = false //(115)!
                metrics {
                    enabled = true //(116)!
                    driverMetrics = true //(117)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000 ] //(118)!
                    tags = { "key1" = "value1", "key2" = "value2" } //(119)!
                }
                tracing {
                    enabled = true //(120)!
                    attributes = { "key1" = "value1", "key2" = "value2" } //(121)!
                }
            }
        }
        ```

    === ":simple-yaml: `YAML`"

        ```yaml
        cassandra:
          auth:
            login: "username" #(1)!
            password: "password" #(2)!
          basic:
            contactPoints: [ "127.0.0.1:9042", "127.0.0.2:9042" ] #(3)!
            sessionName: "some-session-name" #(4)!
            dc: "datacenter1" #(5)!
            sessionKeyspace: "test-db" #(6)!
            loadBalancingPolicy:
              slowReplicaAvoidance: true #(7)!
            cloud:
              secureConnectBundle: "/location/of/secure/connect/bundle" #(8)!
            request:
              timeout: "5s" #(9)!
              consistency: "LOCAL_ONE" #(10)!
              pageSize: 5000 #(11)!
              serialConsistency: "LOCAL_SERIAL" #(12)!
              defaultIdempotence: false #(13)!
          advanced:
            sessionLeak:
              threshold: 4 #(14)!
            connection:
              connectTimeout: "10s" #(15)!
              initQueryTimeout: "10s" #(16)!
              setKeyspaceTimeout: "10s" #(17)!
              maxRequestsPerConnection: 1024 #(18)!
              maxOrphanRequests: 256 #(19)!
              warnOnInitError: true #(20)!
              pool:
                localSize: 10 #(21)!
                remoteSize: 10 #(22)!
            reconnectOnInit: false #(23)!
            reconnectionPolicy:
              baseDelay: "1s" #(24)!
              maxDelay: "60s" #(25)!
            loadBalancingPolicy:
              dcFailover:
                maxNodesPerRemoveDc: 1 #(26)!
                allowForLocalConsistencyLevels: false #(27)!
            sslEngineFactory:
              cipherSuites: [ "TLS_RSA_WITH_AES_128_CBC_SHA", "TLS_RSA_WITH_AES_256_CBC_SHA" ] #(28)!
              hostnameValidation: true #(29)!
              keystorePath: "/path/to/client.keystore" #(30)!
              keystorePassword: "password" #(31)!
              truststorePath: "/path/to/client.truststore" #(32)!
              truststorePassword: "password" #(33)!
            timestampGenerator:
              forceJavaClock: false #(34)!
              driftWarning:
                threshold: "1s" #(35)!
                interval: "10s" #(36)!
            protocol:
              version: "V4" #(37)!
              compression: "lz4" #(38)!
              maxFrameLength: 268435456 #(39)!
            request:
              warnIfSetKeyspace: true #(40)!
              trace:
                attempts: 5 #(41)!
                interval: "1ms" #(42)!
                consistency: "ONE" #(43)!
              logWarnings: true #(44)!
            metrics:
              idGenerator:
                name: "TaggingMetricIdGenerator" #(45)!
                prefix: "my-app" #(46)!
              node:
                enabled: [ "bytes-sent", "bytes-received", "open-connections" ] #(47)!
                cqlMessages:
                  lowestLatency: "1ms" #(48)!
                  highestLatency: "90s" #(49)!
                  significantDigits: 1 #(50)!
                  refreshInterval: "10s" #(51)!
                  slo: [ 1, 10, 50, 100, 200, 500, 1000 ] #(52)!
              session:
                enabled: [ "connected-nodes", "cql-requests", "cql-client-timeouts" ] #(53)!
                cqlRequests:
                  lowestLatency: "1ms" #(54)!
                  highestLatency: "90s" #(55)!
                  significantDigits: 1 #(56)!
                  refreshInterval: "10s" #(57)!
                  slo: [ 1, 10, 50, 100, 200, 500, 1000 ] #(58)!
                throttlingDelay:
                  lowestLatency: "1ms" #(59)!
                  highestLatency: "90s" #(60)!
                  significantDigits: 1 #(61)!
                  refreshInterval: "10s" #(62)!
                  slo: [ 1, 10, 50, 100, 200, 500, 1000 ] #(63)!
              publishPercentileHistogram: false #(64)!
            socket:
              tcpNoDelay: true #(65)!
              keepAlive: false #(66)!
              reuseAddress: true #(67)!
              lingerInterval: 0 #(68)!
              receiveBufferSize: 65535 #(69)!
              sendBufferSize: 65535 #(70)!
            heartbeat:
              interval: "30s" #(71)!
              timeout: "2m" #(72)!
            metadata:
              schema:
                enabled: true #(73)!
                requestTimeout: "20s" #(74)!
                requestPageSize: 20 #(75)!
                refreshedKeyspaces: [ "ks1", "ks2" ] #(76)!
                debouncer:
                  window: "1s" #(77)!
                  maxEvents: 20 #(78)!
              topologyEventDebouncer:
                window: "1s" #(79)!
                maxEvents: 20 #(80)!
              tokenMapEnabled: true #(81)!
            controlConnection:
              timeout: "10s" #(82)!
              schemaAgreement:
                interval: "200ms" #(83)!
                timeout: "10s" #(84)!
                warnOnFailure: true #(85)!
            preparedStatements:
              prepareOnAllNodes: true #(86)!
              reprepareOnUp:
                enabled: true #(87)!
                checkSystemTable: false #(88)!
                maxStatements: 0 #(89)!
                maxParallelism: 100 #(90)!
                timeout: "20s" #(91)!
              preparedCache:
                weakValues: false #(92)!
            netty:
              ioGroup:
                size: 0 #(93)!
                shutdown:
                  quietPeriod: 2 #(94)!
                  timeout: 15 #(95)!
                  unit: "SECONDS" #(96)!
              adminGroup:
                size: 2 #(97)!
                shutdown:
                  quietPeriod: 2 #(98)!
                  timeout: 15 #(99)!
                  unit: "SECONDS" #(100)!
              timer:
                tickDuration: "100ms" #(101)!
                ticksPerWheel: 2048 #(102)!
              daemon: false #(103)!
            coalescer:
              rescheduleInterval: "10ms" #(104)!
            resolveContactPoints: false #(105)!
            throttler:
              throttlerClass: "ConcurrencyLimitingRequestThrottler" #(106)!
              maxConcurrentRequests: 1024 #(107)!
              maxRequestsPerSecond: 10000 #(108)!
              maxQueueSize: 10000 #(109)!
              drainInterval: "1ms" #(110)!
          profiles:
            someProfile:
              basic:
                request:
                  timeout: "10s" #(111)!
                  consistency: "LOCAL_QUORUM" #(112)!
              advanced:
                request:
                  trace:
                    attempts: 3 #(113)!
                    consistency: "ONE" #(114)!
          telemetry:
            logging:
              enabled: false #(115)!
            metrics:
              enabled: true #(116)!
              driverMetrics: true #(117)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000 ] #(118)!
              tags: { key1: "value1", key2: "value2" } #(119)!
            tracing:
              enabled: true #(120)!
              attributes: { key1: "value1", key2: "value2" } #(121)!
        ```

    1. Username for authentication in `Cassandra` (not specified by default, optional).
    2. Password for authentication in `Cassandra` (not specified by default, optional).
    3. `Cassandra` node addresses in `host:port` format (`required`, no default).
    4. Driver session name used in logs, metrics, and diagnostics (not specified by default, optional).
    5. Local datacenter for the load-balancing policy (not specified by default, optional).
    6. `keyspace` that will be set for the session after connection (not specified by default, optional).
    7. Enables slow replica avoidance in the default load-balancing policy (not specified by default, optional).
    8. Path or `URL` to the `Secure Connect Bundle` for connecting to `DataStax Astra` / cloud Cassandra (not specified by default, optional).
    9. Regular request timeout (not specified by default, optional).
    10. Regular request consistency level, for example `ONE`, `LOCAL_ONE`, `LOCAL_QUORUM`, `QUORUM`, `ALL` (not specified by default, optional).
    11. Result page size, meaning the maximum number of rows requested in one network round trip (not specified by default, optional).
    12. Serial consistency level for lightweight transactions `LWT`: `SERIAL` or `LOCAL_SERIAL` (not specified by default, optional).
    13. Default request idempotence value; affects whether retries and speculative execution can be applied safely (not specified by default, optional).
    14. Driver session leak warning threshold (not specified by default, optional).
    15. Timeout for opening a network connection to a node (not specified by default, optional).
    16. Timeout for requests that the driver executes while initializing a connection (not specified by default, optional).
    17. Timeout for setting the `keyspace` on a connection (not specified by default, optional).
    18. Maximum number of simultaneous requests per connection (not specified by default, optional).
    19. Maximum number of requests whose response is no longer awaited but may still complete inside the driver (not specified by default, optional).
    20. Logs a warning when connection initialization fails for an individual node (not specified by default, optional).
    21. Connection pool size for local datacenter nodes (not specified by default, optional).
    22. Connection pool size for remote nodes (not specified by default, optional).
    23. Allows initialization retry when all `contactPoints` do not answer during startup (not specified by default, optional).
    24. Initial delay of the reconnection policy (not specified by default, optional).
    25. Maximum delay of the reconnection policy (not specified by default, optional).
    26. Maximum number of remote datacenter nodes that can be used for failover (not specified by default, optional).
    27. Allows failover to a remote datacenter for local consistency levels (not specified by default, optional).
    28. Allowed cipher suites for `SSL/TLS` (not specified by default, optional).
    29. Checks that the node hostname matches the `SSL/TLS` certificate (not specified by default, optional).
    30. Path to the client keystore (not specified by default, optional).
    31. Client keystore password (not specified by default, optional).
    32. Path to the truststore (not specified by default, optional).
    33. Truststore password (not specified by default, optional).
    34. Forces Java system clock usage for query timestamp generation (not specified by default, optional).
    35. Warning threshold for timestamp drift into the future (not specified by default, optional).
    36. Minimum interval between timestamp drift warnings (not specified by default, optional).
    37. Cassandra binary protocol version, for example `V4` (not specified by default, optional).
    38. Protocol compression algorithm, for example `lz4` or `snappy` (not specified by default, optional).
    39. Maximum protocol frame size in bytes (not specified by default, optional).
    40. Logs a warning when a query explicitly changes the `keyspace` (not specified by default, optional).
    41. Number of attempts to fetch query tracing information from Cassandra (not specified by default, optional).
    42. Interval between attempts to fetch query tracing information (not specified by default, optional).
    43. Consistency level for queries to tracing tables (not specified by default, optional).
    44. Logs warnings returned by Cassandra with a query response (not specified by default, optional).
    45. Driver metric identifier generator name (default: `TaggingMetricIdGenerator`).
    46. Driver metric name prefix (not specified by default, optional).
    47. Enabled node-level driver metrics (default: `open-connections`, `in-flight`, `bytes-received`, `bytes-sent`, `write-timeouts`, `read-timeouts`, `aborted-requests`).
    48. Lowest expected latency for the `node.cqlMessages` metric histogram (default: `1ms`).
    49. Highest expected latency for the `node.cqlMessages` metric histogram (default: `90s`).
    50. Number of significant digits for the `node.cqlMessages` metric histogram (not specified by default, optional).
    51. Snapshot refresh interval for the `node.cqlMessages` metric histogram (not specified by default, optional).
    52. `SLO` boundaries for the `node.cqlMessages` metric (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    53. Enabled session-level driver metrics (default: `connected-nodes`, `cql-requests`, `cql-client-timeouts`, `cql-prepared-cache-size`, `throttling.delay`, `throttling.queue-size`).
    54. Lowest expected latency for the `session.cqlRequests` metric histogram (default: `1ms`).
    55. Highest expected latency for the `session.cqlRequests` metric histogram (default: `90s`).
    56. Number of significant digits for the `session.cqlRequests` metric histogram (not specified by default, optional).
    57. Snapshot refresh interval for the `session.cqlRequests` metric histogram (not specified by default, optional).
    58. `SLO` boundaries for the `session.cqlRequests` metric (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    59. Lowest expected latency for the `session.throttlingDelay` metric histogram (default: `1ms`).
    60. Highest expected latency for the `session.throttlingDelay` metric histogram (default: `90s`).
    61. Number of significant digits for the `session.throttlingDelay` metric histogram (not specified by default, optional).
    62. Snapshot refresh interval for the `session.throttlingDelay` metric histogram (not specified by default, optional).
    63. `SLO` boundaries for the `session.throttlingDelay` metric (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    64. Publishes percentile histograms for driver metrics (default: `false`).
    65. Enables `TCP_NODELAY`, which disables Nagle's algorithm (not specified by default, optional).
    66. Enables `SO_KEEPALIVE` for TCP sockets (not specified by default, optional).
    67. Enables `SO_REUSEADDR` for TCP sockets (not specified by default, optional).
    68. `SO_LINGER` value for TCP sockets (not specified by default, optional).
    69. TCP socket receive buffer size in bytes (not specified by default, optional).
    70. TCP socket send buffer size in bytes (not specified by default, optional).
    71. Interval for sending `heartbeat` on an idle connection (not specified by default, optional).
    72. Timeout for waiting for a `heartbeat` response (not specified by default, optional).
    73. Enables schema metadata loading and refresh (not specified by default, optional).
    74. Timeout for schema metadata queries (not specified by default, optional).
    75. Page size for schema metadata queries (not specified by default, optional).
    76. List of `keyspace` names whose schema metadata is refreshed by the driver (not specified by default, optional).
    77. Window for coalescing schema refresh events before processing (not specified by default, optional).
    78. Maximum number of schema refresh events that can be accumulated in the window (not specified by default, optional).
    79. Window for coalescing cluster topology change events (not specified by default, optional).
    80. Maximum number of topology change events that can be accumulated in the window (not specified by default, optional).
    81. Enables the token map for routing requests by data owners (not specified by default, optional).
    82. Service `control connection` timeout (not specified by default, optional).
    83. Interval for checking `schema agreement` between nodes (not specified by default, optional).
    84. Maximum time to wait for `schema agreement` (not specified by default, optional).
    85. Logs a warning if `schema agreement` is not reached in time (not specified by default, optional).
    86. Prepares a statement on all nodes after it has been prepared successfully on one node (not specified by default, optional).
    87. Re-prepares statements on a node that became available again (not specified by default, optional).
    88. Checks the `system.prepared_statements` system table before re-preparing a statement (not specified by default, optional).
    89. Maximum number of statements to re-prepare; `0` means no driver-side limit (not specified by default, optional).
    90. Maximum number of parallel re-prepare requests (not specified by default, optional).
    91. Timeout for re-preparing statements on one node (not specified by default, optional).
    92. Stores prepared statement cache values through weak references (not specified by default, optional).
    93. Number of `Netty` threads for network I/O; `0` lets the driver choose automatically (not specified by default, optional).
    94. Quiet period for graceful `ioGroup` shutdown (not specified by default, optional).
    95. Maximum wait time for `ioGroup` shutdown (not specified by default, optional).
    96. Unit for `ioGroup` shutdown parameters (not specified by default, optional).
    97. Number of `Netty` threads for driver administrative tasks (not specified by default, optional).
    98. Quiet period for graceful `adminGroup` shutdown (not specified by default, optional).
    99. Maximum wait time for `adminGroup` shutdown (not specified by default, optional).
    100. Unit for `adminGroup` shutdown parameters (not specified by default, optional).
    101. Duration of one `Netty` timer tick for delayed driver tasks (not specified by default, optional).
    102. Number of ticks in the `Netty` timer wheel (not specified by default, optional).
    103. Makes `Netty` threads daemon threads (not specified by default, optional).
    104. Rescheduling interval for message coalescing before sending (not specified by default, optional).
    105. Allows the driver to resolve `contactPoints` through DNS during startup (not specified by default, optional).
    106. Driver request throttler class (not specified by default, optional).
    107. Maximum number of concurrent requests for the throttler (not specified by default, optional).
    108. Maximum number of requests per second for the throttler (not specified by default, optional).
    109. Maximum throttler request queue size (not specified by default, optional).
    110. Interval at which the throttler releases requests from the queue (not specified by default, optional).
    111. `basic.request.timeout` override for the `someProfile` profile (not specified by default, optional).
    112. `basic.request.consistency` override for the `someProfile` profile (not specified by default, optional).
    113. `advanced.request.trace.attempts` override for the `someProfile` profile (not specified by default, optional).
    114. `advanced.request.trace.consistency` override for the `someProfile` profile (not specified by default, optional).
    115. Enables Kora query logging (default: `false`).
    116. Enables Kora query metrics (default: `false`).
    117. Registers the driver's own metrics in the application `MeterRegistry`; when disabled, the whole `advanced.metrics` block has no effect (default: `true`).
    118. Kora metrics `SLO` boundaries (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    119. Additional Kora metric tags (default: `{}`).
    120. Enables Kora query tracing (default: `true`).
    121. Additional Kora tracing attributes (default: `{}`).

### Code configuration { #code-configuration }

Not every driver option is exposed through the `cassandra` section. What is missing can be set in code with `Configurer` components:

- `Configurer<CqlSessionBuilder>` — changes the session builder itself, for example the client identifier, a custom codec registry, or a node state listener;
- `Configurer<ProgrammaticDriverConfigLoaderBuilder>` — writes raw driver options into the configuration loader that Kora assembles from the `cassandra` section.

Both are optional, and both are applied last, after everything read from configuration, so a value set here wins:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyCqlSessionConfigurer implements Configurer<CqlSessionBuilder> {

        @Override
        public CqlSessionBuilder configure(CqlSessionBuilder builder) {
            return builder.withClientId(UUID.randomUUID());
        }
    }

    @Component
    public final class MyDriverOptionsConfigurer implements Configurer<ProgrammaticDriverConfigLoaderBuilder> {

        @Override
        public ProgrammaticDriverConfigLoaderBuilder configure(ProgrammaticDriverConfigLoaderBuilder builder) {
            return builder.withString(DefaultDriverOption.RETRY_POLICY_CLASS, "DefaultRetryPolicy");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyCqlSessionConfigurer : Configurer<CqlSessionBuilder> {

        override fun configure(builder: CqlSessionBuilder): CqlSessionBuilder {
            return builder.withClientId(UUID.randomUUID())
        }
    }

    @Component
    class MyDriverOptionsConfigurer : Configurer<ProgrammaticDriverConfigLoaderBuilder> {

        override fun configure(builder: ProgrammaticDriverConfigLoaderBuilder): ProgrammaticDriverConfigLoaderBuilder {
            return builder.withString(DefaultDriverOption.RETRY_POLICY_CLASS, "DefaultRetryPolicy")
        }
    }
    ```

`Configurer` is `io.koraframework.common.Configurer`, a single-method contract `T configure(T t)`.

### Multiple clusters { #multiple-clusters }

`CassandraDatabaseModule` builds its session from the `cassandra` section by declaring a `CassandraDatabaseFactoryModule("cassandra")`.
A second cluster is added by declaring one more factory module with its own config path and its own tag,
and repositories select it with `@Repository(executorTag = …)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends CassandraDatabaseModule {

        final class Analytics { }

        @Tag(Analytics.class)
        @FactoryModule
        default CassandraDatabaseFactoryModule analyticsCassandra() {
            return new CassandraDatabaseFactoryModule("cassandraAnalytics"); //(1)!
        }
    }

    @Repository(executorTag = Application.Analytics.class)
    public interface AnalyticsRepository extends CassandraRepository { }
    ```

    1.  Section of the configuration file that describes this cluster; it has the same shape as the `cassandra` section.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : CassandraDatabaseModule {

        class Analytics

        @Tag(Analytics::class)
        @FactoryModule
        fun analyticsCassandra(): CassandraDatabaseFactoryModule {
            return CassandraDatabaseFactoryModule("cassandraAnalytics") //(1)!
        }
    }

    @Repository(executorTag = Application.Analytics::class)
    interface AnalyticsRepository : CassandraRepository
    ```

    1.  Section of the configuration file that describes this cluster; it has the same shape as the `cassandra` section.

The tag on the factory module propagates to everything it builds, so the `Configurer` components of that cluster must carry the same tag.
Repositories that use the primary connection need no tag.
The general rules are described in the [common database section](database-common.md#multiple-databases).

## Usage { #usage }

To create a repository, declare an interface with `@Repository` and extend `CassandraRepository`.
Such a repository gets access to `CqlSession` through generated code and uses `@Query` to execute `CQL` queries.
Query parameters are bound by name: `:id`, `:entity.field`, `:filter.value`.

Views are described with the [common database annotations](database-common.md) and marked with `@EntityCassandra`
so that `Kora` generates the view mapper at compile time (see [View](#view)):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends CassandraRepository {

        @EntityCassandra
        @Table("entities")
        record Entity(@Id String id,
                      @Column("value1") int field1,
                      String value2,
                      @Nullable String value3) {}

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        @Nullable
        Entity findById(String id);

        @Query("SELECT id, value1, value2, value3 FROM entities") //(2)!
        List<Entity> findAll();

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        void insert(Entity entity);
    }
    ```

    1.  Uses macros `%{return#selects}` and `%{return#table}`. Expands to query:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        WHERE id = :id
        ```
        Method uses macros for `SELECT`. Details: [Common Database Rules — Macros](database-common.md#macros)
    2.  Fields listed manually without macros — this is valid but requires maintenance when the view changes.
    3.  Uses macro `%{entity#inserts}`. Expands to query:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
        ```
        Method uses macros for `INSERT`. Details: [Common Database Rules — Macros](database-common.md#macros)

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : CassandraRepository {

        @EntityCassandra
        @Table("entities")
        data class Entity(
            @field:Id val id: String,
            @field:Column("value1") val field1: Int,
            val value2: String,
            val value3: String?
        )

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        fun findById(id: String): Entity?

        @Query("SELECT id, value1, value2, value3 FROM entities") //(2)!
        fun findAll(): List<Entity>

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(entity: Entity)
    }
    ```

    1.  Uses macros `%{return#selects}` and `%{return#table}`. Expands to query:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        WHERE id = :id
        ```
        Method uses macros for `SELECT`. Details: [Common Database Rules — Macros](database-common.md#macros)
    2.  Fields listed manually without macros — this is valid but requires maintenance when the view changes.
    3.  Uses macro `%{entity#inserts}`. Expands to query:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
        ```
        Method uses macros for `INSERT`. Details: [Common Database Rules — Macros](database-common.md#macros)

`CQL` remains under the developer's control: you write the query text yourself, while `Kora` only handles parameter binding,
query execution, and result mapping.
Common rules for entities, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch`, and macros are described in
[Common database rules](database-common.md#macros).

**Parameter binding:** Kora performs typed injection of arguments into the CQL query at compile time.
Named placeholders (`:id`, `:entity.field1`) are rewritten into positional `?` placeholders, and the generated code binds each value
through the driver, for example `_stmt.setString(0, id)`, where the index corresponds to the parameter order in the query.
This ensures security (protection against CQL injection) and performance (using driver prepared statements).

Unlike relational databases, `Cassandra` has no transactions.
When you need several statements to be applied atomically, use a `@Batch` method: Kora builds an `UNLOGGED` `CQL` `BATCH`
and binds one bound statement per element of the `@Batch List<T>` argument.
Its semantics and macros are documented in the [common database section](database-common.md#batch-query).

### Profile { #profile }

It is possible to override common settings with private settings from a profile, suppose there is such a profile configuration `someProfile`:

===! ":material-code-json: `Hocon`"

    ```javascript
    cassandra {
        profiles {
            someProfile {
                basic.request.timeout = "10s"
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    cassandra:
      profiles:
        someProfile:
          basic:
            request:
              timeout: "10s"
    ```

In order to apply the settings from the `someProfile` profile, just do the following:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends CassandraRepository {

        @CassandraProfile("someProfile")
        @Query("SELECT id, value FROM test_table WHERE id = :id allow filtering")
        @Nullable
        Entity findById(String id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : CassandraRepository {

        @CassandraProfile("someProfile")
        @Query("SELECT id, value FROM test_table WHERE id = :id allow filtering")
        fun findById(id: String): Entity?
    }
    ```

The settings specified in the profile will be applied to each request, specifically in this case - a timeout of 10s will be set.
The profile applies only to the method annotated with `@CassandraProfile`; other repository methods continue to use the base configuration.
Under the hood, the generated code calls `setExecutionProfileName("someProfile")` on the bound statement, so the profile name must exist in the `cassandra.profiles` section.

## Mapping { #mapping }

It is possible to override the mapping of different parts of [view](database-common.md) and query parameters, Kora provides special interfaces for this.
Out of the box, `CassandraMapperModule` provides mappers for `String`, `Byte`, `Short`, `Integer`, `Long`, `Float`, `Double`, `Boolean`,
`BigDecimal`, `BigInteger`, `UUID`, `ByteBuffer`, `byte[]`, `LocalTime`, `LocalDate`, `LocalDateTime`, `ZonedDateTime`, `Instant`, and `CqlDuration`.
If a type is not covered by that set, or if it needs a custom representation in `CQL`, add a custom mapper through `@Mapping`.

A mapper with constructor dependencies must be declared as a `@Component` so the container can build it.
A mapper without dependencies must not be annotated with `@Component` — Kora instantiates it itself, and an extra component declaration ends the build with `Multiple components match`.

### View { #view }

Use the `@EntityCassandra` annotation for optimal view mapping.
The annotation allows the annotation processor to generate all necessary mappers in **one round** of annotation processing:
a `CassandraRowMapper<T>`, a `CassandraResultSetMapper<T>` for a single result, and a `CassandraResultSetMapper<List<T>>` for a list.
Without this annotation, mappers are generated on-demand, which can require **multiple rounds** of processing and significantly increase compilation time.
This is the recommended way to map every view returned from or bound into a repository.

All nested views and [UDT](#udt) types are also expected to use this annotation.
`@EntityCassandra` is applicable only to records and Java bean-like classes (`data class` in Kotlin).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @EntityCassandra
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @EntityCassandra
    data class Entity(val id: String, val name: String)
    ```

### Result { #result }

If you need to convert the whole synchronous query result manually, use `CassandraResultSetMapper<T>`.
It receives `ResultSet` and returns the repository method value: a single object, list, `Optional<T>`, or another supported type.

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements CassandraResultSetMapper<List<UUID>> {

        @Override
        public List<UUID> apply(ResultSet rows) {
            var result = new ArrayList<UUID>();
            for (var row : rows) {
                result.add(row.getUuid("id"));
            }
            return result;
        }
    }

    @Repository
    public interface EntityRepository extends CassandraRepository {

        @Mapping(ResultMapper.class)
        @Query("SELECT id FROM entities")
        List<UUID> getIds();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ResultMapper : CassandraResultSetMapper<List<UUID>> {

        override fun apply(rows: ResultSet): List<UUID> {
            return rows.map { it.getUuid("id")!! }
        }
    }

    @Repository
    interface EntityRepository : CassandraRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): List<UUID>
    }
    ```

Each result-mapper interface also exposes static factory helpers that build a full result mapper from a `CassandraRowMapper<T>`,
so you can reuse a single row mapper across signatures:

- `CassandraResultSetMapper` — `singleResultSetMapper`, `optionalResultSetMapper`, `listResultSetMapper`;
- `CassandraAsyncResultSetMapper` — `one`, `list` (auto-paginates across result pages).

`CassandraMapperModule` also derives a `CassandraResultSetMapper<Optional<T>>` from any `CassandraRowMapper<T>` in the graph,
so `Optional<T>` signatures need no extra mapper.

### Row { #row }

If you need to convert one result row manually, use `CassandraRowMapper<T>`.
This mapper is applied to every row and suits return values like `T`, `Optional<T>`, and `List<T>`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements CassandraRowMapper<UUID> {

        @Override
        public UUID apply(Row row) {
            return UUID.fromString(row.getString(0));
        }
    }

    @Repository
    public interface EntityRepository extends CassandraRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id FROM entities")
        List<UUID> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RowMapper : CassandraRowMapper<UUID> {

        override fun apply(row: Row): UUID {
            return UUID.fromString(row.getString(0)!!)
        }
    }

    @Repository
    interface EntityRepository : CassandraRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id FROM entities")
        fun findAll(): List<UUID>
    }
    ```

### Column { #column }

If you need to convert the column value manually, it is suggested to use the `CassandraRowColumnMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements CassandraRowColumnMapper<UUID> {

        @Override
        public UUID apply(GettableByName row, int index) {
            return UUID.fromString(row.getString(index));
        }
    }

    @Table("entities")
    public record Entity(@Mapping(ColumnMapper.class) @Id UUID id, String name) { }

    @Repository
    public interface EntityRepository extends CassandraRepository {

        @Query("SELECT id, name FROM entities")
        List<Entity> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ColumnMapper : CassandraRowColumnMapper<UUID> {

        override fun apply(row: GettableByName, index: Int): UUID {
            return UUID.fromString(row.getString(index)!!)
        }
    }

    @Table("entities")
    data class Entity(
        @field:Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : CassandraRepository {

        @Query("SELECT id, name FROM entities")
        fun findAll(): List<Entity>
    }
    ```

`CassandraRowColumnMapper` is also what a `@UDT` type is read through, so the same interface can be used to take over the mapping of a user-defined type.

### Parameter { #parameter }

If you want to convert the value of a query parameter manually, use `CassandraParameterColumnMapper<T>`.
It receives `SettableByName<?>`, the parameter index, and the value from the repository method.
The value is nullable, so the implementation is responsible for leaving the placeholder unset when there is nothing to write.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements CassandraParameterColumnMapper<UUID> {

        @Override
        public void apply(SettableByName<?> stmt, int index, @Nullable UUID value) {
            if (value != null) {
                stmt.setString(index, value.toString());
            }
        }
    }

    @Repository
    public interface EntityRepository extends CassandraRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        List<Entity> findById(@Mapping(ParameterMapper.class) UUID id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ParameterMapper : CassandraParameterColumnMapper<UUID> {

        override fun apply(stmt: SettableByName<*>, index: Int, value: UUID?) {
            if (value != null) {
                stmt.setString(index, value.toString())
            }
        }
    }

    @Repository
    interface EntityRepository : CassandraRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(@Mapping(ParameterMapper::class) id: UUID): List<Entity>
    }
    ```

### Async { #async }

Java repository methods may return `CompletionStage<T>` or `CompletableFuture<T>`.
For such methods Kora executes the statement with `CqlSession#executeAsync` and maps the outcome with `CassandraAsyncResultSetMapper<T>`,
which receives `AsyncResultSet` and returns `CompletionStage<T>`.

For an `@EntityCassandra` view no extra mapper is needed: Kora derives the async mapper from the generated `CassandraRowMapper<T>`,
using `CassandraAsyncResultSetMapper.list(...)` for a `List<T>` result and `CassandraAsyncResultSetMapper.one(...)` otherwise.
The `list` helper walks the result pages, requesting the next one until the result set is exhausted, so a `List<T>` gathers every page before the future completes;
`one` maps only the first row.

```java
@Repository
public interface EntityRepository extends CassandraRepository {

    @EntityCassandra
    @Table("entities")
    record Entity(@Id String id,
                  @Column("value1") int field1,
                  String value2,
                  @Nullable String value3) {}

    @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id")
    CompletableFuture<Entity> findById(String id);

    @Query("SELECT %{return#selects} FROM %{return#table}")
    CompletionStage<List<Entity>> findAll();

    @Query("INSERT INTO %{entity#inserts}")
    CompletionStage<Void> insert(Entity entity);
}
```

A custom async mapper is provided the same way as a synchronous one, through `@Mapping`:

```java
final class AsyncResultMapper implements CassandraAsyncResultSetMapper<List<UUID>> {

    private static final CassandraAsyncResultSetMapper<List<UUID>> DELEGATE =
        CassandraAsyncResultSetMapper.list(row -> row.getUuid("id"));

    @Override
    public CompletionStage<List<UUID>> apply(AsyncResultSet rows) {
        return DELEGATE.apply(rows);
    }
}

@Repository
public interface EntityRepository extends CassandraRepository {

    @Mapping(AsyncResultMapper.class)
    @Query("SELECT id FROM entities")
    CompletionStage<List<UUID>> getIds();
}
```

Kotlin repositories have no asynchronous signatures: methods are synchronous and use `CassandraResultSetMapper` / `CassandraRowMapper`,
see [Result](#result) and [Signatures](#signatures).

## Manual Query { #query }

If a query is hard to express as a single static `@Query`, you can declare a regular method with an implementation and build `CQL` manually.
The repository exposes `executor()`, which returns a `CassandraExecutor`:

- `currentSession()` — the active driver `CqlSession`;
- `telemetry()` — the `DatabaseTelemetry` used for reporting;
- `query(CassandraQuery, CassandraResultSetMapper<T>)`, `queryOne(...)`, `queryOptional(...)`, `queryList(...)` — run a built query and map the result;
- `query(CassandraQuery, Function<BoundStatement, T>)` — run a built query and handle the bound statement yourself;
- `query(QueryContext, Function<PreparedStatement, T>)` — the lowest level: prepare a raw `CQL` string and do everything by hand.

Every one of them wraps the call in `Kora` telemetry, so a manual query is logged, measured, and traced exactly like a generated one.

`CQL` is assembled through the `CassandraQuery` builder, which keeps the query text and the parameter values apart:

- `CassandraQuery.named()` — `CQL` with `:name` placeholders, bound with `bind(name, value)`, `bindAll(map)`, `bindIn(name, values)` for `IN (:name)` clauses,
  and the conditional forms `cqlIf`, `bindIf`, `bindInIf`;
- `CassandraQuery.template()` and `CassandraQuery.template(cql, args...)` — `CQL` that already uses positional `?` placeholders;
- `opts(...)` — per-statement options: `consistencyLevel`, `serialConsistencyLevel`, `pageSize`, `timeout`, `idempotent`, `tracing`.

`build()` validates the query and fails with `IllegalArgumentException` when a placeholder is not bound, when a bound parameter is never used in `CQL`,
or when a `bindIn` collection is empty.
Named parameters are converted to positional `?` placeholders, so the driver still receives a prepared statement and values are never concatenated into the query text.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends CassandraRepository {

        default List<Entity> findByFilter(@Nullable String value2) {
            var query = CassandraQuery.named()
                .cql("SELECT id, value1, value2, value3 FROM entities")
                .cqlIf(" WHERE value2 = :value2 ALLOW FILTERING", value2 != null)
                .bindIf("value2", value2, value2 != null)
                .build();

            return executor().queryList(query, row -> new Entity(
                row.getString("id"),
                row.getInt("value1"),
                row.getString("value2"),
                row.getString("value3")));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : CassandraRepository {

        fun findByFilter(value2: String?): List<Entity> {
            val query = CassandraQuery.named()
                .cql("SELECT id, value1, value2, value3 FROM entities")
                .cqlIf(" WHERE value2 = :value2 ALLOW FILTERING", value2 != null)
                .bindIf("value2", value2, value2 != null)
                .build()

            return executor().queryList(query) { row ->
                Entity(
                    row.getString("id")!!,
                    row.getInt("value1"),
                    row.getString("value2")!!,
                    row.getString("value3")
                )
            }
        }
    }
    ```

When you need full control over statement preparation, use the `QueryContext` overload.
`QueryContext` carries the query identifier, the executable `CQL`, and the operation name:
the identifier is reported as the `db.query.text` telemetry attribute, and the operation name becomes the span name,
so use a stable value such as `Repository.method` — this is exactly what generated repositories do.
The two-argument constructor defaults the operation to `db_query`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends CassandraRepository {

        default List<Entity> findAllValues() {
            var executor = executor();
            var queryContext = new QueryContext(
                "SELECT id, value1, value2, value3 FROM entities",
                "SELECT id, value1, value2, value3 FROM entities",
                "EntityRepository.findAllValues");

            return executor.query(queryContext, statement -> executor.currentSession()
                .execute(statement.bind())
                .map(row -> new Entity(
                    row.getString("id"),
                    row.getInt("value1"),
                    row.getString("value2"),
                    row.getString("value3")))
                .all());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : CassandraRepository {

        fun findAllValues(): List<Entity> {
            val executor = executor()
            val queryContext = QueryContext(
                "SELECT id, value1, value2, value3 FROM entities",
                "SELECT id, value1, value2, value3 FROM entities",
                "EntityRepository.findAllValues"
            )

            return executor.query(queryContext) { statement ->
                executor.currentSession()
                    .execute(statement.bind())
                    .map { row ->
                        Entity(
                            row.getString("id")!!,
                            row.getInt("value1"),
                            row.getString("value2")!!,
                            row.getString("value3")
                        )
                    }
                    .all()
            }
        }
    }
    ```

Because `Cassandra` has no transactions, `query` simply runs on the current session with telemetry; there is no commit or rollback to manage.

## UDT { #udt }

There is support for [UDT](https://docs.datastax.com/en/cql-oss/3.3/cql/cql_using/useCreateUDT.html) types through the `@UDT` annotation.
`UDT` describes a Cassandra user-defined type and can be used as a field of a regular entity.
For every `@UDT` type Kora generates a reader and a writer, so the type works both in results and as a query parameter,
including nested `@UDT` types and `List<T>` of a `@UDT` type.
The `@UDT` type is mapped like any other entity, so the enclosing entity is annotated with `@EntityCassandra`.

Given the following schema, where `username` is a user-defined type stored as a `FROZEN` column:

```cql
CREATE TYPE IF NOT EXISTS username(first text, last text);

CREATE TABLE IF NOT EXISTS entities_udt
(
    id   VARCHAR,
    name FROZEN<username>,
    PRIMARY KEY (id)
);
```

the view and repository look like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends CassandraRepository {

        @EntityCassandra
        record Entity(String id, Name name) {

            @UDT
            record Name(String first, String last) {}
        }

        @Query("SELECT * FROM entities_udt WHERE id = :id")
        @Nullable
        Entity findById(String id);

        @Query("""
                INSERT INTO entities_udt(id, name)
                VALUES (:entity.id, :entity.name)
                """)
        void insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : CassandraRepository {

        @EntityCassandra
        data class Entity(val id: String, val name: Name) {

            @UDT
            data class Name(val first: String, val last: String)
        }

        @Query("SELECT * FROM entities_udt WHERE id = :id")
        fun findById(id: String): Entity?

        @Query("""
                INSERT INTO entities_udt(id, name)
                VALUES (:entity.id, :entity.name)
                """)
        fun insert(entity: Entity)
    }
    ```

If the `UDT` type is not used through an enclosing entity, but is itself the result of a query, add `@EntityCassandra` next to `@UDT`.
`@UDT` alone generates the column reader and writer; `@EntityCassandra` additionally generates the row and result-set mappers,
which is what a repository method returning that type needs.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @UDT
    @EntityCassandra
    public record Name(String first, String last) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @UDT
    @EntityCassandra
    data class Name(val first: String, val last: String)
    ```

### Macros { #macros }

To simplify writing `CQL` queries, use macros — they expand into `CQL` constructs at compile time.
Usage examples are shown above in the [Usage](#usage) section (`findById` and `insert` methods).

**Detailed documentation:** [Common Database Rules — Macros](database-common.md#macros)

## Signatures { #signatures }

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    `T` means the return value type, `List<T>`, or `Void`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `CompletableFuture<T> myMethod()` [CompletableFuture](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html)

    The `CompletionStage<T>` and `CompletableFuture<T>` wrappers can also wrap `List<T>` or `Void`,
    for example `CompletionStage<List<Entity>>` or `CompletableFuture<Void>`.

    Method parameters can include regular values, DTOs, `@Batch List<T>` for batch execution, and `CqlSession` when the method needs access to the current driver session.

=== ":simple-kotlin: `Kotlin`"

    `T` means the return value type, `T?`, `List<T>`, or `Unit`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `myMethod(): List<T>`
    - `myMethod()` for a query with no result

    Kotlin repository methods are synchronous. A `suspend` method annotated with `@Query` is rejected by the symbol processor
    with `Suspend methods are not supported by the repository generator` — run the blocking call and compose concurrency above the repository instead.

    Method parameters can include regular values, DTOs, `@Batch List<T>` for batch execution, and `CqlSession` when the method needs access to the current driver session.

Reactive return types are not supported: there are no `Mono` / `Flux` signatures and no reactive result mapper in the module.

## Telemetry { #telemetry }

Logging, metrics, and tracing are configured via the `telemetry` block in the [configuration](#configuration) and described in the [Metrics Reference](metrics.md#database) section.
By default query logging and metrics are off (`telemetry.logging.enabled = false`, `telemetry.metrics.enabled = false`) and tracing is on (`telemetry.tracing.enabled = true`).
The driver's own metrics are controlled separately by `telemetry.metrics.driverMetrics` and are configured through the `advanced.metrics` block.
To completely override telemetry, you can provide custom SPI factories; see the [Common Database Documentation](database-common.md#telemetry) for details.
