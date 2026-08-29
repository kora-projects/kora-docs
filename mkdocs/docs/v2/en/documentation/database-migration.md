---
description: "Explains Kora database migration modules for Flyway and Liquibase, migration configuration, startup behavior, DBMS dialect artifacts, and JDBC integration. Use when working with FlywayJdbcDatabaseModule, LiquibaseJdbcDatabaseModule, FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDataSource."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora database migration modules for Flyway and Liquibase, migration configuration, migration modes, startup behavior, DBMS dialect artifacts and JDBC integration; key triggers include FlywayJdbcDatabaseModule, LiquibaseJdbcDatabaseModule, FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDataSource, Unsupported Database."
---

Database migrations apply schema and reference data changes in a controlled order: they create tables, indexes, constraints, and perform other `SQL` operations required by a new application version.
In Kora, migration modules are bound to `JdbcDataSource` initialization through a `GraphInterceptor<JdbcDataSource>`: when the application starts, `JdbcDataSource` is created as a graph component, and the interceptor's `afterInit()` runs migrations before the component is published to the rest of the graph.
If a migration fails, `afterInit()` throws, so `JdbcDataSource` component initialization and the whole graph build (application startup) fail as well.
The interceptor's `beforeRelease()` is a no-op: migrations are never rolled back or re-run when the application stops.

This approach is convenient for local development, tests, and small installations where the application runs as a single instance.
For environments with multiple replicas, choose a separate migration execution method in advance so migrations are not run simultaneously from every application instance.
Repositories do not create the database schema themselves: tables, indexes, constraints, and reference data must be created by migrations or by an external database preparation process.

## Flyway { #flyway }

