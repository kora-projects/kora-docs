---
seo_title: "AP and KSP: Generate a DTO Builder | Kora"
seo_description: "Create @GenerateBuilder for Java records and Kotlin data classes with Kora processor bases, JavaPoet/KotlinPoet and generated-code checks."
keywords: [ "Kora Framework", "GenerateBuilder", "AbstractKoraProcessor", "BaseSymbolProcessor", "JavaPoet", "KotlinPoet", "DTO builder" ]
search:
    exclude: true
title: "AP and KSP: Generate a DTO Builder"
summary: "Create @GenerateBuilder for Java records and Kotlin data classes with Kora processor bases, JavaPoet/KotlinPoet and generated-code checks."
description: "Use this guide for a small Kora-style source generator: @GenerateBuilder, AbstractKoraProcessor and annotatedElements, BaseSymbolProcessor and processRound/validateAll, JavaPoet/KotlinPoet DTO builders, service registration, originating elements/files, isolating AP/KSP output, required fields, boxed primitive state, diagnostics and independent Groovy/Kotlin DSL setup."
agent:
    use_when: "Use this guide for a small Kora-style source generator: @GenerateBuilder, AbstractKoraProcessor and annotatedElements, BaseSymbolProcessor and processRound/validateAll, JavaPoet/KotlinPoet DTO builders, service registration, originating elements/files, isolating AP/KSP output, required fields, boxed primitive state, diagnostics and independent Groovy/Kotlin DSL setup."
tags: "integration, ap, ksp, code-generation"
---

# AP and KSP: Generate a DTO Builder { #integration-processors }

This guide implements a small source generator: `@GenerateBuilder` produces a fluent builder for an immutable DTO. You will read the DTO structure, generate typed setters and a constructor call, and
report unsupported input during compilation. The Java and Kotlin implementations use the same processor foundations as Kora itself.

## What You'll Build { #youll-build }

- A shared `@GenerateBuilder` annotation artifact
- A Java processor based on `AbstractKoraProcessor` and a Kotlin processor based on `BaseSymbolProcessor`
- `CreateUserBuilder` with `name(...)`, `email(...)` and `build()`
- A runnable console example, diagnostics and incremental metadata

## What You'll Need { #youll-need }

- JDK 25 or later, Gradle 9+ Wrapper and an editor
- Kotlin `2.4.20` and KSP `2.3.12` for the Kotlin branch
- Kora `2.0.0.RC2` processor-common artifacts
- Familiarity with Java records or Kotlin data classes

## Prerequisites { #prerequisites }

!!! note "An independent processor example"

    Use [Getting Started](getting-started.md) for JDK and Wrapper setup. Create a separate project for this guide and choose Java or Kotlin application sources. The complete build scripts below configure a console application.

The [Neo4j module](integration-neo4j.md) shows ordinary runtime wiring; this example teaches source generation independently. No running application graph or external infrastructure is required.
Commands run from the new project root.

## Overview { #overview }

A DTO with several constructor parameters is easy to build positionally, but named builder calls make call sites readable when several fields have the same type. The processor removes repetitive
builder code while preserving the DTO’s declared field types. Adding a field changes the generated API on the next compilation.

### Runtime and processor artifacts { #artifact-roles }

`builder-annotation` contains only the annotation. The application depends on it through `implementation`; compiler helpers belong only to `builder-annotation-processor` or `builder-symbol-processor`.
The generated builder is an ordinary object created at the call site. It needs neither `@Component` nor a graph node.

### The Kora processor pattern { #processing-rounds }

Java extends `AbstractKoraProcessor`, declares supported `ClassName` values and receives grouped `AnnotatedElement` inputs. Kotlin extends `BaseSymbolProcessor`, implements `processRound` and defers
unresolved symbols through `validateAll`. Both validate the model, create a Poet type and attach diagnostics to the input declaration. Service entries make the compiler discover the processors.

### Supported models and required fields { #supported-contract }

Java supports public top-level non-generic records in named packages with at least one component. Kotlin supports public top-level non-generic data classes with a public primary constructor and
required, non-null `val` parameters. Kotlin `var`, nullable, default-valued and vararg constructor parameters are rejected. A Java record component `Object equals` is also rejected: its fluent setter
would collide with `Object.equals(Object)`. The diagnostic points to the component instead of an invalid generated file.

