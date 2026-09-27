---
title: Никакой магии на этапе выполнения — что на самом деле генерирует фреймворк Kora
date: 2026-08-20
description: Обзор исходных кодов на Java и Kotlin, которые фреймворк Kora генерирует из аннотаций — граф приложения, HTTP-обработчики, JSON-кодеки, репозитории и AOP-прокси, которые можно открыть и прочитать.
search:
  exclude: true
---

# Никакой магии на этапе выполнения: что на самом деле генерирует Kora { #no-runtime-magic }

**20 августа 2026**

Аннотации часто ассоциируют с магией фреймворка. Класс получает `@HttpController`, метод получает `@Transactional`, интерфейс получает `@Repository` — и внезапно работает внедрение зависимостей,
HTTP-запросы достигают методов, выполняются вызовы базы данных, в ответах появляется JSON, а политики отказоустойчивости оборачивают бизнес-логику.

Однако важный вопрос — не использует ли фреймворк аннотации. Важный вопрос — что происходит после того, как эти аннотации прочитаны.

Фреймворк, ориентированный на этап выполнения, может хранить аннотации как метаданные и интерпретировать их во время запуска или работы приложения. Он может сканировать классы, проверять методы,
строить цепочки прокси, создавать обработчики вызовов времени выполнения и динамически разрешать структуру приложения.

Фреймворк Kora идёт другим путём. Его процессоры анализируют объявления приложения во время компиляции и генерируют обычный исходный код на Java или Kotlin. Внедрение зависимостей становится
сгенерированным графом приложения, HTTP-контроллеры становятся обработчиками запросов, репозитории становятся конкретными реализациями, JSON-модели получают сгенерированные ридеры и райдеры, а
AOP-аннотации становятся сгенерированными подклассами или обёртками.

Это означает, что интересная часть Kora — не сама аннотация. Это код, который аннотация производит.

Основную идею можно резюмировать очень просто:

> **Аннотация не обязана означать магию, если реализацию, которую она производит, можно открыть, прочитать и отладить.**

Эта статья прослеживает небольшое приложение Kora через сгенерированные исходные коды и показывает, что на самом деле появляется между аннотацией и выполнением на этапе выполнения.

---

## Начните с обычного приложения { #ordinary-application }

Рассмотрим небольшой HTTP-сервис. На уровне исходного кода он выглядит намеренно обычным:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule {

        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                KoraApplication.run(ApplicationGraph::graph)
            }
        }
    }
    ```

Здесь уже есть одна интересная деталь: `ApplicationGraph` упоминается из кода приложения, но мы его не писали. Kora генерирует его во время компиляции.

Теперь добавим контроллер:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class UserController {

        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        public UserResponse getUser(@Path String id) {
            return userService.getUser(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class UserController(private val userService: UserService) {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        fun getUser(@Path id: String): UserResponse {
            return userService.getUser(id)
        }
    }
    ```

