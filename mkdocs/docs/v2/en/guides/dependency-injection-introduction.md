---
search:
  exclude: true
title: Dependency Injection with Kora
summary: Learn the fundamentals of Kora's compile-time dependency injection container - components, modules, roots, tags, and the generated application graph
description: "Conceptual introduction to Kora 2.0 compile-time dependency injection: how @KoraApp generates the application graph started through KoraApplication and ApplicationGraphDraw, the io.koraframework.common.annotation set (@Component, @Module, @KoraSubmodule, @Root, @DefaultComponent, @Tag, @Conditional, @FactoryModule), component discovery order and the dependency resolution algorithm, the claim kinds required, @Nullable, ValueOf, PromiseOf, All and TypeRef from io.koraframework.application.graph, tag matching with Tag.Any, Lifecycle init and release, and the graph build errors the compiler reports."
agent:
  use_when: "Use this file for questions about how Kora 2.0 compile-time dependency injection actually works: what @KoraApp generates and why nothing is built without @Root, @Component versus a @Module factory method versus @KoraSubmodule, @DefaultComponent priority, @Conditional, @FactoryModule, generic factories, @Tag and Tag.Any matching rules, claiming a dependency as required, @Nullable, ValueOf<T>, PromiseOf<T>, All<T> or TypeRef<T>, Lifecycle release order, and diagnosing 'No component found for dependency', 'Multiple components match dependency' and 'Circular dependency found' build failures."
tags: dependency-injection, di, kora-app, component, module, root, tag, compile-time
---

# Dependency Injection with Kora { #dependency-injection-kora }

This guide introduces dependency injection and inversion of control through Kora's compile-time container. It covers how application objects declare dependencies through constructors, how `@Component`
and `@Module` make those objects available to the graph, how `@Root` decides what actually gets built, and how Kora validates wiring during compilation instead of discovering missing dependencies at
runtime. You will also see why compile-time DI changes startup behavior, type safety, and testability.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Dependency Injection Introduction App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection-introduction-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Dependency Injection Introduction App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-dependency-injection-introduction-app).

## What You'll Learn { #youll-learn }

You'll learn the fundamental concepts of dependency injection and understand:

- **Core DI Concepts**: What dependency injection is and why it matters
- **Kora's Architecture**: How compile-time DI works and its advantages
- **Graph Roots**: Why `@Root` decides which components are actually created
- **Component Lifecycle**: How components are created, initialized, and released
- **Module System**: How to organize and structure your application components
- **Tags and Collections**: How to disambiguate implementations and collect extension points
- **Best Practices**: Patterns for writing maintainable, testable code

## What You'll Need { #youll-need }

- JDK 25 or later, because Kora 2.0 itself is compiled for Java 25
- Gradle 9 or later
- A text editor or IDE
- Basic understanding of Java or Kotlin

## Prerequisites { #prerequisites }

!!! note "No Prerequisites Required"

    This guide is designed for beginners and does not require prior knowledge of dependency injection or Kora.

    You only need basic Java or Kotlin familiarity, because the guide introduces Kora dependency injection concepts from first principles before showing framework-specific patterns.

## Overview { #overview }

Dependency injection is a way to assemble an application from explicit dependencies instead of letting objects create everything they need by themselves. A dependency is simply "something this class
needs in order to work": a repository, a client, a configuration object, a cache, a clock, or another service.

For a tiny program, it is natural to write `new` everywhere. A controller can create a service, the service can create a repository, and the repository can create whatever it needs. But as soon as the
program grows, this becomes hard to maintain:

- classes know too much about how other classes are built
- tests become hard because dependencies are created inside the class
- replacing one implementation requires editing many places
- startup logic spreads across the codebase
- configuration and infrastructure details leak into business code

Dependency injection fixes this by changing the rule: a class should not build its own collaborators. It should declare what it needs, usually through a constructor, and let the application graph
provide those objects.

### Small Example { #small-example }

Without DI, a service might create its repository directly:

```java
public final class UserService {
    private final UserRepository repository = new InMemoryUserRepository();
}
```

That looks simple, but `UserService` is now tied to one repository implementation. A test cannot easily replace it. A future database repository cannot be plugged in without editing the service.

With constructor injection, the service only declares the dependency:

```java
public final class UserService {
    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }
}
```

Now `UserService` does not care whether the repository is in-memory, JDBC-backed, mocked in a test, or wrapped with caching. That decision moves to the application graph.

### Object Graphs { #object-graphs }

An application is not just a pile of classes. It is a graph of objects connected by dependencies. For example:

```text
UserController
  -> UserService
      -> UserRepository
      -> UserValidator
```

This is called a dependency graph or object graph. Each arrow means "this object needs that object". Kora's main job is to build this graph correctly, start lifecycle-aware components in the right
order, and fail the build when the graph cannot be assembled.

Thinking in graphs is one of the most important Kora concepts. When you add a controller, repository, HTTP client, cache, or configuration object, you are adding a node or edge to the graph.

### Inversion of Control { #inversion-control }

The deeper idea behind dependency injection is inversion of control. Instead of a service deciding how to construct its repository, client, cache, or configuration, it only declares that it needs
them. Object creation moves out of the service and into the application graph.

That changes the shape of application code:

- constructors describe required collaborators
- interfaces make replacement points explicit
- tests can provide mocks or alternate implementations
- startup wiring becomes a separate concern from business logic

### Dependency Injection with Kora { #dependency-injection-kora-2 }

