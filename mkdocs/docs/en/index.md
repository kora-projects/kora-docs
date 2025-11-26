---
search:
  exclude: true
hide:
- navigation
- toc
---

Kora is a general purpose Java framework for writing server-side Java or Kotlin applications with a focus on Simplicity, Performance, Efficiency, Transparency.
Kora aims to provide reasonably high-level and simple declarative tools, thin and familiar high-level abstractions for developers,
which at compile time are translated into hardware-performant and human-readable code.
Both programming languages are first-level citizen languages for framework.

Framework is written in Java and has its own dependency container with inversion of control that works at compile time.
Kora is a cloud-oriented server framework and offers many modules for quickly building applications such as 
[HTTP server](documentation/http-server.md), [Kafka](documentation/kafka.md) consumers, 
database abstraction in the form of [repositories](documentation/database-common.md), resilient module and much more.

Kora also places great emphasis on:

- Observability, metrics and tracing of all modules according to the `OpenTelemetry` standard out of the box
- An approach where the contract is primary and code is generated from [OpenAPI specifications](documentation/openapi-codegen.md)

`Performance` - Kora generates high-performant code at compile time,
avoiding the use of Reflection API in runtime, avoiding dynamic proxies, implements thin fine-grained abstraction, free aspects,
only the most efficient modules implementations, all leading to high application performance,
All this leads to high performance, low response time and handling a large number of requests per second.
All this is already implemented in framework and does not require any manipulations or configurations on the part of developer.

<figure markdown="span">
  ![Kora TechEmpower](https://raw.githubusercontent.com/kora-projects/.github/refs/heads/master/storage/images/techempower_squiry_2024_01_24.jpeg "Kora TechEmpower"){ width=600 }
  <figcaption><a href="https://www.techempower.com/benchmarks/#section=test&resultsurl=https%3A%2F%2Fstatic.squiry.xyz%2Fresults%2F20240124114707.json&hw=ph&test=fortune">Kora TechEmpower external measurement</a></figcaption>
</figure>

`Efficiency` - All facts above and the fact that the dependency container is created
at compile time and initialized as parallel as possible, leads to low startup time.
This also allows effectively use horizontal scaling practices
and maximize resource utilization not only within the application, but also within the entire cluster.
Kora assumes exactly one most efficient solution per problem, uses and encourages approaches
that guide the developer to write clear and efficient code.
This utilization not only reduces infrastructure costs, but also significantly increases the stability of services
in the event of sudden peak loads and improves user requests latency.

<figure markdown="span">
  ![Kora startup benchmark](https://raw.githubusercontent.com/kora-projects/.github/refs/heads/master/storage/images/run_in_container_joker_2024.jpeg "Kora Startup"){ width=600 }
  <figcaption>Kora startup benchmark of PetClinic</figcaption>
</figure>

`Transparency` - Kora generates human-readable source code at compile time 
with fine-grained abstractions and free aspects, which leads to high readability of code
and a developer's understanding of the underlying mechanisms of the framework if required with no black box effect.
High readability, one most effective solution per problem, familiar high-level abstractions, 
all this gives transparency in the understanding of the code base on the part of the whole development team 
and makes it easy to immerse new developers, especially interns. Developers are given the opportunity to understand and control
how to work with the development tool, which allows them to use it effectively and not waste unnecessary time studying/learning
and memorizing tricky techniques for working with the framework.
Source code creation approach allows for dependency container checking at compile time 
and compatibility with [GraalVM out of the box](documentation/graalvm-native.md).

`Simplicity` - code transparency that Kora provides, coupled with simple and straightforward abstractions,
makes it easy to learn framework without the need for developers to spend years memorizing the "guts of the framework".
Kora aims to do all framework optimizations in-house, 
provide for you the most optimal implementations of integrations whether it is HTTP server or client,
take the work off you as a developer and provide only productive and efficient solutions out of the box.
Kora does not involve complex designs or abstractions,
but rather encourages the use of small and simple abstraction to solve small problems.
Subsequently, the aggregate of these simple abstractions can eventually solve large complex problems,
but are not difficult to understand when viewed in isolation,
without putting undue mental strain on the developer.
Kora implies exactly one most effective solution to one problem,
uses and encourages approaches that guide developers to write clear and effective code.
This simplifies development and increases the efficiency of the entire development team,
allowing developers to transfer context from their heads into clear code that is easy to write, read and maintain.

<figure markdown="span">
  ![Kora Simplicity](https://raw.githubusercontent.com/kora-projects/.github/refs/heads/master/storage/images/kora_test_example_joker_2024.jpeg "Kora Simplicity"){ width=600 }
  <figcaption>Kora simple and straightforward approach</figcaption>
</figure>

Kora provides all the tools needed for modern Java or Kotlin server-side development:

- Dependency injection and inversion via annotations
- Sufficiently high-level simple abstractions and development tools
- Transparent aspect-oriented programming via annotations
- Large set of preconfigured integrations
- Observability, tracing and metrics according to `OpenTelemetry` standard and logging for all modules
- Easy and rapid testing with [JUnit5](documentation/junit5.md)
- Simple and detailed documentation supported by [examples of working services](examples/kora-examples.md)
