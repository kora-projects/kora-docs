---
search:
  exclude: true
description: "Builds a minimal Kora service from scratch that answers GET /hello/world: Gradle setup with the io.koraframework:kora-bom BOM and annotation-processors or symbol-processors, a @KoraApp graph with HoconConfigModule, LogbackModule, JsonModule and UndertowPublicHttpServerModule, an @HttpController with plaintext, @Json and HttpResponseEntity responses, and the httpServer configuration. Use when writing the very first Kora application."
agent:
  use_when: "Use this file for questions about the smallest possible Kora service: Gradle build file for Java or Kotlin, io.koraframework:kora-bom, annotation-processors, symbol-processors, @KoraApp, KoraApplication.run(ApplicationGraph::graph), UndertowPublicHttpServerModule, HoconConfigModule, LogbackModule, JsonModule, @Component, @HttpController, @HttpRoute, HttpServerResponse, HttpBody.plaintext, @Json, HttpResponseEntity, httpServer.port and httpServer.system.port."
---

This example shows how to create a simple service in Kora, with an HTTP server, logging and probes, that can respond to a `GET /hello/world` request.

The finished applications are available in the `kora-examples` repository:
[Java](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-helloworld) and
[Kotlin](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-helloworld).

## Create project { #create-project }

Create a new Gradle project (via IDEA or `gradle init`).

Kora artifacts are compiled for `Java` `25`, so `JDK` `25` is the minimum required to compile and run the application,
and the [build system](../documentation/general.md#build-system) is `Gradle` `9.5+`.

Let's check the configuration in `gradle/wrapper/gradle-wrapper.properties`:

```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-9.5.1-bin.zip
```

## Gradle configuration { #gradle-configuration }

Basic concepts and description of the framework can be read on the [main page](../documentation/general.md).

Kora dependency versions are managed by the `io.koraframework:kora-bom` `BOM`, so each Kora artifact is declared without an explicit version.

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

    1. `JDK` `25` is the minimum, the `vendor` pin is optional and only matches the toolchain used by the example projects.
    2. Custom configuration that applies the `BOM` to the annotation processor classpath as well, so the processors and the runtime artifacts always resolve to the same Kora version.
    3. Annotation processor that generates the dependency container, the HTTP handlers and the `Json` readers and writers.

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

    1. `Kotlin` and `KSP` versions must match each other, these are the versions the framework itself is built with.
    2. Symbol processor that generates the dependency container, the HTTP handlers and the `Json` readers and writers. The `ksp` configuration does not inherit the `BOM`, so the version is specified explicitly.
    3. `JDK` `25` is the minimum, the `vendor` pin is optional and only matches the toolchain used by the example projects.

## Application configuration { #application-configuration }

In order to run application, we need to create entrypoint and dependency container. Let's create the `Application` interface with this code:

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

If we run the compilation, the `ApplicationGraph` class will be created,
which describes how to build all the components of our future dependency container.

What `UndertowPublicHttpServerModule` module provides us with:

* A server for public api on port `8080`, configured by the `httpServer` config section
* A server for system api on port `8085`, configured by the `httpServer.system` config section
* Probes on the system port: [/system/liveness](../documentation/probes.md) and [/system/readiness](../documentation/probes.md)
* A [/metrics](../documentation/metrics.md) endpoint on the system port, which answers `# Metric Scraper disabled` until a metrics module is added to the application

The system server comes together with the public one because `UndertowPublicHttpServerModule` extends `UndertowSystemHttpServerModule`,
so a single module in the `@KoraApp` interface is enough for both.

Next we need to create an entry point, let's add a `main` method:

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

`KoraApplication.run` starts parallel initialization of all components in the dependency container and blocks the main thread until the `SIGTERM` signal is received,
after which the application initiates graceful shutdown.
Now, if we run this application, we will have access to the routes in the links above.

## Controller { #controller }

Now let's write a controller that will handle the `GET /hello/world` request on the public port.

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

Let's get into the details:

* `@HttpController` - says that this class is a controller
* `@Component` - says that we want to add this class to our dependency container
* `@HttpRoute` - describes which path we want to process
* `HttpServerResponse` - this is the raw response, where you can set anything and give any bytes you want

Handler methods are synchronous: the method returns the response itself, there is no reactive or asynchronous return type involved.

## Json controller { #json-controller }

In normal life we want to return `Json` format more often, for this we will add a `JsonModule` module:

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

And let's change the controller to return an object of the class we want to serialize:

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

    1. Tells the processor to generate a reader and a writer for this type at compile time.
    2. Tells the HTTP server to use the generated `Json` writer for the response body of this route.
    3. `HttpResponseEntity` wraps the body together with a status code and headers, while the body itself is still written by the generated `Json` writer.

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

    1. Tells the processor to generate a reader and a writer for this type at compile time.
    2. Tells the HTTP server to use the generated `Json` writer for the response body of this route.
    3. `HttpResponseEntity` wraps the body together with a status code and headers, while the body itself is still written by the generated `Json` writer.

Now an optimal `Json` writer will be generated for our object, and we will see `Json` in the response:

```json
{"greeting":"Hello World"}
```

## Configuration { #configuration }

The `HoconConfigModule` module reads `application.conf` from the classpath, so let's create `src/main/resources/application.conf`:

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

1. Request and response logging is disabled by default for all modules, so it is enabled explicitly here to see the incoming requests in the console.

Both port values are the module defaults, they are written out only to make the configuration explicit.

## Run application { #run-application }

Use command below to start application:

```shell
./gradlew run
```

Then the routes can be checked:

```shell
curl --location 'http://localhost:8080/hello/world'
# Expected output: Hello World

curl --location 'http://localhost:8080/hello/world/json'
# Expected output: {"greeting":"Hello World"}

curl --location 'http://localhost:8085/system/readiness'
# Expected output: OK
```

## Project template { #project-template }

===! ":fontawesome-brands-java: `Java`"

    You can create a new Java service by using [template on GitHub](https://github.com/kora-projects/kora-java-template).

=== ":simple-kotlin: `Kotlin`"

    You can create a new Kotlin service using [template on GitHub](https://github.com/kora-projects/kora-kotlin-template).
