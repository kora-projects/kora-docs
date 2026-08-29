---
search:
  exclude: true
description: "Builds a minimal Kora service from scratch that answers GET /hello/world: Gradle setup with the io.koraframework:kora-bom BOM and annotation-processors or symbol-processors, a @KoraApp graph with HoconConfigModule, LogbackModule, JsonModule and UndertowPublicHttpServerModule, an @HttpController with plaintext, @Json and HttpResponseEntity responses, and the httpServer configuration. Use when writing the very first Kora application."
agent:
  use_when: "Use this file for questions about the smallest possible Kora service: Gradle build file for Java or Kotlin, io.koraframework:kora-bom, annotation-processors, symbol-processors, @KoraApp, KoraApplication.run(ApplicationGraph::graph), UndertowPublicHttpServerModule, HoconConfigModule, LogbackModule, JsonModule, @Component, @HttpController, @HttpRoute, HttpServerResponse, HttpBody.plaintext, @Json, HttpResponseEntity, httpServer.port and httpServer.system.port."
---

Данный пример разбирает как создать простой сервис на Kora, с HTTP сервером, логгированием и пробами, который умеет отвечать на запрос `GET /hello/world`.

Готовые приложения доступны в репозитории `kora-examples`:
[Java](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-helloworld) и
[Kotlin](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-helloworld).

## Создание проекта { #create-project }

Создаём новый Gradle-проект (через IDEA или `gradle init`).

Артефакты Kora собраны под `Java` `25`, поэтому для компиляции и запуска приложения требуется минимум `JDK` `25`,
а [система сборки](../documentation/general.md#build-system) — `Gradle` `9.5+`.

Проверим конфигурацию в `gradle/wrapper/gradle-wrapper.properties`:

```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-9.5.1-bin.zip
```

## Настройка Gradle { #gradle-configuration }

Основные концепции и описание фреймворка можно прочесть на [основной странице](../documentation/general.md).

Версиями зависимостей Kora управляет `BOM` `io.koraframework:kora-bom`, поэтому каждый артефакт Kora объявляется без явного указания версии.

===! ":fontawesome-brands-java: `Java`"

    `build.gradle`:
    ```groovy
    plugins {
        id "java"
        id "application"
    }

    repositories {
        mavenCentral()
    }

    group = "io.koraframework.example"
    version = "0.1.0-SNAPSHOT"

    java {
        toolchain {
            languageVersion = JavaLanguageVersion.of(25) //(1)!
            vendor = JvmVendorSpec.ADOPTIUM
        }
    }

    configurations {
        koraBom //(2)!
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        api.extendsFrom(koraBom)
        testImplementation.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1")
        annotationProcessor "io.koraframework:annotation-processors" //(3)!

        implementation "io.koraframework:http-server-undertow"
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"
    }

    application {
        applicationName = "application"
        mainClass = "io.koraframework.example.helloworld.Application"
    }

    distTar {
        archiveFileName = "application.tar"
    }
    ```

    1. `JDK` `25` — минимально необходимая версия, закрепление `vendor` необязательно и лишь повторяет тот инструментарий, который используется в проектах-примерах.
    2. Отдельная конфигурация, которая применяет `BOM` в том числе и к classpath обработчика аннотаций, чтобы обработчики и артефакты времени выполнения всегда разрешались в одну и ту же версию Kora.
    3. Обработчик аннотаций, который создаёт контейнер зависимостей, обработчики HTTP запросов и `Json` читатели и писатели.

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:
    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version ("2.4.10") //(1)!
        id("com.google.devtools.ksp") version ("2.3.11")
    }

    repositories {
        mavenCentral()
    }

    group = "io.koraframework.example"
    version = "0.1.0-SNAPSHOT"

    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1"))
        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")
    }

    kotlin {
        jvmToolchain {
            languageVersion.set(JavaLanguageVersion.of(25)) //(3)!
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
    }

    application {
        applicationName = "application"
        mainClass.set("io.koraframework.example.helloworld.ApplicationKt")
    }

    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

    1. Версии `Kotlin` и `KSP` должны соответствовать друг другу, это те версии, на которых собран сам фреймворк.
    2. Обработчик символов, который создаёт контейнер зависимостей, обработчики HTTP запросов и `Json` читатели и писатели. Конфигурация `ksp` не наследует `BOM`, поэтому версия указывается явно.
    3. `JDK` `25` — минимально необходимая версия, закрепление `vendor` необязательно и лишь повторяет тот инструментарий, который используется в проектах-примерах.

## Настройка приложения { #application-configuration }

Для запуска приложения нам нужно сформировать точку входа и контейнер зависимостей. Для этого создадим интерфейс `Application` с таким кодом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.example.helloworld;

    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            UndertowPublicHttpServerModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.example.helloworld

    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application : HoconConfigModule,
        LogbackModule,
        UndertowPublicHttpServerModule
    ```

Если мы запустим компиляцию, то будет создан класс `ApplicationGraph`,
в котором описано как собирать все компоненты нашего будущего контейнера зависимостей.

Что нам предоставляет модуль `UndertowPublicHttpServerModule`:

* Сервер для публичного API на порту `8080`, настраивается секцией конфигурации `httpServer`
* Сервер для системного API на порту `8085`, настраивается секцией конфигурации `httpServer.system`
* Пробы на системном порту: [/system/liveness](../documentation/probes.md) и [/system/readiness](../documentation/probes.md)
* Эндпоинт [/metrics](../documentation/metrics.md) на системном порту, который отвечает `# Metric Scraper disabled` до тех пор, пока в приложение не добавлен модуль метрик

Системный сервер идёт в комплекте с публичным, потому что `UndertowPublicHttpServerModule` наследует `UndertowSystemHttpServerModule`,
поэтому одного модуля в интерфейсе `@KoraApp` достаточно для обоих.

Далее нам нужно создать точку входа, добавим метод `main`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.example.helloworld;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            LogbackModule,
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.example.helloworld

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application : HoconConfigModule,
        LogbackModule,
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run { ApplicationGraph.graph() }
    }
    ```

`KoraApplication.run` запускает параллельную инициализацию всех компонентов в контейнере зависимостей и блокирует основной поток до получения сигнала `SIGTERM`,
после этого приложение начинает штатное завершение.
Теперь, если мы запустим это приложение, то нам будут доступны маршруты по ссылкам выше.

## Контроллер { #controller }

Теперь давайте напишем контроллер, который будет обрабатывать запрос `GET /hello/world` на публичном порту.

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.example.helloworld;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponse;

    @Component
    @HttpController
    public final class HelloWorldController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        public HttpServerResponse helloWorld() {
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello World"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.example.helloworld

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponse

    @Component
    @HttpController
    class HelloWorldController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun helloWorld(): HttpServerResponse {
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello World"))
        }
    }
    ```

