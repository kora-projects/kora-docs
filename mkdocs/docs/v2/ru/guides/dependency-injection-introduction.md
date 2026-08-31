---
search:
  exclude: true
title: Внедрение зависимостей в Kora
summary: Learn the fundamentals of Kora's compile-time dependency injection container - components, modules, roots, tags, and the generated application graph
description: "Conceptual introduction to Kora 2.0 compile-time dependency injection: how @KoraApp generates the application graph started through KoraApplication and ApplicationGraphDraw, the io.koraframework.common.annotation set (@Component, @Module, @KoraSubmodule, @Root, @DefaultComponent, @Tag, @Conditional, @FactoryModule), component discovery order and the dependency resolution algorithm, the claim kinds required, @Nullable, ValueOf, PromiseOf, All and TypeRef from io.koraframework.application.graph, tag matching with Tag.Any, Lifecycle init and release, and the graph build errors the compiler reports."
agent:
  use_when: "Use this file for questions about how Kora 2.0 compile-time dependency injection actually works: what @KoraApp generates and why nothing is built without @Root, @Component versus a @Module factory method versus @KoraSubmodule, @DefaultComponent priority, @Conditional, @FactoryModule, generic factories, @Tag and Tag.Any matching rules, claiming a dependency as required, @Nullable, ValueOf<T>, PromiseOf<T>, All<T> or TypeRef<T>, Lifecycle release order, and diagnosing 'No component found for dependency', 'Multiple components match dependency' and 'Circular dependency found' build failures."
tags: dependency-injection, di, kora-app, component, module, root, tag, compile-time
---

# Внедрение зависимостей в Kora { #dependency-injection-kora }

Это руководство знакомит с внедрением зависимостей и инверсией управления через контейнер Kora, который работает во время компиляции. В нем разбирается, как объекты приложения объявляют зависимости
через конструкторы, как `@Component` и `@Module` делают эти объекты доступными графу, как `@Root` определяет, что вообще будет создано, и как Kora проверяет связывание во время компиляции, а не
обнаруживает отсутствующие зависимости во время выполнения. Вы также увидите, почему внедрение зависимостей во время компиляции меняет поведение запуска, типобезопасность и тестируемость.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Dependency Injection Introduction App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection-introduction-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Dependency Injection Introduction App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-dependency-injection-introduction-app).

## Что вы изучите { #youll-learn }

Вы изучите основные понятия внедрения зависимостей и поймете:

- **Основы DI**: что такое внедрение зависимостей и почему оно важно
- **Архитектура Kora**: как работает внедрение зависимостей во время компиляции и в чем его преимущества
- **Корни графа**: почему именно `@Root` определяет, какие компоненты будут созданы
- **Жизненный цикл компонентов**: как компоненты создаются, инициализируются и освобождаются
- **Система модулей**: как организовывать и структурировать компоненты приложения
- **Теги и коллекции**: как различать несколько реализаций и собирать точки расширения
- **Лучшие практики**: приемы написания поддерживаемого и тестируемого кода

## Что потребуется { #youll-need }

- JDK 25 или новее, поскольку сама Kora 2.0 собирается под Java 25
- Gradle 9 или новее
- текстовый редактор или среда разработки
- базовое понимание Java или Kotlin

## Требования { #prerequisites }

!!! note "Предварительные знания не требуются"

    Это руководство рассчитано на новичков и не требует предварительного знания внедрения зависимостей или Kora.

    Достаточно базового знакомства с Java или Kotlin, потому что руководство вводит понятия внедрения зависимостей в Kora с самых основ, прежде чем показывать шаблоны, связанные с фреймворком.

## Обзор { #overview }

Внедрение зависимостей — это способ собирать приложение из явно объявленных зависимостей, вместо того чтобы позволять объектам самостоятельно создавать все, что им нужно. Зависимость — это просто «то,
что нужно классу для работы»: репозиторий, клиент, объект конфигурации, кеш, часы или другой сервис.

В маленькой программе естественно писать `new` повсюду. Контроллер может создать сервис, сервис может создать репозиторий, а репозиторий — все, что ему нужно. Но как только программа растет, это
становится трудно поддерживать:

- классы знают слишком много о том, как создаются другие классы
- тесты усложняются, потому что зависимости создаются внутри класса
- замена одной реализации требует правок во многих местах
- логика запуска расползается по кодовой базе
- детали конфигурации и инфраструктуры протекают в бизнес-код

Внедрение зависимостей исправляет это, меняя правило: класс не должен создавать своих соисполнителей. Он должен объявить, что ему нужно, обычно через конструктор, и позволить графу приложения
предоставить эти объекты.

### Маленький пример { #small-example }

Без внедрения зависимостей сервис может создавать свой репозиторий напрямую:

```java
public final class UserService {
    private final UserRepository repository = new InMemoryUserRepository();
}
```

Это выглядит просто, но теперь `UserService` привязан к одной реализации репозитория. Тест не может легко ее заменить. Будущий репозиторий поверх базы данных не подключить без правки сервиса.

При внедрении через конструктор сервис только объявляет зависимость:

```java
public final class UserService {
    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }
}
```

Теперь `UserService` не важно, хранит ли репозиторий данные в памяти, работает ли через JDBC, подменяется ли в тесте или обернут кешированием. Это решение переезжает в граф приложения.

### Графы объектов { #object-graphs }

Приложение — это не просто набор классов. Это граф объектов, соединенных зависимостями. Например:

```text
UserController
  -> UserService
      -> UserRepository
      -> UserValidator
```

Это называется графом зависимостей или графом объектов. Каждая стрелка означает «этому объекту нужен тот объект». Главная задача Kora — корректно построить этот граф, запустить компоненты с жизненным
циклом в правильном порядке и завершить сборку ошибкой, если граф невозможно собрать.

Мышление графами — одно из самых важных понятий Kora. Когда вы добавляете контроллер, репозиторий, HTTP-клиент, кеш или объект конфигурации, вы добавляете в граф узел или ребро.

### Инверсия управления { #inversion-control }

Более глубокая идея за внедрением зависимостей — инверсия управления. Вместо того чтобы сервис решал, как построить репозиторий, клиент, кеш или конфигурацию, он лишь объявляет, что они ему нужны.
Создание объектов уходит из сервиса в граф приложения.

Это меняет форму кода приложения:

- конструкторы описывают обязательных соисполнителей
- интерфейсы делают точки замены явными
- тесты могут предоставить заглушки или альтернативные реализации
- связывание при запуске становится задачей, отделенной от бизнес-логики

### Внедрение зависимостей в Kora { #dependency-injection-kora-2 }

[Контейнер Kora, работающий во время компиляции](../documentation/container.md), реализует внедрение зависимостей на этапе сборки. Интерфейс `@KoraApp` помечает корень графа, `@Component` помечает
классы, которыми управляет граф, `@Root` помечает точки входа, которые обязаны существовать, а `@Module` добавляет фабрики или возможности фреймворка. Во время компиляции Kora анализирует граф и
генерирует обычный код на Java или Kotlin, который создает и соединяет компоненты. Во время выполнения ничего не ищется через рефлексию.

Это дает Kora другую модель отказов по сравнению с фреймворками, которые собирают контейнер во время выполнения. Отсутствующие зависимости, неоднозначные связывания, циклы и недостижимые корни
обнаруживаются во время сборки, а не при запуске приложения.

Для новичков самые важные аннотации:

- `@KoraApp`: корневой интерфейс графа приложения
- `@Component`: класс, который Kora может создать автоматически
- `@Module`: набор фабрик компонентов или подключаемых модулей фреймворка
- `@Root`: компонент, который создается, даже если от него никто не зависит

Можно думать об `@KoraApp` как о карте приложения, о `@Component` — как об узле графа, о `@Root` — как о точках входа на карту, а о параметрах конструктора — как о стрелках между узлами.

Все эти аннотации лежат в одном пакете, `io.koraframework.common.annotation`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.DefaultComponent;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.common.annotation.KoraSubmodule;
    import io.koraframework.common.annotation.Module;
    import io.koraframework.common.annotation.Root;
    import io.koraframework.common.annotation.Tag;
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.DefaultComponent
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.common.annotation.KoraSubmodule
    import io.koraframework.common.annotation.Module
    import io.koraframework.common.annotation.Root
    import io.koraframework.common.annotation.Tag
    ```

Типы времени выполнения, которые описывают отношения в графе — `All`, `ValueOf`, `PromiseOf`, `TypeRef`, `Lifecycle` и точка входа `KoraApplication` — находятся в `io.koraframework.application.graph`.

### Внедрение во время компиляции { #compile-time-injection }

Внедрение зависимостей во время компиляции означает, что Kora проверяет и генерирует связывание во время сборки. Это важно, потому что многие ошибки внедрения зависимостей — структурные:

- у обязательной зависимости нет поставщика
- два поставщика подходят под одну зависимость, и Kora не может выбрать
- модуль не подключен к приложению
- компонент зависит от компонента, который невозможно построить
- в приложении не объявлено ни одного корня, поэтому строить нечего

Во фреймворке, который собирает контейнер во время выполнения, часть таких ошибок проявляется только при запуске. В Kora сборка падает раньше, до упаковки и развертывания приложения. Это ускоряет
обратную связь и делает запуск в рабочем окружении предсказуемым.

Сгенерированный граф — обычный байт-код. Нет сканирования classpath, нет поиска конструкторов через рефлексию и нет генерации прокси при старте, поэтому запуск остается быстрым, а приложение — дружелюбным
к ahead-of-time компиляции.

### Область обнаружения { #discovery-scope }

Kora не сканирует вслепую каждый класс в classpath. Компоненты обнаруживаются в Gradle-модулях, которые содержат интерфейсы `@KoraApp` или `@KoraSubmodule`. Компоненты из внешних библиотек тоже не
становятся доступными автоматически только потому, что лежат в JAR. Обычно библиотека предоставляет интерфейс модуля, а приложение подключает его, унаследовав от `@KoraApp`.

Эта явность важна: она сохраняет граф предсказуемым, делает границы модулей видимыми и исключает случайную регистрацию компонентов.

Практический порядок изучения:

1. понять, почему ручное создание объектов становится болезненным
2. разобраться, что такое зависимость
3. ввести внедрение через конструктор
4. связать внедрение зависимостей с графами объектов и инверсией управления
5. сравнить контейнер времени выполнения с графом Kora, который строится во время компиляции
6. узнать, как Kora обнаруживает компоненты и модули
7. увидеть, почему сгенерированный код графа улучшает обратную связь по связыванию

---

## Основы DI { #di-basics }

Этот раздел дает подробное введение во внедрение зависимостей (DI) и принципы инверсии управления (IoC) на примере фреймворка Kora. Независимо от того, знакомитесь ли вы с этими понятиями впервые или
хотите углубить понимание, раздел последовательно выстраивает знания от фундаментальных принципов до практической реализации.

### Что такое внедрение зависимостей? { #dependency-injection }

**Внедрение зависимостей** — это базовый шаблон проектирования, который отвечает на вопрос, как компоненты получают свои зависимости и управляют ими. По сути DI разделяет создание зависимостей и их
использование, что делает архитектуру кода гибче и удобнее в сопровождении.

**Основная идея**: вместо того чтобы компонент создавал свои зависимости, они предоставляются (внедряются) извне. Этим внешним источником обычно выступает фреймворк или контейнер внедрения
зависимостей.

**Базовый пример**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Traditional approach - component creates its own dependencies
    public class OrderProcessor {
        private Database database = new Database();        // Component creates dependency
        private EmailService emailService = new EmailService();

        public void processOrder(Order order) {
            database.save(order);
            emailService.sendConfirmation(order.getCustomerEmail());
        }
    }

    // Dependency injection approach - dependencies are provided
    public class OrderProcessor {
        private final Database database;
        private final EmailService emailService;

        // Dependencies are injected through constructor
        public OrderProcessor(Database database, EmailService emailService) {
            this.database = database;
            this.emailService = emailService;
        }

        public void processOrder(Order order) {
            database.save(order);
            emailService.sendConfirmation(order.getCustomerEmail());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Traditional approach - component creates its own dependencies
    class OrderProcessor {
        private val database = Database()        // Component creates dependency
        private val emailService = EmailService()

        fun processOrder(order: Order) {
            database.save(order)
            emailService.sendConfirmation(order.customerEmail)
        }
    }

    // Dependency injection approach - dependencies are provided
    class OrderProcessor(
        private val database: Database,
        private val emailService: EmailService
    ) {
        // Dependencies are injected through primary constructor

        fun processOrder(order: Order) {
            database.save(order)
            emailService.sendConfirmation(order.customerEmail)
        }
    }
    ```

**Ключевые термины**:

- **Зависимость**: любой объект или сервис, который нужен компоненту для работы
- **Внедрение**: процесс предоставления зависимостей компоненту
- **Контейнер**: механизм, отвечающий за создание и внедрение зависимостей
- **Заявка на зависимость (dependency claim)**: в Kora это конкретный запрос параметра конструктора — тип, необязательный тег и необязательная обертка вроде `All<T>` или `ValueOf<T>`

### Проблемы традиционных подходов { #traditional-approach-problems }

Чтобы понять, зачем нужно внедрение зависимостей, разберем сложности, которые возникают без него, и то, как DI их решает.

**Проблема: сильная связанность**

