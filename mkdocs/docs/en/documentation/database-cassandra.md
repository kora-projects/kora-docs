Module provides a repository implementation for the [Cassandra](https://cassandra.apache.org/_/cassandra-basics.html) database using the [DataStax](https://docs.datastax.com/en/developer/java-driver/4.17/) driver.

## Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:database-cassandra"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CassandraDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:database-cassandra")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : CassandraDatabaseModule
    ```

## Configuration

Example of a simple configuration described in `CassandraConfig` class (example values are indicated):

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

    1. Cassandra node addresses for connection to the database (**required**)
    2. Cassandra datacenter name (optional)
    3. Name of keyspace for connection (optional)
    4. Query execution timeout (optional)
    5. Username for connection (optional)
    6. Password for connection (optional)

=== ":simple-yaml: ``YAML`"

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

    1. Cassandra node addresses for connection to the database (**required**)
    2. Cassandra datacenter name (optional)
    3. Name of keyspace for connection (optional)
    4. Query execution timeout (optional)
    5. Username for connection (optional)
    6. Password for connection (optional)

??? abstract "Full configuration example"

    Full configuration with example values (configuration is in `CassandraConfig` class):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        cassandra {
            auth {
                login = "username" 
                password = "password" 
            }

            basic {
                contactPoints = [ "127.0.0.1:9042", "127.0.0.2:9042" ]  // Nod cassandra hosts
                sessionName = "some-session-name"                       // session name
                dc = "datacenter1"                                      // Datacenter Name
                sessionKeyspace = "test-db"                             // The name of the keyspace for this session
                
                loadBalancingPolicy.slowReplicaAvoidance = true                     // Flag to enable the slow cue avoidance mechanism
                cloud.secureConnectBundle = "/location/of/secure/connect/bundle"    // Bandle locations to connect to Datastax Apache Cassandra. The path must be a valid URL. By default, if no protocol is specified, it will be assumed to be file://
                request {                               // Request settings
                    timeout = "5s"                      // request timeout
                    consistency = "LOCAL_ONE"           // consistency level, permissible values: ANY, ONE, TWO, THREE, QUORUM, ALL, LOCAL_QUORUM, EACH_QUORUM, SERIAL, LOCAL_SERIAL, LOCAL_ONE
                    pageSize = 5000                     // Page size limit (determines how many lines can be returned in a single request)
                    serialConsistency = "LOCAL_SERIAL"  // Consistency level for lightweight transactions(LWT). Allowed values of SERIAL and LOCAL_SERIAL.
                    defaultIdempotence = false          // Settings of idempotency value for queries
                }
            }
            advanced {                                  // Advanced settings
                sessionLeak.threshold = 4               // Maximum number of active sessions
                connection {
                    connectTimeout = "10s"              // Connection timeout
                    initQueryTimeout = "10s"            // Request initialization timeout
                    setKeyspaceTimeout = "10s"          // Keyspace setting timeout
                    maxRequestsPerConnection = 1024     // Limiting requests per connection
                    maxOrphanRequests = 256             // The maximum number of "orphaned" requests, i.e., those for which a response has ceased to be expected for one reason or another.
                    warnOnInitError = true              // Output initialization errors to the log
                    pool {                              // Pool Settings
                        localSize = 10 
                        remoteSize = 10 
                    }
                }
                reconnectOnInit = false             // Retry initialization if all nodes specified in contactpoints did not respond at the first attempt
                reconnectionPolicy {                // Reconnect Policy - Base and Maximum Delay. By default, the first value is used when an attempt fails, then doubles with each subsequent attempt until it reaches the maximum value
                    baseDelay = "1s" 
                    maxDelay = "60s"
                }
               
                sslEngineFactory {
                    cipherSuites = [ "TLS_RSA_WITH_AES_128_CBC_SHA", "TLS_RSA_WITH_AES_256_CBC_SHA" ] 
                    hostnameValidation = true                       // Host name validation
                    keystorePath = "/path/to/client.keystore"       // Path to the key vault
                    keystorePassword = "password"                   // The password to the key vault
                    truststorePath = "/path/to/client.truststore"   // Path to trusted storage
                    truststorePassword = "password"                 // Trusted storage password
                }
                
                timestampGenerator {                    // A generator that adds a timestamp to each request. AtomicTimestampGenerator is used by default
                    forceJavaClock = false              // Forced to use Java system clock
                    driftWarning.threshold = "1s"       // Indicates how far into the future timestamps can "run away" under high loads
                    driftWarning.interval = "10s"       // Interval for logging warnings if timestamps continue to "run" forward.
                }
               
                protocol {
                    version = "V4"                  // Cassandra protocol version
                    compression = "lz4"             // Compression
                    maxFrameLength = 268435456      // Maximum frame length in bytes
                }
                request {
                    warnIfSetKeyspace = true        // Log a warning that keyspace is being set in a query
                    trace {                         // Settings of the built-in query tracing mechanism
                        attempts = 5                // Number of attempts
                        interval = "1ms"            // Interval between attempts
                        consistency = "ONE"         // Consistency level
                    }
                    logWarnings = true
                }
                metrics {                           // session-level metrics, with all metrics turned off by default
                    node.enabled = []               // List of enabled metrics. Included: bytes-sent, connected-nodes, cql-requests, cql-client-timeouts, cql-prepared-cache-size, throttling.delay, throttling.errors, continuous-cql-requests
                    session.enabled = [] 
                    node.cqlMessages {              // Additional customizations for metrics if needed:
                        lowestLatency = "1ms"
                        highestLatency = "1s"
                        significantDigits = 3
                        refreshInterval= 5
                    }
                    session.cqlRequests {
                        lowestLatency = "1ms"
                        highestLatency = "1s"
                        significantDigits = 3
                        refreshInterval= 5
                    }
                    session.throttlingDelay {
                        lowestLatency = "1ms"
                        highestLatency = "1s"
                        significantDigits = 3
                        refreshInterval= 5
                    }
                }
                socket {
                    tcpNoDelay = true           // Flag to disable Nagle algorithm, by default true(off), because the driver has its own message coalescing algorithm.
                    keepAlive = false 
                    reuseAddress = true         // Allow the address to be reused
                    lingerInterval = 0
                    receiveBufferSize = 65535
                    sendBufferSize = 65535
                }
                heartbeat {
                    interval = "30s"
                    timeout = "2m"
                }
                metadata {                      // Settings responsible for schema metadata
                    schema {
                        enabled = true 
                        requestTimeout = "20s"
                        requestPageSize = 20
                        refreshedKeyspaces = [ "ks1", "ks2" ] 
                        debouncer.window = "1s"     // The amount of time the driver waits before applying the update
                        debouncer.maxEvents = 20    // Maximum number of updates that can be accumulated
                    }
                    topologyEventDebouncer.window = "1s"    // A window for sending the event.
                    topologyEventDebouncer.maxEvents = 20   // Maximum number of events in a bundle
                    tokenMapEnabled = true 
                }
                controlConnection {
                    timeout = "10s"
                    schemaAgreement {
                        interval = 200ms 
                        timeout = "10s"
                        warnOnFailure = true 
                    }
                }
                preparedStatements {
                    prepareOnAllNodes = true        // Execute query preparation on all nodes after its successful execution on one node.
                    reprepareOnUp {
                        enabled = true              // Prepare queries for new nodes
                        checkSystemTable = false    // Check if there is a prepare statement in system.prepared_statements node before preparation
                        maxStatements = 0           // Maximum number of requests that can be retrained
                        maxParallelism = 100        // Maximum number of competitive requests
                        timeout = 20s
                    }
                    preparedCache.weakValues = false 
                }
                netty {                         // Netty event loop settings used in the driver
                    ioGroup.size = 0            // Number of tracks
                    ioGroup.shutdown {          // Graceful shutdown settings
                        quietPeriod = 2 
                        timeout = 15 
                        unit = "SECONDS"
                    }
                    adminGroup.size = 2         // Event loop group used only for admin tasks not related to IO
                    adminGroup.shutdown {
                        quietPeriod = 2 
                        timeout = 15 
                        unit = "SECONDS"
                    }
                    timer.tickDuration = "100ms"  // Settings for how often the timer should wake up to check for overdue tasks
                    timer.ticksPerWheel = 2048 
                    daemon = false 
                }
                coalescer.rescheduleInterval = "10ms"
                resolveContactPoints = false 
            }
            profiles {          // Settings overridden in the profile
                someProfile {
                    basic {
                        // basic.request.timeout
                        // basic.request.consistency
                    }
                    advanced {
                        // advanced.request.trace.consistency
                        // advanced.request.trace.attempts
                    }
                }
            }  
            telemetry {
                logging {
                    enabled = false 
                }
                metrics {
                    enabled = true
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ]
                }
                tracing {
                    enabled = true
                }
            }
        }
        ```

    === ":simple-yaml: `YAML`"

        ```yaml
        cassandra:
          advanced:                             # Advanced settings
            coalescer:
              rescheduleInterval: "10ms"
            connection:
              connectTimeout: "10s"             # Connection timeout
              initQueryTimeout: "10s"           # Request initialization timeout
              setKeyspaceTimeout: "10s"         # Keyspace setting timeout
              maxOrphanRequests: 256            # The maximum number of "orphaned" requests, i.e., those for which a response has ceased to be expected for one reason or another.
              maxRequestsPerConnection: 1024    # Limiting requests per connection
              pool:                             # Pool Settings. 
                localSize: 10
                remoteSize: 10
              warnOnInitError: true             # Output initialization errors to the log
            controlConnection:
              schemaAgreement:
                interval: "200ms"
                timeout: "10s"
                warnOnFailure: true
              timeout: "10s"
            heartbeat:
              interval: "30s"
              timeout: "2m"
            metadata:               # Settings responsible for schema metadata
              schema:
                debouncer:
                  maxEvents: 20     # Maximum number of updates that can be accumulated
                  window: "1s"      # The amount of time the driver waits before applying the update
                enabled: true
                refreshedKeyspaces:
                  - ks1
                  - ks2
                requestPageSize: 10
                requestTimeout: "20s"
                tokenMapEnabled: true
                topologyEventDebouncer:
                  maxEvents: 20     # Maximum number of events in a bundle
                  window: "1s"      # A window for sending the event.
              metrics: 
                node:
                  enabled: []           # List of enabled metrics. Included: bytes-sent, connected-nodes, cql-requests, cql-client-timeouts, cql-prepared-cache-size, throttling.delay, throttling.errors, continuous-cql-requests
                  cqlMessages:          # Additional customizations for metrics if needed:
                    highestLatency: "1s"
                    lowestLatency: "1ms"
                    refreshInterval: 5
                    significantDigits: 3
                session:                # session-level metrics, with all metrics turned off by default
                  enabled: []           # List of enabled metrics. Included: bytes-sent, connected-nodes, cql-requests, cql-client-timeouts, cql-prepared-cache-size, throttling.delay, throttling.errors, continuous-cql-requests
                  cqlRequests:
                    highestLatency: "1s"
                    lowestLatency: "1ms"
                    refreshInterval: 5
                    significantDigits: 3
                  throttlingDelay:
                    highestLatency: "1s"
                    lowestLatency: "1ms"
                    refreshInterval: 5
                    significantDigits: 3
              netty:                        # Netty event loop settings used in the driver
                adminGroup:                 # Event loop group used only for admin tasks not related to IO
                  shutdown:
                    quietPeriod: 2
                    timeout: 15
                    unit: SECONDS
                  size: 2
                daemon: false
                ioGroup:
                  shutdown:                 # Graceful shutdown settings
                    quietPeriod: 2
                    timeout: 15
                    unit: SECONDS
                  size: 0                   # Number of tracks
                timer:
                  tickDuration: "100ms"     # Settings for how often the timer should wake up to check for overdue tasks
                  ticksPerWheel: 2048
              preparedStatements:
                prepareOnAllNodes: true     # Execute query preparation on all nodes after its successful execution on one node.
                preparedCache:
                  weakValues: false
                reprepareOnUp:
                  enabled: true             # Prepare queries for new nodes
                  checkSystemTable: false   # Check if there is a prepare statement in system.prepared_statements node before preparation
                  maxParallelism: 100       # Maximum number of competitive requests
                  maxStatements: 0          # Maximum number of requests that can be retrained
                  timeout: "20s"
              protocol:
                compression: "lz4"            # Compression
                maxFrameLength: 268435456   # Maximum frame length in bytes
                version: "V4"                 # Cassandra protocol version
              reconnectOnInit: false        # Retry initialization if all nodes specified in contactpoints did not respond at the first attempt
              reconnectionPolicy:           # Reconnect Policy - Base and Maximum Delay. By default, the first value is used when an attempt fails, then doubles with each subsequent attempt until it reaches the maximum value
                baseDelay: "1s"
                maxDelay: "60s"
              request:
                logWarnings: true
                trace:
                  attempts: 5               # Number of attempts
                  consistency: ONE          # Consistency level
                  interval: "1ms"           # Interval between attempts
                warnIfSetKeyspace: true     # Log a warning that keyspace is being set in a query
              resolveContactPoints: false
              sessionLeak:
                threshold: 4
              socket:
                keepAlive: false
                lingerInterval: 0
                receiveBufferSize: 65535
                reuseAddress: true          # Allow the address to be reused
                sendBufferSize: 65535
                tcpNoDelay: true            # Flag to disable Nagle algorithm, by default true(off), because the driver has its own message coalescing algorithm.
              sslEngineFactory:
                cipherSuites:
                  - TLS_RSA_WITH_AES_128_CBC_SHA
                  - TLS_RSA_WITH_AES_256_CBC_SHA
                hostnameValidation: true                        # Host name validation
                keystorePassword: "password"                    # The password to the key vault
                keystorePath: "/path/to/client.keystore"        # Path to the key vault
                truststorePassword: "password"                  # Trusted storage password
                truststorePath: "/path/to/client.truststore"    # Path to trusted storage
              timestampGenerator:       # A generator that adds a timestamp to each request. AtomicTimestampGenerator is used by default
                driftWarning:
                  interval: "10s"       # Interval for logging warnings if timestamps continue to "run" forward.
                  threshold: "1s"       # Indicates how far into the future timestamps can "run away" under high loads
                forceJavaClock: false   # Forced to use Java system clock
            auth:
              login: "username"
              password: "password"
            basic:
              cloud:
                secureConnectBundle: "/location/of/secure/connect/bundle"
              contactPoints:
                - "127.0.0.1:9042"
                - "127.0.0.2:9042"
              dc: datacenter1
              loadBalancingPolicy:
                slowReplicaAvoidance: true
              request:
                consistency: LOCAL_ONE
                defaultIdempotence: false
                pageSize: 5000
                serialConsistency: LOCAL_SERIAL
                timeout: "5s"
              sessionKeyspace: "test-db"
              sessionName: "some-session-name"
            profiles:       # Settings overridden in the profile
              someProfile:
                advanced:
                  #advanced.request.trace.consistency
                  #advanced.request.trace.attempts
                basic:
                  #basic.request.timeout
                  #basic.request.consistency
          telemetry:
            logging:
              enabled: false
            metrics:
              enabled: true
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ]
            tracing:
              enabled: true
        ```

## Usage

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

### Профиль

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

## Mapping

It is possible to override the mapping of different parts of [entity](database-common.md) and query parameters, Kora provides special interfaces for this.

### Result

If you need to convert the result manually, it is suggested to use `CassandraResultSetMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements CassandraResultSetMapper<UUID> {

        @Override
        public UUID apply(ResultSet rows) {
            // mapping code
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
    class ResultMapper : CassandraResultSetMapper<UUID> {
        override fun apply(rows: ResultSet): UUID {
            // mapping code
        }
    }

    @Repository
    interface EntityRepository : CassandraRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): List<UUID>
    }
    ```

### Row

If you need to convert the string manually, it is suggested to use `CassandraRowMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements CassandraRowMapper<UUID> {

        @Override
        public UUID apply(Row row) {
            return UUID.fromString(rs.getString(0));
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
            return UUID.fromString(rs.getString(0))
        }
    }

    @Repository
    interface EntityRepository : CassandraRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id FROM entities")
        fun findAll(): List<UUID>
    }
    ```

### Column

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

        @Query("SELECT * FROM entities")
        List<Entity> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

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

        @Query("SELECT * FROM entities")
        fun findAll(): List<Entity>
    }
    ```

