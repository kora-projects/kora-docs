---
seo_title: "Создание модуля интеграции с Neo4j | Kora"
seo_description: "Создайте клиент Neo4j с конфигурацией, жизненным циклом, метриками и трассировкой Kora и вызовите его из HTTP на Java или Kotlin."
keywords: [ "Kora Framework", "Neo4j", "создание интеграции", "Lifecycle", "ConfigSource", "метрики", "трассировка" ]
search:
    exclude: true
title: "Создание модуля интеграции с Neo4j"
summary: "Создайте клиент Neo4j с конфигурацией, жизненным циклом, метриками и трассировкой Kora и вызовите его из HTTP на Java или Kotlin."
description: "Руководство по библиотеке Neo4j для Kora 2.0: библиотека Java/Kotlin и kora-bom, AP/KSP, HOCON/YAML, @ConfigSource, таймауты Duration, Lifecycle init/release, владение Driver и Session, повторы executeWrite, параметризованный MERGE, фабрики Neo4jModule, MetricsModule, OpentelemetryTracingModule, контекст ScopedValue, PUT /people/{name}, Docker healthcheck, ограничение уникальности, сгенерированная конфигурация и проверка ошибок."
agent:
    use_when: "Руководство по библиотеке Neo4j для Kora 2.0: библиотека Java/Kotlin и kora-bom, AP/KSP, HOCON/YAML, @ConfigSource, таймауты Duration, Lifecycle init/release, владение Driver и Session, повторы executeWrite, параметризованный MERGE, фабрики Neo4jModule, MetricsModule, OpentelemetryTracingModule, контекст ScopedValue, PUT /people/{name}, Docker healthcheck, ограничение уникальности, сгенерированная конфигурация и проверка ошибок."
tags: "integration, neo4j, lifecycle, telemetry"
---

# Создание модуля интеграции с Neo4j { #neo4j-integration }

В этом руководстве вы превратите сторонний драйвер Java в переиспользуемый модуль Kora. Вы подключите конфигурацию, управление ресурсами и телеметрию к графу приложения, затем проверите запись в БД
через HTTP. Выберите Java или Kotlin для библиотеки интеграции и приложения; обе ветки реализуют одинаковые контракты конфигурации, жизненного цикла и телеметрии.

## Что вы создадите { #youll-build }

- Библиотеку `neo4j-integration` с типизированной конфигурацией и управляемым жизненным циклом клиента
- Модуль фабрик, подключающий клиент к графу при компиляции
- Метрики длительности, span операции и журналирование ошибок
- `PUT /people/{name}`, который создаёт человека или находит существующего и возвращает имя
- Локальную БД с ограничением уникальности и воспроизводимой проверкой

## Что потребуется { #youll-need }

- JDK 25 или новее и Gradle Wrapper 9+
- Рабочее приложение из [вводного руководства](getting-started.md)
- Docker с Compose v2, поддерживающим `up --wait`
- IDE или редактор и базовое знакомство с Cypher

Используйте BOM Kora `2.0.0.RC2` из исходного приложения. Для Kotlin сохраняются Kotlin `2.4.20` и KSP `2.3.12`; Kotlin-библиотека использует KSP для генерации типизированной конфигурации.

## Требования { #prerequisites }

!!! note "Обязательно: рабочее HTTP-приложение"

    Сначала пройдите [вводное руководство](getting-started.md). Сохраните плагин application, обработчики Kora и зависимости HTTP-сервера, выбранного backend HOCON/YAML и Logback. Это руководство добавляет к приложению библиотечный подпроект.

О фабриках модулей читайте в [руководстве по DI](dependency-injection.md), о метриках и трассировке — в [обзоре наблюдаемости](observability.md). Все команды ниже выполняются из корня проекта
приложения.

## Обзор { #overview }

Интеграция — граница между внешней библиотекой и приложением. Neo4j отвечает за сетевой протокол и транзакции; Kora — за конфигурацию, создание, запуск и остановку клиента. Прикладной код зависит от
`Neo4jClient`, а не создаёт драйверы и не читает переменные окружения.

### Конфигурация и граф { #configuration-graph }

`@ConfigSource("neo4j")` генерирует реализацию конфигурации, mapper и модуль фабрики. `Neo4jModule` предоставляет остальные фабрики. Параметры задают связи графа: клиент зависит от конфигурации и
телеметрии, контроллер — от клиента. Обычных фабрик достаточно; собственный генератор AP/KSP — отдельное необязательное удобство.

### Владение ресурсами { #resource-ownership }

Один потокобезопасный `Driver` владеет пулом соединений. Сессия принадлежит одной операции; результат транзакции нужно прочитать до закрытия сессии. Kora вызывает `init()` до обслуживания запросов и
`release()` при остановке графа. Прямой вызов конструктора вне графа не организует этот жизненный цикл.

