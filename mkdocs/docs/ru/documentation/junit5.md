Модуль предоставляет `Extension` для [JUnit5](https://junit.org/junit5/docs/current/user-guide/) который позволяет легко тестировать приложение.

Концепция JUnit 5 расширения Kora предполагает тестирование именно исходного кода который будет в итоге использоваться в бою,
это подразумевает что именно контейнер зависимостей основного приложения и участвует в рамках теста, 
он может быть ограничен либо его части заменены заглушками если этого требуется тест.

## Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    testImplementation "ru.tinkoff.kora:test-junit5"
    ```

    Настроить [JUnit платформу](https://docs.gradle.org/current/userguide/java_testing.html#using_junit5) `build.gradle`:
    ```groovy
    test {
        useJUnitPlatform()
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    testImplementation("ru.tinkoff.kora:test-junit5")
    ```

    Настроить [JUnit платформу](https://docs.gradle.org/current/userguide/java_testing.html#using_junit5) `build.gradle.kts`:
    ```groovy
    tasks.test {
        useJUnitPlatform() 
    }
    ```

## Использование

Примеры будут показаны относительно такого приложения:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        @Root
        Supplier<String> supplier() {
            return () -> "1";
        }

        @Root
        @Tag(Supplier.class)
        Supplier<String> supplierTagged() {
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

### Тест

Предполагается использовать аннотацию `@KoraAppTest` для аннотирования тестового класса.

Параметры аннотации `@KoraAppTest`:

- `value` - обязательный параметр который указывает на класс аннотированный `@KoraApp`, представляющий собой граф всех зависимостей которые будут доступны в рамках теста.
- `components` - список компонентов которые надо инициализировать в рамках теста, 
  указываются компоненты которые не объявлены в рамках теста с помощью специальной аннотации `@TestComponent`.

### Компонент

Для использования компонентов в рамках теста предлагается использовать аннотацию `@TestComponent` 
которая позволяет внедрять компоненты в аргументы метода и/или поля тестового класса.

Все компоненты перечисленные в тестовых полях и/или аргументах метода/конструктора с аннотацией `@TestComponent` будут внедрены как зависимости в рамках теста
и весь контейнер зависимостей будет ограничен именно этими компонентами и их зависимостями в рамках теста.

Пример теста, где компоненты внедряются в поля:

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

#### Тег

Для внедрения зависимости которая имеет `@Tag`, требуется указать соответствующую аннотацию `@Tag` рядом с внедряемым аргументом:

=== ":fontawesome-brands-java: `Java`"

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
        fun example(@Tag(Supplier.class) @TestComponent component1: Supplier<String>) {
            assertEquals("?", component1.get())
        }
    }
    ```

#### Заглушки

=== ":fontawesome-brands-java: `Java`"

    Для создание заглушек компонент в Java в рамках теста предлагается использовать аннотации предоставляемые библиотекой [Mockito](https://site.mockito.org/) в совокупности с аннотацией `@TestComponent`.

    Требуется подключить библиотеку [Mockito](https://site.mockito.org/) как зависимость `build.gradle`:
    ```groovy
    testImplementation "org.mockito:mockito-core:5.7.0"
    ```

    Поддерживаются аннотациии [@Mock](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mock.html) и [@Spy](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Spy.html), а также все параметры этих аннотаций.
    Рекомендуется подробнее ознакомиться с работой этих аннотацией в [официальной документации библиотеки Mockito](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html).

    Аннотация [@Mock](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mock.html) позволяет сделать класс заглушку 
    проаннотированного компонента и контролировать поведение его методов с помощью `Mockito` либо методы будут возвращать значения по-умолчанию: `void`, значения по умолчанию для примитивов, пустые коллекции и `null` для всех остальных объектов. 

    Компонент заглушка будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты которые требовали его как зависимость.
    Все зависимые компоненты которые больше ни где не требуются в рамках теста будут исключены за ненанобностью.

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
    Все зависимые компоненты которые больше ни где не требуются в рамках теста будут исключены за ненанобностью.

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
    testImplementation("io.mockk:mockk:1.13.8")
    ```

    Поддерживаются аннотациии [@MockK](https://mockk.io/#annotations) и [@SpyK](https://mockk.io/#annotations), а также все параметры этих аннотаций.

    Также есть возможность при желании использовать [Mockito](https://site.mockito.org/). 
    Для более подробного описания работы Kora и [Mockito](https://site.mockito.org/) следует ознакопиться с Java вкладкой этого абзаца.
    Чтобы улучшить взаимодействие Mockito и Kotlin можно использовать библиотеку [Mockito Kotlin](https://github.com/mockito/mockito-kotlin).

    Аннотация [@MockK](https://mockk.io/#annotations) позволяет сделать класс заглушку 
    проаннотированного компонента и контролировать поведение его методов с помощью `MockK`. 

    Компонент заглушка будет внедрен как зависимость в аргументы и/или поля тестового класса и во все компоненты которые требовали его как зависимость.
    Все зависимые компоненты которые больше ни где не требуются в рамках теста будут исключены за ненанобностью.

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
    Все зависимые компоненты которые больше ни где не требуются в рамках теста будут исключены за ненанобностью.

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

## Настройка конфигурации

По умолчанию будет использоваться основная конфигурация, как и в случае запуска реального приложения.

Для изменений/добавления конфига в рамках тестов предполагается чтобы тестовый класс реализовал интерфейс `KoraAppTestConfigModifier`, 
где требуется реализовать метод предоставления модификации конфига `KoraConfigModification`.

Запрещено использовать `KoraAppTestConfigModifier` и внедрение в конструктор так как в таком случае нельзя получить конфигуацию до внедрения.

### Переменные окружения

В случае если в рамках теста надо использовать [конфигурацию по умолчанию](config.md#_3) которая использовалась бы во время работы приложения,
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

=== ":fontawesome-brands-java: `Java`"

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

### Файл конфигурации

Пример добавления конфигурации в виде файла:

=== ":fontawesome-brands-java: `Java`"

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

### Текст конфигурации

Пример добавления конфигурации в виде строки будет выглядеть так, 
в таком случае будет использоваться только эта конфигурация без каких либо файлов конфигурации:

=== ":fontawesome-brands-java: `Java`"

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

## Модификация контейнера

Для добавления/замены компонент в рамках контейнера приложения без аннотаций требуется реализовать интерфейс `KoraAppTestGraphModifier` и 
реализовать метод предоставления модификатора контейнера.

Запрещено использовать `KoraAppTestGraphModifier` и внедрение в конструктор так как в таком случае нельзя получить граф до внедрения.

### Добавление

Пример добавления компонента в граф:

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

### Замена

Пример замены компонента в контейнере, этот механизм также можно использовать для создания собственных заглушек:

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

## Инициализация

В случае если требуется инициализировать контейнер один раз в рамках всего тестового класса, следует проаннотировать тестовый класс с помощью `@TestInstance(TestInstance.Lifecycle.PER_CLASS)`:

=== ":fontawesome-brands-java: `Java`"

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

Поведение по умолчанию - инициализация контейнера с нуля для каждого тестового метода.
