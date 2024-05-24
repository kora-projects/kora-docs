Контейнер зависимостей является ядром фреймворка Kora и отвечает за построение графа зависимостей, их валидацию, 
их внедрение и их последующую инициализацию.

Работа контейнера в Kora разделена на две части: то что выполняется во время исполнения и то что выполняется во время компиляции.

## Во время компиляции

На этап компиляции производится поиск компонентов для построения контейнера зависимостей всего приложения. 
Это позволяет проводить валидацию контейнера зависимостей на этапе компиляции, до фактического старта приложения.

### Контейнер

За ядро контейнера зависимостей отвечает интерфейс помеченный аннотацией `@KoraApp`. 
Этой аннотацией необходимо помечать интерфейс, внутри которого лежат фабричные методы для создания компонентов и подключены [модули](#_7) зависимостей.
Такой интерфейс может быть только один в рамках приложения.

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application { }
    ```

### Компоненты

Компонентом называется зависимость в контейнере зависимостей. 
Все компоненты в Kora являются Синглтонами. Синглтон (Singleton) это класс, у которого экземпляр создаётся только один раз.

Компоненты внедряются только если являются [самостоятельным компонентом](#_13), либо если требуются в других компонентах как зависимости.
Компоненты неудовлетворяющие этим требованиям не попадают в контейнер зависимостей.

#### Авто фабрика

Аннотация `@Component` помечает класс, как доступный через контейнер. При этом к классу предъявляются следующие требования:

=== ":fontawesome-brands-java: `Java`"

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

#### Основная фабрика

Фабричный метод представляет собой метод с модификатором `default` который возвращает компонент, метод может принимать
аргументами другие компоненты как зависимости.

Контейнер ниже описывает две фабрики, где фабрика `otherService` требует компонент, создаваемый фабрикой `someService`.
Это самый базовый способ, как в контейнере могут регистрироваться компоненты:

=== ":fontawesome-brands-java: `Java`"

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

        fun otherService(someService: SomeService): OtherService = OtherService(someService)
    }
    ```

Фабричный метод **не должен предоставлять** значение `null` как компонент.

#### Модуль фабрика

Компоненты для контейнера также могут искаться в модулях в проекте приложения. 
Под модулем понимается интерфейс в котором находятся фабричные методы.
Аннотация `@Module` помечает интерфейс как модуль, который нужно внедрить в наш контейнер на этапе компиляции.
Модуль должен находиться в рамках одной директории исходного кода с классом помеченным `@KoraApp`.

Все фабричные методы внутри модуля становятся доступны контейнеру зависимостей:

=== ":fontawesome-brands-java: `Java`"

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

#### Внешняя фабрика

Компоненты для контейнера также могут искаться во внешних модулях из сторонних зависимостей. 
Под модулем понимается интерфейс в котором находятся фабричные методы.
Kora не делает автоматический поиск модулей из внешних зависимостей, как это делают некоторые другие решения внедрения зависимостей. 
Это позволяет разработчику точно контролировать и осознавать какие зависимости используются в его приложении и не допускать
инициализации множества лишних зависимостей и ухудшать тем самым работу приложения.

Все необходимые внешние модули из зависимостей должны быть подключены явно в интерфейс помеченный аннотацией `@KoraApp` через наследование:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends LogbackModule, JsonModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : LogbackModule, JsonModule
    ```

#### Межмодульная фабрика

Аннотация `@KoraSubmodule` помечает интерфейс, для которого нужно собрать модуль для текущего модуля компиляции, 
в него будут помещены все компоненты, помеченные аннотациями `@Module` и `@Component`.
Эта аннотация полезна, если вы разбиваете свой проект на модули с точки зрения своего инструмента сборки `Gradle/итд.`, где
каждый из которых отвечает за какую-то часть функциональности, а само приложение с `@KoraApp` собирается в отдельном модуле от логики.

Для интерфейса будет создан интерфейс наследник, в котором будут унаследованы все интерфейсы помеченные `@Module` и созданы default-методы для классов, помеченных как `@Component`.

Например, у вас есть модуль для работы с пользователями, который содержит контроллеры и другие компоненты и в нём есть свой модуль:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KoraSubmodule
    public interface SomeModule {

        default SomeService someService() {
            return new SomeService();
        } 
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraSubmodule
    interface SomeModule {

        fun someService(): SomeService = SomeService()
    }
    ```

И есть модуль сборки приложения:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends SomeModule {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : SomeModule
    ```

При этом в контейнер итогового приложения будет подключен модуль, созданный на основе `SomeModule`.

#### Дженерик фабрика

Если в контейнере не удалось найти фабрику для конкретного типа, то Kora контейнер во время компиляции может попробовать поискать
методы с [Дженерик](https://habr.com/ru/companies/sberbank/articles/416413/) параметрами, и при помощи этого метода создать экземпляр нужного класса.

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ValidatorsModule {

        default <T> GenericValidator<T> genericValidator(SomeValidationEntity<T> entity) {
            return new GenericValidator<>(entity);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ValidatorsModule {

        fun <T> genericValidator(entity: SomeValidationEntity<T>): GenericValidator<T> = GenericValidator(entity)
    }
    ```

Теперь если какому-то компоненту понадобится GenericValidator как зависимость, то эта фабрика будет использована для его создания.

#### Механизм расширений

В случае, если ни одна из фабрик не смогла предоставить компонент, Kora может попробовать создать эту зависимость во время компиляции сама.
Для этого предусмотрен механизм расширений. Каждое расширение умеет сказать, может ли оно создать компонент нужного типа. 
Если расширение может это сделать, то оно делает нужную кодогенерацию и сообщает, каким образом можно получить этот компонент.

Например, есть расширения, которые умеют создавать оптимальные Json читатели и писатели, JDBC-репозитории и другие компоненты.
Поиск доступных расширений происходит благодаря механизму `ServiceLocator` из всех зависимостей предоставленных в области видимости Annotation Processor. 

Механизм является скорее системным и используется зачастую внутренними модулями Kora.

#### Стандартная фабрика

Чтобы предоставлять фабричными методами компоненты по умолчанию, которые подразумевается что пользователь может у себя переопределить, 
требуется использовать аннотацию `@DefaultComponent`.
В случае если будет контейнером зависимостей на этапе компиляции будет найден любой компонент который не использует эту аннотацию, 
то предпочтение будет отдано ему при внедрении.

=== ":fontawesome-brands-java: `Java`"

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

#### Создание компонента

Если же ни один из способов выше не смог предоставить компонент, 
то Kora может попробовать самостоятельно создать компонент если он удовлетворяет требованиям аналогичным [авто фабрики](#_3):

=== ":fontawesome-brands-java: `Java`"

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

        fun someOtherService(someService: SomeService): SomeOtherService = SomeOtherService(someService)

        fun otherService(): OtherService = OtherService()
    }
    ```

### Переопределение компонент

В случае если компонент предоставляется библиотекой как зависимость по умолчанию, 
то можно создать фабрику в приложении без аннотации `@DefaultComponent` и такая зависимость переопределит ее.

Так как все внешние модули подключаются как интерфейсы в ядро контейнера `@KoraApp` и их фабрики доступны, 
то их можно просто переопределить как метод и предоставить свою реализацию.

### Самостоятельный компонент

Когда компонент требуется всегда инициализировать с запуском приложения, даже если он не является зависимостью других компонент, 
предполагается использовать аннотацию `@Root` над фабричным методов или классом аннотированным `@Component`.

Примером такого компонента может быть HTTP сервер, Kafka потребитель, компонент прогрева кешей.

=== ":fontawesome-brands-java: `Java`"

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

### Необязательные зависимости

=== ":fontawesome-brands-java: `Java`"

    Если хочется внедрить необязательную зависимость, которая может отсутствовать то 
    предполагается пометить такой компонент любой `@Nullable` аннотацией,
    тогда контейнер зависимостей не упадет на этапе компиляции из-за отсутвия компонента:

    ```java
    @Component
    public final class SomeService {

        private OtherService otherService;

        public SomeService(@Nullable OtherService otherService) { //(1)!
            this.otherService = otherService;
        }
    }
    ```

    1.  Подойдет любая аннотация `@Nullable`, такие как `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

=== ":simple-kotlin: `Kotlin`"

    Если хочется внедрить необязательную зависимость, которая может отсутствовать то 
    предполагается использовать [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис и помечать такой компонент как Nullable,
    тогда контейнер зависимостей не упадет на этапе компиляции из-за отсутвия компонента:

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService?) { }
    ```

### Список компонент

В контейнере может быть много экземпляров одного и того же типа, и если их все нужно собрать в одном месте, 
то следует использовать специальный тип `All`.

=== ":fontawesome-brands-java: `Java`"

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

        fun someProcessor(handlers: All<Handler>): SomeProcessor = SomeProcessor(handlers)
    }
    ```

Например, у нас есть некоторая сущность `Handler` и его имплементируют N разных типов в контейнере. 
`SomeProcessor` при этом потребляет все возможные реализации этого типа. 
**Важно** что пример выше возьмет все экземпляры `Handler` без тегов.

Сам тип `All` имеет следующий контракт:

```java
public interface All<T> extends List<T> {}
```

Это маркерный тип, расширяющий `List` и его можно отдавать в конструкторы, которые ожидают `List`.

### Теги

Иногда есть потребность предоставить разные экземпляры одного и того же типа в разные компоненты. Для этого их можно разграничить по тегам. 
Для этого есть аннотация `@Tag`, которая принимает на вход класс тега. 
Ожидается связка, где компонент зарегистрирован с определенным тегом и в точке внедрения он объявлен с точно таким же тегом.

Используется именно класс, а не строковый литерал, потому что это проще для навигации по коду и проще для рефакторинга.

Например, вот так можно внедрить разные экземпляры класса с общим интерфейсом по разным точкам внедрения:

=== ":fontawesome-brands-java: `Java`"

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
        fun someService1(): SomeService = SomeService2()

        fun serviceA(@Tag(MyTag1::class) service: SomeService): ServiceA = ServiceA(service)

        fun serviceB(@Tag(MyTag2::class) service: SomeService): ServiceB = ServiceB(service)
    }
    ```

Теги над методом говорят какой с каким тегом надо зарегистрировать компонент, а теги в точках внедрения говорят с каким тегом ожидается компонент.
Также теги работают на параметрах конструктора, в связке с `@Component` или финальными классами. 

=== ":fontawesome-brands-java: `Java`"

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

#### Тег списка

Можно использовать тег также для получения списка всех компонент по определенному тегу:

=== ":fontawesome-brands-java: `Java`"

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

        fun someProcessor(@Tag(MyTag::class) handlers: All<Handler>): SomeProcessor = SomeProcessor(handlers)
    }
    ```

#### Тег любых

Для получение списка вообще всех компонент с тегом и без, требуется использовать специальный тип тега `@Tag.Any`:

=== ":fontawesome-brands-java: `Java`"

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

        fun someProcessor(@Tag(Tag.Any::class) handlers: All<Handler>): SomeProcessor = SomeProcessor(handlers)
    }
    ```

## Во время исполнения

Контейнер зависимостей инициализируется максимально параллельно насколько это возможно в рамках того графа зависимостей который был построен.

На этапе исполнения приложения выполняются следующие вещи:

* Инициализирует все компоненты в контейнере
* Отслеживает изменения в контейнере
* Атомарно обновляет граф зависимостей при изменениях
* Осуществляет [Graceful Shutdown](https://habr.com/ru/companies/maxilect/articles/666090/) при получении сигнала SIGTERM

Все компоненты используют превентивную инициализацию, то есть инициализируются сразу с запуском приложения.

### Точка входа

Точка входа в приложение должна вызывать запуск `KoraApplication.run` с использованием созданного в процессе компиляции контейнера зависимостей.

В случае если интерфейс помеченный `@KoraApp` называется `Application`, в процессе компиляции в том же пакете
будет создан класс `ApplicationGraph` который будет представлять реализацию контейнера зависимостей и тогда точка входа
в рамках того же пакета будет выглядеть так:

=== ":fontawesome-brands-java: `Java`"

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

### Жизненный цикл контейнера

Контейнер умеет инициализировать все компоненты в правильном порядке, при этом он это делает максимально параллельно, для того, чтобы достичь максимально быстрого времени запуска.

Когда контейнер больше не нужен, то запускается механизм освобождения компонентов в обратном порядке.

В середине жизненного цикла может произойти обновление какого-либо компонента и тогда контейнер обновляет все компоненты, 
зависящие от изменённого. Это происходит атомарно: вначале процесса открывается транзакция,
которая закрывается только при условии успешной инициализации всех компонентов и откатывается, если произошла хотя бы одна ошибка.

### Жизненный цикл компонента

По умолчанию у всех компонентов нет жизненного цикла, они просто создаются через конструктор и собираются GC, когда они больше не нужны.
Если нужно сделать какие-то действия при инициализации компонента или после его освобождения, то необходимо, чтобы компонент реализовал интерфейс `Lifecycle`:

```java
public interface Lifecycle {
    