Every builder field is required. In Java, reference fields cannot be null when `build()` runs; primitive state is boxed internally so an unset `int` is distinguishable from an explicitly supplied `0`.
Kotlin uses nullable private state and `requireNotNull` before construction. This is the builder contract; Java’s direct record constructor remains unchanged.

## Annotation and DTO { #annotation }

===! ":fontawesome-brands-java: `Java`"

    Create `builder-annotation/src/main/java/example/builder/GenerateBuilder.java`:

    ```java
    package example.builder;

    import java.lang.annotation.ElementType;
    import java.lang.annotation.Retention;
    import java.lang.annotation.RetentionPolicy;
    import java.lang.annotation.Target;

    @Target(ElementType.TYPE)
    @Retention(RetentionPolicy.CLASS)
    public @interface GenerateBuilder {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `builder-annotation/src/main/kotlin/example/builder/GenerateBuilder.kt`:

    ```kotlin
    package example.builder

    @Target(AnnotationTarget.CLASS)
    @Retention(AnnotationRetention.BINARY)
    annotation class GenerateBuilder
    ```

`CLASS` / `BINARY` retention supports compile-time discovery and the isolating AP contract. Declare the DTO:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/example/app/CreateUser.java`:

    ```java
    package example.app;

    import example.builder.GenerateBuilder;

    @GenerateBuilder
    public record CreateUser(String name, String email) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/example/app/CreateUser.kt`:

    ```kotlin
    package example.app

    import example.builder.GenerateBuilder

    @GenerateBuilder
    data class CreateUser(val name: String, val email: String)
    ```

## Dependencies and Project Layout { #processor-projects }

Select the application source language, then choose one Gradle DSL. The source language and script language are independent; save only one build script per project.

Root settings:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — settings.gradle"

        ```groovy
        rootProject.name = "builder-guide"
        include("builder-annotation", "builder-annotation-processor")
        ```

    === "Kotlin DSL — settings.gradle.kts"

        ```kotlin
        rootProject.name = "builder-guide"
        include("builder-annotation", "builder-annotation-processor")
        ```

=== ":simple-kotlin: `Kotlin`"

    ===! "Groovy — settings.gradle"

        ```groovy
        rootProject.name = "builder-guide"
        include("builder-annotation", "builder-symbol-processor")
        ```

    === "Kotlin DSL — settings.gradle.kts"

        ```kotlin
        rootProject.name = "builder-guide"
        include("builder-annotation", "builder-symbol-processor")
        ```

Root application build:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — build.gradle"

        ```groovy
        plugins { id 'application' }
        repositories { mavenCentral() }
        java { toolchain { languageVersion = JavaLanguageVersion.of(25) } }
        dependencies {
            implementation project(":builder-annotation")
            annotationProcessor project(":builder-annotation-processor")
        }
        application { mainClass = "example.app.BuilderDemo" }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins { id("application") }
        repositories { mavenCentral() }
        java { toolchain { languageVersion.set(JavaLanguageVersion.of(25)) } }
        dependencies {
            implementation(project(":builder-annotation"))
            annotationProcessor(project(":builder-annotation-processor"))
        }
        application { mainClass.set("example.app.BuilderDemo") }
        ```

=== ":simple-kotlin: `Kotlin`"

    ===! "Groovy — build.gradle"

        ```groovy
        plugins {
            id 'org.jetbrains.kotlin.jvm' version '2.4.20'
            id 'com.google.devtools.ksp' version '2.3.12'
            id 'application'
        }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        dependencies {
            implementation project(":builder-annotation")
            ksp project(":builder-symbol-processor")
        }
        application { mainClass = "example.app.BuilderDemoKt" }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins {
            kotlin("jvm") version "2.4.20"
            id("com.google.devtools.ksp") version "2.3.12"
            application
        }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        dependencies {
            implementation(project(":builder-annotation"))
            ksp(project(":builder-symbol-processor"))
        }
        application { mainClass.set("example.app.BuilderDemoKt") }
        ```

