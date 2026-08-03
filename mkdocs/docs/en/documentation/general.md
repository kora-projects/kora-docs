---
description: "Explains Kora framework fundamentals, annotation processors, compatibility, Gradle build setup, dependencies, application runtime, and terminology. Use when working with @KoraApp, annotation processors, Gradle, BOM, kora-parent, application plugin."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora framework fundamentals, annotation processors, Gradle, BOM, kora-parent, application plugin."
---

Kora is a cloud-oriented server framework written in `Java` for applications written in `Java` and `Kotlin`.
This page describes the basic principles of Kora, environment requirements, annotation processor setup, minimal `Gradle` configuration, dependency management, and application startup.

Kora provides a set of modules for quickly building server applications: `HTTP` server and `HTTP` client, `Kafka` consumers, repositories for working with databases, `S3` client, `gRPC` server and `gRPC` client, `Camunda` integrations, module telemetry, resilience, and other capabilities.
The main framework characteristics are described [on the home page](../index.md).

Kora provides the tools usually needed for modern server-side development:

- dependency injection through annotations;
- inversion of control without a separate container at runtime;
- aspect-oriented programming through annotations;
- sufficiently high-level simple abstractions and development tools;
- a large set of preconfigured integrations;
- telemetry, tracing, metrics according to the `OpenTelemetry` standard, and module logging;
- fast testing with [JUnit5](junit5.md);
- working [examples and guides](../guides/home.md).

For high-performance, efficient, and predictable code, Kora follows these principles:

- does not use `Reflection` during application runtime;
- does not use `dynamic proxy` during application runtime;
- does not generate bytecode during compilation or application runtime;
- creates source code at compile time through annotation processors;
- keeps thin abstractions over integrations;
- provides free aspects: without additional cost during application runtime;
- uses only the most efficient implementations for integrations;
- encourages and uses the most effective development principles and natural language constructs.

If you need a step-by-step walkthrough before the reference description, see [Creating Your First Kora Application](../guides/getting-started.md) and [Dependency Injection Introduction](../guides/dependency-injection-introduction.md).

## Annotation Processors { #annotation-processor }

Kora builds the application at compile time: processors read annotations, validate the code, and generate source files that are then compiled together with the application code.
As a result, the dependency graph, aspects, `HTTP` handlers, repositories, and other components become ordinary compiled code without `Reflection` at runtime.

===! ":fontawesome-brands-java: `Java`"

    An annotation is a construct associated with `Java` source code elements: classes, methods, parameters, and fields.
    An [annotation processor](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/annotation/processing/Processor.html) is started by the compiler, reads these annotations, and can generate additional source code or stop compilation with a clear error.

    Kora provides all annotation processors in a single dependency:

    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    ```

    This dependency is needed only at compile time and does not add extra libraries to the application runtime classpath.

=== ":simple-kotlin: `Kotlin`"

    [`KSP`](https://kotlinlang.org/docs/ksp-overview.html) (`Kotlin Symbol Processing`) is used for `Kotlin`.
    `KSP` reads `Kotlin` source code symbols, passes them to Kora processors, and allows code generation before the main compilation step.

    Kora provides `KSP` processors in a single dependency:

    ```kotlin
    ksp("ru.tinkoff.kora:symbol-processors")
    ```

    At the same time, `Kotlin` processing is usually slower than annotation processing in `Java`.

### `KSP` { #ksp }

`KSP` is needed only for `Kotlin` projects.
If the application is written in `Java`, use the regular `annotationProcessor`; if the application is written in `Kotlin`, connect `com.google.devtools.ksp` and the `ru.tinkoff.kora:symbol-processors` dependency.

## Compatibility { #compatibility }

===! ":fontawesome-brands-java: `Java`"

    Requires at least [JDK 17](https://openjdk.org/projects/jdk/17/), recommended to always use the latest JDK version, or at minimum [`JDK` `25+`](https://openjdk.org/projects/jdk/25/), to unlock all capabilities of virtual threads.

    Minimal configuration in `build.gradle`:
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

    The `vendor` pin is optional and simply matches the `Adoptium` toolchain used by the example projects; you may omit it or select another vendor.

=== ":simple-kotlin: `Kotlin`"

    Requires at least [JDK 17](https://openjdk.org/projects/jdk/17/), recommended [`JDK` `21`](https://openjdk.org/projects/jdk/21/) because Kotlin versions `1.9+` don't stably support higher JDK versions.

    Recommended and supported [`Kotlin` `1.9+`](https://github.com/JetBrains/kotlin/releases), compatibility with versions `1.8+` and `2+` is not guaranteed.
    Recommended and supported [`KSP` `1.9+`](https://github.com/google/ksp/releases) should match the `Kotlin` version.

    Minimal configuration in `build.gradle.kts`:
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

## Build System { #build-system }

Kora is designed to be built with [Gradle](https://gradle.org/guides/) because `Gradle` has good support for annotation processors, `KSP`, incremental builds, and dependency management.
Requires `Gradle` `7+`, recommended `Gradle` `9.5+`.

To avoid specifying versions for each Kora dependency separately, use the [`BOM`](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import) `ru.tinkoff.kora:kora-parent`.
The `BOM` version is specified once, and the rest of the Kora dependencies are declared without an explicit version.

===! ":fontawesome-brands-java: `Java`"

    Minimal application configuration in `build.gradle`:
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
        annotationProcessor "ru.tinkoff.kora:annotation-processors:1.2.19"
        implementation platform("ru.tinkoff.kora:kora-parent:1.2.19")
    }
    ```

    A more detailed example is available in [Creating Your First Kora Application](../guides/getting-started.md).

