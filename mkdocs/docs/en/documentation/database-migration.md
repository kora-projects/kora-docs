Modules to migrate the database along with the service launch.

## Flyway

Module for database migration using the [Flyway](https://documentation.red-gate.com/fd) tool.

### Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-flyway"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends FlywayJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
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
        locations = "db/migration" //(1)!
    }
    ```

    1.  Directory paths where to look for migration scripts

=== ":simple-yaml: `YAML`"

    ```yaml
    flyway:
      locations: "db/migration" #(1)!
    ```

    1.  Directory paths where to look for migration scripts

## Liquibase

Module for database migration using the [Liquibase](https://www.liquibase.com/supported-databases) tool.

### Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-liquibase"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LiquibaseJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
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

???+ warning "Tip"

    **We do not recommend** using migration modules to run applications in an environment where with horizontal scaling 
    by increasing the number of working application replicas. Since this will lead to a migration call on each replica setup.
    Also keep in mind that every restart of the application will also trigger migrations.

    In such cases we recommend using [Flyway Gradle plugin](https://documentation.red-gate.com/fd/gradle-task-184127407.html) for local development,
    for tests use Flyway startup from code after database startup, for Kubernetes combat environment use [K8S Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
    or migration from CI via [Flyway Gradle plugin](https://documentation.red-gate.com/fd/gradle-task-184127407.html).
