---
title: Database Integration with Kora
summary: Learn how to integrate databases with Kora using JDBC and perform CRUD operations
tags: database, jdbc, crud, persistence
---

# Database Integration with Kora

This guide shows you how to integrate a PostgreSQL database with Kora and perform basic CRUD operations.

## What You'll Build

You'll build a REST API for managing users with full CRUD operations (Create, Read, Update, Delete) backed by a PostgreSQL database.

## What You'll Need

- JDK 17 or later
- PostgreSQL database (or Docker)
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide

## Prerequisites

!!! note "Required: Complete Basic Kora Setup"

    This guide assumes you have completed the **[Create Your First Kora App](../getting-started.md)** guide and have a working Kora project with basic setup.

    If you haven't completed the basic guide yet, please do so first as this guide builds upon that foundation.

## Add Dependencies

Now add the database-specific dependencies for PostgreSQL and JDBC support:

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        runtimeOnly("org.postgresql:postgresql:42.7.3")
        implementation("ru.tinkoff.kora:database-jdbc")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        runtimeOnly("org.postgresql:postgresql:42.7.3")
        implementation("ru.tinkoff.kora:database-jdbc")
    }
    ```

## Add Modules

Update your Application interface to include the JDBC database module:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.database.jdbc.JdbcDatabaseModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends 
            UndertowHttpServerModule, 
            JdbcDatabaseModule, 
            LogbackModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.database.jdbc.JdbcDatabaseModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application : 
            UndertowHttpServerModule, 
            JdbcDatabaseModule, 
            LogbackModule
    ```

## Creating the Entity

=== ":fontawesome-brands-java: Java"

    `src/main/java/ru/tinkoff/kora/example/User.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.database.common.annotation.Column;

    public record User(
        @Column("id") Long id,
        @Column("name") String name,
        @Column("email") String email
    ) {}
    ```

=== ":simple-kotlin: Kotlin"

    `src/main/kotlin/ru/tinkoff/kora/example/User.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.database.common.annotation.Column

    data class User(
        @field:Column("id") val id: Long,
        @field:Column("name") val name: String,
        @field:Column("email") val email: String
    )
    ```

## Creating the Repository

=== ":fontawesome-brands-java: Java"

    `src/main/java/ru/tinkoff/kora/example/UserRepository.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.database.jdbc.JdbcRepository;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;

    import java.util.List;
    import java.util.Optional;

    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("SELECT id, name, email FROM users")
        List<User> findAll();

        @Query("SELECT id, name, email FROM users WHERE id = :id")
        Optional<User> findById(Long id);

        @Query("INSERT INTO users(name, email) VALUES (:name, :email) RETURNING id, name, email")
        User save(String name, String email);

        @Query("UPDATE users SET name = :name, email = :email WHERE id = :id")
        void update(Long id, String name, String email);

        @Query("DELETE FROM users WHERE id = :id")
        void delete(Long id);
    }
    ```

=== ":simple-kotlin: Kotlin"

    `src/main/kotlin/ru/tinkoff/kora/example/UserRepository.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.database.jdbc.JdbcRepository
    import ru.tinkoff.kora.database.common.annotation.Query
    import ru.tinkoff.kora.database.common.annotation.Repository

    @Repository
    interface UserRepository : JdbcRepository {

        @Query("SELECT id, name, email FROM users")
        fun findAll(): List<User>

        @Query("SELECT id, name, email FROM users WHERE id = :id")
        fun findById(id: Long): Optional<User>

        @Query("INSERT INTO users(name, email) VALUES (:name, :email) RETURNING id, name, email")
        fun save(name: String, email: String): User

        @Query("UPDATE users SET name = :name, email = :email WHERE id = :id")
        fun update(id: Long, name: String, email: String)

        @Query("DELETE FROM users WHERE id = :id")
        fun delete(id: Long)
    }
    ```

## Why Repository Pattern and SQL in Kora?

Kora's approach to database integration emphasizes **direct SQL usage with repository interfaces** over complex Object-Relational Mapping (ORM) systems. This design choice provides significant advantages in performance, maintainability, and developer control.

### The Repository Pattern in Kora

**Repository interfaces** serve as a clean abstraction layer between your business logic and data access code:

- **Interface Segregation**: Each repository can focus on specific business operations while working with multiple entities as needed
- **Dependency Injection**: Repositories are automatically injected as dependencies
- **Testability**: Easy to mock repositories for unit testing
- **Type Safety**: Compile-time verification of queries and parameters

