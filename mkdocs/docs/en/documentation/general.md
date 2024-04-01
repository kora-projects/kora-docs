Kora provides all the tools needed for modern Java/Kotlin development:

- Dependency injection and inversion at compile time via annotations
- Aspect-oriented programming via annotations
- Pre-configurable integration modules
- Easy and rapid testing with [JUnit5](junit5.md)
- Simple, clear and detailed documentation backed by [service examples](../examples/kora-examples.md)

In order to achieve high-performance and efficient code, Kora stands on these principles:

- Using annotation handlers
- Not using Reflection API
- Avoiding dynamic proxies
- Implementing fine-grained abstractions
- Implementing complimentary aspects through class inheritance
- Using the most efficient implementations for modules
- Implementing and providing the most efficient principles for development
- No bytecode generation at compile time and runtime

## Annotation Handlers

The main pillar on which the Kora framework is built is annotation handlers.

=== ":fontawesome-brands-java: `Java`"

    An annotation is a construct associated with Java source code elements such as classes, methods, and variables.
    Annotations provide the program with information at compile time based on which the program can take further action.
    The [Annotation Processor](https://docs.oracle.com/javase/8/docs/api/javax/annotation/processing/Processor.html) processes these annotations at compile time to provide functions such as code generation, error checking, etc.

    Kora provides within a single dependency all the [annotation processors](https://docs.oracle.com/javase/8/docs/api/javax/annotation/processing/Processor.html) that will be required for all modules, 
    processors do not pull in any unnecessary dependencies that would leak at compile time or application runtime.

=== ":simple-kotlin: `Kotlin`"

    [Kotlin Symbol Processing (KSP)](https://kotlinlang.org/docs/ksp-overview.html) is an API that can be used to develop lightweight plugins for compilers.
    KSP is a simplified API for compiler plugins that allows you to utilize the features of Kotlin
    while minimizing the learning curve. Compared to kapt, annotation processors using KSP can run twice as fast (still drastically slower than Java).

    Another way to think of [KSP](https://kotlinlang.org/docs/ksp-overview.html) is as a preprocessor framework for Kotlin programs. If we think of KSP-based plugins as symbolic processors, or simply processors, the data flow at compile time can be described by the following steps:

    - Processors read and analyze source programs and resources.
    - Processors generate code or other forms of output.
    - The Kotlin compiler compiles the source programs along with the generated code.

This approach allows you to use the familiar paradigm of programming by means of creating HTTP handlers,
Kafka producers, database repositories and so on, but gives a huge performance and transparency advantage over the well-known JVM frameworks.

## Compatibility

=== ":fontawesome-brands-java: `Java`"

    Requires a minimum version of [JDK 17](https://openjdk.org/projects/jdk/17/).

    Configuration in `build.gradle`:
    ```groovy
    plugins {
        id "java"
        id "application"
    }   

    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
    ```

=== ":simple-kotlin: `Kotlin`"

    Requires a minimum version of [JDK 17](https://openjdk.org/projects/jdk/17/).

    Recommended version of [Kotlin `1.9+`](https://github.com/JetBrains/kotlin/releases), compatibility with `1.8+` is not guaranteed.

    Recommended version of [KSP `1.9+`](https://github.com/google/ksp/releases) corresponds to the Kotlin version.

    Configuration in `build.gradle.kts`:
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

## Build System

Since annotation handlers are the main pillar, it is assumed that you will use the [Gradle](https://gradle.org/guides/) build system,
because it supports annotation handlers, incremental builds and is the most advanced build system in the JVM ecosystem.
Gradle version `7+` is required.

In order to avoid having to specify versions for each dependency, it is suggested to use [BOM](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import)
dependency `ru.tinkoff.kora:kora-parent` which requires to specify the version once for all Kora dependencies at once.

=== ":fontawesome-brands-java: `Java`"

    Kora supports incremental builds of multiple rounds at the annotation processing stage,
    a more detailed description of working with Gradle and Java can be found in their [official documentation](https://docs.gradle.org/current/userguide/java_plugin.html).

    The minimum required configuration of the application will be presented below `build.gradle`:
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
        koraBom platform("ru.tinkoff.kora:kora-parent:1.0.8")
        annotationProcessor "ru.tinkoff.kora:annotation-processors"
    }
    ```

    You can also check out [Hello World example](../examples/hello-world.md) for a more detailed description.

=== ":simple-kotlin: `Kotlin`"

    Kora supports incremental builds of multiple rounds at the annotation processing stage,
    a more detailed description of working with Gradle and Kotlin can be found in their [official documentation](https://kotlinlang.org/docs/get-started-with-jvm-gradle-project.html),
    and it will also be useful to familiarize yourself with [KSP in Gradle](https://kotlinlang.org/docs/ksp-quickstart.html).

    For Kotlin it is assumed that [Gradle Kotlin DSL](https://docs.gradle.org/current/userguide/kotlin_dsl.html) will be used,
    so all examples for Kotlin will be given in this syntax, if you use Groovy syntax, use Java examples.

    The minimum required configuration of the application will be presented below `build.gradle.kts`:
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
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.0.8"))
        ksp("ru.tinkoff.kora:symbol-processors")
    }

    kotlin {
        jvmToolchain { languageVersion.set(JavaLanguageVersion.of("17")) }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }
    ```

    You can also check out [Hello World example](../examples/hello-world.md) for a more detailed description.
