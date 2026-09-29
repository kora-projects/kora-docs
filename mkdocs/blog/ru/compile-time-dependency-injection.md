---
title: "Внедрение зависимостей на этапе компиляции в Kora"
date: 2026-08-03
description: "Как Kora строит и проверяет граф зависимостей при компиляции: @KoraApp, @Component, @Module, теги, All<T>, ValueOf<T>, жизненный цикл и ошибки сборки."
keywords: ["Kora Framework", "фреймворк Kora", "DI в Kora", "внедрение зависимостей на этапе компиляции", "compile-time DI", "annotation processing", "KSP", "@KoraApp"]
search:
    exclude: true
---

# Внедрение зависимостей на этапе компиляции: как Kora строит приложение { #compile-time-dependency-injection }

**3 августа 2026**

Внедрение зависимостей часто представляют как механизм удобства: вместо ручного конструирования каждого объекта класс объявляет, что ему нужно, а контейнер это предоставляет. Это описание
полезно, но оно скрывает более интересный архитектурный вопрос: **когда контейнер решает, чем на самом деле является приложение?**

Во многих JVM-фреймворках значительная часть этой работы происходит во время выполнения. Контейнер запускается, обнаруживает компоненты, анализирует конструкторы и фабричные методы, разрешает
зависимости, применяет
квалификаторы, проверяет циклы, создаёт внутренние определения и только затем собирает граф объектов. Kora Framework намеренно переносит большую часть этого рассуждения в компиляцию.

Его движок внедрения зависимостей лучше всего понимать как **компилятор графа на этапе компиляции, поддерживаемый небольшим исполнителем графа во время выполнения**. Во время компиляции Kora
обнаруживает провайдеров, разрешает
запросы зависимостей, проверяет неоднозначность, верифицирует теги и циклы, генерирует недостающие компоненты фреймворка и производит граф приложения. Во время выполнения контейнер исполняет этот уже
известный граф: он создаёт
объекты, инициализирует компоненты с поддержкой жизненного цикла, управляет ссылками, обновляет затронутые узлы при необходимости и корректно завершает всё в порядке зависимостей.

Это разделение — ключ к пониманию DI в Kora.

---

## DI как компиляция графа { #di-as-graph-compilation }