Репозиторий:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("""
            SELECT id, name, email, created_at
            FROM users
            WHERE id = :id
            """)
        Optional<UserDAO> findById(Long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository : JdbcRepository {

        @Query("""
            SELECT id, name, email, created_at
            FROM users
            WHERE id = :id
            """)
        fun findById(id: Long): UserDAO?
    }
    ```

JSON-DTO:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record UserResponse(
        String id,
        String name,
        String email,
        LocalDateTime createdAt
    ) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

И немного отказоустойчивости на слое сервиса:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class UserService {

        @Retryable(DefaultRetry.class)
        public UserResponse getUser(String id) {
            // ...
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class UserService {

        @Retryable(DefaultRetry::class)
        open fun getUser(id: String): UserResponse {
            // ...
        }
    }
    ```

На этом этапе исходный код выглядит похожим на многие JVM-фреймворки, управляемые аннотациями. Архитектурное различие становится видимым только после компиляции.

Выполните:

```bash
./gradlew clean classes
```

и проект получит ещё один слой исходного кода, сгенерированного Kora. Для Java сгенерированные файлы обычно доступны по адресу:

```text
build/generated/sources/annotationProcessor/java/main/
```

а генерация Kotlin обрабатывается через KSP в соответствующем каталоге сгенерированных исходников.

Эти сгенерированные файлы — один из самых наглядных способов понять, что на самом деле делает Kora.

---

## От аннотации к выполнению { #annotation-to-execution }

Для контроллера выше путь от объявления в исходном коде до обработки запроса на этапе выполнения выглядит примерно так:

```text
@HttpController + @HttpRoute
              │
              ▼
     процессор аннотаций
              │
              ▼
 сгенерированный HttpServerRequestHandler
              │
              ▼
       ApplicationGraph
              │
              ▼
          HTTP-роутер
              │
              ▼
           Undertow
```

Другие функции Kora следуют ровно тому же паттерну. `@Json` производит конкретные кодеки, `@Repository` производит реализацию репозитория, аннотации отказоустойчивости производят AOP-подкласс, и все
эти сгенерированные компоненты связываются через один и тот же граф приложения.

Результат — меньше коллекция независимых трюков фреймворка и больше конвейер этапа компиляции, который преобразует декларативный код приложения в явный код JVM.

---

## 1. Внедрение зависимостей становится графом приложения { #dependency-injection }

Внедрение зависимостей — фундамент всей модели.

Приложение Kora начинается с:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application
    ```

Kora использует этот интерфейс как корень графа приложения. Во время компиляции процессор проверяет доступные компоненты и модули, разрешает их зависимости, проверяет граф и выдаёт сгенерированный
код, представляющий результат.

Сгенерированный `ApplicationGraph` содержит узлы компонентов и отношения между ними. В упрощённой форме части его выглядят концептуально так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var controller = graphDraw.addNode(
        ...,
        g -> new UserController(g.get(userService))
    );

    var handler = graphDraw.addNode(
        ...,
        List.of(controller),
        ...,
        g -> generatedControllerModule.getUserHandler(g.get(controller))
    );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val controller = graphDraw.addNode(
        ...,
        { g -> UserController(g.get(userService)) }
    )

    val handler = graphDraw.addNode(
        ...,
        listOf(controller),
        ...,
        { g -> generatedControllerModule.getUserHandler(g.get(controller)) }
    )
    ```

Важная деталь — не точный сгенерированный API, а тот факт, что отношение зависимости уже вычислено. Граф знает, что HTTP-обработчик зависит от контроллера, контроллер зависит от сервиса, а сервис
зависит от других компонентов.

Традиционному DI-контейнеру времени выполнения может понадобиться отвечать на эти вопросы при запуске процесса: какие компоненты существуют, какой конструктор использовать, что удовлетворяет каждый
параметр, неоднозначны ли два кандидата и существует ли цикл. Kora переносит эти рассуждения на этап компиляции.

Поэтому `@Component` лучше понимать не как маркер обнаружения времени выполнения, а как входные данные для генерации графа.

К моменту запуска JVM структура зависимостей — это уже не то, что фреймворку нужно обнаруживать. Она уже закодирована в скомпилированном коде приложения.

---

## 2. `@HttpController` становится конкретным обработчиком запросов { #http-controller }

Теперь рассмотрим HTTP-слой.

Предположим, мы пишем:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class HelloController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        public HttpServerResponse hello() {
            return HttpServerResponse.of(
                200,
                HttpBody.plaintext("Hello, Kora!")
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class HelloController {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        fun hello(): HttpServerResponse {
            return HttpServerResponse.of(
                200,
                HttpBody.plaintext("Hello, Kora!")
            )
        }
    }
    ```

Сам класс не реализует `HttpServerRequestHandler`, и нет ручной регистрации маршрута Undertow. Этот связующий код генерируется.

Kora создаёт модуль контроллера, содержащий фабрики обработчиков. Упрощённый сгенерированный метод выглядит так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface HelloControllerModule {

        default HttpServerRequestHandler get_hello(
            HelloController controller) {

            return HttpServerRequestHandlerImpl.of(
                "GET",
                "/hello",
                request -> controller.hello()
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface HelloControllerModule {

        fun get_hello(controller: HelloController): HttpServerRequestHandler {
            return HttpServerRequestHandlerImpl.of(
                "GET",
                "/hello",
                { request -> controller.hello() }
            )
        }
    }
    ```

Этот код делает поведение `@HttpController` гораздо менее загадочным. Сгенерированная фабрика получает контроллер как обычную зависимость и возвращает обычный `HttpServerRequestHandler`. HTTP-метод,
путь маршрута и вызов контроллера видны прямо в исходном коде.

Для более сложного эндпоинта сгенерированный обработчик также содержит извлечение параметров запроса, маппинг тела, маппинг ответа, перехватчики и интеграцию телеметрии. Файл становится длиннее, но
архитектура остаётся той же: анализ на этапе компиляции производит явный код обработки запросов.

Сгенерированный обработчик затем добавляется в граф приложения и в итоге регистрируется в HTTP-инфраструктуре Kora, которая делегирует в Undertow.

Поэтому фактический путь запроса выглядит как обычные вызовы:

```text
Undertow
   ↓
HTTP-роутер Kora
   ↓
сгенерированный HttpServerRequestHandler
   ↓
UserController.getUser(...)
```

Аннотация определяет контракт эндпоинта. Сгенерированный обработчик — это то, что на самом деле выполняется.

---

## 3. `@Json` становится классами ридера и райдера { #json-codecs }

Сериализация JSON — ещё один полезный пример, потому что многие библиотеки решают её через интроспекцию на этапе выполнения.

В Kora такое объявление:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record UserResponse(
        String id,
        String name,
        String email,
        LocalDateTime createdAt
    ) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

заставляет процессор сгенерировать конкретные JSON-кодеки для этого типа. Для моделей Java эти сгенерированные классы обычно имеют имена, похожие на:

```text
$UserResponse_JsonReader.java
$UserResponse_JsonWriter.java
```

Райдер содержит прямой код сериализации. В упрощённой форме:

===! ":fontawesome-brands-java: `Java`"

    ```java
    generator.writeStartObject();

    generator.writeName("id");
    generator.writeString(value.id());

    generator.writeName("name");
    generator.writeString(value.name());

    generator.writeName("createdAt");
    createdAtWriter.write(generator, value.createdAt());

    generator.writeEndObject();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    generator.writeStartObject()

    generator.writeName("id")
    generator.writeString(value.id)

    generator.writeName("name")
    generator.writeString(value.name)

    generator.writeName("createdAt")
    createdAtWriter.write(generator, value.createdAt)

    generator.writeEndObject()
    ```

Ридер выполняет обратную операцию: читает токены, сопоставляет имена свойств, разбирает значения, валидирует обязательные поля и в итоге конструирует запись.

Концептуально:

===! ":fontawesome-brands-java: `Java`"

    ```java
    String id = null;
    String name = null;

    // цикл парсера...

    return new UserResponse(
        id,
        name,
        email,
        createdAt
    );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    var id: String? = null
    var name: String? = null

    // цикл парсера...

    return UserResponse(
        id,
        name,
        email,
        createdAt
    )
    ```

Сгенерированный кодек может сам зависеть от других кодеков. Например, `JsonWriter<LocalDateTime>` внедряется через граф приложения и вызывается напрямую сгенерированным райдером `UserResponse`.

Это важное отличие от рефлексии на этапе выполнения. `@Json` не означает «запомни этот класс и проверь его поля позже». Это означает «сгенерируй реализацию сериализации для этого класса во время
компиляции».

Когда приложение позже возвращает `UserResponse`, HTTP-слой может вызвать конкретный сгенерированный райдер, а не обнаруживать структуру DTO по требованию.

---

## 4. `@Repository` становится обычным кодом JDBC { #repository-jdbc }

Репозитории делают модель этапа компиляции особенно легко видимой.

Возьмём:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("""
            SELECT id, name, email
            FROM users
            WHERE id = :id
            """)
        Optional<UserDAO> findById(Long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository : JdbcRepository {

        @Query("""
            SELECT id, name, email
            FROM users
            WHERE id = :id
            """)
        fun findById(id: Long): UserDAO?
    }
    ```

Интерфейс исходного кода не содержит тела метода, но после компиляции Kora производит реализацию, обычно с именем вроде:

```text
$UserRepository_Impl.java
```

Эта реализация содержит механизмы, необходимые для выполнения запроса. Упрощённая версия может выглядеть так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Optional<UserDAO> findById(Long id) {
        var connection = executor.currentConnection();

        try (var statement = connection.prepareStatement(
            "SELECT id, name, email FROM users WHERE id = ?")) {

            statement.setLong(1, id);

            try (var resultSet = statement.executeQuery()) {
                return resultSetMapper.apply(resultSet);
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun findById(id: Long): UserDAO? {
        val connection = executor.currentConnection()

        connection.prepareStatement(
            "SELECT id, name, email FROM users WHERE id = ?"
        ).use { statement ->
            statement.setLong(1, id)

            statement.executeQuery().use { resultSet ->
                return resultSetMapper.apply(resultSet)
            }
        }
    }
    ```

Реальная сгенерированная реализация также содержит телеметрию Kora, обработку соединений, контекст запроса, маппинг исключений и любую дополнительную интеграцию, которая требуется репозиторию.

Но структурно это всё ещё код JDBC.

Разработчик пишет важную часть:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("SELECT ...")
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("SELECT ...")
    ```

а компилятор генерирует повторяющийся связующий код вокруг неё: подготовленные операторы, привязку параметров, выполнение, маппинг, очистку ресурсов и телеметрию.

На этапе выполнения такой вызов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    userRepository.findById(id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    userRepository.findById(id)
    ```

— это просто обычный вызов интерфейса к сгенерированной реализации. Нет необходимости в универсальном обработчике вызовов времени выполнения, который проверял бы метод и решал, какой запрос выполнить.

Это один из лучших примеров философии Kora: сохранить явный SQL и информацию о типах, затем сгенерировать скучный механический код вокруг них.

---

## 5. AOP становится классом, который можно открыть { #aop-class }

AOP — это часто то место, где фреймворки, управляемые аннотациями, ощущаются наиболее непрозрачными.

Рассмотрим:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class UserService {

        @Retryable(DefaultRetry.class)
        public UserResponse getUser(String id) {
            return loadUser(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class UserService {

        @Retryable(DefaultRetry::class)
        open fun getUser(id: String): UserResponse {
            return loadUser(id)
        }
    }
    ```

Во фреймворке, ориентированном на этап выполнения, внедрённый `UserService` может на самом деле быть динамически созданным прокси, чья цепочка вызовов строится после запуска.

Kora вместо этого генерирует подкласс во время компиляции. Для аспекта повтора результат концептуально похож на:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class $UserService__AopProxy extends UserService {

        private final Retry retry;

        @Override
        public UserResponse getUser(String id) {
            return retry.retry(() -> super.getUser(id));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class `$UserService__AopProxy`(
        private val retry: Retry
    ) : UserService() {

        override fun getUser(id: String): UserResponse {
            return retry.retry { super.getUser(id) }
        }
    }
    ```

Это и есть слой AOP.

Исходный бизнес-метод по-прежнему вызывается через `super.getUser(id)`, а сгенерированное переопределение оборачивает вызов требуемой политикой.

Та же модель применяется, когда комбинируются несколько аспектов. Предположим, метод использует:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CircuitBreakable(DefaultCircuitBreaker.class)
    @Retryable(DefaultRetry.class)
    @Timeout(DefaultTimeout.class)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CircuitBreakable(DefaultCircuitBreaker::class)
    @Retryable(DefaultRetry::class)
    @Timeout(DefaultTimeout::class)
    ```

Сгенерированный подкласс может содержать цепочку, эквивалентную:

===! ":fontawesome-brands-java: `Java`"

    ```java
    return circuitBreaker.execute(() ->
        retry.retry(() ->
            timeout.execute(() ->
                super.getUsers()
            )
        )
    );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    return circuitBreaker.execute {
        retry.retry {
            timeout.execute {
                super.getUsers()
            }
        }
    }
    ```

Точная сгенерированная структура может быть разбита на вспомогательные методы, но порядок виден прямо в исходном коде.

Это важно, потому что порядку AOP больше не нужно оставаться абстрактной концепцией фреймворка. Если вы хотите знать, какая задача оборачивает какую, вы можете открыть сгенерированный прокси и
прочитать вызовы в том порядке, в котором они фактически выполняются.

Фреймворк по-прежнему предоставляет перехватывание. Исчезает необходимость в том, чтобы это перехватывание оставалось скрытым.

---

## Собирая части вместе { #pieces-together }

Каждый сгенерированный артефакт по отдельности прост. DI становится `ApplicationGraph`, HTTP-аннотации становятся обработчиками запросов, `@Json` становится сериализаторами и десериализаторами,
`@Repository` становится конкретной реализацией базы данных, а AOP-аннотации становятся сгенерированными подклассами.

Более интересная картина появляется, когда все они соединены.

Рассмотрим:

```http
GET /users/42
```

Упрощённый поток запроса выглядит так:

```text
Undertow
   ↓
HTTP-роутер Kora
   ↓
сгенерированный HttpServerRequestHandler
   ↓
UserController
   ↓
сгенерированный AOP-подкласс UserService
   ↓
UserService
   ↓
сгенерированный $UserRepository_Impl
   ↓
JDBC
   ↓
PostgreSQL
```

На пути ответа снова появляется сгенерированный код маппинга:

```text
Результат PostgreSQL
   ↓
сгенерированный JDBC-маппер
   ↓
UserDAO
   ↓
UserService
   ↓
UserResponse
   ↓
сгенерированный JsonWriter<UserResponse>
   ↓
HTTP-ответ
   ↓
Undertow
```

Сгенерированный граф приложения соединяет эти объекты и предоставляет их зависимости.

Это означает, что когда что-то ведёт себя неожиданно, обычно есть очень конкретное место для поиска. Если маршрутизация выглядит неверной, проверьте сгенерированный модуль контроллера. Если вывод JSON
некорректен, проверьте сгенерированный райдер. Если параметр запроса привязан неверно, проверьте сгенерированный репозиторий. Если повторы оборачивают не ту операцию, проверьте AOP-прокси. Если
внедрение зависимостей ведёт себя неожиданно, проверьте граф приложения.

Вы отлаживаете реализацию, а не пытаетесь реконструировать невидимое состояние фреймворка.

---

## Сгенерированный исходный код — это не генерация кода на этапе выполнения { #generated-source }

Здесь есть важное различие, потому что термин «генерация кода» может означать несколько вещей.

Фреймворк может динамически генерировать байткод во время запуска. Он может создавать классы прокси на этапе выполнения. Он может инструментировать классы агентами или строить механизмы вызовов из
метаданных рефлексии.

Модель Kora гораздо проще: его процессоры аннотаций и KSP-процессоры генерируют файлы исходного кода `.java` или `.kt` во время компиляции, и эти файлы затем компилируются обычным образом `javac` или
`kotlinc`.

Поэтому конвейер таков:

```text
исходный код приложения
       +
аннотации
       ↓
процессор аннотаций Kora / KSP
       ↓
сгенерированный исходный код Java / Kotlin
       ↓
javac / kotlinc
       ↓
обычные классы JVM
```

Как только компиляция завершена, JVM не важно, какой класс написан вручную, а какой сгенерирован. Все они — обычные скомпилированные классы.

Именно поэтому читаемая генерация исходного кода так важна для архитектуры Kora.

---

## Аннотации как DSL этапа компиляции { #compile-time-dsl }

Полезная ментальная модель — думать об аннотациях Kora как о небольшом декларативном языке для компилятора.

Когда вы пишете:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = GET, path = "/users/{id}")
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = GET, path = "/users/{id}")
    ```

вы фактически говорите:

> Сгенерируй обработчик запросов для этого маршрута, распарси требуемые аргументы, вызови этот метод и сопоставь результат с HTTP-ответом.

Когда вы пишете:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    @Query(...)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    @Query(...)
    ```

вы говорите:

> Сгенерируй реализацию, которая выполняет этот запрос, используя объявленные типы метода и доступные мапперы.

Когда вы пишете:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retryable(DefaultRetry.class)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retryable(DefaultRetry::class)
    ```

вы говорите:

> Сгенерируй обёртку, которая вызывает этот метод через выбранную политику повтора.

Это лучшая модель, чем думать об аннотациях как о постоянных метаданных времени выполнения. В Kora многие аннотации — просто краткие входные данные для генерации исходного кода.

---

## Почему читаемый сгенерированный код важен { #readable-code }

Одна лишь генерация на этапе компиляции не гарантирует прозрачности. Фреймворк мог бы генерировать огромные и фактически нечитаемые файлы исходного кода и всё равно заявлять, что работает на этапе
компиляции.

Kora явно нацелен на сгенерированный код, который инженеры могут проверять. У этого есть практические следствия.

Предположим, у JSON-поля неожиданное имя. Вы можете открыть сгенерированный райдер и увидеть литеральное имя свойства, которое он выводит.

Предположим, репозиторий, кажется, привязывает параметры неверно. Вы можете открыть `$UserRepository_Impl` и проверить точные вызовы `PreparedStatement`.

Предположим, несколько аспектов отказоустойчивости взаимодействуют в неожиданном порядке. Вы можете открыть `$UserService__AopProxy` и проследить вложенность.

Предположим, DI выбрал компонент, которого вы не ожидали. Вы можете проверить сгенерированный граф приложения и увидеть, как этот компонент попал в граф.

Ключевое преимущество не в том, что разработчики должны каждый день читать сгенерированный код. При обычной разработке большая его часть должна оставаться невидимой. Преимущество в том, что когда
абстракция протекает, под ней ждёт конкретная реализация.

---

## Сгенерированный код — это исполняемая документация { #executable-docs }

Сгенерированный исходный код также полезен как форма исполняемой документации.

Интерфейс репозитория говорит:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("... WHERE id = :id")
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("... WHERE id = :id")
    ```

Сгенерированная реализация говорит вам точно, как `:id` становится параметром JDBC, какой маппер обрабатывает результат, какая телеметрия окружает вызов и какой исполнитель предоставляет соединение.

Контроллер говорит:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(...)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(...)
    ```

Сгенерированный обработчик показывает зарегистрированный HTTP-метод и путь, точный вызов метода контроллера и то, какие мапперы запроса и ответа задействованы.

Сервис говорит:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retryable
    @Timeout
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retryable
    @Timeout
    ```

Сгенерированный AOP-подкласс говорит вам, какой аспект находится снаружи и где в итоге вызывается исходный метод.

Документация может устаревать. Сгенерированный код не может расходиться со скомпилированным приложением так же, потому что он — часть кода, который произвёл это приложение.

---

## Инфраструктура времени выполнения всё ещё существует { #runtime-infrastructure }

«Никакой магии на этапе выполнения» не означает «никакого фреймворка на этапе выполнения».

Undertow по-прежнему принимает сетевые соединения. HTTP-роутер по-прежнему сопоставляет запросы. Граф приложения по-прежнему управляет жизненным циклом компонентов. JDBC по-прежнему общается с базой
данных. Предохранители по-прежнему хранят состояние, повторы по-прежнему считают попытки, а телеметрия по-прежнему записывает активность на этапе выполнения.

Это по своей природе обязанности этапа выполнения.

Важное различие в том, что Kora старается не откладывать **структурные решения** до этапа выполнения, если они уже познаваемы на этапе компиляции.

Маршрут контроллера известен, поэтому обработчик можно сгенерировать. Метод репозитория и SQL известны, поэтому реализацию можно сгенерировать. Структура DTO известна, поэтому JSON-кодек можно
сгенерировать. AOP-аннотации известны, поэтому обёртку можно сгенерировать. Зависимости компонентов известны, поэтому граф приложения можно сгенерировать.

Затем этап выполнения отвечает за выполнение этих реализаций, а не за их обнаружение.

---

## От магии к механическому коду { #mechanical-code }

Как только вы проверяете сгенерированные исходные коды, многие функции Kora становятся удивительно обычными.

`@HttpController` превращается в фабрику обработчиков. `@Json` превращается в вызовы парсера и генератора. `@Repository` превращается в подготовленные операторы. `@Retryable` превращается в один вызов
метода, оборачивающий другой. `@Component` превращается в узел внутри сгенерированного графа зависимостей.

Эта обычность — функция.

Инфраструктурный связующий код часто повторяем и неприятен для ручного написания, но ему не нужно оставаться загадочным просто потому, что его генерирует фреймворк.

Предложение Kora не в том, чтобы заставить разработчиков писать весь этот код самим. Оно в том, чтобы позволить компилятору писать повторяющиеся части, сохраняя реализацию, которую инженеры всё ещё
могут проверять.

---

## Аннотация ≠ магия { #annotation-magic }

Использует ли фреймворк аннотации, говорит очень мало о том, насколько прозрачен этот фреймворк.

Важен жизненный цикл аннотации.

Если:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    ```

означает:

```text
сохранить метаданные
→ обнаружить их во время запуска
→ создать механизмы вызовов времени выполнения
→ интерпретировать вызовы динамически
```

то большая часть поведения остаётся скрытой внутри фреймворка времени выполнения.

Если та же аннотация означает:

```text
@Repository
    ↓
процессор аннотаций
    ↓
$UserRepository_Impl.java
    ↓
javac
    ↓
обычная реализация репозитория
```

то аннотация — просто компактный способ попросить компилятор написать предсказуемый шаблонный код.

Тот же принцип применим к HTTP, JSON, DI и AOP.

Это даёт нам полезное определение магии фреймворка:

> **Аннотация не является магией, когда вы можете открыть реализацию, которую она произвела, и понять, что приложение будет фактически выполнять.**

Вот что читаемые сгенерированные исходные коды означают на практике.

Аннотации предоставляют лаконичную модель программирования. Процессоры генерируют механическую реализацию. Граф приложения связывает эти реализации вместе. На этапе выполнения JVM выполняет обычный
скомпилированный код.

Полный путь остаётся видимым:

```text
аннотация
    ↓
процессор этапа компиляции
    ↓
сгенерированный исходный код Java / Kotlin
    ↓
сгенерированный граф приложения
    ↓
обычное выполнение JVM
```

Фреймворк по-прежнему избавляет разработчиков от ручного написания повторяющейся инфраструктуры. Он просто не требует, чтобы эта инфраструктура оставалась невидимой.
