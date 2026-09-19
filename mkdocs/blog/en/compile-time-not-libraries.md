---
title: A Compile-Time Framework Does Not Mean Compile-Time-Only Libraries — Kora Framework
date: 2026-08-01
description: Why the Kora Framework's compile-time model does not forbid ordinary JVM libraries that use reflection, proxies, or runtime metadata.
search:
  exclude: true
---
# Compile-Time Framework Does Not Mean Compile-Time-Only Libraries { #compile-time-framework }

**August 1, 2026**

The phrase *compile-time framework* is easy to misunderstand.

It can sound as if the framework imposes a global architectural rule on the entire application: every dependency must be reflection-free, every library must generate code ahead of time, dynamic
proxies must never appear anywhere in the process, and runtime metadata must somehow be eliminated from the whole JVM. From that assumption, a much stronger claim often follows: if a third-party
library uses reflection, runtime class loading, proxy generation, or metadata discovery, then it either will not work with Kora or will require a substantial compatibility bridge.

That conclusion does not describe how Kora actually works.

The Kora Framework avoids reflection, runtime dependency discovery, dynamic proxies, and runtime bytecode generation in the parts of the stack that Kora itself controls. It builds the application graph at compile
time, generates repositories and HTTP adapters, produces compile-time AOP subclasses, generates mapping code, and turns framework wiring into ordinary Java or Kotlin bytecode before the process
starts.

That is Kora's implementation strategy.

It is not an application-wide ban on ordinary JVM behavior.

A Kora application is still a normal Java or Kotlin application running on a normal JVM. A library on the classpath can still call `Class.forName`, inspect annotations through reflection, invoke
methods through `Method.invoke`, create `java.lang.reflect.Proxy` instances, load resources dynamically, use `ServiceLoader`, create runtime-generated classes through a bytecode library, or depend on
another library that does any of those things. On HotSpot, those mechanisms remain normal JVM mechanisms.

This is the key distinction:

```text
Kora runtime model
        ≠
third-party library runtime model
        ≠
GraalVM Native Image constraints
```

Confusing these three layers produces a surprisingly large number of incorrect conclusions about Kora compatibility.

The correct model is much simpler:

> **Kora avoids reflection and dynamic proxies in its own runtime model, but that does not mean applications built with Kora are forbidden from using ordinary Java libraries that rely on reflection,
proxies or runtime metadata. Kora is still a normal JVM framework running normal JVM bytecode.**

Once that distinction is clear, several other myths disappear with it.

---

## Framework Implementation Strategy Is Not an Application-Wide Restriction { #framework-implementation-strategy }

Kora makes a strong architectural choice: where the framework already knows enough information at build time, it prefers to generate ordinary source code rather than rediscovering the same information
at runtime.

For dependency injection, that means building and validating the graph during compilation.

For declarative HTTP clients, it means generating the implementation rather than creating a reflective client proxy at startup.

For repositories, it means generating implementation code for SQL execution and mapping.

For AOP, it means generating subclasses around application components rather than constructing runtime interception proxies.

For serialization and mapping, it means generating readers, writers, and mappers where the framework owns that abstraction.

This can be summarized as:

```text
Framework-owned mechanics
        ↓
resolve at compile time where useful
        ↓
generate normal source
        ↓
run normal bytecode
```

This choice improves predictability because the framework does not need to rediscover its own application model after the JVM starts. It also makes generated behavior inspectable, avoids much runtime
framework machinery, and generally fits GraalVM Native Image well.

But none of this changes the semantics of the Java platform itself.

Kora does not install a security manager that disables reflection.

It does not rewrite the JDK.

It does not instrument third-party dependencies and force them to adopt Kora's design.

It does not require every library in the dependency graph to expose compile-time metadata or generated factories.

The framework is making a decision about **how Kora implements Kora**.

It is not legislating how every other library implements itself.

That difference is fundamental.

---

## "Kora Avoids Reflection" Is Not the Same as "Reflection Is Disabled" { #kora-avoids-reflection }

This is probably the most important misconception.

The statement:

```text
Kora avoids reflection at runtime
```

means:

```text
Kora does not need reflection
for its own normal runtime framework machinery.
```

It does **not** mean:

```text
The JVM process is incapable of reflection.
```

Suppose an ordinary library contains code such as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Class<?> type = Class.forName(className);
    var constructor = type.getDeclaredConstructor();
    constructor.setAccessible(true);

    Object value = constructor.newInstance();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val type = Class.forName(className)
    val constructor = type.getDeclaredConstructor()
    constructor.isAccessible = true

    val value = constructor.newInstance()
    ```

On a normal JVM, a Kora application executes that code exactly like another Java application would, subject to the usual Java module-access rules and JDK behavior.

Suppose another library does this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Object proxy = Proxy.newProxyInstance(
        interfaceType.getClassLoader(),
        new Class<?>[]{interfaceType},
        invocationHandler
    );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val proxy = Proxy.newProxyInstance(
        interfaceType.classLoader,
        arrayOf<Class<*>>(interfaceType),
        invocationHandler
    )
    ```

Again, on HotSpot there is nothing about Kora that disables `Proxy.newProxyInstance`.

A third library may scan annotations:

===! ":fontawesome-brands-java: `Java`"

    ```java
    for (var annotation : target.getAnnotations()) {
        // inspect metadata
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    for (annotation in target.annotations) {
        // inspect metadata
    }
    ```

That also continues to work.

Kora's own framework code does not suddenly become reflective merely because such a library is present, and the external library does not suddenly become non-reflective merely because Kora is present.

The two implementation strategies coexist in the same process.

---

## The Real Runtime Picture { #real-runtime-picture }

A realistic Kora service can easily look like this:

```text
Kora application
│
├── generated Kora dependency graph
│
├── generated HTTP mappings
│
├── generated repositories
│
├── generated AOP subclasses
│
├── generated serialization/mapping
│
├── business code
│
├── ordinary Java library A
│      └── uses reflection internally
│
├── ordinary Java library B
│      └── uses dynamic proxies internally
│
├── ordinary Java library C
│      └── loads resources dynamically
│
└── ordinary Java library D
       └── uses ServiceLoader
```

There is no contradiction here.

The Kora portion of the runtime remains generated and explicit.

The third-party libraries continue to use their own implementation strategies.

This is how the JVM ecosystem normally works: different libraries make different trade-offs.

One library may prefer reflection because its model is inherently dynamic.

Another may use bytecode generation because it wants runtime specialization.

Another may use generated classes produced by its own annotation processor.

Another may use handwritten direct Java.

A framework does not need to force a single philosophy onto every dependency in order to optimize the parts it owns.

---

## Kora's Own HTTP Stack Is a Good Counterexample to the Purity Myth { #kora-http-stack }

Kora itself demonstrates that its architecture is selective rather than ideological.

Its HTTP client abstraction can use multiple transport implementations. The current Kora 2 documentation includes transports based on OkHttp, Apache HttpClient 5, and a native implementation. OkHttp
is a mature external library with its own internal architecture, dependencies, connection pool, protocol handling, TLS behavior, HTTP/2 and HTTP/3 support. Apache HttpClient is another mature external
stack with its own abstractions and runtime internals.

Kora does not reimplement those libraries merely because they were not designed around Kora's compile-time model.

Instead, the architecture is approximately:

```text
Kora declarative client
        ↓
generated Kora request/response adapter
        ↓
Kora HttpClient abstraction
        ↓
OkHttp / Apache HttpClient / native transport
```

The top part can be compile-time generated.

The transport remains the transport.

That is an important clue about Kora's actual philosophy.

If compile-time purity were the goal, using an external transport whose implementation strategy is outside Kora's control would be architecturally suspect.

Instead, Kora explicitly supports it.

The practical rule is closer to this:

> **Where Kora owns the abstraction, it can remove unnecessary runtime machinery. Where an existing Java library already solves the problem well, integrate it rather than reproducing the ecosystem.**

That is a very different philosophy from "everything must be compile-time."

---

## Compile-Time Framework Does Not Mean Closed JVM { #compile-time-framework-closed-jvm }

It helps to think in terms of boundaries.

Kora controls:

```text
application graph
generated dependency wiring
generated framework aspects
generated repositories
generated HTTP contracts
generated mapping code
framework lifecycle integration
framework telemetry integration
```

Kora does not control every implementation detail of:

```text
database driver
JDBC pool
Kafka client
gRPC runtime
OkHttp
Apache HttpClient
Logback
Netty
cloud vendor SDK
security library
serialization library
native SDK
proprietary company library
```

Those libraries remain ordinary Java dependencies.

This is not an accidental escape hatch. It is necessary for any practical JVM framework.

The Java ecosystem is too large and too heterogeneous for a framework to own the implementation model of every dependency.

The useful architectural goal is therefore not uniformity.

It is **local optimization**.

---

## Three Questions That Should Never Be Collapsed { #three-questions }

When evaluating a library for a Kora service, ask three separate questions.

## 1. Does the library work on the JVM? { #does-library-work-on-jvm }

This is the ordinary compatibility question.

Does it support the JDK version?

Does it fit the threading model?

Does its API match the application's needs?

Does it have acceptable licensing, performance, and maintenance?

Does it conflict with other dependencies?

This is the same kind of question any Java application asks.

## 2. Does the library integrate cleanly into Kora's application graph? { #library-integrate-into-graph }

This is a much smaller question.

Can its main client or service be constructed through a factory?

Does it need configuration?

Does it need lifecycle?

Does it need telemetry or probes?

Does it expose normal Java objects that can be injected?

In many cases the answer is trivial:

```text
Config
  ↓
factory
  ↓
native client
  ↓
@Module
  ↓
application graph
```

## 3. Does the library work in GraalVM Native Image? { #library-graalvm-native-image }

This is a separate deployment question.

Does it use reflection?

Does it load classes dynamically?

Does it generate bytecode at runtime?

Does it use JNI?

Does it depend on resources that Native Image cannot discover automatically?

Does it ship reachability metadata?

Does the GraalVM metadata repository cover it?

These three questions overlap occasionally, but they are not equivalent.

A library can:

```text
work perfectly on HotSpot
+
integrate trivially with Kora
+
require Native Image metadata
```

There is nothing unusual about that combination.

---

## HotSpot and Native Image Are Different Deployment Models { #hotspot-native-image-deployment }

The distinction becomes clearest when reflection is involved.

On a regular JVM:

```text
HotSpot JVM
      ↓
reflection-heavy library
      ↓
normal JVM behavior
```

Reflection information remains available because classes and metadata exist at runtime and the VM can perform reflective lookup dynamically.

With Native Image:

```text
GraalVM Native Image
      ↓
closed-world analysis
      ↓
reflection-heavy library
      ↓
may require reachability metadata
```

Native Image performs ahead-of-time analysis and cannot always infer reflective access that is assembled dynamically from strings, configuration files, plugin registries, or runtime control flow.

That means a library may need additional metadata describing:

- reflectively accessed classes;
- constructors;
- methods;
- fields;
- dynamic proxies;
- resources;
- serialization;
- JNI;
- runtime class initialization.

This is a GraalVM concern.

It would exist if the application used another framework.

Kora merely starts from a framework architecture that already creates less of this burden itself.

---

## Kora Compatibility and Native Image Compatibility Are Different Questions { #kora-native-image-compatibility }

This deserves to be stated directly:

> **Kora compatibility and Native Image compatibility should not be treated as the same question.**

Suppose a library uses:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Class.forName(...)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    Class.forName(...)
    ```

based on a configuration property.

On HotSpot, that can be completely ordinary.

The Kora graph can create the library through a factory:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface VendorModule {

        default VendorClient vendorClient(VendorConfig config) {
            return VendorClient.create(config);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface VendorModule {

        fun vendorClient(config: VendorConfig): VendorClient {
            return VendorClient.create(config)
        }
    }
    ```

The application runs normally.

If the same service is later compiled into a native executable, GraalVM may need to know which classes can be referenced through that `Class.forName` path.

That is not a Kora bridge problem.

It is a reachability problem.

The integration into Kora may still consist of a single factory method.

---

## Native Image Is an Optimization Target, Not a Framework Law { #native-image-optimization-target }

A Kora service does not have to run as a Native Image.

Kora runs on a normal JVM.

That is important because discussions about compile-time frameworks often slide unconsciously from:

```text
Kora uses compile-time generation
```

to:

```text
Kora applications should be native executables
```

and then to:

```text
every dependency must satisfy native-image restrictions
```

Those are three separate decisions.

A team may choose:

```text
Kora + HotSpot
```

because it values:

- fast startup;
- small framework overhead;
- direct JVM execution;
- virtual threads;
- generated wiring;
- normal JIT optimization.

Another team may choose:

```text
Kora + Native Image
```

because startup latency, memory footprint, deployment density, or a serverless/scale-to-zero environment makes native compilation useful.

The second team must evaluate its dependency set against Native Image requirements.

The first team does not suddenly inherit those restrictions merely because Kora itself is Native Image friendly.

---

## Why Kora Fits Native Image Well { #why-kora-fits-native-image }

Kora does have a real architectural advantage when Native Image is a requirement.

Its own normal runtime does not depend heavily on mechanisms that are difficult for closed-world analysis:

- runtime classpath scanning;
- reflective dependency injection;
- runtime AOP proxy generation;
- dynamically generated repository implementations;
- runtime HTTP client proxy generation.

Instead, Kora generates the necessary source at compile time.

That means the framework itself contributes relatively little hidden reachability.

Conceptually:

```text
Typical runtime-heavy framework

application
   ↓
framework runtime discovery
   ↓
reflection metadata
   ↓
proxy metadata
   ↓
runtime-generated behavior
```

versus:

```text
Kora

application
   ↓
generated source
   ↓
normal bytecode
```

This does not guarantee that every application dependency is Native Image compatible.

It means the framework starts from a cleaner baseline.

That is a much more precise advantage.

---

## Third-Party Reflection Exists Even Inside Kora-Supported Modules { #third-party-reflection-kora-modules }

There is an especially useful example in Kora's own Native Image documentation.

Kora's JDBC support can use HikariCP. HikariCP may perform reflective lookup in some integration paths, including metrics-related construction. Kora handles this for Native Image by shipping the
required reachability metadata in the module artifact.

That is extremely revealing.

If Kora's philosophy were:

```text
No reflection may exist anywhere
```

the existence of such metadata would be an architectural violation.

Instead, Kora's approach is pragmatic:

```text
Kora itself avoids runtime reflection
+
third-party dependency uses reflection
+
native-image metadata describes that dependency
```

There is no contradiction.

The framework optimizes what it controls and integrates what it does not.

---

## Logback Is Another Good Example { #logback-example }

Logging libraries frequently perform runtime discovery, configuration parsing, plugin lookup, or reflective class creation.

Kora's Native Image documentation explicitly discusses resource and reflection metadata for logging-related classes.

Again, this demonstrates that Kora does not pretend the whole Java ecosystem follows one runtime model.

The actual architecture is:

```text
Kora logging integration
       ↓
Logback
       ↓
Logback's own runtime behavior
```

When compiling to Native Image, metadata is added where GraalVM needs help.

On a normal JVM, that metadata is irrelevant.

The JVM does not even consume the Native Image metadata directory as part of ordinary execution.

That separation is exactly the point.

---

## Reachability Metadata Is Not a "Kora Bridge" { #reachability-metadata }

The word *bridge* can make ordinary integration sound more complex than it is.

For Native Image, metadata is often simply a description of dynamic behavior that GraalVM cannot infer.

Examples include:

```text
reflect-config.json
resource-config.json
proxy-config.json
serialization-config.json
jni-config.json
```

This is not a replacement API.

It is not an adapter translating the library into Kora concepts.

It does not mean the application must rewrite the library.

It is build metadata for a different execution environment.

A team may need to provide or consume that metadata whether Kora is involved or not.

---

## The GraalVM Reachability Metadata Repository Changes the Ecosystem Story { #graalvm-reachability-repository }

Native Image compatibility has also become less framework-specific over time.

There is now an ecosystem-level mechanism for sharing reachability metadata.

A library can ship metadata itself.

A framework integration can ship metadata for a dependency it knows about.

The GraalVM Reachability Metadata Repository can provide metadata externally.

An application can add custom metadata for its own unusual paths.

This means Native Image compatibility increasingly looks like a dependency property rather than a requirement for every framework to maintain a proprietary hint system for the entire Java ecosystem.

Kora benefits from that ecosystem rather than trying to replace it.

---

## The Native Image Tracing Agent Is Another Escape Hatch { #native-image-tracing-agent }

If a third-party library's dynamic behavior is not already covered, GraalVM provides a tracing agent that can observe reflective access, resource loading, proxy generation, and related behavior while
the application runs on a JVM.

