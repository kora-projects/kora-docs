---
search:
  exclude: true
title: Создание приложений Kora с внедрением зависимостей
summary: A comprehensive step-by-step tutorial for building complete applications with Kora's dependency injection framework
tags: dependency-injection, tutorial, components, modules, java, kotlin
---

# Создание приложений Kora с внедрением зависимостей { #building-kora-applications-dependency }

В этом руководстве показано, как на практике собирать приложение с помощью внедрения зависимостей Kora, работающего во время компиляции. Вы разберете, как `@KoraApp`, `@Module` и `@Component`
описывают граф зависимостей, как интерфейсы и реализации связываются внутри этого графа, а также как службы с жизненным циклом запускаются и останавливаются контейнером. Вы также увидите, как границы
модулей помогают сохранять полноценное приложение понятным по мере роста.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-dependency-injection-app).

## Что вы создадите { #youll-build }

Вы создадите полноценное приложение системы уведомлений, которое показывает все основные возможности внедрения зависимостей Kora:

- **многомодульную структуру проекта** с правильным разделением ответственностей
- **архитектуру на основе компонентов** с модулями внешней библиотеки
- **зависимости с тегами** для нескольких реализаций одного интерфейса
- **внедрение коллекций**, чтобы внедрять все реализации сразу
- **подмодули** для организации связанных компонентов
- **обобщенные фабрики** для типобезопасного создания компонентов
- **допускающие `null` зависимости** для аккуратной обработки отсутствующих компонентов
- **шаблон `ValueOf<T>`**, чтобы предотвращать каскадные обновления компонентов

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- базовое понимание Java или Kotlin
- знакомство с понятиями внедрения зависимостей (см. [Внедрение зависимостей с Kora](dependency-injection-introduction.md))

## Требования { #prerequisites }

!!! note "Рекомендуется: сначала прочитайте введение в DI"

    Это руководство предполагает, что вы прочитали **[Внедрение зависимостей с Kora](dependency-injection-introduction.md)** и понимаете базовые понятия внедрения зависимостей, которые использует Kora.

    Если вы еще не читали введение, начните с него, потому что это руководство быстро переходит к полноценному многомодульному приложению и сосредоточено на применении шаблонов внедрения зависимостей, а не на их объяснении с нуля.

    Также необходимы навыки базового знакомства с Java или Kotlin.

В этом руководстве вы создадите полноценное приложение Kora с нуля, постепенно вводя понятия внедрения зависимостей. Каждый шаг добавляет новую функциональность и одновременно показывает конкретный
шаблон внедрения зависимостей. К концу у вас будет полностью рабочее приложение, демонстрирующее все основные возможности DI в Kora.

## Обзор { #overview }

Это руководство переводит вас от понятий DI к практической сборке приложения. Примерная предметная область - система уведомлений, но главная тема здесь в том, как настоящий граф Kora остается
понятным, когда в нем есть несколько модулей, реализаций, необязательных зависимостей и вопросов жизненного цикла.

Руководство сохраняет одну предметную модель, постепенно добавляя вокруг нее новые возможности графа. Это похоже на реальную разработку: возможности DI редко изучаются изолированно; вы используете их
потому, что приложению нужны границы модулей, переопределения, несколько реализаций или управление жизненным циклом ресурсов.

### Граф приложения { #application-graph }

[Граф приложения Kora](../documentation/container.md) - это больше чем список классов. Это типизированная структура, которая описывает, какие компоненты существуют, какие зависимости нужны каждому
компоненту и как эти компоненты создаются. `@KoraApp` является корнем графа, `@Module` группирует фабрики и подключаемые части, а классы `@Component` становятся управляемыми узлами графа.

Хорошее проектирование графа сохраняет ответственности видимыми:

- модули приложения описывают собственные компоненты приложения
- библиотечные модули предоставляют переиспользуемые значения по умолчанию
- интерфейсы задают точки замены
- фабрики создают значения, которым нужно особое построение

### Настройка компонент { #component-setup }

Настоящим приложениям часто нужна не одна реализация интерфейса. Теги позволяют Kora различать зависимости, которые имеют один и тот же Java-тип, но выполняют разные роли. Переопределения позволяют
приложению заменить библиотечное значение по умолчанию поведением, специфичным для проекта. Необязательные зависимости позволяют компоненту подстраиваться, когда другого компонента нет в графе.

Эти возможности полезны, потому что они решают задачи связывания компонентов, не пряча их. Граф зависимостей по-прежнему показывает, какая реализация используется и почему.

### Жизненный цикл { #lifecycle }

Некоторые компоненты владеют ресурсами: клиентами, планировщиками, соединениями или фоновыми исполнителями. Kora может управлять компонентами с жизненным циклом так, чтобы запуск и остановка
происходили в порядке графа. Руководство также вводит `ValueOf<T>` как способ зависеть от ссылки на компонент, не заставляя заранее запускать все последующее поведение обновления.

К концу руководства приложение уведомлений должно ощущаться как рабочий пример проектирования графа: границы модулей, внешние значения по умолчанию, переопределения, теги, необязательные зависимости,
обобщенные фабрики и управление жизненным циклом служат одному приложению, а не выглядят разрозненными возможностями.

Практический ход такой:

1. создать многомодульный проект Kora
2. подключить внешние значения модулей по умолчанию
3. переопределить выбранные компоненты
4. использовать теги для нескольких реализаций одного типа
5. описать необязательные зависимости
6. организовать связанные компоненты с помощью подмодулей
7. добавить обобщенные фабрики и поведение с учетом жизненного цикла

## Зависимости { #dependencies }

В этом руководстве используется отдельный `settings.gradle` на верхнем уровне, а общая конфигурация Gradle хранится в `guide-dependency-injection/build.gradle`. В настоящем репозитории над каталогом
этого руководства есть еще один уровень, потому что в одной рабочей области находится несколько приложений руководств.

Создайте каталоги проекта:

```bash
mkdir -p guide-dependency-injection
mkdir -p guide-dependency-injection/guide-dependency-injection-common guide-dependency-injection/guide-dependency-injection-lib guide-dependency-injection/guide-dependency-injection-app
```

Установите JDK перед подготовкой Gradle Wrapper. Для первого запуска достаточно Eclipse Temurin JDK 21: он запускает Gradle, а Gradle-инструменты сможет автоматически скачать JDK, которая нужна
конкретной сборке.

===! ":simple-linux: `Linux`"

    Для Ubuntu/Debian можно подключить репозиторий Adoptium и установить Temurin JDK:

    ```bash
    sudo apt update
    sudo apt install -y wget gpg
    wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /usr/share/keyrings/adoptium.gpg
    echo "deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(. /etc/os-release && echo $VERSION_CODENAME) main" | sudo tee /etc/apt/sources.list.d/adoptium.list
    sudo apt update
    sudo apt install -y temurin-21-jdk
    ```

=== ":simple-apple: `macOS`"

    Если установлен Homebrew, поставьте Temurin JDK через cask:

    ```bash
    brew install --cask temurin@21
    export JAVA_HOME=$(/usr/libexec/java_home -v 21)
    ```

