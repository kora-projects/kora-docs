---
search:
  exclude: true
description: "Explains where to start with Kora examples and guides, how to choose guided tutorials versus complete repository examples, and where to find working Java and Kotlin applications. Use when working with getting started, guides, kora-examples, templates, JUnit tests, Testcontainers, HTTP, OpenAPI, JDBC, Kafka, gRPC, S3, cache, resilience, and observability."
agent:
  use_when: "Use this file for Kora documentation navigation questions about examples, guided tutorials, repository examples, starter templates, learning paths, and choosing the right Kora sample for HTTP, OpenAPI, database, Kafka, gRPC, S3, caching, resilience, observability, or testing."
---

The best first step is the guided [Creating Your First Kora Application](../guides/getting-started.md) tutorial.
It walks through a minimal HTTP service and explains how `@KoraApp`, `@Component`, `@HttpController`, and `@HttpRoute`
fit together in a real Gradle project.

Use the documentation in two complementary ways:

- **Guides** are step-by-step tutorials. They explain the concepts, the code shape, and the reasoning behind each module.
- **Repository examples** are complete runnable services. They are useful when you want to compare your project with a working application or copy a proven setup.

## Guided Learning Path

Start with the basics:

- [Creating Your First Kora Application](../guides/getting-started.md) - build and run the smallest useful HTTP service.
- [Dependency Injection Introduction](../guides/dependency-injection-introduction.md) and [Dependency Injection](../guides/dependency-injection.md) - learn Kora's compile-time graph, components, modules, tags, and factories.
- [HOCON Configuration](../guides/config-hocon.md), [YAML Configuration](../guides/config-yaml.md), [JSON](../guides/json.md), and [Validation](../guides/validation.md) - add the common foundation every service needs.

Then move to application features:

- HTTP and API: [HTTP Server](../guides/http-server.md), [Advanced HTTP Server](../guides/http-server-advanced.md), [HTTP Client](../guides/http-client.md), [Advanced HTTP Client](../guides/http-client-advanced.md), [OpenAPI HTTP Server](../guides/openapi-http-server.md), [Advanced OpenAPI HTTP Server](../guides/openapi-http-server-advanced.md), and [OpenAPI HTTP Client](../guides/openapi-http-client.md).
- Data access: [JDBC Database](../guides/database-jdbc.md), [Advanced JDBC Database](../guides/database-jdbc-advanced.md), and [Cassandra Database](../guides/database-cassandra.md).
- Integration modules: [Kafka Messaging](../guides/messaging-kafka.md), [gRPC Server](../guides/grpc-server.md), [Advanced gRPC Server](../guides/grpc-server-advanced.md), [gRPC Client](../guides/grpc-client.md), [Advanced gRPC Client](../guides/grpc-client-advanced.md), and [S3](../guides/s3.md).
- Production concerns: [Cache](../guides/cache.md), [Multi-Level Cache](../guides/cache-multi-level.md), [Resilience](../guides/resilient.md), and [Observability](../guides/observability.md).
- Testing: [Component Testing](../guides/testing-junit.md), [Integration Testing](../guides/testing-integration.md), and [Black-Box Testing](../guides/testing-black-box.md).

Many guides also link to finished Java and Kotlin applications in the `kora-examples` repository, so you can read the tutorial and immediately inspect the complete project structure.

## Repository Examples

A large number of complete services using different Kora modules can be found in the [kora-examples repository](https://github.com/kora-projects/kora-examples).

Useful starting points include:

- [CRUD service](https://github.com/kora-projects/kora-examples/tree/master/kora-java-crud)
- [HTTP server](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-server)
- [HTTP client](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-client)
- [JDBC database](https://github.com/kora-projects/kora-examples/tree/master/kora-java-database-jdbc)
- [Kafka](https://github.com/kora-projects/kora-examples/tree/master/kora-java-kafka)
- [OpenAPI HTTP server generation](https://github.com/kora-projects/kora-examples/tree/master/kora-java-openapi-generator-http-server)
- [OpenAPI HTTP client generation](https://github.com/kora-projects/kora-examples/tree/master/kora-java-openapi-generator-http-client)

Each example service includes tests that show how to verify the application with the
[Kora JUnit 5 extension](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/ComponentTests.java)
and how to run black-box checks with
[Testcontainers](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/BlackBoxTests.java).

## Project Templates

=== ":fontawesome-brands-java: `Java`"

    You can create a new Java service with the [Kora Java template](https://github.com/kora-projects/kora-java-template).

=== ":simple-kotlin: `Kotlin`"

    You can create a new Kotlin service with the [Kora Kotlin template](https://github.com/kora-projects/kora-kotlin-template).
