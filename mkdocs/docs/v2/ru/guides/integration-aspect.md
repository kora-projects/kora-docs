---
seo_title: "Создание аспекта Kora | Kora"
seo_description: "Создайте @LogDuration через фабрики аспектов AP/KSP Kora, изучите подкласс и проверьте результат, void/Unit и исключения."
keywords: [ "Kora Framework", "AOP", "KoraAspectFactory", "LogDuration", "JavaPoet", "KotlinPoet", "создание аспекта" ]
search:
    exclude: true
title: "Создание аспекта Kora"
summary: "Создайте @LogDuration через фабрики аспектов AP/KSP Kora, изучите подкласс и проверьте результат, void/Unit и исключения."
description: "Руководство по синхронному AOP Kora 2.0: @AopAnnotation, CLASS/BINARY retention, HOCON/YAML, раздельные артефакты аннотации и обработчика, регистрации KoraAspectFactory Java/Kotlin, Palantir JavaPoet и KotlinPoet, callSuper и цепочка аспектов, ApplyResult.MethodBody, измерение try/finally, SLF4J, внедрение из графа, пути AopProxy, ограничения open/final, отклонение suspend, @AopPropagate и fieldFactory."
agent:
    use_when: "Руководство по синхронному AOP Kora 2.0: @AopAnnotation, CLASS/BINARY retention, HOCON/YAML, раздельные артефакты аннотации и обработчика, регистрации KoraAspectFactory Java/Kotlin, Palantir JavaPoet и KotlinPoet, callSuper и цепочка аспектов, ApplyResult.MethodBody, измерение try/finally, SLF4J, внедрение из графа, пути AopProxy, ограничения open/final, отклонение suspend, @AopPropagate и fieldFactory."
tags: "integration, aop, ap, ksp, logging"
---

# Создание аспекта Kora { #integration-aspect }

В этом руководстве вы создадите `@LogDuration` — аннотацию для измерения синхронного вызова метода. Вы предоставите тело метода через SPI аспектов Kora, поручите Kora генерацию подкласса и проверите
поведение обычного результата, `void`/`Unit` и исключения. Сгенерированный код использует SLF4J из существующей зависимости журналирования приложения.

## Что вы создадите { #youll-build }

- Runtime-аннотацию с `@AopAnnotation`
- Фабрики аспектов Java AP и Kotlin KSP с корректной регистрацией
- `GreetingService` с результатом, без результата и с ошибкой
- HTTP-маршруты, вызывающие сервис из графа
- Сгенерированный подкласс с одним вызовом следующего слоя и записью длительности в `finally`

## Что потребуется { #youll-need }

- JDK 25 или новее, Gradle Wrapper 9+ и IDE или редактор
- HTTP-приложение из [вводного руководства](getting-started.md)
- Kora `2.0.0.RC2` в runtime и classpath обработчиков
- Kotlin `2.4.20` и KSP `2.3.12` для ветки Kotlin
- Знакомство с [AP и KSP](integration-processors.md) и просмотром генерации

Для этого самостоятельного примера БД и Docker не нужны.

## Требования { #prerequisites }

!!! note "Обязательно: рабочее приложение /hello"

    Сохраните плагин application, зависимости HTTP, выбранного backend HOCON/YAML и журналирования и обработчик Kora. Замените контроллер полным примером ниже. Руководство по обработчикам объясняет разделение build-time/runtime на `@GenerateBuilder`; аспект использует отдельный SPI.

Для Java выберите фабрику AP, для Kotlin — KSP. Все команды выполняются из корня проекта приложения.

## Обзор { #overview }

Аспект добавляет поведение вокруг метода без изменения его прикладного кода. `@LogDuration` записывает длительность в наносекундах и при возврате, и при исключении. Это пример перехвата при
компиляции; для production-метрик обычно нужна внедряемая телеметрия, а не запись на каждый вызов.

### Подкласс, переопределение и граф { #subclass-graph }

Kora генерирует подкласс аннотированного сервиса и переопределяет метод. Когда контроллер запрашивает `GreetingService`, граф предоставляет этот подкласс. Перехват не использует runtime-прокси на
основе рефлексии: его код виден в сгенерированных исходниках. Прямое создание базового сервиса обходит этот код.

Классы и методы должны допускать переопределение. Java `final`, private и static не перехватываются переопределением; Kotlin требует `open` и у класса, и у метода. Виртуальный вызов аннотированного
метода из другого метода того же объекта тоже попадает в сгенерированное переопределение.

### Фабрики аспектов и обычные обработчики { #aspect-spi }

