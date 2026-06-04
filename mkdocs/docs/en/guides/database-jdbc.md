---
search:
  exclude: true
title: Database Integration with Kora
summary: Learn how to integrate databases with Kora using JDBC and perform CRUD operations
tags: database, jdbc, crud, persistence
---

# Database Integration with Kora { #database-integration-kora }

This guide introduces PostgreSQL persistence with Kora JDBC. It covers how repository interfaces use `@Repository` and `@Query`, how record fields map to database columns, how Flyway migrations create
the schema, and how the Kora JDBC module wires a connection pool into the application graph. You will also see how service and controller code can keep the same API shape while storage moves to a real
database.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-database-jdbc-app).

## What You'll Build { #youll-build }

You will turn the user HTTP API into a PostgreSQL-backed application with:

- a Flyway migration that creates the `users` table
- a JDBC DAO model with explicit column mapping
- a Kora `@Repository` interface with SQL queries for create, read, list, update, and delete operations
- a database-backed repository implementation connected to the existing service layer
- HOCON configuration for the JDBC connection pool and migrations
- Testcontainers-based tests that verify persistence against real PostgreSQL

## What You'll Need { #youll-need }

- JDK 17 or later
- PostgreSQL database (or Docker)
- Gradle 7+
- A text editor or IDE
- Completed [HTTP Server](http-server.md) guide

## Prerequisites { #prerequisites }

!!! note "Required: Complete HTTP Server Guide"

    This guide assumes you have completed the **[HTTP Server](http-server.md)** guide and have a working HTTP API project with `UserController`, `UserService`, and in-memory repository implementation.

    If you haven't completed the HTTP server guide yet, do that first, because this guide replaces the in-memory persistence with JDBC/PostgreSQL.

## Overview { #overview }

