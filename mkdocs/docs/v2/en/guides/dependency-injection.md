---
search:
  exclude: true
title: Building Kora DI Applications
summary: A comprehensive step-by-step tutorial for building complete applications with Kora's dependency injection framework
description: "Step-by-step multi-module Kora 2.0 application built around the dependency graph: a @KoraApp root, io.koraframework.common.annotation annotations (@Component, @Module, @KoraSubmodule, @DefaultComponent, @Tag, @Root, @FactoryModule), All<T> and ValueOf<T> claims, JSpecify @Nullable optional dependencies, Lifecycle and LifecycleWrapper, generic factories, and the Gradle setup with io.koraframework:kora-bom, annotation-processors and symbol-processors."
agent:
  use_when: "Use this file for questions about assembling a real multi-module Kora application graph: @KoraApp with extends, @Module auto-discovery, @KoraSubmodule across Gradle modules, @DefaultComponent overrides, @Tag and Tag.Any, All<T> collection injection, @Nullable optional dependencies, generic factory methods, @FactoryModule, ValueOf<T> and Wrapped<T>/LifecycleWrapper lifecycle control, and the Gradle multi-module build with io.koraframework:kora-bom."
tags: dependency-injection, tutorial, components, modules, java, kotlin
---

# Building Kora Applications with Dependency Injection { #building-kora-applications-dependency }

This guide introduces practical application assembly with Kora's compile-time dependency injection. It covers how `@KoraApp`, `@Module`, and `@Component` describe a dependency graph, how interfaces
and implementations are bound into that graph, and how lifecycle-aware services are started and stopped by the container. You will also see how module boundaries keep a complete application
understandable as it grows.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-dependency-injection).

## What You'll Build { #youll-build }

You'll build a complete notification system application that demonstrates all major Kora dependency injection features:

- **Multi-module project structure** with proper separation of concerns
- **Component-based architecture** with external library modules
- **Tagged dependencies** for multiple implementations of the same interface
- **Collection injection** to inject all implementations at once
- **Submodules** for organizing related components across Gradle modules
- **Generic factories** for type-safe component creation
- **Factory modules** for module instances that are themselves graph components
- **Nullable dependencies** for graceful handling of missing components
- **ValueOf<T>** pattern to prevent cascading component refreshes

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+
- A text editor or IDE
- Basic understanding of Java or Kotlin
- Familiarity with dependency injection concepts (see [Dependency Injection with Kora](dependency-injection-introduction.md))

## Prerequisites { #prerequisites }

!!! note "Recommended: Read the DI Introduction First"

    This tutorial assumes you have read **[Dependency Injection with Kora](dependency-injection-introduction.md)** and understand the basic dependency injection concepts used by Kora.

    If you haven't read the introduction yet, do that first, because this guide moves quickly into a complete multi-module application and focuses on applying DI patterns rather than defining them from scratch.

    You also need basic Java or Kotlin familiarity.

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

All of these annotations live in one package, `io.koraframework.common.annotation`, and all of them are read at compile time only. Nothing in this guide is resolved by reflection at startup: the
annotation processor (Java) or the symbol processor (Kotlin) reads the annotations and writes an `ApplicationGraph` class next to your `Application` type.

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

Some components own resources: clients, schedulers, connections, or background workers. Kora can manage lifecycle-aware components so startup and shutdown happen in graph order. The `Lifecycle`
contract for that lives in `io.koraframework.application.graph` and declares exactly two methods, `init()` and `release()`. The guide also introduces `ValueOf<T>` as a way to depend on a component
reference without eagerly forcing all downstream refresh behavior.

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

This guide uses a dedicated `settings.gradle` at the top level and keeps the shared Gradle configuration inside `guide-dependency-injection/build.gradle`. In the reference repository there is one
additional level above this tutorial directory because multiple guide applications live in the same workspace.

Create the project directories:

```bash
mkdir -p guide-dependency-injection
mkdir -p guide-dependency-injection/guide-dependency-injection-common guide-dependency-injection/guide-dependency-injection-lib guide-dependency-injection/guide-dependency-injection-app
```

Kora modules are published for Java 25, and the reference applications pin a Java 25 toolchain, so install Eclipse Temurin JDK 25 and run Gradle on it.

===! ":simple-linux: `Linux`"

    On Ubuntu/Debian, add the Adoptium repository and install Temurin JDK:

    ```bash
    sudo apt update
    sudo apt install -y wget gpg
    wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /usr/share/keyrings/adoptium.gpg
    echo "deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(. /etc/os-release && echo $VERSION_CODENAME) main" | sudo tee /etc/apt/sources.list.d/adoptium.list
    sudo apt update
    sudo apt install -y temurin-25-jdk
    ```

=== ":simple-apple: `macOS`"

    If Homebrew is installed, install Temurin JDK through cask:

    ```bash
    brew install --cask temurin@25
    export JAVA_HOME=$(/usr/libexec/java_home -v 25)
    ```