В [руководстве по builder](integration-processors.md) обычный `Processor` или `SymbolProcessorProvider` регистрируется для генерации новых типов. Здесь существующий AOP-обработчик Kora загружает
`KoraAspectFactory`, узнаёт поддерживаемые аннотации и запрашивает тело метода. Сгенерированный класс, конструктор, параметры и подключение к графу остаются ответственностью Kora.

`superCall` обозначает следующий слой. При нескольких аспектах это может быть другая сгенерированная оболочка, а не исходный метод. Сохраняйте вызов через предусмотренный helper вместо жёстко
заданного `super.greet(...)`.

### Граница измерения { #measurement-boundary }

Таймер охватывает синхронный вызов до возврата или исключения. Возврат future, publisher или другого отложенного значения завершает измерение раньше завершения операции. Kotlin `suspend` этот аспект
отклоняет. Для async completion нужна отдельная реализация с другим контрактом времени жизни.

Порядок действий: раздельные артефакты, аннотация, реализация и регистрация фабрики, сервис и контроллер, затем просмотр и проверка подкласса.

## Зависимости и структура проекта { #projects }

Добавьте проект аннотации и соответствующий проект обработчика в корневой settings:

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

Настройте `duration-annotation` в любом Gradle DSL. Выберите язык исходников аннотации независимо от Gradle DSL:

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

Настройте проект Java-обработчика `duration-annotation-processor`:

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

Настройте проект Kotlin-обработчика `duration-symbol-processor`:

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

Не повторяйте версию Kotlin-плагина, если она уже объявлена в корне. Артефакты AOP предоставляют SPI Kora и транзитивные API JavaPoet/KotlinPoet. Java использует `com.palantir.javapoet`, а не старый
пакет. Эти compiler-зависимости остаются в classpath обработчика. Приложение уже получает SLF4J через `logging-logback`.

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

### Формат конфигурации { #configuration-format }

Оставьте в приложении один backend конфигурации. HOCON использует `config-hocon`, `HoconConfigModule` и `application.conf`; YAML — `config-yaml`, `YamlConfigModule` и `application.yaml`. Замените
baseline-зависимость конфигурации на выбранную. Полные корни ниже показывают оба варианта модуля.

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

## Аннотация { #annotation }

===! ":fontawesome-brands-java: `Java`"

    Создайте `duration-annotation/src/main/java/example/aspect/LogDuration.java`:

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

    Создайте `duration-annotation/src/main/kotlin/example/aspect/LogDuration.kt`:

    ```kotlin
    package example.aspect

    import io.koraframework.common.annotation.AopAnnotation

    @AopAnnotation
    @Target(AnnotationTarget.FUNCTION)
    @Retention(AnnotationRetention.BINARY)
    annotation class LogDuration
    ```

`@AopAnnotation` сообщает Kora, что аннотация запрашивает перехват. Target только на метод явно задаёт область примера. Политики `CLASS` / `BINARY` достаточно для обработки при компиляции;
runtime-поиск не требуется. Сама аннотация не реализует аспект: поведение предоставляет зарегистрированная фабрика.

## Фабрика аспекта { #aspect-factory }

===! ":fontawesome-brands-java: `Java`"

    <span id="java-aspect"></span>

    Создайте `duration-annotation-processor/src/main/java/example/aspect/processor/LogDurationAspectFactory.java`:

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

    Фабрика возвращает аспект для компиляции. `getSupportedAnnotationClassNames()` связывает его с `@LogDuration`. `apply()` создаёт тело метода: запускает монотонный таймер, вызывает следующий слой один раз и записывает длительность в `finally`. Ветка Java `void` генерирует вызов без некорректного возврата значения. Имя таймера не конфликтует с параметрами метода.

    Подстановки JavaPoet `$L`, `$S` и `$N` обозначают код, строковый литерал и имя. `ApplyResult.MethodBody` передаёт тело Kora, но не создаёт подкласс самостоятельно. Зарегистрируйте фабрику в `duration-annotation-processor/src/main/resources/META-INF/services/io.koraframework.aop.annotation.processor.KoraAspectFactory`:

    ```text
    example.aspect.processor.LogDurationAspectFactory
    ```

