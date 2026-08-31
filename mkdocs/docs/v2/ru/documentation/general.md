---
description: "Explains Kora framework fundamentals, annotation processors, KSP, JDK and Kotlin compatibility, Gradle build setup, dependencies, application entry point, and terminology. Use when working with @KoraApp, KoraApplication, annotation processors, KSP, Gradle, the io.koraframework:kora-bom BOM, application plugin."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora framework fundamentals, annotation processors, KSP, JDK and Kotlin compatibility, Gradle, the io.koraframework:kora-bom BOM, module dependencies, the @KoraApp entry point and the application plugin."
---

Kora - облачно ориентированный серверный фреймворк, написанный на `Java`, для приложений на `Java` и `Kotlin`.
Эта страница описывает базовые принципы Kora, требования к окружению, подключение обработчиков аннотаций, минимальную настройку `Gradle`, управление зависимостями и запуск приложения.

Kora предоставляет набор модулей для быстрого создания серверных приложений: `HTTP`-сервер и `HTTP`-клиент, потребители `Kafka`, репозитории для работы с базами данных, `S3`-клиент, `gRPC`-сервер и `gRPC`-клиент, интеграции с `Camunda`, телеметрию модулей, отказоустойчивость и другие возможности.
Основные характеристики фреймворка описаны [на главной странице](../index.md).

Kora предоставляет инструменты, которые обычно нужны современной серверной разработке:

- внедрение зависимостей через аннотации;
- инверсию управления без отдельного контейнера во время выполнения;
- аспектно-ориентированное программирование через аннотации;
- достаточно высокоуровневые простые абстракции и инструменты разработки;
- большой набор заранее настроенных интеграций;
- телеметрию, трассировку, метрики по стандарту `OpenTelemetry` и логирование модулей;
- быстрое тестирование с помощью [JUnit5](junit5.md);
- рабочие [примеры и руководства](../guides/home.md).

Для высокопроизводительного, эффективного и предсказуемого кода Kora следует нескольким принципам:

- не использует `Reflection` во время работы приложения;
- не использует `динамический прокси` во время работы приложения;
- не генерирует байт-код во время компиляции или работы приложения;
- создает исходный код на этапе компиляции через обработчики аннотаций;
- оставляет тонкие абстракции над интеграциями;
- предоставляет бесплатные аспекты: без дополнительной стоимости во время работы приложения;
- использует только наиболее эффективные реализации для интеграций;
- поощряет и использует наиболее эффективные принципы разработки и естественные конструкции языка.

Kora исполняет код приложения синхронно на [виртуальных потоках](https://openjdk.org/jeps/444).
Контроллеры, `HTTP`-клиенты, репозитории и запланированные задачи объявляются обычными блокирующими сигнатурами, а диспетчеризацией на виртуальные потоки занимается сам фреймворк: например, `HTTP`-запрос обрабатывается на виртуальном потоке, привязанном к его соединению.
Реактивных и `suspend`-контрактов в модулях Kora нет - обработчики отклоняют `suspend`-методы контроллеров, клиентов, репозиториев и планировщика ошибкой компиляции.
Если в рамках одной операции нужно выполнить несколько действий параллельно, используйте `StructuredTaskScope` из `Java` structured concurrency; это preview-API, поэтому и компиляция, и каждый запуск `JVM` требуют `--enable-preview`.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Создание первого приложения на Kora](../guides/getting-started.md) и [Введение во внедрение зависимостей](../guides/dependency-injection-introduction.md).

## Обработчики аннотаций { #annotation-processor }

Kora строит приложение на этапе компиляции: обработчики читают аннотации, проверяют код и генерируют исходные файлы, которые затем компилируются вместе с кодом приложения.
За счет этого граф зависимостей, аспекты, `HTTP`-обработчики, репозитории и другие компоненты становятся обычным скомпилированным кодом без `Reflection` во время работы.

