---
description: "Explains how to build a Kora application into a GraalVM Native Image: the Gradle plugin and JDK 25 toolchain, the fat JAR and the two-stage Docker build, reachability metadata, and how to verify the resulting binary. Use when working with GraalVM, native-image, nativeCompile, reachability metadata, reflect-config.json, AOT, native build."
agent:
  use_when: "Use this file for Kora docs or implementation questions about building a Kora application into a GraalVM Native Image; key triggers include GraalVM, native-image, org.graalvm.buildtools.native, nativeCompile, reachability metadata, reflect-config.json, native-image.properties, tracing agent, AOT, native build, native Docker image."
---

GraalVM Native Image — это инструмент для `AOT-компиляции`, который собирает Java-приложение заранее в отдельный `нативный образ` для целевой платформы.
Такой образ запускается без обычного прогрева JVM, но требует, чтобы часть сведений о коде, ресурсах и отражении была известна уже во время сборки.

Kora создает вспомогательные классы во время компиляции,
не использует `Reflection API` во время выполнения,
не использует `динамические прокси`,
не использует генерацию байт-кода во время компиляции и во время выполнения.
Это упрощает сборку приложений Kora в `нативный образ`, который быстрее запускается и обычно потребляет меньше памяти, чем приложение на обычной JVM.
Основные ограничения при такой сборке чаще связаны не с Kora, а со сторонними библиотеками, которым могут понадобиться дополнительные настройки отражения, ресурсов или инициализации классов.