Сильная связанность возникает, когда компоненты напрямую зависят от конкретных реализаций, из-за чего система становится жесткой и трудной в сопровождении. Типичный пример:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class UserService {
        private DatabaseConnection connection = new DatabaseConnection();  // Direct instantiation

        public User findUserById(long id) {
            return connection.query("SELECT * FROM users WHERE id = ?", id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class UserService {
        private val connection = DatabaseConnection()  // Direct instantiation

        fun findUserById(id: Long): User {
            return connection.query("SELECT * FROM users WHERE id = ?", id)
        }
    }
    ```

Чем плоха сильная связанность:

1. Сложность тестирования: `UserService` нельзя протестировать изолированно, потому что он сам создает `DatabaseConnection`
2. Привязка к реализации: переход на другую базу данных требует правки кода `UserService`
3. Скрытые зависимости: конструктор ничего не сообщает о том, что на самом деле нужно сервису
4. Управление ресурсами: каждый экземпляр создает собственное соединение с базой данных
5. Проблемы конфигурации: настроить соединение снаружи невозможно

### Преимущества внедрения зависимостей { #dependency-injection-benefits }

**Решение через внедрение зависимостей**:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class UserService {
        private final DatabaseConnection connection;

        // Dependencies are explicitly declared
        public UserService(DatabaseConnection connection) {
            this.connection = connection;
        }

        public User findUserById(long id) {
            return connection.query("SELECT * FROM users WHERE id = ?", id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class UserService(
        private val connection: DatabaseConnection
    ) {
        // Dependencies are explicitly declared in primary constructor

        fun findUserById(id: Long): User {
            return connection.query("SELECT * FROM users WHERE id = ?", id)
        }
    }
    ```

**Ключевые преимущества внедрения зависимостей**:

1. **Тестируемость**: компоненты можно тестировать с заглушками

===! ":fontawesome-brands-java: `Java`"

       ```java
       @Test
       public void testUserService() {
           DatabaseConnection mockConnection = mock(DatabaseConnection.class);
           UserService service = new UserService(mockConnection);
           // Test the service logic without database dependencies
       }
       ```

=== ":simple-kotlin: `Kotlin`"

       ```kotlin
       @Test
       fun testUserService() {
           val mockConnection = mock(DatabaseConnection::class.java)
           val service = UserService(mockConnection)
           // Test the service logic without database dependencies
       }
       ```

2. **Гибкость**: разные реализации можно подставлять в зависимости от окружения

===! ":fontawesome-brands-java: `Java`"

       ```java
       // Production environment
       DatabaseConnection prodConnection = new PostgreSQLConnection();
       UserService prodService = new UserService(prodConnection);

       // Test environment
       DatabaseConnection testConnection = new InMemoryDatabaseConnection();
       UserService testService = new UserService(testConnection);
       ```

=== ":simple-kotlin: `Kotlin`"

       ```kotlin
       // Production environment
       val prodConnection = PostgreSQLConnection()
       val prodService = UserService(prodConnection)

       // Test environment
       val testConnection = InMemoryDatabaseConnection()
       val testService = UserService(testConnection)
       ```

3. **Явные зависимости**: параметры конструктора прямо документируют требования
4. **Управление ресурсами**: жизненным циклом соединений можно управлять снаружи
5. **Конфигурация**: настройки базы данных задаются на уровне приложения

### Понимание инверсии управления { #understanding-inversion-control }

**Инверсия управления** — это архитектурный принцип, лежащий в основе внедрения зависимостей. IoC меняет то, как в системе устроен поток управления.

**Традиционный поток управления**:

```
Application Code -> Creates Objects -> Manages Dependencies -> Executes Business Logic
```

**Инвертированный поток управления**:

```
Framework/Container -> Creates Objects -> Injects Dependencies -> Application Code Executes Business Logic
```

**Принцип инверсии**:

В традиционном программировании код приложения отвечает за:

- создание всех необходимых объектов
- управление жизненным циклом объектов
- координацию компонентов
- обработку конфигурации

При IoC эти обязанности переходят к фреймворку:

- фреймворк создает объекты
- фреймворк управляет жизненным циклом
- фреймворк координирует компоненты
- фреймворк работает с конфигурацией

Способы реализации IoC:

1. Фабрика: централизованное создание объектов
2. Service Locator: компоненты сами запрашивают зависимости в центральном реестре
3. Внедрение зависимостей: зависимости передаются компоненту извне

Почему IoC важна:

IoC дает несколько важных архитектурных преимуществ:

- Разделение ответственностей: бизнес-логика отделена от инфраструктуры
- Модульность: компоненты можно разрабатывать и тестировать независимо
- Сопровождаемость: изменения в инфраструктуре не задевают бизнес-логику
- Тестируемость: компоненты легко изолировать для тестов

В коде:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Traditional approach - you control all object creation
    public class Application {
        public static void main(String[] args) {
            Database db = new Database();           // You create
            EmailService email = new EmailService(); // You create
            OrderService service = new OrderService(db, email); // You create

            service.processOrder(order); // You control
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Traditional approach - you control all object creation
    fun main() {
        val db = Database()           // You create
        val email = EmailService()    // You create
        val service = OrderService(db, email) // You create

        service.processOrder(order) // You control
    }
    ```

### Когда старые подходы ломаются { #old-approaches-break }

Традиционный подход с ручным созданием и связыванием зависимостей отлично работает в маленьких приложениях из нескольких классов, но становится все более проблемным, когда приложение вырастает до
десятков или сотен компонентов.

**Почему масштаб важен:**

Традиционный подход требует вручную создать и связать каждый объект приложения. Для приложения из 3–5 классов это тривиально. Но когда классов 20, 50 или больше сотни, ручное связывание превращается в
кошмар сопровождения.

**Пример: приложение из 20+ классов (традиционный подход)**

Представьте приложение со следующими компонентами:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class EcommerceApplication {
        public static void main(String[] args) {
            // Infrastructure Layer (8 classes)
            DatabaseConfig dbConfig = new DatabaseConfig("localhost", "ecommerce", "user", "pass");
            DatabaseConnection dbConnection = new DatabaseConnection(dbConfig);
            RedisConfig redisConfig = new RedisConfig("localhost", 6379);
            RedisConnection redisConnection = new RedisConnection(redisConfig);
            EmailConfig emailConfig = new EmailConfig("smtp.example.com", 587, "user@example.com");
            EmailService emailService = new EmailService(emailConfig);
            PaymentGatewayConfig paymentConfig = new PaymentGatewayConfig("payment_key_123");
            PaymentGateway paymentGateway = new PaymentGateway(paymentConfig);

            // Data Access Layer (6 classes)
            UserRepository userRepository = new UserRepository(dbConnection);
            ProductRepository productRepository = new ProductRepository(dbConnection);
            OrderRepository orderRepository = new OrderRepository(dbConnection);
            CartRepository cartRepository = new CartRepository(redisConnection);
            AuditRepository auditRepository = new AuditRepository(dbConnection);
            InventoryRepository inventoryRepository = new InventoryRepository(dbConnection);

            // Business Logic Layer (8 classes)
            UserService userService = new UserService(userRepository, emailService);
            ProductService productService = new ProductService(productRepository, inventoryRepository);
            CartService cartService = new CartService(cartRepository, productService);
            OrderService orderService = new OrderService(orderRepository, paymentGateway, emailService);
            PaymentService paymentService = new PaymentService(paymentGateway, orderRepository);
            InventoryService inventoryService = new InventoryService(inventoryRepository, productRepository);
            AuditService auditService = new AuditService(auditRepository);
            NotificationService notificationService = new NotificationService(emailService);

            // Presentation Layer (4 classes)
            UserController userController = new UserController(userService, auditService);
            ProductController productController = new ProductController(productService, auditService);
            OrderController orderController = new OrderController(orderService, cartService, auditService);
            CartController cartController = new CartController(cartService, auditService);

            // Application Bootstrap (2 classes)
            // ... and more
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun main() {
        // Infrastructure Layer (8 classes)
        val dbConfig = DatabaseConfig("localhost", "ecommerce", "user", "pass")
        val dbConnection = DatabaseConnection(dbConfig)
        val redisConfig = RedisConfig("localhost", 6379)
        val redisConnection = RedisConnection(redisConfig)
        val emailConfig = EmailConfig("smtp.example.com", 587, "user@example.com")
        val emailService = EmailService(emailConfig)
        val paymentConfig = PaymentGatewayConfig("payment_key_123")
        val paymentGateway = PaymentGateway(paymentConfig)

        // Data Access Layer (6 classes)
        val userRepository = UserRepository(dbConnection)
        val productRepository = ProductRepository(dbConnection)
        val orderRepository = OrderRepository(dbConnection)
        val cartRepository = CartRepository(redisConnection)
        val auditRepository = AuditRepository(dbConnection)
        val inventoryRepository = InventoryRepository(dbConnection)

        // Business Logic Layer (8 classes)
        val userService = UserService(userRepository, emailService)
        val productService = ProductService(productRepository, inventoryRepository)
        val cartService = CartService(cartRepository, productService)
        val orderService = OrderService(orderRepository, paymentGateway, emailService)
        val paymentService = PaymentService(paymentGateway, orderRepository)
        val inventoryService = InventoryService(inventoryRepository, productRepository)
        val auditService = AuditService(auditRepository)
        val notificationService = NotificationService(emailService)

        // Presentation Layer (4 classes)
        val userController = UserController(userService, auditService)
        val productController = ProductController(productService, auditService)
        val orderController = OrderController(orderService, cartService, auditService)
        val cartController = CartController(cartService, auditService)

        // Application Bootstrap (2 classes)
        // ... and more
    }
    ```

**Со 100+ классами это становится невозможным:**

- метод `main` разрастается до тысячи с лишним строк
- чтобы понять граф зависимостей, нужна отдельная схема
- порядок создания компонентов приходится соблюдать вручную
- добавление одной возможности требует правок в десятках файлов
- изменение одного компонента требует понимания всей его цепочки зависимостей
- тестирование любого компонента требует создания сотен объектов
- одно изменение конфигурации расходится по всему приложению
- новая возможность требует правки `main` и легко ломает существующий порядок инициализации

**Решение через внедрение зависимостей:**

При DI зависимости объявляются на уровне компонента, а всю сложность берет на себя фреймворк:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface EcommerceApplication extends
        InfrastructureModule, DataAccessModule, BusinessLogicModule, PresentationModule {

        static void main(String[] args) {
            KoraApplication.run(EcommerceApplicationGraph::graph);
        }
    }

    // Each component just declares what it needs
    @Component
    public final class OrderService {
        private final OrderRepository orderRepository;
        private final PaymentGateway paymentGateway;
        private final EmailService emailService;

        public OrderService(OrderRepository orderRepository,
                            PaymentGateway paymentGateway,
                            EmailService emailService) {
            this.orderRepository = orderRepository;
            this.paymentGateway = paymentGateway;
            this.emailService = emailService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface EcommerceApplication :
        InfrastructureModule, DataAccessModule, BusinessLogicModule, PresentationModule

    fun main() {
        KoraApplication.run(EcommerceApplicationGraph::graph)
    }

    // Each component just declares what it needs
    @Component
    class OrderService(
        private val orderRepository: OrderRepository,
        private val paymentGateway: PaymentGateway,
        private val emailService: EmailService
    )
    ```

**Фреймворк автоматически:**

- создает все объекты в правильном порядке
- управляет жизненным циклом ресурсов
- внедряет конфигурацию
- разрешает зависимости
- упрощает тестирование с заглушками

Именно поэтому внедрение зависимостей становится необходимым, как только приложение выходит за пределы пары классов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    // IoC/DI (framework controls object creation)
    @KoraApp
    public interface Application {

        // Framework creates and injects everything reachable from a root
        @Root
        default OrderService orderService(OrderRepository repository) {
            return new OrderService(repository);
        }

        static void main(String[] args) {
            // Framework handles all object creation and injection
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // IoC/DI (framework controls object creation)
    @KoraApp
    interface Application {

        // Framework creates and injects everything reachable from a root
        @Root
        fun orderService(repository: OrderRepository): OrderService = OrderService(repository)
    }

    fun main() {
        // Framework handles all object creation and injection
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Сравнение подходов:

| Аспект           | Традиционный подход                        | Внедрение зависимостей                       |
|------------------|--------------------------------------------|----------------------------------------------|
| Тестирование     | Сложно (используются реальные сервисы)     | Просто (подставляются заглушки)              |
| Гибкость         | Низкая (зависимости зашиты в код)          | Высокая (внедряется любая реализация)        |
| Переиспользуемость | Низкая (привязка к конкретным реализациям) | Высокая (работает с любым совместимым сервисом) |
| Сопровождаемость | Низкая (правки затрагивают много мест)     | Высокая (меняется связывание, а не код)      |
| Понятность       | Низкая (зависимости скрыты)                | Высокая (конструктор показывает потребности) |

Теперь, когда основы понятны, посмотрим, как Kora реализует эти идеи через внедрение зависимостей во время компиляции.

---

## Архитектура Kora { #kora-architecture }

Kora использует внедрение зависимостей во время компиляции, а значит:

1. Анализ на этапе сборки: зависимости анализируются во время компиляции обработчиком аннотаций (Java) или символьным процессором KSP (Kotlin)
2. Обнаружение компонентов: собираются классы с `@Component`, интерфейсы `@Module` и фабричные методы, доступные из `@KoraApp`
3. Выбор корней: разрешение начинается с объявлений `@Root` и дальше идет по ребрам зависимостей
4. Разрешение зависимостей: обработчик разрешает каждую заявку, находит циклы и строит ациклический граф
5. Генерация кода: класс `<ИмяПриложения>Graph` генерируется как обычный исходник на Java/Kotlin и создает `ApplicationGraphDraw`
6. Производительность: ни рефлексии, ни сканирования classpath — все разрешено во время компиляции

> Важное ограничение области: обработчики Kora сканируют только те Gradle-модули, которые содержат интерфейсы `@KoraApp` или `@KoraSubmodule`. Компоненты в обычных Gradle-модулях без этих
> интерфейсов не будут обнаружены и обработаны системой внедрения зависимостей.

### Как работает в Kora { #it-works-kora }

1. Обработка аннотаций: интерфейсы `@KoraApp` обрабатываются во время компиляции классом `KoraAppProcessor`
2. Обнаружение компонентов: собираются классы `@Component`, интерфейсы `@Module`, методы, унаследованные `@KoraApp`, и сгенерированные подмодули текущего Gradle-модуля
3. Разрешение зависимостей: `GraphBuilder` разрешает каждую заявку, начиная с набора корней, и обнаруживает циклы
4. Генерация графа: генерируется класс `<ИмяПриложения>Graph`, который содержит по одному `Node` на компонент и логику их инициализации
5. Выполнение: `KoraApplication.run(...)` инициализирует компоненты в порядке зависимостей и ставит shutdown-хук

> Критичное ограничение области: обработчики Kora работают только внутри Gradle-модулей с интерфейсами `@KoraApp` или `@KoraSubmodule`. Компоненты в обычных Gradle-модулях без этих
> интерфейсов полностью игнорируются системой внедрения зависимостей.

Архитектурные преимущества явного контроля:
Это осознанное решение дает вам полный контроль над графом зависимостей приложения. В отличие от фреймворков, которые создают все найденное в classpath, Kora требует явно объявить нужные компоненты.
Это исключает:

- расход ресурсов на ненужные компоненты
- риски безопасности от компонентов, приезжающих транзитивно
- сложность отладки из-за неизвестных работающих компонентов
- накладные расходы на сканирование classpath
- непредсказуемое поведение при смене зависимостей

В Kora интерфейс `@KoraApp` служит явным манифестом всего, что работает в вашем приложении.

### Сгенерированный код { #generated-code }

Когда интерфейс помечен `@KoraApp`, обработчик генерирует рядом с ним два типа:

- `$<ИмяПриложения>Impl` — класс, реализующий интерфейс приложения; через него вызываются ваши фабричные методы
- `<ИмяПриложения>Graph` — `Supplier<ApplicationGraphDraw>`, который строит описание графа и предоставляет статический метод `graph()` в качестве точки входа

Упрощенный набросок того, что генерируется для интерфейса `Application`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Generated at compile time, in the same package as Application
    public class ApplicationGraph implements Supplier<ApplicationGraphDraw> {

        private static final ApplicationGraphDraw graphDraw;
        private static final ComponentHolder0 holder0;

        static {
            var impl = new $ApplicationImpl();                            //(1)!
            graphDraw = new ApplicationGraphDraw(Application.class);
            holder0 = new ComponentHolder0(graphDraw, impl);              //(2)!
        }

        public static ApplicationGraphDraw graph() {                      //(3)!
            return graphDraw;
        }

        @Override
        public ApplicationGraphDraw get() {
            return graphDraw;
        }

        public static final class ComponentHolder0 {
            private final Node<MessageFormatter> component0;              //(4)!
            private final Node<EmailNotifier> component1;
            // one Node per component in the graph
        }
    }
    ```

    1. Реализация вашего интерфейса `@KoraApp`; именно она вызывает ваши `default`-фабрики.
    2. Компоненты регистрируются в пронумерованных классах-держателях, по 500 компонентов в каждом, чтобы очень большие графы продолжали компилироваться.
    3. Статический метод, на который ссылаются как `ApplicationGraph::graph` при запуске приложения.
    4. Каждый компонент становится `Node<T>`, который знает свою фабрику, зависимости создания и зависимости обновления.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Generated at compile time, in the same package as Application
    class ApplicationGraph : Supplier<ApplicationGraphDraw> {

        override fun get(): ApplicationGraphDraw = graphDraw

        companion object {
            val graphDraw: ApplicationGraphDraw

            init {
                val impl = `$ApplicationImpl`()                            //(1)!
                graphDraw = ApplicationGraphDraw(Application::class.java)
                holder0 = ComponentHolder0(graphDraw, impl)                //(2)!
            }

            fun graph(): ApplicationGraphDraw = graphDraw                  //(3)!
        }

        class ComponentHolder0(graphDraw: ApplicationGraphDraw, impl: `$ApplicationImpl`) {
            val component0: Node<MessageFormatter>                         //(4)!
            val component1: Node<EmailNotifier>
            // one Node per component in the graph
        }
    }
    ```

    1. Реализация вашего интерфейса `@KoraApp`; именно она вызывает ваши фабричные функции интерфейса.
    2. Компоненты регистрируются в пронумерованных классах-держателях, по 500 компонентов в каждом, чтобы очень большие графы продолжали компилироваться.
    3. Функция, на которую ссылаются как `ApplicationGraph::graph` при запуске приложения.
    4. Каждый компонент становится `Node<T>`, который знает свою фабрику, зависимости создания и зависимости обновления.

Этот класс никогда не пишут вручную, но знать о нем полезно: это обычный исходный код, который лежит в `build/generated`, открывается в IDE, проходится отладчиком и объясняет любое непонятное решение
о связывании.

### Compile Time и Runtime { #compile-time-runtime }

**Compile time (обработка аннотаций):**

- анализирует исходный код на компоненты и зависимости только в модулях с `@KoraApp`/`@KoraSubmodule`
- проверяет граф зависимостей (нет циклов, все зависимости доступны, есть хотя бы один корень)
- генерирует оптимизированный код инициализации
- дает проверки на этапе компиляции

**Runtime (выполнение приложения):**

- выполняет сгенерированный код инициализации
- инициализирует каждый узел на отдельном виртуальном потоке с учетом порядка зависимостей, поэтому независимые ветви стартуют параллельно
- управляет жизненным циклом компонентов через `Lifecycle`
- обеспечивает корректное завершение через shutdown-хук, который ставит `KoraApplication.run(...)`
- поддерживает обновление компонентов через `ValueOf<T>`, когда источник вроде наблюдателя за конфигурацией сообщает об изменении

> **Важно про область**: обработка на этапе компиляции происходит только в Gradle-модулях с интерфейсами `@KoraApp` или `@KoraSubmodule`. Код в обычных модулях не анализируется и не обрабатывается.

Код приложения остается синхронным. Kora 2.0 исполняет блокирующий код на виртуальных потоках и не требует моделировать все через реактивные потоки или корутины, поэтому метод компонента — это обычный
метод, а конструктор — обычный конструктор.

### Обработчики аннотаций { #annotation-processors }

Обработка на этапе компиляции состоит из:

1. `KoraAppProcessor`: основной обработчик `@KoraApp`, `@Module`, `@Component`
2. `KoraSubmoduleProcessor`: генерирует интерфейс `<Имя>SubmoduleImpl` для каждого `@KoraSubmodule`
3. `GraphBuilder`: разрешает заявки на зависимости, начиная с набора корней, находит циклы и упорядочивает компоненты
4. `ComponentDependencyHelper`: разбирает заявки из параметров конструкторов и фабричных методов
5. Расширения: подключаемый механизм, который генерирует компоненты по запросу (`JsonReader`/`JsonWriter`, репозитории, HTTP-клиенты, извлекатели конфигурации, валидаторы, мапперы)

Обработчики подключаются в сборке так:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        annotationProcessor "io.koraframework:annotation-processors"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        ksp("io.koraframework:symbol-processors")
    }
    ```

> Ограничение области: обработчики Kora включаются и работают только внутри Gradle-модулей с интерфейсами `@KoraApp` или `@KoraSubmodule`. Код в обычных Gradle-модулях для них полностью невидим.

### Порядок обнаружения компонентов { #component-discovery-order }

Прежде чем что-либо разрешать, обработчик собирает все объявления, видимые для текущего `@KoraApp`:

1. Классы с аннотацией `@Component` в текущем Gradle-модуле
2. Фабричные методы самого интерфейса `@KoraApp` и всех интерфейсов, которые он наследует, независимо от того, помечены ли они `@Module`
3. Фабричные методы интерфейсов с `@Module`, найденных в текущем Gradle-модуле, включая унаследованные методы
4. Фабричные методы интерфейсов `<Имя>SubmoduleImpl`, сгенерированных из `@KoraSubmodule` и унаследованных от `@KoraApp`
5. Фабричные методы вложенных модулей, подключенных через `@FactoryModule`
6. Компоненты, сгенерированные расширениями по ходу разрешения графа

Объявления с обобщенными параметрами хранятся отдельно как *шаблоны компонентов* и материализуются только тогда, когда запрошен конкретный тип.

> Замечание про область: обнаружение компонентов происходит только внутри Gradle-модулей с интерфейсами `@KoraApp` или `@KoraSubmodule`. Компоненты в обычных Gradle-модулях не будут обнаружены,
> какие бы аннотации на них ни стояли.

### Алгоритм разрешения зависимостей { #dependency-resolution-algorithm }

1. Набор корней: собираются все объявления с `@Root`; если набор пуст, сборка падает с `@KoraApp has no root components`
2. Разбор заявок: каждый параметр конструктора или фабричного метода превращается в `DependencyClaim` — тип, необязательный тег и вид заявки: обязательная, обнуляемая, `ValueOf`, `PromiseOf` или `All`
3. Поиск кандидатов: отбираются объявления, тип которых совместим с типом заявки, а тег совпадает с тегом заявки
4. Разрешение конфликтов: если подходит несколько, побеждают кандидаты без `@DefaultComponent`; если остается больше одного, сборка падает
5. Поиск циклов: цикл ломает сборку, если только ребро цикла не объявлено через интерфейс (или нефинальный класс) — в этом случае Kora генерирует делегирующий прокси
6. Генерация кода: узлы регистрируются в топологическом порядке, чтобы каждая зависимость была зарегистрирована раньше потребителя

В граф попадают только компоненты, достижимые из набора корней. Фабричный метод, от которого никто не зависит, никогда не вызывается — поэтому точкам входа вроде серверов и консьюмеров нужен `@Root`.

---

## Основные аннотации { #core-annotations }

Kora предоставляет несколько ключевых аннотаций внедрения зависимостей, и все они лежат в `io.koraframework.common.annotation`:

### `@KoraApp` { #koraapp }

Помечает главный интерфейс приложения и является ядром контейнера зависимостей Kora. Внутри этого интерфейса объявляются фабричные методы компонентов и подключаются модули. Каждый такой интерфейс порождает
собственный граф зависимостей, и в приложении обычно объявляют ровно один.

Что делает `@KoraApp`:

- Точка входа контейнера: задает корень контейнера зависимостей приложения
- Реестр компонентов: регистрирует все фабричные методы и доступы к компонентам
- Интеграция модулей: подключает внешние модули через наследование интерфейсов
- Запуск приложения: дает стартовую точку для `KoraApplication.run(...)`

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
        // Factory methods and component accessors

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {
        // Factory methods and component accessors
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

**Требования:**

- Должен быть интерфейсом, а не классом — `@KoraApp` на классе падает с ошибкой `@KoraApp can only be applied to interfaces`
- Один на граф приложения; обработчик генерирует отдельный класс графа для каждого найденного интерфейса `@KoraApp`
- Может наследовать несколько интерфейсов-модулей
- Должен доставать хотя бы до одного объявления `@Root`, иначе сборка падает с `@KoraApp has no root components`

**Как строится контейнер:**
Во время компиляции Kora использует интерфейс `@KoraApp`, чтобы:

1. Обнаружить все фабричные методы и зависимости компонентов
2. Проверить граф зависимостей на циклы и отсутствующие компоненты
3. Сгенерировать оптимизированный код инициализации
4. Создать класс `<ИмяПриложения>Graph`, используемый во время выполнения

**Почему интерфейсы? Множественное наследование и контроль над переопределением фабрик**

Kora требует, чтобы `@KoraApp` и все модули были интерфейсами, а не классами, и на то есть архитектурные причины, которые как раз и дают гибкость внедрения зависимостей.

**Множественное наследование**: интерфейсы поддерживают множественное наследование, поэтому приложение собирается из нескольких модулей:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface EcommerceApplication extends
        UndertowPublicHttpServerModule,   // HTTP server capabilities
        JdbcDatabaseModule,               // Database connectivity
        CaffeineCacheModule,              // Caching services
        HoconConfigModule {               // Configuration

        // Your application-specific factories
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface EcommerceApplication :
        UndertowPublicHttpServerModule,   // HTTP server capabilities
        JdbcDatabaseModule,               // Database connectivity
        CaffeineCacheModule,              // Caching services
        HoconConfigModule {               // Configuration

        // Your application-specific factories
    }
    ```

**Переопределение фабричного метода**: методы интерфейса с реализацией по умолчанию можно переопределить, и это дает контроль над внедрением зависимостей средствами самого языка:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Library provides default implementation
    @Module
    public interface CacheModule {
        @DefaultComponent
        default Cache cache() {
            return new InMemoryCache(); // Default implementation
        }
    }

    // Your application can override with custom implementation
    @KoraApp
    public interface Application extends CacheModule {  // <----- Connected module
        @Override
        default Cache cache() {
            return new RedisCache(); // Override with Redis
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Library provides default implementation
    @Module
    interface CacheModule {
        @DefaultComponent
        fun cache(): Cache = InMemoryCache() // Default implementation
    }

    // Your application can override with custom implementation
    @KoraApp
    interface Application : CacheModule {  // <----- Connected module
        override fun cache(): Cache = RedisCache() // Override with Redis
    }
    ```

**Компонент как фабричный метод**: компоненты — это не только классы, их можно объявлять фабричными методами в интерфейсах, декларативно управляя IoC:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
        // Component defined as factory method (not a class)
        default UserService userService(UserRepository repository, EmailService email) {
            // You control exactly how UserService is created
            var service = new UserService(repository, email);
            service.setTimeout(Duration.ofSeconds(30)); // Custom configuration
            return service;
        }

        // Another component as factory method
        default OrderProcessor orderProcessor(UserService userService, PaymentService payment) {
            return new OrderProcessor(userService, payment, new OrderValidator());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {
        // Component defined as factory method (not a class)
        fun userService(repository: UserRepository, email: EmailService): UserService {
            // You control exactly how UserService is created
            val service = UserService(repository, email)
            service.setTimeout(Duration.ofSeconds(30)) // Custom configuration
            return service
        }

        // Another component as factory method
        fun orderProcessor(userService: UserService, payment: PaymentService): OrderProcessor =
            OrderProcessor(userService, payment, OrderValidator())
    }
    ```

Почему такой дизайн важен:

1. Понятный контроль средствами языка: поведение IoC задается привычными конструкциями (интерфейсы, методы по умолчанию), а не XML или конфигурацией через рефлексию
2. Типобезопасная конфигурация: фабричные методы проверяются на этапе компиляции, что исключает ошибки конфигурации во время выполнения
3. Простое тестирование: фабричные методы переопределяются в тестах и подставляют заглушки без сложных тестовых фреймворков
4. Модульная композиция: множественное наследование позволяет чисто разделять ответственности между модулями
5. Гибкость замены: реализация меняется переопределением метода, без специальной конфигурации фреймворка

Такой подход на интерфейсах делает внедрение зависимостей естественным продолжением языка, давая полноценный IoC без потери простоты и типобезопасности.

#### Почему явное управление важно { #explicit-control-matters }

Философия Kora ставит явное управление выше неявной магии. В отличие от традиционных DI-фреймворков, которые сканируют classpath и создают все найденное, Kora требует явно объявить, какие зависимости
нужны приложению.

Проблемы автоматического обнаружения:

- Непредсказуемость: неизвестно, что будет создано после добавления очередного JAR в classpath
- Скрытые зависимости: компоненты создаются без вашего ведома и потребляют ресурсы
- Сложная отладка: при проблеме приходится выяснять, какие лишние компоненты работают
- Риски безопасности: уязвимые компоненты могут быть созданы автоматически
- Производительность: сканируется каждый JAR в classpath, даже если он не нужен

**Явный подход Kora:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        io.koraframework.http.server.undertow.UndertowPublicHttpServerModule,  // Explicitly included
        io.koraframework.database.jdbc.JdbcDatabaseModule,                     // Explicitly included
        // io.koraframework.cache.caffeine.CaffeineCacheModule,                // Commented out = not included
        com.example.MyCustomModule {                                           // Your custom module
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        io.koraframework.http.server.undertow.UndertowPublicHttpServerModule,  // Explicitly included
        io.koraframework.database.jdbc.JdbcDatabaseModule,                     // Explicitly included
        // io.koraframework.cache.caffeine.CaffeineCacheModule,                // Commented out = not included
        com.example.MyCustomModule                                             // Your custom module
    ```

Преимущества явного управления:

- Предсказуемые зависимости: вы точно знаете, что работает в приложении
- Экономия ресурсов: создается только то, что действительно нужно
- Понятный граф зависимостей: связи компонентов легко читать и отлаживать
- Безопасность по умолчанию: никаких неожиданных экземпляров из транзитивных зависимостей
- Производительность: никакого сканирования classpath — все разрешено во время компиляции
- Сопровождаемость: изменения зависимостей явные и видны в коде

Практический эффект:
С автоматическими фреймворками разработчики часами выясняют, почему приложение медленное или ест лишние ресурсы. В Kora, если компонент недостижим из корня графа `@KoraApp`, его в приложении просто
нет — без сюрпризов и скрытых расходов.

### `@Component` { #component }

Помечает класс как компонент (зависимость) контейнера. Все компоненты в Kora — синглтоны: на все время жизни приложения создается ровно один экземпляр класса. Компонент создается только если он корневой
(помечен `@Root`) или требуется как зависимость чему-то, что достижимо из корня.

Что такое компоненты:

- Синглтоны: один экземпляр на жизненный цикл приложения
- Поставщики зависимостей: могут внедряться в другие компоненты
- Условная инициализация: создаются, только если нужны другим компонентам или помечены `@Root`
- Общие: один и тот же экземпляр передается во все точки внедрения

**Важное ограничение области**: классы `@Component` обнаруживаются и используются только внутри Gradle-модулей, которые содержат:

- интерфейс `@KoraApp` (главный модуль приложения)
- либо интерфейс `@KoraSubmodule` (модуль обнаружения компонентов)

Компоненты в обычных Gradle-модулях без этих аннотаций обработчиком Kora не увидятся.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {
        // Implementation
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService {
        // Implementation
    }
    ```

**Требования:**

===! ":fontawesome-brands-java: `Java`"

    - Класс не должен быть абстрактным — `@Component` на абстрактном классе или интерфейсе игнорируется, вместо него используются конкретные реализации
    - У класса должен быть ровно один публичный конструктор, иначе сборка падает с `@Component class must have exactly one public constructor`
    - Параметры конструктора становятся заявками на зависимости
    - Объявлять класс `final` — обычная практика; класс с AOP-аспектами `final` быть **не должен**, потому что Kora генерирует для него класс-наследник
    - Класс должен лежать в Gradle-модуле с `@KoraApp` или `@KoraSubmodule`

=== ":simple-kotlin: `Kotlin`"

    - Класс не должен быть абстрактным — `@Component` на абстрактном классе или интерфейсе игнорируется, вместо него используются конкретные реализации
    - У класса должен быть первичный конструктор, иначе сборка падает с `@Component class must have a primary constructor`
    - Параметры первичного конструктора становятся заявками на зависимости
    - Классы в Kotlin финальны по умолчанию, и это обычная практика; класс с AOP-аспектами нужно объявить `open`, потому что Kora генерирует для него класс-наследник
    - Класс должен лежать в Gradle-модуле с `@KoraApp` или `@KoraSubmodule`

Жизненный цикл компонента:

- Обнаружение: обработчик находит класс во время компиляции
- Проверка: зависимости проверяются на этапе компиляции
- Создание: экземпляр создается при старте приложения, если компонент достижим из корня
- Внедрение: один и тот же экземпляр передается всем зависимым компонентам
- Освобождение: контейнер вызывает `Lifecycle#release` при остановке, в обратном порядке зависимостей

### `@Module` { #module }

Группирует связанные фабрики компонентов и помечает интерфейсы как модули, подключаемые к контейнеру во время компиляции. Модуль — это интерфейс с фабричными методами создания компонентов. Все
фабричные методы модуля становятся доступны контейнеру.

Что дают модули:

- Сбор фабрик: связанные фабрики компонентов лежат в одном месте
- Организация кода: разные задачи разнесены по разным модулям
- Переиспользование: модули можно шарить между приложениями
- Поддержка переопределения: фабричные методы переопределяются в наследующих интерфейсах

Область: интерфейсы `@Module` обрабатываются внутри Gradle-модулей, содержащих `@KoraApp` или `@KoraSubmodule`. Внешние модули из библиотек подключаются наследованием интерфейса.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface DatabaseModule {
        default UserRepository userRepository(DataSource dataSource) {
            return new JdbcUserRepository(dataSource);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface DatabaseModule {
        fun userRepository(dataSource: DataSource): UserRepository =
            JdbcUserRepository(dataSource)
    }
    ```

Виды модулей:

- Внутренние модули: интерфейсы `@Module` в том же Gradle-модуле, что и `@KoraApp`; подхватываются автоматически, наследовать их не нужно
- Подмешанные модули: любой интерфейс, унаследованный от `@KoraApp`, даже без `@Module`; его фабричные методы попадают в граф
- Внешние модули: приходят из библиотек и подключаются наследованием от `@KoraApp`
- Подмодули: интерфейсы `<Имя>SubmoduleImpl`, сгенерированные из `@KoraSubmodule` в другом Gradle-модуле

Требования к модулю:

- Должен быть интерфейсом, а не классом — `@Module` на классе падает с ошибкой `@Module can only be applied to interfaces`
- Фабричные методы должны иметь тело (`default` в Java, обычное тело функции в Kotlin)
- Фабричные методы должны возвращать ссылочный тип; примитивы отвергаются
- Чтобы обнаружиться автоматически, модуль должен лежать в том же Gradle-модуле, что `@KoraApp` или `@KoraSubmodule`

Правила фабричных методов:

- Метод должен возвращать компонент, при этом «сырой» обобщенный тип отвергается
- Метод может принимать другие компоненты параметрами
- Параметры становятся заявками на зависимости
- Параметры могут быть необязательными компонентами (`@Nullable` в Java, `T?` в Kotlin)
- Методы вызываются при старте в порядке зависимостей

> **Компоненты внешних библиотек**: компоненты и модули из внешних библиотек **не обнаруживаются автоматически** обработчиком Kora. Даже если библиотека содержит классы `@Component` или интерфейсы
> `@Module`, они будут невидимы приложению, пока вы явно не унаследуете их интерфейсы модулей в `@KoraApp`. Это осознанное решение в пользу явного управления зависимостями.

### `@KoraSubmodule` { #korasubmodule }

Помечает интерфейс, для которого нужно собрать модуль текущего Gradle-модуля. Сгенерированный интерфейс содержит все компоненты, помеченные `@Module` и `@Component`, найденные в исходниках этого
Gradle-модуля. Аннотация особенно полезна в многомодульных Gradle-приложениях, где разные модули содержат разную функциональность, а главное приложение `@KoraApp` собирается в отдельном модуле.

Что делает `@KoraSubmodule`:

- Обнаружение компонентов: сканирует текущий Gradle-модуль на `@Module` и `@Component`
- Генерация модуля: создает интерфейс `<Имя>SubmoduleImpl` со всеми найденными модулями и компонентами
- Многомодульность: позволяет использовать компоненты в других Gradle-модулях
- Границы: задает область, в которой обработчик Kora ищет компоненты
- Оптимизация сборки: включает кеширование и инкрементальную компиляцию Gradle за счет разделения функциональности по модулям

Область: интерфейсы `@KoraSubmodule` задают границы, внутри которых обработчик Kora ищет компоненты. Компоненты за этими границами не обрабатываются.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraSubmodule
    public interface ApplicationModules {
        // Generated factory methods for all discovered components
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraSubmodule
    interface ApplicationModules {
        // Generated factory methods for all discovered components
    }
    ```

Как это работает:

1. Обнаружение: находятся все интерфейсы `@Module` и классы `@Component` в текущем Gradle-модуле
2. Наследование: сгенерированный интерфейс `ApplicationModulesSubmoduleImpl` наследует все найденные интерфейсы `@Module`
3. Генерация фабрик: для всех найденных классов `@Component` создаются методы по умолчанию
4. Интеграция: ваш `@KoraApp` наследует интерфейс `@KoraSubmodule`, а Kora подставляет за ним сгенерированный `…SubmoduleImpl`

Сценарии использования:

- Многомодульные проекты: переиспользование компонентов между Gradle-модулями
- Разработка библиотек: публикация компонентов из модуля-библиотеки
- Модульная архитектура: разделение ответственностей по модулям сборки
- Организация компонентов: группировка компонентов по функциональности
- Большие монолиты: разбиение сложного приложения на изолированные Gradle-модули ради скорости сборки и сопровождаемости
- Оптимизация сборки: кеш Gradle работает лучше, когда функциональность разнесена по независимым модулям

> Если сгенерированный интерфейс еще не появился в classpath, сборка сообщит `Kora submodule was not generated yet`. Обычно это значит, что модуль с `@KoraSubmodule` не скомпилирован или к нему не
> подключен обработчик Kora.

### `@Root` { #root }

Помечает компоненты, которые обязаны быть созданы при запуске приложения, даже если от них ничего не зависит. Корневые компоненты — это точки входа графа: Kora начинает разрешение зависимостей с набора
корней и строит только то, что из него достижимо.

Что делает `@Root`:

- Гарантированная инициализация: компонент всегда создается при старте
- Точка входа в граф: все, что нужно корню, затягивается в граф
- Жизненный цикл: компонент участвует в старте и остановке приложения
- Точки входа: идеально для серверов, консьюмеров, планировщиков и фоновых сервисов

Типичные сценарии:

- HTTP-серверы: веб-серверы, которые должны сразу начать слушать порт
- Консьюмеры сообщений: Kafka-консьюмеры, обработчики очередей
- Фоновые сервисы: прогрев кеша, health-check, планировщики
- Инициализация: все, что производит только побочные эффекты, например подготовку внешнего состояния

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class NotificationService {
        // Always created, even if nothing injects it
    }

    @KoraApp
    public interface Application {
        @Root
        default HttpServer httpServer(UserController controller) {
            return new HttpServer(controller);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class NotificationService {
        // Always created, even if nothing injects it
    }

    @KoraApp
    interface Application {
        @Root
        fun httpServer(controller: UserController): HttpServer =
            HttpServer(controller)
    }
    ```

`@Root` против обычных компонентов:

- Обычные компоненты: создаются, только если достижимы из корня по ребрам зависимостей
- Компоненты `@Root`: создаются при старте всегда

Когда использовать `@Root`:

- компонент предоставляет сервис, который должен работать постоянно
- компонент должен сразу начать обработку (серверы, консьюмеры)
- компонент выполняет критичную инициализацию (подготовка схемы, прогрев кеша, создание бакета)
- компонент собирает метрики или данные мониторинга

!!! warning "Нужен хотя бы один корень"

    `@KoraApp`, из которого не достижим ни один `@Root`, не компилируется и падает с `@KoraApp has no root components`. Модули фреймворка обычно приносят свои корни — например, модуль HTTP-сервера
    помечает корнем компонент сервера, — но приложение, состоящее только из обычных компонентов, обязано пометить корнем хотя бы один из них.

    Это же правило объясняет коварный класс ошибок: компонент `Lifecycle`, который только подготавливает внешнее состояние и который никто не внедряет, выбрасывается из графа, а вместе с ним исчезает
    и все, что он тянул за собой. Такому компоненту нужен `@Root`.

### `@DefaultComponent` { #defaultcomponent }

Помечает фабрики или компоненты, которые дают реализацию по умолчанию и рассчитаны на замену пользователем. Если в графе есть другой компонент того же типа и с тем же тегом, но без этой аннотации, при
внедрении победит он.

Что делает `@DefaultComponent`:

- Реализация по умолчанию: дает запасной вариант компонента
- Поддержка замены: позволяет заменить умолчание, не трогая код библиотеки
- Удобство для библиотек: библиотеки предоставляют разумные умолчания
- Приоритет: ниже, чем у фабрик без этой аннотации

Сценарии использования:

- Умолчания библиотек: библиотека дает реализацию, которую пользователь может заменить
- Варианты конфигурации: разные реализации в зависимости от окружения
- Точки расширения: пользователь меняет поведение, не меняя код библиотеки

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface CacheModule {
        @DefaultComponent
        default Cache defaultCache() {
            return new InMemoryCache();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface CacheModule {
        @DefaultComponent
        fun defaultCache(): Cache = InMemoryCache()
    }
    ```

**Как работает замена:**

Заменить умолчание можно двумя способами: переопределить сам метод либо просто объявить другую фабрику того же типа без `@DefaultComponent`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends CacheModule {  // <----- Connected module

        // Option 1: override the method - the override carries no @DefaultComponent, so it wins
        @Override
        default Cache defaultCache() {
            return new RedisCache();
        }
    }

    @KoraApp
    public interface OtherApplication extends CacheModule {

        // Option 2: a different method providing the same type without @DefaultComponent also wins
        default Cache applicationCache() {
            return new RedisCache();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : CacheModule {  // <----- Connected module

        // Option 1: override the function - the override carries no @DefaultComponent, so it wins
        override fun defaultCache(): Cache = RedisCache()
    }

    @KoraApp
    interface OtherApplication : CacheModule {

        // Option 2: a different function providing the same type without @DefaultComponent also wins
        fun applicationCache(): Cache = RedisCache()
    }
    ```

**Правило разрешения:**

1. Кандидаты отбираются по типу и тегу
2. Если подходит несколько, предпочтение отдается кандидатам **без** `@DefaultComponent`
3. Если остается ровно один такой кандидат, используется он
4. Если остается несколько, сборка падает с `Multiple components match dependency`

**Лучшие практики:**

- Используйте для умолчаний библиотек, которые пользователь может захотеть заменить
- Не используйте для компонентов, специфичных для приложения
- Явно документируйте, какие умолчания доступны для замены

### `@Tag` { #tag }

Позволяет различать несколько реализаций одного типа и выборочно внедрять нужную. Тег — это ссылка на класс, а не строка, что дает безопасное переименование и типобезопасность. Компонент
регистрируется с конкретным тегом и внедряется туда, где запрошен ровно такой же тег.

Что дают теги:

- Выбор реализации: можно выбрать конкретную реализацию интерфейса
- Несколько экземпляров: в одном графе сосуществует несколько объектов одного типа
- Типобезопасность: используются ссылки на классы, а не строки
- Безопасный рефакторинг: IDE отслеживает использование тегов по всей кодовой базе

Аннотация несет ровно один класс:

```java
public @interface Tag {
    Class<?> value();
}
```

Базовое использование:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Tag classes (usually empty marker classes)
    public final class RedisTag {
        private RedisTag() {}
    }

    public final class InMemoryTag {
        private InMemoryTag() {}
    }

    // Tagged implementations
    @Tag(RedisTag.class)
    @Component
    public final class RedisCache implements Cache {
        // Redis implementation
    }

    @Tag(InMemoryTag.class)
    @Component
    public final class InMemoryCache implements Cache {
        // In-memory implementation
    }

    // Selective injection
    @Component
    public final class UserService {
        public UserService(@Tag(RedisTag.class) Cache cache) {
            // Injects RedisCache specifically
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Tag classes (usually empty marker classes)
    class RedisTag private constructor()

    class InMemoryTag private constructor()

    // Tagged implementations
    @Tag(RedisTag::class)
    @Component
    class RedisCache : Cache {
        // Redis implementation
    }

    @Tag(InMemoryTag::class)
    @Component
    class InMemoryCache : Cache {
        // In-memory implementation
    }

    // Selective injection
    @Component
    class UserService(@Tag(RedisTag::class) private val cache: Cache) {
        // Injects RedisCache specifically
    }
    ```

Куда ставится тег:

- На классы: `@Tag(MyTag.class) @Component final class MyClass`
- На фабричные методы: `@Tag(MyTag.class) default MyClass myClass()`
- На параметры: `MyService(@Tag(MyTag.class) Dependency dep)`
- На аннотации: своя аннотация, помеченная `@Tag(MyTag.class)`, работает как этот тег

Специальные теги:

- `@Tag(Tag.Any.class)`: подходит любому компоненту нужного типа, с тегом и без
- `@Tag(Tag.Factory.class)`: внутри вложенного модуля, подключенного через `@FactoryModule`, означает «взять тег метода-фабрики модуля»

Правила сопоставления тегов:

1. Заявка без тега подходит только компонентам без тега
2. Заявка с тегом подходит только компонентам ровно с этим классом-тегом
3. `Tag.Any` подходит всему нужного типа
4. Сравнивается сам класс-тег; иерархия наследования тегов не учитывается

Свои аннотации-теги:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(RedisTag.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
    public @interface RedisCache {}

    @Tag(InMemoryTag.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
    public @interface InMemoryCache {}

    // Usage
    @RedisCache
    @Component
    public final class RedisCacheImpl implements Cache {}

    @Component
    public final class UserService {
        public UserService(@RedisCache Cache cache) {/* ... */}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(RedisTag::class)
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.VALUE_PARAMETER)
    annotation class RedisCache

    @Tag(InMemoryTag::class)
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.VALUE_PARAMETER)
    annotation class InMemoryCache

    // Usage
    @RedisCache
    @Component
    class RedisCacheImpl : Cache

    @Component
    class UserService(@RedisCache private val cache: Cache)
    ```

### `@Conditional` { #conditional }

Ставит присутствие компонента в работающем графе в зависимость от условия, которое вычисляется при инициализации графа. Само условие — это обычный компонент графа типа `GraphCondition`,
зарегистрированный под тегом, поэтому оно может зависеть от конфигурации или любого другого компонента.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.GraphCondition;
    import io.koraframework.common.annotation.Conditional;

    public final class ExportEnabled {
        private ExportEnabled() {}
    }

    @KoraApp
    public interface Application {

        @Tag(ExportEnabled.class)
        default GraphCondition exportEnabled(ExportConfig config) {       //(1)!
            return () -> config.enabled()
                ? GraphCondition.ConditionResult.matched("export.enabled = true")
                : GraphCondition.ConditionResult.failed("export.enabled = false");
        }

        @Root
        @Conditional(tag = ExportEnabled.class)                           //(2)!
        default ExportJob exportJob(ExportClient client) {
            return new ExportJob(client);
        }
    }
    ```

    1. Компонент `GraphCondition`, зарегистрированный под тегом `ExportEnabled`. Такой компонент для тега должен быть ровно один.
    2. Компонент создается, только если условие вернуло `Matched`; иначе узел остается неинициализированным, и обращение к нему бросает исключение.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.GraphCondition
    import io.koraframework.common.annotation.Conditional

    class ExportEnabled private constructor()

    @KoraApp
    interface Application {

        @Tag(ExportEnabled::class)
        fun exportEnabled(config: ExportConfig): GraphCondition = GraphCondition {   //(1)!
            if (config.enabled()) GraphCondition.ConditionResult.matched("export.enabled = true")
            else GraphCondition.ConditionResult.failed("export.enabled = false")
        }

        @Root
        @Conditional(tag = ExportEnabled::class)                                     //(2)!
        fun exportJob(client: ExportClient): ExportJob = ExportJob(client)
    }
    ```

    1. Компонент `GraphCondition`, зарегистрированный под тегом `ExportEnabled`. Такой компонент для тега должен быть ровно один.
    2. Компонент создается, только если условие вернуло `Matched`; иначе узел остается неинициализированным, и обращение к нему бросает исключение.

Что важно помнить:

- Один тег может нести ровно один `GraphCondition`, иначе сборка падает с `Multiple GraphCondition components match condition tag`
- Отсутствие поставщика условия ломает сборку с `Component condition cannot be resolved`
- Условия каскадируются: все, что существует только благодаря условному компоненту, отключается вместе с ним
- Если два кандидата одного типа оба условные, Kora оставляет в графе оба и позволяет условиям выбрать во время запуска

---

## Приоритет обнаружения компонентов { #component-discovery-priority }

Чтобы удовлетворить одну заявку на зависимость, Kora проходит фиксированную последовательность стратегий. Понимание этого порядка необходимо для отладки проблем разрешения и для уверенности, что
используются нужные реализации.

Порядок разрешения одной заявки (тип + тег):

1. **Конкретные объявления**, уже известные обработчику — классы `@Component`, фабричные методы интерфейса `@KoraApp` и всего, что он наследует, интерфейсы `@Module` текущего Gradle-модуля,
   сгенерированные подмодули, вложенные модули `@FactoryModule` и компоненты, ранее созданные расширениями
2. **Шаблоны компонентов** — обобщенные фабричные методы, чьи параметры типа выводятся под запрошенный тип
3. **Обнуляемый запасной вариант** — если заявка обнуляемая, зависимость разрешается в `null`
4. **Запасной вариант `Optional<T>`** — если заявка объявлена как `Optional<T>` и `T` никто не предоставляет, подставляется пустой `Optional`
5. **Расширения** — расширение генерирует компонент по запросу (`JsonReader` и `JsonWriter`, реализации `@Repository`, реализации `@HttpClient`, извлекатели конфигурации, валидаторы, мапперы)
6. **Ошибка** — иначе сборка падает с `No component found for dependency`

Внутри пункта 1, когда под один тип и тег подходит несколько объявлений:

- Кандидаты **без** `@DefaultComponent` предпочитаются кандидатам с этой аннотацией
- Если остается ровно один кандидат, используется он
- Если все оставшиеся кандидаты помечены `@Conditional`, в графе остаются все, а выбор делает условие при запуске
- Иначе сборка падает с `Multiple components match dependency`

**Что это означает на практике:**

- Конкретный фабричный метод всегда побеждает обобщенный шаблон того же типа
- `@DefaultComponent` из библиотеки заменяется простым объявлением своей фабрики того же типа и тега
- Расширения — крайняя мера, поэтому написанный вручную компонент того же типа молча вытесняет сгенерированный
- Ничего не создается «на всякий случай» — строится только то, что нужно корню

**Практический пример:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Library default - lowest priority
    @Module
    public interface UserModule {
        @DefaultComponent
        default UserService userService() {
            return new DefaultUserService();
        }
    }

    // Application factory - wins, because it carries no @DefaultComponent
    @KoraApp
    public interface Application extends UserModule {
        default UserService customUserService() {
            return new CustomUserService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Library default - lowest priority
    @Module
    interface UserModule {
        @DefaultComponent
        fun userService(): UserService = DefaultUserService()
    }

    // Application factory - wins, because it carries no @DefaultComponent
    @KoraApp
    interface Application : UserModule {
        fun customUserService(): UserService = CustomUserService()
    }
    ```

---

## Объявление компонентов { #declaring-components }

Компоненты в Kora объявляются несколькими способами, каждый со своим сценарием. **Все способы требуют, чтобы код находился в Gradle-модулях с интерфейсами `@KoraApp` или `@KoraSubmodule`** — обработчик
Kora сканирует только эти модули.

### Автоматическая фабрика (`@Component`) { #automatic-factory-component }

Классы с аннотацией `@Component` регистрируются автоматически, если удовлетворяют требованиям:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {
        private final UserRepository repository;

        public UserService(UserRepository repository) {
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(
        private val repository: UserRepository
    )
    ```

**Требования:**

- Не абстрактный
- Ровно один публичный конструктор (Java) или первичный конструктор (Kotlin)
- Нефинальный только тогда, когда применяются AOP-аспекты, потому что Kora наследует компонент, чтобы их встроить
- Параметры конструктора становятся заявками на зависимости

### Базовые фабричные методы { #method-factory-basics }

Методы с телом в интерфейсах `@KoraApp` или `@Module`, возвращающие компоненты:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
        default UserService userService(UserRepository repository) {
            return new UserService(repository);
        }

        default UserRepository userRepository() {
            return new InMemoryUserRepository();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {
        fun userService(repository: UserRepository): UserService =
            UserService(repository)

        fun userRepository(): UserRepository =
            InMemoryUserRepository()
    }
    ```

Фабричный метод удобен всякий раз, когда создание требует решения, которое хочется держать в одном месте: выбор реализации, работа со сторонним билдером или настройка, которой не место в конструкторе
самого компонента.

### Фабрика модуля { #module-factory }

Фабричные методы внутри интерфейсов `@Module`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface DatabaseModule {
        default DataSource dataSource() {
            return new HikariDataSource();
        }

        default UserRepository userRepository(DataSource dataSource) {
            return new JdbcUserRepository(dataSource);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface DatabaseModule {
        fun dataSource(): DataSource =
            HikariDataSource()

        fun userRepository(dataSource: DataSource): UserRepository =
            JdbcUserRepository(dataSource)
    }
    ```

Интерфейс `@Module`, объявленный в том же Gradle-модуле, что и `@KoraApp`, попадает в граф автоматически — наследовать его не нужно. Наследование от `@KoraApp` все же полезно, когда требуется
переопределить один из его методов.

### Фабрика внешнего модуля { #external-module-factory }

Модули из внешних зависимостей подключаются наследованием интерфейса:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;

    @KoraApp
    public interface Application extends
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule {
        // Inherits all factory methods from external modules
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule {
        // Inherits all factory methods from external modules
    }
    ```

> **Требуется явное подключение**: компоненты внешних библиотек недоступны автоматически. Интерфейсы модулей библиотеки нужно явно унаследовать в `@KoraApp`. Просто добавить библиотеку в classpath
> недостаточно — компоненты становятся доступны именно через наследование интерфейса модуля.

**Такой явный подход снимает типичные проблемы автоматических фреймворков:**

- никаких неожиданных экземпляров ненужных компонентов
- видно, какие зависимости реально используются
- лучше безопасность за счет осознанного подключения
- проще отладка и сопровождение

### Фабрика подмодуля { #submodule-factory }

Модули, сгенерированные из интерфейсов `@KoraSubmodule`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Gradle module :persistence
    @Module
    public interface PersistenceModule {
        default UserRepository userRepository() {
            return new InMemoryUserRepository();
        }
    }

    @KoraSubmodule
    public interface PersistenceSubmodule {
        // Generates factory methods for all @Module and @Component in this Gradle module
    }

    // Gradle module :application
    @KoraApp
    public interface Application extends PersistenceSubmodule {  // <----- Connected submodule
        // All components from the submodule are available
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Gradle module :persistence
    @Module
    interface PersistenceModule {
        fun userRepository(): UserRepository =
            InMemoryUserRepository()
    }

    @KoraSubmodule
    interface PersistenceSubmodule {
        // Generates factory methods for all @Module and @Component in this Gradle module
    }

    // Gradle module :application
    @KoraApp
    interface Application : PersistenceSubmodule {  // <----- Connected submodule
        // All components from the submodule are available
    }
    ```

### Обобщенная фабрика { #generic-factory }

Методы с обобщенными параметрами типа, которые создают компоненты любого подходящего типа. Такие объявления хранятся как шаблоны компонентов и материализуются только тогда, когда запрошен конкретный
тип. Обобщенные фабрики особенно полезны для типобезопасных компонентов, работающих с разными обобщенными типами.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ValidatorModule {
        // Generic factory for List validators
        default <T> Validator<List<T>> listValidator(Validator<T> validator, TypeRef<T> valueRef) {
            return new IterableValidator<>(validator);
        }

        // Generic factory for Set validators
        default <T> Validator<Set<T>> setValidator(Validator<T> validator, TypeRef<T> valueRef) {
            return new IterableValidator<>(validator);
        }

        // Generic factory for Collection validators
        default <T> Validator<Collection<T>> collectionValidator(Validator<T> validator, TypeRef<T> valueRef) {
            return new IterableValidator<>(validator);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ValidatorModule {
        // Generic factory for List validators
        fun <T> listValidator(validator: Validator<T>, valueRef: TypeRef<T>): Validator<List<T>> =
            IterableValidator(validator)

        // Generic factory for Set validators
        fun <T> setValidator(validator: Validator<T>, valueRef: TypeRef<T>): Validator<Set<T>> =
            IterableValidator(validator)

        // Generic factory for Collection validators
        fun <T> collectionValidator(validator: Validator<T>, valueRef: TypeRef<T>): Validator<Collection<T>> =
            IterableValidator(validator)
    }
    ```

**Как это работает:**

- Параметр типа `<T>` позволяет создавать валидаторы для любого типа элемента
- `TypeRef<T>` несет конкретный обобщенный тип, под который была материализована фабрика
- Kora может создать `Validator<List<String>>`, `Validator<Set<User>>` и так далее
- Конкретная фабрика всегда побеждает шаблон для того же типа
- «Сырые» типы отвергаются: заявка вида `Validator` без аргументов типа ломает сборку

### Механизм расширений { #extension-mechanism }

Расширения генерируют компоненты по запросу прямо во время разрешения графа. Они срабатывают только тогда, когда заявку не может удовлетворить ничто другое, поэтому написанный вручную компонент того
же типа всегда имеет приоритет.

Расширения поставляются вместе с соответствующими обработчиками Kora и покрывают, в частности:

- реализации `JsonReader<T>` и `JsonWriter<T>` для классов с `@Json`
- реализации интерфейсов `@Repository` для JDBC и Cassandra
- реализации интерфейсов `@HttpClient`
- клиентские заглушки gRPC
- извлекатели конфигурации для интерфейсов `@ConfigSource` и `@ConfigMapper`
- реализации `Validator<T>` для типов с `@Valid`
- реализации мапперов MapStruct и Konvert

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JsonModule {

        @Root
        default UserPrinter userPrinter(JsonWriter<User> writer) {  //(1)!
            return new UserPrinter(writer);
        }
    }

    @Json
    public record User(String name, int age) {}
    ```

    1. `JsonWriter<User>` нигде не объявлен; расширение JSON генерирует его во время разрешения графа.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JsonModule {

        @Root
        fun userPrinter(writer: JsonWriter<User>): UserPrinter =        //(1)!
            UserPrinter(writer)
    }

    @Json
    data class User(val name: String, val age: Int)
    ```

    1. `JsonWriter<User>` нигде не объявлен; расширение JSON генерирует его во время разрешения графа.

### Фабрика `@DefaultComponent` { #defaultcomponent-factory }

Реализации по умолчанию, которые можно заменить:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface CacheModule {
        @DefaultComponent
        default Cache cache() {
            return new InMemoryCache();
        }
    }

    // Can be overridden in the application:
    @KoraApp
    public interface Application extends CacheModule {  // <----- Connected module

        default Cache primaryCache() {
            return new RedisCache(); // Overrides the default
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface CacheModule {
        @DefaultComponent
        fun cache(): Cache = InMemoryCache()
    }

    // Can be overridden in the application:
    @KoraApp
    interface Application : CacheModule {  // <----- Connected module

        fun primaryCache(): Cache = RedisCache() // Overrides the default
    }
    ```

`@DefaultComponent` работает не только на фабричных методах, но и на классах, поэтому класс `@Component` тоже можно объявить заменяемым умолчанием.

### Модуль-фабрика { #factory-module }

`@FactoryModule` помечает метод модуля, **возвращаемое значение которого само является модулем**. Возвращенный объект становится компонентом графа, а его публичные методы обрабатываются как фабрики
компонентов. Именно так один и тот же набор фабрик регистрируется несколько раз с разной конфигурацией.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class MessengerModule {                                //(1)!

        private final String header;

        public MessengerModule(String header) {
            this.header = header;
        }

        @Tag(Tag.Factory.class)                                         //(2)!
        public Messenger messenger(@Tag(Tag.Factory.class) Transport transport) {
            return new Messenger(this.header, transport);
        }
    }

    @KoraApp
    public interface Application {

        @Tag(SlackTag.class)
        @FactoryModule
        default MessengerModule slackModule() {                         //(3)!
            return new MessengerModule("SLACK");
        }

        @Tag(SignalTag.class)
        @FactoryModule
        default MessengerModule signalModule() {
            return new MessengerModule("SIGNAL");
        }

        @Tag(SlackTag.class)
        default Transport slackTransport() {
            return new HttpTransport("https://slack.example.com");
        }

        @Tag(SignalTag.class)
        default Transport signalTransport() {
            return new HttpTransport("https://signal.example.com");
        }

        @Root
        default Dispatcher dispatcher(@Tag(SlackTag.class) Messenger slack,
                                      @Tag(SignalTag.class) Messenger signal) {
            return new Dispatcher(slack, signal);
        }
    }
    ```

    1. Обычный класс, публичные методы которого работают как фабрики компонентов.
    2. `@Tag(Tag.Factory.class)` означает «тег внешнего метода `@FactoryModule`», поэтому каждый экземпляр отдает свои компоненты с тегом и потребляет свои зависимости с тегом.
    3. Возвращенный `MessengerModule` регистрируется в графе под тегом `SlackTag`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class MessengerModule(private val header: String) {                 //(1)!

        @Tag(Tag.Factory::class)                                        //(2)!
        fun messenger(@Tag(Tag.Factory::class) transport: Transport): Messenger =
            Messenger(header, transport)
    }

    @KoraApp
    interface Application {

        @Tag(SlackTag::class)
        @FactoryModule
        fun slackModule(): MessengerModule = MessengerModule("SLACK")   //(3)!

        @Tag(SignalTag::class)
        @FactoryModule
        fun signalModule(): MessengerModule = MessengerModule("SIGNAL")

        @Tag(SlackTag::class)
        fun slackTransport(): Transport = HttpTransport("https://slack.example.com")

        @Tag(SignalTag::class)
        fun signalTransport(): Transport = HttpTransport("https://signal.example.com")

        @Root
        fun dispatcher(
            @Tag(SlackTag::class) slack: Messenger,
            @Tag(SignalTag::class) signal: Messenger
        ): Dispatcher = Dispatcher(slack, signal)
    }
    ```

    1. Обычный класс, публичные функции которого работают как фабрики компонентов.
    2. `@Tag(Tag.Factory::class)` означает «тег внешней функции `@FactoryModule`», поэтому каждый экземпляр отдает свои компоненты с тегом и потребляет свои зависимости с тегом.
    3. Возвращенный `MessengerModule` регистрируется в графе под тегом `SlackTag`.

`@Tag(Tag.Factory.class)` допустим только внутри типа, доступного через `@FactoryModule`; в других местах сборка падает с `@Tag.Factory can only be used inside factory modules`.

### Автоматическое создание отсутствует { #automatic-creation }

Kora никогда не создает класс просто потому, что его в принципе можно создать. Тип должен предоставляться одним из перечисленных выше механизмов — классом `@Component`, фабричным методом, шаблоном или
расширением. Если его не предоставляет ничто, сборка падает:

```
No component found for dependency:
  com.example.SomeService (no tags)
```

Это сделано намеренно. Граф никогда не обрастает объектами, которых вы не просили, и каждый узел работающего приложения прослеживается до написанного вами объявления или подключенного модуля.

Когда зависимость действительно может отсутствовать, скажите об этом явно, а не рассчитывайте на неявное создание:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ReportService {

        public ReportService(@Nullable AuditSink auditSink,          //(1)!
                             Optional<MetricsSink> metricsSink) {    //(2)!
        }
    }
    ```

    1. Разрешается в `null`, когда `AuditSink` никто не предоставляет.
    2. Разрешается в пустой `Optional`, когда `MetricsSink` никто не предоставляет.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ReportService(
        private val auditSink: AuditSink?,                           //(1)!
        private val metricsSink: Optional<MetricsSink>               //(2)!
    )
    ```

    1. Разрешается в `null`, когда `AuditSink` никто не предоставляет.
    2. Разрешается в пустой `Optional`, когда `MetricsSink` никто не предоставляет.

---

## Заявки зависимостей и разрешение { #dependency-claims-resolution }

Kora превращает каждый параметр конструктора и фабричного метода в *заявку на зависимость*: запрошенный тип, необязательный тег и вид заявки, выведенный из типа-обертки и обнуляемости. Именно здесь
параметры перестают быть просто типами Java или Kotlin и становятся требованиями к графу.

Понимание заявок помогает читать ошибки компиляции. Когда Kora сообщает, что зависимость отсутствует, неоднозначна или циклична, она описывает заявку, которую пыталась разрешить, и найденных
кандидатов в графе.

Kora различает следующие виды заявок:

| Форма параметра                         | Значение                                                        |
|-----------------------------------------|------------------------------------------------------------------|
| `T`                                     | ровно один обязательный компонент                                 |
| `@Nullable T` (Java) / `T?` (Kotlin)    | один необязательный компонент, `null` при отсутствии              |
| `Optional<T>`                           | один необязательный компонент, пустой `Optional` при отсутствии   |
| `ValueOf<T>`                            | доступ к текущему значению компонента                             |
| `PromiseOf<T>`                          | доступ, разрешаемый после инициализации графа, ломает циклы       |
| `All<T>`                                | все подходящие компоненты                                         |
| `All<ValueOf<T>>` / `All<PromiseOf<T>>` | все подходящие компоненты, каждый в обертке                       |
| `TypeRef<T>`                            | конкретный обобщенный тип, под который материализован шаблон      |
| `Graph` / `RefreshableGraph`            | сам граф, для инфраструктурных компонентов                        |
| `Node<T>`                               | узел графа компонента, для инфраструктурных компонентов           |

### Базовые типы зависимостей { #basic-dependency-types }

Большинство зависимостей в Kora выражаются прямо в параметрах конструктора или фабричного метода. Форма параметра говорит Kora, обязателен ли компонент, необязателен, доступен отложенно или является
коллекцией реализаций. Эти формы позволяют описать отношения между компонентами, не тащя API контейнера в бизнес-код.

Используйте самую простую форму, которая соответствует правилу предметной области. Если сервис не работает без репозитория, запрашивайте репозиторий напрямую. Если интеграция необязательна, пометьте
зависимость обнуляемой. Если нужны все реализации точки расширения, запрашивайте `All<T>`. Если нужно избежать каскадных пересозданий или отложить доступ к компоненту, запрашивайте `ValueOf<T>`.

#### Обязательные { #required }

Одна обязательная зависимость, которая должна существовать.
Это форма по умолчанию и самая частая. Обязательный параметр означает, что граф приложения некорректен, если подходящий компонент не найден ровно один. Это правильный выбор для основных соисполнителей:
репозиториев, сервисов, валидаторов, интерфейсов конфигурации и клиентов, участвующих в обычном потоке приложения.

Обязательные зависимости делают отказы явными. Если вы забыли подключить модуль или объявить компонент, сборка упадет во время генерации графа, а не оставит приложение стартовать с недонастроенным
окружением.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        private final UserRepository repository;

        public UserService(UserRepository repository) { // ONE_REQUIRED
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(private val repository: UserRepository) // ONE_REQUIRED
    ```

#### Необязательные { #optional }

Одна зависимость, которой может не быть.
Необязательные зависимости полезны для опциональных возможностей, опциональных интеграций и умолчаний библиотек, когда приложение может, но не обязано предоставить дополнительный компонент. Kora
по-прежнему ищет зависимость по типу и тегу, но допускает ее отсутствие, и сгенерированный граф передает `null`.

В Java необязательность выражается аннотацией JSpecify `org.jspecify.annotations.Nullable`. В Kotlin она выражается самим обнуляемым типом — аннотация не нужна.

Пользуйтесь этим осознанно. Обнуляемая зависимость должна означать «компонент умеет работать без этого соисполнителя», а не «я не уверен, что граф корректен». Бизнес-код, получающий обнуляемую
зависимость, должен явно ветвиться, чтобы деградация поведения оставалась видимой.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import org.jspecify.annotations.Nullable;

    @Component
    public final class UserService {

        @Nullable
        private final AuditService auditService;

        public UserService(@Nullable AuditService auditService) { // ONE_NULLABLE
            this.auditService = auditService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(private val auditService: AuditService?) // ONE_NULLABLE
    ```

`Optional<T>` выражает ту же идею контейнером вместо `null` и удобен, когда значение сразу передается в API, которое и так работает с `Optional`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        public UserService(Optional<AuditService> auditService) {
            // empty when nothing provides AuditService
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(private val auditService: Optional<AuditService>) {
        // empty when nothing provides AuditService
    }
    ```

#### `ValueOf` { #valueof }

Доступ к текущему значению компонента.
`ValueOf<T>` — это ссылка на компонент, а не сам компонент. Она позволяет читать актуальное значение в момент обращения, а не захватывать экземпляр один раз. Это важно, когда зависимость может быть
обновлена, например после изменения конфигурации: компоненты, зависящие от `T` напрямую, пересоздаются, а компоненты, держащие `ValueOf<T>`, — нет.

В обычном коде обработки запросов `ValueOf<T>` чаще всего не нужен. Для простого взаимодействия сервисов предпочитайте прямую зависимость. Берите `ValueOf<T>`, когда важно поведение жизненного цикла:
обновление конфигурации, дорогие компоненты или компоненты, которые не должны заставлять потребителей пересоздаваться вместе с собой.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.ValueOf;

    @Component
    public final class OrderService {

        private final ValueOf<UserService> userService;

        public OrderService(ValueOf<UserService> userService) {
            this.userService = userService;
        }

        public void process(Order order) {
            this.userService.get().enrich(order);  //(1)!
        }
    }
    ```

    1. `get()` всегда возвращает актуальный экземпляр, даже после обновления компонента.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.ValueOf

    @Component
    class OrderService(private val userService: ValueOf<UserService>) {

        fun process(order: Order) {
            userService.get().enrich(order)  //(1)!
        }
    }
    ```

    1. `get()` всегда возвращает актуальный экземпляр, даже после обновления компонента.

Может быть и `@Nullable`, если обернутый компонент необязателен:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class OrderService {
        public OrderService(@Nullable ValueOf<AuditService> auditService) {
            // auditService may be null
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class OrderService(private val auditService: ValueOf<AuditService>?) {
        // auditService may be null
    }
    ```

#### `PromiseOf` { #promiseof }

Отложенный доступ к компоненту, которого может еще не быть в момент создания потребителя.
`PromiseOf<T>` возвращает `Optional<T>` и разрешается после инициализации графа. Используйте его в редком случае, когда компонент обязан ссылаться на что-то создаваемое позже, — как правило, чтобы
разорвать цикл зависимостей, который не получается перестроить.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.PromiseOf;

    @Component
    public final class MetricsReporter {

        private final PromiseOf<HttpServer> server;

        public MetricsReporter(PromiseOf<HttpServer> server) {
            this.server = server;
        }

        public void report() {
            this.server.get().ifPresent(s -> log(s.port()));  //(1)!
        }
    }
    ```

    1. `get()` возвращает пустой `Optional`, пока компонент, на который он ссылается, не инициализирован.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.PromiseOf

    @Component
    class MetricsReporter(private val server: PromiseOf<HttpServer>) {

        fun report() {
            server.get().ifPresent { log(it.port()) }  //(1)!
        }
    }
    ```

    1. `get()` возвращает пустой `Optional`, пока компонент, на который он ссылается, не инициализирован.

#### `All` { #all }

Все подходящие реализации типа.
`All<T>` описывает точки расширения. Вместо выбора одной реализации Kora внедряет все подходящие. Это удобно для обработчиков, валидаторов, слушателей, интерцепторов, экспортеров и любых мест, где
приложение должно скомпоновать несколько независимых вкладов.

`All<T>` — это `Iterable<T>`, поэтому по нему итерируются напрямую, а не работают как со списком.

Важный момент дизайна: каждый элемент `All<T>` остается компонентом графа. Kora проверяет каждую реализацию, учитывает теги, если они запрошены, и связывает коллекцию во время компиляции. Так
композиция в стиле плагинов остается типобезопасной и видимой в сгенерированном графе.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.All;

    @Component
    public final class NotificationService {

        private final All<Notifier> notifiers;

        public NotificationService(All<Notifier> notifiers) {
            this.notifiers = notifiers;
        }

        public void broadcast(String message) {
            for (var notifier : this.notifiers) {  //(1)!
                notifier.notifyUser(message);
            }
        }
    }
    ```

    1. `All<T>` наследует `Iterable<T>`, поэтому цикл for-each — естественный способ его обойти.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.All

    @Component
    class NotificationService(private val notifiers: All<Notifier>) {

        fun broadcast(message: String) {
            notifiers.forEach { it.notifyUser(message) }  //(1)!
        }
    }
    ```

    1. `All<T>` наследует `Iterable<T>`, поэтому стандартные функции итерации работают с ним напрямую.

Элементы также можно обернуть:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(All<ValueOf<Notifier>> notifiers) {
            // Each notifier wrapped in ValueOf
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NotificationService(private val notifiers: All<ValueOf<Notifier>>) {
        // Each notifier wrapped in ValueOf
    }
    ```

!!! warning "`All<T>` без тега собирает только компоненты без тега"

    Сопоставление тегов работает для `All<T>` ровно так же, как для одиночной зависимости. Если у ваших реализаций есть теги, запрашивайте `@Tag(Tag.Any.class) All<T>`, чтобы собрать их все, либо
    указывайте конкретный тег, чтобы собрать одну группу. Смотрите [`@Tag.Any`](#tag-any) и [All с тегом](#tagged-all).

#### `TypeRef` { #typeref }

Конкретный обобщенный тип, под который материализован шаблон.
`TypeRef<T>` переносит информацию об обобщенном типе через стирание типов. Он нужен, когда обобщенной фабрике важен не только «сырой» класс, но и полный обобщенный тип, запрошенный графом. JSON-мапперы,
извлекатели конфигурации, сериализаторы и другая генерируемая инфраструктура часто нуждаются в таком токене типа.

Большинству прикладных сервисов внедрять `TypeRef<T>` напрямую не нужно. Считайте его инструментом инфраструктуры для кода, который создает или адаптирует компоненты на основе обобщенных типов. Когда он
все же нужен, параметр типа должен описывать ровно ту модель, за которую отвечает компонент.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.TypeRef;

    @Module
    public interface ValidatorModule {
        default <T> Validator<List<T>> listValidator(Validator<T> validator, TypeRef<T> valueRef) {
            return new IterableValidator<>(validator);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.TypeRef

    @Module
    interface ValidatorModule {
        fun <T> listValidator(validator: Validator<T>, valueRef: TypeRef<T>): Validator<List<T>> =
            IterableValidator(validator)
    }
    ```

### Контракт типов-оберток { #wrapper-type-contract }

Типы-обертки — это способ Kora выразить поведение зависимости, не меняя запрашиваемый компонент. `ValueOf<T>` говорит «дай ссылку на этот компонент», `PromiseOf<T>` — «дай ссылку, которая разрешится
позже», а `All<T>` — «дай все подходящие компоненты». Обернутый `T` остается бизнес-типом; обертка меняет лишь то, как Kora его разрешает и предоставляет.

Такое разделение сохраняет API читаемым. Конструктор, принимающий `UserRepository`, требует один репозиторий. Конструктор с `ValueOf<UserRepository>` требует управляемого доступа к репозиторию.
Конструктор с `All<Notifier>` требует набор реализаций нотификаторов. Эти сигнатуры документируют связь в графе прямо в коде.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface ValueOf<T> {
        T get();

        <Q> ValueOf<Q> map(Function<T, Q> mapper);
    }

    public interface PromiseOf<T> {
        Optional<T> get();

        <Q> PromiseOf<Q> map(Function<T, Q> mapper);
    }

    public sealed interface All<T> extends Iterable<T> {
        // Token type extending Iterable
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface ValueOf<T> {
        fun get(): T

        fun <Q> map(mapper: Function<T, Q>): ValueOf<Q>
    }

    interface PromiseOf<T> {
        fun get(): Optional<T>

        fun <Q> map(mapper: Function<T, Q>): PromiseOf<Q>
    }

    sealed interface All<T> : Iterable<T> {
        // Token type extending Iterable
    }
    ```

Есть и `Wrapped<T>`: компонент, объявленный как `Wrapped<T>`, удовлетворяет заявкам на `T`. Это позволяет модулю навесить обработку жизненного цикла на сторонний объект, не протаскивая обертку в
сигнатуры потребителей. Готовая реализация ровно для этого — `LifecycleWrapper<T>`.

### Правила разрешения зависимостей { #dependency-resolution-rules }

Kora разрешает зависимости предсказуемо. Сначала определяется форма запрошенного типа, затем применяются теги и обертки, затем выбирается подходящее объявление. Если результат отсутствует, неоднозначен
или цикличен, генерация графа падает с ошибкой компиляции.

Именно поэтому важны явные объявления компонентов. Добавить зависимость в файл сборки недостаточно, чтобы все компоненты этой библиотеки появились в графе. Приложение должно подключить нужный модуль,
объявить нужный компонент или запросить нужный тег. Сгенерированный граф — окончательный источник правды о том, что реально работает.

1. **Сопоставление по типу**: кандидатом становится компонент, тип которого совместим с типом заявки
2. **Фильтрация по тегу**: заявка без тега подходит только компонентам без тега, заявка с тегом — только ровно этому тегу, а `Tag.Any` — всему
3. **Предпочтение неумолчальных**: кандидаты без `@DefaultComponent` побеждают кандидатов с ней
4. **Поиск циклов**: циклические зависимости обнаруживаются во время компиляции
5. **Обнуляемость**: `@Nullable` и `Optional<T>` помечают необязательные зависимости и разрешаются в отсутствие вместо ошибки
6. **«Сырые» типы запрещены**: заявка на «сырой» обобщенный тип ломает сборку, потому что делает разрешение неоднозначным

### Косвенные зависимости { #indirect-dependencies }

Используйте `ValueOf<T>`, чтобы избежать каскадного пересоздания компонентов при обновлении зависимостей:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ServiceModule {
        default ServiceA serviceA() {
            return new ServiceA();
        }

        default ServiceB serviceB() {
            return new ServiceB();
        }

        default ServiceC serviceC(ServiceA serviceA, ValueOf<ServiceB> serviceB) {
            // ServiceC depends on ServiceA directly (refreshes cascade to ServiceC)
            // ServiceC depends on ServiceB indirectly via ValueOf<T> (prevents cascading refreshes)
            return new ServiceC(serviceA, serviceB);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ServiceModule {
        fun serviceA(): ServiceA = ServiceA()

        fun serviceB(): ServiceB = ServiceB()

        fun serviceC(serviceA: ServiceA, serviceB: ValueOf<ServiceB>): ServiceC {
            // ServiceC depends on ServiceA directly (refreshes cascade to ServiceC)
            // ServiceC depends on ServiceB indirectly via ValueOf<T> (prevents cascading refreshes)
            return ServiceC(serviceA, serviceB)
        }
    }
    ```

**Почему `ValueOf<T>` важен:** каждый узел сгенерированного графа хранит и *зависимости создания*, и *зависимости обновления*. Прямая зависимость попадает в оба списка, поэтому обновление зависимости
пересоздает потребителя. Зависимость через `ValueOf<T>` попадает только в список создания, поэтому потребитель продолжает работать тем же экземпляром и просто читает новое значение через `get()`.
Обновления инициирует фреймворк — например, наблюдатель за файлом конфигурации, — а не код приложения.

---

## Система тегов { #tag-system }

Теги позволяют нескольким реализациям одного интерфейса сосуществовать и различаться при внедрении зависимостей. Теги используют ссылки на классы, а не строки, поэтому переименования безопасны, а
использования находятся средствами IDE.

### Использование тегов { #tags }

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Tag classes (usually empty marker classes)
    public final class RedisTag {
        private RedisTag() {}
    }

    public final class InMemoryTag {
        private InMemoryTag() {}
    }

    // Tagged implementations
    @Tag(RedisTag.class)
    @Component
    public final class RedisCache implements Cache {
        // Redis implementation
    }

    @Tag(InMemoryTag.class)
    @Component
    public final class InMemoryCache implements Cache {
        // In-memory implementation
    }

    // Selective injection
    @Component
    public final class UserService {
        public UserService(@Tag(RedisTag.class) Cache cache) {
            // Injects RedisCache specifically
        }
    }

    @Component
    public final class ProductService {
        public ProductService(@Tag(InMemoryTag.class) Cache cache) {
            // Injects InMemoryCache specifically
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Tag classes (usually empty marker classes)
    class RedisTag private constructor()

    class InMemoryTag private constructor()

    // Tagged implementations
    @Tag(RedisTag::class)
    @Component
    class RedisCache : Cache {
        // Redis implementation
    }

    @Tag(InMemoryTag::class)
    @Component
    class InMemoryCache : Cache {
        // In-memory implementation
    }

    // Selective injection
    @Component
    class UserService(@Tag(RedisTag::class) private val cache: Cache) {
        // Injects RedisCache specifically
    }

    @Component
    class ProductService(@Tag(InMemoryTag::class) private val cache: Cache) {
        // Injects InMemoryCache specifically
    }
    ```

### Теги на классах { #class-tags }

Теги можно ставить прямо на классы компонентов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(RedisTag.class)
    @Component
    public final class RedisCache implements Cache {
        // Implementation
    }

    @Tag(InMemoryTag.class)
    @Component
    public final class InMemoryCache implements Cache {
        // Implementation
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(RedisTag::class)
    @Component
    class RedisCache : Cache {
        // Implementation
    }

    @Tag(InMemoryTag::class)
    @Component
    class InMemoryCache : Cache {
        // Implementation
    }
    ```

### Теги на методах { #method-tags }

Теги можно ставить на фабричные методы:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface CacheModule {
        @Tag(RedisTag.class)
        default Cache redisCache() {
            return new RedisCache();
        }

        @Tag(InMemoryTag.class)
        default Cache inMemoryCache() {
            return new InMemoryCache();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface CacheModule {
        @Tag(RedisTag::class)
        fun redisCache(): Cache = RedisCache()

        @Tag(InMemoryTag::class)
        fun inMemoryCache(): Cache = InMemoryCache()
    }
    ```

### Теги аннотации { #annotation-tags }

Переиспользуемые аннотации-теги создаются пометкой собственной аннотации через `@Tag`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(RedisTag.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
    public @interface RedisCache {}

    @Tag(InMemoryTag.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
    public @interface InMemoryCache {}

    // Usage
    @RedisCache
    @Component
    public final class RedisCacheImpl implements Cache {}

    @Component
    public final class UserService {
        public UserService(@RedisCache Cache cache) {
            // Injects RedisCacheImpl
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(RedisTag::class)
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.VALUE_PARAMETER)
    annotation class RedisCache

    @Tag(InMemoryTag::class)
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.VALUE_PARAMETER)
    annotation class InMemoryCache

    // Usage
    @RedisCache
    @Component
    class RedisCacheImpl : Cache

    @Component
    class UserService(@RedisCache private val cache: Cache) {
        // Injects RedisCacheImpl
    }
    ```

### Специальные теги { #special-tags }

Специальные формы тегов нужны, когда обычные правила сопоставления слишком узкие. Они позволяют осознанно расширить запрос, не теряя типобезопасности. Чаще всего это встречается с `All<T>`, когда нужны
либо все реализации точки расширения, либо все реализации из конкретной группы тегов.

Пользуйтесь специальными тегами умеренно. Они мощные, потому что меняют смысл запроса зависимости. Обычный тег говорит «только эта группа»; `Tag.Any` говорит «игнорировать группировку»; `All<T>` с тегом
говорит «собрать всю группу».

#### @Tag.Any { #tag-any }

Подходит всем компонентам независимо от их тегов.
`@Tag(Tag.Any.class)` — самый широкий запрос. Он полезен, когда потребитель намеренно универсален: реестр, диагностический компонент или диспетчер, который должен видеть и помеченные, и непомеченные
реализации. Без `Tag.Any` заявка без тега подходит только компонентам без тега.

Поскольку такой запрос расширяет ребро графа, `Tag.Any` должен быть виден в сигнатуре конструктора и использоваться только там, где широкое поведение — часть замысла. Если сервису нужны только
Redis-кеши или только email-нотификаторы, запрашивайте конкретный тег.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(@Tag(Tag.Any.class) All<Notifier> notifiers) {
            // Receives ALL notifiers, both tagged and untagged
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NotificationService(@Tag(Tag.Any::class) private val notifiers: All<Notifier>) {
        // Receives ALL notifiers, both tagged and untagged
    }
    ```

#### All с тегом { #tagged-all }

Получить все компоненты с конкретным тегом.
Этот прием собирает все реализации, разделяющие один тег. Он полезен, когда у подсистемы несколько реализаций, но все они принадлежат одной именованной группе: кеши поверх Redis, интерцепторы
публичного API, внутренние health-check или конкретная группа арендаторов и провайдеров.

Тег удерживает коллекцию в фокусе. Компоненты того же типа могут существовать в графе и в других местах, не попадая в коллекцию. Это делает `All<T>` практичным в больших приложениях, где один интерфейс
переиспользуется для нескольких независимых задач.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CacheRegistry {
        public CacheRegistry(@Tag(RedisTag.class) All<Cache> caches) {
            // Receives all Cache implementations tagged with RedisTag
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CacheRegistry(@Tag(RedisTag::class) private val caches: All<Cache>) {
        // Receives all Cache implementations tagged with RedisTag
    }
    ```

### Правила сопоставления тегов { #tag-matching-rules }

Сопоставление тегов намеренно точное. Kora считает тег частью идентичности зависимости наравне с типом. Это исключает случайное внедрение не той реализации, когда несколько компонентов разделяют
интерфейс, но принадлежат разным контекстам.

Если зависимость не разрешается, проверяйте и тип, и тег. Компонент с нужным типом, но не тем тегом — не кандидат. Компилятор здесь помогает: в сообщении об ошибке перечисляются кандидаты того же типа
с другим тегом.

1. **Без тега к без тега**: заявка без тега подходит только компонентам без тега
2. **Точное совпадение**: заявка с тегом подходит только компонентам ровно с этим классом-тегом
3. **`Tag.Any` побеждает**: заявка с тегом `Tag.Any` подходит любому компоненту этого типа
4. **Один тег на объявление**: `@Tag` несет один класс, поэтому компонент принадлежит максимум одной группе тегов
5. **Наследование тегов не работает**: сравнивается сам класс-тег, поэтому тег-наследник не совпадает с родительским

---

## Законченный пример { #complete-example }

Все описанное выше собирается в небольшом работающем приложении: две реализации нотификатора, различаемые тегами, форматтер, объявленный заменяемым умолчанием, необязательный аудит-приемник, которого в
графе нет, и корневой сервис, собирающий все нотификаторы.

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.dependencyinjection;

    @FunctionalInterface
    public interface MessageFormatter {
        String format(String message);
    }

    public interface Notifier {
        String channel();

        String notifyUser(String message);
    }

    public interface AuditSink {
        void record(String channel, String message);
    }

    public final class EmailTag {
        private EmailTag() {}
    }

    public final class SmsTag {
        private SmsTag() {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.dependencyinjection

    fun interface MessageFormatter {
        fun format(message: String): String
    }

    interface Notifier {
        fun channel(): String

        fun notifyUser(message: String): String
    }

    interface AuditSink {
        fun record(channel: String, message: String)
    }

    class EmailTag private constructor()

    class SmsTag private constructor()
    ```

Оба нотификатора — классы `@Component`, помеченные тегами, чтобы их можно было различить:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;

    @Tag(EmailTag.class)
    @Component
    public final class EmailNotifier implements Notifier {

        private final MessageFormatter formatter;

        public EmailNotifier(MessageFormatter formatter) {
            this.formatter = formatter;
        }

        @Override
        public String channel() {
            return "email";
        }

        @Override
        public String notifyUser(String message) {
            return "EMAIL: " + formatter.format(message);
        }
    }

    @Tag(SmsTag.class)
    @Component
    public final class SmsNotifier implements Notifier {

        private final MessageFormatter formatter;

        public SmsNotifier(MessageFormatter formatter) {
            this.formatter = formatter;
        }

        @Override
        public String channel() {
            return "sms";
        }

        @Override
        public String notifyUser(String message) {
            return "SMS: " + formatter.format(message);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag

    @Tag(EmailTag::class)
    @Component
    class EmailNotifier(
        private val formatter: MessageFormatter
    ) : Notifier {

        override fun channel(): String = "email"

        override fun notifyUser(message: String): String = "EMAIL: ${formatter.format(message)}"
    }

    @Tag(SmsTag::class)
    @Component
    class SmsNotifier(
        private val formatter: MessageFormatter
    ) : Notifier {

        override fun channel(): String = "sms"

        override fun notifyUser(message: String): String = "SMS: ${formatter.format(message)}"
    }
    ```

Сервис является корнем графа. Он запрашивает все нотификаторы через `@Tag(Tag.Any.class)`, один конкретный нотификатор по тегу и необязательный аудит-приемник:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.All;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Root;
    import io.koraframework.common.annotation.Tag;
    import org.jspecify.annotations.Nullable;

    import java.util.ArrayList;
    import java.util.List;

    @Root
    @Component
    public final class NotificationService {

        private final All<Notifier> notifiers;
        private final Notifier emailNotifier;
        @Nullable
        private final AuditSink auditSink;

        public NotificationService(
                @Tag(Tag.Any.class) All<Notifier> notifiers,     //(1)!
                @Tag(EmailTag.class) Notifier emailNotifier,     //(2)!
                @Nullable AuditSink auditSink) {                 //(3)!
            this.notifiers = notifiers;
            this.emailNotifier = emailNotifier;
            this.auditSink = auditSink;
        }

        public List<String> broadcast(String message) {
            var result = new ArrayList<String>();
            for (var notifier : this.notifiers) {
                var output = notifier.notifyUser(message);
                result.add(output);
                if (this.auditSink != null) {
                    this.auditSink.record(notifier.channel(), output);
                }
            }
            return result;
        }

        public String notifyEmailOnly(String message) {
            var output = this.emailNotifier.notifyUser(message);
            if (this.auditSink != null) {
                this.auditSink.record(this.emailNotifier.channel(), output);
            }
            return output;
        }

        public boolean isAuditEnabled() {
            return this.auditSink != null;
        }
    }
    ```

    1. Оба нотификатора помечены тегами, поэтому для сбора их в один `All<Notifier>` нужен `Tag.Any`.
    2. Заявка с тегом выбирает ровно одну реализацию.
    3. `AuditSink` никто не предоставляет, поэтому граф передает `null`, а не ломает сборку.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.All
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Root
    import io.koraframework.common.annotation.Tag

    @Root
    @Component
    class NotificationService(
        @Tag(Tag.Any::class) private val notifiers: All<Notifier>,   //(1)!
        @Tag(EmailTag::class) private val emailNotifier: Notifier,   //(2)!
        private val auditSink: AuditSink?                            //(3)!
    ) {

        fun broadcast(message: String): List<String> {
            return notifiers.map { notifier ->
                val output = notifier.notifyUser(message)
                auditSink?.record(notifier.channel(), output)
                output
            }
        }

        fun notifyEmailOnly(message: String): String {
            val output = emailNotifier.notifyUser(message)
            auditSink?.record(emailNotifier.channel(), output)
            return output
        }

        fun isAuditEnabled(): Boolean = auditSink != null
    }
    ```

    1. Оба нотификатора помечены тегами, поэтому для сбора их в один `All<Notifier>` нужен `Tag.Any`.
    2. Заявка с тегом выбирает ровно одну реализацию.
    3. `AuditSink` никто не предоставляет, поэтому граф передает `null`, а не ломает сборку.

Наконец, интерфейс приложения подключает модули фреймворка, объявляет вложенный модуль с заменяемым форматтером по умолчанию и заменяет его:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.DefaultComponent;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.common.annotation.Module;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends HoconConfigModule, LogbackModule, NotificationModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);    //(1)!
        }

        default MessageFormatter messageFormatter() {       //(2)!
            return message -> "[app] " + message;
        }
    }

    @Module
    interface NotificationModule {

        @DefaultComponent
        default MessageFormatter defaultMessageFormatter() {
            return message -> "[default] " + message;
        }
    }
    ```

    1. `ApplicationGraph` генерируется из интерфейса `Application`; `graph()` возвращает описание графа.
    2. У этой фабрики нет `@DefaultComponent`, поэтому она побеждает `defaultMessageFormatter()`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.DefaultComponent
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.common.annotation.Module
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application : HoconConfigModule, LogbackModule, NotificationModule {

        fun messageFormatter(): MessageFormatter {          //(2)!
            return MessageFormatter { message -> "[app] $message" }
        }
    }

    @Module
    interface NotificationModule {

        @DefaultComponent
        fun defaultMessageFormatter(): MessageFormatter {
            return MessageFormatter { message -> "[default] $message" }
        }
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)         //(1)!
    }
    ```

    1. `ApplicationGraph` генерируется из интерфейса `Application`; `graph()` возвращает описание графа.
    2. У этой фабрики нет `@DefaultComponent`, поэтому она побеждает `defaultMessageFormatter()`.

Сборка подключает BOM Kora, обработчик и два использованных выше модуля фреймворка:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        implementation platform("io.koraframework:kora-bom:$koraVersion")
        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"

        testImplementation "io.koraframework:test-junit5"
        testAnnotationProcessor "io.koraframework:annotation-processors"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:$koraVersion"))
        ksp("io.koraframework:symbol-processors")

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")

        testImplementation("io.koraframework:test-junit5")
    }
    ```

### Тестирование графа { #testing-graph }

Поскольку граф — это скомпилированный артефакт, тест может поднять настоящий граф приложения и достать из него компонент. `@KoraAppTest` указывает на интерфейс `@KoraApp`, а `@TestComponent` внедряет
компонент из инициализированного графа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;
    import org.junit.jupiter.api.Test;

    import static org.junit.jupiter.api.Assertions.*;

    @KoraAppTest(Application.class)
    class NotificationServiceTest {

        @TestComponent
        private NotificationService notificationService;

        @Test
        void broadcastShouldUseAllNotifiers() {
            var result = notificationService.broadcast("Hello");

            assertEquals(2, result.size());
            assertTrue(result.contains("EMAIL: [app] Hello"));
            assertTrue(result.contains("SMS: [app] Hello"));
        }

        @Test
        void notifyEmailOnlyShouldResolveTaggedNotifier() {
            assertEquals("EMAIL: [app] Ping", notificationService.notifyEmailOnly("Ping"));
        }

        @Test
        void optionalAuditDependencyShouldBeAbsent() {
            assertFalse(notificationService.isAuditEnabled());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent
    import org.junit.jupiter.api.Assertions.*
    import org.junit.jupiter.api.Test

    @KoraAppTest(Application::class)
    class NotificationServiceTest {

        @TestComponent
        lateinit var notificationService: NotificationService

        @Test
        fun broadcastUsesAllTaggedAndUntaggedNotifiers() {
            val result = notificationService.broadcast("hello")

            assertEquals(2, result.size)
            assertTrue(result.contains("EMAIL: [app] hello"))
            assertTrue(result.contains("SMS: [app] hello"))
        }

        @Test
        fun emailOnlyUsesTaggedComponent() {
            assertEquals("EMAIL: [app] hello", notificationService.notifyEmailOnly("hello"))
        }

        @Test
        fun optionalAuditSinkIsAbsent() {
            assertFalse(notificationService.isAuditEnabled())
        }
    }
    ```

Ожидание `[app]`, а не `[default]`, — это сквозная проверка правила замены из раздела [`@DefaultComponent`](#defaultcomponent).

### Что дальше { #whats-next }

Теперь, когда основные понятия внедрения зависимостей в Kora понятны, самое время собрать их вместе. Продолжайте с руководства **[Создание приложений Kora с внедрением зависимостей](dependency-injection.md)** —
пошагового разбора, в котором строится полноценная система уведомлений и эти понятия применяются на практике.

Руководство охватывает:

- настройку проекта и многомодульную структуру
- модули внешних библиотек с умолчаниями
- замену и настройку компонентов
- зависимости с тегами и внедрение коллекций
- необязательные зависимости и мягкую деградацию
- подмодули и организацию компонентов
- обобщенные фабрики и типобезопасное создание
- косвенные зависимости через `ValueOf<T>`

---

## Лучшие практики { #best-practices }

### Держите компоненты маленькими и сфокусированными { #components-focused }

Почему это важно: маленькие компоненты проще тестировать, понимать и переиспользовать. У каждого компонента должна быть одна ответственность.

Совет новичку: если компонент делает слишком много, разбейте его. Спросите себя: «в чем единственная задача этого компонента?»

Хороший пример:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Single responsibility components
    @Component
    public final class OrderValidator {
        public ValidationResult validate(Order order) { /* validation logic */ }
    }

    @Component
    public final class OrderProcessor {
        private final PaymentService payment;
        private final OrderRepository repository;

        public OrderProcessor(PaymentService payment, OrderRepository repository) {
            this.payment = payment;
            this.repository = repository;
        }

        public void process(Order order) {
            // Just coordinates payment and storage
            payment.processPayment(order);
            repository.save(order);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Single responsibility components
    @Component
    class OrderValidator {
        fun validate(order: Order): ValidationResult { /* validation logic */ }
    }

    @Component
    class OrderProcessor(
        private val payment: PaymentService,
        private val repository: OrderRepository
    ) {
        fun process(order: Order) {
            // Just coordinates payment and storage
            payment.processPayment(order)
            repository.save(order)
        }
    }
    ```

### Предпочитайте внедрение через конструктор { #prefer-constructor-injection }

Почему это важно: внедрение через конструктор делает зависимости явными и не допускает частично сконструированных объектов. Для компонентов Kora это единственный поддерживаемый способ внедрения и самый
удобный для тестирования.

Совет новичку: всегда объявляйте зависимости в конструкторе. Никогда не ищите зависимости внутри методов — это антипаттерн Service Locator.

Хороший пример:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {
        private final UserRepository repository;
        private final PasswordEncoder encoder;

        // All dependencies declared in constructor
        public UserService(UserRepository repository, PasswordEncoder encoder) {
            this.repository = repository;
            this.encoder = encoder;
        }

        public User createUser(String email, String password) {
            String hashedPassword = encoder.encode(password);
            User user = new User(email, hashedPassword);
            return repository.save(user);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(
        private val repository: UserRepository,
        private val encoder: PasswordEncoder
    ) {
        // All dependencies declared in the primary constructor

        fun createUser(email: String, password: String): User {
            val hashedPassword = encoder.encode(password)
            val user = User(email, hashedPassword)
            return repository.save(user)
        }
    }
    ```

### Аккуратно обрабатывайте необязательные зависимости { #handle-optional-dependencies }

Почему это важно: не все возможности доступны всегда. Необязательные зависимости позволяют приложению работать в разных конфигурациях.

Совет новичку: в Java используйте `@Nullable` из JSpecify, в Kotlin — обнуляемый тип. Всегда явно обрабатывайте отсутствие.

Хороший пример:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import org.jspecify.annotations.Nullable;

    @Component
    public final class NotificationService {
        private final EmailService emailService;
        @Nullable
        private final SmsService smsService; // Might not be configured

        public NotificationService(EmailService emailService, @Nullable SmsService smsService) {
            this.emailService = emailService;
            this.smsService = smsService;
        }

        public void sendNotification(String message) {
            emailService.sendEmail(message); // Always available

            // Graceful handling of optional dependency
            if (smsService != null) {
                smsService.sendSms(message);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NotificationService(
        private val emailService: EmailService,
        private val smsService: SmsService? // Might not be configured
    ) {
        fun sendNotification(message: String) {
            emailService.sendEmail(message) // Always available

            // Graceful handling of optional dependency
            smsService?.sendSms(message)
        }
    }
    ```

### Используйте теги для нескольких реализаций { #use-tags-implementations }

Почему это важно: иногда нужно несколько реализаций одного интерфейса (например, разные каналы уведомлений). Теги позволяют их различать.

Совет новичку: заводите отдельные классы-маркеры с говорящими именами вроде `EmailTag` и делайте им приватный конструктор, чтобы никто случайно не создал экземпляр.

Хороший пример:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Tag classes
    public final class EmailTag {
        private EmailTag() {}
    }

    public final class SmsTag {
        private SmsTag() {}
    }

    // Tagged implementations
    @Tag(EmailTag.class)
    @Component
    public final class EmailNotifier implements Notifier {
        @Override
        public void notifyUser(String message) { /* email logic */ }
    }

    @Tag(SmsTag.class)
    @Component
    public final class SmsNotifier implements Notifier {
        @Override
        public void notifyUser(String message) { /* SMS logic */ }
    }

    // Usage
    @Component
    public final class AlertService {
        private final Notifier emailNotifier;
        private final Notifier smsNotifier;

        public AlertService(
                @Tag(EmailTag.class) Notifier emailNotifier,
                @Tag(SmsTag.class) Notifier smsNotifier) {
            this.emailNotifier = emailNotifier;
            this.smsNotifier = smsNotifier;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Tag classes
    class EmailTag private constructor()

    class SmsTag private constructor()

    // Tagged implementations
    @Tag(EmailTag::class)
    @Component
    class EmailNotifier : Notifier {
        override fun notifyUser(message: String) { /* email logic */ }
    }

    @Tag(SmsTag::class)
    @Component
    class SmsNotifier : Notifier {
        override fun notifyUser(message: String) { /* SMS logic */ }
    }

    // Usage
    @Component
    class AlertService(
        @Tag(EmailTag::class) private val emailNotifier: Notifier,
        @Tag(SmsTag::class) private val smsNotifier: Notifier
    )
    ```

### Организуйте компоненты модулями { #organize-with-modules }

Почему это важно: модули группируют связанные компоненты, что делает приложение понятнее и удобнее в сопровождении.

Совет новичку: создавайте модули по слоям (база данных, сервисы, HTTP) или по предметным областям (сообщения, уведомления, управление пользователями).

Хороший пример:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Individual messenger modules for different channels
    @Module
    public interface SlackModule {

        @Tag(SlackTag.class)
        @DefaultComponent
        default Supplier<String> slackMessengerHeaderSupplier() {
            return () -> "ASCII_PROTOCOL_MESSENGER_SLACK";
        }
    }

    @Module
    public interface SignalModule {

        @Tag(SignalTag.class)
        @DefaultComponent
        default Supplier<String> signalMessengerHeaderSupplier() {
            return () -> "ASCII_PROTOCOL_MESSENGER_SIGNAL";
        }
    }

    @Component
    public final class SlackMessenger implements Messenger {

        private final Supplier<String> headerSupplier;

        public SlackMessenger(@Tag(SlackTag.class) Supplier<String> headerSupplier) {
            this.headerSupplier = headerSupplier;
        }

        @Override
        public void sendMessage(String message) {
            String header = headerSupplier.get();
            System.out.println(header + " ---> " + message);
        }
    }

    @Component
    public final class SignalMessenger implements Messenger {

        private final Supplier<String> headerSupplier;

        public SignalMessenger(@Tag(SignalTag.class) Supplier<String> headerSupplier) {
            this.headerSupplier = headerSupplier;
        }

        @Override
        public void sendMessage(String message) {
            String header = headerSupplier.get();
            System.out.println(header + " ---> " + message);
        }
    }

    // Application combines messenger modules
    @KoraApp
    public interface Application extends
        SlackModule,        // Slack messaging
        SignalModule {      // Signal messaging

        @Root
        default Dispatcher dispatcher(@Tag(Tag.Any.class) All<Messenger> messengers) {
            return new Dispatcher(messengers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Individual messenger modules for different channels
    @Module
    interface SlackModule {

        @Tag(SlackTag::class)
        @DefaultComponent
        fun slackMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SLACK" }
    }

    @Module
    interface SignalModule {

        @Tag(SignalTag::class)
        @DefaultComponent
        fun signalMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SIGNAL" }
    }

    @Component
    class SlackMessenger(
        @Tag(SlackTag::class) private val headerSupplier: Supplier<String>
    ) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    @Component
    class SignalMessenger(
        @Tag(SignalTag::class) private val headerSupplier: Supplier<String>
    ) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    // Application combines messenger modules
    @KoraApp
    interface Application :
        SlackModule,        // Slack messaging
        SignalModule {      // Signal messaging

        @Root
        fun dispatcher(@Tag(Tag.Any::class) messengers: All<Messenger>): Dispatcher =
            Dispatcher(messengers)
    }
    ```

### Избегайте типичных антипаттернов { #anti-patterns }

**Service Locator:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Don't do this
    @Component
    public final class BadService {
        public void doSomething() {
            // Looking dependencies up inside methods
            Database db = ServiceLocator.getDatabase(); // Anti-pattern
            db.save(data);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Don't do this
    @Component
    class BadService {
        fun doSomething() {
            // Looking dependencies up inside methods
            val db = ServiceLocator.getDatabase() // Anti-pattern
            db.save(data)
        }
    }
    ```

**Циклические зависимости:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Don't create circular dependencies
    @Component
    public final class ServiceA {
        public ServiceA(ServiceB b) {} // ServiceA depends on ServiceB
    }

    @Component
    public final class ServiceB {
        public ServiceB(ServiceA a) {} // ServiceB depends on ServiceA - CIRCULAR!
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Don't create circular dependencies
    @Component
    class ServiceA(private val b: ServiceB) // ServiceA depends on ServiceB

    @Component
    class ServiceB(private val a: ServiceA) // ServiceB depends on ServiceA - CIRCULAR!
    ```

Kora сообщает об этом во время компиляции. Когда цикл неизбежен, выразите одно из ребер через интерфейс и позвольте Kora сгенерировать делегирующий прокси либо запросите зависимость как `PromiseOf<T>`.
Перестройка ответственностей почти всегда лучше.

**Слишком большие компоненты:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    // Don't create "God objects"
    @Component
    public final class HugeService {
        // Does everything: validation, database, email, logging, caching...
        private final Validator validator;
        private final Repository repo;
        private final EmailService email;
        private final Logger logger;
        private final Cache cache;

        // Hundreds of methods...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // Don't create "God objects"
    @Component
    class HugeService(
        // Does everything: validation, database, email, logging, caching...
        private val validator: Validator,
        private val repo: Repository,
        private val email: EmailService,
        private val logger: Logger,
        private val cache: Cache
    ) {
        // Hundreds of methods...
    }
    ```

**Правила, которые стоит держать в голове:**

- предпочитайте внедрение через конструктор и позвольте Kora строить граф зависимостей во время компиляции
- держите компоненты сфокусированными на одной ответственности, чтобы ошибки графа оставались понятными
- используйте модули для переиспользуемых фабрик и умолчаний, а не как место, где прячется логика приложения
- используйте теги только тогда, когда у одного контракта есть несколько осмысленных реализаций
- помечайте `@Root` точки входа и только их
- избегайте Service Locator, циклических зависимостей и больших компонентов, смешивающих несвязанные обязанности

## Итоги { #summary }

Вы разобрали основные идеи внедрения зависимостей в Kora:

- компоненты объявляют свои потребности через конструкторы или фабричные методы
- Kora проверяет и генерирует граф зависимостей во время компиляции, без рефлексии во время выполнения
- разрешение начинается с `@Root`, поэтому строится только то, что нужно точке входа
- модули группируют переиспользуемые фабрики, а `@DefaultComponent` делает их заменяемыми
- теги различают несколько реализаций одного типа, а `All<T>` собирает точки расширения
- `ValueOf<T>` и `PromiseOf<T>` выражают косвенный доступ, не меняя бизнес-тип
- внедрение зависимостей сохраняет структуру приложения явной и тестируемой

## Устранение неполадок { #troubleshooting }

**`No component found for dependency`**

```
No component found for dependency:
  com.example.UserRepository (no tags)

Required at:
  com.example.Application#userService(com.example.UserRepository)
  parameter: com.example.UserRepository repository

Dependency resolution path:
  @--- factory  com.example.Application#orderService(...)
  ^--- factory  com.example.Application#userService(...)
  ^--- com.example.UserRepository   [MISSING]

Fix:
  - Add @Component to an implementation of com.example.UserRepository.
  - Add a module method that returns com.example.UserRepository.
  - Include a module that provides com.example.UserRepository in @KoraApp.
```

- Проверьте, что класс помечен `@Component` или возвращается методом модуля
- Убедитесь, что модуль, предоставляющий его, подключен к интерфейсу `@KoraApp`
- Читайте `Dependency resolution path` снизу вверх: строка с `[MISSING]` — это заявка, которая не разрешилась, а строки выше показывают, кто ее запросил
- Если в ошибке упоминаются компоненты «with the same type but different tag», значит тег на заявке или на компоненте указан неверно

**`Multiple components match dependency`**

```
Multiple components match dependency:
  com.example.Cache (no tags)

  Candidates:
  - component  com.example.RedisCache
  - component  com.example.InMemoryCache

Fix:
  - Add different @Tag(...) annotations to candidates and request the needed tag.
  - Mark fallback candidate with @DefaultComponent.
  - Remove one duplicate provider.
```

- Добавьте тег на заявку и на компонент, который должен ее удовлетворить
- Либо пометьте запасного кандидата `@DefaultComponent`, чтобы победил другой
- Либо уберите дублирующего поставщика

**`@KoraApp has no root components`**

- Пометьте `@Root` хотя бы один компонент или метод модуля
- Если корень должен был прийти из модуля фреймворка, проверьте, что интерфейс `@KoraApp` действительно его наследует

**`Circular dependency found`**

```
Circular dependency found:
  com.example.ServiceA (no tags)

  Dependency cycle:
    @--- component  com.example.ServiceA
    ^--- component  com.example.ServiceB [CYCLE]

Fix:
  - Break the cycle with ValueOf<T> or PromiseOf<T> where lazy access is valid.
  - Move shared state into a separate component.
  - Do not create dependency cycles in io.koraframework.application.graph.Lifecycle.
```

- Вынесите общее состояние в третий компонент, от которого зависят обе стороны
- Выразите одно из ребер через интерфейс, чтобы Kora сгенерировала для него делегирующий прокси
- В крайнем случае запросите зависимость как `PromiseOf<T>` или `ValueOf<T>`

**`@Component class must have exactly one public constructor`**

- Оставьте один публичный конструктор, а остальные сделайте непубличными
- Либо уберите `@Component` и предоставьте класс методом модуля

**Сгенерированный граф не компилируется**

- Исправьте первую сообщенную ошибку и соберите заново; последующие ошибки часто являются ее следствием
- Когда решение о связывании непонятно, откройте сгенерированный `<ИмяПриложения>Graph` в `build/generated` — это обычный исходный код

## Что дальше? { #whats-next-2 }

- [Соберите полноценное приложение с внедрением зависимостей](dependency-injection.md), чтобы попрактиковаться с модулями, компонентами, фабриками, тегами, жизненным циклом и построением графа без HTTP-шума.
- [Создайте первое приложение на Kora](getting-started.md), если вы начали со введения и теперь хотите запустить минимальное приложение.
- [Конфигурация через HOCON](config-hocon.md) или [Конфигурация через YAML](config-yaml.md) — после первого запуска, потому что конфигурация опирается на уже работающее приложение Kora.

## Помощь { #help }

Если возникли сложности:

- посмотрите [документацию по контейнеру](../documentation/container.md)
- сравните с базовыми примерами в [Kora Examples](home.md)
- перечитайте [Создание первого приложения на Kora](getting-started.md), где граф запускается целиком
