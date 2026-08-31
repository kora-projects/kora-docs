---
description: "Explains Kora framework fundamentals, annotation processors, KSP, JDK and Kotlin compatibility, Gradle build setup, dependencies, application entry point, and terminology. Use when working with @KoraApp, KoraApplication, annotation processors, KSP, Gradle, the io.koraframework:kora-bom BOM, application plugin."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora framework fundamentals, annotation processors, KSP, JDK and Kotlin compatibility, Gradle, the io.koraframework:kora-bom BOM, module dependencies, the @KoraApp entry point and the application plugin."
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

Kora executes application code synchronously on [virtual threads](https://openjdk.org/jeps/444).
Controllers, `HTTP` clients, repositories, and scheduled tasks are declared with ordinary blocking signatures, and the framework dispatches them onto virtual threads itself: an `HTTP` request, for example, is handled on a virtual thread bound to its connection.
There are no reactive or `suspend` contracts in Kora modules — the processors reject `suspend` controller, client, repository, and scheduler methods with a compilation error.
When a single operation needs to do several things in parallel, use `StructuredTaskScope` from `Java` structured concurrency; it is a preview API, so both compilation and every `JVM` launch require `--enable-preview`.

If you need a step-by-step walkthrough before the reference description, see [Creating Your First Kora Application](../guides/getting-started.md) and [Dependency Injection Introduction](../guides/dependency-injection-introduction.md).

## Annotation Processors { #annotation-processor }

Kora builds the application at compile time: processors read annotations, validate the code, and generate source files that are then compiled together with the application code.
As a result, the dependency graph, aspects, `HTTP` handlers, repositories, and other components become ordinary compiled code without `Reflection` at runtime.

===! ":fontawesome-brands-java: `Java`"

    An annotation is a construct associated with `Java` source code elements: classes, methods, parameters, and fields.
    An [annotation processor](https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/annotation/processing/Processor.html) is started by the compiler, reads these annotations, and can generate additional source code or stop compilation with a clear error.

    Kora provides all annotation processors in a single dependency:

    ```groovy
    annotationProcessor "io.koraframework:annotation-processors"
    ```

    This dependency is needed only at compile time and does not add extra libraries to the application runtime classpath.

=== ":simple-kotlin: `Kotlin`"

    [`KSP`](https://kotlinlang.org/docs/ksp-overview.html) (`Kotlin Symbol Processing`) is used for `Kotlin`.
    `KSP` reads `Kotlin` source code symbols, passes them to Kora processors, and allows code generation before the main compilation step.

    Kora provides `KSP` processors in a single dependency:

    ```kotlin
    ksp("io.koraframework:symbol-processors")
    ```

    At the same time, `Kotlin` processing is usually slower than annotation processing in `Java`.

### `KSP` { #ksp }

`KSP` is needed only for `Kotlin` projects.
If the application is written in `Java`, use the regular `annotationProcessor`; if the application is written in `Kotlin`, connect `com.google.devtools.ksp` and the `io.koraframework:symbol-processors` dependency.

`KSP` writes generated sources into `build/generated/ksp/main/kotlin` and `build/generated/ksp/test/kotlin`.
The `KSP` `Gradle` plugin adds those directories to compilation itself; the build files on this page also declare them explicitly in the source sets:

```kotlin
kotlin {
    sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
    sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
}
```

If another task has to run before code generation (for example `OpenAPI` or `protobuf` generation), bind it to the `KSP` tasks by name.
`KSP` `2` no longer exposes the `KspTask` type, so `tasks.withType<KspTask>()` is not available:

```kotlin
tasks.matching { it.name.startsWith("ksp") }.configureEach {
    dependsOn(openApiGenerateHttpServer)
}
```

## Compatibility { #compatibility }

Kora artifacts are compiled and published for `Java` `25`: both the `Java` and the `Kotlin` parts of the framework are built with `sourceCompatibility`/`targetCompatibility` `25` and `jvmTarget` `25`, and the published `BOM` declares `java.version` `25`.
So `JDK` `25` is the minimum for compiling and running an application on Kora, regardless of the language.

===! ":fontawesome-brands-java: `Java`"

    Requires at least [`JDK` `25`](https://openjdk.org/projects/jdk/25/), it is recommended to use the latest available `GA` release of the `JDK`.

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

    Requires at least [`JDK` `25`](https://openjdk.org/projects/jdk/25/), it is recommended to use the latest available `GA` release of the `JDK`.

    Use the same versions the framework itself is built with: [`Kotlin` `2.4.10`](https://github.com/JetBrains/kotlin/releases) and [`KSP` `2.3.11`](https://github.com/google/ksp/releases).
    A mismatch between the `Kotlin` compiler and the compiler embedded in `KSP` leads to symbol processor failures that are hard to diagnose, so both versions are pinned together.

    Minimal configuration in `build.gradle.kts`:
    ```kotlin
    plugins {
        kotlin("jvm") version "2.4.10"
        id("com.google.devtools.ksp") version "2.3.11"
    }

    kotlin {
        jvmToolchain {
            languageVersion.set(JavaLanguageVersion.of(25))
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }
    ```

!!! warning "The `Gradle` process itself also needs a new enough `JDK`"

    A `Gradle` toolchain only affects compilation and application launch; the `buildscript` classpath is resolved by the `JVM` that runs `Gradle`.
    As soon as a Kora artifact lands there — the most common case is `io.koraframework:openapi-generator` for `OpenAPI` code generation — an older `Gradle` `JVM` fails at the configuration stage:

    ```text
    Dependency requires at least JVM runtime version 25. This build uses a Java 21 JVM.
    ```

    Start `Gradle` on `JDK` `25+` through `JAVA_HOME` or through the `Gradle` daemon `JVM` settings.
    Do not hardcode `org.gradle.java.home` in the repository `gradle.properties`: the path is machine-specific.

!!! note "Toolchain auto-provisioning"

    So that `Gradle` can download a missing `JDK` for the toolchain by itself, Kora example projects register the resolver in `settings.gradle`:

    ```groovy
    plugins {
        id "org.gradle.toolchains.foojay-resolver-convention" version "1.0.0"
    }
    ```

    and enable downloading in `gradle.properties`:

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true
    ```

!!! note "Nullability"

    In `Java`, Kora marks nullability with [JSpecify](https://jspecify.dev/) — `org.jspecify.annotations.Nullable`, which comes transitively with any Kora module.
    These are `type-use` annotations, so their position matters: `Outer.@Nullable Inner`, `List<@Nullable String>`, `String @Nullable []`.
    In `Kotlin` nullability is expressed by the type itself (`T?`) and no annotation is needed; when overriding a Kora contract whose parameter is marked `@Nullable`, declare the parameter as nullable.

## Build System { #build-system }

Kora is designed to be built with [Gradle](https://gradle.org/guides/) because `Gradle` has good support for annotation processors, `KSP`, incremental builds, and dependency management.
The framework itself and all Kora example projects are built with `Gradle` `9.5.1`, so `Gradle` `9.5+` is the recommended version.

To avoid specifying versions for each Kora dependency separately, use the [`BOM`](https://docs.gradle.org/current/userguide/platforms.html#sub:bom_import) `io.koraframework:kora-bom`.
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
            languageVersion = JavaLanguageVersion.of(25)
            vendor = JvmVendorSpec.ADOPTIUM
        }
    }

    configurations {
        koraBom //(1)!
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testImplementation.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1")

        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:http-server-undertow"
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:logging-logback"
    }
    ```

    1.  A separate `koraBom` configuration that all the others extend. `platform()` applied only to `implementation` would not reach `annotationProcessor` and `testAnnotationProcessor`, and the processor dependency would then have to carry an explicit version.

    A more detailed example is available in [Creating Your First Kora Application](../guides/getting-started.md).

=== ":simple-kotlin: `Kotlin`"

    [Gradle Kotlin DSL](https://docs.gradle.org/current/userguide/kotlin_dsl.html) is assumed for `Kotlin`.
    If the project uses `Groovy DSL`, follow the `Java` examples.

    Minimal application configuration in `build.gradle.kts`:
    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version "2.4.10"
        id("com.google.devtools.ksp") version "2.3.11"
    }

    kotlin {
        jvmToolchain {
            languageVersion.set(JavaLanguageVersion.of(25))
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1")) //(1)!

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")
    }
    ```

    1.  In `Kotlin` projects the `BOM` is applied directly to `implementation`; a separate `koraBom` configuration with `extendsFrom` is not created.
    2.  The `ksp` configuration is not covered by the `BOM`, so the processor version is specified explicitly.

    A more detailed example is available in [Creating Your First Kora Application](../guides/getting-started.md).

In real projects the `BOM` version is usually extracted into a `gradle.properties` property (for example `koraVersion`) and referenced as `platform("io.koraframework:kora-bom:$koraVersion")`, so the version is declared in a single place instead of being hardcoded in every module.

!!! note "Compiler internal access"

    Some `Java` annotation processors read `jdk.compiler` internals. On newer `JDK`s this may require exporting the corresponding packages to the compiler.
    All Kora example projects set these `JVM` arguments in `gradle.properties` unconditionally; add them if compilation fails with `IllegalAccessError` or `module jdk.compiler does not export ...`:

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
    configurations {
        koraBom
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testImplementation.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1") //(1)!

        annotationProcessor "io.koraframework:annotation-processors" //(2)!
        testAnnotationProcessor "io.koraframework:annotation-processors" //(3)!
    }
    ```

    1.  `BOM` with the versions of all Kora artifacts (required, no default).
    2.  All Kora annotation processors for the main sources (required, no default).
    3.  The same processors for the test sources — needed only if the test sources declare Kora annotations of their own, for example their own `@KoraApp` (optional).

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1")) //(1)!

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!
        kspTest("io.koraframework:symbol-processors:2.0.0.RC1") //(3)!
    }
    ```

    1.  `BOM` with the versions of all Kora artifacts (required, no default).
    2.  All Kora `KSP` processors for the main sources (required, no default).
    3.  The same processors for the test sources — needed only if the test sources declare their own `@KoraApp`, for example a separate `TestApplication` (optional).

After that, module dependencies can be declared without a version, for example:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    implementation "io.koraframework:http-server-undertow"
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    implementation("io.koraframework:http-server-undertow")
    ```

All Kora artifacts live in the `io.koraframework` group.
The exception is the experimental modules — the declarative `S3` client `s3-client-kora` and the `Camunda` integrations `camunda-engine-bpmn`, `camunda-rest-undertow`, `camunda-zeebe-worker`, together with their processors — they are published in the `io.koraframework.experimental` group.

## Run { #run }

A Kora application is an interface annotated with `@KoraApp` that inherits the modules the application needs.
The processor generates a class next to it, named after the interface with a `Graph` suffix, and its static `graph()` method returns the description of the dependency graph:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, JsonModule, LogbackModule, UndertowPublicHttpServerModule { //(1)!

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph); //(2)!
        }
    }
    ```

    1.  The `@KoraApp` annotation lives in `io.koraframework.common.annotation`, the modules are contributed by the connected Kora artifacts.
    2.  `ApplicationGraph` is generated by the processor from the `Application` interface name and is placed in the same package. `KoraApplication.run` accepts that description (`ApplicationGraphDraw`), initializes the graph, registers a shutdown hook, and blocks the thread until the application shuts down.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, JsonModule, LogbackModule, UndertowPublicHttpServerModule //(1)!

    fun main() {
        KoraApplication.run(ApplicationGraph::graph) //(2)!
    }
    ```

    1.  The `@KoraApp` annotation lives in `io.koraframework.common.annotation`, the modules are contributed by the connected Kora artifacts.
    2.  `ApplicationGraph` is generated by the processor from the `Application` interface name and is placed in the same package. `KoraApplication.run` accepts that description (`ApplicationGraphDraw`), initializes the graph, registers a shutdown hook, and blocks the thread until the application shuts down.

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
        mainClass = "io.koraframework.example.Application" //(2)!
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"] //(3)!
    }

    distTar {
        archiveFileName = "application.tar" //(4)!
    }
    ```

    1.  Application name, used for naming scripts (default: project name). **It's recommended to fix the value `"application"`** to simplify work in `Dockerfile` and CI/CD.
    2.  Fully qualified name of the class with the `main` method for running (not set by default, required).
    3.  Default JVM arguments for running (not set by default, optional). If the application uses `StructuredTaskScope`, `--enable-preview` must be added here as well.
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
        kotlin("jvm") version "2.4.10"
        id("com.google.devtools.ksp") version "2.3.11"
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
        mainClass.set("io.koraframework.example.ApplicationKt") //(2)!
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8") //(3)!
    }

    tasks.distTar {
        archiveFileName.set("application.tar") //(4)!
    }
    ```

    1.  Application name, used for naming scripts (default: project name). **It's recommended to fix the value `"application"`** to simplify work in `Dockerfile` and CI/CD.
    2.  Fully qualified name of the class with the `main` method for running (not set by default, required); for Kotlin this is a class with the `Kt` suffix.
    3.  Default JVM arguments for running (not set by default, optional). If the application uses `StructuredTaskScope`, `--enable-preview` must be added here as well.
    4.  Archive filename (default: `<applicationName>-<version>.tar`). **It's recommended to fix the value `"application.tar"`** to simplify work in `Dockerfile` and CI/CD. More details in the [`Tar` task documentation](https://docs.gradle.org/current/dsl/org.gradle.api.tasks.bundling.Tar.html#org.gradle.api.tasks.bundling.Tar:archiveFileName).

    Build the archive:
    ```shell
    ./gradlew distTar
    ```

    A configured application example is available in the [Kotlin application template](https://github.com/kora-projects/kora-kotlin-template/blob/master/build.gradle.kts).

## Terminology { #terminology }

This section describes the basic terms used throughout the Kora documentation:

- Factory - a method that creates and returns an instance of a component or dependency.
- [Module](container.md#external-module-factory) - a connected dependency or an interface with factory methods that add new components to the application.
- [Component](container.md#components) - an object in the Kora dependency graph. Usually a single instance of a class that implements a part of the application logic.
- Aspect - logic that extends the behavior of a method before, after, or around its execution based on an annotation.
- Dependency graph - the set of application components and the links between them, built by Kora at compile time.

## First Guide { #first-guide }

After this general overview, continue with the [Creating Your First Kora Application](../guides/getting-started.md) guide.
It shows the basic application structure on a small `HTTP` service that can be built and run.
