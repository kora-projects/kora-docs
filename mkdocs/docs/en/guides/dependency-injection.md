---
search:
  exclude: true
title: Building Kora DI Applications
summary: A comprehensive step-by-step tutorial for building complete applications with Kora's dependency injection framework
tags: dependency-injection, tutorial, components, modules, java, kotlin
---

# Building Kora Applications with Dependency Injection { #building-kora-applications-dependency }

This guide introduces practical application assembly with Kora's compile-time dependency injection. It covers how `@KoraApp`, `@Module`, and `@Component` describe a dependency graph, how interfaces
and implementations are bound into that graph, and how lifecycle-aware services are started and stopped by the container. You will also see how module boundaries keep a complete application
understandable as it grows.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-dependency-injection-app).

## What You'll Build { #youll-build }

You'll build a complete notification system application that demonstrates all major Kora dependency injection features:

- **Multi-module project structure** with proper separation of concerns
- **Component-based architecture** with external library modules
- **Tagged dependencies** for multiple implementations of the same interface
- **Collection injection** to inject all implementations at once
- **Submodules** for organizing related components
- **Generic factories** for type-safe component creation
- **Nullable dependencies** for graceful handling of missing components
- **ValueOf<T>** pattern to prevent cascading component refreshes

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Basic understanding of Java or Kotlin
- Familiarity with dependency injection concepts (see [Dependency Injection with Kora](dependency-injection-introduction.md))

## Prerequisites { #prerequisites }

!!! note "Recommended: Read the DI Introduction First"

    This tutorial assumes you have read **[Dependency Injection with Kora](dependency-injection-introduction.md)** and understand the basic dependency injection concepts used by Kora.

    If you haven't read the introduction yet, do that first, because this guide moves quickly into a complete multi-module application and focuses on applying DI patterns rather than defining them from scratch.

    Also you need basic Java or Kotlin familiarit.

This tutorial builds a complete Kora application from scratch, introducing dependency injection concepts progressively. Each step adds new functionality while demonstrating a specific DI pattern. By
the end, you'll have a fully functional application showcasing all major Kora DI features.

## Overview { #overview }

This guide moves from DI concepts to practical application assembly. The sample domain is a notification system, but the important topic is how a real Kora graph stays understandable when it has
multiple modules, implementations, optional dependencies, and lifecycle concerns.

The guide keeps one domain model while adding more graph features around it. That mirrors production work: you rarely learn DI features in isolation; you use them because an application needs module
boundaries, overrides, multiple implementations, or resource lifecycle control.

### Application Graph { #application-graph }

A [Kora application graph](../documentation/container.md) is more than a list of classes. It is a typed structure that describes which components exist, which dependencies each component needs, and
how those components are created. `@KoraApp` is the graph root, `@Module` groups factories and imports, and `@Component` classes become managed graph nodes.

Good graph design keeps responsibilities visible:

- application modules describe the application's own components
- library modules expose reusable defaults
- interfaces define replacement points
- factories create values that need custom construction

### Component Setup { #component-setup }

Real applications often need more than one implementation of an interface. Tags let Kora distinguish dependencies that share the same Java type but have different roles. Overrides let an application
replace a library default with project-specific behavior. Optional dependencies let a component adapt when another component is not present.

These features are powerful because they solve wiring problems without hiding them. The dependency graph still shows which implementation is used and why.

### Lifecycle { #lifecycle }

Some components own resources: clients, schedulers, connections, or background workers. Kora can manage lifecycle-aware components so startup and shutdown happen in graph order. The guide also
introduces `ValueOf<T>` as a way to depend on a component reference without eagerly forcing all downstream refresh behavior.

By the end of this guide, the notification app should feel like a working example of graph design: module boundaries, external defaults, overrides, tags, optional dependencies, generic factories, and
lifecycle control all serve one application instead of appearing as isolated features.

The practical flow is:

1. create a multi-module Kora project
2. import external module defaults
3. override selected components
4. use tags for multiple implementations of one type
5. model optional dependencies
6. organize related components with submodules
7. add generic factories and lifecycle-aware behavior

## Dependencies { #dependencies }

This guide uses a dedicated `settings.gradle` at the top level and keeps the shared Gradle configuration inside `guide-dependency-injection/build.gradle`. In the real repository there is one
additional level above this tutorial directory because multiple guide applications live in the same workspace.

Create the project directories:

```bash
mkdir -p guide-dependency-injection
mkdir -p guide-dependency-injection/guide-dependency-injection-common guide-dependency-injection/guide-dependency-injection-lib guide-dependency-injection/guide-dependency-injection-app
```

Install a JDK before preparing Gradle Wrapper. For the first run, Eclipse Temurin JDK 21 is enough: it starts Gradle, and Gradle toolchain can download the JDK required by the actual build.

===! ":simple-linux: `Linux`"

    On Ubuntu/Debian, add the Adoptium repository and install Temurin JDK:

    ```bash
    sudo apt update
    sudo apt install -y wget gpg
    wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /usr/share/keyrings/adoptium.gpg
    echo "deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(. /etc/os-release && echo $VERSION_CODENAME) main" | sudo tee /etc/apt/sources.list.d/adoptium.list
    sudo apt update
    sudo apt install -y temurin-21-jdk
    ```

=== ":simple-apple: `macOS`"

    If Homebrew is installed, install Temurin JDK through cask:

    ```bash
    brew install --cask temurin@21
    export JAVA_HOME=$(/usr/libexec/java_home -v 21)
    ```

