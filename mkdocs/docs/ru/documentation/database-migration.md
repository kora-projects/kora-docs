---
description: "Explains Kora database migration modules for Flyway and Liquibase, migration configuration, startup behavior, and database integration. Use when working with FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDatabaseModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora database migration modules for Flyway and Liquibase, migration configuration, startup behavior, and database integration; key triggers include FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDatabaseModule."
---

Миграции базы данных применяют изменения схемы и справочных данных в контролируемом порядке: создают таблицы, индексы, ограничения и выполняют другие `SQL`-операции, необходимые новой версии приложения.
В Kora модули миграции привязываются к инициализации `JdbcDatabase`: при запуске приложения база данных создается как компонент графа, после чего перехватчик запускает миграции.
Если миграция завершается ошибкой, инициализация компонента `JdbcDatabase` и запуск приложения тоже завершаются ошибкой.
При остановке приложения модули миграции дополнительных действий не выполняют.

Такой подход удобен для локальной разработки, тестов и небольших установок, где приложение запускается в одном экземпляре.
Для окружений с несколькими репликами важно заранее выбрать отдельный способ запуска миграций, чтобы они не выполнялись одновременно из каждого экземпляра приложения.
Сами репозитории не создают схему базы данных: таблицы, индексы, ограничения и справочные данные должны появиться через миграции или внешний процесс подготовки базы данных.

## Flyway { #flyway }

