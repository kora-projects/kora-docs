---
search:
  exclude: true
---

Introduction to Kora is recommended to start with [Hello World example](hello-world.md) with explanations,
which shows the basics of setting up a project and creating a primitive example of a service.

A large number of service examples using various Kora modules can be found in this [repository](https://github.com/kora-projects/kora-examples).

Lots of examples of working with
[CRUD service](https://github.com/kora-projects/kora-examples/tree/master/kora-java-crud),
[HTTP server](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-server),
[HTTP client](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-client),
[JDBC database](https://github.com/kora-projects/kora-examples/tree/master/kora-java-database-jdbc),
[Kafka](https://github.com/kora-projects/kora-examples/tree/master/kora-java-kafka),
[OpenAPI code generation](https://github.com/kora-projects/kora-examples/tree/master/kora-java-openapi-generator-http-client) 
and various other Kora modules.

Each example service is accompanied by tests that can be used to verify the service's working properly and 
to see how to write primitive tests for certain functionality, both using 
[JUnit 5 extension](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/ComponentTests.java) 
and in black-box format via 
[TestContainers](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/BlackBoxTests.java).

=== “:fontawesome-brands-java: `Java`”

    You can create a new Java service by using [template on GitHub](https://github.com/kora-projects/kora-java-crud-template)

=== “:simple-kotlin: `Kotlin`”

    You can create a new Kotlin service using [template on GitHub](https://github.com/kora-projects/kora-kotlin-crud-template).