Configure `builder-annotation`:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — build.gradle"

        ```groovy
        plugins { id 'java-library' }
        repositories { mavenCentral() }
        java { toolchain { languageVersion = JavaLanguageVersion.of(25) } }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins { id("java-library") }
        repositories { mavenCentral() }
        java { toolchain { languageVersion.set(JavaLanguageVersion.of(25)) } }
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
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins {
            id("java-library")
            id("org.jetbrains.kotlin.jvm") version "2.4.20"
        }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        ```

Configure the matching processor project:

===! ":fontawesome-brands-java: `Java`"

    `builder-annotation-processor/`:

    ===! "Groovy — build.gradle"

        ```groovy
        plugins { id 'java-library' }
        repositories { mavenCentral() }
        java { toolchain { languageVersion = JavaLanguageVersion.of(25) } }
        dependencies {
            implementation platform("io.koraframework:kora-bom:2.0.0.RC2")
            implementation "io.koraframework:annotation-processor-common"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins { id("java-library") }
        repositories { mavenCentral() }
        java { toolchain { languageVersion.set(JavaLanguageVersion.of(25)) } }
        dependencies {
            implementation(platform("io.koraframework:kora-bom:2.0.0.RC2"))
            implementation("io.koraframework:annotation-processor-common")
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    `builder-symbol-processor/`:

    ===! "Groovy — build.gradle"

        ```groovy
        plugins { id 'org.jetbrains.kotlin.jvm' }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        dependencies {
            implementation platform("io.koraframework:kora-bom:2.0.0.RC2")
            implementation "io.koraframework:symbol-processor-common"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins { kotlin("jvm") }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        dependencies {
            implementation(platform("io.koraframework:kora-bom:2.0.0.RC2"))
            implementation("io.koraframework:symbol-processor-common")
        }
        ```

The Kotlin processor uses the plugin version already declared at the root. `annotation-processor-common` provides `AbstractKoraProcessor`, errors, helpers and Palantir JavaPoet;
`symbol-processor-common` provides the Kotlin base, errors, KSP and KotlinPoet APIs. Their versions come from the Kora BOM. The custom processor does not load the annotation class: it matches its
qualified name, so no project dependency on `builder-annotation` is needed in the processor.

```text
settings.gradle[.kts]
build.gradle[.kts]
builder-annotation/
  build.gradle[.kts]
  src/main/java/example/builder/GenerateBuilder.java       # Java branch
  src/main/kotlin/example/builder/GenerateBuilder.kt       # Kotlin branch
builder-annotation-processor/                 # Java branch
  build.gradle[.kts]
  src/main/java/example/builder/processor/GenerateBuilderProcessor.java
  src/main/resources/META-INF/services/javax.annotation.processing.Processor
  src/main/resources/META-INF/gradle/incremental.annotation.processors
builder-symbol-processor/                     # Kotlin branch
  build.gradle[.kts]
  src/main/kotlin/example/builder/processor/GenerateBuilderProvider.kt
  src/main/resources/META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider
```

## Builder Processor { #processor }

The two tabs implement the same transformation: DTO fields → private state → typed fluent setters → constructor call. Each implementation validates input before writing a file.

===! ":fontawesome-brands-java: `Java`"

    <span id="java-ap"></span>

    Create `builder-annotation-processor/src/main/java/example/builder/processor/GenerateBuilderProcessor.java`:

    ```java
    package example.builder.processor;

    import com.palantir.javapoet.ClassName;
    import com.palantir.javapoet.CodeBlock;
    import com.palantir.javapoet.FieldSpec;
    import com.palantir.javapoet.JavaFile;
    import com.palantir.javapoet.MethodSpec;
    import com.palantir.javapoet.TypeName;
    import com.palantir.javapoet.TypeSpec;
    import io.koraframework.annotation.processor.common.AbstractKoraProcessor;
    import io.koraframework.annotation.processor.common.CommonUtils;
    import io.koraframework.annotation.processor.common.ProcessingErrorException;
    import java.util.HashSet;
    import java.util.List;
    import java.util.Map;
    import java.util.Objects;
    import java.util.Set;
    import javax.annotation.processing.RoundEnvironment;
    import javax.lang.model.element.ElementKind;
    import javax.lang.model.element.Modifier;
    import javax.lang.model.element.NestingKind;
    import javax.lang.model.element.TypeElement;

    public final class GenerateBuilderProcessor extends AbstractKoraProcessor {
        private static final ClassName ANNOTATION =
            ClassName.get("example.builder", "GenerateBuilder");
        private final Set<String> generated = new HashSet<>();

        @Override
        public Set<ClassName> getSupportedAnnotationClassNames() {
            return Set.of(ANNOTATION);
        }

        @Override
        protected void process(Set<? extends TypeElement> annotations,
                               RoundEnvironment round,
                               Map<ClassName, List<AnnotatedElement>> annotatedElements) {
            if (round.processingOver() || round.errorRaised()) return;
            for (var annotated : annotatedElements.getOrDefault(ANNOTATION, List.of())) {
                try {
                    if (!(annotated.element() instanceof TypeElement type)
                        || type.getKind() != ElementKind.RECORD
                        || type.getNestingKind() != NestingKind.TOP_LEVEL
                        || !type.getModifiers().contains(Modifier.PUBLIC)
                        || !type.getTypeParameters().isEmpty()
                        || elements.getPackageOf(type).isUnnamed()
                        || type.getRecordComponents().isEmpty()) {
                        throw new ProcessingErrorException(
                            "@GenerateBuilder requires a public top-level non-generic record with fields",
                            annotated.element());
                    }
                    for (var field : type.getRecordComponents()) {
                        if (field.getSimpleName().contentEquals("equals")
                            && types.isSameType(field.asType(), elements.getTypeElement("java.lang.Object").asType())) {
                            throw new ProcessingErrorException(
                                "Field 'equals' of type Object conflicts with Object.equals(Object)", field);
                        }
                    }
                    var name = type.getQualifiedName().toString();
                    if (generated.contains(name)) continue;
                    CommonUtils.safeWriteTo(processingEnv, generateBuilder(type));
                    generated.add(name);
                } catch (ProcessingErrorException e) {
                    e.printError(processingEnv);
                }
            }
        }

        private JavaFile generateBuilder(TypeElement type) {
            var packageName = elements.getPackageOf(type).getQualifiedName().toString();
            var builderType = ClassName.get(packageName, type.getSimpleName() + "Builder");
            var builder = TypeSpec.classBuilder(builderType)
                .addModifiers(Modifier.PUBLIC, Modifier.FINAL)
                .addOriginatingElement(type)
                .addMethod(MethodSpec.constructorBuilder().addModifiers(Modifier.PUBLIC).build());
            var construction = CodeBlock.builder().add("return new $T(", ClassName.get(type));
            var fields = type.getRecordComponents();
            for (int i = 0; i < fields.size(); i++) {
                var field = fields.get(i);
                var fieldName = field.getSimpleName().toString();
                var fieldType = TypeName.get(field.asType());
                builder.addField(FieldSpec.builder(fieldType.box(), fieldName, Modifier.PRIVATE).build());
                builder.addMethod(MethodSpec.methodBuilder(fieldName)
                    .addModifiers(Modifier.PUBLIC)
                    .returns(builderType)
                    .addParameter(fieldType, "value")
                    .addStatement("this.$N = value", fieldName)
                    .addStatement("return this")
                    .build());
                if (i > 0) construction.add(", ");
                construction.add("$T.requireNonNull(this.$N, $S)", Objects.class, fieldName, fieldName);
            }
            construction.add(");\n");
            builder.addMethod(MethodSpec.methodBuilder("build")
                .addModifiers(Modifier.PUBLIC)
                .returns(ClassName.get(type))
                .addCode(construction.build())
                .build());
            return JavaFile.builder(packageName, builder.build()).build();
        }
    }
    ```

    `AbstractKoraProcessor` owns `init`, supported annotation names and the standard processing entry point. Our override receives the grouped inputs, just as Kora’s `HttpClientAnnotationProcessor` does. `ProcessingErrorException.printError` reports invalid DTOs at their declarations.

    `generateBuilder` uses `TypeSpec`, `FieldSpec`, `MethodSpec` and typed placeholders. `box()` keeps primitive fields unset until a setter is called. `addOriginatingElement(type)` links output to the record, and `CommonUtils.safeWriteTo` writes through the compiler Filer. The generated-name set is updated after successful writing.

=== ":simple-kotlin: `Kotlin`"

    <span id="kotlin-ksp"></span>

    Create `builder-symbol-processor/src/main/kotlin/example/builder/processor/GenerateBuilderProvider.kt`:

    ```kotlin
    package example.builder.processor

    import com.google.devtools.ksp.isPublic
    import com.google.devtools.ksp.processing.Resolver
    import com.google.devtools.ksp.processing.SymbolProcessor
    import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
    import com.google.devtools.ksp.processing.SymbolProcessorProvider
    import com.google.devtools.ksp.symbol.ClassKind
    import com.google.devtools.ksp.symbol.KSAnnotated
    import com.google.devtools.ksp.symbol.KSClassDeclaration
    import com.google.devtools.ksp.symbol.Modifier
    import com.google.devtools.ksp.symbol.Nullability
    import com.google.devtools.ksp.symbol.Origin
    import com.squareup.kotlinpoet.ClassName
    import com.squareup.kotlinpoet.CodeBlock
    import com.squareup.kotlinpoet.FileSpec
    import com.squareup.kotlinpoet.FunSpec
    import com.squareup.kotlinpoet.KModifier
    import com.squareup.kotlinpoet.PropertySpec
    import com.squareup.kotlinpoet.TypeSpec
    import com.squareup.kotlinpoet.ksp.toClassName
    import com.squareup.kotlinpoet.ksp.addOriginatingKSFile
    import com.squareup.kotlinpoet.ksp.toTypeName
    import com.squareup.kotlinpoet.ksp.writeTo
    import io.koraframework.ksp.common.BaseSymbolProcessor
    import io.koraframework.ksp.common.exception.ProcessingErrorException

    class GenerateBuilderProvider : SymbolProcessorProvider {
        override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
            GenerateBuilderProcessor(environment)
    }

    private class GenerateBuilderProcessor(
        private val environment: SymbolProcessorEnvironment
    ) : BaseSymbolProcessor(environment) {
        private val generated = mutableSetOf<String>()

        override fun processRound(resolver: Resolver): List<KSAnnotated> {
            val deferred = mutableListOf<KSAnnotated>()
            for (symbol in resolver.getSymbolsWithAnnotation("example.builder.GenerateBuilder")) {
                if (!symbol.validateAll()) {
                    deferred += symbol
                    continue
                }
                try {
                    val type = symbol as? KSClassDeclaration
                    val constructor = type?.primaryConstructor
                    if (type == null || type.classKind != ClassKind.CLASS
                        || type.origin != Origin.KOTLIN || Modifier.DATA !in type.modifiers
                        || !type.isPublic() || type.parentDeclaration != null
                        || type.typeParameters.isNotEmpty() || type.packageName.asString().isEmpty()
                        || type.containingFile == null || constructor == null || !constructor.isPublic()
                        || constructor.parameters.isEmpty()
                        || constructor.parameters.any {
                            !it.isVal || it.isVararg || it.hasDefault
                                || it.type.resolve().nullability != Nullability.NOT_NULL
                        }) {
                        throw ProcessingErrorException(
                            "@GenerateBuilder requires a public top-level non-generic data class with required non-null val parameters",
                            symbol)
                    }
                    val name = type.qualifiedName!!.asString()
                    if (name in generated) continue
                    generateBuilder(type).writeTo(environment.codeGenerator, aggregating = false)
                    generated += name
                } catch (e: ProcessingErrorException) {
                    e.printError(kspLogger)
                }
            }
            return deferred
        }

        private fun generateBuilder(type: KSClassDeclaration): FileSpec {
            val packageName = type.packageName.asString()
            val builderType = ClassName(packageName, type.simpleName.asString() + "Builder")
            val modelType = type.toClassName()
            val builder = TypeSpec.classBuilder(builderType)
                .primaryConstructor(FunSpec.constructorBuilder().build())
                .addOriginatingKSFile(requireNotNull(type.containingFile))
            val construction = CodeBlock.builder().add("return %T(\n", modelType).indent()
            for (parameter in requireNotNull(type.primaryConstructor).parameters) {
                val name = requireNotNull(parameter.name).asString()
                val parameterType = parameter.type.toTypeName()
                builder.addProperty(PropertySpec.builder(name, parameterType.copy(nullable = true), KModifier.PRIVATE)
                    .mutable().initializer("null").build())
                builder.addFunction(FunSpec.builder(name)
                    .addParameter("value", parameterType)
                    .returns(builderType)
                    .addStatement("this.%N = value", name)
                    .addStatement("return this")
                    .build())
                construction.add("%N = kotlin.requireNotNull(this.%N) { %S },\n", name, name, name)
            }
            construction.unindent().add(")\n")
            builder.addFunction(FunSpec.builder("build")
                .returns(modelType).addCode(construction.build()).build())
            return FileSpec.builder(packageName, builderType.simpleName).addType(builder.build()).build()
        }
    }
    ```

    The provider supplies the environment to `BaseSymbolProcessor`. The base owns the standard `process` and finish/error lifecycle; our implementation supplies `processRound`. `validateAll` returns unresolved symbols for a later round, while resolved unsupported models get immediate diagnostics.

    KotlinPoet escapes names and retains field types. `addOriginatingKSFile` supplies the input file, and `writeTo(..., aggregating = false)` emits isolating output. Required constructor parameters become nullable private state, then `kotlin.requireNotNull` checks them before DTO construction.

## Register the Processor { #registration }

===! ":fontawesome-brands-java: `Java`"

    Create `builder-annotation-processor/src/main/resources/META-INF/services/javax.annotation.processing.Processor`:

    ```text
    example.builder.processor.GenerateBuilderProcessor
    ```

    Also create `builder-annotation-processor/src/main/resources/META-INF/gradle/incremental.annotation.processors`:

    ```text
    example.builder.processor.GenerateBuilderProcessor,isolating
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `builder-symbol-processor/src/main/resources/META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider`:

    ```text
    example.builder.processor.GenerateBuilderProvider
    ```

One output file depends on one DTO. Java needs both its originating element and Gradle metadata; KSP derives dependencies from the originating file passed through KotlinPoet. Neither registration
belongs in the runtime annotation JAR. The Kora base class does not register your processor automatically.

## Use the Generated Builder { #usage }

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/example/app/BuilderDemo.java`:

    ```java
    package example.app;

    public final class BuilderDemo {
        public static void main(String[] args) {
            var request = new CreateUserBuilder()
                .name("Anton")
                .email("anton@example.com")
                .build();
            System.out.println(request);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/example/app/BuilderDemo.kt`:

    ```kotlin
    package example.app

    fun main() {
        val request = CreateUserBuilder()
            .name("Anton")
            .email("anton@example.com")
            .build()
        println(request)
    }
    ```

The compiler generates the referenced builder during the same build. The console application consumes it directly; adding Kora’s application-graph processor is only necessary when your application
also declares a Kora graph.

## Generated Builder Code { #generated-code }

After compilation inspect the output below. Imports and formatting can differ; the fields, setter types and constructor arguments must match the DTO.

===! ":fontawesome-brands-java: `Java`"

    `build/generated/sources/annotationProcessor/java/main/example/app/CreateUserBuilder.java`:

    ```java
    package example.app;

    import java.util.Objects;

    public final class CreateUserBuilder {
        private String name;
        private String email;

        public CreateUserBuilder() {}

        public CreateUserBuilder name(String value) {
            this.name = value;
            return this;
        }

        public CreateUserBuilder email(String value) {
            this.email = value;
            return this;
        }

        public CreateUser build() {
            return new CreateUser(
                Objects.requireNonNull(this.name, "name"),
                Objects.requireNonNull(this.email, "email"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `build/generated/ksp/main/kotlin/example/app/CreateUserBuilder.kt`:

    ```kotlin
    package example.app

    class CreateUserBuilder {
        private var name: String? = null
        private var email: String? = null

        fun name(value: String): CreateUserBuilder {
            this.name = value
            return this
        }

        fun email(value: String): CreateUserBuilder {
            this.email = value
            return this
        }

        fun build(): CreateUser = CreateUser(
            name = kotlin.requireNotNull(this.name) { "name" },
            email = kotlin.requireNotNull(this.email) { "email" },
        )
    }
    ```

The only model-specific content is derived from the input DTO. Rename or add a field and its setter and constructor argument are regenerated. Never edit these output files manually.

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

## Check Application { #check-app }

Expected console output:

===! ":fontawesome-brands-java: `Java`"

    ```text
    CreateUser[name=Anton, email=anton@example.com]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    CreateUser(name=Anton, email=anton@example.com)
    ```

Remove `.email(...)` from the demo and run again. Construction must fail with a missing `email`: Java throws `NullPointerException("email")`; Kotlin throws `IllegalArgumentException("email")`. Restore
the setter. `build()` creates a new DTO each time and does not reset the builder, so changed values apply to subsequent builds.

## Verify Diagnostics and Regeneration { #verification }

Temporarily replace the supported model with:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @GenerateBuilder
    public class CreateUser {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @GenerateBuilder
    data class CreateUser(val name: String, val email: String = "")
    ```

Run `classes`. The build must fail at the model declaration with the matching diagnostic:

===! ":fontawesome-brands-java: `Java`"

    ```text
    @GenerateBuilder requires a public top-level non-generic record with fields
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    @GenerateBuilder requires a public top-level non-generic data class with required non-null val parameters
    ```

Restore the DTO, add a required `int age` / `val age: Int`, and add `.age(0)` to the demo. The generated builder must accept the explicit zero and reject a missing age. Run `classes` without `clean`
and inspect the regenerated setter and constructor call. Remove the annotation: a remaining `CreateUserBuilder` call should stop compiling, rather than using stale generated output. Restore the
annotation and finish with a clean build.

Build `:builder-annotation-processor:jar` or `:builder-symbol-processor:jar` and use `jar tf` on the resulting JAR to check the service path. For AP also verify the incremental metadata file.

## Best Practices { #best-practices }

- Derive source from model types and names through Poet APIs.
- Validate supported shapes before creating output files.
- Use Kora’s base lifecycle, grouped Java inputs and Kotlin deferral correctly.
- Keep compiler dependencies off the application runtime classpath.
- Track one originating declaration per builder and verify output compilation.
- Test missing values, explicit primitive defaults, diagnostics and regeneration.

## Summary { #summary }

You implemented the same DTO-to-builder transformation with Kora-style AP and KSP processors. The generated API is useful at normal call sites and remains tied to the DTO’s declared structure.
Registration and originating metadata make it part of the build.

## Key Concepts { #key-concepts }

- `AbstractKoraProcessor` receives grouped annotated Java elements.
- `BaseSymbolProcessor` supplies lifecycle around Kotlin `processRound`.
- JavaPoet/KotlinPoet retain field types and escape names.
- An originating declaration links each builder to its model.
- Generated objects need a DI component only when their role requires one.

## Troubleshooting { #troubleshooting }

**No generated builder**

Check the annotation’s package, service entry inside the processor JAR and the application’s `annotationProcessor` or `ksp` dependency. A runtime `implementation` dependency does not run a processor.

**Compiler APIs are missing while compiling the processor**

Use the matching Kora processor-common artifact and BOM. The runtime annotation project contains no compiler helpers.

**The builder rejects the model**

Read the contract diagnostic. Java needs a public non-generic record; Kotlin needs a public data class with required non-null val parameters. Unsupported shapes are intentionally rejected.

**`build()` fails although the code compiles**

Set every required field, including primitive fields. Missing values are runtime builder-state errors; setter type mismatches are compile-time errors.

**A renamed or removed model leaves old output**

Check originating metadata and service packaging, then clean once. Do not keep handwritten copies of generated builders.

## What's Next? { #whats-next }

Use [Creating a Kora Aspect](integration-aspect.md) to contribute an existing method’s body through `KoraAspectFactory`. Ordinary AP/KSP generators and aspect factories use different registration
SPIs. For runtime integration ownership, return to the [Neo4j module guide](integration-neo4j.md).

## Help { #help }

Compare the Java processor structure with Kora’s `HttpClientAnnotationProcessor` and the Kotlin structure with `HttpClientSymbolProcessor`. The
framework’s [processor-common sources](https://github.com/kora-projects/kora/tree/master/core) define the base APIs; use sources matching the pinned
version. [KSP documentation](https://kotlinlang.org/docs/ksp-overview.html) explains symbols, rounds and incremental output.
