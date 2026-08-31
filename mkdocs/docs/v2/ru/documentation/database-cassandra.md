---
description: "Explains Kora Cassandra repositories, Cassandra driver configuration, execution profiles, entity and UDT mapping, manual CQL queries, and repository signatures. Use when working with @Repository, @Query, @EntityCassandra, @Table, @Id, @Column, @UDT, CassandraDatabaseModule, CassandraExecutor."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Cassandra repositories, Cassandra driver configuration, execution profiles, entity and UDT mapping, manual CQL queries via CassandraQuery, and repository signatures; key triggers include @Repository, @Query, @EntityCassandra, @Table, @Id, @Column, @UDT, @CassandraProfile, CassandraDatabaseModule, CassandraRepository, CassandraExecutor, CassandraSession."
---

Модуль предоставляет реализацию репозитория для базы данных [Cassandra](https://cassandra.apache.org/_/cassandra-basics.html)
поверх [Java-драйвера Cassandra](https://docs.datastax.com/en/developer/java-driver/4.17/) (`org.apache.cassandra:java-driver-core` версии `4.19.3`, подключается модулем транзитивно).
`Cassandra` — это распределенная колоночная база данных, где запросы пишутся на `CQL`, а модель данных обычно проектируется под конкретные сценарии чтения.
В Kora модуль Cassandra предоставляет декларативные репозитории поверх `CqlSession`: приложение пишет `CQL`-запросы в `@Query`, а Kora на этапе компиляции генерирует код подготовки запроса, связывания параметров и отображения результата.

Общие правила для отображений, `@Repository`, `@Query`, макросов, пакетных запросов и аннотаций `@Table`, `@Column`, `@Id`, `@Embedded` описаны в разделе [общих правил работы с базами данных](database-common.md).
Этот документ охватывает специфичные для Cassandra части: подключение драйвера, конфигурацию `CqlSession`, профили выполнения, `UDT`, отображатели и поддерживаемые сигнатуры методов.

Пошаговый разбор перед справочным описанием смотрите в разделе [База данных Cassandra](../guides/database-cassandra.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:database-cassandra"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CassandraDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:database-cassandra")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CassandraDatabaseModule
    ```

`CassandraDatabaseModule` наследует `CassandraMapperModule`, поэтому стандартные отображатели строк, столбцов и параметров подключаются вместе с ним.
Модуль регистрирует компонент `CassandraSession`, который владеет драйверной `CqlSession`: она открывается при старте графа приложения и закрывается при остановке.
`CassandraSession` является `Wrapped<CqlSession>`, поэтому саму `CqlSession` также можно внедрить в любой компонент напрямую.

## Конфигурация { #configuration }

Конфигурация читается из секции `cassandra` и описывается интерфейсом `CassandraConfig`.
Как минимум необходимо указать `basic.contactPoints`. Остальные параметры необязательны или передаются драйверу только при явной настройке.

Пример простой конфигурации:

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

    1. Адреса узлов `Cassandra` для подключения к базе данных (`обязательный`, без значения по умолчанию)
    2. Имя датацентра `Cassandra` (по умолчанию не указано, необязательно)
    3. Имя `keyspace` для подключения (по умолчанию не указано, необязательно)
    4. Таймаут выполнения запроса для подключения (по умолчанию не указано, необязательно)
    5. Имя пользователя для подключения (по умолчанию не указано, необязательно)
    6. Пароль для подключения (по умолчанию не указано, необязательно)

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

    1. Адреса узлов `Cassandra` для подключения к базе данных (`обязательный`, без значения по умолчанию)
    2. Имя датацентра `Cassandra` (по умолчанию не указано, необязательно)
    3. Имя `keyspace` для подключения (по умолчанию не указано, необязательно)
    4. Таймаут выполнения запроса для подключения (по умолчанию не указано, необязательно)
    5. Имя пользователя для подключения (по умолчанию не указано, необязательно)
    6. Пароль для подключения (по умолчанию не указано, необязательно)

??? abstract "Пример полной конфигурации"

    Полная конфигурация с примерами значений. Описания параметров общие для примеров `HOCON` и `YAML`.

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

    1. Имя пользователя для аутентификации в `Cassandra` (по умолчанию не указано, необязательно).
    2. Пароль для аутентификации в `Cassandra` (по умолчанию не указано, необязательно).
    3. Адреса узлов `Cassandra` в формате `host:port` (`обязательный`, без значения по умолчанию).
    4. Имя сессии драйвера, используемое в логах, метриках и диагностике (по умолчанию не указано, необязательно).
    5. Локальный датацентр для политики балансировки нагрузки (по умолчанию не указано, необязательно).
    6. `keyspace`, который будет установлен для сессии после подключения (по умолчанию не указано, необязательно).
    7. Включает избегание медленных реплик в политике балансировки нагрузки по умолчанию (по умолчанию не указано, необязательно).
    8. Путь или `URL` к `Secure Connect Bundle` для подключения к `DataStax Astra` / облачной Cassandra (по умолчанию не указано, необязательно).
    9. Таймаут обычного запроса (по умолчанию не указано, необязательно).
    10. Уровень согласованности обычного запроса, например `ONE`, `LOCAL_ONE`, `LOCAL_QUORUM`, `QUORUM`, `ALL` (по умолчанию не указано, необязательно).
    11. Размер страницы результата, то есть максимальное количество строк, запрашиваемых за один сетевой обмен (по умолчанию не указано, необязательно).
    12. Уровень последовательной согласованности для легковесных транзакций `LWT`: `SERIAL` или `LOCAL_SERIAL` (по умолчанию не указано, необязательно).
    13. Значение идемпотентности запроса по умолчанию; влияет на то, можно ли безопасно применять повторы и спекулятивное выполнение (по умолчанию не указано, необязательно).
    14. Порог предупреждения об утечке сессий драйвера (по умолчанию не указано, необязательно).
    15. Таймаут открытия сетевого соединения с узлом (по умолчанию не указано, необязательно).
    16. Таймаут запросов, которые драйвер выполняет при инициализации соединения (по умолчанию не указано, необязательно).
    17. Таймаут установки `keyspace` на соединении (по умолчанию не указано, необязательно).
    18. Максимальное количество одновременных запросов на одно соединение (по умолчанию не указано, необязательно).
    19. Максимальное количество запросов, ответ на которые больше не ожидается, но которые еще могут завершиться внутри драйвера (по умолчанию не указано, необязательно).
    20. Логирует предупреждение, когда инициализация соединения с отдельным узлом завершилась неудачей (по умолчанию не указано, необязательно).
    21. Размер пула соединений для узлов локального датацентра (по умолчанию не указано, необязательно).
    22. Размер пула соединений для удаленных узлов (по умолчанию не указано, необязательно).
    23. Разрешает повторную попытку инициализации, когда все `contactPoints` не отвечают во время запуска (по умолчанию не указано, необязательно).
    24. Начальная задержка политики переподключения (по умолчанию не указано, необязательно).
    25. Максимальная задержка политики переподключения (по умолчанию не указано, необязательно).
    26. Максимальное количество узлов удаленного датацентра, которые могут использоваться для отказоустойчивого переключения (по умолчанию не указано, необязательно).
    27. Разрешает переключение на удаленный датацентр для локальных уровней согласованности (по умолчанию не указано, необязательно).
    28. Разрешенные наборы шифров для `SSL/TLS` (по умолчанию не указано, необязательно).
    29. Проверяет, что имя хоста узла совпадает с сертификатом `SSL/TLS` (по умолчанию не указано, необязательно).
    30. Путь к клиентскому keystore (по умолчанию не указано, необязательно).
    31. Пароль клиентского keystore (по умолчанию не указано, необязательно).
    32. Путь к truststore (по умолчанию не указано, необязательно).
    33. Пароль truststore (по умолчанию не указано, необязательно).
    34. Принудительно использует системные часы Java для генерации временных меток запросов (по умолчанию не указано, необязательно).
    35. Порог предупреждения о смещении временных меток в будущее (по умолчанию не указано, необязательно).
    36. Минимальный интервал между предупреждениями о смещении временных меток (по умолчанию не указано, необязательно).
    37. Версия бинарного протокола Cassandra, например `V4` (по умолчанию не указано, необязательно).
    38. Алгоритм сжатия протокола, например `lz4` или `snappy` (по умолчанию не указано, необязательно).
    39. Максимальный размер кадра протокола в байтах (по умолчанию не указано, необязательно).
    40. Логирует предупреждение, когда запрос явно меняет `keyspace` (по умолчанию не указано, необязательно).
    41. Количество попыток получить информацию трассировки запроса из Cassandra (по умолчанию не указано, необязательно).
    42. Интервал между попытками получить информацию трассировки запроса (по умолчанию не указано, необязательно).
    43. Уровень согласованности для запросов к таблицам трассировки (по умолчанию не указано, необязательно).
    44. Логирует предупреждения, возвращаемые Cassandra вместе с ответом на запрос (по умолчанию не указано, необязательно).
    45. Имя генератора идентификаторов метрик драйвера (по умолчанию: `TaggingMetricIdGenerator`).
    46. Префикс имен метрик драйвера (по умолчанию не указано, необязательно).
    47. Включенные метрики драйвера уровня узла (по умолчанию: `open-connections`, `in-flight`, `bytes-received`, `bytes-sent`, `write-timeouts`, `read-timeouts`, `aborted-requests`).
    48. Наименьшая ожидаемая задержка для гистограммы метрики `node.cqlMessages` (по умолчанию: `1ms`).
    49. Наибольшая ожидаемая задержка для гистограммы метрики `node.cqlMessages` (по умолчанию: `90s`).
    50. Количество значащих цифр для гистограммы метрики `node.cqlMessages` (по умолчанию не указано, необязательно).
    51. Интервал обновления снимка гистограммы метрики `node.cqlMessages` (по умолчанию не указано, необязательно).
    52. Границы `SLO` для метрики `node.cqlMessages` (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    53. Включенные метрики драйвера уровня сессии (по умолчанию: `connected-nodes`, `cql-requests`, `cql-client-timeouts`, `cql-prepared-cache-size`, `throttling.delay`, `throttling.queue-size`).
    54. Наименьшая ожидаемая задержка для гистограммы метрики `session.cqlRequests` (по умолчанию: `1ms`).
    55. Наибольшая ожидаемая задержка для гистограммы метрики `session.cqlRequests` (по умолчанию: `90s`).
    56. Количество значащих цифр для гистограммы метрики `session.cqlRequests` (по умолчанию не указано, необязательно).
    57. Интервал обновления снимка гистограммы метрики `session.cqlRequests` (по умолчанию не указано, необязательно).
    58. Границы `SLO` для метрики `session.cqlRequests` (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    59. Наименьшая ожидаемая задержка для гистограммы метрики `session.throttlingDelay` (по умолчанию: `1ms`).
    60. Наибольшая ожидаемая задержка для гистограммы метрики `session.throttlingDelay` (по умолчанию: `90s`).
    61. Количество значащих цифр для гистограммы метрики `session.throttlingDelay` (по умолчанию не указано, необязательно).
    62. Интервал обновления снимка гистограммы метрики `session.throttlingDelay` (по умолчанию не указано, необязательно).
    63. Границы `SLO` для метрики `session.throttlingDelay` (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    64. Публикует перцентильные гистограммы для метрик драйвера (по умолчанию: `false`).
    65. Включает `TCP_NODELAY`, отключающий алгоритм Нейгла (по умолчанию не указано, необязательно).
    66. Включает `SO_KEEPALIVE` для TCP-сокетов (по умолчанию не указано, необязательно).
    67. Включает `SO_REUSEADDR` для TCP-сокетов (по умолчанию не указано, необязательно).
    68. Значение `SO_LINGER` для TCP-сокетов (по умолчанию не указано, необязательно).
    69. Размер буфера приема TCP-сокета в байтах (по умолчанию не указано, необязательно).
    70. Размер буфера отправки TCP-сокета в байтах (по умолчанию не указано, необязательно).
    71. Интервал отправки `heartbeat` по простаивающему соединению (по умолчанию не указано, необязательно).
    72. Таймаут ожидания ответа на `heartbeat` (по умолчанию не указано, необязательно).
    73. Включает загрузку и обновление метаданных схемы (по умолчанию не указано, необязательно).
    74. Таймаут запросов метаданных схемы (по умолчанию не указано, необязательно).
    75. Размер страницы для запросов метаданных схемы (по умолчанию не указано, необязательно).
    76. Список имен `keyspace`, метаданные схемы которых обновляет драйвер (по умолчанию не указано, необязательно).
    77. Окно объединения событий обновления схемы перед обработкой (по умолчанию не указано, необязательно).
    78. Максимальное количество событий обновления схемы, которые могут накопиться в окне (по умолчанию не указано, необязательно).
    79. Окно объединения событий изменения топологии кластера (по умолчанию не указано, необязательно).
    80. Максимальное количество событий изменения топологии, которые могут накопиться в окне (по умолчанию не указано, необязательно).
    81. Включает карту токенов для маршрутизации запросов по владельцам данных (по умолчанию не указано, необязательно).
    82. Таймаут служебного `control connection` (по умолчанию не указано, необязательно).
    83. Интервал проверки `schema agreement` между узлами (по умолчанию не указано, необязательно).
    84. Максимальное время ожидания `schema agreement` (по умолчанию не указано, необязательно).
    85. Логирует предупреждение, если `schema agreement` не достигнут вовремя (по умолчанию не указано, необязательно).
    86. Подготавливает запрос на всех узлах после успешной подготовки на одном узле (по умолчанию не указано, необязательно).
    87. Повторно подготавливает запросы на узле, который снова стал доступен (по умолчанию не указано, необязательно).
    88. Проверяет системную таблицу `system.prepared_statements` перед повторной подготовкой запроса (по умолчанию не указано, необязательно).
    89. Максимальное количество запросов для повторной подготовки; `0` означает отсутствие ограничения со стороны драйвера (по умолчанию не указано, необязательно).
    90. Максимальное количество параллельных запросов повторной подготовки (по умолчанию не указано, необязательно).
    91. Таймаут повторной подготовки запросов на одном узле (по умолчанию не указано, необязательно).
    92. Хранит значения кэша подготовленных запросов через слабые ссылки (по умолчанию не указано, необязательно).
    93. Количество потоков `Netty` для сетевого ввода-вывода; `0` позволяет драйверу выбрать автоматически (по умолчанию не указано, необязательно).
    94. Период затишья для плавной остановки `ioGroup` (по умолчанию не указано, необязательно).
    95. Максимальное время ожидания остановки `ioGroup` (по умолчанию не указано, необязательно).
    96. Единица измерения для параметров остановки `ioGroup` (по умолчанию не указано, необязательно).
    97. Количество потоков `Netty` для административных задач драйвера (по умолчанию не указано, необязательно).
    98. Период затишья для плавной остановки `adminGroup` (по умолчанию не указано, необязательно).
    99. Максимальное время ожидания остановки `adminGroup` (по умолчанию не указано, необязательно).
    100. Единица измерения для параметров остановки `adminGroup` (по умолчанию не указано, необязательно).
    101. Длительность одного тика таймера `Netty` для отложенных задач драйвера (по умолчанию не указано, необязательно).
    102. Количество тиков в колесе таймера `Netty` (по умолчанию не указано, необязательно).
    103. Делает потоки `Netty` демон-потоками (по умолчанию не указано, необязательно).
    104. Интервал перепланирования для объединения сообщений перед отправкой (по умолчанию не указано, необязательно).
    105. Разрешает драйверу разрешать `contactPoints` через DNS во время запуска (по умолчанию не указано, необязательно).
    106. Класс ограничителя запросов драйвера (по умолчанию не указано, необязательно).
    107. Максимальное количество одновременных запросов для ограничителя (по умолчанию не указано, необязательно).
    108. Максимальное количество запросов в секунду для ограничителя (по умолчанию не указано, необязательно).
    109. Максимальный размер очереди запросов ограничителя (по умолчанию не указано, необязательно).
    110. Интервал, с которым ограничитель освобождает запросы из очереди (по умолчанию не указано, необязательно).
    111. Переопределение `basic.request.timeout` для профиля `someProfile` (по умолчанию не указано, необязательно).
    112. Переопределение `basic.request.consistency` для профиля `someProfile` (по умолчанию не указано, необязательно).
    113. Переопределение `advanced.request.trace.attempts` для профиля `someProfile` (по умолчанию не указано, необязательно).
    114. Переопределение `advanced.request.trace.consistency` для профиля `someProfile` (по умолчанию не указано, необязательно).
    115. Включает логирование запросов Kora (по умолчанию: `false`).
    116. Включает метрики запросов Kora (по умолчанию: `false`).
    117. Регистрирует собственные метрики драйвера в `MeterRegistry` приложения; при выключении весь блок `advanced.metrics` не имеет эффекта (по умолчанию: `true`).
    118. Границы `SLO` метрик Kora (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    119. Дополнительные теги метрик Kora (по умолчанию: `{}`).
    120. Включает трассировку запросов Kora (по умолчанию: `true`).
    121. Дополнительные атрибуты трассировки Kora (по умолчанию: `{}`).

### Конфигурация в коде { #code-configuration }

Не каждая опция драйвера доступна через секцию `cassandra`. Недостающее можно задать в коде компонентами `Configurer`:

- `Configurer<CqlSessionBuilder>` — меняет сам построитель сессии, например идентификатор клиента, собственный реестр кодеков или слушатель состояния узлов;
- `Configurer<ProgrammaticDriverConfigLoaderBuilder>` — записывает низкоуровневые опции драйвера в загрузчик конфигурации, который Kora собирает из секции `cassandra`.

Оба компонента необязательны и оба применяются последними, после всего прочитанного из конфигурации, поэтому заданное здесь значение побеждает:

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

`Configurer` — это `io.koraframework.common.Configurer`, контракт с единственным методом `T configure(T t)`.

### Несколько кластеров { #multiple-clusters }

`CassandraDatabaseModule` собирает свою сессию из секции `cassandra`, объявляя `CassandraDatabaseFactoryModule("cassandra")`.
Второй кластер добавляется объявлением еще одного фабричного модуля со своим путем конфигурации и своим тегом,
а репозитории выбирают его через `@Repository(executorTag = …)`:

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

    1.  Секция файла конфигурации, описывающая этот кластер; она имеет ту же структуру, что и секция `cassandra`.

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

    1.  Секция файла конфигурации, описывающая этот кластер; она имеет ту же структуру, что и секция `cassandra`.

Тег фабричного модуля распространяется на все, что он создает, поэтому компоненты `Configurer` для такого кластера должны иметь тот же тег.
Репозиториям, работающим с основным подключением, тег не нужен.
Общие правила описаны в разделе [общих правил работы с базами данных](database-common.md#multiple-databases).

## Использование { #usage }

Чтобы создать репозиторий, объявите интерфейс с `@Repository` и унаследуйте `CassandraRepository`.
Такой репозиторий получает доступ к `CqlSession` через сгенерированный код и использует `@Query` для выполнения `CQL`-запросов.
Параметры запроса связываются по имени: `:id`, `:entity.field`, `:filter.value`.

Отображения описываются с помощью [общих аннотаций баз данных](database-common.md) и помечаются `@EntityCassandra`,
чтобы `Kora` сгенерировала отображатель на этапе компиляции (см. [Отображение](#view)):

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

    1.  Использует макрос `%{return#selects}` и `%{return#table}`. Разворачивается в запрос:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        WHERE id = :id
        ```
        Метод использует макросы для `SELECT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)
    2.  Поля перечислены вручную без использования макросов — это допустимо, но требует поддержки при изменении отображения.
    3.  Использует макрос `%{entity#inserts}`. Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
        ```
        Метод использует макросы для `INSERT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)

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

    1.  Использует макрос `%{return#selects}` и `%{return#table}`. Разворачивается в запрос:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        WHERE id = :id
        ```
        Метод использует макросы для `SELECT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)
    2.  Поля перечислены вручную без использования макросов — это допустимо, но требует поддержки при изменении отображения.
    3.  Использует макрос `%{entity#inserts}`. Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
        ```
        Метод использует макросы для `INSERT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)

