---
search:
  exclude: true
title: Advanced JDBC with Kora
summary: Learn advanced Kora JDBC repository patterns with related tables, nullable foreign keys, entity macros, batch inserts, transactions, projections, and custom mappers
tags: database, jdbc, postgres, transactions, batch, macros
---

# Advanced JDBC with Kora { #advanced-jdbc-kora }

This guide extends the PostgreSQL-backed user API with task management. You will add a second table, insert tasks in batches, validate optional assignees, update task state, and then add a read
projection that joins tasks with users.

The main idea is that Kora JDBC repositories are SQL-first and projection-friendly. A repository is not locked to one entity class. One repository can use an insert model, scalar query results, update
counts, and several read projections, each chosen for a specific query. That keeps data access explicit and lets every SQL query select only the fields it really needs.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Database JDBC Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Database JDBC Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-database-jdbc-advanced-app).

## What You'll Build { #youll-build }

You will add task management to the JDBC application with:

- a `tasks` table with a nullable `user_assignee_id` foreign key to `users.id`
- a compact `TaskDAO` insert model
- custom JDBC mappers for `TaskStatus` and PostgreSQL `List<Long>` array parameters
- a `TaskRepository` that inserts batches, validates assignees, and updates task state
- an assigned-task projection that reuses `TaskDAO` and `UserDAO` with `@Embedded`
- request and response DTOs for the HTTP API
- a service layer that keeps validation and batch insert in one transaction

## What You'll Need { #youll-need }

- JDK 17 or later
- Docker or another local PostgreSQL instance
- Gradle 7+
- A text editor or IDE
- Completed [Database JDBC](database-jdbc.md) guide

## Prerequisites { #prerequisites }

!!! note "Required: Complete Database JDBC Guide"

    This guide assumes you have completed **[Database JDBC](database-jdbc.md)** and already have a working PostgreSQL-backed user API with `UserDAO`, `UserRepository`, Flyway migrations, JDBC configuration, and Kora database modules.

    If you have not completed the base JDBC guide yet, do that first. This guide keeps the existing `users` table and adds advanced repository behavior around a related `tasks` table.

## Overview { #overview }

The base JDBC guide uses one table and one repository. That is enough to learn connection configuration, Flyway migrations, `@Repository`, `@Query`, `@EntityJdbc`, and explicit column mapping. Real
applications quickly add related tables, and that is where several practical database questions appear:

- how should an optional relationship be represented in SQL and Java/Kotlin?
- when should an insert model differ from a read projection?
- how can entity macros reduce repetitive SQL while keeping queries visible?
- how do custom JDBC mappers become part of generated repository code?
- where should multi-step consistency checks run in one transaction?
- how do you pass many ids to PostgreSQL without building SQL strings manually?
- how can one repository expose several query-specific result shapes?

Kora's answer stays deliberately SQL-first. A task references a user through `user_assignee_id`, but `TaskDAO` does not become a lazy-loaded object graph. Insert operations use the compact task model.
Read operations that need assignee data use an explicit `JOIN` and a projection that reuses `TaskDAO` and `UserDAO`.

### `Nullable` Foreign Keys { #nullable-foreign-keys }

The `tasks.user_assignee_id` column is nullable. A task can be created before anybody owns it, then assigned later. When the value is present, PostgreSQL still enforces referential integrity:

```sql
user_assignee_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL
```

That nullability is visible in the schema, in the DAO model, and in the service rules. Optional relationships are common in production systems. Keeping them as explicit database columns makes the
behavior easy to reason about, test, and optimize.

### Repository for Everything { #repository-everything }

In many frameworks, the repository pattern is often taught as "one repository for one entity". That can lead to extra repositories or duplicated model classes whenever a query needs a slightly
different shape. Kora JDBC does not force that structure.

A Kora repository method can return:

- a scalar value such as `Long`
- an `UpdateCount`
- a base entity such as `TaskDAO`
- a nested projection such as `TaskDAO.SelectAssigned`
- a list of any of those shapes

That means one repository can stay close to a database area while still exposing query-specific projections. You can select only the fields required by the current use case instead of loading a full
object graph. That improves performance, keeps SQL intentional, and avoids creating a separate repository for every projection.

### Repository Macros { #repository-macros }

Kora Database Common annotations describe how application types map to database columns. JDBC repositories can use that metadata through macros such as `%{entity#inserts}`. This guide first writes the
insert SQL explicitly, then replaces the repetitive insert fragment with the final macro form:

```java

@Query("INSERT INTO %{entity#inserts} RETURNING id")
@Id
List<Long> insert(@Batch List<TaskDAO> entity);
```

The macro is expanded by Kora's annotation processor during compilation. It is not a runtime SQL builder. The generated repository still contains explicit SQL, so you can inspect exactly what will
run.

### Custom Type Mappers { #custom-type-mappers }

JDBC does not know how your domain enum should be represented in the database, and it does not know how a Java/Kotlin `List<Long>` should become a PostgreSQL array. The application provides focused
Kora components:

- `JdbcResultColumnMapper<TaskStatus>` for reading `TaskStatus`
- `JdbcParameterColumnMapper<TaskStatus>` for binding `TaskStatus`
- `JdbcParameterColumnMapper<List<Long>>` for binding PostgreSQL arrays

Because these mappers are components and their generic signatures match repository fields and parameters, Kora can resolve them by type. You do not need to repeat explicit mapper annotations on
every `TaskStatus` parameter.

### Batch Inserts and Transactions { #batch-inserts-transactions }

The detailed `@Batch` and transaction rules are covered in [Batch query](../documentation/database-common.md#batch-query) and [JDBC Transaction](../documentation/database-jdbc.md#transaction).

Batch inserts and transactions solve different problems. `@Batch` reduces repeated JDBC boilerplate when one SQL statement is executed for many entities. `inTx(...)` makes several repository calls use
the same database transaction.

This guide combines both:

1. collect distinct assignee ids from the request
2. query existing user ids with `ANY(:assigneeIds)`
3. fail before insert if any assignee is missing
4. insert all task rows as one batch

If validation fails, no task rows are created. If the insert fails, the transaction rolls back.

### Specific Mappers { #specific-mappers }

PostgreSQL can compare a value against a SQL array with `ANY(:assigneeIds)`. A custom `List<Long>` mapper converts the application list into a PostgreSQL `BIGINT` array. This keeps the query stable
regardless of list size and avoids unsafe string concatenation such as `WHERE id IN (...)` assembled manually.

## Dependencies { #dependencies }

The base JDBC guide already adds the main database dependencies. Keep those dependencies for PostgreSQL, Flyway migrations, and Kora JDBC repositories.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        runtimeOnly("org.postgresql:postgresql:42.7.7")

        implementation("ru.tinkoff.kora:database-flyway")
        implementation("ru.tinkoff.kora:database-jdbc")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        runtimeOnly("org.postgresql:postgresql:42.7.7")

        implementation("ru.tinkoff.kora:database-flyway")
        implementation("ru.tinkoff.kora:database-jdbc")
    }
    ```

`database-jdbc` provides the repository infrastructure and connection factory. `database-flyway` applies schema migrations before repositories are used. The PostgreSQL driver lets the application
connect to the database.

## Modules { #modules }

Make sure the application interface includes the JDBC and Flyway modules. The HTTP, JSON, configuration, and logging modules remain from previous guides.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced;

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

    Update `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced

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

