---
description: "Explains Kora database migration modules for Flyway and Liquibase, migration configuration, startup behavior, and database integration. Use when working with FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDatabaseModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora database migration modules for Flyway and Liquibase, migration configuration, startup behavior, and database integration; key triggers include FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDatabaseModule."
---

Database migrations apply schema and reference data changes in a controlled order: they create tables, indexes, constraints, and perform other `SQL` operations required by a new application version.
In Kora, migration modules are bound to `JdbcDatabase` initialization: when the application starts, the database is created as a graph component, and then an interceptor runs migrations.
If a migration fails, `JdbcDatabase` component initialization and application startup fail as well.
Migration modules do not perform additional actions when the application stops.

This approach is convenient for local development, tests, and small installations where the application runs as a single instance.
For environments with multiple replicas, choose a separate migration execution method in advance so migrations are not run simultaneously from every application instance.
Repositories do not create the database schema themselves: tables, indexes, constraints, and reference data must be created by migrations or by an external database preparation process.

## Flyway { #flyway }

Module for database migration using the [Flyway](https://documentation.red-gate.com/fd) tool.
During `JdbcDatabase` initialization, the module calls `Flyway.migrate()` with settings from the `flyway` section.
Migrations are run by `FlywayJdbcDatabaseInterceptor`, which is provided by `FlywayJdbcDatabaseModule`.

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-flyway"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends FlywayJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-flyway")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : FlywayJdbcDatabaseModule
    ```

Requires the [`JDBC` module](database-jdbc.md) because migrations are executed through `DataSource`.
Applications usually include both modules: `JdbcDatabaseModule` creates `JdbcDatabase`, and `FlywayJdbcDatabaseModule` adds the migration interceptor.

### Configuration { #configuration }

Example of the complete configuration described by the `FlywayConfig` class:

===! ":material-code-json: `HOCON`"

    ```javascript
    flyway {
        enabled = true //(1)!
        locations = ["db/migration"] //(2)!
        executeInTransaction = true //(3)!
        validateOnMigrate = true //(4)!
        mixed = false //(5)!
        configurationProperties {} //(6)!
    }
    ```

    1. Enables migration execution during `JdbcDatabase` initialization (default: `true`). If set to `false`, the module skips the `Flyway.migrate()` call.
    2. Paths to directories with migration scripts (default: `["db/migration"]`).
    3. Executes migrations inside a transaction when supported by the database and the `SQL` operations themselves (default: `true`).
    4. Validates checksums of already applied migrations before executing new ones (default: `true`). If checksums do not match, startup fails with an error.
    5. Allows mixing transactional and non-transactional `SQL` operations in one migration (default: `false`).
       If enabled, the whole migration is executed **without a transaction** to avoid errors in databases where some operations cannot run inside a transaction.
       This setting is relevant for databases that do not support executing certain operations inside a transaction: PostgreSQL, Aurora PostgreSQL, SQL Server, and SQLite.
    6. Additional `Flyway` key-value properties (default: `{}`).
       Use them to pass settings that do not have a separate Kora configuration option, such as `schemas`, `baselineOnMigrate`, `placeholderReplacement`, or `placeholders.*`.

=== ":simple-yaml: `YAML`"

    ```yaml
    flyway:
        enabled: true #(1)!
        locations: ["db/migration"] #(2)!
        executeInTransaction: true #(3)!
        validateOnMigrate: true #(4)!
        mixed: false #(5)!
        configurationProperties: {} #(6)!
    ```

    1. Enables migration execution during `JdbcDatabase` initialization (default: `true`). If set to `false`, the module skips the `Flyway.migrate()` call.
    2. Paths to directories with migration scripts (default: `["db/migration"]`).
    3. Executes migrations inside a transaction when supported by the database and the `SQL` operations themselves (default: `true`).
    4. Validates checksums of already applied migrations before executing new ones (default: `true`). If checksums do not match, startup fails with an error.
    5. Allows mixing transactional and non-transactional `SQL` operations in one migration (default: `false`).
       If enabled, the whole migration is executed **without a transaction** to avoid errors in databases where some operations cannot run inside a transaction.
       This setting is relevant for databases that do not support executing certain operations inside a transaction: PostgreSQL, Aurora PostgreSQL, SQL Server, and SQLite.
    6. Additional `Flyway` key-value properties (default: `{}`).
       Use them to pass settings that do not have a separate Kora configuration option, such as `schemas`, `baselineOnMigrate`, `placeholderReplacement`, or `placeholders.*`.

### Migration Files { #flyway-files }

By default, `Flyway` looks for migrations in `src/main/resources/db/migration`.
A regular migration file has a name like `V1__init_schema.sql`, where `V1` is the version and the part after the double underscore is the description.

```text
src/main/resources/db/migration/
  V1__init_users.sql
  V2__add_user_status.sql
