Kora является облачно ориентированным серверным фреймворком написанным на Java и предлагает
множество различных модулей для быстрого создания приложений такие как HTTP сервер и клиент, Kafka потребители, 
абстракция над базой данных в виде репозиториев, S3-клиент, gRPC сервер и клиент, интеграции с Camunda,
телеметрию всех модулей, модули отказоустойчивости и многое другое.

Прочитать про основные характеристики Kora можно [перейдя по ссылке](../index.md).

Kora предоставляет все необходимые для современной Java или Kotlin серверной разработки инструменты:

- Внедрение и инверсию зависимостей посредствам аннотаций
- Достаточно высокоуровневые простые абстракции и инструменты разработки
- Аспектно-ориентированное программирование посредствам аннотаций
- Большой набор пред-сконфигурированных интеграций
- Трассировка и метрики по `OpenTelemetry` стандарту и логгирование всех модулей
- Легкое и быстрое тестирование с помощью [JUnit5](junit5.md)
- Простая и подробная документация подкрепленная [примерами рабочих сервисов](../examples/kora-examples.md)

Для достижения высокопроизводительного и эффективного кода, Kora стоит на таких принципах:

- Отказ от использования Reflection API во время работы
- Отказ от динамических прокси во время работы
- Отказ от генерации байт-кода во время компиляции и работы
- Создание исходного кода посредствам обработчиков аннотаций во время компиляции
- Тонкие абстракции над модулями
- Бесплатные аспекты
- Использование только наиболее эффективных реализаций для интеграций
- Поощрение и использование наиболее эффективных принципов разработки и естественных конструкций языка

## Обработчики аннотаций

Главный столп на котором строится фреймворк Kora это обработчики аннотаций.

===! ":fontawesome-brands-java: `Java`"

    Аннотация - это конструкция, связанная с элементами исходного кода Java, такими как классы, методы и переменные. 
    Аннотации предоставляют программе информацию во время компиляции на основе которой программа может предпринять дальнейшие действия. 
    [Процессор аннотаций](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/annotation/processing/Processor.html) обрабатывает эти аннотации во время компиляции для обеспечения таких функций, как генерация кода, проверка ошибок и т.д.

    Kora предоставляет в рамках одной зависимости все [обработчики аннотаций](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/annotation/processing/Processor.html), которые потребуются для работы со всеми модулями, 
    процессоры не тянут за собой никакие лишние зависимости которые протекали бы во время компиляции или выполнения приложения.

