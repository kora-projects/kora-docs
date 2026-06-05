---
description: "Explains Kora database migration modules for Flyway and Liquibase, migration configuration, startup behavior, and database integration. Use when working with FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDatabaseModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora database migration modules for Flyway and Liquibase, migration configuration, startup behavior, and database integration; key triggers include FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDatabaseModule."
---

Модуль для миграции базы данных вместе с запуском сервиса.

## Flyway { #flyway }

Модуль для миграции базы данных с помощью инструмента [Flyway](https://documentation.red-gate.com/fd).

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-flyway"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends FlywayJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-flyway")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : FlywayJdbcDatabaseModule
    ```

Требует подключения [JDBC модуля](database-jdbc.md).

### Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `FlywayConfig` (указаны значения по умолчанию):

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

    1. Включена ли миграция базы данных при старте приложения. Если `false`, миграции выполняться не будут.
    2. Пути директорий где искать скрипты миграции
    3. Выполнять ли миграции внутри транзакции
    4. Проверять ли контрольные суммы существующих миграций перед выполнением. Если не совпадают — будет ошибка
    5. Разрешать ли смешивание транзакционных и нетранзакционных SQL-операций в одной миграции. Если включено, 
       вся миграция будет выполняться **без транзакции**, чтобы избежать ошибок в БД, где некоторые операции не могут
       выполняться внутри транзакции.
       Эта настройка актуальна только для СУБД, которые не поддерживают выполнение отдельных операций внутри транзакции:
       PostgreSQL, Aurora PostgreSQL, SQL Server и SQLite.
    6. Дополнительные свойства конфигурации в формате ключ-значение для `Flyway#configurationProperties`

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

    1. Включена ли миграция базы данных при старте приложения. Если `false`, миграции выполняться не будут.
    2. Пути директорий где искать скрипты миграции
    3. Выполнять ли миграции внутри транзакции
    4. Проверять ли контрольные суммы существующих миграций перед выполнением. Если не совпадают — будет ошибка
    5. Разрешать ли смешивание транзакционных и нетранзакционных SQL-операций в одной миграции. Если включено, 
       вся миграция будет выполняться **без транзакции**, чтобы избежать ошибок в БД, где некоторые операции не могут
       выполняться внутри транзакции.
       Эта настройка актуальна только для СУБД, которые не поддерживают выполнение отдельных операций внутри транзакции:
       PostgreSQL, Aurora PostgreSQL, SQL Server и SQLite.
    6. Дополнительные свойства конфигурации в формате ключ-значение для `Flyway#configurationProperties`

## Liquibase { #liquibase }

Модуль для миграции базы данных с помощью инструмента [Liquibase](https://www.liquibase.com/supported-databases).

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-liquibase"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LiquibaseJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-liquibase")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LiquibaseJdbcDatabaseModule
    ```

Требует подключения [JDBC модуля](database-jdbc.md).

### Конфигурация { #configuration-2 }

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

## Совет { #recommendations }

???+ warning "Совет"

    **Мы не советуем** использовать модули миграции для работы приложений в окружении где есть горизонтальное масштабирование 
    посредствам увелечения количества реплик рабочего приложения. Так как это будет вести за собой вызов миграции на каждую запущенную реплику.
    Также имейте в виду что каждый перезапуск приложения также будет вызывать миграции.

    В таких случаях советуем например использовать для локальной разработки [Flyway Gradle plugin](https://plugins.gradle.org/plugin/org.flywaydb.flyway),
    для тестов использовать запуск Flyway из кода после запуска базы данных, для боевого окружения Kubernetes использовать [K8S Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
    либо миграцию из CI через [Flyway Gradle plugin](https://plugins.gradle.org/plugin/org.flywaydb.flyway).
