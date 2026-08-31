---
description: "Explains how to build a Kora application into a GraalVM Native Image: the Gradle plugin and JDK 25 toolchain, the fat JAR and the two-stage Docker build, reachability metadata, and how to verify the resulting binary. Use when working with GraalVM, native-image, nativeCompile, reachability metadata, reflect-config.json, AOT, native build."
agent:
  use_when: "Use this file for Kora docs or implementation questions about building a Kora application into a GraalVM Native Image; key triggers include GraalVM, native-image, org.graalvm.buildtools.native, nativeCompile, reachability metadata, reflect-config.json, native-image.properties, tracing agent, AOT, native build, native Docker image."
---

GraalVM Native Image is a tool for `AOT compilation` that builds a Java application ahead of time into a standalone native image for the target platform.
Such an image starts without regular JVM warmup, but requires part of the information about code, resources, and reflection to be known at build time.

Kora creates its helper classes at compile time,
does not use the Reflection API at runtime,
does not use dynamic proxies,
does not generate bytecode at compile time or runtime.
This makes it easier to build Kora applications into a native image that starts faster and usually consumes less memory than a regular JVM application.
The main limitations of this kind of build are usually related not to Kora itself, but to third-party libraries that may require additional reflection, resource, or class initialization settings.

Therefore, Kora itself usually does not require additional configuration to build a native image:
the modules that depend on such libraries ship the required [reachability metadata](#metadata) inside their own artifacts.

## Requirements { #requirements }

A native build requires a [GraalVM](https://www.graalvm.org/) JDK — **GraalVM Community Edition** or **Oracle GraalVM** — of the **same major version the application is compiled for**.
Kora 2.0 artifacts are compiled for **Java 25**, and `native-image` refuses to read class files of a newer class-file format than its own JDK,
so the native build requires a **GraalVM 25** launcher. The official examples were verified on GraalVM CE 25 (`native-image 25.x`), installed for example with `sdk install java 25.2.4-graalce`.

The major version has to match in **three** places at once, and forgetting any of them is the most common cause of a broken native build:

1. the module toolchain (`java { toolchain { … } }` or `kotlin { jvmToolchain { … } }`);
2. the `javaLauncher` of the `graalvmNative` binary — see [Build](#build);
3. the base image of the builder stage in the [Dockerfile](#docker).

The application itself does not have to be compiled by GraalVM: the module toolchain can be an ordinary JDK,
while the [Gradle plugin](https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html) picks a GraalVM launcher through `JvmVendorSpec.matching("GraalVM Community")` only for `native-image`.
If no matching GraalVM installation is visible to Gradle, `nativeCompile` fails while selecting the toolchain — this is an environment problem, not an application problem.

When building outside the plugin (for example, the `native-image` command inside a [Docker](#docker) builder), the `native-image` tool must be available on `PATH` — the official GraalVM container images already ship it.

## Build { #build }

Example of building a native image using the [Gradle plugin](https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html):

===! ":fontawesome-brands-java: `Java`"

    `build.gradle`:
    ```groovy
    plugins {
        id "application"
        id "com.gradleup.shadow" version "9.4.1"
        id "org.graalvm.buildtools.native" version "1.1.7" //(1)!
    }

    java {
        toolchain {
            languageVersion = JavaLanguageVersion.of(25) //(2)!
            vendor = JvmVendorSpec.ADOPTIUM
        }
    }

    application {
        mainClass = "io.koraframework.example.Application"
    }

    graalvmNative {
        binaries {
            main {
                imageName = project.name //(3)!
                mainClass = application.mainClass //(4)!
                javaLauncher = javaToolchains.launcherFor {
                    languageVersion = JavaLanguageVersion.of(25) //(5)!
                    vendor = JvmVendorSpec.matching("GraalVM Community")
                }
            }
        }
        metadataRepository {
            enabled = true //(6)!
        }
    }
    ```

    1.  Version of the plugin that builds the native image. **1.1.7 or newer is required** for a multi-module build: earlier versions registered a single shared build service for the whole build, and on Gradle 9 the `collectReachabilityMetadata` task of the second and every subsequent native module fails while resolving a configuration of another project.
    2.  JDK the application classes are compiled for — an ordinary JDK is fine here.
    3.  Name of the resulting binary in `build/native/nativeCompile` (default: project name).
    4.  Fully qualified name of the class with the `main` method (required). **Assign the provider itself, not a string interpolation of it**: `application.mainClass` is a `Property<String>`, and `"$application.mainClass"` puts its debug representation (`property(java.lang.String, fixed(...))`) on the `native-image` command line instead of the class name. The failure surfaces as *main class not found* during image build, not as a Gradle configuration error.
    5.  JDK used by `native-image` itself — this one must be GraalVM, see [Requirements](#requirements).
    6.  Enables the [reachability metadata repository](#metadata-repository) (default: `false`).

    Build the binary:
    ```shell
    ./gradlew nativeCompile
    ```

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:
    ```kotlin
    plugins {
        id("application")
        kotlin("jvm") version "2.4.10"
        id("com.google.devtools.ksp") version "2.3.11"
        id("com.gradleup.shadow") version "9.4.1"
        id("org.graalvm.buildtools.native") version "1.1.7" //(1)!
    }

    kotlin {
        jvmToolchain {
            languageVersion.set(JavaLanguageVersion.of(25)) //(2)!
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
    }

    application {
        mainClass.set("io.koraframework.example.ApplicationKt")
    }

    graalvmNative {
        binaries {
            named("main") {
                imageName.set(project.name) //(3)!
                mainClass.set(application.mainClass) //(4)!
                javaLauncher.set(javaToolchains.launcherFor {
                    languageVersion.set(JavaLanguageVersion.of(25)) //(5)!
                    vendor.set(JvmVendorSpec.matching("GraalVM Community"))
                })
            }
        }
        metadataRepository {
            enabled.set(true) //(6)!
        }
    }
    ```

    1.  Version of the plugin that builds the native image. **1.1.7 or newer is required** for a multi-module build: earlier versions registered a single shared build service for the whole build, and on Gradle 9 the `collectReachabilityMetadata` task of the second and every subsequent native module fails while resolving a configuration of another project.
    2.  JDK the application classes are compiled for — an ordinary JDK is fine here.
    3.  Name of the resulting binary in `build/native/nativeCompile` (default: project name).
    4.  Fully qualified name of the class with the `main` method (required); for Kotlin this is a class with the `Kt` suffix. **Pass the provider itself, not a string built from it** — `application.mainClass` is a `Property<String>`, and its `toString()` is a debug representation (`property(java.lang.String, fixed(...))`), which reaches the `native-image` command line instead of the class name. The failure surfaces as *main class not found* during image build, not as a Gradle configuration error.
    5.  JDK used by `native-image` itself — this one must be GraalVM, see [Requirements](#requirements).
    6.  Enables the [reachability metadata repository](#metadata-repository) (default: `false`).

    Build the binary:
    ```shell
    ./gradlew nativeCompile
    ```

Extra flags for `native-image` are passed through the `buildArgs` list of the binary, for example `buildArgs.add("--no-fallback")` — it forbids producing a *fallback* image (one that silently bundles a JVM) and fails the build instead if something cannot be compiled ahead of time.
The `debug` and `verbose` properties of the same block turn on additional build diagnostics.

!!! warning "Do not disable the `jar` task"

    `nativeCompile` builds its class path from the project's own artifacts, so the plain `jar` task must stay enabled.
    With `jar.enabled = false` the class path contains only the dependencies and none of the application classes,
    and the build fails on a missing `Application` class even though `compileJava` succeeded.
    The [fat JAR](#build-jar) does not help here — it is assembled for the [Docker](#docker) path and does not participate in the `nativeCompile` class path.

### Fat JAR { #build-jar }

`native-image` compiles a single class path into the binary, so for the [Docker](#docker) path a Kora application is assembled into one *fat JAR* first.

A fat JAR must be built with `META-INF/services` merging: a naive archive overwrites same-named service files instead of concatenating them,
and both Kora (`io.koraframework:common` ships an `io.opentelemetry.context.ContextStorageProvider` service file) and its dependencies (the XNIO provider of the HTTP server, JDBC drivers, SLF4J) rely on them.
In a native image a lost service file is fatal, because the corresponding provider is simply never discovered.
The [Shadow](https://gradleup.com/shadow/) plugin does the merging:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    shadowJar {
        mergeServiceFiles() //(1)!
        manifest {
            attributes "Main-Class": application.mainClass //(2)!
        }
    }

    assemble.dependsOn shadowJar
    ```

    1.  Concatenates the `META-INF/services` files of all dependencies instead of overwriting them (**required**).
    2.  Entry point of the archive — the same provider that is passed to [`mainClass`](#build).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    tasks.shadowJar {
        mergeServiceFiles() //(1)!
        manifest {
            attributes["Main-Class"] = application.mainClass //(2)!
        }
    }

    tasks.assemble {
        dependsOn(tasks.shadowJar)
    }
    ```

    1.  Concatenates the `META-INF/services` files of all dependencies instead of overwriting them (**required**).
    2.  Entry point of the archive — the same provider that is passed to [`mainClass`](#build).

The Shadow plugin produces an `*-all.jar` in `build/libs`:

```shell
./gradlew shadowJar
```

## Docker { #docker }

In CI and production the native image is usually produced with a two-stage Docker build: a GraalVM *builder* stage compiles the [fat JAR](#build-jar) into a binary, and a slim runtime stage ships only that binary.
This is how the official [examples](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm) build their images, and it does not depend on whether the application is written in Java or Kotlin:

```dockerfile
FROM ghcr.io/graalvm/native-image-community:25 as builder

ARG TARGET_DIR=/opt/app
ARG SOURCE_DIR=build/libs
WORKDIR $TARGET_DIR

COPY $SOURCE_DIR/*-all.jar $TARGET_DIR/application.jar

RUN native-image --no-fallback -classpath $TARGET_DIR/application.jar

FROM ubuntu:noble-20240212 as runner

ARG TARGET_DIR=/opt/app
WORKDIR $TARGET_DIR

COPY --from=builder $TARGET_DIR/application $TARGET_DIR/application

ARG DOCKER_USER=app
RUN groupadd -r $DOCKER_USER && useradd -rg $DOCKER_USER $DOCKER_USER
RUN chmod +x application
USER $DOCKER_USER

EXPOSE 8080/tcp
EXPOSE 8085/tcp
CMD "/opt/app/application"
```

Build the fat JAR first, then the image:

```shell
./gradlew shadowJar
docker build .
```

The two exposed ports are the two Kora HTTP servers: `httpServer.port` (default: `8080`) for the application API and `httpServer.system.port` (default: `8085`) for the [system server](http-server.md#system-server) that serves [probes](probes.md) and metrics.

The builder stage names the binary `application` even though no `-H:Name` is passed on the command line: the name and the entry point come from a `native-image.properties` file inside the JAR, generated from the [annotation hints](#metadata-hints) used by the examples.
Without such a file the class to compile has to be given explicitly, for example `native-image --no-fallback -classpath application.jar io.koraframework.example.Application`.

!!! warning "Two build paths read metadata differently"

    `nativeCompile` adds the [metadata repository](#metadata-repository) to the build itself, whereas `native-image -classpath application.jar` inside Docker knows nothing about Gradle and reads only what physically lies in the JAR.
    If the image built by Gradle works and the one built by Docker does not, the metadata plumbing described in [Repository](#metadata-repository) is the first suspect, not the application code.

## Verification { #verification }

A successful native image **build** is not evidence that the image works.
Missing reachability metadata does not fail the build: `native-image` finishes green and the registrations are simply never applied, so the failure surfaces only at runtime.
Three different things have to succeed, and each one has to be checked separately:

1. **the JVM build** — `./gradlew build` passes and the application runs on a regular JDK;
2. **the native image build** — `./gradlew nativeCompile` (or `docker build`) produces a binary;
3. **the binary at runtime** — the compiled application actually starts and serves traffic.

A minimal checklist for the third point:

- the binary starts and does not die a second later;
- `GET /system/readiness` on the [system server](http-server.md#system-server) answers `200` — meaning the whole dependency graph was initialized;
- `GET /metrics` returns metrics rather than a stub or a `500`;
- the module scenario works against a real dependency (database, broker), not against mocks;
- there are no stack traces in the startup log — in a native image they are often the only sign of a subsystem that silently fell off.

The cheapest way to keep this in CI is a black-box test that builds the image from the `Dockerfile` and runs it with [Testcontainers](https://java.testcontainers.org/) — this is how all three native examples are tested:

```java
waitingFor(Wait.forHttp("/system/readiness")
        .forPort(8085)
        .forStatusCode(200)
        .withStartupTimeout(Duration.ofSeconds(60)));
```

!!! tip "Wait for the probe, not for a log line"

    Base container readiness on the HTTP probe rather than on matching a startup message: the wording of Kora's startup logs is not part of its contract and can change between versions, while `GET /system/readiness` returning `200` is a stable signal that the graph is up.

## Metadata { #metadata }

Some libraries need additional configuration for a native image, and `native-image` can only see what is declared as *reachability metadata*.
Kora ships the metadata for its own modules as `META-INF/native-image/<group>/<artifact>/` resources inside each module artifact, so it is applied automatically once the dependency is on the class path — see [Modules](#modules).

`native-image` reads only files with canonical names in such a directory:

- **`native-image.properties`** — build-time arguments, most importantly the class-initialization flags `--initialize-at-build-time` and `--initialize-at-run-time`. For example, `io.koraframework:logging-common` initializes `io.koraframework.logging.common.MDC` *at build time*, while `io.koraframework:netty-common` initializes the whole `io.netty` package *at run time*.
- **`reflect-config.json`** — classes, methods and fields accessed through reflection. For example, `io.koraframework:database-jdbc` registers the HikariCP constructor `MicrometerMetricsTrackerFactory(MeterRegistry)`, which the pool looks up reflectively when metrics are enabled.
- **`resource-config.json`** — resources that must be embedded into the binary. For example, `io.koraframework:config-hocon` bundles `reference.conf` / `application.conf`, and `io.koraframework:config-yaml` bundles `application.yaml` / `reference.yaml`, so the configuration is readable at runtime.
- **`proxy-config.json`**, **`serialization-config.json`**, **`jni-config.json`**, **`reachability-metadata.json`** — the remaining kinds, for dynamic proxies, serialization, JNI and the combined modern format.

!!! warning "A file with any other name is ignored silently"

    A classic mistake is naming the file **`reflection-config.json`** instead of **`reflect-config.json`**.
    `native-image` does not know that name: there is no error and no warning, the build succeeds, and the registrations are simply never applied — the application then fails at runtime in a place that has nothing to do with the file.
    Checking a project takes one command, and every hit is a dead file:

    ```shell
    find . -name "reflection-config.json"
    ```

### Repository { #metadata-repository }

If the application uses third-party libraries that need reachability metadata they do not ship themselves, enable loading it from the [GraalVM Reachability Metadata Repository](https://github.com/oracle/graalvm-reachability-metadata).

Enabling `metadataRepository` is enough for `nativeCompile`, but not for the [Docker](#docker) path: a bare `native-image -classpath application.jar` reads only what lies in the JAR.
To make both paths see the same metadata, collect it into the resources before packaging:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    graalvmNative {
        metadataRepository {
            enabled = true //(1)!
        }
    }

    processResources.dependsOn tasks.collectReachabilityMetadata //(2)!
    sourceSets.main { resources.srcDirs += "$buildDir/native-reachability-metadata" } //(3)!
    ```

    1.  Enables downloading metadata from the repository (default: `false`).
    2.  Makes resource processing wait for the metadata to be downloaded.
    3.  Adds the downloaded metadata to the resources, so it ends up inside the [fat JAR](#build-jar).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    graalvmNative {
        metadataRepository {
            enabled.set(true) //(1)!
        }
    }

    tasks.processResources {
        dependsOn(tasks.collectReachabilityMetadata) //(2)!
    }
    sourceSets.main {
        resources.srcDir(layout.buildDirectory.dir("native-reachability-metadata")) //(3)!
    }
    ```

    1.  Enables downloading metadata from the repository (default: `false`).
    2.  Makes resource processing wait for the metadata to be downloaded.
    3.  Adds the downloaded metadata to the resources, so it ends up inside the [fat JAR](#build-jar).

### Custom metadata { #metadata-custom }

When neither Kora nor the repository covers a class, supply the metadata by hand: put `native-image.properties`, `reflect-config.json` and/or `resource-config.json` under `src/main/resources/META-INF/native-image/<group>/<artifact>/` in your own application — `native-image` merges every such file found on the class path.

For example, to embed the Logback configuration and the HOCON config file into the binary, an application ships a `resource-config.json`:

```json title="src/main/resources/META-INF/native-image/io.koraframework.examples/logback/resource-config.json"
{
  "resources": {
    "includes": [
      { "pattern": "\\Qlogback.xml\\E" },
      { "pattern": "\\Qapplication.conf\\E" }
    ]
  }
}
```

and a `reflect-config.json` for the appender and encoder Logback instantiates by name from that XML:

```json title="src/main/resources/META-INF/native-image/io.koraframework.examples/logback/reflect-config.json"
[
  {
    "name": "io.koraframework.logging.logback.ConsoleTextRecordEncoder",
    "allDeclaredConstructors": true,
    "allPublicMethods": true
  },
  {
    "name": "io.koraframework.logging.logback.KoraAsyncAppender",
    "allDeclaredConstructors": true,
    "allPublicMethods": true
  },
  {
    "name": "ch.qos.logback.core.status.NopStatusListener",
    "allDeclaredConstructors": true
  }
]
```

The `<group>/<artifact>` path segments do not affect how the files are read — they are a namespace, and they should be unique (usually your application's group and module) so that files from different dependencies do not collide inside one JAR.

!!! warning "The application working on the JVM proves nothing about its metadata"

    The JVM does not read `META-INF/native-image` at all, so metadata cannot be declared unnecessary on the grounds that everything works without it under a regular JDK.
    The reverse mistake is just as common: when the group of an application changes, the `META-INF/native-image/<group>/` directory has to be renamed by hand, while the class names **inside** the files must stay untouched — they name classes of third-party libraries, which were not renamed.

### Agent { #metadata-agent }

For third-party libraries the repository does not cover, the standard way to discover the required metadata is the GraalVM *tracing agent*.
Run the same [fat JAR](#build-jar) that goes into the image on a regular JVM with the agent attached, exercise the code paths that use reflection, resources or proxies, and stop the application normally (`SIGTERM`) — otherwise the configuration is not written:

```shell
java -agentlib:native-image-agent=config-output-dir=/tmp/native-image-config \
     -jar build/libs/application-all.jar
```

The agent sees only the branches that were actually executed — that is a limitation of the approach, not a defect.
Its output is a hypothesis, not a ready-made patch: it contains hundreds of entries about third-party libraries whose proper place is inside those libraries.
Compare it with what the application already ships and move over only the entries that belong to the application:

```shell
diff -r /tmp/native-image-config src/main/resources/META-INF/native-image/<group>/<artifact>
```

Commit the selected entries as [custom metadata](#metadata-custom).

### Annotation hints { #metadata-hints }

The official examples generate part of the metadata from annotations with the third-party [GraalVM Hint Processor](https://github.com/GoodforGod/graalvm-hint) library.
This is **not** a Kora API — it is an external, optional convenience that is interchangeable with the hand-written [custom metadata](#metadata-custom) above.

Add the processor and the annotations:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        annotationProcessor "io.goodforgod:graalvm-hint-processor:1.2.0"
        compileOnly "io.goodforgod:graalvm-hint-annotations:1.2.0"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    plugins {
        kotlin("kapt")
    }

    dependencies {
        kapt("io.goodforgod:graalvm-hint-processor:1.2.0")
        compileOnly("io.goodforgod:graalvm-hint-annotations:1.2.0")
    }
    ```

    The processor is a `kapt` annotation processor, so for a Kotlin application it has to run next to the Kora `KSP` processor.
    If that is undesirable, write the same files by hand as [custom metadata](#metadata-custom) — the result is identical.

Then annotate the `@KoraApp` interface to declare the entrypoint and the resources to embed — the processor generates the matching `native-image` configuration at compile time:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.goodforgod.graalvm.hint.annotation.NativeImageHint;
    import io.goodforgod.graalvm.hint.annotation.ReflectionHint;
    import io.goodforgod.graalvm.hint.annotation.ResourceHint;
    import io.netty.channel.socket.nio.NioDatagramChannel;

    @ResourceHint(include = {"openapi/http-server.yaml"}) //(1)!
    @ReflectionHint(types = NioDatagramChannel.class) //(2)!
    @NativeImageHint(name = "application", entrypoint = Application.class) //(3)!
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

    1.  Resources embedded into the binary — generates a `resource-config.json`.
    2.  Classes registered for reflection — generates a `reflect-config.json`.
    3.  Name of the resulting binary and the class whose `main` method is the entry point — generates a `native-image.properties`, which is what lets the [Docker](#docker) build call `native-image` with nothing but a class path.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.goodforgod.graalvm.hint.annotation.NativeImageHint
    import io.goodforgod.graalvm.hint.annotation.ReflectionHint
    import io.goodforgod.graalvm.hint.annotation.ResourceHint
    import io.netty.channel.socket.nio.NioDatagramChannel

    @ResourceHint(include = ["openapi/http-server.yaml"]) //(1)!
    @ReflectionHint(types = [NioDatagramChannel::class]) //(2)!
    @NativeImageHint(name = "application", entrypoint = Application::class) //(3)!
    @KoraApp
    interface Application : HoconConfigModule, LogbackModule, UndertowPublicHttpServerModule {

        companion object {

            @JvmStatic
            fun main(args: Array<String>) {
                KoraApplication.run { ApplicationGraph.graph() }
            }
        }
    }
    ```

    1.  Resources embedded into the binary — generates a `resource-config.json`.
    2.  Classes registered for reflection — generates a `reflect-config.json`.
    3.  Name of the resulting binary and the class whose `main` method is the entry point — generates a `native-image.properties`, which is what lets the [Docker](#docker) build call `native-image` with nothing but a class path. The entry point must be a class with a static `main`, which is why the `main` method here lives in a companion object with `@JvmStatic` and `mainClass` in the build file is `io.koraframework.example.Application` rather than `…ApplicationKt`.

## Troubleshooting { #troubleshooting }

A native image that builds successfully but misbehaves at runtime is the normal failure mode, and the text of the exception is often misleading:
libraries catch `Throwable` while looking up providers and report a secondary error.
The canonical case is `java.lang.IllegalArgumentException: No XNIO provider found` on HTTP server startup, which meant not that the provider was absent but that its logger could not be created — `jboss-logging` loads a `<interface>_$logger` implementation reflectively.

Three steps, each producing a fact rather than a guess:

1. **Run the tracing [agent](#metadata-agent)** to see what is really loaded reflectively. Use the same fat JAR that goes into the image, on a GraalVM JDK, and exercise the whole scenario.
2. **Isolate with a minimal native probe.** A separate `main` that touches only the suspect library, without Kora, compiled by the same `native-image`. If the probe fails, the cause is in the library or in a module's metadata, and looking for it in the application code is pointless.
3. **Check that the metadata is read at all.** This step is skipped most often, and it is the only one that separates *the entry is incomplete* from *the file is not read*: add a registration whose effect is observable, rebuild the image, and see whether the behaviour changes; if it does not, put the same entry into a file with a [canonical name](#metadata) and repeat.

Frequent symptoms and where to look:

- *main class not found* while building the image — `mainClass` was assigned a string interpolation instead of the provider, see [Build](#build).
- the `Application` class is not found although `compileJava` succeeded — the `jar` task was disabled, see [Build](#build).
- `nativeCompile` fails while selecting a toolchain — no GraalVM of the required major version is visible to Gradle, see [Requirements](#requirements).
- the Gradle image works and the Docker one does not — the metadata is not inside the JAR, see [Repository](#metadata-repository).
- the application starts but the logs are empty or ignore the configuration — the Logback metadata was lost, see [Custom metadata](#metadata-custom).

## Modules { #modules }

Kora modules that ship their own native image configuration inside their artifacts:

- [Configuration](config.md) — `config-common`, `config-hocon`, `config-yaml`
- [Logback logging](logging-slf4j.md) — `logging-logback`
- [Logging](logging-aspect.md) — `logging-common`
- [HTTP server](http-server.md) — `http-server-undertow`
- [Netty](netty.md) — `netty-common`
- [Metrics](metrics.md) — `micrometer-module`
- [Tracing](tracing.md) — `opentelemetry-tracing`
- [JDBC database](database-jdbc.md) — `database-jdbc`
- [Cassandra database](database-cassandra.md) — `database-cassandra`
- [Cache](cache.md) — `cache-caffeine`
- [Kafka](kafka.md) — `kafka`
- [gRPC server](grpc-server.md) — `grpc-server`
- [OpenAPI display](openapi-management.md) — `openapi-management`

The settings are applied automatically once the dependency is on the class path, and no action is required from the application.
Kora modules that are not on this list ship no native image configuration because they do not need any: their code is generated at compile time and is statically reachable.

Ready-to-use examples of building with Gradle and Docker, together with black-box tests that run the resulting binary, are available in the examples repository:

- [`kora-java-graalvm-crud-jdbc`](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm/kora-java-graalvm-crud-jdbc) — native CRUD HTTP service on JDBC with a Caffeine cache
- [`kora-java-graalvm-crud-cassandra`](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm/kora-java-graalvm-crud-cassandra) — native CRUD HTTP service on Cassandra with a Redis cache
- [`kora-java-graalvm-kafka`](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm/kora-java-graalvm-kafka) — native Kafka consumer and producer service
