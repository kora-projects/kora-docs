---
search:
  exclude: true
title: Внедрение зависимостей в Kora
summary: Learn the fundamentals of dependency injection using Kora's compile-time DI framework
tags: dependency-injection, di, kora-app, component, module, compile-time
---

# Внедрение зависимостей в Kora { #dependency-injection-kora }

Это руководство знакомит с внедрением зависимостей и инверсией управления через контейнер Kora, который работает во время компиляции. В нем рассматривается, как объекты приложения объявляют
зависимости через конструкторы, как `@Component` и `@Module` делают эти объекты доступными для графа, и как Kora проверяет связывание во время компиляции вместо того, чтобы обнаруживать отсутствующие
зависимости во время выполнения. Вы также увидите, почему внедрение зависимостей во время компиляции меняет поведение запуска, типобезопасность и тестируемость.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Dependency Injection Introduction App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-dependency-injection-introduction-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Dependency Injection Introduction App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-dependency-injection-introduction-app).

## Что вы изучите { #youll-learn }

Вы изучите основные понятия внедрения зависимостей и поймете:

- Основные понятия внедрения зависимостей: что такое внедрение зависимостей и почему оно важно
- Архитектура Kora: как работает внедрение зависимостей во время компиляции и какие у него преимущества
- Жизненный цикл компонентов: как компоненты создаются, управляются и уничтожаются
- Система модулей: как организовывать и структурировать компоненты приложения
- Лучшие практики: шаблоны для написания поддерживаемого и тестируемого кода

## Что потребуется { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- базовое понимание Java или Kotlin

## Требования { #prerequisites }

!!! note "Предварительные знания не требуются"

    Это руководство рассчитано на новичков и не требует предварительного знания внедрения зависимостей или Kora.

    Достаточно базового знакомства с Java или Kotlin, потому что руководство вводит понятия внедрения зависимостей в Kora с самых основ, прежде чем показывать шаблоны, связанные с фреймворком.

## Обзор { #overview }

Внедрение зависимостей — это способ собирать приложение из явно объявленных зависимостей, вместо того чтобы позволять объектам самостоятельно создавать все, что им нужно. Зависимость — это просто “то,
что нужно классу для работы”: репозиторий, клиент, объект конфигурации, кеш, часы или другой сервис.

В маленькой программе естественно писать `new` повсюду. Контроллер может создать сервис, сервис может создать репозиторий, а репозиторий может создать все, что ему нужно. Но как только программа
растет, это становится трудно поддерживать:

- классы знают слишком много о том, как создаются другие классы
- тесты становятся сложными, потому что зависимости создаются внутри класса
- замена одной реализации требует правок во многих местах
- логика запуска расползается по кодовой базе
- детали конфигурации и инфраструктуры протекают в бизнес-код

Внедрение зависимостей исправляет это, меняя правило: класс не должен строить собственных соисполнителей. Он должен объявить, что ему нужно, обычно через конструктор, и позволить графу приложения
предоставить эти объекты.

### Маленький пример { #small-example }

Без внедрения зависимостей сервис может создавать свой репозиторий напрямую:

```java
public final class UserService {
    private final UserRepository repository = new InMemoryUserRepository();
}
```

Это выглядит просто, но теперь `UserService` привязан к одной реализации репозитория. Тест не может легко заменить ее. Будущий репозиторий для базы данных нельзя подключить без изменения сервиса.

При внедрении через конструктор сервис только объявляет зависимость:

```java
public final class UserService {
    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }
}
```

Теперь `UserService` не важно, будет ли репозиторий хранить данные в памяти, работать через JDBC, подменяться в тесте или оборачиваться кешированием. Это решение переносится в граф приложения.

### Графы объектов { #object-graphs }

Приложение — это не просто куча классов. Это граф объектов, соединенных зависимостями. Например:

```text
UserController
  -> UserService
      -> UserRepository
      -> UserValidator
```

Это называется графом зависимостей или графом объектов. Каждая стрелка означает: “этому объекту нужен тот объект”. Главная задача Kora — корректно построить этот граф, запустить компоненты с жизненным
циклом в правильном порядке и завершить сборку ошибкой, если граф невозможно собрать.

Мышление графами — одно из самых важных понятий Kora. Когда вы добавляете контроллер, репозиторий, HTTP-клиент, кеш или объект конфигурации, вы добавляете в граф узел или ребро.

### Инверсия управления { #inversion-control }

Более глубокая идея внедрения зависимостей — инверсия управления. Вместо того чтобы сервис сам решал, как построить репозиторий, клиент, кеш или конфигурацию, он только объявляет, что они ему нужны.
Создание объектов выходит из сервиса и переходит в граф приложения.

Это меняет форму кода приложения:

- конструкторы описывают обязательных соисполнителей
- интерфейсы делают точки замены явными
- тесты могут предоставить имитации или альтернативные реализации
- связывание при запуске становится отдельной задачей, отделенной от бизнес-логики

### Внедрение зависимостей в Kora { #dependency-injection-kora-2 }

[Контейнер Kora, работающий во время компиляции](../documentation/container.md), реализует внедрение зависимостей во время компиляции. Интерфейс `@KoraApp` помечает корень графа, `@Component` помечает
классы, которыми управляет граф, а `@Module` добавляет фабрики или возможности фреймворка. Во время компиляции Kora анализирует граф и генерирует код, который создает и соединяет компоненты.

Это дает Kora другую модель отказов по сравнению с фреймворками внедрения зависимостей во время выполнения. Отсутствующие зависимости, неоднозначные связывания и некоторые проблемы жизненного цикла
могут быть обнаружены во время сборки, а не во время запуска приложения.

Для новичков самые важные аннотации:

- `@KoraApp`: корень графа приложения
- `@Component`: класс, который Kora может создать автоматически
- `@Module`: набор фабрик компонентов или импортированных модулей фреймворка

Можно думать об `@KoraApp` как о карте приложения, о `@Component` — как об узле графа, а о параметрах конструктора — как о стрелках между узлами.

### Внедрение во время компиляции { #compile-time-injection }

Внедрение зависимостей во время компиляции означает, что Kora проверяет и генерирует связывание во время сборки. Это важно, потому что многие ошибки внедрения зависимостей являются структурными
ошибками:

- у обязательной зависимости нет поставщика
- два поставщика подходят для одной зависимости, и Kora не может выбрать
- модуль не был импортирован в приложение
- компонент зависит от другого компонента, который невозможно построить

Во фреймворке внедрения зависимостей во время выполнения часть таких ошибок может появиться только при запуске приложения. В Kora сборка может упасть раньше, до упаковки или развертывания приложения.
Это ускоряет обратную связь и делает запуск в рабочем окружении более предсказуемым.

### Область обнаружения { #discovery-scope }

Kora не сканирует вслепую каждый класс в пути классов. Компоненты обнаруживаются в Gradle-модулях, которые содержат интерфейсы `@KoraApp` или `@KoraSubmodule`. Компоненты из внешних библиотек также не
становятся автоматически доступными только потому, что существуют в JAR. Обычно библиотека предоставляет интерфейс модуля, а ваше приложение импортирует этот модуль, наследуясь от него в `@KoraApp`.

Эта явность важна: она сохраняет граф предсказуемым, делает границы модулей видимыми и предотвращает случайную регистрацию компонентов.

Практический путь обучения:

1. понять, почему ручное создание объектов становится болезненным
2. узнать, что такое зависимость
3. ввести внедрение через конструктор
4. связать внедрение зависимостей с графами объектов и инверсией управления
5. сравнить внедрение зависимостей во время выполнения с графом Kora, который строится во время компиляции
6. узнать, как Kora обнаруживает компоненты и модули
7. увидеть, почему сгенерированный код графа улучшает обратную связь по связыванию

---

## Основы DI { #di-basics }

Это руководство дает подробное введение во внедрение зависимостей и принципы инверсии управления с использованием фреймворка Kora. Независимо от того, впервые ли вы знакомитесь с этими понятиями или
хотите углубить понимание, этот раздел последовательно выстроит ваши знания от фундаментальных принципов до практической реализации.

### Что такое внедрение зависимостей? { #dependency-injection }

**Внедрение зависимостей** — это фундаментальный шаблон проектирования, который решает вопрос того, как программные компоненты получают свои зависимости и управляют ими. В своей основе внедрение
зависимостей отделяет создание зависимостей от их использования, что позволяет строить более гибкую и поддерживаемую архитектуру кода.

**Основная идея**: вместо того чтобы компонент создавал собственные зависимости, эти зависимости предоставляются (внедряются) из внешнего источника. Этим внешним источником обычно является фреймворк
внедрения зависимостей или контейнер.

