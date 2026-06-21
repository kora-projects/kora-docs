---
description: "Explains Kora JUnit 5 testing support, application graph tests, component replacement, mocks, tags, test configuration, and initialization. Use when working with @KoraAppTest, @TestComponent, @MockComponent, @Tag, @TestConfig, @TestConfigSource, Graph, Mockito."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JUnit 5 testing support, application graph tests, component replacement, mocks, tags, test configuration, and initialization; key triggers include @KoraAppTest, @TestComponent, @MockComponent, @Tag, @TestConfig, @TestConfigSource, Graph, Mockito."
---

Модуль предоставляет расширение для [JUnit 5](https://junit.org/junit5/docs/current/user-guide/), которое позволяет тестировать приложение через тот же граф компонентов, что используется во время работы приложения.

Расширение Kora для `JUnit 5` предназначено для компонентного и интеграционного тестирования исходного кода,
который затем будет использоваться в реальном приложении.
В тесте участвует контейнер зависимостей основного приложения: его можно ограничить только нужными компонентами,
расширить тестовыми компонентами или заменить отдельные части заглушками.

Модуль позволяет проводить:

- `Компонентное тестирование` - тестирование одного компонента.
- `Межкомпонентное тестирование` - тестирование нескольких компонентов и их взаимодействия друг с другом.
- `Интеграционное тестирование` - тестирование компонентов и взаимодействия с внешними системами.

Настоятельно советуем дополнительно проводить интеграционное тестирование запакованного в финальный образ артефакта сервиса,
как черного ящика с помощью [библиотеки Testcontainers](https://java.testcontainers.org/).

Если нужен пошаговый разбор перед справочным описанием, смотрите [Компонентное тестирование](../guides/testing-junit.md), [Интеграционное тестирование](../guides/testing-integration.md) и [Тестирование как черный ящик](../guides/testing-black-box.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    testImplementation "ru.tinkoff.kora:test-junit5"
    ```

    Настроить [JUnit платформу](https://docs.gradle.org/current/userguide/java_testing.html#using_junit5) `build.gradle`:
    ```groovy
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

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    testImplementation("ru.tinkoff.kora:test-junit5")
    ```

    Настроить [JUnit платформу](https://docs.gradle.org/current/userguide/java_testing.html#using_junit5) `build.gradle.kts`:
    ```groovy
    tasks.test {
        useJUnitPlatform()
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = TestExceptionFormat.FULL
        }
    }
    ```

## Использование { #usage }

Примеры будут показаны относительно такого приложения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        @Root
        default Supplier<String> supplier() {
            return () -> "1";
        }

        @Root
        @Tag(Supplier.class)
        default Supplier<String> supplierTagged() {
            return () -> "tag1";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        @Root
        fun supplier(): Supplier<String> {
            return Supplier<String> { "1" }
        }

        @Root
        fun supplierTagged(): @Tag(Supplier::class) Supplier<String> {
            return Supplier<String> { "tag1" }
        }
    }
    ```

### Тест { #test }

Для включения расширения Kora нужно аннотировать тестовый класс аннотацией `@KoraAppTest`.
Аннотация подключает расширение `JUnit 5`, находит сгенерированный граф указанного `@KoraApp` приложения и подготавливает контейнер зависимостей для теста.

Параметры аннотации `@KoraAppTest`:

- `value` - класс, аннотированный `@KoraApp`, чей граф компонентов будет использоваться в тесте (`обязательная`, по умолчанию не указано).
- `components` - дополнительные классы компонентов, которые нужно включить в тестовый граф помимо компонентов, найденных через `@TestComponent` (по умолчанию: `{}`).
- `modules` - дополнительные модули с методами-фабриками компонентов, которые нужно подключить к тестовому графу (по умолчанию: `{}`).

В `modules` можно указывать только интерфейсы модулей. Если нужно протестировать весь граф, достаточно внедрить `KoraAppGraph` или не ограничивать граф только отдельными `@TestComponent` компонентами.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class,
                 components = { SomeComponent.class },
                 modules = { SomeModule.class })
    class SomeTests {

    }
    ```
=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class,
                 components = [SomeComponent::class],
                 modules = [SomeModule::class])
    class SomeTests {

    }
    ```

### Компонент { #component }

Для внедрения и указания компонентов для тестирования используется аннотация `@TestComponent`,
которая позволяет внедрять компоненты в аргументы метода, конструктор и/или поля тестового класса и ограничивать ими контейнер зависимостей теста.

Все компоненты, перечисленные в тестовых полях и/или аргументах метода/конструктора с аннотацией `@TestComponent`,
будут внедрены как зависимости в рамках теста. Тестовый контейнер будет ограничен этими компонентами и их зависимостями.

Важно, что компоненты в рамках теста должны использоваться хотя бы одним [@Root компонентом](container.md#root-component), который также указан в рамках теста.

Пример теста, где компоненты внедряются в поля:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @TestComponent
        private Supplier<String> component1;

        @Test
        void example() {
            assertEquals("1", component1.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @TestComponent
        lateinit var component1: Supplier<String>

        @Test
        fun example() {
            assertEquals("1", component1.get())
        }
    }
    ```

Пример теста, где компоненты внедряются в конструктор:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        private final Supplier<String> component1;

        SomeTests(@TestComponent Supplier<String> component1) {
            this.component1 = component1;
        }

        @Test
        void example() {
            assertEquals("1", component1.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests(@TestComponent val component1: Supplier<String>) {

        @Test
        fun example() {
            assertEquals("1", component1.get())
        }
    }
    ```

Пример теста, где компоненты внедряются в аргументы метода:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Test
        void example(@TestComponent Supplier<String> component1) {
            assertEquals("1", component1.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @Test
        fun example(@TestComponent component1: Supplier<String>) {
            assertEquals("1", component1.get())
        }
    }
    ```

#### Правила внедрения { #injection-rules }

Компоненты можно внедрять тремя способами: в поле тестового класса, в конструктор или в параметр тестового метода.
Выбор способа влияет на то, когда расширение Kora может получить экземпляр тестового класса и какие дополнительные механизмы доступны.

- Поля подходят для большинства тестов и совместимы с `KoraAppTestConfigModifier`, `KoraAppTestGraphModifier`, `PER_METHOD` и `PER_CLASS`.
- Конструктор удобен для неизменяемых полей, но несовместим с `KoraAppTestConfigModifier` и `KoraAppTestGraphModifier`, потому что расширению нужен экземпляр тестового класса, чтобы вызвать `config()` или `graph()`, а при конструкторном внедрении этот экземпляр еще создается.
- Параметры метода удобны для локальных зависимостей конкретного теста; при `PER_METHOD` в граф включаются параметры текущего метода, а при `PER_CLASS` расширение заранее собирает `@TestComponent` параметры всех методов класса.
- Если в тесте используется конструкторное внедрение, нельзя дополнительно внедрять `@TestComponent`, `@Mock`, `@Spy`, `@MockK` или `@SpyK` в параметры тестовых методов.
- В режиме `PER_CLASS` нельзя внедрять `@Mock` / `@MockK` в параметры тестовых методов, потому что заглушки метода живут меньше, чем общий граф тестового класса.
- Один и тот же элемент нельзя одновременно объявлять обычным `@TestComponent`, заглушкой и шпионом: расширение завершит тест ошибкой конфигурации.

Если тесту нужны `KoraAppTestConfigModifier` или `KoraAppTestGraphModifier`, используйте внедрение в поля или параметры методов.
Если нужен конструктор, всю конфигурацию и модификацию графа лучше вынести в отдельный тестовый `@KoraApp` или подключаемый модуль.

### Тег { #tag }

Для внедрения зависимости которая имеет `@Tag`, требуется указать соответствующую аннотацию `@Tag` рядом с внедряемым аргументом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Test
        void example(@Tag(Supplier.class) @TestComponent Supplier<String> component1) {
            assertEquals("?", component1.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @Test
        fun example(@Tag(Supplier::class) @TestComponent component1: Supplier<String>) {
            assertEquals("?", component1.get())
        }
    }
    ```

### Граф приложения { #application-graph }

Если тесту нужен прямой доступ к подготовленному графу, можно внедрить `KoraAppGraph` в поле, конструктор или аргумент тестового метода.
Через него можно получить один или несколько компонентов по типу, а также учитывать `@Tag`.

Основные методы `KoraAppGraph`:

- `getFirst(Type type)` / `getFirst(Class<T> type)` - возвращают первый найденный компонент или `null`.
- `getFirst(Type type, Class<?>... tags)` / `getFirst(Class<T> type, Class<?>... tags)` - возвращают первый компонент с указанными тегами или `null`.
- `findFirst(...)` - возвращает `Optional<T>` вместо `null`.
- `getAll(...)` - возвращает все компоненты указанного типа, при необходимости с учетом тегов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Test
        void example(KoraAppGraph graph) {
            var component = graph.getFirst(Supplier.class, Supplier.class);

            assertNotNull(component);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @Test
        fun example(graph: KoraAppGraph) {
            val component = graph.getFirst(Supplier::class.java, Supplier::class.java)

            assertNotNull(component)
        }
    }
    ```

`KoraAppGraph` нельзя использовать как цель для `@Mock`, `@Spy`, `@MockK` или `@SpyK`, потому что это служебный объект тестового расширения, а не компонент приложения.

### Заглушки { #mock }

===! ":fontawesome-brands-java: `Java`"

    Для создание заглушек компонент в Java в рамках теста предлагается использовать аннотации предоставляемые библиотекой [Mockito](https://site.mockito.org/) в совокупности с аннотацией `@TestComponent`.

    Требуется подключить библиотеку [Mockito](https://site.mockito.org/) как зависимость `build.gradle`:
    ```groovy
    testImplementation "org.mockito:mockito-core:5.18.0"
    ```

    **Важно**, подразумевается что `MockitoExtension` не будет использоваться и будет отключен, нельзя совмещать его работу совместно с `@KoraAppTest`.

    Поддерживаются аннотации [@Mock](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mock.html) и [@Spy](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Spy.html), а также все параметры этих аннотаций.
    Рекомендуется подробнее ознакомиться с работой этих аннотацией в [официальной документации библиотеки Mockito](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html).

    Аннотация [@Mock](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mock.html) позволяет сделать класс заглушку
    проаннотированного компонента и контролировать поведение его методов с помощью `Mockito` либо методы будут возвращать значения по-умолчанию: `void`, значения по умолчанию для примитивов, пустые коллекции и `null` для всех остальных объектов.

    Компонент заглушка будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты которые требовали его как зависимость.
    Все зависимые компоненты, которые больше нигде не требуются в рамках теста, будут исключены за ненадобностью.

    Пример теста с использованием `@Mock` компонента и внедрением заглушки в поле:

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Mock
        @TestComponent
        private Supplier<String> component1;

        @BeforeEach
        void mock() {
            Mockito.when(component1.get()).thenReturn("?");
        }

        @Test
        void example() {
            assertEquals("?", component1.get());
        }
    }
    ```

    Аннотация [@Spy](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Spy.html) позволяет сделать шпион фасад реализации класса
    компонента из контейнера зависимостей который по умолчанию будет иметь оригинальное поведение методов компонента,
    но как и в случае с заглушками, их поведение можно переопределить.

    Компонент шпион будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты которые требовали его как зависимость.

    Пример теста с использованием `@Spy` компонента и внедрением шпиона в аргумент метода:

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Test
        void example(@Spy @TestComponent Supplier<String> component1) {
            Mockito.when(component1.get()).thenReturn("?");
            assertEquals("?", component1.get());
        }
    }
    ```

    Можно также сделать шпиона из значения поля тестового класса.

    Компонент шпион будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты которые требовали его как зависимость.
    Все зависимые компоненты, которые больше нигде не требуются в рамках теста, будут исключены за ненадобностью.

    Пример теста с использованием `@Spy` компонента шпиона:

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Spy
        @TestComponent
        private Supplier<String> component1 = () -> "12345";

        @Test
        void example() {
            assertEquals("12345", component1.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Для создание заглушек компонент в Kotlin в рамках теста предлагается использовать аннотации предоставляемые библиотекой [MockK](https://mockk.io/) в совокупности с аннотацией `@TestComponent`.

    Требуется подключить библиотеку [MockK](https://mockk.io/) как зависимость `build.gradle.kts`:
    ```groovy
    testImplementation("io.mockk:mockk:1.13.11")
    ```

    **Важно**, подразумевается что `MockkExtension` не будет использоваться и будет отключен, нельзя совмещать его работу совместно с `@KoraAppTest`.

    Поддерживаются аннотации [@MockK](https://mockk.io/#annotations) и [@SpyK](https://mockk.io/#annotations), а также все параметры этих аннотаций.

    Также есть возможность при желании использовать [Mockito](https://site.mockito.org/).
    Для более подробного описания работы Kora и [Mockito](https://site.mockito.org/) следует ознакомиться с Java-вкладкой этого абзаца.
    Чтобы улучшить взаимодействие Mockito и Kotlin можно использовать библиотеку [Mockito Kotlin](https://github.com/mockito/mockito-kotlin).
    ```groovy
    testImplementation("org.mockito.kotlin:mockito-kotlin:5.4.0")
    ```

    **Важно**, подразумевается что `MockitoExtension` не будет использоваться и будет отключен, нельзя совмещать его работу совместно с `@KoraAppTest`.

    Аннотация [@MockK](https://mockk.io/#annotations) позволяет сделать класс заглушку
    проаннотированного компонента и контролировать поведение его методов с помощью `MockK`.

    Компонент заглушка будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты которые требовали его как зависимость.
    Все зависимые компоненты, которые больше нигде не требуются в рамках теста, будут исключены за ненадобностью.

    Пример теста с использованием `@MockK` компонента и внедрением заглушки в поле:

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests(@MockK @TestComponent val component1: Supplier<String>) {

        @BeforeEach
        fun mock() {
            every { component1.get() } returns "?"
        }

        @Test
        fun example() {
            assertEquals("?", component1.get())
        }
    }
    ```

    Аннотация [@SpyK](https://mockk.io/#annotations) позволяет сделать шпион фасад реализации класса
    компонента из контейнера зависимостей который по умолчанию будет иметь оригинальное поведение методов компонента,
    но как и в случае с заглушками, их поведение можно переопределить.

    Компонент шпион будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты которые требовали его как зависимость.

    Пример теста с использованием `@SpyK` компонента и внедрением шпиона в аргумент метода:

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @Test
        fun example(@SpyK @TestComponent component1: Supplier<String>) {
            every { component1.get() } returns "?"
            assertEquals("?", component1.get())
        }
    }
    ```

    Можно также сделать шпиона из значения поля тестового класса.

    Компонент шпион будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты которые требовали его как зависимость.
    Все зависимые компоненты, которые больше нигде не требуются в рамках теста, будут исключены за ненадобностью.

    Пример теста с использованием `@SpyK` компонента шпиона:

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @field:SpyK
        @TestComponent
        val component1: Supplier<String> = Supplier { "1" }

        @Test
        fun example() {
            assertEquals("?", component1.get())
        }
    }
    ```

#### Проверка заглушек { #mock-strictness }

Использование заглушек `Mockito` можно проверять через аннотацию `@MockitoStrictness`.
Она задает уровень проверки для заглушек `Mockito`, созданных расширением Kora в рамках тестового класса.

Расширение ведет себя похоже на `MockitoSession`: после выполнения теста оно передает созданные заглушки в проверку `Mockito` и сообщает о неиспользованных или подозрительных настройках.
Если `@MockitoStrictness` не указана, Kora использует `Strictness.WARN`: тест не падает, но предупреждения пишутся в лог.

Поддержанные уровни:

- `Strictness.WARN` - значение по умолчанию; пишет предупреждения в лог и не завершает тест ошибкой.
- `Strictness.STRICT_STUBS` - строгий режим; неиспользованные настройки заглушек приводят к ошибке, например `UnnecessaryStubbingException`.
- `Strictness.LENIENT` - мягкий режим; отключает проверку неиспользованных настроек заглушек.

Если у конкретного `@Mock` указан собственный параметр `strictness`, он применяется к настройкам этой заглушки.
`@MockitoStrictness` удобна как общий уровень для всего тестового класса, чтобы не дублировать настройку на каждой заглушке.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @MockitoStrictness(Strictness.STRICT_STUBS)
    @KoraAppTest(Application.class)
    class SomeTests {

        @Mock
        @TestComponent
        private Supplier<String> component1;

        @BeforeEach
        void mock() {
            Mockito.when(component1.get()).thenReturn("?");
        }

        @Test
        void example() {
            // component1.get() usage required
        }
    }
    ```

В примере выше вызов `Mockito.when(component1.get()).thenReturn("?")` должен быть использован тестом.
Если убрать вызов `component1.get()` из тестового метода, в режиме `Strictness.STRICT_STUBS` проверка завершит тест ошибкой.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @MockitoStrictness(Strictness.STRICT_STUBS)
    @KoraAppTest(Application::class)
    class SomeTests(@Mock @TestComponent val component1: Supplier<String>) {

        @BeforeEach
        fun mock() {
            on { component1.get() } doReturn "?"
        }

        @Test
        fun example() {
            // component1.get() usage required
        }
    }
    ```

Для Kotlin при использовании `Mockito Kotlin` действует тот же механизм, потому что проверку выполняет `Mockito`.
Для заглушек `MockK` аннотация `@MockitoStrictness` не применяется.

### Расширенный контейнер { #test-graph }

Иногда может потребоваться использовать расширенный контейнер зависимостей в рамках тестов.
Например, тестовое приложение может расширять основное приложение и добавлять компоненты,
которые нужны только в тестах.

Такой подход полезен, когда у вас есть разные приложения чтения и записи с общими компонентами,
которые могут потребоваться в рамках тестирования одного и другого.
Либо, вам нужны некоторые функции сохранения/удаления/обновления только для тестирования в
качестве быстрой тестовой утилиты.

???+ warning "Рекомендация"

    **Настоятельно Рекомендуем Тестировать** приложения как [черный ящик](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/BlackBoxTests.java)
    и полагаться на этот подход в качестве основного источника правды и работоспособности приложения.

    Приложение может работать по разному в зависимости от флагов JVM,
    базового образа и нативных библиотек, отличий частичной конфигурации от полной,
    отличий конвертации на точках входа в приложение, использования реестров схем и так далее.
    Только готовый образ может гарантировать максимально приближенную среду для тестирования.

Представим что приложение выглядит так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        @Root
        default String someComponent() {
            return "1";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        @Root
        fun someComponent(): String {
            return "1"
        }
    }
    ```

В тестах можно создать отдельный тестовый `@KoraApp`, который наследуется от основного приложения, и использовать уже его.
Для такого сценария нужен сгенерированный подмодуль основного приложения: без него тестовое приложение не сможет унаследовать и подключить компоненты основного графа.

===! ":fontawesome-brands-java: `Java`"

    Для этого в первую очередь понадобится включить параметр
    для создания подмодуля основного приложения в `build.gradle`:

    ```groovy
    compileJava {
        options.compilerArgs += [
            "-Akora.app.submodule.enabled=true"
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Для этого в первую очередь понадобится включить параметр
    для создания подмодуля основного приложения в `build.gradle.kts`:

    ```groovy
    ksp {
        arg("kora.app.submodule.enabled", "true")
    }
    ```

Затем требуется создать расширенный тестовый граф приложения в директории для тестовых классов.
Не забывайте помечать компоненты как `@Root`, так как они, скорее всего, не используются никем кроме тестов
и не будут иначе включены в граф:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface TestApplication extends Application {

        @Root
        default Integer someOtherComponent() {
            return 1;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface TestApplication : Application {

        @Root
        fun someOtherComponent(): Integer {
            return 1
        }
    }
    ```

===! ":fontawesome-brands-java: `Java`"

    Чтобы граф тестового приложения создался, надо подключить процессоры как тестовые зависимости в `build.gradle`:

    ```groovy
    dependencies {
        testAnnotationProcessor "ru.tinkoff.kora:annotation-processors"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Чтобы граф тестового приложения создался, надо подключить процессоры как тестовые зависимости в `build.gradle.kts`:

    ```groovy
    dependencies {
        kspTest("ru.tinkoff.kora:symbol-processors")
    }
    ```

Возможно, потребуется исключить сканирование созданных Kora классов со стороны JUnit (иногда у JUnit может возникать ошибка при поиске тестов):

===! ":fontawesome-brands-java: `Java`"

    Классы начинаются с символа `$`, надо исключить в `build.gradle`:

    ```java
    test {
        exclude("**/\$*")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Классы начинаются с символа `$`, надо исключить в `build.gradle.kts`:

    ```kotlin
    tasks.test {
        exclude("**/\$*")
    }
    ```

Теперь можно использовать расширенный тестовый граф приложения в тестах:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(TestApplication.class)
    class SomeTests {

        @TestComponent
        private String component1;
        @TestComponent
        private Integer component2;

        @Test
        void testSame() {
            assertEquals(component1, String.valueOf(component2));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(TestApplication::class)
    class SomeTests(val component1: String, val component2: Integer) {

        @Test
        fun testSame() {
            assertEquals(component1, component2.toString());
        }
    }
    ```

Если не нужно наследоваться от основного `@KoraApp`, а требуется только добавить методы-фабрики из отдельного модуля,
можно использовать параметр `modules` у `@KoraAppTest`.
В `modules` указываются интерфейсы модулей, а не классы компонентов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface TestModule {

        @Root
        default Integer testOnlyComponent() {
            return 1;
        }
    }

    @KoraAppTest(value = Application.class, modules = TestModule.class)
    class SomeTests {

        @Test
        void test(@TestComponent Integer component) {
            assertEquals(1, component);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface TestModule {

        @Root
        fun testOnlyComponent(): Int {
            return 1
        }
    }

    @KoraAppTest(value = Application::class, modules = [TestModule::class])
    class SomeTests {

        @Test
        fun test(@TestComponent component: Int) {
            assertEquals(1, component)
        }
    }
    ```

Итого:

- `kora.app.submodule.enabled=true` нужен, когда тестовый `@KoraApp` наследуется от основного `@KoraApp`.
- `@KoraAppTest(modules = ...)` подходит, когда нужно просто подключить дополнительные модули к тестовому графу.
- Компоненты, которые должны попасть в ограниченный тестовый граф, по-прежнему должны быть достижимы от `@TestComponent`, `components` или `KoraAppGraph`.

## Настройка конфигурации { #test-configuration }

По умолчанию будет использоваться основная конфигурация, как и в случае запуска реального приложения.

Для изменения или добавления конфигурации в рамках тестов тестовый класс должен реализовать интерфейс `KoraAppTestConfigModifier`,
а метод `config()` должен вернуть модификацию конфигурации `KoraConfigModification`.

`KoraAppTestConfigModifier` нельзя использовать вместе с внедрением компонентов в конструктор тестового класса:
расширению нужно получить модификацию конфигурации до создания тестового графа, а для этого сначала должен быть создан экземпляр теста.

### Переменные окружения { #environment-variables }

В случае если в рамках теста надо использовать [конфигурацию по умолчанию](config.md#file) которая использовалась бы во время работы приложения,
и требуется лишь подставить переменные окружения то можно использовать механизм `SystemProperty` в `KoraConfigModification`:

===! ":material-code-json: `Hocon`"

    Предположим есть такая конфигурация `application.conf`:

    ```javascript
    db {
        jdbcUrl = ${POSTGRES_JDBC_URL}
        username = ${POSTGRES_USER}
        password = ${POSTGRES_PASS}
        maxPoolSize = 10
        poolName = "example"
    }
    ```

=== ":simple-yaml: `YAML`"

    Предположим есть такая конфигурация `application.yaml`:

    ```yaml
    db:
      jdbcUrl: ${POSTGRES_JDBC_URL}
      username: ${POSTGRES_USER}
      password: ${POSTGRES_PASS}
      maxPoolSize: 10
      poolName: "example"
    ```

Тогда, чтобы использовать такой конфиг и передать в него лишь переменные окружения требуется вернуть такой `KoraConfigModification`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests implements KoraAppTestConfigModifier {

        @NotNull
        @Override
        public KoraConfigModification config() {
            return KoraConfigModification
                .ofSystemProperty("POSTGRES_JDBC_URL", "jdbc:postgresql://localhost:5432/postgres")
                .withSystemProperty("POSTGRES_USER", "postgres")
                .withSystemProperty("POSTGRES_PASS", "postgres");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests : KoraAppTestConfigModifier {

        override fun config(): KoraConfigModification {
            return KoraConfigModification
                .ofSystemProperty("POSTGRES_JDBC_URL", "jdbc:postgresql://localhost:5432/postgres")
                .withSystemProperty("POSTGRES_USER", "postgres")
                .withSystemProperty("POSTGRES_PASS", "postgres")
        }
    }
    ```

Если нужно передать сразу несколько значений, можно использовать `withSystemProperties(Map<String, String>)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests implements KoraAppTestConfigModifier {

        @NotNull
        @Override
        public KoraConfigModification config() {
            return KoraConfigModification
                .ofSystemProperty("POSTGRES_JDBC_URL", "jdbc:postgresql://localhost:5432/postgres")
                .withSystemProperties(Map.of(
                    "POSTGRES_USER", "postgres",
                    "POSTGRES_PASS", "postgres"
                ));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests : KoraAppTestConfigModifier {

        override fun config(): KoraConfigModification {
            return KoraConfigModification
                .ofSystemProperty("POSTGRES_JDBC_URL", "jdbc:postgresql://localhost:5432/postgres")
                .withSystemProperties(
                    mapOf(
                        "POSTGRES_USER" to "postgres",
                        "POSTGRES_PASS" to "postgres"
                    )
                )
        }
    }
    ```

### Файл конфигурации { #configuration-file }

Пример добавления конфигурации в виде файла:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests implements KoraAppTestConfigModifier {

        @Override
        public @Nonnull KoraConfigModification config() {
            return KoraConfigModification.ofResourceFile("application-test.conf");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests : KoraAppTestConfigModifier {

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofResourceFile("application-test.conf")
        }
    }
    ```

### Текст конфигурации { #configuration-text }

Пример добавления конфигурации в виде строки будет выглядеть так,
в таком случае будет использоваться только эта конфигурация без каких либо файлов конфигурации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests implements KoraAppTestConfigModifier {

        @Override
        public @Nonnull KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                myconfig {
                    myproperty = 1
                }
                """);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests : KoraAppTestConfigModifier {

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofString(
                """
                myconfig {
                    myproperty = 1
                }
                """.trimIndent()
            )
        }
    }
    ```

## Модификация контейнера { #container-modification }

Для добавления, замены или программного создания заглушек в контейнере приложения без аннотаций нужно реализовать интерфейс `KoraAppTestGraphModifier`
и вернуть из метода `graph()` модификацию `KoraGraphModification`.

`KoraAppTestGraphModifier` нельзя использовать вместе с внедрением компонентов в конструктор тестового класса:
расширению нужно получить модификацию графа до создания графа и внедрения компонентов.

`KoraGraphModification` поддерживает такие операции:

- `addComponent(...)` - добавляет новый компонент в тестовый граф.
- `replaceComponent(...)` - заменяет существующий компонент, при этом его зависимости остаются в графе.
- `mockComponent(...)` - заменяет существующий компонент заглушкой и удаляет из графа реальные зависимости замененного компонента, если они больше не нужны тесту.

Для `addComponent(...)` и `replaceComponent(...)` доступны перегрузки с `Function<KoraAppGraph, T>`, если новый компонент нужно собрать на основе уже инициализированных компонентов графа.
Для компонентов с `@Tag` используются перегрузки с `List<Class<?>> tags`.

### Добавление { #adding }

Пример добавления компонента в граф:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class)
    class SomeTests implements KoraAppTestGraphModifier {

        @Override
        public @Nonnull KoraGraphModification graph() {
            return KoraGraphModification.create()
                .addComponent(TypeRef.of(Supplier.class, Integer.class), () -> (Supplier<Integer>) () -> 1);
        }

        @Test
        void example(@TestComponent Supplier<Integer> supplier) {
            assertEquals(1, supplier.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class)
    class SomeTests : KoraAppTestGraphModifier {

        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .addComponent(TypeRef.of(Supplier::class.java, Int::class.java), Supplier { Supplier { 1 } })
        }

        @Test
        fun example(@TestComponent supplier: Supplier<Int>) {
            assertEquals(1, supplier.get())
        }
    }
    ```

В случае если требуется добавлять компоненты с использованием компонент из контейнера зависимостей, то это также доступно через другую сигнатуру метода:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class)
    class SomeTests implements KoraAppTestGraphModifier {

        @Override
        public @Nonnull KoraGraphModification graph() {
            return KoraGraphModification.create()
                    .addComponent(TypeRef.of(Supplier.class, String.class),
                            (graph) -> {
                                final Supplier<Integer> existingComponent = (Supplier<Integer>) graph.getFirst(TypeRef.of(Supplier.class, Integer.class));
                                return (Supplier<String>) () -> "1" + existingComponent.get();
                            });
        }

        @Test
        void example(@TestComponent Supplier<String> supplier) {
            assertEquals(1, supplier.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class)
    class SomeTests : KoraAppTestGraphModifier {

        @Nonnull
        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .addComponent(TypeRef.of(Supplier::class.java, String::class.java))
                { graph ->
                    val existingComponent = graph.getFirst(TypeRef.of(Supplier::class.java, Int::class.java))
                            as Supplier<Int>
                    Supplier { "1" + existingComponent.get() }
                }
        }

        @Test
        fun example(@TestComponent supplier: Supplier<String>) {
            assertEquals(1, supplier.get())
        }
    }
    ```

### Замена { #replacement }

Пример замены компонента в контейнере, этот механизм также можно использовать для создания собственных заглушек:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class)
    class SomeTests implements KoraAppTestGraphModifier {

        @Override
        public @Nonnull KoraGraphModification graph() {
            return KoraGraphModification.create()
                .replaceComponent(TypeRef.of(Supplier.class, String.class), List.of(Supplier.class), () -> (Supplier<String>) () -> "?");
        }

        @Test
        void example(@Tag(Supplier.class) @TestComponent Supplier<String> supplier) {
            assertEquals("?", supplier.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class)
    class SomeTests : KoraAppTestGraphModifier {

        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .replaceComponent(TypeRef.of(Supplier::class.java, String::class.java), listOf(Supplier::class.java), Supplier { Supplier { "?" } })
        }

        @Test
        fun example(@Tag(Supplier::class) @TestComponent supplier: Supplier<String>) {
            assertEquals("?", supplier.get())
        }
    }
    ```

В случае если требуется добавлять компоненты с использованием компонент из контейнера зависимостей, то это также доступно через другую сигнатуру метода:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class)
    class SomeTests implements KoraAppTestGraphModifier {

        @Override
        public @Nonnull KoraGraphModification graph() {
            return KoraGraphModification.create()
                    .replaceComponent(TypeRef.of(Supplier.class, Integer.class),
                            (graph) -> {
                                final Supplier<Integer> existingComponent = (Supplier<Integer>) graph.getFirst(TypeRef.of(Supplier.class, Integer.class));
                                return (Supplier<Integer>) () -> 1 + existingComponent.get();
                            });
        }

        @Test
        void example(@TestComponent Supplier<Integer> supplier) {
            assertEquals(1, supplier.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class)
    class SomeTests : KoraAppTestGraphModifier {

        @Nonnull
        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .replaceComponent(TypeRef.of(Supplier::class.java, Int::class.java))
                { graph ->
                    val existingComponent = graph.getFirst(TypeRef.of(Supplier::class.java, Int::class.java))
                            as Supplier<Int>
                    Supplier { 1 + existingComponent.get() }
                }
        }

        @Test
        fun example(@TestComponent supplier: Supplier<Int>) {
            assertEquals(1, supplier.get())
        }
    }
    ```

### Программная заглушка { #programmatic-mock }

Если нужно заменить компонент именно как заглушку, используйте `mockComponent(...)`.
В отличие от `replaceComponent(...)`, этот метод сообщает расширению, что реальные зависимости заменяемого компонента не нужны и могут быть исключены из тестового графа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class)
    class SomeTests implements KoraAppTestGraphModifier {

        @Override
        public @Nonnull KoraGraphModification graph() {
            return KoraGraphModification.create()
                .mockComponent(TypeRef.of(Supplier.class, String.class), () -> Mockito.mock(Supplier.class));
        }

        @Test
        void example(@TestComponent Supplier<String> supplier) {
            Mockito.when(supplier.get()).thenReturn("?");

            assertEquals("?", supplier.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class)
    class SomeTests : KoraAppTestGraphModifier {

        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .mockComponent(TypeRef.of(Supplier::class.java, String::class.java), Supplier { mockk<Supplier<String>>() })
        }

        @Test
        fun example(@TestComponent supplier: Supplier<String>) {
            every { supplier.get() } returns "?"

            assertEquals("?", supplier.get())
        }
    }
    ```

## Инициализация { #initialization }

По умолчанию `JUnit 5` использует `TestInstance.Lifecycle.PER_METHOD`, поэтому Kora создает и очищает тестовый граф для каждого тестового метода.
Если требуется инициализировать контейнер один раз в рамках всего тестового класса, следует проаннотировать тестовый класс с помощью `@TestInstance(TestInstance.Lifecycle.PER_CLASS)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @TestInstance(TestInstance.Lifecycle.PER_CLASS)
    @KoraAppTest(Application.class)
    class SomeTests {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @TestInstance(TestInstance.Lifecycle.PER_CLASS)
    @KoraAppTest(Application::class)
    class SomeTests {

    }
    ```

При `PER_CLASS` один экземпляр графа используется всеми тестовыми методами класса, а очистка выполняется после завершения всего класса.
Это ускоряет тяжелые интеграционные тесты, но требует внимательнее относиться к изменяемому состоянию компонентов и заглушек.

Ограничения жизненного цикла:

- При внедрении компонентов в конструктор нельзя одновременно внедрять `@TestComponent` или заглушки в параметры тестовых методов.
- При внедрении компонентов в конструктор нельзя использовать `KoraAppTestConfigModifier` и `KoraAppTestGraphModifier`.
- В режиме `PER_CLASS` нельзя внедрять `@Mock` / `@MockK` в параметры тестовых методов; используйте поля или конструктор.
- Для `@Nested` классов нельзя использовать внедрение в поля внутреннего класса, если внешний тестовый класс работает в режиме `PER_CLASS`; используйте параметры методов или отдельный жизненный цикл для вложенного класса.
