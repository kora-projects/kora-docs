---
search:
  exclude: true
title: Creating Your First Kora Application
summary: Learn how to create a minimal Kora HTTP application and run your first endpoint
tags: getting-started, http-server, quick-start
---

# Building Your First Kora Application { #building-your-first-kora }

This guide introduces the smallest useful Kora HTTP application. It covers how a `@KoraApp` module starts the compile-time dependency graph, how `@Component` and `@HttpController` register application
code, and how one `@HttpRoute` becomes a runnable endpoint. You will also see the Gradle, module, and configuration pieces required to compile and run the app.

Treat this guide as a guided tour through the minimum shape of a Kora service. Every later guide adds more capabilities, but the same ideas keep repeating: declare dependencies explicitly, let Kora
generate the graph during compilation, keep framework infrastructure in modules, and keep application behavior in your own components.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Getting Started App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-getting-started-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Getting Started App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-getting-started-app).

## What You'll Build { #youll-build }

You will build a small web service that returns `Hello, Kora!` on `http://localhost:8080/hello`.

That sounds tiny, but the application already contains the same architectural pieces as a larger service:

- a Gradle build that enables Kora annotation processing
- a `@KoraApp` root that defines the application graph
- framework modules for configuration, logging, JSON, and the HTTP server
- one controller component that exposes an HTTP route
- an `application.conf` file that configures ports and logging
- generated source code that shows how Kora wires everything together

The endpoint itself is deliberately simple so you can focus on the framework mechanics instead of business logic.

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Basic comfort with reading Java or Kotlin code

You do not need Docker, a database, or any external service for this guide. Everything runs in one process on your machine, which makes it a good place to understand the Kora development loop before
adding real infrastructure.

## Prerequisites { #prerequisites }

!!! note "No Previous Kora Guide Required"

    This guide is the starting point for the rest of the learning path and does not assume any existing Kora project.

    It is recommended to read **[Dependency Injection with Kora](dependency-injection-introduction.md)** either before this guide or immediately after it, because dependency injection, the application graph, components, and modules are core concepts behind every Kora application.

    Also you need basic Java or Kotlin familiarit.

## Overview { #overview }

This guide is the smallest useful entry point into a Kora application. The goal is not just to return `Hello, Kora!`; it is to show the basic shape that every larger Kora service keeps using.

The guide deliberately starts with one endpoint because a minimal application makes Kora's core model visible: the framework module provides infrastructure, your component provides behavior, and the
generated graph connects them.

A useful mental model is: Kora does not hide the application structure from you. You write normal classes and interfaces, annotate the boundaries that should become part of the graph, and Kora turns
those declarations into generated code. The result is close to manual dependency wiring, but without hand-written boilerplate and with compile-time validation.

### Application Graph { #application-graph }

Kora applications start from a dependency graph. The `@KoraApp` interface is the root of that graph: it tells Kora which modules are part of the application and which components should be wired
together. During compilation, Kora generates graph code that knows how to create, connect, start, and stop components. Each node in that graph is a component, and each edge is a dependency from one
component to another. If a controller needs a service, or a repository needs a database connection, that relationship becomes an edge in the graph.

This is different from runtime dependency injection frameworks that scan the classpath when the application starts. Kora does the heavy work during compilation, so many wiring mistakes are reported
before the application can run. That is why a normal `classes` task is already a meaningful validation step in Kora: it checks not only Java/Kotlin syntax, but also whether the application graph can
be built.

### Components and Modules { #components-modules }

A `@Component` is an object Kora can create and manage. A module contributes component factories or framework capabilities. In this first guide, the important framework capability is the Undertow HTTP
server module. It provides the server runtime, while your controller provides application behavior.

There are two kinds of modules you will see in Kora projects. Framework modules, such as `UndertowHttpServerModule`, provide ready-made infrastructure. Application modules are your own interfaces or
classes that provide factories for your domain components. This guide uses framework modules only, then later guides show how to split your own application into services, repositories, clients,
caches, and other components.

That separation appears throughout the guides:

- framework modules provide infrastructure
- your components provide application behavior
- the generated graph connects both sides

### HTTP as the Entry Point { #http-entry-point }

The `HelloController` is intentionally small, but it introduces the same HTTP server model used by larger APIs. `@HttpController` marks a class as containing routes, and `@HttpRoute` maps one method
to one HTTP method and path. The method body stays ordinary Java or Kotlin code. Kora does not force controller methods into a special base class or runtime proxy model. The annotations describe how
the method should be exposed over HTTP; the method implementation remains regular application code.

