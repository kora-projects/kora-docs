---
search:
  exclude: true
title: Тестирование как черный ящик с Kora
summary: Learn comprehensive black box testing strategies for Kora applications using Testcontainers and HTTP APIs
description: "Black box testing for a packaged Kora 2.0 application: building the distribution tar and a Dockerfile image, a Testcontainers 2.0 GenericContainer wrapper exposing httpServer.port 8080 and httpServer.system.port 8085, waiting on GET /system/readiness for status 200, passing configuration through container environment variables, and asserting HTTP status codes and JSON bodies from the outside."
agent:
  use_when: "Use this file for questions about end-to-end testing a packaged Kora 2.0 service through HTTP: Dockerfile and distTar packaging, an AppContainer built with ImageFromDockerfile, Wait.forHttp(\"/system/readiness\").forPort(8085).forStatusCode(200), Network.SHARED between the application and a PostgreSQL container, withEnv configuration, and org.testcontainers:testcontainers-junit-jupiter coordinates."
tags: testing, black-box-tests, testcontainers, http-testing, end-to-end-testing
---

# Тестирование как черный ящик с Kora { #black-box-testing-kora }

Это руководство знакомит с тестированием HTTP-приложений Kora по принципу черного ящика. В нем рассматривается, как запустить приложение целиком как тестируемую цель, обращаться к нему только через
открытые HTTP-эндпоинты и проверять поведение, не заглядывая в службы, репозитории и внутренности сгенерированного графа. Вы также увидите, как Testcontainers и HTTP-клиенты делают такие тесты
максимально близкими к настоящей эксплуатации.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Testing Black Box App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-testing-black-box-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Testing Black Box App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-testing-black-box-app).

## Что вы создадите { #youll-build }

Вы создадите полноценные тесты по принципу черного ящика, которые покрывают:

