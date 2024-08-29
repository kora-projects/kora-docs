Kora является облачно ориентированным серверным фреймворком и предлагает
множество различных модулей для быстрого создания приложений такие как HTTP сервер, Kafka потребители, абстракция над базой данных в виде репозиториев и многое другое.

Kora предоставляет все необходимые для современной Java / Kotlin разработки инструменты:

- Внедрение и инверсию зависимостей на этапе компиляции посредствам аннотаций
- Создание декларативно описанных с помощью аннотаций компонент во время компиляции
- Аспектно-ориентированное программирование посредствам аннотаций
- Пре-конфигурируемые модули интеграций
- Легкое и быстрое тестирование с помощью [JUnit5](junit5.md)
- Простая, понятная и подробная документация подкрепленная [примерами сервисов](../examples/kora-examples.md)

Для достижения высокопроизводительного и эффективного кода, Kora стоит на таких принципах:

- Создание исходного кода посредствам обработчиков аннотаций во время компиляции
- Отказ от использования Reflection API во время работы
- Отказ от динамических прокси
- Тонкие абстракции
- Бесплатные аспекты через наследование классов
- Использование наиболее эффективных реализаций для модулей
- Реализацию и предоставление наиболее эффективных принципов для разработки и естественных конструкций языка
- Отсутствие генерации байт-кода во время компиляции и исполнения

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
        id "application"
    }   

    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
    ```

=== ":simple-kotlin: `Kotlin`"

    Требуется версия не ниже [JDK 17](https://openjdk.org/projects/jdk/17/).

    Рекомендуемая версия [Kotlin `1.9+`](https://github.com/JetBrains/kotlin/releases), совместимость с версией `1.8+` не гарантируется.

    Рекомендуемая версия [KSP `1.9+`](https://github.com/google/ksp/releases) соответсвующая версии Kotlin.

    Конфигурация в `build.gradle.kts`:
    ```groovy
    plugins {
        kotlin("jvm") version ("1.9.10")
        id("com.google.devtools.ksp") version ("1.9.10-1.0.13")
        id("application")
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
        implementation.extendsFrom(koraBom)
        annotationProcessor.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("ru.tinkoff.kora:kora-parent:1.1.8")
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
        kotlin("jvm") version ("1.9.10")
        id("com.google.devtools.ksp") version ("1.9.10-1.0.13")
        id("application")
    }

    val koraBom: Configuration by configurations.creating
    configurations {
        ksp.get().extendsFrom(koraBom)
        api.get().extendsFrom(koraBom)
        implementation.get().extendsFrom(koraBom)
    }

    dependencies {
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.1.8"))
        ksp("ru.tinkoff.kora:symbol-processors")
    }

    kotlin {
        jvmToolchain { languageVersion.set(JavaLanguageVersion.of("17")) }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }
    ```

    Также можно ознакомиться с [ознакомительным примером](../examples/hello-world.md) с более подробным описанием.

## Терминология

В данной секции описываются основные термины которые встречаются во всей документации и в рамках фреймворка Kora:

- Фабрика - под фабрикой подразумевается метод который, создает экземпляры компонент/классов/зависимостей.
- Модуль - под [модулем](container.md#_7) понимается подключаемая зависимость, зачастую внешняя которая предоставляет какие-то фабричные методы и новый функционал в приложение.
- Компонент - под [компонентом](container.md#_3) понимается класс синглтон (Singleton) который реализует какую то логику и является зависимостью в контейнере зависимостей.
- Аспект - под аспектом подразумевается логика которая будет расширять стандартное поведение метода посредствам какой-либо аннотации до и/или после его выполнения.