`CQL` остается под контролем разработчика: вы сами пишете текст запроса, тогда как `Kora` берет на себя только связывание параметров,
выполнение запроса и отображение результата.
Общие правила для отображений, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch` и макросов описаны в разделе
[Общие правила работы с базами данных](database-common.md#macros).

**Связывание параметров:** Kora выполняет типизированное внедрение аргументов в CQL-запрос на этапе компиляции.
Именованные подстановки (`:id`, `:entity.field1`) переписываются в позиционные `?`, а сгенерированный код связывает каждое значение
через драйвер, например `_stmt.setString(0, id)`, где индекс соответствует порядку параметра в запросе.
Это обеспечивает безопасность (защита от CQL-инъекций) и производительность (использование подготовленных запросов драйвером).

В отличие от реляционных баз данных, в `Cassandra` нет транзакций.
Когда нужно, чтобы несколько операторов применились атомарно, используйте `@Batch`-метод: Kora строит `UNLOGGED` `CQL` `BATCH`
и связывает по одному оператору на каждый элемент аргумента `@Batch List<T>`.
Его семантика и макросы описаны в разделе [общих правил работы с базами данных](database-common.md#batch-query).

### Профиль { #profile }

Можно переопределить общие настройки частными настройками из профиля. Предположим, есть такая конфигурация профиля `someProfile`:

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

Чтобы применить настройки из профиля `someProfile`, достаточно сделать следующее:

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

Настройки, указанные в профиле, будут применяться к каждому запросу, в частности в данном случае будет установлен таймаут 10s.
Профиль применяется только к методу, помеченному `@CassandraProfile`; остальные методы репозитория продолжают использовать базовую конфигурацию.
Под капотом сгенерированный код вызывает `setExecutionProfileName("someProfile")` у оператора, поэтому имя профиля должно существовать в секции `cassandra.profiles`.

## Отображение { #mapping }

Можно переопределить отображение различных частей [отображения](database-common.md) и параметров запроса — `Kora` предоставляет для этого специальные интерфейсы.
Из коробки `CassandraMapperModule` предоставляет отображатели для `String`, `Byte`, `Short`, `Integer`, `Long`, `Float`, `Double`, `Boolean`,
`BigDecimal`, `BigInteger`, `UUID`, `ByteBuffer`, `byte[]`, `LocalTime`, `LocalDate`, `LocalDateTime`, `ZonedDateTime`, `Instant` и `CqlDuration`.
Если тип не входит в этот набор или ему нужно особое представление в `CQL`, добавьте собственный отображатель через `@Mapping`.

Отображатель с зависимостями в конструкторе должен быть объявлен как `@Component`, чтобы контейнер мог его собрать.
Отображатель без зависимостей аннотировать `@Component` нельзя — Kora создает его сама, а лишнее объявление компонента завершает сборку ошибкой `Multiple components match`.

### Отображение { #view }

Используйте аннотацию `@EntityCassandra` для оптимального отображения.
Аннотация позволяет обработчику аннотаций сгенерировать все необходимые отображатели за **один раунд** аннотационной обработки:
`CassandraRowMapper<T>`, `CassandraResultSetMapper<T>` для одиночного результата и `CassandraResultSetMapper<List<T>>` для списка.
Без этой аннотации отображатели генерируются по требованию, что может потребовать **множества раундов** обработки и значительно увеличить время компиляции.
Это рекомендуемый способ отображения каждого типа, возвращаемого из репозитория или связываемого в нем.

Ожидается, что все вложенные отображения и типы [UDT](#udt) также используют эту аннотацию.
`@EntityCassandra` применима только к record-ам и классам в стиле Java bean (`data class` в Kotlin).

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

### Результат { #result }

Если нужно вручную преобразовать весь результат синхронного запроса, используйте `CassandraResultSetMapper<T>`.
Он получает `ResultSet` и возвращает значение метода репозитория: одиночный объект, список, `Optional<T>` или другой поддерживаемый тип.

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

Каждый интерфейс отображателя результата также предоставляет статические фабричные методы, которые строят полный отображатель результата из `CassandraRowMapper<T>`,
так что один отображатель строки можно переиспользовать в разных сигнатурах:

- `CassandraResultSetMapper` — `singleResultSetMapper`, `optionalResultSetMapper`, `listResultSetMapper`;
- `CassandraAsyncResultSetMapper` — `one`, `list` (автоматически проходит по страницам результата).

`CassandraMapperModule` дополнительно выводит `CassandraResultSetMapper<Optional<T>>` из любого `CassandraRowMapper<T>` в графе,
поэтому сигнатурам с `Optional<T>` отдельный отображатель не нужен.

### Строка { #row }

Если нужно вручную преобразовать одну строку результата, используйте `CassandraRowMapper<T>`.
Этот отображатель применяется к каждой строке и подходит для возвращаемых значений вида `T`, `Optional<T>` и `List<T>`.

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

### Столбец { #column }

Если нужно вручную преобразовать значение столбца, используйте `CassandraRowColumnMapper`:

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

Через `CassandraRowColumnMapper` читается и тип `@UDT`, поэтому этим же интерфейсом можно взять отображение пользовательского типа под собственный контроль.

### Параметр { #parameter }

Если нужно вручную преобразовать значение параметра запроса, используйте `CassandraParameterColumnMapper<T>`.
Он получает `SettableByName<?>`, индекс параметра и значение из метода репозитория.
Значение может быть `null`, поэтому реализация сама отвечает за то, чтобы не записывать ничего в подстановку, когда записывать нечего.

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

### Асинхронный { #async }

Методы репозитория на Java могут возвращать `CompletionStage<T>` или `CompletableFuture<T>`.
Для таких методов Kora выполняет оператор через `CqlSession#executeAsync` и отображает результат с помощью `CassandraAsyncResultSetMapper<T>`,
который получает `AsyncResultSet` и возвращает `CompletionStage<T>`.