Module for database migration using the [Flyway](https://documentation.red-gate.com/fd) tool.
During `JdbcDataSource` initialization, the module builds a `Flyway` instance from the settings of the `flyway` section and executes the operation selected by [migration mode](#flyway-modes).
Migrations are run by `FlywayJdbcDatabaseInterceptor`, which is provided by `FlywayJdbcDatabaseModule`.
`Flyway` is wired to `SLF4J` (`loggers("slf4j")`), so migration output and the `FlyWay migration in mode 'MIGRATE' applied in ...` timing line (logged at `INFO`) appear in the application's normal logs.

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:database-flyway"
    implementation "org.flywaydb:flyway-database-postgresql:13.3.0" //(1)!
    ```

    1. Support for a specific DBMS, see [Database Support](#flyway-database-support).

    Module:
    ```java
    @KoraApp
    public interface Application extends FlywayJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:database-flyway")
    implementation("org.flywaydb:flyway-database-postgresql:13.3.0") //(1)!
    ```

    1. Support for a specific DBMS, see [Database Support](#flyway-database-support).

    Module:
    ```kotlin
    @KoraApp
    interface Application : FlywayJdbcDatabaseModule
    ```

Requires the [`JDBC` module](database-jdbc.md) because migrations are executed through `DataSource`.
Applications usually include both modules: `JdbcDatabaseModule` creates `JdbcDataSource`, and `FlywayJdbcDatabaseModule` adds the migration interceptor.

### Database Support { #flyway-database-support }

Since `Flyway` 10, support for a specific DBMS lives in a separate artifact, and `io.koraframework:database-flyway` brings only `org.flywaydb:flyway-core`.
The application must add the artifact for its own database, otherwise it fails during `JdbcDataSource` initialization:

```text
FlywayException: Unsupported Database: PostgreSQL 16.x
```

For PostgreSQL the artifact is `org.flywaydb:flyway-database-postgresql`; artifacts for other databases are listed in the [Flyway documentation](https://documentation.red-gate.com/fd).
Version the artifact the same as the `flyway-core` that comes with `database-flyway` — `13.3.0` in Kora 2.0.
The artifact is not part of [`kora-bom`](general.md#dependencies), so the version must always be specified explicitly.

### Configuration { #configuration }

Example of the complete configuration described by the `FlywayConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    flyway {
        enabled = true //(1)!
        mode = "MIGRATE" //(2)!
        locations = ["db/migration"] //(3)!
        executeInTransaction = true //(4)!
        validateOnMigrate = true //(5)!
        mixed = false //(6)!
        configurationProperties {} //(7)!
    }
    ```

    1. Enables migration execution during `JdbcDataSource` initialization (default: `true`). If set to `false`, the module logs `FlyWay is disabled, skipping migrate...` and does not touch the database.
    2. Operation performed by `Flyway` at startup: `MIGRATE`, `REPAIR` or `CLEAN_MIGRATE` (default: `MIGRATE`). The value is matched by exact name, in upper case. See [Migration Modes](#flyway-modes).
    3. Paths to directories with migration scripts (default: `["db/migration"]`). A plain string is also accepted and is split by comma.
    4. Executes migrations inside a transaction when supported by the database and the `SQL` operations themselves (default: `true`).
    5. Validates checksums of already applied migrations before executing new ones (default: `true`). If checksums do not match, startup fails with an error.
    6. Allows mixing transactional and non-transactional `SQL` operations in one migration (default: `false`).
       If enabled, the whole migration is executed **without a transaction** to avoid errors in databases where some operations cannot run inside a transaction.
       This setting is relevant for databases that do not support executing certain operations inside a transaction: PostgreSQL, Aurora PostgreSQL, SQL Server, and SQLite.
    7. Additional `Flyway` key-value properties (default: `{}`).
       Use them to pass settings that do not have a separate Kora configuration option.
       Keys are the standard `Flyway` property names **with the `flyway.` prefix**, for example `flyway.schemas`, `flyway.baselineOnMigrate`, `flyway.placeholderReplacement` or `flyway.placeholders.*`.
       A key without the prefix is not recognized by `Flyway`.

=== ":simple-yaml: `YAML`"

    ```yaml
    flyway:
        enabled: true #(1)!
        mode: "MIGRATE" #(2)!
        locations: ["db/migration"] #(3)!
        executeInTransaction: true #(4)!
        validateOnMigrate: true #(5)!
        mixed: false #(6)!
        configurationProperties: {} #(7)!
    ```

    1. Enables migration execution during `JdbcDataSource` initialization (default: `true`). If set to `false`, the module logs `FlyWay is disabled, skipping migrate...` and does not touch the database.
    2. Operation performed by `Flyway` at startup: `MIGRATE`, `REPAIR` or `CLEAN_MIGRATE` (default: `MIGRATE`). The value is matched by exact name, in upper case. See [Migration Modes](#flyway-modes).
    3. Paths to directories with migration scripts (default: `["db/migration"]`). A plain string is also accepted and is split by comma.
    4. Executes migrations inside a transaction when supported by the database and the `SQL` operations themselves (default: `true`).
    5. Validates checksums of already applied migrations before executing new ones (default: `true`). If checksums do not match, startup fails with an error.
    6. Allows mixing transactional and non-transactional `SQL` operations in one migration (default: `false`).
       If enabled, the whole migration is executed **without a transaction** to avoid errors in databases where some operations cannot run inside a transaction.
       This setting is relevant for databases that do not support executing certain operations inside a transaction: PostgreSQL, Aurora PostgreSQL, SQL Server, and SQLite.
    7. Additional `Flyway` key-value properties (default: `{}`).
       Use them to pass settings that do not have a separate Kora configuration option.
       Keys are the standard `Flyway` property names **with the `flyway.` prefix**, for example `flyway.schemas`, `flyway.baselineOnMigrate`, `flyway.placeholderReplacement` or `flyway.placeholders.*`.
       A key without the prefix is not recognized by `Flyway`.

### Migration Modes { #flyway-modes }

The `mode` setting selects which `Flyway` operation the interceptor performs at startup:

- `MIGRATE` — calls `Flyway.migrate()` and applies migrations that are not yet recorded in the migration history table. This is the normal application mode.
- `REPAIR` — calls `Flyway.repair()`: no new migrations are applied, instead the history table is repaired — checksums are recalculated for the current files and failed entries are removed.
  This is a one-off recovery mode for a deliberately changed migration file; after a successful run, switch back to `MIGRATE`.
- `CLEAN_MIGRATE` — calls `Flyway.clean()` and then `Flyway.migrate()`: the configured schemas are **completely wiped** and migrations are applied from scratch.
  Suitable only for local development and disposable test databases, never for an environment with real data.
  `Flyway` forbids `clean` by default and Kora does not change that setting, so this mode additionally requires allowing cleaning through `configurationProperties { "flyway.cleanDisabled" = "false" }`.

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
During `JdbcDataSource` initialization, the module obtains a connection from `DataSource`, determines the database implementation from that connection, creates a `Liquibase` instance, and calls `update()`.
Migrations are run by `LiquibaseJdbcDatabaseInterceptor`, which is provided by `LiquibaseJdbcDatabaseModule`.
Support for specific databases ships inside `liquibase-core`, so unlike `Flyway`, no additional dialect artifact is required.

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:database-liquibase"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LiquibaseJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:database-liquibase")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : LiquibaseJdbcDatabaseModule
    ```

Requires the [`JDBC` module](database-jdbc.md) because migrations are executed through `DataSource`.
Applications usually include both modules: `JdbcDatabaseModule` creates `JdbcDataSource`, and `LiquibaseJdbcDatabaseModule` adds the migration interceptor.

### Configuration { #configuration-2 }

Example of the complete configuration described by the `LiquibaseConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    liquibase {
        changelog = "db/changelog/db.changelog-master.xml" //(1)!
    }
    ```

    1. Path to the main [`changelog`](https://docs.liquibase.com/concepts/changelogs/home.html) file with migration definitions (default: `db/changelog/db.changelog-master.xml`).
       The file is looked up on the classpath.

=== ":simple-yaml: `YAML`"

    ```yaml
    liquibase:
      changelog: "db/changelog/db.changelog-master.xml" #(1)!
    ```

    1. Path to the main [`changelog`](https://docs.liquibase.com/concepts/changelogs/home.html) file with migration definitions (default: `db/changelog/db.changelog-master.xml`).
       The file is looked up on the classpath.

Unlike `Flyway`, the `Liquibase` module does not have an `enabled` setting: if the module is connected to the application graph, migrations run during `JdbcDataSource` initialization.
If a `Liquibase` migration fails, the module logs `Error during Liquibase migration` and wraps the error in `IllegalStateException`, so application startup is interrupted.
A successful run is reported by the `Liquibase migration applied in ...` line at `INFO` level.

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

## Connection Pool { #pool }

Migrations use the same `Hikari` connection pool as the application, so the `jdbc` section must leave room for the migration tool:

- `Flyway` takes **two** connections during migration — one for the migration itself and one for schema and lock management.
- `Liquibase` normally works over a **single** connection.

The default `jdbc.maxPoolSize` is `10` and is enough for both tools.
If the pool is deliberately shrunk to `1`, a `Flyway` migration will wait for a second connection until `jdbc.connectionTimeout` expires and then fail the application startup.

===! ":material-code-json: `Hocon`"

    ```javascript
    jdbc {
        jdbcUrl = "jdbc:postgresql://localhost:5432/postgres"
        username = "postgres"
        password = "postgres"
        poolName = "kora"
        maxPoolSize = 10
    }

    flyway {
        locations = ["db/migration"]
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    jdbc:
      jdbcUrl: "jdbc:postgresql://localhost:5432/postgres"
      username: "postgres"
      password: "postgres"
      poolName: "kora"
      maxPoolSize: 10

    flyway:
      locations: ["db/migration"]
    ```

Full pool settings are described in the [`JDBC` module](database-jdbc.md) documentation.

## Recommendations { #recommendations }

???+ warning "Recommendation"

    **Migration modules are not recommended** for running migrations on application startup in horizontally scaled environments
    where the application runs with multiple replicas. Each replica will try to execute migrations during startup.
    Also keep in mind that every application restart triggers the migration mechanism again.

    In such cases, use the [Flyway Gradle Plugin](https://plugins.gradle.org/plugin/org.flywaydb.flyway) for local development,
    run `Flyway` from code after database startup in tests,
    use a [Kubernetes Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/) for production Kubernetes environments,
    or run migrations separately from `CI`.

When migrations are moved out of the application, `io.koraframework:database-flyway` is not connected at all and the schema is prepared by a separate step.
The `Flyway` Gradle plugin needs the DBMS artifact just like the module does, but on the `buildscript` classpath:

```groovy
buildscript {
    dependencies {
        classpath "org.flywaydb:flyway-database-postgresql:13.0.0"
    }
}

plugins {
    id "org.flywaydb.flyway" version "13.0.0"
}

flyway {
    url = "jdbc:postgresql://localhost:5432/postgres"
    user = "postgres"
    password = "postgres"
    locations = ["classpath:db/migration"]
    baselineOnMigrate = true
}
```

The Gradle plugin is a separate `Flyway` installation from the one inside the application: here the artifact version follows the plugin version, not the `flyway-core` that `database-flyway` brings.
The two versions are independent, and the build-time dependency lives on the `buildscript` classpath while the runtime one lives in `implementation`.

In tests, the migration module remains the simplest option: the test database lives for the duration of a single run, there is only one instance, and the schema is prepared exactly by the same migrations as in production.
