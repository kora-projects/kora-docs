---
title: Building Kora DI Applications
summary: A comprehensive step-by-step tutorial for building complete applications with Kora's dependency injection framework
tags: dependency-injection, tutorial, components, modules, java, kotlin
---

## Building Kora DI Applications

This comprehensive, hands-on tutorial takes you from dependency injection theory to building production-ready applications with Kora's compile-time DI framework. Unlike the introductory guide that explains DI concepts, this tutorial focuses on **practical implementation** through building a complete, working application.

This tutorial assumes you've read the [Dependency Injection with Kora](../dependency-injection-intro.md) guide for basic concepts. If you haven't, we recommend starting there first, then returning here for the practical implementation.

## What You'll Build

You'll build a complete notification system application that demonstrates all major Kora dependency injection features:

- **Multi-module project structure** with proper separation of concerns
- **Component-based architecture** with external library modules
- **Tagged dependencies** for multiple implementations of the same interface
- **Collection injection** to inject all implementations at once
- **Submodules** for organizing related components
- **Generic factories** for type-safe component creation
- **Optional dependencies** for graceful handling of missing components
- **ValueOf<T>** pattern to prevent cascading component refreshes

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Basic understanding of Java or Kotlin
- Familiarity with dependency injection concepts (see [Dependency Injection with Kora](../dependency-injection-intro.md))

## Prerequisites

!!! note "Recommended: Read the DI Introduction First"

    This tutorial assumes you have read the **[Dependency Injection with Kora](../dependency-injection-intro.md)** guide to understand the basic concepts.

    While not strictly required, the introduction guide will help you better understand the patterns used in this tutorial.

This tutorial builds a complete Kora application from scratch, introducing dependency injection concepts progressively. Each step adds new functionality while demonstrating a specific DI pattern. By the end, you'll have a fully functional application showcasing all major Kora DI features.

### Tutorial Overview

We'll build a notification system that can send messages via email, SMS, and various messengers. The application will demonstrate:

1. **Project Setup** - Basic multi-module structure
2. **External Modules** - Library components with defaults
3. **Component Override** - Customizing library behavior
4. **Tagged Dependencies** - Multiple implementations of the same interface
5. **Collection Injection** - Injecting all implementations at once
6. **Submodules** - Organizing related components
7. **Generic Factories** - Type-safe component creation
8. **Optional Dependencies** - Handling missing dependencies gracefully
9. **Preventing Cascading Refreshes** - Using ValueOf<T> to avoid unwanted component refreshes

## Manual Project Setup

Create the complete multi-module project structure:

```bash
mkdir kora-di-tutorial
cd kora-di-tutorial

# Create initial subproject directories
mkdir common lib app
```

### Project Setup

Setup the multi-module Gradle configuration:

===! ":fontawesome-brands-java: `Java`"

    Create the following directory structure:
    ```
    kora-di-tutorial/
    ├── common/
    ├── lib/
    ├── app/
    ├── settings.gradle
    └── build.gradle
    ```

    Edit your root `settings.gradle` file:

    ```groovy
    rootProject.name = 'kora-di-tutorial'

    include 'common'
    include 'lib'
    include 'app'
    ```

    Edit your root `build.gradle` file:

    ```groovy
    plugins {
        id 'application'
    }

    group = 'com.example.di'
    version = '1.0-SNAPSHOT'

    application {
        mainClass = 'com.example.di.app.Application'
    }

    subprojects {
        apply plugin: 'java'

        java {
            toolchain {
                languageVersion = JavaLanguageVersion.of(17)
            }
        }

        repositories {
            mavenCentral()
        }

        configurations {
            koraBom
            annotationProcessor.extendsFrom(koraBom)
            compileOnly.extendsFrom(koraBom)
            implementation.extendsFrom(koraBom)
            api.extendsFrom(koraBom)
            testImplementation.extendsFrom(koraBom)
            testAnnotationProcessor.extendsFrom(koraBom)
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create the following directory structure:
    ```
    kora-di-tutorial/
    ├── common/
    ├── lib/
    ├── app/
    ├── settings.gradle.kts
    └── build.gradle.kts
    ```

    Edit your root `settings.gradle.kts` file:

    ```kotlin
    rootProject.name = "kora-di-tutorial"

    include("common")
    include("lib")
    include("app")
    ```

    Edit your root `build.gradle.kts` file:

    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version ("1.9.25")
        id("com.google.devtools.ksp") version ("1.9.25-1.0.20")
    }

    group = "com.example.di"
    version = "1.0-SNAPSHOT"

    application {
        mainClass.set("com.example.di.app.Application")
    }

    subprojects {
        apply(plugin = "org.jetbrains.kotlin.jvm")

        kotlin {
            jvmToolchain { languageVersion.set(JavaLanguageVersion.of(17)) }
            sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
            sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
        }

        repositories {
            mavenCentral()
        }

        val koraBom: Configuration by configurations.creating

        configurations {
            "ksp".get().extendsFrom(koraBom)
            compileOnly.get().extendsFrom(koraBom)
            implementation.get().extendsFrom(koraBom)
            api.get().extendsFrom(koraBom)
            testImplementation.get().extendsFrom(koraBom)
            "kspTest".get().extendsFrom(koraBom)
        }
    }
    ```

    Create the module-specific `build.gradle` files:

    ===! ":fontawesome-brands-java: `Java`"

        Create `lib/build.gradle`:

        ```groovy
        plugins {
            id 'java-library'
        }
        ```

    === ":simple-kotlin: `Kotlin`"

        Create `lib/build.gradle.kts`:

        ```kotlin
        plugins {
            kotlin("jvm") version ("1.9.25")
        }
        ```

## Adding Kora Dependencies

For this comprehensive DI tutorial, we need several Kora modules that provide the full range of dependency injection capabilities. Add the dependencies to your root `build.gradle` file:

===! ":fontawesome-brands-java: `Java`"

    Add the Kora dependencies to your root `build.gradle` file (after the subprojects block):

    ```groovy
    // Dependencies
    dependencies {
        koraBom platform("ru.tinkoff.kora:kora-parent:1.2.2")
        annotationProcessor "ru.tinkoff.kora:annotation-processors"

        // Core DI functionality
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ch.qos.logback:logback-classic:1.4.8")

        // Testing dependencies for all subprojects
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

    **Why these dependencies?**

    - **`koraBom platform("ru.tinkoff.kora:kora-parent:1.2.2")`** - Kora's Bill of Materials (BOM) that manages versions for all Kora dependencies, ensuring compatibility across modules.

    - **`annotationProcessor "ru.tinkoff.kora:annotation-processors"`** - Kora's compile-time code generation processors that create dependency injection wiring and component implementations.

    - **`implementation("ru.tinkoff.kora:config-hocon")`** - Configuration management using HOCON format for type-safe configuration loading.

    - **`implementation("ch.qos.logback:logback-classic:1.4.8")`** - High-performance logging framework implementing SLF4J API.

    - **`testImplementation("ru.tinkoff.kora:test-junit5")`** - Kora's JUnit 5 integration for testing components with proper DI context.

=== ":simple-kotlin: `Kotlin`"

    Add the Kora dependencies to your root `build.gradle.kts` file (after the subprojects block):

    ```kotlin
    // Dependencies
    dependencies {
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.2.2"))
        ksp("ru.tinkoff.kora:symbol-processor")

        // Core DI functionality
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ch.qos.logback:logback-classic:1.4.8")

        // Testing dependencies for all subprojects
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

    **Why these dependencies?**

    - **`koraBom(platform("ru.tinkoff.kora:kora-parent:1.2.2"))`** - Kora's Bill of Materials (BOM) that manages versions for all Kora dependencies, ensuring compatibility across modules.

    - **`ksp("ru.tinkoff.kora:symbol-processor")`** - Kotlin Symbol Processing (KSP) for compile-time code generation optimized for Kotlin's type system.

    - **`implementation("ru.tinkoff.kora:config-hocon")`** - Configuration management using HOCON format for type-safe configuration loading.

    - **`implementation("ch.qos.logback:logback-classic:1.4.8")`** - High-performance logging framework implementing SLF4J API.

    - **`testImplementation("ru.tinkoff.kora:test-junit5")`** - Kora's JUnit 5 integration for testing components with proper DI context.

### Step 1: Project Setup and Basic Structure

**Goal**: Create a multi-module project with proper separation of concerns.

**Project Structure**:
```
kora-di-tutorial/
├── common/          # Shared interfaces
├── lib/            # External library modules
├── app/            # Main application
└── submodule/      # Feature-specific submodules (added in Step 6)
```

**Create the shared interfaces** (`common/src/main/java/com/example/di/common/` or `common/src/main/kotlin/com/example/di/common/`):

===! ":fontawesome-brands-java: Java"

    First, create `common/build.gradle`:

    ```groovy
    plugins {
        id 'java-library'
    }
    ```

    Then create the interfaces:

    ```java
    // Notifier.java - Common interface for all notification services
    package com.example.di.common;

    public interface Notifier {
        void notify(String user, String message);
    }

    // SmsCellularProvider.java - Optional cellular service provider
    package com.example.di.common;

    public interface SmsCellularProvider {
        String getCode();
    }
    ```

=== ":simple-kotlin: Kotlin"

    First, create `common/build.gradle.kts`:

    ```kotlin
    plugins {
        kotlin("jvm") version ("1.9.25")
    }
    ```

    Then create the interfaces:

    ```kotlin
    // Notifier.kt - Common interface for all notification services
    package com.example.di.common

    interface Notifier {
        fun notify(user: String, message: String)
    }

    // SmsCellularProvider.kt - Optional cellular service provider
    package com.example.di.common

    interface SmsCellularProvider {
        fun getCode(): String
    }
    ```

**Create the main application** (`app/src/main/java/com/example/di/app/` or `app/src/main/kotlin/com/example/di/app/`):

===! ":fontawesome-brands-java: Java"

    First, create `app/build.gradle`:

    ```groovy
    plugins {
        id 'application'
    }

    application {
        mainClass = 'com.example.di.app.Application'
    }
    ```

    Then create the application:

    ```java
    package com.example.di.app;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;

    @KoraApp
    public interface Application extends HoconConfigModule {
        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    First, create `app/build.gradle.kts`:

    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version ("1.9.25")
        id("com.google.devtools.ksp") version ("1.9.25-1.0.20")
    }

    application {
        mainClass.set("com.example.di.app.Application")
    }
    ```

    Then create the application:

    ```kotlin
    package com.example.di.app

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule

    @KoraApp
    interface Application : HoconConfigModule {
        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                KoraApplication.run(ApplicationGraph::graph)
            }
        }
    }
    ```

**Build and run**:
```bash
./gradlew build
./gradlew run
```

**Expected Output**: Application starts and shuts down cleanly (no components yet).

---

### Step 2: External Modules - Library Components

**Goal**: Create reusable library modules that provide default implementations.

**Create EmailModule** (`lib/src/main/java/com/example/di/email/` or `lib/src/main/kotlin/com/example/di/email/`):

===! ":fontawesome-brands-java: Java"

    Create the EmailModule:

    ```java
    package com.example.di.email;

    import com.example.di.common.Notifier;
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
            return extractor.extract(config.get("notifier.email"));
        }

        @Tag(EmailTag.class)
        @DefaultComponent
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "📧: ";
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

=== ":simple-kotlin: Kotlin"

    Create the EmailModule:

    ```kotlin
    package com.example.di.email

    import com.example.di.common.Notifier
    import ru.tinkoff.kora.common.DefaultComponent
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.config.common.Config
    import ru.tinkoff.kora.config.common.extractor.ConfigValueExtractor

    interface EmailModule {
        class EmailTag {
            // Kotlin classes are final by default, no private constructor needed
        }

        fun config(config: Config, extractor: ConfigValueExtractor<EmailConfig>): EmailConfig {
            return extractor.extract(config.get("notifier.email"))
        }

        @Tag(EmailTag::class)
        @DefaultComponent
        fun emailNotifierHeaderSupplier(): () -> String {
            return { "📧: " }
        }

        @Tag(EmailTag::class)
        fun emailNotifier(emailConfig: EmailConfig,
                         @Tag(EmailTag::class) emailHeaderSupplier: () -> String): Notifier {
            val header = emailHeaderSupplier()
            return Notifier { user, message ->
                println("$header${emailConfig.topic()} [USER:$user]: $message")
            }
        }
    }
    ```

**Create EmailConfig** (`lib/src/main/java/com/example/di/email/` or `lib/src/main/kotlin/com/example/di/email/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.email;

    public record EmailConfig(String topic) {}
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.email

    data class EmailConfig(val topic: String)
    ```

**Update Application** to include the email module:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, EmailModule {
        // EmailModule provides default email notification
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, EmailModule {
        // EmailModule provides default email notification
    }
    ```

**Create application.conf** (`app/src/main/resources/`):

```hocon
notifier.email {
  topic = "USER"
}
```

**Build and run** - Application still has no root component, so it just starts and stops.

**Key Concept**: `@DefaultComponent` provides library defaults that applications can override.

---

### Step 3: Component Override - Customizing Library Behavior

**Goal**: Show how applications can override library defaults.

**Create NotifyRunner** (`app/src/main/java/com/example/di/app/` or `app/src/main/kotlin/com/example/di/app/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.app;

    import com.example.di.common.Notifier;
    import ru.tinkoff.kora.application.graph.All;
    import ru.tinkoff.kora.application.graph.Lifecycle;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Root;

    @Root
    @Component
    public final class NotifyRunner implements Lifecycle {
        private final All<Notifier> notifiers;

        public NotifyRunner(All<Notifier> notifiers) {
            this.notifiers = notifiers;
        }

        @Override
        public void init() throws Exception {
            System.out.println("🚀 === DI Tutorial - Step 3 ===");
            System.out.println("📧 Testing email notification:");
            notifiers.forEach(n -> n.notify("Alice", "Welcome!"));
        }

        @Override
        public void release() throws Exception {
            System.out.println("✅ Application shutdown");
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.app

    import com.example.di.common.Notifier
    import ru.tinkoff.kora.application.graph.All
    import ru.tinkoff.kora.application.graph.Lifecycle
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Root

    @Root
    @Component
    class NotifyRunner(
        private val notifiers: All<Notifier>
    ) : Lifecycle {

        override fun init() {
            println("🚀 === DI Tutorial - Step 3 ===")
            println("📧 Testing email notification:")
            notifiers.forEach { it.notify("Alice", "Welcome!") }
        }

        override fun release() {
            println("✅ Application shutdown")
        }
    }
    ```

**Update Application** to override the email header:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, EmailModule {
        @Tag(EmailTag.class)
        @Override
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "📧 [OVERRIDDEN]: ";
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, EmailModule {
        @Tag(EmailTag::class)
        override fun emailNotifierHeaderSupplier(): () -> String {
            return { "📧 [OVERRIDDEN]: " }
        }
    }
    ```

**Build and run**:

```
🚀 === DI Tutorial - Step 3 ===
📧 Testing email notification:
📧 [OVERRIDDEN]: USER [USER:Alice]: Welcome!
✅ Application shutdown
```

**Key Concept**: Applications can override `@DefaultComponent` implementations by providing their own factory methods.

---

### Step 4: Tagged Dependencies - Multiple Implementations

**Goal**: Demonstrate how tags allow multiple implementations of the same interface.

**Create SmsModule** (`app/src/main/java/com/example/di/app/sms/` or `app/src/main/kotlin/com/example/di/app/sms/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.app.sms;

    import com.example.di.common.Notifier;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Module;
    import ru.tinkoff.kora.common.Tag;

    @Module
    public interface SmsModule {
        final class SmsTag {
            private SmsTag() {}
        }

        @Tag(SmsTag.class)
        @Component
        default Notifier smsNotifier() {
            return (user, message) -> System.out.println("📱 [SMS] " + user + "@" + message);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.app.sms

    import com.example.di.common.Notifier
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Module
    import ru.tinkoff.kora.common.Tag

    @Module
    interface SmsModule {
        class SmsTag {
            // Kotlin classes are final by default
        }

        @Tag(SmsTag::class)
        @Component
        fun smsNotifier(): Notifier {
            return Notifier { user, message ->
                println("📱 [SMS] $user@$message")
            }
        }
    }
    ```

**Update Application** to include SMS module:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, EmailModule, SmsModule {
        // Now has both email and SMS notifiers
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, EmailModule, SmsModule {
        // Now has both email and SMS notifiers
    }
    ```

**Update NotifyRunner** to show tagged injection:

===! ":fontawesome-brands-java: Java"

    ```java
    @Root
    @Component
    public final class NotifyRunner implements Lifecycle {
        private final All<Notifier> allNotifiers;

        public NotifyRunner(All<Notifier> allNotifiers) {
            this.allNotifiers = allNotifiers;
        }

        @Override
        public void init() throws Exception {
            System.out.println("🚀 === DI Tutorial - Step 4 ===");
            System.out.println("📧📱 Testing all notifications:");
            allNotifiers.forEach(n -> n.notify("Bob", "Hello!"));
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Root
    @Component
    class NotifyRunner(
        private val allNotifiers: All<Notifier>
    ) : Lifecycle {

        override fun init() {
            println("🚀 === DI Tutorial - Step 4 ===")
            println("📧📱 Testing all notifications:")
            allNotifiers.forEach { it.notify("Bob", "Hello!") }
        }
    }
    ```

**Build and run**:

```
🚀 === DI Tutorial - Step 4 ===
📧📱 Testing all notifications:
📧 [OVERRIDDEN]: USER [USER:Bob]: Hello!
📱 [SMS] Bob@Hello!
✅ Application shutdown
```

**Key Concept**: `All<T>` injects all implementations of a type, allowing broadcasting to multiple services.

---

### Step 5: Optional Dependencies - Graceful Degradation

**Goal**: Show how to handle dependencies that might not be available.

**Create SmsCellularModule** (`lib/src/main/java/com/example/di/email/` or `lib/src/main/kotlin/com/example/di/email/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.email;

    import com.example.di.common.SmsCellularProvider;
    import ru.tinkoff.kora.common.DefaultComponent;

    public interface SmsCellularModule {
        @DefaultComponent
        default SmsCellularProvider smsCellularProvider() {
            return () -> "1";
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.email

    import com.example.di.common.SmsCellularProvider
    import ru.tinkoff.kora.common.DefaultComponent

    interface SmsCellularModule {
        @DefaultComponent
        fun smsCellularProvider(): SmsCellularProvider {
            return SmsCellularProvider { "1" }
        }
    }
    ```

**Update SmsModule** to use optional cellular provider:

===! ":fontawesome-brands-java: Java"

    ```java
    @Tag(SmsTag.class)
    @Component
    default Notifier smsNotifier(Optional<SmsCellularProvider> cellularProvider) {
        return (user, message) -> {
            if (cellularProvider.isPresent()) {
                String code = cellularProvider.get().getCode();
                System.out.println("+" + code + " 📱 [SMS] " + user + "@" + message);
            } else {
                System.out.println("📱 [SMS] " + user + "@" + message);
            }
        };
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Tag(SmsTag::class)
    @Component
    fun smsNotifier(cellularProvider: Optional<SmsCellularProvider>): Notifier {
        return Notifier { user, message ->
            if (cellularProvider.isPresent) {
                val code = cellularProvider.get().getCode()
                println("+$code 📱 [SMS] $user@$message")
            } else {
                println("📱 [SMS] $user@$message")
            }
        }
    }
    ```

**Update Application** to optionally include cellular module:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, EmailModule, SmsModule {
        // SmsCellularModule not included - SMS works without cellular provider
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, EmailModule, SmsModule {
        // SmsCellularModule not included - SMS works without cellular provider
    }
    ```

**Build and run** - SMS works without cellular provider.

**Now include cellular module**:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, EmailModule, SmsCellularModule, SmsModule {
        // Now SMS includes cellular provider
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, EmailModule, SmsCellularModule, SmsModule {
        // Now SMS includes cellular provider
    }
    ```

**Build and run**:

```
🚀 === DI Tutorial - Step 5 ===
📧📱 Testing all notifications:
📧 [OVERRIDDEN]: USER [USER:Bob]: Hello!
+1 📱 [SMS] Bob@Hello!
✅ Application shutdown
```

**Key Concept**: `Optional<T>` allows graceful handling of missing dependencies.

---

### Step 6: Submodules - Component Organization

**Goal**: Demonstrate @KoraSubmodule for organizing related components.

First, create the submodule directory and update settings.gradle:

```bash
mkdir submodule
```

Then update your `settings.gradle` (or `settings.gradle.kts`) to include the submodule:

```groovy
rootProject.name = 'kora-di-tutorial'

include 'common'
include 'lib'
include 'submodule'
include 'app'
```

**Create MessengerModule** (`submodule/src/main/java/com/example/di/messenger/` or `submodule/src/main/kotlin/com/example/di/messenger/`):

===! ":fontawesome-brands-java: Java"

    First, create `submodule/build.gradle`:

    ```groovy
    plugins {
        id 'java-library'
    }
    ```

    Then create the MessengerModule:

    ```java
    package com.example.di.messenger;

    import ru.tinkoff.kora.common.KoraSubmodule;

    @KoraSubmodule
    public interface MessengerModule {
        final class MessengerTag {
            private MessengerTag() {}
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    First, create `submodule/build.gradle.kts`:

    ```kotlin
    plugins {
        kotlin("jvm") version ("1.9.25")
    }
    ```

    Then create the MessengerModule:

    ```kotlin
    package com.example.di.messenger

    import ru.tinkoff.kora.common.KoraSubmodule

    @KoraSubmodule
    interface MessengerModule {
        class MessengerTag {
            // Kotlin classes are final by default
        }
    }
    ```

**Create Messenger interface** (`submodule/src/main/java/com/example/di/messenger/` or `submodule/src/main/kotlin/com/example/di/messenger/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.messenger;

    public interface Messenger {
        void sendMessage(String message);
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.messenger

    interface Messenger {
        fun sendMessage(message: String)
    }
    ```

**Create Slack implementation** (`submodule/src/main/java/com/example/di/messenger/slack/` or `submodule/src/main/kotlin/com/example/di/messenger/slack/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.messenger.slack;

    import com.example.di.messenger.Messenger;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;

    @Tag(SlackMessenger.class)
    @Component
    public final class SlackMessenger implements Messenger {
        @Override
        public void sendMessage(String message) {
            System.out.println("💬 Slack: " + message);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.messenger.slack

    import com.example.di.messenger.Messenger
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag

    @Tag(SlackMessenger::class)
    @Component
    class SlackMessenger : Messenger {
        override fun sendMessage(message: String) {
            println("💬 Slack: $message")
        }
    }
    ```

**Create MessengerNotifier** (`submodule/src/main/java/com/example/di/messenger/` or `submodule/src/main/kotlin/com/example/di/messenger/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.messenger;

    import com.example.di.common.Notifier;
    import ru.tinkoff.kora.application.graph.All;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;

    @Tag(MessengerTag.class)
    @Component
    public final class MessengerNotifier implements Notifier {
        private final All<Messenger> messengers;

        public MessengerNotifier(@Tag(Tag.Any.class) All<Messenger> messengers) {
            this.messengers = messengers;
        }

        @Override
        public void notify(String user, String message) {
            System.out.println("=== Broadcasting to messengers ===");
            messengers.forEach(m -> m.sendMessage(user + "@" + message));
            System.out.println("=== Broadcast complete ===");
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.messenger

    import com.example.di.common.Notifier
    import ru.tinkoff.kora.application.graph.All
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag

    @Tag(MessengerTag::class)
    @Component
    class MessengerNotifier(
        @Tag(Tag.Any::class) private val messengers: All<Messenger>
    ) : Notifier {

        override fun notify(user: String, message: String) {
            println("=== Broadcasting to messengers ===")
            messengers.forEach { it.sendMessage("$user@$message") }
            println("=== Broadcast complete ===")
        }
    }
    ```

**Update Application** to include messenger module:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, EmailModule, SmsCellularModule, SmsModule, MessengerModule {
        // MessengerModule automatically included via @KoraSubmodule
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, EmailModule, SmsCellularModule, SmsModule, MessengerModule {
        // MessengerModule automatically included via @KoraSubmodule
    }
    ```

**Build and run**:

```
🚀 === DI Tutorial - Step 6 ===
📧📱 Testing all notifications:
📧 [OVERRIDDEN]: USER [USER:Bob]: Hello!
+1 📱 [SMS] Bob@Hello!
=== Broadcasting to messengers ===
💬 Slack: Bob@Hello!
=== Broadcast complete ===
✅ Application shutdown
```

**Key Concept**: `@KoraSubmodule` automatically includes related components without explicit imports.

---

### Step 7: Generic Factories - Type-Safe Component Creation

**Goal**: Demonstrate generic factory methods for flexible component creation.

**Create Storage interface** (`app/src/main/java/com/example/di/app/storage/` or `app/src/main/kotlin/com/example/di/app/storage/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.app.storage;

    import java.util.function.Function;

    public interface Storage<T> {
        void save(T data);
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.app.storage

    interface Storage<T> {
        fun save(data: T)
    }
    ```

**Create TempFileStorage** (`app/src/main/java/com/example/di/app/storage/` or `app/src/main/kotlin/com/example/di/app/storage/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.app.storage;

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
                System.out.println("💾 Saved to: " + tempFile.getFileName());
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.app.storage

    import java.io.IOException
    import java.nio.file.Files
    import java.nio.file.Path

    class TempFileStorage<T>(
        private val mapper: (T) -> ByteArray
    ) : Storage<T> {

        override fun save(data: T) {
            try {
                val tempFile = Files.createTempFile("storage-", ".tmp")
                Files.write(tempFile, mapper(data))
                println("💾 Saved to: ${tempFile.fileName}")
            } catch (e: IOException) {
                throw RuntimeException(e)
            }
        }
    }
    ```

**Create StorageModule** (`app/src/main/java/com/example/di/app/storage/` or `app/src/main/kotlin/com/example/di/app/storage/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.app.storage;

    import ru.tinkoff.kora.common.Module;

    import java.nio.charset.StandardCharsets;
    import java.util.function.Function;

    @Module
    public interface StorageModule {
        default Function<Integer, byte[]> intMapper() {
            return i -> new byte[]{i.byteValue()};
        }

        default Function<String, byte[]> stringMapper() {
            return s -> s.getBytes(StandardCharsets.UTF_8);
        }

        default <T> Storage<T> typedStorage(Function<T, byte[]> mapper) {
            return new TempFileStorage<>(mapper);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.app.storage

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

**Update Application** to include storage module:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, EmailModule, SmsCellularModule, SmsModule, MessengerModule, StorageModule {
        // StorageModule provides generic storage factory
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, EmailModule, SmsCellularModule, SmsModule, MessengerModule, StorageModule {
        // StorageModule provides generic storage factory
    }
    ```

**Update NotifyRunner** to demonstrate storage:

===! ":fontawesome-brands-java: Java"

    ```java
    @Root
    @Component
    public final class NotifyRunner implements Lifecycle {
        private final All<Notifier> allNotifiers;
        private final Storage<String> stringStorage;

        public NotifyRunner(All<Notifier> allNotifiers, Storage<String> stringStorage) {
            this.allNotifiers = allNotifiers;
            this.stringStorage = stringStorage;
        }

        @Override
        public void init() throws Exception {
            System.out.println("🚀 === DI Tutorial - Step 7 ===");
            allNotifiers.forEach(n -> n.notify("Charlie", "Greetings!"));
            stringStorage.save("User data stored");
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Root
    @Component
    class NotifyRunner(
        private val allNotifiers: All<Notifier>,
        private val stringStorage: Storage<String>
    ) : Lifecycle {

        override fun init() {
            println("🚀 === DI Tutorial - Step 7 ===")
            allNotifiers.forEach { it.notify("Charlie", "Greetings!") }
            stringStorage.save("User data stored")
        }
    }
    ```

**Build and run**:

```
🚀 === DI Tutorial - Step 7 ===
📧 [OVERRIDDEN]: USER [USER:Charlie]: Greetings!
+1 📱 [SMS] Charlie@Greetings!
=== Broadcasting to messengers ===
💬 Slack: Charlie@Greetings!
=== Broadcast complete ===
💾 Saved to: storage-123456.tmp
✅ Application shutdown
```

**Key Concept**: Generic factory methods `<T>` enable type-safe component creation with flexible configuration.

---

### Step 8: Preventing Cascading Refreshes with ValueOf<T> - Component Update Control

**Goal**: Demonstrate ValueOf<T> for preventing unwanted cascading component refreshes when dependencies are updated.

**Create ActivityRecorder interface** (`app/src/main/java/com/example/di/app/activity/` or `app/src/main/kotlin/com/example/di/app/activity/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.app.activity;

    public interface ActivityRecorder {
        void connect();
        void disconnect();
        boolean isConnected();
        void recordUser(String user);
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.app.activity

    interface ActivityRecorder {
        fun connect()
        fun disconnect()
        fun isConnected(): Boolean
        fun recordUser(user: String)
    }
    ```

**Create ActivityService** (`app/src/main/java/com/example/di/app/activity/` or `app/src/main/kotlin/com/example/di/app/activity/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.app.activity;

    import ru.tinkoff.kora.application.graph.ValueOf;
    import ru.tinkoff.kora.common.Component;

    @Component
    public final class ActivityService {
        private final ValueOf<ActivityRecorder> activityRecorder;

        public ActivityService(ValueOf<ActivityRecorder> activityRecorder) {
            this.activityRecorder = activityRecorder;
            System.out.println("🔧 ActivityService created (ActivityRecorder not yet accessed)");
        }

        public void recordActivityByUserName(String user) {
            System.out.println("⚙️ Recording activity for: " + user);
            ActivityRecorder recorder = activityRecorder.get(); // Lazy access
            recorder.recordUser(user);
            System.out.println("✅ Activity recorded successfully");
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.app.activity

    import ru.tinkoff.kora.application.graph.ValueOf
    import ru.tinkoff.kora.common.Component

    @Component
    class ActivityService(
        private val activityRecorder: ValueOf<ActivityRecorder>
    ) {

        init {
            println("🔧 ActivityService created (ActivityRecorder not yet accessed)")
        }

        fun recordActivityByUserName(user: String) {
            println("⚙️ Recording activity for: $user")
            val recorder = activityRecorder.get() // Lazy access
            recorder.recordUser(user)
            println("✅ Activity recorded successfully")
        }
    }
    ```

**Create ActivityModule** (`app/src/main/java/com/example/di/app/activity/` or `app/src/main/kotlin/com/example/di/app/activity/`):

===! ":fontawesome-brands-java: Java"

    ```java
    package com.example.di.app.activity;

    import ru.tinkoff.kora.application.graph.LifecycleWrapper;
    import ru.tinkoff.kora.application.graph.Wrapped;
    import ru.tinkoff.kora.common.Module;

    @Module
    public interface ActivityModule {
        default Wrapped<ActivityRecorder> activityRecorder() {
            var recorder = new ActivityRecorder() {
                private boolean connected = false;

                @Override
                public void connect() {
                    if (!connected) {
                        System.out.println("🔌 Connecting to activity recorder...");
                        try { Thread.sleep(100); } catch (InterruptedException e) {}
                        connected = true;
                        System.out.println("✅ Activity recorder connected!");
                    }
                }

                @Override
                public void disconnect() {
                    if (connected) {
                        System.out.println("🔌 Disconnecting from activity recorder...");
                        connected = false;
                    }
                }

                @Override
                public boolean isConnected() {
                    return connected;
                }

                @Override
                public void recordUser(String user) {
                    if (!connected) connect();
                    System.out.println("📊 Recording user activity: " + user);
                }
            };

            return new LifecycleWrapper<>(recorder, c -> {}, ActivityRecorder::disconnect);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    package com.example.di.app.activity

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
                        println("🔌 Connecting to activity recorder...")
                        try { Thread.sleep(100) } catch (e: InterruptedException) {}
                        connected = true
                        println("✅ Activity recorder connected!")
                    }
                }

                override fun disconnect() {
                    if (connected) {
                        println("🔌 Disconnecting from activity recorder...")
                        connected = false
                    }
                }

                override fun isConnected(): Boolean {
                    return connected
                }

                override fun recordUser(user: String) {
                    if (!connected) connect()
                    println("📊 Recording user activity: $user")
                }
            }

            return LifecycleWrapper(recorder, {}, ActivityRecorder::disconnect)
        }
    }
    ```

**Update Application** to include activity module:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, EmailModule, SmsCellularModule, SmsModule, MessengerModule, StorageModule, ActivityModule {
        // ActivityModule provides activity recorder with ValueOf<T> to prevent cascading refreshes
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, EmailModule, SmsCellularModule, SmsModule, MessengerModule, StorageModule, ActivityModule {
        // ActivityModule provides activity recorder with ValueOf<T> to prevent cascading refreshes
    }
    ```

**Update NotifyRunner** to demonstrate ValueOf<T> refresh prevention:

===! ":fontawesome-brands-java: Java"

    ```java
    @Root
    @Component
    public final class NotifyRunner implements Lifecycle {
        private final All<Notifier> allNotifiers;
        private final Storage<String> stringStorage;
        private final ActivityService activityService;

        public NotifyRunner(All<Notifier> allNotifiers, Storage<String> stringStorage, ActivityService activityService) {
            this.allNotifiers = allNotifiers;
            this.stringStorage = stringStorage;
            this.activityService = activityService;
        }

        @Override
        public void init() throws Exception {
            System.out.println("🚀 === DI Tutorial - Complete Application ===");
            allNotifiers.forEach(n -> n.notify("Diana", "Welcome to Kora DI!"));
            stringStorage.save("Complete application data");
            activityService.recordActivityByUserName("Diana");
            System.out.println("🎉 All DI concepts demonstrated successfully!");
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Root
    @Component
    class NotifyRunner(
        private val allNotifiers: All<Notifier>,
        private val stringStorage: Storage<String>,
        private val activityService: ActivityService
    ) : Lifecycle {

        override fun init() {
            println("🚀 === DI Tutorial - Complete Application ===")
            allNotifiers.forEach { it.notify("Diana", "Welcome to Kora DI!") }
            stringStorage.save("Complete application data")
            activityService.recordActivityByUserName("Diana")
            println("🎉 All DI concepts demonstrated successfully!")
        }
    }
    ```

**Build and run**:

```
🔧 ActivityService created (ActivityRecorder not yet accessed)
🚀 === DI Tutorial - Complete Application ===
📧 [OVERRIDDEN]: USER [USER:Diana]: Welcome to Kora DI!
+1 📱 [SMS] Diana@Welcome to Kora DI!
=== Broadcasting to messengers ===
💬 Slack: Diana@Welcome to Kora DI!
=== Broadcast complete ===
💾 Saved to: storage-789012.tmp
⚙️ Recording activity for: Diana
🔌 Connecting to activity recorder...
✅ Activity recorder connected!
📊 Recording user activity: Diana
✅ Activity recorded successfully
🔌 Disconnecting from activity recorder...
🎉 All DI concepts demonstrated successfully!
✅ Application shutdown
```

**Key Concept**: `ValueOf<T>` prevents cascading component refreshes - when a dependency is refreshed, components that depend on it indirectly via `ValueOf<T>` are not automatically refreshed, allowing them to access updated values without being recreated themselves.

---

### Tutorial Summary

You've built a complete Kora application demonstrating all major dependency injection concepts:

1. **Project Structure** - Multi-module organization
2. **External Modules** - Library components with `@DefaultComponent`
3. **Component Override** - Customizing library defaults
4. **Tagged Dependencies** - Multiple implementations with `@Tag`
5. **Collection Injection** - `All<T>` for broadcasting
6. **Submodules** - `@KoraSubmodule` for component organization
7. **Generic Factories** - `<T>` parameterized component creation
8. **Optional Dependencies** - `Optional<T>` for graceful degradation
9. **Preventing Cascading Refreshes** - `ValueOf<T>` to control component refresh behavior

Each step builds upon the previous, showing how Kora's compile-time DI enables clean, modular, and performant applications.

## Troubleshooting

### Common Issues and Solutions

#### Circular Dependencies

**Problem**: Two or more components depend on each other directly or indirectly.

**Symptoms**:
- Compile-time error: "Circular dependency detected"
- Annotation processor fails with dependency resolution error

**Solutions**:

1. **Refactor to Interface Segregation**:

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

=== ":simple-kotlin: Kotlin"

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

2. **Use ValueOf for Indirect Dependencies**:

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

=== ":simple-kotlin: Kotlin"

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

#### Missing Dependencies

**Problem**: Component requires a dependency that cannot be found.

**Symptoms**:
- Compile-time error: "No component found for type X"
- Clear error message showing dependency chain

**Solutions**:

1. **Add Missing Component**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Add the missing component
    @Component
    public final class MissingDependency {
        // Implementation
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Add the missing component
    @Component
    class MissingDependency {
        // Implementation
    }
    ```

2. **Create Factory Method**:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application {
        default MissingDependency missingDependency() {
            return new MissingDependency();
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application {
        fun missingDependency(): MissingDependency {
            return MissingDependency()
        }
    }
    ```

#### Configuration Issues

**Problem**: Components can't access configuration values.

**Symptoms**:
- Runtime error: "Configuration value not found"
- NullPointerException when accessing config properties

**Solutions**:

1. **Add Configuration Module**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Include configuration module
    @KoraApp
    public interface Application extends HoconConfigModule {
        // Now configuration is available
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Include configuration module
    @KoraApp
    interface Application : HoconConfigModule {
        // Now configuration is available
    }
    ```

2. **Check Property Names**:

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

=== ":simple-kotlin: Kotlin"

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

#### Tag Resolution Issues

**Problem**: Tagged dependencies cannot be resolved.

**Symptoms**:
- Compile error: "Multiple components found for type X"
- Or: "No component found for tagged type X"

**Solutions**:

1. **Use Correct Tag Annotation**:

===! ":fontawesome-brands-java: Java"

    ```java
    // ✅ Correct tag usage
    @Component
    public final class MyService {
        public MyService(@Tag(MyTag.class) Dependency dep) {
            // Correct
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // ✅ Correct tag usage
    @Component
    class MyService(
        @Tag(MyTag::class) val dep: Dependency
    ) {
        // Correct
    }
    ```

2. **Check Tag Class Definition**:

===! ":fontawesome-brands-java: Java"

    ```java
    // ✅ Tag class must be public
    public final class MyTag {} // Correct

    // ❌ Private tag won't work
    private final class MyTag {} // Wrong
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // ✅ Tag class must be public
    class MyTag // Correct (public by default)

    // ❌ Private tag won't work
    private class MyTag // Wrong
    ```

#### Module Import Issues

**Problem**: Components from modules are not available.

**Symptoms**:
- Compile error: "No component found for type from module"

**Solutions**:

1. **Include Module in Application**:

===! ":fontawesome-brands-java: Java"

    ```java
    // ✅ Include the module
    @KoraApp
    public interface Application extends MyModule {
        // Components from MyModule now available
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // ✅ Include the module
    @KoraApp
    interface Application : MyModule {
        // Components from MyModule now available
    }
    ```

2. **Check Module Visibility**:

===! ":fontawesome-brands-java: Java"

    ```java
    // ✅ Module methods must be public
    @Module
    public interface MyModule {
        @Component
        default MyComponent myComponent() { // public by default
            return new MyComponent();
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // ✅ Module methods must be public
    @Module
    interface MyModule {
        @Component
        fun myComponent(): MyComponent { // public by default
            return MyComponent()
        }
    }
    ```

#### Collection Injection Issues

**Problem**: `All<T>` doesn't inject expected components.

**Symptoms**:
- Empty collection when expecting multiple implementations
- Missing expected components in `All<T>`

**Solutions**:

1. **Ensure All Implementations are Components**:

===! ":fontawesome-brands-java: Java"

    ```java
    // ✅ All implementations must be @Component
    @Component
    public final class Impl1 implements MyInterface {}

    @Component
    public final class Impl2 implements MyInterface {}

    // Now All<MyInterface> will contain both
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // ✅ All implementations must be @Component
    @Component
    class Impl1 : MyInterface

    @Component
    class Impl2 : MyInterface

    // Now All<MyInterface> will contain both
    ```

2. **Check for Tag Conflicts**:

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // If using tags, make sure you're not accidentally filtering
    @Component
    class MyService(
        val all: All<MyInterface> // Gets all implementations
    ) {
        // ...
    }
    ```

#### Optional Dependency Issues

**Problem**: Optional dependencies behave unexpectedly.

**Symptoms**:
- Optional is empty when expecting a value
- NullPointerException when using optional

**Solutions**:

1. **Handle Optional Correctly**:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class MyService {
        private final Optional<Dependency> optionalDep;

        public MyService(Optional<Dependency> optionalDep) {
            this.optionalDep = optionalDep;
        }

        public void doSomething() {
            // ✅ Safe optional usage
            optionalDep.ifPresent(dep -> dep.doWork());

            // ❌ Dangerous - can cause NPE
            // optionalDep.get().doWork(); // Don't do this without checking
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class MyService(
        private val optionalDep: Optional<Dependency>
    ) {

        fun doSomething() {
            // ✅ Safe optional usage
            optionalDep.ifPresent { it.doWork() }

            // ❌ Dangerous - can cause NPE
            // optionalDep.get().doWork() // Don't do this without checking
        }
    }
    ```

2. **Ensure Optional Component Exists**:

===! ":fontawesome-brands-java: Java"

    ```java
    // If you want optional to have a value, ensure the component exists
    @KoraApp
    public interface Application extends OptionalModule {
        // Include the module that provides the optional dependency
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // If you want optional to have a value, ensure the component exists
    @KoraApp
    interface Application : OptionalModule {
        // Include the module that provides the optional dependency
    }
    ```

#### Lifecycle Issues

**Problem**: Components with lifecycle methods don't start/stop properly.

**Symptoms**:
- `init()` or `destroy()` methods not called
- Resources not cleaned up properly

**Solutions**:

1. **Implement Lifecycle Interface**:

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

=== ":simple-kotlin: Kotlin"

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

2. **Check Component Registration**:

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

=== ":simple-kotlin: Kotlin"

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

#### Generic Type Issues

**Problem**: Generic components (`<T>`) don't resolve correctly.

**Symptoms**:
- Compile error: "Generic type cannot be resolved"
- Wrong generic type injected

**Solutions**:

1. **Use Proper Generic Constraints**:

===! ":fontawesome-brands-java: Java"

    ```java
    // ✅ Specify generic type explicitly
    @Component
    public final class StringStorage implements Storage<String> {}

    @Component
    public final class MyService {
        public MyService(Storage<String> storage) { // Specify type
            // Correct
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // ✅ Specify generic type explicitly
    @Component
    class StringStorage : Storage<String>

    @Component
    class MyService(
        val storage: Storage<String> // Specify type
    ) {
        // Correct
    }
    ```

2. **Check Generic Factory Methods**:

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface StorageModule {
        @Component
        fun <T> storage(type: Class<T>): Storage<T> {
            return InMemoryStorage() // Generic factory
        }
    }
    ```

#### Build and Compilation Issues

**Problem**: Kora annotation processor fails or generates incorrect code.

**Symptoms**:
- Compilation errors in generated code
- "Annotation processor not found" errors
- Generated classes have issues

**Solutions**:

1. **Check Dependencies**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Ensure Kora dependencies are included
    dependencies {
        implementation 'ru.tinkoff.kora:kora-app-annotation-processor'
        implementation 'ru.tinkoff.kora:config-hocon'
        // Other Kora modules...
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Ensure Kora dependencies are included
    dependencies {
        implementation("ru.tinkoff.kora:kora-app-annotation-processor")
        implementation("ru.tinkoff.kora:config-hocon")
        // Other Kora modules...
    }
    ```

2. **Clean Build**:

===! ":fontawesome-brands-java: Java"

    ```bash
    # Clean and rebuild
    ./gradlew clean build
    ```

=== ":simple-kotlin: Kotlin"

    ```bash
    # Clean and rebuild
    ./gradlew clean build
    ```

3. **Check Java Version**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Ensure using supported Java version (11, 17, 21)
    java --version
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Ensure using supported Java version (11, 17, 21)
    java --version
    ```

#### Testing Issues

**Problem**: Components are hard to test or tests fail unexpectedly.

**Symptoms**:
- Difficult to inject mocks
- Test dependencies not resolved
- Integration test failures

**Solutions**:

1. **Use Constructor Injection for Testability**:

===! ":fontawesome-brands-java: Java"

    ```java
    // ✅ Testable component
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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // ✅ Testable component
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

2. **Use Testcontainers for Integration Tests**:

===! ":fontawesome-brands-java: Java"

    ```java
    @Testcontainers
    public class UserServiceIntegrationTest {
        @Container
        private static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");

        @Test
        public void testRealDatabase() {
            // Test with real database
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Testcontainers
    class UserServiceIntegrationTest {
        @Container
        private val postgres = PostgreSQLContainer("postgres:15")

        @Test
        fun testRealDatabase() {
            // Test with real database
        }
    }
    ```

#### Common Beginner Mistakes

**1. Forgetting @Component Annotation**:

===! ":fontawesome-brands-java: Java"

    ```java
    // ❌ Missing @Component
    public final class MyService {
        // This won't be discovered by DI
    }

    // ✅ Correct
    @Component
    public final class MyService {
        // Now discoverable
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // ❌ Missing @Component
    class MyService {
        // This won't be discovered by DI
    }

    // ✅ Correct
    @Component
    class MyService {
        // Now discoverable
    }
    ```

**2. Private Constructor**:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class MyService {
        private MyService() {} // ❌ Private constructor blocks DI
    }

    // ✅ Public or package-private constructor
    @Component
    public final class MyService {
        public MyService() {} // Correct
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class MyService private constructor() // ❌ Private constructor blocks DI

    // ✅ Public constructor (default)
    @Component
    class MyService // Correct
    ```

**3. Not Including Modules**:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application {
        // ❌ Components from modules not included
    }

    @KoraApp
    public interface Application extends MyModule {
        // ✅ Module components now available
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application {
        // ❌ Components from modules not included
    }

    @KoraApp
    interface Application : MyModule {
        // ✅ Module components now available
    }
    ```

**4. Circular Dependencies**:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    class A { A(B b) {} }

    @Component
    class B { B(A a) {} } // ❌ Circular dependency

    // ✅ Break the cycle with interfaces or restructuring
    interface AInterface {}
    interface BInterface {}

    @Component
    class AImpl implements AInterface { AImpl(BInterface b) {} }

    @Component
    class BImpl implements ServiceBInterface { BImpl(ServiceAInterface a) {} }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class A(val b: B)

    @Component
    class B(val a: A) // ❌ Circular dependency

    // ✅ Break the cycle with interfaces or restructuring
    interface AInterface
    interface BInterface

    @Component
    class AImpl(val b: BInterface) : AInterface

    @Component
    class BImpl(val a: AInterface) : BInterface
    ```

**5. Ignoring Optional Results**:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class MyService {
        private final Optional<Dependency> dep;

        public MyService(Optional<Dependency> dep) {
            this.dep = dep;
        }

        public void doSomething() {
            dep.get().work(); // ❌ Can throw NoSuchElementException
        }
    }

    // ✅ Safe usage
    public void doSomething() {
        dep.ifPresent(Dependency::work); // Safe
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class MyService(
        private val dep: Optional<Dependency>
    ) {

        fun doSomething() {
            dep.get().work() // ❌ Can throw NoSuchElementException
        }
    }

    // ✅ Safe usage
    fun doSomething() {
        dep.ifPresent { it.work() } // Safe
    }
    ```

#### Getting Help

If you're still stuck:

1. **Check the Examples**: Look at `kora-examples` for working patterns
2. **Read Documentation**: Consult `kora-docs` for detailed explanations
3. **Simplify**: Remove complexity and test with minimal components
4. **Community**: Ask questions in Kora community channels

**Remember**: Most DI issues come from missing components, incorrect module imports, or circular dependencies. Start simple and build up gradually!

## Conclusion

**Congratulations!** You've completed the comprehensive Kora Dependency Injection Guide. You've learned not just *how* to use dependency injection, but *why* it's such a powerful pattern for building maintainable software.

### What You've Mastered

**🔧 Core Concepts**:
- **Dependency Injection**: Managing object dependencies externally instead of creating them internally
- **Inversion of Control**: Framework controls object creation and injection, not your code
- **Compile-Time DI**: Kora's approach provides superior performance and type safety

**🏗️ Kora Architecture**:
- **Components**: The building blocks of your application (`@Component`)
- **Modules**: Organized groups of related components (`@Module`)
- **Application**: The root that brings everything together (`@KoraApp`)

**🛠️ Advanced Patterns**:
- **Tagged Dependencies**: Multiple implementations distinguished by tags (`@Tag`)
- **Collection Injection**: Broadcasting to multiple services (`All<T>`)
- **Optional Dependencies**: Graceful handling of missing features (`Optional<T>`)
- **Preventing Cascading Refreshes**: Component update control with `ValueOf<T>`
- **Generic Factories**: Type-safe component creation with parameters

**✅ Best Practices**:
- Interface-first design
- Single responsibility components
- Constructor injection
- Comprehensive testing
- Proper error handling

### Your Journey Ahead

**As a new developer learning Kora DI**, remember:

1. **Start Simple**: Begin with basic components and gradually add complexity
2. **Follow Examples**: Use `kora-examples` as your reference implementation
3. **Test Early**: Write tests for every component you create
4. **Document Well**: Future you will thank present you for good documentation
5. **Ask Questions**: Don't hesitate to seek help from the Kora community

### Real-World Impact

The patterns you've learned here are used in production applications worldwide. Companies like Tinkoff (Kora's creators) use these exact patterns to build:
- High-performance microservices
- Scalable web applications
- Complex enterprise systems
- Cloud-native architectures

**Your code is now more:**
- **Testable**: Easy to write unit tests with mock dependencies
- **Maintainable**: Changes to one component don't break others
- **Flexible**: Easy to swap implementations or add new features
- **Understandable**: Clear dependency relationships and component responsibilities

### Next Steps

**Ready to build something amazing?** Here are your next learning milestones:

1. **Explore Kora Examples**: Study the `kora-examples` repository for real-world patterns
2. **Build Your First App**: Create a simple REST API using the tutorial patterns
3. **Add Observability**: Learn Kora's telemetry and monitoring features
4. **Database Integration**: Connect your app to a real database
5. **Deploy to Production**: Learn containerization and cloud deployment

## What's Next?

Now that you've completed this comprehensive tutorial, you can explore other Kora features:

- **[Build Simple HTTP application](../getting-started.md)**: Learn how to create REST endpoints with dependency injection

## Help

If you encounter issues:

- **Review the Examples**: Check `kora-examples` repository for working implementations
- **Read the Documentation**: Visit [Kora Documentation](https://kora-projects.github.io/kora-docs/) for detailed module docs
- **Community Support**: Join the [Kora Community](https://github.com/kora-projects) for help
- **Compilation Errors**: Ensure all dependencies are correctly added to `build.gradle`
- **Component Not Found**: Check that components are properly annotated with `@Component`
- **Injection Issues**: Verify constructor parameters match available components