A team can exercise the relevant scenarios and generate metadata from observed usage.

That does not solve every native-image problem automatically, but it demonstrates the right ownership model:

```text
library behavior
      ↓
GraalVM analysis / metadata
```

not:

```text
library behavior
      ↓
Kora must reimplement library
```

The deployment model determines the compatibility work.

---

## Dynamic Class Loading Is Where the Difference Becomes More Serious { #dynamic-class-loading }

Reflection is not the only Native Image concern.

Some libraries dynamically load entirely unknown classes or generate classes at runtime.

For example:

```text
configuration string
      ↓
classloader
      ↓
load arbitrary implementation
```

or:

```text
runtime schema
      ↓
bytecode generator
      ↓
new class
```

HotSpot handles these patterns naturally because the JVM remains open to runtime class loading.

Native Image works from a closed-world assumption and therefore cannot always reproduce arbitrary unknown runtime loading.

If a library fundamentally depends on loading bytecode that did not exist when the native executable was built, the challenge may be architectural rather than merely metadata-related.

Again, the correct conclusion is:

```text
problem:
Native Image execution model
```

not:

```text
problem:
Kora compile-time DI
```

On a standard JVM, the library may still be perfectly usable with Kora.

---

## JNI Is Also a Separate Constraint { #jni-constraint }

JNI provides another example of why the three layers must be separated.

A library can use native code through JNI and work normally on HotSpot.

Kora can inject its client like any other Java object.

For Native Image, additional configuration and platform compatibility may be required.

None of that means Kora's application graph is incompatible with JNI.

It means the final executable has a native interoperability requirement.

The same distinction applies to:

- JNA;
- Panama-based integrations;
- native database clients;
- cryptographic providers;
- hardware SDKs;
- compression libraries.

Framework DI and deployment format are different concerns.

---

## Runtime Bytecode Generation Does Not Automatically Break Kora Either { #runtime-bytecode-generation }

Java libraries sometimes use Byte Buddy, ASM, CGLIB, Javassist, or similar tooling.

On the JVM, such a library can run inside a Kora application.

Kora's own runtime does not begin using runtime-generated proxies simply because one dependency does.

The costs remain localized.

For Native Image, runtime bytecode generation may be unsupported or require a different approach.

Again:

```text
HotSpot compatibility
≠
Native Image compatibility
```

Kora's compile-time design does not collapse the two.

---

## One Reflective Dependency Does Not Turn Kora Into a Reflective Framework { #reflective-dependency }

Another common overstatement is that a reflection-heavy dependency "destroys Kora's main advantage."

That is not how performance composition works.

An application's cost is roughly the sum of many components:

```text
Application cost
=
framework overhead
+ business code
+ database work
+ networking
+ serialization
+ logging
+ telemetry
+ third-party libraries
+ operating system
+ external services
```

If one library performs expensive reflection on a specific execution path, that path pays for it.

That does not retroactively change how the dependency graph is wired.

It does not turn generated HTTP mappings into runtime reflection.

It does not turn generated repositories into proxies.

It does not cause Kora AOP to become dynamic.

The rest of the stack remains what it was.

---

## Performance Is Local Before It Is Global { #performance-is-local }

Suppose a service handles:

```text
HTTP request
   ↓
Kora generated route
   ↓
service
   ↓
third-party rules engine
   ↓
repository
```

If the rules engine uses reflection heavily, the total request latency may include that cost.

But the decomposition remains:

```text
Kora route cost
+
rules engine cost
+
repository cost
```

If the rules engine becomes a bottleneck, profile the rules engine.

Replacing Kora's compile-time DI with runtime reflection would not make the rules engine cheaper.

Similarly, the presence of the rules engine does not erase savings elsewhere.

This is the normal way systems performance should be analyzed.

---

## Startup Performance Is Compositional Too { #startup-performance }

The same applies at startup.

Kora may start quickly because its graph and framework adapters are already generated.

A third-party library may then spend two seconds scanning a classpath or loading metadata.

The application startup time becomes:

```text
Kora initialization
+
third-party initialization
```

The library can dominate the total.

But that does not mean Kora's compile-time startup design ceased to exist.

It means the application selected a library with expensive initialization.

That distinction matters because it identifies the correct optimization target.

---

## Memory Cost Is Also Additive { #memory-cost-additive }

Suppose Kora uses little runtime metadata for DI and AOP, but a third-party engine keeps a large reflective metadata cache.

The total process includes that memory.

Kora cannot remove memory used by a dependency it does not control.

But its own lower overhead still leaves more of the memory budget available to the dependency and business workload.

This is one reason framework efficiency remains useful even when application libraries are not equally lightweight.

---

## A Framework Can Minimize Its Own Overhead Without Controlling Everything { #framework-minimize-overhead }

This leads to an important principle:

> **A framework can minimize its own overhead without pretending it controls the implementation strategy of every library in the JVM ecosystem.**

This is a much more realistic goal than runtime purity.

The framework controls its own recurring machinery.

The application team controls library selection.

The library controls its internal architecture.

The deployment platform adds its own constraints.

These layers should be optimized independently where possible.

---

## Compile-Time Purity Would Be a Bad Goal { #compile-time-purity-bad-goal }

Imagine Kora required every dependency to satisfy:

```text
no reflection
no proxies
no runtime metadata
no dynamic class loading
no runtime generated code
```

The result would not merely be restrictive.

It would exclude a large amount of useful Java software for reasons unrelated to application correctness.

Teams would lose mature SDKs, specialized protocol libraries, logging systems, drivers, testing tools, and vendor clients unless every dependency were rewritten into a Kora-approved style.

That would be an ecosystem purity test.

Kora does not need one.

The framework's advantage comes from removing avoidable runtime machinery from the framework itself, not from policing unrelated libraries.

---

## Selective Compile-Time Work Is the More Powerful Model { #selective-compile-time }

The real model is:

```text
Known, framework-owned structure
        ↓
compile-time generation

Unknown or library-owned behavior
        ↓
normal library runtime model
```

That is selective.

For example:

```text
Kora knows controller signature
→ generate handler

Kora knows repository interface
→ generate implementation

Kora knows dependency graph
→ generate wiring

Kora does not own OkHttp internals
→ call OkHttp normally

Kora does not own vendor SDK internals
→ call vendor SDK normally
```

This division produces leverage without demanding ecosystem conformity.

---

## Mature External Libraries Are Often Better Than Framework Reimplementations { #mature-external-libraries }

This is closely related to avoiding NIH.

Suppose a mature library already provides:

- battle-tested protocol implementation;
- connection pooling;
- TLS;
- retries;
- compression;
- proxies;
- authentication;
- performance tuning;
- years of compatibility fixes.

Reimplementing all of that merely to ensure "compile-time purity" would usually be wasteful.

A better framework can wrap or compose the mature library through a thin boundary.

Kora's OkHttp and Apache HttpClient integrations demonstrate exactly that pattern.

The framework-specific layer handles:

- configuration;
- DI;
- telemetry;
- common Kora client contracts.

The underlying transport remains a mature independent library.

---

## A Thin Integration Boundary Is Usually Enough { #thin-integration-boundary }

Consider an unsupported vendor SDK.