=== ":simple-kotlin: `Kotlin`"

    <span id="kotlin-aspect"></span>

    Создайте `duration-symbol-processor/src/main/kotlin/example/aspect/processor/LogDurationAspectFactory.kt`:

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

    Helper `ksFunction.superCall(superCall)` сохраняет тот же контракт следующего слоя. Kotlin допускает `return` выражения `Unit`, поэтому одна ветка обрабатывает и результат, и Unit. `ProcessingErrorException` привязывает диагностику неподдерживаемого `suspend` к методу. KotlinPoet использует `%L`, `%S` и `%N` вместо подстановок JavaPoet с долларом.

    Зарегистрируйте фабрику в `duration-symbol-processor/src/main/resources/META-INF/services/io.koraframework.aop.symbol.processor.KoraAspectFactory`:

    ```text
    example.aspect.processor.LogDurationAspectFactory
    ```

    Не регистрируйте её как `SymbolProcessorProvider`: эту фабрику загружает стандартный KSP-обработчик Kora. Для аспекта не нужен собственный цикл раундов обработки.

## Подключение приложения { #usage }

Добавьте в существующие зависимости приложения, сохранив стандартный обработчик Kora:

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

Если вы начали с вводного руководства, используйте полный корень ниже. Если продолжаете приложение Neo4j, сохраните его дополнительные модули в этом корне. Замените прежний корень и обновите
`mainClass` для `example.app`:

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

## Сервис { #service }

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

Сервис задаёт три исхода без кода журналирования в методах. Kotlin `open` разрешает генерацию подкласса; у Java-класса и методов намеренно нет `final`. Приложение использует компонент, когда он
достижим из графа.

## Контроллер { #controller }

Замените исходный `HelloController`, не добавляйте второй маршрут `/hello`:

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

Внедрение через конструктор гарантирует получение сгенерированного подкласса. `/duration/void` показывает выполнение метода без значения; `/duration/fail` оставляет исключение сервиса в обычном пути
HTTP-ошибки. Аспект не превращает ошибки в успешные ответы.

Выберите один формат конфигурации и добавьте соответствующий ресурс:

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

Сгенерированный logger использует SLF4J напрямую, поэтому уровень задаётся [конфигурацией журналирования Kora](../documentation/logging-slf4j.md). Самому аспекту bridge JDK logging не требуется.

## Сгенерированный код аспекта { #generated-code }

После компиляции откройте сгенерированный подкласс:

===! ":fontawesome-brands-java: `Java`"

    ```text
    build/generated/sources/annotationProcessor/java/main/example/app/$GreetingService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    build/generated/ksp/main/kotlin/example/app/$GreetingService__AopProxy.kt
    ```

При одном аспекте переопределение имеет следующую форму. Это сокращённая иллюстрация; для цепочки аспектов Kora может вводить вспомогательные методы:

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

Найдите фабрику в `ApplicationGraph`: для зависимости `GreetingService` она должна создавать подкласс. Исходник показывает границу измерения, единственный вызов и передачу исключения. Для изменения
поведения редактируйте фабрику аспекта или исходный сервис, а не этот файл.

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

Если продолжаете граф Neo4j, запустите БД и задайте `NEO4J_PASSWORD` по предыдущему руководству. Самостоятельному графу аспекта они не нужны.

## Проверка приложения { #check-app }

В другом терминале выполните (`curl.exe` в PowerShell):

```shell
curl -i http://localhost:8080/hello
curl -i http://localhost:8080/duration/void
curl -i http://localhost:8080/duration/fail
```

| Маршрут          | Ожидаемый ответ                                  | Наблюдение аспекта                                                                                                     |
|------------------|--------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|
| `/hello`         | `200`, `Hello, Kora`                             | Одна длительность для `GreetingService.greet`                                                                          |
| `/duration/void` | `200`, `done`                                    | Одна длительность для `GreetingService.nothing`                                                                        |
| `/duration/fail` | Серверная ошибка (`500` с исходным обработчиком) | Одна длительность для `GreetingService.fail`; исходное `IllegalStateException("expected")` доходит до обработки ошибки |

Длительность меняется; запись имеет вид `example.app.GreetingService.greet took ... ns`. HTTP-обработка ошибки может создать дополнительные записи, поэтому считайте только сообщения `example.aspect`.
Не полагайтесь на точное тело ошибки.

## Проверка контракта перехвата { #verification }

Остановите приложение и временно сделайте `GreetingService` final в Java или уберите `open` у Kotlin-класса. Выполните `classes`: компиляция должна отвергнуть непереопределяемую цель аспекта.
Восстановите объявление. В Kotlin временно замените `greet` на `open suspend fun`: фабрика сообщает `@LogDuration supports synchronous methods only` (вызывающему коду тоже понадобится обработка
suspension). Верните синхронную сигнатуру.

