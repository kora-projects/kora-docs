---
search:
  exclude: true
---

This example shows how to create a simple service in Kora, with an HTTP server, metrics, logging and samples, that can respond to a `GET /hello/world` request.

## Create project

Create a new Gradle project (via IDEA or `gradle init`).

We will need gradlew with a customized version of Gradle above `7.*`.

Let's check the configuration in `gradle/wrapper/gradle-wrapper.properties`:

```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.10-bin.zip
```

## Gradle configuration

Basic concepts and description of the framework can be read on the [main page](../documentation/general.md).

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
        koraBom platform("ru.tinkoff.kora:kora-parent:1.1.20")
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
        koraBom(platform("ru.tinkoff.kora:kora-parent:1.1.20"))
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

## Application configuration

In order to run application, we need to create entrypoint and dependency container. Let's create the `Application` interface with this code:

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

If we run the compilation, the `ApplicationGraph` class will be created, 
which describes how to build all the components of our future dependency container.

What `UndertowHttpServerModule` module provides us with:

* A server for public api on port 8080
* A server for system api on port 8085
* Samples on system port: [/system/liveness](../documentation/probes.md) and [/system/readiness](../documentation/probes.md)

Next we need to create an entry point, let's create an `Application` class with a `main` method:

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

`KoraApplication.run` starts parallel initialization of all components in the dependency container and blocks the main thread until the `SIGTERM` signal is received,
after which the application initiates graceful shutdown.
Now, if we run this application, we will have access to the routers in the links above.

## Controller

Now let's write a controller that will handle the `GET /hello/world` request on the public port.

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

Let's get into the details:

* `@HttpController` - says that this class is a controller
* `@Component` - says that we want to add this class to our dependency container
* `@HttpRoute` - describes which path we want to process.
* `HttpServerResponse` - this is the raw response, where you can set anything and give any bytes you want.

Use command below to start application:

=== ":fontawesome-brands-java: `Java`"

    ```shell
    ./gradlew run
    ```

=== ":simple-kotlin: `Kotlin`"

    ```shell
    ./gradlew run
    ```

## Json Controller

In normal life we want to return `Json` format more often, for this we will add a `JsonModule` module:

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

And let's change the controller to return an object of the class we want to serialize:

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

Now an optimal Json writer will be generated for our object, and we will see Json in the response:

```json
{"greeting":"Hello World"}
```

=== ":fontawesome-brands-java: `Java`"

    You can create a new Java service by using [template on GitHub](https://github.com/kora-projects/kora-java-crud-template)

=== ":simple-kotlin: `Kotlin`"

    You can create a new Kotlin service using [template on GitHub](https://github.com/kora-projects/kora-kotlin-crud-template).
