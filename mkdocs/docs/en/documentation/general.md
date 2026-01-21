Kora is a cloud-oriented server-side Java framework and offers
many different modules for quickly building applications such as HTTP server and client, Kafka consumers, 
database abstraction in the form of repositories, S3 client, gRPC server and client,
Camunda integration, telemetry for all modules, resilient module and much more.

You can read about the core features of Kora [on home page](../index.md).

Kora provides all the tools needed for modern Java or Kotlin server-side development:

- Dependency injection and inversion via annotations
- Sufficiently high-level simple abstractions and development tools
- Aspect-oriented programming via annotations
- Large set of preconfigured integrations
- Observability, tracing, metrics according to `OpenTelemetry` standard and logging for all modules
- Easy and rapid testing with [JUnit5](junit5.md)
- Simple and detailed documentation supported by [examples of working services](../examples/kora-examples.md)

In order to achieve high-performance and efficient code, Kora stands on these principles:

- Avoiding Reflection API in runtime
- Avoiding dynamic proxies in runtime
- Avoiding bytecode generation at compile time and runtime
- Source code generation via compile-time annotation processors
- Fine-grained abstractions
- Free aspects
- Using the most efficient implementations for integrations
- Encouraging and using effective programming practices and natural language constructs

## Annotation Handlers

The main pillar on which the Kora framework is built is annotation processors.

===! ":fontawesome-brands-java: `Java`"

    An annotation is a construct associated with Java source code elements such as classes, methods, and variables.
    Annotations provide the program with information at compile time based on which the program can take further action.
    The [Annotation Processor](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/annotation/processing/Processor.html) processes these annotations at compile time to provide functions such as code generation, error checking, etc.

    Kora provides within a single dependency all the [annotation processors](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/annotation/processing/Processor.html) that will be required for all modules, 
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

===! ":fontawesome-brands-java: `Java`"

    Requires a minimum version of [JDK 17](https://openjdk.org/projects/jdk/17/).

    Configuration in `build.gradle`:
    ```groovy
    plugins {
        id "java"
    }   

    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
    ```

=== ":simple-kotlin: `Kotlin`"

    Requires a minimum version of [JDK 17](https://openjdk.org/projects/jdk/17/).

    Recommended version of [Kotlin `1.9+`](https://github.com/JetBrains/kotlin/releases), compatibility with `1.8+` or `2+` is not guaranteed.

    Recommended version of [KSP `1.9+`](https://github.com/google/ksp/releases) corresponds to the Kotlin version.

    Configuration in `build.gradle.kts`:
    ```groovy
    plugins {
        kotlin("jvm") version ("1.9.25")
        id("com.google.devtools.ksp") version ("1.9.25-1.0.20")
    }

    kotlin {
        jvmToolchain { languageVersion.set(JavaLanguageVersion.of("17")) }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }
    ```

## Build System

Since annotation processors are the main pillar, it is assumed that you will use the [Gradle](https://gradle.org/guides/) build system,
because it supports annotation processors, incremental builds and is the most advanced build system in the JVM ecosystem.
Gradle version `7+` is required.

In order to avoid having to specify versions for each dependency, it is suggested to use [BOM](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import)
dependency `ru.tinkoff.kora:kora-parent` which requires to specify the version once for all Kora dependencies at once.

===! ":fontawesome-brands-java: `Java`"

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
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        api.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("ru.tinkoff.kora:kora-parent:1.2.8")
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
        kotlin("jvm") version ("1.9.25")
        id("com.google.devtools.ksp") version ("1.9.25-1.0.20")
        id("application")
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
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.2.8"))
        ksp("ru.tinkoff.kora:symbol-processors")
    }
    ```

    You can also check out [Hello World example](../examples/hello-world.md) for a more detailed description.

## Dependencies

Annotation processors are the main pillar on which Kora is built, they are a mandatory dependency,
and the [BOM dependency](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import) should not be forgotten:

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
        koraBom platform("ru.tinkoff.kora:kora-parent:1.2.8")
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
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.2.8"))
        ksp("ru.tinkoff.kora:symbol-processors")
    }
    ```

## Run

Running and working with the application through the build system is supposed to be done using the [application plugin](https://docs.gradle.org/current/userguide/application_plugin.html)
which is provided by Gradle.

===! ":fontawesome-brands-java: `Java`"

    Requires the plugin to be specified in `build.gradle`:
    ```groovy
    plugins {
        id "application"
    }
    ```

    You can specify both system variables and environment variables when running the application locally in `build.gradle`:
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

    You can run it with command:
    ```shell
    ./gradlew run
    ```

    You can configure the artifact build this way in `build.gradle`:
    ```groovy
    applicationName = "application"
    mainClassName = "ru.tinkoff.kora.java.Application"

    application {
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"]
    }

    distTar {
        archiveFileName = "application.tar"
    }
    ```

    You can build an artifact with the command:
    ```shell
    ./gradlew distTar
    ```

    Example of configured application can be seen [here](https://github.com/kora-projects/kora-java-template/blob/master/build.gradle)

=== ":simple-kotlin: `Kotlin`"

    Requires the plugin to be specified in `build.gradle.kts`:
    ```groovy
    plugins {
        id("application")
        kotlin("jvm") version ("1.9.25")
        id("com.google.devtools.ksp") version ("1.9.25-1.0.20")
    }
    ```

    You can specify both system variables and environment variables when running the application locally in `build.gradle.kts`:
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

    You can run it with command:
    ```shell
    ./gradlew run
    ```

    You can configure the artifact build this way in `build.gradle.kts`:
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

    You can build an artifact with the command:
    ```shell
    ./gradlew distTar
    ```

    Example of configured application can be seen [here](https://github.com/kora-projects/kora-kotlin-template/blob/master/build.gradle.kts)

## Terminology

This section describes the basic terms found throughout the documentation and within the Kora framework:

- Factory - is factory a method that, creates instances of a component/classes/dependencies.
- Module - [module](container.md#external-factory) is a pluggable dependency, often external, that provides some factory methods and new functionality to the application.
- Component - [component](container.md#components) is a singleton class that implements some logic and is a dependency in a dependency container.
- Aspect - is aspect logic that will extend the standard behavior of a method by via annotation before and/or after its execution.