Поэтому со стороны самой Kora обычно не требуется дополнительная настройка для сборки `нативного образа`:
модули, которые зависят от таких библиотек, поставляют нужные [метаданные достижимости](#metadata) прямо внутри своих артефактов.

## Требования { #requirements }

Для нативной сборки требуется JDK [GraalVM](https://www.graalvm.org/) — **GraalVM Community Edition** или **Oracle GraalVM** — **той же мажорной версии, под которую скомпилировано приложение**.
Артефакты Kora 2.0 собраны под **Java 25**, а `native-image` отказывается читать классы более нового class-file формата, чем его собственный JDK,
поэтому для нативной сборки нужен launcher **GraalVM 25**. Официальные примеры проверены на GraalVM CE 25 (`native-image 25.x`), установка — например, `sdk install java 25.2.4-graalce`.

Мажорная версия должна совпадать сразу в **трёх** местах, и забытое место — самая частая причина сломанной нативной сборки:

1. toolchain модуля (`java { toolchain { … } }` или `kotlin { jvmToolchain { … } }`);
2. `javaLauncher` бинарного файла в блоке `graalvmNative` — см. [Сборка](#build);
3. базовый образ этапа-сборщика в [Dockerfile](#docker).

Само приложение компилировать через GraalVM не обязательно: toolchain модуля может быть обычным JDK,
а [Gradle-плагин](https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html) выбирает launcher GraalVM через `JvmVendorSpec.matching("GraalVM Community")` только для `native-image`.
Если подходящей установки GraalVM в системе нет, `nativeCompile` падает на поиске toolchain — это проблема окружения, а не приложения.

При сборке вне плагина (например, командой `native-image` внутри сборочного образа [Docker](#docker)) инструмент `native-image` должен быть доступен в `PATH` — официальные контейнерные образы GraalVM уже содержат его.

## Сборка { #build }

Пример сборки `нативного образа` с помощью [Gradle-плагина](https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html):

===! ":fontawesome-brands-java: `Java`"

    `build.gradle`:
    ```groovy
    plugins {
        id "application"
        id "com.gradleup.shadow" version "9.4.1"
        id "org.graalvm.buildtools.native" version "1.1.7" //(1)!
    }

    java {
        toolchain {
            languageVersion = JavaLanguageVersion.of(25) //(2)!
            vendor = JvmVendorSpec.ADOPTIUM
        }
    }

    application {
        mainClass = "io.koraframework.example.Application"
    }

    graalvmNative {
        binaries {
            main {
                imageName = project.name //(3)!
                mainClass = application.mainClass //(4)!
                javaLauncher = javaToolchains.launcherFor {
                    languageVersion = JavaLanguageVersion.of(25) //(5)!
                    vendor = JvmVendorSpec.matching("GraalVM Community")
                }
            }
        }
        metadataRepository {
            enabled = true //(6)!
        }
    }
    ```

    1.  Версия плагина, который собирает `нативный образ`. Для многомодульного проекта **требуется 1.1.7 или новее**: более ранние версии регистрировали один общий build service на весь build, и на Gradle 9 задача `collectReachabilityMetadata` второго и каждого следующего нативного модуля падает при резолве конфигурации чужого проекта.
    2.  JDK, под который компилируются классы приложения, — здесь достаточно обычного JDK.
    3.  Имя итогового бинарного файла в `build/native/nativeCompile` (по умолчанию: имя проекта).
    4.  Полное имя класса с методом `main` (обязательно). **Присваивайте сам провайдер, а не строковую интерполяцию от него**: `application.mainClass` — это `Property<String>`, и `"$application.mainClass"` отправит в командную строку `native-image` отладочное представление (`property(java.lang.String, fixed(...))`) вместо имени класса. Проявляется это как *main class not found* при сборке образа, а не как ошибка конфигурации Gradle.
    5.  JDK, на котором работает сам `native-image`, — вот он обязан быть GraalVM, см. [Требования](#requirements).
    6.  Включает [репозиторий метаданных достижимости](#metadata-repository) (по умолчанию: `false`).

    Собрать бинарный файл:
    ```shell
    ./gradlew nativeCompile
    ```

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:
    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version "2.4.10"
        id("com.google.devtools.ksp") version "2.3.11"
        id("com.gradleup.shadow") version "9.4.1"
        id("org.graalvm.buildtools.native") version "1.1.7" //(1)!
    }

    kotlin {
        jvmToolchain {
            languageVersion.set(JavaLanguageVersion.of(25)) //(2)!
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
    }

    application {
        mainClass.set("io.koraframework.example.ApplicationKt")
    }

    graalvmNative {
        binaries {
            named("main") {
                imageName.set(project.name) //(3)!
                mainClass.set(application.mainClass) //(4)!
                javaLauncher.set(javaToolchains.launcherFor {
                    languageVersion.set(JavaLanguageVersion.of(25)) //(5)!
                    vendor.set(JvmVendorSpec.matching("GraalVM Community"))
                })
            }
        }
        metadataRepository {
            enabled.set(true) //(6)!
        }
    }
    ```

    1.  Версия плагина, который собирает `нативный образ`. Для многомодульного проекта **требуется 1.1.7 или новее**: более ранние версии регистрировали один общий build service на весь build, и на Gradle 9 задача `collectReachabilityMetadata` второго и каждого следующего нативного модуля падает при резолве конфигурации чужого проекта.
    2.  JDK, под который компилируются классы приложения, — здесь достаточно обычного JDK.
    3.  Имя итогового бинарного файла в `build/native/nativeCompile` (по умолчанию: имя проекта).
    4.  Полное имя класса с методом `main` (обязательно); для Kotlin это класс с суффиксом `Kt`. **Передавайте сам провайдер, а не собранную из него строку** — `application.mainClass` это `Property<String>`, и его `toString()` возвращает отладочное представление (`property(java.lang.String, fixed(...))`), которое и уезжает в командную строку `native-image` вместо имени класса. Проявляется это как *main class not found* при сборке образа, а не как ошибка конфигурации Gradle.
    5.  JDK, на котором работает сам `native-image`, — вот он обязан быть GraalVM, см. [Требования](#requirements).
    6.  Включает [репозиторий метаданных достижимости](#metadata-repository) (по умолчанию: `false`).

    Собрать бинарный файл:
    ```shell
    ./gradlew nativeCompile
    ```

Дополнительные флаги для `native-image` передаются через список `buildArgs` того же блока, например `buildArgs.add("--no-fallback")` — он запрещает создавать `резервный` образ (в который незаметно встраивается JVM) и вместо этого прерывает сборку, если что-то не удаётся скомпилировать заранее.
Свойства `debug` и `verbose` того же блока включают дополнительную диагностику сборки.

!!! warning "Не выключайте задачу `jar`"

    `nativeCompile` строит classpath из артефактов самого проекта, поэтому обычная задача `jar` должна оставаться включённой.
    С `jar.enabled = false` в classpath попадают только зависимости, но не классы приложения,
    и сборка падает на ненайденном классе `Application`, хотя `compileJava` прошёл успешно.
    [Fat JAR](#build-jar) здесь не спасает — он собирается для пути через [Docker](#docker) и в classpath `nativeCompile` не участвует.

### Fat JAR { #build-jar }

`native-image` компилирует в бинарный файл единый classpath, поэтому для пути через [Docker](#docker) приложение Kora сначала собирают в один `fat JAR`.

Собирать `fat JAR` нужно с объединением файлов `META-INF/services`: наивный архив перезаписывает одноимённые сервисные файлы вместо их склейки,
а на них опираются и сама Kora (`io.koraframework:common` поставляет сервисный файл `io.opentelemetry.context.ContextStorageProvider`), и её зависимости (провайдер XNIO у HTTP-сервера, драйверы JDBC, SLF4J).
В `нативном образе` потерянный сервисный файл фатален, потому что соответствующий провайдер просто никогда не находится.
Объединение делает плагин [Shadow](https://gradleup.com/shadow/):

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    shadowJar {
        mergeServiceFiles() //(1)!
        manifest {
            attributes "Main-Class": application.mainClass //(2)!
        }
    }

    assemble.dependsOn shadowJar
    ```

    1.  Склеивает файлы `META-INF/services` всех зависимостей вместо их перезаписи (**обязательно**).
    2.  Точка входа архива — тот же провайдер, который передаётся в [`mainClass`](#build).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    tasks.shadowJar {
        mergeServiceFiles() //(1)!
        manifest {
            attributes["Main-Class"] = application.mainClass //(2)!
        }
    }

    tasks.assemble {
        dependsOn(tasks.shadowJar)
    }
    ```

    1.  Склеивает файлы `META-INF/services` всех зависимостей вместо их перезаписи (**обязательно**).
    2.  Точка входа архива — тот же провайдер, который передаётся в [`mainClass`](#build).

Плагин Shadow создаёт `*-all.jar` в каталоге `build/libs`:

```shell
./gradlew shadowJar
```

## Docker { #docker }

В CI и на проде `нативный образ` обычно создают двухэтапной сборкой Docker: этап-сборщик (`builder`) на GraalVM компилирует [fat JAR](#build-jar) в бинарный файл, а компактный этап выполнения поставляет только этот бинарный файл.
Именно так собирают свои образы официальные [примеры](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm), и это не зависит от того, написано приложение на Java или Kotlin:

```dockerfile
FROM ghcr.io/graalvm/native-image-community:25 as builder

ARG TARGET_DIR=/opt/app
ARG SOURCE_DIR=build/libs
WORKDIR $TARGET_DIR

COPY $SOURCE_DIR/*-all.jar $TARGET_DIR/application.jar

RUN native-image --no-fallback -classpath $TARGET_DIR/application.jar

FROM ubuntu:noble-20240212 as runner

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

Сначала соберите fat JAR, затем образ:

```shell
./gradlew shadowJar
docker build .
```

Два проброшенных порта — это два HTTP-сервера Kora: `httpServer.port` (по умолчанию: `8080`) для API приложения и `httpServer.system.port` (по умолчанию: `8085`) для [системного сервера](http-server.md#system-server), который отдаёт [пробы](probes.md) и метрики.

Этап-сборщик называет бинарный файл `application`, хотя `-H:Name` в командной строке не передаётся: имя и точка входа берутся из файла `native-image.properties` внутри JAR, сгенерированного по [подсказкам через аннотации](#metadata-hints), которые используют примеры.
Без такого файла компилируемый класс нужно указывать явно, например `native-image --no-fallback -classpath application.jar io.koraframework.example.Application`.

!!! warning "Два пути сборки читают метаданные по-разному"

    `nativeCompile` сам подкладывает в сборку [репозиторий метаданных](#metadata-repository), а `native-image -classpath application.jar` внутри Docker ничего не знает про Gradle и читает только то, что физически лежит в JAR.
    Если образ из Gradle работает, а из Docker — нет, первый подозреваемый именно обвязка из раздела [Репозиторий](#metadata-repository), а не код приложения.

## Проверка { #verification }

Успешная **сборка** `нативного образа` не является доказательством того, что образ работает.
Нехватка метаданных достижимости сборку не ломает: `native-image` завершается успешно, регистрации просто никогда не применяются, и отказ проявляется только во время выполнения.
Успешными должны оказаться три разные вещи, и проверять каждую нужно отдельно:

1. **сборка под JVM** — `./gradlew build` проходит и приложение работает на обычном JDK;
2. **сборка нативного образа** — `./gradlew nativeCompile` (или `docker build`) создаёт бинарный файл;
3. **работа бинарного файла** — скомпилированное приложение действительно стартует и обслуживает запросы.

Минимальный набор проверок для третьего пункта:

- бинарный файл стартует и не падает через секунду;
- `GET /system/readiness` на [системном сервере](http-server.md#system-server) отвечает `200` — значит, граф зависимостей инициализировался целиком;
- `GET /metrics` отдаёт метрики, а не заглушку и не `500`;
- сценарий модуля отрабатывает против реальной зависимости (базы данных, брокера), а не на моках;
- в стартовом логе нет стектрейсов — в `нативном образе` они часто единственный признак отвалившейся подсистемы.

Самый дешёвый способ закрепить это в CI — черноящичный тест, который собирает образ по `Dockerfile` и запускает его через [Testcontainers](https://java.testcontainers.org/); именно так протестированы все три нативных примера:

```java
waitingFor(Wait.forHttp("/system/readiness")
        .forPort(8085)
        .forStatusCode(200)
        .withStartupTimeout(Duration.ofSeconds(60)));
```

!!! tip "Ждите пробу, а не строку в логе"

    Готовность контейнера стройте на HTTP-пробе, а не на поиске стартового сообщения: формулировки стартовых логов Kora не являются контрактом и могут меняться между версиями, тогда как ответ `200` на `GET /system/readiness` — стабильный признак поднятого графа.

## Метаданные { #metadata }

Некоторым библиотекам требуется дополнительная конфигурация для `нативного образа`, и `native-image` видит только то, что объявлено как `метаданные достижимости`.
Kora поставляет метаданные для собственных модулей в виде ресурсов `META-INF/native-image/<group>/<artifact>/` внутри артефакта каждого модуля, поэтому они применяются автоматически, как только зависимость оказывается в classpath — см. [Модули](#modules).

`native-image` читает в таком каталоге только файлы с каноническими именами:

- **`native-image.properties`** — аргументы времени сборки, в первую очередь флаги инициализации классов `--initialize-at-build-time` и `--initialize-at-run-time`. Например, `io.koraframework:logging-common` инициализирует `io.koraframework.logging.common.MDC` *во время сборки*, а `io.koraframework:netty-common` инициализирует весь пакет `io.netty` *во время выполнения*.
- **`reflect-config.json`** — классы, методы и поля, к которым обращаются через отражение. Например, `io.koraframework:database-jdbc` регистрирует конструктор HikariCP `MicrometerMetricsTrackerFactory(MeterRegistry)`, который пул ищет рефлексивно при включённых метриках.
- **`resource-config.json`** — ресурсы, которые нужно встроить в бинарный файл. Например, `io.koraframework:config-hocon` включает `reference.conf` / `application.conf`, а `io.koraframework:config-yaml` — `application.yaml` / `reference.yaml`, чтобы конфигурация была доступна для чтения во время выполнения.
- **`proxy-config.json`**, **`serialization-config.json`**, **`jni-config.json`**, **`reachability-metadata.json`** — остальные виды: для динамических прокси, сериализации, JNI и объединённого современного формата.

!!! warning "Файл с любым другим именем игнорируется молча"

    Классическая ошибка — назвать файл **`reflection-config.json`** вместо **`reflect-config.json`**.
    Такого имени `native-image` не знает вовсе: ошибки нет, предупреждения нет, сборка проходит успешно, а регистрации просто никогда не применяются — и приложение падает во время выполнения в месте, никак не связанном с этим файлом.
    Проверка проекта — одна команда, и каждое попадание это мёртвый файл:

    ```shell
    find . -name "reflection-config.json"
    ```

### Репозиторий { #metadata-repository }

Если приложение использует сторонние библиотеки, которым нужны `метаданные достижимости`, не поставляемые ими самими, включите их загрузку из [репозитория метаданных достижимости GraalVM](https://github.com/oracle/graalvm-reachability-metadata).

Включённого `metadataRepository` достаточно для `nativeCompile`, но не для пути через [Docker](#docker): голый `native-image -classpath application.jar` читает только то, что лежит в JAR.
Чтобы оба пути видели одни и те же метаданные, соберите их в ресурсы до упаковки:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    graalvmNative {
        metadataRepository {
            enabled = true //(1)!
        }
    }

    processResources.dependsOn tasks.collectReachabilityMetadata //(2)!
    sourceSets.main { resources.srcDirs += "$buildDir/native-reachability-metadata" } //(3)!
    ```

    1.  Включает загрузку метаданных из репозитория (по умолчанию: `false`).
    2.  Заставляет обработку ресурсов дождаться загрузки метаданных.
    3.  Добавляет загруженные метаданные в ресурсы, чтобы они попали внутрь [fat JAR](#build-jar).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    graalvmNative {
        metadataRepository {
            enabled.set(true) //(1)!
        }
    }

    tasks.processResources {
        dependsOn(tasks.collectReachabilityMetadata) //(2)!
    }
    sourceSets.main {
        resources.srcDir(layout.buildDirectory.dir("native-reachability-metadata")) //(3)!
    }
    ```

    1.  Включает загрузку метаданных из репозитория (по умолчанию: `false`).
    2.  Заставляет обработку ресурсов дождаться загрузки метаданных.
    3.  Добавляет загруженные метаданные в ресурсы, чтобы они попали внутрь [fat JAR](#build-jar).

### Пользовательские метаданные { #metadata-custom }

Когда класс не покрыт ни Kora, ни репозиторием, задайте метаданные вручную: положите `native-image.properties`, `reflect-config.json` и/или `resource-config.json` в каталог `src/main/resources/META-INF/native-image/<group>/<artifact>/` вашего собственного приложения — `native-image` объединяет все такие файлы, найденные в classpath.

Например, чтобы встроить конфигурацию Logback и файл конфигурации HOCON в бинарный файл, приложение поставляет `resource-config.json`:

```json title="src/main/resources/META-INF/native-image/io.koraframework.examples/logback/resource-config.json"
{
  "resources": {
    "includes": [
      { "pattern": "\\Qlogback.xml\\E" },
      { "pattern": "\\Qapplication.conf\\E" }
    ]
  }
}
```

и `reflect-config.json` для аппендера и энкодера, которые Logback создаёт по имени из этого XML:

```json title="src/main/resources/META-INF/native-image/io.koraframework.examples/logback/reflect-config.json"
[
  {
    "name": "io.koraframework.logging.logback.ConsoleTextRecordEncoder",
    "allDeclaredConstructors": true,
    "allPublicMethods": true
  },
  {
    "name": "io.koraframework.logging.logback.KoraAsyncAppender",
    "allDeclaredConstructors": true,
    "allPublicMethods": true
  },
  {
    "name": "ch.qos.logback.core.status.NopStatusListener",
    "allDeclaredConstructors": true
  }
]
```

Сегменты пути `<group>/<artifact>` на чтение файлов не влияют — это пространство имён, и оно должно быть уникальным (обычно это group и модуль вашего приложения), чтобы файлы из разных зависимостей не конфликтовали внутри одного JAR.

!!! warning "Работающее на JVM приложение ничего не доказывает про метаданные"

    JVM не читает `META-INF/native-image` вообще, поэтому нельзя счесть метаданные ненужными на том основании, что без них всё работает под обычным JDK.
    Обратная ошибка так же частая: при смене группы приложения каталог `META-INF/native-image/<group>/` переименовывается вручную, а имена классов **внутри** файлов трогать нельзя — там перечислены классы сторонних библиотек, которые не переименовывались.

### Агент { #metadata-agent }

Для сторонних библиотек, которые не покрыты репозиторием, стандартный способ обнаружить необходимые метаданные — `агент трассировки` GraalVM.
Запустите на обычной JVM с подключённым агентом тот же [fat JAR](#build-jar), который идёт в образ, пройдите по путям кода, которые используют отражение, ресурсы или прокси, и остановите приложение штатно (`SIGTERM`) — иначе конфигурация не запишется:

```shell
java -agentlib:native-image-agent=config-output-dir=/tmp/native-image-config \
     -jar build/libs/application-all.jar
```

Агент видит только те ветки, которые были выполнены, — это ограничение подхода, а не дефект.
Его вывод — гипотеза, а не готовый патч: там будут сотни записей про сторонние библиотеки, место которым внутри самих этих библиотек.
Сравните вывод с тем, что приложение уже поставляет, и перенесите только те записи, которые относятся к приложению:

```shell
diff -r /tmp/native-image-config src/main/resources/META-INF/native-image/<group>/<artifact>
```

Зафиксируйте отобранные записи как [пользовательские метаданные](#metadata-custom).

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

    ```kotlin
    plugins {
        kotlin("kapt")
    }

    dependencies {
        kapt("io.goodforgod:graalvm-hint-processor:1.2.0")
        compileOnly("io.goodforgod:graalvm-hint-annotations:1.2.0")
    }
    ```

    Процессор работает через `kapt`, поэтому в Kotlin-приложении его придётся запускать рядом с `KSP`-процессором Kora.
    Если это нежелательно, напишите те же файлы вручную как [пользовательские метаданные](#metadata-custom) — результат будет идентичным.

Затем разметьте интерфейс `@KoraApp`, чтобы объявить точку входа и ресурсы для встраивания — процессор сгенерирует соответствующую конфигурацию `native-image` во время компиляции:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.goodforgod.graalvm.hint.annotation.NativeImageHint;
    import io.goodforgod.graalvm.hint.annotation.ReflectionHint;
    import io.goodforgod.graalvm.hint.annotation.ResourceHint;
    import io.netty.channel.socket.nio.NioDatagramChannel;

    @ResourceHint(include = {"openapi/http-server.yaml"}) //(1)!
    @ReflectionHint(types = NioDatagramChannel.class) //(2)!
    @NativeImageHint(name = "application", entrypoint = Application.class) //(3)!
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

    1.  Ресурсы, встраиваемые в бинарный файл, — генерирует `resource-config.json`.
    2.  Классы, регистрируемые для отражения, — генерирует `reflect-config.json`.
    3.  Имя итогового бинарного файла и класс, метод `main` которого является точкой входа, — генерирует `native-image.properties`, благодаря которому сборка через [Docker](#docker) может вызывать `native-image`, передав только classpath.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.goodforgod.graalvm.hint.annotation.NativeImageHint
    import io.goodforgod.graalvm.hint.annotation.ReflectionHint
    import io.goodforgod.graalvm.hint.annotation.ResourceHint
    import io.netty.channel.socket.nio.NioDatagramChannel

    @ResourceHint(include = ["openapi/http-server.yaml"]) //(1)!
    @ReflectionHint(types = [NioDatagramChannel::class]) //(2)!
    @NativeImageHint(name = "application", entrypoint = Application::class) //(3)!
    @KoraApp
    interface Application : HoconConfigModule, LogbackModule, UndertowPublicHttpServerModule {

        companion object {

            @JvmStatic
            fun main(args: Array<String>) {
                KoraApplication.run { ApplicationGraph.graph() }
            }
        }
    }
    ```

    1.  Ресурсы, встраиваемые в бинарный файл, — генерирует `resource-config.json`.
    2.  Классы, регистрируемые для отражения, — генерирует `reflect-config.json`.
    3.  Имя итогового бинарного файла и класс, метод `main` которого является точкой входа, — генерирует `native-image.properties`, благодаря которому сборка через [Docker](#docker) может вызывать `native-image`, передав только classpath. Точкой входа должен быть класс со статическим `main`, поэтому метод `main` здесь живёт в companion-объекте с `@JvmStatic`, а `mainClass` в build-файле указывает на `io.koraframework.example.Application`, а не на `…ApplicationKt`.

## Диагностика { #troubleshooting }

Нативный образ, который успешно собрался, но неправильно работает, — это нормальный режим отказа, и текст исключения при этом часто вводит в заблуждение:
библиотеки ловят `Throwable` при поиске провайдеров и репортят вторичную ошибку.
Канонический пример — `java.lang.IllegalArgumentException: No XNIO provider found` при старте HTTP-сервера: он означал не отсутствие провайдера, а невозможность создать его логгер — `jboss-logging` грузит реализацию `<интерфейс>_$logger` рефлексивно.

Три шага, каждый из которых даёт факт, а не гипотезу:

1. **Запустите [агент](#metadata-agent) трассировки** и посмотрите, что реально грузится рефлексивно. Берите тот же fat JAR, что идёт в образ, запускайте на JDK GraalVM и прогоняйте сценарий целиком.
2. **Изолируйте проблему минимальным нативным пробником.** Отдельный `main`, который дёргает только подозреваемую библиотеку без Kora, собранный тем же `native-image`. Если пробник падает, причина в библиотеке или в метаданных модуля, и искать её в коде приложения бессмысленно.
3. **Проверьте, что метаданные вообще читаются.** Этот шаг пропускают чаще всего, а он единственный отличает *запись неполная* от *файл не читается*: добавьте регистрацию с наблюдаемым эффектом, пересоберите образ и посмотрите, изменилось ли поведение; если нет — положите ту же запись в файл с [каноническим именем](#metadata) и повторите.

Частые симптомы и куда смотреть:

- *main class not found* при сборке образа — в `mainClass` присвоена строковая интерполяция вместо провайдера, см. [Сборка](#build).
- класс `Application` не найден, хотя `compileJava` прошёл, — выключена задача `jar`, см. [Сборка](#build).
- `nativeCompile` падает на выборе toolchain — Gradle не видит GraalVM нужной мажорной версии, см. [Требования](#requirements).
- образ из Gradle работает, а из Docker — нет, — метаданных нет внутри JAR, см. [Репозиторий](#metadata-repository).
- приложение стартует, но логи пусты или идут мимо конфигурации, — потеряны метаданные Logback, см. [Пользовательские метаданные](#metadata-custom).

## Модули { #modules }

Модули Kora, которые поставляют собственную конфигурацию `нативного образа` внутри своих артефактов:

- [Конфигурация](config.md) — `config-common`, `config-hocon`, `config-yaml`
- [Логирование Logback](logging-slf4j.md) — `logging-logback`
- [Логирование](logging-aspect.md) — `logging-common`
- [HTTP-сервер](http-server.md) — `http-server-undertow`
- [Netty](netty.md) — `netty-common`
- [Метрики](metrics.md) — `micrometer-module`
- [Трассировка](tracing.md) — `opentelemetry-tracing`
- [База данных JDBC](database-jdbc.md) — `database-jdbc`
- [База данных Cassandra](database-cassandra.md) — `database-cassandra`
- [Кэш](cache.md) — `cache-caffeine`
- [Kafka](kafka.md) — `kafka`
- [gRPC-сервер](grpc-server.md) — `grpc-server`
- [Отображение OpenAPI](openapi-management.md) — `openapi-management`

Настройки применяются автоматически, как только зависимость оказывается в classpath, и от приложения никаких действий не требуется.
Модули Kora, которых нет в этом списке, не поставляют конфигурацию `нативного образа`, потому что она им не нужна: их код генерируется во время компиляции и достижим статически.

Готовые примеры сборки через Gradle и Docker вместе с черноящичными тестами, которые запускают полученный бинарный файл, можно посмотреть в репозитории с примерами:

- [`kora-java-graalvm-crud-jdbc`](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm/kora-java-graalvm-crud-jdbc) — нативный CRUD HTTP-сервис на JDBC с кэшем Caffeine
- [`kora-java-graalvm-crud-cassandra`](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm/kora-java-graalvm-crud-cassandra) — нативный CRUD HTTP-сервис на Cassandra с кэшем Redis
- [`kora-java-graalvm-kafka`](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm/kora-java-graalvm-kafka) — нативный сервис с консьюмером и продюсером Kafka