- **тестирование приложения целиком**: проверку всего приложения через HTTP API
- **тестирование в контейнерах**: использование Docker-контейнеров для реалистичной тестовой среды
- **интеграцию с базой данных**: проверку с настоящей базой данных PostgreSQL
- **проверку контракта API**: уверенность, что поведение API соответствует спецификации
- **сквозные сценарии**: проверку полных пользовательских сценариев

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+ (эталонные приложения используют Gradle Wrapper `9.5.1`)
- Docker (для Testcontainers)
- текстовый редактор или среда разработки
- пройденное руководство [Работа с базой данных](database-jdbc.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по базе данных JDBC"

    Это руководство предполагает, что вы уже прошли **[Работа с базой данных](database-jdbc.md)** и у вас есть рабочий проект Kora с JDBC-репозиторием, миграциями Flyway, `UserService`, `UserController` и базовыми тестовыми зависимостями Kora.

    Если вы еще не прошли руководство по базе данных JDBC, сначала сделайте это, потому что здесь приложение запускается целиком в контейнерах и проверяется через API снаружи.

## Обзор { #overview }

Тестирование по принципу черного ящика относится к приложению как к внешней системе. Тест не вызывает напрямую ни службы, ни репозитории, ни сгенерированные классы графа, ни методы контроллеров. Он
запускает приложение, отправляет настоящие HTTP-запросы и проверяет настоящие HTTP-ответы.

### Почему сначала black box { #black-box-first }

Приложения Kora стартуют быстро, потому что графы зависимостей генерируются во время компиляции и большая часть работы по связыванию известна еще до запуска. Это меняет привычный компромисс в
тестировании. Во многих фреймворках тесты черного ящика настолько дороги, что команды оставляют для них лишь небольшой набор дымовых проверок. В Kora запуск всего приложения обычно достаточно
практичен, чтобы сделать тесты черного ящика основным источником уверенности в поведении, видимом пользователю.

Дело не в том, что компонентные и интеграционные тесты не важны. Они по-прежнему полезны для сфокусированной обратной связи. Дело в том, что многие реальные ошибки живут между слоями:

- маршрут контроллера подключен не так, как предполагал тест службы
- отображение JSON или валидация падают еще до выполнения кода службы
- конфигурация работает в модульном тесте, но не в упакованном приложении
- миграции и настройки базы данных во время выполнения не совпадают
- у ответа с ошибкой неправильный код состояния или форма тела

Тесты черного ящика ловят такие проблемы, потому что работают через ту же открытую границу, которой пользуется настоящий клиент. Они медленнее компонентных, но проверяют поведение, которое важнее всего
для потребителей API.

### Что доказывают внешние тесты { #external-tests-prove }

Тесты черного ящика ценны тем, что включают весь путь выполнения:

- HTTP-маршрутизацию и коды состояния
- сериализацию и десериализацию JSON
- валидацию и ответы с ошибками
- загрузку конфигурации
- запуск графа зависимостей
- подключение к базе данных и миграции
- сквозное поведение вроде журналирования, проб и перехватчиков

Это делает их лучшим типом тестов для поведения, видимого пользователю. Если тест черного ящика проходит, значит клиент может обратиться к приложению ровно так же, как это сделал тест.

### Контейнеры как тестовая среда { #containers-test-environment }

В этом руководстве само приложение работает в контейнере, а [PostgreSQL](https://www.postgresql.org/docs/) — в другом контейнере под управлением [Testcontainers](https://java.testcontainers.org/). Тест
общается с приложением по HTTP, а не через объекты в том же процессе. Такая конфигурация ближе к настоящему развертыванию, чем компонентные и интеграционные тесты.

Практический ход теста черного ящика такой:

1. собрать или запустить контейнер приложения
2. поднять нужные инфраструктурные контейнеры
3. передать конфигурацию во время выполнения в приложение
4. вызвать открытые эндпоинты по HTTP
5. проверить коды состояния, заголовки, тела ответов и сохраненное состояние

### Компромиссы { #trade-offs }

Тесты черного ящика медленнее и требуют [Docker](https://docs.docker.com/), но они ловят классы проблем, которых не видят более узкие тесты: неправильные порты, сломанную упаковку, отсутствующую
конфигурацию времени выполнения, некорректное окружение контейнера, расхождения в HTTP-контракте и проблемы связывания, которые проявляются только при запуске приложения целиком.

Они не должны заменять все точечные проверки. Используйте компонентные тесты для быстрой обратной связи по бизнес-логике, интеграционные — для границ хранилища, а тесты черного ящика — как самую
сильную проверку того, что приложение целиком работает с точки зрения клиента.

Практический ход такой:

1. упаковать приложение так, чтобы его можно было запустить в контейнере
2. поднять PostgreSQL и приложение через Testcontainers
3. передать конфигурацию времени выполнения через переменные окружения контейнера
4. вызвать открытый HTTP API из теста
5. проверить коды ответов, тела JSON и сохраненное состояние

## Зависимости { #dependencies }

Добавьте тестовые зависимости для тестов черного ящика в модуль черного ящика. Для отправки HTTP-запросов ничего из Kora строго не требуется — хватает HTTP-клиента из JDK, — но модуль все равно зависит
от проекта приложения, чтобы Gradle знал, когда нужно пересобрать образ.

Обратите внимание на координаты Testcontainers: начиная с Testcontainers `2.0` расширение JUnit 5 публикуется как `org.testcontainers:testcontainers-junit-jupiter`, а модуль PostgreSQL — как
`org.testcontainers:testcontainers-postgresql`. Версия в этих строках — это версия Testcontainers, а не JUnit.

===! ":fontawesome-brands-java: `Java`"

    Добавьте в `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        testImplementation platform("org.junit:junit-bom:6.1.3")

        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation project(":guide-database-jdbc-app") //(1)!
        testImplementation "io.koraframework:test-junit5"
        testImplementation "org.json:json:20231013" //(2)!
        testImplementation "org.testcontainers:testcontainers:2.0.5"
        testImplementation "org.testcontainers:testcontainers-junit-jupiter:2.0.5" //(3)!
        testImplementation "org.testcontainers:testcontainers-postgresql:2.0.5"
    }

    test {
        dependsOn ":guide-database-jdbc-app:distTar" //(4)!
        inputs.file("../guide-database-jdbc-app/Dockerfile")
        inputs.file("../guide-database-jdbc-app/build/distributions/application.tar")

        useJUnitPlatform()
        testLogging {
            showStandardStreams(true)
            events("passed", "skipped", "failed")
            exceptionFormat("full")
        }
    }
    ```

    1.  Модуль приложения. Тест не импортирует его классы, но зависимость связывает две сборки между собой.
    2.  Небольшая библиотека JSON для сборки тел запросов и чтения ответов. Тест намеренно не переиспользует DTO приложения, поэтому изменение схемы проявится как упавшая проверка.
    3.  Имена модулей Testcontainers `2.0`. Старые координаты `org.testcontainers:junit-jupiter` и `org.testcontainers:postgresql` остановились на `1.21.x`.
    4.  Образ собирается из архива дистрибутива, поэтому архив должен существовать до запуска тестов.

=== ":simple-kotlin: `Kotlin`"

    Добавьте в `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        testImplementation(platform("org.junit:junit-bom:6.1.3"))

        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation(project(":guide-database-jdbc-app")) //(1)!
        testImplementation("io.koraframework:test-junit5")
        testImplementation("org.json:json:20231013") //(2)!
        testImplementation("org.testcontainers:testcontainers:2.0.5")
        testImplementation("org.testcontainers:testcontainers-junit-jupiter:2.0.5") //(3)!
        testImplementation("org.testcontainers:testcontainers-postgresql:2.0.5")
    }

    tasks.test {
        dependsOn(":guide-database-jdbc-app:distTar") //(4)!
        inputs.file("../guide-database-jdbc-app/Dockerfile")
        inputs.file("../guide-database-jdbc-app/build/distributions/application.tar")

        useJUnitPlatform()
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
    ```

    1.  Модуль приложения. Тест не импортирует его классы, но зависимость связывает две сборки между собой.
    2.  Небольшая библиотека JSON для сборки тел запросов и чтения ответов. Тест намеренно не переиспользует DTO приложения, поэтому изменение схемы проявится как упавшая проверка.
    3.  Имена модулей Testcontainers `2.0`. Старые координаты `org.testcontainers:junit-jupiter` и `org.testcontainers:postgresql` остановились на `1.21.x`.
    4.  Образ собирается из архива дистрибутива, поэтому архив должен существовать до запуска тестов.

## Настройка Dockerfile { #dockerfile-setup }

Прежде чем создавать `AppContainer`, добавьте упаковку в Docker для приложения JDBC из руководства [Работа с базой данных](database-jdbc.md).

Модуль приложения уже использует плагин Gradle `application`, поэтому задача `distTar` собирает запускаемый дистрибутив. Зафиксируйте имя архива, чтобы Dockerfile мог копировать предсказуемый путь:

```groovy title="guide-database-jdbc-app/build.gradle"
distTar {
    archiveFileName = "application.tar"
}
```

Создайте `guides/guide-database-jdbc-app/Dockerfile`:

```dockerfile
FROM eclipse-temurin:25-jre-jammy

ARG TARGET_DIR=/opt/app

COPY build/distributions/application.tar /application.tar
RUN mkdir -p ${TARGET_DIR}
RUN tar -xf /application.tar -C ${TARGET_DIR}
RUN rm /application.tar

ARG DOCKER_USER=app
RUN groupadd -r ${DOCKER_USER} && useradd -rg ${DOCKER_USER} ${DOCKER_USER}
USER ${DOCKER_USER}

EXPOSE 8080/tcp
EXPOSE 8085/tcp
CMD ["/opt/app/application/bin/application"]
```

Базовый образ содержит среду выполнения Java 25, потому что модули Kora 2.0 скомпилированы под Java 25. Открываются два порта: `8080` — публичный HTTP-сервер (`httpServer.port`), а `8085` — системный
сервер (`httpServer.system.port`), который отвечает на пробы и отдает метрики.

В `build.gradle` модуля черного ящика сделайте тесты зависимыми от архива дистрибутива:

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    test {
        dependsOn ":guide-database-jdbc-app:distTar"
        inputs.file("../guide-database-jdbc-app/Dockerfile")
        inputs.file("../guide-database-jdbc-app/build/distributions/application.tar")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    tasks.test {
        dependsOn(":guide-database-jdbc-app:distTar")
        inputs.file("../guide-database-jdbc-app/Dockerfile")
        inputs.file("../guide-database-jdbc-app/build/distributions/application.tar")
    }
    ```

## Контейнер приложения { #application-container }

`AppContainer` — это переиспользуемая обертка вокруг Docker-образа вашего приложения.
Она прячет детали запуска, чтобы тестовый класс оставался сосредоточенным на сценариях, а не на возне с контейнерами.

Что происходит внутри `AppContainer`:

- собирается образ по Dockerfile из руководства по JDBC
- открываются публичный (`8080`) и системный (`8085`) порты
- ожидается ответ `/system/readiness` на системном порту до запуска тестов
- предоставляются вспомогательные методы для сборки базового HTTP-адреса

Ожидание готовности здесь — ключевая часть. Kora отдает `/system/readiness`, `/system/liveness` и `/metrics` на системном HTTP-сервере, который дает модуль `SystemHttpServerModule`, наследуемый
модулем `UndertowPublicHttpServerModule` — отдельный модуль подключать не нужно. Эндпоинт готовности отвечает `200`, когда все компоненты `ReadinessProbe` в графе сообщают о готовности, и `503`, пока
хотя бы один из них еще стартует. То есть `200` означает, что граф собран, миграции выполнены и публичный сервер готов обслуживать запросы.

Ждите именно этот эндпоинт, а не строку в журнале запуска. Формулировки журнала не входят в контракт Kora и могут меняться от релиза к релизу, тогда как код состояния готовности — это ровно тот сигнал,
который та же проба отдает оркестратору в промышленной среде.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/io/koraframework/guide/testingblackbox/AppContainer.java`:

    ```java
    package io.koraframework.guide.testingblackbox;

    import java.net.URI;
    import java.nio.file.Path;
    import java.time.Duration;
    import org.slf4j.LoggerFactory;
    import org.testcontainers.containers.GenericContainer;
    import org.testcontainers.containers.output.Slf4jLogConsumer;
    import org.testcontainers.containers.wait.strategy.Wait;
    import org.testcontainers.images.builder.ImageFromDockerfile;

    final class AppContainer extends GenericContainer<AppContainer> {

        AppContainer() {
            super(new ImageFromDockerfile("guide-database-jdbc-black-box")
                    .withDockerfile(Path.of("../guide-database-jdbc-app/Dockerfile")));

            withExposedPorts(8080, 8085);
            withStartupTimeout(Duration.ofSeconds(30));
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200));
            withLogConsumer(new Slf4jLogConsumer(LoggerFactory.getLogger(AppContainer.class)));
        }

        URI getURI() {
            return URI.create("http://" + getHost() + ":" + getMappedPort(8080));
        }

        URI getSystemURI() {
            return URI.create("http://" + getHost() + ":" + getMappedPort(8085));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/test/kotlin/io/koraframework/guide/testingblackbox/AppContainer.kt`:

    ```kotlin
    package io.koraframework.guide.testingblackbox

    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.GenericContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.containers.wait.strategy.Wait
    import org.testcontainers.images.builder.ImageFromDockerfile
    import java.net.URI
    import java.nio.file.Path
    import java.time.Duration

    class AppContainer : GenericContainer<AppContainer>(
        ImageFromDockerfile("guide-database-jdbc-black-box")
            .withDockerfile(Path.of("../guide-database-jdbc-app/Dockerfile"))
    ) {

        init {
            withExposedPorts(8080, 8085)
            withStartupTimeout(Duration.ofSeconds(30))
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200))
            withLogConsumer(Slf4jLogConsumer(LoggerFactory.getLogger(AppContainer::class.java)))
        }

        fun getURI(): URI = URI.create("http://$host:${getMappedPort(8080)}")

        fun getSystemURI(): URI = URI.create("http://$host:${getMappedPort(8085)}")
    }
    ```

Открыты оба порта, `8080` и `8085`, и оба Docker отображает на случайные порты хоста. Именно поэтому тест никогда не зашивает порт: `getMappedPort(8080)` возвращает порт хоста для публичного API, а
`getMappedPort(8085)` — для системного. Метод `getSystemURI()` пригодится, когда тесту нужно прочитать `/metrics` или перепроверить `/system/liveness` после сценария.

## Testcontainers { #testcontainers }

В тесте черного ящика приложение уже собрано как отдельный артефакт Docker. Тест не меняет его граф Kora и не добавляет в приложение тестовые компоненты: контейнер выполняет ровно тот код, который был
упакован во время сборки.

Что тест действительно может менять — это окружение выполнения контейнера: переменные окружения, сеть, порты, порядок запуска и внешнюю инфраструктуру. В этом руководстве тест поднимает PostgreSQL рядом
с приложением и передает настройки подключения через `withEnv(...)`. С точки зрения приложения это обычная промышленная конфигурация из окружения; просто значения на время теста выдает Testcontainers.

Это работает, потому что конфигурация приложения читает эти переменные через подстановки HOCON:

```hocon
jdbc {
  jdbcUrl = ${?POSTGRES_JDBC_URL}
  username = ${?POSTGRES_USER}
  password = ${?POSTGRES_PASS}
  maxPoolSize = 10
  poolName = "guide-jdbc"
}
```

Обратите внимание на имя секции: в Kora 2.0 пул JDBC настраивается в секции `jdbc`. Знак `?` в `${?POSTGRES_JDBC_URL}` делает подстановку необязательной, благодаря чему файл остается корректным и без
этой переменной — например, при локальном запуске через `docker-compose`.

Теперь опишите жизненный цикл инфраструктуры в тестовом классе.
`@Testcontainers` включает автоматическое управление жизненным циклом контейнеров, а `@Container` помечает управляемые контейнеры.

На этом шаге:

- `PostgreSQLContainer` дает настоящую базу данных
- `AppContainer` зависит от запуска Postgres
- значения окружения для базы данных подставляются из геттеров контейнера Postgres
- общая сеть используется для обращения между контейнерами по имени хоста

===! ":fontawesome-brands-java: `Java`"

    Начните `src/test/java/io/koraframework/guide/testingblackbox/BlackBoxTests.java` так:

    ```java
    package io.koraframework.guide.testingblackbox;

    import java.time.Duration;
    import org.junit.jupiter.api.Test;
    import org.slf4j.LoggerFactory;
    import org.testcontainers.containers.Network;
    import org.testcontainers.containers.PostgreSQLContainer;
    import org.testcontainers.containers.output.Slf4jLogConsumer;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;

    @Testcontainers
    class BlackBoxTests {

        @Container
        private static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine")
                .withNetwork(Network.SHARED)
                .withNetworkAliases("postgres")
                .withStartupTimeout(Duration.ofSeconds(30))
                .withLogConsumer(new Slf4jLogConsumer(LoggerFactory.getLogger(PostgreSQLContainer.class)));

        @Container
        private static final AppContainer APP = new AppContainer()
                .withNetwork(Network.SHARED)
                .dependsOn(POSTGRES)
                .withEnv("POSTGRES_JDBC_URL", "jdbc:postgresql://postgres:5432/" + POSTGRES.getDatabaseName())
                .withEnv("POSTGRES_USER", POSTGRES.getUsername())
                .withEnv("POSTGRES_PASS", POSTGRES.getPassword());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Начните `src/test/kotlin/io/koraframework/guide/testingblackbox/BlackBoxTests.kt` так:

    ```kotlin
    package io.koraframework.guide.testingblackbox

    import org.junit.jupiter.api.Test
    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.Network
    import org.testcontainers.containers.PostgreSQLContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers
    import java.time.Duration

    @Testcontainers
    class BlackBoxTests {

        companion object {

            @Container
            @JvmStatic
            private val POSTGRES = PostgreSQLContainer("postgres:16-alpine")
                .withNetwork(Network.SHARED)
                .withNetworkAliases("postgres")
                .withStartupTimeout(Duration.ofSeconds(30))
                .withLogConsumer(Slf4jLogConsumer(LoggerFactory.getLogger(PostgreSQLContainer::class.java)))

            @Container
            @JvmStatic
            private val APP = AppContainer()
                .withNetwork(Network.SHARED)
                .dependsOn(POSTGRES)
                .withEnv("POSTGRES_JDBC_URL", "jdbc:postgresql://postgres:5432/${POSTGRES.databaseName}")
                .withEnv("POSTGRES_USER", POSTGRES.username)
                .withEnv("POSTGRES_PASS", POSTGRES.password)
        }
    }
    ```

В JDBC URL используется имя хоста `postgres`, а не `localhost`. Оба контейнера подключены к `Network.SHARED`, а `withNetworkAliases("postgres")` публикует это имя внутри сети Docker, поэтому приложение
достучится до базы данных по ее внутреннему порту `5432`. Отображенные порты хоста нужны только самому процессу теста.

## Написание тестов { #tests }

После того как контейнеры связаны, добавьте HTTP-сценарии в тот же класс `BlackBoxTests`.
Эти тесты проверяют поведение API от начала до конца через запущенный контейнер приложения.

===! ":fontawesome-brands-java: `Java`"

    Добавьте импорты:

    ```java
    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertTrue;

    import java.net.http.HttpClient;
    import java.net.http.HttpRequest;
    import java.net.http.HttpResponse;
    import java.util.UUID;
    import org.json.JSONArray;
    import org.json.JSONObject;
    ```

    Добавьте тестовые методы и вспомогательные функции:

    ```java
    @Test
    void createUser_ShouldCreateAndReturnUser() throws Exception {
        var response = sendJson("POST", "/users", new JSONObject()
                .put("name", "John Doe")
                .put("email", uniqueEmail("john")));

        assertEquals(201, response.statusCode());
        var responseBody = new JSONObject(response.body());
        assertTrue(responseBody.has("id"));
        assertEquals("John Doe", responseBody.getString("name"));
    }

    @Test
    void getUser_ShouldReturnUser() throws Exception {
        var createResponse = sendJson("POST", "/users", new JSONObject()
                .put("name", "Jane Doe")
                .put("email", uniqueEmail("jane")));
        var userId = new JSONObject(createResponse.body()).getString("id");

        var getRequest = HttpRequest.newBuilder()
                .GET()
                .uri(APP.getURI().resolve("/users/" + userId))
                .timeout(Duration.ofSeconds(10))
                .build();
        var getResponse = HttpClient.newHttpClient().send(getRequest, HttpResponse.BodyHandlers.ofString());

        assertEquals(200, getResponse.statusCode());
        var body = new JSONObject(getResponse.body());
        assertEquals(userId, body.getString("id"));
        assertEquals("Jane Doe", body.getString("name"));
    }

    @Test
    void getUser_NotFound_ShouldReturn404() throws Exception {
        var request = HttpRequest.newBuilder()
                .GET()
                .uri(APP.getURI().resolve("/users/999999"))
                .timeout(Duration.ofSeconds(10))
                .build();

        var response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());

        assertEquals(404, response.statusCode());
    }

    @Test
    void getUsers_WithPagination_ShouldReturnSizedResult() throws Exception {
        sendJson("POST", "/users", new JSONObject().put("name", "Alice").put("email", uniqueEmail("alice")));
        sendJson("POST", "/users", new JSONObject().put("name", "Bob").put("email", uniqueEmail("bob")));
        sendJson("POST", "/users", new JSONObject().put("name", "Charlie").put("email", uniqueEmail("charlie")));

        var request = HttpRequest.newBuilder()
                .GET()
                .uri(APP.getURI().resolve("/users?page=0&size=2&sort=name"))
                .timeout(Duration.ofSeconds(10))
                .build();
        var response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());

        assertEquals(200, response.statusCode());
        var users = new JSONArray(response.body());
        assertEquals(2, users.length());
    }

    @Test
    void updateUser_ShouldUpdateAndReturnUser() throws Exception {
        var createResponse = sendJson("POST", "/users", new JSONObject()
                .put("name", "John")
                .put("email", uniqueEmail("upd")));
        var userId = new JSONObject(createResponse.body()).getString("id");

        var updateRequest = HttpRequest.newBuilder()
                .PUT(HttpRequest.BodyPublishers.ofString(new JSONObject()
                        .put("name", "John Updated")
                        .put("email", uniqueEmail("updated"))
                        .toString()))
                .uri(APP.getURI().resolve("/users/" + userId))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(10))
                .build();
        var updateResponse = HttpClient.newHttpClient().send(updateRequest, HttpResponse.BodyHandlers.ofString());

        assertEquals(200, updateResponse.statusCode());
        var body = new JSONObject(updateResponse.body());
        assertEquals("John Updated", body.getString("name"));
    }

    @Test
    void deleteUser_ShouldRemoveUser() throws Exception {
        var createResponse = sendJson("POST", "/users", new JSONObject()
                .put("name", "John")
                .put("email", uniqueEmail("del")));
        var userId = new JSONObject(createResponse.body()).getString("id");

        var deleteRequest = HttpRequest.newBuilder()
                .DELETE()
                .uri(APP.getURI().resolve("/users/" + userId))
                .timeout(Duration.ofSeconds(10))
                .build();
        var deleteResponse = HttpClient.newHttpClient().send(deleteRequest, HttpResponse.BodyHandlers.ofString());
        assertEquals(204, deleteResponse.statusCode());

        var getRequest = HttpRequest.newBuilder()
                .GET()
                .uri(APP.getURI().resolve("/users/" + userId))
                .timeout(Duration.ofSeconds(10))
                .build();
        var getResponse = HttpClient.newHttpClient().send(getRequest, HttpResponse.BodyHandlers.ofString());
        assertEquals(404, getResponse.statusCode());
    }

    private HttpResponse<String> sendJson(String method, String path, JSONObject payload) throws Exception {
        var request = HttpRequest.newBuilder()
                .uri(APP.getURI().resolve(path))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(10));

        if ("POST".equals(method)) {
            request.POST(HttpRequest.BodyPublishers.ofString(payload.toString()));
        } else if ("PUT".equals(method)) {
            request.PUT(HttpRequest.BodyPublishers.ofString(payload.toString()));
        } else {
            throw new IllegalArgumentException("Unsupported method: " + method);
        }

        return HttpClient.newHttpClient().send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private String uniqueEmail(String prefix) {
        return prefix + "-" + UUID.randomUUID() + "@example.com";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте импорты:

    ```kotlin
    import org.json.JSONArray
    import org.json.JSONObject
    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertTrue
    import java.net.http.HttpClient
    import java.net.http.HttpRequest
    import java.net.http.HttpResponse
    import java.util.UUID
    ```

    Добавьте тестовые методы и вспомогательные функции:

    ```kotlin
    @Test
    fun createUserShouldCreateAndReturnUser() {
        val response = sendJson("POST", "/users", JSONObject()
            .put("name", "John Doe")
            .put("email", uniqueEmail("john")))

        assertEquals(201, response.statusCode())
        val body = JSONObject(response.body())
        assertTrue(body.has("id"))
        assertEquals("John Doe", body.getString("name"))
    }

    @Test
    fun getUserShouldReturnUser() {
        val createResponse = sendJson("POST", "/users", JSONObject()
            .put("name", "Jane Doe")
            .put("email", uniqueEmail("jane")))
        val userId = JSONObject(createResponse.body()).getString("id")

        val getRequest = HttpRequest.newBuilder()
            .GET()
            .uri(APP.getURI().resolve("/users/$userId"))
            .timeout(Duration.ofSeconds(10))
            .build()
        val getResponse = HttpClient.newHttpClient().send(getRequest, HttpResponse.BodyHandlers.ofString())

        assertEquals(200, getResponse.statusCode())
        val body = JSONObject(getResponse.body())
        assertEquals(userId, body.getString("id"))
        assertEquals("Jane Doe", body.getString("name"))
    }

    @Test
    fun getUserNotFoundShouldReturn404() {
        val request = HttpRequest.newBuilder()
            .GET()
            .uri(APP.getURI().resolve("/users/999999"))
            .timeout(Duration.ofSeconds(10))
            .build()

        val response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString())
        assertEquals(404, response.statusCode())
    }

    @Test
    fun getUsersWithPaginationShouldReturnSizedResult() {
        sendJson("POST", "/users", JSONObject().put("name", "Alice").put("email", uniqueEmail("alice")))
        sendJson("POST", "/users", JSONObject().put("name", "Bob").put("email", uniqueEmail("bob")))
        sendJson("POST", "/users", JSONObject().put("name", "Charlie").put("email", uniqueEmail("charlie")))

        val request = HttpRequest.newBuilder()
            .GET()
            .uri(APP.getURI().resolve("/users?page=0&size=2&sort=name"))
            .timeout(Duration.ofSeconds(10))
            .build()
        val response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString())

        assertEquals(200, response.statusCode())
        val users = JSONArray(response.body())
        assertEquals(2, users.length())
    }

    @Test
    fun updateUserShouldUpdateAndReturnUser() {
        val createResponse = sendJson("POST", "/users", JSONObject()
            .put("name", "John")
            .put("email", uniqueEmail("upd")))
        val userId = JSONObject(createResponse.body()).getString("id")

        val updateRequest = HttpRequest.newBuilder()
            .PUT(HttpRequest.BodyPublishers.ofString(JSONObject()
                .put("name", "John Updated")
                .put("email", uniqueEmail("updated"))
                .toString()))
            .uri(APP.getURI().resolve("/users/$userId"))
            .header("Content-Type", "application/json")
            .timeout(Duration.ofSeconds(10))
            .build()
        val updateResponse = HttpClient.newHttpClient().send(updateRequest, HttpResponse.BodyHandlers.ofString())

        assertEquals(200, updateResponse.statusCode())
        val body = JSONObject(updateResponse.body())
        assertEquals("John Updated", body.getString("name"))
    }

    @Test
    fun deleteUserShouldRemoveUser() {
        val createResponse = sendJson("POST", "/users", JSONObject()
            .put("name", "John")
            .put("email", uniqueEmail("del")))
        val userId = JSONObject(createResponse.body()).getString("id")

        val deleteRequest = HttpRequest.newBuilder()
            .DELETE()
            .uri(APP.getURI().resolve("/users/$userId"))
            .timeout(Duration.ofSeconds(10))
            .build()
        val deleteResponse = HttpClient.newHttpClient().send(deleteRequest, HttpResponse.BodyHandlers.ofString())
        assertEquals(204, deleteResponse.statusCode())

        val getRequest = HttpRequest.newBuilder()
            .GET()
            .uri(APP.getURI().resolve("/users/$userId"))
            .timeout(Duration.ofSeconds(10))
            .build()
        val getResponse = HttpClient.newHttpClient().send(getRequest, HttpResponse.BodyHandlers.ofString())
        assertEquals(404, getResponse.statusCode())
    }

    private fun sendJson(method: String, path: String, payload: JSONObject): HttpResponse<String> {
        val requestBuilder = HttpRequest.newBuilder()
            .uri(APP.getURI().resolve(path))
            .header("Content-Type", "application/json")
            .timeout(Duration.ofSeconds(10))

        when (method) {
            "POST" -> requestBuilder.POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
            "PUT" -> requestBuilder.PUT(HttpRequest.BodyPublishers.ofString(payload.toString()))
            else -> throw IllegalArgumentException("Unsupported method: $method")
        }

        return HttpClient.newHttpClient().send(requestBuilder.build(), HttpResponse.BodyHandlers.ofString())
    }

    private fun uniqueEmail(prefix: String): String = "$prefix-${UUID.randomUUID()}@example.com"
    ```

Обе версии используют HTTP-клиент из JDK и отправляют блокирующие запросы. Это соответствует Kora 2.0, где серверная сторона тоже синхронная: один запрос, один ответ, явный код состояния для проверки.
Каждый тест генерирует уникальный email, потому что у таблицы `users` есть уникальное ограничение на эту колонку, а контейнеры общие для всего класса.

!!! tip "Преимущества тестирования как черный ящик"

    Почему стоит отдавать приоритет тестам черного ящика?

    - Реальный пользовательский опыт: проверяются настоящие HTTP API так, как их использовал бы пользователь
    - Проверка интеграции: ловятся проблемы между компонентами, в сериализации и так далее
    - Проверка контракта: контракты API остаются соблюденными
    - Уверенность в развертывании: проверяется поведение приложения целиком
    - Защита от регрессий: ловятся ломающие изменения в поведении, видимом пользователю

!!! note "Управление контейнерами"

    Шаблон `AppContainer` дает:

    - Тестирование по Dockerfile: проверяется настоящий образ вашего приложения
    - Изоляцию окружения: свежий контейнер на каждый запуск тестов
    - Учет готовности: ожидание готовности приложения перед тестами
    - Управление портами: автоматическое отображение портов и сборка адресов
    - Интеграцию журналов: журналы приложения доступны в выводе тестов

## Тестирование { #testing }

Запустите тесты черного ящика через Gradle:

```bash
# Run all tests including black box tests
./gradlew test

# Run with verbose output
./gradlew test --info
```

!!! tip "Советы по запуску тестов"

    - Нужен Docker: тестам черного ящика требуется Docker для запуска контейнеров
    - Доступ к сети: тесты могут занимать больше времени из-за запуска контейнеров
    - Требовательность к ресурсам: тесты черного ящика имеет смысл запускать отдельно от модульных
    - Параллельное выполнение: тесты черного ящика обычно выполняются последовательно из-за конфликтов контейнеров

## Лучшие практики { #best-practices }

Организация тестов:

- Тесты контракта API: проверяйте контракт каждого эндпоинта (формат запроса и ответа)
- Тесты бизнес-логики: проверяйте полные пользовательские сценарии и бизнес-правила
- Тесты сценариев с ошибками: проверяйте ошибочные состояния и граничные случаи
- Интеграционные тесты: проверяйте взаимодействие между службами

Управление тестовыми данными:

- Изолированные тестовые данные: каждый тест должен создавать свои данные
- Стратегия очистки: используйте очистку базы данных или свежие контейнеры между тестами
- Реалистичные данные: используйте данные, похожие на промышленные
- Проверка данных: проверяйте сохранение и чтение данных

Соображения производительности:

- Переиспользование контейнеров: по возможности переиспользуйте контейнеры, чтобы сократить время запуска
- Параллельное выполнение: запускайте тесты черного ящика параллельно, если контейнеры это позволяют
- Ограничения ресурсов: задавайте разумные лимиты ресурсов для тестовых контейнеров
- Управление таймаутами: настраивайте адекватные таймауты HTTP-запросов

Отладка тестов черного ящика:

- Журналы контейнеров: смотрите журналы контейнера для разбора проблем приложения
- Готовность и живучесть: запрашивайте `/system/readiness` и `/system/liveness` на системном порту, чтобы отделить проблемы старта от проблем обработки запросов
- Инспекция базы данных: обращайтесь к тестовой базе данных напрямую для проверки данных
- Метрики приложения: читайте `/metrics` с системного порта во время выполнения тестов

## Итоги { #summary }

Тестирование по принципу черного ящика дает наивысшую уверенность в корректности приложения Kora, потому что проверяет полный пользовательский путь через HTTP API. Используя шаблон `AppContainer`
вместе с Testcontainers, вы получаете реалистичную изолированную тестовую среду, которая проверяет поведение приложения от начала до конца.

Ключевые выводы:

- Сначала черный ящик: Kora рекомендует тестирование черного ящика как основную стратегию
- Тестирование в контейнерах: используйте Docker-контейнеры для реалистичной тестовой среды
- Проверка контракта API: проверяйте полные контракты HTTP API
- Сквозная проверка: проверяйте полные пользовательские сценарии и бизнес-логику
- Изоляция: каждый тест получает свежее окружение с корректной очисткой

Тесты черного ящика дополняют компонентные и интеграционные тесты, давая финальное подтверждение того, что приложение работает правильно с точки зрения пользователя.

## Ключевые понятия { #key-concepts }

Стратегия тестирования черного ящика:

- Сначала черный ящик: рекомендуемый в Kora основной подход для наивысшей уверенности
- Сквозная проверка: проверка полных пользовательских сценариев через HTTP API
- Тестирование контракта API: проверка полных циклов запрос/ответ
- Проверка с точки зрения пользователя: проверка поведения приложения так, как его видит пользователь

Шаблон AppContainer:

- Приложения в контейнерах: запуск приложения целиком в Docker-контейнерах
- Реалистичные окружения: тестирование с настоящей инфраструктурой и зависимостями
- Ворота готовности: сценарии стартуют только после ответа `200` на `/system/readiness` на системном порту
- Автоматический жизненный цикл: контейнеры запускаются и останавливаются вместе с выполнением тестов

Тестирование HTTP API:

- Полный путь запроса: проверка от HTTP-запроса до базы данных и обратно
- Проверка кодов состояния: подтверждение правильных кодов HTTP-ответов
- Проверка содержимого ответа: проверка JSON-ответов и корректности данных
- Обработка ошибок: проверка ошибочных сценариев и правильных ответов с ошибками

Изоляция тестов и производительность:

- Свежие окружения: каждый тест стартует с чистым состоянием базы данных и приложения
- Освобождение ресурсов: автоматическая очистка контейнеров и соединений
- Параллельное выполнение: тесты могут выполняться одновременно для ускорения
- Реалистичная нагрузка: тестирование с настоящими сетевыми вызовами и операциями с базой данных

## Устранение неполадок { #troubleshooting }

AppContainer не запускается:

- Убедитесь, что Docker запущен и доступен
- Проверьте, что архив дистрибутива собран и доступен: образ копирует `build/distributions/application.tar`
- Проверьте настройку Docker-образа и базовые образы; базовый образ должен содержать среду выполнения Java 25
- Посмотрите журналы контейнера на предмет ошибок запуска

Ожидание готовности истекает по таймауту:

- Посмотрите журналы контейнера: неудачная сборка графа, упавшая миграция или неверный JDBC URL держат `/system/readiness` на `503`
- Убедитесь, что стратегия ожидания использует системный порт `8085`, а не публичный `8080`
- Увеличьте `withStartupTimeout(...)`, если при первом запуске еще и собирается образ
- Не переключайте стратегию ожидания на сообщение в журнале: формулировки журнала запуска Kora не являются контрактом

Проблемы с HTTP-подключением:

- Убедитесь, что контейнер приложения полностью запустился до начала тестов
- Проверьте, что HTTP-порт корректно открыт и отображен
- Проверьте настройку сети между тестом и контейнерами приложения
- Посмотрите журналы приложения на предмет проблем запуска HTTP-сервера

Конфликты портов:

- Полагайтесь на отображение портов Testcontainers: `getMappedPort(8080)` и `getMappedPort(8085)` возвращают порты хоста
- Не публикуйте фиксированные порты хоста в тесте; порты контейнера всегда `8080` и `8085`
- Проверьте, что порты не заняты другими процессами
- Убедитесь, что порты освобождаются после завершения тестов

!!! tip "Миграции Flyway в тестах"

    Миграции Flyway можно выполнять из кода подготовки тестов, а не полагаться на автозапуск Flyway внутри контейнера приложения.
    Это полезно, когда нужен явный контроль миграций в жизненном цикле тестов (например, сброс схемы на каждый набор).
    В этом руководстве миграции выполняются на старте приложения, чтобы упростить настройку черного ящика, но подход с миграциями из тестов тоже допустим.

Проблемы с подготовкой базы данных:

- Убедитесь, что контейнер базы данных стартует раньше контейнера приложения через `dependsOn(...)`
- Проверьте, что приложение получает значения контейнера: секция конфигурации называется `jdbc`, а переменные читаются как `${?POSTGRES_JDBC_URL}` и аналогичные
- Используйте в JDBC URL, который передается контейнеру приложения, сетевой алиас, а не `localhost`
- Посмотрите журналы контейнера базы данных на предмет ошибок запуска или подключения

Таймауты тестов:

- Увеличьте значения таймаутов для медленно стартующих контейнеров
- Проверьте время запуска приложения и скорректируйте стратегии ожидания
- Проверьте сетевую связность между контейнерами
- Следите за потреблением ресурсов (CPU/память) во время выполнения тестов

Проблемы очистки контейнеров:

- Убедитесь, что очистка выполняется в методах завершения тестов
- Проверьте, не остались ли зависшие процессы после завершения тестов
- Убедитесь, что демону Docker хватает ресурсов
- Пользуйтесь автоматической очисткой Testcontainers

## Что дальше? { #whats-next }

- [Наблюдаемость](observability.md), чтобы выставить пробы, метрики, трассировки и журналы для упакованного приложения, которое вы теперь тестируете от начала до конца.
- [Шаблоны устойчивости](resilient.md), чтобы проверять обработку сбоев через сценарии на уровне HTTP.
- [OpenAPI HTTP-сервер](openapi-http-server.md), чтобы перейти от написанных вручную эндпоинтов к генерации транспорта из контракта.
- [HTTP-клиент](http-client.md), чтобы тестировать вызовы между службами на запущенном сервере.

## Помощь { #help }

Если возникли проблемы:

- сравните тесты черного ящика с [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app) и [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-jdbc-app)
- проверьте [документацию JUnit5](../documentation/junit5.md)
- проверьте [документацию по миграциям базы данных](../documentation/database-migration.md)
- прочитайте [документацию Testcontainers](https://www.testcontainers.org/)
