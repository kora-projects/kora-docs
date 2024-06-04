Модуль предоставляет реализацию репозиториев для базы данных [Cassandra](https://cassandra.apache.org/_/cassandra-basics.html) с использованием драйвера [DataStax](https://docs.datastax.com/en/developer/java-driver/4.17/).

## Подключение

===! ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:database-cassandra"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CassandraDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:database-cassandra")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CassandraDatabaseModule
    ```

## Конфигурация

Пример простой конфигурация, описанной в классе `CassandraConfig` (указаны примеры значений):

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

    1. Адреса нод Cassandra для подключения к базе данных (**обязательный**)
    2. Имя датацентра Cassandra (по умолчанию отсутвует)
    3. Имя keyspace для подключения (по умолчанию отсутвует)
    4. Ограничение время выполнения запросов в рамках подключения (по умолчанию отсутвует)
    5. Имя пользователя для подключения (по умолчанию отсутвует)
    6. Пароль пользователя для подключения (по умолчанию отсутвует)

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

    1. Адреса нод Cassandra для подключения к базе данных (**обязательный**)
    2. Имя датацентра Cassandra (по умолчанию отсутвует)
    3. Имя keyspace для подключения (по умолчанию отсутвует)
    4. Ограничение время выполнения запросов в рамках подключения (по умолчанию отсутвует)
    5. Имя пользователя для подключения (по умолчанию отсутвует)
    6. Пароль пользователя для подключения (по умолчанию отсутвует)

??? abstract "Пример полной конфигурации"

    Пример полной конфигурации с примерами значений которые могут быть описаны (конфигурация описана в классе `CassandraConfig`):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        cassandra {
            auth {
                login = "username" 
                password = "password" 
            }

            basic {
                contactPoints = [ "127.0.0.1:9042", "127.0.0.2:9042" ]  // хосты нод кассандры
                sessionName = "some-session-name"                       // имя сессии
                dc = "datacenter1"                                      // Имя датацентра
                sessionKeyspace = "test-db"                             // Название keyspace для этой сессии
                
                loadBalancingPolicy.slowReplicaAvoidance = true                     // Флаг включения механизма избегания медленных реплик
                cloud.secureConnectBundle = "/location/of/secure/connect/bundle"    // Расположения бандла для подключения к Datastax Apache Cassandra. Путь должен быть валидным URL'ом. По умолчанию, если не указан протокол, будет считаться что это file://
                request {                               // Настройки запросов
                    timeout = "5s"                      // таймаут запроса
                    consistency = "LOCAL_ONE"           // уровень консистентности, допустимые значения: ANY, ONE, TWO, THREE, QUORUM, ALL, LOCAL_QUORUM, EACH_QUORUM, SERIAL, LOCAL_SERIAL, LOCAL_ONE
                    pageSize = 5000                     // Ограничение размера страницы (определяет, сколько строк может быть возвращено за один запрос)
                    serialConsistency = "LOCAL_SERIAL"  // Уровень консистентности для легковесных транзакций(LWT). Допустимые значения SERIAL и LOCAL_SERIAL.
                    defaultIdempotence = false          // Настройки значения идемпотентности для запросов
                }
            }
            advanced {                                  // Расширенные настройки
                sessionLeak.threshold = 4               // Максимальное количество активных сессий
                connection {
                    connectTimeout = "10s"              // Таймаут подключения
                    initQueryTimeout = "10s"            // Таймаут инициализации запроса
                    setKeyspaceTimeout = "10s"          // Таймаут установки keyspace
                    maxRequestsPerConnection = 1024     // Ограничение запросов на одно подключение
                    maxOrphanRequests = 256             // Максимальное количество "осиротевших" запросов, т.е. тех, ответ на которые по тем или иным причинам прекратили ожидать. 
                    warnOnInitError = true              // Выводить ошибки при инициализации в лог
                    pool {                              // Настройки пула. 
                        localSize = 10 
                        remoteSize = 10 
                    }
                }
                reconnectOnInit = false             // Повторять попытку инициализации, если при первой попытке все ноды, указанные в contactpoints, не ответили
                reconnectionPolicy {                // Политика переподключения - базовая и максимальная задержка. По умолчанию, при неудачно попытке используется первое значение, затем при каждой следующей - удваивается, пока не достигнет максимального значения
                    baseDelay = "1s" 
                    maxDelay = "60s"
                }
               
                sslEngineFactory {
                    cipherSuites = [ "TLS_RSA_WITH_AES_128_CBC_SHA", "TLS_RSA_WITH_AES_256_CBC_SHA" ] 
                    hostnameValidation = true                       // Валидация имени хоста
                    keystorePath = "/path/to/client.keystore"       // Путь к хранилищу ключей
                    keystorePassword = "password"                   // Пароль от хранилища ключей
                    truststorePath = "/path/to/client.truststore"   // Путь к доверенному хранилищу
                    truststorePassword = "password"                 // Пароль от доверенного хранилища
                }
                
                timestampGenerator {                    // Генератор, добавляющий timestamp к каждому запросу. По умолчанию используется AtomicTimestampGenerator
                    forceJavaClock = false              // Принудительно использовать Java system clock
                    driftWarning.threshold = "1s"       // Указывает, насколько далеко в будущее могут "убегать" таймстэмпы при высокой нагрузке
                    driftWarning.interval = "10s"       // Интервал логирования предупреждений, есди таймстэмпы продолжают "убегать" вперёд.
                }
               
                protocol {
                    version = "V4"                  // Версия протокола Cassandra
                    compression = "lz4"             // Сжатие
                    maxFrameLength = 268435456      // Максимальная длина фрейма в байтах
                }
                request {
                    warnIfSetKeyspace = true        // Логировать предупреждение о том, что в запросе выполняется установка keyspace 
                    trace {                         // Настройки встроенного механизма трейсинга запросов
                        attempts = 5                // Количество попыток 
                        interval = "1ms"            // Интервал между попытками
                        consistency = "ONE"         // Уровень консистентности
                    }
                    logWarnings = true
                }
                metrics {                           // session-level метрики, по умолчанию выключены все
                    node.enabled = []               // Список включенных метрик. Включаемые: bytes-sent, connected-nodes, cql-requests, cql-client-timeouts, cql-prepared-cache-size, throttling.delay, throttling.errors, continuous-cql-requests
                    session.enabled = [] 
                    node.cqlMessages {              // Дополнительные настройки для метрик, если нужны:
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
                    tcpNoDelay = true           // Флаг для отключения Nagle алгоритма, по умолчанию true(выключен), т.к. драйвер имеет собственный message coalescing algorithm
                    keepAlive = false 
                    reuseAddress = true         // Позволять переиспользовать адрес
                    lingerInterval = 0
                    receiveBufferSize = 65535
                    sendBufferSize = 65535
                }
                heartbeat {
                    interval = "30s"
                    timeout = "2m"
                }
                metadata {                      // Настройки, отвечающие за schema metadata
                    schema {
                        enabled = true 
                        requestTimeout = "20s"
                        requestPageSize = 20
                        refreshedKeyspaces = [ "ks1", "ks2" ] 
                        debouncer.window = "1s"     // Время, которое драйвер ждёт перед применением обновления
                        debouncer.maxEvents = 20    // Максимальное количество обновлений, которое может быть накоплено
                    }
                    topologyEventDebouncer.window = "1s"    // Окно для отправки события.
                    topologyEventDebouncer.maxEvents = 20   // Максимальное количество событий в пачке
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
                    prepareOnAllNodes = true        // Выполнять подготовку запроса на всех нодах после её успешного выполнения на одной ноде.
                    reprepareOnUp {
                        enabled = true              // Подготавливать запросы для новых нод
                        checkSystemTable = false    // Проверять наличие prepare statement в system.prepared_statements ноды перед подготовкой
                        maxStatements = 0           // Максимальной количество запросов, которые можно переподготовить
                        maxParallelism = 100        // Максимальное количество конкурентных запросов
                        timeout = 20s
                    }
                    preparedCache.weakValues = false 
                }
                netty {                         // Настройки Netty event loop, используемой в драйвере
                    ioGroup.size = 0            // Количество тредов
                    ioGroup.shutdown {          // Настройки graceful shutdown
                        quietPeriod = 2 
                        timeout = 15 
                        unit = "SECONDS"
                    }
                    adminGroup.size = 2         // Event loop группа, используемая только для админских задач, не связанных с IO
                    adminGroup.shutdown {
                        quietPeriod = 2 
                        timeout = 15 
                        unit = "SECONDS"
                    }
                    timer.tickDuration = "100ms"  // Настройки того, как часто таймер должен пробуждаться для проверки просроченных задач
                    timer.ticksPerWheel = 2048 
                    daemon = false 
                }
                coalescer.rescheduleInterval = "10ms"
                resolveContactPoints = false 
            }
            profiles {          // Настройки, переопределяемые в профиле
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
                telemetry {
                    enabled = true
                }
            }
        }
        ```

    === ":simple-yaml: `YAML`"

        ```yaml
        cassandra:
          advanced:                             # Расширенные настройки
            coalescer:
              rescheduleInterval: "10ms"
            connection:
              connectTimeout: "10s"             # Таймаут подключения
              initQueryTimeout: "10s"           # Таймаут инициализации запроса
              setKeyspaceTimeout: "10s"         # Таймаут установки keyspace
              maxOrphanRequests: 256            # Максимальное количество "осиротевших" запросов, т.е. тех, ответ на которые по тем или иным причинам прекратили ожидать. 
              maxRequestsPerConnection: 1024    # Ограничение запросов на одно подключение
              pool:                             # Настройки пула. 
                localSize: 10
                remoteSize: 10
              warnOnInitError: true             # Выводить ошибки при инициализации в лог
            controlConnection:
              schemaAgreement:
                interval: "200ms"
                timeout: "10s"
                warnOnFailure: true
              timeout: "10s"
            heartbeat:
              interval: "30s"
              timeout: "2m"
            metadata:               # Настройки, отвечающие за schema metadata
              schema:
                debouncer:
                  maxEvents: 20     # Максимальное количество обновлений, которое может быть накоплено
                  window: "1s"      # Время, которое драйвер ждёт перед применением обновления
                enabled: true
                refreshedKeyspaces:
                  - ks1
                  - ks2
                requestPageSize: 10
                requestTimeout: "20s"
                tokenMapEnabled: true
                topologyEventDebouncer:
                  maxEvents: 20     # Максимальное количество событий в пачке
                  window: "1s"      # Окно для отправки события.
              metrics: 
                node:
                  enabled: []           # Список включенных метрик. Включаемые: bytes-sent, connected-nodes, cql-requests, cql-client-timeouts, cql-prepared-cache-size, throttling.delay, throttling.errors, continuous-cql-requests
                  cqlMessages:          # Дополнительные настройки для метрик, если нужны:
                    highestLatency: "1s"
                    lowestLatency: "1ms"
                    refreshInterval: 5
                    significantDigits: 3
                session:                # session-level метрики, по умолчанию выключены все
                  enabled: []           # Список включенных метрик. Включаемые: bytes-sent, connected-nodes, cql-requests, cql-client-timeouts, cql-prepared-cache-size, throttling.delay, throttling.errors, continuous-cql-requests
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
              netty:                        # Настройки Netty event loop, используемой в драйвере
                adminGroup:                 # Event loop группа, используемая только для админских задач, не связанных с IO
                  shutdown:
                    quietPeriod: 2
                    timeout: 15
                    unit: SECONDS
                  size: 2
                daemon: false
                ioGroup:
                  shutdown:                 # Настройки graceful shutdown
                    quietPeriod: 2
                    timeout: 15
                    unit: SECONDS
                  size: 0                   # Количество тредов
                timer:
                  tickDuration: "100ms"     # Настройки того, как часто таймер должен пробуждаться для проверки просроченных задач
                  ticksPerWheel: 2048
              preparedStatements:
                prepareOnAllNodes: true     # Выполнять подготовку запроса на всех нодах после её успешного выполнения на одной ноде.
                preparedCache:
                  weakValues: false
                reprepareOnUp:
                  enabled: true             # Подготавливать запросы для новых нод
                  checkSystemTable: false   # Проверять наличие prepare statement в system.prepared_statements ноды перед подготовкой
                  maxParallelism: 100       # Максимальное количество конкурентных запросов
                  maxStatements: 0          # Максимальной количество запросов, которые можно переподготовить
                  timeout: "20s"
              protocol:
                compression: "lz4"            # Сжатие
                maxFrameLength: 268435456   # Максимальная длина фрейма в байтах
                version: "V4"                 # Версия протокола Cassandra
              reconnectOnInit: false        # Повторять попытку инициализации, если при первой попытке все ноды, указанные в contactpoints, не ответили
              reconnectionPolicy:           # Политика переподключения - базовая и максимальная задержка. По умолчанию, при неудачно попытке используется первое значение, затем при каждой следующей - удваивается, пока не достигнет максимального значения
                baseDelay: "1s"
                maxDelay: "60s"
              request:
                logWarnings: true
                trace:
                  attempts: 5               # Количество попыток 
                  consistency: ONE          # Уровень консистентности
                  interval: "1ms"           # Интервал между попытками
                warnIfSetKeyspace: true     # Логировать предупреждение о том, что в запросе выполняется установка keyspace 
              resolveContactPoints: false
              sessionLeak:
                threshold: 4
              socket:
                keepAlive: false
                lingerInterval: 0
                receiveBufferSize: 65535
                reuseAddress: true          # Позволять переиспользовать адрес
                sendBufferSize: 65535
                tcpNoDelay: true            # Флаг для отключения Nagle алгоритма, по умолчанию true(выключен), т.к. драйвер имеет собственный message coalescing algorithm
              sslEngineFactory:
                cipherSuites:
                  - TLS_RSA_WITH_AES_128_CBC_SHA
                  - TLS_RSA_WITH_AES_256_CBC_SHA
                hostnameValidation: true                        # Валидация имени хоста
                keystorePassword: "password"                    # Пароль от хранилища ключей
                keystorePath: "/path/to/client.keystore"        # Путь к хранилищу ключей
                truststorePassword: "password"                  # Пароль от доверенного хранилища
                truststorePath: "/path/to/client.truststore"    # Путь к доверенному хранилищу
              timestampGenerator:       # Генератор, добавляющий timestamp к каждому запросу. По умолчанию используется AtomicTimestampGenerator
                driftWarning:
                  interval: "10s"       # Интервал логирования предупреждений, есди таймстэмпы продолжают "убегать" вперёд.
                  threshold: "1s"       # Указывает, насколько далеко в будущее могут "убегать" таймстэмпы при высокой нагрузке
                forceJavaClock: false   # Принудительно использовать Java system clock
            auth:
              login: "username"
              password: "password"
            basic:
              cloud:
                secureConnectBundle: "/location/of/secure/connect/bundle"
              contactPoints:
                - "127.0.0.1:9042"
                - "127.0.0.2:9042"
              dc: "datacenter1"
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
            profiles:       # Настройки, переопределяемые в профиле
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
            telemetry:
              enabled: true
        ```