Давайте разберёмся детально:

* `@HttpController` - говорит, что этот класс контроллер
* `@Component` - говорит, что мы хотим добавить этот класс в наш контейнер зависимостей
* `@HttpRoute` - описывает какой путь мы хотим обрабатывать
* `HttpServerResponse` - это сырой вариант ответа, в котором можно выставить что угодно и отдать любые байты

Методы-обработчики синхронные: метод возвращает сам ответ, никакие реактивные или асинхронные возвращаемые типы здесь не участвуют.

## Контроллер Json { #json-controller }

В обычной жизни мы зачастую отдаём данные в формате `Json`, для этого добавим модуль `JsonModule`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.example.helloworld;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.example.helloworld

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application : HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run { ApplicationGraph.graph() }
    }
    ```

И изменим контроллер, чтобы он возвращал объект класса, который мы хотим сериализовать:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.example.helloworld;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.HttpResponseEntity;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponse;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class HelloWorldController {

        @Json //(1)!
        public record HelloWorldResponse(String greeting) {}

        @Json //(2)!
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world/json")
        public HelloWorldResponse helloWorldJson() {
            return new HelloWorldResponse("Hello World");
        }

        @Json
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world/json/entity")
        public HttpResponseEntity<HelloWorldResponse> helloWorldJsonEntity() { //(3)!
            return HttpResponseEntity.of(200, new HelloWorldResponse("Hello World"));
        }

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        public HttpServerResponse helloWorld() {
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello World"));
        }
    }
    ```

    1. Говорит обработчику создать читатель и писатель для этого типа во время компиляции.
    2. Говорит HTTP серверу использовать созданный `Json` писатель для тела ответа этого маршрута.
    3. `HttpResponseEntity` оборачивает тело вместе с кодом статуса и заголовками, при этом само тело по-прежнему пишет созданный `Json` писатель.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.example.helloworld

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.HttpResponseEntity
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponse
    import io.koraframework.json.common.annotation.Json

    @Component
    @HttpController
    class HelloWorldController {

        @Json //(1)!
        data class HelloWorldResponse(val greeting: String)

        @Json //(2)!
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world/json")
        fun helloWorldJson(): HelloWorldResponse {
            return HelloWorldResponse("Hello World")
        }

        @Json
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world/json/entity")
        fun helloWorldJsonEntity(): HttpResponseEntity<HelloWorldResponse> { //(3)!
            return HttpResponseEntity.of(200, HelloWorldResponse("Hello World"))
        }

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun helloWorld(): HttpServerResponse {
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello World"))
        }
    }
    ```

    1. Говорит обработчику создать читатель и писатель для этого типа во время компиляции.
    2. Говорит HTTP серверу использовать созданный `Json` писатель для тела ответа этого маршрута.
    3. `HttpResponseEntity` оборачивает тело вместе с кодом статуса и заголовками, при этом само тело по-прежнему пишет созданный `Json` писатель.

Теперь для нашего объекта будет сформирован оптимальный `Json` писатель и в ответе мы увидим `Json`:

```json
{"greeting":"Hello World"}
```

## Конфигурация { #configuration }

Модуль `HoconConfigModule` читает `application.conf` из classpath, поэтому создадим `src/main/resources/application.conf`:

```hocon
httpServer {
  port = 8080
  system.port = 8085
  telemetry.logging.enabled = true //(1)!
}

logging.levels {
  "root": "WARN"
  "io.koraframework": "INFO"
  "io.koraframework.example": "INFO"
}
```

1. Логирование запросов и ответов по умолчанию выключено для всех модулей, поэтому здесь оно включается явно, чтобы видеть входящие запросы в консоли.

Оба значения портов совпадают со значениями по умолчанию у модуля, они выписаны лишь для того, чтобы сделать конфигурацию явной.

## Запуск приложения { #run-application }

Для запуска приложения используйте команду ниже:

```shell
./gradlew run
```

После этого можно проверить маршруты:

```shell
curl --location 'http://localhost:8080/hello/world'
# Expected output: Hello World

curl --location 'http://localhost:8080/hello/world/json'
# Expected output: {"greeting":"Hello World"}

curl --location 'http://localhost:8085/system/readiness'
# Expected output: OK
```

## Шаблон проекта { #project-template }

===! ":fontawesome-brands-java: `Java`"

    Создать новый Java сервис можно использовав [шаблон на GitHub](https://github.com/kora-projects/kora-java-template).

=== ":simple-kotlin: `Kotlin`"

    Создать новый Kotlin сервис можно использовав [шаблон на GitHub](https://github.com/kora-projects/kora-kotlin-template).
