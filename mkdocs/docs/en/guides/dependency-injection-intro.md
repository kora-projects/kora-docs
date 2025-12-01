---
title: Dependency Injection with Kora
summary: Learn the fundamentals of dependency injection using Kora's compile-time DI framework
tags: dependency-injection, di, kora-app, component, module, compile-time
---

# Dependency Injection with Kora

This guide introduces you to dependency injection (DI) concepts using the Kora framework. Learn how Kora's compile-time dependency injection provides superior performance, type safety, and developer experience compared to traditional runtime DI frameworks.

## What You'll Build

You'll learn the fundamental concepts of dependency injection and understand:

- **Core DI Concepts**: What dependency injection is and why it matters
- **Kora's Architecture**: How compile-time DI works and its advantages
- **Component Lifecycle**: How components are created, managed, and destroyed
- **Module System**: How to organize and structure your application components
- **Best Practices**: Patterns for writing maintainable, testable code

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Basic understanding of Java or Kotlin

## Prerequisites

!!! note "No Prerequisites Required"

    This guide is designed for beginners and doesn't require any prior knowledge of dependency injection or Kora. However, basic programming knowledge in Java or Kotlin will be helpful.

## Overview

This comprehensive guide teaches dependency injection (DI) concepts using the Kora framework. Kora implements **compile-time dependency injection**, which provides superior performance, type safety, and developer experience compared to runtime DI frameworks.

**Important Scope Note**: Kora DI components are only discovered within Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces. Components in regular modules without these annotations are not processed.

> **⚠️ External Dependencies**: Components from external libraries are also not automatically available. Even if a library JAR contains `@Component` classes, they must be explicitly imported by extending the library's module interfaces in your `@KoraApp` interface.

