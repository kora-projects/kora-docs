---
search:
  exclude: true
title: Создание первого приложения на Kora
summary: Learn how to create a minimal Kora HTTP application and run your first endpoint
description: "Step-by-step first Kora application: Gradle wrapper and JDK toolchain setup, the io.koraframework:kora-bom BOM, annotation-processors and symbol-processors, a @KoraApp graph root with HoconConfigModule, JsonModule, LogbackModule and UndertowPublicHttpServerModule, one @HttpController route, httpServer configuration and the generated graph and handler sources."
agent:
  use_when: "Use this file for questions about starting a new Kora project from scratch: Gradle setup, io.koraframework:kora-bom, annotation-processors and symbol-processors, @KoraApp, KoraApplication.run(ApplicationGraph::graph), UndertowPublicHttpServerModule, the first @HttpController and @HttpRoute, httpServer.port and httpServer.system.port, and reading Kora generated sources."
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

- JDK 25 или новее
- Gradle 9+ (в руководстве поднимается Gradle Wrapper `9.5.1` — та же версия, что и в эталонных приложениях)
- Текстовый редактор или среда разработки
- Базовое умение читать Java- или Kotlin-код

Артефакты Kora собраны под Java 25, поэтому JDK, которым компилируется ваш код, должен быть версии 25 или новее. Docker, база данных и внешние сервисы для этого руководства не нужны. Все запускается
в одном процессе на вашей машине, поэтому это хороший первый шаг перед добавлением реальной инфраструктуры.

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

В проектах на Kora вы будете встречать два вида модулей. Модули фреймворка, например `UndertowPublicHttpServerModule`, дают готовую инфраструктуру. Прикладные модули — это ваши интерфейсы или классы,
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

HTTP-обработчики Kora синхронные. Undertow переносит каждый запрос на виртуальный поток еще до того, как сгенерированный обработчик вызовет метод контроллера, поэтому блокирующие вызовы внутри
контроллера — это нормальный и ожидаемый стиль: в контракте контроллера нет ни реактивных типов, ни `CompletionStage`, ни `suspend`-функций.