[Kora's compile-time container](../documentation/container.md) implements dependency injection at compile time. The `@KoraApp` interface marks the graph root, `@Component` marks graph-managed classes,
`@Root` marks the entry points that must always exist, and `@Module` contributes factories or framework capabilities. During compilation, Kora analyzes the graph and generates plain Java or Kotlin code
that creates and connects components. Nothing is discovered by reflection at runtime.

This gives Kora a different failure model from runtime DI frameworks. Missing dependencies, ambiguous bindings, dependency cycles, and unreachable roots are reported during the build rather than during
application startup.

For beginners, the most important annotations are:

- `@KoraApp`: the root interface of the application graph
- `@Component`: a class Kora can create automatically
- `@Module`: a collection of component factories or imported framework modules
- `@Root`: a component that must be created even if nothing depends on it

You can think of `@KoraApp` as the map of the application, `@Component` as a graph node, `@Root` as the places where the map is entered, and constructor parameters as arrows between nodes.

All of these annotations live in one package, `io.koraframework.common.annotation`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.DefaultComponent;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.common.annotation.KoraSubmodule;
    import io.koraframework.common.annotation.Module;
    import io.koraframework.common.annotation.Root;
    import io.koraframework.common.annotation.Tag;
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.DefaultComponent
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.common.annotation.KoraSubmodule
    import io.koraframework.common.annotation.Module
    import io.koraframework.common.annotation.Root
    import io.koraframework.common.annotation.Tag
    ```

The runtime types that describe graph relationships - `All`, `ValueOf`, `PromiseOf`, `TypeRef`, `Lifecycle`, and the `KoraApplication` entry point - live in `io.koraframework.application.graph`.

### Compile-Time Injection { #compile-time-injection }

Compile-time DI means Kora checks and generates wiring during the build. That matters because many DI mistakes are structural mistakes:

- a required dependency has no provider
- two providers match the same dependency and Kora cannot choose
- a module was not imported into the application
- a component depends on another component that cannot be built
- the application declares no root at all, so there is nothing to build

In a runtime DI framework, some of these errors may appear only when the app starts. In Kora, the build fails earlier, before the application is packaged or deployed. This makes feedback faster and
keeps production startup more predictable.

The generated graph is ordinary bytecode. There is no classpath scanning, no reflective constructor lookup, and no proxy generation at startup, which keeps startup time short and makes the application
friendly to ahead-of-time compilation.

### Discovery Scope { #discovery-scope }

Kora does not blindly scan every class on the classpath. Components are discovered in Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces. Components from external libraries are also
not automatically available just because they exist in a JAR. A library normally exposes a module interface, and your application imports that module by extending it from `@KoraApp`.

This explicitness is important: it keeps the graph predictable, makes module boundaries visible, and avoids accidental component registration.

The practical learning flow is:

1. understand why manual object creation becomes painful
2. learn what a dependency is
3. introduce constructor injection
4. connect dependency injection to object graphs and inversion of control
5. compare runtime DI with Kora's compile-time graph
6. learn how Kora discovers components and modules
7. see why generated graph code improves wiring feedback

---

## DI Basics { #di-basics }

This guide provides a comprehensive introduction to dependency injection (DI) and inversion of control (IoC) principles using the Kora framework. Whether you're new to these concepts or looking to
deepen your understanding, this section will systematically build your knowledge from fundamental principles to practical implementation.

### What Is Dependency Injection? { #dependency-injection }

**Dependency Injection** is a fundamental design pattern that addresses how software components acquire and manage their dependencies. At its core, DI is about separating the creation of dependencies
from their usage, allowing for more flexible and maintainable code architecture.

**Core Concept**: Instead of a component creating its own dependencies, those dependencies are provided (injected) from an external source. This external source is typically a dependency injection
framework or container.

**Basic Example**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Traditional approach - component creates its own dependencies
    public class OrderProcessor {
        private Database database = new Database();        // Component creates dependency
        private EmailService emailService = new EmailService();

        public void processOrder(Order order) {
            database.save(order);
            emailService.sendConfirmation(order.getCustomerEmail());
        }
    }

    // Dependency injection approach - dependencies are provided
    public class OrderProcessor {
        private final Database database;
        private final EmailService emailService;

        // Dependencies are injected through constructor
        public OrderProcessor(Database database, EmailService emailService) {
            this.database = database;
            this.emailService = emailService;
        }

        public void processOrder(Order order) {
            database.save(order);
            emailService.sendConfirmation(order.getCustomerEmail());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Traditional approach - component creates its own dependencies
    class OrderProcessor {
        private val database = Database()        // Component creates dependency
        private val emailService = EmailService()

        fun processOrder(order: Order) {
            database.save(order)
            emailService.sendConfirmation(order.customerEmail)
        }
    }

    // Dependency injection approach - dependencies are provided
    class OrderProcessor(
        private val database: Database,
        private val emailService: EmailService
    ) {
        // Dependencies are injected through primary constructor

        fun processOrder(order: Order) {
            database.save(order)
            emailService.sendConfirmation(order.customerEmail)
        }
    }
    ```

**Key Terminology**:

- **Dependency**: Any object or service that a component requires to function
- **Injection**: The process of providing dependencies to a component
- **Injector/Container**: The mechanism responsible for creating and injecting dependencies
- **Dependency claim**: In Kora, the concrete request a constructor parameter makes - a type, an optional tag, and an optional wrapper such as `All<T>` or `ValueOf<T>`

### Traditional Approach Problems { #traditional-approach-problems }

To understand the necessity of dependency injection, let's examine the challenges that arise without it and how DI provides solutions.

**The Problem: Tight Coupling**

Tight coupling occurs when components are directly dependent on specific implementations, making the system rigid and difficult to maintain. Consider this common pattern:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class UserService {
        private DatabaseConnection connection = new DatabaseConnection();  // Direct instantiation

        public User findUserById(long id) {
            return connection.query("SELECT * FROM users WHERE id = ?", id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class UserService {
        private val connection = DatabaseConnection()  // Direct instantiation

        fun findUserById(id: Long): User {
            return connection.query("SELECT * FROM users WHERE id = ?", id)
        }
    }
    ```

Problems with Tight Coupling:

1. Testing Difficulties: The `UserService` cannot be tested in isolation because it directly instantiates `DatabaseConnection`
2. Implementation Lock-in: Changing to a different database requires modifying the `UserService` code
3. Hidden Dependencies: The constructor reveals nothing about what the service actually needs
4. Resource Management Issues: Each instance creates its own database connection
5. Configuration Problems: No way to configure the database connection externally

### Dependency Injection Benefits { #dependency-injection-benefits }

**The Dependency Injection Solution**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class UserService {
        private final DatabaseConnection connection;

        // Dependencies are explicitly declared
        public UserService(DatabaseConnection connection) {
            this.connection = connection;
        }

        public User findUserById(long id) {
            return connection.query("SELECT * FROM users WHERE id = ?", id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class UserService(
        private val connection: DatabaseConnection
    ) {
        // Dependencies are explicitly declared in primary constructor

        fun findUserById(id: Long): User {
            return connection.query("SELECT * FROM users WHERE id = ?", id)
        }
    }
    ```

**Key Benefits of Dependency Injection**:

1. **Testability**: Components can be tested with mock dependencies

===! ":fontawesome-brands-java: `Java`"

       ```java
       @Test
       public void testUserService() {
           DatabaseConnection mockConnection = mock(DatabaseConnection.class);
           UserService service = new UserService(mockConnection);
           // Test the service logic without database dependencies
       }
       ```

=== ":simple-kotlin: `Kotlin`"

       ```kotlin
       @Test
       fun testUserService() {
           val mockConnection = mock(DatabaseConnection::class.java)
           val service = UserService(mockConnection)
           // Test the service logic without database dependencies
       }
       ```

2. **Flexibility**: Different implementations can be injected based on environment

===! ":fontawesome-brands-java: `Java`"

       ```java
       // Production environment
       DatabaseConnection prodConnection = new PostgreSQLConnection();
       UserService prodService = new UserService(prodConnection);

       // Test environment
       DatabaseConnection testConnection = new InMemoryDatabaseConnection();
       UserService testService = new UserService(testConnection);
       ```

=== ":simple-kotlin: `Kotlin`"

       ```kotlin
       // Production environment
       val prodConnection = PostgreSQLConnection()
       val prodService = UserService(prodConnection)

       // Test environment
       val testConnection = InMemoryDatabaseConnection()
       val testService = UserService(testConnection)
       ```

3. **Explicit Dependencies**: Constructor parameters clearly document requirements
4. **Resource Management**: Connection lifecycle can be managed externally
5. **Configuration**: Database settings can be configured at the application level

### Understanding Inversion of Control { #understanding-inversion-control }

**Inversion of Control** is the architectural principle that underlies dependency injection. IoC represents a fundamental shift in how control flow is managed in software systems.

**Traditional Control Flow**:

```
Application Code -> Creates Objects -> Manages Dependencies -> Executes Business Logic
```

**Inverted Control Flow**:

```
Framework/Container -> Creates Objects -> Injects Dependencies -> Application Code Executes Business Logic
```

**The Inversion Principle**:

In traditional programming, your application code is responsible for:

- Creating all necessary objects
- Managing object lifecycles
- Coordinating between components
- Handling configuration

With IoC, these responsibilities are inverted:

- The framework creates objects
- The framework manages lifecycles
- The framework coordinates components
- The framework handles configuration

IoC Implementation Patterns:

1. Factory Pattern: Centralized object creation
2. Service Locator: Components request dependencies from a central registry
3. Dependency Injection: Dependencies are pushed into components

Why IoC Matters:

IoC enables several important architectural benefits:

- Separation of Concerns: Business logic is separated from infrastructure concerns
- Modularity: Components can be developed and tested independently
- Maintainability: Changes to infrastructure don't affect business logic
- Testability: Components can be easily isolated for testing

In Code:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Traditional approach - you control all object creation
    public class Application {
        public static void main(String[] args) {
            Database db = new Database();           // You create
            EmailService email = new EmailService(); // You create
            OrderService service = new OrderService(db, email); // You create

            service.processOrder(order); // You control
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Traditional approach - you control all object creation
    fun main() {
        val db = Database()           // You create
        val email = EmailService()    // You create
        val service = OrderService(db, email) // You create

        service.processOrder(order) // You control
    }
    ```

### When Old Approaches Break { #old-approaches-break }

While the traditional approach of manually creating and managing dependencies works perfectly well for small applications with just a few classes, it becomes increasingly problematic as your
application grows to dozens or hundreds of components.

**Why Scale Matters:**

The traditional approach requires you to manually instantiate and wire together every object in your application. For a small app with 3-5 classes, this is straightforward. But when your application
contains 20, 50, or 100+ classes, this manual approach becomes a maintenance nightmare.

**Example: A 20+ Class Application (Traditional Approach)**

Imagine building an application with the following components:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class EcommerceApplication {
        public static void main(String[] args) {
            // Infrastructure Layer (8 classes)
            DatabaseConfig dbConfig = new DatabaseConfig("localhost", "ecommerce", "user", "pass");
            DatabaseConnection dbConnection = new DatabaseConnection(dbConfig);
            RedisConfig redisConfig = new RedisConfig("localhost", 6379);
            RedisConnection redisConnection = new RedisConnection(redisConfig);
            EmailConfig emailConfig = new EmailConfig("smtp.example.com", 587, "user@example.com");
            EmailService emailService = new EmailService(emailConfig);
            PaymentGatewayConfig paymentConfig = new PaymentGatewayConfig("payment_key_123");
            PaymentGateway paymentGateway = new PaymentGateway(paymentConfig);

            // Data Access Layer (6 classes)
            UserRepository userRepository = new UserRepository(dbConnection);
            ProductRepository productRepository = new ProductRepository(dbConnection);
            OrderRepository orderRepository = new OrderRepository(dbConnection);
            CartRepository cartRepository = new CartRepository(redisConnection);
            AuditRepository auditRepository = new AuditRepository(dbConnection);
            InventoryRepository inventoryRepository = new InventoryRepository(dbConnection);

            // Business Logic Layer (8 classes)
            UserService userService = new UserService(userRepository, emailService);
            ProductService productService = new ProductService(productRepository, inventoryRepository);
            CartService cartService = new CartService(cartRepository, productService);
            OrderService orderService = new OrderService(orderRepository, paymentGateway, emailService);
            PaymentService paymentService = new PaymentService(paymentGateway, orderRepository);
            InventoryService inventoryService = new InventoryService(inventoryRepository, productRepository);
            AuditService auditService = new AuditService(auditRepository);
            NotificationService notificationService = new NotificationService(emailService);

            // Presentation Layer (4 classes)
            UserController userController = new UserController(userService, auditService);
            ProductController productController = new ProductController(productService, auditService);
            OrderController orderController = new OrderController(orderService, cartService, auditService);
            CartController cartController = new CartController(cartService, auditService);

            // Application Bootstrap (2 classes)
            // ... and more
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun main() {
        // Infrastructure Layer (8 classes)
        val dbConfig = DatabaseConfig("localhost", "ecommerce", "user", "pass")
        val dbConnection = DatabaseConnection(dbConfig)
        val redisConfig = RedisConfig("localhost", 6379)
        val redisConnection = RedisConnection(redisConfig)
        val emailConfig = EmailConfig("smtp.example.com", 587, "user@example.com")
        val emailService = EmailService(emailConfig)
        val paymentConfig = PaymentGatewayConfig("payment_key_123")
        val paymentGateway = PaymentGateway(paymentConfig)

        // Data Access Layer (6 classes)
        val userRepository = UserRepository(dbConnection)
        val productRepository = ProductRepository(dbConnection)
        val orderRepository = OrderRepository(dbConnection)
        val cartRepository = CartRepository(redisConnection)
        val auditRepository = AuditRepository(dbConnection)
        val inventoryRepository = InventoryRepository(dbConnection)

        // Business Logic Layer (8 classes)
        val userService = UserService(userRepository, emailService)
        val productService = ProductService(productRepository, inventoryRepository)
        val cartService = CartService(cartRepository, productService)
        val orderService = OrderService(orderRepository, paymentGateway, emailService)
        val paymentService = PaymentService(paymentGateway, orderRepository)
        val inventoryService = InventoryService(inventoryRepository, productRepository)
        val auditService = AuditService(auditRepository)
        val notificationService = NotificationService(emailService)

        // Presentation Layer (4 classes)
        val userController = UserController(userService, auditService)
        val productController = ProductController(productService, auditService)
        val orderController = OrderController(orderService, cartService, auditService)
        val cartController = CartController(cartService, auditService)

        // Application Bootstrap (2 classes)
        // ... and more
    }
    ```

**With 100+ Classes, This Becomes Impossible:**

- Your main method would be 1000+ lines long
- Understanding the dependency graph requires a separate diagram
- You must manually ensure components are created in the correct order
- Adding a new feature requires touching dozens of files
- A change to one component requires understanding its entire dependency chain
- Testing any component requires instantiating hundreds of objects and becomes a nightmare
- A single configuration change cascades through the entire application
- Adding a new feature requires updating the main method, potentially breaking existing initialization order

**The Dependency Injection Solution:**

With DI, you declare dependencies at the component level, and the framework handles all the complexity:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface EcommerceApplication extends
        InfrastructureModule, DataAccessModule, BusinessLogicModule, PresentationModule {

        static void main(String[] args) {
            KoraApplication.run(EcommerceApplicationGraph::graph);
        }
    }

    // Each component just declares what it needs
    @Component
    public final class OrderService {
        private final OrderRepository orderRepository;
        private final PaymentGateway paymentGateway;
        private final EmailService emailService;

        public OrderService(OrderRepository orderRepository,
                            PaymentGateway paymentGateway,
                            EmailService emailService) {
            this.orderRepository = orderRepository;
            this.paymentGateway = paymentGateway;
            this.emailService = emailService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface EcommerceApplication :
        InfrastructureModule, DataAccessModule, BusinessLogicModule, PresentationModule

    fun main() {
        KoraApplication.run(EcommerceApplicationGraph::graph)
    }

    // Each component just declares what it needs
    @Component
    class OrderService(
        private val orderRepository: OrderRepository,
        private val paymentGateway: PaymentGateway,
        private val emailService: EmailService
    )
    ```

**The framework automatically:**

- Creates all objects in the correct order
- Manages resource lifecycles
- Handles configuration injection
- Provides dependency resolution
- Enables easy testing with mocks

This is why dependency injection becomes essential as applications grow beyond a handful of classes.

===! ":fontawesome-brands-java: `Java`"

    ```java
    // IoC/DI (framework controls object creation)
    @KoraApp
    public interface Application {

        // Framework creates and injects everything reachable from a root
        @Root
        default OrderService orderService(OrderRepository repository) {
            return new OrderService(repository);
        }

        static void main(String[] args) {
            // Framework handles all object creation and injection
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // IoC/DI (framework controls object creation)
    @KoraApp
    interface Application {

        // Framework creates and injects everything reachable from a root
        @Root
        fun orderService(repository: OrderRepository): OrderService = OrderService(repository)
    }

    fun main() {
        // Framework handles all object creation and injection
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Benefits Comparison:

| Aspect          | Traditional                            | Dependency Injection                     |
|-----------------|----------------------------------------|------------------------------------------|
| Testing         | Hard (uses real services)              | Easy (inject mocks)                      |
| Flexibility     | Low (hardcoded dependencies)           | High (inject any implementation)         |
| Reusability     | Low (tied to specific implementations) | High (works with any compatible service) |
| Maintainability | Low (changes affect multiple places)   | High (change injection, not code)        |
| Clarity         | Low (dependencies hidden)              | High (constructor shows needs)           |

Now that you understand the fundamentals, let's explore how Kora implements these concepts with compile-time dependency injection!

---

## Kora Architecture { #kora-architecture }

Kora uses compile-time dependency injection, which means:

1. Build-time Analysis: Dependencies are analyzed during compilation by an annotation processor (Java) or a KSP symbol processor (Kotlin)
2. Component Discovery: Classes annotated with `@Component`, `@Module` interfaces, and factory methods reachable from `@KoraApp` are collected
3. Root Selection: Resolution starts from `@Root` declarations and walks the dependency edges from there
4. Dependency Resolution: The processor resolves every dependency claim, detects cycles, and builds an acyclic graph
5. Code Generation: An `<AppName>Graph` class is generated as ordinary Java/Kotlin source that produces an `ApplicationGraphDraw`
6. Runtime Performance: No reflection and no classpath scanning - everything is resolved at compile time

> Important Scope Limitation: Kora's processors only scan Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces. Components in regular Gradle modules without these
> interfaces will not be discovered or processed by the DI system.

### How It Works in Kora { #it-works-kora }

1. Annotation Processing: `@KoraApp` interfaces are processed at compile time by `KoraAppProcessor`
2. Component Discovery: Collects `@Component` classes, `@Module` interfaces, methods inherited by `@KoraApp`, and generated submodules within the current Gradle module
3. Dependency Resolution: `GraphBuilder` resolves every dependency claim starting from the root set and detects cycles
4. Graph Generation: Generates the `<AppName>Graph` class holding one `Node` per component plus their initialization logic
5. Runtime Execution: `KoraApplication.run(...)` initializes components in dependency order and installs a shutdown hook

> Critical Scope Limitation: Kora's processors only process Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces. Components in regular Gradle modules without these
> interfaces will be completely ignored by the DI system.

Architectural Benefits of Explicit Control:
This deliberate design choice gives you complete control over your application's dependency graph. Unlike frameworks that automatically instantiate everything on the classpath, Kora ensures you
explicitly declare what components you want. This prevents:

- Resource waste from unwanted component instantiation
- Security risks from transitive dependency components being activated
- Debugging complexity from unknown running components
- Performance overhead from classpath scanning
- Unpredictable behavior when dependencies change

With Kora, your `@KoraApp` interface serves as an explicit manifest of everything running in your application.

### Generated Code { #generated-code }

When you annotate an interface with `@KoraApp`, the processor generates two types next to it:

- `$<AppName>Impl` - a class implementing your application interface, used to invoke your `default` factory methods
- `<AppName>Graph` - a `Supplier<ApplicationGraphDraw>` that builds the graph description, with a `static graph()` accessor used as the entry point

A simplified sketch of what is generated for an interface called `Application`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Generated at compile time, in the same package as Application
    public class ApplicationGraph implements Supplier<ApplicationGraphDraw> {

        private static final ApplicationGraphDraw graphDraw;
        private static final ComponentHolder0 holder0;

        static {
            var impl = new $ApplicationImpl();                            //(1)!
            graphDraw = new ApplicationGraphDraw(Application.class);
            holder0 = new ComponentHolder0(graphDraw, impl);              //(2)!
        }

        public static ApplicationGraphDraw graph() {                      //(3)!
            return graphDraw;
        }

        @Override
        public ApplicationGraphDraw get() {
            return graphDraw;
        }

        public static final class ComponentHolder0 {
            private final Node<MessageFormatter> component0;              //(4)!
            private final Node<EmailNotifier> component1;
            // one Node per component in the graph
        }
    }
    ```

    1. Implementation of your `@KoraApp` interface; it is what actually calls your `default` factory methods.
    2. Components are registered in numbered holder classes, 500 components per class, so that very large graphs still compile.
    3. The static method referenced as `ApplicationGraph::graph` when starting the application.
    4. Each component becomes a `Node<T>` that knows its factory, its create dependencies, and its refresh dependencies.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Generated at compile time, in the same package as Application
    class ApplicationGraph : Supplier<ApplicationGraphDraw> {

        override fun get(): ApplicationGraphDraw = graphDraw

        companion object {
            val graphDraw: ApplicationGraphDraw

            init {
                val impl = `$ApplicationImpl`()                            //(1)!
                graphDraw = ApplicationGraphDraw(Application::class.java)
                holder0 = ComponentHolder0(graphDraw, impl)                //(2)!
            }

            fun graph(): ApplicationGraphDraw = graphDraw                  //(3)!
        }

        class ComponentHolder0(graphDraw: ApplicationGraphDraw, impl: `$ApplicationImpl`) {
            val component0: Node<MessageFormatter>                         //(4)!
            val component1: Node<EmailNotifier>
            // one Node per component in the graph
        }
    }
    ```

    1. Implementation of your `@KoraApp` interface; it is what actually calls your interface factory functions.
    2. Components are registered in numbered holder classes, 500 components per class, so that very large graphs still compile.
    3. The function referenced as `ApplicationGraph::graph` when starting the application.
    4. Each component becomes a `Node<T>` that knows its factory, its create dependencies, and its refresh dependencies.

You never write this class by hand, but knowing that it exists is useful: it is regular source code you can open in `build/generated`, step through in a debugger, and read when a wiring decision is
unclear.

### Compile Time and Runtime { #compile-time-runtime }

**Compile Time (Annotation Processing):**

- Analyzes source code for components and dependencies within `@KoraApp`/`@KoraSubmodule` modules only
- Validates the dependency graph (no cycles, all dependencies available, at least one root)
- Generates optimized initialization code
- Provides compile-time error checking

**Runtime (Application Execution):**

- Executes generated initialization code
- Initializes each node on its own virtual thread, respecting dependency order, so independent branches start in parallel
- Manages component lifecycle through `Lifecycle`
- Handles graceful shutdown through a JVM shutdown hook installed by `KoraApplication.run(...)`
- Supports component refresh via `ValueOf<T>` when a source such as the configuration watcher signals a change

> **Scope Critical**: Compile-time processing only occurs in Gradle modules containing `@KoraApp` or `@KoraSubmodule` interfaces. Code in regular modules is not analyzed or processed at compile time.

Application code stays synchronous. Kora 2.0 runs blocking code on virtual threads instead of asking you to model everything as reactive streams or coroutines, so a component method is a plain method
and a constructor is a plain constructor.

### Annotation Processors { #annotation-processors }

Kora's compile-time processing consists of:

1. `KoraAppProcessor`: main processor handling `@KoraApp`, `@Module`, `@Component`
2. `KoraSubmoduleProcessor`: generates the `<Name>SubmoduleImpl` interface for every `@KoraSubmodule`
3. `GraphBuilder`: resolves dependency claims from the root set, detects cycles, and orders components
4. `ComponentDependencyHelper`: parses dependency claims from constructor and factory method parameters
5. Extensions: a pluggable mechanism that generates components on demand (JSON readers/writers, repositories, HTTP clients, config extractors, validators, mappers)

The processors are wired into the build as:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        annotationProcessor "io.koraframework:annotation-processors"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        ksp("io.koraframework:symbol-processors")
    }
    ```

> Scope Limitation: Kora's processors only activate and process code within Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces. Code in regular Gradle modules is
> completely invisible to these processors.

### Component Discovery Order { #component-discovery-order }

Before anything is resolved, the processor gathers every declaration it can see for the current `@KoraApp`:

1. Classes annotated with `@Component` in the current Gradle module
2. Factory methods declared by the `@KoraApp` interface itself and by every interface it extends, whether or not those interfaces are annotated with `@Module`
3. Factory methods of `@Module`-annotated interfaces found in the current Gradle module, including their inherited methods
4. Factory methods of `<Name>SubmoduleImpl` interfaces generated from `@KoraSubmodule` and extended by `@KoraApp`
5. Factory methods of nested modules contributed with `@FactoryModule`
6. Components generated on demand by extensions while the graph is being resolved

Declarations with generic type parameters are kept separately as *component templates* and are only materialized when a concrete type is requested.

> Scope Note: Component discovery only occurs within Gradle modules containing `@KoraApp` or `@KoraSubmodule` interfaces. Components in regular Gradle modules will not be discovered regardless of
> their annotations.

### Dependency Resolution Algorithm { #dependency-resolution-algorithm }

1. Root Set: collect every declaration annotated with `@Root`; if the set is empty the build fails with `@KoraApp has no root components`
2. Claim Parsing: every constructor or factory method parameter becomes a `DependencyClaim` - a type, an optional tag, and a claim kind such as required, nullable, `ValueOf`, `PromiseOf`, or `All`
3. Component Matching: find declarations whose type is assignable to the claim type and whose tag matches the claim tag
4. Conflict Resolution: if several match, candidates without `@DefaultComponent` win; if more than one remains, the build fails
5. Cycle Detection: a cycle fails the build unless the cycle edge is declared through an interface (or a non-final class), in which case Kora generates a delegating proxy for it
6. Code Generation: emit node registration in topological order so that every dependency is registered before its consumer

Only components reachable from the root set end up in the graph. A factory method nobody depends on is never called, which is why entry points such as servers and consumers need `@Root`.

---

## Core Annotations { #core-annotations }

Kora provides several key annotations for dependency injection, all in `io.koraframework.common.annotation`:

### `@KoraApp` { #koraapp }

Marks the main application interface and serves as the core of Kora's dependency container. This annotation labels the interface within which factory methods for creating components and module
dependencies are defined. Each such interface produces its own dependency graph, and an application normally declares exactly one.

What `@KoraApp` Does:

- Container Entry Point: Defines the root of your application's dependency container
- Component Registry: Registers all factory methods and component accessors
- Module Integration: Connects external modules through interface inheritance
- Application Bootstrap: Provides the starting point for `KoraApplication.run(...)`

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
        // Factory methods and component accessors

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {
        // Factory methods and component accessors
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

**Requirements:**

- Must be an interface, not a class - applying `@KoraApp` to a class fails with `@KoraApp can only be applied to interfaces`
- One per application graph; the processor generates a separate graph class for every `@KoraApp` interface it finds
- Can extend multiple module interfaces
- Must reach at least one `@Root` declaration, otherwise the build fails with `@KoraApp has no root components`

**Container Building Process:**
At compile time, Kora uses the `@KoraApp` interface to:

1. Discover all factory methods and component dependencies
2. Validate the dependency graph for cycles and missing components
3. Generate optimized initialization code
4. Create the `<AppName>Graph` class used at runtime

**Why Interfaces? Multiple Inheritance and Factory Override Control**

Kora requires `@KoraApp` and all modules to be interfaces rather than classes for architectural reasons that enable powerful dependency injection capabilities.

**Multiple Inheritance**: Interfaces support multiple inheritance, allowing your application to compose functionality from multiple modules:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface EcommerceApplication extends
        UndertowPublicHttpServerModule,   // HTTP server capabilities
        JdbcDatabaseModule,               // Database connectivity
        CaffeineCacheModule,              // Caching services
        HoconConfigModule {               // Configuration

        // Your application-specific factories
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface EcommerceApplication :
        UndertowPublicHttpServerModule,   // HTTP server capabilities
        JdbcDatabaseModule,               // Database connectivity
        CaffeineCacheModule,              // Caching services
        HoconConfigModule {               // Configuration

        // Your application-specific factories
    }
    ```

**Factory Method Override**: Interface default methods can be overridden, giving you control over dependency injection at the language level:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Library provides default implementation
    @Module
    public interface CacheModule {
        @DefaultComponent
        default Cache cache() {
            return new InMemoryCache(); // Default implementation
        }
    }

    // Your application can override with custom implementation
    @KoraApp
    public interface Application extends CacheModule {  // <----- Connected module
        @Override
        default Cache cache() {
            return new RedisCache(); // Override with Redis
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Library provides default implementation
    @Module
    interface CacheModule {
        @DefaultComponent
        fun cache(): Cache = InMemoryCache() // Default implementation
    }

    // Your application can override with custom implementation
    @KoraApp
    interface Application : CacheModule {  // <----- Connected module
        override fun cache(): Cache = RedisCache() // Override with Redis
    }
    ```

**Component as Factory Method**: Components aren't limited to classes - they can also be defined as factory methods in interfaces, giving you declarative control over IoC:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
        // Component defined as factory method (not a class)
        default UserService userService(UserRepository repository, EmailService email) {
            // You control exactly how UserService is created
            var service = new UserService(repository, email);
            service.setTimeout(Duration.ofSeconds(30)); // Custom configuration
            return service;
        }

        // Another component as factory method
        default OrderProcessor orderProcessor(UserService userService, PaymentService payment) {
            return new OrderProcessor(userService, payment, new OrderValidator());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {
        // Component defined as factory method (not a class)
        fun userService(repository: UserRepository, email: EmailService): UserService {
            // You control exactly how UserService is created
            val service = UserService(repository, email)
            service.setTimeout(Duration.ofSeconds(30)) // Custom configuration
            return service
        }

        // Another component as factory method
        fun orderProcessor(userService: UserService, payment: PaymentService): OrderProcessor =
            OrderProcessor(userService, payment, OrderValidator())
    }
    ```

Why This Design Matters:

1. Intuitive Language-Level Control: IoC behavior is controlled using familiar language constructs (interfaces, default methods) rather than XML or reflection-driven configuration
2. Type-Safe Configuration: Factory methods are checked at compile time, preventing runtime configuration errors
3. Easy Testing: Factory methods can be overridden in tests to inject mocks without complex test frameworks
4. Modular Composition: Multiple inheritance allows clean separation of concerns across different modules
5. Override Flexibility: Change implementations by overriding a method, with no framework-specific configuration needed

This interface-based approach makes dependency injection feel like a natural extension of the language, giving you powerful IoC capabilities while maintaining simplicity and type safety.

#### Why Explicit Control Matters { #explicit-control-matters }

Kora's design philosophy prioritizes explicit control over implicit magic. Unlike traditional DI frameworks that automatically scan the classpath and instantiate everything they find, Kora
requires you to explicitly declare what dependencies you want in your application.

The Problem with Automatic Discovery:

- Unpredictable Behavior: You never know what will be instantiated just by adding a JAR to your classpath
- Hidden Dependencies: Components can be created without your knowledge, consuming resources
- Debugging Nightmares: When something goes wrong, you have to figure out what unwanted components are running
- Security Risks: Vulnerable components might be instantiated automatically
- Performance Issues: Every JAR on the classpath gets scanned, even if not needed

**Kora's Explicit Approach:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        io.koraframework.http.server.undertow.UndertowPublicHttpServerModule,  // Explicitly included
        io.koraframework.database.jdbc.JdbcDatabaseModule,                     // Explicitly included
        // io.koraframework.cache.caffeine.CaffeineCacheModule,                // Commented out = not included
        com.example.MyCustomModule {                                           // Your custom module
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        io.koraframework.http.server.undertow.UndertowPublicHttpServerModule,  // Explicitly included
        io.koraframework.database.jdbc.JdbcDatabaseModule,                     // Explicitly included
        // io.koraframework.cache.caffeine.CaffeineCacheModule,                // Commented out = not included
        com.example.MyCustomModule                                             // Your custom module
    ```

Benefits of Explicit Control:

- Predictable Dependencies: You know exactly what's running in your application
- Resource Efficiency: Only instantiate what you actually need
- Clear Dependency Graph: Easy to understand and debug component relationships
- Security by Design: No surprise instantiations from transitive dependencies
- Performance: No classpath scanning overhead - everything is resolved at compile time
- Maintainability: Changes to dependencies are explicit and tracked in code

Real-World Impact:
With automatic frameworks, developers often spend hours debugging why their application is slow or consuming unexpected resources. With Kora, if a component isn't reachable from a root in
your `@KoraApp` graph, it simply does not exist in your application - no surprises, no hidden costs.

### `@Component` { #component }

Marks a class as a component (dependency) in the dependency container. All components in Kora are singletons - classes that have only one instance created throughout the application lifecycle.
Components are created only if they are root components (marked with `@Root`) or if they are required as dependencies by something reachable from a root.

What Components Are:

- Singleton Instances: One instance per application lifecycle
- Dependency Providers: Can be injected into other components
- Conditional Initialization: Created only if required by other components or marked with `@Root`
- Shared: The same instance is provided to all injection points

**Important Scope Limitation**: `@Component` classes can only be discovered and used within Gradle modules that contain either:

- A `@KoraApp` interface (main application module)
- A `@KoraSubmodule` interface (component discovery module)

Components in regular Gradle modules without these annotations will not be processed by Kora's processor.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {
        // Implementation
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService {
        // Implementation
    }
    ```

**Requirements:**

===! ":fontawesome-brands-java: `Java`"

    - The class must not be abstract - `@Component` on an abstract class or an interface is ignored, and concrete implementations are used instead
    - It must have exactly one public constructor, otherwise the build fails with `@Component class must have exactly one public constructor`
    - Constructor parameters become dependency claims
    - Declaring the class `final` is the normal choice; a class that uses AOP aspects must **not** be `final`, because Kora generates a proxy subclass for it
    - The class must live in a Gradle module with `@KoraApp` or `@KoraSubmodule`

=== ":simple-kotlin: `Kotlin`"

    - The class must not be abstract - `@Component` on an abstract class or an interface is ignored, and concrete implementations are used instead
    - It must have a primary constructor, otherwise the build fails with `@Component class must have a primary constructor`
    - Primary constructor parameters become dependency claims
    - Classes are final by default, which is the normal choice; a class that uses AOP aspects must be declared `open`, because Kora generates a proxy subclass for it
    - The class must live in a Gradle module with `@KoraApp` or `@KoraSubmodule`

Component Lifecycle:

- Discovery: found by the processor during compilation
- Validation: dependencies checked at compile time
- Creation: instance created at application startup if reachable from a root
- Injection: the same instance provided to all dependent components
- Destruction: `Lifecycle#release` is called by the container during shutdown, in reverse dependency order

### `@Module` { #module }

Groups related component factories together and marks interfaces as modules to be injected into the dependency container at compile time. A module is an interface that contains factory methods for
creating components. All factory methods within a module become available to the dependency container.

What Modules Do:

- Factory Collection: Group related component factories in one place
- Code Organization: Separate concerns across different modules
- Reusability: Modules can be shared across applications
- Override Support: Factory methods can be overridden in extending interfaces

Scope: `@Module` interfaces are processed within Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces. External modules from libraries are inherited through interface extension.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface DatabaseModule {
        default UserRepository userRepository(DataSource dataSource) {
            return new JdbcUserRepository(dataSource);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface DatabaseModule {
        fun userRepository(dataSource: DataSource): UserRepository =
            JdbcUserRepository(dataSource)
    }
    ```

Module Types:

- Internal Modules: `@Module` interfaces defined in the same Gradle module as `@KoraApp`; they are picked up automatically, without being extended
- Mixed-in Modules: any interface extended by `@KoraApp`, even without `@Module`; its factory methods join the graph
- External Modules: provided by libraries and connected by extending them from `@KoraApp`
- Submodules: `<Name>SubmoduleImpl` interfaces generated from `@KoraSubmodule` in another Gradle module

Module Requirements:

- Must be an interface, not a class - `@Module` on a class fails with `@Module can only be applied to interfaces`
- Factory methods must have a body (`default` in Java, a regular function body in Kotlin)
- Factory methods must return a reference type; primitives are rejected
- Must be in the same Gradle module as `@KoraApp` or `@KoraSubmodule` to be discovered automatically

Factory Method Rules:

- Must return a component, and a raw generic return type is rejected
- Can take other components as parameters
- Parameters become dependency claims
- Parameters may be optional components (`@Nullable` in Java, `T?` in Kotlin)
- Methods are called in dependency order at startup

> **External Library Components**: Components and modules from external libraries are **not automatically discovered** by Kora's processor. Even if a library contains `@Component` classes
> or `@Module` interfaces, they will be invisible to your application unless you explicitly extend their module interfaces in your `@KoraApp` interface. This is a deliberate design choice for explicit
> dependency management.

### `@KoraSubmodule` { #korasubmodule }

Marks an interface for which to build a module for the current compilation module. The generated interface contains all components marked with `@Module` and `@Component` annotations found in that
Gradle module's source code. This annotation is particularly useful for multi-module Gradle applications where different modules contain different pieces of functionality, and the main `@KoraApp`
application is built in a separate module.

What `@KoraSubmodule` Does:

- Component Discovery: Scans the current Gradle module for `@Module` and `@Component` annotations
- Module Generation: Creates a `<Name>SubmoduleImpl` interface with all discovered modules and components
- Multi-Module Support: Enables component sharing across Gradle modules
- Boundary Definition: Defines where Kora's processor scans for components
- Build Optimization: Enables Gradle's build caching and incremental compilation by isolating functionality into separate modules

Scope: `@KoraSubmodule` interfaces define the boundaries where Kora's processor will scan for components. Components outside these boundaries are not processed.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraSubmodule
    public interface ApplicationModules {
        // Generated factory methods for all discovered components
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraSubmodule
    interface ApplicationModules {
        // Generated factory methods for all discovered components
    }
    ```

How It Works:

1. Discovery: Finds all `@Module` interfaces and `@Component` classes in the current Gradle module
2. Inheritance: The generated `ApplicationModulesSubmoduleImpl` interface inherits from all discovered `@Module` interfaces
3. Factory Generation: Creates default methods for all discovered `@Component` classes
4. Integration: Your `@KoraApp` extends the `@KoraSubmodule` interface, and Kora resolves the generated `…SubmoduleImpl` behind it

Use Cases:

- Multi-Module Projects: Share components across Gradle modules
- Library Development: Expose components from a library module
- Modular Architecture: Separate concerns across different build modules
- Component Organization: Group related components by functionality
- Large Single Applications: Organize complex monolithic applications into isolated Gradle modules for better build performance and maintainability
- Build Optimization: Leverage Gradle's build caching by separating functionality into independent modules that can be built and cached separately

> If the generated interface is not on the classpath yet, the build reports `Kora submodule was not generated yet`. That normally means the module providing the `@KoraSubmodule` has not been compiled,
> or the Kora processor is not applied to it.

### `@Root` { #root }

Marks components that must always be created when the application starts, even if nothing else depends on them. Root components are the entry points of the graph: Kora starts dependency resolution
from the root set and only builds what is reachable from it.

What `@Root` Does:

- Guaranteed Initialization: Component is always created at startup
- Graph Entry Point: Everything the root needs is pulled into the graph
- Lifecycle Management: The component participates in application startup and shutdown
- Entry Points: Perfect for servers, consumers, schedulers, and background services

Common Use Cases:

- HTTP Servers: Web servers that need to start listening immediately
- Message Consumers: Kafka consumers, queue processors
- Background Services: Cache warmers, health checkers, schedulers
- Bootstrap Components: anything that only produces side effects, such as preparing external state

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class NotificationService {
        // Always created, even if nothing injects it
    }

    @KoraApp
    public interface Application {
        @Root
        default HttpServer httpServer(UserController controller) {
            return new HttpServer(controller);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class NotificationService {
        // Always created, even if nothing injects it
    }

    @KoraApp
    interface Application {
        @Root
        fun httpServer(controller: UserController): HttpServer =
            HttpServer(controller)
    }
    ```

`@Root` vs Regular Components:

- Regular Components: created only if reachable from a root through dependency edges
- `@Root` Components: always created at startup

When to Use `@Root`:

- The component provides a service that should always be running
- The component needs to start processing immediately (servers, consumers)
- The component performs critical initialization (schema preparation, cache warming, bucket creation)
- The component collects metrics or monitoring data

!!! warning "At least one root is required"

    A `@KoraApp` with no reachable `@Root` fails to compile with `@KoraApp has no root components`. Framework modules usually contribute their own roots - for example, an HTTP server module marks its
    server component as a root - but an application that only defines plain components must mark at least one of them itself.

    The same rule explains a subtle class of bugs: a `Lifecycle` component that only prepares external state and that nobody injects is dropped from the graph, and everything it pulled in disappears
    with it. Mark it `@Root`.

### `@DefaultComponent` { #defaultcomponent }

Marks factories or components that provide default implementations intended to be overridden by users. If another component of the same type and tag exists in the graph without this annotation, it
takes precedence during injection over the `@DefaultComponent` one.

What `@DefaultComponent` Does:

- Default Provision: Provides fallback implementations for components
- Override Support: Allows users to replace defaults without modifying library code
- Library-Friendly: Enables libraries to provide sensible defaults
- Priority System: Lower priority than non-annotated factories

Use Cases:

- Library Defaults: Libraries provide default implementations that users can override
- Configuration Options: Different implementations based on environment
- Extension Points: Allow users to customize behavior without changing library code

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface CacheModule {
        @DefaultComponent
        default Cache defaultCache() {
            return new InMemoryCache();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface CacheModule {
        @DefaultComponent
        fun defaultCache(): Cache = InMemoryCache()
    }
    ```

**Override Behavior:**

There are two ways to replace a default. You can override the method itself, or you can simply declare another factory of the same type without `@DefaultComponent`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends CacheModule {  // <----- Connected module

        // Option 1: override the method - the override carries no @DefaultComponent, so it wins
        @Override
        default Cache defaultCache() {
            return new RedisCache();
        }
    }

    @KoraApp
    public interface OtherApplication extends CacheModule {

        // Option 2: a different method providing the same type without @DefaultComponent also wins
        default Cache applicationCache() {
            return new RedisCache();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : CacheModule {  // <----- Connected module

        // Option 1: override the function - the override carries no @DefaultComponent, so it wins
        override fun defaultCache(): Cache = RedisCache()
    }

    @KoraApp
    interface OtherApplication : CacheModule {

        // Option 2: a different function providing the same type without @DefaultComponent also wins
        fun applicationCache(): Cache = RedisCache()
    }
    ```

**Resolution Rule:**

1. Candidates are matched by type and tag
2. If more than one matches, candidates **without** `@DefaultComponent` are preferred
3. If exactly one non-default candidate remains, it is used
4. If several non-default candidates remain, the build fails with `Multiple components match dependency`

**Best Practices:**

- Use for library-provided defaults that users might want to customize
- Don't use for application-specific components
- Clearly document what defaults are available for override

### `@Tag` { #tag }

Allows differentiation of multiple implementations of the same type and provides selective injection based on tags. A tag is a class reference rather than a string, which gives better refactoring
support and type safety. A component is registered with a specific tag and injected at points that request exactly the same tag.

What Tags Do:

- Implementation Selection: Choose specific implementations of interfaces
- Multiple Instances: Support multiple instances of the same type in one graph
- Type Safety: Uses class references instead of strings
- Refactoring Safe: The IDE can track tag usage across the codebase

The annotation carries exactly one class:

```java
public @interface Tag {
    Class<?> value();
}
```

Basic Usage:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Tag classes (usually empty marker classes)
    public final class RedisTag {
        private RedisTag() {}
    }

    public final class InMemoryTag {
        private InMemoryTag() {}
    }

    // Tagged implementations
    @Tag(RedisTag.class)
    @Component
    public final class RedisCache implements Cache {
        // Redis implementation
    }

    @Tag(InMemoryTag.class)
    @Component
    public final class InMemoryCache implements Cache {
        // In-memory implementation
    }

    // Selective injection
    @Component
    public final class UserService {
        public UserService(@Tag(RedisTag.class) Cache cache) {
            // Injects RedisCache specifically
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Tag classes (usually empty marker classes)
    class RedisTag private constructor()

    class InMemoryTag private constructor()

    // Tagged implementations
    @Tag(RedisTag::class)
    @Component
    class RedisCache : Cache {
        // Redis implementation
    }

    @Tag(InMemoryTag::class)
    @Component
    class InMemoryCache : Cache {
        // In-memory implementation
    }

    // Selective injection
    @Component
    class UserService(@Tag(RedisTag::class) private val cache: Cache) {
        // Injects RedisCache specifically
    }
    ```

Tag Application:

- On Classes: `@Tag(MyTag.class) @Component final class MyClass`
- On Factory Methods: `@Tag(MyTag.class) default MyClass myClass()`
- On Parameters: `MyService(@Tag(MyTag.class) Dependency dep)`
- On Annotations: a custom annotation meta-annotated with `@Tag(MyTag.class)` behaves like that tag

Special Tags:

- `@Tag(Tag.Any.class)`: matches every component of the requested type, tagged or untagged
- `@Tag(Tag.Factory.class)`: inside a nested module contributed with `@FactoryModule`, means "use the same tag as the enclosing module method"

Tag Matching Rules:

1. An untagged claim matches only untagged components
2. A tagged claim matches only components carrying exactly that tag class
3. `Tag.Any` matches everything of the requested type
4. Matching compares the tag class itself; a tag hierarchy is not taken into account

Custom Tag Annotations:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(RedisTag.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
    public @interface RedisCache {}

    @Tag(InMemoryTag.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
    public @interface InMemoryCache {}

    // Usage
    @RedisCache
    @Component
    public final class RedisCacheImpl implements Cache {}

    @Component
    public final class UserService {
        public UserService(@RedisCache Cache cache) {/* ... */}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(RedisTag::class)
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.VALUE_PARAMETER)
    annotation class RedisCache

    @Tag(InMemoryTag::class)
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.VALUE_PARAMETER)
    annotation class InMemoryCache

    // Usage
    @RedisCache
    @Component
    class RedisCacheImpl : Cache

    @Component
    class UserService(@RedisCache private val cache: Cache)
    ```

### `@Conditional` { #conditional }

Makes a component's presence in the running graph depend on a condition evaluated during graph initialization. The condition itself is an ordinary graph component of type `GraphCondition`, registered
under a tag, so it can depend on configuration or on any other component.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.GraphCondition;
    import io.koraframework.common.annotation.Conditional;

    public final class ExportEnabled {
        private ExportEnabled() {}
    }

    @KoraApp
    public interface Application {

        @Tag(ExportEnabled.class)
        default GraphCondition exportEnabled(ExportConfig config) {       //(1)!
            return () -> config.enabled()
                ? GraphCondition.ConditionResult.matched("export.enabled = true")
                : GraphCondition.ConditionResult.failed("export.enabled = false");
        }

        @Root
        @Conditional(tag = ExportEnabled.class)                           //(2)!
        default ExportJob exportJob(ExportClient client) {
            return new ExportJob(client);
        }
    }
    ```

    1. A `GraphCondition` component registered under the `ExportEnabled` tag. Exactly one such component must exist for that tag.
    2. The component is created only when the condition reports `Matched`; otherwise the node stays uninitialized and reading it throws.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.GraphCondition
    import io.koraframework.common.annotation.Conditional

    class ExportEnabled private constructor()

    @KoraApp
    interface Application {

        @Tag(ExportEnabled::class)
        fun exportEnabled(config: ExportConfig): GraphCondition = GraphCondition {   //(1)!
            if (config.enabled()) GraphCondition.ConditionResult.matched("export.enabled = true")
            else GraphCondition.ConditionResult.failed("export.enabled = false")
        }

        @Root
        @Conditional(tag = ExportEnabled::class)                                     //(2)!
        fun exportJob(client: ExportClient): ExportJob = ExportJob(client)
    }
    ```

    1. A `GraphCondition` component registered under the `ExportEnabled` tag. Exactly one such component must exist for that tag.
    2. The component is created only when the condition reports `Matched`; otherwise the node stays uninitialized and reading it throws.

Rules worth remembering:

- Exactly one `GraphCondition` may carry a given tag, otherwise the build fails with `Multiple GraphCondition components match condition tag`
- A missing condition provider fails the build with `Component condition cannot be resolved`
- Conditions cascade: everything that exists only because of a conditional component is disabled together with it
- When two candidates of the same type are both conditional, Kora keeps both in the graph and lets the conditions choose at startup

---

## Component Discovery Priority { #component-discovery-priority }

When Kora needs to satisfy one dependency claim, it walks a fixed sequence of strategies. Understanding this order is essential for debugging dependency resolution issues and ensuring the correct
implementations are used.

Resolution order for one claim (type + tag):

1. **Concrete declarations** already known to the processor - `@Component` classes, factory methods of the `@KoraApp` interface and everything it extends, `@Module` interfaces of the current Gradle
   module, generated submodules, nested `@FactoryModule` modules, and components previously generated by extensions
2. **Component templates** - generic factory methods whose type parameters can be bound to the requested type
3. **Nullable fallback** - if the claim is nullable, the dependency resolves to `null`
4. **`Optional<T>` fallback** - if the claim is `Optional<T>` and nothing provides `T`, an empty `Optional` is supplied
5. **Extensions** - an extension generates the component on demand (JSON readers and writers, `@Repository` implementations, `@HttpClient` implementations, config extractors, validators, mappers)
6. **Failure** - otherwise the build fails with `No component found for dependency`

Within step 1, when several declarations match the same type and tag:

- Candidates **without** `@DefaultComponent` are preferred over `@DefaultComponent` ones
- If exactly one candidate remains, it is used
- If all remaining candidates are `@Conditional`, all of them are kept and the condition decides at startup
- Otherwise the build fails with `Multiple components match dependency`

**What This Means:**

- A concrete factory method always wins over a generic template of the same type
- A `@DefaultComponent` from a library is replaced simply by declaring your own factory of the same type and tag
- Extensions are a last resort, which is why a hand-written `JsonWriter<Foo>` component silently replaces the generated one
- Nothing is created "just in case" - only what a root needs is built

**Practical Example:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Library default - lowest priority
    @Module
    public interface UserModule {
        @DefaultComponent
        default UserService userService() {
            return new DefaultUserService();
        }
    }

    // Application factory - wins, because it carries no @DefaultComponent
    @KoraApp
    public interface Application extends UserModule {
        default UserService customUserService() {
            return new CustomUserService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Library default - lowest priority
    @Module
    interface UserModule {
        @DefaultComponent
        fun userService(): UserService = DefaultUserService()
    }

    // Application factory - wins, because it carries no @DefaultComponent
    @KoraApp
    interface Application : UserModule {
        fun customUserService(): UserService = CustomUserService()
    }
    ```

---

## Declaring Components { #declaring-components }

Components in Kora can be declared in multiple ways, each with different use cases. **All component declaration methods require the code to be within Gradle modules that
contain `@KoraApp` or `@KoraSubmodule` interfaces** - Kora's processor only scans these designated modules.

### Automatic Factory (`@Component`) { #automatic-factory-component }

Classes annotated with `@Component` are automatically registered if they meet the requirements:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {
        private final UserRepository repository;

        public UserService(UserRepository repository) {
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(
        private val repository: UserRepository
    )
    ```

**Requirements:**

- Not abstract
- Exactly one public constructor (Java) or a primary constructor (Kotlin)
- Not final only when AOP aspects are applied, because Kora subclasses the component to install them
- Constructor parameters become dependency claims

### Basic Factory Methods { #method-factory-basics }

Methods with a body in `@KoraApp` or `@Module` interfaces that return components:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
        default UserService userService(UserRepository repository) {
            return new UserService(repository);
        }

        default UserRepository userRepository() {
            return new InMemoryUserRepository();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {
        fun userService(repository: UserRepository): UserService =
            UserService(repository)

        fun userRepository(): UserRepository =
            InMemoryUserRepository()
    }
    ```

Use a factory method whenever construction needs a decision you want to keep in one place: choosing an implementation, wiring a third-party builder, or applying settings that do not belong in the
component's own constructor.

### Module Factory { #module-factory }

Factory methods within `@Module` interfaces:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface DatabaseModule {
        default DataSource dataSource() {
            return new HikariDataSource();
        }

        default UserRepository userRepository(DataSource dataSource) {
            return new JdbcUserRepository(dataSource);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface DatabaseModule {
        fun dataSource(): DataSource =
            HikariDataSource()

        fun userRepository(dataSource: DataSource): UserRepository =
            JdbcUserRepository(dataSource)
    }
    ```

A `@Module` interface declared in the same Gradle module as `@KoraApp` joins the graph automatically - you do not have to extend it. Extending it from `@KoraApp` is still useful when you want to
override one of its methods.

### External Module Factory { #external-module-factory }

Modules from external dependencies, inherited through interface extension:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;

    @KoraApp
    public interface Application extends
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule {
        // Inherits all factory methods from external modules
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule {
        // Inherits all factory methods from external modules
    }
    ```

> **Explicit Import Required**: External library components are not automatically available. You must explicitly extend the library's module interfaces in your `@KoraApp` interface. Simply adding a
> library to your classpath is not enough - the module interface extension makes the components available for dependency injection.

**This explicit approach prevents the common problems of automatic frameworks:**

- No surprise instantiation of unwanted components
- Clear visibility into what dependencies are actually used
- Better security through intentional inclusion
- Easier debugging and maintenance

### Submodule Factory { #submodule-factory }

Generated modules from `@KoraSubmodule` interfaces:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Gradle module :persistence
    @Module
    public interface PersistenceModule {
        default UserRepository userRepository() {
            return new InMemoryUserRepository();
        }
    }

    @KoraSubmodule
    public interface PersistenceSubmodule {
        // Generates factory methods for all @Module and @Component in this Gradle module
    }

    // Gradle module :application
    @KoraApp
    public interface Application extends PersistenceSubmodule {  // <----- Connected submodule
        // All components from the submodule are available
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Gradle module :persistence
    @Module
    interface PersistenceModule {
        fun userRepository(): UserRepository =
            InMemoryUserRepository()
    }

    @KoraSubmodule
    interface PersistenceSubmodule {
        // Generates factory methods for all @Module and @Component in this Gradle module
    }

    // Gradle module :application
    @KoraApp
    interface Application : PersistenceSubmodule {  // <----- Connected submodule
        // All components from the submodule are available
    }
    ```

### Generic Factory { #generic-factory }

Methods with generic type parameters that can create components of any matching type. These declarations are kept as component templates and are materialized only when a concrete type is requested.
Generic factories are particularly useful for creating type-safe components that work with different generic types.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ValidatorModule {
        // Generic factory for List validators
        default <T> Validator<List<T>> listValidator(Validator<T> validator, TypeRef<T> valueRef) {
            return new IterableValidator<>(validator);
        }

        // Generic factory for Set validators
        default <T> Validator<Set<T>> setValidator(Validator<T> validator, TypeRef<T> valueRef) {
            return new IterableValidator<>(validator);
        }

        // Generic factory for Collection validators
        default <T> Validator<Collection<T>> collectionValidator(Validator<T> validator, TypeRef<T> valueRef) {
            return new IterableValidator<>(validator);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ValidatorModule {
        // Generic factory for List validators
        fun <T> listValidator(validator: Validator<T>, valueRef: TypeRef<T>): Validator<List<T>> =
            IterableValidator(validator)

        // Generic factory for Set validators
        fun <T> setValidator(validator: Validator<T>, valueRef: TypeRef<T>): Validator<Set<T>> =
            IterableValidator(validator)

        // Generic factory for Collection validators
        fun <T> collectionValidator(validator: Validator<T>, valueRef: TypeRef<T>): Validator<Collection<T>> =
            IterableValidator(validator)
    }
    ```

**How It Works:**

- The `<T>` type parameter allows creating validators for any element type
- `TypeRef<T>` provides the concrete generic type information the factory was materialized for
- Kora can create `Validator<List<String>>`, `Validator<Set<User>>`, and so on
- A concrete factory always wins over a template for the same type
- Raw types are rejected: a claim such as `Validator` without type arguments fails the build

### Extension Mechanism { #extension-mechanism }

Extensions generate components on demand while the graph is being resolved. They run only when nothing else in the graph can satisfy a claim, which means a hand-written component of the same type
always takes precedence.

Extensions ship with the corresponding Kora processors and cover, among others:

- `JsonReader<T>` and `JsonWriter<T>` implementations for `@Json` annotated classes
- Implementations of `@Repository` interfaces for JDBC and Cassandra
- Implementations of `@HttpClient` interfaces
- gRPC client stubs
- Config extractors for `@ConfigSource` and `@ConfigMapper` interfaces
- `Validator<T>` implementations for `@Valid` annotated types
- MapStruct and Konvert mapper implementations

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JsonModule {

        @Root
        default UserPrinter userPrinter(JsonWriter<User> writer) {  //(1)!
            return new UserPrinter(writer);
        }
    }

    @Json
    public record User(String name, int age) {}
    ```

    1. Nothing declares a `JsonWriter<User>`; the JSON extension generates it while the graph is being resolved.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JsonModule {

        @Root
        fun userPrinter(writer: JsonWriter<User>): UserPrinter =        //(1)!
            UserPrinter(writer)
    }

    @Json
    data class User(val name: String, val age: Int)
    ```

    1. Nothing declares a `JsonWriter<User>`; the JSON extension generates it while the graph is being resolved.

### `@DefaultComponent` Factory { #defaultcomponent-factory }

Default implementations that can be overridden:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface CacheModule {
        @DefaultComponent
        default Cache cache() {
            return new InMemoryCache();
        }
    }

    // Can be overridden in the application:
    @KoraApp
    public interface Application extends CacheModule {  // <----- Connected module

        default Cache primaryCache() {
            return new RedisCache(); // Overrides the default
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface CacheModule {
        @DefaultComponent
        fun cache(): Cache = InMemoryCache()
    }

    // Can be overridden in the application:
    @KoraApp
    interface Application : CacheModule {  // <----- Connected module

        fun primaryCache(): Cache = RedisCache() // Overrides the default
    }
    ```

`@DefaultComponent` also works on classes, not only on factory methods, so a `@Component` class can be declared as a replaceable default.

### Factory Module { #factory-module }

`@FactoryModule` marks a module method whose **return value is itself a module**. The returned object becomes a component in the graph, and its public methods are treated as component factories. This
is how you register the same set of factories several times with different configuration.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class MessengerModule {                                //(1)!

        private final String header;

        public MessengerModule(String header) {
            this.header = header;
        }

        @Tag(Tag.Factory.class)                                         //(2)!
        public Messenger messenger(@Tag(Tag.Factory.class) Transport transport) {
            return new Messenger(this.header, transport);
        }
    }

    @KoraApp
    public interface Application {

        @Tag(SlackTag.class)
        @FactoryModule
        default MessengerModule slackModule() {                         //(3)!
            return new MessengerModule("SLACK");
        }

        @Tag(SignalTag.class)
        @FactoryModule
        default MessengerModule signalModule() {
            return new MessengerModule("SIGNAL");
        }

        @Tag(SlackTag.class)
        default Transport slackTransport() {
            return new HttpTransport("https://slack.example.com");
        }

        @Tag(SignalTag.class)
        default Transport signalTransport() {
            return new HttpTransport("https://signal.example.com");
        }

        @Root
        default Dispatcher dispatcher(@Tag(SlackTag.class) Messenger slack,
                                      @Tag(SignalTag.class) Messenger signal) {
            return new Dispatcher(slack, signal);
        }
    }
    ```

    1. A plain class whose public methods act as component factories.
    2. `@Tag(Tag.Factory.class)` means "the tag of the enclosing `@FactoryModule` method", so each instance produces its own tagged components and consumes its own tagged dependencies.
    3. The returned `MessengerModule` is registered in the graph under the `SlackTag` tag.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class MessengerModule(private val header: String) {                 //(1)!

        @Tag(Tag.Factory::class)                                        //(2)!
        fun messenger(@Tag(Tag.Factory::class) transport: Transport): Messenger =
            Messenger(header, transport)
    }

    @KoraApp
    interface Application {

        @Tag(SlackTag::class)
        @FactoryModule
        fun slackModule(): MessengerModule = MessengerModule("SLACK")   //(3)!

        @Tag(SignalTag::class)
        @FactoryModule
        fun signalModule(): MessengerModule = MessengerModule("SIGNAL")

        @Tag(SlackTag::class)
        fun slackTransport(): Transport = HttpTransport("https://slack.example.com")

        @Tag(SignalTag::class)
        fun signalTransport(): Transport = HttpTransport("https://signal.example.com")

        @Root
        fun dispatcher(
            @Tag(SlackTag::class) slack: Messenger,
            @Tag(SignalTag::class) signal: Messenger
        ): Dispatcher = Dispatcher(slack, signal)
    }
    ```

    1. A plain class whose public functions act as component factories.
    2. `@Tag(Tag.Factory::class)` means "the tag of the enclosing `@FactoryModule` function", so each instance produces its own tagged components and consumes its own tagged dependencies.
    3. The returned `MessengerModule` is registered in the graph under the `SlackTag` tag.

`@Tag(Tag.Factory.class)` is only valid inside a type reached through `@FactoryModule`; using it elsewhere fails the build with `@Tag.Factory can only be used inside factory modules`.

### No Automatic Creation { #automatic-creation }

Kora never instantiates a class just because it happens to be instantiable. A type must be provided by one of the mechanisms above - a `@Component` class, a factory method, a template, or an
extension. If nothing provides it, the build fails:

```
No component found for dependency:
  com.example.SomeService (no tags)
```

This is deliberate. It means a graph never silently grows an object you did not ask for, and every node in the running application can be traced back to a declaration you wrote or a module you
connected.

When a dependency genuinely may be absent, say so explicitly instead of relying on implicit creation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ReportService {

        public ReportService(@Nullable AuditSink auditSink,          //(1)!
                             Optional<MetricsSink> metricsSink) {    //(2)!
        }
    }
    ```

    1. Resolves to `null` when nothing provides `AuditSink`.
    2. Resolves to an empty `Optional` when nothing provides `MetricsSink`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ReportService(
        private val auditSink: AuditSink?,                           //(1)!
        private val metricsSink: Optional<MetricsSink>               //(2)!
    )
    ```

    1. Resolves to `null` when nothing provides `AuditSink`.
    2. Resolves to an empty `Optional` when nothing provides `MetricsSink`.

---

## Dependency Claims and Resolution { #dependency-claims-resolution }

Kora turns every constructor and factory method parameter into a *dependency claim*: the requested type, an optional tag, and a claim kind derived from the wrapper type and nullability. This is the
point where parameters stop being just Java or Kotlin types and become graph requirements.

Understanding dependency claims helps you read compiler errors. When Kora says that a dependency is missing, ambiguous, or cyclic, it is describing the claim it tried to resolve and the component
candidates it found in the graph.

The claim kinds Kora recognises are:

| Parameter shape                       | Meaning                                                          |
|---------------------------------------|------------------------------------------------------------------|
| `T`                                   | exactly one required component                                    |
| `@Nullable T` (Java) / `T?` (Kotlin)  | one optional component, `null` when absent                        |
| `Optional<T>`                         | one optional component, empty `Optional` when absent              |
| `ValueOf<T>`                          | handle that reads the current value of the component              |
| `PromiseOf<T>`                        | handle resolved after graph initialization, breaks cycles         |
| `All<T>`                              | every matching component                                          |
| `All<ValueOf<T>>` / `All<PromiseOf<T>>` | every matching component, each wrapped                          |
| `TypeRef<T>`                          | the concrete generic type a template was materialized for         |
| `Graph` / `RefreshableGraph`          | the graph itself, for infrastructure components                   |
| `Node<T>`                             | the graph node of a component, for infrastructure components      |

### Basic Dependency Types { #basic-dependency-types }

Most Kora dependencies are expressed directly in constructors or factory method parameters. The shape of the parameter tells Kora whether the component is required, optional, lazily accessed, or a
collection of implementations. These shapes let you model the relationship between components without adding container APIs to your business code.

Use the simplest shape that matches the domain rule. If the service cannot work without a repository, request the repository directly. If an integration is optional, mark it nullable. If you need all
implementations of an extension point, request `All<T>`. If you want to avoid refresh cascades or delay access to the actual component, request `ValueOf<T>`.

#### Required { #required }

Single required dependency that must exist.
This is the default and most common dependency form. A required parameter means the application graph is invalid unless exactly one matching component is available. It is the right choice for core
collaborators such as repositories, services, validators, configuration interfaces, and clients that are part of the normal application flow.

Required dependencies make failures explicit. If you forget to import a module or define a component, the build fails while Kora generates the graph instead of letting the application start with a
partially configured runtime.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        private final UserRepository repository;

        public UserService(UserRepository repository) { // ONE_REQUIRED
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(private val repository: UserRepository) // ONE_REQUIRED
    ```

#### Optional { #optional }

Single optional dependency that may be absent.
Optional dependencies are useful for optional features, optional integrations, or library defaults where the application may provide an extra component but does not have to. Kora still resolves the
dependency by type and tag, but absence is allowed and the generated graph passes `null`.

In Java, optionality is expressed with the JSpecify annotation `org.jspecify.annotations.Nullable`. In Kotlin it is expressed by the nullable type itself - no annotation is needed.

Use this deliberately. A nullable dependency should mean "the component can operate without this collaborator", not "I am unsure whether the graph is correct". Business code that receives a nullable
dependency should branch explicitly and keep the degraded behavior easy to see.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import org.jspecify.annotations.Nullable;

    @Component
    public final class UserService {

        @Nullable
        private final AuditService auditService;

        public UserService(@Nullable AuditService auditService) { // ONE_NULLABLE
            this.auditService = auditService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(private val auditService: AuditService?) // ONE_NULLABLE
    ```

`Optional<T>` expresses the same idea with a container instead of `null`, and is handy when the value is passed straight into an API that already speaks `Optional`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        public UserService(Optional<AuditService> auditService) {
            // empty when nothing provides AuditService
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(private val auditService: Optional<AuditService>) {
        // empty when nothing provides AuditService
    }
    ```

#### `ValueOf` { #valueof }

Access to a component's current value.
`ValueOf<T>` is a handle to a component rather than the component itself. It lets a component read the current value when it needs it instead of capturing the instance once. This matters when the
dependency may be refreshed, for example after a configuration change: components that depend on `T` directly are recreated, while components that hold a `ValueOf<T>` are not.

In ordinary request-processing code you usually do not need `ValueOf<T>`. Prefer a direct dependency for simple service collaboration. Reach for `ValueOf<T>` when the lifecycle behavior matters:
configuration refresh, expensive components, or components that should not force their consumers to be recreated at the same time.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.ValueOf;

    @Component
    public final class OrderService {

        private final ValueOf<UserService> userService;

        public OrderService(ValueOf<UserService> userService) {
            this.userService = userService;
        }

        public void process(Order order) {
            this.userService.get().enrich(order);  //(1)!
        }
    }
    ```

    1. `get()` always returns the current instance, even after the component has been refreshed.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.ValueOf

    @Component
    class OrderService(private val userService: ValueOf<UserService>) {

        fun process(order: Order) {
            userService.get().enrich(order)  //(1)!
        }
    }
    ```

    1. `get()` always returns the current instance, even after the component has been refreshed.

Can also be `@Nullable` when the wrapped component is optional:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class OrderService {
        public OrderService(@Nullable ValueOf<AuditService> auditService) {
            // auditService may be null
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class OrderService(private val auditService: ValueOf<AuditService>?) {
        // auditService may be null
    }
    ```

#### `PromiseOf` { #promiseof }

Deferred access to a component that may not exist yet when the consumer is created.
`PromiseOf<T>` returns an `Optional<T>` and is resolved after graph initialization. Use it for the rare case where a component must reference something that is created later in the graph, typically to
break a dependency cycle that cannot be restructured.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.PromiseOf;

    @Component
    public final class MetricsReporter {

        private final PromiseOf<HttpServer> server;

        public MetricsReporter(PromiseOf<HttpServer> server) {
            this.server = server;
        }

        public void report() {
            this.server.get().ifPresent(s -> log(s.port()));  //(1)!
        }
    }
    ```

    1. `get()` returns an empty `Optional` until the referenced component has been initialized.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.PromiseOf

    @Component
    class MetricsReporter(private val server: PromiseOf<HttpServer>) {

        fun report() {
            server.get().ifPresent { log(it.port()) }  //(1)!
        }
    }
    ```

    1. `get()` returns an empty `Optional` until the referenced component has been initialized.

#### `All` { #all }

All matching implementations of a type.
`All<T>` models extension points. Instead of choosing one implementation, Kora injects every matching implementation. This is useful for handlers, validators, listeners, interceptors, exporters, or
any place where the application should compose several independent contributions.

`All<T>` is an `Iterable<T>`, so you iterate it directly rather than treating it as a list.

The important design point is that every element in `All<T>` is still a graph component. Kora validates each implementation, applies tags if requested, and wires the collection at compile time. That
keeps plugin-like composition type-safe and visible in the generated graph.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.All;

    @Component
    public final class NotificationService {

        private final All<Notifier> notifiers;

        public NotificationService(All<Notifier> notifiers) {
            this.notifiers = notifiers;
        }

        public void broadcast(String message) {
            for (var notifier : this.notifiers) {  //(1)!
                notifier.notifyUser(message);
            }
        }
    }
    ```

    1. `All<T>` extends `Iterable<T>`, so a for-each loop is the natural way to consume it.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.All

    @Component
    class NotificationService(private val notifiers: All<Notifier>) {

        fun broadcast(message: String) {
            notifiers.forEach { it.notifyUser(message) }  //(1)!
        }
    }
    ```

    1. `All<T>` extends `Iterable<T>`, so the standard iteration functions work on it.

Elements can also be wrapped:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(All<ValueOf<Notifier>> notifiers) {
            // Each notifier wrapped in ValueOf
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NotificationService(private val notifiers: All<ValueOf<Notifier>>) {
        // Each notifier wrapped in ValueOf
    }
    ```

!!! warning "An untagged `All<T>` collects only untagged components"

    Tag matching applies to `All<T>` exactly as it applies to a single dependency. If your implementations carry tags, request `@Tag(Tag.Any.class) All<T>` to collect all of them, or request the
    specific tag to collect one group. See [`@Tag.Any`](#tag-any) and [Tagged All](#tagged-all).

#### `TypeRef` { #typeref }

The concrete generic type a template was materialized for.
`TypeRef<T>` carries generic type information through type erasure. It is useful when a generic factory needs to know not just the raw class, but the full generic type requested by the graph. JSON
mappers, configuration extractors, serializers, and other generated infrastructure often need this kind of type token.

Most application services do not need to inject `TypeRef<T>` directly. Treat it as an infrastructure tool for code that creates or adapts components based on generic types. When you do use it, the type
parameter should describe the exact model shape the component is responsible for.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.TypeRef;

    @Module
    public interface ValidatorModule {
        default <T> Validator<List<T>> listValidator(Validator<T> validator, TypeRef<T> valueRef) {
            return new IterableValidator<>(validator);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.TypeRef

    @Module
    interface ValidatorModule {
        fun <T> listValidator(validator: Validator<T>, valueRef: TypeRef<T>): Validator<List<T>> =
            IterableValidator(validator)
    }
    ```

### Wrapper Type Contract { #wrapper-type-contract }

Wrapper types are Kora's way to express dependency behavior without changing the component being requested. `ValueOf<T>` says "give me a handle to this component", `PromiseOf<T>` says "give me a handle
that is resolved later", and `All<T>` says "give me all matching components". The wrapped `T` is still the business type; the wrapper changes how Kora resolves and exposes it.

This distinction keeps APIs readable. A constructor that takes `UserRepository` needs one repository. A constructor that takes `ValueOf<UserRepository>` needs controlled access to a repository. A
constructor that takes `All<Notifier>` needs a collection of notifier implementations. Those signatures document the graph relationship directly in code.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface ValueOf<T> {
        T get();

        <Q> ValueOf<Q> map(Function<T, Q> mapper);
    }

    public interface PromiseOf<T> {
        Optional<T> get();

        <Q> PromiseOf<Q> map(Function<T, Q> mapper);
    }

    public sealed interface All<T> extends Iterable<T> {
        // Token type extending Iterable
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface ValueOf<T> {
        fun get(): T

        fun <Q> map(mapper: Function<T, Q>): ValueOf<Q>
    }

    interface PromiseOf<T> {
        fun get(): Optional<T>

        fun <Q> map(mapper: Function<T, Q>): PromiseOf<Q>
    }

    sealed interface All<T> : Iterable<T> {
        // Token type extending Iterable
    }
    ```

There is also `Wrapped<T>`: a component declared as `Wrapped<T>` satisfies claims for `T`, which lets a module attach lifecycle handling to a third-party object without leaking the wrapper into
consumer signatures. `LifecycleWrapper<T>` is the ready-made implementation for exactly that.

### Dependency Resolution Rules { #dependency-resolution-rules }

Kora resolves dependencies in a predictable order. First it identifies the requested type shape, then applies tags and wrappers, then chooses the matching declaration. If the result is missing,
ambiguous, or cyclic, graph generation fails with a compile-time error.

This is why explicit component declarations matter. Adding a dependency to the build file is not enough to make every component in that library appear in the graph. The application must import the
right module, define the right component, or request the right tag. The generated graph is the final source of truth for what actually runs.

1. **Type Matching**: dependencies are matched by type; a component whose type is assignable to the claim type is a candidate
2. **Tag Filtering**: an untagged claim matches only untagged components, a tagged claim matches only that exact tag, and `Tag.Any` matches everything
3. **Default Preference**: candidates without `@DefaultComponent` win over `@DefaultComponent` ones
4. **Cycle Detection**: circular dependencies are detected at compile time
5. **Nullability**: `@Nullable` and `Optional<T>` mark optional dependencies and resolve to absence instead of failing
6. **Raw Types Rejected**: a claim on a raw generic type fails the build, because it makes resolution ambiguous

### Indirect Dependencies { #indirect-dependencies }

Use `ValueOf<T>` to avoid cascading component refreshes when dependencies get updated:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ServiceModule {
        default ServiceA serviceA() {
            return new ServiceA();
        }

        default ServiceB serviceB() {
            return new ServiceB();
        }

        default ServiceC serviceC(ServiceA serviceA, ValueOf<ServiceB> serviceB) {
            // ServiceC depends on ServiceA directly (refreshes cascade to ServiceC)
            // ServiceC depends on ServiceB indirectly via ValueOf<T> (prevents cascading refreshes)
            return new ServiceC(serviceA, serviceB);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ServiceModule {
        fun serviceA(): ServiceA = ServiceA()

        fun serviceB(): ServiceB = ServiceB()

        fun serviceC(serviceA: ServiceA, serviceB: ValueOf<ServiceB>): ServiceC {
            // ServiceC depends on ServiceA directly (refreshes cascade to ServiceC)
            // ServiceC depends on ServiceB indirectly via ValueOf<T> (prevents cascading refreshes)
            return ServiceC(serviceA, serviceB)
        }
    }
    ```

**Why `ValueOf<T>` matters:** every node in the generated graph records both its *create* dependencies and its *refresh* dependencies. A direct dependency appears in both lists, so refreshing the
dependency recreates the consumer. A `ValueOf<T>` dependency appears only in the create list, so the consumer keeps working with the same instance and simply reads the new value through `get()`.
Refreshes are triggered by the framework - for example by the configuration file watcher - not by application code.

---

## Tag System { #tag-system }

Tags allow multiple implementations of the same interface to coexist and be differentiated during dependency injection. Tags use class references instead of strings, which keeps renames safe and makes
usages findable in the IDE.

### Using Tags { #tags }

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Tag classes (usually empty marker classes)
    public final class RedisTag {
        private RedisTag() {}
    }

    public final class InMemoryTag {
        private InMemoryTag() {}
    }

    // Tagged implementations
    @Tag(RedisTag.class)
    @Component
    public final class RedisCache implements Cache {
        // Redis implementation
    }

    @Tag(InMemoryTag.class)
    @Component
    public final class InMemoryCache implements Cache {
        // In-memory implementation
    }

    // Selective injection
    @Component
    public final class UserService {
        public UserService(@Tag(RedisTag.class) Cache cache) {
            // Injects RedisCache specifically
        }
    }

    @Component
    public final class ProductService {
        public ProductService(@Tag(InMemoryTag.class) Cache cache) {
            // Injects InMemoryCache specifically
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Tag classes (usually empty marker classes)
    class RedisTag private constructor()

    class InMemoryTag private constructor()

    // Tagged implementations
    @Tag(RedisTag::class)
    @Component
    class RedisCache : Cache {
        // Redis implementation
    }

    @Tag(InMemoryTag::class)
    @Component
    class InMemoryCache : Cache {
        // In-memory implementation
    }

    // Selective injection
    @Component
    class UserService(@Tag(RedisTag::class) private val cache: Cache) {
        // Injects RedisCache specifically
    }

    @Component
    class ProductService(@Tag(InMemoryTag::class) private val cache: Cache) {
        // Injects InMemoryCache specifically
    }
    ```

### Class Tags { #class-tags }

Tags can be applied directly to component classes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(RedisTag.class)
    @Component
    public final class RedisCache implements Cache {
        // Implementation
    }

    @Tag(InMemoryTag.class)
    @Component
    public final class InMemoryCache implements Cache {
        // Implementation
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(RedisTag::class)
    @Component
    class RedisCache : Cache {
        // Implementation
    }

    @Tag(InMemoryTag::class)
    @Component
    class InMemoryCache : Cache {
        // Implementation
    }
    ```

### Method Tags { #method-tags }

Tags can be applied to factory methods:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface CacheModule {
        @Tag(RedisTag.class)
        default Cache redisCache() {
            return new RedisCache();
        }

        @Tag(InMemoryTag.class)
        default Cache inMemoryCache() {
            return new InMemoryCache();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface CacheModule {
        @Tag(RedisTag::class)
        fun redisCache(): Cache = RedisCache()

        @Tag(InMemoryTag::class)
        fun inMemoryCache(): Cache = InMemoryCache()
    }
    ```

### Annotation Tags { #annotation-tags }

Create reusable tag annotations by meta-annotating your own annotation with `@Tag`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(RedisTag.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
    public @interface RedisCache {}

    @Tag(InMemoryTag.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
    public @interface InMemoryCache {}

    // Usage
    @RedisCache
    @Component
    public final class RedisCacheImpl implements Cache {}

    @Component
    public final class UserService {
        public UserService(@RedisCache Cache cache) {
            // Injects RedisCacheImpl
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(RedisTag::class)
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.VALUE_PARAMETER)
    annotation class RedisCache

    @Tag(InMemoryTag::class)
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.VALUE_PARAMETER)
    annotation class InMemoryCache

    // Usage
    @RedisCache
    @Component
    class RedisCacheImpl : Cache

    @Component
    class UserService(@RedisCache private val cache: Cache) {
        // Injects RedisCacheImpl
    }
    ```

### Special Tags { #special-tags }

Special tag forms are useful when the default tag matching rules are too narrow. They let a component intentionally widen a request without losing type safety. This is most common with `All<T>`, where
you may want every implementation of an extension point, or every implementation that belongs to a specific tag group.

Use special tags sparingly. They are powerful because they change the meaning of a dependency request. A normal tag says "only this group"; `Tag.Any` says "ignore grouping"; a tagged `All<T>` says
"collect the whole group".

#### @Tag.Any { #tag-any }

Matches all components regardless of their tags.
`@Tag(Tag.Any.class)` is the broadest request. It is useful when the consumer is intentionally generic, for example a registry, diagnostics component, or dispatcher that should see both tagged and
untagged implementations. Without `Tag.Any`, an untagged dependency matches only untagged components.

Because it widens the graph edge, `Tag.Any` should be visible in the constructor signature and used only where this broad behavior is part of the design. If a service only needs Redis caches or only
email notifiers, request that specific tag instead.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(@Tag(Tag.Any.class) All<Notifier> notifiers) {
            // Receives ALL notifiers, both tagged and untagged
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NotificationService(@Tag(Tag.Any::class) private val notifiers: All<Notifier>) {
        // Receives ALL notifiers, both tagged and untagged
    }
    ```

#### Tagged All { #tagged-all }

Get all components with a specific tag.
This pattern collects all implementations that share a tag. It is useful when a subsystem has several implementations but they all belong to one named group, such as Redis-backed caches, public API
interceptors, internal health checks, or a specific tenant/provider group.

The tag keeps the collection focused. Components of the same Java or Kotlin type can exist elsewhere in the graph without being included. That makes `All<T>` practical in larger applications where the
same interface may be reused for several independent purposes.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CacheRegistry {
        public CacheRegistry(@Tag(RedisTag.class) All<Cache> caches) {
            // Receives all Cache implementations tagged with RedisTag
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CacheRegistry(@Tag(RedisTag::class) private val caches: All<Cache>) {
        // Receives all Cache implementations tagged with RedisTag
    }
    ```

### Tag Matching Rules { #tag-matching-rules }

Tag matching is exact by design. Kora treats the tag as part of the dependency identity, alongside the type. This prevents accidental injection of the wrong implementation when several components
share an interface but belong to different contexts.

When a dependency does not resolve, check both the type and the tag. A component with the right type but the wrong tag is not a match. The compiler helps here: the error message lists candidates of the
same type that carry a different tag.

1. **Untagged to Untagged**: a claim without a tag matches only components without a tag
2. **Exact Match**: a tagged claim matches only components carrying exactly that tag class
3. **`Tag.Any` Wins**: a claim tagged with `Tag.Any` matches every component of that type
4. **One Tag per Declaration**: `@Tag` carries a single class, so a component belongs to at most one tag group
5. **No Tag Inheritance**: matching compares the tag class itself, so a subclass tag does not match its parent

---

## Complete Example { #complete-example }

The pieces above come together in a small runnable application: two notifier implementations distinguished by tags, a formatter provided as an overridable default, an optional audit sink that is not
present in the graph, and a root service that collects every notifier.

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection;

    @FunctionalInterface
    public interface MessageFormatter {
        String format(String message);
    }

    public interface Notifier {
        String channel();

        String notifyUser(String message);
    }

    public interface AuditSink {
        void record(String channel, String message);
    }

    public final class EmailTag {
        private EmailTag() {}
    }

    public final class SmsTag {
        private SmsTag() {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection

    fun interface MessageFormatter {
        fun format(message: String): String
    }

    interface Notifier {
        fun channel(): String

        fun notifyUser(message: String): String
    }

    interface AuditSink {
        fun record(channel: String, message: String)
    }

    class EmailTag private constructor()

    class SmsTag private constructor()
    ```

Both notifiers are `@Component` classes, tagged so that they can be told apart:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;

    @Tag(EmailTag.class)
    @Component
    public final class EmailNotifier implements Notifier {

        private final MessageFormatter formatter;

        public EmailNotifier(MessageFormatter formatter) {
            this.formatter = formatter;
        }

        @Override
        public String channel() {
            return "email";
        }

        @Override
        public String notifyUser(String message) {
            return "EMAIL: " + formatter.format(message);
        }
    }

    @Tag(SmsTag.class)
    @Component
    public final class SmsNotifier implements Notifier {

        private final MessageFormatter formatter;

        public SmsNotifier(MessageFormatter formatter) {
            this.formatter = formatter;
        }

        @Override
        public String channel() {
            return "sms";
        }

        @Override
        public String notifyUser(String message) {
            return "SMS: " + formatter.format(message);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag

    @Tag(EmailTag::class)
    @Component
    class EmailNotifier(
        private val formatter: MessageFormatter
    ) : Notifier {

        override fun channel(): String = "email"

        override fun notifyUser(message: String): String = "EMAIL: ${formatter.format(message)}"
    }

    @Tag(SmsTag::class)
    @Component
    class SmsNotifier(
        private val formatter: MessageFormatter
    ) : Notifier {

        override fun channel(): String = "sms"

        override fun notifyUser(message: String): String = "SMS: ${formatter.format(message)}"
    }
    ```

The service is the graph root. It requests every notifier with `@Tag(Tag.Any.class)`, one specific notifier by tag, and an optional audit sink:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.All;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Root;
    import io.koraframework.common.annotation.Tag;
    import org.jspecify.annotations.Nullable;

    import java.util.ArrayList;
    import java.util.List;

    @Root
    @Component
    public final class NotificationService {

        private final All<Notifier> notifiers;
        private final Notifier emailNotifier;
        @Nullable
        private final AuditSink auditSink;

        public NotificationService(
                @Tag(Tag.Any.class) All<Notifier> notifiers,     //(1)!
                @Tag(EmailTag.class) Notifier emailNotifier,     //(2)!
                @Nullable AuditSink auditSink) {                 //(3)!
            this.notifiers = notifiers;
            this.emailNotifier = emailNotifier;
            this.auditSink = auditSink;
        }

        public List<String> broadcast(String message) {
            var result = new ArrayList<String>();
            for (var notifier : this.notifiers) {
                var output = notifier.notifyUser(message);
                result.add(output);
                if (this.auditSink != null) {
                    this.auditSink.record(notifier.channel(), output);
                }
            }
            return result;
        }

        public String notifyEmailOnly(String message) {
            var output = this.emailNotifier.notifyUser(message);
            if (this.auditSink != null) {
                this.auditSink.record(this.emailNotifier.channel(), output);
            }
            return output;
        }

        public boolean isAuditEnabled() {
            return this.auditSink != null;
        }
    }
    ```

    1. Both notifiers are tagged, so `Tag.Any` is required to collect them into one `All<Notifier>`.
    2. A tagged claim selects exactly one implementation.
    3. Nothing provides `AuditSink`, so the graph passes `null` instead of failing the build.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.All
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Root
    import io.koraframework.common.annotation.Tag

    @Root
    @Component
    class NotificationService(
        @Tag(Tag.Any::class) private val notifiers: All<Notifier>,   //(1)!
        @Tag(EmailTag::class) private val emailNotifier: Notifier,   //(2)!
        private val auditSink: AuditSink?                            //(3)!
    ) {

        fun broadcast(message: String): List<String> {
            return notifiers.map { notifier ->
                val output = notifier.notifyUser(message)
                auditSink?.record(notifier.channel(), output)
                output
            }
        }

        fun notifyEmailOnly(message: String): String {
            val output = emailNotifier.notifyUser(message)
            auditSink?.record(emailNotifier.channel(), output)
            return output
        }

        fun isAuditEnabled(): Boolean = auditSink != null
    }
    ```

    1. Both notifiers are tagged, so `Tag.Any` is required to collect them into one `All<Notifier>`.
    2. A tagged claim selects exactly one implementation.
    3. Nothing provides `AuditSink`, so the graph passes `null` instead of failing the build.

Finally, the application interface connects the framework modules, declares a nested module with an overridable default formatter, and overrides it:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.DefaultComponent;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.common.annotation.Module;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends HoconConfigModule, LogbackModule, NotificationModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);    //(1)!
        }

        default MessageFormatter messageFormatter() {       //(2)!
            return message -> "[app] " + message;
        }
    }

    @Module
    interface NotificationModule {

        @DefaultComponent
        default MessageFormatter defaultMessageFormatter() {
            return message -> "[default] " + message;
        }
    }
    ```

    1. `ApplicationGraph` is generated from the `Application` interface; `graph()` returns the graph description.
    2. This factory carries no `@DefaultComponent`, so it wins over `defaultMessageFormatter()`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.DefaultComponent
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.common.annotation.Module
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application : HoconConfigModule, LogbackModule, NotificationModule {

        fun messageFormatter(): MessageFormatter {          //(2)!
            return MessageFormatter { message -> "[app] $message" }
        }
    }

    @Module
    interface NotificationModule {

        @DefaultComponent
        fun defaultMessageFormatter(): MessageFormatter {
            return MessageFormatter { message -> "[default] $message" }
        }
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)         //(1)!
    }
    ```

    1. `ApplicationGraph` is generated from the `Application` interface; `graph()` returns the graph description.
    2. This factory carries no `@DefaultComponent`, so it wins over `defaultMessageFormatter()`.

The build wires the Kora BOM, the processor, and the two framework modules used above:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        implementation platform("io.koraframework:kora-bom:$koraVersion")
        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"

        testImplementation "io.koraframework:test-junit5"
        testAnnotationProcessor "io.koraframework:annotation-processors"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:$koraVersion"))
        ksp("io.koraframework:symbol-processors")

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")

        testImplementation("io.koraframework:test-junit5")
    }
    ```

### Testing the Graph { #testing-graph }

Because the graph is a compiled artifact, a test can start the real application graph and pull a component out of it. `@KoraAppTest` points at the `@KoraApp` interface, and `@TestComponent` injects a
component from the initialized graph:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;
    import org.junit.jupiter.api.Test;

    import static org.junit.jupiter.api.Assertions.*;

    @KoraAppTest(Application.class)
    class NotificationServiceTest {

        @TestComponent
        private NotificationService notificationService;

        @Test
        void broadcastShouldUseAllNotifiers() {
            var result = notificationService.broadcast("Hello");

            assertEquals(2, result.size());
            assertTrue(result.contains("EMAIL: [app] Hello"));
            assertTrue(result.contains("SMS: [app] Hello"));
        }

        @Test
        void notifyEmailOnlyShouldResolveTaggedNotifier() {
            assertEquals("EMAIL: [app] Ping", notificationService.notifyEmailOnly("Ping"));
        }

        @Test
        void optionalAuditDependencyShouldBeAbsent() {
            assertFalse(notificationService.isAuditEnabled());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent
    import org.junit.jupiter.api.Assertions.*
    import org.junit.jupiter.api.Test

    @KoraAppTest(Application::class)
    class NotificationServiceTest {

        @TestComponent
        lateinit var notificationService: NotificationService

        @Test
        fun broadcastUsesAllTaggedAndUntaggedNotifiers() {
            val result = notificationService.broadcast("hello")

            assertEquals(2, result.size)
            assertTrue(result.contains("EMAIL: [app] hello"))
            assertTrue(result.contains("SMS: [app] hello"))
        }

        @Test
        fun emailOnlyUsesTaggedComponent() {
            assertEquals("EMAIL: [app] hello", notificationService.notifyEmailOnly("hello"))
        }

        @Test
        fun optionalAuditSinkIsAbsent() {
            assertFalse(notificationService.isAuditEnabled())
        }
    }
    ```

The assertion `[app]` rather than `[default]` is the override rule from [`@DefaultComponent`](#defaultcomponent) verified end to end.

### What's Next { #whats-next }

Now that you understand the core concepts of Kora's dependency injection system, you're ready to put it all together. Continue with **[Building Kora DI Applications](dependency-injection.md)** for a
step-by-step tutorial that builds a complete notification system and demonstrates these concepts in a practical context.

The tutorial covers:

- Project setup and multi-module structure
- External library modules with defaults
- Component override and customization
- Tagged dependencies and collection injection
- Optional dependencies and graceful degradation
- Submodules and component organization
- Generic factories and type-safe creation
- Indirect dependencies with `ValueOf<T>`

---

## Best Practices { #best-practices }

### Keep Components Small and Focused { #components-focused }

Why this matters: small components are easier to test, understand, and reuse. Each component should have a single responsibility.

Beginner Tip: if your component is doing too many things, break it apart. Ask yourself: "What is this component's one job?"

Good Example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Single responsibility components
    @Component
    public final class OrderValidator {
        public ValidationResult validate(Order order) { /* validation logic */ }
    }

    @Component
    public final class OrderProcessor {
        private final PaymentService payment;
        private final OrderRepository repository;

        public OrderProcessor(PaymentService payment, OrderRepository repository) {
            this.payment = payment;
            this.repository = repository;
        }

        public void process(Order order) {
            // Just coordinates payment and storage
            payment.processPayment(order);
            repository.save(order);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Single responsibility components
    @Component
    class OrderValidator {
        fun validate(order: Order): ValidationResult { /* validation logic */ }
    }

    @Component
    class OrderProcessor(
        private val payment: PaymentService,
        private val repository: OrderRepository
    ) {
        fun process(order: Order) {
            // Just coordinates payment and storage
            payment.processPayment(order)
            repository.save(order)
        }
    }
    ```

### Prefer Constructor Injection { #prefer-constructor-injection }

Why this matters: constructor injection makes dependencies explicit and prevents partially constructed objects. It is the only injection style Kora supports for components, and it is the most testable
one.

Beginner Tip: always put dependencies in the constructor. Never look dependencies up inside methods - that is the service locator anti-pattern.

Good Example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {
        private final UserRepository repository;
        private final PasswordEncoder encoder;

        // All dependencies declared in constructor
        public UserService(UserRepository repository, PasswordEncoder encoder) {
            this.repository = repository;
            this.encoder = encoder;
        }

        public User createUser(String email, String password) {
            String hashedPassword = encoder.encode(password);
            User user = new User(email, hashedPassword);
            return repository.save(user);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(
        private val repository: UserRepository,
        private val encoder: PasswordEncoder
    ) {
        // All dependencies declared in the primary constructor

        fun createUser(email: String, password: String): User {
            val hashedPassword = encoder.encode(password)
            val user = User(email, hashedPassword)
            return repository.save(user)
        }
    }
    ```

### Handle Optional Dependencies Gracefully { #handle-optional-dependencies }

Why this matters: not all features are always available. Optional dependencies allow your application to work with different configurations.

Beginner Tip: in Java use JSpecify's `@Nullable`; in Kotlin use a nullable type. Always handle absence explicitly.

Good Example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import org.jspecify.annotations.Nullable;

    @Component
    public final class NotificationService {
        private final EmailService emailService;
        @Nullable
        private final SmsService smsService; // Might not be configured

        public NotificationService(EmailService emailService, @Nullable SmsService smsService) {
            this.emailService = emailService;
            this.smsService = smsService;
        }

        public void sendNotification(String message) {
            emailService.sendEmail(message); // Always available

            // Graceful handling of optional dependency
            if (smsService != null) {
                smsService.sendSms(message);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NotificationService(
        private val emailService: EmailService,
        private val smsService: SmsService? // Might not be configured
    ) {
        fun sendNotification(message: String) {
            emailService.sendEmail(message) // Always available

            // Graceful handling of optional dependency
            smsService?.sendSms(message)
        }
    }
    ```

### Use Tags for Multiple Implementations { #use-tags-implementations }

Why this matters: sometimes you need multiple implementations of the same interface (like different notification channels). Tags let you distinguish between them.

Beginner Tip: create dedicated marker classes for tags with descriptive names such as `EmailTag`, and give them a private constructor so nobody instantiates them by accident.

Good Example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Tag classes
    public final class EmailTag {
        private EmailTag() {}
    }

    public final class SmsTag {
        private SmsTag() {}
    }

    // Tagged implementations
    @Tag(EmailTag.class)
    @Component
    public final class EmailNotifier implements Notifier {
        @Override
        public void notifyUser(String message) { /* email logic */ }
    }

    @Tag(SmsTag.class)
    @Component
    public final class SmsNotifier implements Notifier {
        @Override
        public void notifyUser(String message) { /* SMS logic */ }
    }

    // Usage
    @Component
    public final class AlertService {
        private final Notifier emailNotifier;
        private final Notifier smsNotifier;

        public AlertService(
                @Tag(EmailTag.class) Notifier emailNotifier,
                @Tag(SmsTag.class) Notifier smsNotifier) {
            this.emailNotifier = emailNotifier;
            this.smsNotifier = smsNotifier;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Tag classes
    class EmailTag private constructor()

    class SmsTag private constructor()

    // Tagged implementations
    @Tag(EmailTag::class)
    @Component
    class EmailNotifier : Notifier {
        override fun notifyUser(message: String) { /* email logic */ }
    }

    @Tag(SmsTag::class)
    @Component
    class SmsNotifier : Notifier {
        override fun notifyUser(message: String) { /* SMS logic */ }
    }

    // Usage
    @Component
    class AlertService(
        @Tag(EmailTag::class) private val emailNotifier: Notifier,
        @Tag(SmsTag::class) private val smsNotifier: Notifier
    )
    ```

### Organize Components with Modules { #organize-with-modules }

Why this matters: modules group related components together, making your application easier to understand and maintain.

Beginner Tip: create modules for different layers (database, services, HTTP) or business domains (messaging, notifications, user management).

Good Example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Individual messenger modules for different channels
    @Module
    public interface SlackModule {

        @Tag(SlackTag.class)
        @DefaultComponent
        default Supplier<String> slackMessengerHeaderSupplier() {
            return () -> "ASCII_PROTOCOL_MESSENGER_SLACK";
        }
    }

    @Module
    public interface SignalModule {

        @Tag(SignalTag.class)
        @DefaultComponent
        default Supplier<String> signalMessengerHeaderSupplier() {
            return () -> "ASCII_PROTOCOL_MESSENGER_SIGNAL";
        }
    }

    @Component
    public final class SlackMessenger implements Messenger {

        private final Supplier<String> headerSupplier;

        public SlackMessenger(@Tag(SlackTag.class) Supplier<String> headerSupplier) {
            this.headerSupplier = headerSupplier;
        }

        @Override
        public void sendMessage(String message) {
            String header = headerSupplier.get();
            System.out.println(header + " ---> " + message);
        }
    }

    @Component
    public final class SignalMessenger implements Messenger {

        private final Supplier<String> headerSupplier;

        public SignalMessenger(@Tag(SignalTag.class) Supplier<String> headerSupplier) {
            this.headerSupplier = headerSupplier;
        }

        @Override
        public void sendMessage(String message) {
            String header = headerSupplier.get();
            System.out.println(header + " ---> " + message);
        }
    }

    // Application combines messenger modules
    @KoraApp
    public interface Application extends
        SlackModule,        // Slack messaging
        SignalModule {      // Signal messaging

        @Root
        default Dispatcher dispatcher(@Tag(Tag.Any.class) All<Messenger> messengers) {
            return new Dispatcher(messengers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Individual messenger modules for different channels
    @Module
    interface SlackModule {

        @Tag(SlackTag::class)
        @DefaultComponent
        fun slackMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SLACK" }
    }

    @Module
    interface SignalModule {

        @Tag(SignalTag::class)
        @DefaultComponent
        fun signalMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SIGNAL" }
    }

    @Component
    class SlackMessenger(
        @Tag(SlackTag::class) private val headerSupplier: Supplier<String>
    ) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    @Component
    class SignalMessenger(
        @Tag(SignalTag::class) private val headerSupplier: Supplier<String>
    ) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    // Application combines messenger modules
    @KoraApp
    interface Application :
        SlackModule,        // Slack messaging
        SignalModule {      // Signal messaging

        @Root
        fun dispatcher(@Tag(Tag.Any::class) messengers: All<Messenger>): Dispatcher =
            Dispatcher(messengers)
    }
    ```

### Avoid Common Anti-Patterns { #anti-patterns }

**Service Locator Pattern:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Don't do this
    @Component
    public final class BadService {
        public void doSomething() {
            // Looking dependencies up inside methods
            Database db = ServiceLocator.getDatabase(); // Anti-pattern
            db.save(data);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Don't do this
    @Component
    class BadService {
        fun doSomething() {
            // Looking dependencies up inside methods
            val db = ServiceLocator.getDatabase() // Anti-pattern
            db.save(data)
        }
    }
    ```

**Circular Dependencies:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Don't create circular dependencies
    @Component
    public final class ServiceA {
        public ServiceA(ServiceB b) {} // ServiceA depends on ServiceB
    }

    @Component
    public final class ServiceB {
        public ServiceB(ServiceA a) {} // ServiceB depends on ServiceA - CIRCULAR!
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Don't create circular dependencies
    @Component
    class ServiceA(private val b: ServiceB) // ServiceA depends on ServiceB

    @Component
    class ServiceB(private val a: ServiceA) // ServiceB depends on ServiceA - CIRCULAR!
    ```

Kora reports this at compile time. When a cycle is unavoidable, express one of the edges through an interface and let Kora generate a delegating proxy, or request the dependency as `PromiseOf<T>`.
Restructuring the responsibilities is almost always the better fix.

**Large Components:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Don't create "God objects"
    @Component
    public final class HugeService {
        // Does everything: validation, database, email, logging, caching...
        private final Validator validator;
        private final Repository repo;
        private final EmailService email;
        private final Logger logger;
        private final Cache cache;

        // Hundreds of methods...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Don't create "God objects"
    @Component
    class HugeService(
        // Does everything: validation, database, email, logging, caching...
        private val validator: Validator,
        private val repo: Repository,
        private val email: EmailService,
        private val logger: Logger,
        private val cache: Cache
    ) {
        // Hundreds of methods...
    }
    ```

**Summary of the rules worth keeping:**

- Prefer constructor injection and let Kora build the dependency graph at compile time
- Keep components focused on one responsibility so graph errors stay easy to understand
- Use modules for reusable factories and default components, not as a place to hide application logic
- Use tags only when the same contract has multiple meaningful implementations
- Mark entry points with `@Root`, and only entry points
- Avoid service locators, circular dependencies, and large components that mix unrelated responsibilities

## Summary { #summary }

You learned the core ideas behind Kora dependency injection:

- components declare what they need through constructors or factory methods
- Kora validates and generates the dependency graph at compile time, with no reflection at runtime
- resolution starts from `@Root`, so only what an entry point needs is built
- modules group reusable factories, and `@DefaultComponent` makes them replaceable
- tags disambiguate multiple implementations of the same type, and `All<T>` collects extension points
- `ValueOf<T>` and `PromiseOf<T>` express indirect access without changing the business type
- dependency injection keeps application structure explicit and testable

## Troubleshooting { #troubleshooting }

**`No component found for dependency`**

```
No component found for dependency:
  com.example.UserRepository (no tags)

Required at:
  com.example.Application#userService(com.example.UserRepository)
  parameter: com.example.UserRepository repository

Dependency resolution path:
  @--- factory  com.example.Application#orderService(...)
  ^--- factory  com.example.Application#userService(...)
  ^--- com.example.UserRepository   [MISSING]

Fix:
  - Add @Component to an implementation of com.example.UserRepository.
  - Add a module method that returns com.example.UserRepository.
  - Include a module that provides com.example.UserRepository in @KoraApp.
```

- Check that the class is annotated with `@Component` or returned from a module method
- Verify that the module providing it is connected to the `@KoraApp` interface
- Read the `Dependency resolution path` from the bottom: the `[MISSING]` line is the claim that failed, and the lines above it show who asked for it
- If the error notes components "with the same type but different tag", the tag on the claim or on the component is wrong

**`Multiple components match dependency`**

```
Multiple components match dependency:
  com.example.Cache (no tags)

  Candidates:
  - component  com.example.RedisCache
  - component  com.example.InMemoryCache

Fix:
  - Add different @Tag(...) annotations to candidates and request the needed tag.
  - Mark fallback candidate with @DefaultComponent.
  - Remove one duplicate provider.
```

- Add a tag to the claim and to the component that should satisfy it
- Or mark the fallback candidate with `@DefaultComponent` so the other one wins
- Or remove the duplicate provider

**`@KoraApp has no root components`**

- Annotate at least one component or module method with `@Root`
- If a framework module was supposed to contribute the root, check that the `@KoraApp` interface actually extends it

**`Circular dependency found`**

```
Circular dependency found:
  com.example.ServiceA (no tags)

  Dependency cycle:
    @--- component  com.example.ServiceA
    ^--- component  com.example.ServiceB [CYCLE]

Fix:
  - Break the cycle with ValueOf<T> or PromiseOf<T> where lazy access is valid.
  - Move shared state into a separate component.
  - Do not create dependency cycles in io.koraframework.application.graph.Lifecycle.
```

- Move the shared state into a third component that both sides depend on
- Express one edge through an interface so Kora can generate a delegating proxy for it
- As a last resort, request the dependency as `PromiseOf<T>` or `ValueOf<T>`

**`@Component class must have exactly one public constructor`**

- Keep one public constructor and make the extra ones non-public
- Or drop `@Component` and provide the class from a module method instead

**Generated graph does not compile**

- Fix the first reported error and compile again; later errors often depend on the first one
- Open the generated `<AppName>Graph` in `build/generated` when a wiring decision is unclear - it is ordinary source code

## What's Next? { #whats-next-2 }

- [Build a Complete DI Application](dependency-injection.md) to practice modules, components, factories, tags, lifecycle, and graph design without HTTP noise.
- [Create Your First Kora Application](getting-started.md) if you read this introduction first and now want to run a minimal app.
- [Configuration with HOCON](config-hocon.md) or [Configuration with YAML](config-yaml.md) after getting started, because configuration depends on having a runnable Kora app.

## Help { #help }

If you encounter issues:

- check the [Container documentation](../documentation/container.md)
- compare with the basic examples in [Kora Examples](home.md)
- review [Creating Your First Kora Application](getting-started.md) for a runnable graph
