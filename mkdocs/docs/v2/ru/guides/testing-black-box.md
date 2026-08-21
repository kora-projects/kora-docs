---
search:
  exclude: true
title: Тестирование как черный ящик с Kora
summary: Learn comprehensive black box testing strategies for Kora applications using Testcontainers and HTTP APIs
tags: testing, black-box-tests, testcontainers, http-testing, end-to-end-testing
---

# Тестирование как черный ящик с Kora { #black-box-testing-kora }

В этом руководстве рассматривается тестирование HTTP-приложений Kora как черный ящик. Вы узнаете, как запускать полное приложение как цель тестирования, обращаться к нему только через публичные
HTTP-конечные точки и проверять поведение без обращения внутрь сервисов, репозиториев или сгенерированных внутренних частей графа. Вы также увидите, как Testcontainers и HTTP-клиенты делают такие
тесты близкими к реальному использованию во время выполнения.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Testing Black Box App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-testing-black-box-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Testing Black Box App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-testing-black-box-app).

## Что вы создадите { #youll-build }

Вы создадите комплексные тесты по принципу черного ящика, которые покрывают:

- **Тестирование полного приложения**: тестирование всего приложения через HTTP API
- **Контейнерное тестирование**: использование Docker-контейнеров для реалистичных тестовых сред
- **Интеграцию с базой данных**: тестирование с настоящими базами данных PostgreSQL
- **Проверку контракта API**: уверенность, что поведение API соответствует спецификации
- **Сквозные сценарии**: тестирование полных пользовательских потоков

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- Docker (для Testcontainers)
- текстовый редактор или среда разработки
- пройденное руководство [Интеграция с базой данных](database-jdbc.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по базе данных JDBC"

    Это руководство предполагает, что вы уже прошли **[Интеграцию с базой данных](database-jdbc.md)** и у вас есть рабочий проект Kora с JDBC-репозиторием, миграциями Flyway, `UserService`, `UserController` и базовыми тестовыми зависимостями Kora.

    Если вы еще не прошли руководство по базе данных JDBC, сначала сделайте это, потому что здесь полное приложение запускается в контейнерах, а API проверяется снаружи.

## Обзор { #overview }

Тестирование как черный ящик рассматривает приложение как внешнюю систему. Тест не вызывает сервисы, репозитории, сгенерированные классы графа или методы контроллеров напрямую. Он запускает приложение,
отправляет настоящие HTTP-запросы и проверяет настоящие HTTP-ответы.

### Почему сначала black box { #black-box-first }

Приложения Kora быстро запускаются, потому что графы зависимостей генерируются во время компиляции, а большая часть связывания уже известна до выполнения. Это меняет обычный компромисс тестирования.
Во многих фреймворках тесты по принципу черного ящика настолько дороги, что команды оставляют их только для небольшого набора дымовых проверок. В Kora запуск всего приложения часто достаточно практичен, чтобы
сделать тесты по принципу черного ящика главным источником уверенности в поведении, видимом пользователю.

Причина не в том, что компонентные или интеграционные тесты не важны. Они все еще полезны для точечной обратной связи. Причина в том, что многие настоящие ошибки живут между слоями:

- маршрут контроллера связан иначе, чем предполагал тест сервиса
- сопоставление JSON или проверка данных падает до запуска сервисного кода
- конфигурация работает в модульном тесте, но не в упакованном приложении
- миграции и рабочие настройки базы данных не совпадают
- ответ об ошибке имеет неправильный код состояния или форму тела

Тесты по принципу черного ящика ловят такие проблемы, потому что проходят через ту же публичную границу, которую использует настоящий клиент. Они медленнее компонентных тестов, но проверяют поведение, которое
важнее всего для потребителей API.

### Что доказывают внешние тесты { #external-tests-prove }

Тесты по принципу черного ящика ценны, потому что включают весь путь выполнения:

- HTTP-маршрутизацию и коды состояния
- сериализацию и десериализацию JSON
- проверку данных и ответы об ошибках
- загрузку конфигурации
- запуск графа зависимостей
- подключение к базе данных и миграции
- сквозное поведение, например журналирование, пробы или промежуточный слой

Это делает их лучшим типом тестов для поведения, видимого пользователю. Если тест по принципу черного ящика проходит, клиент сможет вызвать приложение тем же способом, каким это сделал тест.

### Контейнеры как тестовая среда { #containers-test-environment }

В этом руководстве само приложение запускается в контейнере, а [PostgreSQL](https://www.postgresql.org/docs/) — в другом контейнере под управлением [Testcontainers](https://java.testcontainers.org/).
Тест общается с приложением по HTTP, а не через внутрипроцессные объекты. Это делает настройку ближе к развертыванию, чем компонентные или интеграционные тесты.

Практический поток тестирования как черный ящик выглядит так:

1. собрать или запустить контейнер приложения
2. запустить контейнеры нужной инфраструктуры
3. передать рабочую конфигурацию в приложение
4. вызвать публичные конечные точки через HTTP
5. проверить коды состояния, заголовки, тела ответов и сохраненное поведение

### Компромиссы { #trade-offs }

Тесты по принципу черного ящика медленнее и требуют [Docker](https://docs.docker.com/), но ловят классы проблем, которые более узкие тесты не видят: неправильные порты, сломанную упаковку, отсутствующую рабочую
конфигурацию, недопустимое окружение контейнера, расхождение HTTP-контракта и проблемы связывания, которые проявляются только при запуске полного приложения.

Они не должны заменять каждый точечный тест. Используйте компонентные тесты для быстрой обратной связи по бизнес-логике, интеграционные тесты для границ хранения данных, а тесты по принципу черного ящика — как
самую сильную проверку того, что полное приложение работает с точки зрения клиента.

Практический поток:

1. упаковать приложение так, чтобы оно могло работать в контейнере
2. запустить PostgreSQL и приложение через Testcontainers
3. внедрить рабочую конфигурацию через переменные окружения контейнера
4. вызвать публичный HTTP API из теста
5. проверить коды ответов, тела JSON и сохраненное состояние

## Зависимости { #dependencies }

Добавьте тестовые зависимости для тестов по принципу черного ящика в модуль с этими тестами.

===! ":fontawesome-brands-java: `Java`"

    Добавьте в `build.gradle`:

    ```groovy
    dependencies {
        testImplementation platform("org.junit:junit-bom:5.14.3")

        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation project(":guide-database-jdbc-app")
        testImplementation "ru.tinkoff.kora:test-junit5"
        testImplementation "org.json:json:20231013"
        testImplementation "org.testcontainers:junit-jupiter:1.21.4"
        testImplementation "org.testcontainers:testcontainers:1.21.4"
        testImplementation "org.testcontainers:postgresql:1.21.4"
    }

    test {
        dependsOn ":guide-database-jdbc-app:distTar"
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

=== ":simple-kotlin: `Kotlin`"

    Добавьте в `build.gradle.kts`:

    ```kotlin
    dependencies {
        testImplementation(platform("org.junit:junit-bom:5.14.3"))

        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation(project(":guide-database-jdbc-app"))
        testImplementation("ru.tinkoff.kora:test-junit5")
        testImplementation("org.json:json:20231013")
        testImplementation("org.testcontainers:junit-jupiter:1.21.4")
        testImplementation("org.testcontainers:testcontainers:1.21.4")
        testImplementation("org.testcontainers:postgresql:1.21.4")
    }

    tasks.test {
        dependsOn(":guide-database-jdbc-app:distTar")
        inputs.file("../guide-database-jdbc-app/Dockerfile")
        inputs.file(project(":guide-database-jdbc-app").tasks.named("distTar").flatMap { it.archiveFile })

        useJUnitPlatform()
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
    ```

## Настройка Dockerfile { #dockerfile-setup }

Перед созданием `AppContainer` добавьте Docker-упаковку для JDBC-приложения из [Интеграции с базой данных](database-jdbc.md).

Создайте `guides/guide-database-jdbc-app/Dockerfile`:

```dockerfile
FROM eclipse-temurin:17-jre-jammy

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

В `build.gradle` модуля тестирования как черный ящик сделайте тесты зависимыми от архива дистрибутива:

```groovy
test {
    dependsOn ":guide-database-jdbc-app:distTar"
    inputs.file("../guide-database-jdbc-app/Dockerfile")
    inputs.file("../guide-database-jdbc-app/build/distributions/application.tar")
}
```

## Контейнер приложения { #application-container }

`AppContainer` — это переиспользуемая обертка вокруг Docker-образа вашего приложения.
Она инкапсулирует детали запуска, чтобы тестовый класс оставался сосредоточен на сценариях, а не на устройстве контейнеров.

Что происходит внутри `AppContainer`:

- собирается образ из Dockerfile JDBC-руководства
- открываются публичный (`8080`) и служебный (`8085`) порты
- перед запуском тестов ожидается `/system/readiness` на служебном порту
- предоставляются вспомогательные методы для построения базового HTTP URI

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/ru/tinkoff/kora/guide/testingblackbox/AppContainer.java`:

    ```java
    package ru.tinkoff.kora.guide.testingblackbox;

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
            withStartupTimeout(Duration.ofMinutes(1));
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

    Создайте `src/test/kotlin/ru/tinkoff/kora/guide/testingblackbox/AppContainer.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.testingblackbox

    import java.net.URI
    import java.nio.file.Path
    import java.time.Duration
    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.GenericContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.containers.wait.strategy.Wait
    import org.testcontainers.images.builder.ImageFromDockerfile

    class AppContainer : GenericContainer<AppContainer>(
        ImageFromDockerfile("guide-database-jdbc-black-box")
            .withDockerfile(Path.of("../guide-database-jdbc-app/Dockerfile"))
    ) {

        init {
            withExposedPorts(8080, 8085)
            withStartupTimeout(Duration.ofMinutes(1))
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200))
            withLogConsumer(Slf4jLogConsumer(LoggerFactory.getLogger(AppContainer::class.java)))
        }

        fun getURI(): URI = URI.create("http://$host:${getMappedPort(8080)}")

        fun getSystemURI(): URI = URI.create("http://$host:${getMappedPort(8085)}")
    }
    ```

## Testcontainers { #testcontainers }

В black-box тесте приложение уже собрано как отдельный Docker-артефакт. Тест не меняет его граф Kora и не добавляет тестовые компоненты внутрь приложения: внутри контейнера запускается тот же код,
который был упакован на этапе сборки.

Менять можно только среду запуска контейнера: переменные окружения, сеть, порты, порядок запуска и внешнюю инфраструктуру. В этом руководстве тест поднимает PostgreSQL рядом с приложением и передает
приложению параметры подключения через `withEnv(...)`. Для приложения это выглядит как обычная production-конфигурация из окружения, просто значения выданы Testcontainers на время теста.

Теперь определите жизненный цикл инфраструктуры в тестовом классе.
`@Testcontainers` включает автоматическое управление жизненным циклом контейнеров, а `@Container` помечает управляемые контейнеры.

На этом шаге:

- `PostgreSQLContainer` предоставляет настоящую БД
- `AppContainer` зависит от запуска Postgres
- значения окружения БД приложения внедряются из методов Postgres-контейнера
- общая сеть используется для доступа между контейнерами по имени узла

===! ":fontawesome-brands-java: `Java`"

    Начните `src/test/java/ru/tinkoff/kora/guide/testingblackbox/BlackBoxTests.java` так:

    ```java
    package ru.tinkoff.kora.guide.testingblackbox;

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

    Начните `src/test/kotlin/ru/tinkoff/kora/guide/testingblackbox/BlackBoxTests.kt` так:

    ```kotlin
    package ru.tinkoff.kora.guide.testingblackbox

    import java.time.Duration
    import org.junit.jupiter.api.Test
    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.Network
    import org.testcontainers.containers.PostgreSQLContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers

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

## Написание тестов { #tests }

После того как контейнерная связка готова, добавьте HTTP-сценарии в тот же класс `BlackBoxTests`.
Эти тесты проверяют поведение API сквозным образом через запущенный контейнер приложения.

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

    Добавьте тестовые методы и вспомогательные методы:

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
    import java.net.http.HttpClient
    import java.net.http.HttpRequest
    import java.net.http.HttpResponse
    import java.util.UUID
    import org.json.JSONArray
    import org.json.JSONObject
    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertTrue
    ```

    Добавьте тестовые методы и вспомогательные методы:

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

!!! tip "Преимущества тестирования как черный ящик"

    Почему стоит отдавать приоритет подходу тестирования как черный ящик?

    - Настоящий пользовательский опыт: тесты проверяют фактические HTTP API так, как ими пользовались бы пользователи
    - Проверка интеграции: ловит проблемы между компонентами, сериализацией и т. д.
    - Проверка контракта: гарантирует сохранение контрактов API
    - Уверенность в развертывании: проверяет поведение полного приложения
    - Предотвращение регрессий: ловит ломающие изменения в поведении, видимом пользователю

!!! note "Управление контейнерами"

    Шаблон `AppContainer` дает:

    - Тестирование на основе Dockerfile: тестирует настоящий образ вашего приложения
    - Изоляцию окружения: свежий контейнер на каждый запуск тестов
    - Интеграцию с проверкой состояния: ожидает готовность приложения
    - Управление портами: автоматическое сопоставление портов и построение URI
    - Интеграцию журналов: журналы приложения доступны в выводе тестов

## Тестирование { #testing }

Запустите тесты по принципу черного ящика через Gradle:

```bash
# Запустить все тесты, включая тесты по принципу черного ящика
./gradlew test

# Run with verbose output
./gradlew test --info
```

!!! tip "Советы по выполнению тестов"

    - Требуется Docker: для тестов по принципу черного ящика нужен Docker, чтобы запускать контейнеры
    - Сетевой доступ: тесты могут занимать больше времени из-за запуска контейнеров
    - Высокое потребление ресурсов: стоит запускать тесты по принципу черного ящика отдельно от модульных тестов
    - Параллельное выполнение: тесты по принципу черного ящика обычно выполняются последовательно из-за конфликтов контейнеров

## Лучшие практики { #best-practices }

Организация тестов:

- Тесты контракта API: проверяйте контракт каждой конечной точки (формат запроса и ответа)
- Тесты бизнес-логики: проверяйте полные пользовательские потоки и бизнес-правила
- Тесты ошибочных сценариев: проверяйте условия ошибок и пограничные случаи
- Интеграционные тесты: проверяйте взаимодействия между сервисами

Управление тестовыми данными:

- Изолированные тестовые данные: каждый тест должен создавать собственные тестовые данные
- Стратегия очистки: используйте очистку базы данных или свежие контейнеры между тестами
- Реалистичные данные: используйте реалистичные тестовые данные, соответствующие промышленным шаблонам
- Проверка данных: проверяйте сохранение и получение данных

Вопросы производительности:

- Переиспользование контейнеров: при возможности переиспользуйте контейнеры, чтобы сократить время запуска
- Параллельное выполнение: запускайте тесты по принципу черного ящика параллельно, когда контейнеры это позволяют
- Ограничения ресурсов: задавайте подходящие ограничения ресурсов для тестовых контейнеров
- Управление ожиданиями: настраивайте подходящие времена ожидания для HTTP-запросов

Отладка тестов по принципу черного ящика:

- Журналы контейнеров: используйте журналы контейнеров для отладки проблем приложения
- Проверка сети: используйте инструменты вроде Wireshark для анализа HTTP-трафика
- Проверка базы данных: напрямую запрашивайте тестовые базы данных для проверки данных
- Метрики приложения: наблюдайте за метриками приложения во время выполнения тестов

## Итоги { #summary }

Тестирование как черный ящик дает максимальную уверенность в корректности приложения Kora, потому что проверяет полный пользовательский опыт через HTTP API. Используя шаблон `AppContainer` с
Testcontainers, вы можете создавать реалистичные, изолированные тестовые среды, которые проверяют поведение приложения сквозным образом.

Главные выводы:

- Сначала тестирование как черный ящик: Kora рекомендует этот подход как основную стратегию тестирования
- Контейнерное тестирование: используйте Docker-контейнеры для реалистичных тестовых сред
- Проверка контракта API: тестируйте полные HTTP-контракты API
- Сквозная проверка: тестируйте полные пользовательские потоки и бизнес-логику
- Изоляция: каждый тест получает свежее окружение с правильной очисткой

Тесты по принципу черного ящика дополняют компонентные и интеграционные тесты, давая финальную проверку того, что приложение работает правильно с точки зрения пользователя.

## Ключевые понятия { #key-concepts }

Стратегия тестирования как черный ящик:

- Сначала тестирование как черный ящик: рекомендуемый Kora основной подход к тестированию для наибольшей уверенности
- Сквозная проверка: тестирование полных пользовательских потоков через HTTP API
- Тестирование контракта API: проверка полных циклов запрос-ответ
- Тестирование с точки зрения пользователя: проверка поведения приложения так, как его видят пользователи

Шаблон контейнера приложения:

- Контейнерные приложения: запуск полных приложений в Docker-контейнерах
- Реалистичные среды: тестирование с настоящей инфраструктурой и зависимостями
- Сетевая изоляция: каждый тест получает выделенные порты и сетевую конфигурацию
- Автоматический жизненный цикл: контейнеры запускаются и останавливаются автоматически вместе с выполнением тестов

Тестирование HTTP API:

- Полный поток запроса: тестирование от HTTP-запроса до базы данных и обратно
- Проверка кодов состояния: проверка правильных HTTP-кодов ответа
- Проверка содержимого ответа: проверка JSON-ответов и корректности данных
- Обработка ошибок: тестирование ошибочных сценариев и правильных ответов об ошибках

Изоляция тестов и производительность:

- Свежие среды: каждый тест начинается с чистого состояния базы данных и приложения
- Очистка ресурсов: автоматическая очистка контейнеров и соединений
- Параллельное выполнение: тесты могут выполняться одновременно для ускорения
- Реалистичная нагрузка: тестирование с настоящими сетевыми вызовами и операциями базы данных

## Устранение неполадок { #troubleshooting }

контейнер приложения не запускается:

- Убедитесь, что Docker запущен и доступен
- Проверьте, что JAR приложения собран и доступен
- Проверьте конфигурацию Docker-образа и базовые образы
- Проверьте журналы контейнера на ошибки запуска

Проблемы HTTP-подключения:

- Убедитесь, что контейнер приложения полностью запущен до выполнения тестов
- Проверьте, что HTTP-порт правильно открыт и сопоставлен
- Проверьте сетевую конфигурацию между тестовым контейнером и контейнером приложения
- Проверьте журналы приложения на проблемы запуска HTTP-сервера

Конфликты портов:

- Убедитесь, что каждый тест использует уникальные порты для контейнеров приложения
- Проверьте, что порты уже не заняты другими процессами
- Используйте динамическое выделение портов, чтобы избежать конфликтов
- Проверьте очистку портов после завершения тестов

!!! tip "Миграции Flyway в тестах"

    Вы можете выполнять миграции Flyway из кода настройки тестов, а не полагаться на автоматический запуск Flyway внутри контейнера приложения.
    Это полезно, когда вам нужен явный контроль миграций в жизненном цикле тестов (например, сброс схемы на каждый набор).
    В этом руководстве мы используем миграции при запуске приложения, чтобы настройка тестирования как черный ящик оставалась простой, но миграции, управляемые тестом, тоже являются допустимым подходом.

Проблемы настройки базы данных:

- Убедитесь, что контейнер базы данных запускается до контейнера приложения
- Проверьте конфигурацию подключения к базе данных в приложении
- Проверьте, что скрипты инициализации схемы базы данных выполняются правильно
- Проверьте журналы контейнера базы данных на ошибки запуска или подключения

Истечения времени ожидания в тестах:

- Увеличьте значения времени ожидания для контейнеров с медленным запуском
- Проверьте время запуска приложения и настройте стратегии ожидания
- Проверьте сетевую связность между контейнерами
- Наблюдайте за использованием ресурсов (CPU/память) во время выполнения тестов

Проблемы очистки контейнеров:

- Убедитесь, что в методах завершения тестов есть правильная очистка
- Проверьте наличие зависших процессов после завершения тестов
- Убедитесь, что демон Docker имеет достаточно ресурсов
- Используйте возможности автоматической очистки Testcontainers

## Что дальше? { #whats-next }

- [Наблюдаемость](observability.md), чтобы открыть пробы, метрики, трассировки и журналы для упакованного приложения, которое вы теперь тестируете сквозным образом.
- [Шаблоны отказоустойчивости](resilient.md), чтобы проверять обработку отказов через HTTP-сценарии.
- [HTTP-сервер OpenAPI](openapi-http-server.md), чтобы перейти от рукописных конечных точек к транспорту, сгенерированному от контракта.
- [HTTP-клиент](http-client.md), чтобы тестировать межсервисные вызовы к запущенному серверу.

## Помощь { #help }

Если вы столкнулись с проблемами:

- сравните тесты по принципу черного ящика с [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app) и [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-jdbc-app)
- проверьте [документацию JUnit5](../documentation/junit5.md)
- проверьте [документацию по миграциям базы данных](../documentation/database-migration.md)
- прочитайте [документацию Testcontainers](https://www.testcontainers.org/)
