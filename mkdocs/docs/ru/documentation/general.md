---
description: "Explains Kora framework fundamentals, annotation processors, compatibility, Gradle build setup, dependencies, application runtime, and terminology. Use when working with @KoraApp, annotation processors, Gradle, BOM, kora-parent, application plugin."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora framework fundamentals, annotation processors, Gradle, BOM, kora-parent, application plugin."
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

Если нужен пошаговый разбор перед справочным описанием, смотрите [Создание первого приложения на Kora](../guides/getting-started.md) и [Введение во внедрение зависимостей](../guides/dependency-injection-introduction.md).

## Обработчики аннотаций { #annotation-processor }

Kora строит приложение на этапе компиляции: обработчики читают аннотации, проверяют код и генерируют исходные файлы, которые затем компилируются вместе с кодом приложения.
За счет этого граф зависимостей, аспекты, `HTTP`-обработчики, репозитории и другие компоненты становятся обычным скомпилированным кодом без `Reflection` во время работы.

===! ":fontawesome-brands-java: `Java`"

    Аннотация - это конструкция, связанная с элементами исходного кода `Java`: классами, методами, параметрами и полями.
    [Обработчик аннотаций](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/annotation/processing/Processor.html) запускается компилятором, читает эти аннотации и может сгенерировать дополнительный исходный код или остановить компиляцию с понятной ошибкой.

    Kora предоставляет все обработчики аннотаций в одной зависимости:

    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    ```

    Эта зависимость нужна только на этапе компиляции и не добавляет лишние библиотеки в путь классов времени выполнения приложения.

=== ":simple-kotlin: `Kotlin`"

    Для `Kotlin` используется [`KSP`](https://kotlinlang.org/docs/ksp-overview.html) (`Kotlin Symbol Processing`).
    `KSP` читает символы исходного кода `Kotlin`, передает их процессорам Kora и позволяет генерировать код до основной компиляции.

    Kora предоставляет `KSP`-обработчики в одной зависимости:

    ```kotlin
    ksp("ru.tinkoff.kora:symbol-processors")
    ```

    При этом обработка `Kotlin` обычно медленнее обработки аннотаций в `Java`.

### `KSP` { #ksp }

`KSP` нужен только для `Kotlin`-проектов.
Если приложение написано на `Java`, используйте обычный `annotationProcessor`; если приложение написано на `Kotlin`, подключайте `com.google.devtools.ksp` и зависимость `ru.tinkoff.kora:symbol-processors`.

## Совместимость { #compatibility }

===! ":fontawesome-brands-java: `Java`"

    Требуется версия не ниже [JDK 17](https://openjdk.org/projects/jdk/17/), рекомендуется [`JDK` `25+`](https://openjdk.org/projects/jdk/25/).

    Минимальная конфигурация в `build.gradle`:
    ```groovy
    plugins {
        id "java"
    }

    sourceCompatibility = JavaVersion.VERSION_25
    targetCompatibility = JavaVersion.VERSION_25
    ```

=== ":simple-kotlin: `Kotlin`"

    Требуется версия не ниже [JDK 17](https://openjdk.org/projects/jdk/17/), рекомендуется [`JDK` `21`](https://openjdk.org/projects/jdk/21/) из-за совместимости с `Kotlin`.

    Рекомендуемая версия [`Kotlin` `1.9+`](https://github.com/JetBrains/kotlin/releases), совместимость с версиями `1.8+` и `2+` не гарантируется.
    Рекомендуемая версия [`KSP` `1.9+`](https://github.com/google/ksp/releases) должна соответствовать версии `Kotlin`.

    Минимальная конфигурация в `build.gradle.kts`:
    ```kotlin
    plugins {
        kotlin("jvm") version "1.9.25"
        id("com.google.devtools.ksp") version "1.9.25-1.0.20"
    }

    kotlin {
        jvmToolchain { languageVersion.set(JavaLanguageVersion.of("21")) }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }
    ```

## Система сборки { #build-system }

Kora рассчитана на сборку через [Gradle](https://gradle.org/guides/), потому что `Gradle` хорошо поддерживает обработчики аннотаций, `KSP`, инкрементальную сборку и управление зависимостями.
Требуется версия `Gradle` `7+`, рекомендуется `Gradle` `9.5+`.

Чтобы не указывать версии для каждой зависимости Kora отдельно, используется [`BOM`](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import) `ru.tinkoff.kora:kora-parent`.
Версия `BOM` задается один раз, а остальные зависимости Kora подключаются без явного указания версии.

===! ":fontawesome-brands-java: `Java`"

    Минимальная конфигурация приложения в `build.gradle`:
    ```groovy
    plugins {
        id "java"
        id "application"
    }

    sourceCompatibility = JavaVersion.VERSION_25
    targetCompatibility = JavaVersion.VERSION_25

    configurations {
        koraBom
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        api.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("ru.tinkoff.kora:kora-parent:1.2.16")
        annotationProcessor "ru.tinkoff.kora:annotation-processors"
    }
    ```

    Более подробный пример есть в [руководстве по созданию первого приложения](../guides/getting-started.md).

=== ":simple-kotlin: `Kotlin`"

    Для `Kotlin` предполагается [Gradle Kotlin DSL](https://docs.gradle.org/current/userguide/kotlin_dsl.html).
    Если проект использует `Groovy DSL`, ориентируйтесь на примеры для `Java`.

    Минимальная конфигурация приложения в `build.gradle.kts`:
    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version "1.9.25"
        id("com.google.devtools.ksp") version "1.9.25-1.0.20"
    }

    kotlin {
        jvmToolchain { languageVersion.set(JavaLanguageVersion.of("21")) }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    val koraBom: Configuration by configurations.creating
    configurations {
        ksp.get().extendsFrom(koraBom)
        compileOnly.get().extendsFrom(koraBom)
        api.get().extendsFrom(koraBom)
        implementation.get().extendsFrom(koraBom)
    }

    dependencies {
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.2.16"))
        ksp("ru.tinkoff.kora:symbol-processors")
    }
    ```

    Более подробный пример есть в [руководстве по созданию первого приложения](../guides/getting-started.md).

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
        api.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("ru.tinkoff.kora:kora-parent:1.2.16")
        annotationProcessor "ru.tinkoff.kora:annotation-processors"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:

    ```kotlin
    val koraBom: Configuration by configurations.creating
    configurations {
        ksp.get().extendsFrom(koraBom)
        compileOnly.get().extendsFrom(koraBom)
        api.get().extendsFrom(koraBom)
        implementation.get().extendsFrom(koraBom)
    }

    dependencies {
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.2.16"))
        ksp("ru.tinkoff.kora:symbol-processors")
    }
    ```