Repositories do not create database infrastructure themselves. They depend on the `JdbcDatabaseModule` graph components. Flyway is also part of the graph, so migrations run before the application
starts serving requests.

## New Entity { #new-entity }

Start with the simplest database model: a task row as the application writes it. Do not add read projections yet. At this point we only need the columns that are supplied during insert.

`TaskDAO` stores task state as a `TaskStatus` enum, so create that shared type first. It lives in the task DTO package because the HTTP API will also use the same enum later, but the full request and
response DTOs are introduced after the repository design is finished.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskStatus.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public enum TaskStatus {
        TODO,
        IN_PROGRESS,
        DONE
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskStatus.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    enum class TaskStatus {
        TODO,
        IN_PROGRESS,
        DONE
    }
    ```

`@Json` is useful immediately because `TaskStatus` will appear in HTTP request and response DTOs. Annotating it now also prevents late JSON mapper generation warnings later.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskDAO.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository;

    import jakarta.annotation.Nullable;
    import ru.tinkoff.kora.database.common.annotation.Column;
    import ru.tinkoff.kora.database.common.annotation.Table;
    import ru.tinkoff.kora.database.jdbc.EntityJdbc;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @EntityJdbc
    @Table("tasks")
    public record TaskDAO(
            @Column("title") String title,
            @Column("status") TaskStatus status,
            @Column("description") @Nullable String description,
            @Column("user_assignee_id") @Nullable Long userAssigneeId) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskDAO.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository

    import ru.tinkoff.kora.database.common.annotation.Column
    import ru.tinkoff.kora.database.common.annotation.Table
    import ru.tinkoff.kora.database.jdbc.EntityJdbc
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @EntityJdbc
    @Table("tasks")
    data class TaskDAO(
        @field:Column("title") val title: String,
        @field:Column("status") val status: TaskStatus,
        @field:Column("description") val description: String?,
        @field:Column("user_assignee_id") val userAssigneeId: Long?
    )
    ```

`@EntityJdbc` tells Kora to generate JDBC mappers for this model. `@Table("tasks")` gives macros a table name. `@Column` keeps database column names explicit, especially where Java/Kotlin names and
SQL names differ. `description` and `userAssigneeId` are nullable because the SQL columns are optional.

## New Database Migration { #new-database-migration }

Now create the database table that matches `TaskDAO`. The base JDBC guide already created `V1__init_users.sql`, so this guide adds `V2__init_tasks.sql`.

```sql title="src/main/resources/db/migration/V2__init_tasks.sql"
CREATE TABLE IF NOT EXISTS tasks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL,
    user_assignee_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_assignee_id ON tasks(user_assignee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
```

The migration is the contract between SQL and repository code. `TaskDAO` describes the writable part of the row, while the table also contains database-managed fields such as `id`, `created_at`,
and `updated_at`. Those fields will become useful later when we add read projections.

## JDBC Mappers { #jdbc-mappers }

For the full mapper selection rules for `JdbcResultColumnMapper` and `JdbcParameterColumnMapper`, see [JDBC Mapping](../documentation/database-jdbc.md#mapping).

The database stores `TaskStatus` as text. JDBC can read a `String`, but it cannot infer how your enum should be converted. Add one mapper for reading and one mapper for binding.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/TaskStatusResultMapper.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper;

    import java.sql.ResultSet;
    import java.sql.SQLException;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.database.jdbc.mapper.result.JdbcResultColumnMapper;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @Component
    public final class TaskStatusResultMapper implements JdbcResultColumnMapper<TaskStatus> {

        @Override
        public TaskStatus apply(ResultSet row, int index) throws SQLException {
            var value = row.getString(index);
            return value == null ? null : TaskStatus.valueOf(value);
        }
    }
    ```

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/TaskStatusParameterMapper.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper;

    import java.sql.PreparedStatement;
    import java.sql.SQLException;
    import java.sql.Types;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.database.jdbc.mapper.parameter.JdbcParameterColumnMapper;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @Component
    public final class TaskStatusParameterMapper implements JdbcParameterColumnMapper<TaskStatus> {

        @Override
        public void set(PreparedStatement stmt, int index, TaskStatus value) throws SQLException {
            if (value == null) {
                stmt.setNull(index, Types.VARCHAR);
            } else {
                stmt.setString(index, value.name());
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/TaskStatusResultMapper.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper

    import java.sql.ResultSet
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.database.jdbc.mapper.result.JdbcResultColumnMapper
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @Component
    class TaskStatusResultMapper : JdbcResultColumnMapper<TaskStatus> {

        override fun apply(row: ResultSet, index: Int): TaskStatus {
            val value = row.getString(index)
            return TaskStatus.valueOf(value)
        }
    }
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/TaskStatusParameterMapper.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper

    import java.sql.PreparedStatement
    import java.sql.Types
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.database.jdbc.mapper.parameter.JdbcParameterColumnMapper
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @Component
    class TaskStatusParameterMapper : JdbcParameterColumnMapper<TaskStatus?> {

        override fun set(stmt: PreparedStatement, index: Int, value: TaskStatus?) {
            if (value == null) {
                stmt.setNull(index, Types.VARCHAR)
            } else {
                stmt.setString(index, value.name)
            }
        }
    }
    ```

Kora finds these mappers by their generic signatures. The repository can use `TaskStatus` directly, and the generated implementation injects the matching mapper where it is needed. That is why the
repository methods below do not need repeated explicit mapper annotations for every `TaskStatus` parameter.

## PostgreSQL Mapper { #postgresql-mapper }

For more on passing lists and arrays into queries, see [Select by list](../documentation/database-jdbc.md#select-by-list) and [JDBC Mapping](../documentation/database-jdbc.md#mapping).

The repository will accept a list of assignee ids and use `ANY(:assigneeIds)` in SQL. JDBC needs help turning `List<Long>` into a PostgreSQL array.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/ListOfLongJdbcParameterMapper.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper;

    import java.sql.PreparedStatement;
    import java.sql.SQLException;
    import java.sql.Types;
    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.database.jdbc.mapper.parameter.JdbcParameterColumnMapper;

    @Component
    public final class ListOfLongJdbcParameterMapper implements JdbcParameterColumnMapper<List<Long>> {

        @Override
        public void set(PreparedStatement stmt, int index, List<Long> value) throws SQLException {
            if (value == null) {
                stmt.setNull(index, Types.ARRAY);
                return;
            }

            var sqlArray = stmt.getConnection().createArrayOf("BIGINT", value.toArray(Long[]::new));
            stmt.setArray(index, sqlArray);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/ListOfLongJdbcParameterMapper.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper

    import java.sql.PreparedStatement
    import java.sql.Types
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.database.jdbc.mapper.parameter.JdbcParameterColumnMapper

    @Component
    class ListOfLongJdbcParameterMapper : JdbcParameterColumnMapper<List<Long>> {

        override fun set(stmt: PreparedStatement, index: Int, value: List<Long>) {
            val sqlArray = stmt.connection.createArrayOf("BIGINT", value.toTypedArray())
            stmt.setArray(index, sqlArray)
        }
    }
    ```

The mapper is small, but it keeps array conversion centralized. Repository methods stay declarative, while the generated implementation delegates binding to this component.

## New Repository { #new-repository }

Now create the first repository version. At this point it does not yet read assigned task projections. It only contains the operations needed to validate assignees, insert tasks in batches, and update
state.

Start with explicit SQL. This makes the binding model visible: every inserted column is listed by hand, and every value comes from a `TaskDAO` property through `:entity.propertyName`.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.database.common.UpdateCount;
    import ru.tinkoff.kora.database.common.annotation.Batch;
    import ru.tinkoff.kora.database.common.annotation.Id;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;
    import ru.tinkoff.kora.database.jdbc.JdbcRepository;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @Repository
    public interface TaskRepository extends JdbcRepository {

        @Query("SELECT id FROM users WHERE id = ANY(:assigneeIds)")
        List<Long> findExistingAssigneeId(List<Long> assigneeIds);

        @Query("""
                INSERT INTO tasks(title, status, description, user_assignee_id)
                VALUES (:entity.title, :entity.status, :entity.description, :entity.userAssigneeId)
                RETURNING id
                """)
        @Id
        List<Long> insert(@Batch List<TaskDAO> entity);

        @Query("""
                UPDATE tasks
                SET status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """)
        UpdateCount updateStatus(long id, TaskStatus status);

        @Query("""
                UPDATE tasks
                SET user_assignee_id = :userAssigneeId, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """)
        UpdateCount updateAssignee(long id, @Nullable Long userAssigneeId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskRepository.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository

    import ru.tinkoff.kora.database.common.UpdateCount
    import ru.tinkoff.kora.database.common.annotation.Batch
    import ru.tinkoff.kora.database.common.annotation.Id
    import ru.tinkoff.kora.database.common.annotation.Query
    import ru.tinkoff.kora.database.common.annotation.Repository
    import ru.tinkoff.kora.database.jdbc.JdbcRepository
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @Repository
    interface TaskRepository : JdbcRepository {

        @Query("SELECT id FROM users WHERE id = ANY(:assigneeIds)")
        fun findExistingAssigneeId(assigneeIds: List<Long>): List<Long>

        @Query(
            """
            INSERT INTO tasks(title, status, description, user_assignee_id)
            VALUES (:entity.title, :entity.status, :entity.description, :entity.userAssigneeId)
            RETURNING id
            """
        )
        @Id
        fun insert(@Batch entity: List<TaskDAO>): List<Long>

        @Query(
            """
            UPDATE tasks
            SET status = :status, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        )
        fun updateStatus(id: Long, status: TaskStatus): UpdateCount

        @Query(
            """
            UPDATE tasks
            SET user_assignee_id = :userAssigneeId, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        )
        fun updateAssignee(id: Long, userAssigneeId: Long?): UpdateCount
    }
    ```

This repository is already valid. It uses plain SQL everywhere, and that is often the best way to introduce a new query because the table, columns, and parameters are fully visible.

There are already three advanced patterns here:

- `findExistingAssigneeId(...)` uses PostgreSQL `ANY(:assigneeIds)` and the list mapper.
- `insert(...)` uses `:entity.title`, `:entity.status`, `:entity.description`, and `:entity.userAssigneeId` to bind fields from each batched `TaskDAO`.
- `@Batch List<TaskDAO>` makes Kora generate repeated parameter binding and `addBatch()` calls.

The tradeoff is duplication. The insert query repeats information already present in `TaskDAO`:

- `@Table("tasks")` already names the table.
- `@Column("title")`, `@Column("status")`, `@Column("description")`, and `@Column("user_assignee_id")` already name the columns.
- the record properties already provide the parameter paths.

Keep this version in mind. The next chapter replaces the repetitive insert SQL with a macro while keeping the rest of the repository explicit.

## New Repository with Macros { #new-repository-macros }

For the full macro syntax, commands such as `%{entity#inserts}`, and `@Batch` limits, see [Macros](../documentation/database-common.md#macros) and [Batch query](../documentation/database-common.md#batch-query).

Kora Database Common macros are compile-time SQL helpers. They do not hide the database behind an ORM and they do not create runtime query builders. A macro expands entity metadata into SQL text
during annotation processing.

Use a macro where the SQL fragment is mechanically derived from one model. In this repository, the insert statement is a good fit because it inserts all fields from `TaskDAO` into the table described
by `@Table("tasks")`.

Do not force macros into every query. `findExistingAssigneeId(...)` returns scalar `Long` ids from the existing `users` table, not a `UserDAO` projection, so
keeping `SELECT id FROM users WHERE id = ANY(:assigneeIds)` explicit is clearer. The update methods also intentionally set only selected columns and `updated_at`, so plain SQL communicates the
behavior better.

Update only the `insert(...)` method:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.database.common.UpdateCount;
    import ru.tinkoff.kora.database.common.annotation.Batch;
    import ru.tinkoff.kora.database.common.annotation.Id;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;
    import ru.tinkoff.kora.database.jdbc.JdbcRepository;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @Repository
    public interface TaskRepository extends JdbcRepository {

        @Query("SELECT id FROM users WHERE id = ANY(:assigneeIds)")
        List<Long> findExistingAssigneeId(List<Long> assigneeIds);

        @Query("INSERT INTO %{entity#inserts} RETURNING id")
        @Id
        List<Long> insert(@Batch List<TaskDAO> entity);

        @Query("""
                UPDATE tasks
                SET status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """)
        UpdateCount updateStatus(long id, TaskStatus status);

        @Query("""
                UPDATE tasks
                SET user_assignee_id = :userAssigneeId, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """)
        UpdateCount updateAssignee(long id, @Nullable Long userAssigneeId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskRepository.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository

    import ru.tinkoff.kora.database.common.UpdateCount
    import ru.tinkoff.kora.database.common.annotation.Batch
    import ru.tinkoff.kora.database.common.annotation.Id
    import ru.tinkoff.kora.database.common.annotation.Query
    import ru.tinkoff.kora.database.common.annotation.Repository
    import ru.tinkoff.kora.database.jdbc.JdbcRepository
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @Repository
    interface TaskRepository : JdbcRepository {

        @Query("SELECT id FROM users WHERE id = ANY(:assigneeIds)")
        fun findExistingAssigneeId(assigneeIds: List<Long>): List<Long>

        @Query("INSERT INTO %{entity#inserts} RETURNING id")
        @Id
        fun insert(@Batch entity: List<TaskDAO>): List<Long>

        @Query(
            """
            UPDATE tasks
            SET status = :status, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        )
        fun updateStatus(id: Long, status: TaskStatus): UpdateCount

        @Query(
            """
            UPDATE tasks
            SET user_assignee_id = :userAssigneeId, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        )
        fun updateAssignee(id: Long, userAssigneeId: Long?): UpdateCount
    }
    ```

`%{entity#inserts}` asks Kora to expand the insert table, column list, and value bindings from the `TaskDAO` metadata. The benefit is not shorter code for its own sake. The benefit is that the column
mapping has one source of truth: if a column name changes in `TaskDAO`, the insert macro follows that mapping during annotation processing. You also do not have to manually keep the insert query
synchronized with the model field by field. The macro works with all fields described by the model metadata, so the main responsibility is to keep `TaskDAO` itself aligned with the database schema.
Complex joins and carefully shaped read queries should usually stay explicit, but repetitive entity insert fragments are a good fit for macros.

This shortened generated repository excerpt shows the macro expansion:

```java
private static final QueryContext QUERY_CONTEXT_2 = new QueryContext(
    "INSERT INTO tasks(title, status, description, user_assignee_id) VALUES (:entity.title, :entity.status, :entity.description, :entity.userAssigneeId) RETURNING id",
    "INSERT INTO tasks(title, status, description, user_assignee_id) VALUES (?, ?, ?, ?) RETURNING id",
    "TaskRepository.insert"
);
```

It also shows exactly how Kora implements the batch insert and generated keys:

```java
try(_conToClose;
var _stmt = _conToUse.prepareStatement(_query.sql(), Statement.RETURN_GENERATED_KEYS)){
    for(
var _i :entity){
    _stmt.

setString(1,_i.title());
    _parameter_mapper_2.

set(_stmt, 2,_i.status());
    if(_i.

description() !=null){
    _stmt.

setString(3,_i.description());
    }else{
    _stmt.

setNull(3,Types.VARCHAR);
    }
        if(_i.

userAssigneeId() !=null){
    _stmt.

setLong(4,_i.userAssigneeId());
    }else{
    _stmt.

setNull(4,Types.BIGINT);
    }
        _stmt.

addBatch();
  }
var _batchResult = _stmt.executeBatch();
  try(
var _rs = _stmt.getGeneratedKeys()){
var _result = _result_mapper_1.apply(_rs);
    return Objects.

requireNonNull(_result, "Result mapping is expected non-null, but was null");
  }
      }
```

This generated-code checkpoint makes the framework behavior inspectable: null binding, enum mapper usage, batch execution, generated key extraction, and connection handling are all visible.

## New Projection { #new-projection }

So far `TaskDAO` is an insert model. It does not contain `id`, `created_at`, `updated_at`, or assignee details. That is good for writes, but it is not enough for the query "find tasks assigned to
these users".

For that query, the result shape is different from `TaskDAO`. You have two common options.

### Option 1: Separate Projection { #option-1-separate-projection }

You could create a completely separate `TaskSelectDAO` and duplicate every selected field:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @EntityJdbc
    public record TaskSelectDAO(
            @Column("task_id") Long id,
            @Column("title") String title,
            @Column("status") TaskStatus status,
            @Nullable @Column("description") String description,
            @Nullable @Column("user_assignee_id") Long userAssigneeId,
            @Column("updated_at") LocalDateTime updatedAt,
            @Column("assignee_id") Long assigneeId,
            @Column("assignee_name") String assigneeName,
            @Column("assignee_email") String assigneeEmail) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @EntityJdbc
    data class TaskSelectDAO(
        @field:Column("task_id") val id: Long,
        @field:Column("title") val title: String,
        @field:Column("status") val status: TaskStatus,
        @field:Column("description") val description: String?,
        @field:Column("user_assignee_id") val userAssigneeId: Long?,
        @field:Column("updated_at") val updatedAt: LocalDateTime,
        @field:Column("assignee_id") val assigneeId: Long,
        @field:Column("assignee_name") val assigneeName: String,
        @field:Column("assignee_email") val assigneeEmail: String
    )
    ```

This is sometimes useful when a query result is truly independent. The downside is duplication: task fields already exist in `TaskDAO`, and user fields already exist in `UserDAO`.

### Option 2: Through `@Embedded` { #option-2-through-embedded }

For more on prefixes, SQL aliases, and nested fields, see [`@Embedded` and embedded fields](../documentation/database-common.md#embedded-fields).

In this guide, use a nested projection inside `TaskDAO`. It reuses `TaskDAO` for task fields and `UserDAO` from the base JDBC guide for assignee fields.

===! ":fontawesome-brands-java: `Java`"

    Update `TaskDAO.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository;

    import jakarta.annotation.Nullable;
    import java.time.LocalDateTime;
    import ru.tinkoff.kora.database.common.annotation.Column;
    import ru.tinkoff.kora.database.common.annotation.Embedded;
    import ru.tinkoff.kora.database.common.annotation.Id;
    import ru.tinkoff.kora.database.common.annotation.Table;
    import ru.tinkoff.kora.database.jdbc.EntityJdbc;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.repository.UserDAO;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @EntityJdbc
    @Table("tasks")
    public record TaskDAO(
            @Column("title") String title,
            @Column("status") TaskStatus status,
            @Column("description") @Nullable String description,
            @Column("user_assignee_id") @Nullable Long userAssigneeId) {

        @EntityJdbc
        public record SelectAssigned(
                @Column("task_id") @Id Long id,
                @Column("created_at") LocalDateTime createdAt,
                @Column("updated_at") LocalDateTime updatedAt,
                @Embedded("assignee_") UserDAO assigned,
                @Embedded TaskDAO base) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `TaskDAO.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository

    import java.time.LocalDateTime
    import ru.tinkoff.kora.database.common.annotation.Column
    import ru.tinkoff.kora.database.common.annotation.Embedded
    import ru.tinkoff.kora.database.common.annotation.Id
    import ru.tinkoff.kora.database.common.annotation.Table
    import ru.tinkoff.kora.database.jdbc.EntityJdbc
    import ru.tinkoff.kora.guide.databasejdbc.advanced.repository.UserDAO
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @EntityJdbc
    @Table("tasks")
    data class TaskDAO(
        @field:Column("title") val title: String,
        @field:Column("status") val status: TaskStatus,
        @field:Column("description") val description: String?,
        @field:Column("user_assignee_id") val userAssigneeId: Long?
    ) {
        @EntityJdbc
        data class SelectAssigned(
            @field:Column("task_id") @field:Id val id: Long,
            @field:Column("created_at") val createdAt: LocalDateTime,
            @field:Column("updated_at") val updatedAt: LocalDateTime,
            @field:Embedded("assignee_") val assigned: UserDAO,
            @field:Embedded val base: TaskDAO
        )
    }
    ```

This shape is compact but expressive:

- `base` reuses the insert model fields: `title`, `status`, `description`, `user_assignee_id`.
- `assigned` reuses the existing `UserDAO`.
- `@Embedded("assignee_")` maps SQL aliases like `assignee_id` into `UserDAO` fields annotated as `id`, `name`, `email`, and `created_at`.
- the repository can still return `List<TaskDAO.SelectAssigned>` from the same `TaskRepository`.

This is the important Kora pattern: a repository is not bound to a single result model. Use whatever projection matches the query. You can compose projections, reuse existing DAO pieces, and select
only the fields needed by the endpoint. That avoids loading unnecessary columns and avoids creating a separate repository for every view of the data, which is common pressure in repository patterns
from frameworks such as Spring or Micronaut.

Now add the projection query to the same repository:

===! ":fontawesome-brands-java: `Java`"

    Update `TaskRepository.java`:

    ```java
    @Query("""
            SELECT
              t.id AS task_id,
              t.created_at,
              t.updated_at,
              u.id AS assignee_id,
              u.name AS assignee_name,
              u.email AS assignee_email,
              u.created_at AS assignee_created_at,
              t.title,
              t.status,
              t.description,
              t.user_assignee_id
            FROM tasks t
            JOIN users u ON u.id = t.user_assignee_id
            WHERE t.user_assignee_id = ANY(:assigneeIds)
            ORDER BY t.id
            """)
    List<TaskDAO.SelectAssigned> findAssignedByAssigneeIds(List<Long> assigneeIds);
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `TaskRepository.kt`:

    ```kotlin
    @Query(
        """
        SELECT
          t.id AS task_id,
          t.created_at,
          t.updated_at,
          u.id AS assignee_id,
          u.name AS assignee_name,
          u.email AS assignee_email,
          u.created_at AS assignee_created_at,
          t.title,
          t.status,
          t.description,
          t.user_assignee_id
        FROM tasks t
        JOIN users u ON u.id = t.user_assignee_id
        WHERE t.user_assignee_id = ANY(:assigneeIds)
        ORDER BY t.id
        """
    )
    fun findAssignedByAssigneeIds(assigneeIds: List<Long>): List<TaskDAO.SelectAssigned>
    ```

The query selects only the columns required to build the assigned-task response. It does not load all user fields unless the response needs them, and it does not pretend that `TaskDAO` owns a lazy
user object. SQL stays honest, and the projection stays typed.

After compilation, Kora generates a row mapper for this projection:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-database-jdbc-advanced-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/$TaskDAO_SelectAssigned_JdbcRowMapper.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-database-jdbc-advanced-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/$TaskDAO_SelectAssigned_JdbcRowMapper.kt
    ```

The generated mapper shows how Kora applies the prefix, reads aliased columns, applies the enum mapper, handles nullable fields, and assembles nested objects:

??? example "Generated JDBC mapper"

    ===! ":fontawesome-brands-java: `Java`"

        ```java
        var _assigned_idColumn = _rs.findColumn("assignee_id");
        var _assigned_nameColumn = _rs.findColumn("assignee_name");
        var _assigned_emailColumn = _rs.findColumn("assignee_email");
        var _assigned_createdAtColumn = _rs.findColumn("assignee_created_at");
        var _base_titleColumn = _rs.findColumn("title");
        var _base_statusColumn = _rs.findColumn("status");
        var _base_descriptionColumn = _rs.findColumn("description");
        var _base_userAssigneeIdColumn = _rs.findColumn("user_assignee_id");

        Long id = _rs.getLong(_idColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field id is not nullable but row task_id has null");
        }
        LocalDateTime createdAt = _rs.getObject(_createdAtColumn, LocalDateTime.class);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field createdAt is not nullable but row created_at has null");
        }
        LocalDateTime updatedAt = _rs.getObject(_updatedAtColumn, LocalDateTime.class);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field updatedAt is not nullable but row updated_at has null");
        }
        Long assigned_id = _rs.getLong(_assigned_idColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field assigned_id is not nullable but row assignee_id has null");
        }
        String assigned_name = _rs.getString(_assigned_nameColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field assigned_name is not nullable but row assignee_name has null");
        }
        String assigned_email = _rs.getString(_assigned_emailColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field assigned_email is not nullable but row assignee_email has null");
        }
        LocalDateTime assigned_createdAt = _rs.getObject(_assigned_createdAtColumn, LocalDateTime.class);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field assigned_createdAt is not nullable but row assignee_created_at has null");
        }
        String base_title = _rs.getString(_base_titleColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field base_title is not nullable but row title has null");
        }
        TaskStatus base_status = this._base_statusMapper.apply(_rs, _base_statusColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field base_status is not nullable but row status has null");
        }
        String base_description = _rs.getString(_base_descriptionColumn);
        if (_rs.wasNull()) {
          base_description = null;
        }
        Long base_userAssigneeId = _rs.getLong(_base_userAssigneeIdColumn);
        if (_rs.wasNull()) {
          base_userAssigneeId = null;
        }

        UserDAO assigned = new UserDAO(assigned_id, assigned_name, assigned_email, assigned_createdAt);
        TaskDAO base = new TaskDAO(base_title, base_status, base_description, base_userAssigneeId);
        var _result = new TaskDAO.SelectAssigned(id, createdAt, updatedAt, assigned, base);
        ```

    === ":simple-kotlin: `Kotlin`"

        ```kotlin
        val _idx_assigned_id = _rs.findColumn("assignee_id")
        val _idx_assigned_name = _rs.findColumn("assignee_name")
        val _idx_assigned_email = _rs.findColumn("assignee_email")
        val _idx_assigned_createdAt = _rs.findColumn("assignee_created_at")
        val _idx_base_title = _rs.findColumn("title")
        val _idx_base_status = _rs.findColumn("status")
        val _idx_base_description = _rs.findColumn("description")
        val _idx_base_userAssigneeId = _rs.findColumn("user_assignee_id")

        var id: Long? = _rs.getLong(_idx_id)
        if (_rs.wasNull() || id == null) {
          throw NullPointerException("Required field task_id is not nullable but row has null")
        }
        var createdAt: LocalDateTime? = _rs.getObject(_idx_createdAt, LocalDateTime::class.java)
        if (_rs.wasNull() || createdAt == null) {
          throw NullPointerException("Required field created_at is not nullable but row has null")
        }
        var updatedAt: LocalDateTime? = _rs.getObject(_idx_updatedAt, LocalDateTime::class.java)
        if (_rs.wasNull() || updatedAt == null) {
          throw NullPointerException("Required field updated_at is not nullable but row has null")
        }
        var assigned_id: Long? = _rs.getLong(_idx_assigned_id)
        if (_rs.wasNull() || assigned_id == null) {
          throw NullPointerException("Required field assignee_id is not nullable but row has null")
        }
        var assigned_name: String? = _rs.getString(_idx_assigned_name)
        if (_rs.wasNull() || assigned_name == null) {
          throw NullPointerException("Required field assignee_name is not nullable but row has null")
        }
        var assigned_email: String? = _rs.getString(_idx_assigned_email)
        if (_rs.wasNull() || assigned_email == null) {
          throw NullPointerException("Required field assignee_email is not nullable but row has null")
        }
        var assigned_createdAt: LocalDateTime? = _rs.getObject(_idx_assigned_createdAt, LocalDateTime::class.java)
        if (_rs.wasNull() || assigned_createdAt == null) {
          throw NullPointerException("Required field assignee_created_at is not nullable but row has null")
        }
        var base_title: String? = _rs.getString(_idx_base_title)
        if (_rs.wasNull() || base_title == null) {
          throw NullPointerException("Required field title is not nullable but row has null")
        }
        var base_status: TaskStatus? = `$base_statusMapper`.apply(_rs, _idx_base_status)
        if (_rs.wasNull() || base_status == null) {
          throw NullPointerException("Required field status is not nullable but row has null")
        }
        var base_description: String? = _rs.getString(_idx_base_description)
        if (_rs.wasNull() || base_description == null) {
          base_description = null
        }
        var base_userAssigneeId: Long? = _rs.getLong(_idx_base_userAssigneeId)
        if (_rs.wasNull() || base_userAssigneeId == null) {
          base_userAssigneeId = null
        }

        val assigned = UserDAO(assigned_id, assigned_name, assigned_email, assigned_createdAt)
        val base = TaskDAO(base_title, base_status, base_description, base_userAssigneeId)
        val _result = TaskDAO.SelectAssigned(id, createdAt, updatedAt, assigned, base)
        ```


This generated-code checkpoint is useful for both humans and AI assistants. It shows the exact mapping Kora compiled from your annotations, so debugging becomes a matter of inspecting concrete code
instead of guessing framework behavior.

## New DTO { #new-dto }

The database projection is not the HTTP response. DTOs are the API boundary. They can hide database-only details, group values for clients, and keep HTTP JSON mapping separate from JDBC row mapping.

`TaskStatus` already exists because the JDBC model and mappers use it. Now add the request and response models that define the HTTP JSON contract.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskRequest.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record TaskRequest(List<TaskCreate> tasks) {

        @Json
        public record TaskCreate(
                String title,
                @Nullable String description,
                @Nullable Long userAssigneeId) {}
    }
    ```

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskResponse.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto;

    import jakarta.annotation.Nullable;
    import java.time.LocalDateTime;
    import java.util.List;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.dto.UserRequest;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record TaskResponse(List<TaskCreated> tasks) {

        @Json
        public record TaskCreated(
                Long id,
                String title,
                @Nullable String description,
                TaskStatus status,
                @Nullable Long userAssigneeId,
                LocalDateTime updatedAt) {}

        @Json
        public record TaskAssigned(
                Long id,
                String title,
                @Nullable String description,
                TaskStatus status,
                UserRequest assignee,
                LocalDateTime updatedAt) {}
    }
    ```

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskStatusRequest.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record TaskStatusRequest(TaskStatus status) {}
    ```

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/MessageResponse.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record MessageResponse(String message) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskRequest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class TaskRequest(
        val tasks: List<TaskCreate>
    ) {
        @Json
        data class TaskCreate(
            val title: String,
            val description: String?,
            val userAssigneeId: Long?
        )
    }
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskResponse.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto

    import java.time.LocalDateTime
    import ru.tinkoff.kora.guide.databasejdbc.advanced.dto.UserRequest
    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class TaskResponse(
        val tasks: List<TaskCreated>
    ) {
        @Json
        data class TaskCreated(
            val id: Long,
            val title: String,
            val description: String?,
            val status: TaskStatus,
            val userAssigneeId: Long?,
            val updatedAt: LocalDateTime
        )

        @Json
        data class TaskAssigned(
            val id: Long,
            val title: String,
            val description: String?,
            val status: TaskStatus,
            val assignee: UserRequest,
            val updatedAt: LocalDateTime
        )
    }
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskStatusRequest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class TaskStatusRequest(
        val status: TaskStatus
    )
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/MessageResponse.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class MessageResponse(
        val message: String
    )
    ```

`@Json` tells Kora to generate JSON readers/writers during annotation processing. Nullable fields mirror optional API values: a task description can be absent, and a task can be created without an
assignee.

## Transaction { #transaction }

For more on how `inTx(...)` opens a transaction boundary and reuses one connection, see [JDBC Transaction](../documentation/database-jdbc.md#transaction).

The service owns application behavior. It decides that tasks with assignees must reference existing users, and it decides that validation and insertion should happen atomically.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/service/TaskService.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.service;

    import java.time.LocalDateTime;
    import java.util.ArrayList;
    import java.util.List;
    import java.util.Objects;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.dto.UserRequest;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskRequest;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskResponse;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.TaskDAO;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.TaskRepository;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;

    @Component
    public final class TaskService {

        private final TaskRepository taskRepository;

        public TaskService(TaskRepository taskRepository) {
            this.taskRepository = taskRepository;
        }

        public List<TaskResponse.TaskCreated> createTasks(List<TaskRequest.TaskCreate> taskCreates) {
            return taskRepository.getJdbcConnectionFactory().inTx(() -> {
                var assigneeIds = taskCreates.stream()
                        .map(TaskRequest.TaskCreate::userAssigneeId)
                        .filter(Objects::nonNull)
                        .distinct()
                        .toList();

                if (!assigneeIds.isEmpty()) {
                    var existingAssigneeIds = taskRepository.findExistingAssigneeId(assigneeIds);
                    if (existingAssigneeIds.size() != assigneeIds.size()) {
                        var nonExistingAssigneeIds = assigneeIds.stream()
                                .filter(aid -> !existingAssigneeIds.contains(aid))
                                .toList();
                        throw HttpServerResponseException.of(404, "Assignee users not found: " + nonExistingAssigneeIds);
                    }
                }

                var tasks = taskCreates.stream()
                        .map(t -> new TaskDAO(t.title(), TaskStatus.TODO, t.description(), t.userAssigneeId()))
                        .toList();
                var taskIds = taskRepository.insert(tasks);

                List<TaskResponse.TaskCreated> taskCreateds = new ArrayList<>();
                for (int i = 0; i < taskIds.size(); i++) {
                    var taskId = taskIds.get(i);
                    var task = tasks.get(i);
                    taskCreateds.add(new TaskResponse.TaskCreated(
                            taskId,
                            task.title(),
                            task.description(),
                            TaskStatus.TODO,
                            task.userAssigneeId(),
                            LocalDateTime.now()));
                }

                return taskCreateds;
            });
        }

        public List<TaskResponse.TaskAssigned> getTasksByAssignees(List<Long> ids) {
            return taskRepository.findAssignedByAssigneeIds(ids).stream()
                    .map(this::toResponseAssigned)
                    .toList();
        }

        public void updateStatus(long id, TaskStatus status) {
            var updated = taskRepository.updateStatus(id, status);
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "Task not found");
            }
        }

        public void assignTask(long taskId, Long userId) {
            taskRepository.getJdbcConnectionFactory().inTx(() -> {
                var updated = taskRepository.updateAssignee(taskId, userId);
                if (updated.value() < 1) {
                    throw HttpServerResponseException.of(404, "Task not found");
                }
            });
        }

        public void unassignTask(long taskId) {
            var updated = taskRepository.updateAssignee(taskId, null);
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "Task not found");
            }
        }

        private TaskResponse.TaskAssigned toResponseAssigned(TaskDAO.SelectAssigned task) {
            return new TaskResponse.TaskAssigned(
                    task.id(),
                    task.base().title(),
                    task.base().description(),
                    task.base().status(),
                    new UserRequest(task.assigned().name(), task.assigned().email()),
                    task.updatedAt());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/service/TaskService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.service

    import java.time.LocalDateTime
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.database.jdbc.JdbcHelper.SqlFunction1
    import ru.tinkoff.kora.guide.databasejdbc.advanced.dto.UserRequest
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskRequest
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskResponse
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.TaskDAO
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.TaskRepository
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException

    @Component
    class TaskService(
        private val taskRepository: TaskRepository
    ) {

        fun createTasks(taskCreates: List<TaskRequest.TaskCreate>): List<TaskResponse.TaskCreated> {
            return taskRepository.jdbcConnectionFactory.inTx(SqlFunction1 {
                val assigneeIds = taskCreates
                    .mapNotNull { it.userAssigneeId }
                    .distinct()

                if (assigneeIds.isNotEmpty()) {
                    val existingAssigneeIds = taskRepository.findExistingAssigneeId(assigneeIds)
                    if (existingAssigneeIds.size != assigneeIds.size) {
                        val nonExistingAssigneeIds = assigneeIds.filter { it !in existingAssigneeIds }
                        throw HttpServerResponseException.of(404, "Assignee users not found: $nonExistingAssigneeIds")
                    }
                }

                val tasks = taskCreates.map {
                    TaskDAO(it.title, TaskStatus.TODO, it.description, it.userAssigneeId)
                }
                val taskIds = taskRepository.insert(tasks)

                taskIds.mapIndexed { index, taskId ->
                    val task = tasks[index]
                    TaskResponse.TaskCreated(
                        taskId,
                        task.title,
                        task.description,
                        TaskStatus.TODO,
                        task.userAssigneeId,
                        LocalDateTime.now()
                    )
                }
            })
        }

        fun getTasksByAssignees(ids: List<Long>): List<TaskResponse.TaskAssigned> {
            return taskRepository.findAssignedByAssigneeIds(ids)
                .map(::toResponseAssigned)
        }

        fun updateStatus(id: Long, status: TaskStatus) {
            val updated = taskRepository.updateStatus(id, status)
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "Task not found")
            }
        }

        fun assignTask(taskId: Long, userId: Long) {
            taskRepository.jdbcConnectionFactory.inTx(SqlFunction1 {
                val updated = taskRepository.updateAssignee(taskId, userId)
                if (updated.value() < 1) {
                    throw HttpServerResponseException.of(404, "Task not found")
                }
            })
        }

        fun unassignTask(taskId: Long) {
            val updated = taskRepository.updateAssignee(taskId, null)
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "Task not found")
            }
        }

        private fun toResponseAssigned(task: TaskDAO.SelectAssigned): TaskResponse.TaskAssigned {
            return TaskResponse.TaskAssigned(
                task.id,
                task.base.title,
                task.base.description,
                task.base.status,
                UserRequest(task.assigned.name, task.assigned.email),
                task.updatedAt
            )
        }
    }
    ```

`createTasks(...)` is the main advanced service method. It keeps validation and batch insert in one transaction. It also demonstrates why repositories expose database-shaped methods while services
expose application-shaped behavior.

The method has one important consistency rule: either all requested tasks are created, or none of them are created. That rule matters because the request is a batch. If the first task has a valid
assignee, the second task has a missing assignee, and the third task has no assignee, saving only part of the request would leave the API client with a surprising partial result.

`taskRepository.getJdbcConnectionFactory().inTx(...)` opens a JDBC transaction around the lambda. Every repository method called from inside that lambda uses the same transactional connection:

1. `findExistingAssigneeId(assigneeIds)` checks the distinct non-null assignee ids.
2. If some assignees are missing, the service throws `HttpServerResponseException`.
3. `insert(tasks)` is called only after validation succeeds.
4. The response DTOs are assembled from the generated ids and the original task values.

If the lambda finishes normally and returns the created DTOs, Kora commits the transaction. The assignee check and batch insert become visible together.

If the lambda throws, Kora rolls the transaction back. That includes the explicit `HttpServerResponseException` for missing assignees and database errors from `insert(...)`, such as constraint
violations or connection failures. Rollback means no task rows from that request are committed. The client receives the error, and the database stays in the same logical state it had
before `createTasks(...)` started.

The transaction is intentionally placed in the service, not in the repository. The repository knows how to execute individual SQL operations. The service knows that "validate all assignees and insert
all tasks" is one business operation and therefore one transaction boundary.

`UpdateCount` is used for update operations because SQL updates can affect zero rows. The service converts that database fact into an HTTP-facing `404`.

## New Controller { #new-controller }

The controller stays thin. It maps HTTP routes to service methods, controls status codes, and returns JSON DTOs. It does not contain SQL or transaction rules.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/controller/TaskController.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.controller;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.MessageResponse;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskRequest;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskResponse;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatusRequest;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.service.TaskService;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.HttpResponseEntity;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.common.annotation.Query;
    import ru.tinkoff.kora.http.common.header.HttpHeaders;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class TaskController {

        private final TaskService taskService;

        public TaskController(TaskService taskService) {
            this.taskService = taskService;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/tasks/assigned")
        @Json
        public List<TaskResponse.TaskAssigned> getTasksByAssignees(@Nullable @Query("ids") List<Long> ids) {
            return taskService.getTasksByAssignees(ids);
        }

        @HttpRoute(method = HttpMethod.POST, path = "/tasks")
        @Json
        public HttpResponseEntity<TaskResponse> createTask(@Json TaskRequest request) {
            var tasks = taskService.createTasks(request.tasks());
            return HttpResponseEntity.of(201, HttpHeaders.of(), new TaskResponse(tasks));
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/tasks/{taskId}/status")
        @Json
        public MessageResponse updateStatus(@Path Long taskId, @Json TaskStatusRequest request) {
            taskService.updateStatus(taskId, request.status());
            return new MessageResponse("OK");
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/tasks/{taskId}/assignee/{userId}")
        @Json
        public MessageResponse assignTask(@Path Long taskId, @Path Long userId) {
            taskService.assignTask(taskId, userId);
            return new MessageResponse("OK");
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/tasks/{taskId}/assignee")
        @Json
        public MessageResponse unassignTask(@Path Long taskId) {
            taskService.unassignTask(taskId);
            return new MessageResponse("OK");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/controller/TaskController.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.MessageResponse
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskRequest
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskResponse
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatusRequest
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.service.TaskService
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.HttpResponseEntity
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.common.annotation.Query
    import ru.tinkoff.kora.http.common.header.HttpHeaders
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class TaskController(
        private val taskService: TaskService
    ) {

        @HttpRoute(method = HttpMethod.GET, path = "/tasks/assigned")
        @Json
        fun getTasksByAssignees(@Query("ids") ids: List<Long>?): List<TaskResponse.TaskAssigned> {
            return taskService.getTasksByAssignees(ids ?: emptyList())
        }

        @HttpRoute(method = HttpMethod.POST, path = "/tasks")
        @Json
        fun createTask(@Json request: TaskRequest): HttpResponseEntity<TaskResponse> {
            val tasks = taskService.createTasks(request.tasks)
            return HttpResponseEntity.of(201, HttpHeaders.of(), TaskResponse(tasks))
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/tasks/{taskId}/status")
        @Json
        fun updateStatus(@Path taskId: Long, @Json request: TaskStatusRequest): MessageResponse {
            taskService.updateStatus(taskId, request.status)
            return MessageResponse("OK")
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/tasks/{taskId}/assignee/{userId}")
        @Json
        fun assignTask(@Path taskId: Long, @Path userId: Long): MessageResponse {
            taskService.assignTask(taskId, userId)
            return MessageResponse("OK")
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/tasks/{taskId}/assignee")
        @Json
        fun unassignTask(@Path taskId: Long): MessageResponse {
            taskService.unassignTask(taskId)
            return MessageResponse("OK")
        }
    }
    ```

The controller deliberately exposes only the operations needed for the advanced JDBC lesson: create several tasks, query assigned tasks by assignee ids, change task status, assign a task, and unassign
a task.

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
      poolName = "guide-jdbc-advanced" //(5)!
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
      poolName: "guide-jdbc-advanced" #(5)!
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

The application needs the same PostgreSQL database from the base JDBC guide. You can reuse that database, or start a local one with Docker Compose.

Create `docker-compose.yml` in the application module directory:

```yaml
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

Start PostgreSQL:

```bash
docker compose up -d
```

This starts PostgreSQL with:

- database: `postgres`
- username: `postgres`
- password: `postgres`
- port: `5432`

### Database Schema { #db-schema }

The base JDBC guide already created `V1__init_users.sql`. This guide adds `V2__init_tasks.sql`, so the final migration set contains both tables:

```text
src/main/resources/db/migration/
  V1__init_users.sql
  V2__init_tasks.sql
```

The `tasks.user_assignee_id` column references `users.id` and stays nullable:

```sql
user_assignee_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL
```

That matches the service behavior: a task can be created without an assignee, assigned later, or unassigned again. The indexes on `user_assignee_id` and `status` support the read and update paths used
by the guide.

## Run Application { #run-app }

Run the application with database connection values:

```bash
POSTGRES_JDBC_URL=jdbc:postgresql://localhost:5432/postgres \
POSTGRES_USER=postgres \
POSTGRES_PASS=postgres \
./gradlew :guides-apps:guide-database-jdbc-advanced-app:run
```

On Windows PowerShell:

```powershell
$env:POSTGRES_JDBC_URL="jdbc:postgresql://localhost:5432/postgres"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASS="postgres"
.\gradlew.bat :guides-apps:guide-database-jdbc-advanced-app:run
```

During startup, Kora builds the application graph, initializes the JDBC pool, runs Flyway, and then starts the HTTP server on port `8080`.

## Run with Docker { #run-docker }

Build the application distribution and Docker image:

```bash
./gradlew :guides-apps:guide-database-jdbc-advanced-app:distTar
docker build -t guide-database-jdbc-advanced-app guides/guide-database-jdbc-advanced-app
```

Run the container against PostgreSQL started by Docker Compose:

```bash
docker run --rm \
  --name guide-database-jdbc-advanced-app \
  --network kora-guide_default \
  -p 8080:8080 \
  -p 8085:8085 \
  -e POSTGRES_JDBC_URL=jdbc:postgresql://postgres:5432/postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASS=postgres \
  guide-database-jdbc-advanced-app
```

If your Compose project uses a different network name, check it with:

```bash
docker network ls
```

The application Dockerfile runs the Gradle distribution entrypoint:

```dockerfile
CMD ["/opt/app/application/bin/application"]
```

That name comes from `applicationName = "application"` in `build.gradle`.

## Check Application { #check-app }

The migration seeds two users:

- `1` / `John Doe`
- `2` / `Jane Smith`

Create several tasks in one request:

```bash
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "title": "Prepare database guide",
        "description": "Explain transactions and projections",
        "userAssigneeId": 1
      },
      {
        "title": "Review generated JDBC mapper",
        "description": null,
        "userAssigneeId": 2
      },
      {
        "title": "Unassigned cleanup task",
        "description": "Can be assigned later",
        "userAssigneeId": null
      }
    ]
  }'
```

Fetch tasks assigned to seeded users:

```bash
curl "http://localhost:8080/tasks/assigned?ids=1&ids=2"
```

Update a task status:

```bash
curl -X PUT http://localhost:8080/tasks/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "IN_PROGRESS"}'
```

Assign a task to a user:

```bash
curl -X PUT http://localhost:8080/tasks/3/assignee/1
```

Unassign a task:

```bash
curl -X DELETE http://localhost:8080/tasks/3/assignee
```

Check transaction rollback by sending one valid assignee and one missing assignee in the same batch:

```bash
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "title": "This task should not be committed",
        "description": null,
        "userAssigneeId": 1
      },
      {
        "title": "This task has a missing assignee",
        "description": null,
        "userAssigneeId": 999999
      }
    ]
  }'
