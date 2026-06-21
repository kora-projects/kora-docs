---
description: "Explains Kora GraalVM Native Image notes and native build considerations for Kora applications. Use when working with GraalVM, native-image, reflection config, AOT, native build."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora GraalVM Native Image notes and native build considerations for Kora applications; key triggers include GraalVM, native-image, reflection config, AOT, native build."
---

GraalVM Native Image — это инструмент для `AOT-компиляции`, который собирает Java-приложение заранее в отдельный `нативный образ` для целевой платформы.
Такой образ запускается без обычного прогрева JVM, но требует, чтобы часть сведений о коде, ресурсах и отражении была известна уже во время сборки.

Kora создает вспомогательные классы во время компиляции,
не использует `Reflection API` во время выполнения,
не использует `динамические прокси`,
не использует генерацию байт-кода во время компиляции и во время выполнения.
Это упрощает сборку приложений Kora в `нативный образ`, который быстрее запускается и обычно потребляет меньше памяти, чем приложение на обычной JVM.
Основные ограничения при такой сборке чаще связаны не с Kora, а со сторонними библиотеками, которым могут понадобиться дополнительные настройки отражения, ресурсов или инициализации классов.

Поэтому со стороны самой Kora обычно не требуется дополнительная настройка для сборки `нативного образа`.

## Сборка { #build }

Пример сборки `нативного образа` с помощью [Gradle-плагина](https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html):

===! ":fontawesome-brands-java: `Java`"

    Плагин `build.gradle`:
    ```groovy
    plugins {
        id "org.graalvm.buildtools.native" version "0.11.5"
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
                    languageVersion = JavaLanguageVersion.of(21)
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
        id("org.graalvm.buildtools.native") version("0.11.5")
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
                    languageVersion = JavaLanguageVersion.of(21)
                    vendor = JvmVendorSpec.matching("GraalVM Community")
                }
            }
        }
        metadataRepository {
            enabled.set(true)
        }
    }
    ```

## Метаданные { #metadata }

Некоторые библиотеки требуют дополнительную конфигурацию для `нативного образа`: настройки отражения, ресурсов или инициализации классов.
Часть таких настроек уже добавлена в модули Kora через файлы `META-INF/native-image`.

Если приложение использует сторонние библиотеки, которым нужны дополнительные `метаданные достижимости`, можно включить их загрузку из репозитория метаданных:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    graalvmNative {
        metadataRepository {
            enabled = true
        }
    }

    processResources.dependsOn tasks.collectReachabilityMetadata
    sourceSets.main { resources.srcDirs += "$buildDir/native-reachability-metadata" }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    graalvmNative {
        metadataRepository {
            enabled.set(true)
        }
    }

    tasks.processResources {
        dependsOn(tasks.collectReachabilityMetadata)
    }
    kotlin.sourceSets.main {
        resources.srcDir(layout.buildDirectory.dir("native-reachability-metadata"))
    }
    ```

## Модули { #modules }

Модули, для которых в Kora уже предусмотрена необходимая часть настроек для `нативного образа`:

- [Конфигурация](config.md)
- [JSON](json.md)
- [Логирование Logback](logging-slf4j.md)
- [Пробы](probes.md)
- [Метрики](metrics.md)
- [Трассировка](tracing.md)
- [HTTP-сервер](http-server.md)
- [HTTP-клиент](http-client.md)
- [Генерация OpenAPI-кода](openapi-codegen.md)
- [Отображение OpenAPI](openapi-management.md)
- [База данных JDBC (Postgres)](database-jdbc.md)
- [База данных R2DBC (Postgres)](database-r2dbc.md)
- [База данных Vert.x (Postgres)](database-vertx.md)
- [База данных Cassandra](database-cassandra.md)
- [Kafka](kafka.md)
- [gRPC-сервер](grpc-server.md)
- [gRPC-клиент](grpc-client.md)
- [Отказоустойчивость](resilient.md)
- [Кэш](cache.md)
- [Валидация](validation.md)
- [Планировщик](scheduling.md)
- [Логирование](logging-aspect.md)

Готовые примеры сборки через Gradle и Docker можно посмотреть в [репозитории с примерами](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm).