После этого зависимости модулей можно указывать без версии, например:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    implementation "ru.tinkoff.kora:http-server-undertow"
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    implementation("ru.tinkoff.kora:http-server-undertow")
    ```

## Запуск { #run }

Для локального запуска и сборки исполняемого архива обычно используется [плагин `application`](https://docs.gradle.org/current/userguide/application_plugin.html).

===! ":fontawesome-brands-java: `Java`"

    Подключите плагин в `build.gradle`:
    ```groovy
    plugins {
        id "application"
    }
    ```

    Системные свойства и переменные окружения для локального запуска можно задать в задаче `run`:
    ```groovy
    run {
        jvmArgs += [
            "-Xmx256m",
        ]

        environment([
            "SOME_ENV": "someValue",
        ])
    }
    ```

    Запуск:
    ```shell
    ./gradlew run
    ```

    Настройка сборки архива:
    ```groovy
    application {
        applicationName = "application"
        mainClassName = "ru.tinkoff.kora.java.Application"
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"]
    }

    distTar {
        archiveFileName = "application.tar"
    }
    ```

    Сборка архива:
    ```shell
    ./gradlew distTar
    ```

    Пример настроенного приложения можно посмотреть в [шаблоне Java-приложения](https://github.com/kora-projects/kora-java-template/blob/master/build.gradle).

=== ":simple-kotlin: `Kotlin`"

    Подключите плагин в `build.gradle.kts`:
    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version "1.9.25"
        id("com.google.devtools.ksp") version "1.9.25-1.0.20"
    }
    ```

    Системные свойства и переменные окружения для локального запуска можно задать в задачах `JavaExec`:
    ```kotlin
    tasks.withType<JavaExec> {
        jvmArgs(
            "-Xmx256m",
        )

        environment(
            "SOME_ENV" to "someValue",
        )
    }
    ```

    Запуск:
    ```shell
    ./gradlew run
    ```

    Настройка сборки архива:
    ```kotlin
    application {
        applicationName = "application"
        mainClass.set("ru.tinkoff.kora.kotlin.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }

    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

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

## Первое руководство

После общего обзора переходите к руководству [Создание первого приложения на Kora](../guides/getting-started.md).
В нем базовая структура приложения показана на небольшом `HTTP`-сервисе, который можно собрать и запустить.
