---
description: "Explains Kora Cassandra repositories, Cassandra driver configuration, profiles, entity and UDT mapping, async access, and repository signatures. Use when working with @Repository, @Query, @EntityCassandra, @Table, @Id, @Column, @UDT, CassandraModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Cassandra repositories, Cassandra driver configuration, profiles, entity and UDT mapping, async access, and repository signatures; key triggers include @Repository, @Query, @EntityCassandra, @Table, @Id, @Column, @UDT, CassandraModule, CassandraRepository."
---

Модуль предоставляет реализацию репозитория для базы данных [Cassandra](https://cassandra.apache.org/_/cassandra-basics.html) с использованием драйвера [DataStax](https://docs.datastax.com/en/developer/java-driver/4.17/).
`Cassandra` — это распределенная колоночная база данных, где запросы пишутся на `CQL`, а модель данных обычно проектируется под конкретные сценарии чтения.
В Kora модуль Cassandra предоставляет декларативные репозитории поверх `CqlSession`: приложение пишет `CQL`-запросы в `@Query`, а Kora на этапе компиляции генерирует код подготовки запроса, связывания параметров и отображения результата.

Общие правила для отображений, `@Repository`, `@Query`, макросов, пакетных запросов и аннотаций `@Table`, `@Column`, `@Id`, `@Embedded` описаны в разделе [общих правил работы с базами данных](database-common.md).
Этот документ охватывает специфичные для Cassandra части: подключение драйвера, конфигурацию `CqlSession`, профили выполнения, `UDT`, отображатели и поддерживаемые сигнатуры методов.

Пошаговый разбор перед справочным описанием смотрите в разделе [База данных Cassandra](../guides/database-cassandra.md).

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

    1. Адреса узлов `Cassandra` для подключения к базе данных (`обязательно`, без значения по умолчанию)
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

    1. Адреса узлов `Cassandra` для подключения к базе данных (`обязательно`, без значения по умолчанию)
    2. Имя датацентра `Cassandra` (по умолчанию не указано, необязательно)
    3. Имя `keyspace` для подключения (по умолчанию не указано, необязательно)
    4. Таймаут выполнения запроса для подключения (по умолчанию не указано, необязательно)
    5. Имя пользователя для подключения (по умолчанию не указано, необязательно)
    6. Пароль для подключения (по умолчанию не указано, необязательно)

??? abstract "Пример полной конфигурации"

    Полная конфигурация с примерами значений. Описания параметров являются общими для примеров `HOCON` и `YAML`.

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

        1. Имя пользователя для аутентификации в `Cassandra` (по умолчанию не указано, необязательно).
        2. Пароль для аутентификации в `Cassandra` (по умолчанию не указано, необязательно).
        3. Адреса узлов `Cassandra` в формате `host:port` (`обязательно`, без значения по умолчанию).
        4. Имя сессии драйвера, используемое в логах, метриках и диагностике (по умолчанию не указано, необязательно).
        5. Локальный датацентр для политики балансировки нагрузки (по умолчанию не указано, необязательно).
        6. `keyspace`, который будет установлен для сессии после подключения (по умолчанию не указано, необязательно).
        7. Включает избегание медленных реплик в стандартной политике балансировки нагрузки (по умолчанию не указано, необязательно).
        8. Путь или `URL` к `Secure Connect Bundle` для подключения к `DataStax Astra` / облачной Cassandra (по умолчанию не указано, необязательно).
        9. Обычный таймаут запроса (по умолчанию не указано, необязательно).
        10. Уровень согласованности обычного запроса, например `ONE`, `LOCAL_ONE`, `LOCAL_QUORUM`, `QUORUM`, `ALL` (по умолчанию не указано, необязательно).
        11. Размер страницы результата, то есть максимальное количество строк, запрашиваемых за один сетевой обмен (по умолчанию не указано, необязательно).
        12. Уровень последовательной согласованности для облегченных транзакций `LWT`: `SERIAL` или `LOCAL_SERIAL` (по умолчанию не указано, необязательно).
        13. Значение идемпотентности запроса по умолчанию; влияет на то, можно ли безопасно применять повторные попытки и спекулятивное выполнение (по умолчанию не указано, необязательно).
        14. Порог предупреждения об утечке сессии драйвера (по умолчанию не указано, необязательно).
        15. Таймаут открытия сетевого соединения с узлом (по умолчанию не указано, необязательно).
        16. Таймаут запросов, которые драйвер выполняет при инициализации соединения (по умолчанию не указано, необязательно).
        17. Таймаут установки `keyspace` на соединении (по умолчанию не указано, необязательно).
        18. Максимальное количество одновременных запросов на одно соединение (по умолчанию не указано, необязательно).
        19. Максимальное количество запросов, ответ на которые уже не ожидается, но которые все еще могут завершиться внутри драйвера (по умолчанию не указано, необязательно).
        20. Логирует предупреждение при неудачной инициализации соединения для отдельного узла (по умолчанию не указано, необязательно).
        21. Размер пула соединений для узлов локального датацентра (по умолчанию не указано, необязательно).
        22. Размер пула соединений для удаленных узлов (по умолчанию не указано, необязательно).
        23. Разрешает повторную попытку инициализации, когда во время запуска все `contactPoints` не отвечают (по умолчанию не указано, необязательно).
        24. Начальная задержка политики переподключения (по умолчанию не указано, необязательно).
        25. Максимальная задержка политики переподключения (по умолчанию не указано, необязательно).
        26. Максимальное количество узлов удаленного датацентра, которые могут использоваться для отказоустойчивости (по умолчанию не указано, необязательно).
        27. Разрешает переключение на удаленный датацентр для локальных уровней согласованности (по умолчанию не указано, необязательно).
        28. Разрешенные наборы шифров для `SSL/TLS` (по умолчанию не указано, необязательно).
        29. Проверяет, что имя хоста узла соответствует сертификату `SSL/TLS` (по умолчанию не указано, необязательно).
        30. Путь к клиентскому keystore (по умолчанию не указано, необязательно).
        31. Пароль клиентского keystore (по умолчанию не указано, необязательно).
        32. Путь к truststore (по умолчанию не указано, необязательно).
        33. Пароль truststore (по умолчанию не указано, необязательно).
        34. Принудительно использует системные часы Java для генерации временных меток запросов (по умолчанию не указано, необязательно).
        35. Порог предупреждения о смещении временной метки в будущее (по умолчанию не указано, необязательно).
        36. Минимальный интервал между предупреждениями о смещении временной метки (по умолчанию не указано, необязательно).
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
        47. Включенные метрики уровня узла (по умолчанию: `open-connections`, `in-flight`, `bytes-received`, `bytes-sent`, `write-timeouts`, `read-timeouts`, `aborted-requests`).
        48. Наименьшая ожидаемая задержка для гистограммы метрики `node.cqlMessages` (по умолчанию: `1ms`).
        49. Наибольшая ожидаемая задержка для гистограммы метрики `node.cqlMessages` (по умолчанию: `90s`).
        50. Количество значащих цифр для гистограммы метрики `node.cqlMessages` (по умолчанию не указано, необязательно).
        51. Интервал обновления снимка для гистограммы метрики `node.cqlMessages` (по умолчанию не указано, необязательно).
        52. Границы `SLO` для метрики `node.cqlMessages` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        53. Включенные метрики уровня сессии (по умолчанию: `connected-nodes`, `cql-requests`, `cql-client-timeouts`, `cql-prepared-cache-size`, `throttling.delay`, `throttling.queue-size`).
        54. Наименьшая ожидаемая задержка для гистограммы метрики `session.cqlRequests` (по умолчанию: `1ms`).
        55. Наибольшая ожидаемая задержка для гистограммы метрики `session.cqlRequests` (по умолчанию: `90s`).
        56. Количество значащих цифр для гистограммы метрики `session.cqlRequests` (по умолчанию не указано, необязательно).
        57. Интервал обновления снимка для гистограммы метрики `session.cqlRequests` (по умолчанию не указано, необязательно).
        58. Границы `SLO` для метрики `session.cqlRequests` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        59. Наименьшая ожидаемая задержка для гистограммы метрики `session.throttlingDelay` (по умолчанию: `1ms`).
        60. Наибольшая ожидаемая задержка для гистограммы метрики `session.throttlingDelay` (по умолчанию: `90s`).
        61. Количество значащих цифр для гистограммы метрики `session.throttlingDelay` (по умолчанию не указано, необязательно).
        62. Интервал обновления снимка для гистограммы метрики `session.throttlingDelay` (по умолчанию не указано, необязательно).
        63. Границы `SLO` для метрики `session.throttlingDelay` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        64. Публикует процентильные гистограммы для метрик драйвера (по умолчанию: `false`).
        65. Включает `TCP_NODELAY`, что отключает алгоритм Нейгла (по умолчанию не указано, необязательно).
        66. Включает `SO_KEEPALIVE` для TCP-сокетов (по умолчанию не указано, необязательно).
        67. Включает `SO_REUSEADDR` для TCP-сокетов (по умолчанию не указано, необязательно).
        68. Значение `SO_LINGER` для TCP-сокетов (по умолчанию не указано, необязательно).
        69. Размер буфера приема TCP-сокета в байтах (по умолчанию не указано, необязательно).
        70. Размер буфера отправки TCP-сокета в байтах (по умолчанию не указано, необязательно).
        71. Интервал отправки `heartbeat` по простаивающему соединению (по умолчанию не указано, необязательно).
        72. Таймаут ожидания ответа на `heartbeat` (по умолчанию не указано, необязательно).
        73. Включает загрузку и обновление метаданных схемы (по умолчанию не указано, необязательно).
        74. Таймаут запросов метаданных схемы (по умолчанию не указано, необязательно).
        75. Размер страницы запросов метаданных схемы (по умолчанию не указано, необязательно).
        76. Список имен `keyspace`, метаданные схемы которых обновляются драйвером (по умолчанию не указано, необязательно).
        77. Окно для объединения событий обновления схемы перед обработкой (по умолчанию не указано, необязательно).
        78. Максимальное количество событий обновления схемы, которое может накопиться в окне (по умолчанию не указано, необязательно).
        79. Окно для объединения событий изменения топологии кластера (по умолчанию не указано, необязательно).
        80. Максимальное количество событий изменения топологии, которое может накопиться в окне (по умолчанию не указано, необязательно).
        81. Включает карту токенов для маршрутизации запросов к владельцам данных (по умолчанию не указано, необязательно).
        82. Таймаут служебного `control connection` (по умолчанию не указано, необязательно).
        83. Интервал проверки `schema agreement` между узлами (по умолчанию не указано, необязательно).
        84. Максимальное время ожидания `schema agreement` (по умолчанию не указано, необязательно).
        85. Логирует предупреждение, если `schema agreement` не достигнута вовремя (по умолчанию не указано, необязательно).
        86. Подготавливает запрос на всех узлах после того, как он успешно подготовлен на одном узле (по умолчанию не указано, необязательно).
        87. Повторно подготавливает запросы на узле, который снова стал доступен (по умолчанию не указано, необязательно).
        88. Проверяет системную таблицу `system.prepared_statements` перед повторной подготовкой запроса (по умолчанию не указано, необязательно).
        89. Максимальное количество запросов для повторной подготовки; `0` означает отсутствие ограничения на стороне драйвера (по умолчанию не указано, необязательно).
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
        116. Включает метрики запросов Kora (по умолчанию: `true`).
        117. Границы `SLO` метрик Kora (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        118. Дополнительные теги метрик Kora (по умолчанию: `{}`).
        119. Включает трассировку запросов Kora (по умолчанию: `true`).
        120. Дополнительные атрибуты трассировки Kora (по умолчанию: `{}`).

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
        2. Пароль для аутентификации в `Cassandra` (по умолчанию не указано, необязательно).
        3. Адреса узлов `Cassandra` в формате `host:port` (`обязательно`, без значения по умолчанию).
        4. Имя сессии драйвера, используемое в логах, метриках и диагностике (по умолчанию не указано, необязательно).
        5. Локальный датацентр для политики балансировки нагрузки (по умолчанию не указано, необязательно).
        6. `keyspace`, который будет установлен для сессии после подключения (по умолчанию не указано, необязательно).
        7. Включает избегание медленных реплик в стандартной политике балансировки нагрузки (по умолчанию не указано, необязательно).
        8. Путь или `URL` к `Secure Connect Bundle` для подключения к `DataStax Astra` / облачной Cassandra (по умолчанию не указано, необязательно).
        9. Обычный таймаут запроса (по умолчанию не указано, необязательно).
        10. Уровень согласованности обычного запроса, например `ONE`, `LOCAL_ONE`, `LOCAL_QUORUM`, `QUORUM`, `ALL` (по умолчанию не указано, необязательно).
        11. Размер страницы результата, то есть максимальное количество строк, запрашиваемых за один сетевой обмен (по умолчанию не указано, необязательно).
        12. Уровень последовательной согласованности для облегченных транзакций `LWT`: `SERIAL` или `LOCAL_SERIAL` (по умолчанию не указано, необязательно).
        13. Значение идемпотентности запроса по умолчанию; влияет на то, можно ли безопасно применять повторные попытки и спекулятивное выполнение (по умолчанию не указано, необязательно).
        14. Порог предупреждения об утечке сессии драйвера (по умолчанию не указано, необязательно).
        15. Таймаут открытия сетевого соединения с узлом (по умолчанию не указано, необязательно).
        16. Таймаут запросов, которые драйвер выполняет при инициализации соединения (по умолчанию не указано, необязательно).
        17. Таймаут установки `keyspace` на соединении (по умолчанию не указано, необязательно).
        18. Максимальное количество одновременных запросов на одно соединение (по умолчанию не указано, необязательно).
        19. Максимальное количество запросов, ответ на которые уже не ожидается, но которые все еще могут завершиться внутри драйвера (по умолчанию не указано, необязательно).
        20. Логирует предупреждение при неудачной инициализации соединения для отдельного узла (по умолчанию не указано, необязательно).
        21. Размер пула соединений для узлов локального датацентра (по умолчанию не указано, необязательно).
        22. Размер пула соединений для удаленных узлов (по умолчанию не указано, необязательно).
        23. Разрешает повторную попытку инициализации, когда во время запуска все `contactPoints` не отвечают (по умолчанию не указано, необязательно).
        24. Начальная задержка политики переподключения (по умолчанию не указано, необязательно).
        25. Максимальная задержка политики переподключения (по умолчанию не указано, необязательно).
        26. Максимальное количество узлов удаленного датацентра, которые могут использоваться для отказоустойчивости (по умолчанию не указано, необязательно).
        27. Разрешает переключение на удаленный датацентр для локальных уровней согласованности (по умолчанию не указано, необязательно).
        28. Разрешенные наборы шифров для `SSL/TLS` (по умолчанию не указано, необязательно).
        29. Проверяет, что имя хоста узла соответствует сертификату `SSL/TLS` (по умолчанию не указано, необязательно).
        30. Путь к клиентскому keystore (по умолчанию не указано, необязательно).
        31. Пароль клиентского keystore (по умолчанию не указано, необязательно).
        32. Путь к truststore (по умолчанию не указано, необязательно).
        33. Пароль truststore (по умолчанию не указано, необязательно).
        34. Принудительно использует системные часы Java для генерации временных меток запросов (по умолчанию не указано, необязательно).
        35. Порог предупреждения о смещении временной метки в будущее (по умолчанию не указано, необязательно).
        36. Минимальный интервал между предупреждениями о смещении временной метки (по умолчанию не указано, необязательно).
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
        47. Включенные метрики уровня узла (по умолчанию: `open-connections`, `in-flight`, `bytes-received`, `bytes-sent`, `write-timeouts`, `read-timeouts`, `aborted-requests`).
        48. Наименьшая ожидаемая задержка для гистограммы метрики `node.cqlMessages` (по умолчанию: `1ms`).
        49. Наибольшая ожидаемая задержка для гистограммы метрики `node.cqlMessages` (по умолчанию: `90s`).
        50. Количество значащих цифр для гистограммы метрики `node.cqlMessages` (по умолчанию не указано, необязательно).
        51. Интервал обновления снимка для гистограммы метрики `node.cqlMessages` (по умолчанию не указано, необязательно).
        52. Границы `SLO` для метрики `node.cqlMessages` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        53. Включенные метрики уровня сессии (по умолчанию: `connected-nodes`, `cql-requests`, `cql-client-timeouts`, `cql-prepared-cache-size`, `throttling.delay`, `throttling.queue-size`).
        54. Наименьшая ожидаемая задержка для гистограммы метрики `session.cqlRequests` (по умолчанию: `1ms`).
        55. Наибольшая ожидаемая задержка для гистограммы метрики `session.cqlRequests` (по умолчанию: `90s`).
        56. Количество значащих цифр для гистограммы метрики `session.cqlRequests` (по умолчанию не указано, необязательно).
        57. Интервал обновления снимка для гистограммы метрики `session.cqlRequests` (по умолчанию не указано, необязательно).
        58. Границы `SLO` для метрики `session.cqlRequests` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        59. Наименьшая ожидаемая задержка для гистограммы метрики `session.throttlingDelay` (по умолчанию: `1ms`).
        60. Наибольшая ожидаемая задержка для гистограммы метрики `session.throttlingDelay` (по умолчанию: `90s`).
        61. Количество значащих цифр для гистограммы метрики `session.throttlingDelay` (по умолчанию не указано, необязательно).
        62. Интервал обновления снимка для гистограммы метрики `session.throttlingDelay` (по умолчанию не указано, необязательно).
        63. Границы `SLO` для метрики `session.throttlingDelay` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        64. Публикует процентильные гистограммы для метрик драйвера (по умолчанию: `false`).
        65. Включает `TCP_NODELAY`, что отключает алгоритм Нейгла (по умолчанию не указано, необязательно).
        66. Включает `SO_KEEPALIVE` для TCP-сокетов (по умолчанию не указано, необязательно).
        67. Включает `SO_REUSEADDR` для TCP-сокетов (по умолчанию не указано, необязательно).
        68. Значение `SO_LINGER` для TCP-сокетов (по умолчанию не указано, необязательно).
        69. Размер буфера приема TCP-сокета в байтах (по умолчанию не указано, необязательно).
        70. Размер буфера отправки TCP-сокета в байтах (по умолчанию не указано, необязательно).
        71. Интервал отправки `heartbeat` по простаивающему соединению (по умолчанию не указано, необязательно).
        72. Таймаут ожидания ответа на `heartbeat` (по умолчанию не указано, необязательно).
        73. Включает загрузку и обновление метаданных схемы (по умолчанию не указано, необязательно).
        74. Таймаут запросов метаданных схемы (по умолчанию не указано, необязательно).
        75. Размер страницы запросов метаданных схемы (по умолчанию не указано, необязательно).
        76. Список имен `keyspace`, метаданные схемы которых обновляются драйвером (по умолчанию не указано, необязательно).
        77. Окно для объединения событий обновления схемы перед обработкой (по умолчанию не указано, необязательно).
        78. Максимальное количество событий обновления схемы, которое может накопиться в окне (по умолчанию не указано, необязательно).
        79. Окно для объединения событий изменения топологии кластера (по умолчанию не указано, необязательно).
        80. Максимальное количество событий изменения топологии, которое может накопиться в окне (по умолчанию не указано, необязательно).
        81. Включает карту токенов для маршрутизации запросов к владельцам данных (по умолчанию не указано, необязательно).
        82. Таймаут служебного `control connection` (по умолчанию не указано, необязательно).
        83. Интервал проверки `schema agreement` между узлами (по умолчанию не указано, необязательно).
        84. Максимальное время ожидания `schema agreement` (по умолчанию не указано, необязательно).
        85. Логирует предупреждение, если `schema agreement` не достигнута вовремя (по умолчанию не указано, необязательно).
        86. Подготавливает запрос на всех узлах после того, как он успешно подготовлен на одном узле (по умолчанию не указано, необязательно).
        87. Повторно подготавливает запросы на узле, который снова стал доступен (по умолчанию не указано, необязательно).
        88. Проверяет системную таблицу `system.prepared_statements` перед повторной подготовкой запроса (по умолчанию не указано, необязательно).
        89. Максимальное количество запросов для повторной подготовки; `0` означает отсутствие ограничения на стороне драйвера (по умолчанию не указано, необязательно).
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
        116. Включает метрики запросов Kora (по умолчанию: `true`).
        117. Границы `SLO` метрик Kora (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        118. Дополнительные теги метрик Kora (по умолчанию: `{}`).
        119. Включает трассировку запросов Kora (по умолчанию: `true`).
        120. Дополнительные атрибуты трассировки Kora (по умолчанию: `{}`).

### Конфигурация в коде { #code-configuration }

Драйвер можно настроить вручную в коде, зарегистрировав компонент `CassandraConfigurer`.
Метод `configure` получает `CqlSessionBuilder` и `ProgrammaticDriverConfigLoaderBuilder`,
поэтому вы можете настроить построитель сессии и переопределить низкоуровневые параметры драйвера, которые не доступны через секцию конфигурации `cassandra`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyCassandraConfigurer implements CassandraConfigurer {

        @Override
        public CqlSessionBuilder configure(CqlSessionBuilder builder, ProgrammaticDriverConfigLoaderBuilder loaderBuilder) {
            return builder.withClientId(UUID.randomUUID());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyCassandraConfigurer : CassandraConfigurer {

        override fun configure(builder: CqlSessionBuilder, loaderBuilder: ProgrammaticDriverConfigLoaderBuilder): CqlSessionBuilder {
            return builder.withClientId(UUID.randomUUID())
        }
    }
    ```

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
Параметры запроса (например, `:id`, `:entity.field1`) заменяются в сгенерированном коде на соответствующие вызовы драйвера Cassandra.
Например, для параметра `String id` будет сгенерировано что-то вроде `statement.setString(1, id)`, где индекс соответствует порядку параметра в запросе.
Это обеспечивает безопасность (защита от CQL-инъекций) и производительность (использование подготовленных запросов драйвером).

В отличие от реляционных баз данных, в `Cassandra` нет транзакций.
Когда нужно, чтобы несколько операторов применились атомарно, используйте `@Batch`-метод (`CQL` `BATCH`), как показано выше;
его семантика и макросы описаны в разделе [общих правил работы с базами данных](database-common.md).

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

## Отображение { #mapping }

Можно переопределить отображение различных частей [отображения](database-common.md) и параметров запроса — `Kora` предоставляет для этого специальные интерфейсы.
Из коробки `CassandraModule` предоставляет отображатели для распространенных типов: `String`, числовых типов, `Boolean`, `BigDecimal`, `BigInteger`, `UUID`, `ByteBuffer`, `LocalDate`, `LocalTime`, `LocalDateTime`, `ZonedDateTime` и `Instant`.
Если тип не входит в этот набор или ему нужно особое представление в `CQL`, добавьте собственный отображатель через `@Mapping`.

### Отображение { #view }

Используйте аннотацию `@EntityCassandra` для оптимального отображения.
Аннотация позволяет обработчику аннотаций сгенерировать все необходимые отображатели за **один раунд** аннотационной обработки.
Без этой аннотации отображатели генерируются по требованию, что может потребовать **множества раундов** обработки и значительно увеличить время компиляции.
Это рекомендуемый способ отображения каждого типа, возвращаемого из репозитория или связываемого в нем.

Ожидается, что все вложенные отображения и типы [UDT](#udt) также используют эту аннотацию.

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

    В Kotlin отображатели нужно писать только для типов `T?`, поэтому в интерфейсах тип указывается как `@Nullable`.

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

Каждый интерфейс отображателя результата также предоставляет статические фабричные методы, которые строят полный отображатель результата из `CassandraRowMapper<T>`,
так что один отображатель строки можно переиспользовать в разных сигнатурах:

- `CassandraResultSetMapper` — `singleResultSetMapper`, `optionalResultSetMapper`, `listResultSetMapper`;
- `CassandraAsyncResultSetMapper` — `one`, `list` (автоматически проходит по страницам результата);
- `CassandraReactiveResultSetMapper` — `flux`, `mono`, `monoVoid`, `monoList`.

### Строка { #row }

Если нужно вручную преобразовать одну строку результата, используйте `CassandraRowMapper<T>`.
Этот отображатель применяется к каждой строке и подходит для возвращаемых значений вида `T`, `Optional<T>`, `List<T>`, `Flux<T>` и `Flow<T>`.

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

    В Kotlin отображатели нужно писать только для типов `T?`, поэтому в интерфейсах тип указывается как `@Nullable`.

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

### Столбец { #column }

Если нужно вручную преобразовать значение столбца, предлагается использовать `CassandraRowColumnMapper`:

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

    В Kotlin отображатели нужно писать только для типов `T?`, поэтому в интерфейсах тип указывается как `@Nullable`.

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

Если нужно вручную преобразовать значение параметра запроса, используйте `CassandraParameterColumnMapper<T>`.
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

    В Kotlin отображатели нужно писать только для типов `T?`, поэтому в интерфейсах тип указывается как `@Nullable`.

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

### Асинхронный { #async }

Для `CompletionStage<T>` и `CompletableFuture<T>` используйте `CassandraAsyncResultSetMapper<T>`, который получает `AsyncResultSet` и возвращает `CompletionStage<T>`.
Его метод `list` автоматически запрашивает последующие страницы результата, поэтому результат `List<T>` собирает все страницы перед завершением.
Для реактивных типов `Mono<T>` / `Flux<T>` используйте `CassandraReactiveResultSetMapper<T, P>`, который получает `ReactiveResultSet` и возвращает нужный `Publisher`.

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

## Ручной запрос { #query }

Если запрос сложно выразить одной статической `@Query`, вы можете объявить обычный метод с реализацией и построить `CQL` вручную.
Репозиторий предоставляет `getCassandraConnectionFactory()`, а `CassandraConnectionFactory#query` выполняет такой запрос:
он подготавливает оператор через текущую `CqlSession`, оборачивает выполнение в телеметрию `Kora` и возвращает значение, полученное из колбэка.
Метод доступа `currentSession()` возвращает активную `CqlSession`, а `telemetry()` возвращает `DataBaseTelemetry`, используемую для отчетности.

`QueryContext` содержит идентификатор запроса и итоговый `CQL`.
Идентификатор передается в телеметрию, поэтому используйте стабильное имя, например `Repository.method`.
Связывайте значения через `BoundStatement`, полученный из подготовленного оператора; никогда не конкатенируйте значения напрямую в строку запроса.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends CassandraRepository {

        default List<Entity> findByFilter(@Nullable String value2) {
            var sql = new StringBuilder("SELECT id, value1, value2, value3 FROM entities");
            if (value2 != null) {
                sql.append(" WHERE value2 = ? ALLOW FILTERING");
            }

            var connectionFactory = getCassandraConnectionFactory();
            var queryContext = new QueryContext("EntityRepository.findByFilter", sql.toString());
            return connectionFactory.query(queryContext, statement -> {
                var boundStatement = (value2 != null)
                    ? statement.bind(value2)
                    : statement.bind();
                var resultSet = connectionFactory.currentSession().execute(boundStatement);

                var result = new ArrayList<Entity>();
                for (var row : resultSet) {
                    result.add(new Entity(
                        row.getString("id"),
                        row.getInt("value1"),
                        row.getString("value2"),
                        row.getString("value3")));
                }
                return result;
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : CassandraRepository {

        fun findByFilter(value2: String?): List<Entity> {
            val sql = StringBuilder("SELECT id, value1, value2, value3 FROM entities")
            if (value2 != null) {
                sql.append(" WHERE value2 = ? ALLOW FILTERING")
            }

            val connectionFactory = cassandraConnectionFactory
            val queryContext = QueryContext("EntityRepository.findByFilter", sql.toString())
            return connectionFactory.query(queryContext) { statement ->
                val boundStatement = if (value2 != null) statement.bind(value2) else statement.bind()
                val resultSet = connectionFactory.currentSession().execute(boundStatement)

                resultSet.map { row ->
                    Entity(
                        row.getString("id"),
                        row.getInt("value1"),
                        row.getString("value2"),
                        row.getString("value3")
                    )
                }
            }
        }
    }
    ```

Поскольку в `Cassandra` нет транзакций, `query` просто выполняется на текущей сессии с телеметрией; здесь нет фиксации или отката, которыми нужно управлять.

## UDT { #udt }

Поддерживаются типы [UDT](https://docs.datastax.com/en/cql-oss/3.3/cql/cql_using/useCreateUDT.html) через аннотацию `@UDT`.
`UDT` описывает пользовательский тип Cassandra и может использоваться как поле обычного отображения.
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

Если тип `UDT` используется не через охватывающее отображение, а как самостоятельный тип Cassandra, генерацию отображателя можно включить явно с помощью `@EntityCassandra`.
Это полезно, когда отображатель нужен как отдельный компонент графа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @EntityCassandra
    public record Name(String first, String last) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
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
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `CompletableFuture<T> myMethod()` [CompletableFuture](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletableFuture.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (требует [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (требует [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

    Обертки `CompletionStage<T>`, `CompletableFuture<T>` и `Mono<T>` также могут оборачивать `List<T>`,
    например `CompletionStage<List<Entity>>` или `Mono<List<Entity>>`.

    Параметры метода могут включать обычные значения, DTO, `@Batch List<T>` для пакетного выполнения и `CqlSession`, когда методу нужен доступ к текущей сессии драйвера.

=== ":simple-kotlin: `Kotlin`"

    `T` означает тип возвращаемого значения, либо `T?`, либо `List<T>`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требует [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требует [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

    Параметры метода могут включать обычные значения, DTO, `@Batch List<T>` для пакетного выполнения и `CqlSession`, когда методу нужен доступ к текущей сессии драйвера.

## Телеметрия { #telemetry }

Логирование, метрики и трассировка настраиваются через блок `telemetry` в [конфигурации](#configuration) и описаны в разделе [Справочник метрик](metrics.md#database).
Чтобы переопределить телеметрию полностью, можно предоставить собственные SPI-фабрики, подробнее в [Общей документации по Базам данных](database-common.md#telemetry).
