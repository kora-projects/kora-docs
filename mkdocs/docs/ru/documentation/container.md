---
description: "Explains Kora compile-time dependency injection container, components, modules, factories, tags, lifecycle, graph resolution, and dependency wrappers. Use when working with @KoraApp, @Component, @Module, @KoraSubmodule, @Root, @Tag, @DefaultComponent, ValueOf."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora compile-time dependency injection container, components, modules, factories, tags, lifecycle, graph resolution, and dependency wrappers; key triggers include @KoraApp, @Component, @Module, @KoraSubmodule, @Root, @Tag, @DefaultComponent, ValueOf, All, PromiseOf."
---

Контейнер зависимостей — это ядро фреймворка `Kora`. Он строит граф зависимостей, проверяет его,
внедряет компоненты, инициализирует их и позднее освобождает.
В отличие от контейнеров, которые собирают приложение при запуске путем сканирования classpath, `Kora` строит большую часть графа
во время компиляции и генерирует обычный `Java`-код для запуска приложения.

Работа контейнера в `Kora` разделена на две части: время компиляции и время выполнения.
Во время компиляции `Kora` проверяет, что все зависимости могут быть найдены и связаны. Во время выполнения контейнер создает
компоненты, управляет их жизненным циклом и обновляет затронутые части графа при возникновении изменений.

Пошаговый разбор перед справочным описанием смотрите в разделах [Введение во внедрение зависимостей](../guides/dependency-injection-introduction.md) и [Внедрение зависимостей](../guides/dependency-injection.md).

## Время компиляции { #compile-time }

Во время компиляции компоненты обнаруживаются, чтобы построить контейнер зависимостей для всего приложения.
Это позволяет проверить контейнер зависимостей до фактического запуска приложения.

### Контейнер { #container }

