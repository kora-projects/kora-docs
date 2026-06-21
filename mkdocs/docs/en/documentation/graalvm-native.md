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

## Metadata { #metadata }

Some libraries require additional configuration for a native image: reflection, resources, or class initialization settings.
Some of these settings are already added to Kora modules through `META-INF/native-image` files.

If the application uses third-party libraries that require additional reachability metadata, you can enable loading it from the metadata repository:

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

Ready-to-use examples for building with Gradle and Docker are available in the [examples repository](https://github.com/kora-projects/kora-examples/tree/master/examples/graalvm).
