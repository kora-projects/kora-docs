---
description: "Explains Kora JUnit 5 testing support, application graph tests, component replacement, mocks, tags, test configuration, and initialization. Use when working with @KoraAppTest, @TestComponent, @Tag, KoraAppTestConfigModifier, Graph, Mockito."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JUnit 5 testing support, application graph tests, component replacement, mocks, tags, test configuration, and initialization; key triggers include @KoraAppTest, @TestComponent, @Tag, KoraAppTestConfigModifier, Graph, Mockito."
---

Модуль предоставляет расширение для [JUnit 5](https://junit.org/junit5/docs/current/user-guide/), которое позволяет тестировать приложение через тот же граф компонентов, что используется во время работы приложения.

Расширение Kora для `JUnit 5` предназначено для компонентного и интеграционного тестирования исходного кода, который впоследствии будет работать в реальном приложении.
В тесте используется контейнер зависимостей основного приложения: его можно ограничить нужными компонентами,
расширить тестовыми компонентами или заменить отдельные части заглушками.

Модуль позволяет проводить:

- `Компонентные тесты` — тестирование одного компонента.
- `Межкомпонентные тесты` — тестирование нескольких компонентов и их взаимодействия друг с другом.
- `Интеграционные тесты` — тестирование компонентов и взаимодействия с внешними системами.

Рекомендуется дополнительно тестировать артефакт сервиса, упакованный в итоговый образ,
как черный ящик с помощью [библиотеки Testcontainers](https://java.testcontainers.org/).

Пошаговый разбор перед справочным описанием смотрите в разделах [Компонентное тестирование](../guides/testing-junit.md), [Интеграционное тестирование](../guides/testing-integration.md) и [Тестирование черного ящика](../guides/testing-black-box.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    testImplementation "ru.tinkoff.kora:test-junit5"
    ```

    Настройка [платформы JUnit](https://docs.gradle.org/current/userguide/java_testing.html#using_junit5) `build.gradle`: 
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

    Настройка [платформы JUnit](https://docs.gradle.org/current/userguide/java_testing.html#using_junit5) `build.gradle.kts`: 
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

Примеры будут показаны применительно к такому приложению:

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

Чтобы включить расширение Kora, пометьте тестовый класс аннотацией `@KoraAppTest`.
Аннотация подключает расширение `JUnit 5`, находит сгенерированный граф указанного приложения `@KoraApp` и подготавливает контейнер зависимостей для теста.

Параметры аннотации `@KoraAppTest`:

- `value` — класс, помеченный `@KoraApp`, граф компонентов которого будет использоваться в тесте (`обязательный`, без значения по умолчанию).
- `components` — дополнительные классы компонентов, которые должны быть включены в тестовый граф в дополнение к компонентам, найденным через `@TestComponent` (по умолчанию: `{}`).
- `modules` — дополнительные модули с фабричными методами компонентов, которые должны быть подключены к тестовому графу (по умолчанию: `{}`).

В `modules` можно указывать только интерфейсы модулей. Если требуется протестировать весь граф, внедрите `KoraAppGraph` или не ограничивайте граф отдельными компонентами `@TestComponent`.

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

Для внедрения и выбора компонентов для тестирования используйте аннотацию `@TestComponent`.
Она позволяет внедрять компоненты в аргументы тестовых методов, в конструктор и/или в поля тестового класса, а также ограничивает контейнер зависимостей этими компонентами.

Все компоненты, перечисленные в полях теста и/или в аргументах метода/конструктора и помеченные `@TestComponent`, будут внедрены как зависимости в рамках теста.
Тестовый контейнер зависимостей будет ограничен этими компонентами и их зависимостями.

Важно, что компоненты внутри теста должны использоваться хотя бы одним [@Root компонентом](container.md#root-component), который также указан в рамках теста.

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
Выбранная форма влияет на то, когда расширение Kora может получить доступ к экземпляру тестового класса и какие дополнительные механизмы доступны.

- Поля подходят для большинства тестов и совместимы с `KoraAppTestConfigModifier`, `KoraAppTestGraphModifier`, `PER_METHOD` и `PER_CLASS`.
- Внедрение через конструктор удобно для неизменяемых полей, но несовместимо с `KoraAppTestConfigModifier` и `KoraAppTestGraphModifier`, поскольку расширению нужен экземпляр тестового класса для вызова `config()` или `graph()`, тогда как этот экземпляр еще создается во время внедрения через конструктор.
- Параметры метода удобны для зависимостей, локальных для конкретного теста; в режиме `PER_METHOD` граф включает параметры текущего метода, а в режиме `PER_CLASS` расширение заранее собирает параметры `@TestComponent` из всех методов класса.
- Если используется внедрение через конструктор, `@TestComponent`, `@Mock`, `@Spy`, `@MockK` или `@SpyK` нельзя также внедрять в параметры тестового метода.
- В режиме `PER_CLASS` `@Mock` / `@MockK` нельзя внедрять в параметры тестового метода, поскольку заглушки уровня метода живут меньше, чем общий граф тестового класса.
- Один и тот же элемент нельзя одновременно объявить как обычный `@TestComponent`, заглушку (mock) и шпион (spy): расширение завершит тест ошибкой конфигурации.

Если тесту нужны `KoraAppTestConfigModifier` или `KoraAppTestGraphModifier`, используйте внедрение через поля или параметры метода.
Если требуется внедрение через конструктор, лучше вынести изменение конфигурации и графа в отдельное тестовое `@KoraApp` или подключаемый модуль.

### Тег { #tag }

Чтобы внедрить зависимость/заглушку, помеченную `@Tag`, необходимо указать соответствующую аннотацию `@Tag` рядом с аргументом для внедрения:

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

Если тесту нужен прямой доступ к подготовленному графу, внедрите `KoraAppGraph` в поле, конструктор или аргумент тестового метода.
Он может получить один или несколько компонентов по типу, а также учитывать `@Tag`.

Основные методы `KoraAppGraph`:

- `getFirst(Type type)` / `getFirst(Class<T> type)` — возвращают первый найденный компонент или `null`.
- `getFirst(Type type, Class<?>... tags)` / `getFirst(Class<T> type, Class<?>... tags)` — возвращают первый компонент с указанными тегами или `null`.
- `findFirst(...)` — возвращает `Optional<T>` вместо `null`.
- `getAll(...)` — возвращает все компоненты указанного типа, при необходимости учитывая теги.

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

`KoraAppGraph` нельзя использовать как цель для `@Mock`, `@Spy`, `@MockK` или `@SpyK`, поскольку это служебный объект тестового расширения, а не компонент приложения.

### Заглушка { #mock }

===! ":fontawesome-brands-java: `Java`"

    Для создания заглушки компонента в Java в рамках теста предлагается использовать аннотации из библиотеки [Mockito](https://site.mockito.org/) совместно с аннотацией `@TestComponent`.

    Требуется добавить библиотеку [Mockito](https://site.mockito.org/) как зависимость в `build.gradle`:
    ```groovy
    testImplementation "org.mockito:mockito-core:5.18.0"
    ```

    **Важно**, предполагается, что `MockitoExtension` использоваться не будет и будет отключено, его нельзя совмещать вместе с `@KoraAppTest`.

    Поддерживаются аннотации [@Mock](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mock.html) и [@Spy](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Spy.html), а также все параметры этих аннотаций.
    Рекомендуется подробнее ознакомиться с тем, как работают эти аннотации, в [официальной документации библиотеки Mockito](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html).

    Аннотация [@Mock](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mock.html) позволяет сделать заглушку класса
    помеченного компонента и управлять поведением его методов с помощью `Mockito`, либо методы будут возвращать значения по умолчанию: `void`, значения по умолчанию для примитивов, пустые коллекции и `null` для всех остальных объектов. 

    Компонент-заглушка будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты, которым он требовался как зависимость.
    Все зависимые компоненты, которые больше нигде в рамках теста не требуются, будут исключены как ненужные.


    Пример теста с использованием компонента `@Mock` и внедрением заглушки в поле:

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

    Аннотация [@Spy](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Spy.html) позволяет сделать шпион-фасад реализации класса
    компонента из контейнера зависимостей, который по умолчанию будет иметь исходное поведение методов компонента,
    но, как и в случае с заглушками, их поведение можно переопределить.

    Компонент-шпион будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты, которым он требовался как зависимость.

    Пример теста с использованием компонента `@Spy` и внедрением шпиона в аргумент метода:

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

    Также можно сделать шпион из значения поля тестового класса.

    Компонент-шпион будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты, которым он требовался как зависимость.
    Все зависимые компоненты, которые больше нигде в рамках теста не требуются, будут исключены как ненужные.

    Пример теста с использованием компонента-шпиона `@Spy`:

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

    Для создания заглушек компонентов в Kotlin предлагается использовать аннотации из библиотеки [MockK](https://mockk.io/) совместно с аннотацией `@TestComponent`.

    Требуется подключить библиотеку [MockK](https://mockk.io/) как зависимость в ``build.gradle.kts``:
    ```groovy
    testImplementation("io.mockk:mockk:1.13.11")
    ```

    **Важно**, предполагается, что `MockkExtension` использоваться не будет и будет отключено, его нельзя совмещать вместе с `@KoraAppTest`.

    Поддерживаются аннотации [@MockK](https://mockk.io/#annotations) и [@SpyK](https://mockk.io/#annotations), а также все параметры этих аннотаций.

    При желании также можно использовать [Mockito](https://site.mockito.org/). 
    Для более подробного описания того, как работают Kora и [Mockito](https://site.mockito.org/), следует прочитать вкладку Java этого раздела.
    Для улучшения взаимодействия между Mockito и Kotlin можно использовать библиотеку [Mockito Kotlin](https://github.com/mockito/mockito-kotlin).
    ```groovy
    testImplementation("org.mockito.kotlin:mockito-kotlin:5.4.0")
    ```

    **Важно**, предполагается, что `MockitoExtension` использоваться не будет и будет отключено, его нельзя совмещать вместе с `@KoraAppTest`.

    Аннотация [@MockK](https://mockk.io/#annotations) позволяет сделать заглушку класса
    помеченного компонента и управлять поведением его методов с помощью `MockK`. 

    Компонент-заглушка будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты, которым он требовался как зависимость.
    Все зависимые компоненты, которые больше нигде в рамках теста не требуются, будут исключены как ненужные.

    Пример теста с использованием компонента `@MockK` и внедрением заглушки:

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

    Аннотация [@SpyK](https://mockk.io/#annotations) позволяет сделать шпион-фасад реализации класса
    компонента из контейнера зависимостей, который по умолчанию будет иметь исходное поведение методов компонента,
    но, как и в случае с заглушками, их поведение можно переопределить.

    Компонент-шпион будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты, которым он требовался как зависимость.

    Пример теста с использованием компонента `@SpyK` и встраиванием шпиона в аргумент метода:

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

    Также можно сделать шпион из значения поля тестового класса.

    Компонент-шпион будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты, которым он требовался как зависимость.
    Все зависимые компоненты, которые больше нигде в рамках теста не требуются, будут исключены как ненужные.

    Пример теста с использованием компонента-шпиона `@SpyK`:

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

#### Строгость заглушек { #mock-strictness }

Заглушки `Mockito` можно проверять с помощью аннотации `@MockitoStrictness`.
Она задает уровень проверки для заглушек `Mockito`, созданных расширением Kora в рамках тестового класса.

Расширение ведет себя аналогично `MockitoSession`: после завершения теста оно передает созданные заглушки на проверку `Mockito` и сообщает о неиспользованных или подозрительных настройках поведения.
Если `@MockitoStrictness` не указана, Kora использует `Strictness.WARN`: тест не падает, но в лог записываются предупреждения.

Поддерживаемые уровни:

- `Strictness.WARN` — значение по умолчанию; записывает предупреждения в лог и не приводит к падению теста.
- `Strictness.STRICT_STUBS` — строгий режим; неиспользованная настройка поведения приводит к падению теста, например с `UnnecessaryStubbingException`.
- `Strictness.LENIENT` — мягкий режим; отключает проверки неиспользованных настроек поведения.

Если у конкретной `@Mock` есть собственный параметр `strictness`, он применяется к настройкам этой заглушки.
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

В примере выше `Mockito.when(component1.get()).thenReturn("?")` должно быть использовано тестом.
Если убрать вызов `component1.get()` из тестового метода, `Strictness.STRICT_STUBS` приведет к падению теста.

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

Для Kotlin с `Mockito Kotlin` действует тот же механизм, поскольку проверку выполняет `Mockito`.
`@MockitoStrictness` не применяется к заглушкам `MockK`.

### Тестовый граф { #test-graph }

Иногда в рамках тестов может потребоваться использовать расширенный контейнер зависимостей.
Например, тестовое приложение может расширять основное приложение и добавлять компоненты, которые нужны только в тестах.

Такой подход полезен, когда у вас есть разные приложения Read API и Write API с общими компонентами,
которые могут потребоваться при тестировании одного и другого.
Или же вам могут понадобиться какие-то функции сохранения/удаления/обновления исключительно для тестирования в качестве быстрой тестовой утилиты.

???+ warning "Рекомендация"

    **Настоятельно рекомендуется тестировать** приложения как [черный ящик](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/BlackBoxTests.java)
    и полагаться на этот подход как на основной источник истины и корректности приложения.

    Приложение может работать по-разному в зависимости от флагов JVM,
    базового образа и нативных библиотек, различий между частичными и полными конфигурациями,
    различий в преобразовании на точках входа приложения, использования реестров схем и так далее.
    Только prod-ready образ может гарантировать максимально близкое к реальному окружение тестирования.

Представим, что приложение выглядит так:

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

В тестах можно создать отдельное тестовое `@KoraApp`, которое расширяет основное приложение, и использовать этот граф.
Для этого сценария требуется сгенерированный субмодуль основного приложения: без него тестовое приложение не сможет унаследовать и подключить компоненты основного графа.

===! ":fontawesome-brands-java: `Java`"

    Сначала включите параметр, который создает субмодуль основного приложения, в `build.gradle`:

    ```groovy
    compileJava {
        options.compilerArgs += [
            "-Akora.app.submodule.enabled=true"
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Сначала включите параметр, который создает субмодуль основного приложения, в `build.gradle.kts`:

    ```groovy
    ksp {
        arg("kora.app.submodule.enabled", "true")
    }
    ```

Затем требуется создать расширенный тестовый граф приложения в каталоге тестовых исходников.
Не забудьте пометить компоненты как `@Root`, поскольку они, скорее всего, никем не используются,
кроме тестов, и иначе не будут включены в граф:

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

    Чтобы граф тестового приложения был сгенерирован, нужно добавить обработчики как тестовые зависимости в `build.gradle`:

    ```groovy
    dependencies {
        testAnnotationProcessor "ru.tinkoff.kora:annotation-processors"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Чтобы граф тестового приложения был сгенерирован, нужно добавить обработчики как тестовые зависимости в `build.gradle.kts`:

    ```groovy
    dependencies {
        kspTest("ru.tinkoff.kora:symbol-processors")
    }
    ```

Может потребоваться исключить сканирование сгенерированных Kora классов средствами JUnit (иногда возникает ошибка при поиске тестов):

===! ":fontawesome-brands-java: `Java`"

    Классы начинаются с символа `$`, исключите их в `build.gradle`:

    ```java
    test {
        exclude("**/\$*")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Классы начинаются с символа `$`, исключите их в `build.gradle.kts`:

    ```kotlin
    tasks.test {
        exclude("**/\$*")
    }
    ```

Теперь вы можете использовать расширенный граф приложения в своих тестах:

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

Если наследование от основного `@KoraApp` не требуется и нужно добавить только фабричные методы из отдельного модуля,
используйте параметр `modules` аннотации `@KoraAppTest`.
`modules` принимает интерфейсы модулей, а не классы компонентов:

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

- `kora.app.submodule.enabled=true` нужен, когда тестовое `@KoraApp` расширяет основное `@KoraApp`.
- `@KoraAppTest(modules = ...)` подходит для случаев, когда к тестовому графу нужно просто подключить дополнительные модули.
- Компоненты, которые должны появиться в ограниченном тестовом графе, все равно должны быть достижимы из `@TestComponent`, `components` или `KoraAppGraph`.

## Конфигурация теста { #test-configuration }

По умолчанию будет использоваться базовая конфигурация, как и в случае запуска реального приложения.

Чтобы изменить или добавить конфигурацию в рамках тестов, тестовый класс должен реализовать `KoraAppTestConfigModifier`,
а метод `config()` должен возвращать `KoraConfigModification`.

`KoraAppTestConfigModifier` нельзя использовать вместе с внедрением компонентов в конструктор тестового класса:
расширению нужно получить изменение конфигурации до создания тестового графа, а для этого экземпляр теста должен уже существовать.

#### Переменные окружения { #environment-variables }

Если тесту нужно использовать [конфигурацию по умолчанию](config.md#file), которая использовалась бы при запуске приложения,
и требуется лишь подставить переменные окружения, можно воспользоваться механизмом `SystemProperty` в `KoraConfigModification`:

===! ":material-code-json: `Hocon`"

    Предположим, есть такая конфигурация `application.conf`:

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

    Предположим, есть такая конфигурация `application.yaml`:

    ```yaml
    db:
      jdbcUrl: ${POSTGRES_JDBC_URL}
      username: ${POSTGRES_USER}
      password: ${POSTGRES_PASS}
      maxPoolSize: 10
      poolName: "example"
    ```

Чтобы использовать такой конфиг и передать только переменные окружения, нужно вернуть такой `KoraConfigModification`:

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

Если нужно передать сразу несколько значений, используйте `withSystemProperties(Map<String, String>)`:

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

Пример предоставления конфигурации в виде файла:

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

Пример добавления конфигурации в виде строки выглядел бы так,
в этом случае будет использоваться только эта конфигурация без каких-либо файлов конфигурации:

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

### Подстановка в конфигурации { #configuration-substitution }

Подстановка переменных окружения, показанная в разделе [Переменные окружения](#environment-variables), также работает со встроенной конфигурацией:
объявите плейсхолдеры `${ENV}` прямо внутри конфигурации `ofString(...)` и разрешите их через цепочку вызовов `withSystemProperty(...)`.
Это удобно, когда вся конфигурация описана в тесте, но некоторые значения (порты, хосты, учетные данные) известны только во время выполнения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests implements KoraAppTestConfigModifier {

        @Override
        public @Nonnull KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                myconfig {
                    myinnerconfig {
                        first = ${ENV_FIRST}
                        second = ${ENV_SECOND}
                    }
                }
                """)
                .withSystemProperty("ENV_FIRST", "1")
                .withSystemProperty("ENV_SECOND", "2");
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
                    myinnerconfig {
                        first = \${ENV_FIRST}
                        second = \${ENV_SECOND}
                    }
                }
                """.trimIndent()
            )
                .withSystemProperty("ENV_FIRST", "1")
                .withSystemProperty("ENV_SECOND", "2")
        }
    }
    ```

### Testcontainers { #testcontainers }

Распространенное применение `KoraAppTestConfigModifier` — интеграция с [Testcontainers](https://java.testcontainers.org/):
тест запускает контейнер и передает его значения подключения времени выполнения в конфигурацию через `config()`.
Testcontainers назначает случайный порт хоста при каждом запуске, поэтому значения нельзя жестко зашивать — они объявляются как плейсхолдеры `${...}` во встроенной конфигурации
и заполняются из геттеров контейнера через `withSystemProperty(...)`.

Поскольку `config()` выполняется **до** построения тестового графа, конфигурация готова до создания любого компонента.
По той же причине `KoraAppTestConfigModifier` несовместим с [внедрением через конструктор](#injection-rules): используйте внедрение через поле или параметр метода, как показано ниже.

===! ":fontawesome-brands-java: `Java`"

    Добавьте зависимости [Testcontainers](https://java.testcontainers.org/) в `build.gradle`:
    ```groovy
    testImplementation "org.testcontainers:junit-jupiter:1.21.4"
    testImplementation "org.testcontainers:postgresql:1.21.4"
    ```

    ```java
    @Testcontainers
    @KoraAppTest(Application.class)
    class SomeIntegrationTests implements KoraAppTestConfigModifier {

        @Container
        private static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16");

        @TestComponent
        private SomeService service;

        @NotNull
        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                db {
                    jdbcUrl = ${POSTGRES_JDBC_URL}
                    username = ${POSTGRES_USER}
                    password = ${POSTGRES_PASS}
                    poolName = "kora"
                }
                """)
                .withSystemProperty("POSTGRES_JDBC_URL", POSTGRES.getJdbcUrl())
                .withSystemProperty("POSTGRES_USER", POSTGRES.getUsername())
                .withSystemProperty("POSTGRES_PASS", POSTGRES.getPassword());
        }

        @Test
        void example() {
            // interact with the service backed by the container
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте зависимости [Testcontainers](https://java.testcontainers.org/) в `build.gradle.kts`:
    ```groovy
    testImplementation("org.testcontainers:junit-jupiter:1.21.4")
    testImplementation("org.testcontainers:postgresql:1.21.4")
    ```

    ```kotlin
    @Testcontainers
    @KoraAppTest(Application::class)
    class SomeIntegrationTests : KoraAppTestConfigModifier {

        companion object {
            @Container
            @JvmStatic
            val POSTGRES = PostgreSQLContainer("postgres:16")
        }

        @TestComponent
        lateinit var service: SomeService

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofString(
                """
                db {
                    jdbcUrl = \${POSTGRES_JDBC_URL}
                    username = \${POSTGRES_USER}
                    password = \${POSTGRES_PASS}
                    poolName = "kora"
                }
                """.trimIndent()
            )
                .withSystemProperty("POSTGRES_JDBC_URL", POSTGRES.jdbcUrl)
                .withSystemProperty("POSTGRES_USER", POSTGRES.username)
                .withSystemProperty("POSTGRES_PASS", POSTGRES.password)
        }

        @Test
        fun example() {
            // interact with the service backed by the container
        }
    }
    ```

Полный разбор — зависимости, тестовое `@KoraApp`, миграции и настройка репозитория — смотрите в руководстве [Интеграционное тестирование](../guides/testing-integration.md).

## Изменение контейнера { #container-modification }

Чтобы добавить, заменить или программно создать заглушки в контейнере приложения без аннотаций, реализуйте `KoraAppTestGraphModifier`
и верните `KoraGraphModification` из метода `graph()`.

`KoraAppTestGraphModifier` нельзя использовать вместе с внедрением компонентов в конструктор тестового класса:
расширению нужно получить изменение графа до создания графа и внедрения компонентов.

`KoraGraphModification` поддерживает следующие операции:

- `addComponent(...)` — добавляет новый компонент в тестовый граф.
- `replaceComponent(...)` — заменяет существующий компонент, при этом его зависимости остаются в графе.
- `mockComponent(...)` — заменяет существующий компонент заглушкой и удаляет реальные зависимости заменяемого компонента из графа, если они больше не нужны тесту.

`addComponent(...)` и `replaceComponent(...)` имеют перегрузки с `Function<KoraAppGraph, T>`, если новый компонент должен быть построен из уже инициализированных компонентов графа.
Для компонентов с `@Tag` используйте перегрузки с `List<Class<?>> tags`.

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

В случае, когда требуется добавить компоненты с использованием реального компонента из графа, это также доступно через другую сигнатуру метода:

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

Пример замены компонента в контейнере зависимостей, этот механизм также можно использовать для создания собственных заглушек:

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

В случае, когда требуется заменить компоненты с использованием реального компонента из графа, это также доступно через другую сигнатуру метода:

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

Если компонент нужно заменить именно как заглушку, используйте `mockComponent(...)`.
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
Если контейнер должен инициализироваться один раз для всего тестового класса, пометьте тестовый класс аннотацией `@TestInstance(TestInstance.Lifecycle.PER_CLASS)`:

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

С `PER_CLASS` один экземпляр графа используется всеми тестовыми методами класса, а очистка выполняется после завершения всего класса.
Это ускоряет тяжелые интеграционные тесты, но с изменяемым состоянием компонентов и заглушек нужно обращаться аккуратнее.

Ограничения жизненного цикла:

- Когда компоненты внедряются в конструктор, `@TestComponent` или заглушки нельзя также внедрять в параметры тестового метода.
- Когда компоненты внедряются в конструктор, нельзя использовать `KoraAppTestConfigModifier` и `KoraAppTestGraphModifier`.
- В режиме `PER_CLASS` `@Mock` / `@MockK` нельзя внедрять в параметры тестового метода; используйте поля или конструктор.
- Для классов `@Nested` нельзя использовать внедрение в поля внутреннего класса, если внешний тестовый класс работает в режиме `PER_CLASS`; используйте параметры метода или отдельный жизненный цикл для вложенного класса.