Ядром контейнера зависимостей является интерфейс, помеченный аннотацией `@KoraApp`.
Эту аннотацию следует использовать на интерфейсе, который содержит фабричные методы для создания компонентов
и подключает [внешние модули](#external-module-factory).
В приложении может быть только один такой интерфейс.

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

    * Класс не должен быть абстрактным
    * У класса должен быть только один публичный конструктор
    * Класс должен быть `final` (только если у него нет аспектов)
    
    ```java
    @Component
    public final class SomeService {

        private OtherService otherService;

        public SomeService(OtherService otherService) {
            this.otherService = otherService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    * Класс не должен быть абстрактным
    * У класса должен быть только один публичный конструктор
    * Класс не должен быть `open` (только если у него нет аспектов)

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService) { }
    ```

#### Фабрика через метод { #basic-factory }

Фабричный метод — это метод с модификатором `default`, который возвращает компонент.
Метод может принимать другие компоненты-зависимости в качестве аргументов.

Контейнер зависимостей ниже описывает две фабрики, где фабрика `otherService` требует компонент, созданный фабрикой `someService`.
Это самый базовый способ, которым компоненты могут быть зарегистрированы в контейнере:

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

Фабричный метод **не должен предоставлять** значение `null` в качестве компонента.

#### Фабрика через модуль { #module-factory }

Компоненты для контейнера зависимостей также могут располагаться в модулях внутри проекта приложения.
Модуль — это интерфейс, который содержит фабричные методы.
Аннотация `@Module` помечает интерфейс как модуль, который должен быть внедрен в контейнер приложения во время компиляции.
Модуль должен находиться в той же директории исходного кода, что и класс, помеченный `@KoraApp`.

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

#### Фабрика через внешний модуль { #external-module-factory }

Компоненты для контейнера зависимостей также могут быть найдены во внешних модулях из сторонних зависимостей.
Модуль — это интерфейс, который содержит фабричные методы.
`Kora` не выполняет автоматический поиск модулей из внешних зависимостей, как это делают некоторые другие DI-решения.
Это позволяет разработчику точно контролировать, какие зависимости используются в приложении, и избегать
инициализации ненужных компонентов.

Все необходимые внешние модули из зависимостей должны быть подключены явно в интерфейсе, помеченном аннотацией `@KoraApp`, через наследование:

Такой модуль может быть объявлен в любом интерфейсе: в сторонней библиотеке, в отдельном модуле проекта или рядом с самим `@KoraApp`.
Важно то, что интерфейс `@KoraApp` явно подключает его через наследование.

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

#### Фабрика через подмодуль { #submodule-factory }

Аннотация `@KoraSubmodule` помечает интерфейс, для которого должен быть построен модуль в рамках текущего модуля компиляции.
Он будет содержать все компоненты, помеченные аннотациями `@Module` и `@Component`.
Эта аннотация полезна, когда вы разбиваете проект на [многомодульное приложение](https://docs.gradle.org/current/userguide/multi_project_builds.html)
с точки зрения инструмента сборки `Gradle`, где каждый модуль отвечает за свою часть функциональности,
а приложение с `@KoraApp` собирается в отдельном модуле компиляции.
Такой подход помогает структурировать большой проект по доменным областям и улучшить время сборки:
изменения в одном модуле проекта не заставляют обработчик аннотаций заново анализировать весь код приложения.

Для интерфейса будет сгенерирован интерфейс-наследник. Он унаследует все интерфейсы, помеченные `@Module`,
и создаст фабричные методы для классов, помеченных как `@Component`.

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

И есть основной модуль приложения с точкой сборки для всего приложения:

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

Это подключит модуль `SomeModule`, найденный через `SomeSubModule`, к итоговому контейнеру приложения.

Распространенный практический сценарий использования `@KoraSubmodule` — это отдельный модуль `Gradle`, который владеет одной доменной областью и просто
агрегирует нужные ему [внешние модули](#external-module-factory) (базы данных, кэши и так далее) путем их наследования,
вместе со своими собственными классами `@Component` и интерфейсами `@Module`. Модуль приложения затем подключает
сгенерированные подмодули так же, как подключает любой другой модуль:

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

#### Обобщенная фабрика { #generic-factory }

Если контейнер зависимостей не смог найти фабрику для конкретного типа, контейнер `Kora` может попытаться найти
методы с обобщенными параметрами во время компиляции и использовать такой метод для создания экземпляра требуемого класса.

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

Теперь, если какому-либо компоненту нужен `GenericValidator` в качестве зависимости, для его создания будет использована эта фабрика.

##### Информация об обобщенном типе { #type-ref }

Если фабричному методу нужно знать точный обобщенный тип, запрашиваемый контейнером в данный момент, он может внедрить `TypeRef<T>`.
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

`TypeRef<T>` переносит информацию об обобщенном типе через стирание типов в `Java`. Большинству компонентов приложения он не нужен,
но он полезен для универсальных фабрик, мапперов и расширений контейнера.

#### Механизм расширений { #extension-mechanism }

Если ни одна из фабрик не смогла предоставить компонент, `Kora` может попытаться создать эту зависимость самостоятельно во время компиляции.
Для этого предоставляется механизм расширений. Каждое расширение способно сообщить, может ли оно создать компонент требуемого типа.
Если расширение может это сделать, оно выполняет необходимую генерацию кода и сообщает, как получить этот компонент.

Например, существуют расширения, которые умеют создавать оптимальные компоненты `JsonReader` и `JsonWriter`, репозитории и другие компоненты.
Доступные расширения обнаруживаются через механизм `ServiceLocator` из всех зависимостей, предоставленных в области видимости обработчика аннотаций.

Этот механизм является системным и чаще всего используется внутренними модулями `Kora`.

#### Стандартная фабрика { #standard-factory }

Чтобы предоставить компоненты по умолчанию через фабричные методы, которые, как предполагается, пользователь может переопределить,
требуется использовать аннотацию `@DefaultComponent`.
Если контейнер зависимостей находит во время компиляции любой компонент того же типа и с теми же тегами, но без `@DefaultComponent`,
то при внедрении будет предпочтен пользовательский компонент.

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

#### Автоматическое создание { #auto-creation }

Если ни один из вышеперечисленных методов не смог предоставить компонент,
то `Kora` может попытаться создать компонент самостоятельно, если он удовлетворяет требованиям, аналогичным [автоматической фабрике](#auto-factory):

===! ":fontawesome-brands-java: `Java`"

    * Класс не должен быть абстрактным
    * У класса должен быть только один публичный конструктор
    * Класс должен быть `final` (только если у него нет аспектов)

    ```java
    public final class SomeService {

        private OtherService otherService;

        public SomeService(OtherService otherService) {
            this.otherService = otherService;
        }
    }

    @KoraApp
    public interface Application {

        default SomeOtherService someOtherService(SomeService someService) {
            return new SomeOtherService(someService);
        }

        default OtherService otherService() {
            return new OtherService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    * Класс не должен быть абстрактным
    * У класса должен быть только один публичный конструктор
    * Класс не должен быть `open` (только если у него нет аспектов)

    ```kotlin
    class SomeService(val otherService: OtherService) { }

    @KoraApp
    interface Application {

        fun someOtherService(someService: SomeService): SomeOtherService {
            return SomeOtherService(someService)
        }

        fun otherService(): OtherService = OtherService()
    }
    ```

### Переопределение компонента { #component-override }

В случае, если компонент предоставляется библиотекой как зависимость по умолчанию,
можно создать фабрику в приложении без аннотации `@DefaultComponent`, и такая зависимость переопределит его.

Поскольку все внешние модули подключаются как интерфейсы к ядру контейнера `@KoraApp` и их фабрики доступны,
вы можете просто переопределить их как метод и предоставить свою собственную реализацию.

### Корневой компонент { #root-component }

Когда требуется, чтобы компонент всегда инициализировался при запуске приложения, даже если он не является зависимостью других компонентов,
предполагается использовать аннотацию `@Root` над фабричным методом или классом, помеченным `@Component`.

Примером такого компонента может быть `HTTP`-сервер, потребитель `Kafka`, компонент прогрева кэша или обработчик выполняемой фоновой задачи.

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

### Необязательные зависимости { #optional-dependencies }

===! ":fontawesome-brands-java: `Java`"

    Если вы хотите ввести необязательную зависимость, которой может не существовать, то
    предполагается пометить такой компонент любой аннотацией `@Nullable`,
    тогда контейнер зависимостей не завершится с ошибкой во время компиляции из-за отсутствия компонента:

    ```java
    @Component
    public final class SomeService {

        private OtherService otherService;

        public SomeService(@Nullable OtherService otherService) { //(1)!
            this.otherService = otherService;
        }
    }
    ```

    1.  Подойдет любая аннотация `@Nullable`, например `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Если вы хотите внедрить необязательную зависимость, которая может отсутствовать, используйте [синтаксис null-безопасности `Kotlin`](https://kotlinlang.org/docs/null-safety.html)
    и пометьте этот компонент как допускающий `null`,
    тогда контейнер зависимостей не завершится с ошибкой во время компиляции из-за отсутствия компонента:

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService?) { }
    ```

Необязательность можно комбинировать с обертками контейнера: `ValueOf<Optional<T>>`, `Optional<ValueOf<T>>`,
`PromiseOf<Optional<T>>` и `Optional<PromiseOf<T>>`. Это полезно, когда зависимость может отсутствовать,
но компоненту при этом все равно нужен отложенный доступ или возможность обновить ее через контейнер.

### Список компонентов { #list-of-components }

В контейнере может быть много экземпляров одного и того же типа, и если вы хотите собрать их все в одном месте, следует использовать специальный тип `All`.

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

Например, у нас есть некоторая сущность `Handler`, и она внедряется N различными типами в контейнере.
`SomeProcessor` при этом потребляет все возможные реализации этого типа.
**Важно**: пример выше берет все экземпляры `Handler` без тегов.

Сам тип `All` имеет следующий контракт:

```java
public sealed interface All<T> extends List<T> permits AllImpl {}
```

Это токен-тип, который расширяет `List` и может быть передан в конструкторы, ожидающие `List`.
Если вам нужно собрать ссылки на компоненты вместо самих компонентов, контейнер также поддерживает
`All<ValueOf<T>>` и `All<PromiseOf<T>>`.

### Теги { #tags }

Иногда возникает необходимость предоставить разные экземпляры одного и того же типа разным компонентам. Для этой цели их можно различать по тегам.
Для этого существует аннотация `@Tag`, которая принимает на вход класс тега.
Ожидается сопоставление, при котором компонент регистрируется с определенным тегом, а в точке внедрения объявляется с точно таким же тегом.

Используется именно класс, а не строковый литерал, потому что так проще ориентироваться в коде и проще выполнять рефакторинг.

Вот как можно внедрять разные экземпляры класса с общим интерфейсом в разные точки внедрения:

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

        default ServiceC serviceA(@Tag(MyTag1.class) SomeService service) {
            return new ServiceA(service);
        }

        default ServiceD serviceB(@Tag(MyTag2.class) SomeService service) {
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

Теги над методом сообщают, с каким тегом зарегистрировать компонент, а теги в точках внедрения сообщают, какой помеченный тегом компонент ожидать.
Теги также работают на параметрах конструктора, в сочетании с `@Component` или финальными классами.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(MyTag1.class)
    class SomeService1 implements SomeService {

    }

    @Tag(MyTag2.class)
    final class SomeService2 implements SomeService {

    }

    final class ServiceA {

        private final SomeService service;

        public ServiceA(@Tag(MyTag1.class) SomeService service) {
            this.service = service;
        }
    }

    final class ServiceB {

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
    class SomeService1 : SomeService

    @Tag(MyTag2::class)
    class SomeService2 : SomeService

    class ServiceA(private val service: @Tag(MyTag1::class) SomeService)

    class ServiceB(private val service: @Tag(MyTag2::class) SomeService)
    ```

#### Собственный тег { #tag-custom }

Вы также можете создавать свои собственные аннотации-теги и работать с ними. Одним из примеров является [аннотация `@Json`](json.md).

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

#### Все по тегу { #tag-all }

Вы также можете использовать тег, чтобы получить список всех компонентов по определенному тегу:

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

Чтобы получить список всех компонентов с тегом и без него, нужно использовать специальный тип тега `@Tag.Any`:

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

### Циклические зависимости { #circular-dependencies }

Поскольку `Kora` строит и проверяет весь граф зависимостей во время компиляции, цикл зависимостей
(компоненту `A` нужен `B`, компоненту `B` нужен `A`, возможно, через несколько компонентов между ними) обнаруживается во время компиляции,
а не приводит к сбою во время выполнения. То, как обрабатывается такой цикл, зависит от того, как объявлена зависимость внутри цикла.

**Прямая зависимость от `final`-класса (или любого не-интерфейсного типа).**
Такой цикл не может быть разрешен, и компиляция завершается ошибкой. Ошибка указывает на тип, который замыкает цикл, и перечисляет
кандидатов цикла:

```
Encountered circular dependency in graph for source type: ru.tinkoff.kora.example.ServiceA (no tags)
  Cycle dependency candidates:
  - ru.tinkoff.kora.example.ServiceA
  - ru.tinkoff.kora.example.ServiceB
Please check that you are not using cycle dependency in ru.tinkoff.kora.application.graph.Lifecycle, this is forbidden.
```

**Зависимость, объявленная через интерфейс (или не-`final`-класс).**
`Kora` разрывает цикл автоматически: для зависимости с типом-интерфейсом она генерирует ленивый прокси, реализующий
`ru.tinkoff.kora.common.PromisedProxy<T>`, и внедряет прокси вместо реального компонента. Прокси разрешает
фактический компонент из графа при первом обращении (и повторно разрешает его после обновления графа), так что оба компонента могут быть
сконструированы. От разработчика никаких действий не требуется, но имейте в виду, что проксируемая сторона становится пригодной к использованию только после
того, как граф полностью связан, поэтому ее нельзя вызывать из конструктора.

В примере ниже `ServiceAImpl` и `ServiceBImpl` ссылаются друг на друга через интерфейсы, поэтому цикл разрывается
автоматически сгенерированным `PromisedProxy`, и граф разрешается успешно:

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

Надежный способ намеренно разорвать цикл — внедрить одну из сторон через [`ValueOf<T>`](#indirect-dependency)
или [`PromiseOf<T>`](#updating-components) вместо прямой зависимости. Это отвязывает потребителя от жизненного цикла другого
компонента, поэтому контейнер больше не рассматривает эти два компонента как жесткий цикл:

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

## Время выполнения { #runtime }

Контейнер зависимостей использует максимально возможный параллелизм в рамках построенного графа.

Во время выполнения приложения контейнер делает следующее:

* Инициализирует все компоненты в контейнере зависимостей
* Отслеживает изменения в контейнере зависимостей
* Атомарно обновляет контейнер зависимостей при внесении изменений
* Выполняет [штатное завершение](#graceful-shutdown) при получении сигнала `SIGTERM`

Все компоненты используют энергичную инициализацию, что означает, что они инициализируются сразу при запуске приложения.

### Точка входа { #entrypoint }

Точка входа приложения должна вызывать `KoraApplication.run`, используя контейнер зависимостей, созданный во время компиляции.

Если интерфейс, помеченный `@KoraApp`, называется `Application`, то во время компиляции в том же пакете будет сгенерирован класс с именем `ApplicationGraph`.
Он представляет собой реализацию контейнера зависимостей, а точка входа
в том же пакете будет выглядеть так:

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
        KoraApplication.run { ApplicationGraph.graph() }
    }
    ```

`KoraApplication.run` запускает контейнер и возвращает `RefreshableGraph` (`Graph` в сочетании с [`Lifecycle`](#component-lifecycle)).
Для работающего приложения вы обычно не взаимодействуете с ним напрямую, но он полезен в тестах и продвинутых сценариях, где
нужно найти компонент в графе или вручную инициировать обновление.

### Жизненный цикл контейнера { #container-lifecycle }

Контейнер зависимостей умеет инициализировать все компоненты в правильном порядке и делает это максимально параллельно, чтобы достичь максимально быстрого времени запуска.

Когда контейнер больше не нужен, он запускает механизм освобождения компонентов в обратном порядке.

В середине жизненного цикла компонент может быть обновлен, и тогда контейнер обновляет все компоненты,
которые зависят от измененного компонента. Это происходит атомарно: в начале процесса открывается транзакция,
которая закрывается только если все компоненты успешно инициализированы, и откатывается, если возникает хотя бы одна ошибка.

### Жизненный цикл компонента { #component-lifecycle }

По умолчанию все компоненты создаются как синглтоны через конструктор или фабричный метод во время инициализации.
Если вам нужно выполнить какие-либо действия при инициализации компонента или перед его освобождением, вы должны реализовать интерфейс `Lifecycle`:

```java
public interface Lifecycle {
    
    void init() throws Exception;

    void release() throws Exception;
}
```

В контейнере зависимостей все компоненты инициализируются асинхронно и максимально параллельно.

Если вам нужно предоставить компонент с жизненным циклом из фабричного метода, вы можете использовать класс `LifecycleWrapper`.
Он реализует сразу два контракта:

* `Lifecycle` — контейнер вызовет `init()` при запуске и `release()` при освобождении компонента
* `Wrapped<T>` — контейнер внедрит значение `T`, возвращаемое методом `value()`

===! ":fontawesome-brands-java: `Java`"

    ```java
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

Если вам нужно вернуть собственную обертку, она должна реализовывать `Wrapped<T>`:

```java
public interface Wrapped<T> {

    T value();
}
```

### Штатное завершение { #graceful-shutdown }

Все интеграции, которые предоставляет `Kora`, такие как [HTTP-сервер](http-server.md) и [потребитель Kafka](kafka.md),
поддерживают [штатное завершение](https://www.techtarget.com/whatis/definition/graceful-shutdown-and-hard-shutdown) из коробки, используя
[жизненный цикл компонента](#component-lifecycle).

Все компоненты, которые реализуют `AutoCloseable`, также будут автоматически закрыты контейнером зависимостей перед освобождением.

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

У нас есть два сервиса и третий сервис, который зависит от них. Но есть разница в жизненном цикле.
Если мы берем тип как зависимость напрямую, то мы сообщаем контейнеру, что при обновлении компонента `ServiceA` нам нужно точно так же обновить компонент `ServiceC`.
Но когда мы используем обертку типа `ValueOf`, мы сообщаем контейнеру,
что `ServiceC` не связан с жизненным циклом `ServiceB`, и если `ServiceB` изменяется, то `ServiceC` обновлять не нужно.

#### Обновление компонентов { #updating-components }

Обновление компонента возможно, если для внедрения зависимости используется обертка `ValueOf`:

```java
public interface ValueOf<T> {
    
    T get();

    void refresh();
}
```

Метод `get()` возвращает текущее состояние компонента в контейнере.
Этот механизм используется в компонентах, которые не могут быть перезагружены во время работы приложения.
Например, это касается различных серверов, которые слушают сокеты (`HTTP`, `gRPC`): обработчики запросов, которые могут изменяться,
поставляются им через `ValueOf`.

С помощью метода `refresh()` вы можете инициировать обновление компонента. Этот механизм используется, например, компонентом,
который отслеживает изменения файла конфигурации на диске.
Когда содержимое файла изменяется, он инициирует обновление компонента конфигурации, и затем все изменения распространяются
по цепочке компонентов, связанных прямыми зависимостями.

`ValueOf` также имеет дополнительные методы для удобной работы с обернутым значением:

* `map(...)` — преобразует значение внутри `ValueOf` без изменения связи с исходным компонентом
* `optional()` — преобразует `ValueOf<T>` в `ValueOf<Optional<T>>`

Если компоненту нужна отложенная ссылка, он может использовать `PromiseOf<T>`.
Метод `get()` возвращает `Optional<T>`: до связывания графа он пуст, а после связывания получает текущий компонент из контейнера.

```java
public interface PromiseOf<T> {

    Optional<T> get();
}
```

Как и `ValueOf`, `PromiseOf` поддерживает `map(...)` и `optional()`.
Большинству бизнес-кода нужна только прямая зависимость или `ValueOf`; `PromiseOf` предназначен для более низкоуровневых сценариев,
где компоненту нужен отложенный доступ к другой части графа.

Если компонент, полученный через `ValueOf<Wrapped<T>>`, нужно передать дальше как обычный `ValueOf<T>`,
вы можете использовать `Wrapped.UnwrappedValue.unwrap(...)`. Это полезно для оберток, которые добавляют жизненный цикл или другое поведение,
но должны предоставлять наружу обычное значение.

#### Слушатели обновлений { #refresh-listener }

Если компоненту нужно знать, что граф был успешно обновлен, он может реализовать `RefreshListener`:

```java
public interface RefreshListener {

    void graphRefreshed() throws Exception;
}
```

Контейнер вызывает `graphRefreshed()` после успешного обновления графа. Если компонент одновременно является оберткой значения и слушателем обновлений,
он может реализовать комбинированный интерфейс `WrappedRefreshListener<T>`.

`RefreshListener` нужен только для получения уведомления после завершения обновления. Он не требуется для того, чтобы контейнер
пересоздал компонент. Если обновление затрагивает компонент или его зависимости, а другие компоненты внедрили его напрямую,
без `ValueOf` или `PromiseOf`, то эти зависимые компоненты также будут обновлены автоматически.

### Инспекция компонента { #component-inspection }

Бывают ситуации, когда компонент в контейнере нужно дополнительно изменить или инициализировать,
но никто не должен начинать работать с этим компонентом до завершения этих действий.
Для этого случая существует механизм перехвата компонентов. Поместите в контейнер объект, реализующий интерфейс `GraphInterceptor`.

```java
public interface GraphInterceptor<T> {

    T init(T value);

    T release(T value);
}
```

Например, этот механизм можно использовать для прогрева кэша на основе `JdbcDatabase`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CacheWarmupInterceptor implements GraphInterceptor<JdbcDatabase> {

        @Override
        public JdbcDatabase init(JdbcDatabase value) {
            // warm up cache
        }

        @Override
        public JdbcDatabase release(JdbcDatabase value) {
            return value;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CacheWarmupInterceptor : GraphInterceptor<JdbcDatabase> {

        override fun init(value: JdbcDatabase): JdbcDatabase {
            // warm up cache
        }

        override fun release(value: JdbcDatabase): JdbcDatabase {
            return value
        }
    }
    ```

Интерфейс `GraphInterceptor` почти такой же, как контракт `Lifecycle`, за исключением возвращаемого типа.
Метод `init(T value)` получает уже полностью инициализированный компонент. Метод может вернуть измененный или совершенно другой
экземпляр данного типа, и этот объект будет использован как зависимость другими компонентами.
Метод `release(T value)` получает компонент перед освобождением, то есть это все еще работающий и еще не очищенный экземпляр.
