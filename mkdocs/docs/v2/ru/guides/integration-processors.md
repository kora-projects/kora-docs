---
seo_title: "AP и KSP: генерация builder для DTO | Kora"
seo_description: "Создайте @GenerateBuilder для Java record и Kotlin data class через базовые обработчики Kora, JavaPoet/KotlinPoet и проверку сгенерированного кода."
keywords: [ "Kora Framework", "GenerateBuilder", "AbstractKoraProcessor", "BaseSymbolProcessor", "JavaPoet", "KotlinPoet", "builder для DTO" ]
search:
    exclude: true
title: "AP и KSP: генерация builder для DTO"
summary: "Создайте @GenerateBuilder для Java record и Kotlin data class через базовые обработчики Kora, JavaPoet/KotlinPoet и проверку сгенерированного кода."
description: "Руководство по небольшому генератору в стиле Kora: @GenerateBuilder, AbstractKoraProcessor и annotatedElements, BaseSymbolProcessor и processRound/validateAll, builder DTO через JavaPoet/KotlinPoet, регистрация сервисов, originating elements/files, изолирующий AP/KSP вывод, обязательные поля, boxed primitive state, диагностики и настройка Groovy/Kotlin DSL."
agent:
    use_when: "Руководство по небольшому генератору в стиле Kora: @GenerateBuilder, AbstractKoraProcessor и annotatedElements, BaseSymbolProcessor и processRound/validateAll, builder DTO через JavaPoet/KotlinPoet, регистрация сервисов, originating elements/files, изолирующий AP/KSP вывод, обязательные поля, boxed primitive state, диагностики и настройка Groovy/Kotlin DSL."
tags: "integration, ap, ksp, code-generation"
---

# AP и KSP: генерация builder для DTO { #integration-processors }

В этом руководстве вы реализуете небольшой генератор: `@GenerateBuilder` создаёт fluent builder для immutable DTO. Вы прочитаете структуру DTO, сгенерируете типизированные методы и вызов конструктора
и выдадите диагностику неподдерживаемого ввода при компиляции. Реализации Java и Kotlin используют те же базовые обработчики, что и сама Kora.

## Что вы создадите { #youll-build }

- Общий артефакт аннотации `@GenerateBuilder`
- Java-обработчик на `AbstractKoraProcessor` и Kotlin-обработчик на `BaseSymbolProcessor`
- `CreateUserBuilder` с методами `name(...)`, `email(...)` и `build()`
- Запускаемый консольный пример, диагностики и инкрементальные метаданные

## Что потребуется { #youll-need }

- JDK 25 или новее, Gradle Wrapper 9+ и редактор
- Kotlin `2.4.20` и KSP `2.3.12` для ветки Kotlin
- Артефакты processor-common Kora `2.0.0.RC2`
- Знакомство с Java record или Kotlin data class

## Требования { #prerequisites }

!!! note "Самостоятельный пример обработчика"

    Используйте [вводное руководство](getting-started.md) для настройки JDK и Wrapper. Создайте отдельный проект и выберите Java или Kotlin для исходников приложения. Полные скрипты ниже настраивают консольное приложение.

[Модуль Neo4j](integration-neo4j.md) показывает обычное runtime-подключение; этот пример отдельно обучает генерации исходников. Работающий граф и внешняя инфраструктура не требуются. Команды
выполняются из корня нового проекта.

## Обзор { #overview }

При нескольких параметрах одного типа именованные вызовы builder делают место создания DTO понятнее позиционного конструктора. Обработчик убирает повторяющийся код builder, сохраняя объявленные типы
полей DTO. Новое поле меняет сгенерированный API при следующей компиляции.

### Runtime и артефакты обработчиков { #artifact-roles }

`builder-annotation` содержит только аннотацию. Приложение подключает её через `implementation`; compiler helpers принадлежат только `builder-annotation-processor` или `builder-symbol-processor`.
Builder — обычный объект, создаваемый в месте использования. Ему не нужны `@Component` и узел графа.

### Подход обработчиков Kora { #processing-rounds }

Java наследует `AbstractKoraProcessor`, объявляет поддерживаемые `ClassName` и получает сгруппированные `AnnotatedElement`. Kotlin наследует `BaseSymbolProcessor`, реализует `processRound` и
откладывает неразрешённые символы через `validateAll`. Оба обработчика проверяют модель, создают тип через Poet и привязывают диагностики к исходному объявлению. Service entries позволяют компилятору
обнаружить обработчики.

### Поддерживаемые модели и обязательные поля { #supported-contract }

Java поддерживает публичные record верхнего уровня в именованном пакете, без параметров типов, с хотя бы одним компонентом. Kotlin поддерживает публичные data class верхнего уровня без параметров
типов, с публичным primary constructor и обязательными non-null `val` параметрами. Kotlin `var`, nullable, default-valued и vararg параметры отвергаются. Компонент Java record `Object equals` также
отвергается: его fluent setter конфликтовал бы с `Object.equals(Object)`. Диагностика указывает на компонент, а не на некорректный сгенерированный файл.

