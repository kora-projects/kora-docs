---
search:
  exclude: true
hide:
- navigation
- toc
---

Kora is a framework for writing Java / Kotlin server-side applications with a focus on Performance, Efficiency, Transparency.
Kora aims to provide sufficiently high-level declarative tools and abstractions for developers,
which at compile time are translated into hardware-performant and human-readable code.
Framework has its own dependency container with inversion of control that works at compile time.
Kora is a cloud-oriented framework and offers
many different modules for quickly building applications such as HTTP server, Kafka consumers, database abstraction in the form of repositories and much more.

`Performance` - Kora generates high-performant code at compile time,
avoiding the use of Reflection API in runtime, avoiding dynamic proxies, implements thin fine-grained abstraction, free aspects,
only the most efficient modules implementations, all leading to high application performance,
All this leads to high performance, low response time and handling a large number of requests per second.

`Efficiency` - All facts above and the fact that the dependency container is created
at compile time and initialized as parallel as possible, leads to low startup time.
This also allows effectively use horizontal scaling practices
and maximize resource utilization not only within the application, but also within the entire cluster.
Kora implies exactly one most efficient solution per problem,
approaches that help and guide the developer to write clear and efficient code.
It brings clarity and understanding to the development team
and allows to be offloaded context from the developer's head into understandable code that can be read by team.

`Transparency` - Kora generates human-readable source code at compile time 
with fine-grained abstractions and free aspects, which leads to high readability of code
and a developer's understanding of the underlying mechanisms of the framework if required with no black box effect.
Kora implies exactly one most effective solution per problem, which brings clarity and understanding to the development team.
This approach also allow to achieve compatibility with GraalVM out of the box and validate the dependency container at compile time.

Kora provides all the tools needed for modern Java/Kotlin server-side development:

- Dependency injection and inversion at compile time via annotations
- Declarative components generation at compile time via annotations
- Aspect-oriented programming via annotations
- Pre-configurable integration modules
- Easy and rapid testing with [JUnit5](documentation/junit5.md)
- Simple, clear and detailed documentation backed by [working service examples](examples/kora-examples.md)
