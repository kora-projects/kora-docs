---
search:
  exclude: true
hide:
- navigation
- toc
---

Kora is a framework for writing Java / Kotlin applications with a focus on Performance, Efficiency, Transparency.
Kora aims to provide sufficiently high-level declarative tools and abstractions for developers,
which are converted at compile time into hardware-performing and human-readable code.

`Performance` - Kora implies the creation of associated high-performance code at compile time,
avoiding the use of Reflection API, avoiding dynamic proxies, implementing fine-grained abstraction and free aspects,
leading to high application performance, low response time and the ability to handle a large number of requests per second.

`Efficiency` - The above factors and the fact that the dependency container is created
at compile time and initialized as parallel as possible,
allow for maximum resource utilization and low startup time.
This allows you to effectively use horizontal scaling practices
and maximize resource utilization not only within the application, but also within the entire cluster.

`Transparency` - Kora involves creating readable source code at compile time,
which, combined with subtle abstractions and free aspects, leads to high readability of code
and a developer's understanding of the underlying mechanisms of the framework if required,
minimal black box effect where neither voodoo magic nor guttersnipes are required.
Kora implies exactly one most effective solution per problem, which brings clarity and understanding to the development team.
This approach also allows you to achieve compatibility with GraalVM out of the box and validate the component container at compile time.

Kora provides all the tools needed for modern Java/Kotlin development:

- Dependency injection and inversion at compile time via annotations
- Aspect-oriented programming via annotations
- Pre-configurable integration modules
- Easy and rapid testing with [JUnit5](documentation/junit5.md)
- Simple, clear and detailed documentation backed by [service examples](examples/kora-examples.md)
