---
description: "Explains the Kora gRPC client: the grpc-client module, protobuf Gradle plugin setup, the grpcClient configuration section, injecting generated stubs, per-client interceptors, TLS credentials, channel tuning and telemetry. Use when working with GrpcClientModule, GrpcClientConfig, GrpcClientChannelFactory, ManagedChannelLifecycle, ChannelCredentials, protobuf plugin."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the Kora gRPC client: injecting BlockingStub / FutureStub / async Stub / Kotlin coroutine stubs, the grpcClient.<Service> configuration section, url scheme and TLS, deadlines, keepAlive and load balancing, per-client ClientInterceptor tagging, authorization metadata, error handling and telemetry; key triggers include GrpcClientModule, GrpcClientConfig, GrpcClientChannelFactory, GrpcOkHttpClientChannelFactory, ManagedChannelLifecycle, Configurer, ChannelCredentials, protobuf plugin."
---

`gRPC-клиент` вызывает удалённые службы, используя контракт `protobuf` и транспорт `HTTP/2`.
В Kora клиент строится поверх сгенерированных классов `stub` библиотеки `grpc-java`: модуль создаёт `ManagedChannel`, подключает перехватчики и регистрирует готовые к использованию экземпляры `stub` в графе приложения.

Для каждой службы Kora делает доступными для внедрения сгенерированные stub-классы (`BlockingStub`, `FutureStub`, асинхронный `Stub` и корутинный stub для Kotlin),
исходный `io.grpc.Channel` и итоговый `GrpcClientConfig`, различая каждый клиент по `@Tag` сгенерированного класса службы
(например, `@Tag(SimpleServiceGrpc.class)`).

Транспорт gRPC-клиента — `grpc-okhttp`: для каждого клиента Kora строит `OkHttpChannelBuilder` через `GrpcOkHttpClientChannelFactory`,
поэтому настройка канала выполняется через конфигурацию или настройщик построителя, а не через общий транспортный модуль.

