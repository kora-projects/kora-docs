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

    Требуется версия не ниже [JDK 17](https://openjdk.org/projects/jdk/17/), рекомендуется всегда использовать самую последнюю версию JDK, или как минимум [`JDK` `25+`](https://openjdk.org/projects/jdk/25/), чтобы раскрыть все возможности виртуальных потоков.

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

    Указание `vendor` необязательно и просто соответствует набору инструментов `Adoptium`, который используется в примерах проектов; его можно опустить или выбрать другого поставщика.

=== ":simple-kotlin: `Kotlin`"

    Требуется версия не ниже [JDK 17](https://openjdk.org/projects/jdk/17/), 
    рекомендуется [`JDK` `21`](https://openjdk.org/projects/jdk/21/) из-за совместимости с `Kotlin`, так как версия Kotlin `1.9+` не поддерживают стабильно версии JDK выше.

    Рекомендуемая и поддерживаенмая версия [`Kotlin` `1.9+`](https://github.com/JetBrains/kotlin/releases), совместимость с версиями `1.8+` и `2+` не гарантируется.
    Рекомендуемая и поддерживаенмая версия [`KSP` `1.9+`](https://github.com/google/ksp/releases) должна соответствовать версии `Kotlin`.

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
Требуется версия `Gradle` `7+`, рекомендуется `Gradle` `9.5+` или самая последняя.

Чтобы не указывать версии для каждой зависимости Kora отдельно, используется [`BOM`](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import) `ru.tinkoff.kora:kora-parent`.
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
            languageVersion = JavaLanguageVersion.of(21)
            vendor = JvmVendorSpec.ADOPTIUM
        }
    }

    dependencies {
        annotationProcessor "ru.tinkoff.kora:annotation-processors:1.2.18"
        implementation(platform("ru.tinkoff.kora:kora-parent:1.2.18"))
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

    dependencies {
        ksp("ru.tinkoff.kora:symbol-processors:1.2.18")
        implementation(platform("ru.tinkoff.kora:kora-parent:1.2.18"))
    }
    ```

    Более подробный пример есть в [руководстве по созданию первого приложения](../guides/getting-started.md).

В реальных проектах версию `BOM` обычно выносят в свойство `gradle.properties` (например `koraVersion`) и ссылаются на нее как `platform("ru.tinkoff.kora:kora-parent:$koraVersion")`, чтобы версия объявлялась в одном месте, а не была прописана в каждом модуле.

!!! note "Доступ к внутренностям компилятора"

    Некоторые обработчики аннотаций `Java` читают внутренние компоненты `jdk.compiler`. На новых версиях `JDK` для этого может потребоваться экспортировать соответствующие пакеты компилятору.
    Если компиляция завершается ошибками `IllegalAccessError` или `module jdk.compiler does not export ...`, добавьте в `gradle.properties` следующие аргументы `JVM`:

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
    dependencies {
        annotationProcessor "ru.tinkoff.kora:annotation-processors:1.2.18"
        implementation(platform("ru.tinkoff.kora:kora-parent:1.2.18"))
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:

    ```kotlin
    dependencies {
        ksp("ru.tinkoff.kora:symbol-processors:1.2.18")
        implementation(platform("ru.tinkoff.kora:kora-parent:1.2.18"))
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
        mainClassName = "ru.tinkoff.kora.java.Application" //(2)!
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"] //(3)!
    }

    distTar {
        archiveFileName = "application.tar" //(4)!
    }
    ```

    1.  Имя приложения, используется для именования скриптов (по умолчанию: имя проекта). **Рекомендуется фиксировать значение `"application"`** для упрощения работы в `Dockerfile` и CI/CD.
    2.  Полное имя класса с методом `main` для запуска (по умолчанию не указан, обязательно).
    3.  JVM-аргументы по умолчанию для запуска (по умолчанию не указаны, опционально).
    4.  Имя файла архива (по умолчанию: `<applicationName>-<version>.tar`). **Рекомендуется фиксировать значение `"application.tar"`** для упрощения работы в `Dockerfile` и CI/CD. Подробнее в [документации по задаче `Tar`](https://docs.gradle.org/current/dsl/org.gradle.api.tasks.bundling.Tar.html#org.gradle.api.tasks.bundling.Tar:archiveFileName).


=== ":simple-kotlin: `Kotlin`"

    Подключите плагин в `build.gradle.kts`:
    ```kotlin
    plugins {
        id("application") //(1)!
        kotlin("jvm") version "1.9.25"
        id("com.google.devtools.ksp") version "1.9.25-1.0.20"
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
        mainClass.set("ru.tinkoff.kora.kotlin.ApplicationKt") //(2)!
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8") //(3)!
    }

    tasks.distTar {
        archiveFileName.set("application.tar") //(4)!
    }
    ```

    1.  Имя приложения, используется для именования скриптов (по умолчанию: имя проекта). **Рекомендуется фиксировать значение `"application"`** для упрощения работы в `Dockerfile` и CI/CD.
    2.  Полное имя класса с методом `main` для запуска (по умолчанию не указан, обязательно); для Kotlin это класс с суффиксом `Kt`.
    3.  JVM-аргументы по умолчанию для запуска (по умолчанию не указаны, опционально).
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

## Первое руководство

После общего обзора переходите к руководству [Создание первого приложения на Kora](../guides/getting-started.md).
В нем базовая структура приложения показана на небольшом `HTTP`-сервисе, который можно собрать и запустить.
