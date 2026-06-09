---
search:
  exclude: true
title: Создание первого приложения на Kora
summary: Learn how to create a minimal Kora HTTP application and run your first endpoint
tags: getting-started, http-server, quick-start
---

# Создание первого приложения на Kora { #building-your-first-kora }

В этом руководстве мы соберем минимальное, но уже полезное HTTP-приложение на Kora. Вы увидите, как модуль с `@KoraApp` запускает граф зависимостей, который строится на этапе компиляции,
как `@Component` и `@HttpController` регистрируют код приложения, и как один метод с `@HttpRoute` превращается в рабочий HTTP-маршрут. Также разберем, какие части Gradle-сборки, модулей Kora и
конфигурации нужны, чтобы приложение скомпилировалось и запустилось.

Относитесь к этому руководству как к экскурсии по минимальной форме сервиса на Kora. Все следующие руководства будут добавлять новые возможности, но базовые идеи останутся теми же: явно объявлять
зависимости, позволять Kora генерировать граф на этапе компиляции, держать инфраструктуру в модулях фреймворка, а поведение приложения — в ваших компонентах.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Getting Started App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-getting-started-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Getting Started App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-getting-started-app).

## Что вы создадите { #youll-build }

Вы создадите небольшой веб-сервис, который возвращает `Hello, Kora!` по адресу `http://localhost:8080/hello`.

Пример выглядит маленьким, но в нем уже есть те же архитектурные части, что и в более крупном сервисе:

- Gradle-сборка с включенной генерацией кода Kora
- корневой `@KoraApp`, который определяет граф приложения
- модули фреймворка для конфигурации, логирования, JSON и HTTP-сервера
- компонент-контроллер, который публикует HTTP-маршрут
- файл `application.conf`, который настраивает порты и логирование
- сгенерированный исходный код, в котором видно, как Kora связывает приложение

Сам маршрут намеренно простой, чтобы не отвлекаться на бизнес-логику и сосредоточиться на механике фреймворка.

## Что потребуется { #youll-need }

- JDK 17 или новее
- Gradle 7+
- Текстовый редактор или среда разработки
- Базовое умение читать Java- или Kotlin-код

Docker, база данных и внешние сервисы для этого руководства не нужны. Все запускается в одном процессе на вашей машине, поэтому это хороший первый шаг перед добавлением реальной инфраструктуры.

## Требования { #prerequisites }

!!! note "Предыдущие руководства по Kora не требуются"

    Это руководство является отправной точкой для всего учебного пути и не предполагает, что у вас уже есть готовый проект на Kora.

    Рекомендуется прочитать **[Введение во внедрение зависимостей в Kora](dependency-injection-introduction.md)** либо до этого руководства, либо сразу после него, потому что внедрение зависимостей, граф приложения, компоненты и модули лежат в основе любого приложения на Kora.

    Также необходимы навыки базового знакомства с Java или Kotlin.

## Обзор { #overview }

Это руководство показывает самый маленький полезный вход в приложение на Kora. Цель не только в том, чтобы вернуть `Hello, Kora!`, а в том, чтобы показать базовую форму, которую сохраняет любой более
крупный сервис на Kora.

Мы намеренно начинаем с одного маршрута, потому что в минимальном приложении хорошо видна основная модель Kora: модуль фреймворка предоставляет инфраструктуру, ваш компонент описывает поведение
приложения, а сгенерированный граф связывает эти части вместе.

Полезная модель мышления такая: Kora не прячет структуру приложения. Вы пишете обычные классы и интерфейсы, аннотациями отмечаете границы, которые должны стать частью графа, а Kora превращает эти
объявления в сгенерированный код. По ощущению это близко к ручному связыванию зависимостей, только без шаблонного кода и с проверкой на этапе компиляции.

### Граф приложения { #application-graph }

Приложения Kora начинаются с графа зависимостей. Интерфейс `@KoraApp` является корнем этого графа: он сообщает Kora, какие модули входят в приложение и какие компоненты должны быть связаны между
собой. Во время компиляции Kora генерирует код графа, который умеет создавать, соединять, запускать и останавливать компоненты. Каждый узел графа — это компонент, а каждое ребро — зависимость одного
компонента от другого. Если контроллеру нужен сервис, а репозиторию нужна база данных, такие связи становятся частью графа.

Это отличается от фреймворков с внедрением зависимостей во время выполнения, которые сканируют classpath при запуске приложения. Kora выполняет основную работу во время компиляции, поэтому многие
ошибки связывания обнаруживаются еще до того, как приложение сможет запуститься. Поэтому обычная задача `classes` в Kora уже является важной проверкой: она проверяет не только синтаксис Java/Kotlin,
но и возможность построить граф приложения.

### Компоненты и модули { #components-modules }

`@Component` — это объект, который Kora может создать и управлять им. Модуль добавляет фабрики компонентов или возможности фреймворка. В этом первом руководстве главная возможность фреймворка — модуль
HTTP-сервера Undertow. Он предоставляет серверную инфраструктуру, а ваш контроллер описывает поведение приложения.