By the end of this guide, you should understand the minimum moving parts of a Kora service: [Gradle](https://docs.gradle.org/current/userguide/userguide.html) dependencies, an application graph, a
framework module, one component, and one route exposed through the [Undertow](https://undertow.io/undertow-docs/undertow-docs-2.3.0/index.html) HTTP server.

The practical flow is:

1. create the Gradle project
2. add Kora HTTP server dependencies
3. define the `@KoraApp` graph root
4. add one `@HttpController`
5. run the application and call the endpoint

## Service Template { #service-template }

If you want the fastest start, use official templates:

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

If you prefer learning setup details, continue with manual setup below. Manual setup is useful for a first read because it shows exactly which Gradle plugins, dependencies, generated sources, modules,
and configuration entries participate in a Kora application.

## Install the JDK { #install-jdk }

Gradle needs a JDK first: the JVM runs Gradle Wrapper, the Java compiler, and the build tooling. For the first run, install Eclipse Temurin JDK 21: it is enough to start Gradle, and Gradle toolchain
can then download the JDK required by the actual build.

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

The output should show Java 21. After that, create the project directory.

## Project Directory { #project-directory }

First, create an empty directory for the future application and move into it. All commands below are executed from this directory:

```bash
mkdir kora-guide-example
cd kora-guide-example
```

## Gradle Setup { #gradle-setup }

This step creates a plain Gradle application project before Kora enters the picture. That is intentional: Kora is added through normal dependencies and annotation processors, so the project still
looks like a standard Java or Kotlin Gradle project.

The package name matters because generated sources are placed next to your application package. Keeping the package stable also makes later generated-code inspection easier.

Use Gradle Wrapper bootstrap for every setup. This keeps the path identical for every reader: first create the minimal wrapper files in the current directory, then run `init` through
`GradleWrapperMain`. This path requires only the JDK from the previous section.

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

Step 3. Initialize the project through the wrapper.

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

## Dependencies { #dependencies }

Now add the minimal Gradle setup that turns a plain Gradle project into a Kora application. Instead of pasting one large `build.gradle` or `build.gradle.kts` block, this section builds the file in small pieces and explains what each piece means.

Gradle has to do several things here:

- choose the JDK used to compile the application
- enable normal application build and `gradlew run`
- import the Kora BOM so all Kora modules use aligned versions
- enable Kora code generation during compilation
- add the HTTP server, configuration, JSON, and logging modules

### Toolchain Resolver { #toolchain }

First, update `settings.gradle`. The `foojay-resolver-convention` plugin helps Gradle find or download the JDK requested by the toolchain. Without it, Gradle can only use JDKs already installed on the local machine, which makes the build more environment-dependent.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    plugins {
        id "org.gradle.toolchains.foojay-resolver-convention" version "1.0.0"
    }

    rootProject.name = "kora-example"
    ```

    Then add `gradle.properties`:

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

    Add `gradle.properties`. The last property is for Kotlin 1.9.25: if the Kotlin compiler cannot target JDK 24 exactly, it reports the fallback as a warning instead of failing this learning build:

    ```properties
    org.gradle.java.installations.auto-detect=true
    org.gradle.java.installations.auto-download=true
    kotlin.jvm.target.validation.mode=warning
    ```

### Imports and Plugins { #imports-plugins }

Now start building the Gradle file. The imports keep the toolchain block readable, and the plugins enable application build, application execution, and code generation.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    import org.gradle.jvm.toolchain.JavaLanguageVersion
    import org.gradle.jvm.toolchain.JvmVendorSpec

    plugins {
        id "java"
        id "application"
    }
    ```

    The `java` plugin adds `compileJava`, `classes`, `test`, and the standard dependency configurations. The `application` plugin adds `run` and distribution packaging for an executable application.

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

    `application` adds `run`, `kotlin("jvm")` compiles Kotlin code for the JVM, and `com.google.devtools.ksp` runs the Kora symbol processor. For Kotlin, Kora uses KSP instead of Java `annotationProcessor`.

### Project Coordinates { #coordinates }

`group` and `version` are the Gradle project coordinates. Even if the application is not published to a Maven repository yet, these values help Gradle, IDEs, and future modules identify the artifact.

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

### Java Toolchain { #java-toolchain }

The toolchain tells Gradle which JDK should compile the code. This is different from `JAVA_HOME`: Gradle may run on one JDK and compile the application with another. This guide uses JDK 24 from Adoptium so the build is reproducible.

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

    The `build/generated/ksp/main/kotlin` and `build/generated/ksp/test/kotlin` directories matter for IDEs and compilation because KSP writes Kora-generated code there.

### Repositories { #repositories }

`mavenCentral()` tells Gradle where to download Kora, Undertow, Logback, and their transitive dependencies.

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

### Kora BOM Configuration { #bom }

Kora is split into multiple modules. Instead of writing a version on every dependency, import a BOM (`Bill of Materials`). The custom `koraBom` configuration holds the platform with versions and then makes those versions available to normal Gradle configurations.

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

    `annotationProcessor` receives the BOM separately because annotation processors have their own classpath. `implementation` receives the BOM for application dependencies.

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

    `ksp` receives the BOM separately because the Kora processor runs on a separate classpath, while `implementation` receives it for application dependencies.

### Dependencies { #gradle-dependencies }

Now add dependencies. First import the Kora BOM. After this line, Kora dependencies can be declared without versions because Gradle takes the versions from `kora-parent`. Then add the annotation processor or KSP processor and the runtime framework modules.

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

These dependencies provide the Undertow HTTP server, HOCON configuration, JSON infrastructure, Logback logging, and Kora graph generation during compilation.

### Application Entry Point { #entry-point }

The last block is for the `application` plugin. It sets the application name, the class with `main`, and default JVM arguments.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    application {
        applicationName = "application"
        mainClass = "ru.tinkoff.kora.guide.gettingstarted.Application"
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"]
    }
    ```

    Here `mainClass` points to your source `Application` type, not the generated `ApplicationGraph`: the `main` method inside `Application` will call `KoraApplication.run(ApplicationGraph::graph)`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    application {
        applicationName.set("application")
        mainClass.set("ru.tinkoff.kora.guide.gettingstarted.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }
    ```

    In Kotlin, a top-level `main` function from `Application.kt` is compiled into a class with the `Kt` suffix, so the main class is `ApplicationKt`.

`ApplicationGraph` is not written by hand and does not exist before the processor runs. The Java annotation processor or KSP generates it during compilation, and `./gradlew classes` validates not only source code, but also Kora graph generation.

The `-Dfile.encoding=UTF-8` argument fixes runtime encoding across operating systems. This is useful for logs, text HTTP responses, and string resources.

## Modules { #modules }

The `Application` type is the root of the Kora application. It is intentionally an interface: you are not writing startup logic by hand; you are declaring which modules form the application, and Kora
generates the implementation.

Extending modules such as `HoconConfigModule` and `UndertowHttpServerModule` means: include the components and factories from those modules in this application graph. If a required module is missing,
Kora usually reports the missing dependency during compilation.

The `main` method calls `KoraApplication.run(ApplicationGraph::graph)`. `ApplicationGraph` is generated from `Application`, so it does not exist until annotation processing or KSP has run.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/gettingstarted/Application.java`:

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
            UndertowHttpServerModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

    ??? abstract "Java: generated `ApplicationGraph` fragment"

        After `./gradlew clean classes`, the annotation processor creates `build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/gettingstarted/ApplicationGraph.java`.
        The full file contains every component from the included modules, so the fragment below focuses on the part that connects your controller, the HTTP route, and the Undertow server:

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

        `ApplicationGraphDraw` is the dependency graph description, and `ComponentHolder0` stores graph nodes. The `graph()` method is the entry point passed to `KoraApplication.run(ApplicationGraph::graph)`.

        Inside `ComponentHolder0`, Kora adds nodes like these:

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

        What this does:

        - `new HelloController()` creates your `@Component`.
        - `impl.module0.get_hello(...)` calls the generated HTTP route factory for `GET /hello`.
        - `publicApiHandler(...)` collects public HTTP routes into one handler.
        - `undertowHttpServer(...)` creates the Undertow server component and receives its configuration from the graph.

        At runtime, Kora does not scan the classpath to discover these links. The graph has already been computed during compilation and written into generated Java code.

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/Application.kt`:

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
        UndertowHttpServerModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

    ??? abstract "Kotlin: generated `ApplicationGraph` fragment"

        For Kotlin, Kora uses KSP and creates `build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/ApplicationGraph.kt`.
        This is Kotlin code generated from the Kotlin application:

        ```kotlin
        @Generated("ru.tinkoff.kora.kora.app.ksp.KoraAppProcessor")
        public class ApplicationGraph : Supplier<ApplicationGraphDraw> {
            override fun `get`(): ApplicationGraphDraw = graphDraw

            public fun graph(): ApplicationGraphDraw {
                return graphDraw
            }
        }
        ```

        Inside the generated component holder, KSP adds graph nodes:

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

        The meaning is the same as in the Java version: KSP describes in advance how to create `HelloController`, turn its method into an HTTP route, add the route to the public handler, and pass that handler to the Undertow server.

## Controller { #controller }

The controller is the first component that belongs to your application code rather than to a framework module. `@Component` makes it available to the graph. `@HttpController` tells the HTTP annotation
processor to inspect it for routes. `@HttpRoute` maps the method to `GET /hello`.

This guide returns `HttpServerResponse` directly because it is the most explicit first example: you can see the status code and body type in one line. Later guides introduce JSON DTOs, request bodies,
validation, error handling, and service layers.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/gettingstarted/HelloController.java`:

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

    ??? abstract "Java: generated route module `HelloControllerModule`"

        After compilation, the HTTP processor creates `build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/gettingstarted/HelloControllerModule.java`:

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

        This file shows what `@HttpController` does:

        - `@Module` adds the generated factory to the Kora graph.
        - `get_hello(...)` creates an `HttpServerRequestHandler` for `GET /hello`.
        - `HelloController _controller` is resolved from the graph as a regular component.
        - `BlockingRequestExecutor _executor` runs the synchronous controller method on the proper executor so the HTTP server event loop is not blocked.
        - `HttpServerRequestHandlerImpl.of(...)` connects the HTTP method, path, and `_controller.hello()` call.

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/HelloController.kt`:

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

    ??? abstract "Kotlin: generated route module `HelloControllerModule`"

        In the Kotlin application, KSP creates `build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/HelloControllerModule.kt`:

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

        This exposes the Kotlin-specific KSP output:

        - The factory is also marked with `@Module`, so it becomes part of the application graph.
        - `get_hello(...)` returns an `HttpServerRequestHandler` for `GET /hello`.
        - The `_controller.hello()` call is executed through `BlockingRequestExecutor`.
        - Exceptions are converted into failed futures: if the exception is already an `HttpServerResponse`, it is passed through as an HTTP response; otherwise Kora wraps it into `HttpServerResponseException` with status `400`.

## Configuration { #config }

Configuration is where the application receives runtime values without changing source code. Even this first app has two HTTP ports: a public port for business endpoints and a private port for
operational endpoints such as readiness checks.

Create `src/main/resources/application.conf`:

For the full configuration reference, see [HTTP Server](../documentation/http-server.md) and [Logging SLF4J](../documentation/logging-slf4j.md).

The guide shows both HOCON and YAML shapes. The Java and Kotlin sample applications use HOCON here, but the same configuration structure can be represented in YAML when the YAML config module is used.

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

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Log level for `ROOT`.
    5. Log level for `ru.tinkoff.kora`.

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

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Log level for `ROOT`.
    5. Log level for `ru.tinkoff.kora`.

## Run Application { #run-app }

Run the build before starting the app. In Kora, `classes` is especially useful because it triggers annotation processing and validates that the dependency graph can be generated. Running tests after
that gives a fast sanity check before the HTTP server starts.

```bash
./gradlew run
```

## Check Application { #check-app }

Once the app is running, call the public endpoint through the public HTTP port. A successful response proves that the server module started, the controller component was created, and the generated
route handler was registered.

```bash
curl http://localhost:8080/hello
# Expected output: Hello, Kora!
```

## Generated Code { #generated-code }

Kora is a compile-time framework. After `./gradlew classes`, the generated sources show how annotations become regular Java or Kotlin code. This is one of the best learning tools in the
framework: when something feels magical, open the generated code and you can usually see the exact factory, graph node, or handler that Kora produced.

Start with the generated controller module:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-getting-started-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/gettingstarted/HelloControllerModule.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-getting-started-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/HelloControllerModule.kt
    ```

It contains the `HttpServerRequestHandler` that Kora generated for `@HttpController` and `@HttpRoute`. This generated handler is the bridge between Undertow's incoming HTTP request and your ordinary
controller method:

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

Then inspect the generated application graph:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-getting-started-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/gettingstarted/ApplicationGraph.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-getting-started-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/gettingstarted/ApplicationGraph.kt
    ```

You will see Kora register the controller and then register the generated HTTP handler that depends on it. That dependency is important: the handler cannot exist without the controller instance, and
the graph records that relationship explicitly:

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

This is the first practical look at Kora's core idea:

- your source code declares components and routes
- annotation processors generate the graph and route handlers
- runtime startup uses the generated graph instead of discovering components through reflection

Generated sources are also useful for AI assistants. They expose the exact compiled wiring, so an assistant can inspect how the framework connected components instead of guessing from annotations
alone.

## Best Practices { #best-practices }

These practices are intentionally small, but they scale into the later guides. A Kora application is easiest to maintain when the graph root is explicit, controllers stay focused on protocol concerns,
and generated code remains something you are willing to inspect during debugging.

- Keep application graph in one `@KoraApp` entry point. This makes it clear which infrastructure modules are connected and where application assembly starts.
- Connect framework modules explicitly through `extends`. The root interface should tell the reader that the service uses HTTP, HOCON, JSON, and Logback.
- Keep controller logic minimal and move business logic to services when complexity grows. In this first guide the controller returns a string directly, but in real APIs controllers usually receive
  HTTP input, call services, and shape HTTP responses.
- Run `./gradlew classes` after adding new components. Compile-time DI is most useful when dependency mistakes are caught during build, not during the first runtime request.
- Inspect generated sources when you want to understand what Kora compiled from your annotations. This helps both humans and AI assistants trace the real component wiring.

## Summary { #summary }

This first application is small, but it already exercised the full Kora development cycle: declare modules, add a component, compile generated code, run the graph, and call an endpoint.

You created a working Kora HTTP application and walked through the development loop that later guides keep using:

- declared the root `@KoraApp` as the dependency graph entry point
- connected framework modules for configuration, logging, JSON, and the HTTP server
- added your first application component through `@Component`
- exposed one controller endpoint (`GET /hello`)
- configured basic ports and logging
- inspected the generated HTTP route handler and generated application graph fragment

## Key Concepts { #key-concepts }

- `@KoraApp` defines the application graph root.
- Kora generates wiring at compile time.
- `@HttpController` + `@HttpRoute` expose HTTP endpoints.
- Generated sources reveal the application graph and route handler code.

## Troubleshooting { #troubleshooting }

**Build fails with generated graph errors**

Generated graph errors usually mean Kora could not build the dependency graph. That may happen when annotation processing is disabled, a framework module is missing, or a component constructor asks
for a dependency that no module provides.

- Ensure annotation processing is configured (`annotationProcessor` for Java, `ksp` for Kotlin).
- Ensure the root interface is annotated with `@KoraApp` and extends the required Kora modules.
- Ensure classes annotated with `@Component` are in the application source set and use the expected package.
- If the error reports a missing dependency, read it as a normal dependency graph: Kora tells you which type it tried to create and which component was not available.

**Application does not start on port 8080**

- Check `application.conf` and port availability.
- Verify no other process uses `8080`.

**Private API smoke-check (`8085`)**

- Verify private API endpoint is reachable:
  ```bash
  curl http://localhost:8085/system/readiness
  ```
- If unavailable, check `privateApiHttpPort = 8085` and `privateApiHttpReadinessPath = "/system/readiness"` in `application.conf` and app startup logs.

**Gradle hangs or behaves unexpectedly**

- Run `./gradlew --stop`, then retry.

## What's Next? { #whats-next }

This guide intentionally stops at a tiny endpoint: now you have a minimal working skeleton where you can add one new concept at a time. The best next step is to understand dependency injection more
deeply, then move into configuration, JSON, and a fuller HTTP API.

- [Learn Dependency Injection Basics](dependency-injection-introduction.md) to understand the application graph, components, modules, and compile-time wiring behind this first endpoint.
- [Configuration with HOCON](config-hocon.md) or [Configuration with YAML](config-yaml.md) to learn how Kora reads typed application settings.
- [JSON Processing](json.md) to add explicit request and response DTO mapping before the full HTTP Server guide.
- [Build an HTTP Server](http-server.md) after JSON, when you are ready to turn the small endpoint into a fuller HTTP API.

## Help { #help }

When debugging your first application, split problems into three groups: build errors, startup errors, and request errors. Build errors usually point to annotation processing or missing graph
components. Startup errors are usually configuration or port conflicts. Request errors belong in the controller, generated handler, or HTTP server logs.

If you encounter issues:

- compare with [Kora Java Getting Started App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-getting-started-app) and [Kora Kotlin Getting Started App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-getting-started-app)
- check the [HTTP Server documentation](../documentation/http-server.md)
- check the [Container documentation](../documentation/container.md)
- check the [Hello World example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-helloworld)
