---
description: "Explains Kora gRPC client generation, protobuf Gradle plugin setup, client configuration, generated services, interceptors, and mapping. Use when working with GrpcClientModule, @GrpcClient, @InterceptWith, GrpcClientConfig, GrpcClientInterceptor, protobuf plugin."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora gRPC client generation, protobuf Gradle plugin setup, client configuration, generated services, interceptors, and mapping; key triggers include GrpcClientModule, @GrpcClient, @InterceptWith, GrpcClientConfig, GrpcClientInterceptor, protobuf plugin."
---

`gRPC-клиент` вызывает удалённые службы, используя контракт `protobuf` и транспорт `HTTP/2`.
В Kora клиент строится поверх сгенерированных классов `stub` библиотеки `grpc-java`: модуль создаёт `ManagedChannel`, подключает перехватчики и регистрирует готовые к использованию экземпляры `stub` в графе приложения.

Для каждой службы Kora делает доступными для внедрения сгенерированные stub-классы (`BlockingStub`, `FutureStub`, асинхронный `Stub` и корутинный stub для Kotlin),
исходный `io.grpc.Channel` и итоговый `GrpcClientConfig`, различая каждый клиент по `@Tag` сгенерированного класса службы
(например, `@Tag(SimpleServiceGrpc.class)`).

Транспорт gRPC-клиента использует Netty, поэтому общие настройки `event loop` и транспорта можно задать в разделе [Netty](netty.md).

