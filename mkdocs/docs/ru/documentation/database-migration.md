Модуль для миграции базы данных с помощью инструмента [Flyway](https://documentation.red-gate.com/fd).

## Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-flyway"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends FlywayJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-flyway")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : FlywayJdbcDatabaseModule
    ```

Требует подключения [JDBC модуля](database-jdbc.md).

## Рекомендации

???+ warning "Совет"

    **Мы не рекомендуем** использовать этот модуль для работы приложений в окружении где есть горизонтальное масштабирование 
    посредствам увелечения количества реплик рабочего приложения. Так как это будет вести за собой вызов миграции на каждую запущенную реплику.

    В таких случаях рекомендуем использовать для локальной разработки [Flyway Gradle plugin](https://documentation.red-gate.com/fd/gradle-task-184127407.html),
    для тестов использовать запуск Flyway из кода после запуска базы данных, для боевого окружения Kubernetes использовать [K8S Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
    либо миграцию из CI через [Flyway Gradle plugin](https://documentation.red-gate.com/fd/gradle-task-184127407.html).