=== ":simple-kotlin: `Kotlin`"

    [Gradle Kotlin DSL](https://docs.gradle.org/current/userguide/kotlin_dsl.html) is assumed for `Kotlin`.
    If the project uses `Groovy DSL`, follow the `Java` examples.

    Minimal application configuration in `build.gradle.kts`:
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
        ksp("ru.tinkoff.kora:symbol-processors:1.2.19")
        implementation(platform("ru.tinkoff.kora:kora-parent:1.2.19"))
    }
    ```

    A more detailed example is available in [Creating Your First Kora Application](../guides/getting-started.md).

In real projects the `BOM` version is usually extracted into a `gradle.properties` property (for example `koraVersion`) and referenced as `platform("ru.tinkoff.kora:kora-parent:$koraVersion")`, so the version is declared in a single place instead of being hardcoded in every module.

!!! note "Compiler internal access"

    Some `Java` annotation processors read `jdk.compiler` internals. On newer `JDK`s this may require exporting the corresponding packages to the compiler.
    If compilation fails with `IllegalAccessError` or `module jdk.compiler does not export ...` errors, add the following `JVM` arguments to `gradle.properties`:

    ```properties
    org.gradle.jvmargs=--add-exports jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED \
      --add-exports jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED \
      --add-exports jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED \
      --add-exports jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED \
      --add-exports jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED \
      --add-exports jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED
    ```

## Dependencies { #dependencies }

Kora module documentation usually shows only the dependency of a specific module.
But the application must also connect the [`BOM`](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import) and processors shown below.

===! ":fontawesome-brands-java: `Java`"

    `build.gradle`:

    ```groovy
    dependencies {
        annotationProcessor "ru.tinkoff.kora:annotation-processors:1.2.19"
        implementation(platform("ru.tinkoff.kora:kora-parent:1.2.19"))
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:

    ```kotlin
    dependencies {
        ksp("ru.tinkoff.kora:symbol-processors:1.2.19")
        implementation(platform("ru.tinkoff.kora:kora-parent:1.2.19"))
    }
    ```

After that, module dependencies can be declared without a version, for example:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    implementation "ru.tinkoff.kora:http-server-undertow"
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    implementation("ru.tinkoff.kora:http-server-undertow")
    ```

## Run { #run }

The [application plugin](https://docs.gradle.org/current/userguide/application_plugin.html) is usually used for local startup and building an executable archive.

> [!TIP]
> It's recommended to always use fixed values `applicationName = "application"` and `archiveFileName = "application.tar"` — this simplifies working with the archive in `Dockerfile` and CI/CD scripts, as the filename doesn't depend on the project version.

===! ":fontawesome-brands-java: `Java`"

    Connect the plugin in `build.gradle`:
    ```groovy
    plugins {
        id "application" //(1)!
    }
    ```

    1.  The `application` plugin provides tasks for running and building an executable archive (not connected by default, optional)

    System properties and environment variables for local startup can be set in the `run` task:
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

    1.  JVM arguments for running the application (not set by default, optional)
    2.  Environment variables available in the application (not set by default, optional)

    Run:
    ```shell
    ./gradlew run
    ```

    Archive build configuration:
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

    1.  Application name, used for naming scripts (default: project name). **It's recommended to fix the value `"application"`** to simplify work in `Dockerfile` and CI/CD.
    2.  Fully qualified name of the class with the `main` method for running (not set by default, required).
    3.  Default JVM arguments for running (not set by default, optional).
    4.  Archive filename (default: `<applicationName>-<version>.tar`). **It's recommended to fix the value `"application.tar"`** to simplify work in `Dockerfile` and CI/CD. More details in the [`Tar` task documentation](https://docs.gradle.org/current/dsl/org.gradle.api.tasks.bundling.Tar.html#org.gradle.api.tasks.bundling.Tar:archiveFileName).

    Build the archive:
    ```shell
    ./gradlew distTar
    ```

    A configured application example is available in the [Java application template](https://github.com/kora-projects/kora-java-template/blob/master/build.gradle).

=== ":simple-kotlin: `Kotlin`"

    Connect the plugin in `build.gradle.kts`:
    ```kotlin
    plugins {
        id("application") //(1)!
        kotlin("jvm") version "1.9.25"
        id("com.google.devtools.ksp") version "1.9.25-1.0.20"
    }
    ```

    1.  The `application` plugin provides tasks for running and building an executable archive (not connected by default, optional)

    System properties and environment variables for local startup can be set in `JavaExec` tasks:
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

    1.  JVM arguments for running the application (not set by default, optional)
    2.  Environment variables available in the application (not set by default, optional)

    Run:
    ```shell
    ./gradlew run
    ```

    Archive build configuration:
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

    1.  Application name, used for naming scripts (default: project name). **It's recommended to fix the value `"application"`** to simplify work in `Dockerfile` and CI/CD.
    2.  Fully qualified name of the class with the `main` method for running (not set by default, required); for Kotlin this is a class with the `Kt` suffix.
    3.  Default JVM arguments for running (not set by default, optional).
    4.  Archive filename (default: `<applicationName>-<version>.tar`). **It's recommended to fix the value `"application.tar"`** to simplify work in `Dockerfile` and CI/CD. More details in the [`Tar` task documentation](https://docs.gradle.org/current/dsl/org.gradle.api.tasks.bundling.Tar.html#org.gradle.api.tasks.bundling.Tar:archiveFileName).

    Build the archive:
    ```shell
    ./gradlew distTar
    ```

    A configured application example is available in the [Kotlin application template](https://github.com/kora-projects/kora-kotlin-template/blob/master/build.gradle.kts).

