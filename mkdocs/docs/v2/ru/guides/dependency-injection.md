---
search:
  exclude: true
title: Создание приложений Kora с внедрением зависимостей
summary: A comprehensive step-by-step tutorial for building complete applications with Kora's dependency injection framework
description: "Step-by-step multi-module Kora 2.0 application built around the dependency graph: a @KoraApp root, io.koraframework.common.annotation annotations (@Component, @Module, @KoraSubmodule, @DefaultComponent, @Tag, @Root, @FactoryModule), All<T> and ValueOf<T> claims, JSpecify @Nullable optional dependencies, Lifecycle and LifecycleWrapper, generic factories, and the Gradle setup with io.koraframework:kora-bom, annotation-processors and symbol-processors."
agent:
  use_when: "Use this file for questions about assembling a real multi-module Kora application graph: @KoraApp with extends, @Module auto-discovery, @KoraSubmodule across Gradle modules, @DefaultComponent overrides, @Tag and Tag.Any, All<T> collection injection, @Nullable optional dependencies, generic factory methods, @FactoryModule, ValueOf<T> and Wrapped<T>/LifecycleWrapper lifecycle control, and the Gradle multi-module build with io.koraframework:kora-bom."
tags: dependency-injection, tutorial, components, modules, java, kotlin
---

# Создание приложений Kora с внедрением зависимостей { #building-kora-applications-dependency }

В этом руководстве показано, как на практике собирать приложение с помощью внедрения зависимостей Kora, работающего во время компиляции. Вы разберете, как `@KoraApp`, `@Module` и `@Component`
описывают граф зависимостей, как интерфейсы и реализации связываются внутри этого графа, а также как службы с жизненным циклом запускаются и останавливаются контейнером. Вы также увидите, как границы
модулей помогают сохранять полноценное приложение понятным по мере роста.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-dependency-injection).

## Что вы построите { #youll-build }

Вы соберете полноценное приложение системы уведомлений, которое демонстрирует все основные возможности внедрения зависимостей Kora:

- **Многомодульная структура проекта** с разделением ответственности
- **Компонентная архитектура** с подключением внешних библиотечных модулей
- **Тегированные зависимости** для нескольких реализаций одного интерфейса
- **Внедрение коллекций**, чтобы получить сразу все реализации
- **Подмодули** для организации связанных компонентов в отдельных модулях Gradle
- **Обобщенные фабрики** для типобезопасного создания компонентов
- **Фабричные модули** для экземпляров модулей, которые сами являются компонентами графа
- **Опциональные зависимости** для корректной работы при отсутствии компонента
- Приём **ValueOf<T>**, который предотвращает каскадное пересоздание компонентов

## Что понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Текстовый редактор или IDE
- Базовое знание Java или Kotlin
- Знакомство с концепциями внедрения зависимостей (см. [Внедрение зависимостей в Kora](dependency-injection-introduction.md))

## Предварительные требования { #prerequisites }

!!! note "Рекомендуется: сначала прочитайте введение в DI"

    Руководство предполагает, что вы уже прочитали **[Внедрение зависимостей в Kora](dependency-injection-introduction.md)** и понимаете базовые концепции внедрения зависимостей, которые использует Kora.

    Если введение еще не прочитано, начните с него: это руководство быстро переходит к полноценному многомодульному приложению и сосредоточено на применении шаблонов DI, а не на их определении с нуля.

    Также понадобится базовое знание Java или Kotlin.

Здесь мы собираем приложение Kora с нуля, вводя концепции внедрения зависимостей постепенно. Каждый шаг добавляет новую функциональность и демонстрирует конкретный шаблон DI. В конце у вас будет
полностью работающее приложение, показывающее все основные возможности DI в Kora.

## Обзор { #overview }

Руководство идет от концепций DI к практической сборке приложения. Предметная область здесь — система уведомлений, но важнее другое: как настоящий граф Kora остается понятным, когда в нем несколько
модулей, реализаций, опциональных зависимостей и объектов с жизненным циклом.

Доменная модель на протяжении руководства остается одной и той же, а возможности графа добавляются вокруг нее. Так же происходит и в реальной работе: возможности DI редко изучают в отрыве от задачи —
их применяют потому, что приложению нужны границы модулей, переопределения, несколько реализаций или управление ресурсами.

### Граф приложения { #application-graph }

[Граф приложения Kora](../documentation/container.md) — это не просто список классов. Это типизированная структура, которая описывает, какие компоненты существуют, какие зависимости нужны каждому из
них и как эти компоненты создаются. `@KoraApp` — корень графа, `@Module` группирует фабрики и подключения, а классы `@Component` становятся управляемыми узлами графа.

Все эти аннотации лежат в одном пакете `io.koraframework.common.annotation` и обрабатываются только во время компиляции. Ничего из описанного здесь не резолвится рефлексией при старте: обработчик
аннотаций (Java) или символьный процессор (Kotlin) читает аннотации и генерирует класс `ApplicationGraph` рядом с вашим типом `Application`.

Хороший дизайн графа делает ответственность видимой:

- модули приложения описывают собственные компоненты приложения
- библиотечные модули предоставляют переиспользуемые значения по умолчанию
- интерфейсы задают точки замены
- фабрики создают значения, которым нужна нестандартная сборка

### Настройка компонентов { #component-setup }

Реальным приложениям часто нужно больше одной реализации интерфейса. Теги позволяют Kora различать зависимости с одинаковым Java-типом, но разной ролью. Переопределения дают приложению возможность
заменить библиотечное значение по умолчанию собственным поведением. Опциональные зависимости позволяют компоненту работать и тогда, когда другого компонента в графе нет.

Эти возможности сильны именно тем, что решают задачи связывания, не пряча их. По графу зависимостей по-прежнему видно, какая реализация используется и почему.

### Жизненный цикл { #lifecycle }

Некоторые компоненты владеют ресурсами: клиентами, планировщиками, соединениями, фоновыми обработчиками. Kora умеет управлять такими компонентами, чтобы запуск и остановка происходили в порядке графа.
Контракт `Lifecycle` для этого лежит в `io.koraframework.application.graph` и объявляет ровно два метода — `init()` и `release()`. Также в руководстве вводится `ValueOf<T>` — способ зависеть от ссылки
на компонент, не заставляя все нижестоящие компоненты пересоздаваться.

К концу руководства приложение уведомлений должно выглядеть как рабочий пример проектирования графа: границы модулей, внешние значения по умолчанию, переопределения, теги, опциональные зависимости,
обобщенные фабрики и управление жизненным циклом служат одному приложению, а не выглядят набором изолированных возможностей.

Практический порядок такой:

1. создать многомодульный проект Kora
2. подключить значения по умолчанию из внешних модулей
3. переопределить отдельные компоненты
4. использовать теги для нескольких реализаций одного типа
5. описать опциональные зависимости
6. вынести связанные компоненты в подмодуль
7. добавить обобщенные фабрики и поведение с жизненным циклом

## Зависимости { #dependencies }

В руководстве используется отдельный `settings.gradle` на верхнем уровне, а общая конфигурация Gradle лежит в `guide-dependency-injection/build.gradle`. В эталонном репозитории над каталогом этого
руководства есть еще один уровень, потому что в одном рабочем пространстве живет сразу несколько приложений-руководств.

Создайте каталоги проекта:

```bash
mkdir -p guide-dependency-injection
mkdir -p guide-dependency-injection/guide-dependency-injection-common guide-dependency-injection/guide-dependency-injection-lib guide-dependency-injection/guide-dependency-injection-app
```

Модули Kora публикуются под Java 25, и эталонные приложения фиксируют toolchain на Java 25, поэтому установите Eclipse Temurin JDK 25 и запускайте Gradle именно на нем.

===! ":simple-linux: `Linux`"

    Для Ubuntu/Debian можно подключить репозиторий Adoptium и установить Temurin JDK:

    ```bash
    sudo apt update
    sudo apt install -y wget gpg
    wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /usr/share/keyrings/adoptium.gpg
    echo "deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(. /etc/os-release && echo $VERSION_CODENAME) main" | sudo tee /etc/apt/sources.list.d/adoptium.list
    sudo apt update
    sudo apt install -y temurin-25-jdk
    ```

=== ":simple-apple: `macOS`"

    Если установлен Homebrew, поставьте Temurin JDK через cask:

    ```bash
    brew install --cask temurin@25
    export JAVA_HOME=$(/usr/libexec/java_home -v 25)
    ```