**Базовый пример**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Традиционный подход — компонент создает собственные зависимости
    public class OrderProcessor {
        private Database database = new Database();        // Компонент создает зависимость
        private EmailService emailService = new EmailService();

        public void processOrder(Order order) {
            database.save(order);
            emailService.sendConfirmation(order.getCustomerEmail());
        }
    }

    // Подход с внедрением зависимостей — зависимости предоставляются извне
    public class OrderProcessor {
        private final Database database;
        private final EmailService emailService;

        // Зависимости внедряются через конструктор
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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Традиционный подход — компонент создает собственные зависимости
    class OrderProcessor {
        private val database = Database()        // Компонент создает зависимость
        private val emailService = EmailService()

        fun processOrder(order: Order) {
            database.save(order)
            emailService.sendConfirmation(order.customerEmail)
        }
    }

    // Подход с внедрением зависимостей — зависимости предоставляются извне
    class OrderProcessor(
        private val database: Database,
        private val emailService: EmailService
    ) {
        // Зависимости внедряются через основной конструктор

        fun processOrder(order: Order) {
            database.save(order)
            emailService.sendConfirmation(order.customerEmail)
        }
    }
    ```

Ключевая терминология:

- Зависимость: любой объект или сервис, который нужен компоненту для работы
- Внедрение: процесс предоставления зависимостей компоненту
- Контейнер: механизм, отвечающий за создание и внедрение зависимостей

### Проблемы традиционных подходов { #traditional-approach-problems }

Чтобы понять необходимость внедрения зависимостей, рассмотрим сложности, которые возникают без него, и то, как внедрение зависимостей дает решения.

**Проблема: жесткая связанность**

Жесткая связанность возникает, когда компоненты напрямую зависят от конкретных реализаций, делая систему негибкой и трудной для сопровождения. Рассмотрим распространенный шаблон:

===! ":fontawesome-brands-java: Java"

    ```java
    public class UserService {
        private DatabaseConnection connection = new DatabaseConnection();  // Прямое создание экземпляра

        public User findUserById(long id) {
            return connection.query("SELECT * FROM users WHERE id = ?", id);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    class UserService {
        private val connection = DatabaseConnection()  // Прямое создание экземпляра

        fun findUserById(id: Long): User {
            return connection.query("SELECT * FROM users WHERE id = ?", id)
        }
    }
    ```

Проблемы жесткой связанности:

1. Сложности тестирования: `UserService` нельзя тестировать изолированно, потому что он напрямую создает `DatabaseConnection`
2. Привязка к реализации: переход на другую базу данных требует изменения кода `UserService`
3. Скрытые зависимости: конструктор ничего не говорит о том, что на самом деле нужно сервису
4. Проблемы управления ресурсами: каждый экземпляр создает собственное соединение с базой данных
5. Проблемы конфигурации: нет способа настроить соединение с базой данных извне

### Преимущества внедрения зависимостей { #dependency-injection-benefits }

**Решение через внедрение зависимостей**:

===! ":fontawesome-brands-java: Java"

    ```java
    public class UserService {
        private final DatabaseConnection connection;

        // Зависимости объявлены явно
        public UserService(DatabaseConnection connection) {
            this.connection = connection;
        }

        public User findUserById(long id) {
            return connection.query("SELECT * FROM users WHERE id = ?", id);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    class UserService(
        private val connection: DatabaseConnection
    ) {
        // Зависимости явно объявлены в основном конструкторе

        fun findUserById(id: Long): User {
            return connection.query("SELECT * FROM users WHERE id = ?", id)
        }
    }
    ```

**Ключевые преимущества внедрения зависимостей**:

1. **Тестируемость**: компоненты можно тестировать с имитациями зависимостей

===! ":fontawesome-brands-java: Java"

       ```java
       @Test
       public void testUserService() {
           DatabaseConnection mockConnection = mock(DatabaseConnection.class);
           UserService service = new UserService(mockConnection);
           // Тестируем логику сервиса без зависимостей от базы данных
       }
       ```

=== ":simple-kotlin: Kotlin"

       ```kotlin
       @Test
       fun testUserService() {
           val mockConnection = mock(DatabaseConnection::class.java)
           val service = UserService(mockConnection)
           // Тестируем логику сервиса без зависимостей от базы данных
       }
       ```

2. **Гибкость**: разные реализации можно внедрять в зависимости от окружения

===! ":fontawesome-brands-java: Java"

       ```java
       // Рабочее окружение
       DatabaseConnection prodConnection = new PostgreSQLConnection();
       UserService prodService = new UserService(prodConnection);

       // Тестовое окружение
       DatabaseConnection testConnection = new InMemoryDatabaseConnection();
       UserService testService = new UserService(testConnection);
       ```

=== ":simple-kotlin: Kotlin"

       ```kotlin
       // Рабочее окружение
       val prodConnection = PostgreSQLConnection()
       val prodService = UserService(prodConnection)

       // Тестовое окружение
       val testConnection = InMemoryDatabaseConnection()
       val testService = UserService(testConnection)
       ```

3. **Явные зависимости**: параметры конструктора ясно документируют требования
4. **Управление ресурсами**: жизненным циклом соединения можно управлять извне
5. **Конфигурация**: настройки базы данных можно задавать на уровне приложения

### Понимание инверсии управления { #understanding-inversion-control }

**Инверсия управления** — это архитектурный принцип, лежащий в основе внедрения зависимостей. Инверсия управления представляет фундаментальный сдвиг в том, как в программных системах управляется поток
управления.

**Традиционный поток управления**:

```
Код приложения -> создает объекты -> управляет зависимостями -> выполняет бизнес-логику
```

**Инвертированный поток управления**:

```
Фреймворк/контейнер -> создает объекты -> внедряет зависимости -> код приложения выполняет бизнес-логику
```

**Принцип инверсии**:

В традиционном программировании код вашего приложения отвечает за:

- создание всех необходимых объектов
- управление жизненными циклами объектов
- координацию между компонентами
- обработку конфигурации

При инверсии управления эти обязанности инвертируются:

- фреймворк создает объекты
- фреймворк управляет жизненными циклами
- фреймворк координирует компоненты
- фреймворк обрабатывает конфигурацию

**Шаблоны реализации инверсии управления**:

1. **Фабрика**: централизованное создание объектов
2. **Поиск сервисов**: компоненты запрашивают зависимости из центрального реестра
3. **Внедрение зависимостей**: зависимости передаются внутрь компонентов

**Почему инверсия управления важна**:

Инверсия управления дает несколько важных архитектурных преимуществ:

- **Разделение ответственности**: бизнес-логика отделяется от инфраструктурных задач
- **Модульность**: компоненты можно разрабатывать и тестировать независимо
- **Сопровождаемость**: изменения инфраструктуры не затрагивают бизнес-логику
- **Тестируемость**: компоненты легко изолировать для тестирования
- **Инверсия управления**: ресторан предоставляет готовую еду, вы просто едите

**В коде**:

===! ":fontawesome-brands-java: Java"

    ```java
    // Традиционный подход — вы управляете всем созданием объектов
    public class Application {
        public static void main(String[] args) {
            Database db = new Database();           // Вы создаете
            EmailService email = new EmailService(); // Вы создаете
            OrderService service = new OrderService(db, email); // Вы создаете

            service.processOrder(order); // Вы управляете
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Традиционный подход — вы управляете всем созданием объектов
    class Application {
        companion object {
            @JvmStatic
            fun main() {
                val db = Database()           // Вы создаете
                val email = EmailService() // Вы создаете
                val service = OrderService(db, email) // Вы создаете

                service.processOrder(order) // Вы управляете
            }
        }
    }
    ```

### Когда старые подходы ломаются { #old-approaches-break }

Хотя традиционный подход с ручным созданием зависимостей и управлением ими прекрасно работает для маленьких приложений из нескольких классов, он становится все более проблемным по мере роста
приложения до десятков или сотен компонентов.

**Почему масштаб важен:**

Традиционный подход требует вручную создавать каждый объект приложения и связывать их между собой. Для маленького приложения из 3-5 классов это просто. Но когда приложение содержит 20, 50 или 100+
классов, такой ручной подход превращается в кошмар сопровождения.

**Пример: приложение из 20+ классов (традиционный подход)**

Представьте, что вы строите приложение со следующими компонентами:

===! ":fontawesome-brands-java: Java"

    ```java
    public class EcommerceApplication {
        public static void main(String[] args) {
            // Infrastructure Layer (8 classes)
            DatabaseConfig dbConfig = new DatabaseConfig("localhost", "ecommerce", "user", "pass");
            DatabaseConnection dbConnection = new DatabaseConnection(dbConfig);
            RedisConfig redisConfig = new RedisConfig("localhost", 6379);
            RedisConnection redisConnection = new RedisConnection(redisConfig);
            EmailConfig emailConfig = new EmailConfig("smtp.gmail.com", 587, "user@gmail.com");
            EmailService emailService = new EmailService(emailConfig);
            PaymentGatewayConfig paymentConfig = new PaymentGatewayConfig("stripe_key_123");
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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    class EcommerceApplication {
        companion object {
            @JvmStatic
            fun main() {
                // Infrastructure Layer (8 classes)
                val dbConfig = DatabaseConfig("localhost", "ecommerce", "user", "pass")
                val dbConnection = DatabaseConnection(dbConfig)
                val redisConfig = RedisConfig("localhost", 6379)
                val redisConnection = RedisConnection(redisConfig)
                val emailConfig = EmailConfig("smtp.gmail.com", 587, "user@gmail.com")
                val emailService = EmailService(emailConfig)
                val paymentConfig = PaymentGatewayConfig("stripe_key_123")
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
                val productService = UserService(productRepository, inventoryRepository)
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
        }
    }
    ```

**При 100+ классах это становится невозможным:**

- ваш метод `main` стал бы длиной в 1000+ строк
- для понимания графа зависимостей потребовалась бы отдельная схема
- вам пришлось бы вручную следить, чтобы компоненты создавались в правильном порядке
- добавление новой функции требовало бы изменения десятков файлов
- изменение одного компонента требовало бы понимания всей цепочки его зависимостей
- тестирование любого компонента требовало бы создания сотен объектов и стало бы кошмаром
- одно изменение конфигурации каскадом проходило бы через все приложение
- добавление новой функции требовало бы обновления метода `main`, потенциально ломая существующий порядок инициализации

**Решение через внедрение зависимостей:**

При внедрении зависимостей вы объявляете зависимости на уровне компонента, а фреймворк берет на себя всю сложность:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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
- управляет жизненными циклами ресурсов
- обрабатывает внедрение конфигурации
- предоставляет разрешение зависимостей
- упрощает тестирование с имитациями

Именно поэтому внедрение зависимостей становится необходимым, когда приложения вырастают за пределы нескольких классов.

===! ":fontawesome-brands-java: Java"

    ```java
    // IoC/DI (framework controls object creation)
    @KoraApp
    public interface Application {
        // Framework creates and injects everything
        OrderService orderService();

        static void main(String[] args) {
            // Framework handles all object creation and injection
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // IoC/DI (framework controls object creation)
    @KoraApp
    interface Application {
        // Framework creates and injects everything
        fun orderService(): OrderService
    }

    fun main() {
        // Framework handles all object creation and injection
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Сравнение преимуществ:

| Аспект                | Традиционный подход                        | Внедрение зависимостей                          |
|-----------------------|--------------------------------------------|-------------------------------------------------|
| Тестирование      | Сложно (использует реальные сервисы)       | Просто (внедряются имитации)                    |
| Гибкость          | Низкая (зависимости зашиты в код)          | Высокая (можно внедрить любую реализацию)       |
| Переиспользование | Низкое (привязка к конкретным реализациям) | Высокое (работает с любым совместимым сервисом) |
| Сопровождаемость  | Низкая (изменения затрагивают много мест)  | Высокая (меняется внедрение, а не код)          |
| Ясность           | Низкая (зависимости скрыты)                | Высокая (конструктор показывает потребности)    |

Теперь, когда вы понимаете основы, посмотрим, как Kora реализует эти понятия через внедрение зависимостей во время компиляции!

---

## Архитектура Kora { #kora-architecture }

Kora использует внедрение зависимостей во время компиляции, что означает:

1. Анализ во время сборки: зависимости анализируются во время компиляции с помощью обработчиков аннотаций
2. Обнаружение компонентов: находятся классы, помеченные `@Component`, и фабричные методы
3. Разрешение зависимостей: обработчик аннотаций разрешает все зависимости и строит граф зависимостей
4. Генерация кода: класс `ApplicationGraphDraw` генерируется как исходный код Java/Kotlin
5. Производительность во время выполнения: нет затрат на рефлексию или анализ во время выполнения — все разрешено во время компиляции

> Важное ограничение области: обработчики аннотаций Kora сканируют только Gradle-модули, которые содержат интерфейсы `@KoraApp` или `@KoraSubmodule`. Компоненты в обычных Gradle-модулях без этих
> интерфейсов не будут обнаружены или обработаны системой внедрения зависимостей.

### Как работает в Kora { #it-works-kora }

1. Обработка аннотаций: интерфейсы `@KoraApp` обрабатываются во время компиляции через `KoraAppProcessor`
2. Обнаружение компонентов: сканируются классы `@Component`, интерфейсы `@Module` и фабричные методы внутри Gradle-модулей, содержащих интерфейсы `@KoraApp` или `@KoraSubmodule`
3. Разрешение зависимостей: используется `GraphBuilder`, чтобы разрешить зависимости и обнаружить циклы
4. Генерация графа: генерируется класс `ApplicationGraph` с фабриками компонентов и логикой инициализации
5. Выполнение во время запуска: `KoraApplication.run()` инициализирует компоненты в правильном порядке

> Критичное ограничение области: обработчики аннотаций Kora обрабатывают только Gradle-модули, которые содержат интерфейсы `@KoraApp` или `@KoraSubmodule`. Компоненты в обычных Gradle-модулях без
> этих интерфейсов будут полностью проигнорированы системой внедрения зависимостей.

Архитектурные преимущества явного управления:
Такой осознанный архитектурный выбор дает вам полный контроль над графом зависимостей приложения. В отличие от фреймворков, которые автоматически создают все из пути классов, Kora гарантирует, что вы
явно объявляете нужные компоненты. Это предотвращает:

- пустую трату ресурсов из-за создания ненужных компонентов
- риски безопасности из-за активации компонентов транзитивных зависимостей
- сложность отладки из-за неизвестных работающих компонентов
- накладные расходы производительности из-за сканирования пути классов
- непредсказуемое поведение при изменении зависимостей

В Kora интерфейс `@KoraApp` служит явным манифестом всего, что работает в вашем приложении.

### Сгенерированный код { #generated-code }

Когда вы помечаете интерфейс аннотацией `@KoraApp`, Kora генерирует:

===! ":fontawesome-brands-java: Java"

    ```java
    // Generated at compile time
    public final class ApplicationGraph implements Application {
        public static ApplicationGraphDraw graph() {
            // Component initialization logic
            // Dependency resolution
            // Lifecycle management
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Generated at compile time
    class ApplicationGraph : Application {
        companion object {
            fun graph(): ApplicationGraphDraw {
                // Component initialization logic
                // Dependency resolution
                // Lifecycle management
            }
        }
    }
    ```

### Compile Time и Runtime { #compile-time-runtime }

**Время компиляции (обработка аннотаций):**

- анализирует исходный код на наличие компонентов и зависимостей только внутри модулей `@KoraApp`/`@KoraSubmodule`
- проверяет граф зависимостей (нет циклов, все зависимости доступны)
- генерирует оптимизированный код инициализации
- обеспечивает проверку ошибок во время компиляции

**Время выполнения (выполнение приложения):**

- выполняет сгенерированный код инициализации
- управляет жизненным циклом компонентов
- обрабатывает корректное завершение работы
- поддерживает обновления компонентов через `ValueOf<T>`

> **Критично про область обработки**: обработка во время компиляции происходит только в Gradle-модулях, содержащих интерфейсы `@KoraApp` или `@KoraSubmodule`. Код в обычных модулях не анализируется и
> не обрабатывается во время компиляции.

### Обработчики аннотаций { #annotation-processors }

Обработка аннотаций в Kora состоит из:

1. `KoraAppProcessor`: основной обработчик `@KoraApp`, `@Module`, `@Component`
2. `GraphBuilder`: строит граф разрешения зависимостей и обнаруживает циклы
3. `ComponentDependencyHelper`: разбирает заявки зависимостей из параметров методов и конструкторов
4. Расширения: подключаемая система для динамической генерации компонентов
5. `ProcessingContext`: предоставляет доступ к окружению компиляции и служебным возможностям

> Ограничение области: обработчики аннотаций Kora активируются и обрабатывают код только внутри Gradle-модулей, которые содержат интерфейсы `@KoraApp` или `@KoraSubmodule`. Код в обычных
> Gradle-модулях полностью невидим для этих обработчиков.

### Порядок обнаружения компонентов { #component-discovery-order }

Компоненты обнаруживаются в следующем порядке приоритета (большие числа переопределяют меньшие):

1. Автоматическое создание: классы, соответствующие требованиям (`final`, один конструктор, не `abstract`)
2. Механизм расширений: динамическая генерация компонентов (JSON-преобразователи, репозитории и т.д.)
3. Обобщенная фабрика: методы с обобщенными параметрами
4. Стандартная фабрика: методы с `@DefaultComponent`
5. Базовая фабрика: обычные фабричные методы
6. Фабрика модуля: методы в интерфейсах `@Module`
7. Фабрика внешнего модуля: унаследована из внешних зависимостей
8. Фабрика подмодуля: сгенерирована из `@KoraSubmodule`
9. Автоматическая фабрика: классы с аннотацией `@Component`

> Примечание об области: обнаружение компонентов происходит только внутри Gradle-модулей, содержащих интерфейсы `@KoraApp` или `@KoraSubmodule`. Компоненты в обычных Gradle-модулях не будут
> обнаружены независимо от их аннотаций.

### Алгоритм разрешения зависимостей { #dependency-resolution-algorithm }

1. Разбор заявки: каждый параметр зависимости разбирается в `DependencyClaim`
2. Сопоставление компонентов: находятся компоненты, соответствующие типу и тегам
3. Обнаружение циклов: проверяется, что циклических зависимостей нет
4. Построение графа: строится ациклический граф зависимостей
5. Генерация кода: код инициализации генерируется в топологическом порядке

---

## Основные аннотации { #core-annotations }

Kora предоставляет несколько ключевых аннотаций для внедрения зависимостей:

### `@KoraApp` { #koraapp }

Помечает главный интерфейс приложения и служит ядром контейнера зависимостей Kora. Эта аннотация помечает интерфейс, внутри которого определяются фабричные методы для создания компонентов и
зависимости модулей. В приложении может быть только один такой интерфейс.

Что делает `@KoraApp`:

- Точка входа в контейнер: определяет корень контейнера зависимостей вашего приложения
- Реестр компонентов: регистрирует все фабричные методы и методы доступа к компонентам
- Интеграция модулей: подключает внешние модули через наследование интерфейсов
- Запуск приложения: предоставляет начальную точку для `KoraApplication.run()`

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application {
        // Factory methods and component accessors
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application {
        // Factory methods and component accessors
    }
    ```

**Требования:**

- должен быть интерфейсом (не классом)
- только один на приложение
- может наследовать несколько интерфейсов модулей
- должен находиться в Gradle-модуле (не в обычном модуле без `@KoraSubmodule`)

**Процесс построения контейнера:**
Во время компиляции Kora использует интерфейс `@KoraApp`, чтобы:

1. обнаружить все фабричные методы и зависимости компонентов
2. проверить граф зависимостей на циклы и отсутствующие компоненты
3. сгенерировать оптимизированный код инициализации
4. создать класс `ApplicationGraph` для выполнения во время запуска

**Почему интерфейсы? Множественное наследование и управление переопределением фабрик**

Kora требует, чтобы `@KoraApp` и все модули были интерфейсами, а не классами, по фундаментальным архитектурным причинам, которые дают мощные возможности внедрения зависимостей.

**Почему интерфейсы? Множественное наследование и управление переопределением фабрик**

Kora требует, чтобы `@KoraApp` и все модули были интерфейсами, а не классами, по фундаментальным архитектурным причинам, которые дают мощные возможности внедрения зависимостей.

**Множественное наследование**: интерфейсы Java поддерживают множественное наследование, позволяя приложению составлять функциональность из нескольких модулей:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface EcommerceApplication extends
        HttpModule,           // HTTP server capabilities
        DatabaseModule,       // Database connectivity
        CacheModule,          // Caching services
        MonitoringModule {    // Observability features

        // Your application-specific factories
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface EcommerceApplication :
        HttpModule,           // HTTP server capabilities
        DatabaseModule,       // Database connectivity
        CacheModule,          // Caching services
        MonitoringModule {    // Observability features

        // Your application-specific factories
    }
    ```

**Переопределение фабричного метода**: методы интерфейса по умолчанию можно легко переопределять, что дает полный контроль над внедрением зависимостей на уровне языка:

===! ":fontawesome-brands-java: Java"

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
    public interface Application extends CacheModule {  // <----- Подключили модуль
        @Override
        default Cache cache() {
            return new RedisCache(); // Override with Redis
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Library provides default implementation
    @Module
    interface CacheModule {
        @DefaultComponent
        fun cache(): Cache = InMemoryCache() // Default implementation
    }

    // Your application can override with custom implementation
    @KoraApp
    interface Application : CacheModule {  // <----- Подключили модуль
        override fun cache(): Cache = RedisCache() // Override with Redis
    }
    ```

**Компонент как фабричный метод**: компоненты не ограничены классами — их также можно определять как фабричные методы в интерфейсах, получая декларативный контроль над инверсией управления:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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

Почему эта архитектура важна:

1. Понятное управление на уровне языка: поведение инверсии управления задается знакомыми конструкциями Java (интерфейсами, методами по умолчанию), а не сложными XML-файлами или аннотациями
2. Типобезопасная конфигурация: фабричные методы проверяются во время компиляции, предотвращая ошибки конфигурации во время выполнения
3. Простое тестирование: фабричные методы можно переопределять в тестах, чтобы внедрять имитации без сложных тестовых фреймворков
4. Модульная композиция: множественное наследование позволяет аккуратно разделять ответственность между разными модулями
5. Гибкость переопределения: реализации меняются простым переопределением методов, без конфигурации, специфичной для фреймворка

Такой подход на основе интерфейсов делает внедрение зависимостей естественным расширением языка Java: вы получаете мощные возможности инверсии управления, сохраняя простоту и типобезопасность.

#### Почему явное управление важно { #explicit-control-matters }

Философия Kora отдает приоритет явному управлению вместо неявной магии. В отличие от традиционных фреймворков внедрения зависимостей, которые автоматически сканируют путь классов и создают все,
что находят, Kora требует явно объявлять, какие зависимости нужны приложению.

Проблема автоматического обнаружения:

- Непредсказуемое поведение: вы никогда точно не знаете, что будет создано просто из-за добавления JAR в путь классов
- Скрытые зависимости: компоненты могут создаваться без вашего ведома и потреблять ресурсы
- Кошмары отладки: когда что-то идет не так, приходится выяснять, какие нежелательные компоненты запущены
- Риски безопасности: вредоносные или уязвимые компоненты могут быть созданы автоматически
- Проблемы производительности: сканируется каждый JAR в пути классов, даже если он не нужен

**Явный подход Kora:**

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
        ru.tinkoff.kora.http.HttpModule,    // ✅ Explicitly included
        ru.tinkoff.kora.database.DatabaseModule, // ✅ Explicitly included
        // ru.tinkoff.kora.cache.CacheModule,     // ❌ Commented out = not included
        com.example.MyCustomModule {         // ✅ Your custom module
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application :
        ru.tinkoff.kora.http.HttpModule,    // ✅ Explicitly included
        ru.tinkoff.kora.database.DatabaseModule, // ✅ Explicitly included
        // ru.tinkoff.kora.cache.CacheModule,     // ❌ Commented out = not included
        com.example.MyCustomModule        // ✅ Your custom module
    ```

Преимущества явного управления:

- Предсказуемые зависимости: вы точно знаете, что работает в приложении
- Эффективность ресурсов: создается только то, что действительно нужно
- Понятный граф зависимостей: связи компонентов легко понимать и отлаживать
- Безопасность по проекту: нет неожиданных созданий из транзитивных зависимостей
- Производительность: нет накладных расходов на сканирование пути классов — все разрешается во время компиляции
- Сопровождаемость: изменения зависимостей явны и отслеживаются в коде

Влияние в реальном мире:
В автоматических фреймворках разработчики часто тратят часы на отладку того, почему приложение медленное или потребляет неожиданные ресурсы. В Kora, если компонент не включен явно в
интерфейс `@KoraApp`, он просто не существует в приложении — никаких сюрпризов и скрытых затрат.

### `@Component` { #component }

Помечает класс как компонент (зависимость) в контейнере зависимостей. Все компоненты в Kora являются `Singleton`: на протяжении жизненного цикла приложения создается только один экземпляр класса.
Компоненты внедряются только если они являются корневыми компонентами (помечены `@Root`) или нужны как зависимости другим компонентам.

Что такое компоненты:

- `Singleton`-экземпляры: один экземпляр на жизненный цикл приложения
- Поставщики зависимостей: могут внедряться в другие компоненты
- Условная инициализация: создаются только если нужны другим компонентам или помечены `@Root`
- Потокобезопасность: один и тот же экземпляр используется во всех точках внедрения

**Важное ограничение области**: классы `@Component` могут быть обнаружены и использованы только внутри Gradle-модулей, которые содержат одно из двух:

- интерфейс `@KoraApp` (главный модуль приложения)
- интерфейс `@KoraSubmodule` (модуль обнаружения компонентов)

Компоненты в обычных Gradle-модулях без этих аннотаций не будут обработаны обработчиком аннотаций Kora.

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class UserService {
        // Implementation
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class UserService {
        // Implementation
    }
    ```

Требования для автоматической фабрики:

- класс не должен быть абстрактным
- должен иметь ровно один публичный конструктор
- должен быть `final` (если в нем нет аспектов AOP)
- параметры конструктора становятся зависимостями
- должен находиться в Gradle-модуле с `@KoraApp` или `@KoraSubmodule`

Жизненный цикл компонента:

- Обнаружение: находится обработчиком аннотаций во время компиляции
- Проверка: зависимости проверяются во время компиляции
- Создание: экземпляр создается при запуске приложения, если нужен (или помечен `@Root`)
- Внедрение: один и тот же экземпляр предоставляется всем зависимым компонентам
- Уничтожение: управляется контейнером при завершении работы

### `@Module` { #module }

Группирует связанные фабрики компонентов и помечает интерфейсы как модули, которые внедряются в контейнер зависимостей во время компиляции. Модуль — это интерфейс, содержащий фабричные методы для
создания компонентов. Все фабричные методы внутри модуля становятся доступными контейнеру зависимостей.

Что делают модули:

- Набор фабрик: группируют связанные фабрики компонентов в одном месте
- Организация кода: разделяют ответственность между разными модулями
- Переиспользование: модули можно разделять между приложениями
- Поддержка переопределения: фабричные методы можно переопределять в наследующих интерфейсах

**Область**: интерфейсы `@Module` обрабатываются внутри Gradle-модулей, которые содержат интерфейсы `@KoraApp` или `@KoraSubmodule`. Внешние модули из библиотек наследуются через расширение
интерфейса.

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface DatabaseModule {
        @Component
        default UserRepository userRepository(DataSource dataSource) {
            return new JdbcUserRepository(dataSource);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface DatabaseModule {
        @Component
        fun userRepository(dataSource: DataSource): UserRepository =
            JdbcUserRepository(dataSource)
    }
    ```

Типы модулей:

- Внутренние модули: определяются в вашем проекте внутри модулей `@KoraApp`
- Внешние модули: предоставляются библиотеками (наследуются через расширение интерфейса)
- Подмодули: генерируются из интерфейсов `@KoraSubmodule`

Требования к модулю:

- должен быть интерфейсом (не классом)
- фабричные методы должны быть методами по умолчанию
- должен находиться в той же директории исходников, что и `@KoraApp` или `@KoraSubmodule`

Правила фабричных методов:

- должен возвращать компонент (ненулевое значение)
- может принимать другие компоненты как параметры
- параметры становятся зависимостями
- параметры могут быть необязательными компонентами (помечаются `@Nullable`)
- методы вызываются во время выполнения в порядке зависимостей

> Компоненты внешних библиотек: компоненты и модули из внешних библиотек не обнаруживаются автоматически обработчиком аннотаций Kora. Даже если библиотека содержит классы `@Component` или
> интерфейсы `@Module`, они будут невидимы для приложения, пока вы явно не унаследуете их интерфейсы модулей в интерфейсе `@KoraApp`. Это осознанное архитектурное решение для явного управления
> зависимостями.

### `@KoraSubmodule` { #korasubmodule }

Помечает интерфейс, для которого нужно построить модуль для текущего модуля компиляции. Он будет содержать все компоненты, помеченные аннотациями `@Module` и `@Component`, найденные в исходном коде.
Эта аннотация особенно полезна для многомодульных Gradle-приложений, где разные модули содержат разные части функциональности, а главное приложение `@KoraApp` собирается в отдельном модуле.

Что делает `@KoraSubmodule`:

- Обнаружение компонентов: сканирует текущий Gradle-модуль на аннотации `@Module` и `@Component`
- Генерация модуля: создает интерфейс-наследник со всеми обнаруженными модулями и компонентами
- Поддержка многомодульности: позволяет разделять компоненты между Gradle-модулями
- Определение границы: задает, где обработчик аннотаций Kora сканирует компоненты
- Оптимизация сборки: позволяет использовать кеширование сборки Gradle и инкрементальную компиляцию, изолируя функциональность в отдельных модулях

**Область**: интерфейсы `@KoraSubmodule` определяют границы, в которых обработчик аннотаций Kora будет сканировать компоненты. Компоненты за пределами этих границ не обрабатываются.

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraSubmodule
    public interface ApplicationModules {
        // Generated factory methods for all discovered components
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraSubmodule
    interface ApplicationModules {
        // Generated factory methods for all discovered components
    }
    ```

Как это работает:

1. Обнаружение: находит все интерфейсы `@Module` и классы `@Component` в текущем Gradle-модуле
2. Наследование: сгенерированный интерфейс наследуется от всех обнаруженных интерфейсов `@Module`
3. Генерация фабрик: создает методы по умолчанию для всех обнаруженных классов `@Component`
4. Интеграция: может наследоваться `@KoraApp`, чтобы включать компоненты из других модулей

Сценарии использования:

- Многомодульные проекты: разделение компонентов между Gradle-модулями
- Разработка библиотек: публикация компонентов из библиотечного модуля
- Модульная архитектура: разделение ответственности между разными модулями сборки
- Организация компонентов: группировка связанных компонентов по функциональности
- Большие единые приложения: организация сложных монолитных приложений в изолированные Gradle-модули для лучшей производительности сборки и сопровождения
- Оптимизация сборки: использование контекста кеширования сборки Gradle через разделение функциональности на независимые модули, которые можно собирать и кешировать отдельно

### `@Root` { #root }

Помечает компоненты, которые всегда должны инициализироваться при запуске приложения, даже если они не являются зависимостями других компонентов. Корневые компоненты гарантированно создаются и
запускаются при старте приложения независимо от того, внедряет ли их кто-либо.

Что делает `@Root`:

- Гарантированная инициализация: компонент всегда создается при запуске
- Жадная загрузка: принудительно создает экземпляр сразу (не лениво)
- Управление жизненным циклом: компонент участвует в запуске и остановке приложения
- Точки входа: отлично подходит для серверов, потребителей, планировщиков и фоновых сервисов

Частые сценарии:

- HTTP-серверы: веб-серверы, которые должны сразу начать слушать порт
- Потребители сообщений: Kafka-потребители, обработчики очередей
- Фоновые сервисы: прогреватели кеша, проверки состояния, планировщики

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application {
        @Root
        default HttpServer httpServer(UserController controller) {
            return new HttpServer(controller);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application {
        @Root
        fun httpServer(controller: UserController): HttpServer =
            HttpServer(controller)
    }
    ```

`@Root` и обычные компоненты:

- Обычные компоненты: создаются только если нужны как зависимости другим компонентам
- Компоненты `@Root`: всегда создаются при запуске (гарантированная инициализация)

Когда использовать `@Root`:

- компонент предоставляет сервис, который всегда должен работать
- компонент должен сразу начать обработку (серверы, потребители)
- компонент выполняет критичную инициализацию (настройка базы данных, прогрев кеша)
- компонент собирает метрики или данные мониторинга

### `@DefaultComponent` { #defaultcomponent }

Помечает фабричные методы, которые предоставляют реализации по умолчанию и предназначены для переопределения пользователями. Если в контейнере зависимостей найден любой компонент без этой аннотации,
он будет иметь приоритет при внедрении над фабриками `@DefaultComponent`.

Что делает `@DefaultComponent`:

- Предоставление по умолчанию: дает резервные реализации компонентов
- Поддержка переопределения: позволяет пользователям заменять значения по умолчанию без изменения кода библиотеки
- Удобство для библиотек: позволяет библиотекам предоставлять разумные значения по умолчанию
- Система приоритетов: имеет более низкий приоритет, чем фабрики без аннотации

Сценарии использования:

- Значения библиотек по умолчанию: библиотеки дают реализации по умолчанию, которые пользователи могут переопределить
- Варианты конфигурации: разные реализации в зависимости от окружения
- Точки расширения: позволяют пользователям настраивать поведение без изменения кода библиотеки

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface CacheModule {
        @DefaultComponent
        default Cache defaultCache() {
            return new InMemoryCache();
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface CacheModule {
        @DefaultComponent
        fun defaultCache(): Cache = InMemoryCache()
    }
    ```

Поведение переопределения:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends CacheModule {  // <----- Подключили модуль
        // This overrides the @DefaultComponent because it has no annotation
        @Override
        default Cache defaultCache() {
            return new RedisCache(); // User provides custom implementation
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application : CacheModule {  // <----- Подключили модуль
        // This overrides the @DefaultComponent because it has no annotation
        override fun defaultCache(): Cache = RedisCache() // User provides custom implementation
    }
    ```

Порядок приоритета:

1. фабрики без аннотаций (наивысший приоритет — переопределяют значения по умолчанию)
2. фабрики `@DefaultComponent` (самый низкий приоритет — могут быть переопределены)
3. другие типы фабрик между ними

Лучшие практики:

- используйте для предоставляемых библиотекой значений по умолчанию, которые пользователи могут захотеть настроить
- не используйте для компонентов, специфичных для приложения
- явно документируйте, какие значения по умолчанию доступны для переопределения

### `@Tag` { #tag }

Позволяет различать несколько реализаций одного и того же типа и выполнять выборочное внедрение на основе тегов. Теги используют ссылки на классы вместо строк, что улучшает поддержку рефакторинга и
типобезопасность. Компонент регистрируется с определенным тегом и внедряется в точки, которые запрашивают точно такой же тег.

Что делают теги:

- Выбор реализации: выбирают конкретные реализации интерфейсов
- Несколько экземпляров: поддерживают несколько реализаций одного типа
- Типобезопасность: используют ссылки на классы вместо строк
- Безопасность при рефакторинге: среда разработки может отслеживать использование тегов по всей кодовой базе

Базовое использование:

===! ":fontawesome-brands-java: Java"

    ```java
    // Tag classes (usually empty marker classes)
    public final class RedisTag {}
    public final class InMemoryTag {}

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Tag classes (usually empty marker classes)
    class RedisTag
    class InMemoryTag

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

Применение тегов:

- На классах: `@Tag(MyTag.class) @Component class MyClass`
- На фабричных методах: `@Tag(MyTag.class) default MyClass myClass()`
- На параметрах: `public MyClass(@Tag(MyTag.class) Dependency dep)`

Специальные теги:

- `@Tag.Any`: сопоставляет все компоненты независимо от их тегов
- для удобства можно создавать собственные аннотации тегов

Правила сопоставления тегов:

1. Точное совпадение: теги должны точно совпадать по ссылке на класс
2. Наследование: классы тегов могут быть частью иерархий наследования
3. Несколько тегов: компоненты могут иметь несколько тегов
4. Фильтрация по тегам: зависимости могут указывать требуемые теги

Теги аннотации:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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

---

## Приоритет обнаружения компонентов { #component-discovery-priority }

Когда Kora нужно создать компонент, она следует определенному порядку приоритетов, чтобы решить, какой фабричный метод или механизм использовать. Фабрики с более высоким приоритетом переопределяют
фабрики с более низким приоритетом. Понимание этого порядка критично для отладки проблем разрешения зависимостей и для уверенности, что используются правильные реализации.

Порядок приоритета (от высшего к низшему):

1. Автоматическое создание: классы, соответствующие требованиям к компонентам (`final`, один конструктор, не `abstract`)
2. Механизм расширений: динамическая генерация компонентов (JSON-преобразователи, репозитории и т.д.)
3. Обобщенная фабрика: методы с обобщенными параметрами типа
4. Стандартная фабрика: методы с `@DefaultComponent`
5. Базовая фабрика: обычные фабричные методы
6. Фабрика модуля: методы в интерфейсах `@Module`
7. Фабрика внешнего модуля: унаследована из внешних зависимостей
8. Фабрика подмодуля: сгенерирована из `@KoraSubmodule`
9. Автоматическая фабрика: классы с аннотацией `@Component`

Что это означает:

- если у вас есть и класс `@Component`, и фабричный метод для того же типа, фабричный метод имеет приоритет
- фабрики `@DefaultComponent` могут быть переопределены обычными фабричными методами
- расширения могут предоставлять компоненты динамически (например, JSON-читатели/писатели)
- автоматическое создание работает как запасной вариант для простых классов

Практический пример:

===! ":fontawesome-brands-java: Java"

    ```java
    // Priority 9: Auto Factory (@Component) - lowest priority
    @Component
    public final class DefaultUserService implements UserService { }

    // Priority 5: Basic Factory - higher priority, overrides @Component
    @KoraApp
    public interface Application {
        default UserService userService() {
            return new CustomUserService(); // This will be used instead
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Priority 9: Auto Factory (@Component) - lowest priority
    @Component
    class DefaultUserService : UserService

    // Priority 5: Basic Factory - higher priority, overrides @Component
    @KoraApp
    interface Application {
        fun userService(): UserService = CustomUserService() // This will be used instead
    }
    ```

---

## Объявление компонентов { #declaring-components }

Компоненты в Kora можно объявлять несколькими способами, и у каждого способа есть свои приоритеты и сценарии применения. **Все способы объявления компонентов требуют, чтобы код находился внутри
Gradle-модулей, содержащих интерфейсы `@KoraApp` или `@KoraSubmodule`** — обработчик аннотаций Kora сканирует только эти явно назначенные модули.

### Автоматическая фабрика (`@Component`) { #automatic-factory-component }

Классы, помеченные `@Component`, автоматически регистрируются, если соответствуют требованиям:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class UserService {
        private final UserRepository repository;

        public UserService(UserRepository repository) {
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class UserService(
        private val repository: UserRepository
    )
    ```

**Требования:**

- не `abstract`
- ровно один публичный конструктор
- класс с модификатором `final` (если не применены AOP-аспекты)
- параметры конструктора становятся зависимостями

### Базовые фабричные методы { #basic-factory-methods }

Методы по умолчанию в интерфейсах `@KoraApp` или `@Module`, которые возвращают компоненты:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application {
        fun userService(repository: UserRepository): UserService =
            UserService(repository)

        fun userRepository(): UserRepository =
            InMemoryUserRepository()
    }
    ```

### Фабрика модуля { #module-factory }

Фабричные методы внутри интерфейсов `@Module`:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface DatabaseModule {
        fun dataSource(): DataSource =
            HikariDataSource()

        fun userRepository(dataSource: DataSource): UserRepository =
            JdbcUserRepository(dataSource)
    }
    ```

### Фабрика внешнего модуля { #external-module-factory }

Модули из внешних зависимостей, унаследованные через расширение интерфейса:

===! ":fontawesome-brands-java: Java"

    ```java
    @KoraApp
    public interface Application extends
        ru.tinkoff.kora.http.HttpModule,
        ru.tinkoff.kora.json.JsonModule {
        // Inherits all factory methods from external modules
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @KoraApp
    interface Application :
        ru.tinkoff.kora.http.HttpModule,
        ru.tinkoff.kora.json.JsonModule {
        // Inherits all factory methods from external modules
    }
    ```

> **Требуется явный импорт**: компоненты внешних библиотек не доступны автоматически. Нужно явно наследовать интерфейсы модулей библиотеки в интерфейсе `@KoraApp`. Простого добавления библиотеки в
> путь классов недостаточно — расширение интерфейса модуля делает компоненты доступными для внедрения зависимостей.

**Такой явный подход предотвращает частые проблемы автоматических фреймворков:**

- нет неожиданного создания ненужных компонентов
- ясно видно, какие зависимости действительно используются
- безопасность выше благодаря намеренному включению
- отладка и сопровождение проще

### Фабрика подмодуля { #submodule-factory }

Сгенерированные модули из интерфейсов `@KoraSubmodule`:

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface PersistenceModule {
        default UserRepository userRepository() {
            return new InMemoryUserRepository();
        }
    }

    @KoraSubmodule
    public interface ApplicationSubmodule {
        // Generates factory methods for all @Module and @Component in the project
    }

    @KoraApp
    public interface Application extends ApplicationSubmodule {  // <----- Подключили модуль
        // All components from submodules are available
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface PersistenceModule {
        fun userRepository(): UserRepository =
            InMemoryUserRepository()
    }

    @KoraSubmodule
    interface ApplicationSubmodule {
        // Generates factory methods for all @Module and @Component in the project
    }

    @KoraApp
    interface Application : ApplicationSubmodule {  // <----- Подключили модуль
        // All components from submodules are available
    }
    ```

### Обобщенная фабрика { #generic-factory }

Методы с обобщенными параметрами типа, которые могут создавать компоненты любого подходящего типа. Обобщенные фабрики особенно полезны для создания типобезопасных компонентов, работающих с разными
обобщенными типами.

===! ":fontawesome-brands-java: Java"

    ```java
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

=== ":simple-kotlin: Kotlin"

    ```kotlin
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

- параметр типа `<T>` позволяет создавать валидаторы для любого типа элементов
- `TypeRef<T>` предоставляет сведения о типе во время выполнения для операций с обобщениями
- можно создавать `Validator<List<String>>`, `Validator<Set<User>>` и т.д.
- обеспечивает типобезопасную валидацию обобщенных коллекций

### Механизм расширений { #extension-mechanism }

Компоненты, динамически генерируемые расширениями (JSON-преобразователи, репозитории и т.д.):

```java
// Extensions automatically generate components for:
-JSON readers/writers for classes
-
Database repositories
from interfaces
-
HTTP clients
from interfaces
-
And many
more...
```

### Фабрика `@DefaultComponent` { #defaultcomponent-factory }

Реализации по умолчанию, которые можно переопределить:

===! ":fontawesome-brands-java: Java"

    ```java
    @Module
    public interface CacheModule {
        @DefaultComponent
        default Cache cache() {
            return new InMemoryCache();
        }
    }

    // Can be overridden in application:
    @KoraApp
    public interface Application extends CacheModule {  // <----- Подключили модуль

        default Cache primaryCache() {
            return new RedisCache(); // Overrides the default
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Module
    interface CacheModule {
        @DefaultComponent
        fun cache(): Cache = InMemoryCache()
    }

    // Can be overridden in application:
    @KoraApp
    interface Application : CacheModule {  // <----- Подключили модуль

        fun primaryCache(): Cache = RedisCache() // Overrides the default
    }
    ```

### Автоматическое создание { #automatic-creation }

Классы, которые соответствуют требованиям к компонентам, но не помечены явно:

===! ":fontawesome-brands-java: Java"

    ```java
    public final class SomeService {
        public SomeService(Dependency dep) {
            // Will be auto-created if needed and meets requirements
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    class SomeService(private val dep: Dependency) {
        // Will be auto-created if needed and meets requirements
    }
    ```

**Порядок приоритета** (от высшего к низшему):

1. автоматическое создание
2. механизм расширений
3. обобщенная фабрика
4. стандартная фабрика (`@DefaultComponent`)
5. базовая фабрика
6. фабрика модуля
7. фабрика внешнего модуля
8. фабрика подмодуля
9. автоматическая фабрика (`@Component`)

## Заявки зависимостей и разрешение { #dependency-claims-resolution }

Kora использует развитую систему разрешения зависимостей, основанную на “заявках”. Каждый параметр зависимости разбирается в `DependencyClaim`, который задает, как должна быть разрешена зависимость.
В этот момент параметры конструктора перестают быть просто Java- или Kotlin-типами и становятся требованиями к графу. Kora смотрит на запрошенный тип, тип-обертку, аннотации nullable и теги, а затем
решает, какой компонент может удовлетворить такой запрос.

Понимание заявок помогает читать ошибки компиляции. Когда Kora сообщает, что зависимость отсутствует, неоднозначна, допускает `null` или участвует в цикле, она описывает именно заявку, которую пыталась
разрешить, и кандидатов, найденных в графе.

### Базовые типы зависимостей { #basic-dependency-types }

Большинство зависимостей Kora выражаются прямо в конструкторах или параметрах фабричных методов. Форма параметра показывает Kora, нужна ли одна обязательная зависимость, необязательная зависимость,
отложенный доступ или коллекция реализаций. Благодаря этому отношения между компонентами описываются в обычном коде, без дополнительных вызовов контейнера.

Выбирайте самую простую форму, которая соответствует правилу предметной области. Если сервис не может работать без репозитория, запрашивайте репозиторий напрямую. Если интеграция необязательна,
помечайте ее nullable. Если нужны все реализации точки расширения, используйте `All<T>`. Если важно избежать каскадного обновления или отложить доступ к компоненту, используйте `ValueOf<T>`.

#### Обязательные { #required }

Одна обязательная зависимость, которая должна существовать:
Это форма зависимости по умолчанию и самый частый вариант. Обязательный параметр означает, что граф приложения недействителен, если в нем нет ровно одного подходящего компонента. Так обычно запрашивают
основные зависимости: репозитории, сервисы, валидаторы, интерфейсы конфигурации и клиенты, без которых обычная сборка приложения невозможена.

Обязательные зависимости делают ошибки явными. Если вы забыли импортировать модуль или объявить компонент, сборка падает на этапе генерации графа, а приложение не стартует с частично настроенным
runtime.

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class UserService {
        public UserService(UserRepository repository) { // ONE_REQUIRED
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class UserService(private val repository: UserRepository) // ONE_REQUIRED
    ```

#### Необязательные { #optional }

Одна необязательная зависимость, которая может быть `null`:
Nullable-зависимости полезны для необязательных возможностей, интеграций и библиотечных расширений, которые приложение может предоставить, но не обязано. Kora все равно разрешает такую зависимость по
типу и тегам, но отсутствие кандидата считается допустимым, и сгенерированный граф передает `null`.

Используйте это намеренно. Nullable-зависимость должна означать “компонент умеет работать без этого участника”, а не “не уверен, правильно ли собран граф”. Код, получающий nullable-зависимость, должен
явно описывать поведение в деградированном режиме.

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class UserService {
        public UserService(@Nullable AuditService auditService) { // ONE_NULLABLE
            this.auditService = auditService;
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class UserService(@Nullable private val auditService: AuditService?) // ONE_NULLABLE
    ```

#### `ValueOf` { #valueof }

Синхронный доступ к текущему значению компонента:
`ValueOf<T>` — это обертка над ссылкой на компонент. Она позволяет компоненту получить текущее значение тогда, когда оно действительно нужно, а не держать прямую зависимость. Это полезно, когда
зависимость может обновляться, когда инициализацию стоит отложить или когда прямое ребро графа заставило бы обновлять больше компонентов, чем нужно.

В обычном коде обработки запросов `ValueOf<T>` чаще всего не требуется. Для простой совместной работы сервисов лучше использовать прямую зависимость. `ValueOf<T>` нужен там, где важно поведение
жизненного цикла: обновление конфигурации, дорогие компоненты или компоненты, которые не должны обновлять своих потребителей одновременно с собой.

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class OrderService {
        public OrderService(ValueOf<UserService> userService) {
            // Can call userService.get() to get current value
            // Can call userService.refresh() to get updated value
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class OrderService(private val userService: ValueOf<UserService>) {
        // Can call userService.get() to get current value
        // Can call userService.refresh() to get updated value
    }
    ```

Также может быть синхронный доступ с `@Nullable`:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class OrderService {
        public OrderService(@Nullable ValueOf<AuditService> auditService) {
            // auditService may be null
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class OrderService(@Nullable private val auditService: ValueOf<AuditService>?) {
        // auditService may be null
    }
    ```

#### `All` { #all }

Все реализации типа как отдельные зависимости:
`All<T>` моделирует точки расширения. Вместо выбора одной реализации Kora внедряет все подходящие реализации в детерминированную коллекцию. Это удобно для обработчиков, валидаторов, слушателей,
перехватчиков, экспортеров и любых мест, где приложение должно собрать несколько независимых вкладов.

Важно, что каждый элемент `All<T>` все равно остается компонентом графа. Kora проверяет каждую реализацию, применяет теги, если они указаны, и собирает коллекцию во время компиляции. Поэтому такая
plugin-like композиция остается типобезопасной и видимой в сгенерированном графе.

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(All<Notifier> notifiers) {
            // Receives all Notifier implementations
            // Each notifier is a separate dependency
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class NotificationService(private val notifiers: All<Notifier>) {
        // Receives all Notifier implementations
        // Each notifier is a separate dependency
    }
    ```

Также реализация может быть обернута в `ValueOf`:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(All<ValueOf<Notifier>> notifiers) {
            // Each notifier wrapped in ValueOf
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class NotificationService(private val notifiers: All<ValueOf<Notifier>>) {
        // Each notifier wrapped in ValueOf
    }
    ```

#### `TypeRef` { #typeref }

Ссылка на тип для рефлексии или операций с обобщениями:
`TypeRef<T>` переносит информацию об обобщенном типе через стирание типов. Он нужен, когда компоненту важен не только сырой класс, но и полная форма типа, запрошенная графом. JSON-преобразователи,
извлекатели конфигурации, сериализаторы и другая сгенерированная инфраструктура часто используют такие type token'ы.

Большинству прикладных сервисов не нужно внедрять `TypeRef<T>` напрямую. Относитесь к нему как к инфраструктурному инструменту для кода, который создает или адаптирует компоненты на основе обобщенных
типов. Если вы используете `TypeRef<T>`, параметр типа должен точно описывать модель, за которую отвечает компонент.

===! ":fontawesome-brands-java: Java"

    ```java
    public interface ValidatorModule {
        default <T> Validator<List<T>> listValidator(Validator<T> validator, TypeRef<T> valueRef) {
            return new IterableValidator<>(validator);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    interface ValidatorModule {
        fun <T> listValidator(validator: Validator<T>, valueRef: TypeRef<T>): Validator<List<T>> =
            IterableValidator(validator)
    }
    ```

### Контракт типов-оберток { #wrapper-type-contract }

Типы-обертки в Kora описывают поведение зависимости, не меняя сам запрашиваемый компонент. `ValueOf<T>` означает “дайте мне управляемый доступ к этому компоненту”, а `All<T>` означает “дайте мне все
подходящие компоненты”. Сам `T` остается бизнес-типом; обертка меняет способ разрешения и предоставления зависимости.

Такой подход сохраняет читаемость API. Конструктор с `UserRepository` требует один репозиторий. Конструктор с `ValueOf<UserRepository>` требует контролируемый доступ к репозиторию. Конструктор с
`All<Notifier>` требует коллекцию реализаций уведомителей. Эти сигнатуры прямо документируют связь компонентов в графе.

===! ":fontawesome-brands-java: Java"

    ```java
    public interface ValueOf<T> {
        T get();
        void refresh();
    }

    public interface All<T> extends List<T> {
        // Token type extending List
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    interface ValueOf<T> {
        fun get(): T
        fun refresh()
    }

    interface All<T> : List<T> {
        // Token type extending List
    }
    ```

### Правила разрешения зависимостей { #dependency-resolution-rules }

Kora разрешает зависимости в предсказуемом порядке. Сначала определяется форма запрошенного типа, затем применяются теги и обертки, после чего выбирается подходящая фабрика или компонент с самым высоким
приоритетом. Если результат отсутствует, неоднозначен или создает цикл, генерация графа завершается ошибкой компиляции.

Именно поэтому явные объявления компонентов важны. Простого добавления зависимости в build-файл недостаточно, чтобы каждый компонент библиотеки появился в графе. Приложение должно импортировать нужный
модуль, объявить нужный компонент или запросить правильный тег. Сгенерированный граф остается финальным источником правды о том, что реально запускается.

1. **Сопоставление по типу**: зависимости сопоставляются по типу и тегам
2. **Фильтрация по тегам**: аннотации `@Tag` сужают поиск
3. **Порядок приоритета**: фабрики с более высоким приоритетом переопределяют более низкие
4. **Обнаружение циклов**: циклические зависимости обнаруживаются во время компиляции
5. **Необязательность**: `@Nullable` помечает необязательные зависимости

### Косвенные зависимости { #indirect-dependencies }

Используйте `ValueOf<T>`, чтобы избежать каскадного обновления компонентов при обновлении зависимостей:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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

**Почему требуется `ValueOf<T>`:** когда компонент обновляется, все компоненты, которые напрямую от него зависят, тоже обновляются. `ValueOf<T>` создает косвенную зависимость, которая предотвращает
такое каскадное обновление и позволяет компонентам получать обновленные значения без собственного обновления.

---

## Система тегов { #tag-system }

Теги позволяют нескольким реализациям одного интерфейса сосуществовать и различаться во время внедрения зависимостей. Теги используют ссылки на классы вместо строк, что улучшает поддержку
рефакторинга.

### Использование тегов { #tags }

===! ":fontawesome-brands-java: Java"

    ```java
    // Tag classes (usually empty marker classes)
    public final class RedisTag {}
    public final class InMemoryTag {}

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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Tag classes (usually empty marker classes)
    class RedisTag
    class InMemoryTag

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

Теги можно применять напрямую к классам компонентов:

===! ":fontawesome-brands-java: Java"

    ```java
    @Tag(RedisTag.class)
    public final class RedisCache implements Cache {
        // Implementation
    }

    @Tag(InMemoryTag.class)
    public final class InMemoryCache implements Cache {
        // Implementation
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Tag(RedisTag::class)
    class RedisCache : Cache {
        // Implementation
    }

    @Tag(InMemoryTag::class)
    class InMemoryCache : Cache {
        // Implementation
    }
    ```

### Теги на методах { #method-tags }

Теги можно применять к фабричным методам:

===! ":fontawesome-brands-java: Java"

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

=== ":simple-kotlin: Kotlin"

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

Создавайте переиспользуемые аннотации тегов:

===! ":fontawesome-brands-java: Java"

    ```java
    @Tag(RedisTag.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
    public @interface RedisCache {}

    @Tag(InMemoryTag.class)
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
    public @interface InMemoryCache {}

    // Использование
    @RedisCache
    @Component
    public final class RedisCacheImpl implements Cache {}

    @Component
    public final class UserService {
        public UserService(@RedisCache Cache cache) {
            // Внедряет RedisCacheImpl
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Tag(RedisTag::class)
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.VALUE_PARAMETER)
    annotation class RedisCache

    @Tag(InMemoryTag::class)
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.VALUE_PARAMETER)
    annotation class InMemoryCache

    // Использование
    @RedisCache
    @Component
    class RedisCacheImpl : Cache

    @Component
    class UserService(@RedisCache private val cache: Cache) {
        // Внедряет RedisCacheImpl
    }
    ```

### Специальные теги { #special-tags }

Специальные формы тегов нужны, когда обычные правила сопоставления слишком узкие. Они позволяют намеренно расширить запрос, не теряя типобезопасность. Чаще всего это встречается с `All<T>`, когда нужно
получить все реализации точки расширения или все реализации внутри конкретной группы тегов.

Используйте специальные теги аккуратно. Они сильны именно потому, что меняют смысл запроса зависимости. Обычный тег означает “только эта группа”; `Tag.Any` означает “игнорировать группировку”;
коллекционный запрос с конкретным тегом означает “собрать всю эту группу”.

#### @Tag.Any { #tag-any }

Подходит ко всем компонентам независимо от их тегов:
`@Tag.Any` — самый широкий запрос. Он полезен, когда потребитель намеренно универсален: например, реестр, диагностический компонент или диспетчер, которому нужно видеть и помеченные, и непомеченные
реализации. Без `Tag.Any` tagged-зависимость обычно ищет только конкретный набор тегов.

Так как `Tag.Any` расширяет ребро графа, он должен быть явно виден в сигнатуре конструктора и использоваться только там, где такое широкое поведение является частью дизайна. Если сервису нужны только
Redis-кеши или только email-уведомители, лучше запросить конкретный тег.

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(@Tag(Tag.Any.class) All<Notifier> notifiers) {
            // Получает ВСЕ уведомители, и с тегами, и без тегов
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class NotificationService(@Tag(Tag.Any::class) private val notifiers: All<Notifier>) {
        // Получает ВСЕ уведомители, и с тегами, и без тегов
    }
    ```

#### All с тегом { #tagged-all }

Получение всех компонентов с конкретным тегом:
Этот паттерн собирает все реализации, имеющие общий тег. Он полезен, когда у подсистемы несколько реализаций, но все они относятся к одной именованной группе: Redis-кеши, перехватчики публичного API,
внутренние health checks или группа конкретного поставщика.

Тег удерживает коллекцию сфокусированной. Компоненты того же Java- или Kotlin-типа могут существовать в других частях графа и не попадать в эту зависимость. Поэтому `All<T>` удобно использовать в
крупных приложениях, где один интерфейс может переиспользоваться в нескольких независимых контекстах.

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class NotificationService {
        public NotificationService(@Tag(RedisTag.class) All<Cache> caches) {
            // Получает все реализации Cache, помеченные RedisTag
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class NotificationService(@Tag(RedisTag::class) private val caches: All<Cache>) {
        // Получает все реализации Cache, помеченные RedisTag
    }
    ```

### Правила сопоставления тегов { #tag-matching-rules }

Сопоставление тегов намеренно точное. Kora рассматривает теги как часть идентичности зависимости наряду с типом. Это предотвращает случайное внедрение неправильной реализации, когда несколько
компонентов имеют один интерфейс, но относятся к разным контекстам.

Если зависимость не разрешается, проверяйте и тип, и тег. Компонент с правильным типом, но неправильным тегом не подходит. Точно так же untagged-зависимость не выберет tagged-компонент автоматически,
если запрос явно не описывает такое поведение.

1. **Точное совпадение**: теги должны точно совпадать по ссылке на класс
2. **Наследование**: классы тегов могут быть частью иерархий наследования
3. **Несколько тегов**: компоненты могут иметь несколько тегов
4. **Фильтрация по тегам**: зависимости могут указывать требуемые теги

### Что дальше { #whats-next }

Теперь, когда вы понимаете основные понятия системы внедрения зависимостей Kora, вы готовы собрать все вместе. Продолжайте с [Созданием приложений Kora с внедрением зависимостей](dependency-injection.md): это пошаговое руководство, где создается полноценная система уведомлений и эти понятия показываются в практическом
контексте.

В руководстве рассматривается:

- настройка проекта и многомодульная структура
- модули внешних библиотек со значениями по умолчанию
- переопределение и настройка компонентов
- зависимости с тегами и внедрение коллекций
- необязательные зависимости и устойчивое поведение при их отсутствии
- подмодули и организация компонентов
- обобщенные фабрики и типобезопасное создание
- отложенная загрузка через `ValueOf<T>` для повышения производительности

## Лучшие практики { #best-practices }

- Предпочитайте внедрение через конструктор и позволяйте Kora строить граф зависимостей во время компиляции.
- Держите компоненты сфокусированными на одной ответственности, чтобы ошибки графа оставались понятными.
- Используйте модули для переиспользуемых фабрик и компонентов по умолчанию, а не как место, где прячется прикладная логика.
- Используйте теги только тогда, когда у одного договора есть несколько осмысленных реализаций.
- Избегайте поиска служб, циклических зависимостей и крупных компонентов, которые смешивают несвязанные ответственности.

Делайте компоненты небольшими:

Почему это важно: небольшие компоненты легче тестировать, понимать и переиспользовать. У каждого компонента должна быть одна ответственность.

Совет новичку: если компонент делает слишком много, разделите его. Спросите себя: "Какая у этого компонента одна задача?"

Хороший пример:

===! ":fontawesome-brands-java: Java"

    ```java
    // ✅ Компоненты с одной ответственностью
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
            // Только координирует оплату и сохранение
            payment.processPayment(order);
            repository.save(order);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // ✅ Компоненты с одной ответственностью
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
            // Только координирует оплату и сохранение
            payment.processPayment(order)
            repository.save(order)
        }
    }
    ```

Внедрение через конструктор:

Почему это важно: внедрение через конструктор делает зависимости явными и не допускает частично созданных объектов. Это самый безопасный и самый удобный для тестирования способ внедрения.

Совет новичку: всегда размещайте зависимости в конструкторе. Никогда не создавайте зависимости внутри методов: это антишаблон "поиск службы".

Хороший пример:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class UserService {
        private final UserRepository repository;
        private final PasswordEncoder encoder;

        // ✅ Все зависимости объявлены в конструкторе
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

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class UserService(
        private val repository: UserRepository,
        private val encoder: PasswordEncoder
    ) {
        // ✅ Все зависимости объявлены в конструкторе

        fun createUser(email: String, password: String): User {
            val hashedPassword = encoder.encode(password)
            val user = User(email, hashedPassword)
            return repository.save(user)
        }
    }
    ```

Обрабатывайте optional-зависимости:

Почему это важно: не все возможности всегда доступны. Необязательные зависимости позволяют приложению работать с разными настройками.

Совет новичку: используйте `@Nullable`, когда зависимости может не быть. Всегда проверяйте значение на `null` перед использованием.

Хороший пример:

===! ":fontawesome-brands-java: Java"

    ```java
    @Component
    public final class NotificationService {
        private final EmailService emailService;
        private final SmsService smsService; // Может быть не настроен

        public NotificationService(EmailService emailService, @Nullable SmsService smsService) {
            this.emailService = emailService;
            this.smsService = smsService;
        }

        public void sendNotification(String message) {
            emailService.sendEmail(message); // Всегда доступен

            // ✅ Аккуратная обработка необязательной зависимости
            if (smsService != null) {
                smsService.sendSms(message);
            }
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    @Component
    class NotificationService(
        private val emailService: EmailService,
        @Nullable private val smsService: SmsService? // Может быть не настроен
    ) {
        fun sendNotification(message: String) {
            emailService.sendEmail(message) // Всегда доступен

            // ✅ Аккуратная обработка необязательной зависимости
            smsService?.sendSms(message)
        }
    }
    ```

Теги:

Почему это важно: иногда нужны несколько реализаций одного интерфейса, например разные каналы уведомлений. Теги помогают различать их.

Совет новичку: создавайте пустые маркерные классы для тегов. Используйте понятные имена вроде `EmailNotification.class`, а не слишком общие.

Хороший пример:

===! ":fontawesome-brands-java: Java"

    ```java
    // Классы тегов
    public final class EmailTag {}
    public final class SmsTag {}

    // Реализации с тегами
    @Tag(EmailTag.class)
    @Component
    public final class EmailNotifier implements Notifier {
        public void notify(String message) { /* email logic */ }
    }

    @Tag(SmsTag.class)
    @Component
    public final class SmsNotifier implements Notifier {
        public void notify(String message) { /* SMS logic */ }
    }

    // Использование
    @Component
    public final class AlertService {
        private final Notifier emailNotifier;
        private final Notifier smsNotifier;

        public AlertService(
            @Tag(EmailTag.class) Notifier emailNotifier,
            @Tag(SmsTag.class) Notifier smsNotifier
        ) {
            this.emailNotifier = emailNotifier;
            this.smsNotifier = smsNotifier;
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Классы тегов
    class EmailTag
    class SmsTag

    // Реализации с тегами
    @Tag(EmailTag::class)
    @Component
    class EmailNotifier : Notifier {
        override fun notify(message: String) { /* email logic */ }
    }

    @Tag(SmsTag::class)
    @Component
    class SmsNotifier : Notifier {
        override fun notify(message: String) { /* SMS logic */ }
    }

    // Использование
    @Component
    class AlertService(
        @Tag(EmailTag::class) private val emailNotifier: Notifier,
        @Tag(SmsTag::class) private val smsNotifier: Notifier
    )
    ```

Компоненты и модули:

Почему это важно: модули группируют связанные компоненты, поэтому приложение проще понимать и сопровождать.

Совет новичку: создавайте модули для разных слоев (база данных, службы, HTTP) или предметных областей (сообщения, уведомления, управление пользователями).

Хороший пример:

===! ":fontawesome-brands-java: Java"

    ```java
    // Отдельные модули отправителей для разных каналов
    @Module
    public interface SlackModule {

        @Tag(SlackMessenger.class)
        @DefaultComponent
        default Supplier<String> slackMessengerHeaderSupplier() {
            return () -> "ASCII_PROTOCOL_MESSENGER_SLACK";
        }
    }

    @Module
    public interface SignalModule {

        @Tag(SignalMessenger.class)
        @DefaultComponent
        default Supplier<String> signalMessengerHeaderSupplier() {
            return () -> "ASCII_PROTOCOL_MESSENGER_SIGNAL";
        }
    }

    @Component
    public final class SlackMessenger implements Messenger {

        private final Supplier<String> headerSupplier;

        public SlackMessenger(@Tag(SlackMessenger.class) Supplier<String> headerSupplier) {
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

        public SignalMessenger(@Tag(SignalMessenger.class) Supplier<String> headerSupplier) {
            this.headerSupplier = headerSupplier;
        }

        @Override
        public void sendMessage(String message) {
            String header = headerSupplier.get();
            System.out.println(header + " ---> " + message);
        }
    }

    // Приложение объединяет модули отправителей
    @KoraApp
    public interface Application extends
        SlackModule,        // Отправка через Slack
        SignalModule {      // Отправка через Signal
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Отдельные модули отправителей для разных каналов
    @Module
    interface SlackModule {

        @Tag(SlackMessenger::class)
        @DefaultComponent
        fun slackMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SLACK" }
    }

    @Module
    interface SignalModule {

        @Tag(SignalMessenger::class)
        @DefaultComponent
        fun signalMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SIGNAL" }
    }

    @Component
    class SlackMessenger(
        @Tag(SlackMessenger::class) private val headerSupplier: Supplier<String>
    ) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    @Component
    class SignalMessenger(
        @Tag(SignalMessenger::class) private val headerSupplier: Supplier<String>
    ) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    // Приложение объединяет модули отправителей
    @KoraApp
    interface Application :
        SlackModule,        // Отправка через Slack
        SignalModule        // Отправка через Signal
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Отдельные модули отправителей для разных каналов
    @Module
    interface SlackModule {

        @Tag(SlackMessenger::class)
        @DefaultComponent
        fun slackMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SLACK" }
    }

    @Module
    interface SignalModule {

        @Tag(SignalMessenger::class)
        @DefaultComponent
        fun signalMessengerHeaderSupplier(): Supplier<String> = Supplier { "ASCII_PROTOCOL_MESSENGER_SIGNAL" }
    }

    @Component
    class SlackMessenger(@Tag(SlackMessenger::class) private val headerSupplier: Supplier<String>) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    @Component
    class SignalMessenger(@Tag(SignalMessenger::class) private val headerSupplier: Supplier<String>) : Messenger {

        override fun sendMessage(message: String) {
            val header = headerSupplier.get()
            println("$header ---> $message")
        }
    }

    // Приложение объединяет модули отправителей
    @KoraApp
    interface Application :
        SlackModule,        // Отправка через Slack
        SignalModule        // Отправка через Signal
    ```

Антишаблоны:

❌ Шаблон поиска службы:

===! ":fontawesome-brands-java: Java"

    ```java
    // Так делать не нужно
    @Component
    public final class BadService {
        public void doSomething() {
            // Создание зависимостей внутри методов
            Database db = ServiceLocator.getDatabase(); // ❌ Антишаблон
            db.save(data);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Так делать не нужно
    @Component
    class BadService {
        fun doSomething() {
            // Создание зависимостей внутри методов
            val db = ServiceLocator.getDatabase() // ❌ Антишаблон
            db.save(data)
        }
    }
    ```

❌ Циклические зависимости:

===! ":fontawesome-brands-java: Java"

    ```java
    // Не создавайте циклические зависимости
    @Component
    class ServiceA {
        ServiceA(ServiceB b) {} // ServiceA зависит от ServiceB
    }

    @Component
    class ServiceB {
        ServiceB(ServiceA a) {} // ServiceB зависит от ServiceA — ЦИКЛ!
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Не создавайте циклические зависимости
    @Component
    class ServiceA(private val b: ServiceB) // ServiceA зависит от ServiceB

    @Component
    class ServiceB(private val a: ServiceA) // ServiceB зависит от ServiceA — ЦИКЛ!
    ```

❌ Крупные компоненты:

===! ":fontawesome-brands-java: Java"

    ```java
    // Не создавайте "божественные объекты"
    @Component
    public final class HugeService {
        // ❌ Делает все: проверку, работу с базой данных, почту, журналирование, кеширование...
        private final Validator validator;
        private final Repository repo;
        private final EmailService email;
        private final Logger logger;
        private final Cache cache;

        // Сотни методов...
    }
    ```

=== ":simple-kotlin: Kotlin"

    ```kotlin
    // Не создавайте "божественные объекты"
    @Component
    class HugeService(
        // ❌ Делает все: проверку, работу с базой данных, почту, журналирование, кеширование...
        private val validator: Validator,
        private val repo: Repository,
        private val email: EmailService,
        private val logger: Logger,
        private val cache: Cache
    ) {
        // Сотни методов...
    }
    ```

## Итоги { #summary }

Вы изучили основные идеи внедрения зависимостей в Kora:

- компоненты объявляют, что им нужно, через конструкторы или методы компонентов
- Kora проверяет и создает граф зависимостей во время компиляции
- модули группируют переиспользуемые фабрики и компоненты по умолчанию
- теги различают несколько реализаций одного типа
- внедрение зависимостей сохраняет структуру приложения явной и удобной для тестирования

## Устранение неполадок { #troubleshooting }

**Компонент не найден:**

- Проверьте, что класс помечен `@Component` или возвращается из метода `@Module`.
- Убедитесь, что модуль подключен к интерфейсу `@KoraApp`.

**Одной зависимости соответствует несколько компонентов:**

- Добавьте тег к зависимости и к компоненту, который должен ее предоставить.
- Держите классы тегов или маркерные аннотации рядом с договором, который они уточняют.

**Сгенерированный граф не компилируется:**

- Прочитайте сгенерированную ошибку о первой отсутствующей или неоднозначной зависимости.
- Компилируйте снова после исправления одной проблемы графа; последующие ошибки часто зависят от первой.

## Что дальше? { #whats-next-2 }

- [Создайте полноценное приложение с внедрением зависимостей](dependency-injection.md), чтобы без лишних деталей HTTP-слоя потренироваться с модулями, компонентами, фабриками, тегами, жизненным циклом и
  устройством графа.
- [Создайте первое приложение Kora](getting-started.md), если вы сначала прочитали это введение и теперь хотите запустить минимальное приложение.
- [Конфигурация с HOCON](config-hocon.md) или [конфигурация с YAML](config-yaml.md) после начального руководства: настройка конфигурации опирается на уже запускаемое приложение Kora.

## Помощь { #help }

Если возникли проблемы:

- проверьте [документацию контейнера](../documentation/container.md)
- сравните с базовыми примерами [Kora](home.md)
- вернитесь к руководству [Создание первого приложения Kora](getting-started.md), чтобы свериться с запускаемым графом
