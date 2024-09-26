Модуль для миграции базы данных вместе с запуском сервиса.

## Flyway

Модуль для миграции базы данных с помощью инструмента [Flyway](https://documentation.red-gate.com/fd).

### Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-flyway"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends FlywayJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-flyway")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : FlywayJdbcDatabaseModule
    ```

Требует подключения [JDBC модуля](database-jdbc.md).

### Конфигурация

Пример полной конфигурации, описанной в классе `FlywayConfig` (указаны значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    flyway {
        locations = "db/migration" //(1)!
    }
    ```

    1.  Пути директорий где искать скрипты миграции

=== ":simple-yaml: `YAML`"

    ```yaml
    flyway:
      locations: "db/migration" #(1)!
    ```

    1.  Пути директорий где искать скрипты миграции

## Liquibase

Модуль для миграции базы данных с помощью инструмента [Liquibase](https://www.liquibase.com/supported-databases).

### Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-liquibase"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LiquibaseJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-liquibase")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LiquibaseJdbcDatabaseModule
    ```

Требует подключения [JDBC модуля](database-jdbc.md).

### Конфигурация

Пример полной конфигурации, описанной в классе `LiquibaseConfig` (указаны значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    liquibase {
        changelog = "db/changelog/db.changelog-master.xml" //(1)!
    }
    ```

    1.  Путь до [мастер файла](https://docs.liquibase.com/concepts/changelogs/home.html) конфигурации миграций

=== ":simple-yaml: `YAML`"

    ```yaml
    liquibase:
      changelog: "db/changelog/db.changelog-master.xml" #(1)!
    ```

    1.  Путь до [мастер файла](https://docs.liquibase.com/concepts/changelogs/home.html) конфигурации миграций

## Рекомендации

???+ warning "Совет"

    **Мы не рекомендуем** использовать модули миграции для работы приложений в окружении где есть горизонтальное масштабирование 
    посредствам увелечения количества реплик рабочего приложения. Так как это будет вести за собой вызов миграции на каждую запущенную реплику.
    Также имейте в виду что каждый перезапуск приложения также будет вызывать миграции.

    В таких случаях рекомендуем например использовать для локальной разработки [Flyway Gradle plugin](https://documentation.red-gate.com/fd/gradle-task-184127407.html),
    для тестов использовать запуск Flyway из кода после запуска базы данных, для боевого окружения Kubernetes использовать [K8S Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
    либо миграцию из CI через [Flyway Gradle plugin](https://documentation.red-gate.com/fd/gradle-task-184127407.html).