Все поля builder обязательны. В Java ссылочные поля не могут быть null при `build()`; примитивное состояние хранится в boxed-типе, поэтому незаданный `int` отличается от явно переданного `0`. В Kotlin
используется nullable private state и `requireNotNull` перед созданием DTO. Это контракт builder; прямой конструктор Java record не меняется.

## Аннотация и DTO { #annotation }

===! ":fontawesome-brands-java: `Java`"

    Создайте `builder-annotation/src/main/java/example/builder/GenerateBuilder.java`:

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

    Создайте `builder-annotation/src/main/kotlin/example/builder/GenerateBuilder.kt`:

    ```kotlin
    package example.builder

    @Target(AnnotationTarget.CLASS)
    @Retention(AnnotationRetention.BINARY)
    annotation class GenerateBuilder
    ```

Политика `CLASS` / `BINARY` подходит для обнаружения при компиляции и контракта изолирующего AP. Объявите DTO:

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

## Зависимости и структура проекта { #processor-projects }

Выберите язык исходников приложения, затем один Gradle DSL. Язык исходников и скрипта независимы; в каждом проекте сохраняйте только один скрипт сборки.

Корневой settings:

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

Корневой скрипт приложения:

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

Настройте `builder-annotation`:

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

Настройте соответствующий проект обработчика:

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

Kotlin-обработчик использует версию плагина, объявленную в корне. `annotation-processor-common` предоставляет `AbstractKoraProcessor`, ошибки, helpers и Palantir JavaPoet; `symbol-processor-common` —
Kotlin base, ошибки, KSP и KotlinPoet API. Версии задаёт BOM Kora. Обработчик не загружает класс аннотации: он сравнивает полное имя, поэтому зависимость проекта обработчика от `builder-annotation` не
нужна.

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

## Обработчик builder { #processor }

Обе вкладки реализуют одно преобразование: поля DTO → private state → типизированные fluent-методы → вызов конструктора. Каждая реализация проверяет ввод до записи файла.

===! ":fontawesome-brands-java: `Java`"

    <span id="java-ap"></span>

    Создайте `builder-annotation-processor/src/main/java/example/builder/processor/GenerateBuilderProcessor.java`:

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

    `AbstractKoraProcessor` отвечает за `init`, имена поддерживаемых аннотаций и стандартную точку обработки. Наш override получает сгруппированный ввод, как `HttpClientAnnotationProcessor` в Kora. `ProcessingErrorException.printError` сообщает о некорректном DTO на его объявлении.

    `generateBuilder` использует `TypeSpec`, `FieldSpec`, `MethodSpec` и типизированные подстановки. `box()` сохраняет состояние примитива незаданным до вызова setter. `addOriginatingElement(type)` связывает результат с record, а `CommonUtils.safeWriteTo` записывает его через compiler Filer. Набор созданных имён обновляется после успешной записи.

=== ":simple-kotlin: `Kotlin`"

    <span id="kotlin-ksp"></span>

    Создайте `builder-symbol-processor/src/main/kotlin/example/builder/processor/GenerateBuilderProvider.kt`:

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

    Provider передаёт environment в `BaseSymbolProcessor`. Базовый класс управляет стандартным `process` и lifecycle finish/error; наша реализация задаёт `processRound`. `validateAll` возвращает неразрешённые символы для следующего раунда, а разрешённые неподдерживаемые модели сразу получают диагностику.

    KotlinPoet экранирует имена и сохраняет типы полей. `addOriginatingKSFile` задаёт входной файл, `writeTo(..., aggregating = false)` создаёт изолирующий вывод. Обязательные параметры конструктора превращаются в nullable private state, а `kotlin.requireNotNull` проверяет их до создания DTO.

## Регистрация обработчика { #registration }

