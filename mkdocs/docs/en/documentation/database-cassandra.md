---
description: "Explains Kora Cassandra repositories, Cassandra driver configuration, profiles, entity and UDT mapping, async access, and repository signatures. Use when working with @Repository, @Query, @EntityCassandra, @Table, @Id, @Column, @UDT, CassandraModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Cassandra repositories, Cassandra driver configuration, profiles, entity and UDT mapping, async access, and repository signatures; key triggers include @Repository, @Query, @EntityCassandra, @Table, @Id, @Column, @UDT, CassandraModule, CassandraRepository."
---

Module provides a repository implementation for the [Cassandra](https://cassandra.apache.org/_/cassandra-basics.html) database using the [DataStax](https://docs.datastax.com/en/developer/java-driver/4.17/) driver.
`Cassandra` is a distributed column-oriented database where queries are written in `CQL`, and the data model is usually designed around specific read scenarios.
In Kora, the Cassandra module provides declarative repositories on top of `CqlSession`: the application writes `CQL` queries in `@Query`, and Kora generates query preparation, parameter binding, and result mapping code at compile time.

Common rules for entities, `@Repository`, `@Query`, macros, batch queries, and the `@Table`, `@Column`, `@Id`, `@Embedded` annotations are described in the [common database section](database-common.md).
This document covers the Cassandra-specific parts: driver connection, `CqlSession` configuration, execution profiles, `UDT`, mappers, and supported method signatures.

For a step-by-step walkthrough before the reference details, see [Cassandra Database](../guides/database-cassandra.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-cassandra"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CassandraDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-cassandra")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : CassandraDatabaseModule
    ```

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
                    slo = [ 1, 10, 50, 100, 200, 500, 1000 ] //(117)!
                    tags = { "key1" = "value1", "key2" = "value2" } //(118)!
                }
                tracing {
                    enabled = true //(119)!
                    attributes = { "key1" = "value1", "key2" = "value2" } //(120)!
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
              slo: [ 1, 10, 50, 100, 200, 500, 1000 ] #(117)!
              tags: { key1: "value1", key2: "value2" } #(118)!
            tracing:
              enabled: true #(119)!
              attributes: { key1: "value1", key2: "value2" } #(120)!
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
    47. Enabled node-level metrics (default: `open-connections`, `in-flight`, `bytes-received`, `bytes-sent`, `write-timeouts`, `read-timeouts`, `aborted-requests`).
    48. Lowest expected latency for the `node.cqlMessages` metric histogram (default: `1ms`).
    49. Highest expected latency for the `node.cqlMessages` metric histogram (default: `90s`).
    50. Number of significant digits for the `node.cqlMessages` metric histogram (not specified by default, optional).
    51. Snapshot refresh interval for the `node.cqlMessages` metric histogram (not specified by default, optional).
    52. `SLO` boundaries for the `node.cqlMessages` metric (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    53. Enabled session-level metrics (default: `connected-nodes`, `cql-requests`, `cql-client-timeouts`, `cql-prepared-cache-size`, `throttling.delay`, `throttling.queue-size`).
    54. Lowest expected latency for the `session.cqlRequests` metric histogram (default: `1ms`).
    55. Highest expected latency for the `session.cqlRequests` metric histogram (default: `90s`).
    56. Number of significant digits for the `session.cqlRequests` metric histogram (not specified by default, optional).
    57. Snapshot refresh interval for the `session.cqlRequests` metric histogram (not specified by default, optional).
    58. `SLO` boundaries for the `session.cqlRequests` metric (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    59. Lowest expected latency for the `session.throttlingDelay` metric histogram (default: `1ms`).
    60. Highest expected latency for the `session.throttlingDelay` metric histogram (default: `90s`).
    61. Number of significant digits for the `session.throttlingDelay` metric histogram (not specified by default, optional).
    62. Snapshot refresh interval for the `session.throttlingDelay` metric histogram (not specified by default, optional).
    63. `SLO` boundaries for the `session.throttlingDelay` metric (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
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
    116. Enables Kora query metrics (default: `true`).
    117. Kora metrics `SLO` boundaries (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    118. Additional Kora metric tags (default: `{}`).
    119. Enables Kora query tracing (default: `true`).
    120. Additional Kora tracing attributes (default: `{}`).

### Code configuration { #code-configuration }

You can configure the driver manually in your code using `CassandraConfigurer` to modify the `CqlSession` builder:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyCassandraConfigurer implements CassandraConfigurer {

        @Override
        public CqlSessionBuilder configure(CqlSessionBuilder builder) {
            return builder.withClientId(UUID.randomUUID());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyCassandraConfigurer : CassandraConfigurer {
        override fun configure(builder: CqlSessionBuilder): CqlSessionBuilder {
            return builder.withClientId(UUID.randomUUID())
        }
    }
    ```

## Usage { #usage }

To create a repository, declare an interface with `@Repository` and extend `CassandraRepository`.
Such a repository gets access to `CqlSession` through generated code and uses `@Query` to execute `CQL` queries.
Query parameters are bound by name: `:id`, `:entity.field`, `:filter.value`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends CassandraRepository { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : CassandraRepository
    ```

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

## Mapping { #mapping }

It is possible to override the mapping of different parts of [entity](database-common.md) and query parameters, Kora provides special interfaces for this.
Out of the box, `CassandraModule` provides mappers for common types: `String`, numeric types, `Boolean`, `BigDecimal`, `BigInteger`, `UUID`, `ByteBuffer`, `LocalDate`, `LocalTime`, `LocalDateTime`, `ZonedDateTime`, and `Instant`.
If a type is not covered by that set, or if it needs a custom representation in `CQL`, add a custom mapper through `@Mapping`.

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

    In Kotlin, you only need to write mappers for `T?` types, so the type is specified as `@Nullable` in the interfaces.

    ```kotlin
    class ResultMapper : CassandraResultSetMapper<List<UUID>> {
        override fun apply(rows: ResultSet): List<UUID> {
            return rows.map { it.getUuid("id") }
        }
    }

    @Repository
    interface EntityRepository : CassandraRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): List<UUID>
    }
    ```

### Row { #row }

If you need to convert one result row manually, use `CassandraRowMapper<T>`.
This mapper is applied to every row and suits return values like `T`, `Optional<T>`, `List<T>`, `Flux<T>`, and `Flow<T>`.

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

    In Kotlin, you only need to write mappers for `T?` types, so the type is specified as `@Nullable` in the interfaces.

    ```kotlin
    class RowMapper : CassandraRowMapper<UUID> {

        override fun apply(row: Row): UUID {
            return UUID.fromString(row.getString(0))
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

    In Kotlin, you only need to write mappers for `T?` types, so the type is specified as `@Nullable` in the interfaces.

    ```kotlin
    class ColumnMapper : CassandraRowColumnMapper<UUID> {

        override fun apply(row: GettableByName, index: Int): UUID {
            return UUID.fromString(row.getString(index))
        }
    }

    @Table("entities")
    data class Entity(
        @Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : CassandraRepository {

        @Query("SELECT id, name FROM entities")
        fun findAll(): List<Entity>
    }
    ```

### Parameter { #parameter }

If you want to convert the value of a query parameter manually, use `CassandraParameterColumnMapper<T>`.
It receives `SettableByName<?>`, the parameter index, and the value from the repository method.

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

    In Kotlin, you only need to write mappers for `T?` types, so the type is specified as `@Nullable` in the interfaces.

    ```kotlin
    class ParameterMapper : CassandraParameterColumnMapper<UUID?> {

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

For `CompletionStage<T>`, use `CassandraAsyncResultSetMapper<T>`, which receives `AsyncResultSet` and returns `CompletionStage<T>`.
For reactive types `Mono<T>` / `Flux<T>`, use `CassandraReactiveResultSetMapper<T, P>`, which receives `ReactiveResultSet` and returns the required `Publisher`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ReactiveResultMapper implements CassandraReactiveResultSetMapper<UUID, Flux<UUID>> {

        @Override
        public Flux<UUID> apply(ReactiveResultSet rows) {
            return Flux.from(rows).map(r -> UUID.fromString(r.getString(0)));
        }
    }

    @Repository
    public interface EntityRepository extends CassandraRepository {

        @Mapping(ReactiveResultMapper.class)
        @Query("SELECT id FROM entities")
        Flux<UUID> getIds();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ReactiveResultMapper : CassandraReactiveResultSetMapper<UUID, Flux<UUID>> {
        override fun apply(rows: ReactiveResultSet): Flux<UUID> {
            return Flux.from(rows).map { r -> UUID.fromString(r.getString(0)) }
        }
    }

    @Repository
    interface EntityRepository : CassandraRepository {

        @Mapping(ReactiveResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): Flux<UUID>
    }
    ```

## UDT { #udt }

There is support for [UDT](https://docs.datastax.com/en/cql-oss/3.3/cql/cql_using/useCreateUDT.html) types through the `@UDT` annotation.
`UDT` describes a Cassandra user-defined type and can be used as a field of a regular entity.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Table("entities")
    public record Entity(String id, Name name) {

        @UDT
        public record Name(String first, String middle, String last) { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Table("entities")
    data class Entity(val id: String, val name: Name) {

        @UDT
        data class Name(val first: String, val middle: String, val last: String)
    }
    ```

If the type is not used as a repository return value, but as a standalone Cassandra type, mapper generation can be enabled explicitly with `@EntityCassandra`.
This is useful when the mapper is needed as a separate graph component.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @EntityCassandra
    public record Name(String first, String middle, String last) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @EntityCassandra
    data class Name(val first: String, val middle: String, val last: String)
    ```

## Signatures { #signatures }

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    `T` means the return value type, `List<T>`, or `Void`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

    Method parameters can include regular values, DTOs, `@Batch List<T>` for batch execution, and `CqlSession` when the method needs access to the current driver session.

=== ":simple-kotlin: `Kotlin`"

    `T` means the return value type, `T?`, `List<T>`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

    Method parameters can include regular values, DTOs, `@Batch List<T>` for batch execution, and `CqlSession` when the method needs access to the current driver session.
