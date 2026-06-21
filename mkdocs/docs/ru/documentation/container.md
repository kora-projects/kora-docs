---
description: "Explains Kora compile-time dependency injection container, components, modules, factories, tags, lifecycle, graph resolution, and dependency wrappers. Use when working with @KoraApp, @Component, @Module, @KoraSubmodule, @Root, @Tag, @DefaultComponent, ValueOf."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora compile-time dependency injection container, components, modules, factories, tags, lifecycle, graph resolution, and dependency wrappers; key triggers include @KoraApp, @Component, @Module, @KoraSubmodule, @Root, @Tag, @DefaultComponent, ValueOf, All, PromiseOf."
---

Контейнер зависимостей является ядром фреймворка `Kora` и отвечает за построение графа зависимостей, его проверку,
внедрение компонентов, их инициализацию и последующее освобождение.
В отличие от контейнеров, которые собирают приложение во время запуска через сканирование пути классов, `Kora`
строит большую часть графа на этапе компиляции и генерирует обычный `Java`-код для запуска приложения.

Работа контейнера в `Kora` разделена на две части: то, что выполняется во время компиляции, и то, что выполняется во время исполнения.
На этапе компиляции проверяется, что все зависимости могут быть найдены и связаны между собой, а во время исполнения
контейнер создает компоненты, управляет их жизненным циклом и обновляет зависимые части графа при изменениях.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Введение во внедрение зависимостей](../guides/dependency-injection-introduction.md) и [Внедрение зависимостей](../guides/dependency-injection.md).

## Во время компиляции { #compile-time }

На этапе компиляции производится поиск компонентов для построения контейнера зависимостей всего приложения.
Это позволяет проверить контейнер зависимостей до фактического старта приложения.

### Контейнер { #container }