### Телеметрия операции { #operation-telemetry }

Измерение охватывает всю операцию `savePerson`, включая получение соединения и повторы управляемой транзакции. На вызов записываются один исход и один дочерний span. Пример не измеряет каждый запрос и
не предоставляет статистику пула драйвера. HTTP-обработчик выполняется синхронно на виртуальном потоке, поэтому блокирующий API драйвера здесь подходит.

Порядок действий: библиотека, генерация конфигурации, телеметрия и жизненный цикл, фабрики, корень графа, HTTP, затем проверка данных и наблюдаемости.

## Зависимости и структура проекта { #project }

Добавьте `include("neo4j-integration")` в корневой `settings.gradle` или `settings.gradle.kts`. Настройте `neo4j-integration/build.gradle` или `neo4j-integration/build.gradle.kts`:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — build.gradle"

        ```groovy
        plugins { id 'java-library' }
        repositories { mavenCentral() }
        java { toolchain { languageVersion = JavaLanguageVersion.of(25) } }
        dependencies {
            annotationProcessor platform("io.koraframework:kora-bom:2.0.0.RC2")
            annotationProcessor "io.koraframework:annotation-processors"
            api platform("io.koraframework:kora-bom:2.0.0.RC2")
            api "io.koraframework:common"
            api "io.koraframework:config-common"
            api "io.koraframework:application-graph"
            api "io.koraframework:micrometer-module"
            api "io.koraframework:opentelemetry-tracing"
            implementation "org.neo4j.driver:neo4j-java-driver:6.1.0"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins { id("java-library") }
        repositories { mavenCentral() }
        java { toolchain { languageVersion.set(JavaLanguageVersion.of(25)) } }
        dependencies {
            annotationProcessor(platform("io.koraframework:kora-bom:2.0.0.RC2"))
            annotationProcessor("io.koraframework:annotation-processors")
            api(platform("io.koraframework:kora-bom:2.0.0.RC2"))
            api("io.koraframework:common")
            api("io.koraframework:config-common")
            api("io.koraframework:application-graph")
            api("io.koraframework:micrometer-module")
            api("io.koraframework:opentelemetry-tracing")
            implementation("org.neo4j.driver:neo4j-java-driver:6.1.0")
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    ===! "Groovy — build.gradle"

        ```groovy
        plugins {
            id 'java-library'
            id 'org.jetbrains.kotlin.jvm' version '2.4.20'
            id 'com.google.devtools.ksp' version '2.3.12'
        }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        dependencies {
            ksp "io.koraframework:symbol-processors:2.0.0.RC2"
            api platform("io.koraframework:kora-bom:2.0.0.RC2")
            api "io.koraframework:common"
            api "io.koraframework:config-common"
            api "io.koraframework:application-graph"
            api "io.koraframework:micrometer-module"
            api "io.koraframework:opentelemetry-tracing"
            implementation "org.neo4j.driver:neo4j-java-driver:6.1.0"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins {
            id("java-library")
            id("org.jetbrains.kotlin.jvm") version "2.4.20"
            id("com.google.devtools.ksp") version "2.3.12"
        }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        dependencies {
            ksp("io.koraframework:symbol-processors:2.0.0.RC2")
            api(platform("io.koraframework:kora-bom:2.0.0.RC2"))
            api("io.koraframework:common")
            api("io.koraframework:config-common")
            api("io.koraframework:application-graph")
            api("io.koraframework:micrometer-module")
            api("io.koraframework:opentelemetry-tracing")
            implementation("org.neo4j.driver:neo4j-java-driver:6.1.0")
        }
        ```

Выберите язык исходников библиотеки, затем один Gradle DSL. Java использует AP, Kotlin — KSP. Согласуйте версии Kotlin/KSP с корнем и не повторяйте версии плагинов, уже объявленные там. Язык
исходников и Gradle DSL независимы. `api` открывает типы Kora из публичных сигнатур; `implementation` оставляет драйвер Neo4j за оболочкой клиента. Совместимость с сервером описана
в [руководстве драйвера](https://neo4j.com/docs/java-manual/current/install/).

Добавьте runtime-проект в существующие зависимости приложения:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — build.gradle"

        ```groovy
        dependencies {
            // Keep existing Kora dependencies.
            implementation project(":neo4j-integration")
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        dependencies {
            // Keep existing Kora dependencies.
            implementation(project(":neo4j-integration"))
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    ===! "Groovy — build.gradle"

        ```groovy
        dependencies {
            // Keep existing Kora dependencies.
            implementation project(":neo4j-integration")
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        dependencies {
            // Keep existing Kora dependencies.
            implementation(project(":neo4j-integration"))
        }
        ```

Java-файлы библиотеки находятся в `neo4j-integration/src/main/java/example/neo4j/`, Kotlin-файлы — в `neo4j-integration/src/main/kotlin/example/neo4j/`. Создавайте одну версию каждого типа согласно
выбранной ветке. Файлы приложения используют `example.app`.

```text
settings.gradle[.kts]
build.gradle[.kts]
compose.yaml
neo4j-integration/
  build.gradle[.kts]
  src/main/java/example/neo4j/
    Neo4jConfig.java
    Neo4jTelemetry.java
    Neo4jClient.java
    Neo4jModule.java
  src/main/kotlin/example/neo4j/                # Kotlin library branch
    Neo4jConfig.kt
    Neo4jTelemetry.kt
    Neo4jClient.kt
    Neo4jModule.kt
src/main/resources/application.conf           # HOCON branch
src/main/resources/application.yaml           # YAML branch
src/main/java/example/app/       # Java application
src/main/kotlin/example/app/     # Kotlin application
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

## Конфигурация { #config }

===! ":fontawesome-brands-java: `Java`"

    Создайте `neo4j-integration/src/main/java/example/neo4j/Neo4jConfig.java`:

    ```java
    package example.neo4j;

    import io.koraframework.config.common.annotation.ConfigSource;
    import java.time.Duration;

    @ConfigSource("neo4j")
    public interface Neo4jConfig {
        String uri();
        String username();
        String password();
        default String database() { return "neo4j"; }
        default Duration connectionTimeout() { return Duration.ofSeconds(5); }
        default Duration acquisitionTimeout() { return Duration.ofSeconds(10); }
        default Duration retryTimeout() { return Duration.ofSeconds(15); }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `neo4j-integration/src/main/kotlin/example/neo4j/Neo4jConfig.kt`:

    ```kotlin
    package example.neo4j

    import io.koraframework.config.common.annotation.ConfigSource
    import java.time.Duration

    @ConfigSource("neo4j")
    interface Neo4jConfig {
        fun uri(): String
        fun username(): String
        fun password(): String
        fun database(): String = "neo4j"
        fun connectionTimeout(): Duration = Duration.ofSeconds(5)
        fun acquisitionTimeout(): Duration = Duration.ofSeconds(10)
        fun retryTimeout(): Duration = Duration.ofSeconds(15)
    }
    ```

URI, имя пользователя и пароль обязательны. Значения по умолчанию находятся в типизированном контракте; приложение может переопределить их без пересборки библиотеки.

Выберите один формат конфигурации и добавьте соответствующий ресурс:

===! ":material-code-json: `HOCON`"

    `src/main/resources/application.conf`:

    ```hocon
    neo4j {
      uri = "bolt://localhost:7687"
      username = "neo4j"
      password = ${NEO4J_PASSWORD}
      database = "neo4j"
      connectionTimeout = "5s"
      acquisitionTimeout = "10s"
      retryTimeout = "15s"
    }
    httpServer.port = 8080
    httpServer.system.port = 8085
    metrics.enabled = true
    httpServer.telemetry.metrics.enabled = true
    tracing.enabled = true
    httpServer.telemetry.tracing.enabled = true
    ```

=== ":simple-yaml: `YAML`"

    `src/main/resources/application.yaml`:

    ```yaml
    neo4j:
      uri: "bolt://localhost:7687"
      username: "neo4j"
      password: "${NEO4J_PASSWORD}"
      database: "neo4j"
      connectionTimeout: "5s"
      acquisitionTimeout: "10s"
      retryTimeout: "15s"
    httpServer:
      port: 8080
      system:
        port: 8085
      telemetry:
        metrics:
          enabled: true
        tracing:
          enabled: true
    metrics:
      enabled: true
    tracing:
      enabled: true
    ```

Пароль берётся из окружения при запуске. Это ограничения подключения, получения соединения и повторов драйвера, а не общий deadline HTTP и не таймаут Cypher-запроса. Экспортёр подключается отдельно
по [руководству трассировки](observability-tracing.md); включение трассировки само по себе не отправляет span в коллектор.

## Телеметрия { #telemetry }

===! ":fontawesome-brands-java: `Java`"

    Создайте `neo4j-integration/src/main/java/example/neo4j/Neo4jTelemetry.java`:

    ```java
    package example.neo4j;

    import io.koraframework.common.telemetry.OpentelemetryContext;
    import io.micrometer.core.instrument.MeterRegistry;
    import io.micrometer.core.instrument.Timer;
    import io.opentelemetry.api.trace.StatusCode;
    import io.opentelemetry.api.trace.Tracer;
    import io.opentelemetry.context.Context;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import java.util.concurrent.TimeUnit;
    import java.util.function.Supplier;

    public final class Neo4jTelemetry {
        private static final Logger log = LoggerFactory.getLogger(Neo4jTelemetry.class);
        private final Tracer tracer;
        private final Timer success;
        private final Timer failure;

        public Neo4jTelemetry(MeterRegistry registry, Tracer tracer) {
            this.tracer = tracer;
            this.success = Timer.builder("neo4j.operation.duration")
                .tag("operation", "savePerson").tag("result", "success").register(registry);
            this.failure = Timer.builder("neo4j.operation.duration")
                .tag("operation", "savePerson").tag("result", "failure").register(registry);
        }

        public <T> T observeSavePerson(Supplier<T> callback) {
            var started = System.nanoTime();
            var parent = Context.current();
            var span = tracer.spanBuilder("neo4j.savePerson").setParent(parent).startSpan();
            try {
                return ScopedValue.where(OpentelemetryContext.VALUE, parent.with(span)).call(() -> {
                    try {
                        var result = callback.get();
                        success.record(System.nanoTime() - started, TimeUnit.NANOSECONDS);
                        return result;
                    } catch (RuntimeException | Error e) {
                        span.setStatus(StatusCode.ERROR);
                        log.warn("Neo4j operation savePerson failed: {}", e.getClass().getSimpleName());
                        throw e;
                    }
                });
            } catch (RuntimeException | Error e) {
                failure.record(System.nanoTime() - started, TimeUnit.NANOSECONDS);
                throw e;
            } finally {
                span.end();
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `neo4j-integration/src/main/kotlin/example/neo4j/Neo4jTelemetry.kt`:

    ```kotlin
    package example.neo4j

    import io.koraframework.common.telemetry.OpentelemetryContext
    import io.micrometer.core.instrument.MeterRegistry
    import io.micrometer.core.instrument.Timer
    import io.opentelemetry.api.trace.StatusCode
    import io.opentelemetry.api.trace.Tracer
    import io.opentelemetry.context.Context
    import org.slf4j.LoggerFactory
    import java.util.concurrent.TimeUnit

    class Neo4jTelemetry(registry: MeterRegistry, private val tracer: Tracer) {
        private val log = LoggerFactory.getLogger(Neo4jTelemetry::class.java)
        private val success = Timer.builder("neo4j.operation.duration")
            .tag("operation", "savePerson").tag("result", "success").register(registry)
        private val failure = Timer.builder("neo4j.operation.duration")
            .tag("operation", "savePerson").tag("result", "failure").register(registry)

        fun <T> observeSavePerson(callback: () -> T): T {
            val started = System.nanoTime()
            val parent = Context.current()
            val span = tracer.spanBuilder("neo4j.savePerson").setParent(parent).startSpan()
            try {
                return ScopedValue.where(OpentelemetryContext.VALUE, parent.with(span)).call<T, Throwable> {
                    try {
                        val result = callback()
                        success.record(System.nanoTime() - started, TimeUnit.NANOSECONDS)
                        result
                    } catch (e: Throwable) {
                        span.setStatus(StatusCode.ERROR)
                        log.warn("Neo4j operation savePerson failed: {}", e.javaClass.simpleName)
                        throw e
                    }
                }
            } catch (e: Throwable) {
                failure.record(System.nanoTime() - started, TimeUnit.NANOSECONDS)
                throw e
            } finally {
                span.end()
            }
        }
    }
    ```

Таймеры регистрируются один раз с фиксированными тегами `operation` и `result`, поэтому имена людей не создают неограниченное число рядов метрик. `Context.current()` получает родительский
HTTP-контекст; новый span привязывается через `OpentelemetryContext.VALUE` на время callback. Выход из `ScopedValue.where(...).call(...)` восстанавливает родителя и при ошибке, а `finally` завершает
span. Не используйте `makeCurrent()` с контекстом Kora на основе scoped values.

В журнал попадает только класс ошибки, без паролей, имён и значений параметров. Для новых операций определяйте отдельный ограниченный контракт телеметрии, а не передавайте пользовательские строки как
имена операций.

## Клиент и жизненный цикл { #lifecycle }

===! ":fontawesome-brands-java: `Java`"

    Создайте `neo4j-integration/src/main/java/example/neo4j/Neo4jClient.java`:

    ```java
    package example.neo4j;

    import io.koraframework.application.graph.Lifecycle;
    import org.neo4j.driver.AuthTokens;
    import org.neo4j.driver.Driver;
    import org.neo4j.driver.Config;
    import java.util.concurrent.TimeUnit;
    import org.neo4j.driver.GraphDatabase;
    import org.neo4j.driver.SessionConfig;
    import org.neo4j.driver.Values;

    public final class Neo4jClient implements Lifecycle {
        private final Driver driver;
        private final SessionConfig sessionConfig;
        private final Neo4jTelemetry telemetry;

        public Neo4jClient(Neo4jConfig config, Neo4jTelemetry telemetry) {
            var driverConfig = Config.builder()
                .withConnectionTimeout(config.connectionTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .withConnectionAcquisitionTimeout(config.acquisitionTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .withMaxTransactionRetryTime(config.retryTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .build();
            this.driver = GraphDatabase.driver(config.uri(),
                AuthTokens.basic(config.username(), config.password()), driverConfig);
            this.sessionConfig = SessionConfig.builder().withDatabase(config.database()).build();
            this.telemetry = telemetry;
        }

        @Override
        public void init() {
            try {
                driver.verifyConnectivity();
            } catch (RuntimeException e) {
                try {
                    driver.close();
                } catch (RuntimeException closeError) {
                    e.addSuppressed(closeError);
                }
                throw e;
            }
        }

        @Override
        public void release() { driver.close(); }

        public String savePerson(String name) {
            return telemetry.observeSavePerson( () -> {
                try (var session = driver.session(sessionConfig)) {
                    return session.executeWrite(tx -> tx.run(
                        "MERGE (p:Person {name: $name}) RETURN p.name AS name",
                        Values.parameters("name", name)
                    ).single().get("name").asString());
                }
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `neo4j-integration/src/main/kotlin/example/neo4j/Neo4jClient.kt`:

    ```kotlin
    package example.neo4j

    import io.koraframework.application.graph.Lifecycle
    import org.neo4j.driver.AuthTokens
    import org.neo4j.driver.Config
    import org.neo4j.driver.GraphDatabase
    import org.neo4j.driver.SessionConfig
    import org.neo4j.driver.Values
    import java.util.concurrent.TimeUnit

    class Neo4jClient(config: Neo4jConfig, private val telemetry: Neo4jTelemetry) : Lifecycle {
        private val driver = GraphDatabase.driver(config.uri(),
            AuthTokens.basic(config.username(), config.password()), Config.builder()
                .withConnectionTimeout(config.connectionTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .withConnectionAcquisitionTimeout(config.acquisitionTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .withMaxTransactionRetryTime(config.retryTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .build())
        private val sessionConfig = SessionConfig.builder().withDatabase(config.database()).build()

        override fun init() {
            try {
                driver.verifyConnectivity()
            } catch (e: RuntimeException) {
                try {
                    driver.close()
                } catch (closeError: RuntimeException) {
                    e.addSuppressed(closeError)
                }
                throw e
            }
        }

        override fun release() { driver.close() }

        fun savePerson(name: String): String = telemetry.observeSavePerson {
            driver.session(sessionConfig).use { session ->
                session.executeWrite { tx ->
                    tx.run("MERGE (p:Person {name: \$name}) RETURN p.name AS name",
                        Values.parameters("name", name)).single().get("name").asString()
                }
            }
        }
    }
    ```

Конструктор создаёт общий драйвер; `init()` проверяет подключение и закрывает драйвер при неудаче. Ошибка очистки добавляется как suppressed exception, чтобы исходная причина сбоя осталась видна.
`release()` закрывает пул при остановке графа.

Сессия локальна для одного вызова. `single().get("name").asString()` материализует значение внутри транзакции; ленивый `Result` оставил бы вызывающий код зависимым от закрытой сессии. `$name` —
параметр Cypher, а не строковая подстановка.

Управляемый `executeWrite` может повторить callback. Отправка email, HTTP-вызовы и другие внешние побочные эффекты должны оставаться за его пределами. Поведение управляемых транзакций описано
в [руководстве Neo4j](https://neo4j.com/docs/java-manual/current/transactions/).

## Модули { #module }

===! ":fontawesome-brands-java: `Java`"

    Создайте `neo4j-integration/src/main/java/example/neo4j/Neo4jModule.java`:

    ```java
    package example.neo4j;

    import io.koraframework.common.annotation.Module;
    import io.micrometer.core.instrument.MeterRegistry;
    import io.opentelemetry.api.trace.Tracer;

    @Module
    public interface Neo4jModule extends Neo4jConfigModule {
        default Neo4jTelemetry neo4jTelemetry(MeterRegistry registry, Tracer tracer) {
            return new Neo4jTelemetry(registry, tracer);
        }

        default Neo4jClient neo4jClient(Neo4jConfig config, Neo4jTelemetry telemetry) {
            return new Neo4jClient(config, telemetry);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `neo4j-integration/src/main/kotlin/example/neo4j/Neo4jModule.kt`:

    ```kotlin
    package example.neo4j

    import io.koraframework.common.annotation.Module
    import io.micrometer.core.instrument.MeterRegistry
    import io.opentelemetry.api.trace.Tracer

    @Module
    interface Neo4jModule : Neo4jConfigModule {
        fun neo4jTelemetry(registry: MeterRegistry, tracer: Tracer): Neo4jTelemetry =
            Neo4jTelemetry(registry, tracer)

        fun neo4jClient(config: Neo4jConfig, telemetry: Neo4jTelemetry): Neo4jClient =
            Neo4jClient(config, telemetry)
    }
    ```

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/example/app/Application.java`:

    ===! ":material-code-json: `HOCON`"

        ```java
        package example.app;

        import example.neo4j.Neo4jModule;
        import io.koraframework.application.graph.KoraApplication;
        import io.koraframework.common.annotation.KoraApp;
        import io.koraframework.config.hocon.HoconConfigModule;
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
        import io.koraframework.logging.logback.LogbackModule;
        import io.koraframework.micrometer.module.MetricsModule;
        import io.koraframework.opentelemetry.tracing.OpentelemetryTracingModule;

        @KoraApp
        public interface Application extends HoconConfigModule, LogbackModule,
                UndertowPublicHttpServerModule, Neo4jModule, MetricsModule,
                OpentelemetryTracingModule {
            static void main(String[] args) {
                KoraApplication.run(ApplicationGraph::graph);
            }
        }
        ```

    === ":simple-yaml: `YAML`"

        ```java
        package example.app;

        import example.neo4j.Neo4jModule;
        import io.koraframework.application.graph.KoraApplication;
        import io.koraframework.common.annotation.KoraApp;
        import io.koraframework.config.yaml.YamlConfigModule;
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
        import io.koraframework.logging.logback.LogbackModule;
        import io.koraframework.micrometer.module.MetricsModule;
        import io.koraframework.opentelemetry.tracing.OpentelemetryTracingModule;

        @KoraApp
        public interface Application extends YamlConfigModule, LogbackModule,
                UndertowPublicHttpServerModule, Neo4jModule, MetricsModule,
                OpentelemetryTracingModule {
            static void main(String[] args) {
                KoraApplication.run(ApplicationGraph::graph);
            }
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/example/app/Application.kt`:

    ===! ":material-code-json: `HOCON`"

        ```kotlin
        package example.app

        import example.neo4j.Neo4jModule
        import io.koraframework.application.graph.KoraApplication
        import io.koraframework.common.annotation.KoraApp
        import io.koraframework.config.hocon.HoconConfigModule
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
        import io.koraframework.logging.logback.LogbackModule
        import io.koraframework.micrometer.module.MetricsModule
        import io.koraframework.opentelemetry.tracing.OpentelemetryTracingModule

        @KoraApp
        interface Application : HoconConfigModule, LogbackModule,
            UndertowPublicHttpServerModule, Neo4jModule, MetricsModule,
            OpentelemetryTracingModule

        fun main() {
            KoraApplication.run(ApplicationGraph::graph)
        }
        ```

    === ":simple-yaml: `YAML`"

        ```kotlin
        package example.app

        import example.neo4j.Neo4jModule
        import io.koraframework.application.graph.KoraApplication
        import io.koraframework.common.annotation.KoraApp
        import io.koraframework.config.yaml.YamlConfigModule
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
        import io.koraframework.logging.logback.LogbackModule
        import io.koraframework.micrometer.module.MetricsModule
        import io.koraframework.opentelemetry.tracing.OpentelemetryTracingModule

        @KoraApp
        interface Application : YamlConfigModule, LogbackModule,
            UndertowPublicHttpServerModule, Neo4jModule, MetricsModule,
            OpentelemetryTracingModule

        fun main() {
            KoraApplication.run(ApplicationGraph::graph)
        }
        ```

`Neo4jModule` наследует сгенерированный `Neo4jConfigModule`, чтобы явно подключить фабрику конфигурации через границу библиотеки. Корень приложения наследует `Neo4jModule`. Одной аннотации на модуле
внутри зависимого JAR недостаточно для подключения фабрики. `MetricsModule` предоставляет `MeterRegistry`, `OpentelemetryTracingModule` — `Tracer`. Kora распознаёт контракт `Lifecycle` возвращаемого
клиента.

Корень использует новый пакет, поэтому обновите существующий блок `application`:

===! ":fontawesome-brands-java: `Java`"

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

Замените прежний корень `@KoraApp`, не оставляйте два корня. Исходный контроллер `/hello` можно сохранить.

## Контроллер { #controller }

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/example/app/PeopleController.java`:

    ```java
    package example.app;

    import example.neo4j.Neo4jClient;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.server.common.response.HttpServerResponse;

    @Component
    @HttpController
    public final class PeopleController {
        private final Neo4jClient client;

        public PeopleController(Neo4jClient client) {
            this.client = client;
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/people/{name}")
        public HttpServerResponse savePerson(@Path String name) {
            return HttpServerResponse.of(200, HttpBody.plaintext(client.savePerson(name)));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/example/app/PeopleController.kt`:

    ```kotlin
    package example.app

    import example.neo4j.Neo4jClient
    import io.koraframework.common.annotation.Component
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.server.common.response.HttpServerResponse

    @Component
    @HttpController
    class PeopleController(private val client: Neo4jClient) {
        @HttpRoute(method = HttpMethod.PUT, path = "/people/{name}")
        fun savePerson(@Path name: String): HttpServerResponse =
            HttpServerResponse.of(200, HttpBody.plaintext(client.savePerson(name)))
    }
    ```

`PUT` соответствует записи: имя идентифицирует ресурс, повтор запроса возвращает то же имя. Ограничение уникальности ниже закрепляет эту идентичность в БД. `GET` не должен создавать данные. Исключение
драйвера проходит обычный путь HTTP-ошибки; преобразование доменных ошибок выходит за рамки этого примера.

## Сгенерированная конфигурация и граф { #generated-code }

После компиляции библиотеки откройте:

===! ":fontawesome-brands-java: `Java`"

    ```text
    neo4j-integration/build/generated/sources/annotationProcessor/java/main/example/neo4j/Neo4jConfigModule.java
    neo4j-integration/build/generated/sources/annotationProcessor/java/main/example/neo4j/$Neo4jConfig_ConfigValueMapper.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    neo4j-integration/build/generated/ksp/main/kotlin/example/neo4j/Neo4jConfigModule.kt
    neo4j-integration/build/generated/ksp/main/kotlin/example/neo4j/$Neo4jConfig_ConfigValueMapper.kt
    ```

Модуль конфигурации содержит такую фабрику (аннотации опущены):

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface Neo4jConfigModule {
        default Neo4jConfig neo4jConfig(
                io.koraframework.config.common.Config config,
                io.koraframework.config.common.mapper.ConfigValueMapper<Neo4jConfig> mapper) {
            return mapper.mapOrThrow(config.get("neo4j"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface Neo4jConfigModule {
        fun neo4jConfig(
            config: io.koraframework.config.common.Config,
            mapper: io.koraframework.config.common.mapper.ConfigValueMapper<Neo4jConfig>
        ): Neo4jConfig = mapper.mapOrThrow(config.get("neo4j"))
    }
    ```

Mapper читает поля и применяет значения по умолчанию интерфейса. В `ApplicationGraph` проследите цепочку `PeopleController → Neo4jClient → Neo4jConfig + Neo4jTelemetry → MeterRegistry + Tracer`.
Java-граф находится в `build/generated/sources/annotationProcessor/java/main/example/app/`, Kotlin-граф — в `build/generated/ksp/main/kotlin/example/app/`. Генерация объясняет подключение компонентов;
редактируйте исходные объявления, не сгенерированные файлы.

## Запуск приложения { #run-app }

Создайте `compose.yaml` в корне приложения:

```yaml
services:
    neo4j:
        image: neo4j:5.26-community
        ports:
            - "127.0.0.1:7687:7687"
        environment:
            NEO4J_AUTH: neo4j/localpassword
        healthcheck:
            test: [ "CMD", "cypher-shell", "-u", "neo4j", "-p", "localpassword", "RETURN 1" ]
            interval: 5s
            timeout: 10s
            retries: 30
            start_period: 20s
```

Эти учётные данные предназначены для локального примера. Дождитесь готовности БД, затем создайте ограничение схемы:

```shell
docker compose up -d --wait
docker compose exec neo4j cypher-shell -u neo4j -p localpassword "CREATE CONSTRAINT person_name_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE"
```

Скомпилируйте и запустите приложение; в PowerShell используйте `gradlew.bat`:

===! "Bash"

    ```bash
    ./gradlew clean classes
    NEO4J_PASSWORD=localpassword ./gradlew run
    ```

=== "PowerShell"

    ```powershell
    ./gradlew.bat clean classes
    $env:NEO4J_PASSWORD = 'localpassword'
    ./gradlew.bat run
    ```

## Проверка приложения { #check-app }

В другом терминале вызовите один ресурс дважды (`curl.exe` в PowerShell):

```shell
curl -i -X PUT http://localhost:8080/people/Alice
curl -i -X PUT http://localhost:8080/people/Alice
```

Оба ответа имеют статус `200` и тело `Alice`. Проверьте, что в БД один соответствующий узел:

```shell
docker compose exec neo4j cypher-shell -u neo4j -p localpassword "MATCH (p:Person {name: 'Alice'}) RETURN count(p) AS people"
```

Значение `people` равно `1`. Проверьте метрики операции:

```shell
curl http://localhost:8085/metrics
```

Найдите `neo4j_operation_duration_seconds_count` с `operation="savePerson"` и `result="success"`; после двух запросов счётчик увеличивается на два. Экспортируется и сумма длительностей; наличие
histogram buckets зависит от конфигурации registry. Если подключён экспортёр, найдите `neo4j.savePerson` под span HTTP-запроса.

### Проверка ошибок и остановки { #failure-checks }

Остановите приложение, задайте неверное значение `NEO4J_PASSWORD` и запустите снова. Инициализация должна завершиться ошибкой до готовности HTTP-сервиса. Верните `localpassword` и перезапустите
приложение. Для проверки ошибки операции остановите БД командой `docker compose stop neo4j` и отправьте PUT: ожидаются серверная ошибка, предупреждение с классом ошибки и увеличение счётчика
неуспешных операций. Верните БД командой `docker compose up -d --wait`. Ограничения повторов драйвера не являются общим deadline запроса.

Остановите приложение через Ctrl+C, чтобы граф освободил драйвер, затем выполните `docker compose down`. В compose-файле нет постоянного volume; данные примера временные.

## Лучшие практики { #best-practices }

- Используйте один драйвер на граф и одну сессию на операцию.
- Параметризуйте Cypher и задавайте ограничения БД для бизнес-ключей.
- Делайте callback безопасным для повторов; материализуйте результат до закрытия ресурсов.
- Настраивайте ограничения под окружение и храните секреты вне исходного кода.
- Ограничивайте набор тегов и имён операций; подключайте span через контекст Kora.
- Отделяйте механику интеграции от доменных ошибок и миграций схемы.

## Итоги { #summary }

Вы создали переиспользуемую библиотеку, сгенерировали конфигурацию, подключили жизненный цикл и телеметрию к графу и проверили повторяемый PUT на локальной БД. Java и Kotlin используют одну реализацию
интеграции.

## Ключевые понятия { #key-concepts }

- `@ConfigSource` генерирует преобразование конфигурации и модуль фабрики.
- Параметры фабрик задают зависимости; `@Module` предоставляет компоненты графа.
- `Lifecycle` связывает проверку запуска и освобождение ресурсов с графом.
- `Driver` общий; `Session` и результат транзакции ограничены операцией.
- Метрики, журнал и span описывают прикладную операцию вместе с повторами.

## Устранение неполадок { #troubleshooting }

**При компиляции не найден `Neo4jConfig` или mapper**

Проверьте AP в библиотеке, runtime-зависимость приложения и сгенерированный `Neo4jConfigModule`. Файл в постороннем каталоге генерации не подключает компонент.

**Не найден `Tracer` или `MeterRegistry`**

Подключите соответствующие модули к `Application`. Одной зависимости от JAR недостаточно для подключения фабрик.

**Ошибка подключения или аутентификации при запуске**

Проверьте `docker compose ps`, healthcheck, Bolt-порт `7687` и совпадение пароля с `NEO4J_AUTH`. Для этой проверки HTTP-запрос не требуется.

**Нет метрик или экспортированных span**

Включите `metrics.enabled`, выполните PUT и проверьте порт `8085`. Для трассировки проверьте оба флага и экспортёр; оболочка драйвера не устанавливает экспортёр.

**Неоднозначный результат или дубликаты людей**

Создайте ограничение уникальности до запросов. Если дубликаты уже существуют, сначала очистите их, иначе ограничение не создастся.

## Что дальше? { #whats-next }

- [AP и KSP для интеграции](integration-processors.md) показывает генерацию кода на небольшом обработчике `@GenerateBuilder`; пример не зависит от клиента БД.
- [Создание аспекта Kora](integration-aspect.md) добавляет перехват методов при компиляции.
- [Интеграционное тестирование](testing-integration.md) помогает проверять поведение инфраструктуры тестами.

## Помощь { #help }

Сверьте подключение графа с [документацией DI](../documentation/container.md), конфигурацию — с [документацией конфигурации](../documentation/config.md), телеметрию —
с [метриками](../documentation/metrics.md) и [трассировкой](../documentation/tracing.md). Поведение драйвера описано в [руководстве Java-драйвера Neo4j](https://neo4j.com/docs/java-manual/current/).