### Why SQL Over Complex ORMs?

While ORMs like Hibernate or JPA offer convenience, they come with significant drawbacks that Kora avoids:

#### Performance Advantages

**Direct SQL Control**:
- **Optimized Queries**: Write exactly the SQL you need, no hidden queries or N+1 problems
- **Predictable Performance**: No unexpected lazy loading or complex query generation
- **Database-Specific Features**: Leverage your database's unique capabilities and optimizations
- **Query Planning**: Full control over execution plans and indexing strategies

**No ORM Overhead**:
- **No Proxy Objects**: Direct access to your data without wrapper objects
- **No Session Management**: No complex session state or flushing strategies
- **No Lazy Loading**: Explicit control over when and what data is loaded
- **Minimal Memory Footprint**: No extensive metadata or caching layers

#### Developer Experience Benefits

**Explicit is Better Than Implicit**:
- **Clear Intent**: SQL queries are explicit and self-documenting
- **Debugging**: Easy to debug and profile actual database queries
- **Maintenance**: Changes to data access logic are obvious and traceable
- **Learning Curve**: SQL knowledge is universally applicable across projects

**Type Safety Without Magic**:
- **Compile-Time Verification**: Query parameters are checked at compile time
- **IDE Support**: Full autocomplete and refactoring support for SQL
- **Runtime Safety**: No runtime query generation failures

#### Maintainability Advantages

**Simple Architecture**:
- **No Complex Mappings**: No XML, annotations, or complex entity relationships
- **No Migration Headaches**: No schema generation or migration complexities
- **No Version Conflicts**: No ORM version compatibility issues
- **No Vendor Lock-in**: SQL works across all database vendors

**Evolutionary Design**:
- **Incremental Changes**: Easy to modify queries as requirements evolve
- **Refactoring Safety**: Database changes don't break application code unexpectedly
- **Team Consistency**: All developers work with the same SQL paradigm

**What Kora Provides**:
- **Connection Management**: Automatic connection pooling and lifecycle management
- **Parameter Binding**: Type-safe parameter binding with named parameters
- **Result Mapping**: Automatic mapping of query results to Java objects
- **Transaction Support**: Transaction management via method handling
- **Error Handling**: Proper exception translation and resource cleanup
- **Observability**: Full metrics, tracing, and structured logging for all repository operations

**What You Control**:
- **Query Optimization**: Full control over SQL execution and performance
- **Schema Design**: Direct influence over database schema and indexing
- **Data Relationships**: Explicit handling of complex data relationships
- **Performance Tuning**: Fine-grained control over query execution

This approach makes Kora particularly well-suited for **enterprise applications** where performance, maintainability, and developer control are paramount.

