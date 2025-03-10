---
search:
  exclude: true
hide:
- navigation
- toc
---

Kora is a general purpose Java framework for writing server-side Java or Kotlin applications with a focus on Performance, Efficiency, Transparency, Simplicity.
Kora aims to provide reasonably high-level and simple declarative tools, thin and familiar high-level abstractions for developers,
which at compile time are translated into hardware-performant and human-readable code.
Both programming languages are first-level citizen languages for framework.

Framework is written in Java and has its own dependency container with inversion of control that works at compile time.
Kora is a cloud-oriented server framework and offers many modules for quickly building applications such as 
[HTTP server](documentation/http-server.md), [Kafka](documentation/kafka.md) consumers, 
database abstraction in the form of [repositories](documentation/database-common.md), telemetry for all modules, resilient module and much more.

`Performance` - Kora generates high-performant code at compile time,
avoiding the use of Reflection API in runtime, avoiding dynamic proxies, implements thin fine-grained abstraction, free aspects,
only the most efficient modules implementations, all leading to high application performance,
All this leads to high performance, low response time and handling a large number of requests per second.

`Efficiency` - All facts above and the fact that the dependency container is created
at compile time and initialized as parallel as possible, leads to low startup time.
This also allows effectively use horizontal scaling practices
and maximize resource utilization not only within the application, but also within the entire cluster.
Kora assumes exactly one most efficient solution per problem, uses and encourages approaches
that guide the developer to write clear and efficient code.
All of this makes the entire development team efficient and allows the context to be offloaded
from the developer's head into understandable code that is easy to write, and subsequently read and maintain.

`Transparency` - Kora generates human-readable source code at compile time 
with fine-grained abstractions and free aspects, which leads to high readability of code
and a developer's understanding of the underlying mechanisms of the framework if required with no black box effect.
High readability, one most effective solution per problem, familiar high-level abstractions, 
all this gives transparency in the understanding of the code base on the part of the whole development team 
and makes it easy to immerse new developers, especially interns.
Also, the source code creation approach allows for dependency container checking at compile time 
and compatibility with [GraalVM out of the box](documentation/graalvm-native.md).

`Simplicity` - code transparency that Kora provides, coupled with simple and straightforward abstractions,
makes it easy to learn framework without the need for developers to spend years memorizing the “guts and intricacies of the framework”.
Kora does not involve complex designs or abstractions,
but rather encourages the use of small and simple abstraction to solve small problems.
Subsequently, the aggregate of these simple abstractions can eventually solve large complex problems,
but are not difficult to understand when viewed in isolation,
without putting undue mental strain on the developer.

Kora provides all the tools needed for modern Java or Kotlin server-side development:

- Dependency injection and inversion via annotations
- Sufficiently high-level simple abstractions and development tools
- Aspect-oriented programming via annotations
- Large set of preconfigured integrations
- Tracing and metrics according to `OpenTelemetry` standard and logging for all modules
- Easy and rapid testing with [JUnit5](documentation/junit5.md)
- Simple and detailed documentation supported by [examples of working services](examples/kora-examples.md)