The integration can often be:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("vendor")
    public interface VendorConfig {
        String endpoint();

        String token();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("vendor")
    interface VendorConfig {
        fun endpoint(): String

        fun token(): String
    }
    ```

and:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface VendorModule {

        default VendorClient vendorClient(VendorConfig config) {
            return VendorClient.builder()
                .endpoint(config.endpoint())
                .token(config.token())
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface VendorModule {

        fun vendorClient(config: VendorConfig): VendorClient {
            return VendorClient.builder()
                .endpoint(config.endpoint())
                .token(config.token())
                .build()
        }
    }
    ```

If the client needs cleanup:

```text
factory
   ↓
lifecycle wrapper / AutoCloseable
```

If the application needs readiness:

```text
client
   ↓
ReadinessProbe
```

If telemetry is missing:

```text
small wrapper
   ↓
OpenTelemetry / metrics
```

At no point does the SDK have to become "compile-time Kora code."

---

## Reflection Inside the SDK Is Its Own Concern { #reflection-inside-sdk }

Suppose the vendor SDK internally discovers credential providers through reflection.

On HotSpot:

```text
Kora
  ↓
VendorClient
  ↓
reflection-based provider discovery
```

works as normal Java, assuming the SDK itself supports the JDK.

If Native Image later becomes a deployment requirement, evaluate whether the SDK ships the necessary metadata.

The Kora integration does not have to change conceptually.

The build may need metadata.

That is a clean separation of responsibilities.

---

## Dynamic Proxies Inside a Library Are Similar { #dynamic-proxies-inside-library }

Suppose an SDK exposes an interface and creates a runtime proxy internally:

===! ":fontawesome-brands-java: `Java`"

    ```java
    MyApi api = sdk.create(MyApi.class);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val api: MyApi = sdk.create(MyApi::class.java)
    ```

On the JVM, Kora can inject `MyApi` or the SDK factory like any other object.

Kora does not need to generate the proxy itself.

If the application uses Native Image, proxy interfaces may need to be registered in Native Image configuration.

Again, this is deployment metadata, not a Kora architectural incompatibility.

---

## Runtime Annotation Scanning Inside a Library Is Similar Too { #runtime-annotation-scanning }

A validation engine, serializer, ORM, or SDK may inspect annotations dynamically.

That does not conflict with Kora's generated DI graph.

The two systems can coexist:

```text
Kora annotation processing
        ↓
generated graph

third-party library
        ↓
runtime annotation scanning
```

The word *annotation* in both mechanisms does not make them mutually exclusive.

They operate at different times for different purposes.

---

## The Cost Is Only a Problem If It Is Actually a Problem { #cost-is-a-problem }

Engineering should resist ideological performance arguments.

Reflection can be slow relative to a direct call.

But a reflective operation executed once during startup may be completely irrelevant.

A proxy dispatch adding nanoseconds or microseconds may be irrelevant if the operation then performs a 20 ms network call.

A metadata scan may matter enormously in a cold-start-sensitive environment and be irrelevant in a long-running batch service.

The correct question is:

```text
Where is the cost?
How often does it occur?
Is it on the critical path?
Does it matter for the SLO?
```

not:

```text
Does this library use reflection?
```

Kora removes reflection from its own general framework machinery because that machinery appears everywhere and can be resolved earlier.

That does not imply every reflective use in the JVM ecosystem is automatically unacceptable.

---

## Compile-Time Generation Is About Repeated Framework Work { #compile-time-repeated-work }

Dependency injection is an excellent example.

If the framework already knows at compilation:

```text
A depends on B
B depends on C
```

rediscovering those relationships through reflection every process startup provides little value for a normal service.

Kora resolves them early.

That is a high-leverage optimization because graph construction is a framework-wide concern.

A third-party SDK doing a small reflective lookup for an optional extension mechanism is a different category of work.

Not all reflection has the same architectural significance.

---

## AOP Is Similar { #aop-is-similar }

Kora generates AOP subclasses because method interception is a framework-owned mechanism and can be constructed ahead of time.

A third-party client may still use a proxy internally.

These facts can coexist:

```text
Application service
   ↓
Kora generated AOP subclass
   ↓
SDK interface
   ↓
SDK dynamic proxy
```

Only the SDK call boundary uses its proxy.

Kora's own aspect behavior remains generated and inspectable.

---

## Serialization Can Be Mixed Too { #serialization-mixed }

An application may use Kora-generated JSON mapping for most HTTP APIs and also depend on a library that uses Jackson reflection internally.

That is technically unremarkable.

For example:

```text
public API
  ↓
Kora generated JSON mapping

vendor SDK
  ↓
Jackson reflection
```

The service can choose the right tool for each boundary.

Again, framework architecture does not need to impose global uniformity.

---

## Testing Libraries Are an Obvious Example { #testing-libraries }

Many test frameworks and mocking libraries use reflection, instrumentation, agents, proxies, or runtime bytecode generation.

A rule banning those mechanisms application-wide would make ordinary JVM testing unnecessarily difficult.

Kora tests still run inside the normal Java ecosystem.

Mockito, JUnit extensions, Testcontainers, bytecode instrumentation tools, profiling agents, and test fixtures can have runtime behavior completely different from Kora's production DI model.

That is expected.

---

## Development Tooling Is Another Layer { #development-tooling }

The same application may use:

- Java agents;
- profilers;
- debugger instrumentation;
- coverage instrumentation;
- hot reload tooling;
- JFR;
- IDE-generated proxies;
- test runtime transforms.

Kora does not require those tools to share its compile-time strategy.

This illustrates why the phrase *compile-time framework* should be scoped carefully.

It describes framework architecture, not the metaphysics of the process.

---

## The JVM Remains the Platform { #jvm-remains-platform }

This is the most important conceptual anchor.

Kora does not replace the JVM.

It runs on it.

Therefore the ordinary Java ecosystem remains available:

```text
class loading
reflection
ServiceLoader
method handles
proxies
JNI
agents
standard libraries
third-party libraries
```

Kora simply tries not to depend on the more dynamic mechanisms when it can generate simpler direct code for framework-owned tasks.

That is a performance and transparency strategy.

Not a compatibility restriction.

---

## Native Image Changes the Platform Assumptions { #native-image-platform-assumptions }

When using Native Image, the execution environment changes.

The resulting binary is still built from Java code, but the assumptions are different because the program is analyzed ahead of time.

Dynamic behavior that HotSpot discovers naturally may need explicit description.

This is why Kora's Native Image documentation discusses:

- reflection metadata;
- resource metadata;
- proxy metadata;
- serialization metadata;
- JNI metadata;
- class initialization.

Those requirements come from Native Image's closed-world analysis.

The same library may therefore have two compatibility profiles:

```text
HotSpot:
works directly

Native Image:
works with metadata
```

or:

```text
HotSpot:
works directly

Native Image:
unsupported due to fundamental dynamic behavior
```

That does not change whether the library is usable in a JVM-based Kora service.

---

## Native Image Compatibility Should Be Dependency-by-Dependency { #native-image-dependency-by-dependency }

If Native Image is required, treat compatibility as a dependency inventory.

For each important library, ask:

```text
Does it officially support Native Image?
Does it ship reachability metadata?
Is it covered by the metadata repository?
Does it use dynamic class loading?
Does it generate bytecode?
Does it need JNI?
Does it use resources dynamically?
```

This is the same due diligence required by other Java stacks targeting Native Image.

Kora's advantage is that the framework itself introduces relatively few additional surprises.

---

## A Cleaner Baseline Matters { #cleaner-baseline }

Consider two applications with the same third-party SDK.

Application A uses a runtime-heavy framework that itself needs extensive reflection, proxies, runtime scanning, and framework-specific native hints.

Application B uses Kora, whose graph, aspects, repositories, and HTTP adapters are already generated.

Both may need metadata for the SDK.

But Application B starts from:

```text
third-party SDK metadata
```

rather than:

```text
framework metadata
+
framework proxy metadata
+
framework discovery metadata
+
third-party SDK metadata
```

The exact real-world difference depends on the frameworks and modules involved, but the architectural baseline is cleaner.

That is the fair Native Image claim.

---

## "No Reflection in Kora" Should Be Read Precisely { #no-reflection-precisely }

A technically precise interpretation is:

> Kora's normal framework runtime does not rely on reflection for its own dependency graph and generated framework mechanisms.

That is different from:

> No bytecode in a Kora process may invoke the Reflection API.

The first statement is an architectural property.

The second would be a platform restriction.

Kora makes the first claim.

---

## "No Dynamic Proxies" Should Also Be Read Precisely { #no-dynamic-proxies-precisely }

Similarly:

```text
Kora does not use dynamic proxies for its framework AOP/DI model
```

does not mean:

```text
Proxy.newProxyInstance is illegal in a Kora process
```

If a dependency uses dynamic proxies, the JVM will run them.

Kora's own application graph does not become proxy-based because of that.

Again, scope matters.

---

## "No Runtime Bytecode Generation" Is Also Scoped { #no-runtime-bytecode-scoped }

Kora avoids runtime bytecode generation for its own framework mechanisms.

But if a library uses Byte Buddy at runtime on HotSpot, Kora does not disable Byte Buddy.

The library's support for Native Image is another question.

The correct reading is always:

```text
Kora implementation strategy
```

not:

```text
global process restriction
```

---

## What Would Actually Make a Library Hard to Use With Kora? { #library-hard-to-use }

A library can still be awkward for Kora, but usually for ordinary architectural reasons.

For example, it may:

- require a global static singleton;
- assume it owns process startup;
- install an incompatible event loop;
- require a specific thread-affinity model;
- hide lifecycle completely;
- rely on a framework-specific container;
- require subclassing an incompatible application base class;
- require bytecode weaving over application classes;
- expect servlet APIs when the application is not servlet-based.

These are real integration mismatches.

Notice that they are not simply:

```text
uses reflection
```

A reflective library with a normal constructor may integrate more easily than a reflection-free library with an invasive lifecycle model.

Compatibility is architectural, not ideological.

---

## Threading Model Matters More Than Reflection in Many Cases { #threading-model }

Kora 2 executes ordinary application code synchronously on virtual threads.

A library's concurrency assumptions may therefore be more important than whether it uses reflection.

For example:

- Is the client thread-safe?
- Does it block?
- Does it require one event loop?
- Does it expose callbacks on its own executor?
- Does it retain thread-local state incorrectly?
- Does it pin carrier threads through native calls or synchronized sections?
- Does it have its own large thread pool?

Those factors can materially affect the service.

A one-time reflective constructor lookup may not.

This is why compatibility must be evaluated in engineering terms rather than by mechanism labels.

---

## Lifecycle Matters Too { #lifecycle-matters }

If a library creates:

- sockets;
- background threads;
- executors;
- pools;
- file watchers;
- native handles;

the important Kora integration question is how those resources enter and leave the application lifecycle.

Often the solution is a small factory:

```text
Library config
     ↓
client factory
     ↓
client
     ↓
lifecycle
     ↓
graph
```

Reflection inside the library is orthogonal.

---

## Configuration Is Usually Simple { #configuration-simple }

A third-party SDK can be configured through a Kora config interface and then constructed with its native builder.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("search")
    public interface SearchConfig {
        String endpoint();

        Duration timeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("search")
    interface SearchConfig {
        fun endpoint(): String

        fun timeout(): Duration
    }
    ```

then:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SearchModule {

        default SearchClient searchClient(SearchConfig config) {
            return SearchClient.builder()
                .endpoint(config.endpoint())
                .timeout(config.timeout())
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SearchModule {

        fun searchClient(config: SearchConfig): SearchClient {
            return SearchClient.builder()
                .endpoint(config.endpoint())
                .timeout(config.timeout())
                .build()
        }
    }
    ```

The SDK may use reflection internally.

Kora does not care unless the deployment model or performance requirements make it relevant.

---

## Telemetry Can Be Added Outside the Library { #telemetry-outside-library }

A library does not need native Kora support to participate in observability.

Options include:

- using the library's own OpenTelemetry integration;
- attaching Micrometer metrics if it supports them;
- wrapping important operations;
- adding an interceptor;
- exposing a small telemetry adapter.

This is often enough to turn an ordinary library into a production-quality Kora component.

No architecture bridge is required.

---

## Probes Can Be Added Independently { #probes-independently }

The same applies to readiness.

If a client exposes health state, create a `ReadinessProbe`.

If it does not, decide whether external dependency health should affect readiness at all.

Again, the library's runtime internals do not need to match Kora.

Operational integration and implementation strategy are separate concerns.

---

## A Real Integration Is Often Smaller Than People Expect { #real-integration-smaller }

The phrase "Kora does not support library X" can sound like a serious compatibility gap.

In practice, the integration may be:

```text
XConfig
XModule
XReadinessProbe
XTelemetry
```

and application code can inject the native `XClient`.

The difference between "official integration" and "usable library" should not be confused.

Official integration provides convenience and standardized production behavior.

Usability often requires much less.

---

## Kora Gives a Default Architecture, Not an Ecosystem Purity Test { #default-architecture }

This is the best way to summarize the extension model:

> **Kora gives you a default architecture, not an ecosystem purity test.**

The default architecture says:

- keep wiring explicit;
- validate the graph early;
- generate framework mechanics where possible;
- prefer direct code;
- use thin abstractions;
- integrate lifecycle and telemetry.

It does not say:

- every dependency must be Kora-authored;
- every library must avoid reflection;
- every library must support code generation;
- every library must be Native Image ready;
- every library must expose Kora-specific APIs.

That would undermine the very idea of a JVM ecosystem.

---

## Framework-Owned Mechanics and External Technology Should Be Treated Differently { #framework-owned-mechanics }

A useful decision rule is:

```text
Does Kora own this mechanism?
        ↓ yes
Can it be resolved at compile time?
        ↓ yes
Generate direct code.

Does an external library own the mechanism?
        ↓
Use its normal Java API.
```

This avoids unnecessary duplication.

It also keeps the framework small.

---

## This Is Why Kora Can Be Both Opinionated and Open { #opinionated-and-open }

At first glance, compile-time frameworks can seem restrictive because they make strong architectural choices.

Kora is indeed opinionated about its own internals.

But that does not make it closed to the Java ecosystem.

In fact, thin abstractions can make a framework more open because fewer external libraries need to be translated into a proprietary framework model.

The graph only needs a Java object.

How that object implements itself is largely its own concern.

---

## The Dependency Graph Does Not Care How an Object Works Internally { #dependency-graph-internals }

This point is almost embarrassingly simple, but it clarifies the whole topic.

Suppose the graph contains:

```text
OrderService
    ↓
FraudSdk
```

Kora needs to know how to obtain a `FraudSdk`.

Once the object exists, the graph does not need to understand whether `FraudSdk` internally uses:

```text
reflection
dynamic proxies
ServiceLoader
method handles
Netty
JNI
a background thread
generated bytecode
```

Those are implementation details of the component.

Dependency injection is about object relationships, not philosophical conformity.

---

## Compile-Time DI and Dynamic Internals Coexist Naturally { #compile-time-di-dynamic }

The complete shape can therefore be:

```text
compile-time graph

OrderService
      ↓
FraudClient
      ↓
factory known at compile time

runtime internals of FraudClient

FraudClient
      ↓
dynamic provider lookup
      ↓
reflection
      ↓
proxy
```

The graph is statically validated.

The component is dynamically implemented.

There is no contradiction.

---

## Native Image Is Where the Boundary Becomes Visible { #native-image-boundary }

When the application moves from HotSpot to Native Image, the second half of that diagram matters to the AOT compiler.

Kora's graph is already visible.

The `FraudClient` internals may not be.

That is when reachability metadata or a library-specific adaptation may be required.

This is precisely why Kora compatibility and Native Image compatibility must be evaluated separately.

---

## When a Library Really Is Native-Image Hostile { #native-image-hostile }

Some libraries are fundamentally poor fits for Native Image.

Examples may include libraries that depend on:

- arbitrary plugin JAR loading;
- runtime compiler invocation;
- runtime class generation for unknown schemas;
- agents that redefine classes;
- unsupported JNI behavior.

If Native Image is mandatory, the team may need:

- a different library;
- a different execution mode;
- a sidecar/service boundary;
- a JVM deployment instead of native.

This is an application architecture decision.

It is not evidence that Kora cannot use ordinary Java libraries.

---

## HotSpot Is Still a First-Class Deployment Choice { #hotspot-first-class }

The JVM remains extraordinarily capable.

JIT compilation, dynamic class loading, mature observability, profilers, agents, adaptive optimization, and broad library compatibility are major strengths.

Kora does not abandon them merely because its own framework machinery is compile-time generated.

A team can use Kora precisely because it wants:

```text
normal JVM
+
lower framework overhead
+
compile-time graph
+
virtual threads
+
native ecosystem
```

Native Image is optional.

That is an important architectural freedom.

---

## Kora's Runtime Performance Argument Survives Third-Party Libraries { #runtime-performance-argument }

Suppose a service uses ten libraries, two of which are relatively dynamic.

Kora still removes its own recurring overhead from:

- dependency injection;
- HTTP mapping;
- repository generation;
- aspect dispatch;
- configuration mapping;
- serialization where generated mapping is used.

Those savings remain real.

The total application may or may not be faster than another stack depending on workload.

But one dynamic dependency does not invalidate the framework architecture.

That is not how additive costs work.

---

## Think in Execution Paths { #execution-paths }

A better performance model is:

```text
request path A
=
Kora route
+ business logic
+ JDBC repository

request path B
=
Kora route
+ business logic
+ reflection-heavy SDK
+ network call

request path C
=
Kafka consumer
+ generated mapping
+ business logic
```

Only path B pays for the SDK.

This is much more precise than saying:

```text
application contains reflection
therefore compile-time performance advantage is gone
```

---

## Think in Frequency Too { #think-in-frequency }

Even inside path B, frequency matters.

If reflection is used once to initialize a metadata cache:

```text
startup:
reflection

steady state:
direct calls
```

the runtime cost may be negligible.

If reflection occurs per field per request, it may matter more.

Only measurement can answer.

Mechanism labels are not performance profiles.

---

## Native Image Has the Same Principle { #native-image-same-principle }

For Native Image, what matters is not morally whether the dependency uses reflection.

What matters is whether the reflective targets can be determined and registered.

A library with significant reflection can work perfectly if its reachable classes are describable.

A library with little reflection can still fail if it loads unknown implementations dynamically.

The implementation details matter more than the label.

---

## Reachability Metadata Localizes the Problem { #reachability-metadata-localizes }

One of the best properties of Native Image metadata is locality.

If dependency X needs:

```text
reflect-config
proxy-config
resource-config
```

those declarations can often live with X or its integration.

The rest of the application does not have to become reflection-aware.

That leads to a useful shape:

```text
Kora application
├── framework: already AOT friendly
├── library A: no metadata needed
├── library B: ships metadata
└── library C: custom metadata required
```

The problem is dependency-specific.

---

## This Is Better Than Framework-Wide Hint Accumulation { #framework-wide-hint }

In a runtime-heavy framework, native support may require a large framework-specific layer of hints covering container internals, proxies, reflection, conditions, serializers, and libraries.

Kora reduces the amount of framework-owned dynamic behavior that needs describing.

That makes remaining native issues easier to isolate.

The problem surface moves toward:

```text
Which dependency is dynamic?
```

instead of:

```text
Which framework subsystem generated the hidden dynamic behavior?
```

That is a genuine maintainability benefit.

---

## The Framework's Native Image Guide Reflects This Philosophy { #native-image-guide-philosophy }

Kora's Native Image support documents:

- metadata bundled in modules;
- third-party metadata;
- the reachability metadata repository;
- custom metadata;
- tracing-agent generation;
- reflection hints.

This is not the documentation of a framework pretending reflection does not exist.

It is the documentation of a framework that removes reflection where it owns the code and acknowledges it where dependencies use it.

That is the right level of pragmatism.

---

## Runtime Metadata Is Not Necessarily Bad Design { #runtime-metadata-not-bad }

There is another philosophical error worth avoiding.

Compile-time generation is often excellent when the information is static.

But some systems are genuinely dynamic.

A plugin library may intentionally discover providers at runtime.

A serializer may intentionally inspect unknown user classes.

A scripting engine may intentionally load unknown code.

A dependency-injection framework for a plugin host may intentionally support mutable definitions.

Reflection is sometimes the correct mechanism.

Kora's design does not need to declare those systems architecturally wrong.

It simply chooses a different trade-off for its own production backend framework model.

---

## The Best Architecture Uses Static Knowledge When It Exists { #static-knowledge }

The stronger principle is:

> If something is known at compile time and expensive or opaque to rediscover at runtime, use the compile-time knowledge.

Kora applies that to:

```text
dependency graph
controller signatures
repository declarations
aspect annotations
mappings
```

But if the information is genuinely dynamic or owned by a third party, there is no benefit in pretending it is static.

That distinction avoids ideology.

---

## Compile-Time and Runtime Techniques Can Coexist in One Service { #compile-time-runtime-coexist }

A modern backend may combine all of these:

```text
Kora compile-time DI
Kora generated repositories
Kora generated HTTP handlers
Jackson reflection in one vendor SDK
ServiceLoader in a driver
dynamic proxy in another SDK
JNI in a compression library
runtime configuration refresh
GraalVM metadata for native build
```

This is not architectural inconsistency.

It is software composition.

Each layer solves a different problem.

---

## JVM Libraries Do Not Need a "Kora Certification" { #jvm-libraries-no-certification }

There is no general requirement that a library be explicitly designed for Kora before it can be used.

If the library exposes normal Java constructors, builders, factories, or static creation methods, it can usually be placed in the graph.

That makes the practical compatibility surface much larger than the list of official Kora modules.

Official modules improve ergonomics.

They are not the border of the ecosystem.

---

## Official Module vs Direct Library Use { #official-module-vs-direct }

An official Kora integration typically adds things such as:

- standardized configuration;
- lifecycle;
- telemetry;
- probes;
- common exceptions;
- framework-specific generated conveniences.

Direct library use may require the application to provide those pieces itself.

The difference is convenience and production integration quality.

It is not necessarily basic compatibility.

---

## This Matters for Small Ecosystem Criticism { #small-ecosystem-criticism }

A common criticism of smaller frameworks is:

> What if the exact library I need has no Kora integration?

The answer is not automatically:

```text
you cannot use it
```

The more accurate answer is:

```text
use the native library
+
expose it through a Kora module
+
add lifecycle/config/telemetry if necessary
```

The fact that the library uses reflection internally does not change that basic path.

This is why framework extensibility matters more than raw starter count.

---

## A Concrete Integration Pattern { #concrete-integration-pattern }

Imagine an analytics SDK that has no official Kora module.

The native library exposes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    AnalyticsClient.builder()
        .endpoint(...)
        .apiKey(...)
        .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    AnalyticsClient.builder()
        .endpoint(...)
        .apiKey(...)
        .build()
    ```

A Kora integration can be:

```text
AnalyticsConfig
       ↓
AnalyticsClient factory
       ↓
Lifecycle if needed
       ↓
Telemetry wrapper if needed
       ↓
application service
```

If the SDK internally scans annotations or uses proxies, HotSpot executes it normally.

If Native Image is later required, check the SDK's Native Image support.

The Kora-side architecture remains almost unchanged.

---

## A "Bridge" Is Only Needed When There Is an Actual Semantic Mismatch { #bridge-semantic-mismatch }

Sometimes a real adapter is necessary.

For example:

- library callback model needs translation to synchronous service semantics;
- library lifecycle conflicts with application lifecycle;
- library returns a type the application does not want to expose;
- telemetry needs normalized instrumentation;
- exceptions need a stable application contract.

That is a semantic bridge.

But it is not caused by reflection.

A reflection-free library may need a large adapter.

A reflective library may need none.

This is another reason mechanism-based compatibility claims are misleading.

---

## Native Image Compatibility Can Be Improved Incrementally { #native-image-incremental }

A team does not have to solve every Native Image concern on day one.

A sensible path can be:

```text
1. Build Kora application on HotSpot.
2. Validate production architecture.
3. Decide whether Native Image creates enough value.
4. Run native build.
5. Identify unsupported dependencies.
6. add metadata / upgrade / replace where justified.
```

This prevents native compatibility from constraining library choice prematurely when the deployment may never require it.

---

## Native Image Should Be an Explicit Non-Functional Requirement { #native-image-non-functional }

If the project *must* ship as a native executable, put that requirement next to:

- JDK version;
- operating system;
- CPU architecture;
- latency SLO;
- memory target;
- startup target.

Then evaluate dependencies accordingly.

Do not infer it merely from choosing Kora.

This keeps architectural requirements honest.

---

## Kora Makes the Native Requirement Easier, Not Automatic { #native-requirement-easier }

The fair statement is:

```text
Kora architecture
→ reduces framework-native-image friction
```

not:

```text
Kora
→ every Java dependency automatically works in Native Image
```

No framework can make arbitrary library internals disappear.

A strong framework can avoid adding unnecessary problems of its own.

That is what Kora does.

---

## The Native Image Boundary Is Also Useful for Debugging { #native-image-boundary-debugging }

Kora's Native Image guide suggests isolating suspect dependencies with minimal probes.

That debugging model reflects the same separation.

If library X fails in a minimal native executable without Kora, the issue belongs to library X or its metadata.

That is a powerful diagnostic technique because it prevents teams from attributing every native-image failure to the framework.

Isolation clarifies ownership.

---

## Normal JVM Execution Remains the Reference Point { #normal-jvm-reference }

When a Kora application works on a normal JVM but fails as a Native Image, that observation already narrows the problem.

The application graph is not suddenly invalid.

The ordinary Java semantics are not necessarily wrong.

The likely difference lies in:

- reachability;
- initialization timing;
- resources;
- proxy metadata;
- JNI;
- unsupported runtime generation.

This makes deployment-specific debugging much more disciplined.

---

## Reflection Performance Should Be Measured, Not Feared { #reflection-performance-measured }

A small reflective library may be completely irrelevant to service performance.

A large generated framework can still be slow for other reasons.

The only reliable method is measurement.

For application code, profile:

- CPU;
- allocation;
- lock contention;
- startup;
- class loading;
- network time;
- database time.

If reflective calls dominate, optimize them.

If the database dominates, reflection is a distraction.

Kora's compile-time model is valuable because it removes a category of framework overhead before profiling begins.

That makes the remaining profile more application-shaped.

---

## This Is a Better Definition of Transparency { #definition-of-transparency }

Transparency does not mean every line of every dependency follows one architectural style.

It means the framework does not introduce hidden behavior unnecessarily.

Kora can be transparent even while integrating opaque third-party libraries because the boundary is clear:

```text
generated Kora graph
      ↓
native client
```

If the client is slow, inspect the client.

If the graph is wrong, the compiler reports it.

The responsibilities are separated.

---

## Compile-Time Is a Tool, Not an Ideology { #compile-time-tool }

This is the larger philosophical conclusion.

Compile-time generation is useful because some information is already available and can be turned into direct code early.

It is not morally superior.

Runtime reflection is useful because some information is only available or conveniently expressed dynamically.

It is not inherently bad.

Dynamic proxies are useful for certain APIs.

Runtime discovery is useful for plugin systems.

Native Image has different constraints because it optimizes for a different execution model.

A good framework uses the right mechanism for the layer it owns.

Kora's value comes from making a disciplined choice, not an absolutist one.

---

## Kora's Actual Philosophy Is Selective { #kora-philosophy-selective }

A concise formulation is:

```text
Where Kora owns the abstraction:
    move unnecessary runtime machinery to compile time.

Where mature external libraries own the technology:
    use their normal Java APIs.

Where Native Image is required:
    evaluate dynamic behavior and metadata explicitly.
```

This model is both performant and ecosystem-friendly.

---

## The Wrong Mental Model { #wrong-mental-model }

The wrong model is:

```text
Kora
  ↓
everything in process
  ↓
must be compile-time generated
```

That makes Kora sound like a restricted language runtime.

It is not.

---

## The Better Mental Model { #better-mental-model }

The better model is:

```text
JVM application
│
├── Kora-owned mechanics
│      └── mostly generated at compile time
│
├── application code
│      └── ordinary Java/Kotlin
│
├── third-party libraries
│      └── use whatever JVM mechanisms they use
│
└── deployment choice
       ├── HotSpot
       └── Native Image
```

Then Native Image adds another analysis layer:

```text
If Native Image:
    evaluate dynamic library behavior
    and provide metadata where required.
```

This accurately separates concerns.

---

## A Decision Matrix { #decision-matrix }

A practical compatibility matrix looks like this:

| Library characteristic           | Kora on HotSpot                       | Kora on Native Image                             |
|----------------------------------|---------------------------------------|--------------------------------------------------|
| Plain Java client                | Normally straightforward              | Normally straightforward                         |
| Uses reflection                  | Normally fine                         | May need reachability metadata                   |
| Uses dynamic proxies             | Normally fine                         | Proxy metadata may be required                   |
| Uses `ServiceLoader`             | Normally fine                         | Providers/resources may need registration        |
| Loads resources dynamically      | Normally fine                         | Resources may need inclusion                     |
| Uses runtime bytecode generation | Normally fine if library supports JDK | May be difficult or unsupported                  |
| Uses JNI                         | Depends on platform/library           | Additional native-image/JNI work may be required |
| Loads unknown plugin JARs        | Normal JVM capability                 | Often poor fit for closed-world native image     |
| Ships GraalVM metadata           | Normal                                | Usually much easier                              |
| Covered by metadata repository   | Normal                                | Usually easier                                   |

Notice that the left-hand column is not "unsupported."

That is the entire point.

---

## A Practical Evaluation Workflow { #evaluation-workflow }

When considering a new library for Kora, use this sequence.

First, ignore Native Image and evaluate the library as Java software.

Does it solve the problem well?

Is it maintained?

Is the API good?

Does it meet performance and security requirements?

Second, integrate it through the graph.

Create typed config, a factory, lifecycle, telemetry, and probes only as needed.

Third, profile if performance matters.

Do not reject the library merely because its internals are dynamic.

Fourth, if Native Image is a deployment requirement, evaluate its metadata and unsupported features.

This ordering prevents three separate engineering concerns from becoming one vague framework compatibility myth.

---

## Why the Myth Persists { #why-myth-persists }

The myth is understandable because compile-time frameworks are often marketed together with Native Image.

The concepts reinforce each other:

```text
compile-time DI
+
no reflection
+
native image
+
fast startup
```

Over time, people compress this into:

```text
compile-time framework
=
reflection forbidden
```

But the actual causal relationship is narrower.

Kora's compile-time architecture makes Native Image easier.

Native Image has stronger restrictions than HotSpot.

Those restrictions do not flow backward and become rules of the JVM deployment.

---

## Framework Native-Friendliness Is Different From Application Native-Friendliness { #framework-native-friendliness }

A framework can be highly Native Image friendly while an application is not.

For example:

```text
Kora framework:
excellent native compatibility

application:
uses runtime scripting engine
loads arbitrary plugins
uses unsupported JNI library
```

The final application may be a poor candidate for Native Image.

That does not undermine Kora's native architecture.

It simply means application dependencies define the final compatibility envelope.

---

## Application Native-Friendliness Is the Intersection of Dependencies { #application-native-friendliness }

A better model is:

```text
Native Image compatibility
=
Kora compatibility
∩ database driver compatibility
∩ HTTP client compatibility
∩ logging compatibility
∩ SDK compatibility
∩ application behavior
∩ native dependencies
```

The weakest dependency can determine the result.

Kora controls only one portion of that equation.

Its advantage is making its portion relatively strong.

---

## This Is True of Every Java Framework { #true-of-every-java-framework }

No Java framework can guarantee Native Image compatibility for arbitrary application dependencies.

Even if the framework itself performs perfect AOT analysis, an application can add:

- a custom agent;
- a proprietary native library;
- a reflection-heavy plugin system;
- an unsupported driver.

The framework can provide hints, metadata, and integrations.

It cannot change arbitrary code semantics without replacing the library.

Therefore dependency-level evaluation is unavoidable.

---

## Kora's Clean Baseline Is Still Valuable { #kora-clean-baseline }

The fact that Native Image is ecosystem-wide does not reduce Kora's advantage.

It clarifies it.

Kora avoids adding a large framework-specific dynamic surface on top of third-party dependencies.

When a problem appears, teams can more often localize it to:

```text
dependency X
```

instead of:

```text
framework internals + dependency X
```

That is operationally useful.

---

## A Library Can Even Use Reflection Intentionally for Extensibility { #reflection-for-extensibility }

Consider a library that discovers codecs from annotations at runtime.

That may be a deliberate design choice.

On HotSpot, using it inside Kora can be perfectly reasonable.

If native compilation is important, the team may prefer Kora's generated mapper instead.

The point is that the choice can be local.

One part of the application can use compile-time mapping.

Another can use a dynamic library.

Kora does not require architectural monoculture.

---

## Mixed Strategies Are Often the Practical Optimum { #mixed-strategies }

Real applications are heterogeneous.

A service may use:

```text
Kora generated DI
Kora generated JSON
JDBC repository generation
OkHttp transport
Logback
a reflective vendor SDK
JNI compression
ServiceLoader-based database driver
```

This may be exactly the correct architecture.

Trying to force every part into the same compile-time model could increase development cost without improving the application.

Framework design should allow composition.

---

## This Is Also Why Thin Abstractions Matter { #thin-abstractions }

If Kora wrapped every third-party library behind a thick proprietary model, incompatibilities would be harder to isolate.

With thin integration:

```text
Kora
  ↓
native client
```

the developer can consult the native library's documentation and Native Image support directly.

There is less semantic distance.

This improves both ordinary JVM integration and native-image troubleshooting.

---

## The Underlying Ecosystem Remains Usable { #underlying-ecosystem }

A Kora application can benefit from the maturity of the Java ecosystem:

- decades of database drivers;
- mature HTTP clients;
- cloud SDKs;
- security libraries;
- observability libraries;
- parsers;
- protocol stacks;
- data formats;
- native integrations.

Kora does not need compile-time-native replacements for all of them.

That is an important reason the framework can remain relatively small.

---

## The Right Compatibility Claim { #right-compatibility-claim }

Instead of saying:

> Kora works only with compile-time libraries.

say:

> Kora's own framework machinery is designed around compile-time generation, while third-party Java libraries keep their normal runtime model.

Instead of saying:

> Reflection-heavy libraries are incompatible with Kora.

say:

> Reflection-heavy libraries generally work normally on a JVM; if Native Image is required, their reachability requirements must be evaluated.

Instead of saying:

> One reflective dependency destroys Kora performance.

say:

> The dependency adds its own cost on the code paths where it runs; Kora's own generated runtime remains unchanged.

This vocabulary is much more accurate.

---

## The Strongest Example: Kora Documents Reflection Metadata Itself { #kora-documents-reflection }

Perhaps the clearest evidence is that Kora's own Native Image documentation explicitly explains how third-party reflection metadata is handled.

That only makes sense if the architecture accepts the possibility that external dependencies use reflection.

The documentation describes metadata for reflective constructors, dynamic proxies, resources, serialization, JNI, and third-party libraries.

This is not a loophole.

It is the expected interoperability model.

---

## Compile-Time Framework and Runtime Ecosystem Are Complementary { #compile-time-runtime-complementary }

The more accurate architectural story is:

```text
Kora:
compile known framework structure early

JVM ecosystem:
retain mature runtime libraries

GraalVM:
add AOT constraints only when native deployment is selected
```

These layers complement each other.

Kora gains performance and transparency without abandoning the ecosystem.

The JVM ecosystem retains dynamic capabilities where libraries need them.

Native Image remains an optional deployment optimization with explicit compatibility requirements.

---

## What Kora Actually Buys You { #what-kora-buys }

Kora's compile-time model gives you:

- dependency graph validation before runtime;
- generated wiring;
- generated aspects instead of runtime AOP proxies;
- generated repository implementations;
- generated HTTP adapters;
- generated mappings;
- less framework discovery at startup;
- less runtime framework metadata;
- a cleaner Native Image baseline;
- inspectable generated source.

It does **not** buy you:

- automatic native compatibility for arbitrary libraries;
- a guarantee that every dependency is fast;
- elimination of all reflection in the process;
- elimination of all dynamic proxies in the process;
- freedom from JNI or classloading issues in external software.

Understanding that boundary makes the advantages more credible, not less.

---

## What Third-Party Libraries Still Decide { #third-party-libraries-decide }

Each dependency still controls:

- its internal object model;
- threading;
- class loading;
- reflection;
- proxy generation;
- serialization;
- resource loading;
- JNI;
- memory usage;
- initialization behavior.

Kora integrates the resulting object into the graph.

That is normal software composition.

---

## What Deployment Still Decides { #deployment-decides }

The deployment environment controls another layer:

```text
HotSpot
OpenJDK
GraalVM JVM mode
Native Image
container limits
OS
CPU architecture
```

A library can behave differently under these environments.

Framework choice and deployment choice interact, but they are not interchangeable.

---

## Do Not Reject a Library for the Wrong Reason { #reject-library-wrong-reason }

If a library is a bad choice because:

- it is unmaintained;
- it allocates excessively;
- it starts hundreds of threads;
- it has security problems;
- it is too slow;
- it has poor failure semantics;
- it does not support the target JDK;

reject it.

If Native Image is mandatory and the library fundamentally cannot support it, reject or isolate it.

But rejecting a useful JVM library simply because it uses reflection internally, when the application will run on HotSpot, is not a Kora requirement.

That would be self-imposed architecture purity.

---

## Do Not Overstate Native Image Either { #overstate-native-image }

Native Image can provide meaningful startup and footprint advantages.

But it also changes build complexity, profiling, debugging, compatibility, and optimization behavior.

A team should choose it because the deployment economics justify it.

Kora makes the option more accessible.

It does not turn it into a mandatory destination.

This is especially important for long-running services where HotSpot's JIT and broad ecosystem compatibility may remain excellent trade-offs.

---

## Kora on HotSpot Is Still Fully Kora { #kora-on-hotspot }

A Kora service does not become somehow less authentic because it runs as ordinary JVM bytecode.

The core architecture remains:

```text
compile-time graph
generated framework code
thin abstractions
virtual threads
native Java ecosystem
```

That is already the framework's central value proposition.

Native Image is an additional deployment mode.

---

## The Best Mental Model Is Layered Freedom { #layered-freedom }

Kora is opinionated where opinion creates strong leverage:

```text
DI
AOP
mapping
repositories
HTTP contracts
```

It is open where ecosystem diversity matters:

```text
transport libraries
drivers
SDKs
logging
native clients
vendor integrations
```

And deployment remains a project choice:

```text
JVM
or
Native Image
```

This layered freedom is more useful than global architectural purity.

---

## Final Myth-Busting Summary { #final-myth-busting }

The myth usually begins with one true statement:

```text
Kora avoids reflection and dynamic proxies.
```

Then it incorrectly expands the scope.

The precise version is:

```text
Kora avoids reflection and dynamic proxies
for the framework mechanisms Kora owns.
```

It does **not** mean:

```text
No third-party code may use reflection.
No proxy may exist in the process.
No runtime metadata may be read.
Every dependency must be code-generated.
Every dependency must support Native Image.
```

Those claims do not follow.

A Kora application is still ordinary JVM software.

---

## Conclusion: Compile-Time Where Kora Owns the Problem, Normal Java Everywhere Else { #conclusion }

Kora's compile-time architecture is powerful precisely because it is targeted.

The framework already knows the application graph, so it validates and generates the graph before startup.

It already knows declarative HTTP contracts, so it generates client and server adapters.

It already knows repository declarations, so it generates repository implementations.

It already knows where AOP applies, so it generates subclasses instead of constructing runtime proxies.

This removes a substantial amount of framework runtime machinery and makes the application easier to understand, faster to start, and easier to compile into a Native Image.

But none of that converts the entire JVM ecosystem into a compile-time-only environment.

A library that uses reflection can still run.

A library that creates dynamic proxies can still run.

A library that performs runtime metadata lookup can still run.

A library that uses `ServiceLoader`, JNI, or runtime class generation can still run on the JVM according to the normal rules of the platform.

Kora's dependency graph only needs to know how to obtain the component.

It does not need the component's internals to adopt Kora's implementation philosophy.

That leads to the most important distinction in the entire discussion:

```text
Kora runtime model
        ≠
third-party library runtime model
        ≠
GraalVM Native Image constraints
```

On HotSpot, ordinary Java dynamic behavior remains ordinary Java dynamic behavior.

If Native Image is selected, the compatibility problem changes because GraalVM needs more information about reflection, proxies, resources, JNI, and dynamic loading. Some dependencies already ship
that metadata. Others are covered by the GraalVM Reachability Metadata Repository. Some require custom metadata. A small number may fundamentally depend on runtime capabilities that do not fit the
closed-world model.

Those are Native Image questions.

They should not be confused with whether the same library works in a Kora application on the JVM.

The performance story is equally compositional. One reflective dependency does not transform Kora's generated DI, routing, repositories, mappings, and AOP into a runtime-reflection framework. The
dependency contributes its own costs to the paths where it runs. The framework continues to contribute its own much smaller runtime machinery.

That is the realistic engineering model:

```text
Application cost
=
Kora framework cost
+ business code
+ database
+ networking
+ third-party libraries
+ serialization
+ telemetry
+ everything else
```

Kora minimizes the part it controls.

It does not pretend it controls everything.

This is why the strongest formulation is not that Kora is a "pure compile-time ecosystem." It is almost the opposite:

> **Framework implementation strategy is not an application-wide restriction.**

Kora says:

```text
"We don't need reflection here."
```

It does not say:

```text
"No dependency in your application may ever use reflection."
```

That difference is what lets Kora combine compile-time certainty with the ordinary Java ecosystem.

And it leads to the final principle:

> **Kora removes reflection and runtime magic from the parts of the stack it controls. It does not ban ordinary Java libraries from the application, nor does it require every dependency to adopt
Kora's compile-time architecture.**

For teams targeting GraalVM Native Image, there is one additional rule:

> **If Native Image is a requirement, Native Image compatibility must be evaluated for each dependency—exactly as with any other Java stack. Kora's advantage is that the framework itself starts from a
much cleaner baseline.**

That is a stronger argument than compile-time purity because it is both technically accurate and operationally useful.

Kora does not require the JVM ecosystem to become Kora.

It simply makes sure Kora itself does not add runtime machinery when compile-time knowledge can do the job better.
