Модуль для подключения gRPC клиентов на основе функционала [grpc.io](https://grpc.io/docs/languages/java/basics/)

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-client"
    implementation "io.grpc:grpc-protobuf:1.62.2"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends GrpcClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:grpc-client")
    implementation("io.grpc:grpc-protobuf:1.62.2")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : GrpcClientModule
    ```

### Плагин

Код для gRPC-клиента создается с помощью [protobuf gradle plugin](https://github.com/google/protobuf-gradle-plugin).

===! ":fontawesome-brands-java: `Java`"

    Плагин `build.gradle`:
    ```groovy
    plugins {
        id "com.google.protobuf" version "0.9.4"
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.25.3" }
        plugins {
            grpc { artifact = "io.grpc:protoc-gen-grpc-java:1.62.2" }
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
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.62.2" }
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

## Конфигурация

Сервис gRPC с именем `SimpleService` будет иметь конфигурацию с путем `grpcClient.SimpleService`.

Пример полной конфигурации, описанной в классе `GrpcClientConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcClient {
        SimpleService {
            url = "grpc://localhost:8090" //(1)!
            timeout = "10s"  //(2)!
            keepAliveTime = "0s" //(3)!
            keepAliveTimeout = "0s" //(4)!
            loadBalancingPolicy = "pick_first" //(5)!
            telemetry {
                logging {
                    enabled = false //(6)!
                }
                metrics {
                    enabled = true //(7)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(8)!
                }
                tracing {
                    enabled = true //(9)!
                }
            }
        }
    }
    ```

    1.  URL сервера куда делать запросы (**обязательный**)
    2.  Максимальное время запроса (по умолчанию отсутвует)
    3.  Устанавливает интервал времени между PING фреймами
    4.  Таймаут времени для подтверждения PING фрейма. Если отправитель не получил подтверждение за данное время, соединение будет закрыто
    5.  Устанавливает политику балансировки
    6.  Включает логгирование модуля (по умолчанию `false`)
    7.  Включает метрики модуля (по умолчанию `true`)
    8.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    9.  Включает трассировку модуля (по умолчанию `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcClient:
      SimpleService:
        url: "grpc://localhost:8090" //(1)!
        timeout: "10s" //(2)!
        keepAliveTime: "0s" //(3)!
        keepAliveTimeout: "0s" //(4)!
        loadBalancingPolicy: "pick_first" //(5)!
        telemetry:
          logging:
            enabled: false #(6)!
          metrics:
            enabled: true #(7)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(8)!
          telemetry:
            enabled: true #(9)!
    ```

    1.  URL сервера куда делать запросы (**обязательный**)
    2.  Максимальное время запроса (по умолчанию отсутвует)
    3.  Устанавливает интервал времени между PING фреймами
    4.  Таймаут времени для подтверждения PING фрейма. Если отправитель не получил подтверждение за данное время, соединение будет закрыто
    5.  Устанавливает политику балансировки
    6.  Включает логгирование модуля (по умолчанию `false`)
    7.  Включает метрики модуля (по умолчанию `true`)
    8.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    9.  Включает трассировку модуля (по умолчанию `true`)

Можно также настроить [Netty транспорт](netty.md).

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#grpc-клиент).

## Сервис

Созданные gRPC сервисы можно внедрять как зависимости:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        default SomeService(SimpleServiceGrpc.SimpleServiceBlockingStub grpcService) {
            return new SomeService(grpcService);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {
        fun SomeService(grpcService: SimpleServiceGrpc.SimpleServiceBlockingStub?) {
            return SomeService(grpcService)
        }
    }
    ```

## Перехватчики

[Перехватчики](https://grpc.github.io/grpc-java/javadoc/io/grpc/ClientInterceptor.html) позволяют перехватывать запросы перед тем, как они будут переданы сервисам.

### Стандартные

При запуске клиента по-умолчанию используются следующие перехватчики:

- `GrpcClientConfigInterceptor`

### Собственные

Для добавления собственного перехватчика требуется зарегистрировать перехватчика как компонент с тегом сервиса.

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

Либо можно модифицировать сервис посредствам [GraphInterceptor](container.md#_26).