=== ":material-microsoft-windows: `Windows`"

    If `winget` is installed, install Temurin JDK from PowerShell:

    ```powershell
    winget install EclipseAdoptium.Temurin.21.JDK
    ```

    If `winget` is not available, download the Windows installer from the [Eclipse Temurin downloads page](https://adoptium.net/temurin/releases/?version=21), choose **JDK 21** for your CPU
    architecture, run the installer, and enable the option that updates `JAVA_HOME` and `PATH` when it is offered.

    Open a new terminal after installation so environment variables are refreshed.

Check that the JDK is available:

```bash
java -version
```

The output should show Java 21.

Prepare Gradle Wrapper in the same directory. This guide creates the multi-module project manually, so there is no `gradle init` step that would generate wrapper files for you.

Step 1. Create `gradle-wrapper.properties`.

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

Step 2. Download `gradle-wrapper.jar`.

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

Step 3. Download the wrapper launcher script.

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

### Project Setup { #project-setup }

Now set up the multi-module Gradle configuration. This guide is not a single-module application: it demonstrates how Kora builds an application graph from several modules, so the project layout is
part of the lesson.

Gradle has to do several things here:

- register three tutorial submodules
- configure the JDK used to compile every submodule
- import the Kora BOM once for all submodules
- make BOM versions available to the required Gradle configurations
- apply common compile and test rules

#### Module Structure { #module-structure }

Create the following directory structure. The file extensions differ between Gradle Groovy DSL and Gradle Kotlin DSL, but the module boundaries stay the same:

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

`guide-dependency-injection-common` holds shared contracts, `guide-dependency-injection-lib` emulates a reusable library, and `guide-dependency-injection-app` contains the runnable application with
`@KoraApp`. This separation is what lets later steps demonstrate overrides, tags, optional dependencies, and adding more modules.

#### Root Settings { #root-settings }

Edit the top-level Gradle settings file. It names the Gradle build and tells Gradle which submodules belong to it:

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

The `foojay-resolver-convention` plugin supports Java toolchains: it helps Gradle find or download the requested JDK. The include lines register nested modules through Gradle paths, such as
`:guide-dependency-injection:guide-dependency-injection-app`, so Gradle can run tasks for a specific module.

#### Gradle Properties { #gradle-properties }

Add `gradle.properties` so Gradle can detect installed JDKs and download the required Temurin toolchain when JDK 24 is not available locally:

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

The first two properties make the tutorial build less dependent on the local machine. The Kotlin-specific validation flag is needed for Kotlin 1.9.25: if the compiler cannot target JDK 24 exactly, it
reports the fallback as a warning instead of failing this tutorial build.

#### Shared Build File { #shared-build-file }

Create a shared build file under `guide-dependency-injection/`. It applies to the three nested modules: `common`, `lib`, and `app`, so the BOM, toolchain, classpath, and test setup do not have to be
duplicated in every module.

Start with imports and an empty `subprojects` block:

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

#### Kora BOM { #kora-bom }

Inside `subprojects {}`, create a dedicated `koraBom` configuration. The BOM (`Bill of Materials`) holds aligned versions for Kora modules, so every submodule can use a compatible version set.

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

#### JDK Toolchain { #jdk-toolchain }

Configure the JDK after the `java` plugin is enabled in a submodule. Gradle may run on one JDK while compiling the project with another, so the toolchain makes the tutorial reproducible.

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

#### Classpath Configurations { #classpath-configurations }

Make the BOM available to the Gradle configurations used by application code, compile-time APIs, annotation processing, public library APIs, and tests.

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

`annotationProcessor` and `testAnnotationProcessor` receive the BOM separately because Kora annotation processors use their own classpath. The `api` configuration matters for `common` and `lib`, where
types can become part of the public API consumed by other modules.

#### Kora Version { #kora-version }

Import the BOM itself. The `$koraVersion` variable comes from the repository `gradle.properties`; after this line, individual modules can declare Kora dependencies without explicit versions.

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

#### Final File { #final-file }

The final shared build file contains the same decisions together: the BOM configuration, the JDK toolchain, classpath wiring, dependency on the Kora BOM, and common test behavior.

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

### Application Base { #application-base }

**Goal**: Create the shared contract module and the runnable application module that the next steps will extend.

**What this step introduces**: the minimal `@KoraApp` entry point, a shared contract module, and the initial multi-module layout. This is the baseline graph before we start layering more DI features
on top of it.

**Why we need it**: we first establish what belongs to the application module and what belongs to reusable modules. This mirrors the separation described
in [Dependency Injection with Kora: @KoraApp](dependency-injection-introduction.md#koraapp), [@Root](dependency-injection-introduction.md#root)
and [Container documentation: Container](../documentation/container.md#container).

**What we are emulating**: a real application root that owns startup and a shared API module that other modules can depend on without pulling in application-specific behavior.

**Create shared contracts** (`guide-dependency-injection/guide-dependency-injection-common/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/common/`
or `guide-dependency-injection/guide-dependency-injection-common/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/common/`):

#### Build the Shared Module { #build-shared-module }

First, create the build file for `guide-dependency-injection-common`. This module contains only interfaces and shared types, so it needs a library-oriented JVM plugin and test dependencies, but not the
application plugin or Kora annotation processing.

===! ":fontawesome-brands-java: Java"

    The `java-library` plugin is the right fit for modules with a public API:

    ```groovy
    plugins {
        id "java-library"
    }
    ```

    Other modules will depend on `common`, so Gradle should distinguish between internal implementation dependencies and types that are part of the public API.

    Add test dependencies:

    ```groovy
    dependencies {
        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
    }
    ```

    `junit-bom` aligns JUnit versions, `junit-jupiter` adds JUnit 5, and `test-junit5` adds Kora testing utilities. This first step may not have tests yet, but the module is ready for contract and
    component checks.

    The final common module `build.gradle` is:

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

    The `kotlin("jvm")` plugin compiles Kotlin code into JVM classes that the `app` and `lib` modules can use:

    ```kotlin
    plugins {
        kotlin("jvm") version "1.9.25"
    }
    ```

    Add test dependencies:

    ```kotlin
    dependencies {
        testImplementation(platform("org.junit:junit-bom:$junitVersion"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

    `junit-bom` aligns JUnit versions, `junit-jupiter` adds JUnit 5, and `test-junit5` adds Kora testing utilities.

    The final common module `build.gradle.kts` is:

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

Then create the interfaces:

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

**Create the main application** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/`
or `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/`):

#### Build the Application { #build-application }

Create the build file for `guide-dependency-injection-app`. This module is runnable, contains `@KoraApp`, and must enable Kora graph generation, so its Gradle setup is more involved than the shared
contract module.

===! ":fontawesome-brands-java: Java"

    Start with plugins:

    ```groovy
    plugins {
        id "java"
        id "application"
    }
    ```

    `java` compiles sources, and `application` adds `./gradlew run` plus main-class configuration.

    Add the Kora annotation processor:

    ```groovy
    dependencies {
        annotationProcessor "ru.tinkoff.kora:annotation-processors"
    }
    ```

    `annotationProcessor` reads `@KoraApp` and generates `ApplicationGraph`. Without this line, Java compilation can reach the generated class reference, but the application graph itself will not be
    produced.

    Now add application dependencies:

    ```groovy
    dependencies {
        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation project(":guide-dependency-injection:guide-dependency-injection-lib")
        implementation "ru.tinkoff.kora:config-hocon"
        implementation "ru.tinkoff.kora:logging-logback"
    }
    ```

    `common` provides the shared `Notifier` interface, `lib` will add library components in later steps, `config-hocon` provides configuration, and `logging-logback` adds logging.

    Add test setup:

    ```groovy
    dependencies {
        testAnnotationProcessor "ru.tinkoff.kora:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
    }
    ```

    `testAnnotationProcessor` is needed when a test graph is generated by Kora. `test-junit5` adds Kora integration for JUnit 5.

    Configure application startup:

    ```groovy
    application {
        applicationName = "application"
        mainClass = "ru.tinkoff.kora.guide.dependencyinjection.Application"
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"]
    }
    ```

    This block belongs to the Gradle `application` plugin. It is not part of Kora's DI container directly, but it connects the Kora-generated graph to the normal JVM application launch path:

    - `applicationName = "application"` sets the short application name in the Gradle distribution. Gradle uses it to create startup scripts such as `bin/application`.
    - `mainClass` points to the class that contains `main`. In Java this is the source `Application` interface, not the generated `ApplicationGraph`: your `main` method calls
      `KoraApplication.run(ApplicationGraph::graph)`.
    - `applicationDefaultJvmArgs` sets JVM arguments used by `./gradlew run` and written into generated startup scripts.

    The important detail is that `mainClass` points to ordinary source code. `ApplicationGraph` exists only after `annotationProcessor` runs, so the `classes` task validates Java compilation, annotation
    processing, and Kora graph generation together.

    Add a stable distribution archive name:

    ```groovy
    distTar {
        archiveFileName = "application.tar"
    }
    ```

    `distTar` is a task added by the Gradle `application` plugin. It builds a tar archive containing the application classes, runtime dependencies, and startup scripts. By default, the archive name is
    derived from the project name and version, which can be long and inconvenient in a multi-module tutorial project.

    `archiveFileName = "application.tar"` makes the artifact name stable. That is useful for tests, CI, and later guide steps because they can reference one predictable file instead of reconstructing
    the Gradle project name and version.

    The final application `build.gradle` is:

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

    Start with plugins:

    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version "1.9.25"
        id("com.google.devtools.ksp") version "1.9.25-1.0.20"
    }
    ```

    `application` adds `./gradlew run`, `kotlin("jvm")` compiles Kotlin code, and `com.google.devtools.ksp` runs the Kora symbol processor.

    Add the Kora KSP processor:

    ```kotlin
    dependencies {
        ksp("ru.tinkoff.kora:symbol-processors")
    }
    ```

    KSP reads `@KoraApp` and generates `ApplicationGraph`. Without this dependency, the application will not get the generated graph.

    Now add application dependencies:

    ```kotlin
    dependencies {
        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-lib"))
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

    `common` provides the shared `Notifier` interface, `lib` will add library components, `config-hocon` provides HOCON configuration, and `logging-logback` adds logging.

    Add test dependencies:

    ```kotlin
    dependencies {
        testImplementation(platform("org.junit:junit-bom:$junitVersion"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

    Configure startup:

    ```kotlin
    application {
        applicationName.set("application")
        mainClass.set("ru.tinkoff.kora.guide.dependencyinjection.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }
    ```

    This block belongs to the Gradle `application` plugin and tells Gradle how to launch the Kotlin application:

    - `applicationName.set("application")` sets the distribution application name and startup script name.
    - `mainClass.set(...)` points to the class that contains `main`. In Kotlin, a top-level `main` function from `Application.kt` is compiled into the JVM class `ApplicationKt`, so the main class is
      `ApplicationKt`.
    - `applicationDefaultJvmArgs` sets JVM arguments for `./gradlew run` and generated startup scripts.

    The `-Dfile.encoding=UTF-8` argument fixes runtime encoding. This avoids differences between Windows, Linux, and macOS when the app writes text to logs or reads string resources.

    Add a stable tar archive name:

    ```kotlin
    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

    `distTar` builds an executable distribution containing classes, runtime dependencies, and startup scripts. The fixed `application.tar` name is useful for tests, CI, and later guide steps that need
    to reference one predictable artifact.

    The final application `build.gradle.kts` is:

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

Then create the application:

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

**Build and run**:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

**Expected Output**: The application starts and shuts down cleanly. The `lib` module is already connected in the build, and the next steps will add more components and modules.

---

### External Modules { #external-modules }

**Goal**: Create reusable library modules that provide default implementations.

**What this step introduces**: external module factories and `@DefaultComponent`. The `EmailModule` lives outside the application module and exposes defaults that the application can adopt or replace
later.

**Why we need it**: external modules are how reusable Kora libraries publish components to applications, but they are not auto-discovered and must be connected explicitly. This
follows [Dependency Injection with Kora: @Module](dependency-injection-introduction.md#module), [@DefaultComponent](dependency-injection-introduction.md#defaultcomponent)
and [Container documentation: External module factory](../documentation/container.md#external-module-factory).

**What we are emulating**: a library that ships a default email notifier implementation and configuration contract, while still allowing the application to override presentation details later.

First, create the library module build file:

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

**Create EmailModule** (`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/email/`
or `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/email/`):

===! ":fontawesome-brands-java: Java"

    Create the EmailModule:

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

    Create the EmailModule:

    ```kotlin
    package ru.tinkoff.kora.guide.dependencyinjection.email

    import java.util.function.Supplier
    import ru.tinkoff.kora.guide.dependencyinjection.common.Notifier
    import ru.tinkoff.kora.common.DefaultComponent
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.config.common.Config
    import ru.tinkoff.kora.config.common.extractor.ConfigValueExtractor

    interface EmailModule {
        class EmailTag private constructor()

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

**Create EmailConfig** (`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/email/`
or `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/email/`):

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

**Update Application** to include the email module:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Connected module
        // EmailModule provides default email notification
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        EmailModule {  // <----- Connected module
        // EmailModule provides default email notification
    }
    ```

**Create application.conf** (`guide-dependency-injection/guide-dependency-injection-app/src/main/resources/`):

For the full configuration reference, see [Configuration](../documentation/config.md).

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

    1. Topic or channel name used by the component.
    2. Log level for `ROOT`.
    3. Log level for `ru.tinkoff.kora`.

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

    1. Topic or channel name used by the component.
    2. Log level for `ROOT`.
    3. Log level for `ru.tinkoff.kora`.

**Build and run** - Application still has no root component, so it just starts and stops.

**Key Concept**: `@DefaultComponent` provides library defaults that applications can override.

**Module registration rule**: if a type is annotated with `@Module`, do not also wire it through `extends` on `@KoraApp` or another module. A module should be registered in exactly one way: either
inherited with `extends`, or discovered because it is annotated with `@Module` and lives under the current `@KoraApp` / `@KoraSubmodule` graph. `@KoraSubmodule` itself is the case where inheritance is
expected.

**What Kora generates for `EmailModule`**: after `./gradlew clean classes`, `ApplicationGraph` will not necessarily contain the exact same `componentN` numbers shown below, because those names are
internal generator details. The structure is the important part: Kora creates a configuration node, a default value node, and the notifier node.

===! ":fontawesome-brands-java: Java"

    ??? abstract "Java: generated graph fragment for `EmailModule`"

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

        This shows why `EmailModule` must be connected through `extends`: only then do its factory methods become part of the application graph.

        - `component8` reads `notifier.email` and turns HOCON configuration into typed `EmailConfig`.
        - `component9` is a tagged `Supplier<String>` with `EmailTag`. This lets Kora distinguish the email header from other possible `Supplier<String>` components.
        - `component10` is a tagged `Notifier` that depends on `EmailConfig` and the tagged `Supplier<String>`.
        - `@DefaultComponent` on `emailNotifierHeaderSupplier()` means the library provides a default value, and the application can replace it in the next section.

=== ":simple-kotlin: `Kotlin`"

    ??? abstract "Kotlin: generated graph fragment for `EmailModule`"

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

        Kotlin/KSP generates the same meaning in Kotlin code:

        - `EmailConfig` becomes a separate graph node.
        - `EmailTag` is written into the tag array for both `Supplier<String>` and `Notifier`.
        - `emailNotifier(...)` receives dependencies from the graph instead of creating them itself.
        - In the next section, the application overrides `emailNotifierHeaderSupplier()`, and Kora substitutes the new node for the library `@DefaultComponent`.

---

### Component Override { #component-override }

**Goal**: Show how applications can override library defaults.

**What this step introduces**: component override of a `@DefaultComponent` factory from an external module. The application replaces only the header supplier and keeps the rest of the library behavior
intact.

**Why we need it**: libraries should provide safe defaults, but applications must keep final control over business-facing behavior. This
matches [Dependency Injection with Kora: Standard factory](dependency-injection-introduction.md#defaultcomponent-factory), [@DefaultComponent](dependency-injection-introduction.md#defaultcomponent)
and [Container documentation: Standard factory](../documentation/container.md#standard-factory).

**What we are emulating**: application-specific customization of a shared library notifier without forking or rewriting the entire module.

**Create NotifyRunner** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/`
or `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/`):

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

**Update Application** to override the email header:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Connected module
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
        EmailModule {  // <----- Connected module
        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

**Build and run**:

```
DI tutorial step 3 start
[EMAIL OVERRIDDEN] USER [USER:Alice]: Welcome!
Application shutdown
```

**Key Concept**: Applications can override `@DefaultComponent` implementations by providing their own factory methods.

---

### Tagged Dependencies { #tagged-dependencies }

**Goal**: Demonstrate how tags allow multiple implementations of the same interface, while `All<T>` lets you consume all matching notifiers at once.

**What this step introduces**: `@Tag` for distinguishing multiple `Notifier` implementations and `All<T>` for broadcasting across them. `SmsModule` is an internal `@Module`, so it is discovered
automatically from the application module instead of being inherited through `extends`.

**Why we need it**: once one contract has multiple implementations, plain type-based injection is no longer enough. Tags make the graph explicit, and `All<T>` gives us a natural way to fan out
notifications.
See [Dependency Injection with Kora: @Tag](dependency-injection-introduction.md#tag), [Dependency Claims and Resolution: All](dependency-injection-introduction.md#all), [Tags System](dependency-injection-introduction.md#tag-system)
and [Container documentation: Tag any](../documentation/container.md#tag-any).

**What we are emulating**: a notification service that can send the same message through every available channel instead of choosing only one implementation.

**Create SmsModule** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/sms/`
or `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/sms/`):

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

**Application note**: `SmsModule` is annotated with `@Module` and lives in the application package, so Kora discovers it automatically. Do not add it with `extends` on `Application`.

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Connected module
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
        EmailModule {  // <----- Connected module
        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

**Update NotifyRunner** to iterate over all notifiers:

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

**Build and run**:

```
DI tutorial step 4 start
[SMS] Bob@Hello!
[EMAIL OVERRIDDEN] USER [USER:Bob]: Hello!
Application shutdown
```

**Key Concept**: `@Tag` allows multiple implementations of the same contract, and `All<T>` lets you broadcast to all of them.

---

### Optional Dependencies { #optional-dependencies }

**Goal**: Add an optional collaborator for SMS without changing the `Notifier` contract.

**What this step introduces**: nullable dependencies for optional behavior. `SmsModule` can work with or without `SmsCellularProvider`, and `SmsCellularModule` adds the provider only when the
application chooses to inherit it.

**Why we need it**: some features should enrich an existing component rather than force a separate implementation branch. This
follows [Dependency Injection with Kora: Nullable](dependency-injection-introduction.md#optional)
and [Container documentation: Optional dependencies](../documentation/container.md#optional-dependencies).

**What we are emulating**: optional enrichment of SMS formatting with a provider code, where the notifier still functions even if that provider is not configured.

**Create SmsCellularProvider and SmsCellularModule** (`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/sms/`
or `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/sms/`):

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

**Update Application** to include the provider module. `SmsCellularModule` is not annotated with `@Module`, so this one is intentionally connected through `extends`:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule,  // <----- Connected module
            SmsCellularModule {  // <----- Connected module
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

**Build and run**:

```
DI tutorial step 5 start
+1 [SMS] Bob@Hello!
[EMAIL OVERRIDDEN] USER [USER:Bob]: Hello!
Application shutdown
```

**Key Concept**: `@Nullable` in Java and nullable types in Kotlin let a component keep working even when an optional dependency is absent.

---

### Submodule { #submodule }

**Goal**: Demonstrate `@KoraSubmodule` for organizing related components.

**What this step introduces**: `@KoraSubmodule` as the boundary that turns another Gradle module into a DI-visible compilation unit. Inside that submodule, `@Module` and `@Component` declarations are
collected and exposed to the main `@KoraApp` through inheritance.

**Why we need it**: regular Gradle modules are not scanned by Kora unless they contain `@KoraApp` or `@KoraSubmodule`. This is the mechanism that lets us move messenger functionality into its own
module without losing DI discovery.
See [Dependency Injection with Kora: @KoraSubmodule](dependency-injection-introduction.md#korasubmodule), [Overview scope note](dependency-injection-introduction.md#overview)
and [Container documentation: Submodule factory](../documentation/container.md#submodule-factory).

**What we are emulating**: a larger codebase where a separate team or package owns messenger delivery, but the main application still composes it into one graph.

Now create and connect the submodule as the tutorial reaches the `@KoraSubmodule` part.

Update `settings.gradle`:

```groovy
include "guide-dependency-injection:guide-dependency-injection-submodule"
```

Update `settings.gradle.kts`:

```kotlin
include("guide-dependency-injection:guide-dependency-injection-submodule")
```

Create the directory:

```bash
mkdir -p guide-dependency-injection/guide-dependency-injection-submodule
```

**Create `guide-dependency-injection/guide-dependency-injection-submodule/build.gradle`**:

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

**Update `guide-dependency-injection-app/build.gradle` to add the new module dependency**:

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

**Create MessengerModule** (`guide-dependency-injection/guide-dependency-injection-submodule/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/messenger/`
or `guide-dependency-injection/guide-dependency-injection-submodule/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/messenger/`):

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

**Create Messenger interface**:

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

**Create SlackMessenger**:

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

**Create MessengerNotifier**:

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

**Update Application** to include the messenger submodule. `MessengerModule` is annotated with `@KoraSubmodule`, so this is the case where inheritance is expected:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule,  // <----- Connected module
            SmsCellularModule,  // <----- Connected module
            MessengerModule {  // <----- Connected module
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

**Build and run**:

```
+1 [SMS] Bob@Hello!
[EMAIL OVERRIDDEN] USER [USER:Bob]: Hello!
Broadcasting to messengers
Slack: Bob@Hello!
Messenger broadcast complete
Application shutdown
```

**Key Concept**: `@KoraSubmodule` groups related components and tags without forcing them into the main application interface file.

---

### Generic Factory { #generic-factory }

**Goal**: Demonstrate generic factory methods for flexible component creation.

**What this step introduces**: generic factories that let one module create many strongly typed components. `StorageModule` produces `Storage<T>` instances from mapper functions instead of hardcoding
one concrete storage per type.

**Why we need it**: generic factories reduce duplication while keeping the graph type-safe. This aligns
with [Dependency Injection with Kora: Generic factory](dependency-injection-introduction.md#generic-factory)
and [Container documentation: Generic factory](../documentation/container.md#generic-factory).

**What we are emulating**: infrastructure code that can persist different payload shapes using the same reusable storage pattern, with Kora selecting the right generic instantiation automatically.

**Create Storage interface** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/storage/`
or `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/storage/`):

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

**Create TempFileStorage**:

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

**Create StorageModule**:

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

**Application note**: No `Application` changes are required here. `StorageModule` is part of the application package, so Kora discovers it as an application module automatically.

**Update NotifyRunner** to use `Storage<String>`:

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

**Build and run**:

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

**Key Concept**: Generic factory methods such as `<T> Storage<T>` allow Kora to build strongly typed components from reusable factories.

---

### Update Management { #update-management }

**Goal**: Demonstrate `ValueOf<T>` for preventing unwanted cascading refreshes when dependencies are updated.

**What this step introduces**: `ValueOf<T>`, `Wrapped<T>`, and `LifecycleWrapper` for lifecycle-aware, indirectly accessed dependencies. `ActivityService` stays stable while `ActivityRecorder` remains
lazily accessible and lifecycle-managed.

**Why we need it**: some infrastructure dependencies are expensive or refreshable, and we do not want every consumer to be recreated just because that dependency changes. This
follows [Dependency Injection with Kora: ValueOf](dependency-injection-introduction.md#valueof) and [Container documentation: Component lifecycle](../documentation/container.md#component-lifecycle).

**What we are emulating**: a service that records activity through a managed connector which can be started, stopped, or refreshed independently from the business service using it.

**Create ActivityRecorder interface** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/ru/tinkoff/kora/guide/dependencyinjection/activity/`
or `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/ru/tinkoff/kora/guide/dependencyinjection/activity/`):

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

**Create ActivityService**:

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

**Create ActivityModule**:

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

**Application note**: No `Application` changes are required here either. `ActivityModule` is also discovered as an application module from the application package.

**Update NotifyRunner** to demonstrate the final scenario:

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

**Build and run**:

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

**Key Concept**: `ValueOf<T>` prevents cascading component refreshes. The `ActivityService` instance is stable, but it can still access the current `ActivityRecorder` lazily when needed.

---

## Guide Summary { #guide-summary }

You've built a complete Kora application demonstrating all major dependency injection concepts:

1. **Project Structure** - Multi-module organization
2. **External Modules** - Library components with `@DefaultComponent`
3. **Component Override** - Customizing library defaults
4. **Tagged Dependencies** - Multiple implementations with `@Tag` and `All<T>`
5. **Nullable Dependencies** - `@Nullable` / nullable types for graceful degradation
6. **Submodules** - `@KoraSubmodule` for component organization
7. **Generic Factories** - `<T>` parameterized component creation
8. **Preventing Cascading Refreshes** - `ValueOf<T>` to control component refresh behavior

Each step builds upon the previous, showing how Kora's compile-time DI enables clean, modular, and performant applications.

## Best Practices { #best-practices }

- Keep components small and focused on one responsibility.
- Prefer constructor injection and explicit module boundaries.
- Use tags only when multiple implementations really need to coexist.
- Keep optional dependencies explicit with nullable types or `@Nullable`.
- Use `ValueOf<T>` when you need controlled component refresh behavior.

## Summary { #summary }

Congratulations! You've completed the comprehensive Kora Dependency Injection Guide. You've learned not just *how* to use dependency injection, but *why* it's such a powerful pattern for building
maintainable software.

The guide covered the main building blocks of a Kora graph: `@KoraApp`, `@Component`, `@Module`, external modules, `@DefaultComponent`, tags, `All<T>`, nullable dependencies, submodules, generic
factories, and `ValueOf<T>`. Together they show how to compose an application from small explicit parts while keeping dependency resolution type-safe and visible at compile time.

The same patterns are used in production services to build:

- High-performance microservices
- Scalable web applications
- Complex enterprise systems
- Cloud-native architectures

They make code easier to test, maintain, extend, and understand because dependencies are declared in constructors and factory methods instead of hidden inside implementation code.

Next learning milestones:

1. Explore Kora Examples: Study the `kora-examples` repository for real-world patterns
2. Build Your First App: Create a simple REST API using the tutorial patterns
3. Add Observability: Learn Kora's telemetry and monitoring features
4. Database Integration: Connect your app to a real database
5. Deploy to Production: Learn containerization and cloud deployment

## Key Concepts { #key-concepts }

- how `@KoraApp`, `@Component`, and `@Module` shape the application graph
- how tags distinguish multiple implementations of the same contract
- how collection and nullable dependency claims affect graph resolution
- how submodules and external modules help organize larger applications
- how `ValueOf<T>` gives controlled access to refreshable components

## Troubleshooting { #troubleshooting }

Common Issues and Solutions:

Circular Dependencies:

Problem: Two or more components depend on each other directly or indirectly.

Symptoms:

- Compile-time error: "Circular dependency detected"
- Annotation processor fails with dependency resolution error

Solutions:

1. Refactor to Interface Segregation:

===! ":fontawesome-brands-java: Java"

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

2. Use ValueOf for Indirect Dependencies:

===! ":fontawesome-brands-java: Java"

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

Missing Dependencies:

Problem: Component requires a dependency that cannot be found.

Symptoms:

- Compile-time error: "No component found for type X"
- Clear error message showing dependency chain

Solutions:

1. Add Missing Component:

===! ":fontawesome-brands-java: Java"

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

2. Create Factory Method:

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

Configuration Issues:

Problem: Components can't access configuration values.

Symptoms:

- Runtime error: "Configuration value not found"
- NullPointerException when accessing config properties

Solutions:

1. Add Configuration Module:

===! ":fontawesome-brands-java: Java"

    ```java
    // Include configuration module
    @KoraApp
    public interface Application extends HoconConfigModule {
        // Now configuration is available
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Include configuration module
    @KoraApp
    interface Application : HoconConfigModule {
        // Now configuration is available
    }
    ```

2. Check Property Names:

===! ":fontawesome-brands-java: Java"

    ```java
    // Ensure property names match
    @Component
    public final class DatabaseConfig {
        private final Config config;

        public DatabaseConfig(Config config) {
            this.config = config;
        }

        public String getUrl() {
            // Check that property exists in config
            return config.getString("db.url");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Ensure property names match
    @Component
    class DatabaseConfig(
        private val config: Config
    ) {

        fun getUrl(): String {
            // Check that property exists in config
            return config.getString("db.url")
        }
    }
    ```

Tag Resolution Issues:

Problem: Tagged dependencies cannot be resolved.

Symptoms:

- Compile error: "Multiple components found for type X"
- Or: "No component found for tagged type X"

Solutions:

1. Use Correct Tag Annotation:

===! ":fontawesome-brands-java: Java"

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

2. Check Tag Class Definition:

===! ":fontawesome-brands-java: Java"

    ```java
    // Tag class must be public
    public final class MyTag {} // Correct

    // Private tag won't work
    private final class MyTag {} // Wrong
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Tag class must be public
    class MyTag // Correct (public by default)

    // Private tag won't work
    private class MyTag // Wrong
    ```

Module Import Issues:

Problem: Components from modules are not available.

Symptoms:

- Compile error: "No component found for type from module"

Solutions:

1. Include Module in Application:

===! ":fontawesome-brands-java: Java"

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

2. Check Module Visibility:

===! ":fontawesome-brands-java: Java"

    ```java
    // Module methods must be public
    @Module
    public interface MyModule {
        @Component
        default MyComponent myComponent() { // public by default
            return new MyComponent();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Module methods must be public
    @Module
    interface MyModule {
        @Component
        fun myComponent(): MyComponent { // public by default
            return MyComponent()
        }
    }
    ```

Collection Injection Issues:

Problem: `All<T>` doesn't inject expected components.

Symptoms:

- Empty collection when expecting multiple implementations
- Missing expected components in `All<T>`

Solutions:

1. Ensure All Implementations are Components:

===! ":fontawesome-brands-java: Java"

    ```java
    // All implementations must be @Component
    @Component
    public final class Impl1 implements MyInterface {}

    @Component
    public final class Impl2 implements MyInterface {}

    // Now All<MyInterface> will contain both
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // All implementations must be @Component
    @Component
    class Impl1 : MyInterface

    @Component
    class Impl2 : MyInterface

    // Now All<MyInterface> will contain both
    ```

2. Check for Tag Conflicts:

===! ":fontawesome-brands-java: Java"

    ```java
    // If using tags, make sure you're not accidentally filtering
    @Component
    public final class MyService {
        public MyService(All<MyInterface> all) { // Gets all implementations
            // ...
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // If using tags, make sure you're not accidentally filtering
    @Component
    class MyService(
        val all: All<MyInterface> // Gets all implementations
    ) {
        // ...
    }
    ```

Optional Dependency Issues:

Problem: Optional dependencies behave unexpectedly.

Symptoms:

- Optional is empty when expecting a value
- NullPointerException when using optional

Solutions:

1. Handle Optional Correctly:

===! ":fontawesome-brands-java: Java"

    ```java
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
            // optionalDep.work() // Don't do this without a null check
        }
    }
    ```

2. Ensure Nullable Component Exists:

===! ":fontawesome-brands-java: Java"

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

Lifecycle Issues:

Problem: Components with lifecycle methods don't start/stop properly.

Symptoms:

- `init()` or `destroy()` methods not called
- Resources not cleaned up properly

Solutions:

1. Implement Lifecycle Interface:

===! ":fontawesome-brands-java: Java"

    ```java
    import ru.tinkoff.kora.common.Lifecycle;

    @Component
    public final class MyService implements Lifecycle {
        @Override
        public void init() throws Exception {
            // Initialize resources here
        }

        @Override
        public void destroy() throws Exception {
            // Clean up resources here
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import ru.tinkoff.kora.common.Lifecycle

    @Component
    class MyService : Lifecycle {
        override fun init() {
            // Initialize resources here
        }

        override fun destroy() {
            // Clean up resources here
        }
    }
    ```

2. Check Component Registration:

===! ":fontawesome-brands-java: Java"

    ```java
    // Ensure component is properly registered in a module
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
    // Ensure component is properly registered in a module
    @Module
    interface MyModule {
        @Component
        fun myService(): MyService {
            return MyService()
        }
    }
    ```

Generic Type Issues:

Problem: Generic components (`<T>`) don't resolve correctly.

Symptoms:

- Compile error: "Generic type cannot be resolved"
- Wrong generic type injected

Solutions:

1. Use Proper Generic Constraints:

===! ":fontawesome-brands-java: Java"

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

2. Check Generic Factory Methods:

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface StorageModule {
        @Component
        default <T> Storage<T> storage(Class<T> type) {
            return new InMemoryStorage<>(); // Generic factory
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface StorageModule {
        @Component
        fun <T> storage(type: Class<T>): Storage<T> {
            return InMemoryStorage() // Generic factory
        }
    }
    ```

Build and Compilation Issues:

Problem: Kora annotation processor fails or generates incorrect code.

Symptoms:

- Compilation errors in generated code
- "Annotation processor not found" errors
- Generated classes have issues

Solutions:

1. Check Dependencies:

===! ":fontawesome-brands-java: Java"

    ```java
    // Ensure Kora dependencies are included
    dependencies {
        implementation "ru.tinkoff.kora:kora-app-annotation-processor"
        implementation "ru.tinkoff.kora:config-hocon"
        // Other Kora modules...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Ensure Kora dependencies are included
    dependencies {
        implementation("ru.tinkoff.kora:kora-app-annotation-processor")
        implementation("ru.tinkoff.kora:config-hocon")
        // Other Kora modules...
    }
    ```

2. Clean Build:

===! ":fontawesome-brands-java: Java"

    ```bash
    # Clean and rebuild
    ./gradlew clean classes
    ```

=== ":simple-kotlin: `Kotlin`"

    ```bash
    # Clean and rebuild
    ./gradlew clean classes
    ```

3. Check Java Version:

===! ":fontawesome-brands-java: Java"

    ```java
    // Ensure using supported Java version (11, 17, 21)
    java --version
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Ensure using supported Java version (11, 17, 21)
    java --version
    ```

Testing Issues:

Problem: Components are hard to test or tests fail unexpectedly.

Symptoms:

- Difficult to inject mocks
- Test dependencies not resolved
- Integration test failures

Solutions:

1. Use Constructor Injection for Testability:

===! ":fontawesome-brands-java: Java"

    ```java
    // Testable component
    @Component
    public final class UserService {
        private final UserRepository repository;

        public UserService(UserRepository repository) {
            this.repository = repository;
        }
    }

    // Test
    @Test
    public void testUserService() {
        UserRepository mockRepo = mock(UserRepository.class);
        UserService service = new UserService(mockRepo);
        // Test...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Testable component
    @Component
    class UserService(
        private val repository: UserRepository
    )

    // Test
    @Test
    fun testUserService() {
        val mockRepo = mock(UserRepository::class.java)
        val service = UserService(mockRepo)
        // Test...
    }
    ```

2. Use Testcontainers for Integration Tests:

===! ":fontawesome-brands-java: Java"

    ```java
    @Testcontainers
    public class UserServiceIntegrationTest {
        @Container
        private static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17.6-alpine");

        @Test
        public void testRealDatabase() {
            // Test with real database
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
            // Test with real database
        }
    }
    ```

Common Beginner Mistakes:

1. Forgetting @Component Annotation:

===! ":fontawesome-brands-java: Java"

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

2. Private Constructor:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class MyService {
        private MyService() {} // Wrong: private constructor blocks DI
    }

    // Public or package-private constructor
    @Component
    public final class MyService {
        public MyService() {} // Correct
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService private constructor() // Wrong: private constructor blocks DI

    // Public constructor (default)
    @Component
    class MyService // Correct
    ```

3. Not Including Modules:

===! ":fontawesome-brands-java: Java"

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

4. Circular Dependencies:

===! ":fontawesome-brands-java: Java"

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
    class BImpl implements ServiceBInterface { BImpl(ServiceAInterface a) {} }
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

5. Ignoring Nullable Results:

===! ":fontawesome-brands-java: Java"

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

Getting Help:

If you're still stuck:

1. Check the Examples: Look at `kora-examples` for working patterns
2. Read Documentation: Consult `kora-docs` for detailed explanations
3. Simplify: Remove complexity and test with minimal components
4. Community: Ask questions in Kora community channels

Remember: Most DI issues come from missing components, incorrect module imports, or circular dependencies. Start simple and build up gradually!

## What's Next? { #whats-next }

- [Create Your First Kora Application](getting-started.md) if you completed the DI-only tutorial before building a runnable HTTP app.
- [Configuration with HOCON](config-hocon.md) or [Configuration with YAML](config-yaml.md) after getting started, to learn how typed configuration enters the graph.
- [JSON Processing](json.md) after getting started, to prepare request and response DTOs before the full HTTP Server guide.

## Help { #help }

If you encounter issues:

- check the [Container documentation](../documentation/container.md)
- compare with [Kora Java Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection-app) and [Kora Kotlin Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-dependency-injection-app)
- run `./gradlew clean classes` and inspect generated graph errors before changing code structure
- verify that components are annotated with `@Component` or provided by a module