    void init() throws Exception;

    void release() throws Exception;
}
```

В контейнере все компоненты инициализируются асинхронно и параллельно настолько, насколько это возможно.

### Непрямые зависимости

Рассмотрим следующий пример:

=== ":fontawesome-brands-java: `Java`"

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

        fun serviceC(serviceA: ServiceA, serviceB: ValueOf<ServiceB>): ServiceC = ServiceC(serviceA, serviceB)
    }
    ```

У нас два сервиса, и третий сервис, который зависит от них. Но есть разница в жизненном цикле.
Если мы принимаем тип как зависимость напрямую, то мы говорим контейнеру, что при обновлении компонента `ServiceA`, нужно точно также обновить компонент `ServiceC`. 
Но когда мы используем тип обёртку `ValueOf`, то мы сообщаем контейнеру, 
что `ServiceC` никак не связан с жизненным циклом `ServiceB` и в случае изменения `ServiceB` нам не нужно обновлять `ServiceC`.

#### Обновление компонентов

Обновление компонент возможно в случае если внедрения зависимостей используется обертка `ValueOf`:

```java
public interface ValueOf<T> {
    
    T get();

    void refresh();
}
```

Мы можем получать актуальное состояние компонента в контейнере при помощи метода `get`.
Этот механизм используется в таких компонентах, которые нельзя перезагружать во время исполнения приложения. 
Например, это касается различных серверов, которые слушают сокеты (http, grpc) — для них через `ValueOf` поставляются обработчики запросов, которые могут быть подвержены изменениям.

При помощи функции `refresh` мы можем инициировать обновление компонента. Этот механизм например используется в компоненте отслеживающем изменения файла конфигурации на диске. 
При изменении контента файла, он инициирует обновления компонента конфигурации, и дальше все изменения распространяются по цепочке компонентов, связанных прямой связью. 

### Инспекция компонента

Есть ситуации, когда есть некоторый компонент в контейнере, который нужно дополнительно изменить или инициализировать, 
но при этом нужно, чтобы никто не начал работать с этим компонентом до того, как мы сделаем эти действия.  
Для этого случая предусмотрен механизм перехвата компонентов. Вам нужно положить в контейнер объект реализующий интерфейс `GraphInterceptor`. 

Например, этот механизм может использоваться для прогрева кэша на базе `JdbcDatabase`:

=== ":fontawesome-brands-java: `Java`"

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
Тут мы ожидаем, что метод может вернуть изменённый или вообще другой экземпляр объекта данного типа,
и уже этот объект будет использован как зависимость другими компонентами.   
