---
seo_title: "Creating a Kora Aspect | Kora"
seo_description: "Create @LogDuration with Kora AP/KSP aspect factories, inspect the generated subclass and verify results, void/Unit and exceptions."
keywords: [ "Kora Framework", "AOP", "KoraAspectFactory", "LogDuration", "JavaPoet", "KotlinPoet", "compile-time interception" ]
search:
    exclude: true
title: "Creating a Kora Aspect"
summary: "Create @LogDuration with Kora AP/KSP aspect factories, inspect the generated subclass and verify results, void/Unit and exceptions."
description: "Use this guide for Kora 2.0 custom synchronous AOP: @AopAnnotation, CLASS/BINARY retention, HOCON/YAML, separate annotation and processor artifacts, KoraAspectFactory Java/Kotlin service registrations, Palantir JavaPoet and KotlinPoet, callSuper and aspect chaining, ApplyResult.MethodBody, try/finally timing, SLF4J logging, graph injection, generated AopProxy paths, open/final constraints, suspend rejection, @AopPropagate and fieldFactory extension points."
agent:
    use_when: "Use this guide for Kora 2.0 custom synchronous AOP: @AopAnnotation, CLASS/BINARY retention, HOCON/YAML, separate annotation and processor artifacts, KoraAspectFactory Java/Kotlin service registrations, Palantir JavaPoet and KotlinPoet, callSuper and aspect chaining, ApplyResult.MethodBody, try/finally timing, SLF4J logging, graph injection, generated AopProxy paths, open/final constraints, suspend rejection, @AopPropagate and fieldFactory extension points."
tags: "integration, aop, ap, ksp, logging"
---

# Creating a Kora Aspect { #integration-aspect }

This guide creates `@LogDuration`, an annotation that measures a synchronous method invocation. You will contribute a method body through Kora’s aspect SPI, let Kora generate the subclass and verify
that normal results, `void`/`Unit` and exceptions keep their behavior. The generated code uses SLF4J from the application’s existing logging dependency.

## What You'll Build { #youll-build }

- A runtime annotation marked with `@AopAnnotation`
- Java AP and Kotlin KSP aspect factories with the correct service entries
- A `GreetingService` that exercises a result, no result and failure
- HTTP routes that reach the service through the graph
- A generated subclass with one next-layer call and duration logging in `finally`

## What You'll Need { #youll-need }

- JDK 25 or later, Gradle 9+ Wrapper and an IDE or editor
- The HTTP application from [Getting Started](getting-started.md)
- Kora `2.0.0.RC2` on runtime and processor classpaths
- Kotlin `2.4.20` and KSP `2.3.12` for the Kotlin branch
- Familiarity with [AP and KSP](integration-processors.md) and generated source inspection

No database or Docker is needed for this independent example.

## Prerequisites { #prerequisites }

!!! note "Required: the working /hello application"

    Keep the baseline application plugin, HTTP, the selected HOCON/YAML config backend and logging dependencies and Kora processor. Replace its controller with the complete example below. The processor guide explains the build-time/runtime split using `@GenerateBuilder`; the aspect is a separate SPI.

Choose the AP factory for Java or the KSP factory for Kotlin. All commands run from the application project root.

## Overview { #overview }

An aspect adds behavior around an existing method without changing that method’s business code. `@LogDuration` records elapsed nanoseconds whether the method returns or throws. It is useful for
understanding compile-time interception; a production duration metric would normally use injected telemetry rather than one log entry per call.

### A subclass, an override and the graph { #subclass-graph }

Kora generates a subclass of the annotated service and overrides the method. The graph supplies that subclass when a controller asks for `GreetingService`. There is no runtime reflection-based proxy:
the intercepting code is visible in generated sources. Directly constructing the base service bypasses this code.

Subclass interception requires overridable classes and methods. Java `final`, private and static methods cannot be overridden; Kotlin needs `open` on both class and method. A virtual self-call to an
annotated method also reaches the generated override.