За ядро контейнера зависимостей отвечает интерфейс, помеченный аннотацией `@KoraApp`.
Этой аннотацией необходимо помечать интерфейс, внутри которого находятся фабричные методы для создания компонентов
и подключены [внешние модули](#external-module-factory) зависимостей.
Такой интерфейс может быть только один в рамках приложения.

Обработчики аннотаций `Kora` анализируют исходный код в модуле компиляции, где объявлен `@KoraApp`, а также в модулях,
для которых объявлен [`@KoraSubmodule`](#submodule-factory). Обычные проектные модули без `@KoraApp` или `@KoraSubmodule`
не становятся областью поиска компонентов автоматически.

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

Компонентом называется зависимость в контейнере зависимостей.
Все компоненты в `Kora` создаются в единственном экземпляре (`Singleton`).
Компоненты внедряются только если являются [самостоятельным компонентом](#root-component) либо если требуются другим компонентам как зависимости.

Компоненты, не удовлетворяющие этим требованиям, не попадают в контейнер зависимостей.

#### Автоматическая фабрика { #auto-factory }

Аннотация `@Component` помечает класс как доступный через контейнер. При этом к классу предъявляются следующие требования:

===! ":fontawesome-brands-java: `Java`"

    * Класс не должен быть абстрактным
    * У класса должен быть только один публичный конструктор
    * Класс должен быть `final` (только если он не имеет аспектов)

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
    * Класс не должен быть `open` (только если он не имеет аспектов)

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService) { }
    ```

#### Метод фабрика { #basic-factory }

Фабричный метод представляет собой метод с модификатором `default`, который возвращает компонент.
Метод может принимать как аргументы другие компоненты-зависимости.

Контейнер ниже описывает две фабрики, где фабрика `otherService` требует компонент, создаваемый фабрикой `someService`.
Это самый базовый способ, как в контейнере могут регистрироваться компоненты:

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

Фабричный метод **не должен предоставлять** значение `null` как компонент.

#### Модуль фабрика { #module-factory }

Компоненты для контейнера также могут находиться в модулях в рамках проекта приложения.
Под модулем понимается интерфейс, в котором находятся фабричные методы.
Аннотация `@Module` помечает интерфейс как модуль, который нужно внедрить в контейнер приложения на этапе компиляции.
Модуль должен находиться в рамках одной директории исходного кода с классом, помеченным `@KoraApp`.

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

#### Внешний модуль фабрика { #external-module-factory }

Компоненты для контейнера также могут искаться во внешних модулях из сторонних зависимостей.
Под модулем понимается интерфейс, в котором находятся фабричные методы.
`Kora` не делает автоматический поиск модулей из внешних зависимостей, как это делают некоторые другие решения внедрения зависимостей.
Это позволяет разработчику точно контролировать, какие зависимости используются в приложении, и не допускать
инициализации лишних компонентов.

Все необходимые внешние модули из зависимостей должны быть подключены явно в интерфейс, помеченный аннотацией `@KoraApp`, через наследование:

Такой модуль может быть объявлен в любом интерфейсе: в сторонней библиотеке, в отдельном модуле проекта или рядом с самим `@KoraApp`.
Главное, чтобы интерфейс с `@KoraApp` явно подключал его через наследование.

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

#### Межмодульная фабрика { #submodule-factory }

Аннотация `@KoraSubmodule` помечает интерфейс, для которого нужно собрать модуль для текущего модуля компиляции.
В него будут помещены все компоненты, помеченные аннотациями `@Module` и `@Component`.
Эта аннотация полезна, если вы разбиваете проект на [многомодульное приложение](https://docs.gradle.org/current/userguide/multi_project_builds.html)
с точки зрения инструмента сборки `Gradle`, где каждый модуль отвечает за свою часть функциональности,
а само приложение с `@KoraApp` собирается в отдельном модуле компиляции.
Такой подход помогает лучше структурировать большой проект по доменным областям и улучшить время сборки:
изменения в одном проектном модуле не заставляют обработчик аннотаций заново анализировать весь код приложения.

Для интерфейса будет создан интерфейс-наследник, в котором будут унаследованы все интерфейсы, помеченные `@Module`,
и созданы фабричные методы для классов, помеченных как `@Component`.

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

И есть основной модуль приложения с точкой сборки всего приложения:

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

При этом в контейнер итогового приложения будет подключен модуль `SomeModule`, найденный в рамках `SomeSubModule`.

#### Дженерик фабрика { #generic-factory }

Если в контейнере не удалось найти фабрику для конкретного типа, то контейнер `Kora` во время компиляции может попробовать найти
методы с дженерик параметрами и при помощи такого метода создать экземпляр нужного класса.

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

Теперь, если какому-то компоненту понадобится `GenericValidator` как зависимость, эта фабрика будет использована для его создания.

##### Сведения о дженерик типе { #type-ref }

Если фабричному методу нужно знать точный дженерик тип, который сейчас запрашивает контейнер, можно внедрить `TypeRef<T>`.
Это нужно для инфраструктурных компонентов, которые создают зависимость по форме типа, а не только по сырому классу.

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

`TypeRef<T>` переносит сведения о дженерик типе через стирание типов `Java`. Большинству прикладных компонентов он не нужен,
но он полезен для универсальных фабрик, преобразователей и расширений контейнера.

#### Механизм расширений { #extension-mechanism }

В случае, если ни одна из фабрик не смогла предоставить компонент, `Kora` может попробовать создать эту зависимость во время компиляции самостоятельно.
Для этого предусмотрен механизм расширений. Каждое расширение умеет сказать, может ли оно создать компонент нужного типа. 
Если расширение может это сделать, то оно делает нужную кодогенерацию и сообщает, каким образом можно получить этот компонент.

Например, есть расширения, которые умеют создавать оптимальные `JsonReader` и `JsonWriter`, репозитории и другие компоненты.
Поиск доступных расширений происходит благодаря механизму `ServiceLocator` из всех зависимостей, предоставленных в области видимости обработчика аннотаций.

Механизм является системным и чаще всего используется внутренними модулями `Kora`.

#### Стандартная фабрика { #standard-factory }

Чтобы предоставлять фабричными методами компоненты по умолчанию, которые пользователь может у себя переопределить,
требуется использовать аннотацию `@DefaultComponent`.
Если контейнер зависимостей на этапе компиляции найдет любой компонент того же типа и с теми же тегами, но без `@DefaultComponent`,
то при внедрении предпочтение будет отдано пользовательскому компоненту.

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

#### Авто создание { #auto-creation }

Если же ни один из способов выше не смог предоставить компонент,
то `Kora` может попробовать самостоятельно создать компонент, если он удовлетворяет требованиям, аналогичным [автоматической фабрике](#auto-factory):

===! ":fontawesome-brands-java: `Java`"

    * Класс не должен быть абстрактным
    * У класса должен быть только один публичный конструктор
    * Класс должен быть `final` (только если он не имеет аспектов)

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
    * Класс не должен быть `open` (только если он не имеет аспектов)

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

### Переопределение компонентов { #component-override }

В случае если компонент предоставляется библиотекой как зависимость по умолчанию,
можно создать фабрику в приложении без аннотации `@DefaultComponent`, и такая зависимость переопределит ее.

Так как все внешние модули подключаются как интерфейсы в ядро контейнера `@KoraApp` и их фабрики доступны,
то их можно просто переопределить как метод и предоставить свою реализацию.

### Самостоятельный компонент { #root-component }

Когда компонент требуется всегда инициализировать с запуском приложения, даже если он не является зависимостью других компонентов,
предполагается использовать аннотацию `@Root` над фабричным методом или классом, аннотированным `@Component`.

Примером такого компонента может быть `HTTP`-сервер, `Kafka`-потребитель, компонент прогрева кешей или запускаемый обработчик фоновой задачи.

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

    Если нужно внедрить необязательную зависимость, которая может отсутствовать, то
    предполагается пометить такой компонент любой аннотацией `@Nullable`,
    тогда контейнер зависимостей не упадет на этапе компиляции из-за отсутствия компонента:

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

    Если нужно внедрить необязательную зависимость, которая может отсутствовать, то
    предполагается использовать синтаксис [null-безопасности `Kotlin`](https://kotlinlang.ru/docs/null-safety.html) и помечать такой компонент как допускающий `null`,
    тогда контейнер зависимостей не упадет на этапе компиляции из-за отсутствия компонента:

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService?) { }
    ```

Необязательность можно сочетать с обертками контейнера: `ValueOf<Optional<T>>`, `Optional<ValueOf<T>>`,
`PromiseOf<Optional<T>>` и `Optional<PromiseOf<T>>`. Это удобно, когда зависимость может отсутствовать,
но компоненту все равно нужен отложенный доступ или возможность обновления через контейнер.

### Список компонентов { #list-of-components }

В контейнере может быть много экземпляров одного и того же типа, и если их все нужно собрать в одном месте,
то следует использовать специальный тип `All`.

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

Например, у нас есть некоторая сущность `Handler`, которую реализуют несколько разных типов в контейнере.
`SomeProcessor` при этом потребляет все возможные реализации этого типа.
**Важно**, что пример выше возьмет все экземпляры `Handler` без тегов.

Сам тип `All` имеет следующий контракт:

```java
public interface All<T> extends List<T> {}
```

Это маркерный тип, расширяющий `List`, и его можно передавать в конструкторы, которые ожидают `List`.
Если нужно собрать не сами компоненты, а ссылки на них, контейнер также поддерживает `All<ValueOf<T>>` и `All<PromiseOf<T>>`.

### Теги { #tags }

Иногда есть потребность предоставить разные экземпляры одного и того же типа в разные компоненты. Для этого их можно разграничить по тегам
посредством аннотации `@Tag`, которая принимает на вход класс тега.
Ожидается связка, где компонент зарегистрирован с определенным тегом и в точке внедрения он объявлен с точно таким же тегом.

Используется именно класс, а не строковый литерал, потому что это проще для навигации по коду стандартными средствами разработки 
и позволяет задать строгую типизацию тегам.

Например, вот так можно внедрить разные экземпляры класса с общим интерфейсом по разным точкам внедрения:

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

Теги над методом говорят, с каким тегом нужно зарегистрировать компонент, а теги в точках внедрения говорят, с каким тегом ожидается компонент.
Также теги работают на параметрах конструктора в связке с `@Component` или финальными классами.

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

#### Тег собственный { #tag-custom }

Можно также вводить собственные аннотации-теги и работать уже с ними. Таким примером может служить [аннотация `@Json`](json.md).

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

#### Тег список { #tag-all }

Можно использовать тег также для получения списка всех компонентов по определенному тегу:

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

#### Тег всех { #tag-any }

Для получения списка всех компонентов с тегом и без него требуется использовать специальный тип тега `@Tag.Any`:

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

## Во время исполнения { #runtime }

Контейнер зависимостей инициализируется настолько параллельно, насколько это возможно в рамках построенного графа.

На этапе исполнения приложения выполняются следующие вещи:

* Инициализирует все компоненты в контейнере зависимостей
* Отслеживает изменения в контейнере зависимостей
* Атомарно обновляет контейнер зависимостей при изменениях
* Осуществляет [штатное завершение](#component-lifecycle) при получении сигнала `SIGTERM`

Все компоненты используют превентивную инициализацию, то есть инициализируются сразу с запуском приложения.

### Точка входа { #entrypoint }

Точка входа в приложение должна вызывать запуск `KoraApplication.run` с использованием созданного в процессе компиляции контейнера зависимостей.

В случае если интерфейс, помеченный `@KoraApp`, называется `Application`, в процессе компиляции в том же пакете
будет создан класс `ApplicationGraph`, который будет представлять реализацию контейнера зависимостей, и тогда точка входа
в рамках того же пакета будет выглядеть так:

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

### Жизненный цикл контейнера { #container-lifecycle }

Контейнер умеет инициализировать все компоненты в правильном порядке, при этом он это делает максимально параллельно, чтобы достигнуть максимально быстрого времени запуска.

Когда контейнер больше не нужен, запускается механизм освобождения компонентов в обратном порядке.

В середине жизненного цикла может произойти обновление какого-либо компонента, и тогда контейнер обновляет все компоненты, 
зависящие от изменённого. Это происходит атомарно: вначале процесса открывается транзакция,
которая закрывается только при условии успешной инициализации всех компонентов и откатывается, если произошла хотя бы одна ошибка.

### Жизненный цикл компонентов { #component-lifecycle }

По умолчанию все компоненты создаются единственным экземпляром через конструктор или фабричный метод на этапе инициализации.
Если нужно сделать какие-то действия перед инициализацией компонента или перед его освобождением, то необходимо реализовать интерфейс `Lifecycle`:

```java
public interface Lifecycle {
    
    void init() throws Exception;

    void release() throws Exception;
}
```

В контейнере все компоненты инициализируются асинхронно и параллельно настолько, насколько это возможно.

Если требуется предоставить компонент в фабричном методе с жизненным циклом, можно воспользоваться классом `LifecycleWrapper`.
Он реализует сразу два контракта:

* `Lifecycle` — контейнер вызовет `init()` при старте и `release()` при освобождении компонента
* `Wrapped<T>` — контейнер будет внедрять значение `T`, которое возвращается из метода `value()`

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        default Wrapped<SomeService> someService() {
            return new LifecycleWrapper<>(new SomeService(),
                    (component) -> {
                        // логика инициализации
                    },
                    (component) -> {
                        // логика освобождения
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
                    // логика инициализации
                },
                { component ->
                    // логика освобождения
                }
            )
        }
    }
    ```

Если нужно вернуть собственную обертку, она должна реализовать `Wrapped<T>`:

```java
public interface Wrapped<T> {

    T value();
}
```

### Штатное завершение { #graceful-shutdown }

Все интеграции, которые предоставляет `Kora`, такие как [HTTP-сервер](http-server.md) и [Kafka-потребитель](kafka.md),
поддерживают [штатное завершение](https://maxilect.ru/blog/pochemu-vazhen-graceful-shutdown-v-oblachnoy-srede-na-pr/) из коробки посредством
[жизненного цикла компонент](#container-lifecycle).

Также все компоненты, которые реализуют интерфейс `AutoCloseable`, будут автоматически штатно завершены контейнером зависимостей перед освобождением.

### Непрямые зависимости { #indirect-dependency }

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

У нас два сервиса и третий сервис, который зависит от них. Но есть разница в жизненном цикле.
Если мы принимаем тип как зависимость напрямую, то мы говорим контейнеру, что при обновлении компонента `ServiceA` нужно также обновить компонент `ServiceC`.
Но когда мы используем тип-обертку `ValueOf`, то сообщаем контейнеру,
что `ServiceC` никак не связан с жизненным циклом `ServiceB` и в случае изменения `ServiceB` нам не нужно обновлять `ServiceC`.

#### Обновление компонентов { #updating-components }

Обновление компонентов возможно в случае, если при внедрении зависимостей используется обертка `ValueOf`:

```java
public interface ValueOf<T> {
    
    T get();

    void refresh();
}
```

Метод `get()` возвращает актуальное состояние компонента в контейнере.
Этот механизм используется в компонентах, которые нельзя перезагружать во время исполнения приложения.
Например, это касается различных серверов, которые слушают сокеты (`HTTP`, `gRPC`): для них через `ValueOf`
поставляются обработчики запросов, которые могут быть подвержены изменениям.

При помощи метода `refresh()` можно инициировать обновление компонента. Этот механизм, например, используется в компоненте,
который отслеживает изменения файла конфигурации на диске.
При изменении содержимого файла он инициирует обновление компонента конфигурации, и дальше все изменения распространяются
по цепочке компонентов, связанных прямой зависимостью.

У `ValueOf` есть дополнительные методы для удобной работы с обернутым значением:

* `map(...)` — преобразует значение внутри `ValueOf` без изменения связи с исходным компонентом
* `optional()` — преобразует `ValueOf<T>` в `ValueOf<Optional<T>>`

Если компонент нужно получить через отложенную ссылку, можно использовать `PromiseOf<T>`.
Метод `get()` возвращает `Optional<T>`: до привязки к графу он пустой, а после привязки получает актуальный компонент из контейнера.

```java
public interface PromiseOf<T> {

    Optional<T> get();
}
```

Как и `ValueOf`, `PromiseOf` поддерживает методы `map(...)` и `optional()`.
Обычной бизнес-логике чаще всего достаточно прямой зависимости или `ValueOf`; `PromiseOf` нужен для более низкоуровневых
сценариев, где компоненту важно отложенно обратиться к другой части графа.

Если компонент, полученный через `ValueOf<Wrapped<T>>`, нужно передать дальше как обычный `ValueOf<T>`, можно использовать
`Wrapped.UnwrappedValue.unwrap(...)`. Это полезно для оберток, которые добавляют жизненный цикл или другое поведение,
но наружу должны отдавать обычное значение.

#### Слушатели обновления { #refresh-listener }

Если компонент должен узнать, что граф был успешно обновлен, он может реализовать интерфейс `RefreshListener`:

```java
public interface RefreshListener {

    void graphRefreshed() throws Exception;
}
```

Контейнер вызывает `graphRefreshed()` после успешного обновления графа. Если компонент одновременно является оберткой над
значением и слушателем обновления, можно реализовать объединенный интерфейс `WrappedRefreshListener<T>`.

`RefreshListener` нужен только для получения уведомления о завершении обновления. Его не нужно реализовывать, чтобы
контейнер пересоздал компонент. Если обновление затрагивает компонент или его зависимости, а другие компоненты внедрили
его напрямую, без `ValueOf` или `PromiseOf`, то такие зависимые компоненты тоже будут обновлены автоматически.

### Инспекция компонентов { #component-inspection }

Есть ситуации, когда некоторый компонент в контейнере нужно дополнительно изменить или инициализировать,
но при этом нужно, чтобы никто не начал работать с этим компонентом до завершения этих действий.
Для этого случая предусмотрен механизм перехвата компонентов. Нужно положить в контейнер объект, реализующий интерфейс `GraphInterceptor`.

```java
public interface GraphInterceptor<T> {

    T init(T value);

    T release(T value);
}
```

Например, этот механизм может использоваться для прогрева кэша на базе `JdbcDatabase`:

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

Интерфейс `GraphInterceptor` практически повторяет контракт `Lifecycle`, за исключением возвращаемого типа.
В `init(T value)` передается уже полностью инициализированный компонент. Метод может вернуть измененный или вообще другой
экземпляр объекта данного типа, и уже этот объект будет использован как зависимость другими компонентами.
В `release(T value)` передается компонент перед освобождением, то есть еще рабочий и не очищенный экземпляр.