=== ":material-microsoft-windows: `Windows`"

    Если установлен `winget`, поставьте Temurin JDK из PowerShell:

    ```powershell
    winget install EclipseAdoptium.Temurin.25.JDK
    ```

    Если `winget` недоступен, скачайте установщик для Windows со [страницы загрузок Eclipse Temurin](https://adoptium.net/temurin/releases/?version=25), выберите **JDK 25** для своей архитектуры,
    запустите установщик и включите опцию, которая обновляет `JAVA_HOME` и `PATH`, если она предлагается.

    После установки откройте новый терминал, чтобы переменные окружения обновились.

Проверьте, что JDK доступен:

```bash
java -version
```

В выводе должна быть Java 25.

Подготовьте Gradle Wrapper в том же каталоге. Многомодульный проект в этом руководстве создается вручную, поэтому шага `gradle init`, который сгенерировал бы файлы wrapper за вас, здесь нет.

Шаг 1. Создайте `gradle-wrapper.properties`.

===! ":simple-linux: `Linux`"

    ```bash
    mkdir -p gradle/wrapper
    cat > gradle/wrapper/gradle-wrapper.properties << 'EOF'
    distributionBase=GRADLE_USER_HOME
    distributionPath=wrapper/dists
    distributionUrl=https\://services.gradle.org/distributions/gradle-9.5.1-bin.zip
    networkTimeout=10000
    validateDistributionUrl=true
    zipStoreBase=GRADLE_USER_HOME
    zipStorePath=wrapper/dists
    EOF
    ```

=== ":simple-apple: `macOS`"

    ```bash
    mkdir -p gradle/wrapper
    cat > gradle/wrapper/gradle-wrapper.properties << 'EOF'
    distributionBase=GRADLE_USER_HOME
    distributionPath=wrapper/dists
    distributionUrl=https\://services.gradle.org/distributions/gradle-9.5.1-bin.zip
    networkTimeout=10000
    validateDistributionUrl=true
    zipStoreBase=GRADLE_USER_HOME
    zipStorePath=wrapper/dists
    EOF
    ```

=== ":material-microsoft-windows: `Windows`"

    ```powershell
    New-Item -ItemType Directory -Force gradle/wrapper
    @'
    distributionBase=GRADLE_USER_HOME
    distributionPath=wrapper/dists
    distributionUrl=https\://services.gradle.org/distributions/gradle-9.5.1-bin.zip
    networkTimeout=10000
    validateDistributionUrl=true
    zipStoreBase=GRADLE_USER_HOME
    zipStorePath=wrapper/dists
    '@ | Set-Content -Encoding UTF8 gradle/wrapper/gradle-wrapper.properties
    ```

Шаг 2. Скачайте `gradle-wrapper.jar`.

===! ":simple-linux: `Linux`"

    ```bash
    curl -L https://raw.githubusercontent.com/gradle/gradle/v9.5.1/gradle/wrapper/gradle-wrapper.jar -o gradle/wrapper/gradle-wrapper.jar
    ```

=== ":simple-apple: `macOS`"

    ```bash
    curl -L https://raw.githubusercontent.com/gradle/gradle/v9.5.1/gradle/wrapper/gradle-wrapper.jar -o gradle/wrapper/gradle-wrapper.jar
    ```

=== ":material-microsoft-windows: `Windows`"

    ```powershell
    Invoke-WebRequest -Uri https://raw.githubusercontent.com/gradle/gradle/v9.5.1/gradle/wrapper/gradle-wrapper.jar -OutFile gradle/wrapper/gradle-wrapper.jar
    ```

Шаг 3. Скачайте запускающий скрипт wrapper.

===! ":simple-linux: `Linux`"

    ```bash
    curl -L https://raw.githubusercontent.com/gradle/gradle/v9.5.1/gradlew -o gradlew
    chmod +x gradlew
    ```

=== ":simple-apple: `macOS`"

    ```bash
    curl -L https://raw.githubusercontent.com/gradle/gradle/v9.5.1/gradlew -o gradlew
    chmod +x gradlew
    ```

=== ":material-microsoft-windows: `Windows`"

    ```powershell
    Invoke-WebRequest -Uri https://raw.githubusercontent.com/gradle/gradle/v9.5.1/gradlew.bat -OutFile gradlew.bat
    ```

### Настройка проекта { #project-setup }

Теперь настроим многомодульную конфигурацию Gradle. Это руководство не про одномодульное приложение: оно показывает, как Kora собирает граф приложения из нескольких модулей, поэтому раскладка проекта
здесь — часть материала.

Gradle должен сделать здесь несколько вещей:

- зарегистрировать модули руководства
- задать JDK, которым компилируется каждый модуль
- сделать версии из BOM Kora доступными нужным конфигурациям Gradle
- включить генерацию кода Kora в каждом модуле, где объявляются элементы графа
- применить общие правила компиляции и тестов

#### Структура модулей { #module-structure }

Создайте следующую структуру каталогов. Расширения файлов отличаются у Gradle Groovy DSL и Gradle Kotlin DSL, но границы модулей остаются теми же:

===! ":fontawesome-brands-java: `Java`"

    ```
    |-- settings.gradle
    |-- gradle.properties
    `-- guide-dependency-injection/
        |-- build.gradle
        |-- guide-dependency-injection-common/
        |-- guide-dependency-injection-lib/
        `-- guide-dependency-injection-app/
    ```

=== ":simple-kotlin: `Kotlin`"

    ```
    |-- settings.gradle.kts
    |-- gradle.properties
    `-- guide-dependency-injection/
        |-- build.gradle.kts
        |-- guide-dependency-injection-common/
        |-- guide-dependency-injection-lib/
        `-- guide-dependency-injection-app/
    ```

`guide-dependency-injection-common` содержит общие контракты, `guide-dependency-injection-lib` имитирует переиспользуемую библиотеку, а `guide-dependency-injection-app` — запускаемое приложение с
`@KoraApp`. Четвертый модуль, `guide-dependency-injection-submodule`, добавляется позже, когда руководство доходит до `@KoraSubmodule`. Именно такое разделение позволяет дальше показать
переопределения, теги, опциональные зависимости и обнаружение компонентов между модулями.

#### Корневые настройки { #root-settings }

Отредактируйте файл настроек Gradle верхнего уровня. Он задает имя сборки Gradle и перечисляет входящие в нее модули:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    plugins {
        id "org.gradle.toolchains.foojay-resolver-convention" version "1.0.0"
    }

    rootProject.name = "kora-guide"

    include "guide-dependency-injection:guide-dependency-injection-common"
    include "guide-dependency-injection:guide-dependency-injection-lib"
    include "guide-dependency-injection:guide-dependency-injection-app"
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    pluginManagement {
        plugins {
            id("org.jetbrains.kotlin.jvm") version "2.4.10" //(1)!
            id("com.google.devtools.ksp") version "2.3.11" //(2)!
        }
    }

    plugins {
        id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
    }

    rootProject.name = "kora-guide"

    include("guide-dependency-injection:guide-dependency-injection-common")
    include("guide-dependency-injection:guide-dependency-injection-lib")
    include("guide-dependency-injection:guide-dependency-injection-app")
    ```

    1.  Версия плагина Kotlin JVM объявляется один раз на всю сборку, чтобы файлы сборки модулей подключали плагин без повторного указания версии.
    2.  Версия плагина KSP. Она привязана к версии Kotlin, поэтому обе поднимаются вместе.

Плагин `foojay-resolver-convention` нужен для Java toolchain: он помогает Gradle найти или скачать требуемый JDK. Строки `include` регистрируют вложенные модули по путям Gradle, например
`:guide-dependency-injection:guide-dependency-injection-app`, чтобы можно было запускать задачи для конкретного модуля.

#### Свойства Gradle { #gradle-properties }

Добавьте `gradle.properties`, чтобы Gradle умел находить установленные JDK, скачивать нужный Temurin toolchain, если JDK 25 нет локально, и чтобы версии Kora и JUnit задавались один раз для всех модулей:

===! ":fontawesome-brands-java: `Java`"

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true

    koraVersion=2.0.0.RC1
    junitVersion=6.1.3
    ```

=== ":simple-kotlin: `Kotlin`"

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true
    kotlin.jvm.target.validation.mode=warning

    koraVersion=2.0.0.RC1
    junitVersion=6.1.3
    ```

Первые два свойства делают сборку руководства менее зависимой от конкретной машины. `koraVersion` и `junitVersion` — обычные свойства проекта Gradle: каждый файл сборки читает их как `$koraVersion` и
`$junitVersion`, поэтому версия поднимается ровно в одном месте. Флаг валидации для Kotlin повторяет эталонные приложения: если компилятор Kotlin не может точно нацелиться на версию JVM из toolchain,
он сообщает об этом предупреждением, а не падает.

#### Общий файл сборки { #shared-build-file }

Создайте общий файл сборки в каталоге `guide-dependency-injection/`. Он применяется к вложенным модулям `common`, `lib`, `app`, а позже и `submodule`, поэтому toolchain, репозитории и настройки тестов
не нужно дублировать в каждом модуле.

Начните с импортов и пустого блока `subprojects`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    subprojects {
        repositories {
            mavenCentral()
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import org.gradle.api.plugins.JavaPluginExtension
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    subprojects {
        repositories {
            mavenCentral()
        }
    }
    ```

Из `mavenCentral()` скачиваются сама Kora, Logback, HOCON и их транзитивные зависимости.

#### BOM Kora { #kora-bom }

Kora состоит из множества модулей. Чтобы не указывать версию у каждой зависимости, подключается BOM (`Bill of Materials`) `io.koraframework:kora-bom`. Он согласует версии всех модулей Kora и тех
сторонних библиотек, с которыми Kora поставляется. Java и Kotlin подключают этот BOM по-разному, и разницу полезно понять до того, как писать остальную часть файла сборки.

===! ":fontawesome-brands-java: `Java`"

    В Java BOM кладется в отдельную конфигурацию `koraBom`, объявленную один раз в `subprojects {}`. Пока она ничего не резолвит; в следующих разделах реальные конфигурации начнут ее наследовать:

    ```groovy
    subprojects {
        configurations {
            koraBom
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    В Kotlin общей конфигурации для BOM нет. Каждый модуль подключает platform прямо в `implementation`, который уже наследует `testImplementation`:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:$koraVersion"))
    }
    ```

    Конфигурация `ksp` не наследует `implementation`, поэтому symbol processor Kora — единственная зависимость, у которой всегда остается явная версия.

#### Toolchain JDK { #jdk-toolchain }

Настраивайте JDK после того, как в модуле включен плагин `java`. Gradle может работать на одном JDK, а компилировать проект другим, поэтому toolchain делает сборку руководства воспроизводимой. Модули
Kora компилируются под Java 25, поэтому toolchain должен быть Java 25 или новее.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    subprojects {
        plugins.withId("java") {
            java {
                toolchain {
                    languageVersion = JavaLanguageVersion.of(25)
                    vendor = JvmVendorSpec.ADOPTIUM
                }
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    subprojects {
        plugins.withId("org.jetbrains.kotlin.jvm") {
            extensions.configure<org.jetbrains.kotlin.gradle.dsl.KotlinJvmProjectExtension>("kotlin") {
                jvmToolchain {
                    languageVersion.set(JavaLanguageVersion.of(25))
                    vendor.set(JvmVendorSpec.ADOPTIUM)
                }
            }
        }

        plugins.withId("java") {
            extensions.configure<JavaPluginExtension>("java") {
                toolchain {
                    languageVersion.set(JavaLanguageVersion.of(25))
                    vendor.set(JvmVendorSpec.ADOPTIUM)
                }
            }
        }
    }
    ```

    Kotlin требует оба блока: `jvmToolchain` управляет компилятором Kotlin, а toolchain для `java` — вызовом `javac` для Java-исходников, которые KSP и Gradle все равно компилируют в том же модуле.

#### Конфигурации classpath { #classpath-configurations }

Генерация кода Kora выполняется на своем classpath, отдельном от classpath приложения. В Java это `annotationProcessor`, в Kotlin — конфигурация `ksp`, которую добавляет плагин KSP. Обеим нужны
согласованные версии Kora.

===! ":fontawesome-brands-java: `Java`"

    Сделайте BOM доступным конфигурациям, которые используются кодом приложения, compile-time API, обработкой аннотаций, публичным API библиотек и тестами:

    ```groovy
    subprojects {
        plugins.withId("java") {
            configurations.annotationProcessor.extendsFrom(configurations.koraBom)
            configurations.compileOnly.extendsFrom(configurations.koraBom)
            configurations.implementation.extendsFrom(configurations.koraBom)
            configurations.testImplementation.extendsFrom(configurations.koraBom)
            configurations.testAnnotationProcessor.extendsFrom(configurations.koraBom)
        }

        plugins.withId("java-library") {
            configurations.api.extendsFrom(configurations.koraBom)
        }
    }
    ```

    `annotationProcessor` и `testAnnotationProcessor` получают BOM отдельно, потому что обработчики аннотаций Kora резолвятся в своем classpath. Конфигурация `api` важна для `common` и `lib`, где типы
    становятся частью публичного API, доступного другим модулям.

=== ":simple-kotlin: `Kotlin`"

    В Kotlin общий блок `extendsFrom` не нужен. Каждый модуль, объявляющий элементы графа, подключает плагин KSP и указывает процессор с явной версией:

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("java-library")
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:$koraVersion"))

        ksp("io.koraframework:symbol-processors:$koraVersion")
    }

    kotlin {
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
    }
    ```

    Каталог исходников `build/generated/ksp/main/kotlin` важен для IDE и для компиляции, потому что KSP пишет туда сгенерированный Kotlin-код Kora. Модули, которые генерируют код и для тестов,
    добавляют `sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }`.

#### Версия Kora { #kora-version }

Теперь подключите сам BOM. Переменная `$koraVersion` берется из `gradle.properties`; после этой строки модули могут объявлять зависимости Kora без явных версий.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    subprojects {
        dependencies {
            koraBom platform("io.koraframework:kora-bom:$koraVersion")
        }
    }
    ```

    Поскольку `implementation`, `annotationProcessor`, `compileOnly`, `testImplementation`, `testAnnotationProcessor` и `api` наследуют `koraBom`, одной строки достаточно для всех модулей.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:$koraVersion"))

        ksp("io.koraframework:symbol-processors:$koraVersion")
    }
    ```

    В Kotlin эти две строки живут в файле сборки каждого модуля, а не в общем файле, потому что конфигурация `ksp` появляется только у модулей с плагином KSP.

#### Итоговый файл { #final-file }

Итоговый общий файл сборки собирает все решения вместе: репозитории, toolchain JDK, связывание classpath, BOM Kora и общее поведение тестов.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    subprojects {
        repositories {
            mavenCentral()
        }

        configurations {
            koraBom
        }

        plugins.withId("java") {
            java {
                toolchain {
                    languageVersion = JavaLanguageVersion.of(25)
                    vendor = JvmVendorSpec.ADOPTIUM
                }
            }

            configurations.annotationProcessor.extendsFrom(configurations.koraBom)
            configurations.compileOnly.extendsFrom(configurations.koraBom)
            configurations.implementation.extendsFrom(configurations.koraBom)
            configurations.testImplementation.extendsFrom(configurations.koraBom)
            configurations.testAnnotationProcessor.extendsFrom(configurations.koraBom)
        }

        plugins.withId("java-library") {
            configurations.api.extendsFrom(configurations.koraBom)
        }

        dependencies {
            koraBom platform("io.koraframework:kora-bom:$koraVersion")
        }

        tasks.withType(JavaCompile).configureEach {
            options.encoding = "UTF-8"
        }

        tasks.withType(Test).configureEach {
            useJUnitPlatform()
            testLogging {
                showStandardStreams(true)
                events("passed", "skipped", "failed")
                exceptionFormat("full")
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import org.gradle.api.plugins.JavaPluginExtension
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    subprojects {
        repositories {
            mavenCentral()
        }

        plugins.withId("org.jetbrains.kotlin.jvm") {
            extensions.configure<org.jetbrains.kotlin.gradle.dsl.KotlinJvmProjectExtension>("kotlin") {
                jvmToolchain {
                    languageVersion.set(JavaLanguageVersion.of(25))
                    vendor.set(JvmVendorSpec.ADOPTIUM)
                }
            }
        }

        plugins.withId("java") {
            extensions.configure<JavaPluginExtension>("java") {
                toolchain {
                    languageVersion.set(JavaLanguageVersion.of(25))
                    vendor.set(JvmVendorSpec.ADOPTIUM)
                }
            }
        }

        tasks.withType<Test>().configureEach {
            useJUnitPlatform()
            testLogging {
                showStandardStreams = true
                events("passed", "skipped", "failed")
                exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
            }
        }
    }
    ```

### Основа приложения { #application-base }

**Цель**: создать модуль общих контрактов и запускаемый модуль приложения, которые будут расширяться на следующих шагах.

**Что вводит этот шаг**: минимальную точку входа `@KoraApp`, модуль общих контрактов и исходную многомодульную раскладку. Это базовый граф до того, как поверх него начнут накладываться остальные
возможности DI.

**Зачем это нужно**: сначала мы определяем, что относится к модулю приложения, а что — к переиспользуемым модулям. Это повторяет разделение, описанное
в [Внедрении зависимостей в Kora: @KoraApp](dependency-injection-introduction.md#koraapp), [@Root](dependency-injection-introduction.md#root)
и [Документации контейнера: Контейнер](../documentation/container.md#container).

**Что мы эмулируем**: настоящий корень приложения, который владеет запуском, и общий API-модуль, от которого могут зависеть другие модули, не притягивая при этом специфичное для приложения поведение.

В руководстве используется пакет `io.koraframework.guide.dependencyinjection` — тот же, что и в эталонных приложениях. Стабильное имя пакета упрощает сверку вашего проекта с готовым примером и поиск
сгенерированных Kora исходников.

**Создайте общие контракты** (`guide-dependency-injection/guide-dependency-injection-common/src/main/java/io/koraframework/guide/dependencyinjection/common/`
или `guide-dependency-injection/guide-dependency-injection-common/src/main/kotlin/io/koraframework/guide/dependencyinjection/common/`):

#### Сборка общего модуля { #build-shared-module }

Сначала создайте файл сборки для `guide-dependency-injection-common`. В этом модуле лежат только интерфейсы и общие типы, поэтому ему нужен библиотечный JVM-плагин и тестовые зависимости, но не плагин
приложения и не генерация кода Kora.

===! ":fontawesome-brands-java: `Java`"

    Плагин `java-library` подходит модулям с публичным API:

    ```groovy
    plugins {
        id "java-library"
    }
    ```

    От `common` будут зависеть другие модули, поэтому Gradle должен различать внутренние зависимости реализации и типы, входящие в публичный API.

    Добавьте тестовые зависимости:

    ```groovy
    dependencies {
        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

    `junit-bom` согласует версии JUnit, `junit-jupiter` добавляет JUnit 5, а `test-junit5` — тестовые утилиты Kora. На этом шаге тестов может еще не быть, но модуль уже готов к проверкам контрактов и
    компонентов. Версия у `test-junit5` не нужна, потому что общий файл сборки уже заставил `testImplementation` наследовать `koraBom`.

    Итоговый `build.gradle` общего модуля:

    ```groovy
    plugins {
        id "java-library"
    }

    dependencies {
        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Плагин Kotlin JVM компилирует Kotlin-код в классы JVM, которые смогут использовать модули `app` и `lib`, а `java-library` отделяет публичный API от зависимостей реализации:

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("java-library")
    }
    ```

    Ни у одного плагина здесь нет версии: обе версии объявлены один раз в `settings.gradle.kts`.

    Добавьте BOM Kora и тестовые зависимости:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }
    ```

    `junit-bom` согласует версии JUnit, `junit-jupiter` добавляет JUnit 5, а `test-junit5` — тестовые утилиты Kora. `testImplementation` наследует `implementation`, поэтому именно подключенный выше BOM
    Kora позволяет объявить `test-junit5` без версии.

    Итоговый `build.gradle.kts` общего модуля:

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("java-library")
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }
    ```

Затем создайте интерфейсы:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.common;

    public interface Notifier {
        void notify(String user, String message);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.common

    fun interface Notifier {
        fun notify(user: String, message: String)
    }
    ```

В Kotlin `Notifier` объявлен как `fun interface`, чтобы дальше в руководстве фабрики модулей могли возвращать его лямбдой.

**Создайте основное приложение** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/io/koraframework/guide/dependencyinjection/`
или `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/io/koraframework/guide/dependencyinjection/`):

#### Сборка приложения { #build-application }

Создайте файл сборки для `guide-dependency-injection-app`. Этот модуль запускаемый, содержит `@KoraApp` и должен включать генерацию графа Kora, поэтому его настройка Gradle сложнее, чем у модуля общих
контрактов.

===! ":fontawesome-brands-java: `Java`"

    Начните с плагинов:

    ```groovy
    plugins {
        id "application"
    }
    ```

    Плагин `application` сам подключает `java` и добавляет `./gradlew run` вместе с настройкой главного класса, поэтому отдельная строка `id "java"` не нужна.

    Добавьте обработчик аннотаций Kora:

    ```groovy
    dependencies {
        annotationProcessor "io.koraframework:annotation-processors"
    }
    ```

    `annotationProcessor` читает `@KoraApp` и генерирует `ApplicationGraph`. Без этой строки компиляция Java может дойти до ссылки на сгенерированный класс, но сам граф приложения создан не будет.

    Теперь добавьте зависимости приложения:

    ```groovy
    dependencies {
        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"
    }
    ```

    `common` дает общий интерфейс `Notifier`, `config-hocon` — конфигурацию, `logging-logback` — логирование. Проектные зависимости на `lib` и `submodule` добавляются на тех шагах, где эти модули
    создаются.

    Добавьте настройку тестов:

    ```groovy
    dependencies {
        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

    `testAnnotationProcessor` нужен только тогда, когда в тестовых исходниках объявлен собственный `@KoraApp` или другие аннотации Kora, требующие обработки. `test-junit5` добавляет расширение Kora для
    JUnit 5.

    Настройте запуск приложения:

    ```groovy
    application {
        applicationName = "application"
        mainClass = "io.koraframework.guide.dependencyinjection.Application"
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"]
    }
    ```

    Этот блок относится к плагину Gradle `application`. Он не является частью DI-контейнера Kora напрямую, но связывает сгенерированный Kora граф с обычным запуском JVM-приложения:

    - `applicationName = "application"` задает короткое имя приложения в дистрибутиве Gradle. По нему создаются стартовые скрипты вроде `bin/application`.
    - `mainClass` указывает на класс с `main`. В Java это исходный интерфейс `Application`, а не сгенерированный `ApplicationGraph`: ваш метод `main` вызывает
      `KoraApplication.run(ApplicationGraph::graph)`.
    - `applicationDefaultJvmArgs` задает аргументы JVM для `./gradlew run` и для сгенерированных стартовых скриптов.

    Важно, что `mainClass` указывает на обычный исходный код. `ApplicationGraph` появляется только после работы `annotationProcessor`, поэтому задача `classes` проверяет сразу компиляцию Java,
    обработку аннотаций и генерацию графа Kora.

    Задайте стабильное имя архива дистрибутива:

    ```groovy
    distTar {
        archiveFileName = "application.tar"
    }
    ```

    `distTar` — задача плагина Gradle `application`. Она собирает tar-архив с классами приложения, runtime-зависимостями и стартовыми скриптами. По умолчанию имя архива формируется из имени и версии
    проекта, что в многомодульном учебном проекте получается длинным и неудобным.

    `archiveFileName = "application.tar"` делает имя артефакта стабильным. Это удобно для тестов, CI и дальнейших шагов руководства, потому что они могут ссылаться на один предсказуемый файл, а не
    собирать имя из имени проекта и версии.

    Итоговый `build.gradle` приложения:

    ```groovy
    plugins {
        id "application"
    }

    dependencies {
        annotationProcessor "io.koraframework:annotation-processors"

        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"

        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }

    application {
        applicationName = "application"
        mainClass = "io.koraframework.guide.dependencyinjection.Application"
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"]
    }

    distTar {
        archiveFileName = "application.tar"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Начните с плагинов:

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("application")
    }
    ```

    `org.jetbrains.kotlin.jvm` компилирует Kotlin-код, `com.google.devtools.ksp` запускает symbol processor Kora, а `application` добавляет `./gradlew run`.

    Добавьте BOM Kora и KSP-процессор:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")
    }
    ```

    KSP читает `@KoraApp` и генерирует `ApplicationGraph`. Без этой зависимости приложение не получит сгенерированный граф. Конфигурация `ksp` не покрывается BOM, поэтому у нее сохраняется явная версия.

    Теперь добавьте зависимости приложения:

    ```kotlin
    dependencies {
        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")
    }
    ```

    `common` дает общий интерфейс `Notifier`, `config-hocon` — конфигурацию HOCON, `logging-logback` — логирование. Проектные зависимости на `lib` и `submodule` добавляются на тех шагах, где эти модули
    создаются.

    Добавьте тестовые зависимости:

    ```kotlin
    dependencies {
        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }
    ```

    Строки `kspTest(...)` здесь нет. Она нужна только когда в тестовых исходниках объявлен собственный `@KoraApp` или другие аннотации Kora, требующие обработки; тестам, которые переиспользуют основной
    граф `Application` через `@KoraAppTest`, она не нужна.

    Зарегистрируйте каталоги вывода KSP и настройте запуск:

    ```kotlin
    kotlin {
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    application {
        applicationName = "application"
        mainClass.set("io.koraframework.guide.dependencyinjection.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }
    ```

    Блок `application` объясняет Gradle, как запускать Kotlin-приложение:

    - `applicationName` задает имя приложения в дистрибутиве и имя стартового скрипта.
    - `mainClass.set(...)` указывает на класс с `main`. В Kotlin функция `main` верхнего уровня из `Application.kt` компилируется в JVM-класс `ApplicationKt`, поэтому главный класс — `ApplicationKt`.
    - `applicationDefaultJvmArgs` задает аргументы JVM для `./gradlew run` и сгенерированных стартовых скриптов.

    Аргумент `-Dfile.encoding=UTF-8` фиксирует кодировку во время выполнения. Это убирает различия между Windows, Linux и macOS при записи текста в логи и чтении строковых ресурсов.

    Задайте стабильное имя tar-архива:

    ```kotlin
    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

    `distTar` собирает исполняемый дистрибутив с классами, runtime-зависимостями и стартовыми скриптами. Фиксированное имя `application.tar` удобно для тестов, CI и дальнейших шагов руководства,
    которым нужен один предсказуемый артефакт.

    Итоговый `build.gradle.kts` приложения:

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("application")
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }

    kotlin {
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    application {
        applicationName = "application"
        mainClass.set("io.koraframework.guide.dependencyinjection.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }

    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

Затем создайте приложение:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends HoconConfigModule, LogbackModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application : HoconConfigModule, LogbackModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`KoraApplication.run(...)` принимает `Supplier<ApplicationGraphDraw>`, а сгенерированный класс `ApplicationGraph` предоставляет ровно это через статический метод `graph()` — поэтому ссылка на метод
`ApplicationGraph::graph` сюда подходит. Сгенерированный класс всегда называется по типу с `@KoraApp` плюс суффикс `Graph`, то есть интерфейс `Application` дает `ApplicationGraph`. До первого запуска
обработки аннотаций или KSP этого класса не существует.

**Соберите и запустите**:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

**Ожидаемый вывод**: приложение стартует и корректно завершается. Kora пишет `Application initialized in ...ms`, а по `Ctrl+C` — `Application shutdown...`. Корневых компонентов в графе пока нет,
поэтому больше ничего не происходит; компоненты и модули добавляются на следующих шагах.

---

### Внешние модули { #external-modules }

**Цель**: создать переиспользуемые библиотечные модули, которые предоставляют реализации по умолчанию.

**Что вводит этот шаг**: фабрики внешних модулей и `@DefaultComponent`. `EmailModule` находится вне модуля приложения и предоставляет значения по умолчанию, которые приложение может принять или
заменить позже.

**Зачем это нужно**: внешние модули — это способ, которым переиспользуемые библиотеки Kora публикуют компоненты для приложений, но они не обнаруживаются автоматически и должны подключаться явно. Это
соответствует разделам [Внедрение зависимостей в Kora: @Module](dependency-injection-introduction.md#module), [@DefaultComponent](dependency-injection-introduction.md#defaultcomponent)
и [Документация контейнера: фабрика внешнего модуля](../documentation/container.md#external-module-factory).

**Что мы эмулируем**: библиотеку, которая поставляет реализацию уведомителя по электронной почте и договор конфигурации по умолчанию, но при этом позволяет приложению позже переопределить детали
представления.

Сначала создайте файл сборки библиотечного модуля. В отличие от `common`, этот модуль объявляет тип с `@ConfigMapper`, поэтому ему нужна собственная генерация кода Kora:

===! ":fontawesome-brands-java: `Java`"

    `guide-dependency-injection/guide-dependency-injection-lib/build.gradle`

    ```groovy
    plugins {
        id "java-library"
    }

    dependencies {
        annotationProcessor "io.koraframework:annotation-processors"

        api project(":guide-dependency-injection:guide-dependency-injection-common")

        implementation "io.koraframework:config-common"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `guide-dependency-injection/guide-dependency-injection-lib/build.gradle.kts`

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("java-library")
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        api(project(":guide-dependency-injection:guide-dependency-injection-common"))

        implementation("io.koraframework:config-common")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }

    kotlin {
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
    }
    ```

`api project(...)` выбран намеренно: `Notifier` встречается в сигнатурах, которые публикует этот модуль, поэтому потребители `lib` тоже должны его видеть. `config-common` приносит контракты
конфигурации `Config` и `ConfigValueMapper`, не навязывая библиотеке конкретный формат конфигурации — выбор между HOCON и YAML остается за приложением.

Затем зарегистрируйте новый модуль в корневом файле настроек и добавьте его в classpath приложения:

===! ":fontawesome-brands-java: `Java`"

    В `settings.gradle` модуль уже перечислен, а `guide-dependency-injection-app/build.gradle` теперь зависит от него:

    ```groovy
    dependencies {
        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation project(":guide-dependency-injection:guide-dependency-injection-lib")
        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    В `settings.gradle.kts` модуль уже перечислен, а `guide-dependency-injection-app/build.gradle.kts` теперь зависит от него:

    ```kotlin
    dependencies {
        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-lib"))
        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")
    }
    ```

**Создайте EmailConfig** (`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/io/koraframework/guide/dependencyinjection/email/`
или `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/io/koraframework/guide/dependencyinjection/email/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.email;

    import io.koraframework.config.common.annotation.ConfigMapper;

    @ConfigMapper
    public record EmailConfig(String topic) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.email

    import io.koraframework.config.common.annotation.ConfigMapper

    @ConfigMapper
    data class EmailConfig(val topic: String)
    ```

`@ConfigMapper` — это библиотечная аннотация конфигурации: она указывает Kora сгенерировать `ConfigValueMapper<EmailConfig>`, не привязывая тип к фиксированному пути конфигурации. Путь выбирает
метод модуля ниже, поэтому один и тот же тип конфигурации можно переиспользовать в разных секциях. Для типа конфигурации, который принадлежит приложению и привязан к одному пути, используйте
`@ConfigSource` — см. [Конфигурация](../documentation/config.md).

**Создайте EmailModule** (тот же пакет):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.email;

    import java.util.function.Supplier;
    import io.koraframework.common.annotation.DefaultComponent;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.config.common.Config;
    import io.koraframework.config.common.mapper.ConfigValueMapper;
    import io.koraframework.guide.dependencyinjection.common.Notifier;

    public interface EmailModule {

        final class EmailTag {
            private EmailTag() {}
        }

        default EmailConfig config(Config config, ConfigValueMapper<EmailConfig> extractor) {
            return extractor.mapOrThrow(config.get("notifier.email")); //(1)!
        }

        @Tag(EmailTag.class)
        @DefaultComponent //(2)!
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL DEFAULT] ";
        }

        @Tag(EmailTag.class)
        default Notifier emailNotifier(EmailConfig emailConfig, @Tag(EmailTag.class) Supplier<String> headerSupplier) {
            return (user, message) -> System.out.println(headerSupplier.get() + emailConfig.topic() + " [USER:" + user + "]: " + message);
        }
    }
    ```

    1.  `mapOrThrow` завершает сборку графа ошибкой конфигурации, если секции нет или ее не удается отобразить. Используйте `map`, если отсутствующая секция должна давать `null`.
    2.  Помечает фабрику как стандартную: приложение может объявить собственную фабрику для того же типа и тега, и Kora предпочтет фабрику приложения.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.email

    import java.util.function.Supplier
    import io.koraframework.common.annotation.DefaultComponent
    import io.koraframework.common.annotation.Tag
    import io.koraframework.config.common.Config
    import io.koraframework.config.common.mapper.ConfigValueMapper
    import io.koraframework.guide.dependencyinjection.common.Notifier

    interface EmailModule {

        class EmailTag private constructor()

        fun config(config: Config, extractor: ConfigValueMapper<EmailConfig>): EmailConfig {
            return extractor.mapOrThrow(config["notifier.email"]) //(1)!
        }

        @Tag(EmailTag::class)
        @DefaultComponent //(2)!
        fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL DEFAULT] " }
        }

        @Tag(EmailTag::class)
        fun emailNotifier(
            emailConfig: EmailConfig,
            @Tag(EmailTag::class) headerSupplier: Supplier<String>
        ): Notifier {
            return Notifier { user, message ->
                println("${headerSupplier.get()}${emailConfig.topic} [USER:$user]: $message")
            }
        }
    }
    ```

    1.  `mapOrThrow` завершает сборку графа ошибкой конфигурации, если секции нет или ее не удается отобразить. Используйте `map`, если отсутствующая секция должна давать `null`.
    2.  Помечает фабрику как стандартную: приложение может объявить собственную фабрику для того же типа и тега, и Kora предпочтет фабрику приложения.

`EmailTag` — обычный вложенный класс, который служит только маркером во время компиляции. Он никогда не создается, поэтому у него может быть приватный конструктор. Классы-теги должны быть видны из
каждого места, которое на них ссылается, поэтому package-private или `private` тег верхнего уровня не будет работать между модулями.

**Обновите Application**, чтобы подключить модуль электронной почты:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        EmailModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

**Создайте application.conf** (`guide-dependency-injection/guide-dependency-injection-app/src/main/resources/`):

Полный справочник по конфигурации смотрите в разделе [Конфигурация](../documentation/config.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    notifier.email {
      topic = "USER" //(1)!
    }

    logging {
      levels {
        "ROOT": "WARN" //(2)!
        "io.koraframework": "INFO" //(3)!
      }
    }
    ```

    1.  Тема или название канала, которое использует компонент.
    2.  Уровень журналирования для `ROOT`.
    3.  Уровень журналирования для `io.koraframework` — это же пакет приложения из руководства.

=== ":simple-yaml: `YAML`"

    ```yaml
    notifier:
      email:
        topic: "USER" #(1)!

    logging:
      levels:
        ROOT: "WARN" #(2)!
        "io.koraframework": "INFO" #(3)!
    ```

    1.  Тема или название канала, которое использует компонент.
    2.  Уровень журналирования для `ROOT`.
    3.  Уровень журналирования для `io.koraframework` — это же пакет приложения из руководства.

Модуль приложения зависит от `config-hocon`, поэтому фактически читается `application.conf`. Если вам удобнее YAML, замените зависимость на `io.koraframework:config-yaml`, а модуль — на
`YamlConfigModule`.

**Соберите и запустите** — у приложения все еще нет корневого компонента, поэтому оно просто запускается и останавливается.

**Ключевое понятие**: `@DefaultComponent` предоставляет библиотечные значения по умолчанию, которые приложения могут переопределять.

**Правило регистрации модулей**: если тип помечен `@Module`, не подключайте его одновременно через `extends` в `@KoraApp` или другом модуле. Модуль должен регистрироваться ровно одним способом: либо
наследоваться через `extends`, либо обнаруживаться потому, что он помечен `@Module` и компилируется вместе с текущим `@KoraApp` / `@KoraSubmodule`. Сам `@KoraSubmodule` — это как раз тот случай, где
наследование ожидаемо, потому что обработчик ищет `@KoraSubmodule` только среди интерфейсов, которые расширяет тип с `@KoraApp`.

Учтите, что `@Module` можно ставить только на интерфейсы. На классе аннотация приводит к ошибке компиляции `@Module can only be applied to interfaces.`

**Что Kora генерирует для `EmailModule`**: после `./gradlew clean classes` в `ApplicationGraph` не обязательно окажутся ровно те же номера `componentN`, что показаны ниже, — это внутренние детали
генератора. Важна структура: Kora создает узел конфигурации, узел значения по умолчанию и узел уведомителя.

===! ":fontawesome-brands-java: `Java`"

    ??? abstract "Java: фрагмент сгенерированного графа для `EmailModule`"

        ```java
        private final Node<EmailConfig> component8;
        private final Node<Supplier<String>> component9;
        private final Node<Notifier> component10;

        component8 = graphDraw.addNode(_type_of_component8,
            null,
            null,
            List.of(component6, component7),
            List.of(component6, component7),
            List.of(),
            g -> impl.config(
                g.get(ApplicationGraph.holder0.component6),
                g.get(ApplicationGraph.holder0.component7)
            ));

        component9 = graphDraw.addNode(_type_of_component9,
            EmailModule.EmailTag.class,
            null,
            List.of(),
            List.of(),
            List.of(),
            g -> impl.emailNotifierHeaderSupplier());

        component10 = graphDraw.addNode(_type_of_component10,
            EmailModule.EmailTag.class,
            null,
            List.of(component8, component9),
            List.of(component8, component9),
            List.of(),
            g -> impl.emailNotifier(
                g.get(ApplicationGraph.holder0.component8),
                g.get(ApplicationGraph.holder0.component9)
            ));
        ```

        Здесь видно, почему `EmailModule` нужно подключать через `extends`: только тогда его фабричные методы попадают в граф приложения.

        - `component8` читает `notifier.email` и превращает HOCON-конфигурацию в типизированный `EmailConfig`.
        - `component9` — это `Supplier<String>` с тегом `EmailTag`. Так Kora отличает заголовок письма от других возможных компонентов `Supplier<String>`.
        - `component10` — это `Notifier` с тегом, который зависит от `EmailConfig` и от `Supplier<String>` с тегом.
        - Второй аргумент `addNode` — это тег, третий — необязательный предикат `@Conditional`, а два аргумента `List.of(...)` — зависимости на создание и на обновление.
        - `@DefaultComponent` у `emailNotifierHeaderSupplier()` означает, что библиотека дает значение по умолчанию, а приложение сможет заменить его в следующем разделе.

=== ":simple-kotlin: `Kotlin`"

    ??? abstract "Kotlin: фрагмент сгенерированного графа для `EmailModule`"

        ```kotlin
        public val component8: Node<EmailConfig>
        public val component9: Node<Supplier<String>>
        public val component10: Node<Notifier>

        component8 = graphDraw.addNode(map["component8"],
          null,
          null,
          listOf(component6, component7),
          listOf(component6, component7),
          listOf(),
          { impl.config(
            it.get(holder0.component6),
            it.get(holder0.component7)
          ) }
        )

        component9 = graphDraw.addNode(map["component9"],
          EmailModule.EmailTag::class.java,
          null,
          listOf(),
          listOf(),
          listOf(),
          { impl.emailNotifierHeaderSupplier() }
        )

        component10 = graphDraw.addNode(map["component10"],
          EmailModule.EmailTag::class.java,
          null,
          listOf(component8, component9),
          listOf(component8, component9),
          listOf(),
          { impl.emailNotifier(
            it.get(holder0.component8),
            it.get(holder0.component9)
          ) }
        )
        ```

        Kotlin/KSP генерирует тот же смысл в Kotlin-коде:

        - `EmailConfig` становится отдельным узлом графа.
        - `EmailTag` передается как тег узла и для `Supplier<String>`, и для `Notifier`.
        - `emailNotifier(...)` получает зависимости из графа, а не создает их сам.
        - В следующем разделе приложение переопределит `emailNotifierHeaderSupplier()`, и Kora подставит новый узел вместо библиотечного `@DefaultComponent`.

---

### Переопределение компонента { #component-override }

**Цель**: показать, как приложения могут переопределять библиотечные значения по умолчанию.

**Что вводит этот шаг**: переопределение компонента для фабрики `@DefaultComponent` из внешнего модуля. Приложение заменяет только поставщика заголовка и оставляет остальное библиотечное поведение
без изменений.

**Зачем это нужно**: библиотеки должны предоставлять надежные значения по умолчанию, но приложения должны сохранять окончательный контроль над поведением, видимым для предметной области. Это
соответствует разделам [Внедрение зависимостей в Kora: стандартная фабрика](dependency-injection-introduction.md#defaultcomponent-factory), [@DefaultComponent](dependency-injection-introduction.md#defaultcomponent)
и [Документация контейнера: стандартная фабрика](../documentation/container.md#default-factory).

**Что мы эмулируем**: настройку общего библиотечного уведомителя под конкретное приложение без ответвления или полного переписывания модуля.

**Создайте NotifyRunner** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/io/koraframework/guide/dependencyinjection/`
или `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/io/koraframework/guide/dependencyinjection/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection;

    import io.koraframework.application.graph.All;
    import io.koraframework.application.graph.Lifecycle;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Root;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.dependencyinjection.common.Notifier;

    @Root //(1)!
    @Component
    public final class NotifyRunner implements Lifecycle {

        private final All<Notifier> allNotifiers;

        public NotifyRunner(@Tag(Tag.Any.class) All<Notifier> allNotifiers) { //(2)!
            this.allNotifiers = allNotifiers;
        }

        @Override
        public void init() {
            System.out.println("DI tutorial step 3 start");
            for (var notifier : allNotifiers) {
                notifier.notify("Alice", "Welcome!");
            }
        }

        @Override
        public void release() {
            System.out.println("Application shutdown");
        }
    }
    ```

    1.  От `NotifyRunner` никто не зависит, поэтому без `@Root` Kora убрала бы его из графа и он никогда не был бы создан.
    2.  `@Tag(Tag.Any.class)` расширяет запрос на все `Notifier` независимо от тега. Без него запрос `All<Notifier>` без тега попадает только в уведомители без тегов.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection

    import io.koraframework.application.graph.All
    import io.koraframework.application.graph.Lifecycle
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Root
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.dependencyinjection.common.Notifier

    @Root //(1)!
    @Component
    class NotifyRunner(
        @Tag(Tag.Any::class) private val allNotifiers: All<Notifier> //(2)!
    ) : Lifecycle {

        override fun init() {
            println("DI tutorial step 3 start")
            for (notifier in allNotifiers) {
                notifier.notify("Alice", "Welcome!")
            }
        }

        override fun release() {
            println("Application shutdown")
        }
    }
    ```

    1.  От `NotifyRunner` никто не зависит, поэтому без `@Root` Kora убрала бы его из графа и он никогда не был бы создан.
    2.  `@Tag(Tag.Any::class)` расширяет запрос на все `Notifier` независимо от тега. Без него запрос `All<Notifier>` без тега попадает только в уведомители без тегов.

`Lifecycle` находится в `io.koraframework.application.graph` и объявляет ровно два метода — `init()` и `release()`. При старте Kora вызывает `init()` в порядке графа, а при остановке `release()` — в
обратном порядке, поэтому компонент всегда инициализируется после всего, от чего он зависит, и освобождается раньше своих зависимостей.

**Обновите Application**, чтобы переопределить заголовок письма:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import java.util.function.Supplier;
    import io.koraframework.common.annotation.Tag;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

        @Tag(EmailModule.EmailTag.class)
        @Override
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL OVERRIDDEN] ";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import java.util.function.Supplier
    import io.koraframework.common.annotation.Tag

    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        EmailModule {  // <----- Connected module

        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Переопределение — это обычное переопределение метода Java или Kotlin, поэтому совпадение сигнатуры уже гарантирует компилятор. `@Tag` нужно повторить на переопределяющем методе: тег входит в
идентичность компонента и не наследуется от переопределенного метода. Обратите внимание также, что переопределение намеренно не несет `@DefaultComponent` — именно поэтому фабрика приложения
побеждает библиотечное значение по умолчанию.

**Соберите и запустите**:

```
DI tutorial step 3 start
[EMAIL OVERRIDDEN] USER [USER:Alice]: Welcome!
Application shutdown
```

**Ключевое понятие**: приложения могут переопределять реализации `@DefaultComponent`, предоставляя собственные фабричные методы.

---

### Зависимости с тегами { #tagged-dependencies }

**Цель**: показать, как теги позволяют иметь несколько реализаций одного интерфейса, а `All<T>` — получать сразу все подходящие уведомители.

**Что вводит этот шаг**: `@Tag` для различения нескольких реализаций `Notifier` и `All<T>` для рассылки через них. `SmsModule` — внутренний `@Module`, поэтому он обнаруживается автоматически из модуля
приложения, а не наследуется через `extends`.

**Зачем это нужно**: как только у одного договора появляется несколько реализаций, обычного внедрения только по типу уже недостаточно. Теги делают граф явным, а `All<T>` дает естественный способ
разослать уведомления по всем каналам.
См. [Внедрение зависимостей в Kora: @Tag](dependency-injection-introduction.md#tag), [Запросы зависимостей и разрешение: All](dependency-injection-introduction.md#all), [Система тегов](dependency-injection-introduction.md#tag-system)
и [Документация контейнера: Tag any](../documentation/container.md#tag-any).

**Что мы эмулируем**: службу уведомлений, которая может отправить одно и то же сообщение через каждый доступный канал, а не выбирать только одну реализацию.

**Создайте контракт SMS-провайдера** в библиотечном модуле
(`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/io/koraframework/guide/dependencyinjection/sms/`
или `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/io/koraframework/guide/dependencyinjection/sms/`). Пока существует только контракт, его никто не предоставляет:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.sms;

    public interface SmsCellularProvider {
        String getCode();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.sms

    fun interface SmsCellularProvider {
        fun getCode(): String
    }
    ```

**Создайте SmsModule** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/io/koraframework/guide/dependencyinjection/sms/`
или `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/io/koraframework/guide/dependencyinjection/sms/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.sms;

    import org.jspecify.annotations.Nullable;
    import io.koraframework.common.annotation.Module;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.dependencyinjection.common.Notifier;

    @Module
    public interface SmsModule {

        final class SmsTag {
            private SmsTag() {}
        }

        @Tag(SmsTag.class)
        default Notifier smsNotifier(@Nullable SmsCellularProvider cellularProvider) {
            return (user, message) -> {
                if (cellularProvider == null) {
                    System.out.println("[SMS] " + user + "@" + message);
                } else {
                    System.out.println("+" + cellularProvider.getCode() + " [SMS] " + user + "@" + message);
                }
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.sms

    import io.koraframework.common.annotation.Module
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.dependencyinjection.common.Notifier

    @Module
    interface SmsModule {

        class SmsTag private constructor()

        @Tag(SmsTag::class)
        fun smsNotifier(cellularProvider: SmsCellularProvider?): Notifier {
            return Notifier { user, message ->
                if (cellularProvider == null) {
                    println("[SMS] $user@$message")
                } else {
                    println("+${cellularProvider.getCode()} [SMS] $user@$message")
                }
            }
        }
    }
    ```

В Java для необязательных зависимостей используется [JSpecify](https://jspecify.dev/) `org.jspecify.annotations.Nullable`. Он приходит транзитивно с любым модулем Kora, поэтому отдельная зависимость
не нужна. В Kotlin аннотации нет вообще: `?` у типа параметра — это и есть все объявление.

**Примечание о приложении**: `SmsModule` помечен `@Module` и компилируется вместе с `@KoraApp`, поэтому Kora обнаруживает его автоматически. Не добавляйте его через `extends` в `Application`.
Интерфейс `Application` остается ровно таким же, каким был на предыдущем шаге:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

        @Tag(EmailModule.EmailTag.class)
        @Override
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL OVERRIDDEN] ";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        EmailModule {  // <----- Connected module

        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

**Обновите NotifyRunner**, чтобы пройтись по всем уведомителям:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class NotifyRunner implements Lifecycle {

        private final All<Notifier> allNotifiers;

        public NotifyRunner(@Tag(Tag.Any.class) All<Notifier> allNotifiers) {
            this.allNotifiers = allNotifiers;
        }

        @Override
        public void init() {
            System.out.println("DI tutorial step 4 start");
            for (var notifier : allNotifiers) {
                notifier.notify("Bob", "Hello!");
            }
        }

        @Override
        public void release() {
            System.out.println("Application shutdown");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class NotifyRunner(
        @Tag(Tag.Any::class) private val allNotifiers: All<Notifier>
    ) : Lifecycle {

        override fun init() {
            println("DI tutorial step 4 start")
            for (notifier in allNotifiers) {
                notifier.notify("Bob", "Hello!")
            }
        }

        override fun release() {
            println("Application shutdown")
        }
    }
    ```

**Соберите и запустите**:

```
DI tutorial step 4 start
[SMS] Bob@Hello!
[EMAIL OVERRIDDEN] USER [USER:Bob]: Hello!
Application shutdown
```

В строке SMS пока нет кода оператора: `SmsCellularProvider` никто в графе не предоставляет, и nullable-параметр разрешился в `null`. Следующий шаг это исправляет.

**Ключевое понятие**: `@Tag` позволяет иметь несколько реализаций одного договора, а `@Tag(Tag.Any.class) All<T>` — рассылать сообщение сразу по всем из них.

---

### Опциональные зависимости { #optional-dependencies }

**Цель**: добавить необязательного соисполнителя для SMS, не меняя договор `Notifier`.

**Что вводит этот шаг**: допускающие `null` зависимости для необязательного поведения. `SmsModule` может работать как с `SmsCellularProvider`, так и без него, а `SmsCellularModule` добавляет
поставщика только тогда, когда приложение решает его унаследовать.

**Зачем это нужно**: некоторые возможности должны дополнять существующий компонент, а не вынуждать создавать отдельную ветку реализации. Это
соответствует разделам [Внедрение зависимостей в Kora: Nullable](dependency-injection-introduction.md#optional)
и [Документация контейнера: необязательные зависимости](../documentation/container.md#optional-dependencies).

**Что мы эмулируем**: необязательное обогащение форматирования SMS кодом оператора, при котором уведомитель продолжает работать даже без настроенного поставщика.

**Создайте SmsCellularModule** рядом с `SmsCellularProvider` в библиотечном модуле
(`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/io/koraframework/guide/dependencyinjection/sms/`
или `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/io/koraframework/guide/dependencyinjection/sms/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.sms;

    import io.koraframework.common.annotation.DefaultComponent;

    public interface SmsCellularModule {

        @DefaultComponent
        default SmsCellularProvider smsCellularProvider() {
            return () -> "1";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.sms

    import io.koraframework.common.annotation.DefaultComponent

    interface SmsCellularModule {

        @DefaultComponent
        fun smsCellularProvider(): SmsCellularProvider {
            return SmsCellularProvider { "1" }
        }
    }
    ```

**Обновите Application**, чтобы подключить модуль поставщика. `SmsCellularModule` не помечен `@Module`, поэтому он намеренно подключается через `extends`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule,  // <----- Connected module
            SmsCellularModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

        @Tag(EmailModule.EmailTag.class)
        @Override
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL OVERRIDDEN] ";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        EmailModule,  // <----- Connected module
        SmsCellularModule {  // <----- Connected module

        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

**Соберите и запустите**:

```
DI tutorial step 5 start
+1 [SMS] Bob@Hello!
[EMAIL OVERRIDDEN] USER [USER:Bob]: Hello!
Application shutdown
```

**Ключевое понятие**: `@Nullable` в Java и nullable-типы в Kotlin позволяют компоненту продолжать работать даже тогда, когда необязательная зависимость отсутствует. Отсутствие обязательной
зависимости — ошибка компиляции, а отсутствие необязательной молча разрешается в `null`, поэтому ветку с `null` стоит делать осмысленной.

---

### Подмодуль { #submodule }

**Цель**: показать `@KoraSubmodule` для организации связанных компонентов.

**Что вводит этот шаг**: `@KoraSubmodule` как границу, которая превращает другой Gradle-модуль в видимую для DI единицу компиляции. Внутри этого подмодуля объявления `@Module` и `@Component`
собираются и передаются основному `@KoraApp` через наследование.

**Зачем это нужно**: обычные Gradle-модули не сканируются Kora, если в них нет `@KoraApp` или `@KoraSubmodule`. Именно этот механизм позволяет вынести функциональность отправки сообщений в
собственный модуль и не потерять обнаружение DI.
См. [Внедрение зависимостей в Kora: @KoraSubmodule](dependency-injection-introduction.md#korasubmodule), [примечание об области обзора](dependency-injection-introduction.md#overview)
и [Документация контейнера: фабрика подмодуля](../documentation/container.md#submodule-factory).

**Что мы эмулируем**: более крупную кодовую базу, где отдельная команда или пакет владеет доставкой сообщений, но основное приложение все равно собирает это в один граф.

Теперь создайте и подключите подмодуль: руководство подошло к части про `@KoraSubmodule`.

Обновите `settings.gradle`:

```groovy
include "guide-dependency-injection:guide-dependency-injection-submodule"
```

Обновите `settings.gradle.kts`:

```kotlin
include("guide-dependency-injection:guide-dependency-injection-submodule")
```

Создайте каталог:

```bash
mkdir -p guide-dependency-injection/guide-dependency-injection-submodule
```

**Создайте `guide-dependency-injection/guide-dependency-injection-submodule/build.gradle`**:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    plugins {
        id "java-library"
    }

    dependencies {
        annotationProcessor "io.koraframework:annotation-processors" //(1)!

        api project(":guide-dependency-injection:guide-dependency-injection-common")

        implementation "io.koraframework:common" //(2)!

        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

    1.  Обязательно: `@KoraSubmodule` обрабатывается в этом модуле, а не в модуле приложения. Обработчик пишет здесь интерфейс `MessengerModuleSubmoduleImpl`, а модуль приложения затем наследует
        его через `MessengerModule`.
    2.  `io.koraframework:common` содержит аннотации DI и транзитивно приносит `application-graph` с `All`, `ValueOf` и `Lifecycle`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("java-library")
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}") //(1)!

        api(project(":guide-dependency-injection:guide-dependency-injection-common"))

        implementation("io.koraframework:common") //(2)!

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }

    kotlin {
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }
    ```

    1.  Обязательно: `@KoraSubmodule` обрабатывается в этом модуле, а не в модуле приложения. KSP пишет здесь интерфейс `MessengerModuleSubmoduleImpl`, а модуль приложения затем наследует его
        через `MessengerModule`.
    2.  `io.koraframework:common` содержит аннотации DI и транзитивно приносит `application-graph` с `All`, `ValueOf` и `Lifecycle`.

**Обновите файл сборки `guide-dependency-injection-app`**, чтобы добавить зависимость на новый модуль:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        annotationProcessor "io.koraframework:annotation-processors"

        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation project(":guide-dependency-injection:guide-dependency-injection-lib")
        implementation project(":guide-dependency-injection:guide-dependency-injection-submodule")
        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"

        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-lib"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-submodule"))
        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }
    ```

**Создайте MessengerModule** (`guide-dependency-injection/guide-dependency-injection-submodule/src/main/java/io/koraframework/guide/dependencyinjection/messenger/`
или `guide-dependency-injection/guide-dependency-injection-submodule/src/main/kotlin/io/koraframework/guide/dependencyinjection/messenger/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.messenger;

    import io.koraframework.common.annotation.KoraSubmodule;

    @KoraSubmodule
    public interface MessengerModule {

        final class MessengerTag {
            private MessengerTag() {}
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.messenger

    import io.koraframework.common.annotation.KoraSubmodule

    @KoraSubmodule
    interface MessengerModule {

        class MessengerTag private constructor()
    }
    ```

Тело интерфейса почти пустое намеренно. `@KoraSubmodule` — это маркер: при компиляции этого Gradle-модуля Kora собирает все объявления `@Module` и `@Component` из той же единицы компиляции и
записывает их в сгенерированный интерфейс `MessengerModuleSubmoduleImpl`. Приложение подхватывает все это, унаследовав `MessengerModule`.

**Создайте интерфейс Messenger**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.messenger;

    public interface Messenger {
        void sendMessage(String message);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.messenger

    fun interface Messenger {
        fun sendMessage(message: String)
    }
    ```

**Создайте SlackMessenger**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.messenger.slack;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.dependencyinjection.messenger.Messenger;

    @Tag(SlackMessenger.class) //(1)!
    @Component
    public final class SlackMessenger implements Messenger {

        @Override
        public void sendMessage(String message) {
            System.out.println("Slack: " + message);
        }
    }
    ```

    1.  Компонент может быть собственным тегом. Это удобно, когда единственная задача тега — обозначить одну конкретную реализацию.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.messenger.slack

    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.dependencyinjection.messenger.Messenger

    @Tag(SlackMessenger::class) //(1)!
    @Component
    class SlackMessenger : Messenger {

        override fun sendMessage(message: String) {
            println("Slack: $message")
        }
    }
    ```

    1.  Компонент может быть собственным тегом. Это удобно, когда единственная задача тега — обозначить одну конкретную реализацию.

**Создайте MessengerNotifier**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.messenger;

    import io.koraframework.application.graph.All;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.dependencyinjection.common.Notifier;

    @Tag(MessengerModule.MessengerTag.class)
    @Component
    public final class MessengerNotifier implements Notifier {

        private final All<Messenger> messengers;

        public MessengerNotifier(@Tag(Tag.Any.class) All<Messenger> messengers) {
            this.messengers = messengers;
        }

        @Override
        public void notify(String user, String message) {
            System.out.println("Broadcasting to messengers");
            for (var messenger : messengers) {
                messenger.sendMessage(user + "@" + message);
            }
            System.out.println("Messenger broadcast complete");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.messenger

    import io.koraframework.application.graph.All
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.dependencyinjection.common.Notifier

    @Tag(MessengerModule.MessengerTag::class)
    @Component
    class MessengerNotifier(
        @Tag(Tag.Any::class) private val messengers: All<Messenger>
    ) : Notifier {

        override fun notify(user: String, message: String) {
            println("Broadcasting to messengers")
            for (messenger in messengers) {
                messenger.sendMessage("$user@$message")
            }
            println("Messenger broadcast complete")
        }
    }
    ```

**Обновите Application**, чтобы подключить подмодуль отправки сообщений. `MessengerModule` помечен `@KoraSubmodule`, поэтому здесь наследование ожидаемо:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule,  // <----- Connected module
            SmsCellularModule,  // <----- Connected module
            MessengerModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

        @Tag(EmailModule.EmailTag.class)
        @Override
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL OVERRIDDEN] ";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        EmailModule,  // <----- Connected module
        SmsCellularModule,  // <----- Connected module
        MessengerModule {  // <----- Connected module

        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

!!! warning "Kora submodule was not generated yet"

    Если модуль приложения падает с `Kora submodule was not generated yet: expected type: ...MessengerModuleSubmoduleImpl`, значит в самом Gradle-модуле подмодуля не отработал обработчик Kora.
    Проверьте, что `guide-dependency-injection-submodule` объявляет `annotationProcessor "io.koraframework:annotation-processors"` (Java) или `ksp("io.koraframework:symbol-processors:...")` (Kotlin),
    затем выполните `./gradlew clean classes`, чтобы сгенерированный интерфейс существовал до компиляции модуля приложения.

**Соберите и запустите**:

```
+1 [SMS] Bob@Hello!
[EMAIL OVERRIDDEN] USER [USER:Bob]: Hello!
Broadcasting to messengers
Slack: Bob@Hello!
Messenger broadcast complete
Application shutdown
```

**Ключевое понятие**: `@KoraSubmodule` группирует связанные компоненты и теги, не заставляя помещать их в основной файл интерфейса приложения.

---

### Дженерик фабрики { #generic-factory }

**Цель**: показать обобщенные фабричные методы для гибкого создания компонентов.

**Что вводит этот шаг**: обобщенные фабрики, которые позволяют одному модулю создавать много строго типизированных компонентов. `StorageModule` создает экземпляры `Storage<T>` из функций
преобразования вместо того, чтобы жестко прописывать отдельное конкретное хранилище для каждого типа.

**Зачем это нужно**: обобщенные фабрики уменьшают дублирование и при этом сохраняют граф типобезопасным. Это соответствует
разделам [Внедрение зависимостей в Kora: обобщенная фабрика](dependency-injection-introduction.md#generic-factory)
и [Документация контейнера: обобщенная фабрика](../documentation/container.md#generic-factory).

**Что мы эмулируем**: инфраструктурный код, который может сохранять разные формы полезной нагрузки с помощью одного переиспользуемого шаблона хранилища, а Kora автоматически выбирает нужную
обобщенную конкретизацию.

**Создайте интерфейс Storage** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/io/koraframework/guide/dependencyinjection/storage/`
или `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/io/koraframework/guide/dependencyinjection/storage/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.storage;

    public interface Storage<T> {
        void save(T data);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.storage

    interface Storage<T> {
        fun save(data: T)
    }
    ```

**Создайте TempFileStorage**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.storage;

    import java.io.IOException;
    import java.nio.file.Files;
    import java.nio.file.Path;
    import java.util.function.Function;

    public final class TempFileStorage<T> implements Storage<T> {

        private final Function<T, byte[]> mapper;

        public TempFileStorage(Function<T, byte[]> mapper) {
            this.mapper = mapper;
        }

        @Override
        public void save(T data) {
            try {
                Path tempFile = Files.createTempFile("storage-", ".tmp");
                Files.write(tempFile, mapper.apply(data));
                System.out.println("Saved to: " + tempFile.getFileName());
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.storage

    import java.nio.file.Files
    import java.util.function.Function

    class TempFileStorage<T>(
        private val mapper: Function<T, ByteArray>
    ) : Storage<T> {

        override fun save(data: T) {
            val tempFile = Files.createTempFile("storage-", ".tmp")
            Files.write(tempFile, mapper.apply(data))
            println("Saved to: ${tempFile.fileName}")
        }
    }
    ```

`TempFileStorage` не помечен аннотациями. Его создает фабрика модуля ниже, а `@Component` здесь добавил бы второго, конфликтующего поставщика того же типа.

**Создайте StorageModule**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.storage;

    import java.nio.charset.StandardCharsets;
    import java.util.function.Function;
    import io.koraframework.common.annotation.Module;

    @Module
    public interface StorageModule {

        default Function<Integer, byte[]> intMapper() {
            return i -> new byte[] {i.byteValue()};
        }

        default Function<String, byte[]> stringMapper() {
            return s -> s.getBytes(StandardCharsets.UTF_8);
        }

        default <T> Storage<T> typedStorage(Function<T, byte[]> mapper) { //(1)!
            return new TempFileStorage<>(mapper);
        }
    }
    ```

    1.  Фабричный метод с собственным параметром типа — это *шаблон*. Kora не создает его заранее: она создает по одному узлу на каждый конкретный `Storage<T>`, который реально запросил другой
        компонент, разрешая `Function<T, byte[]>` для того же `T`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.storage

    import java.nio.charset.StandardCharsets
    import java.util.function.Function
    import io.koraframework.common.annotation.Module

    @Module
    interface StorageModule {

        fun intMapper(): Function<Int, ByteArray> {
            return Function { i -> byteArrayOf(i.toByte()) }
        }

        fun stringMapper(): Function<String, ByteArray> {
            return Function { s -> s.toByteArray(StandardCharsets.UTF_8) }
        }

        fun <T> typedStorage(mapper: Function<T, ByteArray>): Storage<T> { //(1)!
            return TempFileStorage(mapper)
        }
    }
    ```

    1.  Фабричный метод с собственным параметром типа — это *шаблон*. Kora не создает его заранее: она создает по одному узлу на каждый конкретный `Storage<T>`, который реально запросил другой
        компонент, разрешая `Function<T, ByteArray>` для того же `T`.

Kotlin-вариант намеренно использует `java.util.function.Function`, а не функциональный тип Kotlin вроде `(T) -> ByteArray`. Функциональные типы Kotlin компилируются в `kotlin.jvm.functions.FunctionN`,
из-за чего в графе любая функция с одним аргументом имеет один и тот же стертый тип, и `(Int) -> ByteArray` и `(String) -> ByteArray` становятся неразличимыми кандидатами. Явный `Function<T, R>`
оставляет оба аргумента типа видимыми для разрешения зависимостей.

**Примечание о приложении**: здесь не нужно менять `Application`. `StorageModule` компилируется вместе с `@KoraApp` и помечен `@Module`, поэтому Kora автоматически обнаруживает его как модуль
приложения.

**Обновите NotifyRunner**, чтобы использовать `Storage<String>`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class NotifyRunner implements Lifecycle {

        private final All<Notifier> allNotifiers;
        private final Storage<String> stringStorage;

        public NotifyRunner(@Tag(Tag.Any.class) All<Notifier> allNotifiers, Storage<String> stringStorage) {
            this.allNotifiers = allNotifiers;
            this.stringStorage = stringStorage;
        }

        @Override
        public void init() {
            System.out.println("DI tutorial step 7 start");
            for (var notifier : allNotifiers) {
                notifier.notify("Charlie", "Greetings!");
            }
            stringStorage.save("User data stored");
        }

        @Override
        public void release() {
            System.out.println("Application shutdown");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class NotifyRunner(
        @Tag(Tag.Any::class) private val allNotifiers: All<Notifier>,
        private val stringStorage: Storage<String>
    ) : Lifecycle {

        override fun init() {
            println("DI tutorial step 7 start")
            for (notifier in allNotifiers) {
                notifier.notify("Charlie", "Greetings!")
            }
            stringStorage.save("User data stored")
        }

        override fun release() {
            println("Application shutdown")
        }
    }
    ```

Запрашивается только `Storage<String>`, поэтому в граф попадают лишь `stringMapper()` и один узел `Storage<String>`. `intMapper()` остается невостребованным и, раз его никто не запрашивает, никогда не создается.

**Соберите и запустите**:

```
DI tutorial step 7 start
+1 [SMS] Charlie@Greetings!
[EMAIL OVERRIDDEN] USER [USER:Charlie]: Greetings!
Broadcasting to messengers
Slack: Charlie@Greetings!
Messenger broadcast complete
Saved to: storage-123456.tmp
Application shutdown
```

**Ключевое понятие**: обобщенные фабричные методы вроде `<T> Storage<T>` позволяют Kora строить строго типизированные компоненты из переиспользуемых фабрик.

#### Фабричный модуль { #factory-module-object }

Есть второй способ группировать фабрики, и его стоит знать, потому что он решает другую задачу. Интерфейс `@Module` не хранит состояние: Kora создает его анонимную реализацию и вызывает методы по
умолчанию. **Фабричный модуль** — это обычный объект, который сам является компонентом графа и чьи публичные методы тоже считаются фабриками. Благодаря этому один экземпляр модуля может нести
состояние для создания компонентов — клиент, префикс, объект конфигурации — и передавать его каждому создаваемому компоненту.

Фрагмент ниже показывает форму такого модуля. Он не входит в приложение из руководства, потому что предоставил бы второй `Storage<String>` и конфликтовал бы с обобщенной фабрикой выше:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ArchiveFactory { //(1)!

        private final Function<String, byte[]> mapper;

        public ArchiveFactory(Function<String, byte[]> mapper) {
            this.mapper = mapper;
        }

        public Archive archive() { //(2)!
            return data -> mapper.apply(data).length;
        }
    }

    @Module
    public interface ArchiveModule {

        @FactoryModule //(3)!
        default ArchiveFactory archiveFactory(Function<String, byte[]> mapper) {
            return new ArchiveFactory(mapper);
        }
    }
    ```

    1.  Обычный класс, а не интерфейс, и без аннотаций.
    2.  Публичные методы возвращаемого объекта становятся фабриками компонентов — ровно как методы по умолчанию у интерфейса `@Module`.
    3.  `@FactoryModule` из `io.koraframework.common.annotation`. Она регистрирует сам `ArchiveFactory` как узел графа и дополнительно обрабатывает его методы как поставщиков.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ArchiveFactory( //(1)!
        private val mapper: Function<String, ByteArray>
    ) {

        fun archive(): Archive { //(2)!
            return Archive { data -> mapper.apply(data).size }
        }
    }

    @Module
    interface ArchiveModule {

        @FactoryModule //(3)!
        fun archiveFactory(mapper: Function<String, ByteArray>): ArchiveFactory {
            return ArchiveFactory(mapper)
        }
    }
    ```

    1.  Обычный класс, а не интерфейс, и без аннотаций.
    2.  Публичные методы возвращаемого объекта становятся фабриками компонентов — ровно как методы интерфейса `@Module`.
    3.  `@FactoryModule` из `io.koraframework.common.annotation`. Она регистрирует сам `ArchiveFactory` как узел графа и дополнительно обрабатывает его методы как поставщиков.

Два фабричных модуля одного типа могут сосуществовать, если у них разные теги, а внутри такого модуля `@Tag(Tag.Factory.class)` означает «тег объемлющего фабричного модуля». Так один класс можно
создать дважды, и каждый экземпляр даст собственный набор компонентов со своим тегом. Использование `@Tag.Factory` вне фабричного модуля — ошибка компиляции:
`@Tag.Factory can only be used inside factory modules.`

Полный контракт описан в разделах [Документация контейнера: фабричный модуль](../documentation/container.md#factory-module)
и [Внедрение зависимостей в Kora: фабричный модуль](dependency-injection-introduction.md#factory-module).

---

### Управление обновлением { #update-management }

**Цель**: показать `ValueOf<T>` для предотвращения нежелательных каскадных обновлений при изменении зависимостей.

**Что вводит этот шаг**: `ValueOf<T>`, `Wrapped<T>` и `LifecycleWrapper` для зависимостей, которые учитывают жизненный цикл и доступны через косвенную ссылку. `ActivityService` остается стабильным,
а `ActivityRecorder` остается доступным отложенно и при этом управляется жизненным циклом.

**Зачем это нужно**: некоторые инфраструктурные зависимости дороги в создании или могут обновляться, и мы не хотим пересоздавать каждого потребителя только потому, что такая зависимость изменилась.
Это соответствует разделам [Внедрение зависимостей в Kora: ValueOf](dependency-injection-introduction.md#valueof) и [Документация контейнера: жизненный цикл компонента](../documentation/container.md#component-lifecycle).

**Что мы эмулируем**: службу, которая записывает активность через управляемый соединитель, способный запускаться, останавливаться или обновляться независимо от бизнес-службы, которая его использует.

**Создайте интерфейс ActivityRecorder** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/io/koraframework/guide/dependencyinjection/activity/`
или `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/io/koraframework/guide/dependencyinjection/activity/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.activity;

    public interface ActivityRecorder {

        void connect();

        void disconnect();

        boolean isConnected();

        void recordUser(String user);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.activity

    interface ActivityRecorder {

        fun connect()

        fun disconnect()

        fun isConnected(): Boolean

        fun recordUser(user: String)
    }
    ```

**Создайте ActivityService**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.activity;

    import io.koraframework.application.graph.ValueOf;
    import io.koraframework.common.annotation.Component;

    @Component
    public final class ActivityService {

        private final ValueOf<ActivityRecorder> activityRecorder;

        public ActivityService(ValueOf<ActivityRecorder> activityRecorder) {
            this.activityRecorder = activityRecorder;
            System.out.println("ActivityService created (ActivityRecorder not yet accessed)");
        }

        public void recordActivityByUserName(String user) {
            System.out.println("Recording activity for: " + user);
            ActivityRecorder recorder = activityRecorder.get(); //(1)!
            recorder.recordUser(user);
            System.out.println("Activity recorded successfully");
        }
    }
    ```

    1.  `ValueOf.get()` всегда возвращает текущий экземпляр из графа. Вызывайте его в момент использования и не кэшируйте результат в поле, иначе после обновления останется устаревшая ссылка.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.activity

    import io.koraframework.application.graph.ValueOf
    import io.koraframework.common.annotation.Component

    @Component
    class ActivityService(
        private val activityRecorder: ValueOf<ActivityRecorder>
    ) {

        init {
            println("ActivityService created (ActivityRecorder not yet accessed)")
        }

        fun recordActivityByUserName(user: String) {
            println("Recording activity for: $user")
            val recorder = activityRecorder.get() //(1)!
            recorder.recordUser(user)
            println("Activity recorded successfully")
        }
    }
    ```

    1.  `ValueOf.get()` всегда возвращает текущий экземпляр из графа. Вызывайте его в момент использования и не кэшируйте результат в свойстве, иначе после обновления останется устаревшая ссылка.

**Создайте ActivityModule**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.activity;

    import io.koraframework.application.graph.LifecycleWrapper;
    import io.koraframework.application.graph.Wrapped;
    import io.koraframework.common.annotation.Module;

    @Module
    public interface ActivityModule {

        default Wrapped<ActivityRecorder> activityRecorder() { //(1)!
            var recorder = new ActivityRecorder() {
                private boolean connected;

                @Override
                public void connect() {
                    if (!connected) {
                        System.out.println("Connecting to activity recorder");
                        connected = true;
                        System.out.println("Activity recorder connected");
                    }
                }

                @Override
                public void disconnect() {
                    if (connected) {
                        System.out.println("Disconnecting from activity recorder");
                        connected = false;
                    }
                }

                @Override
                public boolean isConnected() {
                    return connected;
                }

                @Override
                public void recordUser(String user) {
                    if (!connected) {
                        connect();
                    }
                    System.out.println("Recording user activity: " + user);
                }
            };

            return new LifecycleWrapper<>(recorder, r -> {}, ActivityRecorder::disconnect); //(2)!
        }
    }
    ```

    1.  Возврат `Wrapped<T>` регистрирует узел как `Wrapped<ActivityRecorder>`, но потребители запрашивают обычный `ActivityRecorder` — Kora разворачивает его автоматически.
    2.  `LifecycleWrapper` принимает значение и действия инициализации и освобождения. Оба — `ThrowingConsumer<T>`, поэтому они могут объявлять проверяемые исключения.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.activity

    import io.koraframework.application.graph.LifecycleWrapper
    import io.koraframework.application.graph.Wrapped
    import io.koraframework.common.annotation.Module

    @Module
    interface ActivityModule {

        fun activityRecorder(): Wrapped<ActivityRecorder> { //(1)!
            val recorder = object : ActivityRecorder {
                private var connected = false

                override fun connect() {
                    if (!connected) {
                        println("Connecting to activity recorder")
                        connected = true
                        println("Activity recorder connected")
                    }
                }

                override fun disconnect() {
                    if (connected) {
                        println("Disconnecting from activity recorder")
                        connected = false
                    }
                }

                override fun isConnected(): Boolean = connected

                override fun recordUser(user: String) {
                    if (!connected) {
                        connect()
                    }
                    println("Recording user activity: $user")
                }
            }

            return LifecycleWrapper(recorder, {}, ActivityRecorder::disconnect) //(2)!
        }
    }
    ```

    1.  Возврат `Wrapped<T>` регистрирует узел как `Wrapped<ActivityRecorder>`, но потребители запрашивают обычный `ActivityRecorder` — Kora разворачивает его автоматически.
    2.  `LifecycleWrapper` принимает значение и действия инициализации и освобождения. Оба — `ThrowingConsumer<T>`, поэтому они могут бросать исключения.

**Примечание о приложении**: менять `Application` здесь тоже не нужно. `ActivityModule` также обнаруживается как модуль приложения из единицы компиляции приложения.

**Обновите NotifyRunner**, чтобы показать финальный сценарий:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class NotifyRunner implements Lifecycle {

        private final All<Notifier> allNotifiers;
        private final Storage<String> stringStorage;
        private final ActivityService activityService;

        public NotifyRunner(@Tag(Tag.Any.class) All<Notifier> allNotifiers,
                            Storage<String> stringStorage,
                            ActivityService activityService) {
            this.allNotifiers = allNotifiers;
            this.stringStorage = stringStorage;
            this.activityService = activityService;
        }

        @Override
        public void init() {
            System.out.println("DI tutorial complete scenario start");
            for (var notifier : allNotifiers) {
                notifier.notify("Diana", "Welcome to Kora DI!");
            }
            stringStorage.save("Scenario payload for Diana");
            activityService.recordActivityByUserName("Diana");
            System.out.println("DI tutorial complete scenario done");
        }

        @Override
        public void release() {
            System.out.println("Application shutdown");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class NotifyRunner(
        @Tag(Tag.Any::class) private val allNotifiers: All<Notifier>,
        private val stringStorage: Storage<String>,
        private val activityService: ActivityService
    ) : Lifecycle {

        override fun init() {
            println("DI tutorial complete scenario start")
            for (notifier in allNotifiers) {
                notifier.notify("Diana", "Welcome to Kora DI!")
            }
            stringStorage.save("Scenario payload for Diana")
            activityService.recordActivityByUserName("Diana")
            println("DI tutorial complete scenario done")
        }

        override fun release() {
            println("Application shutdown")
        }
    }
    ```

**Соберите и запустите**:

```
ActivityService created (ActivityRecorder not yet accessed)
DI tutorial complete scenario start
+1 [SMS] Diana@Welcome to Kora DI!
[EMAIL OVERRIDDEN] USER [USER:Diana]: Welcome to Kora DI!
Broadcasting to messengers
Slack: Diana@Welcome to Kora DI!
Messenger broadcast complete
Saved to: storage-789012.tmp
Recording activity for: Diana
Connecting to activity recorder
Activity recorder connected
Recording user activity: Diana
Activity recorded successfully
DI tutorial complete scenario done
Application shutdown
Disconnecting from activity recorder
```

Обратите внимание на две последние строки: `NotifyRunner.release()` выполняется раньше, чем отключается регистратор, потому что `release()` обходит граф в обратном порядке зависимостей.

**Ключевое понятие**: `ValueOf<T>` предотвращает каскадные обновления компонентов. Экземпляр `ActivityService` остается стабильным, но все равно может отложенно получить текущий `ActivityRecorder`,
когда это нужно.

---

## Итоги руководства { #guide-summary }

Вы создали полноценное приложение Kora, которое демонстрирует все основные понятия внедрения зависимостей:

1. **Структура проекта** — многомодульная организация
2. **Внешние модули** — библиотечные компоненты с `@DefaultComponent`
3. **Переопределение компонента** — настройка библиотечных значений по умолчанию
4. **Зависимости с тегами** — несколько реализаций с `@Tag` и `All<T>`
5. **Допускающие `null` зависимости** — JSpecify `@Nullable` / nullable-типы для аккуратной деградации
6. **Подмодули** — `@KoraSubmodule` для организации компонентов между Gradle-модулями
7. **Обобщенные фабрики** — параметризованное `<T>` создание компонентов и `@FactoryModule` для модулей с состоянием
8. **Предотвращение каскадных обновлений** — `ValueOf<T>` для управления поведением обновления компонентов

Каждый шаг опирается на предыдущий и показывает, как DI Kora во время компиляции помогает создавать чистые, модульные и производительные приложения.

## Лучшие практики { #best-practices }

- Держите компоненты небольшими и сфокусированными на одной ответственности.
- Предпочитайте внедрение через конструктор и явные границы модулей.
- Используйте теги только тогда, когда несколько реализаций действительно должны сосуществовать.
- Держите необязательные зависимости явными с помощью nullable-типов или JSpecify `@Nullable`.
- Используйте `ValueOf<T>`, когда нужно управляемое поведение обновления компонентов, и вызывайте `get()` в момент использования, а не кэшируйте значение.
- Подключайте обработчик Kora в каждом Gradle-модуле, где объявлены `@KoraApp`, `@KoraSubmodule`, `@ConfigMapper` или `@ConfigSource` — обработчик видит только тот модуль, в котором запущен.
- Прячьте переиспользуемые значения по умолчанию за `@DefaultComponent`, чтобы приложения могли переопределять их без форка библиотеки.

## Итоги { #summary }

Поздравляем! Вы завершили подробное руководство по внедрению зависимостей Kora. Вы изучили не только *как* использовать внедрение зависимостей, но и *почему* это настолько мощный шаблон для
создания сопровождаемого программного обеспечения.

В руководстве разобраны основные элементы графа Kora: `@KoraApp`, `@Component`, `@Module`, внешние модули, `@DefaultComponent`, теги, `All<T>`, nullable-зависимости, подмодули, обобщенные фабрики,
`@FactoryModule` и `ValueOf<T>`. Вместе они показывают, как собирать приложение из небольших явных частей и при этом сохранять типобезопасное разрешение зависимостей во время компиляции.

Такие же шаблоны используются в промышленных сервисах, чтобы строить:

- высокопроизводительные микросервисы
- масштабируемые веб-приложения
- сложные корпоративные системы
- облачно-ориентированные архитектуры

Они делают код проще для тестирования, сопровождения, расширения и чтения, потому что зависимости объявляются в конструкторах и фабричных методах, а не прячутся внутри реализации.

Следующие учебные рубежи:

1. Изучите примеры Kora: разберите репозиторий `kora-examples`, чтобы увидеть шаблоны из реальных проектов
2. Создайте первое приложение: сделайте простой REST API, используя шаблоны из руководства
3. Добавьте наблюдаемость: изучите возможности телеметрии и наблюдения в Kora
4. Подключите базу данных: соедините приложение с настоящей базой данных
5. Разверните в промышленной среде: изучите контейнеризацию и развертывание в облаке

## Ключевые понятия { #key-concepts }

- как `@KoraApp`, `@Component` и `@Module` формируют граф приложения
- как теги различают несколько реализаций одного договора
- как запросы коллекций и допускающих `null` зависимостей влияют на разрешение графа
- как подмодули и внешние модули помогают организовывать большие приложения
- как `ValueOf<T>` дает управляемый доступ к обновляемым компонентам

## Устранение неполадок { #troubleshooting }

Kora сообщает о проблемах связывания во время компиляции, и каждое сообщение называет запрос, место, где он требуется, дерево зависимостей, которое к нему привело, и блок `Fix:`. Читайте этот блок
первым: он генерируется по фактическому состоянию графа, а не по статическому шаблону. См. также [Документация контейнера: ошибки сборки графа](../documentation/container.md#graph-build-errors).

Распространенные проблемы и решения:

Циклические зависимости:

Проблема: два или больше компонентов зависят друг от друга напрямую или косвенно.

Признаки:

- ошибка компиляции, начинающаяся с `Circular dependency found:`, за которой идет `Dependency cycle:` со списком всех объявлений в цикле и завершающим `[CYCLE]`
- предлагаемое исправление упоминает `ValueOf<T>` или `PromiseOf<T>`

Решения:

1. Переработайте код через разделение интерфейсов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Instead of circular dependency
    @Component
    class ServiceA { ServiceA(ServiceB b) {} }

    @Component
    class ServiceB { ServiceB(ServiceA a) {} }

    // Use interfaces
    interface ServiceAInterface { void methodA(); }
    interface ServiceBInterface { void methodB(); }

    @Component
    class AImpl implements ServiceAInterface { AImpl(ServiceBInterface b) {} }

    @Component
    class BImpl implements ServiceBInterface { BImpl(ServiceAInterface a) {} }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Instead of circular dependency
    @Component
    class ServiceA(val b: ServiceB)

    @Component
    class ServiceB(val a: ServiceA)

    // Use interfaces
    interface ServiceAInterface { fun methodA() }
    interface ServiceBInterface { fun methodB() }

    @Component
    class AImpl(val b: ServiceBInterface) : ServiceAInterface {
        override fun methodA() {}
    }

    @Component
    class BImpl(val a: ServiceAInterface) : ServiceBInterface {
        override fun methodB() {}
    }
    ```

2. Используйте ValueOf для косвенных зависимостей:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ServiceModule {
        default ServiceA serviceA(ValueOf<ServiceB> serviceB) {
            // ServiceA doesn't directly depend on ServiceB lifecycle
            return new ServiceA(serviceB);
        }

        default ServiceB serviceB() {
            return new ServiceB();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ServiceModule {
        fun serviceA(serviceB: ValueOf<ServiceB>): ServiceA {
            // ServiceA doesn't directly depend on ServiceB lifecycle
            return ServiceA(serviceB)
        }

        fun serviceB(): ServiceB {
            return ServiceB()
        }
    }
    ```

Отсутствующие зависимости:

Проблема: компоненту нужна зависимость, которую невозможно найти.

Признаки:

- ошибка компиляции, начинающаяся с `No component found for dependency:`, за которой идет запрошенный тип и либо `(no tags)`, либо `with @Tag(...)`
- секция `Note:` со списком компонентов того же типа, но с другим тегом, когда тег просто забыли
- секция `Fix:` с предложением добавить `@Component`, метод модуля или подключить модуль в `@KoraApp`

Решения:

1. Добавьте отсутствующий компонент:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Add the missing component
    @Component
    public final class MissingDependency {
        // Implementation
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Add the missing component
    @Component
    class MissingDependency {
        // Implementation
    }
    ```

2. Создайте фабричный метод:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
        default MissingDependency missingDependency() {
            return new MissingDependency();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {
        fun missingDependency(): MissingDependency {
            return MissingDependency()
        }
    }
    ```

Проблемы с конфигурацией:

Проблема: компоненты не могут получить доступ к значениям конфигурации.

Признаки:

- падение при старте с `ConfigValueException: Config expected value, but got null at path: '...' for origin '...'`
- ошибка сборки графа для `Config` или `ConfigValueMapper<T>`, когда не подключен ни один модуль конфигурации

Решения:

1. Добавьте модуль конфигурации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Include configuration module
    @KoraApp
    public interface Application extends HoconConfigModule {
        // Now Config and ConfigValueMapper<T> are available
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Include configuration module
    @KoraApp
    interface Application : HoconConfigModule {
        // Now Config and ConfigValueMapper<T> are available
    }
    ```

2. Отобразите секцию конфигурации в типизированный класс:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Application-owned configuration bound to one path
    @ConfigSource("db")
    public interface DatabaseConfig {

        String url();

        @Nullable
        String username();

        default int poolSize() {
            return 10;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Application-owned configuration bound to one path
    @ConfigSource("db")
    interface DatabaseConfig {

        fun url(): String

        fun username(): String?

        fun poolSize(): Int {
            return 10
        }
    }
    ```

`@ConfigSource` генерирует маппер и регистрирует полученный `DatabaseConfig` как компонент графа, поэтому любой компонент может просто объявить его параметром конструктора. Методы без значения по
умолчанию и без `@Nullable` обязательны: отсутствующий ключ приводит к падению при старте с показанным выше `ConfigValueException`. Используйте `@ConfigMapper`, когда библиотечный тип должен
оставаться независимым от пути, как `EmailConfig` в этом руководстве.

Проблемы с разрешением тегов:

Проблема: зависимости с тегами не удается разрешить.

Признаки:

- ошибка компиляции, начинающаяся с `Multiple components match dependency:`, за которой идет список объявлений-кандидатов
- либо `No component found for dependency:` с секцией `Note:`, где перечислен тот же тип под другим тегом

Решения:

1. Используйте правильную аннотацию тега:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Correct tag usage
    @Component
    public final class MyService {
        public MyService(@Tag(MyTag.class) Dependency dep) {
            // Correct
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Correct tag usage
    @Component
    class MyService(
        @Tag(MyTag::class) val dep: Dependency
    ) {
        // Correct
    }
    ```

2. Проверьте определение класса тега:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Tag class must be visible everywhere it is referenced
    public final class MyTag {} // Correct

    // Package-private tag cannot be referenced from another package
    final class MyTag {} // Wrong
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Tag class must be visible everywhere it is referenced
    class MyTag // Correct (public by default)

    // Private tag cannot be referenced from another file
    private class MyTag // Wrong
    ```

3. Либо сделайте одного кандидата запасным вариантом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface DefaultsModule {

        @DefaultComponent //(1)!
        default Dependency dependency() {
            return new Dependency();
        }
    }
    ```

    1.  Сгенерированное сообщение об ошибке предлагает именно это: пометьте запасного кандидата `@DefaultComponent`, и любой кандидат без этой аннотации победит.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface DefaultsModule {

        @DefaultComponent //(1)!
        fun dependency(): Dependency {
            return Dependency()
        }
    }
    ```

    1.  Сгенерированное сообщение об ошибке предлагает именно это: пометьте запасного кандидата `@DefaultComponent`, и любой кандидат без этой аннотации победит.

Проблемы с подключением модулей:

Проблема: компоненты из модулей недоступны.

Признаки:

- `No component found for dependency:` для типа, который точно объявлен в каком-то модуле
- модуль лежит в другом Gradle-модуле и при этом не является `@KoraSubmodule` и не наследуется через `extends`

Решения:

1. Подключите модуль в приложении:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Include the module
    @KoraApp
    public interface Application extends MyModule {  // <----- Connected module
        // Components from MyModule now available
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Include the module
    @KoraApp
    interface Application : MyModule {  // <----- Connected module
        // Components from MyModule now available
    }
    ```

2. Проверьте вид модуля и его видимость:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // @Module works on interfaces only, and its factory methods must be public
    @Module
    public interface MyModule {
        default MyComponent myComponent() { // public by default
            return new MyComponent();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // @Module works on interfaces only, and its factory methods must be public
    @Module
    interface MyModule {
        fun myComponent(): MyComponent { // public by default
            return MyComponent()
        }
    }
    ```

`@Module` действует только в той единице компиляции, в которой он компилируется. Интерфейс `@Module` из другого Gradle-модуля невидим, пока вы не унаследуете его через `extends` или не поместите в тот
Gradle-модуль маркерный интерфейс `@KoraSubmodule` и не унаследуете уже его.

Проблемы с внедрением коллекций:

Проблема: `All<T>` не внедряет ожидаемые компоненты.

Признаки:

- в `All<T>` меньше компонентов, чем ожидалось
- реализации с тегами отсутствуют в коллекции

Решения:

1. Убедитесь, что все реализации есть в графе:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // All implementations must be @Component or produced by a module factory
    @Component
    public final class Impl1 implements MyInterface {}

    @Component
    public final class Impl2 implements MyInterface {}

    // Now All<MyInterface> will contain both
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // All implementations must be @Component or produced by a module factory
    @Component
    class Impl1 : MyInterface

    @Component
    class Impl2 : MyInterface

    // Now All<MyInterface> will contain both
    ```

2. Запрашивайте именно те теги, которые вам нужны:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {

        public MyService(All<MyInterface> untagged, //(1)!
                         @Tag(Tag.Any.class) All<MyInterface> everything, //(2)!
                         @Tag(MyTag.class) All<MyInterface> onlyMyTag) { //(3)!
            // ...
        }
    }
    ```

    1.  Запрос без тега попадает только в компоненты без тегов. Реализации с тегами молча отсутствуют.
    2.  `Tag.Any` совпадает с любым компонентом этого типа независимо от тега.
    3.  Конкретный тег совпадает только с компонентами, несущими ровно этот тег.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(
        val untagged: All<MyInterface>, //(1)!
        @Tag(Tag.Any::class) val everything: All<MyInterface>, //(2)!
        @Tag(MyTag::class) val onlyMyTag: All<MyInterface> //(3)!
    ) {
        // ...
    }
    ```

    1.  Запрос без тега попадает только в компоненты без тегов. Реализации с тегами молча отсутствуют.
    2.  `Tag.Any` совпадает с любым компонентом этого типа независимо от тега.
    3.  Конкретный тег совпадает только с компонентами, несущими ровно этот тег.

Это самая частая неожиданность с `All<T>`: пустая или неполная коллекция почти всегда означает, что запрос и поставщики расходятся в тегах, а не что компонентов нет в
графе. См. [Документация контейнера: Tag any](../documentation/container.md#tag-any).

Проблемы с необязательными зависимостями:

Проблема: необязательные зависимости ведут себя неожиданно.

Признаки:

- зависимость равна `null`, хотя ожидалось значение
- `NullPointerException` при первом использовании

Решения:

1. Правильно обрабатывайте nullable-значения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import org.jspecify.annotations.Nullable;

    @Component
    public final class MyService {
        private final @Nullable Dependency optionalDep;

        public MyService(@Nullable Dependency optionalDep) {
            this.optionalDep = optionalDep;
        }

        public void doSomething() {
            // Safe nullable usage
            if (optionalDep != null) { optionalDep.doWork(); }

            // Dangerous - can cause NPE
            // optionalDep.doWork(); // Don't do this without a null check
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(
        private val optionalDep: Dependency?
    ) {

        fun doSomething() {
            // Safe nullable usage
            optionalDep?.doWork()

            // Dangerous - can cause NPE
            // optionalDep!!.doWork() // Don't do this without a null check
        }
    }
    ```

2. Убедитесь, что nullable-компонент существует:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // If you want the nullable dependency to be available, include its provider module
    @KoraApp
    public interface Application extends NullableModule {  // <----- Connected module
        // Include the module that provides the optional dependency
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // If you want the nullable dependency to be available, include its provider module
    @KoraApp
    interface Application : NullableModule {  // <----- Connected module
        // Include the module that provides the optional dependency
    }
    ```

В Java JSpecify `@Nullable` — это аннотация *на использование типа*, поэтому ее позиция важна для вложенных и обобщенных типов: пишите `List<@Nullable String>`, `String @Nullable []` и
`Outer.@Nullable Inner`. В Kotlin аннотации нет вообще — объявлением служит `?` у типа.

Проблемы с жизненным циклом:

Проблема: компоненты с методами жизненного цикла не запускаются или не останавливаются.

Признаки:

- `init()` или `release()` никогда не вызываются
- ресурсы не освобождаются при остановке

Решения:

1. Реализуйте интерфейс Lifecycle:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.Lifecycle; //(1)!

    @Component
    public final class MyService implements Lifecycle {

        @Override
        public void init() throws Exception {
            // Initialize resources here
        }

        @Override
        public void release() throws Exception { //(2)!
            // Clean up resources here
        }
    }
    ```

    1.  `Lifecycle` находится в `io.koraframework.application.graph`, а не в пакете аннотаций.
    2.  Метод остановки называется `release()`. Метода `destroy()` в контракте нет.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.Lifecycle //(1)!

    @Component
    class MyService : Lifecycle {

        override fun init() {
            // Initialize resources here
        }

        override fun release() { //(2)!
            // Clean up resources here
        }
    }
    ```

    1.  `Lifecycle` находится в `io.koraframework.application.graph`, а не в пакете аннотаций.
    2.  Метод остановки называется `release()`. Метода `destroy()` в контракте нет.

2. Проверьте, что компонент действительно есть в графе:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // A component nothing depends on is pruned unless it is a root
    @Root
    @Component
    public final class MyService implements Lifecycle {
        // init()/release() now really run
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // A component nothing depends on is pruned unless it is a root
    @Root
    @Component
    class MyService : Lifecycle {
        // init()/release() now really run
    }
    ```

3. Оберните сторонний объект, который нельзя изменить:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ClientModule {

        default Wrapped<ExternalClient> externalClient() {
            var client = new ExternalClient();
            return new LifecycleWrapper<>(client, ExternalClient::start, ExternalClient::stop);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ClientModule {

        fun externalClient(): Wrapped<ExternalClient> {
            val client = ExternalClient()
            return LifecycleWrapper(client, ExternalClient::start, ExternalClient::stop)
        }
    }
    ```

Проблемы с обобщенными типами:

Проблема: обобщенные компоненты (`<T>`) не разрешаются корректно.

Признаки:

- `No component found for dependency:` для конкретной параметризации вроде `Storage<String>`
- `Component provider returns a raw type:`, когда фабрика возвращает сырой обобщенный тип

Решения:

1. Используйте конкретные аргументы типа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Specify generic type explicitly
    @Component
    public final class StringStorage implements Storage<String> {}

    @Component
    public final class MyService {
        public MyService(Storage<String> storage) { // Specify type
            // Correct
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Specify generic type explicitly
    @Component
    class StringStorage : Storage<String>

    @Component
    class MyService(
        val storage: Storage<String> // Specify type
    ) {
        // Correct
    }
    ```

2. Сделайте каждый параметр шаблона разрешимым:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface StorageModule {

        // Every type parameter of the method must appear in a parameter or in the return type
        default <T> Storage<T> storage(Function<T, byte[]> mapper) {
            return new TempFileStorage<>(mapper);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface StorageModule {

        // Every type parameter of the method must appear in a parameter or in the return type
        fun <T> storage(mapper: Function<T, ByteArray>): Storage<T> {
            return TempFileStorage(mapper)
        }
    }
    ```

Сырые типы отвергаются сразу с сообщением `Raw component types are forbidden because they make dependency resolution ambiguous.`, поэтому всегда указывайте аргументы типа.

Проблемы сборки и компиляции:

Проблема: обработчик Kora не запускается или сгенерированный класс графа отсутствует.

Признаки:

- `cannot find symbol: class ApplicationGraph`
- `Kora submodule was not generated yet: expected type: ...SubmoduleImpl`
- все компилируется, но ни один компонент не создается

Решения:

1. Проверьте подключение обработчика:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        annotationProcessor "io.koraframework:annotation-processors" //(1)!

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"
    }
    ```

    1.  Обработчик указывается в `annotationProcessor`, никогда в `implementation`. Он должен быть объявлен в каждом Gradle-модуле, где есть `@KoraApp`, `@KoraSubmodule`, `@ConfigMapper` или
        `@ConfigSource`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp") //(1)!
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1"))

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")
    }
    ```

    1.  Без плагина KSP конфигурации `ksp` не существует и ничего не генерируется.
    2.  Обработчик указывается в `ksp` с явной версией, потому что `ksp` не покрывается BOM.

2. Соберите начисто:

```bash
./gradlew clean classes
```

3. Проверьте версию Java:

```bash
java -version
```

Модули Kora собраны под Java 25, поэтому и toolchain Gradle, и JDK, на котором запускается сам Gradle, должны быть версии 25 или новее.

Проблемы с тестированием:

Проблема: компоненты сложно тестировать или тестовый граф не стартует.

Признаки:

- сложно внедрять тестовые подмены
- поля `@TestComponent` остаются `null`

Решения:

1. Используйте внедрение через конструктор для обычных модульных тестов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Testable component: no framework needed to construct it
    @Component
    public final class UserService {
        private final UserRepository repository;

        public UserService(UserRepository repository) {
            this.repository = repository;
        }
    }

    @Test
    void testUserService() {
        UserRepository stubRepo = id -> null;
        UserService service = new UserService(stubRepo);
        // Test...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Testable component: no framework needed to construct it
    @Component
    class UserService(
        private val repository: UserRepository
    )

    @Test
    fun testUserService() {
        val stubRepo = UserRepository { null }
        val service = UserService(stubRepo)
        // Test...
    }
    ```

2. Поднимайте настоящий граф через `@KoraAppTest`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection;

    import static org.junit.jupiter.api.Assertions.assertNotNull;

    import org.junit.jupiter.api.Test;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class) //(1)!
    class DependencyInjectionGuideSmokeTest {

        @TestComponent //(2)!
        private NotifyRunner notifyRunner;

        @Test
        void graph_ShouldStart() {
            assertNotNull(notifyRunner);
        }
    }
    ```

    1.  Собирает настоящий граф `Application` для теста, поэтому любая ошибка связывания валит тест, а не старт в промышленной среде.
    2.  Внедряет компонент из этого графа в экземпляр теста.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection

    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Test
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent

    @KoraAppTest(Application::class) //(1)!
    class DependencyInjectionGuideSmokeTest {

        @TestComponent //(2)!
        private lateinit var notifyRunner: NotifyRunner

        @Test
        fun graphShouldStart() {
            assertNotNull(notifyRunner)
        }
    }
    ```

    1.  Собирает настоящий граф `Application` для теста, поэтому любая ошибка связывания валит тест, а не старт в промышленной среде.
    2.  Внедряет компонент из этого графа в экземпляр теста.

Обоим вариантам нужен `io.koraframework:test-junit5` в `testImplementation`. О подмене компонентов графа моками, переопределении конфигурации и интеграционных тестах на Testcontainers читайте в
разделе [Тестирование с JUnit 5](testing-junit.md#test-component).

Распространенные ошибки новичков:

1. Забыли аннотацию @Component:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Missing @Component
    public final class MyService {
        // This won't be discovered by DI
    }

    // Correct
    @Component
    public final class MyService {
        // Now discoverable
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Missing @Component
    class MyService {
        // This won't be discovered by DI
    }

    // Correct
    @Component
    class MyService {
        // Now discoverable
    }
    ```

2. Неоднозначные конструкторы:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {
        private MyService() {} // Wrong: no public constructor at all
    }

    @Component
    public final class MyService {
        public MyService() {}
        public MyService(Dependency dep) {} // Wrong: two public constructors
    }

    // Correct: exactly one public constructor
    @Component
    public final class MyService {
        public MyService(Dependency dep) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService private constructor() // Wrong: no public constructor at all

    @Component
    class MyService(dep: Dependency) {
        constructor() : this(Dependency()) // Wrong: two public constructors
    }

    // Correct: exactly one public constructor
    @Component
    class MyService(dep: Dependency)
    ```

Оба случая Kora сообщает как `@Component class must have exactly one public constructor.` и предлагает оставить один публичный конструктор или перенести сложное создание в метод модуля.

3. Не подключили модули:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
        // Components from modules not included
    }

    @KoraApp
    public interface Application extends MyModule {  // <----- Connected module
        // Module components now available
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {
        // Components from modules not included
    }

    @KoraApp
    interface Application : MyModule {  // <----- Connected module
        // Module components now available
    }
    ```

4. Циклические зависимости:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    class A { A(B b) {} }

    @Component
    class B { B(A a) {} } // Wrong: circular dependency

    // Break the cycle with interfaces or restructuring
    interface AInterface {}
    interface BInterface {}

    @Component
    class AImpl implements AInterface { AImpl(BInterface b) {} }

    @Component
    class BImpl implements BInterface { BImpl(AInterface a) {} }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class A(val b: B)

    @Component
    class B(val a: A) // Wrong: circular dependency

    // Break the cycle with interfaces or restructuring
    interface AInterface
    interface BInterface

    @Component
    class AImpl(val b: BInterface) : AInterface

    @Component
    class BImpl(val a: AInterface) : BInterface
    ```

5. Игнорирование nullable-результатов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {
        private final @Nullable Dependency dep;

        public MyService(@Nullable Dependency dep) {
            this.dep = dep;
        }

        public void doSomething() {
            dep.work(); // Wrong: can throw NullPointerException
        }
    }

    // Safe usage
    public void doSomething() {
        if (dep != null) dep.work(); // Safe
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(
        private val dep: Dependency?
    ) {

        fun doSomething() {
            dep!!.work() // Wrong: can throw NullPointerException
        }
    }

    // Safe usage
    fun doSomething() {
        dep?.work() // Safe
    }
    ```

6. Дважды зарегистрировали один модуль:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module //(1)!
    public interface MyModule {
        default MyComponent myComponent() { return new MyComponent(); }
    }

    @KoraApp
    public interface Application extends MyModule { //(2)!
    }
    ```

    1.  Уже обнаруживается автоматически, потому что компилируется вместе с `@KoraApp`.
    2.  Наследование регистрирует те же фабрики второй раз и приводит к `Multiple components match dependency:`. Выберите один способ регистрации.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module //(1)!
    interface MyModule {
        fun myComponent(): MyComponent = MyComponent()
    }

    @KoraApp
    interface Application : MyModule { //(2)!
    }
    ```

    1.  Уже обнаруживается автоматически, потому что компилируется вместе с `@KoraApp`.
    2.  Наследование регистрирует те же фабрики второй раз и приводит к `Multiple components match dependency:`. Выберите один способ регистрации.

Как получить помощь:

Если вы все еще не можете разобраться:

1. Проверьте примеры: посмотрите `kora-examples`, чтобы увидеть рабочие шаблоны
2. Прочитайте документацию: обратитесь к [Документации контейнера](../documentation/container.md) за полным контрактом контейнера
3. Упростите: уберите сложность и проверьте минимальные компоненты
4. Сообщество: задайте вопросы в каналах сообщества Kora

Помните: большинство проблем DI возникают из-за отсутствующих компонентов, неправильного подключения модулей, несовпадающих тегов или циклических зависимостей. Начинайте с простого и постепенно наращивайте сложность!

## Что дальше? { #whats-next }

- [Создайте первое приложение Kora](getting-started.md), если вы прошли руководство только по DI до создания запускаемого HTTP-приложения.
- [Конфигурация с HOCON](config-hocon.md) или [Конфигурация с YAML](config-yaml.md) после начального руководства, чтобы узнать, как типизированная конфигурация попадает в граф.
- [Работа с JSON](json.md) после начального руководства, чтобы подготовить DTO запросов и ответов перед полноценным руководством по HTTP-серверу.
- [Тестирование с JUnit 5](testing-junit.md), чтобы покрыть собранный граф компонентными тестами.

## Помощь { #help }

Если возникли проблемы:

- проверьте [Документацию контейнера](../documentation/container.md)
- сравните с [Kora Java Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection) и [Kora Kotlin Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-dependency-injection)
- запустите `./gradlew clean classes` и прочитайте блок `Fix:` первой ошибки Kora, прежде чем менять структуру кода
- убедитесь, что компоненты помечены `@Component` или предоставляются модулем и что обработчик Kora включен в этом Gradle-модуле
