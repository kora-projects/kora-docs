---
description: "Explains Kora GraalVM Native Image notes and native build considerations for Kora applications. Use when working with GraalVM, native-image, reflection config, AOT, native build."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora GraalVM Native Image notes and native build considerations for Kora applications; key triggers include GraalVM, native-image, reflection config, AOT, native build."
---

GraalVM Native Image is a tool for `AOT compilation` that builds a Java application ahead of time into a standalone native image for the target platform.
Such an image starts without regular JVM warmup, but requires part of the information about code, resources, and reflection to be known at build time.

Kora creates its helper classes at compile time,
does not use the Reflection API at runtime,
does not use dynamic proxies,
does not generate bytecode at compile time or runtime.
This makes it easier to build Kora applications into a native image that starts faster and usually consumes less memory than a regular JVM application.
The main limitations of this kind of build are usually related not to Kora itself, but to third-party libraries that may require additional reflection, resource, or class initialization settings.

Therefore, Kora itself usually does not require additional configuration to build a native image.

## Requirements { #requirements }

A native build requires a [GraalVM](https://www.graalvm.org/) JDK: **GraalVM Community Edition** or **Oracle GraalVM**, version 21.
The [Gradle plugin](https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html) selects such a toolchain through the `javaLauncher` block shown in [Build](#build) (`JvmVendorSpec.matching("GraalVM Community")`),
so an ordinary JDK can drive the build while `native-image` itself runs on GraalVM.
When building outside the plugin (for example, the `native-image` command inside a [Docker](#docker) builder), the `native-image` tool must be available on `PATH` — the official GraalVM container images already ship it.

## Build { #build }

Example of building a native image using the [Gradle plugin](https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html):

===! ":fontawesome-brands-java: `Java`"

    Plugin `build.gradle`:
    ```groovy
    plugins {
        id "org.graalvm.buildtools.native" version "0.11.5"
    }
    ```

    Plugin setup `build.gradle`:
    ```groovy
    graalvmNative {
        binaries {
            main {
                imageName = "application"
                mainClass = "ru.tinkoff.kora.example.Application"
                debug = true
                verbose = true
                buildArgs.add("--report-unsupported-elements-at-runtime")
                javaLauncher = javaToolchains.launcherFor {
                    languageVersion = JavaLanguageVersion.of(21)
                    vendor = JvmVendorSpec.matching("GraalVM Community")
                }
            }
        }
        metadataRepository {
            enabled = true
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Plugin `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.graalvm.buildtools.native") version("0.11.5")
    }
    ```

    Plugin setup `build.gradle.kts`:
    ```groovy
    graalvmNative {
        binaries {
            named("main") {
                imageName.set("application")
                mainClass.set("ru.tinkoff.kora.example.Application")
                debug.set(true)
                verbose.set(true)
                buildArgs.add("--report-unsupported-elements-at-runtime")
                javaLauncher = javaToolchains.launcherFor {
                    languageVersion = JavaLanguageVersion.of(21)
                    vendor = JvmVendorSpec.matching("GraalVM Community")
                }
            }
        }
        metadataRepository {
            enabled.set(true)
        }
    }
    ```

Values added to `buildArgs` are passed straight to `native-image`. The most common ones:

- `--report-unsupported-elements-at-runtime` — defer errors about unsupported features to runtime instead of failing the build (used in the example above).
- `--no-fallback` — never produce a *fallback* image (one that silently bundles a JVM); fail the build instead if something cannot be compiled ahead of time. This flag is used when invoking `native-image` directly (see [Docker](#docker)).
- `debug` / `verbose` — extra build diagnostics; can be dropped for release builds.

Flags that Kora itself needs are contributed automatically by its modules and do **not** have to be added by hand:

- `ru.tinkoff.kora:application-graph` ships `--install-exit-handlers` and `--initialize-at-build-time` for the virtual-thread executor holder.
- `ru.tinkoff.kora:common` ships `--initialize-at-run-time` for `Context` and the Reactor context hook.

These come from `META-INF/native-image` resources inside the module JARs and are merged into the build once the dependency is on the class path (see [Metadata](#metadata)).

### Fat JAR { #build-jar }

`native-image` compiles a single class path into the binary, so a Kora application is usually assembled into one *fat JAR* first.
Kora relies on merged `META-INF/services` files (compile-time generated modules and extensions), therefore the JAR must be built with service-file merging — for example with the [Shadow](https://gradleup.com/shadow/) plugin:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    plugins {
        id "application"
        id "com.gradleup.shadow" version "9.4.1"
    }

    jar.enabled = false
    shadowJar {
        mergeServiceFiles()
        manifest {
            attributes "Main-Class": application.mainClass
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    plugins {
        id("application")
        id("com.gradleup.shadow") version("9.4.1")
    }

    tasks.jar {
        enabled = false
    }
    tasks.shadowJar {
        mergeServiceFiles()
        manifest {
            attributes["Main-Class"] = "ru.tinkoff.kora.example.Application"
        }
    }
    ```

The Shadow plugin produces an `*-all.jar` in `build/libs` that both the Gradle plugin and a direct `native-image` invocation can consume.

## Docker { #docker }

In CI and production the native image is usually produced with a two-stage Docker build: a GraalVM *builder* stage compiles the [fat JAR](#build-jar) into a binary, and a slim runtime stage ships only that binary.
This is how the [examples](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm) build their images, and it is independent of whether the application is written in Java or Kotlin:

```dockerfile
FROM ghcr.io/graalvm/native-image-community:21 AS builder

ARG TARGET_DIR=/opt/app
ARG SOURCE_DIR=build/libs
WORKDIR $TARGET_DIR

COPY $SOURCE_DIR/*-all.jar $TARGET_DIR/application.jar
RUN native-image --no-fallback -classpath $TARGET_DIR/application.jar

FROM ubuntu:noble AS runner

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

The builder stage compiles `application.jar` into a native binary named `application`, and the runtime stage runs it as a non-root user.
Build the fat JAR first (`./gradlew shadowJar`), then `docker build .`.

## Metadata { #metadata }

Some libraries need additional configuration for a native image, and `native-image` can only see what is declared as *reachability metadata*.
Kora ships the metadata for its own modules as `META-INF/native-image/<group>/<artifact>/` resources inside each module JAR, so it is applied automatically once the dependency is on the class path.

Three kinds of files cover the common cases:

- **`native-image.properties`** — build-time arguments, most importantly the class-initialization flags `--initialize-at-build-time` and `--initialize-at-run-time`. For example, Kora's `common` module initializes `ru.tinkoff.kora.common.Context` *at run time* (its thread/context state must not be baked into the image), while `application-graph` initializes the virtual-thread executor holder *at build time*.
- **`reflect-config.json`** — classes, methods and fields accessed through reflection. For example, Kora registers `Thread.ofVirtual` / `Executors.newVirtualThreadPerTaskExecutor` so Loom virtual threads work in the native image.
- **`resource-config.json`** — resources that must be embedded into the binary. For example, Kora bundles `reference.conf` / `application.conf` so HOCON configuration is readable at runtime.

### Repository { #metadata-repository }

If the application uses third-party libraries that need reachability metadata they do not ship themselves, enable loading it from the [GraalVM Reachability Metadata Repository](https://github.com/oracle/graalvm-reachability-metadata):

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    graalvmNative {
        metadataRepository {
            enabled = true
        }
    }

    processResources.dependsOn tasks.collectReachabilityMetadata
    sourceSets.main { resources.srcDirs += "$buildDir/native-reachability-metadata" }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    graalvmNative {
        metadataRepository {
            enabled.set(true)
        }
    }

    tasks.processResources {
        dependsOn(tasks.collectReachabilityMetadata)
    }
    kotlin.sourceSets.main {
        resources.srcDir(layout.buildDirectory.dir("native-reachability-metadata"))
    }
    ```

### Custom metadata { #metadata-custom }

When neither Kora nor the repository covers a class, supply the metadata by hand: drop `native-image.properties`, `reflect-config.json` and/or `resource-config.json` under `src/main/resources/META-INF/native-image/<group>/<artifact>/` in your own application — `native-image` merges every such file found on the class path.

For example, to embed the Logback configuration and the HOCON config file into the binary, an application can ship a `resource-config.json`:

```json title="src/main/resources/META-INF/native-image/ru.tinkoff.kora.examples/logback/resource-config.json"
{
  "resources": {
    "includes": [
      { "pattern": "\\Qlogback.xml\\E" },
      { "pattern": "\\Qapplication.conf\\E" }
    ]
  }
}
```

The `<group>/<artifact>` path segments are arbitrary but should be unique (usually your application's group and module) so that files from different dependencies do not collide.

### Agent { #metadata-agent }

For third-party libraries the repository does not cover, the standard way to discover the required metadata is the GraalVM *tracing agent*.
Run the application on a regular JVM with the agent attached, exercise the code paths that use reflection, resources or proxies, and the agent writes the corresponding config files:

```bash
java -agentlib:native-image-agent=config-output-dir=src/main/resources/META-INF/native-image/<group>/<artifact> \
     -jar build/libs/application-all.jar
```

Commit the generated files as [custom metadata](#metadata-custom).
This is the usual fallback when a native build fails at runtime with a missing-reflection or missing-resource error.

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

    ```groovy
    plugins {
        kotlin("kapt")
    }

    dependencies {
        kapt("io.goodforgod:graalvm-hint-processor:1.2.0")
        compileOnly("io.goodforgod:graalvm-hint-annotations:1.2.0")
    }
    ```

Then annotate the `@KoraApp` interface to declare the entrypoint and the resources to embed — the processor generates the matching `native-image` config at compile time:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.goodforgod.graalvm.hint.annotation.NativeImageHint;
    import io.goodforgod.graalvm.hint.annotation.ResourceHint;

    @ResourceHint(include = {"openapi/http-server.yaml"})
    @NativeImageHint(name = "application", entrypoint = Application.class)
    @KoraApp
    public interface Application {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.goodforgod.graalvm.hint.annotation.NativeImageHint
    import io.goodforgod.graalvm.hint.annotation.ResourceHint

    @ResourceHint(include = ["openapi/http-server.yaml"])
    @NativeImageHint(name = "application", entrypoint = Application::class)
    @KoraApp
    interface Application {

        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                KoraApplication.run(ApplicationGraph::graph)
            }
        }
    }
    ```

## Modules { #modules }

Modules for which Kora already provides the required part of native image configuration:

- [Configuration](config.md)
- [JSON](json.md)
- [Logback logging](logging-slf4j.md)
- [Probes](probes.md)
- [Metrics](metrics.md)
- [Tracing](tracing.md)
- [HTTP server](http-server.md)
- [HTTP client](http-client.md)
- [OpenAPI code generation](openapi-codegen.md)
- [OpenAPI display](openapi-management.md)
- [JDBC (Postgres) database](database-jdbc.md)
- [R2DBC (Postgres) database](database-r2dbc.md)
- [Vert.x database (Postgres)](database-vertx.md)
- [Cassandra database](database-cassandra.md)
- [Kafka](kafka.md)
- [gRPC server](grpc-server.md)
- [gRPC client](grpc-client.md)
- [Resilience](resilient.md)
- [Cache](cache.md)
- [Validation](validation.md)
- [Scheduling](scheduling.md)
- [Logging](logging-aspect.md)

Each of these modules ships its `META-INF/native-image` configuration inside its own JAR, so the settings are applied automatically once the dependency is on the class path; the core class-initialization and virtual-thread flags come from `ru.tinkoff.kora:application-graph` and `ru.tinkoff.kora:common`.

Ready-to-use examples for building with Gradle and Docker are available in the [examples repository](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm).