Модуль для миграции базы данных с помощью инструмента [Flyway](https://documentation.red-gate.com/fd).
При инициализации `JdbcDatabase` модуль вызывает `Flyway.migrate()` с настройками из секции `flyway`.
Миграции запускает `FlywayJdbcDatabaseInterceptor`, который подключается через `FlywayJdbcDatabaseModule`.

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

Требует подключения [`JDBC`-модуля](database-jdbc.md), так как миграции выполняются через `DataSource`.
В приложении обычно подключаются оба модуля: `JdbcDatabaseModule` создает `JdbcDatabase`, а `FlywayJdbcDatabaseModule` добавляет перехватчик миграций.

### Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `FlywayConfig`:

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

    1. Включает выполнение миграций при инициализации `JdbcDatabase` (по умолчанию: `true`). Если указать `false`, модуль пропустит вызов `Flyway.migrate()`.
    2. Пути к директориям со скриптами миграций (по умолчанию: `["db/migration"]`).
    3. Выполняет миграции внутри транзакции, если это поддерживается базой данных и самими `SQL`-операциями (по умолчанию: `true`).
    4. Проверяет контрольные суммы уже примененных миграций перед выполнением новых (по умолчанию: `true`). Если контрольные суммы не совпадают, запуск завершится ошибкой.
    5. Разрешает смешивать транзакционные и нетранзакционные `SQL`-операции в одной миграции (по умолчанию: `false`).
       Если настройка включена, вся миграция будет выполняться **без транзакции**, чтобы избежать ошибок в базах данных, где часть операций нельзя выполнять внутри транзакции.
       Настройка актуальна для СУБД, которые не поддерживают выполнение отдельных операций внутри транзакции: PostgreSQL, Aurora PostgreSQL, SQL Server и SQLite.
    6. Дополнительные свойства `Flyway` в формате ключ-значение (по умолчанию: `{}`).
       Через них можно передать параметры, которых нет в отдельной конфигурации Kora, например `schemas`, `baselineOnMigrate`, `placeholderReplacement` или `placeholders.*`.

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

    1. Включает выполнение миграций при инициализации `JdbcDatabase` (по умолчанию: `true`). Если указать `false`, модуль пропустит вызов `Flyway.migrate()`.
    2. Пути к директориям со скриптами миграций (по умолчанию: `["db/migration"]`).
    3. Выполняет миграции внутри транзакции, если это поддерживается базой данных и самими `SQL`-операциями (по умолчанию: `true`).
    4. Проверяет контрольные суммы уже примененных миграций перед выполнением новых (по умолчанию: `true`). Если контрольные суммы не совпадают, запуск завершится ошибкой.
    5. Разрешает смешивать транзакционные и нетранзакционные `SQL`-операции в одной миграции (по умолчанию: `false`).
       Если настройка включена, вся миграция будет выполняться **без транзакции**, чтобы избежать ошибок в базах данных, где часть операций нельзя выполнять внутри транзакции.
       Настройка актуальна для СУБД, которые не поддерживают выполнение отдельных операций внутри транзакции: PostgreSQL, Aurora PostgreSQL, SQL Server и SQLite.
    6. Дополнительные свойства `Flyway` в формате ключ-значение (по умолчанию: `{}`).
       Через них можно передать параметры, которых нет в отдельной конфигурации Kora, например `schemas`, `baselineOnMigrate`, `placeholderReplacement` или `placeholders.*`.

### Файлы миграций { #flyway-files }

По умолчанию `Flyway` ищет миграции в `src/main/resources/db/migration`.
Обычный файл миграции имеет имя вида `V1__init_schema.sql`, где `V1` — версия, а часть после двойного подчеркивания — описание.

```text
src/main/resources/db/migration/
  V1__init_users.sql
  V2__add_user_status.sql
```

Пример простой миграции:

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL
);
```

При запуске `Flyway` создает служебную таблицу истории миграций и применяет только новые версии.
Если включена проверка `validateOnMigrate`, уже примененные файлы нельзя менять без отдельного процесса исправления истории миграций.

## Liquibase { #liquibase }

Модуль для миграции базы данных с помощью инструмента [Liquibase](https://www.liquibase.com/supported-databases).
При инициализации `JdbcDatabase` модуль получает соединение из `DataSource`, создает экземпляр `Liquibase` и вызывает `update()`.
Миграции запускает `LiquibaseJdbcDatabaseInterceptor`, который подключается через `LiquibaseJdbcDatabaseModule`.

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

Требует подключения [`JDBC`-модуля](database-jdbc.md), так как миграции выполняются через `DataSource`.
В приложении обычно подключаются оба модуля: `JdbcDatabaseModule` создает `JdbcDatabase`, а `LiquibaseJdbcDatabaseModule` добавляет перехватчик миграций.

### Конфигурация { #configuration-2 }

Пример полной конфигурации, описанной в классе `LiquibaseConfig`:

===! ":material-code-json: `HOCON`"

    ```javascript
    liquibase {
        changelog = "db/changelog/db.changelog-master.xml" //(1)!
    }
    ```

    1.  Путь к основному файлу [`changelog`](https://docs.liquibase.com/concepts/changelogs/home.html) с описанием миграций (по умолчанию: `db/changelog/db.changelog-master.xml`).

=== ":simple-yaml: `YAML`"

    ```yaml
    liquibase:
      changelog: "db/changelog/db.changelog-master.xml" #(1)!
    ```

    1.  Путь к основному файлу [`changelog`](https://docs.liquibase.com/concepts/changelogs/home.html) с описанием миграций (по умолчанию: `db/changelog/db.changelog-master.xml`).

В отличие от `Flyway`, у модуля `Liquibase` нет настройки `enabled`: если модуль подключен к графу приложения, миграции будут запускаться при инициализации `JdbcDatabase`.
Если миграция `Liquibase` завершается ошибкой, модуль оборачивает ее в `IllegalStateException`, и запуск приложения прерывается.

### Файлы миграций { #liquibase-files }

По умолчанию `Liquibase` ищет основной файл `changelog` в `src/main/resources/db/changelog/db.changelog-master.xml`.
В `Liquibase` можно использовать разные форматы `changelog`, но для `SQL`-ориентированного проекта часто удобнее хранить миграции в форматированном `SQL`.
Основной файл может подключать такие миграции через `include`.

```text
src/main/resources/db/changelog/
  db.changelog-master.xml
  changes/
    001-init-users.sql
```

Минимальный основной `changelog`:

```xml
<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

    <include file="db/changelog/changes/001-init-users.sql"/>
</databaseChangeLog>
```

Пример подключенной миграции в форматированном `SQL`:

```sql
--liquibase formatted sql

--changeset app:001-init-users
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL
);
```

## Совет { #recommendations }

???+ warning "Совет"

    **Не рекомендуется** использовать модули миграции на старте приложения в окружениях с горизонтальным масштабированием,
    где рабочее приложение запускается в нескольких репликах. Каждая реплика будет пытаться выполнить миграции при запуске.
    Также учитывайте, что каждый перезапуск приложения снова приводит к запуску механизма миграций.

    В таких случаях для локальной разработки можно использовать [Flyway Gradle Plugin](https://plugins.gradle.org/plugin/org.flywaydb.flyway),
    для тестов — запуск `Flyway` из кода после старта базы данных,
    для промышленного окружения Kubernetes — [Kubernetes Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/),
    либо отдельный запуск миграций из `CI`.
