Модуль для подключения gRPC клиентов на основе функционала [grpc.io](https://grpc.io/docs/languages/java/basics/)

## Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-client"
    implementation "io.grpc:grpc-protobuf:1.58.0"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends GrpcClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:grpc-client")
    implementation("io.grpc:grpc-protobuf:1.58.0")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : GrpcClientModule
    ```

## Конфигурация

Параметры, описанные в классе `GrpcClientConfig` и ниже показан пример конфигурации для сервиса с именем `UserService`:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcClient {
        UserService {
            url = "grpc://localhost:8090" //(1)!
            timeout = "10s"  //(2)!
            telemetry {
                logging {
                    enabled = true //(3)!
                }
                metrics {
                    enabled = true //(4)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(5)!
                }
                telemetry {
                    enabled = true //(6)!
                }
            }
        }
    }
    ```

    1.  URL сервера куда делать запросы
    2.  Максимальное время запроса
    3.  Включает логгирование модуля
    4.  Включает метрики модуля
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    6.  Включает трассировку модуля

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcClient:
      UserService:
        url: "grpc://localhost:8090" //(1)!
        timeout: "10s" //(2)!
        telemetry:
          logging:
            enabled: true #(1)!
          metrics:
            enabled: true #(2)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(3)!
          telemetry:
            enabled: true #(4)!
    ```

    1.  URL сервера куда делать запросы
    2.  Максимальное время запроса
    3.  Включает логгирование модуля
    4.  Включает метрики модуля
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    6.  Включает трассировку модуля

## Плагин

Код для gRPC-сервера можно создать с помощью [protobuf gradle plugin](https://github.com/google/protobuf-gradle-plugin).

=== ":fontawesome-brands-java: `Java`"

    Плагин `build.gradle`:
    ```groovy
    plugins {
        id "com.google.protobuf" version "0.9.4"
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.24.4" }
        plugins {
            grpc { artifact = "io.grpc:protoc-gen-grpc-java:1.58.0" }
        }

        generateProtoTasks {
            all()*.plugins { grpc {} }
        }
    }

    sourceSets {
        main {
            java {
                srcDirs "build/generated/source/proto/main/grpc"
                srcDirs "build/generated/source/proto/main/java"
            }
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
        protoc { artifact = "com.google.protobuf:protoc:3.24.4" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.58.0" }
        }

        generateProtoTasks {
            ofSourceSet("main").forEach {
                it.plugins { id("grpc") { } }
            }
        }
    }

    kotlin {
        sourceSets.main {
            kotlin.srcDir("build/generated/source/proto/main/grpc")
            kotlin.srcDir("build/generated/source/proto/main/java")
        }
    }
    ```

## Сервис

Созданные gRPC сервисы можно внедрять как зависимости:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        default SomeService(UserServiceGrpc.UserServiceBlockingStub grpcService) {
            return new SomeService(grpcService);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {
        fun SomeService(grpcService: UserServiceGrpc.UserServiceBlockingStub?) {
            return SomeService(grpcService)
        }
    }
    ```
