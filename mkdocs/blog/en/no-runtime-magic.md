---
title: No Runtime Magic — What the Kora Framework Actually Generates
date: 2026-08-21
description: A walk through the Java and Kotlin sources the Kora Framework generates from annotations — the application graph, HTTP handlers, JSON codecs, repositories, and AOP proxies you can open and read.
search:
  exclude: true
---

# No Runtime Magic: What Kora Actually Generates { #no-runtime-magic }

**August 21, 2026**

Annotations often get associated with framework magic. A class gets `@HttpController`, a method gets `@Transactional`, an interface gets `@Repository`, and suddenly dependency injection works, HTTP
requests reach methods, database calls execute, JSON appears in responses, and resilience policies wrap business logic.

The important question, however, is not whether a framework uses annotations. The important question is what happens after those annotations are read.

A runtime-oriented framework can keep annotations as metadata and interpret them while the application is starting or running. It can scan classes, inspect methods, build proxy chains, create runtime
invocation handlers, and resolve application structure dynamically.

The Kora Framework takes a different route. Its processors analyze application declarations during compilation and generate ordinary Java or Kotlin source code. Dependency injection becomes a generated application
graph, HTTP controllers become request handlers, repositories become concrete implementations, JSON models get generated readers and writers, and AOP annotations become generated subclasses or
wrappers.

That means the interesting part of Kora is not the annotation itself. It is the code the annotation produces.

The core idea can be summarized very simply:

> **Annotation does not have to mean magic if the implementation it produces can be opened, read, and debugged.**

This article follows a small Kora application through the generated sources and shows what actually appears between an annotation and runtime execution.

---
## Start With an Ordinary Application { #ordinary-application }

Consider a small HTTP service. At the source level, it looks deliberately normal:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule {

        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                KoraApplication.run(ApplicationGraph::graph)
            }
        }
    }
    ```

There is already one interesting detail here: `ApplicationGraph` is referenced from application code, but we did not write it. Kora generates it during compilation.

Now add a controller:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class UserController {

        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        public UserResponse getUser(@Path String id) {
            return userService.getUser(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class UserController(private val userService: UserService) {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        fun getUser(@Path id: String): UserResponse {
            return userService.getUser(id)
        }
    }
    ```