### Aspect factories versus ordinary processors { #aspect-spi }

The [builder guide](integration-processors.md) registers an ordinary `Processor` or `SymbolProcessorProvider` to generate new types. Here Kora’s existing AOP processor loads a `KoraAspectFactory`,
asks which annotations it supports and requests a method body. Kora still owns the generated class, constructor, parameters and graph wiring.

`superCall` identifies the next layer. With several aspects, it may call another generated wrapper rather than the original method. Preserve it using the supplied helper instead of hardcoding
`super.greet(...)`.

### Measurement boundary { #measurement-boundary }

The timer covers synchronous invocation until return or throw. Returning a future, publisher or other deferred value ends this measurement before that value completes. Kotlin `suspend` is rejected by
this aspect. Async completion requires a separate implementation with a different lifetime contract.

The flow is: separate artifacts, declare the annotation, implement and register the matching factory, add the service and controller, then inspect and exercise the generated subclass.

## Dependencies and Project Layout { #projects }

Add the annotation project and the matching processor project to root settings:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — settings.gradle"

        ```groovy
        include("duration-annotation", "duration-annotation-processor")
        ```

    === "Kotlin DSL — settings.gradle.kts"

        ```kotlin
        include("duration-annotation", "duration-annotation-processor")
        ```

=== ":simple-kotlin: `Kotlin`"

    ===! "Groovy — settings.gradle"

        ```groovy
        include("duration-annotation", "duration-symbol-processor")
        ```

    === "Kotlin DSL — settings.gradle.kts"

        ```kotlin
        include("duration-annotation", "duration-symbol-processor")
        ```

Configure `duration-annotation` using either Gradle DSL. Choose the annotation source language independently of the Gradle DSL:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — build.gradle"

        ```groovy
        plugins { id 'java-library' }
        repositories { mavenCentral() }
        java { toolchain { languageVersion = JavaLanguageVersion.of(25) } }
        dependencies {
            api platform("io.koraframework:kora-bom:2.0.0.RC2")
            api "io.koraframework:common"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins { id("java-library") }
        repositories { mavenCentral() }
        java { toolchain { languageVersion.set(JavaLanguageVersion.of(25)) } }
        dependencies {
            api(platform("io.koraframework:kora-bom:2.0.0.RC2"))
            api("io.koraframework:common")
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    ===! "Groovy — build.gradle"

        ```groovy
        plugins {
            id 'java-library'
            id 'org.jetbrains.kotlin.jvm' version '2.4.20'
        }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        dependencies {
            api platform("io.koraframework:kora-bom:2.0.0.RC2")
            api "io.koraframework:common"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins {
            id("java-library")
            id("org.jetbrains.kotlin.jvm") version "2.4.20"
        }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        dependencies {
            api(platform("io.koraframework:kora-bom:2.0.0.RC2"))
            api("io.koraframework:common")
        }
        ```

Configure the Java processor project `duration-annotation-processor`:

===! "Groovy — build.gradle"

    ```groovy
    plugins { id 'java-library' }
    repositories { mavenCentral() }
    java { toolchain { languageVersion = JavaLanguageVersion.of(25) } }
    dependencies {
        implementation platform("io.koraframework:kora-bom:2.0.0.RC2")
        implementation "io.koraframework:aop-annotation-processor"
    }
    ```

=== "Kotlin DSL — build.gradle.kts"

    ```kotlin
    plugins { id("java-library") }
    repositories { mavenCentral() }
    java { toolchain { languageVersion.set(JavaLanguageVersion.of(25)) } }
    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC2"))
        implementation("io.koraframework:aop-annotation-processor")
    }
    ```

Configure the Kotlin processor project `duration-symbol-processor`:

===! "Groovy — build.gradle"

    ```groovy
    plugins { id 'org.jetbrains.kotlin.jvm' version '2.4.20' }
    repositories { mavenCentral() }
    kotlin { jvmToolchain(25) }
    dependencies {
        implementation platform("io.koraframework:kora-bom:2.0.0.RC2")
        implementation "io.koraframework:aop-symbol-processor"
    }
    ```

=== "Kotlin DSL — build.gradle.kts"

    ```kotlin
    plugins { kotlin("jvm") version "2.4.20" }
    repositories { mavenCentral() }
    kotlin { jvmToolchain(25) }
    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC2"))
        implementation("io.koraframework:aop-symbol-processor")
    }
    ```

Omit the repeated Kotlin plugin version if the root already declares it. The AOP artifacts provide the Kora SPI and their transitive JavaPoet/KotlinPoet APIs. Java uses `com.palantir.javapoet`, not
the older package. These compiler dependencies stay on the processor classpath. The application already receives SLF4J through `logging-logback`.

```text
duration-annotation/
  src/main/java/example/aspect/LogDuration.java       # Java branch
  src/main/kotlin/example/aspect/LogDuration.kt       # Kotlin branch
