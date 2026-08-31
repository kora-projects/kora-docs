---
search:
  exclude: true
description: "Explains where to start with Kora guides and examples, how to choose between step-by-step guides and complete repository examples, and where to find working Java and Kotlin applications for HTTP, OpenAPI, JDBC, Cassandra, Kafka, gRPC, S3, cache, resilience, validation, observability and testing. Use when planning a learning path through the Kora documentation."
agent:
  use_when: "Use this file for Kora documentation navigation questions about guides, repository examples, starter templates and learning paths: which guide to read first, where the finished kora-examples applications live, and which sample covers HTTP, OpenAPI, JDBC, Cassandra, Kafka, gRPC, S3, caching, resilience, validation, observability or testing."
---

The best first step is the guided [Creating Your First Kora Application](getting-started.md) tutorial.
It walks through a minimal HTTP service and explains how `@KoraApp`, `@Component`, `@HttpController`, and `@HttpRoute`
fit together in a real Gradle project.

Use the documentation in two complementary ways:

- **Guides** are step-by-step tutorials. They explain the concepts, the code shape, and the reasoning behind each module.
- **Repository examples** are complete runnable services. They are useful when you want to compare your project with a working application or copy a proven setup.

Every guide and every example targets the same toolchain: `JDK` `25`, `Gradle` `9.5+`, the `io.koraframework:kora-bom` `BOM`,
and, for `Kotlin`, `Kotlin` `2.4.10` with `KSP` `2.3.11`.
The toolchain itself is described in [Compatibility](../documentation/general.md#compatibility) and [Build System](../documentation/general.md#build-system).

## Guided Learning Path { #guided-learning-path }

Start with the basics:

- [Creating Your First Kora Application](getting-started.md) - build and run the smallest useful HTTP service.
- [Dependency Injection Introduction](dependency-injection-introduction.md) and [Dependency Injection](dependency-injection.md) - learn Kora's compile-time graph, components, modules, tags, and factories.
- [HOCON Configuration](config-hocon.md), [YAML Configuration](config-yaml.md) and [JSON](json.md) - add the common foundation every service needs.

Then move to application features:

- HTTP and API: [HTTP Server](http-server.md), [Advanced HTTP Server](http-server-advanced.md), [HTTP Client](http-client.md), [Advanced HTTP Client](http-client-advanced.md), [OpenAPI HTTP Server](openapi-http-server.md), [Advanced OpenAPI HTTP Server](openapi-http-server-advanced.md), and [OpenAPI HTTP Client](openapi-http-client.md).
- Data access: [JDBC Database](database-jdbc.md), [Advanced JDBC Database](database-jdbc-advanced.md), and [Cassandra Database](database-cassandra.md).
- Integration modules: [Kafka Messaging](messaging-kafka.md), [gRPC Server](grpc-server.md), [Advanced gRPC Server](grpc-server-advanced.md), [gRPC Client](grpc-client.md), [Advanced gRPC Client](grpc-client-advanced.md), and [S3](s3.md).
- Production concerns: [Cache](cache.md), [Multi-Level Cache](cache-multi-level.md), [Resilience](resilient.md), and [Validation](validation.md).
- Observability: [Metrics](observability-metrics.md), [Tracing](observability-tracing.md), and [Probes](observability-probes.md).
- Testing: [Component Testing](testing-junit.md), [Integration Testing](testing-integration.md), and [Black-Box Testing](testing-black-box.md).

Many guides also link to finished Java and Kotlin applications in the `kora-examples` repository, so you can read the tutorial and immediately inspect the complete project structure.

## Repository Examples { #repository-examples }

A large number of complete services using different Kora modules can be found in the [kora-examples repository](https://github.com/kora-projects/kora-examples).

Useful starting points include:

===! ":fontawesome-brands-java: `Java`"

    - [Hello World service](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-helloworld)
    - [CRUD service](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-crud)
    - [HTTP server](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-http-server)
    - [HTTP client](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-http-client)
    - [JDBC database](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-database-jdbc)
    - [Kafka](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-kafka)
    - [OpenAPI HTTP server generation](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-openapi-generator-http-server)
    - [OpenAPI HTTP client generation](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-openapi-generator-http-client)
    - [PetClinic application](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-petclinic)

    Each example service includes tests that show how to verify the application with the
    [Kora JUnit 5 extension](https://github.com/kora-projects/kora-examples/blob/master/examples/java/kora-java-crud/src/test/java/io/koraframework/example/crud/ComponentTests.java)
    and how to run black-box checks with
    [Testcontainers](https://github.com/kora-projects/kora-examples/blob/master/examples/java/kora-java-crud/src/test/java/io/koraframework/example/crud/BlackBoxTests.java).

=== ":simple-kotlin: `Kotlin`"

    - [Hello World service](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-helloworld)
    - [CRUD service](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-crud)
    - [HTTP server](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-http-server)
    - [HTTP client](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-http-client)
    - [JDBC database](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-database-jdbc)
    - [Kafka](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-kafka)
    - [OpenAPI HTTP server generation](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-openapi-generator-http-server)
    - [OpenAPI HTTP client generation](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-openapi-generator-http-client)
    - [PetClinic application](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-petclinic)

    Each example service includes tests that show how to verify the application with the
    [Kora JUnit 5 extension](https://github.com/kora-projects/kora-examples/blob/master/examples/kotlin/kora-kotlin-crud/src/test/kotlin/io/koraframework/kotlin/example/crud/ComponentTests.kt)
    and how to run black-box checks with
    [Testcontainers](https://github.com/kora-projects/kora-examples/blob/master/examples/kotlin/kora-kotlin-crud/src/test/kotlin/io/koraframework/kotlin/example/crud/BlackBoxTests.kt).

The finished applications that the guides themselves build live next to the examples, under
[guides/java](https://github.com/kora-projects/kora-examples/tree/master/guides/java) and
[guides/kotlin](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin).

## Project Templates { #project-templates }

===! ":fontawesome-brands-java: `Java`"

    You can create a new Java service with the [Kora Java template](https://github.com/kora-projects/kora-java-template).

=== ":simple-kotlin: `Kotlin`"

    You can create a new Kotlin service with the [Kora Kotlin template](https://github.com/kora-projects/kora-kotlin-template).
