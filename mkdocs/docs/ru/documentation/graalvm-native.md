Kora создает свои вспомогательные классы во время компиляции, 
не использует Reflection API во время работы, 
не использует динамических прокси,
не использует генерацию байт-кода во время компиляции и во время работы,
так что проблем для сборки нативного образа со стороны самой Kora нет.

Пример сборки нативного образа с помощью [плагина](https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html) для `gradle`:

===! ":fontawesome-brands-java: `Java`"

    Плагин `build.gradle`:
    ```groovy
    plugins {
        id "org.graalvm.buildtools.native" version "0.10.4"
    }
    ```

    Настройка плагина `build.gradle`:
    ```groovy
    graalvmNative {
        binaries {
            main {
                imageName = "application"
                mainClass = "ru.tinkoff.kora.example.Application"
                debug = true
                verbose = true
                buildArgs.add("--report-unsupported-elements-at-runtime")
                javaLauncher = javaToolchains.launcherFor {
                    languageVersion = JavaLanguageVersion.of(17)
                    vendor = JvmVendorSpec.matching("GraalVM Community")
                }
            }
        }
        metadataRepository {
            enabled = true
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Плагин `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.graalvm.buildtools.native") version("0.10.4")
    }
    ```

    Настройка плагина `build.gradle.kts`:
    ```groovy
    graalvmNative {
        binaries {
            named("main") {
                imageName.set("application")
                mainClass.set("ru.tinkoff.kora.example.Application")
                debug.set(true)
                verbose.set(true)
                buildArgs.add("--report-unsupported-elements-at-runtime")
                javaLauncher = javaToolchains.launcherFor {
                    languageVersion = JavaLanguageVersion.of(17)
                    vendor = JvmVendorSpec.matching("GraalVM Community")
                }
            }
        }
        metadataRepository {
            enabled.set(true)
        }
    }
    ```

Некоторые библиотеки требуют дополнительной конфигурации, часть конфигураций сделана в Kora.

Проверенные модули, которые должны работать без дополнительной конфигурации:

- [Конфигурация](config.md)
- [Json](json.md)
- [Logback](logging-slf4j.md)
- [Пробы](probes.md)
- [Метрики](metrics.md)
- [Трасcировка](tracing.md)
- [HTTP сервер](http-server.md)
- [HTTP клиент](http-client.md)
- [OpenAPI генерация](openapi-codegen.md)
- [OpenAPI отображение](openapi-management.md)
- [База данных JDBC (Postgres)](database-jdbc.md)
- [База данных R2DBC (Postgres)](database-r2dbc.md)
- [База данных Vertx (Postgres)](database-vertx.md)
- [База данных Cassandra](database-cassandra.md)
- [Kafka](kafka.md)
- [gRPC сервер](grpc-server.md)
- [gRPC клиент](grpc-client.md)
- [Отказоустойчивость](resilient.md)
- [Кеш](cache.md)
- [Валидация](validation.md)
- [Планировщик](scheduling.md)
- [Логирование](logging-aspect.md)

Посмотреть примеры рабочих нативных сервисов можно в [репозитории с примерами](https://github.com/kora-projects/kora-examples).