duration-annotation-processor/             # Java branch
  src/main/java/example/aspect/processor/LogDurationAspectFactory.java
  src/main/resources/META-INF/services/io.koraframework.aop.annotation.processor.KoraAspectFactory
duration-symbol-processor/                 # Kotlin branch
  src/main/kotlin/example/aspect/processor/LogDurationAspectFactory.kt
  src/main/resources/META-INF/services/io.koraframework.aop.symbol.processor.KoraAspectFactory
src/main/resources/application.conf           # HOCON branch
src/main/resources/application.yaml           # YAML branch
src/main/java/example/app/                 # Java application
src/main/kotlin/example/app/               # Kotlin application
```

### Configuration format { #configuration-format }

Keep exactly one config backend in the application. HOCON uses `config-hocon`, `HoconConfigModule` and `application.conf`; YAML uses `config-yaml`, `YamlConfigModule` and `application.yaml`. Replace
the baseline config dependency with the selected one. The complete roots below show both module choices.

===! ":material-code-json: `HOCON`"

    ===! "Groovy — build.gradle"

        ```groovy
        dependencies {
            implementation "io.koraframework:config-hocon"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        dependencies {
            implementation("io.koraframework:config-hocon")
        }
        ```

=== ":simple-yaml: `YAML`"

    ===! "Groovy — build.gradle"

        ```groovy
        dependencies {
            implementation "io.koraframework:config-yaml"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        dependencies {
            implementation("io.koraframework:config-yaml")
        }
        ```

## Annotation { #annotation }

===! ":fontawesome-brands-java: `Java`"

    Create `duration-annotation/src/main/java/example/aspect/LogDuration.java`:

    ```java
    package example.aspect;

    import io.koraframework.common.annotation.AopAnnotation;
    import java.lang.annotation.ElementType;
    import java.lang.annotation.Retention;
    import java.lang.annotation.RetentionPolicy;
    import java.lang.annotation.Target;

    @AopAnnotation
    @Target(ElementType.METHOD)
    @Retention(RetentionPolicy.CLASS)
    public @interface LogDuration {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `duration-annotation/src/main/kotlin/example/aspect/LogDuration.kt`:

    ```kotlin
    package example.aspect

    import io.koraframework.common.annotation.AopAnnotation

    @AopAnnotation
    @Target(AnnotationTarget.FUNCTION)
    @Retention(AnnotationRetention.BINARY)
    annotation class LogDuration
    ```

`@AopAnnotation` tells Kora this annotation requests interception. Method-only targeting keeps the example’s scope explicit. `CLASS` / `BINARY` retention is enough for compile-time processing; runtime
scanning is not required. The annotation itself does not implement the aspect: a registered factory supplies its behavior.

## Aspect Factory { #aspect-factory }

===! ":fontawesome-brands-java: `Java`"

    <span id="java-aspect"></span>

    Create `duration-annotation-processor/src/main/java/example/aspect/processor/LogDurationAspectFactory.java`:

    ```java
    package example.aspect.processor;

    import com.palantir.javapoet.ClassName;
    import com.palantir.javapoet.CodeBlock;
    import io.koraframework.aop.annotation.processor.KoraAspect;
    import io.koraframework.aop.annotation.processor.KoraAspectFactory;
    import javax.annotation.processing.ProcessingEnvironment;
    import javax.lang.model.element.ExecutableElement;
    import javax.lang.model.type.TypeKind;
    import java.util.Optional;
    import java.util.Set;

    public final class LogDurationAspectFactory implements KoraAspectFactory {
        @Override
        public Optional<KoraAspect> create(ProcessingEnvironment environment) {
            return Optional.of(new LogDurationAspect());
        }

        private static final class LogDurationAspect implements KoraAspect {
            @Override
            public Set<ClassName> getSupportedAnnotationClassNames() {
                return Set.of(ClassName.get("example.aspect", "LogDuration"));
            }

            @Override
            public ApplyResult apply(ExecutableElement method, String superCall, AspectContext context) {
                var call = KoraAspect.callSuper(method, superCall);
                var started = "_logDurationStarted";
                var parameterNames = method.getParameters().stream()
                    .map(p -> p.getSimpleName().toString()).collect(java.util.stream.Collectors.toSet());
                while (parameterNames.contains(started)) started += "_";
                var body = CodeBlock.builder()
                    .addStatement("long $N = System.nanoTime()", started)
                    .beginControlFlow("try");
                if (method.getReturnType().getKind() == TypeKind.VOID) {
                    body.addStatement("$L", call);
                } else {
                    body.addStatement("return $L", call);
                }
                body.nextControlFlow("finally")
                    .addStatement("org.slf4j.LoggerFactory.getLogger($S).info($S, $S, System.nanoTime() - $N)",
                        "example.aspect", "{} took {} ns",
                        method.getEnclosingElement() + "." + method.getSimpleName(), started)
                    .endControlFlow();
                return new ApplyResult.MethodBody(body.build());
            }
        }
    }
    ```

    The factory returns an aspect for the compilation. `getSupportedAnnotationClassNames()` maps it to `@LogDuration`. `apply()` creates a method body: start a monotonic timer, invoke the next layer once, then log in `finally`. The Java `void` branch emits a call rather than an invalid `return` of a value. The local timer name avoids collisions with method parameters.

    JavaPoet `$L`, `$S` and `$N` represent code, a string literal and a name. `ApplyResult.MethodBody` gives that body to Kora; it does not create the subclass itself. Register the factory in `duration-annotation-processor/src/main/resources/META-INF/services/io.koraframework.aop.annotation.processor.KoraAspectFactory`:

    ```text
    example.aspect.processor.LogDurationAspectFactory
    ```

=== ":simple-kotlin: `Kotlin`"

    <span id="kotlin-aspect"></span>

    Create `duration-symbol-processor/src/main/kotlin/example/aspect/processor/LogDurationAspectFactory.kt`:

    ```kotlin
    package example.aspect.processor

    import com.google.devtools.ksp.processing.Resolver
    import com.google.devtools.ksp.symbol.KSFunctionDeclaration
    import com.google.devtools.ksp.symbol.Modifier
    import com.squareup.kotlinpoet.CodeBlock
    import io.koraframework.aop.symbol.processor.KoraAspect
    import io.koraframework.aop.symbol.processor.KoraAspectFactory
    import io.koraframework.ksp.common.exception.ProcessingErrorException

    class LogDurationAspectFactory : KoraAspectFactory {
        override fun create(resolver: Resolver): KoraAspect = LogDurationAspect()
    }

    private class LogDurationAspect : KoraAspect {
        override fun getSupportedAnnotationTypes(): Set<String> = setOf("example.aspect.LogDuration")

        override fun apply(
            ksFunction: KSFunctionDeclaration,
            superCall: String,
            aspectContext: KoraAspect.AspectContext
        ): KoraAspect.ApplyResult {
            if (Modifier.SUSPEND in ksFunction.modifiers) {
                throw ProcessingErrorException("@LogDuration supports synchronous methods only", ksFunction)
            }
            val operation = ksFunction.parentDeclaration?.qualifiedName?.asString() + "." + ksFunction.simpleName.asString()
            val call = ksFunction.superCall(superCall)
            var started = "_logDurationStarted"
            val parameterNames = ksFunction.parameters.mapNotNull { it.name?.asString() }.toSet()
            while (started in parameterNames) started += "_"
            val body = CodeBlock.builder()
                .addStatement("val %N = System.nanoTime()", started)
                .beginControlFlow("try")
                .addStatement("return %L", call)
                .nextControlFlow("finally")
                .addStatement("org.slf4j.LoggerFactory.getLogger(%S).info(%S, %S, System.nanoTime() - %N)",
                    "example.aspect", "{} took {} ns", operation, started)
                .endControlFlow()
                .build()
            return KoraAspect.ApplyResult.MethodBody(body)
        }
    }
    ```

    Kotlin’s helper `ksFunction.superCall(superCall)` preserves the same next-layer contract. `return` of a `Unit` expression is valid Kotlin, so one branch handles both result-bearing and Unit methods. `ProcessingErrorException` attaches the unsupported `suspend` diagnostic to the method. KotlinPoet uses `%L`, `%S` and `%N` rather than JavaPoet’s dollar placeholders.

    Register the factory in `duration-symbol-processor/src/main/resources/META-INF/services/io.koraframework.aop.symbol.processor.KoraAspectFactory`:

    ```text
    example.aspect.processor.LogDurationAspectFactory
    ```

    Do not register it as a `SymbolProcessorProvider`: Kora’s standard KSP processor loads this factory. You do not write a new standalone processing round loop for an aspect.

## Connect the Application { #usage }

Add to the existing application dependencies, preserving Kora’s standard processor:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — build.gradle"

        ```groovy
        dependencies {
            // Keep existing Kora processor and runtime dependencies.
            implementation project(":duration-annotation")
            annotationProcessor project(":duration-annotation-processor")
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        dependencies {
            // Keep existing Kora processor and runtime dependencies.
            implementation(project(":duration-annotation"))
            annotationProcessor(project(":duration-annotation-processor"))
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    ===! "Groovy — build.gradle"

        ```groovy
        dependencies {
            // Keep existing Kora processor and runtime dependencies.
            implementation project(":duration-annotation")
            ksp project(":duration-symbol-processor")
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        dependencies {
            // Keep existing Kora processor and runtime dependencies.
            implementation(project(":duration-annotation"))
            ksp(project(":duration-symbol-processor"))
        }
        ```

Use the complete root below when starting from Getting Started. If continuing the Neo4j application, keep its additional modules on this root. Replace the old root, and update `mainClass` for
`example.app`:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/example/app/Application.java`:

    ===! ":material-code-json: `HOCON`"

        ```java
        package example.app;

        import io.koraframework.application.graph.KoraApplication;
        import io.koraframework.common.annotation.KoraApp;
        import io.koraframework.config.hocon.HoconConfigModule;
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
        import io.koraframework.logging.logback.LogbackModule;

        @KoraApp
        public interface Application extends HoconConfigModule, LogbackModule,
                UndertowPublicHttpServerModule {
            static void main(String[] args) {
                KoraApplication.run(ApplicationGraph::graph);
            }
        }
        ```

    === ":simple-yaml: `YAML`"

        ```java
        package example.app;

        import io.koraframework.application.graph.KoraApplication;
        import io.koraframework.common.annotation.KoraApp;
        import io.koraframework.config.yaml.YamlConfigModule;
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
        import io.koraframework.logging.logback.LogbackModule;

        @KoraApp
        public interface Application extends YamlConfigModule, LogbackModule,
                UndertowPublicHttpServerModule {
            static void main(String[] args) {
                KoraApplication.run(ApplicationGraph::graph);
            }
        }
        ```

    ===! "Groovy — build.gradle"

        ```groovy
        application {
            mainClass = "example.app.Application"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        application {
            mainClass.set("example.app.Application")
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/example/app/Application.kt`:

    ===! ":material-code-json: `HOCON`"

        ```kotlin
        package example.app

        import io.koraframework.application.graph.KoraApplication
        import io.koraframework.common.annotation.KoraApp
        import io.koraframework.config.hocon.HoconConfigModule
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
        import io.koraframework.logging.logback.LogbackModule

        @KoraApp
        interface Application : HoconConfigModule, LogbackModule, UndertowPublicHttpServerModule

        fun main() {
            KoraApplication.run(ApplicationGraph::graph)
        }
        ```

    === ":simple-yaml: `YAML`"

        ```kotlin
        package example.app

        import io.koraframework.application.graph.KoraApplication
        import io.koraframework.common.annotation.KoraApp
        import io.koraframework.config.yaml.YamlConfigModule
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
        import io.koraframework.logging.logback.LogbackModule

        @KoraApp
        interface Application : YamlConfigModule, LogbackModule, UndertowPublicHttpServerModule

        fun main() {
            KoraApplication.run(ApplicationGraph::graph)
        }
        ```

    ===! "Groovy — build.gradle"

        ```groovy
        application {
            mainClass = "example.app.ApplicationKt"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        application {
            mainClass.set("example.app.ApplicationKt")
        }
        ```

## Service { #service }

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/example/app/GreetingService.java`:

    ```java
    package example.app;

    import example.aspect.LogDuration;
    import io.koraframework.common.annotation.Component;

    @Component
    public class GreetingService {
        @LogDuration
        public String greet(String name) {
            return "Hello, " + name;
        }

        @LogDuration
        public void nothing() {}

        @LogDuration
        public String fail() {
            throw new IllegalStateException("expected");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/example/app/GreetingService.kt`:

    ```kotlin
    package example.app

    import example.aspect.LogDuration
    import io.koraframework.common.annotation.Component

    @Component
    open class GreetingService {
        @LogDuration
        open fun greet(name: String): String = "Hello, $name"

        @LogDuration
        open fun nothing() {}

        @LogDuration
        open fun fail(): String = throw IllegalStateException("expected")
    }
    ```

The service defines all three outcomes without logging code in its methods. Kotlin `open` permits subclass generation; the Java class and methods deliberately omit `final`. The component must be
reachable through the graph to be used by the application.

## Controller { #controller }

Replace the original `HelloController` rather than adding a second `/hello` route:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/example/app/HelloController.java`:

    ```java
    package example.app;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponse;

    @Component
    @HttpController
    public final class HelloController {
        private final GreetingService service;

        public HelloController(GreetingService service) {
            this.service = service;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        public HttpServerResponse hello() {
            return HttpServerResponse.of(200, HttpBody.plaintext(service.greet("Kora")));
        }

        @HttpRoute(method = HttpMethod.GET, path = "/duration/void")
        public HttpServerResponse nothing() {
            service.nothing();
            return HttpServerResponse.of(200, HttpBody.plaintext("done"));
        }

        @HttpRoute(method = HttpMethod.GET, path = "/duration/fail")
        public HttpServerResponse fail() {
            return HttpServerResponse.of(200, HttpBody.plaintext(service.fail()));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/example/app/HelloController.kt`:

    ```kotlin
    package example.app

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponse

    @Component
    @HttpController
    class HelloController(private val service: GreetingService) {
        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        fun hello(): HttpServerResponse =
            HttpServerResponse.of(200, HttpBody.plaintext(service.greet("Kora")))

        @HttpRoute(method = HttpMethod.GET, path = "/duration/void")
        fun nothing(): HttpServerResponse {
            service.nothing()
            return HttpServerResponse.of(200, HttpBody.plaintext("done"))
        }

        @HttpRoute(method = HttpMethod.GET, path = "/duration/fail")
        fun fail(): HttpServerResponse =
            HttpServerResponse.of(200, HttpBody.plaintext(service.fail()))
    }
    ```

Constructor injection ensures the controller receives the generated subclass. `/duration/void` proves a method without a value still runs; `/duration/fail` leaves the service exception on the normal
HTTP error path. The aspect does not convert errors into successful responses.

Choose one configuration format and add the matching resource:

===! ":material-code-json: `HOCON`"

    `src/main/resources/application.conf`:

    ```hocon
    httpServer.port = 8080
    httpServer.system.port = 8085
    logging.levels {
      "example.aspect" = "INFO"
    }
    ```

=== ":simple-yaml: `YAML`"

    `src/main/resources/application.yaml`:

    ```yaml
    httpServer:
      port: 8080
      system:
        port: 8085
    logging:
      levels:
            "example.aspect": "INFO"
    ```

The generated logger uses SLF4J directly, so its level follows [Kora logging configuration](../documentation/logging-slf4j.md). No JDK logging bridge is required by this aspect.

## Generated Aspect Code { #generated-code }

Inspect the generated subclass after compilation:

===! ":fontawesome-brands-java: `Java`"

    ```text
    build/generated/sources/annotationProcessor/java/main/example/app/$GreetingService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    build/generated/ksp/main/kotlin/example/app/$GreetingService__AopProxy.kt
    ```

For a single aspect the override has the following shape. This is a shortened illustration; Kora may introduce helper methods for aspect composition:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public String greet(String name) {
        long _logDurationStarted = System.nanoTime();
        try {
            return super.greet(name);
        } finally {
            org.slf4j.LoggerFactory.getLogger("example.aspect")
                .info("{} took {} ns", "example.app.GreetingService.greet",
                    System.nanoTime() - _logDurationStarted);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun greet(name: String): String {
        val _logDurationStarted = System.nanoTime()
        try {
            return super.greet(name)
        } finally {
            org.slf4j.LoggerFactory.getLogger("example.aspect")
                .info("{} took {} ns", "example.app.GreetingService.greet",
                    System.nanoTime() - _logDurationStarted)
        }
    }
    ```

Follow the generated `ApplicationGraph` factory: it should construct the subclass for the `GreetingService` dependency. The source makes the timing boundary, single invocation and exception
propagation visible. Edit the factory or service declaration when changing behavior, never this generated file.

## Run Application { #run-app }

===! "Bash"

    ```bash
    ./gradlew clean classes
    ./gradlew run
    ```

=== "PowerShell"

    ```powershell
    ./gradlew.bat clean classes
    ./gradlew.bat run
    ```

When continuing the Neo4j graph, start its database and set `NEO4J_PASSWORD` as in that guide. The standalone aspect graph needs neither.

## Check Application { #check-app }

Run in another terminal (`curl.exe` in PowerShell):

```shell
curl -i http://localhost:8080/hello
curl -i http://localhost:8080/duration/void
curl -i http://localhost:8080/duration/fail
```

| Route            | Expected response                              | Aspect observation                                                                                           |
|------------------|------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `/hello`         | `200`, `Hello, Kora`                           | One duration for `GreetingService.greet`                                                                     |
| `/duration/void` | `200`, `done`                                  | One duration for `GreetingService.nothing`                                                                   |
| `/duration/fail` | Server error (`500` with the baseline handler) | One duration for `GreetingService.fail`; original `IllegalStateException("expected")` reaches error handling |

Elapsed nanoseconds vary; a log entry has the shape `example.app.GreetingService.greet took ... ns`. HTTP error logging can produce additional entries, so count only messages from `example.aspect`. Do
not depend on an exact error body.

## Verify the Interception Contract { #verification }

Stop the app and temporarily make `GreetingService` final in Java, or remove `open` from the Kotlin class. Run `classes`: compilation must reject the non-overridable aspect target. Restore it. For
Kotlin, temporarily change `greet` to `open suspend fun`: the factory reports `@LogDuration supports synchronous methods only` (callers also need suspension handling). Restore the synchronous
signature.

In generated source, inspect all three methods: the next layer is called once, timing is in `finally`, and no catch replaces the original exception. If extending the aspect, add direct tests for
returned values, the same exception instance, void/Unit, parameter-name collisions and self-invocation. Instrumentation added in `finally` should not throw and mask application failures. Stop the
application with Ctrl+C after verification.

## Extending the Aspect { #next }

For injected telemetry, AP uses `context.fieldFactory().constructorParam(...)`; KSP uses `aspectContext.fieldFactory.constructorParam(...)`. Kora adds the returned field to the generated constructor
and resolves its type from the graph. `constructorInitialized(...)` creates a field initialized once by generated constructor code. Keep runtime telemetry in a normal module; processor code emits
calls instead of connecting to runtime services.

Mark a supporting annotation with `@AopPropagate` from `io.koraframework.common.annotation` when Kora generators must carry it onto generated methods or parameters. Examples include `@Log.off` and
`@Fallback.Reason`. Propagation does not activate an aspect: the main annotation still needs `@AopAnnotation` and a registered factory.

For multiple aspects, preserve `superCall` and inspect their actual generated order. The [Resilience combinations](../documentation/resilient.md#combination) show why wrapper ordering changes
behavior.

## Best Practices { #best-practices }

- Keep runtime annotations separate from compiler SPI dependencies.
- Preserve the supplied next-layer call and original method contract.
- Use `System.nanoTime()` for elapsed time, not wall-clock timestamps.
- Declare synchronous/async limits before promising completion metrics.
- Obtain the service through the graph and keep target methods overridable.
- Keep logging and telemetry non-throwing; verify aspect composition in generated code.

## Summary { #summary }

You created an annotation, registered a matching AP/KSP aspect factory, connected a graph-managed service and inspected its generated subclass. The HTTP checks demonstrate timing on return, void/Unit
and failure without changing the service’s business code.

## Key Concepts { #key-concepts }

- `@AopAnnotation` requests compile-time interception.
- `KoraAspectFactory` supplies behavior to Kora’s AOP processor.
- `ApplyResult.MethodBody` contributes a body, while Kora generates the class.
- `superCall` preserves the next layer in an aspect chain.
- `finally` covers return and throw, but synchronous timing ends at method return.
- Graph injection selects the generated subclass; direct construction bypasses it.

## Troubleshooting { #troubleshooting }

**No generated subclass**

Check `@AopAnnotation`, the exact factory service path inside the processor JAR, the matching `annotationProcessor`/`ksp` dependency and Kora’s standard processor. An ordinary provider registration is
not an aspect registration.

**Cannot generate an override**

Remove Java `final`, or add Kotlin `open` to class and method. Do not annotate private/static methods; use an accessible unambiguous constructor.

**The method runs without duration logging**

Inspect graph construction for the generated subclass, avoid manual `new GreetingService()` and check `example.aspect` at INFO. Confirm the route calls the annotated method.

**Async duration looks too short**

This factory times only synchronous invocation. An async return needs completion-aware instrumentation; `suspend` is deliberately rejected.

## What's Next? { #whats-next }

- Use [Observability](observability.md) to turn this log-only example into injected telemetry.
- Review [Resilience](resilient.md) for real aspect composition.
- Use [Component Testing](testing-junit.md) to exercise services through the generated graph.

## Help { #help }

Check [DI documentation](../documentation/container.md) for graph resolution and [logging](../documentation/logging-slf4j.md) for logger configuration. The framework sources define
the [Java aspect SPI](https://github.com/kora-projects/kora/tree/master/aop/aop-annotation-processor/src/main/java/io/koraframework/aop/annotation/processor)
and [Kotlin aspect SPI](https://github.com/kora-projects/kora/tree/master/aop/aop-symbol-processor/src/main/kotlin/io/koraframework/aop/symbol/processor); match them to your pinned Kora version before
extending the example.