=== ":material-microsoft-windows: `Windows`"

    If `winget` is installed, install Temurin JDK from PowerShell:

    ```powershell
    winget install EclipseAdoptium.Temurin.25.JDK
    ```

    If `winget` is not available, download the Windows installer from the [Eclipse Temurin downloads page](https://adoptium.net/temurin/releases/?version=25), choose **JDK 25** for your CPU
    architecture, run the installer, and enable the option that updates `JAVA_HOME` and `PATH` when it is offered.

    Open a new terminal after installation so environment variables are refreshed.

Check that the JDK is available:

```bash
java -version
```

The output should show Java 25.

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

- register the tutorial submodules
- configure the JDK used to compile every submodule
- make the Kora BOM versions available to the required Gradle configurations
- enable Kora code generation in every module that declares graph elements
- apply common compile and test rules

#### Module Structure { #module-structure }

Create the following directory structure. The file extensions differ between Gradle Groovy DSL and Gradle Kotlin DSL, but the module boundaries stay the same:

===! ":fontawesome-brands-java: `Java`"

    ```
    |-- settings.gradle
    |-- gradle.properties
    `-- guide-dependency-injection/
        |-- build.gradle
        |-- guide-dependency-injection-common/
        |-- guide-dependency-injection-lib/
        `-- guide-dependency-injection-app/
    ```

=== ":simple-kotlin: `Kotlin`"

    ```
    |-- settings.gradle.kts
    |-- gradle.properties
    `-- guide-dependency-injection/
        |-- build.gradle.kts
        |-- guide-dependency-injection-common/
        |-- guide-dependency-injection-lib/
        `-- guide-dependency-injection-app/
    ```

`guide-dependency-injection-common` holds shared contracts, `guide-dependency-injection-lib` emulates a reusable library, and `guide-dependency-injection-app` contains the runnable application with
`@KoraApp`. A fourth module, `guide-dependency-injection-submodule`, is added later when the guide reaches `@KoraSubmodule`. This separation is what lets later steps demonstrate overrides, tags,
optional dependencies, and cross-module graph discovery.

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
    pluginManagement {
        plugins {
            id("org.jetbrains.kotlin.jvm") version "2.4.10" //(1)!
            id("com.google.devtools.ksp") version "2.3.11" //(2)!
        }
    }

    plugins {
        id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
    }

    rootProject.name = "kora-guide"

    include("guide-dependency-injection:guide-dependency-injection-common")
    include("guide-dependency-injection:guide-dependency-injection-lib")
    include("guide-dependency-injection:guide-dependency-injection-app")
    ```

    1.  Kotlin JVM plugin version, declared once for the whole build so module build files can apply the plugin without repeating the version.
    2.  KSP plugin version. It is tied to the Kotlin version, so the two are always raised together.

The `foojay-resolver-convention` plugin supports Java toolchains: it helps Gradle find or download the requested JDK. The include lines register nested modules through Gradle paths, such as
`:guide-dependency-injection:guide-dependency-injection-app`, so Gradle can run tasks for a specific module.

#### Gradle Properties { #gradle-properties }

Add `gradle.properties` so Gradle can detect installed JDKs, download the required Temurin toolchain when JDK 25 is not available locally, and share the Kora and JUnit versions across all modules:

===! ":fontawesome-brands-java: `Java`"

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true

    koraVersion=2.0.0.RC1
    junitVersion=6.1.3
    ```

=== ":simple-kotlin: `Kotlin`"

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true
    kotlin.jvm.target.validation.mode=warning

    koraVersion=2.0.0.RC1
    junitVersion=6.1.3
    ```

The first two properties make the tutorial build less dependent on the local machine. `koraVersion` and `junitVersion` are ordinary Gradle project properties: every module build file reads them as
`$koraVersion` and `$junitVersion`, so a version bump happens in exactly one place. The Kotlin-specific validation flag mirrors the reference applications: when the Kotlin compiler cannot target the
toolchain JVM version exactly, it reports the fallback as a warning instead of failing the build.

#### Shared Build File { #shared-build-file }

Create a shared build file under `guide-dependency-injection/`. It applies to the nested modules `common`, `lib`, `app`, and later `submodule`, so the toolchain, repositories, and test setup do not
have to be duplicated in every module.

Start with imports and an empty `subprojects` block:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    subprojects {
        repositories {
            mavenCentral()
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import org.gradle.api.plugins.JavaPluginExtension
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    subprojects {
        repositories {
            mavenCentral()
        }
    }
    ```

`mavenCentral()` is where Kora, Logback, HOCON, and their transitive dependencies are downloaded from.

#### Kora BOM { #kora-bom }

Kora is split into many modules. Instead of writing a version on every dependency, import a BOM (`Bill of Materials`) named `io.koraframework:kora-bom`. It aligns the versions of all Kora modules and
of the third-party libraries Kora ships with. Java and Kotlin wire that BOM in differently, and the difference is worth understanding before writing the rest of the build file.

===! ":fontawesome-brands-java: `Java`"

    In Java the BOM goes into a dedicated `koraBom` configuration declared once in `subprojects {}`. Nothing resolves it yet; the next sections make the real configurations extend it:

    ```groovy
    subprojects {
        configurations {
            koraBom
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    In Kotlin there is no shared BOM configuration. Each module imports the platform straight into `implementation`, which `testImplementation` already extends:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:$koraVersion"))
    }
    ```

    The `ksp` configuration does not extend `implementation`, so the Kora symbol processor is the one dependency that always carries an explicit version.

#### JDK Toolchain { #jdk-toolchain }

Configure the JDK after the `java` plugin is enabled in a submodule. Gradle may run on one JDK while compiling the project with another, so the toolchain makes the tutorial reproducible. Kora modules
are compiled for Java 25, so the toolchain must be Java 25 or newer.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    subprojects {
        plugins.withId("java") {
            java {
                toolchain {
                    languageVersion = JavaLanguageVersion.of(25)
                    vendor = JvmVendorSpec.ADOPTIUM
                }
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    subprojects {
        plugins.withId("org.jetbrains.kotlin.jvm") {
            extensions.configure<org.jetbrains.kotlin.gradle.dsl.KotlinJvmProjectExtension>("kotlin") {
                jvmToolchain {
                    languageVersion.set(JavaLanguageVersion.of(25))
                    vendor.set(JvmVendorSpec.ADOPTIUM)
                }
            }
        }

        plugins.withId("java") {
            extensions.configure<JavaPluginExtension>("java") {
                toolchain {
                    languageVersion.set(JavaLanguageVersion.of(25))
                    vendor.set(JvmVendorSpec.ADOPTIUM)
                }
            }
        }
    }
    ```

    Kotlin needs both blocks: `jvmToolchain` drives the Kotlin compiler, and the `java` toolchain drives `javac` for the Java sources KSP and Gradle still compile in the same module.

#### Classpath Configurations { #classpath-configurations }

Kora code generation runs on its own classpath, separate from the application classpath. In Java that is `annotationProcessor`; in Kotlin it is the `ksp` configuration added by the KSP plugin. Both
need the aligned Kora versions.

===! ":fontawesome-brands-java: `Java`"

    Make the BOM available to the configurations used by application code, compile-time APIs, annotation processing, public library APIs, and tests:

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

    `annotationProcessor` and `testAnnotationProcessor` receive the BOM separately because Kora annotation processors are resolved on their own classpath. The `api` configuration matters for `common`
    and `lib`, where types become part of the public API consumed by other modules.

=== ":simple-kotlin: `Kotlin`"

    Kotlin does not need a shared `extendsFrom` block. Every module that declares graph elements applies the KSP plugin and declares the processor with an explicit version:

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("java-library")
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:$koraVersion"))

        ksp("io.koraframework:symbol-processors:$koraVersion")
    }

    kotlin {
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
    }
    ```

    The `build/generated/ksp/main/kotlin` source directory matters for IDEs and for compilation, because KSP writes Kora-generated Kotlin code there. Modules that also generate code for test sources
    add `sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }`.

#### Kora Version { #kora-version }

Now import the BOM itself. The `$koraVersion` variable comes from `gradle.properties`; after this line, individual modules can declare Kora dependencies without explicit versions.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    subprojects {
        dependencies {
            koraBom platform("io.koraframework:kora-bom:$koraVersion")
        }
    }
    ```

    Because `implementation`, `annotationProcessor`, `compileOnly`, `testImplementation`, `testAnnotationProcessor`, and `api` all extend `koraBom`, a single line covers every module.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:$koraVersion"))

        ksp("io.koraframework:symbol-processors:$koraVersion")
    }
    ```

    In Kotlin these two lines live in each module build file rather than in the shared file, because `ksp` is only added by modules that apply the KSP plugin.

#### Final File { #final-file }

The final shared build file contains the same decisions together: repositories, the JDK toolchain, classpath wiring, the Kora BOM, and common test behavior.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    subprojects {
        repositories {
            mavenCentral()
        }

        configurations {
            koraBom
        }

        plugins.withId("java") {
            java {
                toolchain {
                    languageVersion = JavaLanguageVersion.of(25)
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
            koraBom platform("io.koraframework:kora-bom:$koraVersion")
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
        repositories {
            mavenCentral()
        }

        plugins.withId("org.jetbrains.kotlin.jvm") {
            extensions.configure<org.jetbrains.kotlin.gradle.dsl.KotlinJvmProjectExtension>("kotlin") {
                jvmToolchain {
                    languageVersion.set(JavaLanguageVersion.of(25))
                    vendor.set(JvmVendorSpec.ADOPTIUM)
                }
            }
        }

        plugins.withId("java") {
            extensions.configure<JavaPluginExtension>("java") {
                toolchain {
                    languageVersion.set(JavaLanguageVersion.of(25))
                    vendor.set(JvmVendorSpec.ADOPTIUM)
                }
            }
        }

        tasks.withType<Test>().configureEach {
            useJUnitPlatform()
            testLogging {
                showStandardStreams = true
                events("passed", "skipped", "failed")
                exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
            }
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

This guide uses the package `io.koraframework.guide.dependencyinjection`, the same package as the reference applications. Keeping the package stable makes it easier to compare your project with the
finished example and to find Kora-generated sources later.

**Create shared contracts** (`guide-dependency-injection/guide-dependency-injection-common/src/main/java/io/koraframework/guide/dependencyinjection/common/`
or `guide-dependency-injection/guide-dependency-injection-common/src/main/kotlin/io/koraframework/guide/dependencyinjection/common/`):

#### Build the Shared Module { #build-shared-module }

First, create the build file for `guide-dependency-injection-common`. This module contains only interfaces and shared types, so it needs a library-oriented JVM plugin and test dependencies, but not the
application plugin or Kora code generation.

===! ":fontawesome-brands-java: `Java`"

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
        testImplementation "io.koraframework:test-junit5"
    }
    ```

    `junit-bom` aligns JUnit versions, `junit-jupiter` adds JUnit 5, and `test-junit5` adds Kora testing utilities. This first step may not have tests yet, but the module is ready for contract and
    component checks. `test-junit5` needs no version because the shared build file already made `testImplementation` extend `koraBom`.

    The final common module `build.gradle` is:

    ```groovy
    plugins {
        id "java-library"
    }

    dependencies {
        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    The Kotlin JVM plugin compiles Kotlin code into JVM classes that the `app` and `lib` modules can use, and `java-library` separates the public API from implementation dependencies:

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("java-library")
    }
    ```

    Neither plugin carries a version here: both versions were declared once in `settings.gradle.kts`.

    Add the Kora BOM and test dependencies:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }
    ```

    `junit-bom` aligns JUnit versions, `junit-jupiter` adds JUnit 5, and `test-junit5` adds Kora testing utilities. `testImplementation` extends `implementation`, so the Kora BOM imported above is what
    lets `test-junit5` be declared without a version.

    The final common module `build.gradle.kts` is:

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("java-library")
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }
    ```

Then create the interfaces:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.common;

    public interface Notifier {
        void notify(String user, String message);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.common

    fun interface Notifier {
        fun notify(user: String, message: String)
    }
    ```

`Notifier` is declared as a `fun interface` in Kotlin so that module factories can return it as a lambda later in the guide.

**Create the main application** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/io/koraframework/guide/dependencyinjection/`
or `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/io/koraframework/guide/dependencyinjection/`):

#### Build the Application { #build-application }

Create the build file for `guide-dependency-injection-app`. This module is runnable, contains `@KoraApp`, and must enable Kora graph generation, so its Gradle setup is more involved than the shared
contract module.

===! ":fontawesome-brands-java: `Java`"

    Start with plugins:

    ```groovy
    plugins {
        id "application"
    }
    ```

    The `application` plugin applies `java` for you and adds `./gradlew run` plus main-class configuration, so no separate `id "java"` line is needed.

    Add the Kora annotation processor:

    ```groovy
    dependencies {
        annotationProcessor "io.koraframework:annotation-processors"
    }
    ```

    `annotationProcessor` reads `@KoraApp` and generates `ApplicationGraph`. Without this line, Java compilation can reach the generated class reference, but the application graph itself will not be
    produced.

    Now add application dependencies:

    ```groovy
    dependencies {
        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"
    }
    ```

    `common` provides the shared `Notifier` interface, `config-hocon` provides configuration, and `logging-logback` adds logging. The `lib` and `submodule` project dependencies are added in the steps
    that create those modules.

    Add test setup:

    ```groovy
    dependencies {
        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

    `testAnnotationProcessor` is only needed when test sources declare their own `@KoraApp` or Kora annotations that must be processed. `test-junit5` adds the Kora JUnit 5 extension.

    Configure application startup:

    ```groovy
    application {
        applicationName = "application"
        mainClass = "io.koraframework.guide.dependencyinjection.Application"
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
        id "application"
    }

    dependencies {
        annotationProcessor "io.koraframework:annotation-processors"

        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"

        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }

    application {
        applicationName = "application"
        mainClass = "io.koraframework.guide.dependencyinjection.Application"
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
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("application")
    }
    ```

    `org.jetbrains.kotlin.jvm` compiles Kotlin code, `com.google.devtools.ksp` runs the Kora symbol processor, and `application` adds `./gradlew run`.

    Add the Kora BOM and the KSP processor:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")
    }
    ```

    KSP reads `@KoraApp` and generates `ApplicationGraph`. Without this dependency, the application will not get the generated graph. The `ksp` configuration is not covered by the BOM, so it keeps an
    explicit version.

    Now add application dependencies:

    ```kotlin
    dependencies {
        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")
    }
    ```

    `common` provides the shared `Notifier` interface, `config-hocon` provides HOCON configuration, and `logging-logback` adds logging. The `lib` and `submodule` project dependencies are added in the
    steps that create those modules.

    Add test dependencies:

    ```kotlin
    dependencies {
        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }
    ```

    There is no `kspTest(...)` line here. It is only needed when test sources declare their own `@KoraApp` or other Kora annotations that must be processed; tests that reuse the main `Application`
    graph through `@KoraAppTest` do not.

    Register the KSP output directories and configure startup:

    ```kotlin
    kotlin {
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    application {
        applicationName = "application"
        mainClass.set("io.koraframework.guide.dependencyinjection.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }
    ```

    The `application` block tells Gradle how to launch the Kotlin application:

    - `applicationName` sets the distribution application name and startup script name.
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
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("application")
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }

    kotlin {
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    application {
        applicationName = "application"
        mainClass.set("io.koraframework.guide.dependencyinjection.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }

    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

Then create the application:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends HoconConfigModule, LogbackModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application : HoconConfigModule, LogbackModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`KoraApplication.run(...)` accepts a `Supplier<ApplicationGraphDraw>`, and the generated `ApplicationGraph` class provides exactly that through its static `graph()` method, which is why the method
reference `ApplicationGraph::graph` fits. The generated class is always named after the `@KoraApp` type plus the `Graph` suffix, so an `Application` interface produces `ApplicationGraph`. It does not
exist until annotation processing or KSP has run once.

**Build and run**:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

**Expected Output**: The application starts and shuts down cleanly. Kora logs `Application initialized in ...ms` and, on `Ctrl+C`, `Application shutdown...`. The graph has no root component yet, so
nothing else happens; the next steps add components and modules.

---

### External Modules { #external-modules }

**Goal**: Create reusable library modules that provide default implementations.

**What this step introduces**: external module factories and `@DefaultComponent`. The `EmailModule` lives outside the application module and exposes defaults that the application can adopt or replace
later.

**Why we need it**: external modules are how reusable Kora libraries publish components to applications, but they are not auto-discovered and must be connected explicitly. This
follows [Dependency Injection with Kora: @Module](dependency-injection-introduction.md#module), [@DefaultComponent](dependency-injection-introduction.md#defaultcomponent)
and [Container documentation: External module factory](../documentation/container.md#external-module-factory).

**What we are emulating**: a library that ships a default email notifier implementation and configuration contract, while still allowing the application to override presentation details later.

First, create the library module build file. Unlike `common`, this module declares a `@ConfigMapper` type, so it needs Kora code generation of its own:

===! ":fontawesome-brands-java: `Java`"

    `guide-dependency-injection/guide-dependency-injection-lib/build.gradle`

    ```groovy
    plugins {
        id "java-library"
    }

    dependencies {
        annotationProcessor "io.koraframework:annotation-processors"

        api project(":guide-dependency-injection:guide-dependency-injection-common")

        implementation "io.koraframework:config-common"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `guide-dependency-injection/guide-dependency-injection-lib/build.gradle.kts`

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("java-library")
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        api(project(":guide-dependency-injection:guide-dependency-injection-common"))

        implementation("io.koraframework:config-common")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }

    kotlin {
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
    }
    ```

`api project(...)` is deliberate: `Notifier` appears in the signatures this module exposes, so consumers of `lib` must see it too. `config-common` brings the configuration contracts `Config` and
`ConfigValueMapper` without forcing a specific configuration format on the library — the application decides between HOCON and YAML.

Then register the new module in the root settings file and add it to the application classpath:

===! ":fontawesome-brands-java: `Java`"

    `settings.gradle` already contains the module, and `guide-dependency-injection-app/build.gradle` now depends on it:

    ```groovy
    dependencies {
        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation project(":guide-dependency-injection:guide-dependency-injection-lib")
        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `settings.gradle.kts` already contains the module, and `guide-dependency-injection-app/build.gradle.kts` now depends on it:

    ```kotlin
    dependencies {
        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-lib"))
        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")
    }
    ```

**Create EmailConfig** (`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/io/koraframework/guide/dependencyinjection/email/`
or `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/io/koraframework/guide/dependencyinjection/email/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.email;

    import io.koraframework.config.common.annotation.ConfigMapper;

    @ConfigMapper
    public record EmailConfig(String topic) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.email

    import io.koraframework.config.common.annotation.ConfigMapper

    @ConfigMapper
    data class EmailConfig(val topic: String)
    ```

`@ConfigMapper` is the library-side configuration annotation: it tells Kora to generate a `ConfigValueMapper<EmailConfig>` without binding the type to a fixed configuration path. The module method
below is what chooses the path, so the same config type can be reused under different sections. For an application-owned configuration type bound to one path, use `@ConfigSource` instead — see
[Configuration](../documentation/config.md).

**Create EmailModule** (same package):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.email;

    import java.util.function.Supplier;
    import io.koraframework.common.annotation.DefaultComponent;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.config.common.Config;
    import io.koraframework.config.common.mapper.ConfigValueMapper;
    import io.koraframework.guide.dependencyinjection.common.Notifier;

    public interface EmailModule {

        final class EmailTag {
            private EmailTag() {}
        }

        default EmailConfig config(Config config, ConfigValueMapper<EmailConfig> extractor) {
            return extractor.mapOrThrow(config.get("notifier.email")); //(1)!
        }

        @Tag(EmailTag.class)
        @DefaultComponent //(2)!
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL DEFAULT] ";
        }

        @Tag(EmailTag.class)
        default Notifier emailNotifier(EmailConfig emailConfig, @Tag(EmailTag.class) Supplier<String> headerSupplier) {
            return (user, message) -> System.out.println(headerSupplier.get() + emailConfig.topic() + " [USER:" + user + "]: " + message);
        }
    }
    ```

    1.  `mapOrThrow` fails the graph build with a configuration error when the section is missing or cannot be mapped. Use `map` instead if a missing section should produce `null`.
    2.  Marks the factory as a default: the application may declare its own factory for the same type and tag, and Kora will prefer the application one.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.email

    import java.util.function.Supplier
    import io.koraframework.common.annotation.DefaultComponent
    import io.koraframework.common.annotation.Tag
    import io.koraframework.config.common.Config
    import io.koraframework.config.common.mapper.ConfigValueMapper
    import io.koraframework.guide.dependencyinjection.common.Notifier

    interface EmailModule {

        class EmailTag private constructor()

        fun config(config: Config, extractor: ConfigValueMapper<EmailConfig>): EmailConfig {
            return extractor.mapOrThrow(config["notifier.email"]) //(1)!
        }

        @Tag(EmailTag::class)
        @DefaultComponent //(2)!
        fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL DEFAULT] " }
        }

        @Tag(EmailTag::class)
        fun emailNotifier(
            emailConfig: EmailConfig,
            @Tag(EmailTag::class) headerSupplier: Supplier<String>
        ): Notifier {
            return Notifier { user, message ->
                println("${headerSupplier.get()}${emailConfig.topic} [USER:$user]: $message")
            }
        }
    }
    ```

    1.  `mapOrThrow` fails the graph build with a configuration error when the section is missing or cannot be mapped. Use `map` instead if a missing section should produce `null`.
    2.  Marks the factory as a default: the application may declare its own factory for the same type and tag, and Kora will prefer the application one.

`EmailTag` is an ordinary nested class used only as a compile-time marker. It never gets instantiated, which is why it can have a private constructor. Tag classes must be visible from every place that
references them, so a package-private or `private` top-level tag will not work across modules.

**Update Application** to include the email module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        EmailModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
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
        "io.koraframework": "INFO" //(3)!
      }
    }
    ```

    1.  Topic or channel name used by the component.
    2.  Log level for `ROOT`.
    3.  Log level for `io.koraframework`, which is also the package of this tutorial application.

=== ":simple-yaml: `YAML`"

    ```yaml
    notifier:
      email:
        topic: "USER" #(1)!

    logging:
      levels:
        ROOT: "WARN" #(2)!
        "io.koraframework": "INFO" #(3)!
    ```

    1.  Topic or channel name used by the component.
    2.  Log level for `ROOT`.
    3.  Log level for `io.koraframework`, which is also the package of this tutorial application.

The application module depends on `config-hocon`, so `application.conf` is what actually gets read. Switch the dependency to `io.koraframework:config-yaml` and the module to `YamlConfigModule` if you
prefer the YAML file instead.

**Build and run** - Application still has no root component, so it just starts and stops.

**Key Concept**: `@DefaultComponent` provides library defaults that applications can override.

**Module registration rule**: if a type is annotated with `@Module`, do not also wire it through `extends` on `@KoraApp` or another module. A module should be registered in exactly one way: either
inherited with `extends`, or discovered because it is annotated with `@Module` and is compiled together with the current `@KoraApp` / `@KoraSubmodule`. `@KoraSubmodule` itself is the case where
inheritance is expected, because the processor looks for `@KoraSubmodule` only among the interfaces the `@KoraApp` type extends.

Note that `@Module` may only be applied to interfaces. Applying it to a class fails compilation with `@Module can only be applied to interfaces.`

**What Kora generates for `EmailModule`**: after `./gradlew clean classes`, `ApplicationGraph` will not necessarily contain the exact same `componentN` numbers shown below, because those names are
internal generator details. The structure is the important part: Kora creates a configuration node, a default value node, and the notifier node.

===! ":fontawesome-brands-java: `Java`"

    ??? abstract "Java: generated graph fragment for `EmailModule`"

        ```java
        private final Node<EmailConfig> component8;
        private final Node<Supplier<String>> component9;
        private final Node<Notifier> component10;

        component8 = graphDraw.addNode(_type_of_component8,
            null,
            null,
            List.of(component6, component7),
            List.of(component6, component7),
            List.of(),
            g -> impl.config(
                g.get(ApplicationGraph.holder0.component6),
                g.get(ApplicationGraph.holder0.component7)
            ));

        component9 = graphDraw.addNode(_type_of_component9,
            EmailModule.EmailTag.class,
            null,
            List.of(),
            List.of(),
            List.of(),
            g -> impl.emailNotifierHeaderSupplier());

        component10 = graphDraw.addNode(_type_of_component10,
            EmailModule.EmailTag.class,
            null,
            List.of(component8, component9),
            List.of(component8, component9),
            List.of(),
            g -> impl.emailNotifier(
                g.get(ApplicationGraph.holder0.component8),
                g.get(ApplicationGraph.holder0.component9)
            ));
        ```

        This shows why `EmailModule` must be connected through `extends`: only then do its factory methods become part of the application graph.

        - `component8` reads `notifier.email` and turns HOCON configuration into typed `EmailConfig`.
        - `component9` is a tagged `Supplier<String>` with `EmailTag`. This lets Kora distinguish the email header from other possible `Supplier<String>` components.
        - `component10` is a tagged `Notifier` that depends on `EmailConfig` and the tagged `Supplier<String>`.
        - The second argument of `addNode` is the tag, the third is an optional `@Conditional` predicate, and the two `List.of(...)` arguments are the create-time and refresh-time dependencies.
        - `@DefaultComponent` on `emailNotifierHeaderSupplier()` means the library provides a default value, and the application can replace it in the next section.

=== ":simple-kotlin: `Kotlin`"

    ??? abstract "Kotlin: generated graph fragment for `EmailModule`"

        ```kotlin
        public val component8: Node<EmailConfig>
        public val component9: Node<Supplier<String>>
        public val component10: Node<Notifier>

        component8 = graphDraw.addNode(map["component8"],
          null,
          null,
          listOf(component6, component7),
          listOf(component6, component7),
          listOf(),
          { impl.config(
            it.get(holder0.component6),
            it.get(holder0.component7)
          ) }
        )

        component9 = graphDraw.addNode(map["component9"],
          EmailModule.EmailTag::class.java,
          null,
          listOf(),
          listOf(),
          listOf(),
          { impl.emailNotifierHeaderSupplier() }
        )

        component10 = graphDraw.addNode(map["component10"],
          EmailModule.EmailTag::class.java,
          null,
          listOf(component8, component9),
          listOf(component8, component9),
          listOf(),
          { impl.emailNotifier(
            it.get(holder0.component8),
            it.get(holder0.component9)
          ) }
        )
        ```

        Kotlin/KSP generates the same meaning in Kotlin code:

        - `EmailConfig` becomes a separate graph node.
        - `EmailTag` is passed as the node tag for both `Supplier<String>` and `Notifier`.
        - `emailNotifier(...)` receives dependencies from the graph instead of creating them itself.
        - In the next section, the application overrides `emailNotifierHeaderSupplier()`, and Kora substitutes the new node for the library `@DefaultComponent`.

---

### Component Override { #component-override }

**Goal**: Show how applications can override library defaults.

**What this step introduces**: component override of a `@DefaultComponent` factory from an external module. The application replaces only the header supplier and keeps the rest of the library behavior
intact.

**Why we need it**: libraries should provide safe defaults, but applications must keep final control over business-facing behavior. This
matches [Dependency Injection with Kora: Standard factory](dependency-injection-introduction.md#defaultcomponent-factory), [@DefaultComponent](dependency-injection-introduction.md#defaultcomponent)
and [Container documentation: Standard factory](../documentation/container.md#default-factory).

**What we are emulating**: application-specific customization of a shared library notifier without forking or rewriting the entire module.

**Create NotifyRunner** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/io/koraframework/guide/dependencyinjection/`
or `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/io/koraframework/guide/dependencyinjection/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection;

    import io.koraframework.application.graph.All;
    import io.koraframework.application.graph.Lifecycle;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Root;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.dependencyinjection.common.Notifier;

    @Root //(1)!
    @Component
    public final class NotifyRunner implements Lifecycle {

        private final All<Notifier> allNotifiers;

        public NotifyRunner(@Tag(Tag.Any.class) All<Notifier> allNotifiers) { //(2)!
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

    1.  Nothing depends on `NotifyRunner`, so without `@Root` Kora would prune it from the graph and it would never be created.
    2.  `@Tag(Tag.Any.class)` widens the claim to every `Notifier` regardless of tag. Without it, an untagged `All<Notifier>` claim matches untagged notifiers only.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection

    import io.koraframework.application.graph.All
    import io.koraframework.application.graph.Lifecycle
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Root
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.dependencyinjection.common.Notifier

    @Root //(1)!
    @Component
    class NotifyRunner(
        @Tag(Tag.Any::class) private val allNotifiers: All<Notifier> //(2)!
    ) : Lifecycle {

        override fun init() {
            println("DI tutorial step 3 start")
            for (notifier in allNotifiers) {
                notifier.notify("Alice", "Welcome!")
            }
        }

        override fun release() {
            println("Application shutdown")
        }
    }
    ```

    1.  Nothing depends on `NotifyRunner`, so without `@Root` Kora would prune it from the graph and it would never be created.
    2.  `@Tag(Tag.Any::class)` widens the claim to every `Notifier` regardless of tag. Without it, an untagged `All<Notifier>` claim matches untagged notifiers only.

`Lifecycle` comes from `io.koraframework.application.graph` and declares exactly two methods, `init()` and `release()`. Kora calls `init()` in graph order during startup and `release()` in reverse
order during shutdown, so a component is always initialized after everything it depends on and released before them.

**Update Application** to override the email header:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import java.util.function.Supplier;
    import io.koraframework.common.annotation.Tag;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

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
    import io.koraframework.common.annotation.Tag

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

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

The override is an ordinary Java or Kotlin method override, so the compiler already guarantees the signature matches. `@Tag` must be repeated on the override: the tag is part of the component identity,
not something inherited from the overridden method. Note also that the override intentionally drops `@DefaultComponent`, which is what makes the application factory win over the library default.

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

**Create the SMS provider contract** in the library module
(`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/io/koraframework/guide/dependencyinjection/sms/`
or `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/io/koraframework/guide/dependencyinjection/sms/`). Only the contract exists for now; nothing provides it yet:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.sms;

    public interface SmsCellularProvider {
        String getCode();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.sms

    fun interface SmsCellularProvider {
        fun getCode(): String
    }
    ```

**Create SmsModule** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/io/koraframework/guide/dependencyinjection/sms/`
or `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/io/koraframework/guide/dependencyinjection/sms/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.sms;

    import org.jspecify.annotations.Nullable;
    import io.koraframework.common.annotation.Module;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.dependencyinjection.common.Notifier;

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
    package io.koraframework.guide.dependencyinjection.sms

    import io.koraframework.common.annotation.Module
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.dependencyinjection.common.Notifier

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

Java uses [JSpecify](https://jspecify.dev/) `org.jspecify.annotations.Nullable` for optional dependencies. It comes transitively with any Kora module, so no extra dependency is needed. Kotlin has no
annotation at all: the `?` on the parameter type is the whole declaration.

**Application note**: `SmsModule` is annotated with `@Module` and is compiled together with `@KoraApp`, so Kora discovers it automatically. Do not add it with `extends` on `Application`. The
`Application` interface stays exactly as it was in the previous step:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

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
        EmailModule {  // <----- Connected module

        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

**Update NotifyRunner** to iterate over all notifiers:

===! ":fontawesome-brands-java: `Java`"

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
            for (notifier in allNotifiers) {
                notifier.notify("Bob", "Hello!")
            }
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

The SMS line has no provider code yet, because nothing in the graph provides `SmsCellularProvider` and the nullable parameter resolved to `null`. The next step fixes that.

**Key Concept**: `@Tag` allows multiple implementations of the same contract, and `@Tag(Tag.Any.class) All<T>` lets you broadcast to all of them.

---

### Optional Dependencies { #optional-dependencies }

**Goal**: Add an optional collaborator for SMS without changing the `Notifier` contract.

**What this step introduces**: nullable dependencies for optional behavior. `SmsModule` can work with or without `SmsCellularProvider`, and `SmsCellularModule` adds the provider only when the
application chooses to inherit it.

**Why we need it**: some features should enrich an existing component rather than force a separate implementation branch. This
follows [Dependency Injection with Kora: Nullable](dependency-injection-introduction.md#optional)
and [Container documentation: Optional dependencies](../documentation/container.md#optional-dependencies).

**What we are emulating**: optional enrichment of SMS formatting with a provider code, where the notifier still functions even if that provider is not configured.

**Create SmsCellularModule** next to `SmsCellularProvider` in the library module
(`guide-dependency-injection/guide-dependency-injection-lib/src/main/java/io/koraframework/guide/dependencyinjection/sms/`
or `guide-dependency-injection/guide-dependency-injection-lib/src/main/kotlin/io/koraframework/guide/dependencyinjection/sms/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.sms;

    import io.koraframework.common.annotation.DefaultComponent;

    public interface SmsCellularModule {

        @DefaultComponent
        default SmsCellularProvider smsCellularProvider() {
            return () -> "1";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.sms

    import io.koraframework.common.annotation.DefaultComponent

    interface SmsCellularModule {

        @DefaultComponent
        fun smsCellularProvider(): SmsCellularProvider {
            return SmsCellularProvider { "1" }
        }
    }
    ```

**Update Application** to include the provider module. `SmsCellularModule` is not annotated with `@Module`, so this one is intentionally connected through `extends`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule,  // <----- Connected module
            SmsCellularModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

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

**Key Concept**: `@Nullable` in Java and nullable types in Kotlin let a component keep working even when an optional dependency is absent. A missing required dependency is a compile-time error; a
missing optional one silently resolves to `null`, so keep the null branch meaningful.

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

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    plugins {
        id "java-library"
    }

    dependencies {
        annotationProcessor "io.koraframework:annotation-processors" //(1)!

        api project(":guide-dependency-injection:guide-dependency-injection-common")

        implementation "io.koraframework:common" //(2)!

        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

    1.  Required: `@KoraSubmodule` is processed in this module, not in the application module. The processor writes a `MessengerModuleSubmoduleImpl` interface here, and the application module later
        inherits it through `MessengerModule`.
    2.  `io.koraframework:common` carries the DI annotations and, transitively, `application-graph` with `All`, `ValueOf`, and `Lifecycle`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("java-library")
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}") //(1)!

        api(project(":guide-dependency-injection:guide-dependency-injection-common"))

        implementation("io.koraframework:common") //(2)!

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }

    kotlin {
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }
    ```

    1.  Required: `@KoraSubmodule` is processed in this module, not in the application module. KSP writes a `MessengerModuleSubmoduleImpl` interface here, and the application module later inherits it
        through `MessengerModule`.
    2.  `io.koraframework:common` carries the DI annotations and, transitively, `application-graph` with `All`, `ValueOf`, and `Lifecycle`.

**Update `guide-dependency-injection-app` build file to add the new module dependency**:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        annotationProcessor "io.koraframework:annotation-processors"

        implementation project(":guide-dependency-injection:guide-dependency-injection-common")
        implementation project(":guide-dependency-injection:guide-dependency-injection-lib")
        implementation project(":guide-dependency-injection:guide-dependency-injection-submodule")
        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"

        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        implementation(project(":guide-dependency-injection:guide-dependency-injection-common"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-lib"))
        implementation(project(":guide-dependency-injection:guide-dependency-injection-submodule"))
        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }
    ```

**Create MessengerModule** (`guide-dependency-injection/guide-dependency-injection-submodule/src/main/java/io/koraframework/guide/dependencyinjection/messenger/`
or `guide-dependency-injection/guide-dependency-injection-submodule/src/main/kotlin/io/koraframework/guide/dependencyinjection/messenger/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.messenger;

    import io.koraframework.common.annotation.KoraSubmodule;

    @KoraSubmodule
    public interface MessengerModule {

        final class MessengerTag {
            private MessengerTag() {}
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.messenger

    import io.koraframework.common.annotation.KoraSubmodule

    @KoraSubmodule
    interface MessengerModule {

        class MessengerTag private constructor()
    }
    ```

The interface body is almost empty on purpose. `@KoraSubmodule` is a marker: during compilation of this Gradle module, Kora collects every `@Module` and `@Component` declared in the same compilation
unit and writes them into a generated interface named `MessengerModuleSubmoduleImpl`. The application picks all of that up by extending `MessengerModule`.

**Create Messenger interface**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.messenger;

    public interface Messenger {
        void sendMessage(String message);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.messenger

    fun interface Messenger {
        fun sendMessage(message: String)
    }
    ```

**Create SlackMessenger**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.messenger.slack;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.dependencyinjection.messenger.Messenger;

    @Tag(SlackMessenger.class) //(1)!
    @Component
    public final class SlackMessenger implements Messenger {

        @Override
        public void sendMessage(String message) {
            System.out.println("Slack: " + message);
        }
    }
    ```

    1.  A component can be its own tag. That is convenient when the only purpose of the tag is to identify one specific implementation.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.messenger.slack

    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.dependencyinjection.messenger.Messenger

    @Tag(SlackMessenger::class) //(1)!
    @Component
    class SlackMessenger : Messenger {

        override fun sendMessage(message: String) {
            println("Slack: $message")
        }
    }
    ```

    1.  A component can be its own tag. That is convenient when the only purpose of the tag is to identify one specific implementation.

**Create MessengerNotifier**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.messenger;

    import io.koraframework.application.graph.All;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.dependencyinjection.common.Notifier;

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
    package io.koraframework.guide.dependencyinjection.messenger

    import io.koraframework.application.graph.All
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.dependencyinjection.common.Notifier

    @Tag(MessengerModule.MessengerTag::class)
    @Component
    class MessengerNotifier(
        @Tag(Tag.Any::class) private val messengers: All<Messenger>
    ) : Notifier {

        override fun notify(user: String, message: String) {
            println("Broadcasting to messengers")
            for (messenger in messengers) {
                messenger.sendMessage("$user@$message")
            }
            println("Messenger broadcast complete")
        }
    }
    ```

**Update Application** to include the messenger submodule. `MessengerModule` is annotated with `@KoraSubmodule`, so this is the case where inheritance is expected:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            EmailModule,  // <----- Connected module
            SmsCellularModule,  // <----- Connected module
            MessengerModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }

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

!!! warning "Kora submodule was not generated yet"

    If the application module fails with `Kora submodule was not generated yet: expected type: ...MessengerModuleSubmoduleImpl`, the submodule's own Gradle module did not run the Kora processor.
    Check that `guide-dependency-injection-submodule` declares `annotationProcessor "io.koraframework:annotation-processors"` (Java) or `ksp("io.koraframework:symbol-processors:...")` (Kotlin), then
    run `./gradlew clean classes` so the generated interface exists before the application module is compiled.

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

**Create Storage interface** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/io/koraframework/guide/dependencyinjection/storage/`
or `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/io/koraframework/guide/dependencyinjection/storage/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.storage;

    public interface Storage<T> {
        void save(T data);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.storage

    interface Storage<T> {
        fun save(data: T)
    }
    ```

**Create TempFileStorage**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.storage;

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
    package io.koraframework.guide.dependencyinjection.storage

    import java.nio.file.Files
    import java.util.function.Function

    class TempFileStorage<T>(
        private val mapper: Function<T, ByteArray>
    ) : Storage<T> {

        override fun save(data: T) {
            val tempFile = Files.createTempFile("storage-", ".tmp")
            Files.write(tempFile, mapper.apply(data))
            println("Saved to: ${tempFile.fileName}")
        }
    }
    ```

`TempFileStorage` is not annotated. It is created by the module factory below, and a `@Component` annotation here would add a second, conflicting provider for the same type.

**Create StorageModule**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.storage;

    import java.nio.charset.StandardCharsets;
    import java.util.function.Function;
    import io.koraframework.common.annotation.Module;

    @Module
    public interface StorageModule {

        default Function<Integer, byte[]> intMapper() {
            return i -> new byte[] {i.byteValue()};
        }

        default Function<String, byte[]> stringMapper() {
            return s -> s.getBytes(StandardCharsets.UTF_8);
        }

        default <T> Storage<T> typedStorage(Function<T, byte[]> mapper) { //(1)!
            return new TempFileStorage<>(mapper);
        }
    }
    ```

    1.  A factory method with its own type parameter is a *template*. Kora does not instantiate it eagerly: it creates one node per concrete `Storage<T>` actually requested by some other component,
        resolving `Function<T, byte[]>` for that same `T`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.storage

    import java.nio.charset.StandardCharsets
    import java.util.function.Function
    import io.koraframework.common.annotation.Module

    @Module
    interface StorageModule {

        fun intMapper(): Function<Int, ByteArray> {
            return Function { i -> byteArrayOf(i.toByte()) }
        }

        fun stringMapper(): Function<String, ByteArray> {
            return Function { s -> s.toByteArray(StandardCharsets.UTF_8) }
        }

        fun <T> typedStorage(mapper: Function<T, ByteArray>): Storage<T> { //(1)!
            return TempFileStorage(mapper)
        }
    }
    ```

    1.  A factory method with its own type parameter is a *template*. Kora does not instantiate it eagerly: it creates one node per concrete `Storage<T>` actually requested by some other component,
        resolving `Function<T, ByteArray>` for that same `T`.

The Kotlin version deliberately uses `java.util.function.Function` rather than a Kotlin function type such as `(T) -> ByteArray`. Kotlin function types compile to `kotlin.jvm.functions.FunctionN`,
which makes every one-argument function the same erased type in the graph, so a `(Int) -> ByteArray` and a `(String) -> ByteArray` become indistinguishable candidates. An explicit `Function<T, R>`
keeps both type arguments visible to the resolver.

**Application note**: No `Application` changes are required here. `StorageModule` is compiled together with `@KoraApp` and is annotated with `@Module`, so Kora discovers it as an application module
automatically.

**Update NotifyRunner** to use `Storage<String>`:

===! ":fontawesome-brands-java: `Java`"

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
        private val stringStorage: Storage<String>
    ) : Lifecycle {

        override fun init() {
            println("DI tutorial step 7 start")
            for (notifier in allNotifiers) {
                notifier.notify("Charlie", "Greetings!")
            }
            stringStorage.save("User data stored")
        }

        override fun release() {
            println("Application shutdown")
        }
    }
    ```

Only `Storage<String>` is requested, so only `stringMapper()` and one `Storage<String>` node end up in the graph. `intMapper()` stays unused and, because nothing claims it, it is never instantiated.

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

#### Factory Module { #factory-module-object }

There is a second way to group factories, and it is worth knowing because it solves a different problem. A `@Module` interface is stateless: Kora instantiates an anonymous implementation of it and
calls its default methods. A **factory module** is an ordinary object that is itself a graph component and whose public methods are also treated as factories. That lets one module instance carry
construction state — a client, a prefix, a configuration object — and hand it to every component it creates.

The snippet below illustrates the shape. It is not part of the tutorial application, because it would provide a second `Storage<String>` and collide with the generic factory above:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ArchiveFactory { //(1)!

        private final Function<String, byte[]> mapper;

        public ArchiveFactory(Function<String, byte[]> mapper) {
            this.mapper = mapper;
        }

        public Archive archive() { //(2)!
            return data -> mapper.apply(data).length;
        }
    }

    @Module
    public interface ArchiveModule {

        @FactoryModule //(3)!
        default ArchiveFactory archiveFactory(Function<String, byte[]> mapper) {
            return new ArchiveFactory(mapper);
        }
    }
    ```

    1.  A plain class, not an interface, and not annotated.
    2.  Public methods of the returned object become component factories, exactly like default methods of a `@Module` interface.
    3.  `@FactoryModule` from `io.koraframework.common.annotation`. It registers `ArchiveFactory` itself as a graph node and also processes its methods as providers.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ArchiveFactory( //(1)!
        private val mapper: Function<String, ByteArray>
    ) {

        fun archive(): Archive { //(2)!
            return Archive { data -> mapper.apply(data).size }
        }
    }

    @Module
    interface ArchiveModule {

        @FactoryModule //(3)!
        fun archiveFactory(mapper: Function<String, ByteArray>): ArchiveFactory {
            return ArchiveFactory(mapper)
        }
    }
    ```

    1.  A plain class, not an interface, and not annotated.
    2.  Public methods of the returned object become component factories, exactly like methods of a `@Module` interface.
    3.  `@FactoryModule` from `io.koraframework.common.annotation`. It registers `ArchiveFactory` itself as a graph node and also processes its methods as providers.

Two factory modules of the same type can coexist if they carry different tags, and inside such a module `@Tag(Tag.Factory.class)` means "the tag of the enclosing factory module". That is how one class
can be instantiated twice, each instance producing its own tagged set of components. Using `@Tag.Factory` outside a factory module is a compile error:
`@Tag.Factory can only be used inside factory modules.`

See [Container documentation: Factory module](../documentation/container.md#factory-module) and [Dependency Injection with Kora: Factory Module](dependency-injection-introduction.md#factory-module) for
the full contract.

---

### Update Management { #update-management }

**Goal**: Demonstrate `ValueOf<T>` for preventing unwanted cascading refreshes when dependencies are updated.

**What this step introduces**: `ValueOf<T>`, `Wrapped<T>`, and `LifecycleWrapper` for lifecycle-aware, indirectly accessed dependencies. `ActivityService` stays stable while `ActivityRecorder` remains
lazily accessible and lifecycle-managed.

**Why we need it**: some infrastructure dependencies are expensive or refreshable, and we do not want every consumer to be recreated just because that dependency changes. This
follows [Dependency Injection with Kora: ValueOf](dependency-injection-introduction.md#valueof) and [Container documentation: Component lifecycle](../documentation/container.md#component-lifecycle).

**What we are emulating**: a service that records activity through a managed connector which can be started, stopped, or refreshed independently from the business service using it.

**Create ActivityRecorder interface** (`guide-dependency-injection/guide-dependency-injection-app/src/main/java/io/koraframework/guide/dependencyinjection/activity/`
or `guide-dependency-injection/guide-dependency-injection-app/src/main/kotlin/io/koraframework/guide/dependencyinjection/activity/`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.activity;

    public interface ActivityRecorder {

        void connect();

        void disconnect();

        boolean isConnected();

        void recordUser(String user);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.activity

    interface ActivityRecorder {

        fun connect()

        fun disconnect()

        fun isConnected(): Boolean

        fun recordUser(user: String)
    }
    ```

**Create ActivityService**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.activity;

    import io.koraframework.application.graph.ValueOf;
    import io.koraframework.common.annotation.Component;

    @Component
    public final class ActivityService {

        private final ValueOf<ActivityRecorder> activityRecorder;

        public ActivityService(ValueOf<ActivityRecorder> activityRecorder) {
            this.activityRecorder = activityRecorder;
            System.out.println("ActivityService created (ActivityRecorder not yet accessed)");
        }

        public void recordActivityByUserName(String user) {
            System.out.println("Recording activity for: " + user);
            ActivityRecorder recorder = activityRecorder.get(); //(1)!
            recorder.recordUser(user);
            System.out.println("Activity recorded successfully");
        }
    }
    ```

    1.  `ValueOf.get()` always returns the current instance from the graph. Call it at use time, never cache the result in a field, otherwise a refresh would leave a stale reference behind.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.activity

    import io.koraframework.application.graph.ValueOf
    import io.koraframework.common.annotation.Component

    @Component
    class ActivityService(
        private val activityRecorder: ValueOf<ActivityRecorder>
    ) {

        init {
            println("ActivityService created (ActivityRecorder not yet accessed)")
        }

        fun recordActivityByUserName(user: String) {
            println("Recording activity for: $user")
            val recorder = activityRecorder.get() //(1)!
            recorder.recordUser(user)
            println("Activity recorded successfully")
        }
    }
    ```

    1.  `ValueOf.get()` always returns the current instance from the graph. Call it at use time, never cache the result in a property, otherwise a refresh would leave a stale reference behind.

**Create ActivityModule**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection.activity;

    import io.koraframework.application.graph.LifecycleWrapper;
    import io.koraframework.application.graph.Wrapped;
    import io.koraframework.common.annotation.Module;

    @Module
    public interface ActivityModule {

        default Wrapped<ActivityRecorder> activityRecorder() { //(1)!
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

            return new LifecycleWrapper<>(recorder, r -> {}, ActivityRecorder::disconnect); //(2)!
        }
    }
    ```

    1.  Returning `Wrapped<T>` registers the node under `Wrapped<ActivityRecorder>` but lets consumers claim plain `ActivityRecorder`; Kora unwraps it automatically.
    2.  `LifecycleWrapper` takes the value plus an init and a release action. Both are `ThrowingConsumer<T>`, so they may declare checked exceptions.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection.activity

    import io.koraframework.application.graph.LifecycleWrapper
    import io.koraframework.application.graph.Wrapped
    import io.koraframework.common.annotation.Module

    @Module
    interface ActivityModule {

        fun activityRecorder(): Wrapped<ActivityRecorder> { //(1)!
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

                override fun isConnected(): Boolean = connected

                override fun recordUser(user: String) {
                    if (!connected) {
                        connect()
                    }
                    println("Recording user activity: $user")
                }
            }

            return LifecycleWrapper(recorder, {}, ActivityRecorder::disconnect) //(2)!
        }
    }
    ```

    1.  Returning `Wrapped<T>` registers the node under `Wrapped<ActivityRecorder>` but lets consumers claim plain `ActivityRecorder`; Kora unwraps it automatically.
    2.  `LifecycleWrapper` takes the value plus an init and a release action. Both are `ThrowingConsumer<T>`, so they may throw.

**Application note**: No `Application` changes are required here either. `ActivityModule` is also discovered as an application module from the application compilation unit.

**Update NotifyRunner** to demonstrate the final scenario:

===! ":fontawesome-brands-java: `Java`"

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
            for (notifier in allNotifiers) {
                notifier.notify("Diana", "Welcome to Kora DI!")
            }
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

Note the last two lines: `NotifyRunner.release()` runs before the recorder is disconnected, because `release()` walks the graph in reverse dependency order.

**Key Concept**: `ValueOf<T>` prevents cascading component refreshes. The `ActivityService` instance is stable, but it can still access the current `ActivityRecorder` lazily when needed.

---

## Guide Summary { #guide-summary }

You've built a complete Kora application demonstrating all major dependency injection concepts:

1. **Project Structure** - Multi-module organization
2. **External Modules** - Library components with `@DefaultComponent`
3. **Component Override** - Customizing library defaults
4. **Tagged Dependencies** - Multiple implementations with `@Tag` and `All<T>`
5. **Nullable Dependencies** - JSpecify `@Nullable` / nullable types for graceful degradation
6. **Submodules** - `@KoraSubmodule` for component organization across Gradle modules
7. **Generic Factories** - `<T>` parameterized component creation, and `@FactoryModule` for stateful module instances
8. **Preventing Cascading Refreshes** - `ValueOf<T>` to control component refresh behavior

Each step builds upon the previous, showing how Kora's compile-time DI enables clean, modular, and performant applications.

## Best Practices { #best-practices }

- Keep components small and focused on one responsibility.
- Prefer constructor injection and explicit module boundaries.
- Use tags only when multiple implementations really need to coexist.
- Keep optional dependencies explicit with nullable types or JSpecify `@Nullable`.
- Use `ValueOf<T>` when you need controlled component refresh behavior, and call `get()` at use time instead of caching the value.
- Enable the Kora processor in every Gradle module that declares `@KoraApp`, `@KoraSubmodule`, `@ConfigMapper`, or `@ConfigSource` — the processor only sees the module it runs in.
- Put reusable defaults behind `@DefaultComponent` so applications can override them without forking the library.

## Summary { #summary }

Congratulations! You've completed the comprehensive Kora Dependency Injection Guide. You've learned not just *how* to use dependency injection, but *why* it's such a powerful pattern for building
maintainable software.

The guide covered the main building blocks of a Kora graph: `@KoraApp`, `@Component`, `@Module`, external modules, `@DefaultComponent`, tags, `All<T>`, nullable dependencies, submodules, generic
factories, `@FactoryModule`, and `ValueOf<T>`. Together they show how to compose an application from small explicit parts while keeping dependency resolution type-safe and visible at compile time.

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

Kora reports wiring problems while compiling, and every message names the claim, the place that requires it, the dependency tree that led there, and a `Fix:` block. Read that block first: it is
generated from the actual graph state, not from a static template. See also [Container documentation: Graph build errors](../documentation/container.md#graph-build-errors).

Common Issues and Solutions:

Circular Dependencies:

Problem: Two or more components depend on each other directly or indirectly.

Symptoms:

- Compile-time error starting with `Circular dependency found:`, followed by a `Dependency cycle:` listing every declaration in the cycle and ending with `[CYCLE]`
- The suggested fix mentions `ValueOf<T>` or `PromiseOf<T>`

Solutions:

1. Refactor to Interface Segregation:

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

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

- Compile-time error starting with `No component found for dependency:` followed by the claimed type and either `(no tags)` or `with @Tag(...)`
- A `Note:` section listing components of the same type but with a different tag, when the tag was simply forgotten
- A `Fix:` section suggesting `@Component`, a module method, or including a module in `@KoraApp`

Solutions:

1. Add Missing Component:

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

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

- Startup failure with `ConfigValueException: Config expected value, but got null at path: '...' for origin '...'`
- A graph build error for `Config` or `ConfigValueMapper<T>` when no configuration module is connected

Solutions:

1. Add Configuration Module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Include configuration module
    @KoraApp
    public interface Application extends HoconConfigModule {
        // Now Config and ConfigValueMapper<T> are available
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Include configuration module
    @KoraApp
    interface Application : HoconConfigModule {
        // Now Config and ConfigValueMapper<T> are available
    }
    ```

2. Map the Configuration Section into a Typed Class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Application-owned configuration bound to one path
    @ConfigSource("db")
    public interface DatabaseConfig {

        String url();

        @Nullable
        String username();

        default int poolSize() {
            return 10;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Application-owned configuration bound to one path
    @ConfigSource("db")
    interface DatabaseConfig {

        fun url(): String

        fun username(): String?

        fun poolSize(): Int {
            return 10
        }
    }
    ```

`@ConfigSource` generates the mapper and registers the resulting `DatabaseConfig` as a graph component, so any component may just declare it as a constructor parameter. Methods without a default value
and without `@Nullable` are required: a missing key fails at startup with the `ConfigValueException` above. Use `@ConfigMapper` instead when a library type must stay path-agnostic, as `EmailConfig`
does in this guide.

Tag Resolution Issues:

Problem: Tagged dependencies cannot be resolved.

Symptoms:

- Compile error starting with `Multiple components match dependency:` followed by the list of candidate declarations
- Or `No component found for dependency:` with a `Note:` listing the same type under a different tag

Solutions:

1. Use Correct Tag Annotation:

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Tag class must be visible everywhere it is referenced
    public final class MyTag {} // Correct

    // Package-private tag cannot be referenced from another package
    final class MyTag {} // Wrong
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Tag class must be visible everywhere it is referenced
    class MyTag // Correct (public by default)

    // Private tag cannot be referenced from another file
    private class MyTag // Wrong
    ```

3. Or Make One Candidate the Fallback:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface DefaultsModule {

        @DefaultComponent //(1)!
        default Dependency dependency() {
            return new Dependency();
        }
    }
    ```

    1.  The generated error message suggests exactly this: mark the fallback candidate with `@DefaultComponent` and any non-default candidate wins.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface DefaultsModule {

        @DefaultComponent //(1)!
        fun dependency(): Dependency {
            return Dependency()
        }
    }
    ```

    1.  The generated error message suggests exactly this: mark the fallback candidate with `@DefaultComponent` and any non-default candidate wins.

Module Import Issues:

Problem: Components from modules are not available.

Symptoms:

- `No component found for dependency:` for a type you know is declared in some module
- The module lives in another Gradle module and is neither `@KoraSubmodule` nor inherited through `extends`

Solutions:

1. Include Module in Application:

===! ":fontawesome-brands-java: `Java`"

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

2. Check Module Kind and Visibility:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // @Module works on interfaces only, and its factory methods must be public
    @Module
    public interface MyModule {
        default MyComponent myComponent() { // public by default
            return new MyComponent();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // @Module works on interfaces only, and its factory methods must be public
    @Module
    interface MyModule {
        fun myComponent(): MyComponent { // public by default
            return MyComponent()
        }
    }
    ```

`@Module` only affects the compilation unit it is compiled in. A `@Module` interface that lives in a different Gradle module is invisible until you either inherit it with `extends` or place a
`@KoraSubmodule` marker interface in that Gradle module and inherit that instead.

Collection Injection Issues:

Problem: `All<T>` doesn't inject expected components.

Symptoms:

- Fewer components than expected in `All<T>`
- Tagged implementations missing from the collection

Solutions:

1. Ensure All Implementations Are in the Graph:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // All implementations must be @Component or produced by a module factory
    @Component
    public final class Impl1 implements MyInterface {}

    @Component
    public final class Impl2 implements MyInterface {}

    // Now All<MyInterface> will contain both
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // All implementations must be @Component or produced by a module factory
    @Component
    class Impl1 : MyInterface

    @Component
    class Impl2 : MyInterface

    // Now All<MyInterface> will contain both
    ```

2. Match the Tags You Actually Want:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {

        public MyService(All<MyInterface> untagged, //(1)!
                         @Tag(Tag.Any.class) All<MyInterface> everything, //(2)!
                         @Tag(MyTag.class) All<MyInterface> onlyMyTag) { //(3)!
            // ...
        }
    }
    ```

    1.  An untagged claim matches untagged components only. Tagged implementations are silently absent.
    2.  `Tag.Any` matches every component of that type regardless of tag.
    3.  A concrete tag matches only components carrying exactly that tag.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(
        val untagged: All<MyInterface>, //(1)!
        @Tag(Tag.Any::class) val everything: All<MyInterface>, //(2)!
        @Tag(MyTag::class) val onlyMyTag: All<MyInterface> //(3)!
    ) {
        // ...
    }
    ```

    1.  An untagged claim matches untagged components only. Tagged implementations are silently absent.
    2.  `Tag.Any` matches every component of that type regardless of tag.
    3.  A concrete tag matches only components carrying exactly that tag.

This is the single most common surprise with `All<T>`: an empty or short collection almost always means the claim and the providers disagree about tags, not that the components are missing from the
graph. See [Container documentation: Tag any](../documentation/container.md#tag-any).

Optional Dependency Issues:

Problem: Optional dependencies behave unexpectedly.

Symptoms:

- The dependency is `null` when a value was expected
- `NullPointerException` on first use

Solutions:

1. Handle Nullable Correctly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import org.jspecify.annotations.Nullable;

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
            // optionalDep!!.doWork() // Don't do this without a null check
        }
    }
    ```

2. Ensure Nullable Component Exists:

===! ":fontawesome-brands-java: `Java`"

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

JSpecify `@Nullable` is a *type-use* annotation in Java, so its position matters for nested and generic types: write `List<@Nullable String>`, `String @Nullable []`, and `Outer.@Nullable Inner`. Kotlin
carries no annotation at all — the `?` on the type is the declaration.

Lifecycle Issues:

Problem: Components with lifecycle methods don't start or stop.

Symptoms:

- `init()` or `release()` never called
- Resources not cleaned up on shutdown

Solutions:

1. Implement the Lifecycle Interface:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.Lifecycle; //(1)!

    @Component
    public final class MyService implements Lifecycle {

        @Override
        public void init() throws Exception {
            // Initialize resources here
        }

        @Override
        public void release() throws Exception { //(2)!
            // Clean up resources here
        }
    }
    ```

    1.  `Lifecycle` lives in `io.koraframework.application.graph`, not in the annotation package.
    2.  The shutdown callback is `release()`. There is no `destroy()` method in the contract.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.Lifecycle //(1)!

    @Component
    class MyService : Lifecycle {

        override fun init() {
            // Initialize resources here
        }

        override fun release() { //(2)!
            // Clean up resources here
        }
    }
    ```

    1.  `Lifecycle` lives in `io.koraframework.application.graph`, not in the annotation package.
    2.  The shutdown callback is `release()`. There is no `destroy()` method in the contract.

2. Check That the Component Is Actually in the Graph:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // A component nothing depends on is pruned unless it is a root
    @Root
    @Component
    public final class MyService implements Lifecycle {
        // init()/release() now really run
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // A component nothing depends on is pruned unless it is a root
    @Root
    @Component
    class MyService : Lifecycle {
        // init()/release() now really run
    }
    ```

3. Wrap a Third-Party Object You Cannot Modify:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ClientModule {

        default Wrapped<ExternalClient> externalClient() {
            var client = new ExternalClient();
            return new LifecycleWrapper<>(client, ExternalClient::start, ExternalClient::stop);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ClientModule {

        fun externalClient(): Wrapped<ExternalClient> {
            val client = ExternalClient()
            return LifecycleWrapper(client, ExternalClient::start, ExternalClient::stop)
        }
    }
    ```

Generic Type Issues:

Problem: Generic components (`<T>`) don't resolve correctly.

Symptoms:

- `No component found for dependency:` for a concrete parameterization such as `Storage<String>`
- `Component provider returns a raw type:` when a factory returns a raw generic type

Solutions:

1. Use Concrete Type Arguments:

===! ":fontawesome-brands-java: `Java`"

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

2. Make Every Template Parameter Resolvable:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface StorageModule {

        // Every type parameter of the method must appear in a parameter or in the return type
        default <T> Storage<T> storage(Function<T, byte[]> mapper) {
            return new TempFileStorage<>(mapper);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface StorageModule {

        // Every type parameter of the method must appear in a parameter or in the return type
        fun <T> storage(mapper: Function<T, ByteArray>): Storage<T> {
            return TempFileStorage(mapper)
        }
    }
    ```

Raw types are rejected outright with `Raw component types are forbidden because they make dependency resolution ambiguous.`, so always write the type arguments.

Build and Compilation Issues:

Problem: The Kora processor does not run, or the generated graph class is missing.

Symptoms:

- `cannot find symbol: class ApplicationGraph`
- `Kora submodule was not generated yet: expected type: ...SubmoduleImpl`
- Everything compiles, but no component is ever created

Solutions:

1. Check Processor Wiring:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        annotationProcessor "io.koraframework:annotation-processors" //(1)!

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"
    }
    ```

    1.  The processor goes into `annotationProcessor`, never into `implementation`. It must be declared in every Gradle module that contains `@KoraApp`, `@KoraSubmodule`, `@ConfigMapper`, or
        `@ConfigSource`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp") //(1)!
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1"))

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")
    }
    ```

    1.  Without the KSP plugin the `ksp` configuration does not exist and nothing is generated.
    2.  The processor goes into `ksp` with an explicit version, because `ksp` is not covered by the BOM.

2. Clean Build:

```bash
./gradlew clean classes
```

3. Check Java Version:

```bash
java -version
```

Kora modules are compiled for Java 25, so both the Gradle toolchain and the JDK running Gradle must be 25 or newer.

Testing Issues:

Problem: Components are hard to test, or the test graph does not start.

Symptoms:

- Difficulty injecting test doubles
- `@TestComponent` fields left `null`

Solutions:

1. Use Constructor Injection for Plain Unit Tests:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Testable component: no framework needed to construct it
    @Component
    public final class UserService {
        private final UserRepository repository;

        public UserService(UserRepository repository) {
            this.repository = repository;
        }
    }

    @Test
    void testUserService() {
        UserRepository stubRepo = id -> null;
        UserService service = new UserService(stubRepo);
        // Test...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Testable component: no framework needed to construct it
    @Component
    class UserService(
        private val repository: UserRepository
    )

    @Test
    fun testUserService() {
        val stubRepo = UserRepository { null }
        val service = UserService(stubRepo)
        // Test...
    }
    ```

2. Start the Real Graph With `@KoraAppTest`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection;

    import static org.junit.jupiter.api.Assertions.assertNotNull;

    import org.junit.jupiter.api.Test;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class) //(1)!
    class DependencyInjectionGuideSmokeTest {

        @TestComponent //(2)!
        private NotifyRunner notifyRunner;

        @Test
        void graph_ShouldStart() {
            assertNotNull(notifyRunner);
        }
    }
    ```

    1.  Builds the real `Application` graph for the test, so any wiring mistake fails the test instead of production startup.
    2.  Injects a component from that graph into the test instance.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection

    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Test
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent

    @KoraAppTest(Application::class) //(1)!
    class DependencyInjectionGuideSmokeTest {

        @TestComponent //(2)!
        private lateinit var notifyRunner: NotifyRunner

        @Test
        fun graphShouldStart() {
            assertNotNull(notifyRunner)
        }
    }
    ```

    1.  Builds the real `Application` graph for the test, so any wiring mistake fails the test instead of production startup.
    2.  Injects a component from that graph into the test instance.

Both need `io.koraframework:test-junit5` on `testImplementation`. For replacing graph components with mocks, overriding configuration, and Testcontainers-backed integration tests, see
[Testing with JUnit 5](testing-junit.md#test-component).

Common Beginner Mistakes:

1. Forgetting @Component Annotation:

===! ":fontawesome-brands-java: `Java`"

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

2. Ambiguous Constructors:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {
        private MyService() {} // Wrong: no public constructor at all
    }

    @Component
    public final class MyService {
        public MyService() {}
        public MyService(Dependency dep) {} // Wrong: two public constructors
    }

    // Correct: exactly one public constructor
    @Component
    public final class MyService {
        public MyService(Dependency dep) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService private constructor() // Wrong: no public constructor at all

    @Component
    class MyService(dep: Dependency) {
        constructor() : this(Dependency()) // Wrong: two public constructors
    }

    // Correct: exactly one public constructor
    @Component
    class MyService(dep: Dependency)
    ```

Kora reports both cases with `@Component class must have exactly one public constructor.` and suggests keeping one public constructor or moving complex construction into a module method.

3. Not Including Modules:

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

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
    class BImpl implements BInterface { BImpl(AInterface a) {} }
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

===! ":fontawesome-brands-java: `Java`"

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

6. Registering the Same Module Twice:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module //(1)!
    public interface MyModule {
        default MyComponent myComponent() { return new MyComponent(); }
    }

    @KoraApp
    public interface Application extends MyModule { //(2)!
    }
    ```

    1.  Already discovered automatically, because it is compiled together with `@KoraApp`.
    2.  Inheriting it as well registers the same factories twice and leads to `Multiple components match dependency:`. Pick one registration path.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module //(1)!
    interface MyModule {
        fun myComponent(): MyComponent = MyComponent()
    }

    @KoraApp
    interface Application : MyModule { //(2)!
    }
    ```

    1.  Already discovered automatically, because it is compiled together with `@KoraApp`.
    2.  Inheriting it as well registers the same factories twice and leads to `Multiple components match dependency:`. Pick one registration path.

Getting Help:

If you're still stuck:

1. Check the Examples: Look at `kora-examples` for working patterns
2. Read Documentation: Consult the [Container documentation](../documentation/container.md) for the full container contract
3. Simplify: Remove complexity and test with minimal components
4. Community: Ask questions in Kora community channels

Remember: Most DI issues come from missing components, incorrect module imports, mismatched tags, or circular dependencies. Start simple and build up gradually!

## What's Next? { #whats-next }

- [Create Your First Kora Application](getting-started.md) if you completed the DI-only tutorial before building a runnable HTTP app.
- [Configuration with HOCON](config-hocon.md) or [Configuration with YAML](config-yaml.md) after getting started, to learn how typed configuration enters the graph.
- [JSON Processing](json.md) after getting started, to prepare request and response DTOs before the full HTTP Server guide.
- [Testing with JUnit 5](testing-junit.md) to cover the graph you just built with component tests.

## Help { #help }

If you encounter issues:

- check the [Container documentation](../documentation/container.md)
- compare with [Kora Java Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection) and [Kora Kotlin Dependency Injection App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-dependency-injection)
- run `./gradlew clean classes` and read the `Fix:` block of the first Kora error before changing code structure
- verify that components are annotated with `@Component` or provided by a module, and that the Kora processor is enabled in that Gradle module
