---
search:
  exclude: true
title: Интеграционное тестирование с Kora
summary: Learn comprehensive integration testing for Kora JDBC applications with real PostgreSQL, Flyway migrations, and KoraAppTest
description: "Integration testing for Kora 2.0 JDBC applications: a test-scope @KoraApp that extends the production application, io.koraframework:test-junit5 with @KoraAppTest and @TestComponent, Testcontainers 2.0 PostgreSQLContainer, KoraAppTestConfigModifier feeding the jdbc and flyway configuration sections through withSystemProperty, Flyway dialect artifacts and the kora.app.submodule.enabled processor option."
agent:
  use_when: "Use this file for questions about running Kora 2.0 components against a real database in tests: a test-scope @KoraApp extending the application graph, @KoraAppTest with a Testcontainers PostgreSQLContainer, KoraConfigModification.ofString with the jdbc section and ${PLACEHOLDER} substitutions, org.testcontainers:testcontainers-postgresql and testcontainers-junit-jupiter coordinates, flyway-database-postgresql, kspTest and testAnnotationProcessor, and the 'Expected @KoraApp as SubModule' warning."
tags: testing, integration-tests, testcontainers, postgres, flyway
---

# Интеграционное тестирование с Kora { #integration-testing-kora }

Это руководство знакомит с интеграционным тестированием приложений Kora на JDBC. В нем рассматривается, как запускать граф приложения поверх настоящей инфраструктуры PostgreSQL, как Testcontainers
передает настройки подключения к базе данных и как репозитории, миграции, конфигурация и службы проверяются вместе. Вы также увидите, какие проблемы связывания и сохранения данных ловят интеграционные
тесты, которых модульные тесты избегают намеренно.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Testing Integration App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-testing-integration-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Testing Integration App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-testing-integration-app).

## Что вы создадите { #youll-build }

Вы создадите интеграционные тесты, которые покрывают:

- **проверку на настоящей базе данных**: запуск тестов поверх настоящего экземпляра PostgreSQL
- **проверку миграций**: уверенность, что миграции Flyway применяются корректно
- **интеграцию службы и репозитория**: проверку полных сценариев сохранения данных
- **переопределение конфигурации**: подстановку настроек контейнера во время выполнения
- **детерминированную изоляцию тестов**: чистое и повторяемое поведение тестов