=== ":material-microsoft-windows: `Windows`"

    Если установлен `winget`, поставьте Temurin JDK из терминала PowerShell:

    ```powershell
    winget install EclipseAdoptium.Temurin.21.JDK
    ```

    Если `winget` недоступен, скачайте установщик Windows со [страницы загрузок Eclipse Temurin](https://adoptium.net/temurin/releases/?version=21), выберите **JDK 21** для архитектуры вашего
    процессора, запустите установщик и включите обновление `JAVA_HOME` и `PATH`, если установщик предложит такой пункт.

    После установки откройте новый терминал, чтобы обновились переменные окружения.

Проверьте, что JDK доступен:

```bash
java -version
```

В выводе должна быть версия Java 21.

Подготовьте Gradle Wrapper в том же каталоге. Это руководство создает многомодульный проект вручную, поэтому здесь нет шага `gradle init`, который автоматически создал бы wrapper-файлы.

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

Шаг 3. Скачайте скрипт запуска wrapper.

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

Теперь настроим многомодульную конфигурацию Gradle. Этот гайд не ограничивается одним приложением: он показывает, как Kora собирает граф из нескольких модулей, поэтому структура проекта сама является
частью обучения.

В этой настройке Gradle должен сделать несколько вещей:

- зарегистрировать три подмодуля руководства
- настроить JDK, которым будут компилироваться все подмодули
- подключить BOM Kora один раз для всех подмодулей
- распространить версии из BOM на нужные Gradle-конфигурации
- включить общие правила компиляции и запуска тестов

#### Структура модулей { #module-structure }

Создайте следующую структуру каталогов. Расширения файлов отличаются между Gradle Groovy DSL и Gradle Kotlin DSL, но границы модулей остаются одинаковыми:

===! ":fontawesome-brands-java: `Java`"

    ```
    |-- settings.gradle
    `-- guide-dependency-injection/
        |-- build.gradle
        |-- guide-dependency-injection-common/
        |-- guide-dependency-injection-lib/
        `-- guide-dependency-injection-app/
    ```

=== ":simple-kotlin: `Kotlin`"

    ```
    |-- settings.gradle.kts
    `-- guide-dependency-injection/
        |-- build.gradle.kts
        |-- guide-dependency-injection-common/
        |-- guide-dependency-injection-lib/
        `-- guide-dependency-injection-app/
    ```

`guide-dependency-injection-common` хранит общие договоры, `guide-dependency-injection-lib` имитирует переиспользуемую библиотеку, а `guide-dependency-injection-app` содержит запускаемое приложение с
`@KoraApp`. Такое разделение нужно, чтобы дальше показать переопределения, теги, необязательные зависимости и подключение дополнительных модулей.

#### Корневой settings { #root-settings }

Отредактируйте файл настроек Gradle верхнего уровня. Он задает имя всей сборки и сообщает Gradle, какие подмодули в нее входят:

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
    plugins {
        id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
    }

    rootProject.name = "kora-guide"

    include("guide-dependency-injection:guide-dependency-injection-common")
    include("guide-dependency-injection:guide-dependency-injection-lib")
    include("guide-dependency-injection:guide-dependency-injection-app")
    ```

Плагин `foojay-resolver-convention` нужен для Java toolchains: он помогает Gradle найти или скачать JDK нужной версии. Строки include регистрируют вложенные модули через Gradle-пути, например
`:guide-dependency-injection:guide-dependency-injection-app`, чтобы дальше можно было запускать задачи конкретного модуля.

#### Свойства Gradle { #gradle-properties }

Добавьте `gradle.properties`, чтобы Gradle мог находить установленные JDK и загружать нужный JDK Temurin, если JDK 24 отсутствует локально:

===! ":fontawesome-brands-java: `Java`"

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true
    ```

=== ":simple-kotlin: `Kotlin`"

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true
    kotlin.jvm.target.validation.mode=warning
    ```

Первые два свойства делают учебную сборку менее зависимой от локального окружения. Kotlin-флаг нужен для Kotlin 1.9.25: если компилятор не может выставить target ровно как JDK 24, он сообщает об этом
как warning и не останавливает учебную сборку.

#### Общий build-файл { #shared-build-file }

Создайте общий build-файл в `guide-dependency-injection/`. Он применяется к трем вложенным модулям: `common`, `lib` и `app`, поэтому BOM, toolchain, classpath и тестовые настройки не придется
дублировать в каждом модуле.

Начните с импортов и пустого блока `subprojects`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    subprojects {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import org.gradle.api.plugins.JavaPluginExtension
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    subprojects {
    }
    ```

#### BOM Kora { #kora-bom }

Внутри `subprojects {}` создайте отдельную конфигурацию `koraBom`. BOM (`Bill of Materials`) хранит согласованные версии модулей Kora, чтобы все подмодули использовали совместимый набор версий.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    subprojects {
        configurations {
            koraBom
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    subprojects {
        val koraBom by configurations.creating
    }
    ```

#### JDK toolchain { #jdk-toolchain }

Настройте JDK после подключения плагина `java` в подмодуле. Gradle может запускаться одной JDK, а компилировать проект другой, поэтому toolchain делает учебную сборку воспроизводимой.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    subprojects {
        plugins.withId("java") {
            java {
                toolchain {
                    languageVersion = JavaLanguageVersion.of(24)
                    vendor = JvmVendorSpec.ADOPTIUM
                }
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    subprojects {
        plugins.withId("java") {
            extensions.configure<JavaPluginExtension>("java") {
                toolchain {
                    languageVersion.set(JavaLanguageVersion.of(24))
                    vendor.set(JvmVendorSpec.ADOPTIUM)
                }
            }
        }
    }
    ```

#### Classpath-конфигурации { #classpath-configurations }

Распространите BOM на Gradle-конфигурации, которые используются кодом приложения, compile-time API, обработчиками аннотаций, публичным API библиотек и тестами.

===! ":fontawesome-brands-java: `Java`"

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

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    subprojects {
        configurations {
            compileOnly.get().extendsFrom(koraBom)
            implementation.get().extendsFrom(koraBom)
            api.get().extendsFrom(koraBom)
            testImplementation.get().extendsFrom(koraBom)
        }
    }
    ```

`annotationProcessor` и `testAnnotationProcessor` получают BOM отдельно, потому что обработчики аннотаций Kora работают в собственном classpath. Конфигурация `api` важна для `common` и `lib`, где
типы могут становиться частью публичного API, который видят другие модули.

#### Версия Kora { #kora-version }

Подключите сам BOM. Переменная `$koraVersion` берется из `gradle.properties` репозитория; после этой строки отдельные модули смогут писать Kora-зависимости без явной версии.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    subprojects {
        dependencies {
            koraBom platform("ru.tinkoff.kora:kora-parent:$koraVersion")
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    subprojects {
        dependencies {
            koraBom(platform("ru.tinkoff.kora:kora-parent:$koraVersion"))
        }
    }
    ```

#### Итоговый файл { #final-file }

Итоговый общий build-файл собирает эти решения вместе: конфигурацию BOM, JDK toolchain, classpath, зависимость от BOM Kora и общее поведение тестов.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    subprojects {
        configurations {
            koraBom
        }

        plugins.withId("java") {
            java {
                toolchain {
                    languageVersion = JavaLanguageVersion.of(24)
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
            koraBom platform("ru.tinkoff.kora:kora-parent:$koraVersion")
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
        val koraBom by configurations.creating

        plugins.withId("java") {
            extensions.configure<JavaPluginExtension>("java") {
                toolchain {
                    languageVersion.set(JavaLanguageVersion.of(24))
                    vendor.set(JvmVendorSpec.ADOPTIUM)
                }
            }
        }

        configurations {
            compileOnly.get().extendsFrom(koraBom)
            implementation.get().extendsFrom(koraBom)
            api.get().extendsFrom(koraBom)
            testImplementation.get().extendsFrom(koraBom)
        }

        dependencies {
            koraBom(platform("ru.tinkoff.kora:kora-parent:$koraVersion"))
        }
    }
    ```

### Основа приложения { #application-base }

**Цель**: создать модуль общих договоров и запускаемый модуль приложения, который будут расширять следующие шаги.

**Что вводит этот шаг**: минимальную точку входа `@KoraApp`, модуль общих договоров и начальную многомодульную структуру. Это базовый граф, прежде чем мы начнем накладывать поверх него дополнительные
возможности DI.

**Зачем это нужно**: сначала мы задаем, что относится к модулю приложения, а что относится к переиспользуемым модулям. Это повторяет разделение, описанное
в [Внедрение зависимостей с Kora: @KoraApp](dependency-injection-introduction.md#koraapp), [@Root](dependency-injection-introduction.md#root)
и [документации контейнера: Контейнер](../documentation/container.md#container).

**Что мы имитируем**: настоящий корень приложения, который отвечает за запуск, и модуль общего API, от которого другие модули могут зависеть, не подтягивая поведение, специфичное для приложения.

**Создайте общие договоры** (`guide-dependency-injection/guide-dependency-injection-common/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/common/`
или `guide-dependency-injection/guide-dependency-injection-common/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/common/`):

#### Сборка общего модуля { #build-shared-module }

Сначала создайте build-файл для `guide-dependency-injection-common`. Этот модуль содержит только интерфейсы и общие типы, поэтому ему нужен библиотечный JVM-плагин и тестовые зависимости, но не нужен
плагин `application` и не нужна обработка аннотаций Kora.

===! ":fontawesome-brands-java: Java"

    Плагин `java-library` подходит для модулей с публичным API:

    ```groovy
    plugins {
        id "java-library"
    }
    ```

    Позже другие модули будут зависеть от `common`, поэтому Gradle должен понимать разницу между внутренними зависимостями реализации и типами, которые являются частью API.

    Добавьте тестовые зависимости:

    ```groovy
    dependencies {
        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
    }
    ```

    Здесь `junit-bom` выравнивает версии JUnit, `junit-jupiter` добавляет JUnit 5, а `test-junit5` подключает тестовые утилиты Kora. В этом первом шаге тестов еще может не быть, но модуль сразу готов к
    проверкам договоров и будущих компонентов.

    Итоговый `build.gradle` общего модуля:

    ```groovy
    plugins {
        id "java-library"
    }

    dependencies {
        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Плагин `kotlin("jvm")` компилирует Kotlin-код в JVM-классы, которые смогут использовать `app` и `lib` модули:

    ```kotlin
    plugins {
        kotlin("jvm") version "1.9.25"
    }
    ```

    Добавьте тестовые зависимости:

    ```kotlin
    dependencies {
        testImplementation(platform("org.junit:junit-bom:$junitVersion"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

    `junit-bom` выравнивает версии JUnit, `junit-jupiter` добавляет JUnit 5, а `test-junit5` подключает тестовые утилиты Kora.

    Итоговый `build.gradle.kts` общего модуля:

    ```kotlin
    plugins {
        kotlin("jvm") version "1.9.25"
    }

    dependencies {
        testImplementation(platform("org.junit:junit-bom:$junitVersion"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

Затем создайте интерфейсы:

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.common;

    public interface Notifier {
        void notify(String user, String message);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.common

    fun interface Notifier {
        fun notify(user: String, message: String)
    }
    ```

**Создайте основное приложение** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/`
или `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/`):

#### Сборка приложения { #build-application }

Создайте build-файл для `guide-dependency-injection-app`. Этот модуль запускается, содержит `@KoraApp` и должен включить генерацию графа Kora, поэтому его Gradle-настройка подробнее, чем у общего
модуля договоров.

===! ":fontawesome-brands-java: Java"

    Начните с плагинов:

    ```groovy
    plugins {
        id "java"
        id "application"
    }
    ```

    `java` компилирует исходники, а `application` добавляет запуск через `./gradlew run` и настройки main-класса.

    Добавьте обработчик аннотаций Kora:

    ```groovy
    dependencies {
        annotationProcessor "ru.tinkoff.kora:annotation-processors"
    }
    ```

    Именно `annotationProcessor` читает `@KoraApp` и генерирует `ApplicationGraph`. Без этой строки Java-код может дойти до ссылки на сгенерированный класс, но сам граф приложения не будет создан.

    Теперь добавьте зависимости приложения:

    ```groovy
    dependencies {
        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation project(":guide-dependency-injection:guide-dependency-injection-lib")
        implementation "ru.tinkoff.kora:config-hocon"
        implementation "ru.tinkoff.kora:logging-logback"
    }
    ```

    `common` дает общий интерфейс `Notifier`, `lib` будет добавлять библиотечные компоненты в следующих шагах, `config-hocon` подключает конфигурацию, а `logging-logback` добавляет логирование.

    Добавьте настройки для тестов:

    ```groovy
    dependencies {
        testAnnotationProcessor "ru.tinkoff.kora:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
    }
    ```

    `testAnnotationProcessor` нужен, когда тестовый граф тоже генерируется Kora. `test-junit5` дает интеграцию Kora с JUnit 5.

    Настройте запуск приложения:

    ```groovy
    application {
        applicationName = "application"
        mainClass = "ru.tinkoff.kora.guide.dependencyinjection.Application"
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"]
    }
    ```

    Этот блок принадлежит Gradle-плагину `application`. Он не имеет прямого отношения к DI-контейнеру Kora, но связывает сгенерированный граф Kora с обычным способом запуска JVM-приложения:

    - `applicationName = "application"` задает короткое имя приложения в Gradle-дистрибутиве. По этому имени Gradle создаст стартовые скрипты внутри архива, например `bin/application`.
    - `mainClass` указывает на класс, где находится метод `main`. В Java это исходный интерфейс `Application`, а не сгенерированный `ApplicationGraph`: ваш `main` сам вызывает
      `KoraApplication.run(ApplicationGraph::graph)`.
    - `applicationDefaultJvmArgs` задает JVM-аргументы, которые будут использоваться при `./gradlew run` и попадут в стартовые скрипты дистрибутива.

    Важно, что `mainClass` ссылается на обычный исходный тип приложения. `ApplicationGraph` появится только после работы `annotationProcessor`, поэтому задача `classes` одновременно проверяет Java-код,
    запуск обработчика аннотаций и возможность построить граф Kora.

    Добавьте имя архива дистрибутива:

    ```groovy
    distTar {
        archiveFileName = "application.tar"
    }
    ```

    `distTar` — это задача, которую добавляет Gradle-плагин `application`. Она собирает tar-архив с приложением: скомпилированные классы, runtime-зависимости и стартовые скрипты. По умолчанию имя
    архива зависит от имени проекта и версии, а в многомодульном учебном проекте это может давать длинные и менее удобные имена.

    `archiveFileName = "application.tar"` делает имя артефакта стабильным. Это удобно для тестов, CI и дальнейших шагов руководства: можно ссылаться на один предсказуемый файл, не вычисляя имя
    Gradle-проекта и версию.

    Итоговый `build.gradle` приложения:

    ```groovy
    plugins {
        id "java"
        id "application"
    }

    dependencies {
        annotationProcessor "ru.tinkoff.kora:annotation-processors"

        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation project(":guide-dependency-injection:guide-dependency-injection-lib")
        implementation "ru.tinkoff.kora:config-hocon"
        implementation "ru.tinkoff.kora:logging-logback"

        testAnnotationProcessor "ru.tinkoff.kora:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
    }

    application {
        applicationName = "application"
        mainClass = "ru.tinkoff.kora.guide.dependencyinjection.Application"
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
        id("application")
        kotlin("jvm") version "1.9.25"
        id("com.google.devtools.ksp") version "1.9.25-1.0.20"
    }
    ```

    `application` добавляет запуск через `./gradlew run`, `kotlin("jvm")` компилирует Kotlin-код, а `com.google.devtools.ksp` запускает символьный процессор Kora.

    Добавьте KSP-процессор Kora:

    ```kotlin
    dependencies {
        ksp("ru.tinkoff.kora:symbol-processors")
    }
    ```

    KSP читает `@KoraApp` и генерирует `ApplicationGraph`. Без этой зависимости приложение не получит сгенерированный граф.

    Теперь добавьте зависимости приложения:

    ```kotlin
    dependencies {
        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-lib"))
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

    `common` дает общий интерфейс `Notifier`, `lib` будет добавлять библиотечные компоненты, `config-hocon` подключает HOCON-конфигурацию, а `logging-logback` добавляет логирование.

    Добавьте тестовые зависимости:

    ```kotlin
    dependencies {
        testImplementation(platform("org.junit:junit-bom:$junitVersion"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

    Настройте запуск:

    ```kotlin
    application {
        applicationName.set("application")
        mainClass.set("ru.tinkoff.kora.guide.dependencyinjection.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }
    ```

    Этот блок принадлежит Gradle-плагину `application` и объясняет Gradle, как запускать Kotlin-приложение:

    - `applicationName.set("application")` задает имя приложения в дистрибутиве и имя стартового скрипта.
    - `mainClass.set(...)` указывает на класс, где находится функция `main`. В Kotlin top-level функция `main` из файла `Application.kt` компилируется в JVM-класс `ApplicationKt`, поэтому здесь указан
      именно `ApplicationKt`.
    - `applicationDefaultJvmArgs` задает JVM-аргументы для `./gradlew run` и будущих стартовых скриптов.

    Аргумент `-Dfile.encoding=UTF-8` фиксирует кодировку при запуске. Это помогает избежать различий между Windows, Linux и macOS, особенно когда приложение пишет текст в логи или читает строковые
    ресурсы.

    Добавьте стабильное имя tar-архива:

    ```kotlin
    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

    `distTar` собирает исполняемый дистрибутив приложения: классы, runtime-зависимости и стартовые скрипты. Фиксированное имя `application.tar` удобно для тестов, CI и следующих шагов руководства,
    где важно ссылаться на один предсказуемый артефакт.

    Итоговый `build.gradle.kts` приложения:

    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version "1.9.25"
        id("com.google.devtools.ksp") version "1.9.25-1.0.20"
    }

    dependencies {
        ksp("ru.tinkoff.kora:symbol-processors")

        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-lib"))
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:logging-logback")

        testImplementation(platform("org.junit:junit-bom:$junitVersion"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }

    application {
        applicationName.set("application")
        mainClass.set("ru.tinkoff.kora.guide.dependencyinjection.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }

    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

Затем создайте приложение:

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends HoconConfigModule, LogbackModule {
        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application : HoconConfigModule, LogbackModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

**Соберите и запустите**:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

**Ожидаемый результат**: приложение запускается и завершается без ошибок. Модуль `lib` уже подключен в сборке, а следующие шаги добавят больше компонентов и модулей.

---

### Внешние модули { #external-modules }

**Цель**: создать переиспользуемые библиотечные модули, которые предоставляют реализации по умолчанию.

**Что вводит этот шаг**: фабрики внешних модулей и `@DefaultComponent`. `EmailModule` находится вне модуля приложения и предоставляет значения по умолчанию, которые приложение может принять или
заменить позже.

**Зачем это нужно**: внешние модули - это способ, которым переиспользуемые библиотеки Kora публикуют компоненты для приложений, но они не обнаруживаются автоматически и должны подключаться явно. Это
соответствует разделам [Внедрение зависимостей с Kora: @Module](dependency-injection-introduction.md#module), [@DefaultComponent](dependency-injection-introduction.md#defaultcomponent)
и [документация контейнера: фабрика внешнего модуля](../documentation/container.md#external-module-factory).

**Что мы имитируем**: библиотеку, которая поставляет реализацию уведомителя по электронной почте и договор конфигурации по умолчанию, но при этом позволяет приложению позже переопределить детали
представления.

Сначала создайте файл сборки библиотечного модуля:

===! ":fontawesome-brands-java: Java"

    `guide-dependency-injection/guide-dependency-injection-lib/build.gradle`

    ```groovy
    plugins {
        id "java-library"
    }

    dependencies {
        api project(":guide-dependency-injection:guide-dependency-injection-common")

        implementation "ru.tinkoff.kora:config-common"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `guide-dependency-injection/guide-dependency-injection-lib/build.gradle.kts`

    ```kotlin
    plugins {
        kotlin("jvm") version "1.9.25"
    }

    dependencies {
        api(project(":guide-dependency-injection:guide-dependency-injection-common"))

        implementation("ru.tinkoff.kora:config-common")

        testImplementation(platform("org.junit:junit-bom:$junitVersion"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

**Создайте EmailModule** (`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/email/`
или `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/email/`):

===! ":fontawesome-brands-java: Java"

    Создайте EmailModule:

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.email;

    import ru.tinkoff.kora.guide.dependencyinjection.common.Notifier;
    import ru.tinkoff.kora.common.DefaultComponent;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.config.common.Config;
    import ru.tinkoff.kora.config.common.extractor.ConfigValueExtractor;

    import java.util.function.Supplier;

    public interface EmailModule {
        final class EmailTag {
            private EmailTag() {}
        }

        default EmailConfig config(Config config, ConfigValueExtractor<EmailConfig> extractor) {
            return extractor.extract(config["notifier.email"]);
        }

        @Tag(EmailTag.class)
        @DefaultComponent
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL DEFAULT] ";
        }

        @Tag(EmailTag.class)
        default Notifier emailNotifier(EmailConfig emailConfig,
                                       @Tag(EmailTag.class) Supplier<String> emailHeaderSupplier) {
            String header = emailHeaderSupplier.get();
            return (user, message) -> {
                System.out.println(String.format("%s%s [USER:%s]: %s", header, emailConfig.topic(), user, message));
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте EmailModule:

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.email

    import java.util.function.Supplier
    import ru.tinkoff.kora.guide.dependencyinjection.common.Notifier
    import ru.tinkoff.kora.common.DefaultComponent
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.config.common.Config
    import ru.tinkoff.kora.config.common.extractor.ConfigValueExtractor

    interface EmailModule {
        class EmailTag {
            // Классы Kotlin по умолчанию final, закрытый конструктор не нужен
        }

        fun config(config: Config, extractor: ConfigValueExtractor<EmailConfig>): EmailConfig {
            return extractor.extract(config["notifier.email"])
        }

        @Tag(EmailTag::class)
        @DefaultComponent
        fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL DEFAULT] " }
        }

        @Tag(EmailTag::class)
        fun emailNotifier(emailConfig: EmailConfig,
                         @Tag(EmailTag::class) headerSupplier: Supplier<String>): Notifier {
            return Notifier { user, message ->
                println("${headerSupplier.get()}${emailConfig.topic} [USER:$user]: $message")
            }
        }
    }
    ```

**Создайте EmailConfig** (`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/email/`
или `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/email/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.email;

    public record EmailConfig(String topic) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.email

    data class EmailConfig(val topic: String)
    ```

**Обновите Application**, чтобы подключить модуль электронной почты:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Подключили модуль
        // EmailModule предоставляет уведомление по электронной почте по умолчанию
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        EmailModule {  // <----- Подключили модуль
        // EmailModule предоставляет уведомление по электронной почте по умолчанию
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
        "ru.tinkoff.kora": "INFO" //(3)!
      }
    }
    ```

    1. Тема или название канала, которое использует компонент.
    2. Уровень журналирования для `ROOT`.
    3. Уровень журналирования для `ru.tinkoff.kora`.

=== ":simple-yaml: `YAML`"

    ```yaml
    notifier:
      email:
        topic: "USER" #(1)!
      logging:
        levels:
          ROOT: "WARN" #(2)!
          "ru.tinkoff.kora": "INFO" #(3)!
    ```

    1. Тема или название канала, которое использует компонент.
    2. Уровень журналирования для `ROOT`.
    3. Уровень журналирования для `ru.tinkoff.kora`.

**Соберите и запустите** - у приложения все еще нет корневого компонента, поэтому оно просто запускается и останавливается.

**Ключевое понятие**: `@DefaultComponent` предоставляет библиотечные значения по умолчанию, которые приложения могут переопределять.

**Правило регистрации модулей**: если тип помечен `@Module`, не подключайте его одновременно через `extends` в `@KoraApp` или другом модуле. Модуль должен регистрироваться ровно одним способом: либо
наследоваться через `extends`, либо обнаруживаться потому, что он помечен `@Module` и находится под текущим графом `@KoraApp` / `@KoraSubmodule`. Сам `@KoraSubmodule` - это как раз случай, где
наследование ожидаемо.

**Что сгенерирует Kora для `EmailModule`**: после `./gradlew clean classes` в `ApplicationGraph` появятся не все строки из примера ниже один в один, потому что номера `componentN` являются внутренними
именами генератора. Но структура будет такой: Kora создаст узел конфигурации, узел значения по умолчанию и узел самого уведомителя.

===! ":fontawesome-brands-java: Java"

    ??? abstract "Java: фрагмент generated-графа для `EmailModule`"

        ```java
        private final Node<EmailConfig> component8;
        private final Node<Supplier<String>> component9;
        private final Node<Notifier> component10;

        component8 = graphDraw.addNode0(_type_of_component8,
            new Class<?>[]{},
            g -> impl.config(
                g.get(ApplicationGraph.holder0.component6),
                g.get(ApplicationGraph.holder0.component7)
            ),
            List.of(), component6, component7);

        component9 = graphDraw.addNode0(_type_of_component9,
            new Class<?>[]{EmailModule.EmailTag.class},
            g -> impl.emailNotifierHeaderSupplier(),
            List.of());

        component10 = graphDraw.addNode0(_type_of_component10,
            new Class<?>[]{EmailModule.EmailTag.class},
            g -> impl.emailNotifier(
                g.get(ApplicationGraph.holder0.component8),
                g.get(ApplicationGraph.holder0.component9)
            ),
            List.of(), component8, component9);
        ```

        Здесь видно, почему `EmailModule` нужно подключить через `extends`: только после этого его фабричные методы попадают в граф приложения.

        - `component8` создается из `notifier.email` и превращает HOCON-конфигурацию в типизированный `EmailConfig`.
        - `component9` - tagged-компонент `Supplier<String>` с `EmailTag`. Так Kora отличает email-заголовок от других возможных `Supplier<String>`.
        - `component10` - tagged `Notifier`, который зависит от `EmailConfig` и tagged `Supplier<String>`.
        - `@DefaultComponent` у `emailNotifierHeaderSupplier()` означает: библиотека дает значение по умолчанию, а приложение сможет заменить его в следующей главе.

=== ":simple-kotlin: `Kotlin`"

    ??? abstract "Kotlin: фрагмент generated-графа для `EmailModule`"

        ```kotlin
        public val component8: Node<EmailConfig>
        public val component9: Node<Supplier<String>>
        public val component10: Node<Notifier>

        component8 = graphDraw.addNode0(map["component8"],
          arrayOf(),
          { impl.config(
            it.get(holder0.component6),
            it.get(holder0.component7)
          ) },
          listOf(),
          component6, component7
        )

        component9 = graphDraw.addNode0(map["component9"],
          arrayOf(EmailModule.EmailTag::class.java),
          { impl.emailNotifierHeaderSupplier() },
          listOf()
        )

        component10 = graphDraw.addNode0(map["component10"],
          arrayOf(EmailModule.EmailTag::class.java),
          { impl.emailNotifier(
            it.get(holder0.component8),
            it.get(holder0.component9)
          ) },
          listOf(),
          component8, component9
        )
        ```

        Kotlin/KSP генерирует тот же смысл в Kotlin-коде:

        - `EmailConfig` становится отдельным узлом графа.
        - `EmailTag` записывается в массив тегов у `Supplier<String>` и `Notifier`.
        - `emailNotifier(...)` получает зависимости из графа, а не создает их сам.
        - В следующей главе приложение переопределит `emailNotifierHeaderSupplier()`, и Kora подставит новый узел вместо библиотечного `@DefaultComponent`.

---

### Переопределение компонента { #component-override }

**Цель**: показать, как приложения могут переопределять библиотечные значения по умолчанию.

**Что вводит этот шаг**: переопределение компонента для фабрики `@DefaultComponent` из внешнего модуля. Приложение заменяет только поставщика заголовка и оставляет остальное библиотечное поведение без
изменений.

**Зачем это нужно**: библиотеки должны предоставлять надежные значения по умолчанию, но приложения должны сохранять окончательный контроль над поведением, видимым для предметной области. Это
соответствует
разделам [Внедрение зависимостей с Kora: стандартная фабрика](dependency-injection-introduction.md#defaultcomponent-factory), [@DefaultComponent](dependency-injection-introduction.md#defaultcomponent)
и [документация контейнера: стандартная фабрика](../documentation/container.md#standard-factory).

**Что мы имитируем**: настройку общего библиотечного уведомителя под конкретное приложение без ответвления или полного переписывания модуля.

**Создайте NotifyRunner** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/`
или `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection;

    import ru.tinkoff.kora.application.graph.All;
    import ru.tinkoff.kora.application.graph.Lifecycle;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.common.annotation.Root;
    import ru.tinkoff.kora.guide.dependencyinjection.common.Notifier;

    @Root
    @Component
    public final class NotifyRunner implements Lifecycle {

        private final All<Notifier> allNotifiers;

        public NotifyRunner(@Tag(Tag.Any.class) All<Notifier> allNotifiers) {
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

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection

    import ru.tinkoff.kora.application.graph.All
    import ru.tinkoff.kora.application.graph.Lifecycle
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.common.annotation.Root
    import ru.tinkoff.kora.guide.dependencyinjection.common.Notifier

    @Root
    @Component
    class NotifyRunner(
        @Tag(Tag.Any::class) private val allNotifiers: All<Notifier>
    ) : Lifecycle {

        override fun init() {
            println("DI tutorial step 3 start")
            allNotifiers.forEach { it.notify("Alice", "Welcome!") }
        }

        override fun release() {
            println("Application shutdown")
        }
    }
    ```

**Обновите Application**, чтобы переопределить заголовок электронной почты:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Подключили модуль
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

    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        EmailModule {  // <----- Подключили модуль
        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

**Соберите и запустите**:

```
DI tutorial step 3 start
[EMAIL OVERRIDDEN] USER [USER:Alice]: Welcome!
Application shutdown
```

**Ключевое понятие**: приложения могут переопределять реализации `@DefaultComponent`, предоставляя собственные фабричные методы.

---

### Зависимости с тегами { #tagged-dependencies }

**Цель**: показать, как теги позволяют иметь несколько реализаций одного интерфейса, а `All<T>` позволяет получить все подходящие уведомители сразу.

**Что вводит этот шаг**: `@Tag` для различения нескольких реализаций `Notifier` и `All<T>` для рассылки через них. `SmsModule` - внутренний `@Module`, поэтому он автоматически обнаруживается из модуля
приложения, а не наследуется через `extends`.

**Зачем это нужно**: как только у одного договора появляется несколько реализаций, обычного внедрения только по типу уже недостаточно. Теги делают граф явным, а `All<T>` дает естественный способ
разослать уведомления по нескольким каналам.
См. [Внедрение зависимостей с Kora: @Tag](dependency-injection-introduction.md#tag), [Запросы зависимостей и разрешение: All](dependency-injection-introduction.md#all), [Система тегов](dependency-injection-introduction.md#tag-system)
и [документация контейнера: `Tag.Any`](../documentation/container.md#tag-any).

**Что мы имитируем**: службу уведомлений, которая может отправить одно и то же сообщение через каждый доступный канал, а не выбирать только одну реализацию.

**Создайте SmsModule** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/sms/`
или `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/sms/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.sms;

    import jakarta.annotation.Nullable;
    import ru.tinkoff.kora.common.Module;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.dependencyinjection.common.Notifier;

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
    package ru.tinkoff.kora.guide.dependencyinjection.sms

    import ru.tinkoff.kora.common.Module
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.dependencyinjection.common.Notifier

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

**Примечание о приложении**: `SmsModule` помечен `@Module` и находится в пакете приложения, поэтому Kora обнаруживает его автоматически. Не добавляйте его через `extends` в `Application`.

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Подключили модуль
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

    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        EmailModule {  // <----- Подключили модуль
        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

**Обновите NotifyRunner**, чтобы пройтись по всем уведомителям:

===! ":fontawesome-brands-java: Java"

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
            allNotifiers.forEach { it.notify("Bob", "Hello!") }
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

**Ключевое понятие**: `@Tag` позволяет иметь несколько реализаций одного договора, а `All<T>` позволяет отправлять сообщение через все из них.

---

### Опциональные зависимости { #optional-dependencies }

**Цель**: добавить необязательного соисполнителя для SMS, не меняя договор `Notifier`.

**Что вводит этот шаг**: допускающие `null` зависимости для необязательного поведения. `SmsModule` может работать как с `SmsCellularProvider`, так и без него, а `SmsCellularModule` добавляет
поставщика только тогда, когда приложение решает его унаследовать.

**Зачем это нужно**: некоторые возможности должны дополнять существующий компонент, а не вынуждать создавать отдельную ветку реализации. Это соответствует
разделам [Внедрение зависимостей с Kora: `Nullable`](dependency-injection-introduction.md#optional)
и [документация контейнера: необязательные зависимости](../documentation/container.md#optional-dependencies).

**Что мы имитируем**: необязательное обогащение форматирования SMS кодом поставщика, при котором уведомитель продолжает работать даже без настроенного поставщика.

**Создайте SmsCellularProvider и SmsCellularModule** (`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/sms/`
или `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/sms/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.sms;

    public interface SmsCellularProvider {
        String getCode();
    }
    ```

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.sms;

    import ru.tinkoff.kora.common.DefaultComponent;

    public interface SmsCellularModule {

        @DefaultComponent
        default SmsCellularProvider smsCellularProvider() {
            return () -> "1";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.sms

    fun interface SmsCellularProvider {
        fun getCode(): String
    }
    ```

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.sms

    import ru.tinkoff.kora.common.DefaultComponent

    interface SmsCellularModule {
        @DefaultComponent
        fun smsCellularProvider(): SmsCellularProvider {
            return SmsCellularProvider { "1" }
        }
    }
    ```

**Обновите Application**, чтобы подключить модуль поставщика. `SmsCellularModule` не помечен `@Module`, поэтому он намеренно подключается через `extends`:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule,  // <----- Подключили модуль
            SmsCellularModule {  // <----- Подключили модуль
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
        EmailModule,  // <----- Подключили модуль
        SmsCellularModule {  // <----- Подключили модуль
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

**Ключевое понятие**: `@Nullable` в Java и nullable-типы в Kotlin позволяют компоненту продолжать работу даже тогда, когда необязательная зависимость отсутствует.

---

### Подмодуль { #submodule }

**Цель**: показать `@KoraSubmodule` для организации связанных компонентов.

**Что вводит этот шаг**: `@KoraSubmodule` как границу, которая превращает другой Gradle-модуль в видимую для DI единицу компиляции. Внутри этого подмодуля объявления `@Module` и `@Component`
собираются и передаются основному `@KoraApp` через наследование.

**Зачем это нужно**: обычные Gradle-модули не сканируются Kora, если в них нет `@KoraApp` или `@KoraSubmodule`. Именно этот механизм позволяет вынести функциональность отправителей сообщений в
собственный модуль и не потерять обнаружение DI.
См. [Внедрение зависимостей с Kora: @KoraSubmodule](dependency-injection-introduction.md#korasubmodule), [примечание об области обзора](dependency-injection-introduction.md#overview)
и [документация контейнера: фабрика подмодуля](../documentation/container.md#submodule-factory).

**Что мы имитируем**: более крупную кодовую базу, где отдельная команда или пакет владеет доставкой сообщений, но основное приложение все равно собирает это в один граф.

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

===! ":fontawesome-brands-java: Java"

    ```groovy
    plugins {
        id "java-library"
    }

    dependencies {
        annotationProcessor "ru.tinkoff.kora:annotation-processors"

        api project(":guide-dependency-injection:guide-dependency-injection-common")

        implementation "ru.tinkoff.kora:common"

        testAnnotationProcessor "ru.tinkoff.kora:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    plugins {
        kotlin("jvm") version "1.9.25"
        id("com.google.devtools.ksp") version "1.9.25-1.0.20"
    }

    dependencies {
        ksp("ru.tinkoff.kora:symbol-processors")

        api(project(":guide-dependency-injection:guide-dependency-injection-common"))

        implementation("ru.tinkoff.kora:common")

        testImplementation(platform("org.junit:junit-bom:$junitVersion"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

**Обновите `guide-dependency-injection-app/build.gradle`**, чтобы добавить зависимость на новый модуль:

===! ":fontawesome-brands-java: Java"

    ```groovy
    dependencies {
        annotationProcessor "ru.tinkoff.kora:annotation-processors"

        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation project(":guide-dependency-injection:guide-dependency-injection-lib")
        implementation project(":guide-dependency-injection:guide-dependency-injection-submodule")
        implementation "ru.tinkoff.kora:config-hocon"
        implementation "ru.tinkoff.kora:logging-logback"

        testAnnotationProcessor "ru.tinkoff.kora:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        ksp("ru.tinkoff.kora:symbol-processors")

        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-lib"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-submodule"))
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:logging-logback")

        testImplementation(platform("org.junit:junit-bom:$junitVersion"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

**Создайте MessengerModule** (`guide-dependency-injection/guide-dependency-injection-submodule/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/messenger/`
или `guide-dependency-injection/guide-dependency-injection-submodule/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/messenger/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.messenger;

    import ru.tinkoff.kora.common.KoraSubmodule;

    @KoraSubmodule
    public interface MessengerModule {

        final class MessengerTag {
            private MessengerTag() {}
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.messenger

    import ru.tinkoff.kora.common.KoraSubmodule

    @KoraSubmodule
    interface MessengerModule {
        class MessengerTag
    }
    ```

**Создайте интерфейс Messenger**:

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.messenger;

    public interface Messenger {
        void sendMessage(String message);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.messenger

    interface Messenger {
        fun sendMessage(message: String)
    }
    ```

**Создайте SlackMessenger**:

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.messenger.slack;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.dependencyinjection.messenger.Messenger;

    @Tag(SlackMessenger.class)
    @Component
    public final class SlackMessenger implements Messenger {

        @Override
        public void sendMessage(String message) {
            System.out.println("Slack: " + message);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.messenger.slack

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.dependencyinjection.messenger.Messenger

    @Tag(SlackMessenger::class)
    @Component
    class SlackMessenger : Messenger {
        override fun sendMessage(message: String) {
            println("Slack: $message")
        }
    }
    ```

**Создайте MessengerNotifier**:

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.messenger;

    import ru.tinkoff.kora.application.graph.All;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.dependencyinjection.common.Notifier;

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
    package ru.tinkoff.kora.guide.dependencyinjection.messenger

    import ru.tinkoff.kora.application.graph.All
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.dependencyinjection.common.Notifier

    @Tag(MessengerModule.MessengerTag::class)
    @Component
    class MessengerNotifier(
        @Tag(Tag.Any::class) private val messengers: All<Messenger>
    ) : Notifier {

        override fun notify(user: String, message: String) {
            println("Broadcasting to messengers")
            messengers.forEach { it.sendMessage("$user@$message") }
            println("Messenger broadcast complete")
        }
    }
    ```

**Обновите Application**, чтобы подключить подмодуль отправителей. `MessengerModule` помечен `@KoraSubmodule`, поэтому здесь наследование ожидаемо:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule,  // <----- Подключили модуль
            SmsCellularModule,  // <----- Подключили модуль
            MessengerModule {  // <----- Подключили модуль
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
        EmailModule,  // <----- Подключили модуль
        SmsCellularModule,  // <----- Подключили модуль
        MessengerModule {  // <----- Подключили модуль
        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

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
разделам [Внедрение зависимостей с Kora: обобщенная фабрика](dependency-injection-introduction.md#generic-factory)
и [документация контейнера: обобщенная фабрика](../documentation/container.md#generic-factory).

**Что мы имитируем**: инфраструктурный код, который может сохранять разные формы полезной нагрузки с помощью одного переиспользуемого шаблона хранилища, а Kora автоматически выбирает нужную обобщенную
конкретизацию.

**Создайте интерфейс Storage** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/storage/`
или `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/storage/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.storage;

    public interface Storage<T> {
        void save(T data);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.storage

    interface Storage<T> {
        fun save(data: T)
    }
    ```

**Создайте TempFileStorage**:

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.storage;

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
    package ru.tinkoff.kora.guide.dependencyinjection.storage

    import java.io.IOException
    import java.nio.file.Files

    class TempFileStorage<T>(
        private val mapper: (T) -> ByteArray
    ) : Storage<T> {

        override fun save(data: T) {
            try {
                val tempFile = Files.createTempFile("storage-", ".tmp")
                Files.write(tempFile, mapper(data))
                println("Saved to: ${tempFile.fileName}")
            } catch (e: IOException) {
                throw RuntimeException(e)
            }
        }
    }
    ```

**Создайте StorageModule**:

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.storage;

    import java.nio.charset.StandardCharsets;
    import java.util.function.Function;
    import ru.tinkoff.kora.common.Module;

    @Module
    public interface StorageModule {

        default Function<Integer, byte[]> intMapper() {
            return i -> new byte[] {i.byteValue()};
        }

        default Function<String, byte[]> stringMapper() {
            return s -> s.getBytes(StandardCharsets.UTF_8);
        }

        default <T> Storage<T> typedStorage(Function<T, byte[]> mapper) {
            return new TempFileStorage<>(mapper);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.storage

    import ru.tinkoff.kora.common.Module
    import java.nio.charset.StandardCharsets

    @Module
    interface StorageModule {
        fun intMapper(): (Int) -> ByteArray {
            return { i -> byteArrayOf(i.toByte()) }
        }

        fun stringMapper(): (String) -> ByteArray {
            return { s -> s.toByteArray(StandardCharsets.UTF_8) }
        }

        fun <T> typedStorage(mapper: (T) -> ByteArray): Storage<T> {
            return TempFileStorage(mapper)
        }
    }
    ```

**Примечание о приложении**: здесь не нужно менять `Application`. `StorageModule` находится в пакете приложения, поэтому Kora автоматически обнаруживает его как модуль приложения.

**Обновите NotifyRunner**, чтобы использовать `Storage<String>`:

===! ":fontawesome-brands-java: Java"

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
            allNotifiers.forEach { it.notify("Charlie", "Greetings!") }
            stringStorage.save("User data stored")
        }
    }
    ```

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

---

### Управление обновлением { #update-management }

**Цель**: показать `ValueOf<T>` для предотвращения нежелательных каскадных обновлений, когда зависимости обновляются.

**Что вводит этот шаг**: `ValueOf<T>`, `Wrapped<T>` и `LifecycleWrapper` для зависимостей, которые учитывают жизненный цикл и доступны через косвенную ссылку. `ActivityService` остается стабильным,
а `ActivityRecorder` остается доступным отложенно и при этом управляется жизненным циклом.

**Зачем это нужно**: некоторые инфраструктурные зависимости дороги в создании или могут обновляться, и мы не хотим пересоздавать каждого потребителя только потому, что такая зависимость изменилась.
Это соответствует разделам [Внедрение зависимостей с Kora: ValueOf](dependency-injection-introduction.md#valueof)
и [документация контейнера: жизненный цикл компонента](../documentation/container.md#component-lifecycle).

**Что мы имитируем**: службу, которая записывает активность через управляемый соединитель, способный запускаться, останавливаться или обновляться независимо от бизнес-службы, которая его использует.

**Создайте интерфейс ActivityRecorder** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/activity/`
или `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/activity/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.activity;

    public interface ActivityRecorder {

        void connect();

        void disconnect();

        boolean isConnected();

        void recordUser(String user);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.activity

    interface ActivityRecorder {
        fun connect()
        fun disconnect()
        fun isConnected(): Boolean
        fun recordUser(user: String)
    }
    ```

**Создайте ActivityService**:

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.activity;

    import ru.tinkoff.kora.application.graph.ValueOf;
    import ru.tinkoff.kora.common.Component;

    @Component
    public final class ActivityService {

        private final ValueOf<ActivityRecorder> activityRecorder;

        public ActivityService(ValueOf<ActivityRecorder> activityRecorder) {
            this.activityRecorder = activityRecorder;
            System.out.println("ActivityService created (ActivityRecorder not yet accessed)");
        }

        public void recordActivityByUserName(String user) {
            System.out.println("Recording activity for: " + user);
            ActivityRecorder recorder = activityRecorder.get();
            recorder.recordUser(user);
            System.out.println("Activity recorded successfully");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.activity

    import ru.tinkoff.kora.application.graph.ValueOf
    import ru.tinkoff.kora.common.Component

    @Component
    class ActivityService(
        private val activityRecorder: ValueOf<ActivityRecorder>
    ) {

        init {
            println("ActivityService created (ActivityRecorder not yet accessed)")
        }

        fun recordActivityByUserName(user: String) {
            println("Recording activity for: $user")
            val recorder = activityRecorder.get()
            recorder.recordUser(user)
            println("Activity recorded successfully")
        }
    }
    ```

**Создайте ActivityModule**:

===! ":fontawesome-brands-java: Java"

    ```java
    package ru.tinkoff.kora.guide.dependencyinjection.activity;

    import ru.tinkoff.kora.application.graph.LifecycleWrapper;
    import ru.tinkoff.kora.application.graph.Wrapped;
    import ru.tinkoff.kora.common.Module;

    @Module
    public interface ActivityModule {

        default Wrapped<ActivityRecorder> activityRecorder() {
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

            return new LifecycleWrapper<>(recorder, r -> {}, ActivityRecorder::disconnect);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.activity

    import ru.tinkoff.kora.application.graph.LifecycleWrapper
    import ru.tinkoff.kora.application.graph.Wrapped
    import ru.tinkoff.kora.common.Module

    @Module
    interface ActivityModule {
        fun activityRecorder(): Wrapped<ActivityRecorder> {
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

                override fun isConnected(): Boolean {
                    return connected
                }

                override fun recordUser(user: String) {
                    if (!connected) connect()
                    println("Recording user activity: $user")
                }
            }

            return LifecycleWrapper(recorder, {}, ActivityRecorder::disconnect)
        }
    }
    ```

**Примечание о приложении**: здесь тоже не требуется менять `Application`. `ActivityModule` также обнаруживается как модуль приложения из пакета приложения.

**Обновите NotifyRunner**, чтобы показать финальный сценарий:

===! ":fontawesome-brands-java: Java"

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
            allNotifiers.forEach { it.notify("Diana", "Welcome to Kora DI!") }
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

**Ключевое понятие**: `ValueOf<T>` предотвращает каскадные обновления компонентов. Экземпляр `ActivityService` остается стабильным, но все равно может отложенно получить текущий `ActivityRecorder`,
когда это нужно.

---

## Итоги руководства { #guide-summary }

Вы создали полноценное приложение Kora, которое демонстрирует все основные понятия внедрения зависимостей:

1. **Структура проекта** - многомодульная организация
2. **Внешние модули** - библиотечные компоненты с `@DefaultComponent`
3. **Переопределение компонента** - настройка библиотечных значений по умолчанию
4. **Зависимости с тегами** - несколько реализаций с `@Tag` и `All<T>`
5. **Допускающие `null` зависимости** - `@Nullable` / nullable-типы для аккуратной деградации
6. **Подмодули** - `@KoraSubmodule` для организации компонентов
7. **Обобщенные фабрики** - параметризованное `<T>` создание компонентов
8. **Предотвращение каскадных обновлений** - `ValueOf<T>` для управления поведением обновления компонентов

Каждый шаг опирается на предыдущий и показывает, как DI Kora во время компиляции помогает создавать чистые, модульные и производительные приложения.

## Лучшие практики { #best-practices }

- Держите компоненты небольшими и сфокусированными на одной ответственности.
- Предпочитайте внедрение через конструктор и явные границы модулей.
- Используйте теги только тогда, когда несколько реализаций действительно должны сосуществовать.
- Держите необязательные зависимости явными с помощью nullable-типов или `@Nullable`.
- Используйте `ValueOf<T>`, когда нужно управляемое поведение обновления компонентов.

## Итоги { #summary }

Поздравляем! Вы завершили подробное руководство по внедрению зависимостей Kora. Вы изучили не только *как* использовать внедрение зависимостей, но и *почему* это настолько мощный шаблон для
создания сопровождаемого программного обеспечения.

В руководстве разобраны основные элементы графа Kora: `@KoraApp`, `@Component`, `@Module`, внешние модули, `@DefaultComponent`, теги, `All<T>`, nullable-зависимости, подмодули, обобщенные фабрики и
`ValueOf<T>`. Вместе они показывают, как собирать приложение из небольших явных частей и при этом сохранять типобезопасное разрешение зависимостей во время компиляции.

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

Распространенные проблемы и решения:

Циклические зависимости:

Проблема: два или больше компонентов зависят друг от друга напрямую или косвенно.

Признаки:

- ошибка во время компиляции: "Circular dependency detected"
- обработчик аннотаций завершается ошибкой разрешения зависимостей

Решения:

1. Переработайте код через разделение интерфейсов:

===! ":fontawesome-brands-java: Java"

    ```java
    // Вместо циклической зависимости
    @Component
    class ServiceA { ServiceA(ServiceB b) {} }

    @Component
    class ServiceB { ServiceB(ServiceA a) {} }

    // Используйте интерфейсы
    interface ServiceAInterface { void methodA(); }
    interface ServiceBInterface { void methodB(); }

    @Component
    class AImpl implements ServiceAInterface { AImpl(ServiceBInterface b) {} }

    @Component
    class BImpl implements ServiceBInterface { BImpl(ServiceAInterface a) {} }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Вместо циклической зависимости
    @Component
    class ServiceA(val b: ServiceB)

    @Component
    class ServiceB(val a: ServiceA)

    // Используйте интерфейсы
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

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface ServiceModule {
        default ServiceA serviceA(ValueOf<ServiceB> serviceB) {
            // ServiceA не зависит напрямую от жизненного цикла ServiceB
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
            // ServiceA не зависит напрямую от жизненного цикла ServiceB
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

- ошибка во время компиляции: "No component found for type X"
- понятное сообщение об ошибке с цепочкой зависимостей

Решения:

1. Добавьте отсутствующий компонент:

===! ":fontawesome-brands-java: Java"

    ```java
    // Добавьте отсутствующий компонент
    @Component
    public final class MissingDependency {
        // Реализация
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Добавьте отсутствующий компонент
    @Component
    class MissingDependency {
        // Реализация
    }
    ```

2. Создайте фабричный метод:

===! ":fontawesome-brands-java: Java"

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

- ошибка во время выполнения: "Configuration value not found"
- `NullPointerException` при обращении к свойствам конфигурации

Решения:

1. Добавьте модуль конфигурации:

===! ":fontawesome-brands-java: Java"

    ```java
    // Подключите модуль конфигурации
    @KoraApp
    public interface Application extends HoconConfigModule {
        // Теперь конфигурация доступна
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Подключите модуль конфигурации
    @KoraApp
    interface Application : HoconConfigModule {
        // Теперь конфигурация доступна
    }
    ```

2. Проверьте имена свойств:

===! ":fontawesome-brands-java: Java"

    ```java
    // Убедитесь, что имена свойств совпадают
    @Component
    public final class DatabaseConfig {
        private final Config config;

        public DatabaseConfig(Config config) {
            this.config = config;
        }

        public String getUrl() {
            // Проверьте, что свойство существует в конфигурации
            return config.getString("db.url");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Убедитесь, что имена свойств совпадают
    @Component
    class DatabaseConfig(
        private val config: Config
    ) {

        fun getUrl(): String {
            // Проверьте, что свойство существует в конфигурации
            return config.getString("db.url")
        }
    }
    ```

Проблемы с разрешением тегов:

Проблема: зависимости с тегами не удается разрешить.

Признаки:

- ошибка компиляции: "Multiple components found for type X"
- или: "No component found for tagged type X"

Решения:

1. Используйте правильную аннотацию тега:

===! ":fontawesome-brands-java: Java"

    ```java
    // Правильное использование тега
    @Component
    public final class MyService {
        public MyService(@Tag(MyTag.class) Dependency dep) {
            // Правильно
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Правильное использование тега
    @Component
    class MyService(
        @Tag(MyTag::class) val dep: Dependency
    ) {
        // Правильно
    }
    ```

2. Проверьте определение класса тега:

===! ":fontawesome-brands-java: Java"

    ```java
    // Класс тега должен быть public
    public final class MyTag {} // Правильно

    // Закрытый тег не сработает
    private final class MyTag {} // Неправильно
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Класс тега должен быть public
    class MyTag // Правильно (public по умолчанию)

    // Закрытый тег не сработает
    private class MyTag // Неправильно
    ```

Проблемы с подключением модулей:

Проблема: компоненты из модулей недоступны.

Признаки:

- ошибка компиляции: "No component found for type from module"

Решения:

1. Подключите модуль в приложении:

===! ":fontawesome-brands-java: Java"

    ```java
    // Подключите модуль
    @KoraApp
    public interface Application extends MyModule {  // <----- Подключили модуль
        // Компоненты из MyModule теперь доступны
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Подключите модуль
    @KoraApp
    interface Application : MyModule {  // <----- Подключили модуль
        // Компоненты из MyModule теперь доступны
    }
    ```

2. Проверьте видимость модуля:

===! ":fontawesome-brands-java: Java"

    ```java
    // Методы модуля должны быть public
    @Module
    public interface MyModule {
        @Component
        default MyComponent myComponent() { // public по умолчанию
            return new MyComponent();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Методы модуля должны быть public
    @Module
    interface MyModule {
        @Component
        fun myComponent(): MyComponent { // public по умолчанию
            return MyComponent()
        }
    }
    ```

Проблемы с внедрением коллекций:

Проблема: `All<T>` не внедряет ожидаемые компоненты.

Признаки:

- пустая коллекция, хотя ожидались несколько реализаций
- в `All<T>` отсутствуют ожидаемые компоненты

Решения:

1. Убедитесь, что все реализации являются компонентами:

===! ":fontawesome-brands-java: Java"

    ```java
    // Все реализации должны быть @Component
    @Component
    public final class Impl1 implements MyInterface {}

    @Component
    public final class Impl2 implements MyInterface {}

    // Теперь All<MyInterface> будет содержать обе
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Все реализации должны быть @Component
    @Component
    class Impl1 : MyInterface

    @Component
    class Impl2 : MyInterface

    // Теперь All<MyInterface> будет содержать обе
    ```

2. Проверьте конфликты тегов:

===! ":fontawesome-brands-java: Java"

    ```java
    // Если используете теги, убедитесь, что случайно не фильтруете лишнее
    @Component
    public final class MyService {
        public MyService(All<MyInterface> all) { // Получает все реализации
            // ...
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Если используете теги, убедитесь, что случайно не фильтруете лишнее
    @Component
    class MyService(
        val all: All<MyInterface> // Получает все реализации
    ) {
        // ...
    }
    ```

Проблемы с необязательными зависимостями:

Проблема: необязательные зависимости ведут себя неожиданно.

Признаки:

- `Optional` пуст, хотя ожидалось значение
- `NullPointerException` при использовании необязательной зависимости

Решения:

1. Правильно обрабатывайте `Optional`:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class MyService {
        private final @Nullable Dependency optionalDep;

        public MyService(@Nullable Dependency optionalDep) {
            this.optionalDep = optionalDep;
        }

        public void doSomething() {
            // Безопасное использование nullable-значения
            if (optionalDep != null) { optionalDep.doWork(); }

            // Опасно — может вызвать NPE
            // optionalDep.doWork(); // Не делайте так без проверки на null
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
            // Безопасное использование nullable-значения
            optionalDep?.doWork()

            // Опасно — может вызвать NPE
            // optionalDep.work() // Не делайте так без проверки на null
        }
    }
    ```

2. Убедитесь, что nullable-компонент существует:

===! ":fontawesome-brands-java: Java"

    ```java
    // Если хотите, чтобы nullable-зависимость была доступна, подключите модуль ее поставщика
    @KoraApp
    public interface Application extends NullableModule {  // <----- Подключили модуль
        // Подключите модуль, который предоставляет необязательную зависимость
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Если хотите, чтобы nullable-зависимость была доступна, подключите модуль ее поставщика
    @KoraApp
    interface Application : NullableModule {  // <----- Подключили модуль
        // Подключите модуль, который предоставляет необязательную зависимость
    }
    ```

Проблемы с жизненным циклом:

Проблема: компоненты с методами жизненного цикла не запускаются или не останавливаются правильно.

Признаки:

- методы `init()` или `destroy()` не вызываются
- ресурсы не освобождаются должным образом

Решения:

1. Реализуйте интерфейс `Lifecycle`:

===! ":fontawesome-brands-java: Java"

    ```java
    import ru.tinkoff.kora.common.Lifecycle;

    @Component
    public final class MyService implements Lifecycle {
        @Override
        public void init() throws Exception {
            // Инициализируйте ресурсы здесь
        }

        @Override
        public void destroy() throws Exception {
            // Освободите ресурсы здесь
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import ru.tinkoff.kora.common.Lifecycle

    @Component
    class MyService : Lifecycle {
        override fun init() {
            // Инициализируйте ресурсы здесь
        }

        override fun destroy() {
            // Освободите ресурсы здесь
        }
    }
    ```

2. Проверьте регистрацию компонента:

===! ":fontawesome-brands-java: Java"

    ```java
    // Убедитесь, что компонент правильно зарегистрирован в модуле
    @Module
    public interface MyModule {
        @Component
        default MyService myService() {
            return new MyService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Убедитесь, что компонент правильно зарегистрирован в модуле
    @Module
    interface MyModule {
        @Component
        fun myService(): MyService {
            return MyService()
        }
    }
    ```

Проблемы с обобщенными типами:

Проблема: обобщенные компоненты (`<T>`) не разрешаются корректно.

Признаки:

- ошибка компиляции: "Generic type cannot be resolved"
- внедрен неверный обобщенный тип

Решения:

1. Используйте правильные ограничения обобщенных типов:

===! ":fontawesome-brands-java: Java"

    ```java
    // Укажите обобщенный тип явно
    @Component
    public final class StringStorage implements Storage<String> {}

    @Component
    public final class MyService {
        public MyService(Storage<String> storage) { // Укажите тип
            // Правильно
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Укажите обобщенный тип явно
    @Component
    class StringStorage : Storage<String>

    @Component
    class MyService(
        val storage: Storage<String> // Укажите тип
    ) {
        // Правильно
    }
    ```

2. Проверьте обобщенные фабричные методы:

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface StorageModule {
        @Component
        default <T> Storage<T> storage(Class<T> type) {
            return new InMemoryStorage<>(); // Обобщенная фабрика
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface StorageModule {
        @Component
        fun <T> storage(type: Class<T>): Storage<T> {
            return InMemoryStorage() // Обобщенная фабрика
        }
    }
    ```

Проблемы сборки и компиляции:

Проблема: обработчик аннотаций Kora завершается ошибкой или создает некорректный код.

Признаки:

- ошибки компиляции в сгенерированном коде
- ошибки "Annotation processor not found"
- проблемы в сгенерированных классах

Решения:

1. Проверьте зависимости:

===! ":fontawesome-brands-java: Java"

    ```java
    // Убедитесь, что зависимости Kora подключены
    dependencies {
        implementation "ru.tinkoff.kora:kora-app-annotation-processor"
        implementation "ru.tinkoff.kora:config-hocon"
        // Другие модули Kora...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Убедитесь, что зависимости Kora подключены
    dependencies {
        implementation("ru.tinkoff.kora:kora-app-annotation-processor")
        implementation("ru.tinkoff.kora:config-hocon")
        // Другие модули Kora...
    }
    ```

2. Сделайте чистую сборку:

===! ":fontawesome-brands-java: Java"

    ```bash
    # Очистите и соберите заново
    ./gradlew clean classes
    ```

=== ":simple-kotlin: `Kotlin`"

    ```bash
    # Очистите и соберите заново
    ./gradlew clean classes
    ```

3. Проверьте версию Java:

===! ":fontawesome-brands-java: Java"

    ```java
    // Убедитесь, что используете поддерживаемую версию Java (11, 17, 21)
    java --version
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Убедитесь, что используете поддерживаемую версию Java (11, 17, 21)
    java --version
    ```

Проблемы с тестированием:

Проблема: компоненты сложно тестировать или тесты неожиданно падают.

Признаки:

- сложно внедрять подмены
- тестовые зависимости не разрешаются
- падают интеграционные тесты

Решения:

1. Используйте внедрение через конструктор для удобства тестирования:

===! ":fontawesome-brands-java: Java"

    ```java
    // Тестируемый компонент
    @Component
    public final class UserService {
        private final UserRepository repository;

        public UserService(UserRepository repository) {
            this.repository = repository;
        }
    }

    // Тест
    @Test
    public void testUserService() {
        UserRepository mockRepo = mock(UserRepository.class);
        UserService service = new UserService(mockRepo);
        // Тест...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Тестируемый компонент
    @Component
    class UserService(
        private val repository: UserRepository
    )

    // Тест
    @Test
    fun testUserService() {
        val mockRepo = mock(UserRepository::class.java)
        val service = UserService(mockRepo)
        // Тест...
    }
    ```

2. Используйте Testcontainers для интеграционных тестов:

===! ":fontawesome-brands-java: Java"

    ```java
    @Testcontainers
    public class UserServiceIntegrationTest {
        @Container
        private static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17.6-alpine");

        @Test
        public void testRealDatabase() {
            // Тест с настоящей базой данных
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Testcontainers
    class UserServiceIntegrationTest {
        @Container
        private val postgres = PostgreSQLContainer("postgres:17.6-alpine")

        @Test
        fun testRealDatabase() {
            // Тест с настоящей базой данных
        }
    }
    ```

Распространенные ошибки новичков:

1. Забыли аннотацию @Component:

===! ":fontawesome-brands-java: Java"

    ```java
    // Нет @Component
    public final class MyService {
        // Этот класс не будет обнаружен DI
    }

    // Правильно
    @Component
    public final class MyService {
        // Теперь обнаруживается
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Нет @Component
    class MyService {
        // Этот класс не будет обнаружен DI
    }

    // Правильно
    @Component
    class MyService {
        // Теперь обнаруживается
    }
    ```

2. Закрытый конструктор:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class MyService {
        private MyService() {} // Неправильно: закрытый конструктор блокирует DI
    }

    // Public или package-private конструктор
    @Component
    public final class MyService {
        public MyService() {} // Правильно
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService private constructor() // Неправильно: закрытый конструктор блокирует DI

    // Public-конструктор (по умолчанию)
    @Component
    class MyService // Правильно
    ```

3. Не подключили модули:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application {
        // Компоненты из модулей не подключены
    }

    @KoraApp
    public interface Application extends MyModule {  // <----- Подключили модуль
        // Компоненты модуля теперь доступны
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {
        // Компоненты из модулей не подключены
    }

    @KoraApp
    interface Application : MyModule {  // <----- Подключили модуль
        // Компоненты модуля теперь доступны
    }
    ```

4. Циклические зависимости:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    class A { A(B b) {} }

    @Component
    class B { B(A a) {} } // Неправильно: циклическая зависимость

    // Разорвите цикл с помощью интерфейсов или переработки структуры
    interface AInterface {}
    interface BInterface {}

    @Component
    class AImpl implements AInterface { AImpl(BInterface b) {} }

    @Component
    class BImpl implements ServiceBInterface { BImpl(ServiceAInterface a) {} }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class A(val b: B)

    @Component
    class B(val a: A) // Неправильно: циклическая зависимость

    // Разорвите цикл с помощью интерфейсов или переработки структуры
    interface AInterface
    interface BInterface

    @Component
    class AImpl(val b: BInterface) : AInterface

    @Component
    class BImpl(val a: AInterface) : BInterface
    ```

5. Игнорирование nullable-результатов:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class MyService {
        private final @Nullable Dependency dep;

        public MyService(@Nullable Dependency dep) {
            this.dep = dep;
        }

        public void doSomething() {
            dep.work(); // Неправильно: может выбросить NullPointerException
        }
    }

    // Безопасное использование
    public void doSomething() {
        if (dep != null) dep.work(); // Безопасно
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(
        private val dep: Dependency?
    ) {

        fun doSomething() {
            dep!!.work() // Неправильно: может выбросить NullPointerException
        }
    }

    // Безопасное использование
    fun doSomething() {
        dep?.work() // Безопасно
    }
    ```

Как получить помощь:

Если вы все еще не можете разобраться:

1. Проверьте примеры: посмотрите `kora-examples`, чтобы увидеть рабочие шаблоны
2. Прочитайте документацию: обратитесь к `kora-docs` за подробными объяснениями
3. Упростите: уберите сложность и проверьте минимальные компоненты
4. Сообщество: задайте вопросы в каналах сообщества Kora

Помните: большинство проблем DI возникают из-за отсутствующих компонентов, неправильного подключения модулей или циклических зависимостей. Начинайте с простого и постепенно наращивайте сложность!

## Что дальше? { #whats-next }

- [Создайте первое приложение Kora](getting-started.md), если вы прошли руководство только по DI до создания запускаемого HTTP-приложения.
- [Конфигурация с HOCON](config-hocon.md) или [конфигурация с YAML](config-yaml.md) после начального руководства, чтобы узнать, как типизированная конфигурация попадает в граф.
- [Работа с JSON](json.md) после начального руководства, чтобы подготовить DTO запросов и ответов перед полноценным руководством по HTTP-серверу.

## Помощь { #help }

Если возникли проблемы:

- проверьте [документацию контейнера](../documentation/container.md)
- сравните с [Kora Java Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection-app) и [Kora Kotlin Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-dependency-injection-app)
- запустите `./gradlew clean classes` и изучите ошибки сгенерированного графа перед изменением структуры кода
- убедитесь, что компоненты помечены `@Component` или предоставляются модулем
