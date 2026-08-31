---
description: "Explains Kora compile-time dependency injection container, components, modules, factory modules, tags, conditions, lifecycle, graph resolution, and dependency wrappers. Use when working with @KoraApp, @Component, @Module, @KoraSubmodule, @FactoryModule, @Root, @Tag, @DefaultComponent, @Conditional, ValueOf."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora compile-time dependency injection container, components, modules, factory modules, tags, conditions, lifecycle, graph resolution, and dependency wrappers; key triggers include @KoraApp, @Component, @Module, @KoraSubmodule, @FactoryModule, @Root, @Tag, @DefaultComponent, @Conditional, ValueOf, All, PromiseOf, GraphInterceptor, KoraApplication.run."
---

Контейнер зависимостей — это ядро фреймворка `Kora`. Он строит граф зависимостей, проверяет его,
внедряет компоненты, инициализирует их и позднее освобождает.
В отличие от контейнеров, которые собирают приложение при запуске путем сканирования classpath, `Kora` строит большую часть графа
во время компиляции и генерирует обычный `Java`-код для запуска приложения.

Работа контейнера в `Kora` разделена на две части: время компиляции и время выполнения.
Во время компиляции `Kora` проверяет, что все зависимости могут быть найдены и связаны. Во время выполнения контейнер создает
компоненты, управляет их жизненным циклом и обновляет затронутые части графа при возникновении изменений.

Все аннотации контейнера находятся в пакете `io.koraframework.common.annotation`,
а все контракты графа времени выполнения — в пакете `io.koraframework.application.graph`.

Пошаговый разбор перед справочным описанием смотрите в разделах [Введение во внедрение зависимостей](../guides/dependency-injection-introduction.md) и [Внедрение зависимостей](../guides/dependency-injection.md).

## Время компиляции { #compile-time }

Во время компиляции компоненты обнаруживаются, чтобы построить контейнер зависимостей для всего приложения.
Это позволяет проверить контейнер зависимостей до фактического запуска приложения.

### Контейнер { #container }