Если нужен пошаговый разбор перед справочным описанием, смотрите [gRPC-клиент](../guides/grpc-client.md) и [продвинутый gRPC-клиент](../guides/grpc-client-advanced.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:grpc-client"
    implementation "io.grpc:grpc-protobuf:1.83.1"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends GrpcClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:grpc-client")
    implementation("io.grpc:grpc-protobuf:1.83.1")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : GrpcClientModule
    ```

### Плагин { #plugin }

Код `gRPC-клиента` создаётся с помощью [Gradle-плагина protobuf](https://github.com/google/protobuf-gradle-plugin).
Плагин генерирует Java-классы сообщений из контракта `protobuf` и классы `stub` для gRPC, которые затем использует Kora.

===! ":fontawesome-brands-java: `Java`"

    Плагин `build.gradle`:
    ```groovy
    plugins {
        id "com.google.protobuf" version "0.10.0"
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:4.35.1" }
        plugins {
            grpc { artifact = "io.grpc:protoc-gen-grpc-java:1.83.1" }
        }
        generateProtoTasks {
            all()*.plugins { grpc {} }
        }
    }

    sourceSets {
        main.java {
            srcDirs "build/generated/source/proto/main/grpc"
            srcDirs "build/generated/source/proto/main/java"
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Плагин `build.gradle.kts`:
    ```groovy
    import com.google.protobuf.gradle.id

    plugins {
        id("com.google.protobuf") version ("0.10.0")
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:4.35.1" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.83.1" }
        }
        generateProtoTasks {
            ofSourceSet("main").forEach { it.plugins { id("grpc") { } } }
        }
    }

    kotlin {
        sourceSets.main {
            kotlin.srcDir("build/generated/source/proto/main/grpc")
            kotlin.srcDir("build/generated/source/proto/main/java")
        }
    }
    ```

    Дополнительно подключайте [генератор gRPC Kotlin](https://github.com/grpc/grpc-kotlin), только если нужны корутинные stub-классы:
    ```groovy
    dependencies {
        implementation("io.grpc:grpc-kotlin-stub:1.5.0")
    }

    protobuf {
        plugins {
            id("grpckt") { artifact = "io.grpc:protoc-gen-grpc-kotlin:1.5.0:jdk8@jar" }
        }
        generateProtoTasks {
            ofSourceSet("main").forEach { it.plugins { id("grpc") { }; id("grpckt") { } } }
        }
    }

    kotlin {
        sourceSets.main {
            kotlin.srcDir("build/generated/source/proto/main/grpckt")
        }
    }
    ```

## Конфигурация { #configuration }

`gRPC-клиент` для службы `SimpleService` будет иметь путь конфигурации `grpcClient.SimpleService`.

Сегмент пути — это *простое* имя службы `protobuf`: Kora берёт сгенерированную константу `SERVICE_NAME`
(полное имя вместе с `proto`-пакетом) и оставляет только часть после последней точки.
Служба, объявленная как `package my.company.api; service SimpleService`, настраивается в `grpcClient.SimpleService`.

Основные параметры конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcClient {
        SimpleService {
            url = "http://localhost:8090" //(1)!
            timeout = "10s"  //(2)!
        }
    }
    ```

    1. `URL` сервера, куда будут отправляться запросы (`обязательный`, без значения по умолчанию).
    2. Максимальное время выполнения запроса (по умолчанию не указано, опционально). Значение применяется как `deadline`, если у вызова ещё нет собственного `deadline`.

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcClient:
      SimpleService:
        url: "http://localhost:8090" #(1)!
        timeout: "10s" #(2)!
    ```

    1. `URL` сервера, куда будут отправляться запросы (`обязательный`, без значения по умолчанию).
    2. Максимальное время выполнения запроса (по умолчанию не указано, опционально). Значение применяется как `deadline`, если у вызова ещё нет собственного `deadline`.

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классе `GrpcClientConfig`:

    ===! ":material-code-json: `Hocon`"

        ```javascript
        grpcClient {
            SimpleService {
                url = "http://localhost:8090" //(1)!
                timeout = "10s"  //(2)!
                keepAliveTime = "30s" //(3)!
                keepAliveTimeout = "10s" //(4)!
                loadBalancingPolicy = "round_robin" //(5)!
                defaultServiceConfig { //(6)!
                    loadBalancingConfig = [
                        {
                            round_robin = {}
                        }
                    ]
                }
                telemetry {
                    logging {
                        enabled = false //(7)!
                    }
                    metrics {
                        enabled = false //(8)!
                        slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(9)!
                        tags = { // (10)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                    tracing {
                        enabled = true //(11)!
                        attributes = { // (12)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                }
            }
        }
        ```

        1. `URL` сервера, куда будут отправляться запросы (обязательный, без значения по умолчанию).
        2. Максимальное время выполнения запроса (по умолчанию не указано, опционально). Значение применяется как `deadline`, если у вызова ещё нет собственного `deadline`.
        3. Интервал между фреймами `PING` протокола gRPC (по умолчанию не указано, опционально).
        4. Время ожидания подтверждения фрейма `PING` (по умолчанию не указано, опционально). Если подтверждение не получено за это время, соединение закрывается.
        5. Политика балансировки нагрузки для `ManagedChannelBuilder` (по умолчанию не указано, опционально).
        6. Стандартная конфигурация службы gRPC, передаваемая в `ManagedChannelBuilder.defaultServiceConfig` (по умолчанию не указано, опционально).
        7. Включает логирование модуля (по умолчанию: `false`).
        8. Включает метрики модуля (по умолчанию: `false`).
        9. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`). Обычные числа читаются как миллисекунды.
        10. Дополнительные теги для метрик (по умолчанию: `{}`).
        11. Включает трассировку модуля (по умолчанию: `true`).
        12. Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

    === ":simple-yaml: `YAML`"

        ```yaml
        grpcClient:
          SimpleService:
            url: "http://localhost:8090" #(1)!
            timeout: "10s" #(2)!
            keepAliveTime: "30s" #(3)!
            keepAliveTimeout: "10s" #(4)!
            loadBalancingPolicy: "round_robin" #(5)!
            defaultServiceConfig: #(6)!
              loadBalancingConfig:
                - round_robin: {}
            telemetry:
              logging:
                enabled: false #(7)!
              metrics:
                enabled: false #(8)!
                slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(9)!
                tags: #(10)!
                  key1: value1
                  key2: value2
              tracing:
                enabled: true #(11)!
                attributes: #(12)!
                  key1: value1
                  key2: value2
        ```

        1. `URL` сервера, куда будут отправляться запросы (обязательный, без значения по умолчанию).
        2. Максимальное время выполнения запроса (по умолчанию не указано, опционально). Значение применяется как `deadline`, если у вызова ещё нет собственного `deadline`.
        3. Интервал между фреймами `PING` протокола gRPC (по умолчанию не указано, опционально).
        4. Время ожидания подтверждения фрейма `PING` (по умолчанию не указано, опционально). Если подтверждение не получено за это время, соединение закрывается.
        5. Политика балансировки нагрузки для `ManagedChannelBuilder` (по умолчанию не указано, опционально).
        6. Стандартная конфигурация службы gRPC, передаваемая в `ManagedChannelBuilder.defaultServiceConfig` (по умолчанию не указано, опционально).
        7. Включает логирование модуля (по умолчанию: `false`).
        8. Включает метрики модуля (по умолчанию: `false`).
        9. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`). Обычные числа читаются как миллисекунды.
        10. Дополнительные теги для метрик (по умолчанию: `{}`).
        11. Включает трассировку модуля (по умолчанию: `true`).
        12. Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

### Транспорт и TLS { #transport-tls }

Схема в `url` определяет транспорт при создании `ManagedChannel` (`ManagedChannelLifecycle`):

- `http` — незашифрованный транспорт (`usePlaintext()` у построителя), порт по умолчанию `80`, если порт не указан.
- `https` — транспорт `TLS`, порт по умолчанию `443`, если порт не указан.
- любая другая схема — порт нужно указать явно, иначе приложение не запустится с ошибкой
  `IllegalArgumentException: Unsupported gRPC client URL scheme '<scheme>' in '<url>'; use http://host[:port] or https://host[:port]`.
  Режим plaintext включается только для схемы `http`, поэтому другая схема с явным портом всё равно использует транспорт `TLS`.

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcClient {
        SimpleService {
            url = "http://localhost:8090" // plaintext, default port 80
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcClient:
      SimpleService:
        url: "http://localhost:8090" # plaintext, default port 80
    ```

Для собственного `TLS` (`mTLS`, приватный удостоверяющий центр) зарегистрируйте компонент `io.grpc.ChannelCredentials` с тегом сгенерированного класса службы.
`ManagedChannelLifecycle` подхватывает его для конкретного клиента и создаёт канал с этими учётными данными вместо настроек транспорта по умолчанию:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        @Tag(SimpleServiceGrpc.class)
        default ChannelCredentials simpleServiceCredentials() {
            try {
                return TlsChannelCredentials.newBuilder()
                    .trustManager(new File("/etc/certs/ca.pem")) //(1)!
                    .keyManager(new File("/etc/certs/client.pem"), new File("/etc/certs/client.key")) //(2)!
                    .build();
            } catch (IOException e) {
                throw new IllegalStateException("Failed to read gRPC client TLS certificates", e);
            }
        }
    }
    ```

    1. Доверенный удостоверяющий центр в формате `PEM`, используемый для проверки сертификата сервера.
    2. Сертификат клиента и приватный ключ в формате `PEM` — нужны только для `mTLS`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {

        @Tag(SimpleServiceGrpc::class)
        fun simpleServiceCredentials(): ChannelCredentials = TlsChannelCredentials.newBuilder()
            .trustManager(File("/etc/certs/ca.pem")) //(1)!
            .keyManager(File("/etc/certs/client.pem"), File("/etc/certs/client.key")) //(2)!
            .build()
    }
    ```

    1. Доверенный удостоверяющий центр в формате `PEM`, используемый для проверки сертификата сервера.
    2. Сертификат клиента и приватный ключ в формате `PEM` — нужны только для `mTLS`.

Учётные данные необязательны: без такого компонента канал создаётся только по `url`.
Если учётные данные заданы, оставляйте в `url` схему `https` (или явный порт) — схема `http` включает `usePlaintext()` и отключает их.

Чтобы заменить сам транспорт, зарегистрируйте собственный компонент `GrpcClientChannelFactory`. Это один общий компонент на все gRPC-клиенты,
и он переопределяет реализацию по умолчанию `GrpcOkHttpClientChannelFactory`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CustomGrpcClientChannelFactory implements GrpcClientChannelFactory {

        @Override
        public ManagedChannelBuilder<?> forTarget(String target) {
            return OkHttpChannelBuilder.forTarget(target);
        }

        @Override
        public ManagedChannelBuilder<?> forTarget(String target, ChannelCredentials creds) {
            return OkHttpChannelBuilder.forTarget(target, creds);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CustomGrpcClientChannelFactory : GrpcClientChannelFactory {

        override fun forTarget(target: String): ManagedChannelBuilder<*> {
            return OkHttpChannelBuilder.forTarget(target)
        }

        override fun forTarget(target: String, creds: ChannelCredentials): ManagedChannelBuilder<*> {
            return OkHttpChannelBuilder.forTarget(target, creds)
        }
    }
    ```

Реализовать нужно только `forTarget` — у перегрузок `forAddress(host, port)` есть реализации по умолчанию, которые собирают строку `host:port` и делегируют в `forTarget`.
Переопределяйте `forAddress` дополнительно, если транспорт ожидает не такую строку адреса.

### Ограничение по времени { #timeouts }

Значение `timeout` применяется всегда включённым перехватчиком `GrpcClientConfigInterceptor` как `deadline` вызова, но **только если у вызова нет собственного deadline**.
Заданный для конкретного вызова deadline попадает в `CallOptions` ещё до запуска перехватчиков, поэтому он всегда имеет приоритет над настроенным `timeout`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // uses the configured grpcClient.SimpleService.timeout as the deadline
    var response = stub.createUser(request);

    // overrides the configured timeout for this single call
    var responseWithDeadline = stub.withDeadlineAfter(2, TimeUnit.SECONDS).createUser(request);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // uses the configured grpcClient.SimpleService.timeout as the deadline
    val response = stub.createUser(request)

    // overrides the configured timeout for this single call
    val responseWithDeadline = stub.withDeadlineAfter(2, TimeUnit.SECONDS).createUser(request)
    ```

Когда истекает deadline, вызов завершается с ошибкой `StatusRuntimeException`, несущей `Status.DEADLINE_EXCEEDED`.

### Конфигурация канала { #channel-config }

- `keepAliveTime` / `keepAliveTimeout` соответствуют настройкам `PING` у `ManagedChannelBuilder`. `keepAliveTime` — интервал между фреймами `PING` протокола `HTTP/2` на простаивающем соединении; `keepAliveTimeout` — как долго ждать подтверждения `PING` перед закрытием соединения. Оба отключены, если не заданы.
- `loadBalancingPolicy` соответствует `ManagedChannelBuilder.defaultLoadBalancingPolicy`. Значение по умолчанию в gRPC — `pick_first` (единственное соединение с первым разрешённым адресом); `round_robin` распределяет вызовы по всем разрешённым адресам и обычно используется с DNS-адресами, возвращающими несколько записей `A`/`AAAA`.
- `defaultServiceConfig` передаётся как есть в `ManagedChannelBuilder.defaultServiceConfig` и содержит нативную карту [конфигурации службы](https://github.com/grpc/grpc/blob/master/doc/service_config.md) gRPC (`loadBalancingConfig`, `methodConfig` для отдельных методов с политикой повторов/хеджирования и т. д.). Она описана обёрткой `DefaultServiceConfig` над `Map<String, Object>`, и все числа в ней читаются как значения `double`, как того требует формат service config в gRPC.

### Настройщик построителя канала { #builder-configurer }

Если конфигурации из файла недостаточно, можно зарегистрировать компонент `Configurer<ManagedChannelBuilder<?>>`.
Он получает уже подготовленный `ManagedChannelBuilder` и позволяет донастроить канал в коде до его создания.

Компонент регистрируется на двух уровнях:

- **с тегом сгенерированного класса службы** — применяется только к этому клиенту, после всего из `GrpcClientConfig` (перехватчики, `keepAlive`, `loadBalancingPolicy`, `defaultServiceConfig`), поэтому может переопределить любую из этих настроек;
- **без тега** — передаётся в фабрику по умолчанию `GrpcOkHttpClientChannelFactory` и применяется к построителю каждого gRPC-клиента в момент создания, то есть до значений конфигурации.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(SimpleServiceGrpc.class)
    @Component
    public final class SimpleServiceChannelConfigurer implements Configurer<ManagedChannelBuilder<?>> { //(1)!

        @Override
        public ManagedChannelBuilder<?> configure(ManagedChannelBuilder<?> builder) {
            return builder.maxInboundMessageSize(8 * 1024 * 1024);
        }
    }

    @Component
    public final class CommonChannelConfigurer implements Configurer<ManagedChannelBuilder<?>> { //(2)!

        @Override
        public ManagedChannelBuilder<?> configure(ManagedChannelBuilder<?> builder) {
            return builder.userAgent("my-service");
        }
    }
    ```

    1. Применяется только к клиенту `SimpleService` и позже всех остальных настроек.
    2. Применяется к каждому gRPC-клиенту приложения.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class)
    @Component
    class SimpleServiceChannelConfigurer : Configurer<ManagedChannelBuilder<*>> { //(1)!

        override fun configure(builder: ManagedChannelBuilder<*>): ManagedChannelBuilder<*> {
            return builder.maxInboundMessageSize(8 * 1024 * 1024)
        }
    }

    @Component
    class CommonChannelConfigurer : Configurer<ManagedChannelBuilder<*>> { //(2)!

        override fun configure(builder: ManagedChannelBuilder<*>): ManagedChannelBuilder<*> {
            return builder.userAgent("my-service")
        }
    }
    ```

    1. Применяется только к клиенту `SimpleService` и позже всех остальных настроек.
    2. Применяется к каждому gRPC-клиенту приложения.

Настройщик без тега — это параметр фабрики `GrpcClientChannelFactory` по умолчанию, поэтому он игнорируется, если вы заменили эту фабрику своим компонентом:
в таком случае подключите его самостоятельно.

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#grpc-client).

## Служба { #service }

Созданные экземпляры gRPC `stub` можно внедрять как зависимости:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        default SomeService someService(SimpleServiceGrpc.SimpleServiceBlockingStub grpcService) {
            return new SomeService(grpcService);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {
        fun someService(grpcService: SimpleServiceGrpc.SimpleServiceBlockingStub): SomeService {
            return SomeService(grpcService)
        }
    }
    ```

Stub можно внедрить и напрямую в конструктор `@Component`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final SimpleServiceGrpc.SimpleServiceBlockingStub grpcService;

        public SomeService(SimpleServiceGrpc.SimpleServiceBlockingStub grpcService) {
            this.grpcService = grpcService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val grpcService: SimpleServiceGrpc.SimpleServiceBlockingStub)
    ```

### Типы реализаций { #stub-types }

Плагин `protobuf` генерирует для одной службы (`SimpleService`) несколько классов stub. Каждый внедряется простым объявлением соответствующего типа;
`@Tag` на самом stub не требуется (Kora сама подставляет `Channel` с нужным тегом):

| Тип stub                               | Модель вызова                                                           | Когда использовать                                   |
|----------------------------------------|------------------------------------------------------------------------|------------------------------------------------------|
| `SimpleServiceBlockingStub`            | Синхронная; возвращает ответ напрямую (или `Iterator` для серверного стриминга) | Блокирующий код, самый простой стиль вызова          |
| `SimpleServiceFutureStub`              | Асинхронная; возвращает `ListenableFuture<T>` (только unary)           | Неблокирующий код на `ListenableFuture`              |
| `SimpleServiceStub` (async)            | Асинхронная; отдаёт результаты через колбэки `StreamObserver<T>`        | Любой стриминг, асинхронные вызовы в стиле колбэков  |
| Корутинный stub для Kotlin             | `suspend`-функции и `Flow<T>`                                          | Идиоматичные корутины Kotlin                         |

`BlockingStub`, `FutureStub` и асинхронный `Stub` подключает расширение `GrpcClientExtension` для процессора аннотаций (или KSP): оно находит типы stub, помеченные `@GrpcGenerated`,
и вызывает сгенерированные фабрики `newBlockingStub` / `newFutureStub` / `newStub` для `Channel` с соответствующим тегом.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        default BlockingCaller blockingCaller(SimpleServiceGrpc.SimpleServiceBlockingStub stub) {
            return new BlockingCaller(stub);
        }

        default FutureCaller futureCaller(SimpleServiceGrpc.SimpleServiceFutureStub stub) {
            return new FutureCaller(stub);
        }

        default AsyncCaller asyncCaller(SimpleServiceGrpc.SimpleServiceStub stub) {
            return new AsyncCaller(stub);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {

        fun blockingCaller(stub: SimpleServiceGrpc.SimpleServiceBlockingStub) = BlockingCaller(stub)

        fun futureCaller(stub: SimpleServiceGrpc.SimpleServiceFutureStub) = FutureCaller(stub)

        fun asyncCaller(stub: SimpleServiceGrpc.SimpleServiceStub) = AsyncCaller(stub)

        fun coroutineCaller(stub: SimpleServiceGrpcKt.SimpleServiceCoroutineStub) = CoroutineCaller(stub) //(1)!
    }
    ```

    1. Требует [генератор gRPC Kotlin](#plugin). Сгенерированный stub наследует `io.grpc.kotlin.AbstractCoroutineStub` и помечен аннотацией `@StubFor`;
       KSP-процессор рядом с ним создаёт Kora-модуль `@Module`, который публикует этот stub как `@DefaultComponent`, связанный с `Channel` нужного тега.
       Kora подхватывает такой модуль автоматически, наследовать его вручную не нужно, а компонент можно переопределить, объявив свой.

### Стили вызова { #call-styles }

Форма `rpc` в контракте `.proto` (одиночное значение или `stream` в запросе/ответе) определяет сигнатуру сгенерированного метода.
Примеры ниже расширяют базовый контракт всеми четырьмя стилями вызова:

```protobuf
service SimpleService {
  rpc unary(RequestEvent) returns (ResponseEvent) {}                     // unary
  rpc serverStream(RequestEvent) returns (stream ResponseEvent) {}       // server streaming
  rpc clientStream(stream RequestEvent) returns (ResponseEvent) {}       // client streaming
  rpc biDiStream(stream RequestEvent) returns (stream ResponseEvent) {}  // bidirectional streaming
}
```

Запросы собираются сгенерированными построителями сообщений (`RequestEvent.newBuilder()`).
В Java unary- и серверный стриминг доступны у `BlockingStub`, а клиентский и двунаправленный стриминг требуют асинхронного `Stub`
(блокирующего варианта у них нет). Корутинный stub для Kotlin выражает все стили через `suspend`-функции и `Flow<T>`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var request = RequestEvent.newBuilder().setName("bob").setCode("b1").build();

    // unary — BlockingStub
    ResponseEvent unary = blockingStub.unary(request);

    // unary — FutureStub
    ListenableFuture<ResponseEvent> future = futureStub.unary(request);

    // server streaming — BlockingStub returns an iterator
    Iterator<ResponseEvent> responses = blockingStub.serverStream(request);

    // server streaming — async Stub delivers results to a StreamObserver
    asyncStub.serverStream(request, new StreamObserver<>() {
        @Override public void onNext(ResponseEvent value) { /* ... */ }
        @Override public void onError(Throwable t) { /* ... */ }
        @Override public void onCompleted() { /* ... */ }
    });

    // client streaming — async Stub, write requests, read one response
    StreamObserver<ResponseEvent> responseObserver = new StreamObserver<>() {
        @Override public void onNext(ResponseEvent value) { /* single response */ }
        @Override public void onError(Throwable t) { /* ... */ }
        @Override public void onCompleted() { /* ... */ }
    };
    StreamObserver<RequestEvent> requestObserver = asyncStub.clientStream(responseObserver);
    requestObserver.onNext(request);
    requestObserver.onCompleted();

    // bidirectional streaming — async Stub, both sides stream
    StreamObserver<RequestEvent> bidi = asyncStub.biDiStream(responseObserver);
    bidi.onNext(request);
    bidi.onCompleted();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = RequestEvent.newBuilder().setName("bob").setCode("b1").build()

    // unary — suspend function
    val response: ResponseEvent = coroutineStub.unary(request)

    // server streaming — returns a Flow
    val serverFlow: Flow<ResponseEvent> = coroutineStub.serverStream(request)
    serverFlow.collect { event -> /* ... */ }

    // client streaming — accepts a Flow, returns a single response
    val clientResponse: ResponseEvent = coroutineStub.clientStream(flowOf(request))

    // bidirectional streaming — Flow in, Flow out
    val biDiFlow: Flow<ResponseEvent> = coroutineStub.biDiStream(flowOf(request))
    biDiFlow.collect { event -> /* ... */ }
    ```

Java-совместимые stub-классы работают в Kotlin точно так же, поэтому асинхронный `Stub` со `StreamObserver` остаётся доступен и там, где генератор корутин не подключён.

### Внедрение Channel и конфигурации { #inject-channel-config }

Для продвинутого или ручного создания stub можно внедрить исходный `io.grpc.Channel` и итоговый `GrpcClientConfig`,
пометив их тегом сгенерированного класса службы. Оба предоставляются расширением `GrpcClientExtension`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        default SomeService someService(@Tag(SimpleServiceGrpc.class) Channel channel,
                                        @Tag(SimpleServiceGrpc.class) GrpcClientConfig config) {
            return new SomeService(SimpleServiceGrpc.newBlockingStub(channel), config.url());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {

        fun someService(
            @Tag(SimpleServiceGrpc::class) channel: Channel,
            @Tag(SimpleServiceGrpc::class) config: GrpcClientConfig
        ): SomeService = SomeService(SimpleServiceGrpc.newBlockingStub(channel), config.url())
    }
    ```

## Перехватчики { #interceptors }

[Перехватчики](https://grpc.github.io/grpc-java/javadoc/io/grpc/ClientInterceptor.html) позволяют перехватывать запросы до того, как они будут переданы службам.

### По умолчанию { #default }

Для каждого клиента регистрируются следующие перехватчики:

- `GrpcClientTelemetryInterceptor` — открывает наблюдение телеметрии для вызова. Регистрируется всегда и становится сквозным, если логирование, метрики и трассировка выключены.
- `GrpcClientConfigInterceptor` — применяет `timeout` как `deadline` вызова, если у вызова его нет.

### Собственные { #custom }

В отличие от [HTTP-клиента](http-client.md#interceptors), у gRPC-перехватчиков нет уровней метода/класса/приложения.
Каждый перехватчик действует **в рамках одного клиента** — за счёт тега компонента со сгенерированным классом службы (`@Tag(SimpleServiceGrpc.class)`).
Зарегистрируйте перехватчик как компонент с этим тегом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(SimpleServiceGrpc.class)
    @Component
    public final class MyClientInterceptor implements ClientInterceptor {
        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
            LoggerFactory.getLogger(Application.class).info("INTERCEPTED");
            return next.newCall(method, callOptions);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class)
    @Component
    class MyClientInterceptor : ClientInterceptor {
        override fun <ReqT : Any, RespT : Any> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return next.newCall(method, callOptions)
        }
    }
    ```

### Общие для нескольких клиентов { #shared-interceptors }

У компонента ровно один `@Tag`, поэтому один экземпляр перехватчика не может обслуживать несколько клиентов.
Чтобы переиспользовать одну реализацию, объявите класс без `@Component` и опубликуйте его из модуля приложения по разу на каждый клиент, каждый раз со своим тегом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class SharedInterceptor implements ClientInterceptor {
        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
            return next.newCall(method, callOptions);
        }
    }

    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        @Tag(SimpleServiceGrpc.class)
        default ClientInterceptor simpleServiceSharedInterceptor() {
            return new SharedInterceptor();
        }

        @Tag(OtherServiceGrpc.class)
        default ClientInterceptor otherServiceSharedInterceptor() {
            return new SharedInterceptor();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class SharedInterceptor : ClientInterceptor {
        override fun <ReqT : Any, RespT : Any> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return next.newCall(method, callOptions)
        }
    }

    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {

        @Tag(SimpleServiceGrpc::class)
        fun simpleServiceSharedInterceptor(): ClientInterceptor = SharedInterceptor()

        @Tag(OtherServiceGrpc::class)
        fun otherServiceSharedInterceptor(): ClientInterceptor = SharedInterceptor()
    }
    ```

**Порядок выполнения:**

`ManagedChannelLifecycle` собирает все перехватчики с тегом службы как `All<ClientInterceptor>` и регистрирует их у построителя канала
в порядке: сначала ваши перехватчики, затем перехватчик телеметрии, затем перехватчик конфигурации/deadline.
gRPC выполняет зарегистрированные перехватчики в обратном порядке регистрации, поэтому вызов проходит так:

```
Call → Config (deadline) interceptor → Telemetry interceptor → Custom interceptors → gRPC Server
```

Отсюда два практических следствия: ваши перехватчики уже видят итоговый `deadline` в `CallOptions` и могут заменить его через `withDeadlineAfter`,
а всё, что они делают, попадает внутрь span телеметрии и в измеряемую длительность вызова.
Относительный порядок нескольких собственных перехватчиков — это обратный порядок их объявления в графе; не стройте на нём логику.

Также можно изменить `stub` с помощью [GraphInterceptor](container.md#component-inspection).

## Авторизация { #authorization }

У gRPC нет отдельного модуля авторизации: авторизация делается перехватчиком `ClientInterceptor` с тегом класса службы, который добавляет
заголовок `Authorization` (или API-ключ) в `Metadata` исходящего вызова. Перехватчик оборачивает вызов в `ForwardingClientCall.SimpleForwardingClientCall`
и кладёт заголовок в `start(...)`, до отправки запроса.

### Bearer { #bearer }

Перехватчик [Bearer](https://swagger.io/docs/specification/authentication/bearer-authentication/) берёт токен у вашего поставщика и
кладёт его в заголовок `Authorization` каждого вызова. `TokenProvider` ниже — ваш собственный компонент:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(SimpleServiceGrpc.class)
    @Component
    public final class BearerAuthInterceptor implements ClientInterceptor {

        private static final Metadata.Key<String> AUTHORIZATION =
            Metadata.Key.of("Authorization", Metadata.ASCII_STRING_MARSHALLER);

        private final TokenProvider tokenProvider;

        public BearerAuthInterceptor(TokenProvider tokenProvider) {
            this.tokenProvider = tokenProvider;
        }

        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
            return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, callOptions)) {
                @Override
                public void start(Listener<RespT> responseListener, Metadata headers) {
                    headers.put(AUTHORIZATION, "Bearer " + tokenProvider.getToken());
                    super.start(responseListener, headers);
                }
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class)
    @Component
    class BearerAuthInterceptor(private val tokenProvider: TokenProvider) : ClientInterceptor {

        override fun <ReqT : Any, RespT : Any> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return object : ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(next.newCall(method, callOptions)) {
                override fun start(responseListener: Listener<RespT>, headers: Metadata) {
                    headers.put(AUTHORIZATION, "Bearer " + tokenProvider.getToken())
                    super.start(responseListener, headers)
                }
            }
        }

        companion object {
            private val AUTHORIZATION: Metadata.Key<String> =
                Metadata.Key.of("Authorization", Metadata.ASCII_STRING_MARSHALLER)
        }
    }
    ```

### ApiKey { #apikey }

Перехватчик [API-ключа](https://swagger.io/docs/specification/authentication/api-keys/) кладёт статический ключ в собственный заголовок metadata (например, `X-API-KEY`).
Ключ читается из интерфейса [`@ConfigSource`](config.md), внедрённого в перехватчик:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(SimpleServiceGrpc.class)
    @Component
    public final class ApiKeyInterceptor implements ClientInterceptor {

        private static final Metadata.Key<String> API_KEY =
            Metadata.Key.of("X-API-KEY", Metadata.ASCII_STRING_MARSHALLER);

        private final String apiKey;

        public ApiKeyInterceptor(ApiKeyConfig config) { //(1)!
            this.apiKey = config.value();
        }

        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
            return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, callOptions)) {
                @Override
                public void start(Listener<RespT> responseListener, Metadata headers) {
                    headers.put(API_KEY, apiKey);
                    super.start(responseListener, headers);
                }
            };
        }
    }
    ```

    1. Любой интерфейс `@ConfigSource`, отдающий API-ключ, например `@ConfigSource("auth.apiKey") public interface ApiKeyConfig { String value(); }`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class)
    @Component
    class ApiKeyInterceptor(config: ApiKeyConfig) : ClientInterceptor { //(1)!

        private val apiKey: String = config.value()

        override fun <ReqT : Any, RespT : Any> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return object : ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(next.newCall(method, callOptions)) {
                override fun start(responseListener: Listener<RespT>, headers: Metadata) {
                    headers.put(API_KEY, apiKey)
                    super.start(responseListener, headers)
                }
            }
        }

        companion object {
            private val API_KEY: Metadata.Key<String> =
                Metadata.Key.of("X-API-KEY", Metadata.ASCII_STRING_MARSHALLER)
        }
    }
    ```

    1. Любой интерфейс `@ConfigSource`, отдающий API-ключ, например `@ConfigSource("auth.apiKey") interface ApiKeyConfig { fun value(): String }`

## Обработка ошибок { #error-handling }

Неудачный gRPC-вызов бросает `io.grpc.StatusRuntimeException`. Его `getStatus()` несёт `Status.Code`
([коды статусов](https://grpc.io/docs/guides/status-codes/)), например `UNAVAILABLE` (сервер недоступен), `DEADLINE_EXCEEDED` (истёк `timeout`/deadline),
`UNAUTHENTICATED` (учётные данные отклонены) или `INVALID_ARGUMENT`. Metadata ответа доступна через `getTrailers()`.

**Причины:**

- `UNAVAILABLE` — неверный `url`, несовпадение plaintext/TLS или сервер не работает.
- `DEADLINE_EXCEEDED` — превышен настроенный `timeout` или заданный для вызова `withDeadlineAfter`.
- `UNAUTHENTICATED` / `PERMISSION_DENIED` — отсутствующая или неверная metadata авторизации.

**Рекомендации:**

- Ветвитесь по `e.getStatus().getCode()`, а не по типу исключения.
- Для временных сбоев используйте аспекты [resilient](resilient.md) (`@Retryable`, `@CircuitBreakable`, `@Timeout`) на методе обёртывающей службы.

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        var response = stub.createUser(request);
    } catch (StatusRuntimeException e) {
        var code = e.getStatus().getCode();
        if (code == Status.Code.DEADLINE_EXCEEDED) {
            // timeout / deadline exceeded
        } else if (code == Status.Code.UNAVAILABLE) {
            // server unreachable
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        val response = stub.createUser(request)
    } catch (e: StatusRuntimeException) {
        when (e.status.code) {
            Status.Code.DEADLINE_EXCEEDED -> { /* timeout / deadline exceeded */ }
            Status.Code.UNAVAILABLE -> { /* server unreachable */ }
            else -> throw e
        }
    }
    ```

Сам запуск канала не роняет приложение: `ManagedChannelLifecycle` пишет предупреждение, если первая проба `getState(true)` не удалась,
а соединение будет установлено позже, при вызове. Ошибки конфигурации, наоборот, ломают сборку графа — отсутствующий `url` или неподдерживаемая схема прерывают запуск.

## Тестирование { #testing }

gRPC-клиент тестируется как любой другой компонент Kora с помощью [`@KoraAppTest`](junit5.md).
Реализуйте `KoraAppTestConfigModifier`, чтобы задать `url` (через ту же подстановку переменной окружения, что используется в конфигурации приложения),
внедрите службу на основе stub через `@TestComponent`, соберите запрос сгенерированным построителем и проверьте `StatusRuntimeException`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class GrpcClientTests implements KoraAppTestConfigModifier {

        @TestComponent
        private RootService service;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty("GRPC_URL", "http://localhost:8090");
        }

        @Test
        void createUser() {
            var event = Message.RequestEvent.newBuilder()
                .setName("bob")
                .setCode("b1")
                .build();

            var stub = service.service();
            assertThrows(StatusRuntimeException.class, () -> stub.createUser(event));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class GrpcClientTests : KoraAppTestConfigModifier {

        @TestComponent
        lateinit var service: RootService

        override fun config(): KoraConfigModification =
            KoraConfigModification.ofSystemProperty("GRPC_URL", "http://localhost:8090")

        @Test
        fun createUser() {
            val event = Message.RequestEvent.newBuilder()
                .setName("bob")
                .setCode("b1")
                .build()

            val stub = service.service()
            assertThrows(StatusRuntimeException::class.java) { stub.createUser(event) }
        }
    }
    ```

## Телеметрия { #telemetry }

gRPC Client использует контракт телеметрии для логирования, метрик и трассировки вызовов.
Конфигурация телеметрии (секция `telemetry { logging / metrics / tracing }`) описана в разделе [Конфигурация](#configuration).
Точки расширения находятся в `io.koraframework.grpc.client.telemetry` и `io.koraframework.grpc.client.telemetry.impl`.

`GrpcClientTelemetryFactory` строит по одному `GrpcClientTelemetry` на клиент из `GrpcClientTelemetryConfig`, `ServiceDescriptor` и целевого `URI`.
Для каждого gRPC-вызова `GrpcClientTelemetry.observe(...)` создаёт `GrpcClientObservation`, который получает события `observeStart`, `observeSend`, `observeReceive`,
`observeClose` и `observeError` и закрывается вызовом `end()` по завершении вызова.

Фабрика по умолчанию `DefaultGrpcClientTelemetryFactory` объединяет:

- `Tracer` из OpenTelemetry — span вида `CLIENT` на каждый вызов с именем полного gRPC-метода и атрибутами `rpc.system`, `rpc.service`, `rpc.method`, `server.address`, `server.port`;
- `MeterRegistry` из Micrometer — таймер `rpc.client.duration` с настроенными корзинами `slo`;
- `DefaultGrpcClientLoggerFactory` — логи начала и конца вызова в логгеры `<serviceName>.request` и `<serviceName>.response`, где `serviceName` — полное имя службы `protobuf`. Заголовки запроса и ответа добавляются на уровне `DEBUG`;
- `DefaultGrpcClientMetricsFactory` — саму реализацию метрик.

Если для клиента выключены логирование, метрики и трассировка, фабрика возвращает `NoopGrpcClientTelemetry`, а перехватчик телеметрии становится сквозным.
Дополнительно метрикам нужен `MeterRegistry` в графе, а трассировке — `Tracer`; без них соответствующая часть остаётся выключенной независимо от конфигурации.

Метрики и трассировка описаны в разделе [Справочник метрик](metrics.md#grpc-client).