Для отображения с `@EntityCassandra` дополнительный отображатель не нужен: Kora выводит асинхронный отображатель из сгенерированного `CassandraRowMapper<T>`,
используя `CassandraAsyncResultSetMapper.list(...)` для результата `List<T>` и `CassandraAsyncResultSetMapper.one(...)` в остальных случаях.
Метод `list` проходит по страницам результата, запрашивая следующую, пока набор не закончится, поэтому `List<T>` соберет все страницы до завершения future;
`one` отображает только первую строку.

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

Собственный асинхронный отображатель подключается так же, как синхронный, через `@Mapping`:

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

У репозиториев на Kotlin асинхронных сигнатур нет: методы синхронные и используют `CassandraResultSetMapper` / `CassandraRowMapper`,
см. [Результат](#result) и [Сигнатуры](#signatures).

## Ручной запрос { #query }

Если запрос сложно выразить одной статической `@Query`, вы можете объявить обычный метод с реализацией и построить `CQL` вручную.
Репозиторий предоставляет `executor()`, который возвращает `CassandraExecutor`:

- `currentSession()` — активная драйверная `CqlSession`;
- `telemetry()` — `DatabaseTelemetry`, используемая для отчетности;
- `query(CassandraQuery, CassandraResultSetMapper<T>)`, `queryOne(...)`, `queryOptional(...)`, `queryList(...)` — выполняют построенный запрос и отображают результат;
- `query(CassandraQuery, Function<BoundStatement, T>)` — выполняет построенный запрос и отдает связанный оператор вам;
- `query(QueryContext, Function<PreparedStatement, T>)` — самый низкий уровень: подготавливает сырую строку `CQL`, все остальное делаете вы.

Каждый из них оборачивает вызов в телеметрию `Kora`, поэтому ручной запрос логируется, измеряется и трассируется точно так же, как сгенерированный.

`CQL` собирается построителем `CassandraQuery`, который держит текст запроса и значения параметров раздельно:

- `CassandraQuery.named()` — `CQL` с подстановками `:name`, значения задаются через `bind(name, value)`, `bindAll(map)`, `bindIn(name, values)` для конструкций `IN (:name)`
  и условные формы `cqlIf`, `bindIf`, `bindInIf`;
- `CassandraQuery.template()` и `CassandraQuery.template(cql, args...)` — `CQL`, в котором уже используются позиционные подстановки `?`;
- `opts(...)` — параметры конкретного оператора: `consistencyLevel`, `serialConsistencyLevel`, `pageSize`, `timeout`, `idempotent`, `tracing`.

`build()` проверяет запрос и завершается `IllegalArgumentException`, если подстановка не связана, если связанный параметр нигде не используется в `CQL`
или если коллекция `bindIn` пуста.
Именованные параметры преобразуются в позиционные `?`, поэтому драйвер по-прежнему получает подготовленный запрос, а значения никогда не подставляются в текст запроса.

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

Когда нужен полный контроль над подготовкой оператора, используйте перегрузку с `QueryContext`.
`QueryContext` содержит идентификатор запроса, исполняемый `CQL` и имя операции:
идентификатор попадает в телеметрию как атрибут `db.query.text`, а имя операции становится именем спана,
поэтому используйте стабильное значение вида `Repository.method` — именно так делают сгенерированные репозитории.
Конструктор с двумя аргументами подставляет операцию `db_query`.

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

Поскольку в `Cassandra` нет транзакций, `query` просто выполняется на текущей сессии с телеметрией; здесь нет фиксации или отката, которыми нужно управлять.

## UDT { #udt }

Поддерживаются типы [UDT](https://docs.datastax.com/en/cql-oss/3.3/cql/cql_using/useCreateUDT.html) через аннотацию `@UDT`.
`UDT` описывает пользовательский тип Cassandra и может использоваться как поле обычного отображения.
Для каждого типа `@UDT` Kora генерирует чтение и запись, поэтому тип работает и в результатах, и как параметр запроса,
включая вложенные типы `@UDT` и `List<T>` из типа `@UDT`.
Тип `@UDT` отображается как любое другое отображение, поэтому охватывающее отображение помечается `@EntityCassandra`.

Для следующей схемы, где `username` — пользовательский тип, хранящийся в столбце `FROZEN`:

```cql
CREATE TYPE IF NOT EXISTS username(first text, last text);

CREATE TABLE IF NOT EXISTS entities_udt
(
    id   VARCHAR,
    name FROZEN<username>,
    PRIMARY KEY (id)
);
```

отображение и репозиторий выглядят так:

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

Если тип `UDT` используется не через охватывающее отображение, а сам является результатом запроса, добавьте `@EntityCassandra` рядом с `@UDT`.
Одна `@UDT` генерирует чтение и запись столбца; `@EntityCassandra` дополнительно генерирует отображатели строки и результата,
а именно они нужны методу репозитория, возвращающему такой тип.

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

### Макросы { #macros }

Для упрощения написания `CQL`-запросов используйте макросы — они разворачиваются в `CQL`-конструкции на этапе компиляции.
Примеры использования показаны выше в секции [Использование](#usage) (методы `findById` и `insert`).

**Подробная документация:** [Общие правила работы с базами данных — Макросы](database-common.md#macros)

## Сигнатуры { #signatures }

Доступные из коробки сигнатуры методов репозитория:

===! ":fontawesome-brands-java: `Java`"

    `T` означает тип возвращаемого значения, либо `List<T>`, либо `Void`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `CompletableFuture<T> myMethod()` [CompletableFuture](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html)

    Обертки `CompletionStage<T>` и `CompletableFuture<T>` также могут оборачивать `List<T>` или `Void`,
    например `CompletionStage<List<Entity>>` или `CompletableFuture<Void>`.

    Параметры метода могут включать обычные значения, DTO, `@Batch List<T>` для пакетного выполнения и `CqlSession`, когда методу нужен доступ к текущей сессии драйвера.

=== ":simple-kotlin: `Kotlin`"

    `T` означает тип возвращаемого значения, либо `T?`, либо `List<T>`, либо `Unit`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `myMethod(): List<T>`
    - `myMethod()` для запроса без результата

    Методы репозитория на Kotlin синхронные. Метод `suspend`, помеченный `@Query`, отклоняется процессором символов
    с сообщением `Suspend methods are not supported by the repository generator` — выполняйте блокирующий вызов, а конкурентность стройте над репозиторием.

    Параметры метода могут включать обычные значения, DTO, `@Batch List<T>` для пакетного выполнения и `CqlSession`, когда методу нужен доступ к текущей сессии драйвера.

Реактивные возвращаемые типы не поддерживаются: сигнатур `Mono` / `Flux` нет, реактивного отображателя результата в модуле тоже нет.

## Телеметрия { #telemetry }

Логирование, метрики и трассировка настраиваются через блок `telemetry` в [конфигурации](#configuration) и описаны в разделе [Справочник метрик](metrics.md#database).
По умолчанию логирование и метрики запросов выключены (`telemetry.logging.enabled = false`, `telemetry.metrics.enabled = false`), а трассировка включена (`telemetry.tracing.enabled = true`).
Собственные метрики драйвера управляются отдельно ключом `telemetry.metrics.driverMetrics` и настраиваются блоком `advanced.metrics`.
Чтобы переопределить телеметрию полностью, можно предоставить собственные SPI-фабрики, подробнее в [Общей документации по Базам данных](database-common.md#telemetry).
