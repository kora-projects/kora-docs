Modules to migrate the database along with the service launch.

## Flyway

Module for database migration using the [Flyway](https://documentation.red-gate.com/fd) tool.

### Dependency

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

Requires [JDBC module](database-jdbc.md) dependency.

### Configuration

Example of the complete configuration described in the `FlywayConfig` class (default values are specified):

===! ":material-code-json: `Hocon`"

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

    1. Whether database migration is enabled when the application starts. If `false`, migrations will not be executed.
    2. Directory paths where migration scripts are located.
    3. Whether to execute migrations within a transaction.
    4. Whether to verify checksums of existing migrations before execution. An error will occur if they do not match.
    5. Whether to allow mixing transactional and non-transactional SQL operations in a single migration. If enabled, the entire migration will be executed **without a transaction** to avoid errors in databases where certain operations cannot be run inside a transaction.
       This setting is only relevant for databases that do not support executing certain operations within a transaction: PostgreSQL, Aurora PostgreSQL, SQL Server, and SQLite.
    6. Additional key-value configuration properties for `Flyway#configurationProperties`.

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

    1. Whether database migration is enabled when the application starts. If `false`, migrations will not be executed.
    2. Directory paths where migration scripts are located.
    3. Whether to execute migrations within a transaction.
    4. Whether to verify checksums of existing migrations before execution. An error will occur if they do not match.
    5. Whether to allow mixing transactional and non-transactional SQL operations in a single migration. If enabled, the entire migration will be executed **without a transaction** to avoid errors in databases where certain operations cannot be run inside a transaction.
       This setting is only relevant for databases that do not support executing certain operations within a transaction: PostgreSQL, Aurora PostgreSQL, SQL Server, and SQLite.
    6. Additional key-value configuration properties for `Flyway#configurationProperties`.

## Liquibase

Module for database migration using the [Liquibase](https://www.liquibase.com/supported-databases) tool.

### Dependency

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

Requires [JDBC module](database-jdbc.md) dependency.

### Configuration

Example of the complete configuration described in the `LiquibaseConfig` class (default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    liquibase {
        changelog = "db/changelog/db.changelog-master.xml" //(1)!
    }
    ```

    1.  Path to [master file](https://docs.liquibase.com/concepts/changelogs/home.html) migration configuration

=== ":simple-yaml: `YAML`"

    ```yaml
    liquibase:
      changelog: "db/changelog/db.changelog-master.xml" #(1)!
    ```

    1.  Path to [master file](https://docs.liquibase.com/concepts/changelogs/home.html) migration configuration

## Recommendations

???+ warning "Recommendation"

    **We do not recommend** using migration modules to run applications in an environment where with horizontal scaling 
    by increasing the number of working application replicas. Since this will lead to a migration call on each replica setup.
    Also keep in mind that every restart of the application will also trigger migrations.

    In such cases we recommend using something like [Flyway Gradle plugin](https://plugins.gradle.org/plugin/org.flywaydb.flyway) for local development,
    for tests use Flyway startup from code after database startup, for Kubernetes combat environment use [K8S Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
    or migration from CI via [Flyway Gradle plugin](https://plugins.gradle.org/plugin/org.flywaydb.flyway).
