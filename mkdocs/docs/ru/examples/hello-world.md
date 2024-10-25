---
search:
  exclude: true
---

Данный пример разбирает как создать простой сервис на Kora, с HTTP сервером, настроенными метриками, логгированием и пробами, который умеет отвечать на запрос `GET /hello/world`.

## Создание проекта

Создаем новый Gradle-проект (через IDEA или `gradle init`).

Для работы нам потребуется `gradlew` с настроенной версией [Gradle](../documentation/general.md#_3) выше `7.*`.

Проверим конфигурацию в `gradle/wrapper/gradle-wrapper.properties`:

```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.6-bin.zip
```

## Настройка Gradle

=== ":fontawesome-brands-java: `Java`"

    `build.gradle`:
    ```groovy
    plugins {
        id "java"
        id "application"
    }

    repositories {
        mavenCentral()
    }

    group = "ru.tinkoff.kora.example"
    version = "0.1.0-SNAPSHOT"

    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17

    mainClassName = "ru.tinkoff.kora.example.Application"

    configurations {
        koraBom
        annotationProcessor.extendsFrom(koraBom)
        compileOnly.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        api.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("ru.tinkoff.kora:kora-parent:1.1.11")
        annotationProcessor "ru.tinkoff.kora:annotation-processors"

        implementation "ru.tinkoff.kora:http-server-undertow"
        implementation "ru.tinkoff.kora:json-module"
        implementation "ru.tinkoff.kora:config-hocon"
        implementation "ch.qos.logback:logback-classic:1.4.8"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:
    ```groovy
    plugins {
        kotlin("jvm") version ("1.9.10")
        id("com.google.devtools.ksp") version ("1.9.10-1.0.13")
        id("application")
    }

    repositories {
        mavenCentral()
    }

    application {
        mainClass.set("ru.tinkoff.kora.example.ApplicationKt")
    }

    val koraBom: Configuration by configurations.creating
    configurations {
        ksp.get().extendsFrom(koraBom)
        compileOnly.get().extendsFrom(koraBom)
        api.get().extendsFrom(koraBom)
        implementation.get().extendsFrom(koraBom)
    }

    dependencies {
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.1.11"))
        ksp("ru.tinkoff.kora:symbol-processors")

        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor:1.7.3")
        implementation("org.jetbrains.kotlinx:kotlinx-coroutines-jdk8:1.7.3")
        implementation("ch.qos.logback:logback-classic:1.4.8")
    }

    kotlin {
        jvmToolchain { languageVersion.set(JavaLanguageVersion.of("17")) }
        sourceSets.main { kotlin.srcDir("build/generated/ksp/main/kotlin") }
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") }
    }

    tasks.distTar {
        archiveFileName.set("application.tar")
    }
    ```

## Конфигурация приложения

Для запуска приложения нам нужно сформировать контейнер. Для этого создадим интерфейс `Application` с таким кодом:

=== ":fontawesome-brands-java: `Java`"

    ```java
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;

    @KoraApp
    public interface Application extends HoconConfigModule, UndertowHttpServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule

    @KoraApp
    interface Application : HoconConfigModule, UndertowHttpServerModule
    ```

Если мы запустим компиляцию, то будет создан класс `ApplicationGraph`, в котором описано как собирать все компоненты нашего будущего контейнера.
Что нам предоставляет `UndertowHttpServerModule`:

* Сервер для публичного апи на порту 8080
* Сервер для системного апи на порту 8085
* Пробы на системном порту: [/system/liveness](../documentation/probes.md) и [/system/readiness](../documentation/probes.md)

Далее нам нужно создать точку входа, добавим в класс `Application` метод `main`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    import ru.tinkoff.kora.application.graph.KoraApplication;

    @KoraApp
    public interface Application extends HoconConfigModule, UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import ru.tinkoff.kora.application.graph.KoraApplication

    @KoraApp
    interface Application : HoconConfigModule, UndertowHttpServerModule

    fun main() {
        KoraApplication.run { ApplicationGraph.graph() }
    }
    ```

`KoraApplication.run` запускает параллельную инициализацию всех компонентов в контейнере и блокирует основной поток до получения сигнала `SIGTERM`, 
после этого приложение начинает штатное завершение.
Теперь, если мы запустим это приложение, то нам будут доступны маршруты по ссылкам выше.

## Контроллер

Теперь давайте напишем контроллер, который будет обрабатывать запрос `GET /hello/world` на публичном порту.

=== ":fontawesome-brands-java: `Java`"

    ```java
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.HttpHeaders;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;

    import java.nio.charset.StandardCharsets;

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
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.HttpHeaders
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import java.nio.charset.StandardCharsets

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
* `@Component` - говорит, что мы хотим добавить этот класс в наш контейнер
* `@HttpRoute` - описывает какой путь мы хотим обрабатывать
* `HttpServerResponse` - это сырой вариант ответа, в котором можно выставить что угодно и отдать любые байты

Для запуска приложения можно использовать команду:

=== ":fontawesome-brands-java: `Java`"

    ```shell
    ./gradlew run
    ```

=== ":simple-kotlin: `Kotlin`"

    ```shell
    ./gradlew run
    ```

## Контроллер Json

В обычной жизни мы зачастую отдаём данные в формате `Json`, для этого добавим модуль `JsonModule`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;

    @KoraApp
    public interface Application extends HoconConfigModule, UndertowHttpServerModule, JsonModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule

    @KoraApp
    interface Application : HoconConfigModule, UndertowHttpServerModule, JsonModule
    ```

И изменим контроллер, чтобы он возвращал объект класса, который мы хотим сериализовать:

=== ":fontawesome-brands-java: `Java`"

    ```java
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class HelloWorldController {

        record HelloWorldResponse(String greeting) {}

        @Json
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        public HelloWorldResponse helloWorld() {
            return new HelloWorldResponse("hello World");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class HelloWorldController {

        data class HelloWorldResponse(val greeting: String)

        @Json
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun helloWorld(): HelloWorldResponse {
            return HelloWorldResponse("Hello World")
        }
    }
    ```

Теперь для нашего объекта будет сформирован оптимальный Json писатель и в ответе мы увидим Json:

```json
{"greeting":"Hello World"}
```

=== ":fontawesome-brands-java: `Java`"

    Создать новый Java сервис можно использовав [шаблон на GitHub](https://github.com/kora-projects/kora-java-crud-template)

=== ":simple-kotlin: `Kotlin`"

    Создать новый Kotlin сервис можно использовав [шаблон на GitHub](https://github.com/kora-projects/kora-kotlin-crud-template)