## Creating the Service    

    `src/main/java/ru/tinkoff/kora/example/UserService.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.Component;

    import java.util.List;
    import java.util.Optional;

    @Component
    public final class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        public List<User> getAllUsers() {
            return userRepository.findAll();
        }

        public Optional<User> getUserById(Long id) {
            return userRepository.findById(id);
        }

        public User createUser(String name, String email) {
            return userRepository.save(name, email);
        }

        public Optional<User> updateUser(Long id, String name, String email) {
            var existingUser = userRepository.findById(id);
            if (existingUser.isPresent()) {
                userRepository.update(id, name, email);
                return userRepository.findById(id);
            }
            return Optional.empty();
        }

        public boolean deleteUser(Long id) {
            var existingUser = userRepository.findById(id);
            if (existingUser.isPresent()) {
                userRepository.delete(id);
                return true;
            }
            return false;
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    `src/main/kotlin/ru/tinkoff/kora/example/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.Component

    @Component
    class UserService(private val userRepository: UserRepository) {

        fun getAllUsers(): List<User> = userRepository.findAll()

        fun getUserById(id: Long): Optional<User> = userRepository.findById(id)

        fun createUser(name: String, email: String): User = userRepository.save(name, email)

        fun updateUser(id: Long, name: String, email: String): Optional<User> {
            val existingUser = userRepository.findById(id)
            return if (existingUser.isPresent) {
                userRepository.update(id, name, email)
                userRepository.findById(id)
            } else {
                Optional.empty()
            }
        }

        fun deleteUser(id: Long): Boolean {
            val existingUser = userRepository.findById(id)
            return if (existingUser.isPresent) {
                userRepository.delete(id)
                true
            } else {
                false
            }
        }
    }
    ```

## Creating the Controller    

    `src/main/java/ru/tinkoff/kora/example/UserController.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.http.server.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.server.common.annotation.PathParam;
    import ru.tinkoff.kora.http.server.common.annotation.RequestBody;

    import java.util.List;

    @Component
    @HttpController
    public final class UserController {

        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        public List<User> getAllUsers() {
            return userService.getAllUsers();
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        public User getUser(@PathParam("id") Long id) {
            return userService.getUserById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        public User createUser(@RequestBody CreateUserRequest request) {
            return userService.createUser(request.name(), request.email());
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/users/{id}")
        public User updateUser(@PathParam("id") Long id, @RequestBody UpdateUserRequest request) {
            return userService.updateUser(id, request.name(), request.email())
                .orElseThrow(() -> new RuntimeException("User not found"));
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{id}")
        public void deleteUser(@PathParam("id") Long id) {
            if (!userService.deleteUser(id)) {
                throw new RuntimeException("User not found");
            }
        }
    }

    record CreateUserRequest(String name, String email) {}
    record UpdateUserRequest(String name, String email) {}
    ```

=== ":simple-kotlin: Kotlin"

    `src/main/kotlin/ru/tinkoff/kora/example/UserController.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.http.server.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.server.common.annotation.PathParam
    import ru.tinkoff.kora.http.server.common.annotation.RequestBody

    @Component
    @HttpController
    class UserController(private val userService: UserService) {

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        fun getAllUsers(): List<User> = userService.allUsers

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        fun getUser(@PathParam("id") id: Long): User =
            userService.getUserById(id).orElseThrow { RuntimeException("User not found") }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        fun createUser(@RequestBody request: CreateUserRequest): User =
            userService.createUser(request.name, request.email)

        @HttpRoute(method = HttpMethod.PUT, path = "/users/{id}")
        fun updateUser(@PathParam("id") id: Long, @RequestBody request: UpdateUserRequest): User =
            userService.updateUser(id, request.name, request.email)
                .orElseThrow { RuntimeException("User not found") }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{id}")
        fun deleteUser(@PathParam("id") id: Long) {
            if (!userService.deleteUser(id)) {
                throw RuntimeException("User not found")
            }
        }
    }

    data class CreateUserRequest(val name: String, val email: String)
    data class UpdateUserRequest(val name: String, val email: String)
    ```

## Database Setup

### Using Docker Compose (Recommended)

Create a `docker-compose.yml` file in your project root:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Start the database:

```bash
docker-compose up -d
```

This will start PostgreSQL with:
- **Database**: `postgres`
- **Username**: `postgres`
- **Password**: `postgres`
- **Port**: `5432`

### Database Configuration

Create `src/main/resources/application.conf`:

```hocon
db {
    jdbcUrl = "jdbc:postgresql://localhost:5432/postgres"
    username = "postgres"
    password = "postgres"
    maxPoolSize = 10
    }
```

### Database Configuration

### Database Schema

Create the database table:

```sql
-- Connect to your database and run:
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- Insert some test data
INSERT INTO users (name, email) VALUES
('John Doe', 'john@example.com'),
('Jane Smith', 'jane@example.com');
```

### Running the Application

```bash
./gradlew run
```

### Testing the API

### Get all users
```bash
curl http://localhost:8080/users
```

### Get user by ID
```bash
curl http://localhost:8080/users/1
```

### Create a new user
```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Johnson", "email": "bob@example.com"}'
```

### Update a user
```bash
curl -X PUT http://localhost:8080/users/3 \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Smith", "email": "bob.smith@example.com"}'
```

### Delete a user
```bash
curl -X DELETE http://localhost:8080/users/3
```

## What's Next?

- [Add Validation](../validation.md)
- [Add Caching](../cache.md)
- [Add Observability & Monitoring](../observability.md)
- [Explore More Examples](../examples/kora-examples.md)

## Troubleshooting

### Connection Issues
- Ensure PostgreSQL is running on port 5432
- Verify database credentials in `application.conf`
- Check that the database and user exist

### Compilation Errors
- Ensure annotation processor is configured
- Check that all dependencies are included
- Verify Java version compatibility (17+)

### Runtime Errors
- Check database connectivity
- Verify table schema matches entity
- Review application logs for detailed error messages

## Help

- [Database JDBC Documentation](../documentation/database-jdbc.md)
- [Kora GitHub Repository](https://github.com/kora-projects/kora)
- [GitHub Discussions](https://github.com/kora-projects/kora/discussions)