## Использование

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

Можно переопределять общие настройки, частными настройками из профиля, предположим есть такая конфигурация профиля `someProfile`:

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

Применить настройки из профиля `someProfile`, достаточно сделать следующее:

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

Настройки, указанные в профиле, будут применяться к каждому запросу, конкретно в этом случае — будет установлен таймаут в 10с.

## Конвертация

Возможно переопределять преобразование различных частей [сущности](database-common.md) и параметров запроса, для этого Kora предоставляет специальные интерфейсы.

### Результат

Если требуется преобразовать результат в ручную, предлагается использовать `CassandraResultSetMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements CassandraResultSetMapper<UUID> {

        @Override
        public UUID apply(ResultSet rows) {
            // код преобразования
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
            // код преобразования
        }
    }

    @Repository
    interface EntityRepository : CassandraRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): List<UUID>
    }
    ```

### Строка

Если требуется преобразовать строку в ручную, предлагается использовать `CassandraRowMapper`:

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

### Колонка

Если требуется преобразовать значение колонки в ручную, предлагается использовать `CassandraRowColumnMapper`:

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

### Параметр

Если требуется преобразовать значение параметра запроса в ручную, предлагается использовать `CassandraParameterColumnMapper`:

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

### Асинхронно

Из-за особенностей вспомогательного класса для извлечения данных из `AsyncResultSet` для асинхронных запросов (Mono или Suspend), можно использовать только `CassandraReactiveResultSetMapper`:

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

Есть поддержка [UDT](https://docs.datastax.com/en/cql-oss/3.3/cql/cql_using/useCreateUDT.html) 
типов с помощью `@UDT` аннотации:

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

## Сигнатуры

Доступные сигнатуры для методов репозитория из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `Void`, либо `UpdateCount`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `List<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)
    - `Mono<List<T>> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `Unit`, либо `UpdateCount`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `myMethod(): List<T>`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): List<T>?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
