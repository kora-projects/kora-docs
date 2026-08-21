---
search:
  exclude: true
title: Интеграционное тестирование с Kora
summary: Learn comprehensive integration testing for Kora JDBC applications with real PostgreSQL, Flyway migrations, and KoraAppTest
tags: testing, integration-tests, testcontainers, postgres, flyway
---

# Интеграционное тестирование с Kora { #integration-testing-kora }

Это руководство знакомит с интеграционным тестированием JDBC-приложений Kora. В нем рассматривается, как запускать граф приложения на настоящей инфраструктуре PostgreSQL, как Testcontainers
предоставляет настройки подключения к базе данных, и как репозитории, миграции, конфигурация и службы проверяются вместе. Вы также увидите, как интеграционные тесты находят проблемы связывания и
постоянного хранения, которые модульные тесты намеренно обходят.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Testing Integration App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-testing-integration-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Testing Integration App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-testing-integration-app).

## Что вы создадите { #youll-build }

Вы создадите интеграционные тесты, которые покрывают:

- **проверку настоящей базы данных**: запуск тестов на настоящем экземпляре PostgreSQL
- **проверку миграций**: уверенность, что миграции Flyway применяются корректно
- **интеграцию службы и репозитория**: проверку полного потока постоянного хранения
- **тестирование переопределений конфигурации**: внедрение конфигурации времени выполнения из контейнеров
- **детерминированную изоляцию тестов**: чистое и повторяемое поведение тестов

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- Docker (для Testcontainers)
- текстовый редактор или среда разработки
- пройденное руководство [Интеграция с базой данных](database-jdbc.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по базе данных JDBC"

    Это руководство предполагает, что вы уже прошли **[Интеграцию с базой данных](database-jdbc.md)** и у вас уже есть реализация JDBC-репозитория, миграции Flyway в `db/migration`, `UserService`, связанный с настоящим JDBC-репозиторием, и рабочее CRUD-поведение в приложении с базой данных.

    Если вы еще не прошли руководство по базе данных JDBC, сначала сделайте это, потому что здесь проверяется настоящий поток службы с базой данных через Testcontainers.

## Обзор { #overview }

Интеграционное тестирование проверяет, как код приложения ведет себя при работе с настоящей инфраструктурой. Оно находится между компонентными тестами и тестами по принципу черного ящика: шире, чем тест службы с
подменами, но уже, чем запуск всего приложения как внешнего процесса.

Ключевое отличие от компонентного теста в том, что инфраструктура является частью проверяемого поведения. Метод репозитория нельзя считать полностью доказанным, пока его SQL не выполнится на базе
данных того же типа, которую использует приложение.

### Граница интеграции { #integration-boundary }

В этом руководстве границей интеграции является слой службы и репозитория, подкрепленный настоящей базой данных [PostgreSQL](https://www.postgresql.org/docs/). Тест все еще выполняется внутри
процесса [JUnit](https://junit.org/junit5/docs/current/user-guide/) и использует тестовый граф Kora, но база данных не подменяется. Это позволяет тесту проверить поведение, которое существует только
тогда, когда SQL, миграции, конфигурация подключения и сопоставление строк работают вместе.

Интеграционные тесты особенно ценны для:

- выполнения настоящего SQL на PostgreSQL
- сопоставления записей и колонок
- совместимости миграций Flyway с кодом репозитория
- постраничной выдачи, сортировки, обновления и удаления на настоящих данных
- логики службы, которая зависит от семантики постоянного хранения

### Тесты и Testcontainers { #tests-plus-testcontainers }

Подробнее о расширенном тестовом графе, замене компонентов и модификации контейнера смотрите в разделах [Test graph](../documentation/junit5.md#test-graph) и [модификации контейнера](../documentation/junit5.md#container-modification).

Kora предоставляет граф приложения; [Testcontainers](https://java.testcontainers.org/) предоставляет одноразовую инфраструктуру. Тест запускает контейнер PostgreSQL, передает значения подключения в
граф, а затем выполняет компоненты приложения с настоящим состоянием базы данных.

Это сочетание мощное, потому что код репозитория генерируется и связывается так же, как в приложении, а база данных изолирована на каждый запуск тестов. Вы получаете реалистичное поведение постоянного
хранения без необходимости вручную подготовленной локальной базы данных.

### Интеграционники или черная коробка { #integration-black-box-tests }

Интеграционные тесты обычно вызывают компоненты напрямую. Тесты по принципу черного ящика вызывают открытый API работающего приложения. Это значит, что интеграционные тесты лучше подходят для сфокусированной
обратной связи по постоянному хранению, а тесты по принципу черного ящика лучше доказывают полный путь запроса.

Используйте интеграционные тесты, когда вопрос звучит так: "работает ли эта логика приложения с настоящей инфраструктурой?" Используйте тесты по принципу черного ящика, когда вопрос звучит так: "ведет ли себя
развернутое приложение корректно с точки зрения клиента?"

Практический ход такой:

1. добавить зависимости Kora test и Testcontainers
2. запустить PostgreSQL через Testcontainers
3. передать настройки подключения контейнера в граф Kora
4. выполнить миграции на тестовой базе данных
5. вызвать службы и репозитории, управляемые графом
6. проверить поведение постоянного хранения на настоящем состоянии базы данных

## Зависимости { #dependencies }

В этом руководстве тесты живут в отдельном Gradle-модуле, а не внутри модуля самого приложения. Поэтому список зависимостей выглядит длиннее, чем в обычном `src/test` рядом с production-кодом:
тестовый модуль должен явно подключить и приложение, и те Kora-модули, которые нужны для сборки тестового графа, чтения конфигурации, JDBC, Flyway, JSON, HTTP-модулей и логирования.

Эти зависимости не "протекают" транзитивно из сервиса как полноценная тестовая среда. Сервисный модуль отдает свой API и скомпилированный код, но отдельный тестовый модуль сам описывает, из каких
частей собрать тестовую среду выполнения. Если бы интеграционные тесты лежали прямо в модуле приложения, большая часть этих зависимостей уже была бы доступна из основного `build.gradle`, и отдельно
повторять их в таком объеме не пришлось бы.

===! ":fontawesome-brands-java: `Java`"

    Добавьте следующие тестовые зависимости в `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        testImplementation platform("org.junit:junit-bom:5.14.3")

        testRuntimeOnly "org.postgresql:postgresql:42.7.7"

        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation project(":guide-database-jdbc-app")
        testImplementation "ru.tinkoff.kora:config-hocon"
        testImplementation "ru.tinkoff.kora:database-flyway"
        testImplementation "ru.tinkoff.kora:database-jdbc"
        testImplementation "ru.tinkoff.kora:http-client-common"
        testImplementation "ru.tinkoff.kora:http-server-undertow"
        testImplementation "ru.tinkoff.kora:json-module"
        testImplementation "ru.tinkoff.kora:logging-logback"
        testImplementation "ru.tinkoff.kora:test-junit5"
        testImplementation "org.testcontainers:junit-jupiter:1.21.4"
        testImplementation "org.testcontainers:postgresql:1.21.4"
    }

    test {
        useJUnitPlatform()
        filter {
            excludeTestsMatching '*$*'
            excludeTestsMatching "*TestApplication"
        }
        testLogging {
            showStandardStreams(true)
            events("passed", "skipped", "failed")
            exceptionFormat("full")
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте следующие тестовые зависимости в `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        testImplementation(platform("org.junit:junit-bom:5.14.3"))

        testRuntimeOnly("org.postgresql:postgresql:42.7.7")

        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation(project(":guide-database-jdbc-app"))
        testImplementation("ru.tinkoff.kora:config-hocon")
        testImplementation("ru.tinkoff.kora:database-flyway")
        testImplementation("ru.tinkoff.kora:database-jdbc")
        testImplementation("ru.tinkoff.kora:http-client-common")
        testImplementation("ru.tinkoff.kora:http-server-undertow")
        testImplementation("ru.tinkoff.kora:json-module")
        testImplementation("ru.tinkoff.kora:logging-logback")
        testImplementation("ru.tinkoff.kora:test-junit5")
        testImplementation("org.testcontainers:junit-jupiter:1.21.4")
        testImplementation("org.testcontainers:postgresql:1.21.4")
    }

    tasks.test {
        useJUnitPlatform()
        filter {
            excludeTestsMatching('*$*')
            excludeTestsMatching("*TestApplication")
        }
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
    ```

!!! note "Включите генерацию подмодуля в JDBC-приложении"

    Добавьте генерацию подмодуля в **настоящий граф приложения** (`guide-database-jdbc-app`), а не в компиляцию тестов.

    ===! ":fontawesome-brands-java: `Java`"

        Добавьте в `guide-database-jdbc-app/build.gradle`:

        ```groovy title="guide-database-jdbc-app/build.gradle"
        tasks.named("compileJava", JavaCompile) {
            options.compilerArgs += ['-Akora.app.submodule.enabled=true']
        }
        ```

    === ":simple-kotlin: `Kotlin`"

        Добавьте в `guide-kotlin-database-jdbc-app/build.gradle.kts`:

        ```kotlin title="guide-kotlin-database-jdbc-app/build.gradle.kts"
        ksp {
            arg("kora.app.submodule.enabled", "true")
        }
        ```

## Тестовый граф { #test-graph }

Перед написанием интеграционных тестовых методов создайте отдельный `TestApplication`.
Он расширяет промышленный `Application`, но добавляет **тестовый репозиторий** с `deleteAll()` для очистки.
Так промышленный `UserRepository` остается сфокусированным на поведении приложения, а тестовые утилиты переносятся в область тестов.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/ru/tinkoff/kora/guide/testingintegration/TestApplication.java`:

    ```java
    package ru.tinkoff.kora.guide.testingintegration;

    import java.util.List;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.common.annotation.Root;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;
    import ru.tinkoff.kora.database.jdbc.JdbcRepository;
    import ru.tinkoff.kora.guide.databasejdbc.Application;
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserDAO;

    @KoraApp
    public interface TestApplication extends Application {

        @Repository
        interface TestUserRepository extends JdbcRepository {

            @Query("SELECT id, name, email, created_at FROM users ORDER BY id")
            List<UserDAO> findAll();

            @Query("DELETE FROM users")
            void deleteAll();
        }

        @Tag(TestApplication.class)
        @Root
        default String testRoot(TestUserRepository ignored) {
            return "test-root";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/test/kotlin/ru/tinkoff/kora/guide/testingintegration/TestApplication.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.testingintegration

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.common.annotation.Root
    import ru.tinkoff.kora.database.common.annotation.Query
    import ru.tinkoff.kora.database.common.annotation.Repository
    import ru.tinkoff.kora.database.jdbc.JdbcRepository
    import ru.tinkoff.kora.guide.databasejdbc.Application
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserDAO

    @KoraApp
    interface TestApplication : Application {

        @Repository
        interface TestUserRepository : JdbcRepository {

            @Query("SELECT id, name, email, created_at FROM users ORDER BY id")
            fun findAll(): List<UserDAO>

            @Query("DELETE FROM users")
            fun deleteAll()
        }

        @Tag(TestApplication::class)
        @Root
        fun testRoot(ignored: TestUserRepository): String = "test-root"
    }
    ```

Теперь создайте основу интеграционного теста с:

- `@Testcontainers` для управления жизненным циклом контейнера
- `PostgreSQLContainer` как настоящей базой данных для интеграционных проверок
- явным тайм-аутом запуска и потребителем журналов контейнера для упрощения отладки
- `@KoraAppTest(TestApplication...)` для запуска тестового графа
- переопределением конфигурации времени выполнения через JDBC-значения контейнера

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/ru/tinkoff/kora/guide/testingintegration/UserServiceIntegrationPostgresTest.java`:

    ```java
    package ru.tinkoff.kora.guide.testingintegration;

    import java.time.Duration;
    import org.jetbrains.annotations.NotNull;
    import org.junit.jupiter.api.BeforeEach;
    import org.slf4j.LoggerFactory;
    import org.testcontainers.containers.PostgreSQLContainer;
    import org.testcontainers.containers.output.Slf4jLogConsumer;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;
    import ru.tinkoff.kora.guide.databasejdbc.service.UserService;
    import ru.tinkoff.kora.guide.testingintegration.TestApplication.TestUserRepository;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier;
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification;
    import ru.tinkoff.kora.test.extension.junit5.TestComponent;

    @Testcontainers
    @KoraAppTest(TestApplication.class)
    class UserServiceIntegrationPostgresTest implements KoraAppTestConfigModifier {

        @Container
        static final PostgreSQLContainer<?> POSTGRES =
                new PostgreSQLContainer<>("postgres:16-alpine")
                        .withStartupTimeout(Duration.ofSeconds(30))
                        .withLogConsumer(new Slf4jLogConsumer(LoggerFactory.getLogger(PostgreSQLContainer.class)));

        @TestComponent
        private UserService userService;

        @TestComponent
        private TestUserRepository testUserRepository;

        @NotNull
        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                    db {
                      jdbcUrl = ${POSTGRES_JDBC_URL}
                      username = ${POSTGRES_USER}
                      password = ${POSTGRES_PASS}
                      poolName = "kora-test"
                    }
                    flyway {
                      locations = "db/migration"
                    }
                    """)
                    .withSystemProperty("POSTGRES_JDBC_URL", POSTGRES.getJdbcUrl())
                    .withSystemProperty("POSTGRES_USER", POSTGRES.getUsername())
                    .withSystemProperty("POSTGRES_PASS", POSTGRES.getPassword());
        }

        @BeforeEach
        void cleanup() {
            testUserRepository.deleteAll();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/test/kotlin/ru/tinkoff/kora/guide/testingintegration/UserServiceIntegrationPostgresTest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.testingintegration

    import java.time.Duration
    import org.junit.jupiter.api.BeforeEach
    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.PostgreSQLContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers
    import ru.tinkoff.kora.guide.databasejdbc.service.UserService
    import ru.tinkoff.kora.guide.testingintegration.TestApplication.TestUserRepository
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification
    import ru.tinkoff.kora.test.extension.junit5.TestComponent

    @Testcontainers
    @KoraAppTest(TestApplication::class)
    class UserServiceIntegrationPostgresTest : KoraAppTestConfigModifier {

        companion object {
            @Container
            @JvmStatic
            val POSTGRES = PostgreSQLContainer("postgres:16-alpine")
                .withStartupTimeout(Duration.ofSeconds(30))
                .withLogConsumer(Slf4jLogConsumer(LoggerFactory.getLogger(PostgreSQLContainer::class.java)))
        }

        @TestComponent
        lateinit var userService: UserService

        @TestComponent
        lateinit var testUserRepository: TestUserRepository

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofString(
                """
                db {
                  jdbcUrl = \${POSTGRES_JDBC_URL}
                  username = \${POSTGRES_USER}
                  password = \${POSTGRES_PASS}
                  poolName = "kora-test"
                }
                flyway {
                  locations = "db/migration"
                }
                """.trimIndent()
            )
                .withSystemProperty("POSTGRES_JDBC_URL", POSTGRES.jdbcUrl)
                .withSystemProperty("POSTGRES_USER", POSTGRES.username)
                .withSystemProperty("POSTGRES_PASS", POSTGRES.password)
        }

        @BeforeEach
        fun cleanup() {
            testUserRepository.deleteAll()
        }
    }
    ```

`config()` в этом тесте подменяет не код приложения, а конфигурацию, с которой `@KoraAppTest` собирает тестовый граф. Сначала `KoraConfigModification.ofString(...)` добавляет небольшой HOCON-фрагмент:
в нем описаны настройки `db` и `flyway`, которые нужны JDBC-пулу и миграциям. Значения подключения не зашиты строками прямо в конфиг, а вынесены в `${POSTGRES_JDBC_URL}`, `${POSTGRES_USER}` и
`${POSTGRES_PASS}`.

Затем `withSystemProperty(...)` подставляет реальные значения из запущенного `PostgreSQLContainer`. Testcontainers каждый раз может выдать другой порт, имя пользователя или пароль, поэтому тест не
должен полагаться на заранее известный `localhost:5432`. Когда Kora читает конфигурацию, placeholders уже разрешаются через системные свойства, и граф получает обычный `JdbcDatabase`, но подключенный
к одноразовой базе данных конкретного тестового запуска.

Это полезно сразу в нескольких местах: рабочая конфигурация приложения не меняется ради тестов, тесты не зависят от локальной базы разработчика, а один и тот же код приложения проверяется с настоящим
PostgreSQL и настоящими миграциями. При этом вы по-прежнему можете точечно менять только нужные настройки, не переписывая весь конфигурационный файл.

## Написание тестов { #tests }

Теперь добавьте настоящие интеграционные тестовые методы в тот же класс `UserServiceIntegrationPostgresTest`.
Контейнер намеренно настроен с явным тайм-аутом запуска и подключенными журналами, чтобы проблемы запуска было легче диагностировать.
Эти методы проверяют поведение службы и сохраненное состояние на настоящем PostgreSQL.

===! ":fontawesome-brands-java: `Java`"

    Добавьте импорты:

    ```java
    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertTrue;

    import java.util.List;
    import org.junit.jupiter.api.Test;
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserRequest;
    ```

    Добавьте тестовые методы:

    ```java
    @Test
    void createUser_ShouldPersistUserInDatabase() {
        var result = userService.createUser(new UserRequest("John", "john@example.com"));

        assertEquals("John", result.name());
        assertTrue(Long.parseLong(result.id()) > 0);
        assertEquals(1, testUserRepository.findAll().size());
    }

    @Test
    void getUsers_WithPagination_ShouldReturnCorrectPage() {
        List.of(
                        new UserRequest("Alice", "alice@example.com"),
                        new UserRequest("Bob", "bob@example.com"),
                        new UserRequest("Charlie", "charlie@example.com"),
                        new UserRequest("David", "david@example.com"))
                .forEach(userService::createUser);

        var result = userService.getUsers(1, 2, "name");

        assertEquals(2, result.size());
        assertEquals("Charlie", result.get(0).name());
        assertEquals("David", result.get(1).name());
    }

    @Test
    void updateUser_ShouldUpdateUserInDatabase() {
        var created = userService.createUser(new UserRequest("John", "john@example.com"));

        var updated = userService.updateUser(created.id(), new UserRequest("John Updated", "john.updated@example.com"));

        assertEquals("John Updated", updated.name());
    }

    @Test
    void deleteUser_ShouldRemoveUserFromDatabase() {
        var created = userService.createUser(new UserRequest("John", "john@example.com"));

        userService.deleteUser(created.id());

        assertEquals(0, testUserRepository.findAll().size());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте импорты:

    ```kotlin
    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertTrue
    import org.junit.jupiter.api.Test
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserRequest
    ```

    Добавьте тестовые методы:

    ```kotlin
    @Test
    fun createUserShouldPersistUserInDatabase() {
        val result = userService.createUser(UserRequest("John", "john@example.com"))

        assertEquals("John", result.name())
        assertTrue(result.id().toLong() > 0)
        assertEquals(1, testUserRepository.findAll().size)
    }

    @Test
    fun getUsersWithPaginationShouldReturnCorrectPage() {
        listOf(
            UserRequest("Alice", "alice@example.com"),
            UserRequest("Bob", "bob@example.com"),
            UserRequest("Charlie", "charlie@example.com"),
            UserRequest("David", "david@example.com")
        ).forEach(userService::createUser)

        val result = userService.getUsers(1, 2, "name")

        assertEquals(2, result.size)
        assertEquals("Charlie", result[0].name())
        assertEquals("David", result[1].name())
    }

    @Test
    fun updateUserShouldUpdateUserInDatabase() {
        val created = userService.createUser(UserRequest("John", "john@example.com"))

        val updated = userService.updateUser(created.id(), UserRequest("John Updated", "john.updated@example.com"))

        assertEquals("John Updated", updated.name())
    }

    @Test
    fun deleteUserShouldRemoveUserFromDatabase() {
        val created = userService.createUser(UserRequest("John", "john@example.com"))

        userService.deleteUser(created.id())

        assertEquals(0, testUserRepository.findAll().size)
    }
    ```

## Тестирование { #testing }

Запустите интеграционные тесты через Gradle:

```bash
# Запустить все тесты
./gradlew test

# Запустить с подробными журналами
./gradlew test --info
```

!!! tip "Примечания к выполнению"

    - Docker должен быть запущен до старта тестов.
    - Первый запуск обычно медленнее из-за загрузки образов.
    - Оставьте журналирование тестов включенным, чтобы упростить диагностику запуска и миграций.

## Тестовое покрытие { #coverage }

Используйте стандартные отчеты Gradle для диагностики интеграционных тестов:

```bash
# Выполнить тесты и сформировать отчеты
./gradlew test

# Сформировать отчет покрытия JaCoCo
./gradlew jacocoTestReport
```

Интеграционные сбои обычно проще всего отлаживать через:

- `build/reports/tests/test/index.html`
- журналы запуска контейнера в выводе Gradle
- SQL/журналы миграций от компонентов Flyway и JDBC

!!! tip "Миграции Flyway в тестах"

    Миграции Flyway можно запускать напрямую в жизненном цикле тестов, а не полагаться на запуск Flyway внутри приложения.
    Такой подход полезен, когда нужен более строгий контроль настройки схемы на набор тестов или на тестовый класс.
    В этом руководстве для простоты мы оставляем миграцию Flyway в запуске приложения, но оба подхода допустимы.

## Лучшие практики { #best-practices }

**Проектирование интеграционных тестов:**

- Держите тестовые сценарии сфокусированными на бизнес-поведении (создание, чтение, обновление, удаление, постраничная выдача)
- Проверяйте и ответ службы, и состояние базы данных
- Используйте детерминированные поля сортировки для проверок постраничной выдачи
- Избегайте скрытого связывания между тестами

**Изоляция данных:**

- Очищайте тестовые данные в `@BeforeEach`
- Используйте уникальные тестовые записи там, где возможны пересечения
- Не опирайтесь на идентификаторы из предыдущих тестовых методов
- Держите каждый тест независимо исполняемым

**Стабильность инфраструктуры:**

- Используйте явные тайм-ауты запуска для контейнеров
- Всегда внедряйте JDBC URL/пользователя/пароль из getter-методов контейнера
- Держите расположения Flyway явными в тестовой конфигурации
- Предпочитайте значения контейнера по умолчанию жестко заданным учетным данным БД

## Итоги { #summary }

Интеграционное тестирование дает высокую уверенность, что ваше JDBC-приложение Kora корректно работает с настоящим PostgreSQL и настоящими миграциями. Оно проверяет слой постоянного хранения,
связывание DI и поведение службы в реалистичных условиях, оставаясь быстрее и уже, чем полноценное тестирование API черного ящика.

В этом руководстве вы настроили:

- настройку PostgreSQL на основе Testcontainers
- переопределения конфигурации Kora для значений контейнера времени выполнения
- настоящую интеграционную проверку `UserService` с тестовыми вспомогательными методами репозитория
- повторяемую очистку и детерминированное выполнение тестов

## Ключевые понятия { #key-concepts }

**Область интеграционного тестирования:**

- настоящая инфраструктура, настоящий SQL, настоящие миграции
- фокус на поведении службы + репозитория + БД
- высокая уверенность для потоков постоянного хранения

**Тестовая инфраструктура Kora:**

- `@KoraAppTest` для запуска настоящего графа приложения
- `@TestComponent` для внедрения проверяемых компонентов
- `KoraAppTestConfigModifier` для переопределений конфигурации времени выполнения

**Конфигурация от контейнеров:**

- получайте сведения подключения из `PostgreSQLContainer`
- передавайте значения через `withSystemProperty(...)`
- сохраняйте конфигурацию переносимой между окружениями

## Устранение неполадок { #troubleshooting }

**Контейнер не запускается:**

- Убедитесь, что демон Docker запущен
- Проверьте конфликты портов/ресурсов в журналах контейнера
- Увеличьте тайм-аут запуска, если окружение медленное

**Ошибки миграций:**

- Проверьте, что миграции находятся в `src/main/resources/db/migration`
- Убедитесь, что `flyway.locations = "db/migration"` присутствует в тестовой конфигурации
- Проверьте вывод Flyway в журналах Gradle

**Проблемы подключения к базе данных:**

- Используйте JDBC URL/учетные данные только из getter-методов контейнера
- Избегайте жестко заданных localhost-учетных данных в тестовой конфигурации
- Убедитесь, что драйвер PostgreSQL доступен во время выполнения тестов
- Добавьте явные тестовые зависимости `database-jdbc` и `database-flyway`, когда TestApplication расширяет граф приложения из другого модуля

**Нестабильные или зависающие тесты:**

- Оставьте `testLogging` с `showStandardStreams(true)`
- Используйте тестовый запускатель среда разработки для сфокусированной отладки, когда это нужно
- Проверьте логику очистки и предположения об изоляции тестов

**Предупреждение `Expected @KoraApp as SubModule`:**

Если ваш тестовый модуль расширяет `Application` из другого модуля и вы видите предупреждения вроде:

- `Expected @KoraApp as SubModule, but Submodule implementation not found`

включите генерацию подмодуля в **исходном модуле приложения**:

===! ":fontawesome-brands-java: `Java`"

    Добавьте в `guide-database-jdbc-app/build.gradle`:

    ```groovy title="guide-database-jdbc-app/build.gradle"
    tasks.named("compileJava", JavaCompile) {
        options.compilerArgs += ["-Akora.app.submodule.enabled=true"]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в `guide-kotlin-database-jdbc-app/build.gradle.kts`:

    ```kotlin title="guide-kotlin-database-jdbc-app/build.gradle.kts"
    ksp {
        arg("kora.app.submodule.enabled", "true")
    }
    ```

**JUnit обнаруживает сгенерированный `$TestApplicationImpl`:**

Если обнаружение тестов падает до выполнения (например, с `NoClassDefFoundError` из сгенерированных классов), исключите сгенерированные классы через фильтр тестов Gradle:

===! ":fontawesome-brands-java: `Java`"

    Добавьте в `build.gradle`:

    ```groovy title="build.gradle"
    test {
        useJUnitPlatform()
        filter {
            excludeTestsMatching '*$*'
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    tasks.test {
        useJUnitPlatform()
        filter {
            excludeTestsMatching("*${'$'}*")
        }
    }
    ```

**AccessDeniedException в кеше Gradle:**

В Windows это может происходить, когда кешированные JAR-файлы временно заблокированы другим процессом.

Попробуйте по порядку:

1. Остановить демоны: `./gradlew --stop`
2. Повторить сборку: `./gradlew test`
3. Если блокировка остается, запустите с изолированным кешем на время сеанса:
   `GRADLE_USER_HOME=.gradle-user-home ./gradlew test`

## Что дальше? { #whats-next }

- [Тестирование как черный ящик](testing-black-box.md), чтобы перейти от интеграционных тестов уровня графа к тестам упакованного приложения.
- [Наблюдаемость](observability.md), чтобы наблюдать то же приложение с базой данных через метрики, трассировки, журналы и пробы.
- [Продвинутый JDBC](database-jdbc-advanced.md), если хотите больше сценариев с репозиториями, транзакциями, преобразователями и проекциями для тестирования.
- [Кеширование](cache.md), когда повторным чтениям из базы данных нужен слой производительности.

## Помощь { #help }

Если возникли проблемы:

- сравните интеграционные тесты с [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app) и [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-jdbc-app)
- проверьте [документацию JUnit5](../documentation/junit5.md)
- проверьте [документацию по базе данных JDBC](../documentation/database-jdbc.md)
- проверьте [документацию по миграциям базы данных](../documentation/database-migration.md)
- прочитайте [документацию Testcontainers](https://www.testcontainers.org/)
