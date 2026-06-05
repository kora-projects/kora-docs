---
search:
  exclude: true
title: Cassandra Database Integration with Kora
summary: Learn how to integrate Cassandra-compatible storage with Kora and perform CRUD operations
tags: database, cassandra, scylla, cql, crud, persistence
---

# Cassandra Database Integration with Kora { #cassandra-database-integration-kora }

This guide introduces Cassandra-compatible persistence with Kora. It covers how repository interfaces use `@Repository` and `@Query`, how DAO records map to CQL rows, how Cassandra configuration
creates a session in the application graph, and how the same HTTP API shape can use a distributed wide-column database instead of in-memory storage.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Database Cassandra App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-cassandra-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Database Cassandra App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-database-cassandra-app).

## What You'll Build { #youll-build }

You will turn the user HTTP API into a Cassandra-backed application with:

- a CQL schema that creates a `users` table
- a Cassandra DAO model with `@EntityCassandra` and explicit column mapping
- a Kora `@Repository` interface with CQL queries for create, read, list, update, and delete operations
- service logic that preserves the HTTP guide behavior while respecting Cassandra mutation semantics
- HOCON configuration for Cassandra contact points, datacenter, keyspace, and credentials
- Scylla Testcontainers tests that verify persistence against a Cassandra-compatible database

## What You'll Need { #youll-need }

