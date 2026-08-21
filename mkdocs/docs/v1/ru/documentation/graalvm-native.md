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

## Требования { #requirements }

Для нативной сборки требуется JDK [GraalVM](https://www.graalvm.org/): **GraalVM Community Edition** или **Oracle GraalVM** версии 21.
[Gradle-плагин](https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html) выбирает такой набор инструментов через блок `javaLauncher`, показанный в разделе [Сборка](#build) (`JvmVendorSpec.matching("GraalVM Community")`),
поэтому саму сборку может запускать обычный JDK, а `native-image` при этом выполняется на GraalVM.
При сборке вне плагина (например, командой `native-image` внутри сборочного образа [Docker](#docker)) инструмент `native-image` должен быть доступен в `PATH` — официальные контейнерные образы GraalVM уже содержат его.

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

Значения, добавленные в `buildArgs`, передаются напрямую в `native-image`. Наиболее распространённые из них:

- `--report-unsupported-elements-at-runtime` — откладывает ошибки о неподдерживаемых возможностях на время выполнения вместо того, чтобы прерывать сборку (используется в примере выше).
- `--no-fallback` — никогда не создавать `резервный` образ (в который незаметно встраивается JVM); вместо этого прервать сборку, если что-то не удаётся скомпилировать заранее. Этот флаг используется при прямом вызове `native-image` (см. [Docker](#docker)).
- `debug` / `verbose` — дополнительная диагностика сборки; для релизных сборок их можно убрать.

Флаги, необходимые самой Kora, добавляются её модулями автоматически, и их **не** нужно указывать вручную:

- `ru.tinkoff.kora:application-graph` поставляет `--install-exit-handlers` и `--initialize-at-build-time` для держателя исполнителя виртуальных потоков.
- `ru.tinkoff.kora:common` поставляет `--initialize-at-run-time` для `Context` и хука контекста Reactor.

Они берутся из ресурсов `META-INF/native-image` внутри JAR-файлов модулей и подмешиваются в сборку, как только зависимость оказывается в classpath (см. [Метаданные](#metadata)).

### Fat JAR { #build-jar }

`native-image` компилирует в бинарный файл единый classpath, поэтому приложение Kora обычно сначала собирают в один `fat JAR`.
Kora опирается на объединённые файлы `META-INF/services` (сгенерированные во время компиляции модули и расширения), поэтому JAR нужно собирать с объединением сервисных файлов — например, с помощью плагина [Shadow](https://gradleup.com/shadow/):

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    plugins {
        id "application"
        id "com.gradleup.shadow" version "9.4.1"
    }

    jar.enabled = false
    shadowJar {
        mergeServiceFiles()
        manifest {
            attributes "Main-Class": application.mainClass
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    plugins {
        id("application")
        id("com.gradleup.shadow") version("9.4.1")
    }

    tasks.jar {
        enabled = false
    }
    tasks.shadowJar {
        mergeServiceFiles()
        manifest {
            attributes["Main-Class"] = "ru.tinkoff.kora.example.Application"
        }
    }
    ```

Плагин Shadow создаёт `*-all.jar` в каталоге `build/libs`, который может использовать как Gradle-плагин, так и прямой вызов `native-image`.

## Docker { #docker }

В CI и на проде `нативный образ` обычно создают двухэтапной сборкой Docker: этап-сборщик (`builder`) на GraalVM компилирует [fat JAR](#build-jar) в бинарный файл, а компактный этап выполнения поставляет только этот бинарный файл.
Именно так собирают свои образы [примеры](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm), и это не зависит от того, написано приложение на Java или Kotlin:

```dockerfile
FROM ghcr.io/graalvm/native-image-community:21 AS builder

ARG TARGET_DIR=/opt/app
ARG SOURCE_DIR=build/libs
WORKDIR $TARGET_DIR

COPY $SOURCE_DIR/*-all.jar $TARGET_DIR/application.jar
RUN native-image --no-fallback -classpath $TARGET_DIR/application.jar

FROM ubuntu:noble AS runner

ARG TARGET_DIR=/opt/app
WORKDIR $TARGET_DIR

COPY --from=builder $TARGET_DIR/application $TARGET_DIR/application

ARG DOCKER_USER=app
RUN groupadd -r $DOCKER_USER && useradd -rg $DOCKER_USER $DOCKER_USER
RUN chmod +x application
USER $DOCKER_USER

EXPOSE 8080/tcp
EXPOSE 8085/tcp
CMD "/opt/app/application"
```

Этап-сборщик компилирует `application.jar` в нативный бинарный файл с именем `application`, а этап выполнения запускает его от имени пользователя без прав root.
Сначала соберите fat JAR (`./gradlew shadowJar`), затем выполните `docker build .`.

## Метаданные { #metadata }

Некоторым библиотекам требуется дополнительная конфигурация для `нативного образа`, и `native-image` видит только то, что объявлено как `метаданные достижимости`.
Kora поставляет метаданные для собственных модулей в виде ресурсов `META-INF/native-image/<group>/<artifact>/` внутри JAR-файла каждого модуля, поэтому они применяются автоматически, как только зависимость оказывается в classpath.

Распространённые случаи покрываются тремя видами файлов:

- **`native-image.properties`** — аргументы времени сборки, в первую очередь флаги инициализации классов `--initialize-at-build-time` и `--initialize-at-run-time`. Например, модуль `common` в Kora инициализирует `ru.tinkoff.kora.common.Context` *во время выполнения* (его состояние потока/контекста не должно запекаться в образ), а `application-graph` инициализирует держатель исполнителя виртуальных потоков *во время сборки*.
- **`reflect-config.json`** — классы, методы и поля, к которым обращаются через отражение. Например, Kora регистрирует `Thread.ofVirtual` / `Executors.newVirtualThreadPerTaskExecutor`, чтобы виртуальные потоки Loom работали в `нативном образе`.
- **`resource-config.json`** — ресурсы, которые нужно встроить в бинарный файл. Например, Kora включает `reference.conf` / `application.conf`, чтобы конфигурация HOCON была доступна для чтения во время выполнения.

### Репозиторий { #metadata-repository }

Если приложение использует сторонние библиотеки, которым нужны `метаданные достижимости`, не поставляемые ими самими, включите их загрузку из [репозитория метаданных достижимости GraalVM](https://github.com/oracle/graalvm-reachability-metadata):

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

### Пользовательские метаданные { #metadata-custom }

Когда класс не покрыт ни Kora, ни репозиторием, задайте метаданные вручную: положите `native-image.properties`, `reflect-config.json` и/или `resource-config.json` в каталог `src/main/resources/META-INF/native-image/<group>/<artifact>/` вашего собственного приложения — `native-image` объединяет все такие файлы, найденные в classpath.

Например, чтобы встроить конфигурацию Logback и файл конфигурации HOCON в бинарный файл, приложение может поставить `resource-config.json`:

```json title="src/main/resources/META-INF/native-image/ru.tinkoff.kora.examples/logback/resource-config.json"
{
  "resources": {
    "includes": [
      { "pattern": "\\Qlogback.xml\\E" },
      { "pattern": "\\Qapplication.conf\\E" }
    ]
  }
}
```

Сегменты пути `<group>/<artifact>` произвольны, но должны быть уникальными (обычно это group и модуль вашего приложения), чтобы файлы из разных зависимостей не конфликтовали.

### Агент { #metadata-agent }

Для сторонних библиотек, которые не покрыты репозиторием, стандартный способ обнаружить необходимые метаданные — `агент трассировки` GraalVM.
Запустите приложение на обычной JVM с подключённым агентом, пройдите по путям кода, которые используют отражение, ресурсы или прокси, и агент запишет соответствующие файлы конфигурации:

```bash
java -agentlib:native-image-agent=config-output-dir=src/main/resources/META-INF/native-image/<group>/<artifact> \
     -jar build/libs/application-all.jar
```

Зафиксируйте сгенерированные файлы как [пользовательские метаданные](#metadata-custom).
Это обычный резервный вариант, когда нативная сборка падает во время выполнения с ошибкой об отсутствующем отражении или отсутствующем ресурсе.

### Подсказки через аннотации { #metadata-hints }

Официальные примеры генерируют часть метаданных из аннотаций с помощью сторонней библиотеки [GraalVM Hint Processor](https://github.com/GoodforGod/graalvm-hint).
Это **не** API Kora — это внешнее, необязательное удобство, взаимозаменяемое с написанными вручную [пользовательскими метаданными](#metadata-custom) выше.

Добавьте процессор и аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        annotationProcessor "io.goodforgod:graalvm-hint-processor:1.2.0"
        compileOnly "io.goodforgod:graalvm-hint-annotations:1.2.0"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    plugins {
        kotlin("kapt")
    }

    dependencies {
        kapt("io.goodforgod:graalvm-hint-processor:1.2.0")
        compileOnly("io.goodforgod:graalvm-hint-annotations:1.2.0")
    }
    ```

Затем разметьте интерфейс `@KoraApp`, чтобы объявить точку входа и ресурсы для встраивания — процессор сгенерирует соответствующую конфигурацию `native-image` во время компиляции:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.goodforgod.graalvm.hint.annotation.NativeImageHint;
    import io.goodforgod.graalvm.hint.annotation.ResourceHint;

    @ResourceHint(include = {"openapi/http-server.yaml"})
    @NativeImageHint(name = "application", entrypoint = Application.class)
    @KoraApp
    public interface Application {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.goodforgod.graalvm.hint.annotation.NativeImageHint
    import io.goodforgod.graalvm.hint.annotation.ResourceHint

    @ResourceHint(include = ["openapi/http-server.yaml"])
    @NativeImageHint(name = "application", entrypoint = Application::class)
    @KoraApp
    interface Application {

        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                KoraApplication.run(ApplicationGraph::graph)
            }
        }
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

Каждый из этих модулей поставляет свою конфигурацию `META-INF/native-image` внутри собственного JAR, поэтому настройки применяются автоматически, как только зависимость оказывается в classpath; основные флаги инициализации классов и виртуальных потоков берутся из `ru.tinkoff.kora:application-graph` и `ru.tinkoff.kora:common`.

Готовые примеры сборки через Gradle и Docker можно посмотреть в [репозитории с примерами](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm).