### Parameter

If you want to convert the value of a query parameter manually, it is suggested to use `CassandraParameterColumnMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements CassandraParameterColumnMapper<UUID> {

        @Override
        public void set(SettableByName<?> stmt, int index, @Nullable UUID value) {
            if (value != null) {
                stmt.setString(index, value.toString());
            }
        }
    }

    @Repository
    public interface EntityRepository extends CassandraRepository {

        @Query("SELECT * FROM entities WHERE id = :id")
        List<Entity> findById(@Mapping(ParameterMapper.class) UUID id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ParameterMapper : CassandraParameterColumnMapper<UUID?> {

        override fun set(stmt: SettableByName<*>, index: Int, value: UUID?) {
            if (value != null) {
                stmt.setString(index, value.toString())
            }
        }
    }

    @Repository
    interface EntityRepository : CassandraRepository {

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(@Mapping(ParameterMapper::class) id: UUID): List<Entity>
    }
    ```

### Async

Due to the nature of the helper class for extracting data from `AsyncResultSet` for asynchronous queries (Mono or Suspend), only `CassandraReactiveResultSetMapper` can be used:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class AsyncResultMapper implements CassandraReactiveResultSetMapper<UUID, Flux<UUID>> {

        @Override
        public UUID apply(ResultSet rows) {
            return Flux.from(rows).map(r -> UUID.fromString(r.getString(0)));
        }
    }

    @Repository
    public interface EntityRepository extends CassandraRepository {

        @Mapping(AsyncResultMapper.class)
        @Query("SELECT id FROM entities")
        Flux<UUID> getIds();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class AsyncResultMapper : CassandraReactiveResultSetMapper<UUID, Flux<UUID>> {
        override fun apply(rows: ReactiveResultSet): Flux<UUID> {
            return Flux.from(rows).map { r -> UUID.fromString(r.getString(0)) }
        }
    }

    @Repository
    interface EntityRepository : CassandraRepository {

        @Mapping(AsyncResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): Flux<UUID>
    }
    ```

## UDT

There is support for [UDT](https://docs.datastax.com/en/cql-oss/3.3/cql/cql_using/useCreateUDT.html)
types using the `@UDT` annotation:

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

## Signatures

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value, either `Void` or `UpdateCount`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `List<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (add [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Mono<List<T>>> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (add [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (add [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `Unit` or `UpdateCount`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `myMethod(): List<T>`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (add [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (add [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `suspend myMethod(): List<T>?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (add [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (add [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