Ядром контейнера зависимостей является интерфейс, помеченный аннотацией `@KoraApp`.
Эту аннотацию следует использовать на интерфейсе, который содержит фабричные методы для создания компонентов
и подключает [внешние модули](#external-module-factory).
В приложении может быть только один такой интерфейс.

`@KoraApp` можно ставить только на интерфейс — на классе аннотация приводит к ошибке компиляции.

Обработчики аннотаций `Kora` анализируют исходный код в модуле компиляции, где объявлен `@KoraApp`,
а также в модулях, где объявлен [`@KoraSubmodule`](#submodule-factory). Обычные модули проекта без
`@KoraApp` или `@KoraSubmodule` не становятся областями обнаружения компонентов автоматически.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application { }
    ```

### Компоненты { #components }

Компонент — это зависимость в контейнере зависимостей.
Все компоненты в `Kora` создаются в единственном экземпляре (`Singleton`).
Компоненты внедряются только если они являются [корневыми компонентами](#root-component) или если другие компоненты нуждаются в них как в зависимостях.

Компоненты, которые не удовлетворяют этим требованиям, не включаются в контейнер зависимостей.

#### Автоматическая фабрика { #auto-factory }

Аннотация `@Component` помечает класс как доступный через контейнер. К классу предъявляются следующие требования:

===! ":fontawesome-brands-java: `Java`"

    * Класс не должен быть абстрактным (`@Component` на абстрактном классе или интерфейсе игнорируется)
    * У класса должен быть ровно один публичный конструктор
    * Класс должен быть `final` (только если у него нет аспектов)

    ```java
    @Component
    public final class SomeService {

        private final OtherService otherService;

        public SomeService(OtherService otherService) {
            this.otherService = otherService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    * Класс не должен быть абстрактным (`@Component` на абстрактном классе или интерфейсе игнорируется)
    * У класса должен быть ровно один публичный конструктор
    * Класс не должен быть `open` (только если у него нет аспектов)

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService)
    ```

#### Фабричный метод { #method-factory }

Фабричный метод — это метод с модификатором `default`, который возвращает компонент.
Метод может принимать другие компоненты-зависимости в качестве аргументов.

Контейнер зависимостей ниже описывает две фабрики, где фабрика `otherService` требует компонент, созданный фабрикой `someService`.
Это самый простой способ зарегистрировать компоненты в контейнере:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default SomeService someService() {
            return new SomeService();
        }

        default OtherService otherService(SomeService someService) {
            return new OtherService(someService);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        fun someService(): SomeService = SomeService()

        fun otherService(someService: SomeService): OtherService {
            return OtherService(someService)
        }
    }
    ```

Фабричный метод **не должен** возвращать `null` в качестве компонента,
и он обязан возвращать ссылочный тип: фабрика с примитивным типом или `void` не компилируется.

#### Модуль { #module-factory }

Компоненты контейнера зависимостей также могут находиться в модулях внутри проекта приложения.
Модулем называется интерфейс, содержащий фабричные методы.
Аннотация `@Module` помечает интерфейс как модуль, который во время компиляции будет внедрен в контейнер приложения.
Модуль должен находиться в том же модуле компиляции, что и интерфейс, помеченный `@KoraApp`.

`@Module` поддерживается только на интерфейсах.

Все фабричные методы внутри модуля становятся доступны контейнеру зависимостей:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        default SomeService someService() {
            return new SomeService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun someService(): SomeService = SomeService()
    }
    ```

#### Внешний модуль { #external-module-factory }

Компоненты контейнера зависимостей также можно искать во внешних модулях из сторонних зависимостей.
Модулем называется интерфейс, содержащий фабричные методы.
`Kora` не выполняет автоматический поиск модулей во внешних зависимостях, как это делают некоторые другие DI-решения.
Это позволяет разработчику точно контролировать, какие зависимости используются в приложении, и избежать
инициализации ненужных компонентов.

Все необходимые внешние модули из зависимостей должны подключаться явно в интерфейсе, помеченном аннотацией `@KoraApp`, через наследование:

Такой модуль может быть объявлен в любом интерфейсе: в сторонней библиотеке, в отдельном модуле проекта или рядом с самим `@KoraApp`.
Важно лишь то, что интерфейс `@KoraApp` явно подключает его через наследование.
Внешнему модулю не нужна аннотация `@Module` — подключает его именно наследование.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends LogbackModule, JsonModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : LogbackModule, JsonModule
    ```

#### Подмодуль { #submodule-factory }

Аннотация `@KoraSubmodule` помечает интерфейс, для которого должен быть построен модуль текущего модуля компиляции.
Он будет содержать все компоненты, помеченные аннотациями `@Module` и `@Component`.
Эта аннотация полезна, когда проект разделен на [многомодульное приложение](https://docs.gradle.org/current/userguide/multi_project_builds.html)
с точки зрения системы сборки `Gradle`, где каждый модуль отвечает за свою часть функциональности,
а приложение с `@KoraApp` собирается в отдельном модуле компиляции.
Такой подход помогает структурировать большой проект по предметным областям и улучшить время сборки:
изменения в одном модуле проекта не заставляют обработчик аннотаций заново анализировать весь код приложения.

Для интерфейса будет сгенерирован интерфейс-наследник с именем `<ИмяИнтерфейса>SubmoduleImpl`. Он унаследует все интерфейсы, помеченные `@Module`,
и создаст фабричные методы для классов, помеченных `@Component`. Приложение подключает сам аннотированный интерфейс,
а `Kora` сама находит для него сгенерированную реализацию.

Например, у вас есть отдельный модуль приложения, который содержит такой `@KoraSubmodule`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeSmallModule {

        default SomeService someService() {
            return new SomeService();
        }
    }

    @KoraSubmodule
    public interface SomeSubModule {

        default OtherService otherService(SomeService someService) {
            return new OtherService(someService);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun someService(): SomeService = SomeService()
    }

    @KoraSubmodule
    interface SomeSubModule {

        fun otherService(someService: SomeService): OtherService {
            return OtherService(someService)
        }
    }
    ```

И есть главный модуль приложения с точкой сборки всего приложения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends SomeSubModule {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : SomeSubModule
    ```

Это подключит найденный через `SomeSubModule` модуль `SomeModule` к итоговому контейнеру приложения.

Типичный практический сценарий использования `@KoraSubmodule` — отдельный `Gradle`-модуль, который владеет одной предметной областью
и просто агрегирует нужные ему [внешние модули](#external-module-factory) (базы данных, кэши и так далее) через наследование,
вместе со своими классами `@Component` и интерфейсами `@Module`. Модуль приложения затем подключает
сгенерированные подмодули так же, как любой другой модуль:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // in the "pet" Gradle module
    @KoraSubmodule
    public interface PetModule extends JdbcDatabaseModule, CaffeineCacheModule { }

    // in the application Gradle module
    @KoraApp
    public interface Application extends PetModule, VetModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // in the "pet" Gradle module
    @KoraSubmodule
    interface PetModule : JdbcDatabaseModule, CaffeineCacheModule

    // in the application Gradle module
    @KoraApp
    interface Application : PetModule, VetModule
    ```

#### Фабричный модуль { #factory-module }

Аннотация `@FactoryModule` помечает метод модуля, **возвращаемое значение которого само является модулем**.
Возвращенный объект регистрируется в контейнере как обычный компонент, а его публичные методы
обрабатываются как фабрики компонентов.

Это позволяет собрать модуль, поведение которого параметризуется обычными аргументами конструктора, чего
нельзя сделать в простом модуле-интерфейсе. Сама `Kora` использует этот механизм: `JdbcDatabaseModule` предоставляет свои компоненты
через `new JdbcDatabaseFactoryModule("jdbc")`, где строка — это путь конфигурации, который читает модуль.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class InnerModule {

        private final Config config;

        public InnerModule(Config config) {
            this.config = config;
        }

        public SomeService someService() {
            return new SomeService(config);
        }
    }

    @Module
    public interface OuterModule {

        @FactoryModule
        default InnerModule inner(Config config) { //(1)!
            return new InnerModule(config);
        }
    }
    ```

    1.  Метод может принимать любые компоненты графа в качестве аргументов, как и обычный фабричный метод.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class InnerModule(private val config: Config) {

        fun someService(): SomeService = SomeService(config)
    }

    @Module
    interface OuterModule {

        @FactoryModule
        fun inner(config: Config): InnerModule { //(1)!
            return InnerModule(config)
        }
    }
    ```

    1.  Метод может принимать любые компоненты графа в качестве аргументов, как и обычный фабричный метод.

В графе из примера выше будет два узла: `InnerModule` и созданный им `SomeService`.
Методы, унаследованные возвращаемым типом от его супертипов, также обрабатываются как фабрики.
`@FactoryModule` работает и на методах, объявленных прямо в интерфейсе `@KoraApp`,
а аннотированный метод обязан возвращать класс или интерфейс.

##### Тег фабричного модуля { #factory-module-tag }

`@Tag` на методе `@FactoryModule` помечает **экземпляр модуля**.
Внутри класса модуля `@Tag(Tag.Factory.class)` означает «использовать тег объемлющего фабричного модуля».
Именно так один тип фабричного модуля можно объявить несколько раз с разными тегами и получить несколько
независимо сконфигурированных наборов компонентов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class DataSourceModule {

        private final String configPath;

        public DataSourceModule(String configPath) {
            this.configPath = configPath;
        }

        @Tag(Tag.Factory.class) //(1)!
        public DataSourceConfig config(Config config, ConfigValueMapper<DataSourceConfig> mapper) {
            return mapper.mapOrThrow(config.get(this.configPath));
        }

        @Tag(Tag.Factory.class)
        public DataSource dataSource(@Tag(Tag.Factory.class) DataSourceConfig config) { //(2)!
            return new DataSource(config);
        }
    }

    @KoraApp
    public interface Application {

        @Tag(MainDb.class)
        @FactoryModule
        default DataSourceModule mainDb() {
            return new DataSourceModule("db.main");
        }

        @Tag(ReplicaDb.class)
        @FactoryModule
        default DataSourceModule replicaDb() {
            return new DataSourceModule("db.replica");
        }
    }
    ```

    1.  Созданный компонент получает тег метода фабричного модуля, то есть `@Tag(MainDb.class)` и `@Tag(ReplicaDb.class)` соответственно.
    2.  На параметре `@Tag(Tag.Factory.class)` запрашивает компонент, созданный **тем же** экземпляром фабричного модуля.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class DataSourceModule(private val configPath: String) {

        @Tag(Tag.Factory::class) //(1)!
        fun config(config: Config, mapper: ConfigValueMapper<DataSourceConfig>): DataSourceConfig {
            return mapper.mapOrThrow(config.get(configPath))
        }

        @Tag(Tag.Factory::class)
        fun dataSource(@Tag(Tag.Factory::class) config: DataSourceConfig): DataSource { //(2)!
            return DataSource(config)
        }
    }

    @KoraApp
    interface Application {

        @Tag(MainDb::class)
        @FactoryModule
        fun mainDb(): DataSourceModule = DataSourceModule("db.main")

        @Tag(ReplicaDb::class)
        @FactoryModule
        fun replicaDb(): DataSourceModule = DataSourceModule("db.replica")
    }
    ```

    1.  Созданный компонент получает тег метода фабричного модуля, то есть `@Tag(MainDb::class)` и `@Tag(ReplicaDb::class)` соответственно.
    2.  На параметре `@Tag(Tag.Factory::class)` запрашивает компонент, созданный **тем же** экземпляром фабричного модуля.

Если у метода фабричного модуля тега нет, `@Tag(Tag.Factory)` разворачивается в «без тега», и созданные компоненты остаются нетегированными.
Использование `@Tag(Tag.Factory)` вне фабричного модуля — ошибка компиляции.

#### Обобщенная фабрика { #generic-factory }

Если контейнер зависимостей не смог найти фабрику для конкретного типа, контейнер `Kora` может во время компиляции
попытаться найти методы с обобщенными параметрами и использовать такой метод для создания экземпляра требуемого класса.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        default <T> GenericValidator<T> genericValidator(SomeValidationEntity<T> entity) {
            return new GenericValidator<>(entity);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun <T> genericValidator(entity: SomeValidationEntity<T>): GenericValidator<T> {
            return GenericValidator(entity)
        }
    }
    ```

Теперь, если какому-либо компоненту потребуется `GenericValidator` в качестве зависимости, для его создания будет использована эта фабрика.

##### Информация об обобщенном типе { #type-ref }

Если фабричному методу нужно знать точный обобщенный тип, который контейнер запрашивает в данный момент, он может внедрить `TypeRef<T>`.
Это полезно для инфраструктурных компонентов, которые создают зависимость по форме типа, а не только по «сырому» классу.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        default <T> Validator<List<T>> listValidator(Validator<T> validator, TypeRef<T> typeRef) {
            return new ListValidator<>(validator, typeRef);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun <T> listValidator(validator: Validator<T>, typeRef: TypeRef<T>): Validator<List<T>> {
            return ListValidator(validator, typeRef)
        }
    }
    ```

`TypeRef<T>` переносит информацию об обобщенном типе через стирание типов `Java`. Большинству прикладных компонентов он не нужен,
но полезен для универсальных фабрик, преобразователей и расширений контейнера.
`TypeRef<T>` не является узлом графа: контейнер подставляет его из разрешенного типа запроса, поэтому
его запрос никогда не завершается ошибкой об отсутствующей зависимости.

#### Механизм расширений { #extension-mechanism }

Если ни одна из фабрик не смогла предоставить компонент, `Kora` может попробовать создать эту зависимость во время компиляции самостоятельно.
Для этого предусмотрен механизм расширений. Каждое расширение может сообщить, способно ли оно создать компонент нужного типа.
Если расширение это умеет, оно выполняет необходимую генерацию кода и сообщает, как получить такой компонент.

Например, есть расширения, которые умеют создавать оптимальные компоненты `JsonReader` и `JsonWriter`, репозитории,
декларативные `HTTP`-клиенты, `gRPC`-заглушки, преобразователи конфигурации, валидаторы, а также мапперы `MapStruct` и `Konvert`.
Доступные расширения обнаруживаются через механизм `ServiceLoader` во всех зависимостях, поданных в область обработчика аннотаций.

Этот механизм системного уровня и чаще всего используется внутренними модулями `Kora`.

#### Компонент по умолчанию { #default-factory }

Чтобы фабричные методы предоставляли компоненты по умолчанию, которые пользователь может переопределить,
требуется использовать аннотацию `@DefaultComponent`.
Если во время компиляции контейнер зависимостей найдет компонент того же типа и с теми же тегами, но без `@DefaultComponent`,
при внедрении предпочтение будет отдано пользовательскому компоненту.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        @DefaultComponent
        default SomeService someService() {
            return new SomeService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        @DefaultComponent
        fun someService(): SomeService = SomeService()
    }
    ```

`@DefaultComponent` можно ставить как на фабричный метод, так и на класс с `@Component`.
Кандидат с `@DefaultComponent` также пропускается при сборе [списка компонентов](#list-of-components),
если существует хотя бы один кандидат того же типа без этой аннотации.

#### Явная регистрация { #explicit-registration }

Каждый компонент графа появляется из явного объявления: класса с [`@Component`](#auto-factory),
[фабричного метода](#method-factory) в интерфейсе `@KoraApp` или в подключенном [модуле](#module-factory),
[фабричного модуля](#factory-module), [обобщенной фабрики](#generic-factory) либо [механизма расширений](#extension-mechanism).

`Kora` не создает класс, который нигде не был зарегистрирован. Если класс используется как зависимость, но не
объявлен ни одним из этих способов, компиляция падает с ошибкой `No component found for dependency`, а не молча
конструирует класс. Подробности — в разделе [ошибки сборки графа](#graph-build-errors).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component //(1)!
    public final class SomeService {

        private final OtherService otherService;

        public SomeService(OtherService otherService) {
            this.otherService = otherService;
        }
    }

    @KoraApp
    public interface Application {

        default SomeOtherService someOtherService(SomeService someService) {
            return new SomeOtherService(someService);
        }

        default OtherService otherService() { //(2)!
            return new OtherService();
        }
    }
    ```

    1.  Без `@Component` (или фабричного метода, возвращающего `SomeService`) граф не соберется.
    2.  `OtherService` зарегистрирован фабричным методом, поэтому `SomeService` может быть создан.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component //(1)!
    class SomeService(val otherService: OtherService)

    @KoraApp
    interface Application {

        fun someOtherService(someService: SomeService): SomeOtherService {
            return SomeOtherService(someService)
        }

        fun otherService(): OtherService = OtherService() //(2)!
    }
    ```

    1.  Без `@Component` (или фабричного метода, возвращающего `SomeService`) граф не соберется.
    2.  `OtherService` зарегистрирован фабричным методом, поэтому `SomeService` может быть создан.

Из этого правила есть одно намеренное исключение. Типы, которые `Kora` создает сама — мапперы, преобразователи,
мапперы ключей кэша и подобные контракты, на которые ссылаются через `@Mapping`, — **не должны** помечаться `@Component`,
если у них нет зависимостей в конструкторе: `Kora` уже создает их напрямую, и второе объявление приводит к ошибке
`Multiple components match dependency`. Решает конструктор:

* класс принимает зависимости в конструкторе — он должен быть компонентом графа (`@Component` или фабричный метод)
* у класса нет зависимостей в конструкторе — аннотацию не ставим

### Переопределение компонента { #component-override }

Если компонент предоставляется библиотекой как зависимость по умолчанию,
в приложении можно создать фабрику без аннотации `@DefaultComponent`, и такая зависимость его переопределит.

Поскольку все внешние модули подключаются как интерфейсы к ядру контейнера `@KoraApp` и их фабрики доступны,
их можно просто переопределить как метод и предоставить свою реализацию.
Любые [теги](#tags), объявленные на исходном фабричном методе, необходимо повторить на переопределении,
поскольку именно тег идентифицирует компонент в графе:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface EmailModule {

        final class EmailTag {
            private EmailTag() {}
        }

        @Tag(EmailTag.class)
        @DefaultComponent
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL DEFAULT] ";
        }
    }

    @KoraApp
    public interface Application extends EmailModule {

        @Tag(EmailModule.EmailTag.class)
        @Override
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL OVERRIDDEN] ";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface EmailModule {

        class EmailTag private constructor()

        @Tag(EmailTag::class)
        @DefaultComponent
        fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL DEFAULT] " }
        }
    }

    @KoraApp
    interface Application : EmailModule {

        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

### Корневой компонент { #root-component }

Когда компонент обязан всегда инициализироваться при старте приложения, даже если он не является зависимостью других компонентов,
предполагается использовать аннотацию `@Root` над фабричным методом или классом, помеченным `@Component`.

Примером такого компонента может быть `HTTP`-сервер, потребитель `Kafka`, компонент прогрева кэша или обработчик фоновых задач.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        @Root
        default SomeService someService() {
            return new SomeService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        @Root
        fun someService(): SomeService = SomeService()
    }
    ```

Корни — это точки входа разрешения графа: все, что недостижимо из корня, выбрасывается из контейнера.
Приложение, в котором нет ни одного корня, не компилируется:

```
@KoraApp has no root components.

Fix:
  - Check that modules with @Root components are plugged-in.
  - Annotate at least one component or module method with @Root.
  - Check that root component is visible from this @KoraApp module set.
```

По этой же причине компоненту с [`Lifecycle`](#component-lifecycle), который только подготавливает внешнее состояние
и от которого никто не зависит, нужен `@Root` — иначе он молча исчезнет из графа вместе со всем, что тянул за собой.

### Условные компоненты { #conditional-component }

Компонент можно исключить из контейнера при старте по условию, вычисляемому во время выполнения.
Само условие — это компонент, реализующий `GraphCondition`, зарегистрированный под `@Tag`, который его именует,
а зависящий от него компонент помечается `@Conditional(tag = ...)`.

```java
public interface GraphCondition {

    ConditionResult eval();

    sealed interface ConditionResult {

        record Matched(String reason) implements ConditionResult {}

        record Failed(String reason) implements ConditionResult {}
    }
}
```

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class OnPrimaryNode implements GraphCondition {

        @Override
        public ConditionResult eval() {
            return "primary".equals(System.getenv("NODE_ROLE"))
                    ? ConditionResult.matched("NODE_ROLE is primary")
                    : ConditionResult.failed("NODE_ROLE is not primary");
        }
    }

    @KoraApp
    public interface Application {

        @Tag(OnPrimaryNode.class) //(1)!
        default GraphCondition onPrimaryNode() {
            return new OnPrimaryNode();
        }

        @Root
        @Conditional(tag = OnPrimaryNode.class) //(2)!
        default LeaderElectionJob leaderElectionJob() {
            return new LeaderElectionJob();
        }
    }
    ```

    1.  Условие — обычный компонент типа `GraphCondition`, который опознается по тегу.
    2.  Для тега должен существовать ровно один компонент `GraphCondition`, иначе компиляция падает.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class OnPrimaryNode : GraphCondition {

        override fun eval(): GraphCondition.ConditionResult {
            return if (System.getenv("NODE_ROLE") == "primary") {
                GraphCondition.ConditionResult.matched("NODE_ROLE is primary")
            } else {
                GraphCondition.ConditionResult.failed("NODE_ROLE is not primary")
            }
        }
    }

    @KoraApp
    interface Application {

        @Tag(OnPrimaryNode::class) //(1)!
        fun onPrimaryNode(): GraphCondition = OnPrimaryNode()

        @Root
        @Conditional(tag = OnPrimaryNode::class) //(2)!
        fun leaderElectionJob(): LeaderElectionJob = LeaderElectionJob()
    }
    ```

    1.  Условие — обычный компонент типа `GraphCondition`, который опознается по тегу.
    2.  Для тега должен существовать ровно один компонент `GraphCondition`, иначе компиляция падает.

Условия вычисляются при инициализации графа и заново при каждом его обновлении:

* если условие вернуло `Matched`, компонент создается как обычно
* если условие вернуло `Failed`, узел остается пустым, а чтение бросает `Graph node value was not initialized because condition failed: <reason>`
* [список компонентов](#list-of-components) молча пропускает компоненты, чье условие не выполнилось
* `@Conditional` допустима и на компонентах `@Root` — тогда не создается все поддерево за этим корнем

Когда за одну точку внедрения конкурирует несколько кандидатов одного типа и **все** они условные,
`Kora` не падает во время компиляции: она выберет тот, чье условие выполнилось во время работы.
Если не выполнилось ни одно или выполнилось больше одного, граф не инициализируется.

`GraphCondition` также предоставляет `GraphCondition.and(...)` и `GraphCondition.or(...)` для композиции условий.

### Необязательные зависимости { #optional-dependencies }

===! ":fontawesome-brands-java: `Java`"

    Если требуется ввести необязательную зависимость, которой может не быть,
    следует пометить такой компонент аннотацией `@Nullable` —
    тогда контейнер зависимостей не упадет во время компиляции из-за отсутствия компонента:

    ```java
    @Component
    public final class SomeService {

        private final OtherService otherService;

        public SomeService(@Nullable OtherService otherService) { //(1)!
            this.otherService = otherService;
        }
    }
    ```

    1.  `Kora` распознает любую аннотацию с простым именем `Nullable`; вместе с фреймворком поставляется
        [JSpecify](https://jspecify.dev) `org.jspecify.annotations.Nullable`, доступная транзитивно из ядра.
        Аннотации JSpecify являются **type-use**, поэтому их позиция важна в квалифицированных и обобщенных типах
        (`Outer.@Nullable Inner`, `List<@Nullable String>`).

=== ":simple-kotlin: `Kotlin`"

    Если требуется внедрить необязательную зависимость, которой может не быть, используйте
    [синтаксис null-безопасности `Kotlin`](https://kotlinlang.org/docs/null-safety.html)
    и пометьте такой компонент как допускающий `null` —
    тогда контейнер зависимостей не упадет во время компиляции из-за отсутствия компонента:

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService?)
    ```

Отсутствующую зависимость можно запросить и как `java.util.Optional<T>` — тогда контейнер внедрит пустой
`Optional` вместо того, чтобы упасть. Необязательность комбинируется с обертками контейнера: `ValueOf<Optional<T>>`, `Optional<ValueOf<T>>`,
`PromiseOf<Optional<T>>` и `Optional<PromiseOf<T>>`. Это полезно, когда зависимость может отсутствовать,
но компоненту при этом нужен отложенный доступ или возможность обновить ее через контейнер.

### Список компонентов { #list-of-components }

В контейнере может быть множество экземпляров одного типа, и если требуется собрать их все в одном месте, следует использовать специальный тип `All`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        default HandlerA handlerA() {
            return new HandlerA();
        }

        default HandlerB handlerB() {
            return new HandlerB();
        }

        default SomeProcessor someProcessor(All<Handler> handlers) {
            return new SomeProcessor(handlers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {

        fun handlerA(): HandlerA = HandlerA()

        fun handlerB(): HandlerB = HandlerB()

        fun someProcessor(handlers: All<Handler>): SomeProcessor {
            return SomeProcessor(handlers)
        }
    }
    ```

Например, есть сущность `Handler`, и в контейнере она представлена N разными типами.
`SomeProcessor` при этом потребляет все возможные реализации этого типа.
**Важно**: пример выше берет все экземпляры `Handler` без тегов.

Сам тип `All` имеет следующий контракт:

```java
public sealed interface All<T> extends Iterable<T> { }
```

`All<T>` — это `Iterable<T>`, а не `List<T>`: обходите его циклом `for` или скопируйте в коллекцию, если нужен
произвольный доступ. Если нужно собрать ссылки на компоненты, а не сами компоненты, контейнер также поддерживает
`All<ValueOf<T>>` и `All<PromiseOf<T>>`. Запрос `All<T>` для типа, который никто не предоставляет, ошибкой не является —
коллекция просто будет пустой. `All.of(...)` создает статический экземпляр, что удобно в тестах.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class NotifyRunner {

        private final All<Notifier> notifiers;

        public NotifyRunner(All<Notifier> notifiers) {
            this.notifiers = notifiers;
        }

        public void notifyAll(String user, String message) {
            for (var notifier : notifiers) {
                notifier.notify(user, message);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class NotifyRunner(private val notifiers: All<Notifier>) {

        fun notifyAll(user: String, message: String) {
            for (notifier in notifiers) {
                notifier.notify(user, message)
            }
        }
    }
    ```

### Теги { #tags }

Иногда требуется предоставлять разные экземпляры одного типа разным компонентам. Для этого их можно различать тегами.
Для этого существует аннотация `@Tag`, которая принимает на вход класс-тег.
Ожидается связка, где компонент регистрируется с определенным тегом, а в точке внедрения объявляется ровно тот же тег.

Используется именно класс, а не строковый литерал, потому что по классу проще навигироваться в коде и проще выполнять рефакторинг.

Так можно внедрять разные экземпляры класса с общим интерфейсом в разные точки внедрения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        @Tag(MyTag1.class)
        default SomeService someService1() {
            return new SomeService1();
        }

        @Tag(MyTag2.class)
        default SomeService someService2() {
            return new SomeService2();
        }

        default ServiceA serviceA(@Tag(MyTag1.class) SomeService service) {
            return new ServiceA(service);
        }

        default ServiceB serviceB(@Tag(MyTag2.class) SomeService service) {
            return new ServiceB(service);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {

        @Tag(MyTag1::class)
        fun someService1(): SomeService = SomeService1()

        @Tag(MyTag2::class)
        fun someService2(): SomeService = SomeService2()

        fun serviceA(@Tag(MyTag1::class) service: SomeService): ServiceA {
            return ServiceA(service)
        }

        fun serviceB(@Tag(MyTag2::class) service: SomeService): ServiceB {
            return ServiceB(service)
        }
    }
    ```

Теги над методом говорят, с каким тегом зарегистрировать компонент, а теги в точках внедрения — какой тегированный компонент ожидать.
Теги также работают на классах `@Component` и на параметрах их конструкторов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(MyTag1.class)
    @Component
    public final class SomeService1 implements SomeService { }

    @Tag(MyTag2.class)
    @Component
    public final class SomeService2 implements SomeService { }

    @Component
    public final class ServiceA {

        private final SomeService service;

        public ServiceA(@Tag(MyTag1.class) SomeService service) {
            this.service = service;
        }
    }

    @Component
    public final class ServiceB {

        private final SomeService service;

        public ServiceB(@Tag(MyTag2.class) SomeService service) {
            this.service = service;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeService

    @Tag(MyTag1::class)
    @Component
    class SomeService1 : SomeService

    @Tag(MyTag2::class)
    @Component
    class SomeService2 : SomeService

    @Component
    class ServiceA(@Tag(MyTag1::class) private val service: SomeService)

    @Component
    class ServiceB(@Tag(MyTag2::class) private val service: SomeService)
    ```

В `Kotlin` аннотация ставится на **параметр** конструктора, перед его именем, а не внутрь типа.

#### Пользовательский тег { #tag-custom }

Также можно создавать собственные аннотации-теги и работать с ними. Один из примеров — [аннотация `@Json`](json.md).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(MyTag.class)
    @interface MyTag { }

    public interface SomeModule {

        @MyTag
        default SomeService someService() {
            return new SomeService();
        }

        default OtherService otherService(@MyTag SomeService service) {
            return new OtherService(service);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(MyTag::class)
    annotation class MyTag

    interface SomeModule {

        @MyTag
        fun someService(): SomeService = SomeService()

        fun otherService(@MyTag service: SomeService): OtherService {
            return OtherService(service)
        }
    }
    ```

#### Список по тегу { #tag-all }

Тег также можно использовать, чтобы получить список всех компонентов с определенным тегом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        @Tag(MyTag.class)
        default HandlerA handlerA() {
            return new HandlerA();
        }

        @Tag(MyTag.class)
        default HandlerB handlerB() {
            return new HandlerB();
        }

        default SomeProcessor someProcessor(@Tag(MyTag.class) All<Handler> handlers) {
            return new SomeProcessor(handlers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {

        @Tag(MyTag::class)
        fun handlerA(): HandlerA = HandlerA()

        @Tag(MyTag::class)
        fun handlerB(): HandlerB = HandlerB()

        fun someProcessor(@Tag(MyTag::class) handlers: All<Handler>): SomeProcessor {
            return SomeProcessor(handlers)
        }
    }
    ```

#### Любой тег { #tag-any }

Чтобы получить список всех компонентов и с тегом, и без него, нужно использовать специальный тип тега `@Tag.Any`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        @Tag(MyTag.class)
        default HandlerA handlerA() {
            return new HandlerA();
        }

        default HandlerB handlerB() {
            return new HandlerB();
        }

        default SomeProcessor someProcessor(@Tag(Tag.Any.class) All<Handler> handlers) {
            return new SomeProcessor(handlers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {

        @Tag(MyTag::class)
        fun handlerA(): HandlerA = HandlerA()

        fun handlerB(): HandlerB = HandlerB()

        fun someProcessor(@Tag(Tag.Any::class) handlers: All<Handler>): SomeProcessor {
            return SomeProcessor(handlers)
        }
    }
    ```

`@Tag.Any` имеет смысл только в точке внедрения: он объявляет, что там подойдет любой тег.
Точка внедрения без тега соответствует только компонентам, зарегистрированным без тега.

### Циклические зависимости { #circular-dependencies }

Поскольку `Kora` строит и проверяет весь граф зависимостей во время компиляции, цикл зависимостей
(компонент `A` нуждается в `B`, `B` — в `A`, возможно, через промежуточные компоненты) обнаруживается при компиляции,
а не взрывается во время выполнения. Как именно обрабатывается такой цикл, зависит от того, как объявлена зависимость внутри него.

**Прямая зависимость от `final`-класса (или любого не-интерфейсного типа).**
Такой цикл разрешить нельзя, и компиляция падает. Ошибка называет тип, который замыкает цикл, печатает сам цикл
и предлагает способы выхода:

```
Circular dependency found:
  io.koraframework.example.ServiceA (no tags)

  Dependency cycle:
    @--- component  io.koraframework.example.ServiceB
    ^--- component  io.koraframework.example.ServiceA [CYCLE]

Fix:
  - Break the cycle with ValueOf<T> or PromiseOf<T> where lazy access is valid.
  - Move shared state into a separate component.
  - Do not create dependency cycles in io.koraframework.application.graph.Lifecycle.
```

**Зависимость объявлена через интерфейс (или не-`final`-класс).**
`Kora` разрывает цикл автоматически: для зависимости с интерфейсным типом она генерирует ленивый прокси, реализующий
`io.koraframework.common.PromisedProxy<T>`, и внедряет прокси вместо настоящего компонента. Прокси разрешает
настоящий компонент из графа при первом обращении (и разрешает заново после обновления графа), поэтому оба компонента
могут быть созданы. От разработчика ничего не требуется, но нужно помнить, что проксируемая сторона становится
работоспособной только после полной сборки графа, поэтому вызывать ее из конструктора нельзя.

В примере ниже `ServiceAImpl` и `ServiceBImpl` ссылаются друг на друга через интерфейсы, поэтому цикл разрывается
автоматически сгенерированным `PromisedProxy`, и граф успешно собирается:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface ServiceA { }

    public interface ServiceB { }

    @Component
    public final class ServiceAImpl implements ServiceA {

        public ServiceAImpl(ServiceB serviceB) { }
    }

    @Component
    public final class ServiceBImpl implements ServiceB {

        public ServiceBImpl(ServiceA serviceA) { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface ServiceA

    interface ServiceB

    @Component
    class ServiceAImpl(serviceB: ServiceB) : ServiceA

    @Component
    class ServiceBImpl(serviceA: ServiceA) : ServiceB
    ```

Надежный способ разорвать цикл осознанно — внедрить одну из сторон через [`ValueOf<T>`](#indirect-dependency)
или [`PromiseOf<T>`](#updating-components) вместо прямой зависимости. Это отвязывает потребителя от жизненного цикла
другого компонента, и контейнер перестает считать эту пару жестким циклом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ServiceAImpl implements ServiceA {

        public ServiceAImpl(ValueOf<ServiceB> serviceB) { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ServiceAImpl(serviceB: ValueOf<ServiceB>) : ServiceA
    ```

### Ошибки сборки графа { #graph-build-errors }

Все ошибки графа — это ошибки времени компиляции, привязанные к конкретному элементу исходного кода, который их вызвал.
Каждое сообщение говорит, что не получилось, откуда это потребовалось, и содержит блок `Fix:` с возможными решениями.

**У зависимости нет поставщика.** Сообщение печатает весь путь от корня до отсутствующего запроса:

```
No component found for dependency:
  io.koraframework.example.PetRepository (no tags)

Required at:
  io.koraframework.example.Application#petService(io.koraframework.example.PetRepository)
  parameter: io.koraframework.example.PetRepository repository

Dependency resolution path:
  ^--- factory  io.koraframework.example.Application#petController(...)
  ^--- factory  io.koraframework.example.Application#petService(...)
  ^--- io.koraframework.example.PetRepository    [MISSING]

Fix:
  - Add @Component to an implementation of io.koraframework.example.PetRepository.
  - Add a module method that returns io.koraframework.example.PetRepository.
  - Include a module that provides io.koraframework.example.PetRepository in @KoraApp.
```

В сообщении могут появиться два дополнительных блока:

* блок `Note:` со списком компонентов того же типа, зарегистрированных с **другим** тегом — обычный признак забытого или перепутанного `@Tag`
* блок `Hint:` для хорошо известных типов, например с советом пометить модель `@Json`, когда не хватает `JsonWriter`

**Одной точке внедрения соответствует несколько поставщиков.** Кандидаты перечисляются вместе с фабрикой или компонентом, который их объявил:

```
Multiple components match dependency:
  io.koraframework.example.PetService (no tags)

Required at:
  petController(io.koraframework.example.PetService)
  parameter: io.koraframework.example.PetService petService

  Candidates:
  - factory  io.koraframework.example.Application#petServicePrimary()
  - factory  io.koraframework.example.Application#petServiceSecondary()

Fix:
  - Add different @Tag(...) annotations to candidates and request the needed tag.
  - Mark fallback candidate with @DefaultComponent.
  - Remove one duplicate provider.
```

**Другие частые ошибки сборки:**

* `@KoraApp has no root components.` — ни один элемент графа не помечен [`@Root`](#root-component)
* `Circular dependency found:` — смотрите [циклические зависимости](#circular-dependencies)
* `Component condition cannot be resolved:` — для тега [`@Conditional`](#conditional-component) нет компонента `GraphCondition`
* `@Component class must have exactly one public constructor.` — смотрите [автоматическую фабрику](#auto-factory)
* `Kora submodule was not generated yet:` — модуль с [`@KoraSubmodule`](#submodule-factory) собран без обработчика аннотаций `Kora`

## Время выполнения { #runtime }

Контейнер зависимостей использует максимально возможный параллелизм в рамках построенного графа.
Каждый узел создается, инициализируется и освобождается в собственном виртуальном потоке, в порядке зависимостей.

Во время работы приложения контейнер делает следующее:

* Инициализирует все компоненты контейнера зависимостей
* Отслеживает изменения в контейнере зависимостей
* Атомарно обновляет контейнер зависимостей при изменениях
* Выполняет [плавную остановку](#graceful-shutdown) при получении сигнала `SIGTERM`

Все компоненты используют жадную инициализацию, то есть инициализируются сразу при запуске приложения.

### Точка входа { #entrypoint }

Точка входа приложения должна вызывать `KoraApplication.run`, используя контейнер зависимостей, созданный во время компиляции.

Если интерфейс, помеченный `@KoraApp`, называется `Application`, то при компиляции в том же пакете будет сгенерирован класс
`ApplicationGraph`. Он реализует `Supplier<ApplicationGraphDraw>` и предоставляет статический метод `graph()`,
поэтому точка входа в том же пакете будет выглядеть так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Сигнатура `KoraApplication.run` — `public static void run(Supplier<ApplicationGraphDraw> supplier)`.
Метод строит граф, логирует длительность инициализации, регистрирует shutdown-hook, освобождающий граф,
и затем блокирует вызывающий поток до остановки. Если инициализация упала, ошибка логируется, а JVM завершается с кодом `-1`.

Если нужен сам объект графа — в тестах или в продвинутых сценариях, где компонент достают вручную или инициируют обновление, —
вызовите `ApplicationGraph.graph().init()`, который возвращает `InitializedGraph` (это `RefreshableGraph` с методами
`init()` и `release()`).

### Жизненный цикл контейнера { #container-lifecycle }

Контейнер зависимостей умеет инициализировать все компоненты в правильном порядке и делает это максимально параллельно, чтобы добиться наиболее быстрого старта.

Когда контейнер больше не нужен, он запускает механизм освобождения компонентов в обратном порядке.

В середине жизненного цикла компонент может быть обновлен, и тогда контейнер обновляет все компоненты,
которые зависят от изменившегося. Это происходит атомарно: контейнер собирает затронутую часть графа
во временную копию, и только когда все компоненты в ней успешно инициализированы, подменяет ее и освобождает
замененные объекты. Если хотя бы один компонент упал, временные объекты освобождаются, а старый граф остается на месте.

### Жизненный цикл компонента { #component-lifecycle }

По умолчанию все компоненты создаются как синглтоны через конструктор или фабричный метод во время инициализации.
Если нужно выполнить какие-то действия при инициализации компонента или перед его освобождением, следует реализовать интерфейс `Lifecycle`:

```java
public interface Lifecycle {

    void init() throws Exception;

    void release() throws Exception;
}
```

В контейнере зависимостей все компоненты инициализируются параллельно настолько, насколько это позволяет граф,
каждый в собственном виртуальном потоке.

Если нужно предоставить компонент с жизненным циклом из фабричного метода, можно использовать класс `LifecycleWrapper`.
Он реализует сразу два контракта:

* `Lifecycle` — контейнер вызовет `init()` при запуске и `release()` при освобождении компонента
* `Wrapped<T>` — контейнер внедрит значение `T`, которое возвращает метод `value()`

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        default Wrapped<SomeService> someService() {
            return new LifecycleWrapper<>(new SomeService(),
                    (component) -> {
                        // initialize logic
                    },
                    (component) -> {
                        // release logic
                    });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun someService(): Wrapped<SomeService> {
            return LifecycleWrapper(SomeService(),
                { component ->
                    // initialize logic
                },
                { component ->
                    // release logic
                }
            )
        }
    }
    ```

Если нужно вернуть собственную обертку, она должна реализовывать `Wrapped<T>`:

```java
public interface Wrapped<T> {

    T value();
}
```

Компонент, предоставленный как `Wrapped<T>`, можно внедрять и как `T` (контейнер его разворачивает), и как сам `Wrapped<T>`,
в том числе через обертки `ValueOf`, `PromiseOf` и `All`.

### Плавная остановка { #graceful-shutdown }

Все интеграции, которые предоставляет `Kora`, такие как [HTTP-сервер](http-server.md) и [потребитель Kafka](kafka.md),
поддерживают [плавную остановку](https://www.techtarget.com/whatis/definition/graceful-shutdown-and-hard-shutdown) из коробки за счет
[жизненного цикла компонента](#component-lifecycle).

Компоненты освобождаются в порядке, обратном порядку зависимостей. Для каждого компонента контейнер сначала выполняет
`beforeRelease` у [перехватчиков графа](#component-inspection), затем `Lifecycle.release()` и в конце `AutoCloseable.close()`,
так что компонент, реализующий `AutoCloseable`, закрывается автоматически даже без реализации `Lifecycle`.

### Косвенная зависимость { #indirect-dependency }

Рассмотрим следующий пример:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        default ServiceA serviceA() {
            return new ServiceA();
        }

        default ServiceB serviceB() {
            return new ServiceB();
        }

        default ServiceC serviceC(ServiceA serviceA, ValueOf<ServiceB> serviceB) {
            return new ServiceC(serviceA, serviceB);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {
        fun serviceA(): ServiceA = ServiceA()

        fun serviceB(): ServiceB = ServiceB()

        fun serviceC(serviceA: ServiceA, serviceB: ValueOf<ServiceB>): ServiceC {
            return ServiceC(serviceA, serviceB)
        }
    }
    ```

Есть два сервиса и третий сервис, который от них зависит. Но есть разница в жизненном цикле.
Если взять тип как зависимость напрямую, мы сообщаем контейнеру, что при обновлении компонента `ServiceA` точно так же нужно обновить компонент `ServiceC`.
А когда используется обертка `ValueOf`, мы сообщаем контейнеру,
что `ServiceC` не связан с жизненным циклом `ServiceB`, и если `ServiceB` изменится, `ServiceC` обновлять не нужно.

#### Обновление компонентов { #updating-components }

Обертка `ValueOf` дает компоненту «живую» ссылку на другой компонент вместо зафиксированного экземпляра:

```java
public interface ValueOf<T> {

    T get();
}
```

Метод `get()` возвращает текущее состояние компонента в контейнере.
Этот механизм используется в компонентах, которые нельзя перезагрузить во время работы приложения.
Например, это относится к серверам, слушающим сокеты (`HTTP`, `gRPC`): обработчики запросов, которые могут меняться,
передаются им через `ValueOf`.

У `ValueOf` также есть дополнительные методы для удобной работы с обернутым значением:

* `map(...)` — преобразует значение внутри `ValueOf`, не разрывая связь с исходным компонентом
* `optional()` — превращает `ValueOf<T>` в `ValueOf<Optional<T>>`

Само обновление инициируется через граф — передачей `Node<T>` изменившегося компонента:

```java
public interface RefreshableGraph extends Graph {

    void refresh(Node<?> fromNode);
}
```

Все, что зависит от этого узла **напрямую**, пересоздается; все, что связано с ним только через
`ValueOf` или `PromiseOf`, сохраняет свой экземпляр и просто видит новое значение.
Именно так работает встроенный наблюдатель за файлом конфигурации: он внедряет `RefreshableGraph` вместе с
`Node<ConfigOrigin>` конфигурации приложения и вызывает `graph.refresh(node)`, когда файл на диске изменился.

Если компоненту нужна отложенная ссылка, он может использовать `PromiseOf<T>`.
Метод `get()` возвращает `Optional<T>`: до сборки графа он пуст, а после сборки получает текущий компонент из контейнера.

```java
public interface PromiseOf<T> {

    Optional<T> get();
}
```

Как и `ValueOf`, `PromiseOf` поддерживает `map(...)` и `optional()`.
Большинству прикладного кода достаточно прямой зависимости или `ValueOf`; `PromiseOf` предназначен для низкоуровневых сценариев,
где компоненту нужен отложенный доступ к другой части графа.

Если компонент, полученный как `ValueOf<Wrapped<T>>`, нужно передать дальше как обычный `ValueOf<T>`,
можно использовать `Wrapped.unwrap(...)`. Это полезно для оберток, которые добавляют жизненный цикл или другое поведение,
но наружу должны отдавать обычное значение.

#### Слушатели обновления { #refresh-listener }

Если компоненту нужно знать, что граф был успешно обновлен, он может реализовать `RefreshListener`:

```java
public interface RefreshListener {

    void graphRefreshed() throws Exception;
}
```

Контейнер вызывает `graphRefreshed()` после успешного обновления графа. Если компонент является одновременно оберткой значения и слушателем обновления,
он может реализовать комбинированный интерфейс `WrappedRefreshListener<T>`.

`RefreshListener` нужен только для получения уведомления после завершения обновления. Он не требуется для того, чтобы контейнер
пересоздал компонент. Если обновление затрагивает компонент или его зависимости, а другие компоненты внедрили его напрямую,
без `ValueOf` или `PromiseOf`, эти зависимые компоненты также будут обновлены автоматически.

### Доступ к графу { #graph-access }

Инфраструктурным компонентам иногда нужен сам контейнер, а не конкретная зависимость.
Для этого можно внедрить три типа:

* `Graph` — доступ только на чтение: `get(Node<T>)`, `valueOf(Node<T>)`, `promiseOf(Node<T>)`
* `RefreshableGraph` — то же самое плюс `refresh(Node<?>)`
* `Node<T>` — дескриптор конкретного компонента в графе, разрешаемый по типу и тегу так же, как обычная зависимость

`Graph` и `RefreshableGraph` сами компонентами не являются: контейнер подставляет самого себя, поэтому их запрос
не добавляет узел и не может завершиться ошибкой. `Node<T>`, наоборот, разрешает реальный компонент и подтягивает его в граф.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class ConfigReloader implements Lifecycle {

        private final RefreshableGraph graph;
        private final Node<AppConfig> configNode;

        public ConfigReloader(RefreshableGraph graph, Node<AppConfig> configNode) {
            this.graph = graph;
            this.configNode = configNode;
        }

        public void reload() {
            graph.refresh(configNode);
        }

        @Override
        public void init() { }

        @Override
        public void release() { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class ConfigReloader(
        private val graph: RefreshableGraph,
        private val configNode: Node<AppConfig>
    ) : Lifecycle {

        fun reload() {
            graph.refresh(configNode)
        }

        override fun init() { }

        override fun release() { }
    }
    ```

`Node<T>` нельзя запросить для nullable-типа; если нужен доступ, допускающий `null`, внедряйте зависимость напрямую.

### Перехват компонента { #component-inspection }

Бывают ситуации, когда компонент в контейнере нужно дополнительно изменить или инициализировать,
но никто не должен начать работать с этим компонентом до завершения этих действий.
Для этого случая существует механизм перехвата компонентов. Поместите в контейнер объект, реализующий интерфейс `GraphInterceptor`.

```java
public interface GraphInterceptor<T> {

    T afterInit(T value);

    T beforeRelease(T value);
}
```

Например, этот механизм можно использовать для прогрева кэша на основе `JdbcDataSource`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CacheWarmupInterceptor implements GraphInterceptor<JdbcDataSource> {

        @Override
        public JdbcDataSource afterInit(JdbcDataSource value) {
            // warm up cache
            return value;
        }

        @Override
        public JdbcDataSource beforeRelease(JdbcDataSource value) {
            return value;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CacheWarmupInterceptor : GraphInterceptor<JdbcDataSource> {

        override fun afterInit(value: JdbcDataSource): JdbcDataSource {
            // warm up cache
            return value
        }

        override fun beforeRelease(value: JdbcDataSource): JdbcDataSource {
            return value
        }
    }
    ```

Перехватчик — это обычный компонент: его можно объявить через `@Component` или фабричным методом,
и у него могут быть собственные зависимости.

Интерфейс `GraphInterceptor` почти совпадает с контрактом `Lifecycle`, за исключением возвращаемого типа.
Метод `afterInit(T value)` вызывается после того, как компонент создан и его собственный `Lifecycle.init()` завершился.
Метод может вернуть измененный или совершенно другой
экземпляр указанного типа, и именно этот объект будет использоваться другими компонентами как зависимость.
Метод `beforeRelease(T value)` получает компонент перед освобождением, то есть это все еще рабочий и еще не очищенный экземпляр,
и он выполняется до `Lifecycle.release()` и `AutoCloseable.close()`.

Перехватчик привязывается к компоненту по **точному** объявленному типу этого компонента — `GraphInterceptor<JdbcDataSource>`
перехватывает компонент, объявленный как `JdbcDataSource`, а не его подтипы — и по тегу: перехватчик без тега перехватывает
компоненты без тега, а `@Tag(Tag.Any.class)` на перехватчике заставляет его перехватывать компоненты с любым тегом.