=== ":simple-kotlin: `Kotlin`"

    [Kotlin Symbol Processing (KSP)](https://kotlinlang.org/docs/ksp-overview.html) - это API, который можно использовать для разработки легких плагинов для компиляторов. 
    KSP представляет собой упрощенный API для плагинов к компиляторам, который позволяет использовать возможности Kotlin 
    при минимальной кривой обучения. По сравнению с kapt, процессоры аннотаций, использующие KSP, могут работать в два раза быстрее (но в разы медленее чем Java).

    Другой способ представить [KSP](https://kotlinlang.org/docs/ksp-overview.html) как препроцессорный фреймворк программ на языке Kotlin. Если рассматривать плагины на базе KSP как символьные процессоры, или просто процессоры, то поток данных при компиляции можно описать следующими шагами:

    - Процессоры читают и анализируют исходные программы и ресурсы.
    - Процессоры генерируют код или другие формы вывода.
    - Компилятор Kotlin компилирует исходные программы вместе со сгенерированным кодом.

Такой подход позволяет использовать привычную всем парадигму программирования посредствам создания с помощью аннотаций HTTP-обработчиков,
Kafka продюсеров, репозиториев баз данных и так далее, но дает огромный выйгрыш в производительности и прозрачности относительно известных всем JVM фреймворков.

## Совместимость

===! ":fontawesome-brands-java: `Java`"

    Требуется версия не ниже [JDK 17](https://openjdk.org/projects/jdk/17/).

    Конфигурация в `build.gradle`:
    ```groovy
    plugins {
        id "java"
    }   

    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
    ```

=== ":simple-kotlin: `Kotlin`"

    Требуется версия не ниже [JDK 17](https://openjdk.org/projects/jdk/17/).

    Рекомендуемая версия [Kotlin `1.9+`](https://github.com/JetBrains/kotlin/releases), совместимость с версией `1.8+` и `2+` не гарантируется.

    Рекомендуемая версия [KSP `1.9+`](https://github.com/google/ksp/releases) соответсвующая версии Kotlin.

    Конфигурация в `build.gradle.kts`:
    ```groovy
    plugins {
        kotlin("jvm") version ("1.9.10")
        id("com.google.devtools.ksp") version ("1.9.10-1.0.13")
    }

    kotlin {
        jvmToolchain { languageVersion.set(JavaLanguageVersion.of("17")) }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }
    ```

## Система сборки

Поскольку основным столпом являются обработчики аннотаций, то подразумевается что вы будете использовать именно систему сборки [Gradle](https://gradle.org/guides/),
так как она лучше других поддерживает обработчики аннотаций, инкрементальную сборку и является наиболее совершенной системой сборки в JVM экосистеме.
Требуется версия Gradle `7+`.

Для того чтобы не прописывать версии для каждой зависимости, предполагается использовать [BOM](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import)
зависимость `ru.tinkoff.kora:kora-parent` в которой требуется один раз указать версию для всех Kora зависимостей разом.

===! ":fontawesome-brands-java: `Java`"

    Kora поддерживает инкрементальную сборку из нескольких раундов на этапе обработки аннотаций,
    более подробное описание по работе с Gradle и Java можно почитать в их [официальной документации](https://docs.gradle.org/current/userguide/java_plugin.html).

    Ниже будет представлена минимально необходимая конфигурация приложения `build.gradle`:
    ```groovy
    plugins {
        id "java"
        id "application"
    }   

    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17

    configurations {
        koraBom
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        api.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("ru.tinkoff.kora:kora-parent:1.1.24")
        annotationProcessor "ru.tinkoff.kora:annotation-processors"
    }
    ```

    Также можно ознакомиться с [ознакомительным примером](../examples/hello-world.md) с более подробным описанием.

=== ":simple-kotlin: `Kotlin`"

    Kora поддерживает инкрементальную сборку из нескольких раундов на этапе обработки аннотаций,
    более подробное описание по работе с Gradle и Kotlin можно почитать в их [официальной документации](https://kotlinlang.org/docs/get-started-with-jvm-gradle-project.html),
    а также будет полезно ознакомиться с работой [KSP в Gradle](https://kotlinlang.org/docs/ksp-quickstart.html)

    Для Kotlin предполагается что будет использоваться [Gradle Kotlin DSL](https://docs.gradle.org/current/userguide/kotlin_dsl.html),
    так что все примеры для Kotlin будут даваться именно в этом синтаксисе, если вы используете Groovy синтаксис, то используйте Java примеры.

    Ниже будет представлена минимально необходимая конфигурация приложения `build.gradle.kts`:
    ```groovy
    plugins {
        id("application")
        kotlin("jvm") version ("1.9.10")
        id("com.google.devtools.ksp") version ("1.9.10-1.0.13")
    }

    kotlin {
        jvmToolchain { languageVersion.set(JavaLanguageVersion.of("17")) }
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
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.1.24"))
        ksp("ru.tinkoff.kora:symbol-processors")
    }
    ```

    Также можно ознакомиться с [ознакомительным примером](../examples/hello-world.md) с более подробным описанием.

## Зависимости

Так как основным столпом на котором строится Kora являются обработчики аннотаций, то они являются обязательной зависимостью,
также не стоит забывать и о [BOM зависимости](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import):

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
        koraBom platform("ru.tinkoff.kora:kora-parent:1.1.24")
        annotationProcessor "ru.tinkoff.kora:annotation-processors"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:

    ```groovy
    val koraBom: Configuration by configurations.creating
    configurations {
        ksp.get().extendsFrom(koraBom)
        compileOnly.get().extendsFrom(koraBom)
        api.get().extendsFrom(koraBom)
        implementation.get().extendsFrom(koraBom)
    }

    dependencies {
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.1.24"))
        ksp("ru.tinkoff.kora:symbol-processors")
    }
    ```

## Запуск

Запускать и работать с приложением через систему сборки, предполагается с помощью [application плагина](https://docs.gradle.org/current/userguide/application_plugin.html)
который предоставляет Gradle.

===! ":fontawesome-brands-java: `Java`"

    Требуется указать плагин в `build.gradle`:
    ```groovy
    plugins {
        id "application"
    }
    ```

    Можно указывать как системные переменные, так и переменные окружения при локальном запуске приложения в `build.gradle`:
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

    Запускать надо с помощью команды:
    ```shell
    ./gradlew run
    ```

    Настроить сборку артефакта можно таким способом в `build.gradle`:
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

    Собирать артефакт можно командой:
    ```shell
    ./gradlew distTar
    ```

    Пример настроенного приложения можно посмотреть [тут](https://github.com/kora-projects/kora-java-crud-template/blob/master/build.gradle)

=== ":simple-kotlin: `Kotlin`"

    Требуется указать плагин в `build.gradle`:
    ```groovy
    plugins {
        id("application")
        kotlin("jvm") version ("1.9.10")
        id("com.google.devtools.ksp") version ("1.9.10-1.0.13")
    }
    ```

    Можно указывать как системные переменные, так и переменные окружения при локальном запуске приложения в `build.gradle.kts`:
    ```groovy
    tasks.withType<JavaExec> {
        jvmArgs(
            "-Xmx256m",
        )

        environment(
            "SOME_ENV" to "someValue",
        )
    }
    ```

    Запускать надо с помощью команды:
    ```shell
    ./gradlew run
    ```

    Настроить сборку артефакта можно таким способом:
    ```groovy
    application {
        applicationName = "application"
        mainClass.set("ru.tinkoff.kora.kotlin.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }

    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

    Собирать артефакт можно командой:
    ```shell
    ./gradlew distTar
    ```

    Пример настроенного приложения можно посмотреть [тут](https://github.com/kora-projects/kora-kotlin-crud-template/blob/master/build.gradle.kts)

## Терминология

В данной секции описываются основные термины которые встречаются во всей документации и в рамках фреймворка Kora:

- Фабрика - под фабрикой подразумевается метод который, создает экземпляры компонент/классов/зависимостей.
- Модуль - под [модулем](container.md#_7) понимается подключаемая зависимость, зачастую внешняя которая предоставляет какие-то фабричные методы и новый функционал в приложение.
- Компонент - под [компонентом](container.md#_3) понимается класс в одном экземпляре (`Singleton`) который реализует какую то логику и является зависимостью в контейнере зависимостей.
- Аспект - под аспектом подразумевается логика которая будет расширять стандартное поведение метода посредствам какой-либо аннотации до и/или после его выполнения.