В проектах на Kora вы будете встречать два вида модулей. Модули фреймворка, например `UndertowHttpServerModule`, дают готовую инфраструктуру. Прикладные модули — это ваши интерфейсы или классы,
которые предоставляют фабрики для доменных компонентов. В этом руководстве используются только модули фреймворка, а дальше вы увидите, как приложение разделяется на сервисы, репозитории, клиенты, кэши
и другие компоненты.

Такое разделение будет встречаться во всех руководствах:

- модули фреймворка предоставляют инфраструктуру
- ваши компоненты описывают поведение приложения
- сгенерированный граф связывает обе стороны

### HTTP как точка входа { #http-entry-point }

`HelloController` намеренно сделан маленьким, но он показывает ту же модель HTTP-сервера, которая используется в более крупных API. `@HttpController` помечает класс как содержащий маршруты,
а `@HttpRoute` связывает один метод с HTTP-методом и путем. Тело метода при этом остается обычным Java- или Kotlin-кодом. Kora не заставляет наследоваться от специального базового класса и не
превращает контроллер в прокси-объект во время выполнения. Аннотации описывают, как метод должен быть опубликован по HTTP, а реализация метода остается обычным кодом приложения.

К концу руководства вы должны понимать минимальный набор движущихся частей сервиса на Kora: зависимости [Gradle](https://docs.gradle.org/current/userguide/userguide.html), граф приложения, модуль
фреймворка, один компонент и один маршрут, опубликованный через HTTP-сервер [Undertow](https://undertow.io/undertow-docs/undertow-docs-2.3.0/index.html).

Практический порядок такой:

1. создать Gradle-проект
2. добавить зависимости Kora для HTTP-сервера
3. определить корень графа `@KoraApp`
4. добавить один `@HttpController`
5. запустить приложение и вызвать маршрут

## Шаблон сервиса { #service-template }

Если нужен самый быстрый старт, используйте официальные шаблоны:

===! ":fontawesome-brands-java: Java Template"

    ```bash
    git clone https://github.com/kora-projects/kora-java-template.git kora-guide-example
    cd kora-guide-example
    ```

=== ":simple-kotlin: Kotlin Template"

    ```bash
    git clone https://github.com/kora-projects/kora-kotlin-template.git kora-guide-example
    cd kora-guide-example
    ```

Шаблон удобен, когда нужно быстро получить рабочий проект и сразу перейти к бизнес-логике. Ручная сборка ниже полезнее для первого знакомства: она показывает, какие Gradle-плагины нужны, какие модули
Kora подключаются в корневой граф, где лежит конфигурация и какой минимальный код действительно требуется для запуска HTTP-приложения.

Если вы хотите лучше понять детали настройки, продолжайте ручную сборку ниже.

## Установите JDK { #install-jdk }

Перед Gradle нужен установленный JDK: именно JVM запускает Gradle Wrapper, компилятор Java и инструменты сборки. Для первого запуска поставьте Eclipse Temurin JDK 21: этого достаточно, чтобы запустить
Gradle, а дальше Gradle-инструменты сможет автоматически скачать JDK, которая нужна конкретной сборке.

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

В выводе должна быть версия Java 21. После этого можно создавать каталог проекта.

## Каталог проекта { #project-directory }

Сначала создайте пустой каталог будущего приложения и перейдите в него. Все следующие команды в руководстве выполняются из этого каталога:

```bash
mkdir kora-guide-example
cd kora-guide-example
```

## Настройка Gradle { #gradle-setup }

Начнем с обычного Gradle-проекта. На этом этапе в нем еще нет ничего специфичного для Kora: мы только создаем стандартную структуру каталогов, выбираем язык, тестовый фреймворк и пакет приложения. Это
важно, потому что Kora не требует специального генератора проекта: приложение остается обычным Java- или Kotlin-проектом, который Gradle умеет собирать стандартными задачами.

Дальше Gradle будет компилировать код приложения и запускать обработчики аннотаций или KSP-процессоры Kora, которые сгенерируют граф приложения.

Используйте начальную подготовку Gradle Wrapper для всех вариантов установки. Так путь настройки остается одинаковым для всех читателей: сначала создаем минимальные файлы wrapper в текущем каталоге,
затем запускаем `init` через `GradleWrapperMain`. Для этого нужна только JDK из предыдущей главы.

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

Шаг 3. Инициализируйте проект через wrapper.

===! ":fontawesome-brands-java: `Java`"

    ```bash
    java -cp gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain init \
      --type java-application \
      --dsl groovy \
      --test-framework junit-jupiter \
      --package ru.tinkoff.kora.guide.gettingstarted \
      --project-name kora-example \
      --java-version 24
    ```

=== ":simple-kotlin: `Kotlin`"

    ```bash
    java -cp gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain init \
      --type kotlin-application \
      --dsl kotlin \
      --test-framework junit-jupiter \
      --package ru.tinkoff.kora.guide.gettingstarted \
      --project-name kora-example \
      --java-version 24
    ```

## Зависимости { #dependencies }

Теперь добавим минимальный набор Gradle-настроек, который превращает обычный Gradle-проект в Kora-приложение. Не будем вставлять весь `build.gradle` одним большим фрагментом: полезнее собрать его по частям и сразу понять, какую роль играет каждая часть.

В этом разделе Gradle должен сделать несколько вещей:

- выбрать JDK, которым компилируется приложение
- включить обычную сборку приложения и запуск через `gradlew run`
- подключить Kora BOM, чтобы все модули Kora использовали согласованные версии
- включить генерацию кода Kora на этапе компиляции
- добавить модули HTTP-сервера, конфигурации, JSON и логирования

### Поиск JDK для сборки { #toolchain }

Сначала обновите `settings.gradle`. Плагин `foojay-resolver-convention` помогает Gradle найти или скачать JDK, который указан в toolchain. Без него Gradle может использовать только уже установленные JDK и сборка станет сильнее зависеть от локальной машины.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    plugins {
        id "org.gradle.toolchains.foojay-resolver-convention" version "1.0.0"
    }

    rootProject.name = "kora-example"
    ```

    Затем добавьте `gradle.properties`:

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    plugins {
        id "org.gradle.toolchains.foojay-resolver-convention" version "1.0.0"
    }

    rootProject.name = "kora-example"
    ```

    Добавьте `gradle.properties`. Последнее свойство нужно из-за Kotlin 1.9.25: если Kotlin-компилятор не может выставить target ровно как JDK 24, он сообщит об этом как warning, а не остановит учебную сборку:

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true
    kotlin.jvm.target.validation.mode=warning
    ```

### Импорты и плагины { #imports-plugins }

Теперь начнем собирать Gradle-файл. Импорты нужны для читаемой настройки toolchain, а плагины включают сборку, запуск приложения и генерацию кода.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    plugins {
        id "java"
        id "application"
    }
    ```

    Плагин `java` добавляет задачи `compileJava`, `classes`, `test` и стандартные конфигурации зависимостей. Плагин `application` добавляет задачу `run` и правила упаковки исполняемого приложения.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    plugins {
        id("application")
        kotlin("jvm") version "1.9.25"
        id("com.google.devtools.ksp") version "1.9.25-1.0.20"
    }
    ```

    `application` добавляет `run`, `kotlin("jvm")` компилирует Kotlin-код для JVM, а `com.google.devtools.ksp` запускает Kora symbol processor. Для Kotlin Kora использует KSP вместо Java `annotationProcessor`.

### Координаты проекта { #coordinates }

`group` и `version` — это координаты Gradle-проекта. Даже если приложение пока не публикуется в Maven-репозиторий, эти значения помогают Gradle, IDE и будущим модулям однозначно называть артефакт.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    group = "ru.tinkoff.kora.guide.gettingstarted"
    version = "1.0-SNAPSHOT"
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    group = "ru.tinkoff.kora.guide.gettingstarted"
    version = "1.0-SNAPSHOT"
    ```

### JDK инструментарий { #java-toolchain }

Toolchain говорит Gradle, каким JDK компилировать код. Это отличается от `JAVA_HOME`: Gradle может быть запущен одним JDK, а компилировать приложение другим. В руководстве используется JDK 24 от Adoptium, чтобы сборка была воспроизводимой.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    java {
        toolchain {
            languageVersion = JavaLanguageVersion.of(24)
            vendor = JvmVendorSpec.ADOPTIUM
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    kotlin {
        jvmToolchain {
            languageVersion.set(JavaLanguageVersion.of(24))
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    java {
        toolchain {
            languageVersion.set(JavaLanguageVersion.of(24))
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
    }
    ```

    Директории `build/generated/ksp/main/kotlin` и `build/generated/ksp/test/kotlin` важны для IDE и компиляции: там KSP размещает код, который сгенерировала Kora.

### Репозитории зависимостей { #repositories }

Репозиторий `mavenCentral()` нужен Gradle, чтобы скачать Kora, Undertow, Logback и их транзитивные зависимости.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    repositories {
        mavenCentral()
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    repositories {
        mavenCentral()
    }
    ```

### Конфигурация BOM { #bom }

Kora состоит из нескольких модулей. Чтобы не указывать версию у каждого модуля отдельно, подключается BOM (`Bill of Materials`). Отдельная конфигурация `koraBom` хранит платформу с версиями, а затем распространяет эти версии на обычные Gradle-конфигурации.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configurations {
        koraBom
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testImplementation.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
    }
    ```

    `annotationProcessor` получает BOM отдельно, потому что обработчики аннотаций живут в своем classpath. `implementation` получает BOM для зависимостей приложения.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val koraBom: Configuration by configurations.creating

    configurations {
        ksp.get().extendsFrom(koraBom)
        compileOnly.get().extendsFrom(koraBom)
        implementation.get().extendsFrom(koraBom)
        testImplementation.get().extendsFrom(koraBom)
    }
    ```

    `ksp` получает BOM отдельно, потому что процессор Kora работает в отдельном classpath, а `implementation` получает его для зависимостей приложения.

### Зависимости { #gradle-dependencies }

Теперь добавьте зависимости. Сначала подключается сам BOM Kora. После этого зависимости Kora можно указывать без версий: Gradle возьмет версии из `kora-parent`. Затем добавляется обработчик аннотаций или KSP-процессор и runtime-модули фреймворка.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        koraBom platform("ru.tinkoff.kora:kora-parent:1.2.16")

        annotationProcessor "ru.tinkoff.kora:annotation-processors"

        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.2.16"))

        ksp("ru.tinkoff.kora:symbol-processor")

        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

Эти зависимости дают приложению HTTP-сервер Undertow, HOCON-конфигурацию, JSON-инфраструктуру, Logback-логирование и генерацию графа Kora во время компиляции.

### Точка входа приложения { #entry-point }

Последний блок нужен плагину `application`. Он задает имя приложения, класс с методом `main` и аргументы JVM по умолчанию.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    application {
        applicationName = "application"
        mainClass = "ru.tinkoff.kora.guide.gettingstarted.Application"
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"]
    }
    ```

    Здесь `mainClass` указывает на ваш исходный тип `Application`, а не на сгенерированный `ApplicationGraph`: метод `main` внутри `Application` сам вызовет `KoraApplication.run(ApplicationGraph::graph)`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    application {
        applicationName.set("application")
        mainClass.set("ru.tinkoff.kora.guide.gettingstarted.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }
    ```

    В Kotlin top-level функция `main` из файла `Application.kt` компилируется в класс с суффиксом `Kt`, поэтому здесь указан `ApplicationKt`.

`ApplicationGraph` не пишется руками и не существует до запуска обработчика. Java annotation processor или KSP сгенерирует его во время компиляции, а `./gradlew classes` проверит не только исходный код, но и возможность построить граф Kora.

Аргумент `-Dfile.encoding=UTF-8` фиксирует кодировку запуска на разных ОС. Это полезно для логов, текстовых HTTP-ответов и любых строковых ресурсов.

## Модули { #modules }

Корневой интерфейс приложения — это место, где Kora начинает строить граф зависимостей. Аннотация `@KoraApp` говорит обработчику: этот тип является входной точкой приложения, из него нужно собрать все
компоненты, фабрики и модули в один граф.

Интерфейс расширяет модули Kora. Каждый модуль добавляет в граф набор готовых фабрик: `HoconConfigModule` умеет загрузить конфигурацию, `UndertowHttpServerModule` добавляет HTTP-сервер и
обработчики, `JsonModule` добавляет JSON-отображения, а `LogbackModule` настраивает логирование. Вы не создаете эти объекты руками — Kora связывает их по типам и сгенерированным фабричным методам.

Метод `main` запускает уже сгенерированный класс `ApplicationGraph`. В исходниках его еще нет, но после компиляции Kora создаст его рядом с другими сгенерированными исходниками. Поэтому в Kora обычная
последовательность такая: сначала описываем граф аннотациями и модулями, затем запускаем `./gradlew clean classes`, после чего сгенерированный класс становится доступен для запуска приложения.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/gettingstarted/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.gettingstarted;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowHttpServerModule {  // <----- Подключили модуль

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

    ??? abstract "Java: фрагмент сгенерированного `ApplicationGraph`"

        После `./gradlew clean classes` обработчик аннотаций создаст файл `build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/gettingstarted/ApplicationGraph.java`.
        Полный файл содержит все компоненты из подключенных модулей, поэтому ниже показан только фрагмент, который связывает ваш контроллер, HTTP-маршрут и Undertow-сервер:

        ```java
        @Generated("ru.tinkoff.kora.kora.app.annotation.processor.KoraAppProcessor")
        public class ApplicationGraph implements Supplier<ApplicationGraphDraw> {
            private static final ApplicationGraphDraw graphDraw;
            private static final ComponentHolder0 holder0;

            static {
                var impl = new $ApplicationImpl();
                graphDraw = new ApplicationGraphDraw(Application.class);
                holder0 = new ComponentHolder0(graphDraw, impl);
            }

            public static ApplicationGraphDraw graph() {
                return graphDraw;
            }
        }
        ```

        `ApplicationGraphDraw` — описание графа зависимостей, а `ComponentHolder0` хранит узлы графа. Метод `graph()` — именно та точка, которую вы передали в `KoraApplication.run(ApplicationGraph::graph)`.

        Внутри `ComponentHolder0` Kora добавляет узлы примерно такого вида:

        ```java
        component21 = graphDraw.addNode0(_type_of_component21, new Class<?>[]{}, g -> new HelloController(), List.of());

        component26 = graphDraw.addNode0(_type_of_component26, new Class<?>[]{}, g -> impl.module0.get_hello(
            g.get(ApplicationGraph.holder0.component21),
            g.get(ApplicationGraph.holder0.component25)
        ), List.of(), component21, component25);

        component29 = graphDraw.addNode0(_type_of_component29, new Class<?>[]{}, g -> impl.publicApiHandler(
            All.of(g.get(ApplicationGraph.holder0.component26)),
            All.of(),
            g.get(ApplicationGraph.holder0.component28),
            g.get(ApplicationGraph.holder0.component20)
        ), List.of(), component26, component28, component20);

        component32 = graphDraw.addNode0(_type_of_component32, new Class<?>[]{}, g -> impl.undertowHttpServer(
            g.valueOf(ApplicationGraph.holder0.component20).map(v -> (HttpServerConfig) v),
            g.valueOf(ApplicationGraph.holder0.component30).map(v -> (UndertowPublicApiHandler) v),
            g.get(ApplicationGraph.holder0.component22).value(),
            g.get(ApplicationGraph.holder0.component31)
        ), List.of(), component20.valueOf(), component30.valueOf(), component22, component31);
        ```

        Что здесь происходит:

        - `new HelloController()` — Kora создает ваш `@Component`.
        - `impl.module0.get_hello(...)` — Kora вызывает сгенерированную фабрику HTTP-маршрута для `GET /hello`.
        - `publicApiHandler(...)` собирает публичные HTTP-маршруты в общий обработчик.
        - `undertowHttpServer(...)` создает серверный компонент Undertow и получает конфигурацию из графа.

        Поэтому при старте приложения Kora не сканирует classpath в runtime. Все связи уже рассчитаны на этапе компиляции и записаны в сгенерированный Java-код.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.gettingstarted

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowHttpServerModule  // <----- Подключили модуль

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

    ??? abstract "Kotlin: фрагмент сгенерированного `ApplicationGraph`"

        Для Kotlin Kora использует KSP и создает файл `build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/ApplicationGraph.kt`.
        Это Kotlin-код, сгенерированный из Kotlin-приложения:

        ```kotlin
        @Generated("ru.tinkoff.kora.kora.app.ksp.KoraAppProcessor")
        public class ApplicationGraph : Supplier<ApplicationGraphDraw> {
            override fun `get`(): ApplicationGraphDraw = graphDraw

            public fun graph(): ApplicationGraphDraw {
                return graphDraw
            }
        }
        ```

        Внутри сгенерированного держателя компонентов KSP добавляет узлы графа:

        ```kotlin
        component26 = graphDraw.addNode0(map["component26"],
            arrayOf(),
            { HelloController() },
            listOf()
        )

        component31 = graphDraw.addNode0(map["component31"],
            arrayOf(),
            { impl.module0.get_hello(
                it.get(holder0.component26),
                it.get(holder0.component30)
            ) },
            listOf(),
            component26, component30
        )

        component34 = graphDraw.addNode0(map["component34"],
            arrayOf(),
            { impl.publicApiHandler(
                All.of(it.get(holder0.component31)),
                All.of(),
                it.get(holder0.component33),
                it.get(holder0.component24)
            ) },
            listOf(),
            component31, component33, component24
        )

        component37 = graphDraw.addNode0(map["component37"],
            arrayOf(),
            { impl.undertowHttpServer(
                it.valueOf(holder0.component24).map { it as HttpServerConfig },
                it.valueOf(holder0.component35).map { it as UndertowPublicApiHandler },
                it.get(holder0.component27).value(),
                it.get(holder0.component36)
            ) },
            listOf(),
            component24.valueOf(), component35.valueOf(), component27, component36
        )
        ```

        Смысл тот же, что и в Java-версии: KSP заранее описывает, как создать `HelloController`, как превратить его метод в HTTP-маршрут, как добавить маршрут в публичный обработчик и как передать обработчик в Undertow-сервер.

## Контроллер { #controller }

Контроллер — первый собственный компонент приложения. `@Component` регистрирует класс в графе зависимостей, а `@HttpController` говорит HTTP-модулю, что внутри класса нужно искать HTTP-маршруты. Метод
с `@HttpRoute` описывает конкретный маршрут: HTTP-метод, путь и Java/Kotlin-метод, который будет вызван при запросе.

В этом первом примере метод возвращает `HttpServerResponse` напрямую. Такой вариант самый явный для старта: в одной строке видно HTTP-статус, тип тела ответа и сам текст. В следующих руководствах появятся
JSON DTO, тело запроса, проверка входных данных, обработка ошибок и сервисный слой, но здесь полезно увидеть самый нижний понятный уровень HTTP-ответа.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/gettingstarted/HelloController.java`:

    ```java
    package ru.tinkoff.kora.guide.gettingstarted;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;

    @Component
    @HttpController
    public final class HelloController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        public HttpServerResponse hello() {
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello, Kora!"));
        }
    }
    ```

    ??? abstract "Java: сгенерированный модуль маршрута `HelloControllerModule`"

        После компиляции HTTP-процессор создаст файл `build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/gettingstarted/HelloControllerModule.java`:

        ```java
        package ru.tinkoff.kora.guide.gettingstarted;

        import ru.tinkoff.kora.common.Module;
        import ru.tinkoff.kora.common.annotation.Generated;
        import ru.tinkoff.kora.http.server.common.handler.BlockingRequestExecutor;
        import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandler;
        import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandlerImpl;

        @Generated("ru.tinkoff.kora.http.server.annotation.processor.ControllerModuleGenerator")
        @Module
        public interface HelloControllerModule {
            default HttpServerRequestHandler get_hello(HelloController _controller,
                BlockingRequestExecutor _executor) {
                return HttpServerRequestHandlerImpl.of("GET", "/hello", (_ctx, _request) -> {
                    return _executor.execute(_ctx, () -> {
                        return _controller.hello();
                    });
                });
            }
        }
        ```

        Этот файл показывает, что делает `@HttpController`:

        - `@Module` добавляет сгенерированную фабрику в граф Kora.
        - Метод `get_hello(...)` создает `HttpServerRequestHandler` для `GET /hello`.
        - `HelloController _controller` берется из графа как обычный компонент.
        - `BlockingRequestExecutor _executor` выполняет синхронный метод контроллера в подходящем executor, чтобы не блокировать event loop HTTP-сервера.
        - `HttpServerRequestHandlerImpl.of(...)` связывает HTTP-метод, путь и вызов `_controller.hello()`.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/HelloController.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.gettingstarted

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.http.server.common.annotation.HttpController

    @Component
    @HttpController
    class HelloController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        fun hello(): HttpServerResponse {
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello, Kora!"))
        }
    }
    ```

    ??? abstract "Kotlin: сгенерированный модуль маршрута `HelloControllerModule`"

        В Kotlin-приложении KSP создает файл `build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/HelloControllerModule.kt`:

        ```kotlin
        package ru.tinkoff.kora.guide.gettingstarted

        import java.util.concurrent.CompletableFuture
        import ru.tinkoff.kora.common.Module
        import ru.tinkoff.kora.common.`annotation`.Generated
        import ru.tinkoff.kora.http.server.common.HttpServerResponse
        import ru.tinkoff.kora.http.server.common.HttpServerResponseException
        import ru.tinkoff.kora.http.server.common.handler.BlockingRequestExecutor
        import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandler
        import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandlerImpl

        @Generated("ru.tinkoff.kora.http.server.symbol.procesor.HttpControllerProcessor")
        @Module
        public interface HelloControllerModule {
            public fun get_hello(_controller: HelloController, _executor: BlockingRequestExecutor):
                HttpServerRequestHandler = HttpServerRequestHandlerImpl.of("GET", "/hello") { _ctx,
                _request ->
                try {
                    _executor.execute(_ctx) {
                        val _result = _controller.hello()
                        return@execute _result
                    }
                } catch (_e: Exception) {
                    if (_e is HttpServerResponse) {
                        CompletableFuture.failedFuture(_e)
                    } else {
                        CompletableFuture.failedFuture(HttpServerResponseException.of(400, _e))
                    }
                }
            }
        }
        ```

        Здесь видно Kotlin-специфику KSP-генерации:

        - Фабрика также помечена `@Module`, поэтому попадет в общий граф.
        - `get_hello(...)` возвращает `HttpServerRequestHandler` для `GET /hello`.
        - Вызов `_controller.hello()` выполняется через `BlockingRequestExecutor`.
        - Исключения преобразуются в failed future: если исключение уже является `HttpServerResponse`, оно передается как HTTP-ответ; иначе Kora оборачивает его в `HttpServerResponseException` со статусом `400`.

## Конфигурация { #config }

Kora ожидает, что инфраструктурные настройки будут вынесены из кода в конфигурацию. Даже в маленьком приложении это полезно: порт публичного HTTP API, порт служебного API и уровень логирования
меняются без перекомпиляции. В реальных сервисах по тому же принципу задаются подключения к базам данных, Kafka, HTTP-клиентам, кешам и системам наблюдаемости.

В этом руководстве используется HOCON, потому что он хорошо подходит для вложенных настроек и подстановки переменных окружения. Если проект использует YAML, структура ключей остается такой же: меняется
только синтаксис файла.

Создайте `src/main/resources/application.conf`:

Полную справку по настройкам смотрите в документации [HTTP-сервер](../documentation/http-server.md), [журналирование SLF4J](../documentation/logging-slf4j.md) и [Config](../documentation/config.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      publicApiHttpPort = 8080 //(1)!
      privateApiHttpPort = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    logging {
      levels {
        "ROOT": "WARN" //(4)!
        "ru.tinkoff.kora": "INFO" //(5)!
      }
    }
    ```

    1. Публичный HTTP-порт по умолчанию для маршрутов приложения.
    2. Приватный HTTP-порт по умолчанию для проб, метрик и служебных маршрутов.
    3. Включает указанную возможность в этой секции конфигурации.
    4. Уровень логирования для `ROOT`.
    5. Уровень логирования для `ru.tinkoff.kora`.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      publicApiHttpPort: 8080 #(1)!
      privateApiHttpPort: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    logging:
      levels:
        ROOT: "WARN" #(4)!
        "ru.tinkoff.kora": "INFO" #(5)!
    ```

    1. Публичный HTTP-порт по умолчанию для маршрутов приложения.
    2. Приватный HTTP-порт по умолчанию для проб, метрик и служебных маршрутов.
    3. Включает указанную возможность в этой секции конфигурации.
    4. Уровень логирования для `ROOT`.
    5. Уровень логирования для `ru.tinkoff.kora`.

## Запуск приложения { #run-app }

Перед запуском полезно выполнить три команды именно в таком порядке. `clean classes` заставляет Gradle пересобрать проект и заново сгенерировать код Kora, поэтому ошибки графа находятся еще до старта
приложения. `test` проверяет, что тестовая инфраструктура проекта корректна. `run` запускает приложение через плагин Gradle `application` и использует `mainClass`, который мы указали в сборке.

```bash
./gradlew run
```

## Проверка приложения { #check-app }

Когда приложение запущено, публичный HTTP-сервер слушает порт `8080`. Запрос к `/hello` проходит через Undertow, затем через сгенерированный обработчик Kora и в итоге вызывает
метод `HelloController#hello`.

```bash
curl http://localhost:8080/hello
# Ожидаемый вывод: Hello, Kora!
```

## Сгенерированный код { #generated-code }

Kora — фреймворк, который выполняет основную работу во время компиляции. После `./gradlew classes` сгенерированные исходники показывают, как аннотации превращаются в обычный Java- или
Kotlin-код. Это один из лучших способов изучать фреймворк: если что-то кажется магией, откройте сгенерированные исходники и обычно вы увидите конкретную фабрику, узел графа или HTTP-обработчик,
который создала Kora.

Начните со сгенерированного модуля контроллера:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-getting-started-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/gettingstarted/HelloControllerModule.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-getting-started-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/HelloControllerModule.kt
    ```

В нем находится `HttpServerRequestHandler`, который Kora сгенерировала для `@HttpController` и `@HttpRoute`. Этот обработчик является мостом между входящим HTTP-запросом Undertow и обычным методом
вашего контроллера:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Generated("ru.tinkoff.kora.http.server.annotation.processor.ControllerModuleGenerator")
    @Module
    public interface HelloControllerModule {
      default HttpServerRequestHandler get_hello(HelloController _controller,
          BlockingRequestExecutor _executor) {
        return HttpServerRequestHandlerImpl.of("GET", "/hello", (_ctx, _request) -> {
          return _executor.execute(_ctx, () -> {
            return _controller.hello();
          });
        });
      }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Generated("ru.tinkoff.kora.http.server.symbol.procesor.HttpControllerProcessor")
    @Module
    public interface HelloControllerModule {
      public fun get_hello(_controller: HelloController, _executor: BlockingRequestExecutor):
          HttpServerRequestHandler = HttpServerRequestHandlerImpl.of("GET", "/hello") { _ctx, _request ->
        try {
          _executor.execute(_ctx) {
            val _result = _controller.hello()
            return@execute _result
          }
        } catch (_e: Exception) {
          if (_e is HttpServerResponse) {
            CompletableFuture.failedFuture(_e)
          } else {
            CompletableFuture.failedFuture(HttpServerResponseException.of(400, _e))
          }
        }
      }
    }
    ```

Затем посмотрите сгенерированный граф приложения:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-getting-started-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/gettingstarted/ApplicationGraph.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-getting-started-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/ApplicationGraph.kt
    ```

Вы увидите, что Kora регистрирует контроллер, а затем регистрирует сгенерированный HTTP-обработчик, который зависит от этого контроллера. Эта зависимость важна: обработчик не может существовать без
экземпляра контроллера, и граф фиксирует эту связь явно:

===! ":fontawesome-brands-java: `Java`"

    ```java
    component21 = graphDraw.addNode0(_type_of_component21, new Class<?>[]{},
          g -> new HelloController(), List.of());

    component26 = graphDraw.addNode0(_type_of_component26, new Class<?>[]{},
          g -> impl.module0.get_hello(
            g.get(ApplicationGraph.holder0.component21),
            g.get(ApplicationGraph.holder0.component25)
          ), List.of(), component21, component25);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    component26 = graphDraw.addNode0(map["component26"],
      arrayOf(),
      { HelloController() },
      listOf()
    )

    component31 = graphDraw.addNode0(map["component31"],
      arrayOf(),
      { impl.module0.get_hello(
        it.get(holder0.component26),
        it.get(holder0.component30)
      ) },
      listOf(),
      component26, component30
    )
    ```

Это первый практический взгляд на ключевую идею Kora:

- ваш исходный код объявляет компоненты и маршруты
- обработчики аннотаций генерируют граф и обработчики маршрутов
- запуск приложения использует сгенерированный граф вместо поиска компонентов через reflection

Сгенерированные исходники также полезны для нейро-ассистентов и разбора работы приложения. В них видно точное скомпилированное связывание компонентов, поэтому можно посмотреть, как фреймворк соединил
части приложения, а не гадать только по аннотациям.

## Лучшие практики { #best-practices }

- Держите граф приложения в одной точке входа `@KoraApp`. Так проще видеть, какие модули инфраструктуры подключены к сервису, и где начинается сборка приложения.
- Подключайте модули фреймворка явно через `extends`. Это делает зависимости приложения читаемыми: по корневому интерфейсу сразу видно, что сервис использует HTTP, HOCON, JSON и Logback.
- Оставляйте контроллеры тонкими и переносите бизнес-логику в сервисы, когда сложность растет. В первом руководстве контроллер сам возвращает строку, но в настоящем API он обычно только принимает
  HTTP-запрос, вызывает сервис и формирует HTTP-ответ.
- Запускайте `./gradlew classes` после добавления новых компонентов. Внедрение зависимостей на этапе компиляции хорошо тем, что многие ошибки зависимостей находятся сразу при сборке, а не во
  время первого запроса при выполнении приложения.
- Изучайте сгенерированные исходники, если хотите понять, что Kora скомпилировала из ваших аннотаций. Это помогает быстрее найти реальное связывание компонентов.

## Итоги { #summary }

Вы создали рабочее HTTP-приложение на Kora и прошли основной путь, который будет повторяться в следующих руководствах:

- описали корневой `@KoraApp`, который является входной точкой графа зависимостей
- подключили модули фреймворка для конфигурации, логирования, JSON и HTTP-сервера
- добавили собственный компонент приложения через `@Component`
- опубликовали первый маршрут контроллера (`GET /hello`)
- настроили базовую конфигурацию портов и логирования
- посмотрели сгенерированный обработчик HTTP-маршрута и фрагмент сгенерированного графа приложения

## Ключевые понятия { #key-concepts }

- `@KoraApp` определяет корень графа приложения.
- Kora генерирует связывание компонентов на этапе компиляции.
- `@HttpController` + `@HttpRoute` публикуют HTTP-маршруты.
- Сгенерированные исходники показывают код графа приложения и обработчик маршрута.

## Устранение неполадок { #troubleshooting }

**Сборка падает с ошибками сгенерированного графа**

- Проверьте, что annotation processing настроен: `annotationProcessor` для Java или `ksp` для Kotlin.
- Проверьте, что корневой интерфейс помечен `@KoraApp` и расширяет нужные модули Kora.
- Проверьте, что все классы с `@Component` доступны из набора исходных файлов приложения и находятся в корректном пакете.
- Если ошибка говорит о недостающей зависимости, прочитайте ее как обычный граф зависимостей: Kora показывает, какой тип пыталась создать и какого компонента не хватило.

**Приложение не запускается на порту 8080**

- Проверьте `application.conf` и доступность порта.
- Убедитесь, что другой процесс не использует `8080`.

**Smoke-check приватного API (`8085`)**

- Проверьте, что маршрут приватного API доступен:

  ```bash
  curl http://localhost:8085/system/readiness
  ```

- Если маршрут недоступен, проверьте `privateApiHttpPort = 8085`, `privateApiHttpReadinessPath = "/system/readiness"` в `application.conf` и логи запуска приложения.

**Gradle зависает или ведет себя неожиданно**

- Выполните `./gradlew --stop`, затем повторите команду.

## Что дальше? { #whats-next }

Это руководство намеренно останавливается на маленьком маршруте: теперь у вас есть минимальный рабочий каркас, к которому можно добавлять новые понятия по одному. Лучший следующий шаг — сначала глубже
понять внедрение зависимостей, а затем перейти к конфигурации, JSON и полноценному HTTP API.

- [Изучите основы внедрения зависимостей](dependency-injection-introduction.md), чтобы понять граф приложения, компоненты, модули и связывание на этапе компиляции, которое стоит за первым маршрутом.
- [Конфигурация с HOCON](config-hocon.md) или [конфигурация с YAML](config-yaml.md), чтобы узнать, как Kora читает типизированные настройки приложения.
- [Работа с JSON](json.md), чтобы добавить явное преобразование DTO запросов и ответов перед полноценным руководством по HTTP-сервер.
- [Создание HTTP-сервера](http-server.md), когда после JSON вы будете готовы превратить маленький маршрут в более полноценный HTTP API.

## Помощь { #help }

При отладке первого приложения удобно разделять проблемы на три группы: ошибки сборки, ошибки старта и ошибки запроса. Ошибки сборки чаще всего связаны с обработкой аннотаций или недостающими
компонентами графа. Ошибки старта обычно связаны с конфигурацией или занятым портом. Ошибки запроса нужно искать в контроллере, сгенерированном обработчике и логах HTTP-сервера.

Если что-то не совпадает с вашим локальным приложением:

- сравните с [Kora Java Getting Started App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-getting-started-app) и [Kora Kotlin Getting Started App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-getting-started-app)
- проверьте [документацию HTTP-сервера](../documentation/http-server.md)
- проверьте [документацию контейнера](../documentation/container.md)
- посмотрите [пример Hello World](https://github.com/kora-projects/kora-examples/tree/master/kora-java-helloworld)