К концу руководства вы должны понимать минимальный набор движущихся частей сервиса на Kora: зависимости [Gradle](https://docs.gradle.org/current/userguide/userguide.html), граф приложения, модуль
фреймворка, один компонент и один маршрут, опубликованный через HTTP-сервер [Undertow](https://undertow.io/).

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

Шаблон — это уже готовый к запуску Gradle-проект, но оба шаблона пока собраны под Kora 1.x: BOM в них — `ru.tinkoff.kora:kora-parent`, а в Kotlin-шаблоне зафиксированы toolchain JDK 17 и Kotlin
`1.9.25`. Чтобы запустить их на Kora 2.0, файл сборки придется поправить руками: заменить платформу на `io.koraframework:kora-bom`, убрать группу `ru.tinkoff.kora` из всех зависимостей и поднять
toolchain до JDK 25. Если нужен проект на Kora 2.0 без этих правок, используйте ручную настройку ниже.

Ручная сборка ниже полезнее для первого знакомства: она показывает, какие Gradle-плагины нужны, какие модули Kora подключаются в корневой граф, где лежит конфигурация и какой минимальный код
действительно требуется для запуска HTTP-приложения.

## Установите JDK { #install-jdk }

Перед Gradle нужен установленный JDK: именно JVM запускает Gradle Wrapper, компилятор Java и инструменты сборки. Модули Kora публикуются под Java 25, и эталонные приложения настраивают toolchain на
Java 25, поэтому поставьте Eclipse Temurin JDK 25 и запускайте Gradle именно на нем.

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

    Если установлен `winget`, поставьте Temurin JDK из терминала PowerShell:

    ```powershell
    winget install EclipseAdoptium.Temurin.25.JDK
    ```

    Если `winget` недоступен, скачайте установщик Windows со [страницы загрузок Eclipse Temurin](https://adoptium.net/temurin/releases/?version=25), выберите **JDK 25** для архитектуры вашего
    процессора, запустите установщик и включите обновление `JAVA_HOME` и `PATH`, если установщик предложит такой пункт.

    После установки откройте новый терминал, чтобы обновились переменные окружения.

Проверьте, что JDK доступен:

```bash
java -version
```

В выводе должна быть версия Java 25. После этого можно создавать каталог проекта.

!!! tip "JVM Gradle и toolchain — это разные вещи"

    Toolchain выбирает JDK, которым компилируется ваш код. Сам процесс Gradle работает на JDK из `JAVA_HOME`, и часть плагинов резолвится на buildscript classpath именно этой JVM. Генератор OpenAPI
    от Kora — как раз такой плагин, поэтому как только в проекте появится генерация кода из контракта, JVM самого Gradle тоже должна быть Java 25 или новее. Если сразу держать обе на одном JDK,
    этот класс ошибок не возникнет вовсе.

## Каталог проекта { #project-directory }

Сначала создайте пустой каталог будущего приложения и перейдите в него. Все следующие команды в руководстве выполняются из этого каталога:

```bash
mkdir kora-guide-example
cd kora-guide-example
```

## Настройка Gradle { #gradle-setup }

Начнем с обычного Gradle-проекта. На этом этапе в нем еще нет ничего специфичного для Kora, и это намеренно: Kora подключается обычными зависимостями и обработчиками аннотаций, поэтому приложение
остается стандартным Java- или Kotlin-проектом, который Gradle собирает привычными задачами.

Имя пакета важно, потому что сгенерированные исходники раскладываются рядом с пакетом приложения. Стабильный пакет также упрощает последующий разбор сгенерированного кода. В руководстве используется
`io.koraframework.guide.gettingstarted` — тот же пакет, что и в эталонных приложениях.

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
      --package io.koraframework.guide.gettingstarted \
      --project-name kora-example \
      --java-version 25 \
      --overwrite
    ```

=== ":simple-kotlin: `Kotlin`"

    ```bash
    java -cp gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain init \
      --type kotlin-application \
      --dsl kotlin \
      --test-framework junit-jupiter \
      --package io.koraframework.guide.gettingstarted \
      --project-name kora-example \
      --java-version 25 \
      --overwrite
    ```

`--overwrite` здесь обязателен: в каталоге уже лежат файлы wrapper из предыдущих шагов, и без этой опции `init` прерывается с ошибкой `Aborting build initialization due to existing files in the project directory`.

`init` создает каркас многомодульного проекта: подпроект `app` с файлом сборки и примерами исходников, плюс корневой файл настроек, который его подключает. В этом руководстве используется
одномодульная раскладка, поэтому удалите подпроект — файлы сборки мы напишем сами в следующем разделе:

```bash
rm -rf app
```

Файл настроек, файл сборки и исходники, которые мы пишем дальше, лежат в корне проекта и заменяют собой все, что сгенерировал `init`, поэтому точные умолчания, выбранные им, большой роли не играют.

## Зависимости { #dependencies }

Теперь добавим минимальный набор Gradle-настроек, который превращает обычный Gradle-проект в Kora-приложение. Не будем вставлять весь `build.gradle` одним большим фрагментом: полезнее собрать его по частям и сразу понять, какую роль играет каждая часть.

В этом разделе Gradle должен сделать несколько вещей:

- выбрать JDK, которым компилируется приложение
- включить обычную сборку приложения и запуск через `gradlew run`
- подключить Kora BOM, чтобы все модули Kora использовали согласованные версии
- включить генерацию кода Kora на этапе компиляции
- добавить модули HTTP-сервера, конфигурации, JSON и логирования

### Поиск JDK для сборки { #toolchain }

Сначала обновите файл настроек проекта. Плагин `foojay-resolver-convention` помогает Gradle найти или скачать JDK, который указан в toolchain. Без него Gradle может использовать только уже установленные JDK и сборка станет сильнее зависеть от локальной машины.

===! ":fontawesome-brands-java: `Java`"

    `settings.gradle`:

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

    `settings.gradle.kts`:

    ```kotlin
    plugins {
        id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
    }

    rootProject.name = "kora-example"
    ```

    Затем добавьте `gradle.properties`. Последнее свойство повторяет настройку эталонных приложений: если компилятор Kotlin не может выставить JVM target ровно как в toolchain, он сообщит об этом предупреждением, а не остановит сборку:

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true
    kotlin.jvm.target.validation.mode=warning
    ```

### Импорты и плагины { #imports-plugins }

Теперь начнем собирать Gradle-файл. Плагины включают сборку, запуск приложения и генерацию кода. Groovy DSL сам находит типы toolchain, а Kotlin DSL требует для них явных импортов.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
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
        id("org.jetbrains.kotlin.jvm") version "2.4.10"
        id("com.google.devtools.ksp") version "2.3.11"
        id("application")
    }
    ```

    `application` добавляет `run`, `org.jetbrains.kotlin.jvm` компилирует Kotlin-код для JVM, а `com.google.devtools.ksp` запускает symbol processor Kora. Для Kotlin вместо Java-конфигурации `annotationProcessor` используется KSP. Версия плагина KSP привязана к версии Kotlin, поэтому поднимать их нужно вместе.

### Координаты проекта { #coordinates }

`group` и `version` — это координаты Gradle-проекта. Даже если приложение пока не публикуется в Maven-репозиторий, эти значения помогают Gradle, IDE и будущим модулям однозначно называть артефакт.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    group = "io.koraframework.guide.gettingstarted"
    version = "1.0-SNAPSHOT"
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    group = "io.koraframework.guide.gettingstarted"
    version = "1.0-SNAPSHOT"
    ```

### JDK инструментарий { #java-toolchain }

Toolchain говорит Gradle, каким JDK компилировать код. Это отличается от `JAVA_HOME`: Gradle может быть запущен одним JDK, а компилировать приложение другим. Модули Kora требуют Java 25, а эталонные приложения фиксируют toolchain на Temurin JDK 25, чтобы сборка была воспроизводимой.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    java {
        toolchain {
            languageVersion = JavaLanguageVersion.of(25)
            vendor = JvmVendorSpec.ADOPTIUM
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    kotlin {
        jvmToolchain {
            languageVersion.set(JavaLanguageVersion.of(25))
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    java {
        toolchain {
            languageVersion.set(JavaLanguageVersion.of(25))
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

Kora состоит из нескольких модулей. Чтобы не указывать версию у каждого модуля отдельно, подключается BOM (`Bill of Materials`) `io.koraframework:kora-bom`. Он согласует версии всех модулей Kora и тех сторонних библиотек, с которыми Kora поставляется.

===! ":fontawesome-brands-java: `Java`"

    В Java BOM кладут в отдельную конфигурацию `koraBom`, а конфигурации, которым нужны согласованные версии, наследуют ее:

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

    `annotationProcessor` получает BOM отдельно, потому что обработчики аннотаций резолвятся в своем classpath. `implementation` получает BOM для зависимостей приложения.

=== ":simple-kotlin: `Kotlin`"

    В Kotlin BOM подключается прямо в `implementation`, который уже наследует `testImplementation`:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1"))
    }
    ```

    Конфигурация `ksp` не наследует `implementation`, поэтому symbol processor Kora — единственная зависимость, у которой остается явная версия.

### Зависимости { #gradle-dependencies }

Теперь добавьте зависимости. Сначала подключается сам BOM Kora. После этого модули Kora можно указывать без версий: Gradle возьмет их из `kora-bom`. Затем добавляется обработчик аннотаций или KSP-процессор и runtime-модули фреймворка.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1") //(1)!

        annotationProcessor "io.koraframework:annotation-processors" //(2)!

        implementation "io.koraframework:config-hocon" //(3)!
        implementation "io.koraframework:http-server-undertow" //(4)!
        implementation "io.koraframework:json-common" //(5)!
        implementation "io.koraframework:logging-logback" //(6)!
    }
    ```

    1.  BOM Kora: согласует версии всех модулей Kora и библиотек, от которых Kora зависит.
    2.  Обработчик аннотаций Kora: во время компиляции создает граф приложения, модули контроллеров и JSON-читатели/писатели.
    3.  Чтение HOCON-конфигурации из `application.conf`.
    4.  Транспорт HTTP-сервера на Undertow.
    5.  Инфраструктура JSON, генерируемая на этапе компиляции.
    6.  Реализация логирования Logback, встроенная в граф Kora.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1")) //(1)!

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

        implementation("io.koraframework:config-hocon") //(3)!
        implementation("io.koraframework:http-server-undertow") //(4)!
        implementation("io.koraframework:json-common") //(5)!
        implementation("io.koraframework:logging-logback") //(6)!
    }
    ```

    1.  BOM Kora: согласует версии всех модулей Kora и библиотек, от которых Kora зависит.
    2.  KSP-процессор Kora: во время компиляции создает граф приложения, модули контроллеров и JSON-читатели/писатели.
    3.  Чтение HOCON-конфигурации из `application.conf`.
    4.  Транспорт HTTP-сервера на Undertow.
    5.  Инфраструктура JSON, генерируемая на этапе компиляции.
    6.  Реализация логирования Logback, встроенная в граф Kora.

Эти зависимости дают приложению HTTP-сервер Undertow, HOCON-конфигурацию, JSON-инфраструктуру, Logback-логирование и генерацию графа Kora во время компиляции.

### Точка входа приложения { #entry-point }

Последний блок нужен плагину `application`. Он задает имя приложения, класс с методом `main` и аргументы JVM по умолчанию.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    application {
        applicationName = "application"
        mainClass = "io.koraframework.guide.gettingstarted.Application"
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"]
    }
    ```

    Здесь `mainClass` указывает на ваш исходный тип `Application`, а не на сгенерированный `ApplicationGraph`: метод `main` внутри `Application` сам вызовет `KoraApplication.run(ApplicationGraph::graph)`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    application {
        applicationName = "application"
        mainClass.set("io.koraframework.guide.gettingstarted.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }
    ```

    В Kotlin top-level функция `main` из файла `Application.kt` компилируется в класс с суффиксом `Kt`, поэтому здесь указан `ApplicationKt`.

`ApplicationGraph` не пишется руками и не существует до запуска обработчика. Java annotation processor или KSP сгенерирует его во время компиляции, а `./gradlew classes` проверит не только исходный код, но и возможность построить граф Kora.

Аргумент `-Dfile.encoding=UTF-8` фиксирует кодировку запуска на разных ОС. Это полезно для логов, текстовых HTTP-ответов и любых строковых ресурсов.

## Модули { #modules }

Тип `Application` — корень приложения на Kora. Он намеренно является интерфейсом: вы не пишете логику запуска руками, а объявляете, из каких модулей состоит приложение, и Kora генерирует реализацию.

Наследование модулей вроде `HoconConfigModule` и `UndertowPublicHttpServerModule` означает: включить компоненты и фабрики этих модулей в граф текущего приложения. Если нужный модуль не подключен,
Kora обычно сообщает о недостающей зависимости прямо на компиляции.

`UndertowPublicHttpServerModule` — это тот модуль, который нужен приложению с бизнес-маршрутами. Он наследует `UndertowSystemHttpServerModule`, поэтому одно наследование дает сразу два сервера:
публичный на `httpServer.port` и служебный на `httpServer.system.port` с маршрутами readiness, liveness и метрик.

Метод `main` вызывает `KoraApplication.run(ApplicationGraph::graph)`. Класс `ApplicationGraph` генерируется из `Application`, поэтому в исходниках его нет до запуска обработчика аннотаций или KSP.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/gettingstarted/Application.java`:

    ```java
    package io.koraframework.guide.gettingstarted;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp //(1)!
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule { //(2)!

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph); //(3)!
        }
    }
    ```

    1.  Помечает корень графа. Обработчик аннотаций строит весь граф приложения, начиная с этого интерфейса.
    2.  Подключенные модули фреймворка. Каждый модуль добавляет свои фабрики в тот же граф.
    3.  Запускает сгенерированный граф и держит процесс, пока shutdown hook JVM не освободит его.

    ??? abstract "Java: фрагмент сгенерированного `ApplicationGraph`"

        После `./gradlew clean classes` обработчик аннотаций создаст файл `build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/gettingstarted/ApplicationGraph.java`.
        Полный файл содержит все компоненты из подключенных модулей, поэтому ниже показан только фрагмент, который связывает ваш контроллер, HTTP-маршрут и Undertow-сервер:

        ```java
        @Generated("io.koraframework.kora.app.annotation.processor.KoraAppProcessor")
        public class ApplicationGraph implements Supplier<ApplicationGraphDraw> {
            private static final ApplicationGraphDraw graphDraw;
            private static final ComponentHolder0 holder0;

            static {
                var impl = new $ApplicationImpl();
                graphDraw = new ApplicationGraphDraw(Application.class);
                holder0 = new ComponentHolder0(graphDraw, impl);
            }

            @Override
            public ApplicationGraphDraw get() {
                return graphDraw;
            }

            public static ApplicationGraphDraw graph() {
                return graphDraw;
            }
        }
        ```

        `ApplicationGraphDraw` — описание графа зависимостей, а `ComponentHolder0` хранит узлы графа. Метод `graph()` — именно та точка, которую вы передали в `KoraApplication.run(ApplicationGraph::graph)`.

        Внутри `ComponentHolder0` Kora добавляет узлы примерно такого вида. Номера компонентов зависят от того, сколько компонентов дают подключенные модули, поэтому в вашей сборке они будут другими:

        ```java
        var _type_of_component21 = map.get("component21");
        component21 = graphDraw.addNode(_type_of_component21,
            null,
            null,
            List.of(),
            List.of(),
            List.of(),
            g -> new HelloController());

        var _type_of_component26 = map.get("component26");
        component26 = graphDraw.addNode(_type_of_component26,
            null,
            null,
            List.of(component21),
            List.of(component21),
            List.of(),
            g -> impl.module0.get_hello(
                g.get(ApplicationGraph.holder0.component21)
            ));
        ```

        Что здесь происходит:

        - `addNode(...)` регистрирует один узел графа: его тип, необязательный тег, необязательное условие, узлы, нужные для создания, узлы, вызывающие обновление, перехватчики и фабричную лямбду.
        - `new HelloController()` — Kora создает ваш `@Component`.
        - `impl.module0.get_hello(...)` — Kora вызывает сгенерированную фабрику HTTP-маршрута для `GET /hello`, и единственной ее зависимостью является узел контроллера.
        - Ниже в том же держателе Kora регистрирует HTTP-роутер и компонент `UndertowHttpServer`, который получает конфигурацию из графа.

        Поэтому при старте приложения Kora не сканирует classpath в runtime. Все связи уже рассчитаны на этапе компиляции и записаны в сгенерированный Java-код.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/gettingstarted/Application.kt`:

    ```kotlin
    package io.koraframework.guide.gettingstarted

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp //(1)!
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule //(2)!

    fun main() {
        KoraApplication.run(ApplicationGraph::graph) //(3)!
    }
    ```

    1.  Помечает корень графа. KSP строит весь граф приложения, начиная с этого интерфейса.
    2.  Подключенные модули фреймворка. Каждый модуль добавляет свои фабрики в тот же граф.
    3.  Запускает сгенерированный граф и держит процесс, пока shutdown hook JVM не освободит его.

    ??? abstract "Kotlin: фрагмент сгенерированного `ApplicationGraph`"

        Для Kotlin Kora использует KSP и создает файл `build/generated/ksp/main/kotlin/io/koraframework/guide/gettingstarted/ApplicationGraph.kt`.
        Это Kotlin-код, сгенерированный из Kotlin-приложения:

        ```kotlin
        @Generated("io.koraframework.kora.app.ksp.KoraAppProcessor")
        public class ApplicationGraph : Supplier<ApplicationGraphDraw> {
            override fun `get`(): ApplicationGraphDraw = graphDraw

            public fun graph(): ApplicationGraphDraw {
                return graphDraw
            }
        }
        ```

        Внутри сгенерированного держателя компонентов KSP добавляет узлы графа. Номера компонентов зависят от того, сколько компонентов дают подключенные модули, поэтому в вашей сборке они будут другими:

        ```kotlin
        component26 = graphDraw.addNode(map["component26"],
            null,
            null,
            listOf(),
            listOf(),
            listOf(),
            { HelloController() }
        )

        component31 = graphDraw.addNode(map["component31"],
            null,
            null,
            listOf(component26),
            listOf(component26),
            listOf(),
            { impl.module0.get_hello(
                it.get(holder0.component26)
            ) }
        )
        ```

        Смысл тот же, что и в Java-версии: KSP заранее описывает, как создать `HelloController`, как превратить его метод в HTTP-маршрут, как добавить маршрут в роутер и как передать роутер в Undertow-сервер.

## Контроллер { #controller }

Контроллер — первый собственный компонент приложения. `@Component` регистрирует класс в графе зависимостей, а `@HttpController` говорит обработчику HTTP, что внутри класса нужно искать маршруты. Метод
с `@HttpRoute` описывает конкретный маршрут: HTTP-метод, путь и Java/Kotlin-метод, который будет вызван при запросе.

В этом первом примере метод возвращает `HttpServerResponse` напрямую. Такой вариант самый явный для старта: в одной строке видно HTTP-статус, тип тела ответа и сам текст. В следующих руководствах появятся
JSON DTO, тело запроса, проверка входных данных, обработка ошибок и сервисный слой, но здесь полезно увидеть самый нижний понятный уровень HTTP-ответа.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/gettingstarted/HelloController.java`:

    ```java
    package io.koraframework.guide.gettingstarted;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponse;

    @Component //(1)!
    @HttpController //(2)!
    public final class HelloController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello") //(3)!
        public HttpServerResponse hello() {
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello, Kora!")); //(4)!
        }
    }
    ```

    1.  Регистрирует класс как компонент графа, чтобы Kora могла его создать и внедрить туда, где он нужен.
    2.  Говорит HTTP-обработчику просканировать класс на маршруты и сгенерировать модуль с обработчиками запросов.
    3.  Привязывает метод к `GET /hello`. В `HttpMethod` лежат стандартные названия HTTP-методов.
    4.  Формирует ответ явно: статус `200` и тело `text/plain`.

    ??? abstract "Java: сгенерированный модуль маршрута `HelloControllerModule`"

        После компиляции HTTP-процессор создаст файл `build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/gettingstarted/HelloControllerModule.java`:

        ```java
        package io.koraframework.guide.gettingstarted;

        import io.koraframework.common.annotation.Generated;
        import io.koraframework.common.annotation.Module;
        import io.koraframework.http.server.common.request.HttpServerRequestHandler;
        import io.koraframework.http.server.common.request.HttpServerRequestHandlerImpl;

        @Generated("io.koraframework.http.server.annotation.processor.ControllerModuleGenerator")
        @Module
        public interface HelloControllerModule {
            default HttpServerRequestHandler get_hello(HelloController _controller) {
                return HttpServerRequestHandlerImpl.of("GET", "/hello", (_request) -> {
                    return _controller.hello();
                });
            }
        }
        ```

        Этот файл показывает, что делает `@HttpController`:

        - `@Module` добавляет сгенерированную фабрику в граф Kora.
        - Метод `get_hello(...)` создает `HttpServerRequestHandler` для `GET /hello`; имя метода собирается из HTTP-метода и пути.
        - `HelloController _controller` берется из графа как обычный компонент.
        - `HttpServerRequestHandlerImpl.of(...)` связывает HTTP-метод, шаблон пути и вызов `_controller.hello()`.
        - Обработчик синхронный. Undertow переносит запрос на виртуальный поток до запуска этой лямбды, поэтому блокирующая работа в контроллере не блокирует IO-потоки сервера.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/gettingstarted/HelloController.kt`:

    ```kotlin
    package io.koraframework.guide.gettingstarted

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponse

    @Component //(1)!
    @HttpController //(2)!
    class HelloController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello") //(3)!
        fun hello(): HttpServerResponse {
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello, Kora!")) //(4)!
        }
    }
    ```

    1.  Регистрирует класс как компонент графа, чтобы Kora могла его создать и внедрить туда, где он нужен.
    2.  Говорит HTTP-обработчику просканировать класс на маршруты и сгенерировать модуль с обработчиками запросов.
    3.  Привязывает метод к `GET /hello`. В `HttpMethod` лежат стандартные названия HTTP-методов.
    4.  Формирует ответ явно: статус `200` и тело `text/plain`.

    ??? abstract "Kotlin: сгенерированный модуль маршрута `HelloControllerModule`"

        В Kotlin-приложении KSP создает файл `build/generated/ksp/main/kotlin/io/koraframework/guide/gettingstarted/HelloControllerModule.kt`:

        ```kotlin
        package io.koraframework.guide.gettingstarted

        import io.koraframework.common.`annotation`.Generated
        import io.koraframework.common.`annotation`.Module
        import io.koraframework.http.server.common.request.HttpServerRequestHandler
        import io.koraframework.http.server.common.request.HttpServerRequestHandlerImpl

        @Generated("io.koraframework.http.server.symbol.procesor.HttpControllerProcessor")
        @Module
        public interface HelloControllerModule {
          public fun get_hello(_controller: HelloController): HttpServerRequestHandler = HttpServerRequestHandlerImpl.of("GET", "/hello") process@{ _request ->
            val _result = _controller.hello()
            return@process _result
          }
        }
        ```

        Здесь видно Kotlin-специфику KSP-генерации:

        - Фабрика также помечена `@Module`, поэтому попадет в общий граф.
        - `get_hello(...)` возвращает `HttpServerRequestHandler` для `GET /hello`.
        - Лямбда помечена меткой `process@`, чтобы сгенерированный разбор параметров и код перехватчиков могли досрочно выйти из обработчика.
        - Обработчик синхронный, а `suspend`-методы контроллера процессор отклоняет с ошибкой компиляции.

## Конфигурация { #config }

Конфигурация — это место, где приложение получает значения времени выполнения без изменения исходного кода. Даже в этом первом приложении есть два HTTP-сервера: публичный для бизнес-маршрутов и
служебный для эксплуатационных маршрутов вроде проб readiness и liveness.

Создайте `src/main/resources/application.conf`:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system.port = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    logging {
      levels {
        "root": "WARN" //(4)!
        "io.koraframework": "INFO" //(5)!
      }
    }
    ```

    1.  Публичный HTTP-порт для маршрутов приложения (по умолчанию: `8080`).
    2.  Служебный HTTP-порт для проб, метрик и управляющих маршрутов (по умолчанию: `8085`).
    3.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4.  Уровень логирования корневого логгера.
    5.  Уровень логирования для логгеров фреймворка Kora.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    logging:
      levels:
        root: "WARN" #(4)!
        "io.koraframework": "INFO" #(5)!
    ```

    1.  Публичный HTTP-порт для маршрутов приложения (по умолчанию: `8080`).
    2.  Служебный HTTP-порт для проб, метрик и управляющих маршрутов (по умолчанию: `8085`).
    3.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4.  Уровень логирования корневого логгера.
    5.  Уровень логирования для логгеров фреймворка Kora.

Здесь показаны оба формата. В наборе зависимостей выше подключен `config-hocon`, который читает `application.conf`; если удобнее `application.yaml`, замените его на `config-yaml` и наследуйте
`YamlConfigModule`. Имена ключей в обоих форматах одинаковые.

У каждого ключа в этом файле уже есть значение по умолчанию, поэтому приложение стартует и вовсе без `application.conf` — именно на это полагаются эталонные приложения. Файл становится нужен, как
только требуется сменить порт, поднять уровень логирования или прочитать секрет из переменной окружения.

Полную справку по настройкам смотрите в документации [HTTP-сервер](../documentation/http-server.md), [журналирование SLF4J](../documentation/logging-slf4j.md) и [Config](../documentation/config.md).

## Запуск приложения { #run-app }

Перед запуском соберите проект. В Kora задача `classes` особенно полезна: она запускает обработку аннотаций и проверяет, что граф зависимостей вообще может быть сгенерирован:

```bash
./gradlew clean classes
```

Затем запустите приложение через плагин `application`, который использует `mainClass` из файла сборки:

```bash
./gradlew run
```

Лог запуска заканчивается строкой `Application initialized in ...`, когда граф построен и оба HTTP-сервера слушают свои порты.

## Проверка приложения { #check-app }

Когда приложение запущено, обратитесь к публичному маршруту через публичный HTTP-порт. Успешный ответ подтверждает, что модуль сервера стартовал, компонент-контроллер создан и сгенерированный
обработчик маршрута зарегистрирован.

```bash
curl http://localhost:8080/hello
# Expected output: Hello, Kora!
```

Служебный сервер работает в том же процессе на своем порту и отвечает на пробу readiness строкой `OK`:

```bash
curl http://localhost:8085/system/readiness
# Expected output: OK
```

## Сгенерированный код { #generated-code }

Kora — фреймворк, который выполняет основную работу во время компиляции. После `./gradlew classes` сгенерированные исходники показывают, как аннотации превращаются в обычный Java- или
Kotlin-код. Это один из лучших способов изучать фреймворк: если что-то кажется магией, откройте сгенерированные исходники и обычно вы увидите конкретную фабрику, узел графа или HTTP-обработчик,
который создала Kora.

Начните со сгенерированного модуля контроллера:

===! ":fontawesome-brands-java: `Java`"

    ```text
    build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/gettingstarted/HelloControllerModule.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    build/generated/ksp/main/kotlin/io/koraframework/guide/gettingstarted/HelloControllerModule.kt
    ```

В нем находится `HttpServerRequestHandler`, который Kora сгенерировала для `@HttpController` и `@HttpRoute`. Этот обработчик является мостом между входящим HTTP-запросом Undertow и обычным методом
вашего контроллера:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Generated("io.koraframework.http.server.annotation.processor.ControllerModuleGenerator")
    @Module
    public interface HelloControllerModule {
      default HttpServerRequestHandler get_hello(HelloController _controller) {
        return HttpServerRequestHandlerImpl.of("GET", "/hello", (_request) -> {
          return _controller.hello();
        });
      }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Generated("io.koraframework.http.server.symbol.procesor.HttpControllerProcessor")
    @Module
    public interface HelloControllerModule {
      public fun get_hello(_controller: HelloController): HttpServerRequestHandler = HttpServerRequestHandlerImpl.of("GET", "/hello") process@{ _request ->
        val _result = _controller.hello()
        return@process _result
      }
    }
    ```

Затем посмотрите сгенерированный граф приложения:

===! ":fontawesome-brands-java: `Java`"

    ```text
    build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/gettingstarted/ApplicationGraph.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    build/generated/ksp/main/kotlin/io/koraframework/guide/gettingstarted/ApplicationGraph.kt
    ```

Вы увидите, что Kora регистрирует контроллер, а затем регистрирует сгенерированный HTTP-обработчик, который зависит от этого контроллера. Эта зависимость важна: обработчик не может существовать без
экземпляра контроллера, и граф фиксирует эту связь явно — и в списке узлов, нужных для создания, и в фабричной лямбде:

===! ":fontawesome-brands-java: `Java`"

    ```java
    component21 = graphDraw.addNode(_type_of_component21,
        null, null, List.of(), List.of(), List.of(),
        g -> new HelloController());

    component26 = graphDraw.addNode(_type_of_component26,
        null, null, List.of(component21), List.of(component21), List.of(),
        g -> impl.module0.get_hello(
          g.get(ApplicationGraph.holder0.component21)
        ));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    component26 = graphDraw.addNode(map["component26"],
      null, null, listOf(), listOf(), listOf(),
      { HelloController() }
    )

    component31 = graphDraw.addNode(map["component31"],
      null, null, listOf(component26), listOf(component26), listOf(),
      { impl.module0.get_hello(
        it.get(holder0.component26)
      ) }
    )
    ```

Это первый практический взгляд на ключевую идею Kora:

- ваш исходный код объявляет компоненты и маршруты
- обработчики аннотаций генерируют граф и обработчики маршрутов
- запуск приложения использует сгенерированный граф вместо поиска компонентов через reflection

Сгенерированные исходники также полезны для нейро-ассистентов и разбора работы приложения. В них видно точное скомпилированное связывание компонентов, поэтому можно посмотреть, как фреймворк соединил
части приложения, а не гадать только по аннотациям.

## Лучшие практики { #best-practices }

Эти практики выглядят мелочами, но они масштабируются на все следующие руководства. Приложение на Kora проще всего поддерживать, когда корень графа явный, контроллеры занимаются только протоколом, а в
сгенерированный код не страшно заглянуть во время отладки.

- Держите граф приложения в одной точке входа `@KoraApp`. Так проще видеть, какие модули инфраструктуры подключены к сервису, и где начинается сборка приложения.
- Подключайте модули фреймворка явно через `extends`. Это делает зависимости приложения читаемыми: по корневому интерфейсу сразу видно, что сервис использует HTTP, HOCON, JSON и Logback.
- Оставляйте контроллеры тонкими и переносите бизнес-логику в сервисы, когда сложность растет. В первом руководстве контроллер сам возвращает строку, но в настоящем API он обычно только принимает
  HTTP-запрос, вызывает сервис и формирует HTTP-ответ.
- Пишите методы контроллеров синхронно. Kora выполняет каждый запрос на виртуальном потоке, поэтому обычный блокирующий код — это и есть нужный стиль, а реактивные обертки ничего не добавляют.
- Запускайте `./gradlew classes` после добавления новых компонентов. Внедрение зависимостей на этапе компиляции хорошо тем, что многие ошибки зависимостей находятся сразу при сборке, а не во
  время первого запроса при выполнении приложения.
- Изучайте сгенерированные исходники, если хотите понять, что Kora скомпилировала из ваших аннотаций. Это помогает быстрее найти реальное связывание компонентов.

## Итоги { #summary }

Первое приложение получилось маленьким, но оно уже прошло полный цикл разработки на Kora: объявить модули, добавить компонент, скомпилировать сгенерированный код, запустить граф и вызвать маршрут.

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
- `UndertowPublicHttpServerModule` поднимает и публичный сервер, и служебный сервер с маршрутами проб.
- Сгенерированные исходники показывают код графа приложения и обработчик маршрута.

## Устранение неполадок { #troubleshooting }

**Сборка падает с ошибками сгенерированного графа**

Ошибки сгенерированного графа обычно означают, что Kora не смогла построить граф зависимостей: не настроена обработка аннотаций, не подключен нужный модуль фреймворка или конструктор компонента
просит зависимость, которую никто не предоставляет.

- Проверьте, что обработка аннотаций настроена: `annotationProcessor "io.koraframework:annotation-processors"` для Java или `ksp("io.koraframework:symbol-processors:<version>")` для Kotlin.
- Проверьте, что корневой интерфейс помечен `@KoraApp` и расширяет нужные модули Kora.
- Проверьте, что все классы с `@Component` доступны из набора исходных файлов приложения и находятся в корректном пакете.
- Если ошибка говорит о недостающей зависимости, прочитайте ее как обычный граф зависимостей: Kora показывает, какой тип пыталась создать и какого компонента не хватило.

**Сборка падает с `Dependency requires at least JVM runtime version 25`**

- Модули Kora публикуются под Java 25. Укажите в toolchain JDK 25 или новее и запускайте сам Gradle на том же JDK.
- Проверяйте, какой JDK реально использует Gradle, командой `./gradlew -version`, а не только `java -version`.

**Ошибки обработчиков не исчезают после исправления исходников**

- Обработчики аннотаций и KSP могут читать устаревший вывод предыдущей сборки. Прежде чем искать причину дальше, выполните `./gradlew clean classes`.

**Приложение не запускается на порту 8080**

- Проверьте `application.conf` и доступность порта.
- Убедитесь, что другой процесс не использует `8080`, и помните, что в том же процессе служебный сервер занимает `8085`.

**Smoke-check служебного API (`8085`)**

- Проверьте, что служебный маршрут доступен:

  ```bash
  curl http://localhost:8085/system/readiness
  ```

- Если маршрут недоступен, проверьте `httpServer.system.port` и `httpServer.system.readinessPath` в `application.conf` и логи запуска приложения. Значения по умолчанию — `8085` и `/system/readiness`.

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
- проверьте [документацию по пробам](../documentation/probes.md)
- посмотрите [пример Hello World](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-helloworld)