## Что понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+ (эталонные приложения используют Gradle Wrapper `9.5.1`)
- Docker (для Testcontainers)
- текстовый редактор или среда разработки
- пройденное руководство [Работа с базой данных](database-jdbc.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по базе данных JDBC"

    Это руководство предполагает, что вы уже прошли **[Работа с базой данных](database-jdbc.md)** и у вас есть реализация JDBC-репозитория, миграции Flyway в `db/migration`, `UserService`, подключенный к настоящему JDBC-репозиторию, и рабочие CRUD-сценарии в приложении с базой данных.

    Если вы еще не прошли руководство по базе данных JDBC, сначала сделайте это, потому что здесь проверяется настоящий поток работы службы с базой данных через Testcontainers.

## Обзор { #overview }

Интеграционное тестирование проверяет, как код приложения ведет себя при работе с настоящей инфраструктурой. Оно находится между компонентными тестами и тестами по принципу черного ящика: шире, чем тест
службы с подменами, но уже, чем запуск всего приложения как внешнего процесса.

Ключевое отличие от компонентного теста в том, что инфраструктура становится частью проверяемого поведения. Метод репозитория нельзя считать полностью доказанным, пока его SQL не выполнится на такой же
базе данных, какую использует приложение.

### Граница интеграции { #integration-boundary }

В этом руководстве границей интеграции является слой службы и репозитория поверх настоящей базы данных [PostgreSQL](https://www.postgresql.org/docs/). Тест по-прежнему выполняется внутри
процесса [JUnit](https://junit.org/junit5/docs/current/user-guide/) и использует тестовый граф Kora, но база данных уже не подменяется. Это позволяет проверить поведение, которое существует только
тогда, когда SQL, миграции, настройки подключения и отображение строк работают вместе.

Интеграционные тесты особенно ценны для:

- настоящего выполнения SQL на PostgreSQL
- отображения записей и колонок
- совместимости миграций Flyway с кодом репозитория
- поведения пагинации, сортировки, обновления и удаления на настоящих данных
- логики службы, которая зависит от семантики хранения

JDBC-репозитории в Kora 2.0 синхронные: метод с `@Query` возвращает отображенное значение, `List`, `Optional` или `UpdateCount`, а вызывающий поток блокируется до завершения запроса. Поэтому
интеграционный тест читается как обычный код — вызвали службу, затем прочитали данные из базы и проверили — без ожиданий, без реактивных подписок и без корутинных билдеров.

### Тесты и Testcontainers { #tests-plus-testcontainers }

Подробнее о расширенных тестовых графах, подмене компонентов и изменении контейнера — в разделах [Тестовый граф](../documentation/junit5.md#test-graph) и [Изменение контейнера](../documentation/junit5.md#container-modification).

Kora дает граф приложения, а [Testcontainers](https://java.testcontainers.org/) — одноразовую инфраструктуру. Тест поднимает контейнер PostgreSQL, передает его параметры подключения в граф, а затем
работает с компонентами приложения на настоящем состоянии базы данных.

Такое сочетание сильно тем, что код репозитория генерируется и связывается точно так же, как в приложении, а база данных изолирована на каждый запуск тестов. Вы получаете реалистичное поведение
хранилища, не требуя вручную подготовленной локальной базы данных.

### Интеграционники или черная коробка { #integration-black-box-tests }

Интеграционные тесты обычно вызывают компоненты напрямую. Тесты по принципу черного ящика вызывают открытый API запущенного приложения. Поэтому интеграционные тесты лучше подходят для сфокусированной
обратной связи по хранилищу, а тесты черного ящика — для доказательства полного пути запроса.

Используйте интеграционные тесты, когда вопрос звучит как «работает ли эта логика приложения с настоящей инфраструктурой?». Используйте тесты черного ящика, когда вопрос звучит как «правильно ли ведет
себя развернутое приложение с точки зрения клиента?».

Практический ход такой:

1. добавить тестовые зависимости Kora и Testcontainers
2. поднять PostgreSQL через Testcontainers
3. передать настройки подключения контейнера в граф Kora
4. выполнить миграции на тестовой базе данных
5. вызвать службы и репозитории, управляемые графом
6. проверить поведение хранилища на настоящем состоянии базы данных

## Зависимости { #dependencies }

В этом руководстве тесты живут в отдельном модуле Gradle, а не внутри модуля приложения. Именно поэтому список зависимостей длиннее, чем для обычного `src/test` рядом с промышленным кодом: тестовый
модуль должен явно зависеть от приложения и от модулей Kora, нужных для построения тестового графа, чтения конфигурации, работы с JDBC, запуска Flyway, работы с JSON, подключения HTTP-модулей и
инициализации журналирования.

Эти зависимости не приезжают транзитивно от службы как готовая тестовая среда выполнения. Модуль службы отдает свой API и скомпилированный код, но отдельный тестовый модуль все равно сам объявляет,
какие части должны присутствовать в тестовой среде выполнения. Если бы эти интеграционные тесты лежали прямо внутри модуля приложения, большая часть зависимостей уже была бы доступна из основного
`build.gradle`, и повторять их в таком объеме не пришлось бы.

Две координаты требуют внимания. В Testcontainers `2.0` модули переименованы: расширение JUnit 5 теперь называется `org.testcontainers:testcontainers-junit-jupiter`, а модуль PostgreSQL —
`org.testcontainers:testcontainers-postgresql`, и обе несут версию Testcontainers, а не JUnit. А `org.flywaydb:flyway-core` `13` больше не включает диалекты СУБД, поэтому артефакт диалекта PostgreSQL
нужно добавить той же версии — иначе миграции падают на старте с ошибкой `Unsupported Database: PostgreSQL`.

===! ":fontawesome-brands-java: `Java`"

    Добавьте следующие тестовые зависимости в `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        testAnnotationProcessor "io.koraframework:annotation-processors" //(1)!

        testImplementation platform("org.junit:junit-bom:6.1.3")

        testRuntimeOnly "org.postgresql:postgresql:42.7.13" //(2)!

        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation project(":guide-database-jdbc-app") //(3)!
        testImplementation "io.koraframework:config-hocon"
        testImplementation "io.koraframework:database-flyway"
        testImplementation "org.flywaydb:flyway-database-postgresql:13.3.0" //(4)!
        testImplementation "io.koraframework:database-jdbc"
        testImplementation "io.koraframework:http-client-common"
        testImplementation "io.koraframework:http-server-undertow"
        testImplementation "io.koraframework:json-common"
        testImplementation "io.koraframework:logging-logback"
        testImplementation "io.koraframework:test-junit5"
        testImplementation "org.testcontainers:testcontainers-junit-jupiter:2.0.5" //(5)!
        testImplementation "org.testcontainers:testcontainers-postgresql:2.0.5"
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

    1.  Здесь это обязательно, в отличие от руководства по компонентным тестам: тестовые исходники объявляют собственный `@KoraApp` и собственный `@Repository`, поэтому обработчик аннотаций Kora должен отработать по тестовому набору исходников.
    2.  JDBC-драйвер PostgreSQL, нужен только во время выполнения.
    3.  Модуль приложения, граф которого расширяет тест.
    4.  Артефакт диалекта Flyway той же версии, что и `flyway-core` из BOM Kora.
    5.  Имена модулей Testcontainers `2.0`. Старые координаты `org.testcontainers:junit-jupiter` и `org.testcontainers:postgresql` остановились на `1.21.x`.

=== ":simple-kotlin: `Kotlin`"

    Добавьте следующие тестовые зависимости в `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        kspTest("io.koraframework:symbol-processors:2.0.0.RC1") //(1)!

        testImplementation(platform("org.junit:junit-bom:6.1.3"))

        testRuntimeOnly("org.postgresql:postgresql:42.7.13") //(2)!

        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation(project(":guide-database-jdbc-app")) //(3)!
        testImplementation("io.koraframework:config-hocon")
        testImplementation("io.koraframework:database-flyway")
        testImplementation("org.flywaydb:flyway-database-postgresql:13.3.0") //(4)!
        testImplementation("io.koraframework:database-jdbc")
        testImplementation("io.koraframework:http-client-common")
        testImplementation("io.koraframework:http-server-undertow")
        testImplementation("io.koraframework:json-common")
        testImplementation("io.koraframework:logging-logback")
        testImplementation("io.koraframework:test-junit5")
        testImplementation("org.testcontainers:testcontainers-junit-jupiter:2.0.5") //(5)!
        testImplementation("org.testcontainers:testcontainers-postgresql:2.0.5")
    }

    kotlin {
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") } //(6)!
    }

    tasks.test {
        useJUnitPlatform()
        filter {
            excludeTestsMatching("*${'$'}*")
            excludeTestsMatching("*TestApplication")
        }
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
    ```

    1.  Здесь это обязательно, в отличие от руководства по компонентным тестам: тестовые исходники объявляют собственный `@KoraApp` и собственный `@Repository`, поэтому KSP должен отработать по тестовому набору исходников. Конфигурация `ksp` покрывает только основной набор.
    2.  JDBC-драйвер PostgreSQL, нужен только во время выполнения.
    3.  Модуль приложения, граф которого расширяет тест.
    4.  Артефакт диалекта Flyway той же версии, что и `flyway-core` из BOM Kora.
    5.  Имена модулей Testcontainers `2.0`. Старые координаты `org.testcontainers:junit-jupiter` и `org.testcontainers:postgresql` остановились на `1.21.x`.
    6.  Каталог, куда KSP пишет сгенерированный тестовый граф. Без этой строки компилятор и среда разработки не увидят `TestApplicationGraph`.

!!! note "Включите генерацию подмодуля в приложении JDBC"

    Генерация подмодуля добавляется в **настоящий граф приложения** (`guide-database-jdbc-app`), а не в компиляцию тестов. Она делает `@KoraApp` приложения пригодным для переиспользования как модуль —
    именно это и нужно тестовому `@KoraApp`, который его расширяет.

    ===! ":fontawesome-brands-java: `Java`"

        Добавьте в `guide-database-jdbc-app/build.gradle`:

        ```groovy title="guide-database-jdbc-app/build.gradle"
        tasks.named("compileJava", JavaCompile) {
            options.compilerArgs += ["-Akora.app.submodule.enabled=true"]
        }
        ```

    === ":simple-kotlin: `Kotlin`"

        Добавьте в `guide-database-jdbc-app/build.gradle.kts`:

        ```kotlin title="guide-database-jdbc-app/build.gradle.kts"
        ksp {
            arg("kora.app.submodule.enabled", "true")
        }
        ```

## Тестовый граф { #test-graph }

Прежде чем писать методы интеграционных тестов, создайте отдельный `TestApplication`.
Он расширяет промышленный `Application`, но добавляет **репозиторий только для тестов** с методом `deleteAll()` для очистки данных.
Так промышленный `UserRepository` остается сосредоточенным на поведении приложения, а тестовые вспомогательные средства уезжают в тестовую область.

Сам `TestApplication` помечен аннотацией `@KoraApp`, поэтому обработчик Kora генерирует для тестового набора исходников второй граф. Все, что объявляет промышленное приложение, наследуется; тест
добавляет только то, что нужно ему. Метод с `@Root` существует, чтобы `TestUserRepository` вообще был создан, хотя от него не зависит ни один другой компонент — без корня Kora выбросила бы его из графа
как недостижимый. Маркер `@Tag(TestApplication.class)` отличает этот корень от компонентов приложения того же типа `String`.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/io/koraframework/guide/testingintegration/TestApplication.java`:

    ```java
    package io.koraframework.guide.testingintegration;

    import java.util.List;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.common.annotation.Root;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.database.common.annotation.Query;
    import io.koraframework.database.common.annotation.Repository;
    import io.koraframework.database.jdbc.JdbcRepository;
    import io.koraframework.guide.databasejdbc.Application;
    import io.koraframework.guide.databasejdbc.repository.UserDAO;

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

    Создайте `src/test/kotlin/io/koraframework/guide/testingintegration/TestApplication.kt`:

    ```kotlin
    package io.koraframework.guide.testingintegration

    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.common.annotation.Root
    import io.koraframework.common.annotation.Tag
    import io.koraframework.database.common.annotation.Query
    import io.koraframework.database.common.annotation.Repository
    import io.koraframework.database.jdbc.JdbcRepository
    import io.koraframework.guide.databasejdbc.Application
    import io.koraframework.guide.databasejdbc.repository.UserDAO

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

Теперь создайте основу интеграционного теста:

- `@Testcontainers` управляет жизненным циклом контейнеров
- `PostgreSQLContainer` служит настоящей базой данных для интеграционных проверок
- явный таймаут запуска и потребитель журналов контейнера упрощают отладку
- `@KoraAppTest(TestApplication...)` поднимает тестовый граф
- переопределение конфигурации во время выполнения подставляет JDBC-значения контейнера

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/io/koraframework/guide/testingintegration/UserServiceIntegrationPostgresTest.java`:

    ```java
    package io.koraframework.guide.testingintegration;

    import java.time.Duration;
    import org.junit.jupiter.api.BeforeEach;
    import org.slf4j.LoggerFactory;
    import org.testcontainers.containers.PostgreSQLContainer;
    import org.testcontainers.containers.output.Slf4jLogConsumer;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;
    import io.koraframework.guide.databasejdbc.service.UserService;
    import io.koraframework.guide.testingintegration.TestApplication.TestUserRepository;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier;
    import io.koraframework.test.extension.junit5.KoraConfigModification;
    import io.koraframework.test.extension.junit5.TestComponent;

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

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                    jdbc {
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

    Создайте `src/test/kotlin/io/koraframework/guide/testingintegration/UserServiceIntegrationPostgresTest.kt`:

    ```kotlin
    package io.koraframework.guide.testingintegration

    import org.junit.jupiter.api.BeforeEach
    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.PostgreSQLContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers
    import io.koraframework.guide.databasejdbc.service.UserService
    import io.koraframework.guide.testingintegration.TestApplication.TestUserRepository
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier
    import io.koraframework.test.extension.junit5.KoraConfigModification
    import io.koraframework.test.extension.junit5.TestComponent
    import java.time.Duration

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
                jdbc {
                  jdbcUrl = ${'$'}{POSTGRES_JDBC_URL}
                  username = ${'$'}{POSTGRES_USER}
                  password = ${'$'}{POSTGRES_PASS}
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

Метод `config()` в этом тесте подменяет конфигурацию, а не код приложения. `KoraConfigModification.ofString(...)` добавляет небольшой фрагмент HOCON с настройками `jdbc` и `flyway`, которые нужны пулу
JDBC и миграциям. Значения подключения не зашиты в строку конфигурации: они записаны как подстановки `${POSTGRES_JDBC_URL}`, `${POSTGRES_USER}` и `${POSTGRES_PASS}`.

Имя секции здесь принципиально: в Kora 2.0 пул JDBC настраивается в секции `jdbc`, потому что именно этот путь использует `JdbcDatabaseModule` при создании фабрики. В raw-строке Kotlin символ `$`
начинает шаблонное выражение, поэтому подстановку HOCON нужно писать как `${'$'}{POSTGRES_JDBC_URL}`, чтобы плейсхолдер дошел до текста конфигурации.

Дальше `withSystemProperty(...)` подставляет настоящие значения из запущенного `PostgreSQLContainer`. Testcontainers может выдать другой порт, пользователя или пароль на каждый запуск, поэтому тест не
должен рассчитывать на фиксированный `localhost:5432`. Когда Kora читает конфигурацию, эти подстановки разрешаются через системные свойства, и граф получает обычный `JdbcDatabase`, подключенный к
одноразовой базе данных именно этого запуска.

Пользы здесь сразу несколько: промышленная конфигурация не меняется ради тестов, тесты не зависят от локальной базы данных разработчика, а один и тот же код приложения проверяется на настоящем
PostgreSQL и настоящих миграциях. При этом переопределяются только те настройки, которые действительно важны, без переписывания всего файла конфигурации.

## Написание тестов { #tests }

Теперь добавьте настоящие интеграционные тестовые методы в тот же класс `UserServiceIntegrationPostgresTest`.
Контейнер намеренно настроен с явным таймаутом запуска и подключенными журналами, чтобы проблемы старта было легко диагностировать.
Эти методы проверяют поведение службы и сохраненное состояние на настоящем PostgreSQL.

Каждый метод использует обе точки контроля, которые есть у теста: `userService` выполняет настоящую логику приложения, а `testUserRepository` читает получившиеся строки прямо из базы данных. Именно
проверка обеих сторон отличает интеграционный тест от компонентного — вторая половина доказывает, что данные действительно дошли до PostgreSQL и пережили отображение.

===! ":fontawesome-brands-java: `Java`"

    Добавьте импорты:

    ```java
    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertTrue;

    import java.util.List;
    import org.junit.jupiter.api.Test;
    import io.koraframework.guide.databasejdbc.dto.UserRequest;
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
    import io.koraframework.guide.databasejdbc.dto.UserRequest
    ```

    Добавьте тестовые методы:

    ```kotlin
    @Test
    fun createUserShouldPersistUserInDatabase() {
        val result = userService.createUser(UserRequest("John", "john@example.com"))

        assertEquals("John", result.name)
        assertTrue(result.id.toLong() > 0)
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
        assertEquals("Charlie", result[0].name)
        assertEquals("David", result[1].name)
    }

    @Test
    fun updateUserShouldUpdateUserInDatabase() {
        val created = userService.createUser(UserRequest("John", "john@example.com"))

        val updated = userService.updateUser(created.id, UserRequest("John Updated", "john.updated@example.com"))

        assertEquals("John Updated", updated.name)
    }

    @Test
    fun deleteUserShouldRemoveUserFromDatabase() {
        val created = userService.createUser(UserRequest("John", "john@example.com"))

        userService.deleteUser(created.id)

        assertEquals(0, testUserRepository.findAll().size)
    }
    ```

## Тестирование { #testing }

Запустите интеграционные тесты через Gradle:

```bash
# Run all tests
./gradlew test

# Run with detailed logs
./gradlew test --info
```

!!! tip "Замечания по запуску"

    - Docker должен быть запущен до старта тестов.
    - Первый запуск обычно медленнее из-за загрузки образов.
    - Оставляйте журналирование тестов включенным: так проще диагностировать старт и миграции.

## Тестовое покрытие { #coverage }

Для диагностики интеграционных тестов используйте стандартные отчеты Gradle:

```bash
# Execute tests and generate reports
./gradlew test

# Generate JaCoCo coverage report
./gradlew jacocoTestReport
```

Сбои интеграционных тестов обычно проще всего разбирать по:

- `build/reports/tests/test/index.html`
- журналам запуска контейнеров в выводе Gradle
- журналам SQL и миграций от компонентов Flyway и JDBC

!!! tip "Миграции Flyway в тестах"

    Миграции Flyway можно выполнять прямо в жизненном цикле тестов, а не полагаться на их запуск внутри приложения.
    Такой подход полезен, когда нужен более строгий контроль над подготовкой схемы для набора тестов или для отдельного класса.
    В этом руководстве миграции остаются на старте приложения ради простоты, но оба подхода допустимы.

## Лучшие практики { #best-practices }

**Проектирование интеграционных тестов:**

- Держите сценарии тестов ориентированными на бизнес-поведение (создание, чтение, обновление, удаление, пагинация)
- Проверяйте и ответ службы, и состояние базы данных
- Используйте детерминированные поля сортировки для проверок пагинации
- Избегайте скрытых связей между тестами

**Изоляция данных:**

- Очищайте тестовые данные в `@BeforeEach`
- Используйте уникальные тестовые записи там, где возможны конфликты
- Не полагайтесь на идентификаторы из предыдущих тестовых методов
- Держите каждый тест независимо запускаемым

**Стабильность инфраструктуры:**

- Задавайте явные таймауты запуска контейнеров
- Всегда берите JDBC URL, пользователя и пароль из геттеров контейнера
- Указывайте расположение миграций Flyway явно в тестовой конфигурации
- Предпочитайте значения по умолчанию контейнера жестко заданным учетным данным

## Итоги { #summary }

Интеграционное тестирование дает высокую уверенность в том, что приложение Kora на JDBC работает корректно с настоящим PostgreSQL и настоящими миграциями. Оно проверяет слой хранения, связывание
зависимостей и поведение служб в реалистичных условиях, оставаясь быстрее и уже, чем полноценное тестирование API по принципу черного ящика.

В этом руководстве вы настроили:

- поднятие PostgreSQL через Testcontainers
- переопределения конфигурации Kora значениями контейнера во время выполнения
- проверку интеграции настоящего `UserService` с вспомогательным репозиторием только для тестов
- повторяемую очистку и детерминированное выполнение тестов

## Ключевые понятия { #key-concepts }

**Область интеграционного тестирования:**

- Настоящая инфраструктура, настоящий SQL, настоящие миграции
- Фокус на поведении связки служба + репозиторий + база данных
- Высокая уверенность в сценариях сохранения данных

**Тестовая инфраструктура Kora:**

- `@KoraAppTest` поднимает настоящий граф приложения
- `@TestComponent` внедряет тестируемые компоненты
- `KoraAppTestConfigModifier` переопределяет конфигурацию во время выполнения
- Тестовый `@KoraApp` с `@Root` для компонентов, от которых не зависит код приложения

**Конфигурация от контейнера:**

- Берите параметры подключения из `PostgreSQLContainer`
- Передавайте значения через `withSystemProperty(...)`
- Держите конфигурацию переносимой между окружениями

## Устранение неполадок { #troubleshooting }

**Контейнер не запускается:**

- Убедитесь, что демон Docker запущен
- Проверьте конфликты портов и ресурсов в журналах контейнера
- Увеличьте таймаут запуска, если окружение медленное

**Ошибки миграций:**

- Проверьте, что миграции лежат в `src/main/resources/db/migration`
- Убедитесь, что в тестовой конфигурации есть `flyway.locations = "db/migration"`
- Добавьте `org.flywaydb:flyway-database-postgresql` той же версии, что и `flyway-core`, иначе старт падает с ошибкой `Unsupported Database: PostgreSQL`
- Посмотрите вывод Flyway в журналах Gradle

**Проблемы с подключением к базе данных:**

- Берите JDBC URL и учетные данные только из геттеров контейнера
- Настраивайте пул в секции `jdbc`; фрагмент, записанный в любую другую секцию, просто игнорируется, и граф падает на отсутствующем `jdbcUrl`
- Не задавайте в тестовой конфигурации жестко прописанные учетные данные для localhost
- Убедитесь, что JDBC-драйвер PostgreSQL доступен в тестовой среде выполнения
- Явно добавляйте тестовые зависимости database-jdbc и database-flyway, если TestApplication расширяет граф приложения из другого модуля

**Подстановки не разрешаются:**

- Каждой подстановке `${NAME}` во фрагменте нужен свой `withSystemProperty("NAME", ...)`
- В Kotlin пишите плейсхолдер как `${'$'}{NAME}`; обычный `${NAME}` — это шаблонное выражение Kotlin, а `\${NAME}` в raw-строке не является escape-последовательностью

**Нестабильные или зависающие тесты:**

- Оставляйте `testLogging` с `showStandardStreams(true)`
- При точечной отладке пользуйтесь тест-раннером среды разработки
- Проверяйте логику очистки и предположения об изоляции тестов

**Предупреждение `Expected @KoraApp as SubModule`:**

Если тестовый модуль расширяет `Application` из другого модуля и вы видите предупреждения вида:

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

    Добавьте в `guide-database-jdbc-app/build.gradle.kts`:

    ```kotlin title="guide-database-jdbc-app/build.gradle.kts"
    ksp {
        arg("kora.app.submodule.enabled", "true")
    }
    ```

**JUnit находит сгенерированный `$TestApplicationImpl`:**

Если обнаружение тестов падает еще до выполнения (например, с `NoClassDefFoundError` из сгенерированных классов), исключите сгенерированные классы фильтром тестов Gradle:

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

В Windows такое случается, когда закешированные JAR временно заблокированы другим процессом.

Попробуйте по порядку:

1. Остановить демоны: `./gradlew --stop`
2. Перезапустить сборку: `./gradlew test`
3. Если блокировка не уходит, запустить сессию с изолированным кешем:
   `GRADLE_USER_HOME=.gradle-user-home ./gradlew test`

## Что дальше? { #whats-next }

- [Тестирование как черный ящик](testing-black-box.md), чтобы перейти от интеграционных тестов на уровне графа к тестам упакованного приложения.
- [Наблюдаемость](observability.md), чтобы следить за тем же приложением с базой данных через метрики, трассировки, журналы и пробы.
- [Расширенный JDBC](database-jdbc-advanced.md), если нужны более сложные сценарии репозиториев, транзакций, мапперов и проекций для тестирования.
- [Кеширование](cache.md), когда повторные чтения из базы данных требуют слоя производительности.

## Помощь { #help }

Если возникли проблемы:

- сравните интеграционные тесты с [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app) и [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-jdbc-app)
- проверьте [документацию JUnit5](../documentation/junit5.md)
- проверьте [документацию по базе данных JDBC](../documentation/database-jdbc.md)
- проверьте [документацию по миграциям базы данных](../documentation/database-migration.md)
- прочитайте [документацию Testcontainers](https://www.testcontainers.org/)
