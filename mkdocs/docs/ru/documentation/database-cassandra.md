---
description: "Explains Kora Cassandra repositories, Cassandra driver configuration, profiles, entity and UDT mapping, async access, and repository signatures. Use when working with @Repository, @Query, @EntityCassandra, @Table, @Id, @Column, @UDT, CassandraModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Cassandra repositories, Cassandra driver configuration, profiles, entity and UDT mapping, async access, and repository signatures; key triggers include @Repository, @Query, @EntityCassandra, @Table, @Id, @Column, @UDT, CassandraModule, CassandraRepository."
---

Модуль предоставляет реализацию репозиториев для базы данных [Cassandra](https://cassandra.apache.org/_/cassandra-basics.html) с использованием драйвера [DataStax](https://docs.datastax.com/en/developer/java-driver/4.17/).
`Cassandra` — распределенная колоночная база данных, где запросы выполняются на языке `CQL`, а схема данных обычно проектируется под конкретные сценарии чтения.
В Kora модуль Cassandra дает декларативные репозитории поверх `CqlSession`: приложение пишет `CQL`-запросы в `@Query`, а Kora во время компиляции создает код подготовки запроса, привязки параметров и преобразования результата.

Общие правила для сущностей, `@Repository`, `@Query`, макросов, пакетных запросов и аннотаций `@Table`, `@Column`, `@Id`, `@Embedded` описаны в [общем разделе про базы данных](database-common.md).
Этот документ описывает именно Cassandra-часть: подключение драйвера, конфигурацию `CqlSession`, профили выполнения, `UDT`, преобразователи и поддержанные сигнатуры методов.

Если нужен пошаговый разбор перед справочным описанием, смотрите [База данных Cassandra](../guides/database-cassandra.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-cassandra"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CassandraDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-cassandra")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CassandraDatabaseModule
    ```

## Конфигурация { #configuration }

Конфигурация читается из раздела `cassandra` и описана интерфейсом `CassandraConfig`.
Минимально нужно указать `basic.contactPoints`; остальные параметры либо необязательны, либо передаются в драйвер только когда явно заданы.

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

    1. Адреса узлов `Cassandra` для подключения к базе данных (`обязательная`, по умолчанию не указано)
    2. Имя дата-центра `Cassandra` (по умолчанию не указано, необязательно)
    3. Имя `keyspace` для подключения (по умолчанию не указано, необязательно)
    4. Ограничение времени выполнения запроса в рамках подключения (по умолчанию не указано, необязательно)
    5. Имя пользователя для подключения (по умолчанию не указано, необязательно)
    6. Пароль пользователя для подключения (по умолчанию не указано, необязательно)

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

    1. Адреса узлов `Cassandra` для подключения к базе данных (`обязательная`, по умолчанию не указано)
    2. Имя дата-центра `Cassandra` (по умолчанию не указано, необязательно)
    3. Имя `keyspace` для подключения (по умолчанию не указано, необязательно)
    4. Ограничение времени выполнения запроса в рамках подключения (по умолчанию не указано, необязательно)
    5. Имя пользователя для подключения (по умолчанию не указано, необязательно)
    6. Пароль пользователя для подключения (по умолчанию не указано, необязательно)

??? abstract "Пример полной конфигурации"

    Пример полной конфигурации с примерами значений. Описание параметров общее для `HOCON` и `YAML`.

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

    1. Имя пользователя для аутентификации в `Cassandra` (по умолчанию не указано, необязательно).
    2. Пароль пользователя для аутентификации в `Cassandra` (по умолчанию не указано, необязательно).
    3. Адреса узлов `Cassandra` в формате `host:port` (`обязательная`, по умолчанию не указано).
    4. Имя сессии драйвера, используется для логов, метрик и диагностики (по умолчанию не указано, необязательно).
    5. Локальный дата-центр для политики балансировки нагрузки (по умолчанию не указано, необязательно).
    6. `keyspace`, который будет установлен для сессии после подключения (по умолчанию не указано, необязательно).
    7. Включает избегание медленных реплик в стандартной политике балансировки нагрузки (по умолчанию не указано, необязательно).
    8. Путь или `URL` к `Secure Connect Bundle` для подключения к `DataStax Astra` / облачной Cassandra (по умолчанию не указано, необязательно).
    9. Тайм-аут обычного запроса (по умолчанию не указано, необязательно).
    10. Уровень согласованности обычного запроса, например `ONE`, `LOCAL_ONE`, `LOCAL_QUORUM`, `QUORUM`, `ALL` (по умолчанию не указано, необязательно).
    11. Размер страницы результата, то есть максимальное количество строк, запрашиваемое за один сетевой обмен (по умолчанию не указано, необязательно).
    12. Уровень последовательной согласованности для легковесных транзакций `LWT`: `SERIAL` или `LOCAL_SERIAL` (по умолчанию не указано, необязательно).
    13. Значение идемпотентности запроса по умолчанию; влияет на возможность безопасных повторов и спекулятивного выполнения (по умолчанию не указано, необязательно).
    14. Порог предупреждения об утечке сессий драйвера (по умолчанию не указано, необязательно).
    15. Тайм-аут установки сетевого соединения с узлом (по умолчанию не указано, необязательно).
    16. Тайм-аут запросов, которые драйвер выполняет при инициализации подключения (по умолчанию не указано, необязательно).
    17. Тайм-аут установки `keyspace` на подключении (по умолчанию не указано, необязательно).
    18. Максимальное количество одновременных запросов на одно подключение (по умолчанию не указано, необязательно).
    19. Максимальное количество запросов, ответ на которые больше не ожидается, но которые еще могут завершиться на стороне драйвера (по умолчанию не указано, необязательно).
    20. Логировать предупреждение при ошибке инициализации подключения к отдельному узлу (по умолчанию не указано, необязательно).
    21. Размер пула подключений к узлам локального дата-центра (по умолчанию не указано, необязательно).
    22. Размер пула подключений к удаленным узлам (по умолчанию не указано, необязательно).
    23. Разрешает повторять инициализацию, если при старте не ответили все `contactPoints` (по умолчанию не указано, необязательно).
    24. Начальная задержка политики переподключения (по умолчанию не указано, необязательно).
    25. Максимальная задержка политики переподключения (по умолчанию не указано, необязательно).
    26. Максимальное количество узлов удаленного дата-центра, которые можно использовать при аварийном переключении (по умолчанию не указано, необязательно).
    27. Разрешает аварийное переключение на удаленный дата-центр для локальных уровней согласованности (по умолчанию не указано, необязательно).
    28. Разрешенные наборы шифров для `SSL/TLS` (по умолчанию не указано, необязательно).
    29. Проверять соответствие имени узла сертификату `SSL/TLS` (по умолчанию не указано, необязательно).
    30. Путь к клиентскому хранилищу ключей (по умолчанию не указано, необязательно).
    31. Пароль клиентского хранилища ключей (по умолчанию не указано, необязательно).
    32. Путь к доверенному хранилищу сертификатов (по умолчанию не указано, необязательно).
    33. Пароль доверенного хранилища сертификатов (по умолчанию не указано, необязательно).
    34. Принудительно использовать системные часы Java для генерации временных меток запросов (по умолчанию не указано, необязательно).
    35. Порог предупреждения о дрейфе временных меток в будущее (по умолчанию не указано, необязательно).
    36. Минимальный интервал между предупреждениями о дрейфе временных меток (по умолчанию не указано, необязательно).
    37. Версия бинарного протокола Cassandra, например `V4` (по умолчанию не указано, необязательно).
    38. Алгоритм сжатия протокола, например `lz4` или `snappy` (по умолчанию не указано, необязательно).
    39. Максимальный размер фрейма протокола в байтах (по умолчанию не указано, необязательно).
    40. Логировать предупреждение, если запрос явно меняет `keyspace` (по умолчанию не указано, необязательно).
    41. Количество попыток получить трассировку запроса из Cassandra (по умолчанию не указано, необязательно).
    42. Интервал между попытками получить трассировку запроса (по умолчанию не указано, необязательно).
    43. Уровень согласованности запроса к таблицам трассировки (по умолчанию не указано, необязательно).
    44. Логировать предупреждения, которые Cassandra вернула вместе с ответом на запрос (по умолчанию не указано, необязательно).
    45. Имя генератора идентификаторов метрик драйвера (по умолчанию: `TaggingMetricIdGenerator`).
    46. Префикс имен метрик драйвера (по умолчанию не указано, необязательно).
    47. Список включенных метрик уровня узла (по умолчанию: `open-connections`, `in-flight`, `bytes-received`, `bytes-sent`, `write-timeouts`, `read-timeouts`, `aborted-requests`).
    48. Нижняя ожидаемая граница задержки для гистограммы метрики `node.cqlMessages` (по умолчанию: `1ms`).
    49. Верхняя ожидаемая граница задержки для гистограммы метрики `node.cqlMessages` (по умолчанию: `90s`).
    50. Количество значимых цифр для гистограммы метрики `node.cqlMessages` (по умолчанию не указано, необязательно).
    51. Интервал обновления снимка гистограммы метрики `node.cqlMessages` (по умолчанию не указано, необязательно).
    52. `SLO`-границы для метрики `node.cqlMessages` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    53. Список включенных метрик уровня сессии (по умолчанию: `connected-nodes`, `cql-requests`, `cql-client-timeouts`, `cql-prepared-cache-size`, `throttling.delay`, `throttling.queue-size`).
    54. Нижняя ожидаемая граница задержки для гистограммы метрики `session.cqlRequests` (по умолчанию: `1ms`).
    55. Верхняя ожидаемая граница задержки для гистограммы метрики `session.cqlRequests` (по умолчанию: `90s`).
    56. Количество значимых цифр для гистограммы метрики `session.cqlRequests` (по умолчанию не указано, необязательно).
    57. Интервал обновления снимка гистограммы метрики `session.cqlRequests` (по умолчанию не указано, необязательно).
    58. `SLO`-границы для метрики `session.cqlRequests` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    59. Нижняя ожидаемая граница задержки для гистограммы метрики `session.throttlingDelay` (по умолчанию: `1ms`).
    60. Верхняя ожидаемая граница задержки для гистограммы метрики `session.throttlingDelay` (по умолчанию: `90s`).
    61. Количество значимых цифр для гистограммы метрики `session.throttlingDelay` (по умолчанию не указано, необязательно).
    62. Интервал обновления снимка гистограммы метрики `session.throttlingDelay` (по умолчанию не указано, необязательно).
    63. `SLO`-границы для метрики `session.throttlingDelay` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    64. Публиковать гистограмму процентилей для метрик драйвера (по умолчанию: `false`).
    65. Включает `TCP_NODELAY`, то есть отключает алгоритм Nagle (по умолчанию не указано, необязательно).
    66. Включает `SO_KEEPALIVE` для TCP-сокетов (по умолчанию не указано, необязательно).
    67. Включает `SO_REUSEADDR` для TCP-сокетов (по умолчанию не указано, необязательно).
    68. Значение `SO_LINGER` для TCP-сокетов (по умолчанию не указано, необязательно).
    69. Размер буфера приема TCP-сокета в байтах (по умолчанию не указано, необязательно).
    70. Размер буфера отправки TCP-сокета в байтах (по умолчанию не указано, необязательно).
    71. Интервал отправки `heartbeat` на простаивающее подключение (по умолчанию не указано, необязательно).
    72. Тайм-аут ожидания ответа на `heartbeat` (по умолчанию не указано, необязательно).
    73. Включает загрузку и обновление метаданных схемы (по умолчанию не указано, необязательно).
    74. Тайм-аут запросов метаданных схемы (по умолчанию не указано, необязательно).
    75. Размер страницы для запросов метаданных схемы (по умолчанию не указано, необязательно).
    76. Список `keyspace`, для которых драйвер обновляет метаданные схемы (по умолчанию не указано, необязательно).
    77. Окно объединения событий обновления схемы перед обработкой (по умолчанию не указано, необязательно).
    78. Максимальное количество событий обновления схемы, которое может быть накоплено в окне (по умолчанию не указано, необязательно).
    79. Окно объединения событий изменения топологии кластера (по умолчанию не указано, необязательно).
    80. Максимальное количество событий изменения топологии, которое может быть накоплено в окне (по умолчанию не указано, необязательно).
    81. Включает карту токенов для маршрутизации запросов по владельцам данных (по умолчанию не указано, необязательно).
    82. Тайм-аут служебного `control connection` (по умолчанию не указано, необязательно).
    83. Интервал проверки достижения `schema agreement` между узлами (по умолчанию не указано, необязательно).
    84. Максимальное время ожидания `schema agreement` (по умолчанию не указано, необязательно).
    85. Логировать предупреждение, если `schema agreement` не достигнут за отведенное время (по умолчанию не указано, необязательно).
    86. Подготавливать запрос на всех узлах после успешной подготовки на одном узле (по умолчанию не указано, необязательно).
    87. Переподготавливать запросы на узле, который снова стал доступен (по умолчанию не указано, необязательно).
    88. Проверять системную таблицу `system.prepared_statements` перед переподготовкой запроса (по умолчанию не указано, необязательно).
    89. Максимальное количество запросов для переподготовки; `0` означает отсутствие ограничения в драйвере (по умолчанию не указано, необязательно).
    90. Максимальное количество параллельных запросов переподготовки (по умолчанию не указано, необязательно).
    91. Тайм-аут переподготовки запросов на одном узле (по умолчанию не указано, необязательно).
    92. Хранить значения кэша подготовленных запросов через слабые ссылки (по умолчанию не указано, необязательно).
    93. Количество потоков `Netty` для сетевого ввода-вывода; `0` позволяет драйверу выбрать значение автоматически (по умолчанию не указано, необязательно).
    94. Период тишины при штатном завершении `ioGroup` (по умолчанию не указано, необязательно).
    95. Максимальное время ожидания завершения `ioGroup` (по умолчанию не указано, необязательно).
    96. Единица измерения параметров завершения `ioGroup` (по умолчанию не указано, необязательно).
    97. Количество потоков `Netty` для административных задач драйвера (по умолчанию не указано, необязательно).
    98. Период тишины при штатном завершении `adminGroup` (по умолчанию не указано, необязательно).
    99. Максимальное время ожидания завершения `adminGroup` (по умолчанию не указано, необязательно).
    100. Единица измерения параметров завершения `adminGroup` (по умолчанию не указано, необязательно).
    101. Длительность одного шага таймера `Netty` для отложенных задач драйвера (по умолчанию не указано, необязательно).
    102. Количество шагов в кольце таймера `Netty` (по умолчанию не указано, необязательно).
    103. Делать потоки `Netty` потоками-демонами (по умолчанию не указано, необязательно).
    104. Интервал повторного планирования объединения сообщений перед отправкой (по умолчанию не указано, необязательно).
    105. Разрешать драйверу выполнять DNS-разрешение `contactPoints` при запуске (по умолчанию не указано, необязательно).
    106. Класс ограничителя запросов драйвера (по умолчанию не указано, необязательно).
    107. Максимальное количество одновременных запросов для ограничителя (по умолчанию не указано, необязательно).
    108. Максимальное количество запросов в секунду для ограничителя (по умолчанию не указано, необязательно).
    109. Максимальный размер очереди ограничителя запросов (по умолчанию не указано, необязательно).
    110. Интервал, с которым ограничитель выпускает запросы из очереди (по умолчанию не указано, необязательно).
    111. Переопределение `basic.request.timeout` для профиля `someProfile` (по умолчанию не указано, необязательно).
    112. Переопределение `basic.request.consistency` для профиля `someProfile` (по умолчанию не указано, необязательно).
    113. Переопределение `advanced.request.trace.attempts` для профиля `someProfile` (по умолчанию не указано, необязательно).
    114. Переопределение `advanced.request.trace.consistency` для профиля `someProfile` (по умолчанию не указано, необязательно).
    115. Включает логирование запросов Kora (по умолчанию: `false`).
    116. Включает метрики Kora для запросов (по умолчанию: `true`).
    117. `SLO`-границы метрик Kora (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    118. Дополнительные теги метрик Kora (по умолчанию: `{}`).
    119. Включает трассировку Kora для запросов (по умолчанию: `true`).
    120. Дополнительные атрибуты трассировки Kora (по умолчанию: `{}`).

### Ручная конфигурация { #code-configuration }

Возможно конфигурировать драйвер вручную в коде, используя `CassandraConfigurer` для модификации построителя `CqlSession`:

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

## Использование { #usage }

Для создания репозитория нужно объявить интерфейс с `@Repository` и унаследовать его от `CassandraRepository`.
Такой репозиторий получает доступ к `CqlSession` через сгенерированный код и использует `@Query` для выполнения `CQL`-запросов.
Параметры запроса связываются по имени: `:id`, `:entity.field`, `:filter.value`.

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

### Профиль { #profile }

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
Профиль применяется только к методу, над которым стоит `@CassandraProfile`; остальные методы репозитория продолжают работать с базовой конфигурацией.

## Конвертация { #mapping }

Возможно переопределять преобразование различных частей [сущности](database-common.md) и параметров запроса, для этого Kora предоставляет специальные интерфейсы.
Из коробки `CassandraModule` предоставляет преобразователи для основных типов: `String`, числовые типы, `Boolean`, `BigDecimal`, `BigInteger`, `UUID`, `ByteBuffer`, `LocalDate`, `LocalTime`, `LocalDateTime`, `ZonedDateTime` и `Instant`.
Если тип не входит в этот набор или требуется нестандартное представление значения в `CQL`, можно добавить собственный преобразователь через `@Mapping`.

### Результат { #result }

Если требуется преобразовать весь синхронный результат запроса вручную, используется `CassandraResultSetMapper<T>`.
Он получает `ResultSet` и возвращает значение метода репозитория: один объект, список, `Optional<T>` или другой поддержанный тип.

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements CassandraResultSetMapper<UUID> {

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

    Для Kotlin писать преобразователи надо только для `T?` типов, так в интерфейсах тип указан как `@Nullable`.

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

### Строка { #row }

Если требуется преобразовать одну строку результата, используется `CassandraRowMapper<T>`.
Такой преобразователь применяется к каждой строке и подходит для возвращаемого значения `T`, `Optional<T>`, `List<T>`, `Flux<T>` и `Flow<T>`.

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

    Для Kotlin писать преобразователи надо только для `T?` типов, так в интерфейсах тип указан как `@Nullable`.

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

### Колонка { #column }

Если требуется преобразовать значение колонки вручную, предлагается использовать `CassandraRowColumnMapper`:

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

    Для Kotlin писать преобразователи надо только для `T?` типов, так в интерфейсах тип указан как `@Nullable`.

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

### Параметр { #parameter }

Если требуется преобразовать значение параметра запроса вручную, используется `CassandraParameterColumnMapper<T>`.
Он получает `SettableByName<?>`, индекс параметра и значение из метода репозитория.

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

    Для Kotlin писать преобразователи надо только для `T?` типов, так в интерфейсах тип указан как `@Nullable`.

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

### Асинхронно { #async }

Для `CompletionStage<T>` используется `CassandraAsyncResultSetMapper<T>`, который получает `AsyncResultSet` и возвращает `CompletionStage<T>`.
Для реактивных типов `Mono<T>` / `Flux<T>` используется `CassandraReactiveResultSetMapper<T, P>`, который получает `ReactiveResultSet` и возвращает нужный `Publisher`.

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

Есть поддержка [UDT](https://docs.datastax.com/en/cql-oss/3.3/cql/cql_using/useCreateUDT.html) типов с помощью аннотации `@UDT`.
`UDT` описывает пользовательский тип Cassandra и может использоваться как поле обычной сущности.

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

Если тип используется не как возвращаемое значение репозитория, а как отдельный Cassandra-тип, для него можно явно включить генерацию преобразователей аннотацией `@EntityCassandra`.
Это полезно, когда преобразователь нужен как отдельный компонент графа.

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

## Сигнатуры { #signatures }

Доступные сигнатуры для методов репозитория из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, `List<T>` или `Void`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

    В параметры метода можно передавать обычные значения, DTO, `@Batch List<T>` для пакетного выполнения и `CqlSession`, если методу нужен доступ к текущей сессии драйвера.

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, `T?`, `List<T>` или `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

    В параметры метода можно передавать обычные значения, DTO, `@Batch List<T>` для пакетного выполнения и `CqlSession`, если методу нужен доступ к текущей сессии драйвера.
