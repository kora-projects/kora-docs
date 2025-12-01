---
title: Creating Your First Kora Application
summary: Learn how to create a simple Kora application with HTTP server in minutes
tags: getting-started, http-server, quick-start
---

# Creating Your First Kora Application

This guide shows you how to create a simple Kora application with an HTTP server that responds to `GET /hello` requests.

## What You'll Build

You'll build a simple web service that returns "Hello, Kora!" when you visit `http://localhost:8080/hello`.

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE

## Quick Start with Templates (Recommended)

!!! tip "🚀 Fastest Way: Use GitHub Templates"

    **Choose your approach:**

    - **Use templates if you understand key Kora principles** - For developers who want to jump straight into building features
    - **Create from scratch if you're new to Kora** - Follow the manual setup below to learn core concepts like dependency injection, annotation processing, and module configuration

    For the quickest start with Kora (if you already understand the core principles), use our official GitHub templates that provide everything you need:

    === ":fontawesome-brands-java: Java Template"

        **Option 1: Use GitHub Template (Recommended)**

        ```bash
        # Visit: https://github.com/kora-projects/kora-java-template
        # Click "Use this template" → "Create a new repository"
        # Name your repo (e.g., "kora-guide-example") and clone it
        ```

        **Option 2: Clone and Rename**

        ```bash
        git clone https://github.com/kora-projects/kora-java-template.git kora-guide-example
        cd kora-guide-example
        ```

    === ":simple-kotlin: Kotlin Template"

        **Option 1: Use GitHub Template (Recommended)**

        ```bash
        # Visit: https://github.com/kora-projects/kora-kotlin-template
        # Click "Use this template" → "Create a new repository"
        # Name your repo (e.g., "kora-guide-example") and clone it
        ```

        **Option 2: Clone and Rename**

        ```bash
        git clone https://github.com/kora-projects/kora-kotlin-template.git kora-guide-example
        cd kora-guide-example
        ```

    **The templates include:**
    - ✅ Complete project structure
    - ✅ Gradle build configuration
    - ✅ Docker configuration
    - ✅ Test setup with Testcontainers

    **[Skip to "Creating the Controller"](#creating-the-controller)** if using templates!

## Manual Project Setup

If you prefer to set up the project manually:

Create a new directory for your project and initialize it:

===! ":fontawesome-brands-java: `Java`"

    ```bash
    mkdir kora-guide-example
    cd kora-guide-example
    gradle init \
      --type java-application \
      --dsl groovy \
      --test-framework junit-jupiter \
      --package ru.tinkoff.kora.example \
      --project-name kora-example \
      --java-version 25
    ```

=== ":simple-kotlin: `Kotlin`"

    ```bash
    mkdir kora-guide-example
    cd kora-guide-example
    gradle init \
      --type kotlin-application \
      --dsl kotlin \
      --test-framework junit-jupiter \
      --package ru.tinkoff.kora.example \
      --project-name kora-example \
      --java-version 25
    ```

## Project Setup

Now let's configure your Gradle build files. Kora requires specific Gradle configurations to work properly with its compile-time code generation and dependency injection system.

===! ":fontawesome-brands-java: `Java`"

    Edit your `build.gradle` file with the following configuration:

    ```groovy
    plugins {
        id "java"
        id "application"
    }

    group = "ru.tinkoff.kora.example"
    version = "1.0-SNAPSHOT"

    java {
        sourceCompatibility = JavaVersion.VERSION_25
        targetCompatibility = JavaVersion.VERSION_25
    }

    repositories {
        mavenCentral()
    }

    configurations {
        koraBom
        annotationProcessor.extendsFrom(koraBom); compileOnly.extendsFrom(koraBom); implementation.extendsFrom(koraBom)
        api.extendsFrom(koraBom); testImplementation.extendsFrom(koraBom); testAnnotationProcessor.extendsFrom(koraBom)
    }

    application {
        applicationName = "application"
        mainClass = "ru.tinkoff.kora.example.Application"
        applicationDefaultJvmArgs = ["-Dfile.encoding=UTF-8"]
    }

    distTar {
        archiveFileName = "application.tar"
    }
    ```

    **Understanding the Java configuration:**

    - **`plugins`**: The `java` plugin provides standard Java compilation and packaging. The `application` plugin enables running your application with `./gradlew run` and creates distribution archives.

    - **`java { ... }`**: Sets Java 25 as both source and target compatibility, ensuring your code uses the latest Java features while maintaining runtime compatibility.

    - **`repositories`**: Configures Maven Central as the dependency repository where Kora and other libraries will be downloaded from.

    - **`configurations { ... }`**: Creates a custom `koraBom` configuration and extends standard configurations to inherit from it. This ensures all Kora modules use compatible versions managed by the BOM (Bill of Materials).

    - **`application { ... }`**: Configures the application plugin with a custom name and JVM arguments. The UTF-8 encoding ensures proper character handling across different environments.

    - **`distTar { ... }`**: Customizes the distribution archive name for easier deployment identification.

=== ":simple-kotlin: `Kotlin`"

    Edit your `build.gradle.kts` file with the following configuration:

    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version ("1.9.25")
        id("com.google.devtools.ksp") version ("1.9.25-1.0.20")
    }

    group = "ru.tinkoff.kora.example"
    version = "1.0-SNAPSHOT"

    kotlin {
        jvmToolchain { languageVersion.set(JavaLanguageVersion.of(25)) }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    repositories {
        mavenCentral()
    }

    val koraBom: Configuration by configurations.creating

    configurations {
        ksp.get().extendsFrom(koraBom); compileOnly.get().extendsFrom(koraBom); api.get().extendsFrom(koraBom); 
        implementation.get().extendsFrom(koraBom); testImplementation.get().extendsFrom(koraBom)
    }

    application {
        applicationName = "application"
        mainClass.set("ru.tinkoff.kora.example.ApplicationKt")
        applicationDefaultJvmArgs = listOf("-Dfile.encoding=UTF-8")
    }

    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

    **Understanding the Kotlin configuration:**

    - **`plugins`**: The `application` plugin enables running your application. The `kotlin("jvm")` plugin handles Kotlin compilation. The `com.google.devtools.ksp` plugin enables Kotlin Symbol Processing (KSP) for compile-time code generation, which Kora uses instead of Java annotation processors.

    - **`kotlin { ... }`**: Configures the JVM toolchain to use Java 25 and sets up source directories for KSP-generated code. The `kotlin.srcDir` directives tell Kotlin where to find code generated by Kora's symbol processors.

    - **`repositories`**: Same as Java - configures Maven Central for dependency resolution.

    - **`val koraBom: Configuration`**: Creates a custom configuration for the Kora BOM, similar to the Java version but using Kotlin syntax.

    - **`configurations { ... }`**: Extends standard configurations to inherit from the Kora BOM, ensuring version compatibility. Note that `ksp` is used instead of `annotationProcessor` for Kotlin Symbol Processing.

    - **`application { ... }`**: Same configuration as Java but using Kotlin list syntax for JVM arguments.

    - **`tasks.distTar { ... }`**: Customizes the distribution archive name, same as Java configuration.

## Adding Kora Dependencies

Kora uses a modular architecture where you only include the dependencies you need. For this guide, we need several key components that provide essential functionality:

===! ":fontawesome-brands-java: `Java`"

    Add the Kora dependencies to your `build.gradle` file:

    ```groovy
    dependencies {
        koraBom platform("ru.tinkoff.kora:kora-parent:1.2.2")
        annotationProcessor "ru.tinkoff.kora:annotation-processors"

        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ch.qos.logback:logback-classic:1.4.8")
    }
    ```

    **Why these dependencies?**

    - **`koraBom platform("ru.tinkoff.kora:kora-parent:1.2.2")`** - This is Kora's Bill of Materials (BOM) that manages versions for all Kora dependencies. Using a BOM ensures all Kora modules use compatible versions and simplifies dependency management by specifying the version once.

    - **`annotationProcessor "ru.tinkoff.kora:annotation-processors"`** - Kora's core innovation is compile-time code generation using annotation processors. These processors analyze your code at compile time and generate the necessary implementation classes, dependency injection wiring, and other boilerplate code. This approach provides excellent performance since no reflection or dynamic proxies are used at runtime.

    - **`implementation("ru.tinkoff.kora:http-server-undertow")`** - This module provides HTTP server functionality built on top of the Undertow web server. It includes annotations for creating REST endpoints (`@HttpController`, `@HttpRoute`) and handles HTTP request/response processing. Undertow is chosen for its high performance and low resource usage.

    - **`implementation("ru.tinkoff.kora:config-hocon")`** - Enables configuration management using HOCON (Human-Optimized Config Object Notation) format. This provides type-safe configuration loading from files, environment variables, and system properties. HOCON supports includes, substitutions, and a human-readable syntax.

    - **`implementation("ch.qos.logback:logback-classic:1.4.8")`** - A high-performance logging framework that implements the SLF4J API. Logback provides flexible configuration options, multiple appenders (console, file, database), and structured logging capabilities essential for production applications.

=== ":simple-kotlin: `Kotlin`"

    Add the Kora dependencies to your `build.gradle.kts` file:

    ```kotlin
    dependencies {
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.2.2"))
        ksp("ru.tinkoff.kora:symbol-processor")

        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ch.qos.logback:logback-classic:1.4.8")
    }
    ```

    **Why these dependencies?**

    - **`koraBom(platform("ru.tinkoff.kora:kora-parent:1.2.2"))`** - This is Kora's Bill of Materials (BOM) that manages versions for all Kora dependencies. Using a BOM ensures all Kora modules use compatible versions and simplifies dependency management by specifying the version once.

    - **`ksp("ru.tinkoff.kora:symbol-processor")`** - For Kotlin, Kora uses Kotlin Symbol Processing (KSP) instead of traditional Java annotation processors. KSP provides similar compile-time code generation capabilities but is optimized for Kotlin's type system and syntax. These processors generate the necessary implementation classes and dependency injection wiring at compile time.

    - **`implementation("ru.tinkoff.kora:http-server-undertow")`** - This module provides HTTP server functionality built on top of the Undertow web server. It includes annotations for creating REST endpoints (`@HttpController`, `@HttpRoute`) and handles HTTP request/response processing. Undertow is chosen for its high performance and low resource usage.

    - **`implementation("ru.tinkoff.kora:config-hocon")`** - Enables configuration management using HOCON (Human-Optimized Config Object Notation) format. This provides type-safe configuration loading from files, environment variables, and system properties. HOCON supports includes, substitutions, and a human-readable syntax.

    - **`implementation("ch.qos.logback:logback-classic:1.4.8")`** - A high-performance logging framework that implements the SLF4J API. Logback provides flexible configuration options, multiple appenders (console, file, database), and structured logging capabilities essential for production applications.

## Creating the Application

Create the main application class:

=== ":fontawesome-brands-java: Java"

    Create `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends UndertowHttpServerModule, LogbackModule {
    }
    ```

=== ":simple-kotlin: Kotlin"

    Create `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application : UndertowHttpServerModule, LogbackModule
    ```

**What does this Application interface do?**

The `@KoraApp` annotation marks this interface as the entry point for your Kora application. During compilation, Kora's annotation processors will generate an `ApplicationGraph` class that describes how to build and wire all the components of your application.

The `UndertowHttpServerModule` provides:
- An HTTP server running on port 8080 for your public API endpoints
- A system API server on port 8085 with health check endpoints (`/system/liveness` and `/system/readiness`)
- Automatic handling of HTTP requests and responses

The `LogbackModule` provides:
- Structured logging configuration using Logback
- SLF4J logger instances for your components
- Configurable log levels and appenders

## Creating the Controller

Create a controller to handle HTTP requests:

=== ":fontawesome-brands-java: Java"

    Create `src/main/java/ru/tinkoff/kora/example/HelloController.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.http.server.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.HttpMethod;

    @Component
    @HttpController
    public final class HelloController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        public String hello() {
            return "Hello, Kora!";
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    Create `src/main/kotlin/ru/tinkoff/kora/example/HelloController.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.http.server.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.HttpMethod

    @Component
    @HttpController
    class HelloController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        fun hello(): String {
            return "Hello, Kora!"
        }
    }
    ```

**Understanding the Controller annotations:**

- **`@Component`** - Registers this class with Kora's dependency injection container, making it available for injection into other components.

- **`@HttpController`** - Marks this class as a web controller that handles HTTP requests.

- **`@HttpRoute`** - Defines the HTTP endpoint. The `method` parameter specifies the HTTP method (GET, POST, etc.) and `path` defines the URL path. When you return a String, Kora automatically converts it to an HTTP response with the appropriate content type.

## Running the Application

Before running, Gradle will compile your code and Kora's annotation processors will generate the necessary wiring code (including the `ApplicationGraph` class) to connect all your components together.

```bash
./gradlew run
```

## Testing the Application

Open your browser and visit `http://localhost:8080/hello`

You should see: `Hello, Kora!`

You can also test it with curl:

```bash
curl http://localhost:8080/hello
# Expected output: Hello, Kora!
```

## What's Next?

- [Add JSON Support](../json.md)
- [Add Database Integration](../database-jdbc.md)
- [Add Validation](../validation.md)
- [Add Caching](../cache.md)
- [Add Observability & Monitoring](../observability.md)
- [Explore More Examples](../examples/kora-examples.md)

## Help

If you encounter issues:

- Check the [HTTP Server Documentation](../documentation/http-server.md)
- Check the [Hello World Example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-helloworld)
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)