===! ":fontawesome-brands-java: `Java`"

    Создайте `builder-annotation-processor/src/main/resources/META-INF/services/javax.annotation.processing.Processor`:

    ```text
    example.builder.processor.GenerateBuilderProcessor
    ```

    Также создайте `builder-annotation-processor/src/main/resources/META-INF/gradle/incremental.annotation.processors`:

    ```text
    example.builder.processor.GenerateBuilderProcessor,isolating
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `builder-symbol-processor/src/main/resources/META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider`:

    ```text
    example.builder.processor.GenerateBuilderProvider
    ```

Один выходной файл зависит от одного DTO. Java нужны originating element и метаданные Gradle; KSP получает зависимости из originating file, переданного через KotlinPoet. Регистрация не помещается в
runtime-JAR аннотации. Базовый класс Kora не регистрирует ваш обработчик автоматически.

## Использование сгенерированного builder { #usage }

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

Компилятор создаёт используемый builder в той же сборке. Консольное приложение обращается к нему напрямую; обработчик application graph Kora нужен только тогда, когда приложение также объявляет граф
Kora.

## Сгенерированный код builder { #generated-code }

После компиляции проверьте результат ниже. Импорты и форматирование могут отличаться; поля, типы setter и аргументы конструктора должны соответствовать DTO.

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

Всё содержимое, связанное с конкретной моделью, выводится из DTO. Переименуйте или добавьте поле — его setter и аргумент конструктора будут пересозданы. Не редактируйте выходные файлы вручную.

## Запуск приложения { #run-app }

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

## Проверка приложения { #check-app }

Ожидаемый вывод:

===! ":fontawesome-brands-java: `Java`"

    ```text
    CreateUser[name=Anton, email=anton@example.com]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    CreateUser(name=Anton, email=anton@example.com)
    ```

Уберите `.email(...)` из примера и запустите его снова. Создание должно завершиться ошибкой отсутствующего `email`: Java бросает `NullPointerException("email")`, Kotlin —
`IllegalArgumentException("email")`. Верните setter. `build()` каждый раз создаёт новый DTO и не сбрасывает builder, поэтому изменение значения влияет на последующие создания.

## Проверка диагностик и повторной генерации { #verification }

Временно замените поддерживаемую модель на:

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

Выполните `classes`. Сборка должна завершиться ошибкой на объявлении модели с соответствующей диагностикой:

===! ":fontawesome-brands-java: `Java`"

    ```text
    @GenerateBuilder requires a public top-level non-generic record with fields
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    @GenerateBuilder requires a public top-level non-generic data class with required non-null val parameters
    ```

Восстановите DTO, добавьте обязательный `int age` / `val age: Int` и `.age(0)` в пример. Builder должен принять явный ноль и отвергнуть незаданный age. Выполните `classes` без `clean` и проверьте
пересозданные setter и вызов конструктора. Уберите аннотацию: оставшийся вызов `CreateUserBuilder` должен перестать компилироваться, а не использовать устаревшую генерацию. Верните аннотацию и
завершите чистой сборкой.

Соберите `:builder-annotation-processor:jar` или `:builder-symbol-processor:jar` и проверьте service path через `jar tf`. Для AP также проверьте incremental metadata.

## Лучшие практики { #best-practices }

- Выводите код из типов и имён модели через Poet API.
- Проверяйте поддерживаемую форму до создания файлов.
- Правильно используйте lifecycle базовых классов Kora, сгруппированный Java-ввод и отложенные Kotlin-символы.
- Не включайте compiler-зависимости в runtime приложения.
- Связывайте builder с одним исходным объявлением и проверяйте компиляцию результата.
- Проверяйте отсутствующие значения, явный ноль, диагностики и повторную генерацию.

## Итоги { #summary }

Вы реализовали одно преобразование DTO в builder через AP и KSP в стиле Kora. Полученный API используется в обычном прикладном коде и соответствует объявленной структуре DTO. Регистрация и originating
metadata подключают генерацию к сборке.

## Ключевые понятия { #key-concepts }

- `AbstractKoraProcessor` получает сгруппированные аннотированные Java elements.
- `BaseSymbolProcessor` организует lifecycle вокруг Kotlin `processRound`.
- JavaPoet/KotlinPoet сохраняют типы полей и экранируют имена.
- Originating declaration связывает builder с моделью.
- DI-компонент нужен сгенерированному объекту только тогда, когда этого требует его роль.

## Устранение неполадок { #troubleshooting }

**Builder не сгенерирован**

Проверьте пакет аннотации, service entry внутри JAR обработчика и зависимость приложения `annotationProcessor` или `ksp`. Runtime-зависимость `implementation` не запускает обработчик.

**При сборке обработчика не найдены compiler API**

Используйте соответствующий processor-common артефакт Kora и BOM. Runtime-проект аннотации не содержит compiler helpers.

**Builder отвергает модель**

Прочитайте диагностику контракта. Java требует публичный non-generic record; Kotlin — публичную data class с обязательными non-null val параметрами. Неподдерживаемая форма намеренно отвергается.

**`build()` падает, хотя код компилируется**

Задайте все обязательные поля, включая примитивы. Отсутствующие значения — runtime-ошибки состояния builder; несовпадение типов setter — ошибка компиляции.

**После переименования или удаления модели остаётся старый файл**

Проверьте originating metadata и упаковку сервисов, затем выполните clean. Не храните рукописные копии сгенерированных builder.

## Что дальше? { #whats-next }

Перейдите к [созданию аспекта Kora](integration-aspect.md), чтобы предоставить тело существующего метода через `KoraAspectFactory`. Обычные генераторы AP/KSP и фабрики аспектов используют разные SPI
регистрации. Управление runtime-интеграцией показано в [руководстве модуля Neo4j](integration-neo4j.md).

## Помощь { #help }

Сравните структуру Java с `HttpClientAnnotationProcessor` Kora, Kotlin — с `HttpClientSymbolProcessor`. Базовые API находятся
в [исходниках processor-common](https://github.com/kora-projects/kora/tree/master/core); сверяйтесь с зафиксированной версией. [Документация KSP](https://kotlinlang.org/docs/ksp-overview.html)
объясняет символы, раунды и инкрементальный вывод.