A repository:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("""
            SELECT id, name, email, created_at
            FROM users
            WHERE id = :id
            """)
        Optional<UserDAO> findById(Long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository : JdbcRepository {

        @Query("""
            SELECT id, name, email, created_at
            FROM users
            WHERE id = :id
            """)
        fun findById(id: Long): UserDAO?
    }
    ```

A JSON DTO:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record UserResponse(
        String id,
        String name,
        String email,
        LocalDateTime createdAt
    ) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

And some resilience on the service layer:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class UserService {

        @Retryable(DefaultRetry.class)
        public UserResponse getUser(String id) {
            // ...
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class UserService {

        @Retryable(DefaultRetry::class)
        open fun getUser(id: String): UserResponse {
            // ...
        }
    }
    ```

At this point the source looks similar to many annotation-driven JVM frameworks. The architectural difference becomes visible only after compilation.

Run:

```bash
./gradlew clean classes
```

and the project gains another layer of source code generated by Kora. For Java, generated files are typically available under:

```text
build/generated/sources/annotationProcessor/java/main/
```

and Kotlin generation is handled through KSP under the corresponding generated source directory.

These generated files are one of the clearest ways to understand what Kora actually does.

---
## From Annotation to Execution { #annotation-to-execution }

For the controller above, the path from source declaration to runtime request handling looks roughly like this:

```text
@HttpController + @HttpRoute
              │
              ▼
     annotation processor
              │
              ▼
 generated HttpServerRequestHandler
              │
              ▼
       ApplicationGraph
              │
              ▼
          HTTP router
              │
              ▼
           Undertow
```

Other Kora features follow exactly the same pattern. `@Json` produces concrete codecs, `@Repository` produces a repository implementation, resilience annotations produce an AOP subclass, and all of
these generated components are wired through the same application graph.

The result is less a collection of independent framework tricks and more a compile-time pipeline that converts declarative application code into explicit JVM code.

---
## 1. Dependency Injection Becomes an Application Graph { #dependency-injection }

Dependency injection is the foundation of the whole model.

A Kora application starts with:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application
    ```

Kora uses that interface as the root of the application graph. During compilation, the processor inspects available components and modules, resolves their dependencies, verifies the graph, and emits
generated code representing the result.

The generated `ApplicationGraph` contains the component nodes and the relationships between them. In simplified form, parts of it look conceptually like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var controller = graphDraw.addNode(
        ...,
        g -> new UserController(g.get(userService))
    );

    var handler = graphDraw.addNode(
        ...,
        List.of(controller),
        ...,
        g -> generatedControllerModule.getUserHandler(g.get(controller))
    );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val controller = graphDraw.addNode(
        ...,
        { g -> UserController(g.get(userService)) }
    )

    val handler = graphDraw.addNode(
        ...,
        listOf(controller),
        ...,
        { g -> generatedControllerModule.getUserHandler(g.get(controller)) }
    )
    ```

The important detail is not the exact generated API, but the fact that the dependency relationship has already been calculated. The graph knows that the HTTP handler depends on the controller, the
controller depends on the service, and the service depends on other components.

A traditional runtime DI container may need to answer those questions when the process starts: which components exist, which constructor to use, what satisfies each parameter, whether two candidates
are ambiguous, and whether a cycle exists. Kora moves that reasoning into compilation.

So `@Component` is better understood not as a runtime discovery marker, but as input into graph generation.

By the time the JVM starts, the dependency structure is no longer something the framework needs to discover. It is already encoded in compiled application code.

---
## 2. `@HttpController` Becomes a Concrete Request Handler { #http-controller }

Now consider the HTTP layer.

Suppose we write:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class HelloController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        public HttpServerResponse hello() {
            return HttpServerResponse.of(
                200,
                HttpBody.plaintext("Hello, Kora!")
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class HelloController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        fun hello(): HttpServerResponse {
            return HttpServerResponse.of(
                200,
                HttpBody.plaintext("Hello, Kora!")
            )
        }
    }
    ```

The class itself does not implement `HttpServerRequestHandler`, and there is no manual Undertow route registration. That plumbing is generated.

Kora creates a controller module containing handler factories. A simplified generated method looks like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface HelloControllerModule {

        default HttpServerRequestHandler get_hello(
            HelloController controller) {

            return HttpServerRequestHandlerImpl.of(
                "GET",
                "/hello",
                request -> controller.hello()
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface HelloControllerModule {

        fun get_hello(controller: HelloController): HttpServerRequestHandler {
            return HttpServerRequestHandlerImpl.of(
                "GET",
                "/hello",
                { request -> controller.hello() }
            )
        }
    }
    ```

That code makes the behavior of `@HttpController` much less mysterious. The generated factory receives the controller as a normal dependency and returns a normal `HttpServerRequestHandler`. The HTTP
method, route path, and controller invocation are visible directly in source.

For a more complex endpoint, the generated handler also contains request parameter extraction, body mapping, response mapping, interceptors, and telemetry integration. The file becomes longer, but the
architecture remains the same: compile-time analysis produces explicit request-handling code.

The generated handler is then added to the application graph and eventually registered with Kora's HTTP infrastructure, which delegates to Undertow.

The actual request path therefore looks like ordinary calls:

```text
Undertow
   ↓
Kora HTTP router
   ↓
generated HttpServerRequestHandler
   ↓
UserController.getUser(...)
```

The annotation defines the endpoint contract. The generated handler is what actually runs.

---
## 3. `@Json` Becomes Reader and Writer Classes { #json-codecs }

JSON serialization is another useful example because many libraries solve it through runtime introspection.

In Kora, a declaration such as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record UserResponse(
        String id,
        String name,
        String email,
        LocalDateTime createdAt
    ) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

causes the processor to generate concrete JSON codecs for that type. For Java models, those generated classes typically have names similar to:

```text
$UserResponse_JsonReader.java
$UserResponse_JsonWriter.java
```

The writer contains direct serialization code. In simplified form:

===! ":fontawesome-brands-java: `Java`"

    ```java
    generator.writeStartObject();

    generator.writeName("id");
    generator.writeString(value.id());

    generator.writeName("name");
    generator.writeString(value.name());

    generator.writeName("createdAt");
    createdAtWriter.write(generator, value.createdAt());

    generator.writeEndObject();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    generator.writeStartObject()

    generator.writeName("id")
    generator.writeString(value.id)

    generator.writeName("name")
    generator.writeString(value.name)

    generator.writeName("createdAt")
    createdAtWriter.write(generator, value.createdAt)

    generator.writeEndObject()
    ```

The reader performs the inverse operation: it reads tokens, matches property names, parses values, validates required fields, and finally constructs the record.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    String id = null;
    String name = null;

    // parser loop...

    return new UserResponse(
        id,
        name,
        email,
        createdAt
    );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    var id: String? = null
    var name: String? = null

    // parser loop...

    return UserResponse(
        id,
        name,
        email,
        createdAt
    )
    ```

The generated codec can itself depend on other codecs. A `JsonWriter<LocalDateTime>`, for example, is injected through the application graph and called directly by the generated `UserResponse` writer.

This is an important distinction from runtime reflection. `@Json` does not mean “remember this class and inspect its fields later.” It means “generate the serialization implementation for this class
during compilation.”

When the application later returns `UserResponse`, the HTTP layer can invoke a concrete generated writer rather than discovering the DTO structure on demand.

---
## 4. `@Repository` Becomes Normal JDBC Code { #repository-jdbc }

Repositories make the compile-time model especially easy to see.

Take:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("""
            SELECT id, name, email
            FROM users
            WHERE id = :id
            """)
        Optional<UserDAO> findById(Long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository : JdbcRepository {

        @Query("""
            SELECT id, name, email
            FROM users
            WHERE id = :id
            """)
        fun findById(id: Long): UserDAO?
    }
    ```

The source interface contains no method body, but after compilation Kora produces an implementation, typically with a name such as:

```text
$UserRepository_Impl.java
```

That implementation contains the mechanics required to execute the query. A simplified version might look like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Optional<UserDAO> findById(Long id) {
        var connection = executor.currentConnection();

        try (var statement = connection.prepareStatement(
            "SELECT id, name, email FROM users WHERE id = ?")) {

            statement.setLong(1, id);

            try (var resultSet = statement.executeQuery()) {
                return resultSetMapper.apply(resultSet);
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun findById(id: Long): UserDAO? {
        val connection = executor.currentConnection()

        connection.prepareStatement(
            "SELECT id, name, email FROM users WHERE id = ?"
        ).use { statement ->
            statement.setLong(1, id)

            statement.executeQuery().use { resultSet ->
                return resultSetMapper.apply(resultSet)
            }
        }
    }
    ```

The real generated implementation also contains Kora telemetry, connection handling, query context, exception mapping, and whatever additional integration the repository requires.

But structurally, it is still JDBC code.

The developer writes the part that matters:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("SELECT ...")
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("SELECT ...")
    ```

and the compiler generates the repetitive plumbing around it: prepared statements, parameter binding, execution, mapping, resource cleanup, and telemetry.

At runtime, a call such as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    userRepository.findById(id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    userRepository.findById(id)
    ```

is simply a normal interface call to a generated implementation. There is no need for a generic runtime invocation handler to inspect the method and decide what query should execute.

This is one of the best examples of Kora's philosophy: preserve explicit SQL and type information, then generate the boring mechanical code around it.

---
## 5. AOP Becomes a Class You Can Open { #aop-class }

AOP is often where annotation-driven frameworks feel most opaque.

Consider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class UserService {

        @Retryable(DefaultRetry.class)
        public UserResponse getUser(String id) {
            return loadUser(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class UserService {

        @Retryable(DefaultRetry::class)
        open fun getUser(id: String): UserResponse {
            return loadUser(id)
        }
    }
    ```

In a runtime-oriented framework, the injected `UserService` may actually be a dynamically created proxy whose invocation chain is constructed after startup.

Kora instead generates the subclass during compilation. For a retry aspect, the result is conceptually similar to:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class $UserService__AopProxy extends UserService {

        private final Retry retry;

        @Override
        public UserResponse getUser(String id) {
            return retry.retry(() -> super.getUser(id));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class `$UserService__AopProxy`(
        private val retry: Retry
    ) : UserService() {

        override fun getUser(id: String): UserResponse {
            return retry.retry { super.getUser(id) }
        }
    }
    ```

That is the AOP layer.

The original business method is still called through `super.getUser(id)`, while the generated override wraps the invocation with the required policy.

The same model applies when several aspects are combined. Suppose a method uses:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CircuitBreakable(DefaultCircuitBreaker.class)
    @Retryable(DefaultRetry.class)
    @Timeout(DefaultTimeout.class)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CircuitBreakable(DefaultCircuitBreaker::class)
    @Retryable(DefaultRetry::class)
    @Timeout(DefaultTimeout::class)
    ```

The generated subclass may contain a chain equivalent to:

===! ":fontawesome-brands-java: `Java`"

    ```java
    return circuitBreaker.execute(() ->
        retry.retry(() ->
            timeout.execute(() ->
                super.getUsers()
            )
        )
    );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    return circuitBreaker.execute {
        retry.retry {
            timeout.execute {
                super.getUsers()
            }
        }
    }
    ```

The precise generated structure may be split into helper methods, but the ordering is visible directly in source.

This is important because AOP ordering no longer needs to remain an abstract framework concept. If you want to know which concern wraps which, you can open the generated proxy and read the calls in
the order they actually execute.

The framework still provides interception. What disappears is the need for that interception to remain hidden.

---
## Putting the Pieces Together { #pieces-together }

Each generated artifact is straightforward in isolation. DI becomes `ApplicationGraph`, HTTP annotations become request handlers, `@Json` becomes serializers and deserializers, `@Repository` becomes a
concrete database implementation, and AOP annotations become generated subclasses.

The more interesting picture appears when all of them are connected.

Consider:

```http
GET /users/42
```

A simplified request flow looks like this:

```text
Undertow
   ↓
Kora HTTP router
   ↓
generated HttpServerRequestHandler
   ↓
UserController
   ↓
generated UserService AOP subclass
   ↓
UserService
   ↓
generated $UserRepository_Impl
   ↓
JDBC
   ↓
PostgreSQL
```

On the response path, generated mapping code appears again:

```text
PostgreSQL result
   ↓
generated JDBC mapper
   ↓
UserDAO
   ↓
UserService
   ↓
UserResponse
   ↓
generated JsonWriter<UserResponse>
   ↓
HTTP response
   ↓
Undertow
```

The generated application graph connects these objects and provides their dependencies.

This means that when something behaves unexpectedly, there is usually a very concrete place to look. If routing looks wrong, inspect the generated controller module. If JSON output is incorrect,
inspect the generated writer. If a query parameter is bound incorrectly, inspect the generated repository. If retries wrap the wrong operation, inspect the AOP proxy. If dependency injection behaves
unexpectedly, inspect the application graph.

You debug the implementation rather than trying to reconstruct invisible framework state.

---
## Generated Source Is Not Runtime Code Generation { #generated-source }

There is an important distinction here because the term “code generation” can mean several things.

A framework can generate bytecode dynamically during startup. It can create proxy classes at runtime. It can instrument classes with agents or construct invocation machinery from reflection metadata.

Kora's model is much simpler: its annotation processors and KSP processors generate `.java` or `.kt` source files during compilation, and those files are then compiled normally by `javac` or
`kotlinc`.

The pipeline is therefore:

```text
application source
       +
annotations
       ↓
Kora annotation processor / KSP
       ↓
generated Java / Kotlin source
       ↓
javac / kotlinc
       ↓
ordinary JVM classes
```

Once compilation finishes, the JVM does not care which class was written manually and which class was generated. They are all ordinary compiled classes.

That is why readable source generation matters so much to Kora's architecture.

---
## Annotations as Compile-Time DSL { #compile-time-dsl }

A useful mental model is to think of Kora annotations as a small declarative language for the compiler.

When you write:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = GET, path = "/users/{id}")
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = GET, path = "/users/{id}")
    ```

you are effectively saying:

> Generate a request handler for this route, parse the required arguments, invoke this method, and map the result into an HTTP response.

When you write:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    @Query(...)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    @Query(...)
    ```

you are saying:

> Generate an implementation that executes this query using the declared method types and available mappers.

When you write:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retryable(DefaultRetry.class)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retryable(DefaultRetry::class)
    ```

you are saying:

> Generate a wrapper that invokes this method through the selected retry policy.

This is a better model than thinking about annotations as permanent runtime metadata. In Kora, many annotations are simply concise input to source generation.

---
## Why Readable Generated Code Matters { #readable-code }

Compile-time generation alone does not guarantee transparency. A framework could generate enormous and effectively unreadable source files and still claim to be compile-time.

Kora explicitly aims for generated code that engineers can inspect. That has practical consequences.

Suppose a JSON field has an unexpected name. You can open the generated writer and see the literal property name it emits.

Suppose a repository appears to bind parameters incorrectly. You can open `$UserRepository_Impl` and inspect the exact `PreparedStatement` calls.

Suppose several resilience aspects interact in an unexpected order. You can open `$UserService__AopProxy` and follow the nesting.

Suppose DI chose a component you did not expect. You can inspect the generated application graph and see how that component entered the graph.

The key advantage is not that developers must read generated code every day. In normal development, most of it should remain invisible. The advantage is that when the abstraction leaks, there is a
concrete implementation waiting underneath.

---
## Generated Code Is Executable Documentation { #executable-docs }

Generated source is also useful as a form of executable documentation.

A repository interface says:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("... WHERE id = :id")
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("... WHERE id = :id")
    ```

The generated implementation tells you exactly how `:id` becomes a JDBC parameter, which mapper processes the result, which telemetry surrounds the call, and which executor supplies the connection.

A controller says:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(...)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(...)
    ```

The generated handler shows the registered HTTP method and path, the exact controller method invocation, and which request and response mappers are involved.

A service says:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retryable
    @Timeout
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retryable
    @Timeout
    ```

The generated AOP subclass tells you which aspect sits on the outside and where the original method is finally invoked.

Documentation can become stale. Generated code cannot drift from the compiled application in the same way because it is part of the code that produced that application.

---
## There Is Still Runtime Infrastructure { #runtime-infrastructure }

“No runtime magic” does not mean “no runtime framework.”

Undertow still accepts network connections. The HTTP router still matches requests. The application graph still manages component lifecycle. JDBC still communicates with the database. Circuit breakers
still maintain state, retries still count attempts, and telemetry still records runtime activity.

Those are inherently runtime responsibilities.

The important distinction is that Kora tries not to postpone **structural decisions** until runtime if they are already knowable at compile time.

The controller route is known, so the handler can be generated. The repository method and SQL are known, so the implementation can be generated. The DTO structure is known, so the JSON codec can be
generated. The AOP annotations are known, so the wrapper can be generated. The component dependencies are known, so the application graph can be generated.

Runtime is then responsible for executing these implementations, not discovering them.

---
## From Magic to Mechanical Code { #mechanical-code }

Once you inspect the generated sources, many Kora features become surprisingly ordinary.

`@HttpController` turns into a handler factory. `@Json` turns into parser and generator calls. `@Repository` turns into prepared statements. `@Retryable` turns into one method call wrapping another.
`@Component` turns into a node inside a generated dependency graph.

That ordinariness is a feature.

Infrastructure plumbing is often repetitive and unpleasant to write manually, but it does not need to remain mysterious simply because a framework generates it.

Kora's proposition is not to make developers write all of this code themselves. It is to let the compiler write the repetitive parts while preserving an implementation that engineers can still
inspect.

---
## Annotation ≠ Magic { #annotation-magic }

Whether a framework uses annotations says very little about how transparent that framework is.

What matters is the lifecycle of the annotation.

If:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    ```

means:

```text
store metadata
→ discover it during startup
→ create runtime invocation machinery
→ interpret calls dynamically
```

then a large part of the behavior remains hidden inside the runtime framework.

If the same annotation means:

```text
@Repository
    ↓
annotation processor
    ↓
$UserRepository_Impl.java
    ↓
javac
    ↓
ordinary repository implementation
```

then the annotation is simply a compact way to ask the compiler to write predictable boilerplate.

The same principle applies to HTTP, JSON, DI, and AOP.

That gives us a useful definition of framework magic:

> **An annotation is not magic when you can open the implementation it produced and understand what the application will actually execute.**

This is what readable generated sources mean in practice.

The annotations provide a concise programming model. The processors generate the mechanical implementation. The application graph wires those implementations together. At runtime, the JVM executes
ordinary compiled code.

The complete path stays visible:

```text
annotation
    ↓
compile-time processor
    ↓
generated Java / Kotlin source
    ↓
generated application graph
    ↓
ordinary JVM execution
```

The framework still saves developers from writing repetitive infrastructure by hand. It simply does not require that infrastructure to remain invisible.
