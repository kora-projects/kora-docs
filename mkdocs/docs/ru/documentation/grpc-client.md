---
description: "Explains Kora gRPC client generation, protobuf Gradle plugin setup, client configuration, generated services, interceptors, and mapping. Use when working with GrpcClientModule, @GrpcClient, @InterceptWith, GrpcClientConfig, GrpcClientInterceptor, protobuf plugin."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora gRPC client generation, protobuf Gradle plugin setup, client configuration, generated services, interceptors, and mapping; key triggers include GrpcClientModule, @GrpcClient, @InterceptWith, GrpcClientConfig, GrpcClientInterceptor, protobuf plugin."
---

`gRPC-клиент` вызывает удаленные сервисы по контракту `protobuf` и использует транспорт `HTTP/2`.
В Kora клиент строится поверх сгенерированных `stub`-классов `grpc-java`: модуль создает `ManagedChannel`, подключает к нему перехватчики и регистрирует готовые `stub` в графе приложения.

Клиентский транспорт gRPC работает через Netty, поэтому общие параметры `event loop` и транспорта можно настраивать в разделе [Netty](netty.md).

Если нужен пошаговый разбор перед справочным описанием, смотрите [gRPC клиент](../guides/grpc-client.md) и [gRPC клиент продвинутый](../guides/grpc-client-advanced.md).

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

Код для `gRPC-клиента` создается с помощью [protobuf Gradle-плагина](https://github.com/google/protobuf-gradle-plugin).
Плагин генерирует Java-классы сообщений из `protobuf`-контракта и gRPC-`stub`, которые затем используются Kora.

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

`gRPC-клиент` для сервиса `SimpleService` будет иметь конфигурацию с путем `grpcClient.SimpleService`.

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

    1.  `URL` сервера, куда будут отправляться запросы (`обязательная`, по умолчанию не указано).
    2.  Максимальное время выполнения запроса (по умолчанию не указано, необязательно). Значение применяется как `deadline`, если у вызова еще нет своего `deadline`.
    3.  Интервал между `PING`-кадрами gRPC (по умолчанию не указано, необязательно).
    4.  Время ожидания подтверждения `PING`-кадра (по умолчанию не указано, необязательно). Если подтверждение не получено за это время, соединение будет закрыто.
    5.  Политика балансировки нагрузки для `ManagedChannelBuilder` (по умолчанию не указано, необязательно).
    6.  Стандартная gRPC-конфигурация сервиса, передаваемая в `ManagedChannelBuilder.defaultServiceConfig` (по умолчанию не указано, необязательно).
    7.  Включает логирование модуля (по умолчанию: `false`).
    8.  Включает метрики модуля (по умолчанию: `true`).
    9.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
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

    1.  `URL` сервера, куда будут отправляться запросы (`обязательная`, по умолчанию не указано).
    2.  Максимальное время выполнения запроса (по умолчанию не указано, необязательно). Значение применяется как `deadline`, если у вызова еще нет своего `deadline`.
    3.  Интервал между `PING`-кадрами gRPC (по умолчанию не указано, необязательно).
    4.  Время ожидания подтверждения `PING`-кадра (по умолчанию не указано, необязательно). Если подтверждение не получено за это время, соединение будет закрыто.
    5.  Политика балансировки нагрузки для `ManagedChannelBuilder` (по умолчанию не указано, необязательно).
    6.  Стандартная gRPC-конфигурация сервиса, передаваемая в `ManagedChannelBuilder.defaultServiceConfig` (по умолчанию не указано, необязательно).
    7.  Включает логирование модуля (по умолчанию: `false`).
    8.  Включает метрики модуля (по умолчанию: `true`).
    9.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    10. Дополнительные теги для метрик (по умолчанию: `{}`).
    11. Включает трассировку модуля (по умолчанию: `true`).
    12. Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

При создании канала схема `http` включает режим без TLS через `usePlaintext()`.
Если порт не указан явно, для схемы `http` используется порт `80`, а для `https` — `443`.

Если возможностей файловой конфигурации недостаточно, можно зарегистрировать компонент `GrpcClientBuilderConfigurer`.
Он получает уже подготовленный `ManagedChannelBuilder` и позволяет донастроить канал в коде перед его созданием.
Настройки из `GrpcClientConfig` применяются раньше, затем вызывается `GrpcClientBuilderConfigurer`.

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

Можно также настроить [транспорт Netty](netty.md).

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#grpc-client).

## Сервис { #service }

Созданные gRPC-`stub` можно внедрять как зависимости:

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

## Перехватчики { #interceptors }

[Перехватчики](https://grpc.github.io/grpc-java/javadoc/io/grpc/ClientInterceptor.html) позволяют перехватывать запросы перед тем, как они будут переданы сервисам.

### Стандартные { #default }

При запуске клиента по умолчанию используются следующие перехватчики:

- `GrpcClientConfigInterceptor`
- `GrpcClientTelemetryInterceptor`, если для клиента доступна телеметрия

### Собственные { #custom }

Для добавления собственного перехватчика требуется зарегистрировать `ClientInterceptor` как компонент с тегом сервиса.

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
        fun <ReqT, RespT> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return next.newCall(method, callOptions)
        }
    }
    ```

Либо можно модифицировать `stub` посредством [GraphInterceptor](container.md#indirect-dependency).