Проверьте три сгенерированных метода: следующий слой вызывается один раз, измерение находится в `finally`, а catch не заменяет исходное исключение. При расширении аспекта добавьте прямые тесты
возвращаемых значений, идентичности исключения, void/Unit, конфликтов имён параметров и self-invocation. Телеметрия в `finally` не должна бросать исключения и скрывать прикладную ошибку. После
проверки остановите приложение через Ctrl+C.

## Расширение аспекта { #next }

Для внедрения телеметрии AP использует `context.fieldFactory().constructorParam(...)`, KSP — `aspectContext.fieldFactory.constructorParam(...)`. Kora добавляет поле в сгенерированный конструктор и
разрешает тип из графа. `constructorInitialized(...)` создаёт поле, инициализируемое один раз кодом конструктора. Runtime-телеметрия остаётся в обычном модуле; обработчик генерирует вызовы, а не
подключается к runtime-сервисам.

Помечайте вспомогательную аннотацию `@AopPropagate` из `io.koraframework.common.annotation`, если генераторы Kora должны перенести её на методы или параметры. Примеры — `@Log.off` и
`@Fallback.Reason`. Перенос не активирует аспект: основной аннотации по-прежнему нужны `@AopAnnotation` и зарегистрированная фабрика.

При нескольких аспектах сохраняйте `superCall` и смотрите фактический порядок генерации. [Комбинации отказоустойчивости](../documentation/resilient.md#combination) показывают, почему порядок оболочек
меняет поведение.

## Лучшие практики { #best-practices }

- Отделяйте runtime-аннотации от зависимостей compiler SPI.
- Сохраняйте переданный вызов следующего слоя и исходный контракт метода.
- Используйте `System.nanoTime()` для длительности, а не календарное время.
- Объявляйте синхронные и async-границы до обещания метрик завершения.
- Получайте сервис из графа и оставляйте методы переопределяемыми.
- Не допускайте исключений в журналировании и телеметрии; проверяйте цепочку аспектов в генерации.

## Итоги { #summary }

Вы создали аннотацию, зарегистрировали фабрику AP/KSP, подключили управляемый графом сервис и изучили подкласс. HTTP-проверки показывают измерение при возврате, void/Unit и ошибке без изменения
прикладного кода сервиса.

## Ключевые понятия { #key-concepts }

- `@AopAnnotation` запрашивает перехват при компиляции.
- `KoraAspectFactory` предоставляет поведение AOP-обработчику Kora.
- `ApplyResult.MethodBody` задаёт тело; класс генерирует Kora.
- `superCall` сохраняет следующий слой цепочки аспектов.
- `finally` охватывает возврат и исключение; синхронный таймер заканчивается при возврате.
- Граф выбирает подкласс; прямой конструктор его обходит.

## Устранение неполадок { #troubleshooting }

**Подкласс не сгенерирован**

Проверьте `@AopAnnotation`, точный service path фабрики в JAR обработчика, зависимость `annotationProcessor`/`ksp` и стандартный обработчик Kora. Регистрация обычного provider не является регистрацией
аспекта.

**Невозможно переопределить метод**

Уберите Java `final` или добавьте Kotlin `open` классу и методу. Не аннотируйте private/static; используйте доступный однозначный конструктор.

**Метод выполняется без записи длительности**

Найдите создание подкласса в графе, исключите ручной `new GreetingService()` и проверьте INFO для `example.aspect`. Убедитесь, что маршрут вызывает аннотированный метод.

**Async-длительность слишком короткая**

Фабрика измеряет только синхронный вызов. Для async-результата нужен перехват завершения; `suspend` намеренно отвергается.

## Что дальше? { #whats-next }

- Используйте [наблюдаемость](observability.md), чтобы заменить учебное журналирование внедряемой телеметрией.
- Изучите [отказоустойчивость](resilient.md) для реальной композиции аспектов.
- Используйте [компонентное тестирование](testing-junit.md) для проверки сервисов через сгенерированный граф.

## Помощь { #help }

Проверьте [документацию DI](../documentation/container.md) для разрешения графа и [журналирование](../documentation/logging-slf4j.md) для настройки logger. В исходниках фреймворка
определены [Java SPI аспектов](https://github.com/kora-projects/kora/tree/master/aop/aop-annotation-processor/src/main/java/io/koraframework/aop/annotation/processor)
и [Kotlin SPI аспектов](https://github.com/kora-projects/kora/tree/master/aop/aop-symbol-processor/src/main/kotlin/io/koraframework/aop/symbol/processor); перед расширением примера сверяйте их с
зафиксированной версией Kora.
