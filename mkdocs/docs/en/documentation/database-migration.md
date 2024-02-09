Module for database migration using the [Flyway](https://documentation.red-gate.com/fd).

## Dependency

=== ":fontawesome-brands-java: `Java`"

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

Requires [JDBC module](database-jdbc.md) connection.

## Recommendations

???+ warning "Tip"

    **We do not recommend** using this module to run applications in an environment where with horizontal scaling 
    by increasing the number of working application replicas. Since this will lead to a migration call on each replica setup.

    In such cases we recommend using [Flyway Gradle plugin](https://documentation.red-gate.com/fd/gradle-task-184127407.html) for local development,
    for tests use Flyway startup from code after database startup, for Kubernetes combat environment use [K8S Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
    or migration from CI via [Flyway Gradle plugin](https://documentation.red-gate.com/fd/gradle-task-184127407.html).