```

The service throws before `insert(tasks)` completes successfully, so the whole `createTasks(...)` transaction rolls back. Re-run the assigned-task query and the first task from the failed batch will
not appear.

## Best Practices { #best-practices }

- Keep database relationships visible in schema and SQL.
- Start with the model needed for the operation; do not force one "entity" to serve every query.
- Use query-specific projections for read paths.
- Reuse existing DAO pieces with `@Embedded` when a projection naturally contains them.
- Use `@Embedded("prefix_")` for joined projections so SQL aliases stay unique while nested models keep natural column names.
- Use macros for repetitive entity insert fragments, but keep complex joins explicit.
- Register focused custom mappers and let Kora resolve them by generic type.
- Put multi-step consistency rules in `inTx(...)`.
- Inspect generated repository implementations when debugging parameter binding, batch behavior, generated keys, or row mapping.

## Summary { #summary }

You extended the base JDBC application with a second table and several advanced Kora JDBC patterns:

- nullable foreign key from `tasks` to `users`
- a compact insert model with `TaskDAO`
- entity metadata and insert macros
- custom enum and PostgreSQL array parameter mappers
- batch task creation with generated ids
- transactional validation before writing related rows
- query-specific projection with `TaskDAO.SelectAssigned`
- reuse of `UserDAO` through prefixed `@Embedded`

The result stays SQL-first and explicit. The repository is not tied to one model, so it can expose exactly the projection each query needs without multiplying repositories.

## Key Concepts { #key-concepts }

- how `@EntityJdbc`, `@Table`, `@Id`, `@Column`, and prefixed `@Embedded` describe entity/projection shapes
- how `%{entity#inserts}` expands into concrete insert SQL
- how nullable database columns become nullable Java/Kotlin fields and generated null checks
- how custom mappers are resolved by generic mapper type
- how `@Batch` becomes generated `addBatch()` / `executeBatch()` code
- how one repository can return different projections for different SQL queries
- how `inTx(...)` shares one connection across repository calls
- how to pass a Java/Kotlin list into PostgreSQL with `ANY(:ids)`

## Troubleshooting { #troubleshooting }

**Task status mapper is not used:**

Ensure `TaskStatusParameterMapper` and `TaskStatusResultMapper` are `@Component` classes and implement the exact generic mapper types. In Java that is `JdbcParameterColumnMapper<TaskStatus>`
and `JdbcResultColumnMapper<TaskStatus>`; in Kotlin the parameter mapper should usually be `JdbcParameterColumnMapper<TaskStatus?>`.

**Assigned task query maps the wrong columns:**

Check SQL aliases in the join and the embedded prefix. With `@Embedded("assignee_") UserDAO assigned`, the `UserDAO` field `@Column("created_at")` expects the SQL alias `assignee_created_at`.

**Projection design feels duplicated:**

Do not create a separate repository just because the query returns a different shape. Keep the query in the repository that owns the database operation and return a projection type that matches that
query.

**Batch insert fails with missing assignee:**

The service validates assignee ids before insert. Create the user first, or send `null` for `userAssigneeId` when the task should be unassigned.

**Query with `ANY(:ids)` fails:**

Ensure `ListOfLongJdbcParameterMapper` is a `@Component` and creates a PostgreSQL `BIGINT` array.

**JSON mapper warning appears for `TaskStatus` or task DTOs:**

Annotate JSON-facing DTOs and enums with `@Json`, because they appear in HTTP request or response bodies.

## What's Next? { #whats-next }

- [Integration Testing](testing-integration.md) to verify transactions, migrations, custom mappers, and repository projections against PostgreSQL.
- [Black Box Testing](testing-black-box.md) to exercise the advanced JDBC application through its HTTP API.
- [Observability](observability.md) to add metrics, traces, logs, and probes around database-backed operations.
- [Caching](cache.md) to reduce repeated database reads after the persistence layer is stable.
- [Resilient Patterns](resilient.md) to protect service operations that call unstable downstream dependencies.

## Help { #help }

If you encounter issues:

- compare with [Kora Java Database JDBC Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-advanced-app) and [Kora Kotlin Database JDBC Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-database-jdbc-advanced-app)
- check the [Database JDBC documentation](../documentation/database-jdbc.md)
- check the [Database Common documentation](../documentation/database-common.md)
- check the [Database Migration documentation](../documentation/database-migration.md)
