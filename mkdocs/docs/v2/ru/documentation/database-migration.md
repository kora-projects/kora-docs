---
description: "Explains Kora database migration modules for Flyway and Liquibase, migration configuration, startup behavior, DBMS dialect artifacts, and JDBC integration. Use when working with FlywayJdbcDatabaseModule, LiquibaseJdbcDatabaseModule, FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDataSource."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora database migration modules for Flyway and Liquibase, migration configuration, migration modes, startup behavior, DBMS dialect artifacts and JDBC integration; key triggers include FlywayJdbcDatabaseModule, LiquibaseJdbcDatabaseModule, FlywayJdbcDatabaseInterceptor, LiquibaseJdbcDatabaseInterceptor, FlywayConfig, LiquibaseConfig, JdbcDataSource, Unsupported Database."
---

Миграции базы данных применяют изменения схемы и справочных данных в контролируемом порядке: они создают таблицы, индексы, ограничения и выполняют другие операции `SQL`, необходимые новой версии приложения.
В Kora модули миграций привязаны к инициализации `JdbcDataSource` через `GraphInterceptor<JdbcDataSource>`: при запуске приложения `JdbcDataSource` создается как компонент графа, а метод `afterInit()` перехватчика выполняет миграции до того, как компонент будет опубликован для остальной части графа.
Если миграция завершается ошибкой, метод `afterInit()` выбрасывает исключение, поэтому инициализация компонента `JdbcDataSource` и построение всего графа (запуск приложения) также завершаются неудачей.
Метод `beforeRelease()` перехватчика ничего не делает: миграции никогда не откатываются и не выполняются повторно при остановке приложения.

Такой подход удобен для локальной разработки, тестов и небольших установок, где приложение запускается в одном экземпляре.
Для окружений с несколькими репликами заранее выберите отдельный способ выполнения миграций, чтобы они не запускались одновременно из каждого экземпляра приложения.
Репозитории не создают схему базы данных сами: таблицы, индексы, ограничения и справочные данные должны создаваться миграциями или внешним процессом подготовки базы данных.

## Flyway { #flyway }