## Introduction to Dependency Injection
    - [What is Dependency Injection?](#what-is-dependency-injection)
    - [Problems with Traditional Approaches](#problems-with-traditional-approaches)
    - [Benefits of Dependency Injection](#benefits-of-dependency-injection)
    - [Understanding Inversion of Control (IoC)](#understanding-inversion-of-control-ioc)
    - [When Traditional Approaches Break Down](#when-traditional-approaches-break-down)
- [Dependency Injection with Kora](#dependency-injection-with-kora)
  - [What You'll Build](#what-youll-build)
  - [What You'll Need](#what-youll-need)
  - [Prerequisites](#prerequisites)
  - [Overview](#overview)
  - [Introduction to Dependency Injection](#introduction-to-dependency-injection)
  - [Introduction to Dependency Injection](#introduction-to-dependency-injection-1)
    - [What is Dependency Injection?](#what-is-dependency-injection)
    - [Problems with Traditional Approaches](#problems-with-traditional-approaches)
    - [Benefits of Dependency Injection](#benefits-of-dependency-injection)
    - [Understanding Inversion of Control (IoC)](#understanding-inversion-of-control-ioc)
    - [When Traditional Approaches Break Down](#when-traditional-approaches-break-down)
  - [Kora's Compile-Time DI Architecture](#koras-compile-time-di-architecture)
    - [How Kora DI Works](#how-kora-di-works)
    - [Generated Code Structure](#generated-code-structure)
    - [Compile-Time vs Runtime Processing](#compile-time-vs-runtime-processing)
    - [Annotation Processor Architecture](#annotation-processor-architecture)
    - [Component Discovery Order](#component-discovery-order)
    - [Dependency Resolution Algorithm](#dependency-resolution-algorithm)
  - [Core Annotations](#core-annotations)
    - [@KoraApp](#koraapp)
      - [Why Explicit Control Matters](#why-explicit-control-matters)
    - [@Component](#component)
    - [@Module](#module)
    - [@KoraSubmodule](#korasubmodule)
    - [@Root](#root)
    - [@DefaultComponent](#defaultcomponent)
    - [@Tag](#tag)
  - [Component Discovery Priority](#component-discovery-priority)
  - [Component Declaration](#component-declaration)
    - [Auto Factory (@Component)](#auto-factory-component)
    - [Basic Factory Methods](#basic-factory-methods)
    - [Module Factory](#module-factory)
    - [External Module Factory](#external-module-factory)
    - [Submodule Factory](#submodule-factory)
    - [Generic Factory](#generic-factory)
    - [Extension Mechanism](#extension-mechanism)
    - [Standard Factory (@DefaultComponent)](#standard-factory-defaultcomponent)
    - [Auto Creation](#auto-creation)
  - [Dependency Claims and Resolution](#dependency-claims-and-resolution)
    - [Basic Dependency Types](#basic-dependency-types)
      - [Required](#required)
      - [Nullable](#nullable)
      - [ValueOf](#valueof)
      - [All](#all)
      - [TypeRef](#typeref)
    - [Wrapper Types Contract](#wrapper-types-contract)
    - [Dependency Resolution Rules](#dependency-resolution-rules)
    - [Indirect Dependencies](#indirect-dependencies)
  - [Tags System](#tags-system)
    - [Basic Tag Usage](#basic-tag-usage)
    - [Tag Annotations on Classes](#tag-annotations-on-classes)
    - [Tag Annotations on Factory Methods](#tag-annotations-on-factory-methods)
    - [Custom Tag Annotations](#custom-tag-annotations)
    - [Special Tag Types](#special-tag-types)
      - [@Tag.Any](#tagany)
      - [Tag.All with Specific Tag](#tagall-with-specific-tag)
    - [Tag Matching Rules](#tag-matching-rules)
    - [Advanced Tag Patterns](#advanced-tag-patterns)
      - [Tag Hierarchies](#tag-hierarchies)
      - [Conditional Tagging](#conditional-tagging)
    - [Next Steps](#next-steps)
    - [Best Practices](#best-practices)
      - [Keep Components Small and Focused](#keep-components-small-and-focused)
      - [Use Constructor Injection](#use-constructor-injection)
      - [Handle Optional Dependencies Gracefully](#handle-optional-dependencies-gracefully)
      - [Use Tags for Multiple Implementations](#use-tags-for-multiple-implementations)
      - [Organize Components with Modules](#organize-components-with-modules)
      - [Avoid Common Anti-Patterns](#avoid-common-anti-patterns)
  - [What's Next?](#whats-next)
  - [Help](#help)

---

## Introduction to Dependency Injection

This guide provides a comprehensive introduction to dependency injection (DI) and inversion of control (IoC) principles using the Kora framework. Whether you're new to these concepts or looking to deepen your understanding, this section will systematically build your knowledge from fundamental principles to practical implementation.

### What is Dependency Injection?

**Dependency Injection** is a fundamental design pattern that addresses how software components acquire and manage their dependencies. At its core, DI is about separating the creation of dependencies from their usage, allowing for more flexible and maintainable code architecture.

**Core Concept**: Instead of a component creating its own dependencies, those dependencies are provided (injected) from an external source. This external source is typically a dependency injection framework or container.

**Basic Example**:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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

### Problems with Traditional Approaches

To understand the necessity of dependency injection, let's examine the challenges that arise without it and how DI provides solutions.

**The Problem: Tight Coupling**

Tight coupling occurs when components are directly dependent on specific implementations, making the system rigid and difficult to maintain. Consider this common pattern:

===! ":fontawesome-brands-java: Java"

    ```java
    public class UserService {
        private DatabaseConnection connection = new DatabaseConnection();  // Direct instantiation

        public User findUserById(long id) {
            return connection.query("SELECT * FROM users WHERE id = ?", id);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    class UserService {
        private val connection = DatabaseConnection()  // Direct instantiation

        fun findUserById(id: Long): User {
            return connection.query("SELECT * FROM users WHERE id = ?", id)
        }
    }
    ```

**Problems with Tight Coupling**:

1. **Testing Difficulties**: The `UserService` cannot be tested in isolation because it directly instantiates `DatabaseConnection`
2. **Implementation Lock-in**: Changing to a different database requires modifying the `UserService` code
3. **Hidden Dependencies**: The constructor reveals nothing about what the service actually needs
4. **Resource Management Issues**: Each instance creates its own database connection
5. **Configuration Problems**: No way to configure the database connection externally

### Benefits of Dependency Injection

**The Dependency Injection Solution**:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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

   ===! ":fontawesome-brands-java: Java"

       ```java
       @Test
       public void testUserService() {
           DatabaseConnection mockConnection = mock(DatabaseConnection.class);
           UserService service = new UserService(mockConnection);
           // Test the service logic without database dependencies
       }
       ```

   === ":simple-kotlin: Kotlin"

       ```kotlin
       @Test
       fun testUserService() {
           val mockConnection = mock(DatabaseConnection::class.java)
           val service = UserService(mockConnection)
           // Test the service logic without database dependencies
       }
       ```

2. **Flexibility**: Different implementations can be injected based on environment

   ===! ":fontawesome-brands-java: Java"

       ```java
       // Production environment
       DatabaseConnection prodConnection = new PostgreSQLConnection();
       UserService prodService = new UserService(prodConnection);

       // Test environment
       DatabaseConnection testConnection = new InMemoryDatabaseConnection();
       UserService testService = new UserService(testConnection);
       ```

   === ":simple-kotlin: Kotlin"

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

### Understanding Inversion of Control (IoC)

**Inversion of Control** is the architectural principle that underlies dependency injection. IoC represents a fundamental shift in how control flow is managed in software systems.

**Traditional Control Flow**:
```
Application Code â†’ Creates Objects â†’ Manages Dependencies â†’ Executes Business Logic
```

**Inverted Control Flow**:
```
Framework/Container â†’ Creates Objects â†’ Injects Dependencies â†’ Application Code Executes Business Logic
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

**IoC Implementation Patterns**:

1. **Factory Pattern**: Centralized object creation
2. **Service Locator**: Components request dependencies from a central registry
3. **Dependency Injection**: Dependencies are pushed into components

**Why IoC Matters**:

IoC enables several important architectural benefits:
- **Separation of Concerns**: Business logic is separated from infrastructure concerns
- **Modularity**: Components can be developed and tested independently
- **Maintainability**: Changes to infrastructure don't affect business logic
- **Testability**: Components can be easily isolated for testing
- **IoC**: Restaurant provides ready-made meals, you just eat

**In Code**:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Traditional approach - you control all object creation
    class Application {
        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                val db = Database()           // You create
                val email = EmailService() // You create
                val service = OrderService(db, email) // You create

                service.processOrder(order) // You control
            }
        }
    }
    ```

### When Traditional Approaches Break Down

While the traditional approach of manually creating and managing dependencies works perfectly well for small applications with just a few classes, it becomes increasingly problematic as your application grows to dozens or hundreds of components.

**Why Scale Matters:**

The traditional approach requires you to manually instantiate and wire together every object in your application. For a small app with 3-5 classes, this is straightforward. But when your application contains 20, 50, or 100+ classes, this manual approach becomes a maintenance nightmare.

**Example: A 20+ Class Application (Traditional Approach)**

Imagine building an application with the following components:

===! ":fontawesome-brands-java: Java"

    ```java
    public class EcommerceApplication {
        public static void main(String[] args) {
            // Infrastructure Layer (8 classes)
            DatabaseConfig dbConfig = new DatabaseConfig("localhost", "ecommerce", "user", "pass");
            DatabaseConnection dbConnection = new DatabaseConnection(dbConfig);
            RedisConfig redisConfig = new RedisConfig("localhost", 6379);
            RedisConnection redisConnection = new RedisConnection(redisConfig);
            EmailConfig emailConfig = new EmailConfig("smtp.gmail.com", 587, "user@gmail.com");
            EmailService emailService = new EmailService(emailConfig);
            PaymentGatewayConfig paymentConfig = new PaymentGatewayConfig("stripe_key_123");
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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    class EcommerceApplication {
        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                // Infrastructure Layer (8 classes)
                val dbConfig = DatabaseConfig("localhost", "ecommerce", "user", "pass")
                val dbConnection = DatabaseConnection(dbConfig)
                val redisConfig = RedisConfig("localhost", 6379)
                val redisConnection = RedisConnection(redisConfig)
                val emailConfig = EmailConfig("smtp.gmail.com", 587, "user@gmail.com")
                val emailService = EmailService(emailConfig)
                val paymentConfig = PaymentGatewayConfig("stripe_key_123")
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
        }
    }
    ```

**With 100+ Classes, This Becomes Impossible:**

- Your main method would be 1000+ lines long
- Understanding the dependency graph requires a separate diagram
- You must manually ensure components are created in the correct order
- Adding a new feature requires touching dozens of files
- A change to one component requires understanding its entire dependency chain
- Testing any component requires instantiating hundreds of objects and becomes nightmare
- A single configuration change cascades through the entire application
- Adding a new feature requires updating the main method, potentially breaking existing initialization order

**The Dependency Injection Solution:**

With DI, you declare dependencies at the component level, and the framework handles all the complexity:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface EcommerceApplication :
        InfrastructureModule, DataAccessModule, BusinessLogicModule, PresentationModule {

        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                KoraApplication.run(EcommerceApplicationGraph::graph)
            }
        }
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

===! ":fontawesome-brands-java: Java"

    ```java
    // IoC/DI (framework controls object creation)
    @KoraApp
    public interface Application {
        // Framework creates and injects everything
        OrderService orderService();

        static void main(String[] args) {
            // Framework handles all object creation and injection
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // IoC/DI (framework controls object creation)
    @KoraApp
    interface Application {
        // Framework creates and injects everything
        fun orderService(): OrderService

        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                // Framework handles all object creation and injection
                KoraApplication.run(ApplicationGraph::graph)
            }
        }
    }
    ```

**Benefits Comparison:**

| Aspect | Traditional | Dependency Injection |
|--------|-------------|---------------------|
| **Testing** | Hard (uses real services) | Easy (inject mocks) |
| **Flexibility** | Low (hardcoded dependencies) | High (inject any implementation) |
| **Reusability** | Low (tied to specific implementations) | High (works with any compatible service) |
| **Maintainability** | Low (changes affect multiple places) | High (change injection, not code) |
| **Clarity** | Low (dependencies hidden) | High (constructor shows needs) |

Now that you understand the fundamentals, let's explore how Kora implements these concepts with compile-time dependency injection!

---

## Kora's Compile-Time DI Architecture

Kora uses **compile-time dependency injection**, which means:

1. **Build-time Analysis**: Dependencies are analyzed during compilation using annotation processors
2. **Component Discovery**: Classes annotated with `@Component` and factory methods are found
3. **Dependency Resolution**: The annotation processor resolves all dependencies and builds a dependency graph
4. **Code Generation**: An `ApplicationGraphDraw` class is generated as Java/Kotlin source code
5. **Runtime Performance**: No reflection or runtime analysis overhead - everything is resolved at compile time

> **âš ï¸ Important Scope Limitation**: Kora's annotation processors only scan Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces. Components in regular Gradle modules without these interfaces will not be discovered or processed by the DI system.

### How Kora DI Works

1. **Annotation Processing**: `@KoraApp` interfaces are processed at compile time by `KoraAppProcessor`
2. **Component Discovery**: Scans for `@Component` classes, `@Module` interfaces, and factory methods within Gradle modules containing `@KoraApp` or `@KoraSubmodule` interfaces
3. **Dependency Resolution**: Uses `GraphBuilder` to resolve dependencies and detect cycles
4. **Graph Generation**: Generates `ApplicationGraph` class with component factories and initialization logic
5. **Runtime Execution**: `KoraApplication.run()` initializes components in correct order

> **âš ï¸ Critical Scope Limitation**: Kora's annotation processors only process Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces. Components in regular Gradle modules without these interfaces will be completely ignored by the DI system.

**Architectural Benefits of Explicit Control:**
This deliberate design choice gives you complete control over your application's dependency graph. Unlike frameworks that automatically instantiate everything on the classpath, Kora ensures you explicitly declare what components you want. This prevents:
- **Resource waste** from unwanted component instantiation
- **Security risks** from transitive dependency components being activated
- **Debugging complexity** from unknown running components
- **Performance overhead** from classpath scanning
- **Unpredictable behavior** when dependencies change

With Kora, your `@KoraApp` interface serves as an explicit manifest of everything running in your application.

### Generated Code Structure

When you annotate an interface with `@KoraApp`, Kora generates:

===! ":fontawesome-brands-java: Java"

    ```java
    // Generated at compile time
    public final class ApplicationGraph implements Application {
        public static ApplicationGraphDraw graph() {
            // Component initialization logic
            // Dependency resolution
            // Lifecycle management
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Generated at compile time
    class ApplicationGraph : Application {
        companion object {
            fun graph(): ApplicationGraphDraw {
                // Component initialization logic
                // Dependency resolution
                // Lifecycle management
            }
        }
    }
    ```

### Compile-Time vs Runtime Processing

**Compile Time (Annotation Processing):**
- Analyzes source code for components and dependencies within `@KoraApp`/`@KoraSubmodule` modules only
- Validates dependency graph (no cycles, all dependencies available)
- Generates optimized initialization code
- Provides compile-time error checking

**Runtime (Application Execution):**
- Executes generated initialization code
- Manages component lifecycle
- Handles graceful shutdown
- Supports component updates via `ValueOf<T>`

> **âš ï¸ Scope Critical**: Compile-time processing only occurs in Gradle modules containing `@KoraApp` or `@KoraSubmodule` interfaces. Code in regular modules is not analyzed or processed at compile time.

### Annotation Processor Architecture

Kora's annotation processing consists of:

1. **KoraAppProcessor**: Main processor handling `@KoraApp`, `@Module`, `@Component`
2. **GraphBuilder**: Builds dependency resolution graph and detects cycles
3. **ComponentDependencyHelper**: Parses dependency claims from method/constructor parameters
4. **Extensions**: Pluggable system for generating components dynamically
5. **ProcessingContext**: Provides access to compilation environment and utilities

> **âš ï¸ Scope Limitation**: Kora's annotation processors only activate and process code within Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces. Code in regular Gradle modules is completely invisible to these processors.

### Component Discovery Order

Components are discovered in this priority order (higher numbers override lower):

1. **Auto Creation**: Classes meeting requirements (final, single constructor, no abstract)
2. **Extension Mechanism**: Dynamic component generation (JSON mappers, repositories, etc.)
3. **Generic Factory**: Methods with generic parameters
4. **Standard Factory**: Methods with `@DefaultComponent`
5. **Basic Factory**: Regular factory methods
6. **Module Factory**: Methods in `@Module` interfaces
7. **External Module Factory**: Inherited from external dependencies
8. **Submodule Factory**: Generated from `@KoraSubmodule`
9. **Auto Factory**: Classes with `@Component` annotation

> **âš ï¸ Scope Note**: Component discovery only occurs within Gradle modules containing `@KoraApp` or `@KoraSubmodule` interfaces. Components in regular Gradle modules will not be discovered regardless of their annotations.

### Dependency Resolution Algorithm

1. **Claim Parsing**: Each dependency parameter is parsed into a `DependencyClaim`
2. **Component Matching**: Find components matching type and tags
3. **Cycle Detection**: Ensure no circular dependencies exist
4. **Graph Construction**: Build acyclic dependency graph
5. **Code Generation**: Generate initialization code in topological order

---

## Core Annotations

Kora provides several key annotations for dependency injection:

### @KoraApp

Marks the main application interface and serves as the core of Kora's dependency container. This annotation labels the interface within which factory methods for creating components and module dependencies are defined. There can be only one such interface within an application.

**What @KoraApp Does:**
- **Container Entry Point**: Defines the root of your application's dependency container
- **Component Registry**: Registers all factory methods and component accessors
- **Module Integration**: Connects external modules through interface inheritance
- **Application Bootstrap**: Provides the starting point for `KoraApplication.run()`

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application {
        // Factory methods and component accessors
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application {
        // Factory methods and component accessors
    }
    ```

**Requirements:**
- Must be an interface (not a class)
- Only one per application
- Can extend multiple module interfaces
- Must be in a Gradle module (not regular modules without @KoraSubmodule)

**Container Building Process:**
At compile time, Kora uses the `@KoraApp` interface to:
1. Discover all factory methods and component dependencies
2. Validate the dependency graph for cycles and missing components
3. Generate optimized initialization code
4. Create the `ApplicationGraph` class for runtime execution

**Why Interfaces? Multiple Inheritance and Factory Override Control**

Kora requires `@KoraApp` and all modules to be interfaces rather than classes for fundamental architectural reasons that enable powerful dependency injection capabilities.

**Why Interfaces? Multiple Inheritance and Factory Override Control**

Kora requires `@KoraApp` and all modules to be interfaces rather than classes for fundamental architectural reasons that enable powerful dependency injection capabilities.

**Multiple Inheritance**: Java interfaces support multiple inheritance, allowing your application to compose functionality from multiple modules:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface EcommerceApplication extends
        HttpModule,           // HTTP server capabilities
        DatabaseModule,       // Database connectivity
        CacheModule,          // Caching services
        MonitoringModule {    // Observability features

        // Your application-specific factories
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface EcommerceApplication :
        HttpModule,           // HTTP server capabilities
        DatabaseModule,       // Database connectivity
        CacheModule,          // Caching services
        MonitoringModule {    // Observability features

        // Your application-specific factories
    }
    ```

**Factory Method Override**: Interface default methods can be easily overridden, giving you complete control over dependency injection at the language level:

===! ":fontawesome-brands-java: Java"

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
    public interface Application extends CacheModule {
        @Override
        default Cache cache() {
            return new RedisCache(); // Override with Redis
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Library provides default implementation
    @Module
    interface CacheModule {
        @DefaultComponent
        fun cache(): Cache = InMemoryCache() // Default implementation
    }

    // Your application can override with custom implementation
    @KoraApp
    interface Application : CacheModule {
        override fun cache(): Cache = RedisCache() // Override with Redis
    }
    ```

**Component as Factory Method**: Components aren't limited to classes - they can also be defined as factory methods in interfaces, giving you declarative control over IoC:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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

**Why This Design Matters**:

1. **Intuitive Language-Level Control**: IoC behavior is controlled using familiar Java language constructs (interfaces, default methods) rather than complex XML/annotations
2. **Type-Safe Configuration**: Factory methods are checked at compile-time, preventing runtime configuration errors
3. **Easy Testing**: Factory methods can be overridden in tests to inject mocks without complex test frameworks
4. **Modular Composition**: Multiple inheritance allows clean separation of concerns across different modules
5. **Override Flexibility**: Change implementations by simply overriding methods, no framework-specific configuration needed

This interface-based approach makes dependency injection feel like a natural extension of the Java language, giving you powerful IoC capabilities while maintaining simplicity and type safety.

#### Why Explicit Control Matters

Kora's design philosophy prioritizes **explicit control over implicit magic**. Unlike traditional DI frameworks that automatically scan the classpath and instantiate everything they find, Kora requires you to explicitly declare what dependencies you want in your application.

**The Problem with Automatic Discovery:**
- **Unpredictable Behavior**: You never know what will be instantiated just by adding a JAR to your classpath
- **Hidden Dependencies**: Components can be created without your knowledge, consuming resources
- **Debugging Nightmares**: When something goes wrong, you have to figure out what unwanted components are running
- **Security Risks**: Malicious or vulnerable components might be instantiated automatically
- **Performance Issues**: Every JAR on the classpath gets scanned, even if not needed

**Kora's Explicit Approach:**

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
        ru.tinkoff.kora.http.HttpModule,    // ✅ Explicitly included
        ru.tinkoff.kora.database.DatabaseModule, // ✅ Explicitly included
        // ru.tinkoff.kora.cache.CacheModule,     // ❌ Commented out = not included
        com.example.MyCustomModule {         // ✅ Your custom module
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application :
        ru.tinkoff.kora.http.HttpModule,    // ✅ Explicitly included
        ru.tinkoff.kora.database.DatabaseModule, // ✅ Explicitly included
        // ru.tinkoff.kora.cache.CacheModule,     // ❌ Commented out = not included
        com.example.MyCustomModule        // ✅ Your custom module
    ```

**Benefits of Explicit Control:**
- **Predictable Dependencies**: You know exactly what's running in your application
- **Resource Efficiency**: Only instantiate what you actually need
- **Clear Dependency Graph**: Easy to understand and debug component relationships
- **Security by Design**: No surprise instantiations from transitive dependencies
- **Performance**: No classpath scanning overhead - everything is resolved at compile time
- **Maintainability**: Changes to dependencies are explicit and tracked in code

**Real-World Impact:**
With automatic frameworks, developers often spend hours debugging why their application is slow or consuming unexpected resources. With Kora, if a component isn't explicitly included in your `@KoraApp` interface, it simply doesn't exist in your application - no surprises, no hidden costs.

### @Component

Marks a class as a component (dependency) in the dependency container. All components in Kora are singletons - classes that have only one instance created throughout the application lifecycle. Components are injected only if they are root components (marked with `@Root`) or if they are required as dependencies by other components.

**What Components Are:**
- **Singleton Instances**: One instance per application lifecycle
- **Dependency Providers**: Can be injected into other components
- **Conditional Initialization**: Created only if required by other components or marked with `@Root`
- **Thread-Safe**: Same instance shared across all injection points

**Important Scope Limitation**: `@Component` classes can only be discovered and used within Gradle modules that contain either:
- A `@KoraApp` interface (main application module)
- A `@KoraSubmodule` interface (component discovery module)

Components in regular Gradle modules without these annotations will not be processed by Kora's annotation processor.

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class UserService {
        // Implementation
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class UserService {
        // Implementation
    }
    ```

**Requirements for Auto Factory:**
- Class must not be abstract
- Must have exactly one public constructor
- Must be `final` (unless it has AOP aspects)
- Constructor parameters become dependencies
- **Must be in a Gradle module with @KoraApp or @KoraSubmodule**

**Component Lifecycle:**
- **Discovery**: Found by annotation processor during compilation
- **Validation**: Dependencies checked at compile time
- **Creation**: Instance created at application startup if required (or marked with `@Root`)
- **Injection**: Same instance provided to all dependent components
- **Destruction**: Managed by container during shutdown

### @Module

Groups related component factories together and marks interfaces as modules to be injected into the dependency container at compile time. A module is an interface that contains factory methods for creating components. All factory methods within a module become available to the dependency container.

**What Modules Do:**
- **Factory Collection**: Group related component factories in one place
- **Code Organization**: Separate concerns across different modules
- **Reusability**: Modules can be shared across applications
- **Override Support**: Factory methods can be overridden in extending interfaces

**Scope**: `@Module` interfaces are processed within Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces. External modules from libraries are inherited through interface extension.

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface DatabaseModule {
        @Component
        default UserRepository userRepository(DataSource dataSource) {
            return new JdbcUserRepository(dataSource);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface DatabaseModule {
        @Component
        fun userRepository(dataSource: DataSource): UserRepository =
            JdbcUserRepository(dataSource)
    }
    ```

**Module Types:**
- **Internal Modules**: Defined in your project within `@KoraApp` modules
- **External Modules**: Provided by libraries (inherited via interface extension)
- **Submodules**: Generated from `@KoraSubmodule` interfaces

**Module Requirements:**
- Must be an interface (not a class)
- Factory methods must be `default` methods
- Must be in the same source directory as `@KoraApp` or `@KoraSubmodule`

**Factory Method Rules:**
- Must return a component (non-null value)
- Can take other components as parameters
- Parameters become dependencies
- Parameters mey be optional components (mark `@Nullable`)
- Methods are called in dependency order at runtime

> **âš ï¸ External Library Components**: Components and modules from external libraries are **not automatically discovered** by Kora's annotation processor. Even if a library contains `@Component` classes or `@Module` interfaces, they will be invisible to your application unless you explicitly extend their module interfaces in your `@KoraApp` interface. This is a deliberate design choice for explicit dependency management.

### @KoraSubmodule

Marks an interface for which to build a module for the current compilation module. It will contain all components marked with `@Module` and `@Component` annotations found in the source code. This annotation is particularly useful for multi-module Gradle applications where different modules contain different pieces of functionality, and the main `@KoraApp` application is built in a separate module.

**What @KoraSubmodule Does:**
- **Component Discovery**: Scans the current Gradle module for `@Module` and `@Component` annotations
- **Module Generation**: Creates an inheritor interface with all discovered modules and components
- **Multi-Module Support**: Enables component sharing across Gradle modules
- **Boundary Definition**: Defines where Kora's annotation processor scans for components
- **Build Optimization**: Enables Gradle's build caching and incremental compilation by isolating functionality into separate modules

**Scope**: `@KoraSubmodule` interfaces define the boundaries where Kora's annotation processor will scan for components. Components outside these boundaries are not processed.

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraSubmodule
    public interface ApplicationModules {
        // Generated factory methods for all discovered components
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraSubmodule
    interface ApplicationModules {
        // Generated factory methods for all discovered components
    }
    ```

**How It Works:**
1. **Discovery**: Finds all `@Module` interfaces and `@Component` classes in the current Gradle module
2. **Inheritance**: Generated interface inherits from all discovered `@Module` interfaces
3. **Factory Generation**: Creates default methods for all discovered `@Component` classes
4. **Integration**: Can be extended by `@KoraApp` to include components from other modules

**Use Cases:**
- **Multi-Module Projects**: Share components across Gradle modules
- **Library Development**: Expose components from a library module
- **Modular Architecture**: Separate concerns across different build modules
- **Component Organization**: Group related components by functionality
- **Large Single Applications**: Organize complex monolithic applications into isolated Gradle modules for better build performance and maintainability
- **Build Optimization**: Leverage Gradle's build caching context by separating functionality into independent modules that can be built and cached separately

### @Root

Marks components that should always be initialized with application startup, even if they are not dependencies of other components. Root components are guaranteed to be created and started when the application launches, regardless of whether anything injects them.

**What @Root Does:**
- **Guaranteed Initialization**: Component is always created at startup
- **Eager Loading**: Forces immediate instantiation (not lazy)
- **Lifecycle Management**: Component participates in application startup/shutdown
- **Entry Points**: Perfect for servers, consumers, schedulers, and background services

**Common Use Cases:**
- **HTTP Servers**: Web servers that need to start listening immediately
- **Message Consumers**: Kafka consumers, queue processors
- **Background Services**: Cache warmers, health checkers, schedulers

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application {
        @Root
        default HttpServer httpServer(UserController controller) {
            return new HttpServer(controller);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application {
        @Root
        fun httpServer(controller: UserController): HttpServer =
            HttpServer(controller)
    }
    ```

**@Root vs Regular Components:**
- **Regular Components**: Created only if required as dependencies by other components
- **@Root Components**: Always created at startup (guaranteed initialization)

**When to Use @Root:**
- Component provides a service that should always be running
- Component needs to start processing immediately (servers, consumers)
- Component performs critical initialization (database setup, cache warming)
- Component collects metrics or monitoring data

### @DefaultComponent

Marks factory methods that provide default implementations, which are intended to be overridden by users. If any component is found in the dependency container without this annotation, it will take precedence during injection over `@DefaultComponent` factories.

**What @DefaultComponent Does:**
- **Default Provision**: Provides fallback implementations for components
- **Override Support**: Allows users to replace defaults without modifying library code
- **Library-Friendly**: Enables libraries to provide sensible defaults
- **Priority System**: Lower priority than non-annotated factories

**Use Cases:**
- **Library Defaults**: Libraries provide default implementations that users can override
- **Configuration Options**: Different implementations based on environment
- **Extension Points**: Allow users to customize behavior without changing library code

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface CacheModule {
        @DefaultComponent
        default Cache defaultCache() {
            return new InMemoryCache();
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface CacheModule {
        @DefaultComponent
        fun defaultCache(): Cache = InMemoryCache()
    }
    ```

**Override Behavior:**

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends CacheModule {
        // This overrides the @DefaultComponent because it has no annotation
        @Override
        default Cache defaultCache() {
            return new RedisCache(); // User provides custom implementation
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application : CacheModule {
        // This overrides the @DefaultComponent because it has no annotation
        override fun defaultCache(): Cache = RedisCache() // User provides custom implementation
    }
    ```

**Priority Order:**
1. Non-annotated factories (highest priority - overrides defaults)
2. `@DefaultComponent` factories (lowest priority - can be overridden)
3. Other factory types in between

**Best Practices:**
- Use for library-provided defaults that users might want to customize
- Don't use for application-specific components
- Clearly document what defaults are available for override

### @Tag

Allows differentiation of multiple implementations of the same type and provides selective injection based on tags. Tags use class references instead of strings for better refactoring support and type safety. A component is registered with a specific tag and injected at points that request exactly the same tag.

**What Tags Do:**
- **Implementation Selection**: Choose specific implementations of interfaces
- **Multiple Instances**: Support multiple implementations of the same type
- **Type Safety**: Uses class references instead of strings
- **Refactoring Safe**: IDE can track tag usage across codebase

**Basic Usage:**

===! ":fontawesome-brands-java: Java"

    ```java
    // Tag classes (usually empty marker classes)
    public final class RedisTag {}
    public final class InMemoryTag {}

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Tag classes (usually empty marker classes)
    class RedisTag
    class InMemoryTag

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

**Tag Application:**
- **On Classes**: `@Tag(MyTag.class) @Component class MyClass`
- **On Factory Methods**: `@Tag(MyTag.class) default MyClass myClass()`
- **On Parameters**: `public MyClass(@Tag(MyTag.class) Dependency dep)`

**Special Tags:**
- `@Tag.Any`: Matches all components regardless of their tags
- Custom tag annotations can be created for convenience

**Tag Matching Rules:**
1. **Exact Match**: Tags must match exactly by class reference
2. **Inheritance**: Tag classes can be part of inheritance hierarchies
3. **Multiple Tags**: Components can have multiple tags
4. **Tag Filtering**: Dependencies can specify required tags

**Custom Tag Annotations:**

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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

---

## Component Discovery Priority

When Kora needs to create a component, it follows a specific priority order to determine which factory method or mechanism to use. Higher priority factories override lower priority ones. Understanding this order is crucial for debugging dependency resolution issues and ensuring the correct implementations are used.

**Priority Order (Highest to Lowest):**

1. **Auto Creation**: Classes meeting component requirements (final, single constructor, no abstract)
2. **Extension Mechanism**: Dynamic component generation (JSON mappers, repositories, etc.)
3. **Generic Factory**: Methods with generic type parameters
4. **Standard Factory**: Methods with `@DefaultComponent`
5. **Basic Factory**: Regular factory methods
6. **Module Factory**: Methods in `@Module` interfaces
7. **External Module Factory**: Inherited from external dependencies
8. **Submodule Factory**: Generated from `@KoraSubmodule`
9. **Auto Factory**: Classes with `@Component` annotation

**What This Means:**
- If you have both a `@Component` class and a factory method for the same type, the factory method takes precedence
- `@DefaultComponent` factories can be overridden by regular factory methods
- Extensions can provide components dynamically (like JSON readers/writers)
- Auto creation works as a fallback for simple classes

**Practical Example:**

===! ":fontawesome-brands-java: Java"

    ```java
    // Priority 9: Auto Factory (@Component) - lowest priority
    @Component
    public final class DefaultUserService implements UserService { }

    // Priority 5: Basic Factory - higher priority, overrides @Component
    @KoraApp
    public interface Application {
        default UserService userService() {
            return new CustomUserService(); // This will be used instead
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Priority 9: Auto Factory (@Component) - lowest priority
    @Component
    class DefaultUserService : UserService

    // Priority 5: Basic Factory - higher priority, overrides @Component
    @KoraApp
    interface Application {
        fun userService(): UserService = CustomUserService() // This will be used instead
    }
    ```

---

## Component Declaration

Components in Kora can be declared in multiple ways, each with different priorities and use cases. **All component declaration methods require the code to be within Gradle modules that contain `@KoraApp` or `@KoraSubmodule` interfaces** - Kora's annotation processor only scans these designated modules.

### Auto Factory (@Component)

Classes annotated with `@Component` are automatically registered if they meet the requirements:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class UserService {
        private final UserRepository repository;

        public UserService(UserRepository repository) {
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class UserService(
        private val repository: UserRepository
    )
    ```

**Requirements:**
- Not abstract
- Exactly one public constructor
- Final class (unless AOP aspects applied)
- Constructor parameters become dependencies

### Basic Factory Methods

Default methods in `@KoraApp` or `@Module` interfaces that return components:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application {
        fun userService(repository: UserRepository): UserService =
            UserService(repository)

        fun userRepository(): UserRepository =
            InMemoryUserRepository()
    }
    ```

### Module Factory

Factory methods within `@Module` interfaces:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface DatabaseModule {
        fun dataSource(): DataSource =
            HikariDataSource()

        fun userRepository(dataSource: DataSource): UserRepository =
            JdbcUserRepository(dataSource)
    }
    ```

### External Module Factory

Modules from external dependencies, inherited through interface extension:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
        ru.tinkoff.kora.http.HttpModule,
        ru.tinkoff.kora.json.JsonModule {
        // Inherits all factory methods from external modules
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application :
        ru.tinkoff.kora.http.HttpModule,
        ru.tinkoff.kora.json.JsonModule {
        // Inherits all factory methods from external modules
    }
    ```

> **âš ï¸ Explicit Import Required**: External library components are not automatically available. You must explicitly extend the library's module interfaces in your `@KoraApp` interface. Simply adding a library to your classpath is not enough - the module interface extension makes the components available for dependency injection.

**This explicit approach prevents the common problems of automatic frameworks:**
- No surprise instantiation of unwanted components
- Clear visibility into what dependencies are actually used
- Better security through intentional inclusion
- Easier debugging and maintenance

### Submodule Factory

Generated modules from `@KoraSubmodule` interfaces:

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface PersistenceModule {
        default UserRepository userRepository() {
            return new InMemoryUserRepository();
        }
    }

    @KoraSubmodule
    public interface ApplicationSubmodule {
        // Generates factory methods for all @Module and @Component in the project
    }

    @KoraApp
    public interface Application extends ApplicationSubmodule {
        // All components from submodules are available
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface PersistenceModule {
        fun userRepository(): UserRepository =
            InMemoryUserRepository()
    }

    @KoraSubmodule
    interface ApplicationSubmodule {
        // Generates factory methods for all @Module and @Component in the project
    }

    @KoraApp
    interface Application : ApplicationSubmodule {
        // All components from submodules are available
    }
    ```

### Generic Factory

Methods with generic type parameters that can create components of any matching type. Generic factories are particularly useful for creating type-safe components that work with different generic types.

===! ":fontawesome-brands-java: Java"

    ```java
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

=== ":simple-kotlin: Kotlin"

    ```kotlin
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
- `TypeRef<T>` provides runtime type information for generic operations
- Can create `Validator<List<String>>`, `Validator<Set<User>>`, etc.
- Enables type-safe validation of generic collections

### Extension Mechanism

Components generated dynamically by extensions (JSON mappers, repositories, etc.):

```java
// Extensions automatically generate components for:
- JSON readers/writers for classes
- Database repositories from interfaces
- HTTP clients from interfaces
- And many more...
```

### Standard Factory (@DefaultComponent)

Default implementations that can be overridden:

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface CacheModule {
        @DefaultComponent
        default Cache cache() {
            return new InMemoryCache();
        }
    }

    // Can be overridden in application:
    @KoraApp
    public interface Application extends CacheModule {

        default Cache primaryCache() {
            return new RedisCache(); // Overrides the default
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface CacheModule {
        @DefaultComponent
        fun cache(): Cache = InMemoryCache()
    }

    // Can be overridden in application:
    @KoraApp
    interface Application : CacheModule {

        fun primaryCache(): Cache = RedisCache() // Overrides the default
    }
    ```

### Auto Creation

Classes that meet component requirements but aren't explicitly annotated:

===! ":fontawesome-brands-java: Java"

    ```java
    public final class SomeService {
        public SomeService(Dependency dep) {
            // Will be auto-created if needed and meets requirements
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    class SomeService(private val dep: Dependency) {
        // Will be auto-created if needed and meets requirements
    }
    ```

**Priority Order** (highest to lowest):

1. Auto Creation
2. Extension Mechanism
3. Generic Factory
4. Standard Factory (@DefaultComponent)
5. Basic Factory
6. Module Factory
7. External Module Factory
8. Submodule Factory
9. Auto Factory (@Component)

## Dependency Claims and Resolution

Kora uses a sophisticated dependency resolution system based on "claims". Each dependency parameter is parsed into a `DependencyClaim` that specifies how the dependency should be resolved.

### Basic Dependency Types

#### Required

Single required dependency that must exist:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class UserService {
        public UserService(UserRepository repository) { // ONE_REQUIRED
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class UserService(private val repository: UserRepository) // ONE_REQUIRED
    ```

#### Nullable

Single optional dependency that may be null:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class UserService {
        public UserService(@Nullable AuditService auditService) { // ONE_NULLABLE
            this.auditService = auditService;
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class UserService(@Nullable private val auditService: AuditService?) // ONE_NULLABLE
    ```

#### ValueOf

Synchronous access to a component's current value:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class OrderService {
        public OrderService(ValueOf<UserService> userService) {
            // Can call userService.get() to get current value
            // Can call userService.refresh() to get updated value
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class OrderService(private val userService: ValueOf<UserService>) {
        // Can call userService.get() to get current value
        // Can call userService.refresh() to get updated value
    }
    ```

Can be also `@Nullable` synchronous access:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class OrderService {
        public OrderService(@Nullable ValueOf<AuditService> auditService) {
            // auditService may be null
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class OrderService(@Nullable private val auditService: ValueOf<AuditService>?) {
        // auditService may be null
    }
    ```

#### All

All implementations of a type as individual dependencies:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(All<Notifier> notifiers) {
            // Receives all Notifier implementations
            // Each notifier is a separate dependency
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class NotificationService(private val notifiers: All<Notifier>) {
        // Receives all Notifier implementations
        // Each notifier is a separate dependency
    }
    ```

Can also be implementation wrapped in ValueOf:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(All<ValueOf<Notifier>> notifiers) {
            // Each notifier wrapped in ValueOf
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class NotificationService(private val notifiers: All<ValueOf<Notifier>>) {
        // Each notifier wrapped in ValueOf
    }
    ```

#### TypeRef

Reference to a type for reflection or generic operations:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class JsonMapper {
        public JsonMapper(TypeRef<User> userType) {
            // Used for generic type information
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class JsonMapper(private val userType: TypeRef<User>) {
        // Used for generic type information
    }
    ```

### Wrapper Types Contract

===! ":fontawesome-brands-java: Java"

    ```java
    public interface ValueOf<T> {
        T get();
        void refresh();
    }

    public interface All<T> extends List<T> {
        // Token type extending List
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    interface ValueOf<T> {
        fun get(): T
        fun refresh()
    }

    interface All<T> : List<T> {
        // Token type extending List
    }
    ```

### Dependency Resolution Rules

1. **Type Matching**: Dependencies are matched by type and tags
2. **Tag Filtering**: `@Tag` annotations narrow the search
3. **Priority Order**: Higher priority factories override lower ones
4. **Cycle Detection**: Circular dependencies are detected at compile time
5. **Nullability**: `@Nullable` marks optional dependencies

### Indirect Dependencies
Use `ValueOf<T>` to avoid cascading component refreshes when dependencies get updated:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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

**Why ValueOf<T> is required:** When a component is refreshed, all components that directly depend on it are also refreshed. `ValueOf<T>` creates an indirect dependency that prevents this cascading refresh behavior, allowing components to access updated values without being refreshed themselves.

---

## Tags System

Tags allow multiple implementations of the same interface to coexist and be differentiated during dependency injection. Tags use class references instead of strings for better refactoring support.

### Basic Tag Usage

===! ":fontawesome-brands-java: Java"

    ```java
    // Tag classes (usually empty marker classes)
    public final class RedisTag {}
    public final class InMemoryTag {}

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Tag classes (usually empty marker classes)
    class RedisTag
    class InMemoryTag

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

### Tag Annotations on Classes

Tags can be applied directly to component classes:

===! ":fontawesome-brands-java: Java"

    ```java
    @Tag(RedisTag.class)
    public final class RedisCache implements Cache {
        // Implementation
    }

    @Tag(InMemoryTag.class)
    public final class InMemoryCache implements Cache {
        // Implementation
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Tag(RedisTag::class)
    class RedisCache : Cache {
        // Implementation
    }

    @Tag(InMemoryTag::class)
    class InMemoryCache : Cache {
        // Implementation
    }
    ```

### Tag Annotations on Factory Methods

Tags can be applied to factory methods:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface CacheModule {
        @Tag(RedisTag::class)
        fun redisCache(): Cache = RedisCache()

        @Tag(InMemoryTag::class)
        fun inMemoryCache(): Cache = InMemoryCache()
    }
    ```

### Custom Tag Annotations

Create reusable tag annotations:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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

### Special Tag Types

#### @Tag.Any

Matches all components regardless of their tags:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(@Tag(Tag.Any.class) All<Notifier> notifiers) {
            // Receives ALL notifiers, both tagged and untagged
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class NotificationService(@Tag(Tag.Any::class) private val notifiers: All<Notifier>) {
        // Receives ALL notifiers, both tagged and untagged
    }
    ```

#### Tag.All with Specific Tag

Get all components with a specific tag:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(@Tag(RedisTag.class) All<Cache> caches) {
            // Receives all Cache implementations tagged with RedisTag
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class NotificationService(@Tag(RedisTag::class) private val caches: All<Cache>) {
        // Receives all Cache implementations tagged with RedisTag
    }
    ```

### Tag Matching Rules

1. **Exact Match**: Tags must match exactly by class reference
2. **Inheritance**: Tag classes can be part of inheritance hierarchies
3. **Multiple Tags**: Components can have multiple tags
4. **Tag Filtering**: Dependencies can specify required tags

### Advanced Tag Patterns

#### Tag Hierarchies

===! ":fontawesome-brands-java: Java"

    ```java
    public interface CacheTag {}
    public final class RedisTag implements CacheTag {}
    public final class InMemoryTag implements CacheTag {}

    @Tag(RedisTag.class)
    @Component
    public final class RedisCache implements Cache {}

    @Tag(InMemoryTag.class)
    @Component
    public final class InMemoryCache implements Cache {}

    @Component
    public final class CacheManager {
        public CacheManager(@Tag(CacheTag.class) All<Cache> caches) {
            // Receives all caches (both Redis and InMemory)
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    interface CacheTag
    class RedisTag : CacheTag
    class InMemoryTag : CacheTag

    @Tag(RedisTag::class)
    @Component
    class RedisCache : Cache

    @Tag(InMemoryTag::class)
    @Component
    class InMemoryCache : Cache

    @Component
    class CacheManager(@Tag(CacheTag::class) private val caches: All<Cache>) {
        // Receives all caches (both Redis and InMemory)
    }
    ```

#### Conditional Tagging

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface CacheModule {
        default Cache cache() {
            if (isProduction()) {
                return redisCache();
            } else {
                return inMemoryCache();
            }
        }

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface CacheModule {
        fun cache(): Cache = if (isProduction()) redisCache() else inMemoryCache()

        @Tag(RedisTag::class)
        fun redisCache(): Cache = RedisCache()

        @Tag(InMemoryTag::class)
        fun inMemoryCache(): Cache = InMemoryCache()
    }
    ```

### Next Steps

Now that you understand the core concepts of Kora's dependency injection system, you're ready to put it all together! Check out the companion guide **[BUILDING-KORA-DI-APPLICATIONS.md](BUILDING-KORA-DI-APPLICATIONS.md)** for a comprehensive step-by-step tutorial that builds a complete notification system application, demonstrating all the concepts you've learned here in a practical, real-world context.

The tutorial covers:
- Project setup and multi-module structure
- External library modules with defaults
- Component override and customization
- Tagged dependencies and collection injection
- Optional dependencies and graceful degradation
- Submodules and component organization
- Generic factories and type-safe creation
- Lazy loading with `ValueOf<T>` for performance optimization

### Best Practices

#### Keep Components Small and Focused

**Why this matters**: Small components are easier to test, understand, and reuse. Each component should have a single responsibility.

**Beginner Tip**: If your component is doing too many things, break it apart. Ask yourself: "What is this component's one job?"

**Good Example**:

===! ":fontawesome-brands-java: Java"

    ```java
    // ✅ Single responsibility components
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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // ✅ Single responsibility components
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

#### Use Constructor Injection

**Why this matters**: Constructor injection makes dependencies explicit and prevents partially constructed objects. It's the safest and most testable injection method.

**Beginner Tip**: Always put dependencies in the constructor. Never create dependencies inside methods (that's "service locator" anti-pattern).

**Good Example**:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class UserService {
        private final UserRepository repository;
        private final PasswordEncoder encoder;

        // ✅ All dependencies declared in constructor
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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class UserService(
        private val repository: UserRepository,
        private val encoder: PasswordEncoder
    ) {
        // ✅ All dependencies declared in constructor

        fun createUser(email: String, password: String): User {
            val hashedPassword = encoder.encode(password)
            val user = User(email, hashedPassword)
            return repository.save(user)
        }
    }
    ```

#### Handle Optional Dependencies Gracefully

**Why this matters**: Not all features are always available. Optional dependencies allow your application to work with different configurations.

**Beginner Tip**: Use `@Nullable` when a dependency might not be present. Always check for null before using.

**Good Example**:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class NotificationService {
        private final EmailService emailService;
        private final SmsService smsService; // Might not be configured

        public NotificationService(EmailService emailService, @Nullable SmsService smsService) {
            this.emailService = emailService;
            this.smsService = smsService;
        }

        public void sendNotification(String message) {
            emailService.sendEmail(message); // Always available

            // ✅ Graceful handling of optional dependency
            if (smsService != null) {
                smsService.sendSms(message);
            }
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class NotificationService(
        private val emailService: EmailService,
        @Nullable private val smsService: SmsService? // Might not be configured
    ) {
        fun sendNotification(message: String) {
            emailService.sendEmail(message) // Always available

            // ✅ Graceful handling of optional dependency
            smsService?.sendSms(message)
        }
    }
    ```

#### Use Tags for Multiple Implementations

**Why this matters**: Sometimes you need multiple implementations of the same interface (like different notification channels). Tags help you distinguish between them.

**Beginner Tip**: Create empty marker classes for tags. Use descriptive names like `EmailNotification.class`, not generic names.

**Good Example**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Tag classes
    public final class EmailTag {}
    public final class SmsTag {}

    // Tagged implementations
    @Tag(EmailTag.class)
    @Component
    public final class EmailNotifier implements Notifier {
        public void notify(String message) { /* email logic */ }
    }

    @Tag(SmsTag.class)
    @Component
    public final class SmsNotifier implements Notifier {
        public void notify(String message) { /* SMS logic */ }
    }

    // Usage
    @Component
    public final class AlertService {
        private final Notifier emailNotifier;
        private final Notifier smsNotifier;

        public AlertService(
            @Tag(EmailTag.class) Notifier emailNotifier,
            @Tag(SmsTag.class) Notifier smsNotifier
        ) {
            this.emailNotifier = emailNotifier;
            this.smsNotifier = smsNotifier;
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Tag classes
    class EmailTag
    class SmsTag

    // Tagged implementations
    @Tag(EmailTag::class)
    @Component
    class EmailNotifier : Notifier {
        override fun notify(message: String) { /* email logic */ }
    }

    @Tag(SmsTag::class)
    @Component
    class SmsNotifier : Notifier {
        override fun notify(message: String) { /* SMS logic */ }
    }

    // Usage
    @Component
    class AlertService(
        @Tag(EmailTag::class) private val emailNotifier: Notifier,
        @Tag(SmsTag::class) private val smsNotifier: Notifier
    )
    ```

#### Organize Components with Modules

**Why this matters**: Modules group related components together, making your application easier to understand and maintain.

**Beginner Tip**: Create modules for different layers (database, services, HTTP) or business domains (messaging, notifications, user management).

**Good Example**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Individual messenger modules for different channels
    @Module
    public interface SlackModule {

        @Tag(SlackMessenger.class)
        @DefaultComponent
        default Supplier<String> slackMessengerHeaderSupplier() {
            return () -> "ASCII_PROTOCOL_MESSENGER_SLACK";
        }
    }

    @Module
    public interface SignalModule {

        @Tag(SignalMessenger.class)
        @DefaultComponent
        default Supplier<String> signalMessengerHeaderSupplier() {
            return () -> "ASCII_PROTOCOL_MESSENGER_SIGNAL";
        }
    }

    @Component
    public final class SlackMessenger implements Messenger {

        private final Supplier<String> headerSupplier;

        public SlackMessenger(@Tag(SlackMessenger.class) Supplier<String> headerSupplier) {
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

        public SignalMessenger(@Tag(SignalMessenger.class) Supplier<String> headerSupplier) {
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
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Individual messenger modules for different channels
    @Module
    interface SlackModule {

        @Tag(SlackMessenger::class)
        @DefaultComponent
        fun slackMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SLACK" }
    }

    @Module
    interface SignalModule {

        @Tag(SignalMessenger::class)
        @DefaultComponent
        fun signalMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SIGNAL" }
    }

    @Component
    class SlackMessenger(
        @Tag(SlackMessenger::class) private val headerSupplier: Supplier<String>
    ) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    @Component
    class SignalMessenger(
        @Tag(SignalMessenger::class) private val headerSupplier: Supplier<String>
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
        SignalModule        // Signal messaging
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Individual messenger modules for different channels
    @Module
    interface SlackModule {

        @Tag(SlackMessenger::class)
        @DefaultComponent
        fun slackMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SLACK" }
    }

    @Module
    interface SignalModule {

        @Tag(SignalMessenger::class)
        @DefaultComponent
        fun signalMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SIGNAL" }
    }

    @Component
    class SlackMessenger(@Tag(SlackMessenger::class) private val headerSupplier: Supplier<String>) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    @Component
    class SignalMessenger(@Tag(SignalMessenger::class) private val headerSupplier: Supplier<String>) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    // Application combines messenger modules
    @KoraApp
    interface Application :
        SlackModule,        // Slack messaging
        SignalModule        // Signal messaging
    ```

#### Avoid Common Anti-Patterns

**❌ Service Locator Pattern**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Don't do this
    @Component
    public final class BadService {
        public void doSomething() {
            // Creating dependencies inside methods
            Database db = ServiceLocator.getDatabase(); // ❌ Anti-pattern
            db.save(data);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Don't do this
    @Component
    class BadService {
        fun doSomething() {
            // Creating dependencies inside methods
            val db = ServiceLocator.getDatabase() // ❌ Anti-pattern
            db.save(data)
        }
    }
    ```

**❌ Circular Dependencies**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Don't create circular dependencies
    @Component
    class ServiceA {
        ServiceA(ServiceB b) {} // ServiceA depends on ServiceB
    }

    @Component
    class ServiceB {
        ServiceB(ServiceA a) {} // ServiceB depends on ServiceA - CIRCULAR!
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Don't create circular dependencies
    @Component
    class ServiceA(private val b: ServiceB) // ServiceA depends on ServiceB

    @Component
    class ServiceB(private val a: ServiceA) // ServiceB depends on ServiceA - CIRCULAR!
    ```

**❌ Large Components**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Don't create "God objects"
    @Component
    public final class HugeService {
        // ❌ Does everything: validation, database, email, logging, caching...
        private final Validator validator;
        private final Repository repo;
        private final EmailService email;
        private final Logger logger;
        private final Cache cache;

        // Hundreds of methods...
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Don't create "God objects"
    @Component
    class HugeService(
        // ❌ Does everything: validation, database, email, logging, caching...
        private val validator: Validator,
        private val repo: Repository,
        private val email: EmailService,
        private val logger: Logger,
        private val cache: Cache
    ) {
        // Hundreds of methods...
    }
    ```

## What's Next?

- **[Build a Complete DI Application](../dependency-injection-guide.md)**: Follow the comprehensive step-by-step tutorial to build a real notification system
- **[Build Simple HTTP application](../getting-started.md)**: Learn how to create REST endpoints with dependency injection

## Help

If you encounter issues:

- Check the [Dependency Injection Documentation](../../documentation/dependency-injection.md)
- Check the [Component Examples](https://github.com/kora-projects/kora-examples)
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)