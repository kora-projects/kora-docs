Kora creates its helper classes at compile time, so there should be no problem building a native image.

An example of building a native image using [plugin](https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html) for `gradle`:

=== ":fontawesome-brands-java: `Java`"

    Plugin `build.gradle`:
    ```groovy
    plugins {
        id "org.graalvm.buildtools.native" version "0.10.1"
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
                    languageVersion = JavaLanguageVersion.of(17)
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
        id("org.graalvm.buildtools.native") version("0.10.1")
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
                    languageVersion = JavaLanguageVersion.of(17)
                    vendor = JvmVendorSpec.matching("GraalVM Community")
                }
            }
        }
        metadataRepository {
            enabled.set(true)
        }
    }
    ```

Some libraries require additional configuration, some configurations are made in the framework.

Tested modules that should work without additional configuration:

- [Configuration](config.md)
- [Json](json.md)
- [Logback](logging-slf4j.md)
- [Probes](probes.md)
- [Metrics](metrics.md)
- [Tracing](tracing.md)
- [HTTP server](http-server.md)
- [HTTP client](http-client.md)
- [OpenAPI generation](openapi-codegen.md)
- [OpenAPI mapping](openapi-management.md)
- [JDBC (Postgres) database](database-jdbc.md)
- [R2DBC (Postgres) database](database-r2dbc.md)
- [Database Vertx (Postgres)](database-vertx.md)
- Cassandra database](database-cassandra.md)
- [Kafka](kafka.md)
- [gRPC Server](grpc-server.md)
- [gRPC client](grpc-client.md)
- [resilient](resilient.md)
- [Cache](cache.md)
- [Validation](validation.md)
- [Scheduling](scheduling.md)
- [Logging](logging-aspect.md)