Рассмотрим небольшое приложение:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class OrderController {

        public OrderController(OrderService service) {
        }
    }

    @Component
    public final class OrderService {

        public OrderService(OrderRepository repository) {
        }
    }

    @Component
    public final class OrderRepository {

        public OrderRepository(DataSource dataSource) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class OrderController(service: OrderService)

    @Component
    class OrderService(repository: OrderRepository)

    @Component
    class OrderRepository(dataSource: DataSource)
    ```

С точки зрения движка DI эти конструкторы описывают граф:

```text
OrderController → OrderService → OrderRepository → DataSource
```

Каждый конструируемый компонент становится узлом, а каждый параметр конструктора или фабрики становится требованием зависимости, которое должно быть разрешено в другой узел.

Например:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public OrderService(OrderRepository repository)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class OrderService(repository: OrderRepository)
    ```

можно читать как запрос ровно одного компонента, совместимого с `OrderRepository`.

Тегированная зависимость:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public OrderService(
        @Tag(MainDb.class) OrderRepository repository) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class OrderService(
        @Tag(MainDb::class) repository: OrderRepository
    )
    ```

запрашивает ровно один соответствующий `OrderRepository` с требуемым тегом.

Зависимость в виде коллекции:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Dispatcher(All<Handler> handlers) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class Dispatcher(handlers: All<Handler>)
    ```

меняет запрос снова: вместо ровно одного провайдера конструктор запрашивает все соответствующие компоненты `Handler`.

Контейнер времени компиляции многократно разрешает эти требования, пока не построит достижимый граф приложения. Если требуемый провайдер не существует, если несколько одинаково валидных провайдеров
конкурируют за одну точку внедрения или если жёсткий цикл зависимостей делает конструирование невозможным, Kora останавливает компиляцию, а не откладывает ошибку до запуска.

Это делает внедрение зависимостей менее похожим на поиск во время выполнения и больше похожим на статическое разрешение графа.

---

## `@KoraApp`: корень графа приложения { #kora-app }

Каждое приложение Kora начинается с интерфейса, аннотированного `@KoraApp`:

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

Этот интерфейс определяет корневую границу сборки приложения. Он может содержать фабричные методы напрямую или наследовать модули, которые вносят инфраструктуру и провайдеров уровня приложения.

Более реалистичное приложение могло бы выглядеть так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        HoconConfigModule,
        LogbackModule,
        JsonModule,
        UndertowPublicHttpServerModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        JsonModule,
        UndertowPublicHttpServerModule
    ```

Это не просто организационный синтаксис. Это сообщает компилятору, какие внешние модули являются частью вселенной зависимостей приложения.

Kora намеренно избегает модели, в которой каждая зависимость classpath сканируется, а произвольные определения фреймворка присоединяются неявно. Компоненты и модули из текущей области компиляции могут
участвовать напрямую, тогда как внешние модули подключаются через явное наследование от интерфейса приложения. Для многомодульных сборок `@KoraSubmodule` предоставляет дополнительную границу
времени компиляции.

Во время обработки аннотаций Kora использует интерфейс `@KoraApp` как отправную точку для генерации `ApplicationGraph`. Запуск затем напрямую ссылается на этот сгенерированный граф:

===! ":fontawesome-brands-java: `Java`"

    ```java
    KoraApplication.run(ApplicationGraph::graph);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    KoraApplication.run(ApplicationGraph::graph)
    ```

Поэтому граф — не структура, обнаруженная во время выполнения. Это скомпилированное представление того, как должно собираться приложение.

---

## `@Component`: объявление конструируемого узла { #component }

Самый простой способ сделать класс приложения доступным для DI — `@Component`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PaymentService {

        private final PaymentRepository repository;

        public PaymentService(PaymentRepository repository) {
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PaymentService(private val repository: PaymentRepository)
    ```

Это объявление даёт Kora два фрагмента информации. Во-первых, `PaymentService` может стать узлом графа. Во-вторых, его конструктор сообщает компилятору, какие другие узлы требуются для его создания.

Kora держит эту модель намеренно простой. Java-компонент имеет публичный конструктор, а его параметры конструктора описывают его зависимости. Фреймворк в целом не пытается инстанцировать произвольные
классы просто потому, что они
оказываются конструируемыми.

Это различие важно. Предположим, мы пишем:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PaymentService {

        public PaymentService(PaymentRepository repository) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PaymentService(repository: PaymentRepository)
    ```

но ни компонент, ни фабрика модуля, ни обобщённый провайдер, ни расширение времени компиляции никогда не поставляют `PaymentRepository`. Kora не решает молча инстанцировать какой-то подходящий класс.
Граф зависимостей
неполон, поэтому компиляция завершается ошибкой.

Эта модель явной регистрации делает каждый узел прослеживаемым до конкретного механизма провайдера, а не позволяет контейнеру изобретать структуру приложения из случайного содержимого classpath.

---

## Фабричные методы: провайдеры без `@Component` { #factory-methods }

Не каждый объект может или должен быть аннотирован.

Сторонние библиотеки — очевидный случай. Вам может понадобиться `ExecutorService`, клиент из внешнего SDK или какой-то ресурс, создаваемый через builder API. Kora обрабатывает это через фабричные
методы:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default ExecutorService executor() {
            return Executors.newVirtualThreadPerTaskExecutor();
        }

        default JobService jobService(ExecutorService executor) {
            return new JobService(executor);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        fun executor(): ExecutorService {
            return Executors.newVirtualThreadPerTaskExecutor()
        }

        fun jobService(executor: ExecutorService): JobService {
            return JobService(executor)
        }
    }
    ```

Для компилятора графа эти фабричные методы ведут себя точно так же, как провайдеры на основе конструкторов. Первый вносит узел `ExecutorService` без зависимостей. Второй вносит узел
`JobService`, который зависит от этого исполнителя.

Параметры фабрики разрешаются по тем же правилам, что и параметры конструктора, поэтому движку DI не нужна отдельная концептуальная модель для классов приложения и внешне созданных объектов.

Это одна из причин, по которой контейнер Kora остаётся относительно лёгким для рассуждения: логика конструирования выражается как обычные методы Java или Kotlin, а компилятор графа использует эти
методы как
определения провайдеров.

---

## `@Module`: группировка связанных провайдеров { #module }

По мере роста приложений размещение каждого фабричного метода напрямую на `@KoraApp` становится громоздким. `@Module` позволяет группировать связанные провайдеры:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface PaymentModule {

        default PaymentClient paymentClient(
            HttpClient httpClient,
            PaymentConfig config) {
            return new PaymentClient(httpClient, config);
        }

        default PaymentGateway paymentGateway(
            PaymentClient client) {
            return new PaymentGateway(client);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface PaymentModule {

        fun paymentClient(
            httpClient: HttpClient,
            config: PaymentConfig
        ): PaymentClient {
            return PaymentClient(httpClient, config)
        }

        fun paymentGateway(client: PaymentClient): PaymentGateway {
            return PaymentGateway(client)
        }
    }
    ```

Эти методы остаются обычными провайдерами компонентов. Модуль просто даёт им связную границу.

Приложение затем может явно компоновать модули:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        PaymentModule,
        JsonModule,
        UndertowPublicHttpServerModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        PaymentModule,
        JsonModule,
        UndertowPublicHttpServerModule
    ```

Это делает композицию модулей саму по себе информацией времени компиляции. Библиотека может публиковать модули провайдеров, а приложение выбирает, какие из них станут частью его графа, не полагаясь на
хуки
регистрации во время выполнения или глобальное обнаружение.

Это важно для прозрачности. Взгляд на интерфейс `@KoraApp` рассказывает вам значимую часть архитектурной композиции приложения до того, как сервис когда-либо запустится.

---

## Достижимость: не каждый провайдер становится компонентом рантайма { #reachability }

Граф Kora — не обязательно реестр каждого объявления компонента, которое он может обнаружить. Что в конечном счёте важно — какие узлы достижимы из корней приложения.

Рассмотрим:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class DebugReporter {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class DebugReporter
    ```

Если ни один корень или достижимый компонент не зависит от `DebugReporter`, нет сильной причины инстанцировать его. Простое существование в исходном коде не автоматически подразумевает, что он должен
участвовать в
инициализации рантайма.

Инфраструктура, которой нужно запускаться независимо, вместо этого может быть помечена как корень:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class EventConsumer implements Lifecycle {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class EventConsumer : Lifecycle {
        // ...
    }
    ```

HTTP-серверы, фоновые рабочие, потребители, планировщики и подобные компоненты часто ведут себя как корни графа, потому что представляют активные точки входа в работающую систему.

Это даёт DI в Kora модель, ориентированную на достижимость, а не простой глобальный реестр бинов. Результирующий граф содержит то, что приложению фактически нужно для работы.

---

## Разрешение зависимостей как точное сопоставление { #dependency-resolution }

Как только Kora обнаружил возможных провайдеров, начинается настоящая работа разрешения.

Предположим, у нас есть:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CheckoutService {

        public CheckoutService(PaymentGateway gateway) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CheckoutService(gateway: PaymentGateway)
    ```

Компилятор фактически видит требование зависимости, описанное типом, тегами и кардинальностью. В этом случае требование простое: разрешить ровно один `PaymentGateway`.

Если есть один валидный провайдер, Kora создаёт ребро. Если их нет, компиляция завершается ошибкой. Если есть несколько одинаково валидных кандидатов, зависимость неоднозначна, и компиляция также
завершается ошибкой.

Например:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class StripeGateway implements PaymentGateway {
    }

    @Component
    public final class InternalGateway implements PaymentGateway {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class StripeGateway : PaymentGateway

    @Component
    class InternalGateway : PaymentGateway
    ```

в сочетании с:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CheckoutService {

        public CheckoutService(PaymentGateway gateway) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CheckoutService(gateway: PaymentGateway)
    ```

не содержит достаточно информации, чтобы идентифицировать задуманного провайдера.

Kora не угадывает на основе порядка объявления, порядка classpath, соглашений об именах или какого-то неявного ранжирования. Приложение выразило неоднозначную архитектуру, поэтому компилятор сообщает
об этом.

Это важный дизайнерский выбор. Внедрение зависимостей остаётся детерминированным, потому что неоднозначность должна моделироваться явно, а не скрываться за эвристиками контейнера.

---

## Теги — часть идентичности зависимости { #tags }

Теги решают случаи, когда несколько компонентов разделяют один и тот же тип Java, но служат разным ролям.

Предположим, есть два шлюза:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(Primary.class)
    @Component
    public final class StripeGateway implements PaymentGateway {
    }

    @Tag(Backup.class)
    @Component
    public final class BackupGateway implements PaymentGateway {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(Primary::class)
    @Component
    class StripeGateway : PaymentGateway

    @Tag(Backup::class)
    @Component
    class BackupGateway : PaymentGateway
    ```

Потребитель может указать, какой из них ему требуется:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CheckoutService {

        public CheckoutService(
            @Tag(Primary.class) PaymentGateway gateway) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CheckoutService(
        @Tag(Primary::class) gateway: PaymentGateway
    )
    ```

Архитектурно Kora больше не разрешает только тип Java. Он разрешает тип вместе с набором тегов.

Это делает теги больше, чем косметическими квалификаторами. Они часть идентичности запроса зависимости.

Использование классов как тегов вместо строковых имён также держит эти различия внутри обычной системы типов Java. Теги можно просматривать, переименовывать и рефакторить через обычные инструменты,
вместо того чтобы
становиться хрупкими строковыми идентификаторами.

Одна деталь особенно важна: нетэгированная точка внедрения не означает «любой компонент этого типа». Она конкретно запрашивает нетэгированный вариант. Если приложение намеренно хочет
игнорировать различия тегов, Kora предоставляет `Tag.Any` для этой цели.

Это держит семантические границы явными. Клиент, настроенный для одной базы данных, арендатора, региона или транспорта, не должен случайно удовлетворять несвязанную точку внедрения просто потому, что
сырой тип Java
совпадает.

---

## `All<T>`: когда корректно более одного совпадения { #all-t }

Неоднозначность — ошибка только тогда, когда зависимость ожидает один компонент.

Иногда приложение действительно хочет каждую реализацию.

Представьте:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface NotificationChannel {
        void send(Notification notification);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface NotificationChannel {
        fun send(notification: Notification)
    }
    ```

с несколькими реализациями:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class EmailChannel implements NotificationChannel {
    }

    @Component
    public final class SmsChannel implements NotificationChannel {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class EmailChannel : NotificationChannel

    @Component
    class SmsChannel : NotificationChannel
    ```

Диспетчер может запросить их все:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class NotificationDispatcher {

        private final All<NotificationChannel> channels;

        public NotificationDispatcher(
            All<NotificationChannel> channels) {
            this.channels = channels;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NotificationDispatcher(
        private val channels: All<NotificationChannel>
    )
    ```

Это меняет зависимость с единственного числа на множественное.

Обычный `NotificationChannel` требует ровно одного совместимого провайдера. `All<NotificationChannel>` разрешает каждый соответствующий провайдер и раскрывает их через итерируемую коллекцию.

===! ":fontawesome-brands-java: `Java`"

    ```java
    for (var channel : channels) {
        channel.send(notification);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    for (channel in channels) {
        channel.send(notification)
    }
    ```

В отличие от обычной сингулярной зависимости, `All<T>` также может валидно быть пустым. Это делает его полезным для необязательных точек расширения, паттернов в стиле плагинов, обработчиков событий,
валидаторов, перехватчиков или любого
другого сценария, где приложение хочет собрать ноль или более реализаций.

Теги естественно сочетаются с `All<T>`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Dispatcher(
        @Tag(External.class)
        All<NotificationChannel> channels) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class Dispatcher(
        @Tag(External::class)
        channels: All<NotificationChannel>
    )
    ```

в то время как `@Tag(Tag.Any.class)` позволяет коллекции намеренно охватывать тегированные и нетэгированные реализации.

Поэтому модель DI имеет небольшой, но выразительный словарь кардинальности: обычные зависимости означают ровно один, обнуляемые или необязательные зависимости означают ноль или один, а `All<T>`
означает от нуля до многих.

---

## Значения по умолчанию и переопределения приложения { #defaults-and-overrides }

Библиотекам часто нужно предоставлять реализацию по умолчанию, не мешая приложениям заменять её.

Kora моделирует это с помощью `@DefaultComponent`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ClientModule {

        @DefaultComponent
        default RetryPolicy retryPolicy() {
            return new DefaultRetryPolicy();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ClientModule {

        @DefaultComponent
        fun retryPolicy(): RetryPolicy {
            return DefaultRetryPolicy()
        }
    }
    ```

Приложение затем может предоставить другой компонент с тем же типом и тегами. Построитель графа рассматривает значение по умолчанию как запасной вариант, а не как равного кандидата, поэтому явная
реализация уровня приложения
побеждает.

Это избегает превращения кастомизации в механизм замены бинов во время выполнения. Модуль может поставлять разумные значения по умолчанию, при этом переопределение остаётся обычной композицией на
уровне исходного кода.

---

## Отсутствующие зависимости становятся ошибками компиляции { #missing-dependencies }

Одно из самых ясных следствий DI времени компиляции — местоположение отказа.

Предположим:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PetService {

        public PetService(PetRepository repository) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PetService(repository: PetRepository)
    ```

но приложение не предоставляет `PetRepository`.

В модели DI времени выполнения эта ошибка может пережить компиляцию, упаковку, создание образа, развёртывание и запуск процесса, прежде чем контейнер наконец сообщит, что граф не может быть построен.

Kora уже знает во время обработки аннотаций, что валидного провайдера не существует. Поэтому компиляция останавливается.

Более важно, у компилятора достаточно информации о графе, чтобы объяснить, *почему* требовалась зависимость. Он может сообщить отсутствующий тип, точку внедрения и путь зависимости, ведущий от
корня графа к неразрешённому узлу.

Концептуально отказ можно понять так:

```text
PetController
    ↓
PetService
    ↓
PetRepository   ← не разрешён
```

Этот путь графа полезен, потому что место, где разрешение терпит неудачу, может быть на несколько зависимостей удалено от корня, который сделал узел достижимым в первую очередь.

Поэтому DI времени компиляции улучшает не только то, когда происходит ошибка, но и контекст, доступный для её объяснения.

---

## Циклы обнаруживаются как структура графа { #cycles }

Циклы — естественная проблема графа.

Валидная цепочка зависимостей может выглядеть так:

```text
A → B → C
```

в то время как случайный цикл выглядит так:

```text
A → B → C → A
```

Например:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ServiceA {

        public ServiceA(ServiceB b) {
        }
    }

    @Component
    public final class ServiceB {

        public ServiceB(ServiceA a) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ServiceA(b: ServiceB)

    @Component
    class ServiceB(a: ServiceA)
    ```

Поскольку Kora разрешает граф во время компиляции, он может обнаружить эту структуру до запуска приложения.

Для жёстких зависимостей, которые нельзя проксировать или отложить, цикл — ошибка времени компиляции. Kora может сообщить фактический путь цикла, а не позволять сервису падать только после того, как
создание объектов
уже началось.

Фреймворк может разрешать некоторые циклы на основе интерфейсов через сгенерированные ленивые прокси, но это не меняет лежащую в основе архитектурную точку: циклы видимы компилятору графа.

Во многих случаях более чистое решение — не полагаться на проксирование вообще, а изменить природу одного из рёбер. Здесь важным становится `ValueOf<T>`.

---

## `ValueOf<T>` меняет смысл ребра зависимости { #value-of-t }

`ValueOf<T>` может изначально выглядеть как абстракция провайдера:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ValueOf<PaymentConfig>
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    ValueOf<PaymentConfig>
    ```

которую позже можно разыменовать:

===! ":fontawesome-brands-java: `Java`"

    ```java
    PaymentConfig config = paymentConfig.get();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val config: PaymentConfig = paymentConfig.get()
    ```

Но в модели графа Kora оно представляет нечто более важное: косвенную зависимость, которая не участвует в распространении жизненного цикла так же, как прямая зависимость.

Рассмотрим:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ServiceC(ServiceB serviceB)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ServiceC(serviceB: ServiceB)
    ```

Прямая зависимость означает, что `ServiceC` построен против конкретного экземпляра `ServiceB`. Если граф позже обновляет `ServiceB`, нижестоящие компоненты, которые напрямую зависят от него, также
могут нуждаться в
пересборке.

Теперь измените конструктор на:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ServiceC(ValueOf<ServiceB> serviceB)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ServiceC(serviceB: ValueOf<ServiceB>)
    ```

`ServiceC` теперь держит ссылку на узел графа, а не на фиксированный экземпляр `ServiceB`. Вызов `serviceB.get()` разрешает текущее значение. Если `ServiceB` обновляется, сам `ServiceC` может
оставаться живым.

Это делает `ValueOf<T>` полезным на архитектурных границах, где один компонент должен наблюдать изменения в другом, не разделяя его жизненный цикл.

Долгоживущий HTTP-сервер — хороший пример. Сервер владеет слушающим сокетом и не должен перезапускаться просто потому, что изменилась некоторая структура нижестоящего обработчика. Удержание `ValueOf`
на
эту изменяющуюся зависимость позволяет серверу оставаться стабильным, при этом наблюдая последнее значение графа.

Тот же механизм может разорвать жёсткий цикл:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ServiceA {

        public ServiceA(ValueOf<ServiceB> serviceB) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ServiceA(serviceB: ValueOf<ServiceB>)
    ```

Отношение всё ещё существует семантически, но это больше не жёсткое ребро конструирования в том же смысле.

Это показывает, что граф Kora моделирует больше, чем ссылки на объекты. Он также моделирует распространение жизненного цикла.

---

## Граф можно обновлять во время выполнения { #graph-refresh }

DI времени компиляции не означает, что каждое значение графа навсегда заморожено после компиляции.

**Форма** графа известна заранее, но некоторые узлы могут обновляться во время выполнения.

Обновляемый граф Kora может пересобрать узел и напрямую затронутую нижестоящую часть графа. Заменяющий подграф создаётся и инициализируется сначала, и только затем подменяется в работающее
приложение. Если инициализация терпит неудачу, временный граф освобождается, а предыдущий граф остаётся активным.

Эта транзакционная модель обновления делает `ValueOf<T>` особенно важным, потому что она определяет, где останавливается распространение обновления.

Предположим, у нас есть:

```text
Config
  ↓
DatabaseConfig
  ↓
DatabaseClient
  ↓
Repository
  ↓
Service
```

Если каждое ребро прямое, обновление конфигурации может требовать пересборки нескольких нижестоящих узлов.

Если долгоживущий компонент вместо этого зависит от:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ValueOf<Repository>
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    ValueOf<Repository>
    ```

этот компонент может пережить, наблюдая обновлённый экземпляр репозитория.

Поэтому граф статичен по структуре, но не обязательно статичен по значению. Kora валидирует топологию на этапе компиляции, а затем позволяет операциям рантайма действовать в пределах этой
валидированной топологии.

---

## Жизненный цикл следует за графом зависимостей { #lifecycle }

Тот же граф, используемый для внедрения, также говорит Kora, как приложение должно запускаться и останавливаться.

Рассмотрим:

```text
HTTP-сервер
    ↓
Контроллер
    ↓
Сервис
    ↓
Репозиторий
    ↓
База данных
```

База данных должна быть готова до репозитория, репозиторий до сервиса, а сервис до того, как сервер начнёт принимать трафик. Во время завершения порядок должен быть обратным.

Kora может естественно вывести это из зависимостей графа.

Компоненты, владеющие ресурсами, могут реализовать:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface Lifecycle {
        void init() throws Exception;

        void release() throws Exception;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface Lifecycle {
        fun init()

        fun release()
    }
    ```

Например:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class EventLoop implements Lifecycle {

        @Override
        public void init() {
            // acquire resources
        }

        @Override
        public void release() {
            // release resources
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class EventLoop : Lifecycle {

        override fun init() {
            // acquire resources
        }

        override fun release() {
            // release resources
        }
    }
    ```

Контейнер инициализирует зависимости до их зависимых и освобождает их в обратном порядке. `AutoCloseable` также интегрируется с завершением, а объекты, созданные фабрикой, могут быть обёрнуты, когда
исходный тип не может реализовать интерфейс жизненного цикла Kora напрямую.

Это делает жизненный цикл свойством графа приложения, а не полностью отдельной подсистемой запуска.

---

## Параллельная инициализация выпадает естественно { #parallel-initialization }

Как только граф известен, Kora также знает, какие ветви независимы.

Предположим, граф запуска выглядит так:

```text
               ┌─ Database ─ Repository ─┐
Application ───┤                        ├─ HTTP-сервер
               └─ Kafka Client ─────────┘
```

Ветвь базы данных и ветвь Kafka не зависят друг от друга, поэтому они могут инициализироваться конкурентно, пока не достигнут узла, требующего обеих.

Поскольку порядок зависимостей явный, запуск рантайма может планировать готовые узлы параллельно, вместо серийной инициализации всего приложения.

Это недооценённая выгода построения графа на этапе компиляции. Граф — не только структура поиска DI; это также план исполнения для инициализации и завершения.

Поэтому Kora может инициализировать независимые узлы жизненного цикла на виртуальных потоках, сохраняя при этом корректность зависимостей.

---

## `@KoraSubmodule`: масштабирование DI по модулям сборки { #kora-submodule }

Большие приложения часто охватывают несколько Gradle-модулей:

```text
application
├── payments
├── orders
├── catalog
└── users
```

`@KoraSubmodule` Kora предоставляет границу времени компиляции для этих случаев.

Модуль может объявить:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraSubmodule
    public interface PaymentsModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraSubmodule
    interface PaymentsModule
    ```

Kora обрабатывает компоненты и модули внутри этой единицы компиляции и генерирует интерфейс подмодуля, необходимый приложению.

Главное приложение затем компонует их:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        PaymentsModule,
        OrdersModule,
        CatalogModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        PaymentsModule,
        OrdersModule,
        CatalogModule
    ```

Во время выполнения по-прежнему существует один граф приложения, но работа обнаружения организована вокруг границ компиляции.

Это важно для инкрементальных сборок, потому что изменения внутри одного модуля проекта не обязательно требуют повторного обнаружения каждого компонента во всей кодовой базе. Поэтому граница модуля
помогает
не только организации кода, но и масштабируемости компиляции DI.

---

## Функции фреймворка используют тот же движок DI { #framework-features }

Контейнер не ограничен написанными вручную классами приложения.

Многие интеграции Kora участвуют в том же процессе разрешения.

Предположим, сгенерированному HTTP-обработчику требуется:

===! ":fontawesome-brands-java: `Java`"

    ```java
    JsonWriter<OrderResponse>
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    JsonWriter<OrderResponse>
    ```

но приложение не объявило такой компонент явно.

Расширение времени компиляции Kora может распознать, что запрошенная зависимость генерируема, создать необходимый JSON-писатель и вернуть результирующего провайдера обратно в граф DI.

Концептуально:

```text
нужен JsonWriter<OrderResponse>
        ↓
нет явного провайдера
        ↓
спросить расширения времени компиляции
        ↓
JSON-процессор может его сгенерировать
        ↓
сгенерировать $OrderResponse_JsonWriter
        ↓
зарегистрировать сгенерированного провайдера
        ↓
продолжить разрешение графа
```

Тот же паттерн используется репозиториями, декларативными HTTP-клиентами, маппингами конфигурации, валидацией, gRPC и другими сгенерированными функциями.

Это одна из самых важных архитектурных деталей в Kora. Компилятор DI и подсистемы генерации кода сотрудничают. Сгенерированная инфраструктура фреймворка становится обычными узлами графа, а
эти узлы разрешаются по тем же правилам типов и тегов, что и написанные вручную компоненты.

---

## DI времени компиляции как валидация архитектуры { #architecture-validation }

Когда все эти механизмы объединены, компиляция становится больше, чем проверкой синтаксиса и типов.

Kora может верифицировать такие вопросы, как: есть ли у каждой зависимости провайдер, неоднозначна ли зависимость, совпадают ли теги, конструируемы ли корни графа, существуют ли жёсткие циклы,
может ли быть произведена требуемая сгенерированная инфраструктура и может ли приложение сформировать валидный граф жизненного цикла.

Это архитектурные свойства.

Традиционный DI-фреймворк времени выполнения может не отвечать на них, пока не создан контекст приложения. Kora отвечает на большую их часть, пока компилятор уже обрабатывает исходный код.

Поэтому граница отказа смещается раньше:

```text
модель, ориентированная на рантайм:

компиляция
→ упаковка
→ сборка образа
→ развёртывание
→ запуск JVM
→ построение DI-контейнера
→ отказ
```

становится:

```text
модель Kora:

компиляция
→ разрешение графа терпит неудачу
→ диагностика
```

Вот почему DI времени компиляции не следует сводить к оптимизации запуска.

Более быстрый запуск ценен, но более глубокая выгода в том, что недопустимый граф приложения рассматривается гораздо больше как недопустимый исходный код.

---

## Что контейнер рантайма всё ещё делает { #runtime-container }

У Kora всё ещё есть контейнер зависимостей времени выполнения.

Его работа просто другая.

На этапе компиляции Kora определяет, какие провайдеры существуют, как разрешаются зависимости, как совпадают теги и кардинальности, какие компоненты достижимы, где существуют циклы и как связан
финальный
граф.

Во время выполнения исполнитель графа создаёт синглтоны, инициализирует компоненты с поддержкой жизненного цикла, хранит состояние узлов, обслуживает косвенные ссылки, такие как `ValueOf<T>`,
выполняет обновления графа, подменяет
обновлённые подграфы в живое приложение и освобождает компоненты в правильном порядке.

Полезный способ резюмировать разделение:

```text
время компиляции:
определить и валидировать граф приложения

рантайм:
исполнять и управлять этим графом
```

Это держит рантайм динамичным там, где состояние рантайма действительно имеет значение, не требуя от приложения повторного обнаружения собственной архитектуры при каждом запуске.

---

## Приложение — это граф { #application-is-graph }

Небольшое приложение Kora может выглядеть обманчиво простым:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
    }

    @Component
    public final class Controller {

        public Controller(Service service) {
        }
    }

    @Component
    public final class Service {

        public Service(Repository repository) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application

    @Component
    class Controller(service: Service)

    @Component
    class Service(repository: Repository)
    ```

Но этот исходный код уже кодирует существенный объём архитектуры.

`@KoraApp` определяет границу графа. Объявления `@Component` вводят провайдеров. Параметры конструкторов и фабрик определяют требования зависимостей. Теги уточняют идентичность. `All<T>` меняет
кардинальность. `ValueOf<T>` меняет связность жизненного цикла. `@Root` определяет активные точки входа графа. `Lifecycle` даёт узлам поведение запуска и завершения. Модули вносят дополнительных
провайдеров.
Расширения времени компиляции генерируют инфраструктуру, удовлетворяющую иначе неразрешённые зависимости.

Kora затем валидирует эти отношения и выдаёт результирующий граф приложения.

Полный процесс выглядит примерно так:

```text
объявления в исходном коде
        ↓
обнаружить провайдеров
        ↓
идентифицировать корни графа
        ↓
разрешить требования зависимостей
        ↓
применить типы, теги, значения по умолчанию и кардинальность
        ↓
сгенерировать компоненты, предоставляемые фреймворком
        ↓
обнаружить недостающие, неоднозначные или циклические зависимости
        ↓
сгенерировать ApplicationGraph
        ↓
скомпилировать
        ↓
рантайм инициализирует и управляет графом
```

Традиционное внедрение зависимостей часто описывают как контейнер, который находит объекты за вас.

Модель Kora точнее этого.

> **Компилятор доказывает, как приложение может быть собрано, генерирует этот граф сборки, а рантайм его исполняет.**

Это архитектурное различие за внедрением зависимостей времени компиляции в Kora.