- JDK 17 or later
- Cassandra-compatible database, such as [Apache Cassandra](https://cassandra.apache.org/_/index.html) or [ScyllaDB](https://www.scylladb.com/)
- Docker for the integration tests
- Gradle 7+
- A text editor or IDE
- Completed [HTTP Server](http-server.md) guide

## Prerequisites { #prerequisites }

!!! note "Required: Complete HTTP Server Guide"

    This guide assumes you have completed the **[HTTP Server](http-server.md)** guide and have a working HTTP API project with `UserController`, `UserService`, and an in-memory repository implementation.

    If you have not completed the HTTP server guide yet, do that first, because this guide replaces the in-memory persistence with Cassandra-compatible storage.

## Overview { #overview }

Moving from in-memory storage to [Apache Cassandra](https://cassandra.apache.org/doc/latest/) changes the persistence layer without changing the public HTTP API contract. The controller can still
expose `/users`, the service can still return `UserResponse`, and the repository boundary becomes the place where application operations are translated into CQL.

Cassandra is not a relational database with SQL joins, foreign keys, sequences, and row-level update counts. It is a distributed wide-column database designed around partitioned access patterns, high
write throughput, tunable consistency, and horizontal scaling. That means the guide is not a mechanical JDBC rewrite. It keeps the same CRUD-shaped learning goal, but adapts the implementation to
Cassandra rules.

### How Persistence Changes the Application { #persistence-changes-application }

An in-memory repository is useful while learning HTTP controllers, but it disappears on restart, cannot be shared between application instances, and does not exercise real storage behavior.

A database-backed application introduces new concerns:

- records must survive application restarts
- schema must be created before repositories run
- queries must match the database access model
- configuration must point to different clusters in local, test, and deployed environments
- tests should verify real driver, query, and mapping behavior

This guide introduces the full persistence boundary: table schema, Cassandra session configuration, repository CQL, generated repository implementation, row mapping, and container-based tests.

### Cassandra as the Source of Truth { #cassandra-source-truth }

In this guide, Cassandra becomes the source of truth for user data. The repository no longer stores users in a local map; it reads and writes rows in a `users` table.

Cassandra data modeling starts from query patterns. A table is usually designed for the reads and writes the service needs, not for a normalized entity graph. This guide keeps the table intentionally
small:

- `id` is the partition key
- `name`, `email`, and `created_at` are regular columns
- reads by id are direct partition reads
- listing users is acceptable for a learning guide, but in production it should be designed around a bounded query pattern

That last point matters. `SELECT ... FROM users` is convenient in a small tutorial table, but production Cassandra systems usually avoid unbounded table scans.

### Cassandra Repositories { #cassandra-repositories }

[CQL](https://cassandra.apache.org/doc/latest/cassandra/developing/cql/) is the Cassandra Query Language. It looks familiar if you know SQL, but it follows Cassandra's storage model. Kora Cassandra
repositories keep CQL explicit while generating the driver boilerplate.

You declare a repository interface, annotate methods with `@Query`, and Kora generates an implementation that:

- prepares CQL statements
- binds named parameters to positional driver parameters
- executes statements through the configured Cassandra session
- applies telemetry around each query
- maps rows into Java records or Kotlin data classes

The explicit CQL stays visible in code review, while the repetitive driver code is generated.

### Entities and Row Mapping { #dao-models }

HTTP DTOs and database rows should stay separate. `UserRequest` and `UserResponse` describe API input and output. `UserDAO` describes the database row shape.

Because `UserRequest` and `UserResponse` are still HTTP JSON DTOs, the application keeps `@Json` on those classes. Cassandra mapping belongs on `UserDAO`; JSON mapping belongs on the request and
response DTOs that form the API boundary.

Kora maps Cassandra rows into typed Java records. `@EntityCassandra` asks Kora to generate Cassandra mappers for the DAO model directly, and `@Column` makes each CQL column name explicit. This is
useful when Java uses `createdAt` and the table uses `created_at`.

This guide uses `Instant` for `created_at` because Cassandra `timestamp` maps naturally to an instant in time.

### Cassandra Mutation Semantics { #cassandra-mutation-semantics }

JDBC updates often return an affected row count. Cassandra writes are different: `INSERT`, `UPDATE`, and `DELETE` are mutations and do not naturally behave like SQL update-count operations.

To keep the HTTP API behavior from the previous guide, the service checks existence with `findById(...)` before `update` and `delete`. That lets the API still return `404` for missing users, while the
repository methods remain idiomatic Cassandra mutations.

In a real system, you may choose another design:

- accept idempotent deletes
- use lightweight transactions for conditional writes when the consistency cost is justified
- model commands so the client already knows whether absence is an error

The guide keeps the behavior familiar so the storage differences are easier to see.

### Runtime Configuration { #runtime-config }

Kora wires Cassandra through `CassandraDatabaseModule`. The application graph owns the configured session, repositories depend on it, and tests override contact points and keyspace values with Scylla
Testcontainers.

The core settings are:

- contact points: where the driver connects
- datacenter: local DC used by the load-balancing policy
- keyspace: logical namespace for tables
- credentials: username and password when authentication is enabled
- request timeout: maximum time for a query attempt

Keeping these values outside code makes the same application runnable against local Scylla, test containers, staging Cassandra, or production clusters.

### Persistence Testing { #persistence-testing }

Mocks cannot prove that CQL syntax is valid, that a table exists, or that the generated Cassandra mapper reads the right columns.

The practical flow is:

1. add Cassandra and Scylla Testcontainers dependencies
2. add `CassandraDatabaseModule` to the Kora application
3. define the `users` table in CQL
4. define a Cassandra DAO with `@EntityCassandra`
5. create a Kora Cassandra repository with CQL queries
6. refactor the service to use Cassandra persistence
7. verify repository behavior with Scylla Testcontainers

## Dependencies { #dependencies }

Add Cassandra support and Scylla Testcontainers verification dependencies.

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:database-cassandra")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:database-cassandra")
    }
    ```

## Modules { #modules }

Update your Application interface to include the Cassandra module.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasecassandra/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.databasecassandra;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.database.cassandra.CassandraDatabaseModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            CassandraDatabaseModule,  // <----- Connected module
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/databasecassandra/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasecassandra

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.database.cassandra.CassandraDatabaseModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        CassandraDatabaseModule,  // <----- Connected module
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Database entity { #entity-db }

Replace the old in-memory storage model with a Cassandra DAO model used by repository mappings.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasecassandra/repository/UserDAO.java`:

    ```java
    package ru.tinkoff.kora.guide.databasecassandra.repository;

    import java.time.Instant;
    import ru.tinkoff.kora.database.cassandra.annotation.EntityCassandra;
    import ru.tinkoff.kora.database.common.annotation.Column;
    import ru.tinkoff.kora.database.common.annotation.Table;

    @EntityCassandra
    @Table("users")
    public record UserDAO(
            @Column("id") String id,
            @Column("name") String name,
            @Column("email") String email,
            @Column("created_at") Instant createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/databasecassandra/repository/UserDAO.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasecassandra.repository

    import java.time.Instant
    import ru.tinkoff.kora.database.cassandra.annotation.EntityCassandra
    import ru.tinkoff.kora.database.common.annotation.Column
    import ru.tinkoff.kora.database.common.annotation.Table

    @EntityCassandra
    @Table("users")
    data class UserDAO(
        @field:Column("id") val id: String,
        @field:Column("name") val name: String,
        @field:Column("email") val email: String,
        @field:Column("created_at") val createdAt: Instant,
    )
    ```

`@EntityCassandra` tells Kora to generate Cassandra row and result-set mappers for this DAO directly. That keeps mapper generation explicit and avoids slower late-generation rounds when the repository
graph first requests a mapper.

## Repository { #repository }

Remove the old `InMemoryUserRepository` from the HTTP server guide and create a Cassandra repository with CQL queries.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasecassandra/repository/UserRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.databasecassandra.repository;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.database.cassandra.CassandraRepository;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;

    @Repository
    public interface UserRepository extends CassandraRepository {

        @Query("SELECT id, name, email, created_at FROM users")
        List<UserDAO> findAll();

        @Query("SELECT id, name, email, created_at FROM users WHERE id = :id")
        @Nullable
        UserDAO findById(String id);

        @Query("""
                INSERT INTO users(id, name, email, created_at)
                VALUES (:user.id, :user.name, :user.email, :user.createdAt)
                """)
        void save(UserDAO user);

        @Query("""
                UPDATE users
                SET name = :user.name, email = :user.email, created_at = :user.createdAt
                WHERE id = :user.id
                """)
        void update(UserDAO user);

        @Query("DELETE FROM users WHERE id = :id")
        void deleteById(String id);
    }
    ```

After compilation, Kora generates the repository implementation and mappers:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-database-cassandra-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasecassandra/repository/$UserRepository_Impl.java
    guides/guide-database-cassandra-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasecassandra/repository/$UserDAO_CassandraRowMapper.java
    guides/guide-database-cassandra-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasecassandra/repository/$UserDAO_ListCassandraResultSetMapper.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-database-cassandra-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasecassandra/repository/$UserRepository_Impl.kt
    guides/kotlin/guide-kotlin-database-cassandra-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasecassandra/repository/$UserDAO_CassandraRowMapper.kt
    guides/kotlin/guide-kotlin-database-cassandra-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasecassandra/repository/$UserDAO_ListCassandraResultSetMapper.kt
    ```

This shortened generated repository excerpt shows how named CQL parameters become DataStax driver statement parameters:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static final QueryContext QUERY_CONTEXT_3 = new QueryContext(
          "INSERT INTO users(id, name, email, created_at)\n"
        + "VALUES (:user.id, :user.name, :user.email, :user.createdAt)\n",
          "INSERT INTO users(id, name, email, created_at)\n"
        + "VALUES (?, ?, ?, ?)\n",
          "UserRepository.save"
        );

    @Override
    public void save(UserDAO user) {
        var _query = QUERY_CONTEXT_3;
        var _ctxCurrent = Context.current();
        var _telemetry = this._connectionFactory.telemetry().createContext(_ctxCurrent, _query);
        var _session = this._connectionFactory.currentSession();
        var _stmt = _session.prepare(_query.sql()).boundStatementBuilder();
        _stmt.setString(0, user.id());
        _stmt.setString(1, user.name());
        _stmt.setString(2, user.email());
        _stmt.setInstant(3, user.createdAt());
        var _s = _stmt.build();
        try {
            var _rs = _session.execute(_s);
            _telemetry.close(null);
        } catch (Exception _e) {
            _telemetry.close(_e);
            throw _e;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val _queryContext_3: QueryContext = QueryContext(
      "INSERT INTO users(id, name, email, created_at) VALUES (:user.id, :user.name, :user.email, :user.createdAt)",
      "INSERT INTO users(id, name, email, created_at) VALUES (?, ?, ?, ?)",
      "UserRepository.save"
    )

    override fun save(user: UserDAO) {
      val _query = _queryContext_3
      val _ctxCurrent = Context.current()
      val _telemetry = this._cassandraConnectionFactory.telemetry().createContext(_ctxCurrent, _query)
      val _session = this._cassandraConnectionFactory.currentSession()
      var _stmt = _session.prepare(_query.sql()).boundStatementBuilder()
      _stmt.setString(0, user.id)
      _stmt.setString(1, user.name)
      _stmt.setString(2, user.email)
      _stmt.setInstant(3, user.createdAt)
      val _s = _stmt.build()
      try {
        _session.execute(_s)
        _telemetry.close(null)
      } catch (_e: Exception) {
        _telemetry.close(_e)
        throw _e
      }
    }
    ```

This shortened generated row mapper excerpt also shows why explicit column names matter:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var _idx_id = _row.firstIndexOf("id");
    var _idx_name = _row.firstIndexOf("name");
    var _idx_email = _row.firstIndexOf("email");
    var _idx_createdAt = _row.firstIndexOf("created_at");

    String id = _row.getString(_idx_id);
    String name = _row.getString(_idx_name);
    String email = _row.getString(_idx_email);
    Instant createdAt = _row.getInstant(_idx_createdAt);

    return new UserDAO(id, name, email, createdAt);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val _idx_id = _row.columnDefinitions.firstIndexOf("id")
    val _idx_name = _row.columnDefinitions.firstIndexOf("name")
    val _idx_email = _row.columnDefinitions.firstIndexOf("email")
    val _idx_createdAt = _row.columnDefinitions.firstIndexOf("created_at")

    var id: String? = _row.getString(_idx_id)
    if (_row.isNull(_idx_id) || id == null) {
      throw NullPointerException("Required field id is not nullable but row has null")
    }
    var name: String? = _row.getString(_idx_name)
    if (_row.isNull(_idx_name) || name == null) {
      throw NullPointerException("Required field name is not nullable but row has null")
    }
    var email: String? = _row.getString(_idx_email)
    if (_row.isNull(_idx_email) || email == null) {
      throw NullPointerException("Required field email is not nullable but row has null")
    }
    var createdAt: Instant? = _row.getInstant(_idx_createdAt)
    if (_row.isNull(_idx_createdAt) || createdAt == null) {
      throw NullPointerException("Required field created_at is not nullable but row has null")
    }

    val _result = UserDAO(id, name, email, createdAt)
    return _result
    ```

This is the best place to debug CQL binding and row mapping because it shows exactly what Kora compiled from `@Repository`, `@Query`, `@EntityCassandra`, and `@Column`.

## Refactor the Service { #refactor-service }

At this step, refactor the existing `UserService` from the HTTP server guide.

Important rules:

- Keep the same public service contracts used by `UserController`.
- Generate ids in the application because Cassandra does not use PostgreSQL-style `RETURNING id`.
- Check existence before update/delete if your HTTP API should return `404`.
- Keep `UserController` and its HTTP contracts unchanged.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/guide/databasecassandra/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.guide.databasecassandra.service;

    import java.time.Instant;
    import java.util.Comparator;
    import java.util.List;
    import java.util.Optional;
    import java.util.UUID;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.databasecassandra.dto.UserRequest;
    import ru.tinkoff.kora.guide.databasecassandra.dto.UserResponse;
    import ru.tinkoff.kora.guide.databasecassandra.repository.UserDAO;
    import ru.tinkoff.kora.guide.databasecassandra.repository.UserRepository;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;

    @Component
    public final class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        public UserResponse createUser(UserRequest request) {
            var user = new UserDAO(UUID.randomUUID().toString(), request.name(), request.email(), Instant.now());
            userRepository.save(user);
            return toResponse(user);
        }

        public Optional<UserResponse> getUser(String id) {
            return Optional.ofNullable(userRepository.findById(id)).map(this::toResponse);
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
            var existing = userRepository.findById(id);
            if (existing == null) {
                throw HttpServerResponseException.of(404, "User not found");
            }
            var updated = new UserDAO(id, request.name(), request.email(), existing.createdAt());
            userRepository.update(updated);
            return toResponse(updated);
        }

        public void deleteUser(String id) {
            if (userRepository.findById(id) == null) {
                throw HttpServerResponseException.of(404, "User not found");
            }
            userRepository.deleteById(id);
        }

        private UserResponse toResponse(UserDAO user) {
            return new UserResponse(user.id(), user.name(), user.email(), user.createdAt());
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

!!! note "Controller stays as-is"

    Do not rewrite `UserController` in this guide. Keep the controller from `http-server.md` unchanged, so only the repository implementation is replaced under the hood.

## Configuration { #configuration }

Create `src/main/resources/application.conf`:

For the full configuration reference, see [Database Cassandra](../documentation/database-cassandra.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    cassandra {
      auth {
        login = ${CASSANDRA_USER} //(1)!
        password = ${CASSANDRA_PASS} //(2)!
      }
      basic {
        contactPoints = ${CASSANDRA_CONTACT_POINTS} //(3)!
        dc = ${CASSANDRA_DC} //(4)!
        sessionKeyspace = ${CASSANDRA_KEYSPACE} //(5)!
        request {
          timeout = "5s" //(6)!
        }
      }
      telemetry.logging.enabled = true //(7)!
    }
    ```

    1. Login used by the Cassandra connection. Required value from `CASSANDRA_USER`.
    2. Database user password. Required value from `CASSANDRA_PASS`.
    3. Cassandra contact points used to open sessions. Required value from `CASSANDRA_CONTACT_POINTS`.
    4. Value for `cassandra.basic.dc`. Required value from `CASSANDRA_DC`.
    5. Value for `cassandra.basic.sessionKeyspace`. Required value from `CASSANDRA_KEYSPACE`.
    6. Value for `cassandra.basic.request.timeout`.
    7. Enables Cassandra client telemetry logging.

=== ":simple-yaml: `YAML`"

    ```yaml
    cassandra:
      auth:
        login: ${CASSANDRA_USER} #(1)!
        password: ${CASSANDRA_PASS} #(2)!
      basic:
        contactPoints: ${CASSANDRA_CONTACT_POINTS} #(3)!
        dc: ${CASSANDRA_DC} #(4)!
        sessionKeyspace: ${CASSANDRA_KEYSPACE} #(5)!
        request:
          timeout: "5s" #(6)!
      telemetry:
        logging:
          enabled: true #(7)!
    ```

    1. Login used by the Cassandra connection. Required value from `CASSANDRA_USER`.
    2. Database user password. Required value from `CASSANDRA_PASS`.
    3. Cassandra contact points used to open sessions. Required value from `CASSANDRA_CONTACT_POINTS`.
    4. Value for `cassandra.basic.dc`. Required value from `CASSANDRA_DC`.
    5. Value for `cassandra.basic.sessionKeyspace`. Required value from `CASSANDRA_KEYSPACE`.
    6. Value for `cassandra.basic.request.timeout`.
    7. Enables Cassandra client telemetry logging.

For local Scylla, typical values are:

```bash
export CASSANDRA_CONTACT_POINTS=127.0.0.1:9042
export CASSANDRA_USER=cassandra
export CASSANDRA_PASS=cassandra
export CASSANDRA_DC=datacenter1
export CASSANDRA_KEYSPACE=guide
```

## Database Setup { #database-setup }

### Docker Compose { #docker-compose }

Create a `docker-compose.yml` file in the application module directory:

```yaml
services:
  scylla:
    image: scylladb/scylla:2025.3
    command: ["--smp", "1", "--memory", "750M", "--overprovisioned", "1", "--developer-mode", "1"]
    ports:
      - "9042:9042"
```

Start the database:

```bash
docker compose up -d
```

Create a keyspace and table:

```sql
CREATE KEYSPACE IF NOT EXISTS guide
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS guide.users
(
    id         TEXT,
    name       TEXT,
    email      TEXT,
    created_at TIMESTAMP,
    PRIMARY KEY (id)
);
```

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
curl http://localhost:8080/users/{id}
```

**Create a new user:**

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Johnson", "email": "bob@example.com"}'
```

**Update a user:**

```bash
curl -X PUT http://localhost:8080/users/{id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Smith", "email": "bob.smith@example.com"}'
```

**Delete a user:**

```bash
curl -X DELETE http://localhost:8080/users/{id}
```

## Best Practices { #best-practices }

- Design Cassandra tables from query patterns, not from normalized relational models.
- Keep CQL in repository methods and business decisions in the service layer.
- Use `@EntityCassandra` on DAO models so Kora generates Cassandra mappers explicitly.
- Add `@Column` to every DAO record component so database mappings stay explicit.
- Avoid unbounded table scans in production; model list endpoints around bounded partitions or dedicated read tables.
- Treat Cassandra mutations as idempotent by default unless you deliberately use conditional writes.
- Use Scylla or Cassandra Testcontainers tests to verify CQL, schema, and generated mappers.
- Inspect generated repository implementations when CQL binding or row mapping is unclear.

## Summary { #summary }

You replaced the in-memory repository from the HTTP guide with a Cassandra-backed repository, added Cassandra configuration, created a CQL table, and verified persistence with Scylla Testcontainers.

The HTTP contract stays stable while the persistence layer becomes distributed and Cassandra-compatible. You also inspected generated Cassandra code to see how Kora turns repository annotations into
prepared statements, telemetry calls, and row mappers.

## Key Concepts { #key-concepts }

- how Kora Cassandra repositories are declared
- how DAO records use `@EntityCassandra` and `@Column`
- how Cassandra configuration creates a session in the application graph
- how Cassandra mutation semantics differ from JDBC update counts
- how generated repository implementations bind CQL parameters and map rows
- how Scylla Testcontainers verifies Cassandra-compatible persistence

## Troubleshooting { #troubleshooting }

**Connection Issues:**

- Ensure Cassandra or Scylla is running and reachable from your app.
- Verify `CASSANDRA_CONTACT_POINTS`, `CASSANDRA_USER`, `CASSANDRA_PASS`, `CASSANDRA_DC`, and `CASSANDRA_KEYSPACE`.
- Ensure the configured datacenter matches the running cluster.

**Schema Issues:**

- Ensure the keyspace exists before application startup.
- Ensure the `users` table exists in the configured keyspace.
- Verify CQL column names match `UserDAO` `@Column` mappings.

**Compilation Errors:**

- Ensure `ru.tinkoff.kora:database-cassandra` is added.
- Ensure annotation processing is enabled for Kora.
- Use `@EntityCassandra` for DAO models that repositories return.

**Runtime Query Errors:**

- Check that queries match Cassandra access rules.
- Avoid filtering or ordering patterns that Cassandra cannot execute without an appropriate table design.
- Review generated `$UserRepository_Impl.java` or `$UserRepository_Impl.kt` for exact parameter binding.

## What's Next? { #whats-next }

- [Caching](cache.md) to reduce repeated reads from Cassandra-compatible storage.
- [Observability](observability.md) to monitor database-backed request paths with metrics, traces, logs, and probes.
- [Database JDBC](database-jdbc.md) if you want to compare the same CRUD persistence lesson with relational SQL.
- [Messaging with Kafka](messaging-kafka.md) when database writes should also publish events.
- [Testing with JUnit](testing-junit.md) for component-level tests that do not assume the JDBC-specific testing guides.

## Help { #help }

If you encounter issues:

- compare with [Kora Java Database Cassandra App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-cassandra-app) and [Kora Kotlin Database Cassandra App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-database-cassandra-app)
- check the [Database Cassandra documentation](../documentation/database-cassandra.md)
- check the [Database Common documentation](../documentation/database-common.md)
- read the [Apache Cassandra documentation](https://cassandra.apache.org/doc/latest/)
- read the [ScyllaDB documentation](https://opensource.docs.scylladb.com/)