Если нужен пошаговый разбор перед справочным описанием, смотрите [gRPC-клиент](../guides/grpc-client.md) и [продвинутый gRPC-клиент](../guides/grpc-client-advanced.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-client"
    implementation "io.grpc:grpc-protobuf:1.74.0"
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
    implementation("ru.tinkoff.kora:grpc-client")
    implementation("io.grpc:grpc-protobuf:1.74.0")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : GrpcClientModule
    ```

### Плагин { #plugin }

Код `gRPC-клиента` создаётся с помощью [Gradle-плагина protobuf](https://github.com/google/protobuf-gradle-plugin).
Плагин генерирует классы Java-сообщений из контракта `protobuf` и gRPC-классы `stub`, которые затем используются Kora.

===! ":fontawesome-brands-java: `Java`"

    Плагин `build.gradle`:
    ```groovy
    plugins {
        id "com.google.protobuf" version "0.9.4"
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.25.3" }
        plugins {
            grpc { artifact = "io.grpc:protoc-gen-grpc-java:1.74.0" }
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
        id("com.google.protobuf") version ("0.9.4")
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.25.3" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.74.0" }
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

## Конфигурация { #configuration }

`gRPC-клиент` для службы `SimpleService` будет иметь путь конфигурации `grpcClient.SimpleService`.

Пример полной конфигурации, описанной в классе `GrpcClientConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcClient {
        SimpleService {
            url = "http://localhost:8090" //(1)!
            timeout = "10s"  //(2)!
            keepAliveTime = "0s" //(3)!
            keepAliveTimeout = "0s" //(4)!
            loadBalancingPolicy = "pick_first" //(5)!
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
                    enabled = true //(8)!
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

    1. `URL` сервера, куда будут отправляться запросы (`обязательная`, по умолчанию не указано).
    2. Максимальное время выполнения запроса (по умолчанию не указано, необязательно). Значение применяется как `deadline`, если у вызова ещё нет собственного `deadline`.
    3. Интервал между gRPC-фреймами `PING` (по умолчанию не указано, необязательно).
    4. Время ожидания подтверждения фрейма `PING` (по умолчанию не указано, необязательно). Если подтверждение не получено за это время, соединение закрывается.
    5. Политика балансировки нагрузки для `ManagedChannelBuilder` (по умолчанию не указано, необязательно).
    6. Стандартная конфигурация службы gRPC, передаваемая в `ManagedChannelBuilder.defaultServiceConfig` (по умолчанию не указано, необязательно).
    7. Включает логирование модуля (по умолчанию: `false`).
    8. Включает метрики модуля (по умолчанию: `true`).
    9. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    10. Дополнительные теги для метрик (по умолчанию: `{}`).
    11. Включает трассировку модуля (по умолчанию: `true`).
    12. Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcClient:
      SimpleService:
        url: "http://localhost:8090" #(1)!
        timeout: "10s" #(2)!
        keepAliveTime: "0s" #(3)!
        keepAliveTimeout: "0s" #(4)!
        loadBalancingPolicy: "pick_first" #(5)!
        defaultServiceConfig: #(6)!
          loadBalancingConfig:
            - round_robin: {}
        telemetry:
          logging:
            enabled: false #(7)!
          metrics:
            enabled: true #(8)!
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

    1. `URL` сервера, куда будут отправляться запросы (`обязательная`, по умолчанию не указано).
    2. Максимальное время выполнения запроса (по умолчанию не указано, необязательно). Значение применяется как `deadline`, если у вызова ещё нет собственного `deadline`.
    3. Интервал между gRPC-фреймами `PING` (по умолчанию не указано, необязательно).
    4. Время ожидания подтверждения фрейма `PING` (по умолчанию не указано, необязательно). Если подтверждение не получено за это время, соединение закрывается.
    5. Политика балансировки нагрузки для `ManagedChannelBuilder` (по умолчанию не указано, необязательно).
    6. Стандартная конфигурация службы gRPC, передаваемая в `ManagedChannelBuilder.defaultServiceConfig` (по умолчанию не указано, необязательно).
    7. Включает логирование модуля (по умолчанию: `false`).
    8. Включает метрики модуля (по умолчанию: `true`).
    9. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    10. Дополнительные теги для метрик (по умолчанию: `{}`).
    11. Включает трассировку модуля (по умолчанию: `true`).
    12. Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

### Транспорт и TLS { #transport-tls }

Схема в `url` выбирает транспорт при создании `ManagedChannel` (`ManagedChannelLifecycle`):

- `http` — незашифрованный транспорт `plaintext` (`usePlaintext()` у построителя), порт по умолчанию `80`, если порт не указан.
- `https` — транспорт `TLS`, порт по умолчанию `443`, если порт не указан.
- любая другая схема — порт должен быть указан явно, иначе при определении порта по умолчанию во время запуска будет выброшено исключение `IllegalArgumentException` с сообщением `Unknown scheme '<scheme>'`. Режим `plaintext` включается только для схемы `http`, поэтому остальные схемы используют транспорт gRPC по умолчанию (`TLS`), если недоступен порт `plaintext`.

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcClient {
        SimpleService {
            url = "http://localhost:8090" // plaintext, порт по умолчанию 80
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcClient:
      SimpleService:
        url: "http://localhost:8090" # plaintext, порт по умолчанию 80
    ```

Для нестандартного `TLS` (`mTLS`, собственное хранилище доверенных сертификатов или транспорт, отличный от Netty) зарегистрируйте свой компонент `GrpcClientChannelFactory`.
Он создаёт `ManagedChannelBuilder` и может передавать `io.grpc.ChannelCredentials`; реализация по умолчанию — `GrpcNettyClientChannelFactory`,
которая привязывает канал к общей для Kora группе Netty `EventLoopGroup`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class TlsGrpcClientChannelFactory implements GrpcClientChannelFactory {

        @Override
        public ManagedChannelBuilder<?> forAddress(SocketAddress serverAddress) {
            return NettyChannelBuilder.forAddress(serverAddress);
        }

        @Override
        public ManagedChannelBuilder<?> forAddress(SocketAddress serverAddress, ChannelCredentials creds) {
            return NettyChannelBuilder.forAddress(serverAddress, creds);
        }

        @Override
        public ManagedChannelBuilder<?> forTarget(String target) {
            return NettyChannelBuilder.forTarget(target);
        }

        @Override
        public ManagedChannelBuilder<?> forTarget(String target, ChannelCredentials creds) {
            return NettyChannelBuilder.forTarget(target, creds);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class TlsGrpcClientChannelFactory : GrpcClientChannelFactory {

        override fun forAddress(serverAddress: SocketAddress): ManagedChannelBuilder<*> {
            return NettyChannelBuilder.forAddress(serverAddress)
        }

        override fun forAddress(serverAddress: SocketAddress, creds: ChannelCredentials): ManagedChannelBuilder<*> {
            return NettyChannelBuilder.forAddress(serverAddress, creds)
        }

        override fun forTarget(target: String): ManagedChannelBuilder<*> {
            return NettyChannelBuilder.forTarget(target)
        }

        override fun forTarget(target: String, creds: ChannelCredentials): ManagedChannelBuilder<*> {
            return NettyChannelBuilder.forTarget(target, creds)
        }
    }
    ```

Реализация для промышленного окружения также должна привязывать построитель к общей для Kora группе Netty `EventLoopGroup` и `NettyChannelFactory`
так же, как это делает `GrpcNettyClientChannelFactory`, вместо того чтобы позволять Netty создавать собственный event loop.

### Таймауты и deadline { #timeouts }

Значение `timeout` применяется всегда включённым перехватчиком `GrpcClientConfigInterceptor` как `deadline` вызова, но **только если у вызова нет собственного deadline**.
Заданный для конкретного вызова deadline через stub всегда имеет приоритет над настроенным `timeout`:

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

### Keep-alive, балансировка нагрузки и конфигурация службы { #keepalive-lb }

- `keepAliveTime` / `keepAliveTimeout` соответствуют настройкам `PING` у `ManagedChannelBuilder`. `keepAliveTime` — интервал между фреймами `PING` протокола `HTTP/2` на простаивающем соединении; `keepAliveTimeout` — как долго ждать подтверждения `PING` перед закрытием соединения. Оба отключены, если не заданы.
- `loadBalancingPolicy` соответствует `ManagedChannelBuilder.defaultLoadBalancingPolicy`. Значение по умолчанию в gRPC — `pick_first` (единственное соединение с первым разрешённым адресом); `round_robin` распределяет вызовы по всем разрешённым адресам и обычно используется с DNS-адресами, возвращающими несколько записей `A`/`AAAA`.
- `defaultServiceConfig` передаётся как есть в `ManagedChannelBuilder.defaultServiceConfig` и содержит нативную карту [конфигурации службы](https://github.com/grpc/grpc/blob/master/doc/service_config.md) gRPC (`loadBalancingConfig`, `methodConfig` для отдельных методов с политикой повторов/хеджирования и т. д.). Она описана обёрткой `DefaultServiceConfig` над `Map<String, Object>`.

### Настройщик построителя канала { #builder-configurer }

Если конфигурации через файл недостаточно, можно зарегистрировать компонент `GrpcClientBuilderConfigurer`.
Он получает уже подготовленный `ManagedChannelBuilder` и позволяет настроить канал в коде до его создания.
Сначала применяются настройки из `GrpcClientConfig`, затем вызывается `GrpcClientBuilderConfigurer`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CustomGrpcClientBuilderConfigurer implements GrpcClientBuilderConfigurer {
        @Override
        public ManagedChannelBuilder<?> configure(ManagedChannelBuilder<?> builder) {
            return builder.maxInboundMessageSize(8 * 1024 * 1024);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CustomGrpcClientBuilderConfigurer : GrpcClientBuilderConfigurer {
        override fun configure(builder: ManagedChannelBuilder<*>): ManagedChannelBuilder<*> {
            return builder.maxInboundMessageSize(8 * 1024 * 1024)
        }
    }
    ```

Также можно настроить [транспорт Netty](netty.md).

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#grpc-client).

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

stub также можно внедрить напрямую в конструктор `@Component`:

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

### Типы stub { #stub-types }

Плагин `protobuf` генерирует для одной службы (`SimpleService`) несколько stub-классов. Каждый доступен для внедрения простым объявлением соответствующего типа;
на самом stub указывать `@Tag` не нужно (Kora самостоятельно разрешает помеченный тегом `Channel`):

| Тип stub                               | Модель вызова                                                          | Когда использовать                                   |
|----------------------------------------|------------------------------------------------------------------------|------------------------------------------------------|
| `SimpleServiceBlockingStub`            | Синхронная; возвращает ответ напрямую (или `Iterator` для серверной потоковой передачи) | Блокирующий код, простейший стиль вызова             |
| `SimpleServiceFutureStub`              | Асинхронная; возвращает `ListenableFuture<T>` (только унарные вызовы)  | Неблокирующий код с использованием `ListenableFuture`|
| `SimpleServiceStub` (асинхронный)      | Асинхронная; передаёт результаты через обратные вызовы `StreamObserver<T>` | Любая потоковая передача, асинхронные вызовы на обратных вызовах |
| Корутинный stub для Kotlin             | `suspend`-функции и `Flow<T>`                                          | Идиоматичные корутины Kotlin                         |

`BlockingStub`, `FutureStub` и асинхронный `Stub` связываются расширением обработчика аннотаций (`GrpcClientExtension`), которое обнаруживает stub-типы `@GrpcGenerated`
и вызывает сгенерированную фабрику `newBlockingStub` / `newFutureStub` / `newStub` для помеченного тегом `Channel`.

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
    }
    ```

Для вызовов на корутинах Kotlin сгенерируйте корутинный stub с помощью [генератора gRPC Kotlin](https://github.com/grpc/grpc-kotlin)
(`io.grpc:protoc-gen-grpc-kotlin`). Сгенерированный stub наследуется от `io.grpc.kotlin.AbstractCoroutineStub` и помечен аннотацией `@StubFor`;
далее обработчик символов KSP генерирует модуль Kora, который предоставляет его как `@DefaultComponent`, привязанный к помеченному тегом `Channel`, поэтому он внедряется таким же образом:

===! ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {

        fun coroutineCaller(stub: SimpleServiceGrpcKt.SimpleServiceCoroutineStub) = CoroutineCaller(stub)
    }
    ```

### Стили вызова { #call-styles }

Форма `rpc` в контракте `.proto` (одиночный или `stream` запрос/ответ) определяет сигнатуру сгенерированного метода.
В примерах ниже базовый контракт дополнен всеми четырьмя стилями вызова:

```protobuf
service SimpleService {
  rpc unary(RequestEvent) returns (ResponseEvent) {}                     // унарный
  rpc serverStream(RequestEvent) returns (stream ResponseEvent) {}       // серверная потоковая передача
  rpc clientStream(stream RequestEvent) returns (ResponseEvent) {}       // клиентская потоковая передача
  rpc biDiStream(stream RequestEvent) returns (stream ResponseEvent) {}  // двунаправленная потоковая передача
}
```

Запросы создаются с помощью сгенерированных построителей сообщений (`RequestEvent.newBuilder()`).
В Java унарные вызовы и серверная потоковая передача доступны у `BlockingStub`, тогда как клиентская потоковая передача и двунаправленные вызовы требуют асинхронного `Stub`
(у них нет блокирующего варианта). Корутинный stub Kotlin выражает каждый стиль через `suspend`-функции и `Flow<T>`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var request = RequestEvent.newBuilder().setName("bob").setCode("b1").build();

    // унарный — BlockingStub
    ResponseEvent unary = blockingStub.unary(request);

    // унарный — FutureStub
    ListenableFuture<ResponseEvent> future = futureStub.unary(request);

    // серверная потоковая передача — BlockingStub возвращает итератор
    Iterator<ResponseEvent> responses = blockingStub.serverStream(request);

    // серверная потоковая передача — асинхронный Stub передаёт результаты в StreamObserver
    asyncStub.serverStream(request, new StreamObserver<>() {
        @Override public void onNext(ResponseEvent value) { /* ... */ }
        @Override public void onError(Throwable t) { /* ... */ }
        @Override public void onCompleted() { /* ... */ }
    });

    // клиентская потоковая передача — асинхронный Stub, пишем запросы, читаем один ответ
    StreamObserver<ResponseEvent> responseObserver = new StreamObserver<>() {
        @Override public void onNext(ResponseEvent value) { /* единственный ответ */ }
        @Override public void onError(Throwable t) { /* ... */ }
        @Override public void onCompleted() { /* ... */ }
    };
    StreamObserver<RequestEvent> requestObserver = asyncStub.clientStream(responseObserver);
    requestObserver.onNext(request);
    requestObserver.onCompleted();

    // двунаправленная потоковая передача — асинхронный Stub, потоки с обеих сторон
    StreamObserver<RequestEvent> bidi = asyncStub.biDiStream(responseObserver);
    bidi.onNext(request);
    bidi.onCompleted();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = RequestEvent.newBuilder().setName("bob").setCode("b1").build()

    // унарный — suspend-функция
    val response: ResponseEvent = coroutineStub.unary(request)

    // серверная потоковая передача — возвращает Flow
    val serverFlow: Flow<ResponseEvent> = coroutineStub.serverStream(request)
    serverFlow.collect { event -> /* ... */ }

    // клиентская потоковая передача — принимает Flow, возвращает один ответ
    val clientResponse: ResponseEvent = coroutineStub.clientStream(flowOf(request))

    // двунаправленная потоковая передача — Flow на вход, Flow на выход
    val biDiFlow: Flow<ResponseEvent> = coroutineStub.biDiStream(flowOf(request))
    biDiFlow.collect { event -> /* ... */ }
    ```

### Внедрение Channel и конфигурации { #inject-channel-config }

Для продвинутого или ручного создания stub можно внедрить исходный `io.grpc.Channel` и итоговый `GrpcClientConfig`,
пометив их сгенерированным классом службы. Оба предоставляются `GrpcClientExtension`:

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

По умолчанию при запуске клиента используются следующие перехватчики:

- `GrpcClientConfigInterceptor` — применяет `timeout` как `deadline` вызова, если у вызова его нет.
- `GrpcClientTelemetryInterceptor`, если для клиента доступна телеметрия.

### Собственные { #custom }

В отличие от [HTTP-клиента](http-client.md#interceptors), у перехватчиков gRPC нет уровней метода/класса/глобального уровня.
Каждый перехватчик действует **в пределах одного клиента** — за счёт пометки компонента сгенерированным классом службы (`@Tag(SimpleServiceGrpc.class)`).
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

Чтобы применить один компонент-перехватчик к нескольким клиентам («общий» перехватчик), укажите ему несколько значений `@Tag` — по одному сгенерированному классу службы на каждый клиент:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag({SimpleServiceGrpc.class, OtherServiceGrpc.class})
    @Component
    public final class SharedInterceptor implements ClientInterceptor {
        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
            return next.newCall(method, callOptions);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class, OtherServiceGrpc::class)
    @Component
    class SharedInterceptor : ClientInterceptor {
        override fun <ReqT : Any, RespT : Any> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return next.newCall(method, callOptions)
        }
    }
    ```

**Порядок выполнения:**

`ManagedChannelLifecycle` собирает все перехватчики, помеченные для службы, как `All<ClientInterceptor>` и применяет их в фиксированном порядке:
сначала ваши собственные перехватчики, затем перехватчик телеметрии (если телеметрия включена), и последним — перехватчик конфигурации/deadline.

```
Запрос → Собственные перехватчики → Перехватчик телеметрии → Перехватчик конфигурации (deadline) → gRPC-сервер
```

Поскольку перехватчик deadline выполняется последним, deadline, установленный собственным перехватчиком в `CallOptions`, сохраняется, а настроенный `timeout`
применяется только тогда, когда его не задал ни один более ранний перехватчик (или `withDeadlineAfter` для конкретного вызова).

В качестве альтернативы можно изменить `stub` с помощью [GraphInterceptor](container.md#component-inspection).

## Авторизация { #authorization }

В gRPC нет отдельного модуля авторизации: авторизация выполняется с помощью `ClientInterceptor`, помеченного классом службы, который добавляет заголовок
`Authorization` (или API-ключа) в `Metadata` исходящего вызова. Перехватчик оборачивает вызов в `ForwardingClientCall.SimpleForwardingClientCall`
и помещает заголовок в `start(...)`, до отправки запроса.

### Bearer { #bearer }

Перехватчик [Bearer](https://swagger.io/docs/specification/authentication/bearer-authentication/) читает токен из вашего собственного поставщика и
помещает его в заголовок `Authorization` каждого вызова. `TokenProvider` ниже — ваш собственный компонент:

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

Перехватчик [API-ключа](https://swagger.io/docs/specification/authentication/api-keys/) помещает статический ключ в собственный заголовок метаданных (например, `X-API-KEY`).
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
            this.apiKey = config.apiKey();
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

    1. Любой интерфейс `@ConfigSource`, предоставляющий API-ключ, например `String apiKey();`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class)
    @Component
    class ApiKeyInterceptor(config: ApiKeyConfig) : ClientInterceptor { //(1)!

        private val apiKey: String = config.apiKey()

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

    1. Любой интерфейс `@ConfigSource`, предоставляющий API-ключ, например `fun apiKey(): String`

## Обработка ошибок { #error-handling }

Неуспешный вызов gRPC выбрасывает `io.grpc.StatusRuntimeException`. Его `getStatus()` несёт `Status.Code`
([коды статусов](https://grpc.io/docs/guides/status-codes/)), например `UNAVAILABLE` (сервер недоступен), `DEADLINE_EXCEEDED` (истёк `timeout`/deadline),
`UNAUTHENTICATED` (отклонённые учётные данные) или `INVALID_ARGUMENT`. Метаданные ответа доступны через `getTrailers()`.

**Причины:**

- `UNAVAILABLE` — неверный `url`, несоответствие plaintext/TLS или сервер не работает.
- `DEADLINE_EXCEEDED` — превышен настроенный `timeout` или `withDeadlineAfter` для конкретного вызова.
- `UNAUTHENTICATED` / `PERMISSION_DENIED` — отсутствуют или недействительны метаданные авторизации.

**Рекомендации:**

- Ветвитесь по `e.getStatus().getCode()`, а не по типу исключения.
- Используйте аспекты [отказоустойчивости](resilient.md) (`@Retry`, `@CircuitBreaker`, `@Timeout`) на оборачивающем методе службы для временных сбоев.

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        var response = stub.createUser(request);
    } catch (StatusRuntimeException e) {
        var code = e.getStatus().getCode();
        if (code == Status.Code.DEADLINE_EXCEEDED) {
            // превышен timeout / deadline
        } else if (code == Status.Code.UNAVAILABLE) {
            // сервер недоступен
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        val response = stub.createUser(request)
    } catch (e: StatusRuntimeException) {
        when (e.status.code) {
            Status.Code.DEADLINE_EXCEEDED -> { /* превышен timeout / deadline */ }
            Status.Code.UNAVAILABLE -> { /* сервер недоступен */ }
            else -> throw e
        }
    }
    ```

## Тестирование { #testing }

gRPC-клиент тестируется как любой другой компонент Kora с помощью [`@KoraAppTest`](junit5.md).
Реализуйте `KoraAppTestConfigModifier`, чтобы задать `url` (например, через подстановку переменной окружения `GRPC_URL`, используемую в примере),
внедрите службу на основе stub через `@TestComponent`, соберите запрос сгенерированным построителем и проверьте `StatusRuntimeException`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class GrpcClientTests implements KoraAppTestConfigModifier {

        @TestComponent
        private RootService service;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty("GRPC_URL", "grpc://localhost:8090");
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
            KoraConfigModification.ofSystemProperty("GRPC_URL", "grpc://localhost:8090")

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

Логирование, метрики и трассировка по умолчанию настраиваются через блок `telemetry` в [конфигурации](#configuration) и
описаны в разделе [Справочник метрик](metrics.md#grpc-client).

Чтобы настроить собираемые сигналы, переопределите SPI-фабрики телеметрии как компоненты: `GrpcClientTelemetryFactory`
(вся телеметрия), `GrpcClientLoggerFactory`, `GrpcClientMetricsFactory` или `GrpcClientTracerFactory`.
Реализации по умолчанию связываются `GrpcClientModule`; предоставление собственного компонента заменяет соответствующую реализацию по умолчанию.
