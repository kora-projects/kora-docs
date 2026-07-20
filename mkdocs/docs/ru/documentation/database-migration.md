---
description: "Explains Kora database migration modules for Flyway and Liquibase, migration configuration, startup behavior, and database integration. Use when working with FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDatabaseModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora database migration modules for Flyway and Liquibase, migration configuration, startup behavior, and database integration; key triggers include FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDatabaseModule."
---

Миграции базы данных применяют изменения схемы и справочных данных в контролируемом порядке: они создают таблицы, индексы, ограничения и выполняют другие операции `SQL`, необходимые новой версии приложения.
В Kora модули миграций привязаны к инициализации `JdbcDatabase` через `GraphInterceptor<JdbcDatabase>`: при запуске приложения `JdbcDatabase` создается как компонент графа, а метод `init()` перехватчика выполняет миграции до того, как компонент будет опубликован для остальной части графа.
Если миграция завершается ошибкой, метод `init()` выбрасывает исключение, поэтому инициализация компонента `JdbcDatabase` и построение всего графа (запуск приложения) также завершаются неудачей.
Метод `release()` перехватчика ничего не делает: миграции никогда не откатываются и не выполняются повторно при остановке приложения.

Такой подход удобен для локальной разработки, тестов и небольших установок, где приложение запускается в одном экземпляре.
Для окружений с несколькими репликами заранее выберите отдельный способ выполнения миграций, чтобы они не запускались одновременно из каждого экземпляра приложения.
Репозитории не создают схему базы данных сами: таблицы, индексы, ограничения и справочные данные должны создаваться миграциями или внешним процессом подготовки базы данных.

## Flyway { #flyway }

Модуль для миграции базы данных с помощью инструмента [Flyway](https://documentation.red-gate.com/fd).
При инициализации `JdbcDatabase` модуль вызывает `Flyway.migrate()` с настройками из секции `flyway`.
Миграции запускает `FlywayJdbcDatabaseInterceptor`, который предоставляется модулем `FlywayJdbcDatabaseModule`.
`Flyway` подключен к `SLF4J` (`loggers("slf4j")`), поэтому вывод миграций и строка с замером времени `FlyWay migration applied in ...` (журналируемая на уровне `INFO`) попадают в обычные логи приложения.

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
    3. Выполняет миграции внутри транзакции, если это поддерживается базой данных и самими операциями `SQL` (по умолчанию: `true`).
    4. Проверяет контрольные суммы уже примененных миграций перед выполнением новых (по умолчанию: `true`). Если контрольные суммы не совпадают, запуск завершится ошибкой.
    5. Разрешает смешивать транзакционные и нетранзакционные операции `SQL` в одной миграции (по умолчанию: `false`).
       Если настройка включена, вся миграция выполняется **без транзакции**, чтобы избежать ошибок в базах данных, где часть операций нельзя выполнять внутри транзакции.
       Настройка актуальна для баз данных, которые не поддерживают выполнение отдельных операций внутри транзакции: PostgreSQL, Aurora PostgreSQL, SQL Server и SQLite.
    6. Дополнительные свойства `Flyway` в формате ключ-значение (по умолчанию: `{}`).
       Через них можно передать настройки, у которых нет отдельной опции конфигурации Kora, например `schemas`, `baselineOnMigrate`, `placeholderReplacement` или `placeholders.*`.

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
    3. Выполняет миграции внутри транзакции, если это поддерживается базой данных и самими операциями `SQL` (по умолчанию: `true`).
    4. Проверяет контрольные суммы уже примененных миграций перед выполнением новых (по умолчанию: `true`). Если контрольные суммы не совпадают, запуск завершится ошибкой.
    5. Разрешает смешивать транзакционные и нетранзакционные операции `SQL` в одной миграции (по умолчанию: `false`).
       Если настройка включена, вся миграция выполняется **без транзакции**, чтобы избежать ошибок в базах данных, где часть операций нельзя выполнять внутри транзакции.
       Настройка актуальна для баз данных, которые не поддерживают выполнение отдельных операций внутри транзакции: PostgreSQL, Aurora PostgreSQL, SQL Server и SQLite.
    6. Дополнительные свойства `Flyway` в формате ключ-значение (по умолчанию: `{}`).
       Через них можно передать настройки, у которых нет отдельной опции конфигурации Kora, например `schemas`, `baselineOnMigrate`, `placeholderReplacement` или `placeholders.*`.

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
Миграции запускает `LiquibaseJdbcDatabaseInterceptor`, который предоставляется модулем `LiquibaseJdbcDatabaseModule`.

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

    1. Путь к основному файлу [`changelog`](https://docs.liquibase.com/concepts/changelogs/home.html) с описанием миграций (по умолчанию: `db/changelog/db.changelog-master.xml`).

=== ":simple-yaml: `YAML`"

    ```yaml
    liquibase:
      changelog: "db/changelog/db.changelog-master.xml" #(1)!
    ```

    1. Путь к основному файлу [`changelog`](https://docs.liquibase.com/concepts/changelogs/home.html) с описанием миграций (по умолчанию: `db/changelog/db.changelog-master.xml`).

В отличие от `Flyway`, у модуля `Liquibase` нет настройки `enabled`: если модуль подключен к графу приложения, миграции запускаются при инициализации `JdbcDatabase`.
Если миграция `Liquibase` завершается ошибкой, модуль оборачивает ее в `IllegalStateException`, и запуск приложения прерывается.

### Файлы миграций { #liquibase-files }

По умолчанию `Liquibase` ищет основной файл `changelog` в `src/main/resources/db/changelog/db.changelog-master.xml`.
`Liquibase` поддерживает разные форматы `changelog`, но в `SQL`-ориентированном проекте часто удобнее хранить миграции в форматированном `SQL`.
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

## Рекомендации { #recommendations }

???+ warning "Рекомендация"

    **Модули миграций не рекомендуется** использовать для выполнения миграций на старте приложения в горизонтально масштабируемых окружениях,
    где приложение запускается в нескольких репликах. Каждая реплика будет пытаться выполнить миграции при запуске.
    Также учитывайте, что каждый перезапуск приложения снова приводит к запуску механизма миграций.

    В таких случаях для локальной разработки используйте [Flyway Gradle Plugin](https://plugins.gradle.org/plugin/org.flywaydb.flyway),
    для тестов — запуск `Flyway` из кода после старта базы данных,
    для промышленного окружения Kubernetes — [Kubernetes Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/),
    либо выполняйте миграции отдельно из `CI`.