Moving from in-memory storage to [PostgreSQL](https://www.postgresql.org/docs/) changes the persistence layer without changing the public API contract. That is an important production pattern:
controllers and service methods can keep the same shape while the repository implementation becomes durable, transactional, and backed by real SQL.

The guide is built around the same separation used in the HTTP server guide: transport code stays in the controller, application behavior stays in the service, and persistence details move behind a
repository contract.

### How Persistence Changes the Application { #persistence-changes-application }

An in-memory repository is useful for learning because it has no external setup and makes the first HTTP API easy to run. But in-memory state disappears when the process stops, cannot be shared
between application instances, and does not give you the database guarantees that real services usually need.

A database-backed application introduces new concerns:

- data must survive application restarts
- concurrent requests may read and write the same records
- schema changes must be repeatable across environments
- queries must be explicit and safe
- tests should verify behavior against real database semantics

That is why this guide does not just "add a database dependency". It introduces the full persistence boundary: schema, connection configuration, repository queries, row mapping, generated
implementations, and container-based tests.

### PostgreSQL as the Source of Truth { #postgresql-source-truth }

In this guide, PostgreSQL becomes the source of truth for user data. The repository no longer stores users in a local map; it reads and writes rows in a `users` table. That changes runtime behavior in
several important ways:

- created users remain available after application restart
- multiple app instances can work with the same database
- database constraints can protect data consistency
- SQL queries define exactly how data is selected, inserted, updated, and deleted

The service layer should not need to know those details. It should still ask the repository to create, find, list, update, or delete users. The repository is the adapter that translates those
application operations into SQL.

### JDBC Repositories in Kora { #jdbc-repositories-kora }

For the full repository model, `@Repository`, `@Query`, and row mapping rules, see the [JDBC documentation](../documentation/database-jdbc.md) and [Database Common documentation](../documentation/database-common.md).

[JDBC](https://docs.oracle.com/javase/tutorial/jdbc/) is the standard Java API for relational database access. On its own, JDBC is low level: you usually need to manage connections, prepare
statements, bind parameters, execute queries, handle result sets, and close resources correctly.

Kora JDBC repositories keep explicit SQL while removing most repetitive boilerplate. You declare a repository interface, annotate methods with SQL queries, and Kora generates the implementation. Named
SQL parameters bind method arguments, and result rows are mapped into Java records or Kotlin data classes.

This guide focuses on several core repository ideas:

- explicit SQL through `@Query`
- named parameters instead of string concatenation
- DAO models with `@Column` mappings
- generated repository implementations
- repository methods that match service needs

The explicit SQL is intentional. It makes the data access contract easy to inspect, review, and optimize. The generated implementation handles framework glue, while the query itself stays visible in
the repository.

### Entities and Row Mapping { #dao-models }

HTTP DTOs and database rows are not always the same thing. A response DTO describes what the API returns. A DAO model describes how data is stored and read from the database. In small examples they
may look similar, but keeping the distinction clear helps as systems grow.

Because `UserRequest` and `UserResponse` are still HTTP JSON DTOs, the application keeps `@Json` on those classes. That lets Kora generate the JSON reader and writer for the API boundary during normal
annotation processing, while `UserDAO` uses database annotations for row mapping.

Kora maps database rows into records or data classes. `@Column` annotations make the mapping explicit, which is especially useful when Java field names and database column names use different
conventions. For example, Java often uses `createdAt`, while SQL schemas often use `created_at`.

This guide keeps row mapping straightforward so the main lesson stays visible: SQL results become typed application objects, and the repository boundary hides database details from the service layer.

### Schema and Migrations { #schema-migrations }

For Flyway, Liquibase, and migration configuration details, see the [Database Migration documentation](../documentation/database-migration.md).

A database-backed application needs a repeatable way to create and evolve schema. [Flyway](https://documentation.red-gate.com/fd) migrations provide that history. Each migration is a versioned SQL
file, and the application can run migrations at startup before repositories are used. That prevents "works on my machine" schema drift and makes tests easier to reproduce.

Migrations are part of the application contract. If the repository expects a `users` table with specific columns, that schema must be created in a predictable way. Versioned migrations make schema
changes reviewable and repeatable for local development, CI, staging, and production.

### Runtime Configuration { #runtime-config }

JDBC also introduces runtime infrastructure: a PostgreSQL driver, a connection pool, credentials, and database URLs. Kora wires those pieces through configuration and modules. The application graph
owns the database object, the repository depends on it, and tests can override connection values with Testcontainers.

A connection pool matters because applications should not open a new database connection for every request. The pool manages a bounded set of reusable connections, which improves performance and
protects the database from uncontrolled connection growth.

Configuration matters because database URLs and credentials differ between local development, tests, and deployed environments. Kora keeps those values outside code and injects the configured database
component into the graph.

### Persistence Testing { #persistence-testing }

The architectural lesson is that persistence should be replaceable behind a stable service boundary. The API can keep returning the same DTOs, while the repository moves from memory to SQL and gains
durability, migrations, and realistic integration tests.

Database code should be tested against a real database whenever possible. Mocks cannot prove that SQL syntax is valid, that migrations match repository expectations, or that row mapping works. This
guide uses [Testcontainers](https://java.testcontainers.org/) so tests can start PostgreSQL automatically and verify persistence behavior in an isolated environment.

The practical flow is:

1. add JDBC, PostgreSQL, and Flyway dependencies
2. add database modules to the Kora application
3. create a migration for the `users` table
4. define DAO records and repository SQL methods
5. connect the JDBC repository to the service layer
6. verify persistence with [Testcontainers](https://java.testcontainers.org/)

## Dependencies { #dependencies }

Now add the database-specific dependencies for PostgreSQL and JDBC support:

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        runtimeOnly("org.postgresql:postgresql:42.7.7")
        implementation("ru.tinkoff.kora:database-jdbc")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        runtimeOnly("org.postgresql:postgresql:42.7.7")
        implementation("ru.tinkoff.kora:database-jdbc")
    }
    ```

## Modules { #modules }

Update your Application interface to include JDBC and Flyway modules.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasejdbc/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.database.flyway.FlywayJdbcDatabaseModule;
    import ru.tinkoff.kora.database.jdbc.JdbcDatabaseModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            JdbcDatabaseModule,  // <----- Connected module
            FlywayJdbcDatabaseModule,  // <----- Connected module
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.database.flyway.FlywayJdbcDatabaseModule
    import ru.tinkoff.kora.database.jdbc.JdbcDatabaseModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        JdbcDatabaseModule,  // <----- Connected module
        FlywayJdbcDatabaseModule,  // <----- Connected module
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Database entity { #entity-db }

Replace the old in-memory `User` storage model with JDBC DAO model used by repository mappings.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasejdbc/repository/UserDAO.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.repository;

    import java.time.LocalDateTime;
    import ru.tinkoff.kora.database.common.annotation.Column;
    import ru.tinkoff.kora.database.jdbc.EntityJdbc;

    @EntityJdbc
    public record UserDAO(
            @Column("id") Long id,
            @Column("name") String name,
            @Column("email") String email,
            @Column("created_at") LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/repository/UserDAO.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.repository

    import java.time.LocalDateTime
    import ru.tinkoff.kora.database.common.annotation.Column
    import ru.tinkoff.kora.database.jdbc.EntityJdbc

    @EntityJdbc
    data class UserDAO(
        @field:Column("id") val id: Long,
        @field:Column("name") val name: String,
        @field:Column("email") val email: String,
        @field:Column("created_at") val createdAt: LocalDateTime,
    )
    ```

## Repository { #repository }

At this step, remove the old `InMemoryUserRepository` from the HTTP server guide and create a real JDBC repository with SQL queries.

For `update` and `delete`, use `UpdateCount` so service logic can decide whether row was actually changed/deleted.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasejdbc/repository/UserRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.repository;

    import java.util.List;
    import java.util.Optional;
    import ru.tinkoff.kora.database.common.UpdateCount;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;
    import ru.tinkoff.kora.database.jdbc.JdbcRepository;

    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("SELECT id, name, email, created_at FROM users ORDER BY id")
        List<UserDAO> findAll();

        @Query("SELECT id, name, email, created_at FROM users WHERE id = :id")
        Optional<UserDAO> findById(Long id);

        @Query("INSERT INTO users(name, email) VALUES (:name, :email) RETURNING id")
        long save(String name, String email);

        @Query("UPDATE users SET name = :name, email = :email WHERE id = :id")
        UpdateCount update(Long id, String name, String email);

        @Query("DELETE FROM users WHERE id = :id")
        UpdateCount deleteById(Long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/repository/UserRepository.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.repository

    import ru.tinkoff.kora.database.common.UpdateCount
    import ru.tinkoff.kora.database.common.annotation.Query
    import ru.tinkoff.kora.database.common.annotation.Repository
    import ru.tinkoff.kora.database.jdbc.JdbcRepository

    @Repository
    interface UserRepository : JdbcRepository {

        @Query("SELECT id, name, email, created_at FROM users ORDER BY id")
        fun findAll(): List<UserDAO>

        @Query("SELECT id, name, email, created_at FROM users WHERE id = :id")
        fun findById(id: Long): UserDAO?

        @Query("INSERT INTO users(name, email) VALUES (:name, :email) RETURNING id")
        fun save(name: String, email: String): Long

        @Query("UPDATE users SET name = :name, email = :email WHERE id = :id")
        fun update(id: Long, name: String, email: String): UpdateCount

        @Query("DELETE FROM users WHERE id = :id")
        fun deleteById(id: Long): UpdateCount
    }
    ```

`@EntityJdbc` tells Kora to generate JDBC mappers for the DAO model directly. That keeps mapper generation explicit and avoids slower late-generation rounds when the repository graph first requests a
mapper.

After compilation, Kora generates the repository implementation and row mapper for this interface:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-database-jdbc-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasejdbc/repository/$UserRepository_Impl.java
    guides/guide-database-jdbc-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasejdbc/repository/$UserDAO_JdbcResultSetMapper.java
    guides/guide-database-jdbc-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasejdbc/repository/$UserDAO_JdbcRowMapper.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-database-jdbc-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/repository/$UserRepository_Impl.kt
    guides/kotlin/guide-kotlin-database-jdbc-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/repository/$UserDAO_JdbcResultSetMapper.kt
    guides/kotlin/guide-kotlin-database-jdbc-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/repository/$UserDAO_JdbcRowMapper.kt
    ```

This shortened generated repository excerpt shows how named SQL parameters become JDBC prepared statement parameters:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static final QueryContext QUERY_CONTEXT_3 = new QueryContext(
          "INSERT INTO users(name, email) VALUES (:name, :email) RETURNING id",
          "INSERT INTO users(name, email) VALUES (?, ?) RETURNING id",
          "UserRepository.save"
        );

    @Override
    public long save(String name, String email) {
        var _ctxCurrent = ru.tinkoff.kora.common.Context.current();
        var _query = QUERY_CONTEXT_3;
        var _telemetry = this._connectionFactory.telemetry().createContext(_ctxCurrent, _query);
        var _conToUse = this._connectionFactory.currentConnection();
        Connection _conToClose;
        if (_conToUse == null) {
            _conToUse = this._connectionFactory.newConnection();
            _conToClose = _conToUse;
        } else {
            _conToClose = null;
        }
        try (_conToClose; var _stmt = _conToUse.prepareStatement(_query.sql())) {
            _stmt.setString(1, name);
            _stmt.setString(2, email);
            try (var _rs = _stmt.executeQuery()) {
                var _result = _result_mapper_3.apply(_rs);
                _telemetry.close(null);
                return _result;
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val _queryContext_3: QueryContext = QueryContext(
      "INSERT INTO users(name, email) VALUES (:name, :email) RETURNING id",
      "INSERT INTO users(name, email) VALUES (?, ?) RETURNING id",
      "UserRepository.save"
    )

    override fun save(name: String, email: String): Long {
      val _query = _queryContext_3
      val _ctxCurrent = Context.current()
      val _telemetry = _jdbcConnectionFactory.telemetry().createContext(_ctxCurrent, _query)
      var _conToUse = _jdbcConnectionFactory.currentConnection()
      val _conToClose = if (_conToUse == null) {
        _conToUse = _jdbcConnectionFactory.newConnection()
        _conToUse
      } else {
        null
      }
      try {
        _conToClose.use {
          _conToUse!!.prepareStatement(_query.sql()).use { _stmt ->
            _stmt.setString(1, name)
            _stmt.setString(2, email)
            _stmt.executeQuery().use { _rs ->
              val _result = _result_mapper_3.apply(_rs)
                ?: throw NullPointerException("Result mapping is expected non-null, but was null")
              _telemetry.close(null)
              return _result
            }
          }
        }
      } finally {
        _ctxCurrent.inject()
      }
    }
    ```

That fragment shows the concrete framework work hidden behind the repository interface: parameter binding, connection handling, query telemetry, and result mapping.

This shortened generated row mapper excerpt also shows why explicit `@Column` names matter:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var _idColumn = _rs.findColumn("id");
    var _nameColumn = _rs.findColumn("name");
    var _emailColumn = _rs.findColumn("email");
    var _createdAtColumn = _rs.findColumn("created_at");

    Long id = _rs.getLong(_idColumn);
    String name = _rs.getString(_nameColumn);
    String email = _rs.getString(_emailColumn);
    LocalDateTime createdAt = _rs.getObject(_createdAtColumn, LocalDateTime.class);

    return new UserDAO(id, name, email, createdAt);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val _idx_id = _rs.findColumn("id")
    val _idx_name = _rs.findColumn("name")
    val _idx_email = _rs.findColumn("email")
    val _idx_createdAt = _rs.findColumn("created_at")

    var id: Long? = _rs.getLong(_idx_id)
    if (_rs.wasNull() || id == null) {
      throw NullPointerException("Required field id is not nullable but row has null")
    }
    var name: String? = _rs.getString(_idx_name)
    if (_rs.wasNull() || name == null) {
      throw NullPointerException("Required field name is not nullable but row has null")
    }
    var email: String? = _rs.getString(_idx_email)
    if (_rs.wasNull() || email == null) {
      throw NullPointerException("Required field email is not nullable but row has null")
    }
    var createdAt: LocalDateTime? = _rs.getObject(_idx_createdAt, LocalDateTime::class.java)
    if (_rs.wasNull() || createdAt == null) {
      throw NullPointerException("Required field created_at is not nullable but row has null")
    }

    val _result = UserDAO(id, name, email, createdAt)
    return _result
    ```

This is the best place to debug SQL binding and row mapping because it shows exactly what Kora compiled from `@Repository`, `@Query`, and `@Column`.

## Why the Repository Pattern? { #repository-pattern }

Kora's approach to database integration emphasizes direct SQL usage with repository interfaces over complex Object-Relational Mapping (ORM) systems. This design choice provides significant
advantages in performance, maintainability, and developer control.

The Repository Pattern in Kora:

Repository interfaces serve as a clean abstraction layer between your business logic and data access code:

- Interface Segregation: Each repository can focus on specific business operations while working with multiple entities as needed
- Dependency Injection: Repositories are automatically injected as dependencies
- Testability: Easy to mock repositories for unit testing
- Type Safety: Compile-time verification of queries and parameters

Why SQL Over Complex ORMs?

While ORMs like Hibernate or JPA offer convenience, they come with significant drawbacks that Kora avoids:

Performance Advantages:

Direct SQL Control:

- Optimized Queries: Write exactly the SQL you need, no hidden queries or N+1 problems
- Predictable Performance: No unexpected lazy loading or complex query generation
- Database-Specific Features: Leverage your database's unique capabilities and optimizations
- Query Planning: Full control over execution plans and indexing strategies

No ORM Overhead:

- No Proxy Objects: Direct access to your data without wrapper objects
- No Session Management: No complex session state or flushing strategies
- No Lazy Loading: Explicit control over when and what data is loaded
- Minimal Memory Footprint: No extensive metadata or caching layers

Developer Experience Benefits:

Explicit is Better Than Implicit:

- Clear Intent: SQL queries are explicit and self-documenting
- Debugging: Easy to debug and profile actual database queries
- Maintenance: Changes to data access logic are obvious and traceable
- Learning Curve: SQL knowledge is universally applicable across projects

Type Safety Without Magic:

- Compile-Time Verification: Query parameters are checked at compile time
- IDE Support: Full autocomplete and refactoring support for SQL
- Runtime Safety: No runtime query generation failures

Maintainability Advantages:

Simple Architecture:

- No Complex Mappings: No XML, annotations, or complex entity relationships
- No Migration Headaches: No schema generation or migration complexities
- No Version Conflicts: No ORM version compatibility issues
- No Vendor Lock-in: SQL works across all database vendors

Evolutionary Design:

- Incremental Changes: Easy to modify queries as requirements evolve
- Refactoring Safety: Database changes don't break application code unexpectedly
- Team Consistency: All developers work with the same SQL paradigm

What Kora Provides:

- Connection Management: Automatic connection pooling and lifecycle management
- Parameter Binding: Type-safe parameter binding with named parameters
- Result Mapping: Automatic mapping of query results to Java objects
- Transaction Support: Transaction management via method handling
- Error Handling: Proper exception translation and resource cleanup
- Observability: Full metrics, tracing, and structured logging for all repository operations

What You Control:

- Query Optimization: Full control over SQL execution and performance
- Schema Design: Direct influence over database schema and indexing
- Data Relationships: Explicit handling of complex data relationships
- Performance Tuning: Fine-grained control over query execution

This approach makes Kora particularly well-suited for enterprise applications where performance, maintainability, and developer control are paramount.

## Refactor the Service { #refactor-service }

At this step, you refactor the existing `UserService` from the HTTP server guide.

Important rules:

- Keep the same public service contracts used by `UserController`.
- Replace only persistence internals: use JDBC repository calls instead of in-memory storage.
- Keep `UserController` and its HTTP contracts unchanged.
- For invalid path id format, throw `HttpServerResponseException` with `400`.
- For update/delete when no row is affected, throw `HttpServerResponseException` with `404`.

===! ":fontawesome-brands-java: Java"

    Update `src/main/java/ru/tinkoff/kora/guide/databasejdbc/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.service;

    import java.time.LocalDateTime;
    import java.util.Comparator;
    import java.util.List;
    import java.util.Optional;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserRequest;
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserResponse;
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserDAO;
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserRepository;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;

    @Component
    public final class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        public UserResponse createUser(UserRequest request) {
            var generatedId = userRepository.save(request.name(), request.email());
            return new UserResponse(String.valueOf(generatedId), request.name(), request.email(), LocalDateTime.now());
        }

        public Optional<UserResponse> getUser(String id) {
            return parseId(id).flatMap(userRepository::findById).map(this::toResponse);
        }

        public List<UserResponse> getUsers(int page, int size, String sort) {
            return userRepository.findAll().stream()
                    .map(this::toResponse)
                    .sorted(getComparator(sort))
                    .skip((long) page * size)
                    .limit(size)
                    .toList();
        }

        public UserResponse updateUser(String id, UserRequest request) {
            var parsedId = parseIdOrThrow(id);
            var updated = userRepository.update(parsedId, request.name(), request.email());
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "User not found");
            }
            return new UserResponse(String.valueOf(parsedId), request.name(), request.email(), LocalDateTime.now());
        }

        public void deleteUser(String id) {
            var parsedId = parseIdOrThrow(id);
            var deleted = userRepository.deleteById(parsedId);
            if (deleted.value() < 1) {
                throw HttpServerResponseException.of(404, "User not found");
            }
        }

        private long parseIdOrThrow(String id) {
            try {
                return Long.parseLong(id);
            } catch (NumberFormatException ignored) {
                throw HttpServerResponseException.of(400, "Invalid user id: " + id);
            }
        }

        private Optional<Long> parseId(String id) {
            try {
                return Optional.of(Long.parseLong(id));
            } catch (NumberFormatException ignored) {
                return Optional.empty();
            }
        }

        private UserResponse toResponse(UserDAO user) {
            return new UserResponse(String.valueOf(user.id()), user.name(), user.email(), user.createdAt());
        }

        private Comparator<UserResponse> getComparator(String sort) {
            return switch (sort.toLowerCase()) {
                case "name" -> Comparator.comparing(UserResponse::name);
                case "email" -> Comparator.comparing(UserResponse::email);
                case "createdat" -> Comparator.comparing(UserResponse::createdAt);
                default -> Comparator.comparing(UserResponse::name);
            };
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    Update `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.service

    import java.time.LocalDateTime
    import java.util.Comparator
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserRequest
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserResponse
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserDAO
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserRepository
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException

    @Component
    class UserService(private val userRepository: UserRepository) {

        fun createUser(request: UserRequest): UserResponse {
            val generatedId = userRepository.save(request.name, request.email)
            return UserResponse(generatedId.toString(), request.name, request.email, LocalDateTime.now())
        }

        fun getUser(id: String): UserResponse? =
            parseId(id)?.let { userRepository.findById(it) }?.let { toResponse(it) }

        fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> =
            userRepository.findAll()
                .map { toResponse(it) }
                .sortedWith(getComparator(sort))
                .drop(page * size)
                .take(size)

        fun updateUser(id: String, request: UserRequest): UserResponse {
            val parsedId = parseIdOrThrow(id)
            val updated = userRepository.update(parsedId, request.name, request.email)
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "User not found")
            }
            return UserResponse(parsedId.toString(), request.name, request.email, LocalDateTime.now())
        }

        fun deleteUser(id: String) {
            val parsedId = parseIdOrThrow(id)
            val deleted = userRepository.deleteById(parsedId)
            if (deleted.value() < 1) {
                throw HttpServerResponseException.of(404, "User not found")
            }
        }

        private fun parseIdOrThrow(id: String): Long =
            id.toLongOrNull() ?: throw HttpServerResponseException.of(400, "Invalid user id: $id")

        private fun parseId(id: String): Long? = id.toLongOrNull()

        private fun toResponse(user: UserDAO): UserResponse =
            UserResponse(user.id.toString(), user.name, user.email, user.createdAt)

        private fun getComparator(sort: String): Comparator<UserResponse> = when (sort.lowercase()) {
            "name" -> compareBy { it.name }
            "email" -> compareBy { it.email }
            "createdat" -> compareBy { it.createdAt }
            else -> compareBy { it.name }
        }
    }
    ```

!!! note "Controller stays as-is"

    Do not rewrite `UserController` in this guide. Keep the controller from `http-server.md` unchanged, so only the repository implementation is replaced under the hood.

## Configuration { #configuration }

Create `src/main/resources/application.conf`:

For the full configuration reference,
see [Database JDBC](../documentation/database-jdbc.md) and [Database Migration](../documentation/database-migration.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    db {
      jdbcUrl = ${POSTGRES_JDBC_URL} //(1)!
      username = ${POSTGRES_USER} //(2)!
      password = ${POSTGRES_PASS} //(3)!
      maxPoolSize = 10 //(4)!
      poolName = "guide-jdbc" //(5)!
    }

    flyway {
      locations = "db/migration" //(6)!
    }
    ```

    1. JDBC connection URL. Optional override from `POSTGRES_JDBC_URL`.
    2. Database user name. Optional override from `POSTGRES_USER`.
    3. Database user password. Optional override from `POSTGRES_PASS`.
    4. Maximum number of connections in the pool.
    5. Human-readable connection pool name used in diagnostics.
    6. Migration locations scanned by Flyway.

=== ":simple-yaml: `YAML`"

    ```yaml
    db:
      jdbcUrl: ${POSTGRES_JDBC_URL} #(1)!
      username: ${POSTGRES_USER} #(2)!
      password: ${POSTGRES_PASS} #(3)!
      maxPoolSize: 10 #(4)!
      poolName: "guide-jdbc" #(5)!
    flyway:
      locations: "db/migration" #(6)!
    ```

    1. JDBC connection URL. Optional override from `POSTGRES_JDBC_URL`.
    2. Database user name. Optional override from `POSTGRES_USER`.
    3. Database user password. Optional override from `POSTGRES_PASS`.
    4. Maximum number of connections in the pool.
    5. Human-readable connection pool name used in diagnostics.
    6. Migration locations scanned by Flyway.

## Database Setup { #database-setup }

### Docker Compose { #docker-compose }

Create a `docker-compose.yml` file in the application module directory:

```yaml
version: '3.8'
services:
    postgres:
        image: postgres:17.6-alpine
        environment:
            POSTGRES_DB: postgres
            POSTGRES_USER: postgres
            POSTGRES_PASSWORD: postgres
        ports:
            - "5432:5432"
```

Start the database:

```bash
docker compose up -d
```

This will start PostgreSQL with:

- **Database**: `postgres`
- **Username**: `postgres`
- **Password**: `postgres`
- **Port**: `5432`

### Database Migration { #db-migration }

Use Flyway migrations instead of manual SQL execution.

Create `src/main/resources/db/migration/V1__init_users.sql`:

```sql
CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email)
VALUES ('John Doe', 'john@example.com'),
       ('Jane Smith', 'jane@example.com')
ON CONFLICT (email) DO NOTHING;
```

`BIGINT GENERATED ALWAYS AS IDENTITY` is the modern SQL-standard way to auto-generate ids in PostgreSQL.
Internally PostgreSQL still uses a sequence object, so repository `save(...)` can return generated `id` via `RETURNING id`, and service can build response DTO directly from request data + generated
id.

## Run Application { #run-app }

```bash
./gradlew run
```

## Check Application { #check-app }

**Get all users:**

```bash
curl http://localhost:8080/users
```

**Get user by ID:**

```bash
curl http://localhost:8080/users/1
```

**Create a new user:**

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Johnson", "email": "bob@example.com"}'
```

**Update a user:**

```bash
curl -X PUT http://localhost:8080/users/3 \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Smith", "email": "bob.smith@example.com"}'
```

**Delete a user:**

```bash
curl -X DELETE http://localhost:8080/users/3
```

## Best Practices { #best-practices }

- Keep SQL in repository methods and business decisions in the service layer.
- Use named parameters in queries instead of string concatenation.
- Add `@Column` to every DAO record component so database mappings stay explicit.
- Keep Flyway migrations versioned and committed with the code that depends on them.
- Use `RETURNING` for generated ids and update/delete counts for not-found decisions.
- Inspect generated repository implementations when SQL binding or row mapping is unclear.

## Summary { #summary }

You replaced the in-memory repository from the HTTP guide with a JDBC-backed repository, added PostgreSQL configuration, and introduced Flyway migrations for repeatable schema setup.

The HTTP contract stays stable while the persistence layer becomes production-like.
You also inspected generated JDBC code to see how Kora turns repository annotations into prepared statements, telemetry calls, and row mappers.

## Key Concepts { #key-concepts }

- how Kora JDBC repositories are declared
- how DAO records map columns explicitly with `@Column`
- how Flyway migrations initialize schema
- how service logic translates repository results into HTTP behavior
- how generated repository implementations execute SQL and map result rows

## Troubleshooting { #troubleshooting }

**Connection Issues:**

- Ensure PostgreSQL is running and reachable from your app.
- Verify `POSTGRES_JDBC_URL`, `POSTGRES_USER`, `POSTGRES_PASS` values.
- Ensure migration files exist in `src/main/resources/db/migration`.

**Compilation Errors:**

- Ensure JDBC and PostgreSQL dependencies are added.
- Ensure annotation processing is enabled for Kora.
- Verify Java version compatibility (17+).

**Runtime Errors:**

- Check Flyway logs and database connectivity.
- Verify table schema matches `UserDAO` column mappings.
- Review application logs for detailed SQL/HTTP error details.

## What's Next? { #whats-next }

- [Advanced JDBC Patterns](database-jdbc-advanced.md) to add a second table, transactions, custom mappers, macros, and projections.
- [Integration Testing](testing-integration.md) to verify JDBC repositories, migrations, and PostgreSQL behavior with Testcontainers.
- [Black Box Testing](testing-black-box.md) to validate the packaged HTTP application end to end.
- [Cassandra Database](database-cassandra.md) if you want to compare the same persistence lesson with a distributed database model.
- [Caching](cache.md) to speed up read-heavy database-backed operations.

## Help { #help }

If you encounter issues:

- compare with [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app) and [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-database-jdbc-app)
- check the [Database JDBC documentation](../documentation/database-jdbc.md)
- check the [Database Common documentation](../documentation/database-common.md)
- check the [Database Migration documentation](../documentation/database-migration.md)