Модуль для миграции базы данных с помощью инструмента [Flyway](https://documentation.red-gate.com/fd).
При инициализации `JdbcDataSource` модуль собирает экземпляр `Flyway` из настроек секции `flyway` и выполняет операцию, выбранную [режимом миграции](#flyway-modes).
Миграции запускает `FlywayJdbcDatabaseInterceptor`, который предоставляется модулем `FlywayJdbcDatabaseModule`.
`Flyway` подключен к `SLF4J` (`loggers("slf4j")`), поэтому вывод миграций и строка с замером времени `FlyWay migration in mode 'MIGRATE' applied in ...` (журналируемая на уровне `INFO`) попадают в обычные логи приложения.

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:database-flyway"
    implementation "org.flywaydb:flyway-database-postgresql:13.3.0" //(1)!
    ```

    1. Поддержка конкретной СУБД, смотрите [Поддержка баз данных](#flyway-database-support).

    Модуль:
    ```java
    @KoraApp
    public interface Application extends FlywayJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:database-flyway")
    implementation("org.flywaydb:flyway-database-postgresql:13.3.0") //(1)!
    ```

    1. Поддержка конкретной СУБД, смотрите [Поддержка баз данных](#flyway-database-support).

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : FlywayJdbcDatabaseModule
    ```

Требует подключения [`JDBC`-модуля](database-jdbc.md), так как миграции выполняются через `DataSource`.
В приложении обычно подключаются оба модуля: `JdbcDatabaseModule` создает `JdbcDataSource`, а `FlywayJdbcDatabaseModule` добавляет перехватчик миграций.

### Поддержка баз данных { #flyway-database-support }

Начиная с `Flyway` 10 поддержка конкретной СУБД вынесена в отдельный артефакт, а `io.koraframework:database-flyway` приносит только `org.flywaydb:flyway-core`.
Приложение обязано добавить артефакт для своей базы данных, иначе оно падает при инициализации `JdbcDataSource`:

```text
FlywayException: Unsupported Database: PostgreSQL 16.x
```

Для PostgreSQL это артефакт `org.flywaydb:flyway-database-postgresql`, артефакты для остальных баз данных перечислены в [документации Flyway](https://documentation.red-gate.com/fd).
Версию артефакта указывайте такой же, как у `flyway-core`, который приходит вместе с `database-flyway`, — в Kora 2.0 это `13.3.0`.
Артефакт не входит в [`kora-bom`](general.md#dependencies), поэтому версию всегда требуется указывать явно.

### Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `FlywayConfig`:

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

    1. Включает выполнение миграций при инициализации `JdbcDataSource` (по умолчанию: `true`). Если указать `false`, модуль напишет в лог `FlyWay is disabled, skipping migrate...` и не будет обращаться к базе данных.
    2. Операция, которую `Flyway` выполняет при старте: `MIGRATE`, `REPAIR` или `CLEAN_MIGRATE` (по умолчанию: `MIGRATE`). Значение сопоставляется по точному имени в верхнем регистре. Смотрите [Режимы миграций](#flyway-modes).
    3. Пути к директориям со скриптами миграций (по умолчанию: `["db/migration"]`). Допускается и обычная строка — она разбивается по запятой.
    4. Выполняет миграции внутри транзакции, если это поддерживается базой данных и самими операциями `SQL` (по умолчанию: `true`).
    5. Проверяет контрольные суммы уже примененных миграций перед выполнением новых (по умолчанию: `true`). Если контрольные суммы не совпадают, запуск завершится ошибкой.
    6. Разрешает смешивать транзакционные и нетранзакционные операции `SQL` в одной миграции (по умолчанию: `false`).
       Если настройка включена, вся миграция выполняется **без транзакции**, чтобы избежать ошибок в базах данных, где часть операций нельзя выполнять внутри транзакции.
       Настройка актуальна для баз данных, которые не поддерживают выполнение отдельных операций внутри транзакции: PostgreSQL, Aurora PostgreSQL, SQL Server и SQLite.
    7. Дополнительные свойства `Flyway` в формате ключ-значение (по умолчанию: `{}`).
       Через них передаются настройки, у которых нет отдельной опции конфигурации Kora.
       Ключами служат стандартные имена свойств `Flyway` **с префиксом `flyway.`**, например `flyway.schemas`, `flyway.baselineOnMigrate`, `flyway.placeholderReplacement` или `flyway.placeholders.*`.
       Ключ без префикса `Flyway` не распознает.

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

    1. Включает выполнение миграций при инициализации `JdbcDataSource` (по умолчанию: `true`). Если указать `false`, модуль напишет в лог `FlyWay is disabled, skipping migrate...` и не будет обращаться к базе данных.
    2. Операция, которую `Flyway` выполняет при старте: `MIGRATE`, `REPAIR` или `CLEAN_MIGRATE` (по умолчанию: `MIGRATE`). Значение сопоставляется по точному имени в верхнем регистре. Смотрите [Режимы миграций](#flyway-modes).
    3. Пути к директориям со скриптами миграций (по умолчанию: `["db/migration"]`). Допускается и обычная строка — она разбивается по запятой.
    4. Выполняет миграции внутри транзакции, если это поддерживается базой данных и самими операциями `SQL` (по умолчанию: `true`).
    5. Проверяет контрольные суммы уже примененных миграций перед выполнением новых (по умолчанию: `true`). Если контрольные суммы не совпадают, запуск завершится ошибкой.
    6. Разрешает смешивать транзакционные и нетранзакционные операции `SQL` в одной миграции (по умолчанию: `false`).
       Если настройка включена, вся миграция выполняется **без транзакции**, чтобы избежать ошибок в базах данных, где часть операций нельзя выполнять внутри транзакции.
       Настройка актуальна для баз данных, которые не поддерживают выполнение отдельных операций внутри транзакции: PostgreSQL, Aurora PostgreSQL, SQL Server и SQLite.
    7. Дополнительные свойства `Flyway` в формате ключ-значение (по умолчанию: `{}`).
       Через них передаются настройки, у которых нет отдельной опции конфигурации Kora.
       Ключами служат стандартные имена свойств `Flyway` **с префиксом `flyway.`**, например `flyway.schemas`, `flyway.baselineOnMigrate`, `flyway.placeholderReplacement` или `flyway.placeholders.*`.
       Ключ без префикса `Flyway` не распознает.

### Режимы миграций { #flyway-modes }

Настройка `mode` определяет, какую операцию `Flyway` выполняет перехватчик при старте:

- `MIGRATE` — вызывает `Flyway.migrate()` и применяет миграции, которых еще нет в таблице истории миграций. Обычный режим работы приложения.
- `REPAIR` — вызывает `Flyway.repair()`: новые миграции не применяются, вместо этого чинится таблица истории — контрольные суммы пересчитываются по текущим файлам, а записи о неудачных миграциях удаляются.
  Это разовый восстановительный режим для случая, когда файл миграции был изменен осознанно; после успешного запуска верните `MIGRATE`.
- `CLEAN_MIGRATE` — вызывает `Flyway.clean()`, а затем `Flyway.migrate()`: настроенные схемы **полностью очищаются**, и миграции применяются с нуля.
  Подходит только для локальной разработки и одноразовых тестовых баз, но не для окружения с реальными данными.
  `Flyway` по умолчанию запрещает `clean`, и Kora эту настройку не меняет, поэтому режим дополнительно требует разрешить очистку через `configurationProperties { "flyway.cleanDisabled" = "false" }`.

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
При инициализации `JdbcDataSource` модуль получает соединение из `DataSource`, определяет по нему реализацию базы данных, создает экземпляр `Liquibase` и вызывает `update()`.
Миграции запускает `LiquibaseJdbcDatabaseInterceptor`, который предоставляется модулем `LiquibaseJdbcDatabaseModule`.
Поддержка конкретных баз данных входит в состав `liquibase-core`, поэтому, в отличие от `Flyway`, дополнительный артефакт диалекта не требуется.

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:database-liquibase"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LiquibaseJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:database-liquibase")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LiquibaseJdbcDatabaseModule
    ```

Требует подключения [`JDBC`-модуля](database-jdbc.md), так как миграции выполняются через `DataSource`.
В приложении обычно подключаются оба модуля: `JdbcDatabaseModule` создает `JdbcDataSource`, а `LiquibaseJdbcDatabaseModule` добавляет перехватчик миграций.

### Конфигурация { #configuration-2 }

Пример полной конфигурации, описанной в классе `LiquibaseConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    liquibase {
        changelog = "db/changelog/db.changelog-master.xml" //(1)!
    }
    ```

    1. Путь к основному файлу [`changelog`](https://docs.liquibase.com/concepts/changelogs/home.html) с описанием миграций (по умолчанию: `db/changelog/db.changelog-master.xml`).
       Файл ищется в classpath.

=== ":simple-yaml: `YAML`"

    ```yaml
    liquibase:
      changelog: "db/changelog/db.changelog-master.xml" #(1)!
    ```

    1. Путь к основному файлу [`changelog`](https://docs.liquibase.com/concepts/changelogs/home.html) с описанием миграций (по умолчанию: `db/changelog/db.changelog-master.xml`).
       Файл ищется в classpath.

В отличие от `Flyway`, у модуля `Liquibase` нет настройки `enabled`: если модуль подключен к графу приложения, миграции запускаются при инициализации `JdbcDataSource`.
Если миграция `Liquibase` завершается ошибкой, модуль пишет в лог `Error during Liquibase migration` и оборачивает ошибку в `IllegalStateException`, из-за чего запуск приложения прерывается.
Об успешном выполнении сообщает строка `Liquibase migration applied in ...` на уровне `INFO`.

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

## Пул соединений { #pool }

Миграции используют тот же пул соединений `Hikari`, что и приложение, поэтому в секции `jdbc` нужно оставить запас для инструмента миграций:

- `Flyway` во время миграции занимает **два** соединения — одно под саму миграцию, второе под управление схемой и блокировкой.
- `Liquibase` обычно работает через **одно** соединение.

Значение `jdbc.maxPoolSize` по умолчанию равно `10` и достаточно для обоих инструментов.
Если пул намеренно уменьшить до `1`, миграция `Flyway` будет ждать второе соединение до истечения `jdbc.connectionTimeout`, а затем завершит запуск приложения ошибкой.

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

Полное описание настроек пула смотрите в документации [`JDBC`-модуля](database-jdbc.md).

## Рекомендации { #recommendations }

???+ warning "Рекомендация"

    **Модули миграций не рекомендуется** использовать для выполнения миграций на старте приложения в горизонтально масштабируемых окружениях,
    где приложение запускается в нескольких репликах. Каждая реплика будет пытаться выполнить миграции при запуске.
    Также учитывайте, что каждый перезапуск приложения снова приводит к запуску механизма миграций.

    В таких случаях для локальной разработки используйте [Flyway Gradle Plugin](https://plugins.gradle.org/plugin/org.flywaydb.flyway),
    для тестов — запуск `Flyway` из кода после старта базы данных,
    для промышленного окружения Kubernetes — [Kubernetes Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/),
    либо выполняйте миграции отдельно из `CI`.

Когда миграции вынесены из приложения, `io.koraframework:database-flyway` не подключается вовсе, а схему готовит отдельный шаг.
Gradle-плагину `Flyway` артефакт СУБД нужен так же, как и модулю, но уже на classpath блока `buildscript`:

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

Gradle-плагин — это отдельная установка `Flyway`, не та, что работает внутри приложения: здесь версия артефакта следует за версией плагина, а не за `flyway-core`, который приносит `database-flyway`.
Эти версии независимы, а сборочная зависимость живет на classpath блока `buildscript`, тогда как рантаймовая — в `implementation`.

В тестах модуль миграций остается самым простым вариантом: тестовая база живет только на время одного прогона, экземпляр приложения один, а схема готовится ровно теми же миграциями, что и в промышленном окружении.