===! ":fontawesome-brands-java: `Java`"

    Аннотация - это конструкция, связанная с элементами исходного кода `Java`: классами, методами, параметрами и полями.
    [Обработчик аннотаций](https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/annotation/processing/Processor.html) запускается компилятором, читает эти аннотации и может сгенерировать дополнительный исходный код или остановить компиляцию с понятной ошибкой.

    Kora предоставляет все обработчики аннотаций в одной зависимости:

    ```groovy
    annotationProcessor "io.koraframework:annotation-processors"
    ```

    Эта зависимость нужна только на этапе компиляции и не добавляет лишние библиотеки в путь классов времени выполнения приложения.

=== ":simple-kotlin: `Kotlin`"

    Для `Kotlin` используется [`KSP`](https://kotlinlang.org/docs/ksp-overview.html) (`Kotlin Symbol Processing`).
    `KSP` читает символы исходного кода `Kotlin`, передает их процессорам Kora и позволяет генерировать код до основной компиляции.

    Kora предоставляет `KSP`-обработчики в одной зависимости:

    ```kotlin
    ksp("io.koraframework:symbol-processors")
    ```

    При этом обработка `Kotlin` обычно медленнее обработки аннотаций в `Java`.

### `KSP` { #ksp }

`KSP` нужен только для `Kotlin`-проектов.
Если приложение написано на `Java`, используйте обычный `annotationProcessor`; если приложение написано на `Kotlin`, подключайте `com.google.devtools.ksp` и зависимость `io.koraframework:symbol-processors`.

`KSP` складывает сгенерированные исходники в `build/generated/ksp/main/kotlin` и `build/generated/ksp/test/kotlin`.
Плагин `KSP` для `Gradle` сам добавляет эти каталоги в компиляцию; в файлах сборки на этой странице они дополнительно объявлены в исходных наборах явно:

```kotlin
kotlin {
    sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
    sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
}
```

Если перед генерацией кода должна отработать другая задача (например, генерация `OpenAPI` или `protobuf`), привязывайте ее к задачам `KSP` по имени.
В `KSP` `2` тип `KspTask` больше не доступен, поэтому конструкция `tasks.withType<KspTask>()` не работает:

```kotlin
tasks.matching { it.name.startsWith("ksp") }.configureEach {
    dependsOn(openApiGenerateHttpServer)
}
```

## Совместимость { #compatibility }

Артефакты Kora компилируются и публикуются под `Java` `25`: и `Java`-, и `Kotlin`-часть фреймворка собираются с `sourceCompatibility`/`targetCompatibility` `25` и `jvmTarget` `25`, а публикуемый `BOM` объявляет `java.version` `25`.
Поэтому `JDK` `25` - минимальная версия для компиляции и запуска приложения на Kora независимо от языка.

===! ":fontawesome-brands-java: `Java`"

    Требуется версия не ниже [`JDK` `25`](https://openjdk.org/projects/jdk/25/), рекомендуется использовать последний доступный `GA`-релиз `JDK`.

    Минимальная конфигурация в `build.gradle`:
    ```groovy
    plugins {
        id "java"
    }

    java {
        toolchain {
            languageVersion = JavaLanguageVersion.of(25)
            vendor = JvmVendorSpec.ADOPTIUM
        }
    }
    ```

    Указание `vendor` необязательно и просто соответствует `toolchain` `Adoptium`, который используется в примерах проектов; его можно опустить или выбрать другого поставщика.

=== ":simple-kotlin: `Kotlin`"

    Требуется версия не ниже [`JDK` `25`](https://openjdk.org/projects/jdk/25/), рекомендуется использовать последний доступный `GA`-релиз `JDK`.

    Используйте те же версии, на которых собран сам фреймворк: [`Kotlin` `2.4.10`](https://github.com/JetBrains/kotlin/releases) и [`KSP` `2.3.11`](https://github.com/google/ksp/releases).
    Расхождение между компилятором `Kotlin` и компилятором, встроенным в `KSP`, приводит к труднодиагностируемым падениям обработчиков символов, поэтому обе версии закрепляются вместе.

    Минимальная конфигурация в `build.gradle.kts`:
    ```kotlin
    plugins {
        kotlin("jvm") version "2.4.10"
        id("com.google.devtools.ksp") version "2.3.11"
    }

    kotlin {
        jvmToolchain {
            languageVersion.set(JavaLanguageVersion.of(25))
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }
    ```

!!! warning "Самому процессу `Gradle` тоже нужен достаточно новый `JDK`"

    `toolchain` в `Gradle` влияет только на компиляцию и запуск приложения, а classpath `buildscript` разрешается той `JVM`, на которой работает сам `Gradle`.
    Как только туда попадает артефакт Kora - чаще всего это `io.koraframework:openapi-generator` для генерации кода по `OpenAPI` - сборка на старой `JVM` падает уже на стадии конфигурации:

    ```text
    Dependency requires at least JVM runtime version 25. This build uses a Java 21 JVM.
    ```

    Запускайте `Gradle` на `JDK` `25+` через `JAVA_HOME` или через настройки `JVM` демона `Gradle`.
    Не прописывайте `org.gradle.java.home` в `gradle.properties` репозитория: этот путь зависит от конкретной машины.

!!! note "Автоматическая загрузка `JDK` для `toolchain`"

    Чтобы `Gradle` мог сам скачать недостающий `JDK` для `toolchain`, в примерах проектов Kora подключен резолвер в `settings.gradle`:

    ```groovy
    plugins {
        id "org.gradle.toolchains.foojay-resolver-convention" version "1.0.0"
    }
    ```

    и включена загрузка в `gradle.properties`:

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true
    ```

!!! note "Нуллабельность"

    В `Java` Kora размечает нуллабельность через [JSpecify](https://jspecify.dev/) - `org.jspecify.annotations.Nullable`, которая приходит транзитивно с любым модулем Kora.
    Это `type-use`-аннотации, поэтому их позиция значима: `Outer.@Nullable Inner`, `List<@Nullable String>`, `String @Nullable []`.
    В `Kotlin` нуллабельность выражается самим типом (`T?`) и никакой аннотации не требуется; при переопределении контракта Kora, параметр которого помечен `@Nullable`, объявляйте параметр нуллабельным.

## Система сборки { #build-system }

Kora рассчитана на сборку через [Gradle](https://gradle.org/guides/), потому что `Gradle` хорошо поддерживает обработчики аннотаций, `KSP`, инкрементальную сборку и управление зависимостями.
Сам фреймворк и все примеры проектов Kora собираются на `Gradle` `9.5.1`, поэтому рекомендуемая версия - `Gradle` `9.5+`.

Чтобы не указывать версии для каждой зависимости Kora отдельно, используется [`BOM`](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import) `io.koraframework:kora-bom`.
Версия `BOM` задается один раз, а остальные зависимости Kora подключаются без явного указания версии.

===! ":fontawesome-brands-java: `Java`"

    Минимальная конфигурация приложения в `build.gradle`:
    ```groovy
    plugins {
        id "java"
        id "application"
    }

    java {
        toolchain {
            languageVersion = JavaLanguageVersion.of(25)
            vendor = JvmVendorSpec.ADOPTIUM
        }
    }

    configurations {
        koraBom //(1)!
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testImplementation.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1")

        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:http-server-undertow"
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:logging-logback"
    }
    ```

    1.  Отдельная конфигурация `koraBom`, которую наследуют все остальные. `platform()`, подключенный только к `implementation`, не дошел бы до `annotationProcessor` и `testAnnotationProcessor`, и тогда зависимость обработчика пришлось бы указывать с явной версией.

    Более подробный пример есть в [руководстве по созданию первого приложения](../guides/getting-started.md).

=== ":simple-kotlin: `Kotlin`"

    Для `Kotlin` предполагается [Gradle Kotlin DSL](https://docs.gradle.org/current/userguide/kotlin_dsl.html).
    Если проект использует `Groovy DSL`, ориентируйтесь на примеры для `Java`.

    Минимальная конфигурация приложения в `build.gradle.kts`:
    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version "2.4.10"
        id("com.google.devtools.ksp") version "2.3.11"
    }

    kotlin {
        jvmToolchain {
            languageVersion.set(JavaLanguageVersion.of(25))
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1")) //(1)!

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")
    }
    ```

    1.  В `Kotlin`-проектах `BOM` подключается прямо к `implementation`, отдельная конфигурация `koraBom` с `extendsFrom` не создается.
    2.  Конфигурация `ksp` не покрывается `BOM`, поэтому версия обработчика указывается явно.

    Более подробный пример есть в [руководстве по созданию первого приложения](../guides/getting-started.md).

В реальных проектах версию `BOM` обычно выносят в свойство `gradle.properties` (например `koraVersion`) и ссылаются на нее как `platform("io.koraframework:kora-bom:$koraVersion")`, чтобы версия объявлялась в одном месте, а не была прописана в каждом модуле.

!!! note "Доступ к внутренностям компилятора"

    Некоторые обработчики аннотаций `Java` читают внутренние компоненты `jdk.compiler`. На новых версиях `JDK` для этого может потребоваться экспортировать соответствующие пакеты компилятору.
    Все примеры проектов Kora задают эти аргументы `JVM` в `gradle.properties` безусловно; добавьте их, если компиляция завершается ошибками `IllegalAccessError` или `module jdk.compiler does not export ...`:

    ```properties
    org.gradle.jvmargs=--add-exports jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED \
      --add-exports jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED \
      --add-exports jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED \
      --add-exports jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED \
      --add-exports jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED \
      --add-exports jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED
    ```

## Зависимости { #dependencies }

В документации модулей Kora обычно показывается только зависимость конкретного модуля.
Но в приложении также должны быть подключены [`BOM`](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import) и обработчики, показанные ниже.

===! ":fontawesome-brands-java: `Java`"

    `build.gradle`:

    ```groovy
    configurations {
        koraBom
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testImplementation.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1") //(1)!

        annotationProcessor "io.koraframework:annotation-processors" //(2)!
        testAnnotationProcessor "io.koraframework:annotation-processors" //(3)!
    }
    ```

    1.  `BOM` с версиями всех артефактов Kora (обязательно, без значения по умолчанию).
    2.  Все обработчики аннотаций Kora для основных исходников (обязательно, без значения по умолчанию).
    3.  Те же обработчики для тестовых исходников - нужны только если в тестах объявлены собственные аннотации Kora, например собственный `@KoraApp` (опционально).

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1")) //(1)!

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!
        kspTest("io.koraframework:symbol-processors:2.0.0.RC1") //(3)!
    }
    ```

    1.  `BOM` с версиями всех артефактов Kora (обязательно, без значения по умолчанию).
    2.  Все `KSP`-обработчики Kora для основных исходников (обязательно, без значения по умолчанию).
    3.  Те же обработчики для тестовых исходников - нужны только если в тестах объявлен собственный `@KoraApp`, например отдельный `TestApplication` (опционально).

После этого зависимости модулей можно указывать без версии, например:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    implementation "io.koraframework:http-server-undertow"
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    implementation("io.koraframework:http-server-undertow")
    ```

Все артефакты Kora находятся в группе `io.koraframework`.
Исключение - экспериментальные модули: декларативный `S3`-клиент `s3-client-kora` и интеграции с `Camunda` `camunda-engine-bpmn`, `camunda-rest-undertow`, `camunda-zeebe-worker` вместе с их обработчиками - они публикуются в группе `io.koraframework.experimental`.

## Запуск { #run }

Приложение Kora - это интерфейс с аннотацией `@KoraApp`, который наследует нужные приложению модули.
Обработчик генерирует рядом с ним класс, названный по имени интерфейса с суффиксом `Graph`, а его статический метод `graph()` возвращает описание графа зависимостей:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, JsonModule, LogbackModule, UndertowPublicHttpServerModule { //(1)!

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph); //(2)!
        }
    }
    ```

    1.  Аннотация `@KoraApp` лежит в `io.koraframework.common.annotation`, а модули приходят из подключенных артефактов Kora.
    2.  `ApplicationGraph` генерируется обработчиком по имени интерфейса `Application` и попадает в тот же пакет. `KoraApplication.run` принимает это описание (`ApplicationGraphDraw`), инициализирует граф, регистрирует обработчик остановки и блокирует поток до завершения работы приложения.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, JsonModule, LogbackModule, UndertowPublicHttpServerModule //(1)!

    fun main() {
        KoraApplication.run(ApplicationGraph::graph) //(2)!
    }
    ```

    1.  Аннотация `@KoraApp` лежит в `io.koraframework.common.annotation`, а модули приходят из подключенных артефактов Kora.
    2.  `ApplicationGraph` генерируется обработчиком по имени интерфейса `Application` и попадает в тот же пакет. `KoraApplication.run` принимает это описание (`ApplicationGraphDraw`), инициализирует граф, регистрирует обработчик остановки и блокирует поток до завершения работы приложения.

Для локального запуска и сборки исполняемого архива обычно используется [плагин `application`](https://docs.gradle.org/current/userguide/application_plugin.html).

> [!TIP]
> Рекомендуется всегда использовать фиксированные значения `applicationName = "application"` и `archiveFileName = "application.tar"` — это упрощает работу с архивом в `Dockerfile` и CI/CD-скриптах, так как имя файла не зависит от версии проекта.

===! ":fontawesome-brands-java: `Java`"

    Подключите плагин в `build.gradle`:
    ```groovy
    plugins {
        id "application" //(1)!
    }
    ```

    1.  Плагин `application` предоставляет задачи для запуска и сборки исполняемого архива (по умолчанию не подключен, опционально). Подробнее в [документации Gradle](https://docs.gradle.org/current/userguide/application_plugin.html).

    Системные свойства и переменные окружения для локального запуска можно задать в задаче `run`:
    ```groovy
    run {
        jvmArgs += [
            "-Xmx256m", //(1)!
        ]

        environment([
            "SOME_ENV": "someValue", //(2)!
        ])
    }
    ```

    1.  JVM-аргументы для запуска приложения (по умолчанию не указаны, опционально)
    2.  Переменные окружения, доступные в приложении (по умолчанию не указаны, опционально)

    Запуск:
    ```shell
    ./gradlew run
    ```

    Настройка сборки архива:
    ```groovy
    application {
        applicationName = "application" //(1)!
        mainClass = "io.koraframework.example.Application" //(2)!
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"] //(3)!
    }

    distTar {
        archiveFileName = "application.tar" //(4)!
    }
    ```

    1.  Имя приложения, используется для именования скриптов (по умолчанию: имя проекта). **Рекомендуется фиксировать значение `"application"`** для упрощения работы в `Dockerfile` и CI/CD.
    2.  Полное имя класса с методом `main` для запуска (по умолчанию не указан, обязательно).
    3.  JVM-аргументы по умолчанию для запуска (по умолчанию не указаны, опционально). Если приложение использует `StructuredTaskScope`, сюда также нужно добавить `--enable-preview`.
    4.  Имя файла архива (по умолчанию: `<applicationName>-<version>.tar`). **Рекомендуется фиксировать значение `"application.tar"`** для упрощения работы в `Dockerfile` и CI/CD. Подробнее в [документации по задаче `Tar`](https://docs.gradle.org/current/dsl/org.gradle.api.tasks.bundling.Tar.html#org.gradle.api.tasks.bundling.Tar:archiveFileName).

    Сборка архива:
    ```shell
    ./gradlew distTar
    ```

    Пример настроенного приложения можно посмотреть в [шаблоне Java-приложения](https://github.com/kora-projects/kora-java-template/blob/master/build.gradle).

=== ":simple-kotlin: `Kotlin`"

    Подключите плагин в `build.gradle.kts`:
    ```kotlin
    plugins {
        id("application") //(1)!
        kotlin("jvm") version "2.4.10"
        id("com.google.devtools.ksp") version "2.3.11"
    }
    ```

    1.  Плагин `application` предоставляет задачи для запуска и сборки исполняемого архива (по умолчанию не подключен, опционально)

    Системные свойства и переменные окружения для локального запуска можно задать в задачах `JavaExec`:
    ```kotlin
    tasks.withType<JavaExec> {
        jvmArgs(
            "-Xmx256m", //(1)!
        )

        environment(
            "SOME_ENV" to "someValue", //(2)!
        )
    }
    ```

    1.  JVM-аргументы для запуска приложения (по умолчанию не указаны, опционально)
    2.  Переменные окружения, доступные в приложении (по умолчанию не указаны, опционально)

    Запуск:
    ```shell
    ./gradlew run
    ```

    Настройка сборки архива:
    ```kotlin
    application {
        applicationName = "application" //(1)!
        mainClass.set("io.koraframework.example.ApplicationKt") //(2)!
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8") //(3)!
    }

    tasks.distTar {
        archiveFileName.set("application.tar") //(4)!
    }
    ```

    1.  Имя приложения, используется для именования скриптов (по умолчанию: имя проекта). **Рекомендуется фиксировать значение `"application"`** для упрощения работы в `Dockerfile` и CI/CD.
    2.  Полное имя класса с методом `main` для запуска (по умолчанию не указан, обязательно); для Kotlin это класс с суффиксом `Kt`.
    3.  JVM-аргументы по умолчанию для запуска (по умолчанию не указаны, опционально). Если приложение использует `StructuredTaskScope`, сюда также нужно добавить `--enable-preview`.
    4.  Имя файла архива (по умолчанию: `<applicationName>-<version>.tar`). **Рекомендуется фиксировать значение `"application.tar"`** для упрощения работы в `Dockerfile` и CI/CD. Подробнее в [документации по задаче `Tar`](https://docs.gradle.org/current/dsl/org.gradle.api.tasks.bundling.Tar.html#org.gradle.api.tasks.bundling.Tar:archiveFileName).

    Сборка архива:
    ```shell
    ./gradlew distTar
    ```

    Пример настроенного приложения можно посмотреть в [шаблоне Kotlin-приложения](https://github.com/kora-projects/kora-kotlin-template/blob/master/build.gradle.kts).

## Терминология { #terminology }

В этой секции описаны базовые термины, которые встречаются в документации Kora:

- Фабрика - метод, который создает и возвращает экземпляр компонента или зависимости.
- [Модуль](container.md#external-module-factory) - подключаемая зависимость или интерфейс с фабричными методами, которые добавляют в приложение новые компоненты.
- [Компонент](container.md#components) - объект в графе зависимостей Kora. Обычно это единственный экземпляр класса, который реализует часть логики приложения.
- Аспект - логика, которая расширяет поведение метода до, после или вокруг его выполнения на основании аннотации.
- Граф зависимостей - набор компонентов приложения и связей между ними, построенный Kora на этапе компиляции.

## Первое руководство { #first-guide }

После общего обзора переходите к руководству [Создание первого приложения на Kora](../guides/getting-started.md).
В нем базовая структура приложения показана на небольшом `HTTP`-сервисе, который можно собрать и запустить.
