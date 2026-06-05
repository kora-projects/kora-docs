---
search:
  exclude: true
title: Компонентное тестирование в Kora
summary: Learn comprehensive component and integration testing strategies for Kora applications including dependency injection testing and database integration with Testcontainers
tags: testing, junit, testcontainers, integration-tests, component-tests
---

# Компонентное тестирование в Kora { #component-testing-kora }

Это руководство знакомит с основным подходом к тестированию приложений Kora с помощью JUnit. В нем рассматривается, как тестовые аннотации Kora создают управляемые графы приложения, как подмены и
изменения графа изолируют компоненты, и как тесты с Testcontainers проверяют поведение на инфраструктуре, близкой к реальной. Вы также увидите, как тесты служб, контроллеров, интеграционные тесты и
тесты по принципу черного ящика складываются в одну практичную стратегию тестирования.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Testing JUnit App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-testing-junit-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Testing JUnit App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-testing-junit-app).

## Что вы создадите { #youll-build }

Вы создадите полноценный набор тестов, который покрывает:

- **компонентные тесты**: проверку взаимодействия служб с настоящими зависимостями
- **интеграционные тесты**: проверку с настоящими базами данных через Testcontainers
- **тестовые утилиты**: переиспользуемую тестовую инфраструктуру и вспомогательные средства

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- пройденное руководство [HTTP-сервер](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по HTTP-серверу"

    Это руководство предполагает, что вы уже прошли **[HTTP-сервер](http-server.md)** и у вас есть рабочий проект Kora с `UserService`, `UserController`, DTO и потоком работы через репозиторий в памяти.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь тестируется уже существующее поведение службы и контроллера, а не создается приложение с нуля.

## Обзор { #overview }

Тестирование приложения Kora с [JUnit](https://junit.org/junit5/docs/current/user-guide/) начинается с выбора правильной границы для вопроса, на который должен ответить тест. Тест службы может
ответить, корректно ли работает бизнес-логика. Интеграционный тест может ответить, работает ли служба с настоящей инфраструктурой. Тест по принципу черного ящика может ответить, корректно ли полноценное
приложение ведет себя через открытый API.

Важное отличие от обычного модульного тестирования в том, что код Kora часто определяется графом приложения. Конструкторы, сгенерированные компоненты, конфигурация и модули фреймворка влияют на
поведение, поэтому тесты должны явно показывать, какую часть графа они проверяют.

### Уровни тестирования { #testing-levels }

Это руководство вводит основные уровни тестирования, которые используются в руководствах Kora:

- компонентные тесты строят часть графа Kora и заменяют выбранные зависимости подменами
- интеграционные тесты оставляют больше настоящих компонентов и добавляют инфраструктуру, например [PostgreSQL](https://www.postgresql.org/docs/)
  через [Testcontainers](https://java.testcontainers.org/)
- тесты по принципу черного ящика запускают полноценное приложение и взаимодействуют с ним только через открытые HTTP API

Эти уровни не конкурируют друг с другом. Они по-разному соотносят скорость, изоляцию и уверенность. Компонентные тесты полезны для быстрой обратной связи и проверки сфокусированного поведения.
Интеграционные тесты полезны, когда важны SQL, конфигурация, миграции или настоящие клиенты. Тесты по принципу черного ящика дают самую сильную уверенность на уровне пользователя, потому что включают
маршрутизацию, сериализацию, конфигурацию, связывание фреймворка и инфраструктуру.

### Тестовые графы Kora { #kora-test-graphs }

Граф Kora, создаваемый во время компиляции, является важным инструментом тестирования. `@KoraAppTest` может запустить граф приложения для теста, а аннотации изменения графа могут заменять компоненты,
внедрять подмены или добавлять компоненты только для тестов. Так тесты остаются близкими к настоящему связыванию приложения, но при этом не заставляют каждый тест запускать всю среду выполнения.

Важная идея в том, что тест Kora часто проверяет форму графа, а не только отдельный класс. Это полезно, когда поведение зависит от внедрения зависимостей, сгенерированных компонентов, конфигурации или
модулей фреймворка.

### Testcontainers и реалистичность { #testcontainers-realism }

Проверки быстрые, но они не доказывают, что SQL выполняется, миграции соответствуют коду или внешние протоколы настроены правильно. Testcontainers дает тестам изолированную настоящую инфраструктуру,
например PostgreSQL, и при этом сохраняет окружение одноразовым и повторяемым.

Это руководство закладывает основу для последующих специальных руководств по тестированию: используйте компонентные тесты для сфокусированной обратной связи, интеграционные тесты для границ с
инфраструктурой, а тесты по принципу черного ящика — как самую сильную проверку поведения полноценного приложения.

Практический ход такой:

1. добавить зависимости JUnit, Mockito для Java, MockK для Kotlin, Kora test и Testcontainers
2. объявить тестовый граф Kora
3. заменить выбранные зависимости подменами
4. проверить поведение службы через компоненты, управляемые графом
5. добавить переопределения конфигурации для тестовых сценариев
6. подготовить проект к более глубокому интеграционному тестированию и тестированию как черный ящик

## Зависимости { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    Добавьте следующие тестовые зависимости в `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        // ... существующие зависимости ...

        testImplementation(platform("org.junit:junit-bom:5.14.3"))
        testImplementation(project(":guide-http-server-app"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:http-server-undertow")

        // Тестовый фреймворк Kora с интеграцией JUnit 5
        testImplementation("ru.tinkoff.kora:test-junit5")

        // Фреймворк подмен для компонентного тестирования
        testImplementation("org.mockito:mockito-core:5.23.0")
    }

    test {
        useJUnitPlatform()
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
        // ... существующие зависимости ...

        testImplementation(platform("org.junit:junit-bom:5.14.3"))
        testImplementation(project(":guide-http-server-app"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:http-server-undertow")

        // Тестовый фреймворк Kora с интеграцией JUnit 5
        testImplementation("ru.tinkoff.kora:test-junit5")

        // Фреймворк подмен для компонентного тестирования Kotlin
        testImplementation("io.mockk:mockk:1.13.11")
    }

    tasks.test {
        useJUnitPlatform()
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
    ```

## Компонентные тесты { #kora-component-tests }

Компонентный тест в Kora находится между простой проверкой отдельного класса и полноценным запуском приложения. Вы не создаете `UserService` руками через `new` и не собираете его зависимости
вручную. Вместо этого тест просит Kora построить небольшой тестовый граф, достать из него нужный компонент и внедрить этот компонент в тестовый класс.

Это важно по двум причинам:

- тест проверяет тот же способ связывания зависимостей, который используется в приложении
- граф можно ограничить только теми компонентами, которые нужны конкретному тесту
- такой обрезанный граф собирается очень быстро, потому что `@KoraAppTest` не инициализирует лишние ветки приложения
- по умолчанию тестовый граф создается заново для каждого тестового метода, если вы явно не выбрали другой жизненный цикл JUnit

В этом руководстве мы сначала подключим настоящий `UserService` как тестовый компонент. Потом заменим его зависимость `UserRepository` моком и посмотрим, как такая подмена попадает в граф.

### Тестовый компонент { #test-component }

Начните с самого простого варианта: попросите Kora дать тесту настоящий компонент `UserService`.

`@KoraAppTest(Application.class)` говорит JUnit-расширению Kora, какой `@KoraApp` использовать как источник графа. Это не означает, что тест обязательно поднимет все приложение целиком. Тестовый граф
ограничивается компонентами, которые вы явно запросили через `@TestComponent`, и зависимостями, которые нужны этим компонентам.

`@TestComponent` на поле `userService` означает две вещи одновременно:

- этот компонент нужно найти в графе приложения и внедрить в поле тестового класса
- этот компонент становится одной из корневых точек тестового графа

То есть Kora начинает с `UserService`, смотрит его конструктор, находит нужные зависимости и добавляет только необходимую часть графа. Если `UserService` зависит от `UserRepository`, то репозиторий
тоже попадет в тестовый граф. Если HTTP-сервер, контроллеры или другие компоненты не нужны для создания `UserService`, они не обязаны инициализироваться в таком компонентном тесте.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/ru/tinkoff/kora/guide/testingjunit/UserServiceComponentTest.java`:

    ```java
    package ru.tinkoff.kora.guide.testingjunit;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertNotNull;

    import org.junit.jupiter.api.Test;
    import ru.tinkoff.kora.guide.httpserver.Application;
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest;
    import ru.tinkoff.kora.guide.httpserver.service.UserService;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class)
    class UserServiceComponentTest {

        @TestComponent
        private UserService userService;

        @Test
        void createUserWithRealGraph() {
            var request = new UserRequest("John", "john@example.com");

            var result = userService.createUser(request);

            assertNotNull(result);
            assertEquals("John", result.name());
            assertEquals("john@example.com", result.email());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/test/kotlin/ru/tinkoff/kora/guide/testingjunit/UserServiceComponentTest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.testingjunit

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Test
    import ru.tinkoff.kora.guide.httpserver.Application
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest
    import ru.tinkoff.kora.guide.httpserver.service.UserService
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.TestComponent

    @KoraAppTest(Application::class)
    class UserServiceComponentTest {

        @TestComponent
        lateinit var userService: UserService

        @Test
        fun createUserWithRealGraph() {
            val request = UserRequest("John", "john@example.com")

            val result = userService.createUser(request)

            assertNotNull(result)
            assertEquals("John", result.name())
            assertEquals("john@example.com", result.email())
        }
    }
    ```

На этом шаге нет мока. `UserService` настоящий, его зависимости тоже настоящие, если Kora может построить их из приложения. Такой тест полезен, когда зависимость дешевая и полностью локальная:
например, репозиторий из HTTP-гайда хранит данные в памяти и не требует внешней базы данных.

### Жизненный цикл тестового графа { #test-graph-lifecycle }

Когда JUnit запускает тестовый класс с `@KoraAppTest`, расширение Kora делает несколько вещей до выполнения тестового метода:

1. берет `Application` из `@KoraAppTest`
2. строит тестовую версию графа приложения
3. оставляет в графе компоненты, запрошенные через `@TestComponent`, и их зависимости
4. применяет тестовые подмены, если они объявлены
5. инициализирует нужные компоненты графа
6. внедряет готовые компоненты в поля, конструктор или параметры тестовых методов

После этого выполняется обычный JUnit-тест. Для тестового метода `userService` уже является не `null`, а готовым компонентом из графа Kora.

Практически это означает следующее:

- конструктор `UserService` вызывается Kora, а не тестом
- зависимости `UserService` берутся из того же описания приложения, что и в реальном графе
- компоненты, которые не нужны запрошенной части графа, не создаются только ради теста
- если компонент имеет жизненный цикл, она выполняется в рамках инициализации тестового графа
- после завершения тестового контекста Kora закрывает инициализированные ранее компоненты
- по умолчанию такой контейнер создается с нуля для каждого тестового метода; если нужно один раз на весь класс, в документации Kora используется `@TestInstance(TestInstance.Lifecycle.PER_CLASS)`

Такой тест отвечает на вопрос: “может ли Kora построить нужную часть приложения, и ведет ли себя настоящий компонент правильно?” Но иногда настоящая зависимость мешает сфокусированной проверке. Например,
вы хотите проверить сортировку, обработку `404` или вызов репозитория, не завися от состояния хранилища. Тогда нужна подмена.

### Мок компонента { #mock-component }

Мок — это тестовая замена настоящего компонента. Он выглядит для графа как обычный компонент нужного типа, но его поведение задается в тесте.

Конкретный фреймворк моков зависит от языка, но роль подмены остается одинаковой:

- аннотация мок-фреймворка создает мок нужного типа
- `@TestComponent` сообщает Kora, что этот мок является компонентом тестового графа
- тип поля `UserRepository` говорит, какой компонент приложения нужно заменить

Самое важное: мок попадает не только в поле тестового класса. Kora также внедряет этот же мок во все компоненты графа, которым нужен `UserRepository`. Поэтому `UserService` остается настоящим, но его
конструктор получает уже не настоящий in-memory репозиторий, а тестовую подмену.

Граф для такого теста можно представить так:

```text
test field userRepository
        |
        | same mock instance
        v
UserService ---depends on--- UserRepository
   ^                         ^
   |                         |
@TestComponent          mock @TestComponent
real component          replacement component
```

В результате тест получает две точки контроля:

- через `userRepository` можно задать ответы зависимости
- через `userService` можно вызвать настоящий код службы и проверить результат

===! ":fontawesome-brands-java: `Java`"

    В Java используйте Mockito: `@Mock` создает мок `UserRepository`, а `when(...).thenReturn(...)` задает ответ для конкретного вызова зависимости.

    Обновите тестовый класс:

    ```java
    package ru.tinkoff.kora.guide.testingjunit;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.mockito.Mockito.verify;
    import static org.mockito.Mockito.when;

    import java.time.LocalDateTime;
    import java.util.Optional;
    import org.junit.jupiter.api.Test;
    import org.mockito.Mock;
    import ru.tinkoff.kora.guide.httpserver.Application;
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse;
    import ru.tinkoff.kora.guide.httpserver.repository.UserRepository;
    import ru.tinkoff.kora.guide.httpserver.service.UserService;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class)
    class UserServiceComponentTest {

        @Mock
        @TestComponent
        private UserRepository userRepository;

        @TestComponent
        private UserService userService;

        @Test
        void getUserUsesRepositoryMock() {
            var expected = new UserResponse("1", "John", "john@example.com", LocalDateTime.now());
            when(userRepository.findById("1")).thenReturn(Optional.of(expected));

            var result = userService.getUser("1");

            assertEquals(Optional.of(expected), result);
            verify(userRepository).findById("1");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    В Kotlin используйте MockK: `@MockK` создает мок `UserRepository`, а `every { ... } returns ...` задает ответ для конкретного вызова зависимости без экранирования ключевых слов Kotlin.

    Обновите тестовый класс:

    ```kotlin
    package ru.tinkoff.kora.guide.testingjunit

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Test
    import io.mockk.every
    import io.mockk.impl.annotations.MockK
    import io.mockk.verify
    import ru.tinkoff.kora.guide.httpserver.Application
    import ru.tinkoff.kora.guide.httpserver.dto.UserResponse
    import ru.tinkoff.kora.guide.httpserver.repository.UserRepository
    import ru.tinkoff.kora.guide.httpserver.service.UserService
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.TestComponent
    import java.time.LocalDateTime

    @KoraAppTest(Application::class)
    class UserServiceComponentTest {

        @MockK
        @TestComponent
        lateinit var userRepository: UserRepository

        @TestComponent
        lateinit var userService: UserService

        @Test
        fun getUserUsesRepositoryMock() {
            val expected = UserResponse("1", "John", "john@example.com", LocalDateTime.now())
            every { userRepository.findById("1") } returns expected

            val result = userService.getUser("1")

            assertEquals(expected, result)
            verify { userRepository.findById("1") }
        }
    }
    ```

Теперь тест проверяет не репозиторий, а поведение `UserService` при заданном ответе репозитория. Это и есть основная ценность мока: вы фиксируете поведение зависимости и проверяете реакцию компонента,
который находится над ней.

### Что именно инициализируется { #what-is-initialized }

В тесте с мокнутым `UserRepository` граф становится меньше и понятнее:

- `UserService` создается как настоящий компонент приложения
- `UserRepository` заменяется тестовым моком
- компоненты, которые нужны только настоящему `UserRepository`, больше не нужны и не попадают в тестовый граф
- HTTP-сервер и контроллеры не создаются, если вы не запросили их как `@TestComponent`
- тестовый класс получает ссылки на оба компонента: настоящий `userService` и мокнутый `userRepository`

Это отличается от обычного ручного компонентного теста с моками без Kora. В таком тесте вы часто пишете `new UserService(userRepository)` руками. В Kora-тесте это делает граф. Поэтому тест
одновременно проверяет:

- что `UserService` действительно является компонентом графа
- что Kora умеет собрать его с нужной зависимостью
- что подмена зависимости применяется в том же месте, где production-граф использовал бы настоящий компонент
- что бизнес-логика службы работает при заданных ответах зависимости

Не используйте отдельное JUnit-расширение мок-фреймворка вместе с `@KoraAppTest`. Жизненным циклом моков и их внедрением в граф управляет `@KoraAppTest`. Если подключить второе JUnit-расширение,
становится неочевидно, кто создает мок, кто сбрасывает его состояние и какой экземпляр попадает в граф.

### Написание тестов { #write-tests }

Теперь добавьте проверки основного поведения службы с подмененным репозиторием. В каждом тесте есть три части: сначала вы задаете поведение зависимости, затем вызываете настоящий `UserService`, а
после этого проверяете результат и факт обращения к репозиторию.

Разберем первый тест. `assertNotNull(result)` проверяет, что служба вообще вернула ответ, а не `null`. `assertEquals("1", result.id())`, `assertEquals("John", result.name())` и проверка email
фиксируют контракт ответа: идентификатор пришел из репозитория, а имя и почта перенесены из запроса без искажений. Проверка вызова репозитория дополняет asserts: она проверяет уже не значение
результата, а взаимодействие с зависимостью.

В примерах ниже используются стандартные assertions из JUnit Jupiter: `assertEquals`, `assertNotNull`, `assertTrue`, `assertThrows`. Для более выразительных проверок в реальных проектах можно
подключить AssertJ и писать проверки в стиле `assertThat(result.name()).isEqualTo("John")`, `assertThat(result).isNotNull()` или `assertThatThrownBy { ... }`.

===! ":fontawesome-brands-java: `Java`"

    В Java-версии поведение мока задается через Mockito: `when(...).thenReturn(...)` говорит, что должен вернуть репозиторий при конкретном вызове. `verify(userRepository).save(...)` проверяет, что
    настоящий `UserService` действительно обратился к репозиторию с ожидаемыми аргументами. Это полезно, когда результат метода важен, но не менее важно убедиться, что служба использует правильную
    зависимость и не пропускает нужное действие.

    Добавьте импорты:

    ```java
    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertNotNull;
    import static org.junit.jupiter.api.Assertions.assertThrows;
    import static org.junit.jupiter.api.Assertions.assertTrue;

    import java.util.List;
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    ```

    Добавьте тестовые методы:

    ```java
    @Test
    void createUser_ShouldCreateAndReturnUser() {
        var request = new UserRequest("John", "john@example.com");

        when(userRepository.save("John", "john@example.com")).thenReturn("1");

        var result = userService.createUser(request);

        assertNotNull(result);
        assertEquals("1", result.id());
        assertEquals("John", result.name());
        assertEquals("john@example.com", result.email());
        verify(userRepository).save("John", "john@example.com");
    }

    @Test
    void getUser_ShouldReturnUserWhenExists() {
        var expected = new UserResponse("1", "John", "john@example.com", LocalDateTime.now());
        when(userRepository.findById("1")).thenReturn(Optional.of(expected));

        var result = userService.getUser("1");

        assertTrue(result.isPresent());
        assertEquals(expected, result.get());
        verify(userRepository).findById("1");
    }

    @Test
    void getUsers_ShouldReturnPagedUsers() {
        var users = List.of(
                new UserResponse("2", "Jane", "jane@example.com", LocalDateTime.now()),
                new UserResponse("1", "John", "john@example.com", LocalDateTime.now()));
        when(userRepository.findAll()).thenReturn(users);

        var result = userService.getUsers(0, 10, "name");

        assertEquals(2, result.size());
        assertEquals("Jane", result.get(0).name());
        assertEquals("John", result.get(1).name());
        verify(userRepository).findAll();
    }

    @Test
    void updateUser_ShouldUpdateAndReturnUserWhenExists() {
        var request = new UserRequest("John Updated", "john.updated@example.com");
        when(userRepository.update("1", request.name(), request.email())).thenReturn(true);

        var result = userService.updateUser("1", request);

        assertEquals("1", result.id());
        assertEquals("John Updated", result.name());
        verify(userRepository).update("1", request.name(), request.email());
    }

    @Test
    void deleteUser_ShouldCallRepositoryWhenUserExists() {
        when(userRepository.deleteById("1")).thenReturn(true);

        userService.deleteUser("1");
        verify(userRepository).deleteById("1");
    }

    @Test
    void deleteUser_ShouldThrow404WhenUserMissing() {
        when(userRepository.deleteById("missing")).thenReturn(false);

        var exception = assertThrows(HttpServerResponseException.class, () -> userService.deleteUser("missing"));

        assertEquals(404, exception.code());
        verify(userRepository).deleteById("missing");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    В Kotlin-версии используется MockK. Поведение мока задается DSL-выражением `every { ... } returns ...`: внутри фигурных скобок описывается вызов зависимости, а после `returns` — ответ для этого
    вызова. Проверка взаимодействия пишется как `verify { userRepository.save(...) }`. Такой синтаксис хорошо ложится на Kotlin: не нужны экранированные вызовы вроде `` `when` ``, а проверяемый вызов
    остается обычным Kotlin-кодом внутри блока.

    Добавьте импорты:

    ```kotlin
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Assertions.assertThrows
    import ru.tinkoff.kora.guide.httpserver.dto.UserRequest
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    ```

    Добавьте тестовые методы:

    ```kotlin
    @Test
    fun createUserShouldCreateAndReturnUser() {
        val request = UserRequest("John", "john@example.com")

        every { userRepository.save("John", "john@example.com") } returns "1"

        val result = userService.createUser(request)

        assertNotNull(result)
        assertEquals("1", result.id())
        assertEquals("John", result.name())
        assertEquals("john@example.com", result.email())
        verify { userRepository.save("John", "john@example.com") }
    }

    @Test
    fun getUserShouldReturnUserWhenExists() {
        val expected = UserResponse("1", "John", "john@example.com", LocalDateTime.now())
        every { userRepository.findById("1") } returns expected

        val result = userService.getUser("1")

        assertEquals(expected, result)
        verify { userRepository.findById("1") }
    }

    @Test
    fun getUsersShouldReturnPagedUsers() {
        val users = listOf(
            UserResponse("2", "Jane", "jane@example.com", LocalDateTime.now()),
            UserResponse("1", "John", "john@example.com", LocalDateTime.now())
        )
        every { userRepository.findAll() } returns users

        val result = userService.getUsers(0, 10, "name")

        assertEquals(2, result.size)
        assertEquals("Jane", result[0].name())
        assertEquals("John", result[1].name())
        verify { userRepository.findAll() }
    }

    @Test
    fun updateUserShouldUpdateAndReturnUserWhenExists() {
        val request = UserRequest("John Updated", "john.updated@example.com")
        every { userRepository.update("1", request.name(), request.email()) } returns true

        val result = userService.updateUser("1", request)

        assertEquals("1", result.id())
        assertEquals("John Updated", result.name())
        verify { userRepository.update("1", request.name(), request.email()) }
    }

    @Test
    fun deleteUserShouldCallRepositoryWhenUserExists() {
        every { userRepository.deleteById("1") } returns true

        userService.deleteUser("1")
        verify { userRepository.deleteById("1") }
    }

    @Test
    fun deleteUserShouldThrow404WhenUserMissing() {
        every { userRepository.deleteById("missing") } returns false

        val exception = assertThrows(HttpServerResponseException::class.java) {
            userService.deleteUser("missing")
        }

        assertEquals(404, exception.code())
        verify { userRepository.deleteById("missing") }
    }
    ```

## Интеграционные тесты { #integration-testing }

Интеграционное тестирование с настоящим PostgreSQL, `TestApplication` и `UserServiceIntegrationPostgresTest` рассматривается в отдельном
руководстве: [Интеграционное тестирование](testing-integration.md).

Это руководство по JUnit сосредоточено на компонентном тестировании с `@KoraAppTest`, `@TestComponent`, `@Mock` для Java и `@MockK` для Kotlin.

## Переопределения конфигурации { #config-overrides }

Полные правила тестовой конфигурации Kora описаны в разделе [настройки конфигурации для тестов](../documentation/junit5.md#test-configuration).

Kora предоставляет мощные возможности переопределения конфигурации для разных тестовых сценариев.

!!! tip "Шаблоны переопределения конфигурации"

    **Распространенные шаблоны переопределения:**

    - отключать внешние службы для компонентных тестов
    - использовать базы данных в памяти для более быстрых тестов
    - переопределять настройки подключения для тестовой инфраструктуры
    - отключать кеширование или фоновые задачи во время тестирования
    - настраивать другие порты или конечные точки

## Запуск тестов { #testing }

Запустите тесты через Gradle:

```bash
# Запустить все тесты
./gradlew test

# Запустить с подробным выводом
./gradlew test --info

# Запустить тесты параллельно
./gradlew test --parallel
```

## Тестовое покрытие { #coverage }

Проекты Kora включают встроенные отчеты о тестах и покрытии:

```bash
# Сформировать отчеты о тестах
./gradlew test

# Сформировать отчеты о покрытии
./gradlew jacocoTestReport

# Открыть HTML-отчет о покрытии
open build/jacocoHtml/index.html
```

## Лучшие практики { #best-practices }

Стратегия тестирования:

1. Отдавайте приоритет тестам по принципу черного ящика: они дают наибольшую уверенность
2. Используйте компонентные тесты для логики: быстрая обратная связь во время разработки
3. Интеграционные тесты для инфраструктуры: проверка взаимодействия с настоящей базой данных
4. Тестирование алгоритмов: сложная бизнес-логика со сфокусированной изоляцией, когда это нужно

Организация тестов:

- Один тестовый класс на промышленный класс: `UserService` → `UserServiceComponentTest`
- Понятные имена тестов: `createUser_ShouldCreateAndReturnUser`
- Структура Given-When-Then: четкие фазы теста
- Строители тестовых данных: единообразное создание тестовых данных

Изоляция тестов:

- Свежая база данных для каждого теста: используйте Testcontainers с жизненным циклом на каждый метод
- Никаких зависимостей между тестами: тесты должны выполняться независимо
- Чистое состояние: сбрасывайте состояние между тестами
- Освобождение ресурсов: корректно освобождайте контейнеры и соединения

Соображения производительности:

- Параллельное выполнение: запускайте тесты параллельно, когда это возможно
- Общие контейнеры: используйте совместное использование контейнеров для более быстрого запуска
- Выборочное тестирование: запускайте только нужные тесты во время разработки
- Быстрая обратная связь: компонентные тесты для быстрой проверки

## Итоги { #summary }

Вы изучили полноценные стратегии тестирования приложений Kora:

- Компонентные тесты: проверка взаимодействий компонентов с помощью DI-фреймворка Kora
- Интеграционные тесты: проверка с настоящими базами данных через Testcontainers
- Тесты по принципу черного ящика: проверка поведения полноценного приложения через HTTP API

Каждый уровень тестирования дает разную уверенность и помогает находить разные виды ошибок. Начинайте с компонентных тестов для быстрой обратной связи, добавляйте интеграционные тесты для проверки
инфраструктуры и полагайтесь на тесты по принципу черного ящика для уверенности на всем пути выполнения.

Тестовый фреймворк использует внедрение зависимостей Kora для удобных подмен и настройки, Testcontainers для реалистичного тестирования инфраструктуры и стандартные шаблоны JUnit 5 для привычной
структуры тестов.

## Ключевые понятия { #key-concepts }

Обзор стратегии тестирования:

- Компонентные тесты: быстрое изолированное тестирование отдельных компонентов с использованием внедрения зависимостей Kora
- Интеграционные тесты: реалистичное тестирование с настоящей инфраструктурой через Testcontainers
- Тесты по принципу черного ящика: сквозное тестирование поведения полноценного приложения

Тестовый фреймворк Kora:

- @KoraAppTest: аннотация, которая запускает внедрение зависимостей Kora для тестирования
- Шаблон TestApplication: пользовательский класс приложения для тестовой конфигурации
- Переопределения конфигурации: переменные окружения и системные свойства для тестовой конфигурации

Интеграция Testcontainers:

- Настоящая инфраструктура: PostgreSQL, Redis и другие службы в Docker-контейнерах
- Автоматический жизненный цикл: контейнеры автоматически запускаются и останавливаются вместе с выполнением тестов
- Настройка сети: автоматическое внедрение строки подключения

Лучшие практики:

- Изоляция тестов: каждый тест выполняется в полной изоляции со свежими контейнерами
- Быстрая обратная связь: компонентные тесты для быстрой проверки во время разработки
- Освобождение ресурсов: автоматическая очистка контейнеров и соединений
- Параллельное выполнение: тесты могут выполняться параллельно для ускорения

## Устранение неполадок { #troubleshooting }

**Testcontainers не запускается:**

- Убедитесь, что Docker запущен и доступен
- Проверьте, что зависимости Testcontainers подключены
- Убедитесь, что имена Docker-образов указаны правильно и образы доступны

**@KoraAppTest не работает:**

- Убедитесь, что обработчик аннотаций настроен в build.gradle
- Проверьте, что интерфейс Application включает TestModule
- Убедитесь, что тестовый класс правильно помечен @KoraAppTest

**Проблемы с подключением к базе данных:**

- Убедитесь, что контейнер PostgreSQL запущен до выполнения теста
- Проверьте конфигурацию подключения к базе данных в тестовых свойствах
- Убедитесь, что схема базы данных соответствует определениям сущностей

**Переопределения конфигурации не применяются:**

- Убедитесь, что переменные окружения заданы до выполнения тестов
- Проверьте, что системные свойства передаются в JVM тестов
- Убедитесь, что имена свойств конфигурации соответствуют ожиданиям приложения

**Проблемы выполнения тестов:**

- Проверьте журналы тестов: в них есть подробные сообщения об ошибках
- Убедитесь, что все зависимости правильно внедрены
- Проверьте изоляцию тестов: между тестами не должно быть общего состояния

## Что дальше? { #whats-next }

- [База данных JDBC](database-jdbc.md), если хотите перейти к тестам, которым нужны PostgreSQL, Flyway и миграции репозиториев.
- [Интеграционное тестирование](testing-integration.md) после базы данных JDBC, чтобы тестировать репозитории, миграции и внешние зависимости через Testcontainers.
- [Тестирование как черный ящик](testing-black-box.md) после базы данных JDBC, чтобы проверять упакованное HTTP-приложение от начала до конца.
- [Наблюдаемость](observability.md), чтобы добавить метрики, трассировки, журналы и пробы, которые тоже можно проверять в тестах.
- [Шаблоны устойчивости](resilient.md), чтобы потренироваться тестировать сбои и резервное поведение.

## Помощь { #help }

Если возникли проблемы:

- сравните с тестовыми классами в соответствующем модуле `guides/*`
- проверьте [документацию JUnit5](../documentation/junit5.md)
- вернитесь к [HTTP-серверу](http-server.md), чтобы свериться с базовой формой графа
- прочитайте [документацию Testcontainers](https://www.testcontainers.org/) по проблемам жизненного цикла контейнеров