```

Example of a simple migration:

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL
);
```

When `Flyway` starts, it creates a service migration history table and applies only new versions.
If `validateOnMigrate` is enabled, already applied files must not be changed without a separate migration history repair process.

## Liquibase { #liquibase }

Module for database migration using the [Liquibase](https://www.liquibase.com/supported-databases) tool.
During `JdbcDatabase` initialization, the module obtains a connection from `DataSource`, creates a `Liquibase` instance, and calls `update()`.
Migrations are run by `LiquibaseJdbcDatabaseInterceptor`, which is provided by `LiquibaseJdbcDatabaseModule`.

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-liquibase"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LiquibaseJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-liquibase")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : LiquibaseJdbcDatabaseModule
    ```

Requires the [`JDBC` module](database-jdbc.md) because migrations are executed through `DataSource`.
Applications usually include both modules: `JdbcDatabaseModule` creates `JdbcDatabase`, and `LiquibaseJdbcDatabaseModule` adds the migration interceptor.

### Configuration { #configuration-2 }

Example of the complete configuration described by the `LiquibaseConfig` class:

===! ":material-code-json: `HOCON`"

    ```javascript
    liquibase {
        changelog = "db/changelog/db.changelog-master.xml" //(1)!
    }
    ```

    1. Path to the main [`changelog`](https://docs.liquibase.com/concepts/changelogs/home.html) file with migration definitions (default: `db/changelog/db.changelog-master.xml`).

=== ":simple-yaml: `YAML`"

    ```yaml
    liquibase:
      changelog: "db/changelog/db.changelog-master.xml" #(1)!
    ```

    1. Path to the main [`changelog`](https://docs.liquibase.com/concepts/changelogs/home.html) file with migration definitions (default: `db/changelog/db.changelog-master.xml`).

Unlike `Flyway`, the `Liquibase` module does not have an `enabled` setting: if the module is connected to the application graph, migrations run during `JdbcDatabase` initialization.
If a `Liquibase` migration fails, the module wraps the error in `IllegalStateException`, and application startup is interrupted.

### Migration Files { #liquibase-files }

By default, `Liquibase` looks for the main `changelog` file at `src/main/resources/db/changelog/db.changelog-master.xml`.
`Liquibase` supports different `changelog` formats, but an `SQL`-oriented project often benefits from keeping migrations as formatted `SQL`.
The main file can include such migrations with `include`.

```text
src/main/resources/db/changelog/
  db.changelog-master.xml
  changes/
    001-init-users.sql
```

Minimal main `changelog`:

```xml
<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

    <include file="db/changelog/changes/001-init-users.sql"/>
</databaseChangeLog>
```

Example of an included migration in formatted `SQL`:

```sql
--liquibase formatted sql

--changeset app:001-init-users
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL
);
```

## Recommendations { #recommendations }

???+ warning "Recommendation"

    **Migration modules are not recommended** for running migrations on application startup in horizontally scaled environments
    where the application runs with multiple replicas. Each replica will try to execute migrations during startup.
    Also keep in mind that every application restart triggers the migration mechanism again.

    In such cases, use the [Flyway Gradle Plugin](https://plugins.gradle.org/plugin/org.flywaydb.flyway) for local development,
    run `Flyway` from code after database startup in tests,
    use a [Kubernetes Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/) for production Kubernetes environments,
    or run migrations separately from `CI`.
