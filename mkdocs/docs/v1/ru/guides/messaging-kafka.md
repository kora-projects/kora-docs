---
search:
  exclude: true
title: Обмен сообщениями с Kafka
summary: Extend the HTTP Server guide with asynchronous user creation using Kafka producer and consumer components in the same Kora application
tags: kafka, messaging, asynchronous, event-driven, producer, consumer
---

# Обмен сообщениями с Kafka { #messaging-kafka }

В этом руководстве рассматривается событийный обмен сообщениями с Kora и Apache Kafka. Вы узнаете, как продюсеры публикуют доменные события, как потребители обрабатывают эти события асинхронно и
как Kora подключает модули Kafka, JSON-сериализаторы, конфигурацию и слушателей с управляемым жизненным циклом в граф приложения. Вы также увидите, как HTTP-запрос может передать работу в Kafka, пока
потребитель завершает операцию в фоне.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-messaging-kafka-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-messaging-kafka-app).

## Что вы создадите { #youll-build }

Вы превратите существующий пользовательский API в небольшой событийный поток:

- контроллер примет `POST /users`
- он сгенерирует будущий идентификатор пользователя
- он опубликует `UserCreatedEvent` в Kafka
- он сразу вернет `202 Accepted`
- потребитель Kafka в том же приложении получит событие
- этот потребитель создаст пользователя через тот же стек сервиса и репозитория

Остальная часть API по-прежнему ведет себя как в руководстве по HTTP-серверу:

- `GET /users/{userId}`
- `GET /users`
- `PUT /users/{userId}`
- `DELETE /users/{userId}`

Поэтому главное изменение в этом руководстве — не вся архитектура приложения. Главное изменение в том, что **создание пользователя становится асинхронным**.

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- Docker для локальной Kafka и интеграционных тестов
- текстовый редактор или среда разработки
- пройденное руководство [HTTP-сервер](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательно: сначала пройдите HTTP-сервер"

    Это руководство предполагает, что вы уже прошли **[HTTP-сервер](http-server.md)** и у вас уже есть `UserController`, `UserService`, `UserRepository`, `InMemoryUserRepository`, `UserRequest` и `UserResponse`.

    Мы сохраним эту знакомую структуру и будем развивать ее, а не начинать с нуля.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь меняется поток создания пользователя, но сохраняются существующие HTTP API и структура сервисов.

## Обзор { #overview }

Это руководство переводит одну часть HTTP-приложения из синхронного поведения «запрос-ответ» в событийное поведение. Вместо того чтобы завершать создание пользователя внутри HTTP-запроса, контроллер
публикует событие и быстро возвращает ответ. Потребитель получает это событие позже и выполняет фактическую запись.

В коде этот сдвиг небольшой, но архитектурно важный. Он вводит асинхронную работу, итоговую согласованность, сериализацию сообщений, обработку потребителем и необходимость сохранять бизнес-логику
переиспользуемой, когда пусковой механизм больше не только HTTP-запрос.

### Что такое событийная архитектура? { #event-driven-architecture }

Событийная архитектура — это стиль проектирования, в котором компоненты взаимодействуют через публикацию и потребление событий. Событие — это факт или запрос на выполнение работы, на который другие
части системы могут реагировать без прямого вызова со стороны продюсера.

В синхронном потоке вызывающая сторона ждет, пока завершится каждый шаг:

1. Приходит HTTP-запрос.
2. Контроллер вызывает сервис.
3. Сервис записывает данные в репозиторий.
4. Ответ возвращается только после завершения записи.

В событийном потоке часть работы переносится за границу сообщения:

1. Приходит HTTP-запрос.
2. Контроллер публикует `UserCreatedEvent`.
3. Ответ возвращается с подтверждением принятия или будущим идентификатором.
4. Потребитель получает событие.
5. Потребитель вызывает сервис и репозиторий, чтобы завершить запись.

Это означает, что система становится в итоге согласованной. Клиент может получить ответ до того, как пользователь станет видим через `GET /users/{id}`. Для асинхронных потоков это нормально, но
поведение API, тесты и раздел устранения неполадок должны явно это показывать.

### Зачем нужны события { #messaging-needed }

Обмен сообщениями помогает, когда выполнение всей работы внутри одного запроса становится неподходящим:

- дорогая работа не должна блокировать запрос, видимый пользователю
- нескольким компонентам нужно реагировать на одно бизнес-событие
- продюсеры и потребители должны масштабироваться независимо
- временный отказ потребителя не всегда должен ломать входную точку
- всплески трафика нужно буферизовать вместо немедленного давления на нижележащие системы

Обмен сообщениями не является заменой простых вызовов методов по умолчанию. Он добавляет операционную сложность: брокеры, темы, сериализацию, повторы, обработку дублей, отставание и порядок.
Используйте его, когда развязка или асинхронное поведение стоят этой сложности.

### Что такое Apache Kafka? { #apache-kafka }

[Apache Kafka](https://kafka.apache.org/documentation/) — это распределенная платформа потоковой передачи событий. Она хранит события в именованных темах, позволяет продюсерам добавлять записи в
эти темы, а потребителям — читать записи в своем темпе. Kafka часто используется как надежная основа событийных систем, потому что она рассчитана на высокую пропускную способность, хранение, повторное
чтение и горизонтальное масштабирование.

На практическом уровне Kafka дает приложениям надежное место, куда можно публиковать факты о произошедшем, и позволяет другим компонентам позже реагировать на эти факты.

### Основные понятия Kafka { #core-kafka-concepts }

- Тема: именованный поток записей
- Продюсер: код приложения, который записывает записи в тему
- Потребитель: код приложения, который читает записи из темы
- Группа потребителей: группа потребителей, которые делят работу по теме
- Брокер: сервер Kafka, который хранит данные тем и обслуживает продюсеров и потребителей
- Ключ и значение записи: данные, отправляемые в Kafka, часто сериализованные из типизированных объектов приложения

Kafka не заменяет базу данных. Основное состояние приложения по-прежнему должно находиться в базе данных или слое репозитория. Kafka — это транспорт, который переносит бизнес-события между
компонентами и сервисами.

### События в сервисах { #messaging-services }

В микросервисных архитектурах обмен сообщениями часто выступает слоем координации между независимо развернутыми компонентами. Вместо того чтобы одному сервису знать каждый нижележащий API и ждать
каждого ответа, он может публиковать события, которые потребляют другие сервисы.

Распространенные шаблоны:

- Публикация-подписка: одно событие может быть потреблено одним или многими подписчиками
- Событийное хранение состояния: состояние приложения восстанавливается из сохраненных событий
- CQRS: изменения на стороне записи публикуют события, которые обновляют одну или несколько моделей чтения
- Шаблон Saga: распределенные рабочие процессы координируются через последовательность событий

В этом руководстве используется минимальная полезная версия этой идеи. Продюсер и потребитель живут в одном приложении, чтобы руководство могло сосредоточиться на модели обмена сообщениями до
разделения потока на несколько сервисов.

### Kafka и Kora { #kora-kafka }

Модули Kafka в Kora подключают продюсеров и потребителей в граф приложения. Конфигурация описывает брокеры, темы, группы потребителей и сериализацию. JSON-сериализаторы сохраняют полезную нагрузку
событий типизированной, а потребители с управляемым жизненным циклом стартуют вместе с приложением и обрабатывают записи в фоне.

Важная граница остается той же, что и в HTTP-руководстве:

- контроллер обрабатывает HTTP-вход и публикует событие
- продюсер является исходящим адаптером обмена сообщениями
- потребитель является входящим адаптером обмена сообщениями
- сервис по-прежнему владеет поведением приложения
- репозиторий по-прежнему владеет хранением

Практический поток:

1. добавить модули и зависимости Kafka
2. ввести `UserCreatedEvent`
3. опубликовать событие из `createUser()`
4. добавить потребителя Kafka для этого события
5. направить работу потребителя обратно через сервис и репозиторий
6. настроить Kafka для локальной разработки и тестов

## Зависимости { #dependencies }

Сначала добавьте поддержку Kafka в проект, который вы уже собрали в руководстве по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    Добавьте эти зависимости в `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        implementation("ru.tinkoff.kora:kafka")
        implementation("ru.tinkoff.kora:json-module")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте эти зависимости в `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        implementation("ru.tinkoff.kora:kafka")
        implementation("ru.tinkoff.kora:json-module")
    }
    ```

Поддержка Kafka в Kora приходит из `KafkaModule`, а поддержка JSON важна, потому что мы хотим отправлять структурированные объекты событий, а не сырые строки.

## Модули { #modules }

Теперь расширьте приложение поддержкой Kafka.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/Application.java"
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowHttpServerModule,
            JsonModule,
            KafkaModule,  // <----- Подключили модуль
            LogbackModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/Application.kt"
    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowHttpServerModule,
        JsonModule,
        KafkaModule,  // <----- Подключили модуль
        LogbackModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

На этом этапе еще ничего не публикуется и не потребляется. Мы только включаем модули фреймворка, которые позже сгенерируют для нас компоненты продюсера и потребителя.

## События { #events }

В руководстве по HTTP-серверу `createUser()` сразу возвращал созданного пользователя, потому что запись происходила в том же запросе.

Здесь нам нужен другой контракт:

- контроллер принимает запрос
- он генерирует будущий идентификатор
- он публикует событие
- он сразу возвращает этот идентификатор

Поэтому нам нужны два новых DTO:

- `UserCreatedEvent` для Kafka
- `UserAcceptedResponse` для HTTP-ответа

Это не только изменение DTO. Это еще и изменение того, как приложение думает о работе.

В синхронном CRUD-приложении поток запроса обычно выполняет все до возврата HTTP-ответа. Часто это хорошая отправная точка, но она становится гораздо менее привлекательной, когда создание пользователя
также требует других медленных или хрупких операций, например:

- вызова внешних поставщиков удостоверений
- выделения данных в другой платформе
- отправки писем или уведомлений
- обновления поисковых индексов
- отправки данных в аналитические системы
- запуска рабочих процессов в других сервисах

Если вся эта работа происходит внутри запроса, конечная точка становится медленнее и хрупче. Одна медленная нижележащая интеграция может заставить пользователя ждать намного дольше ожидаемого, а отказ
одной зависимости может сломать весь путь запроса.

Публикация события и последующая обработка могут быть лучшим решением, потому что:

- HTTP-запрос может быстро завершиться
- долгая работа выходит из потока запроса
- обработка может падать или повторяться независимо
- логика обработки позже может жить в другом приложении без изменения контракта события

Именно это мы моделируем в этом руководстве.

Для простоты продюсер и потребитель все еще живут в одном приложении. Однако концептуально это нужно воспринимать как небольшую имитацию более крупной событийной системы:

- контроллер принимает команду
- Kafka переносит событие
- потребитель позже выполняет фактическую работу создания

Так что, хотя в руководстве используется одно приложение, архитектура относится к тому же виду архитектур, которые команды применяют, когда один сервис публикует событие, а другой сервис его
потребляет.

Добавьте `UserCreatedEvent`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedEvent.java"
    @Json
    public record UserCreatedEvent(
            String id,
            String name,
            String email,
            LocalDateTime createdAt
    ) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedEvent.kt"
    @Json
    data class UserCreatedEvent(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

Это полезная нагрузка, которую Kafka перенесет от продюсера к потребителю.

Добавьте `UserAcceptedResponse`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/dto/UserAcceptedResponse.java"
    @Json
    public record UserAcceptedResponse(String id) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/dto/UserAcceptedResponse.kt"
    @Json
    data class UserAcceptedResponse(val id: String)
    ```

Возврат только будущего идентификатор важен для повествования руководства. Он делает асинхронный контракт видимым для читателя: нет гарантии, что пользователь уже существует ровно в момент
возврата `POST /users`.

## Продюсер { #kafka-producer }

Подробности генерации Kafka-продюсеров, конфигурации топиков и обработки ошибок смотрите в разделе [Producer](../documentation/kafka.md#producer).

Теперь нам нужен компонент продюсера, который может публиковать `UserCreatedEvent`.

Kora генерирует реализации продюсеров из аннотированных интерфейсов, поэтому мы объявляем только контракт.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedPublisher.java"
    @KafkaPublisher("kafka.producer.user-created")
    public interface UserCreatedPublisher {

        @Topic("kafka.producer.user-created-topic")
        void send(@Json UserCreatedEvent event);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedPublisher.kt"
    @KafkaPublisher("kafka.producer.user-created")
    interface UserCreatedPublisher {

        @Topic("kafka.producer.user-created-topic")
        fun send(@Json event: UserCreatedEvent)
    }
    ```

Что здесь происходит:

- `@KafkaPublisher(...)` говорит Kora сгенерировать компонент продюсера Kafka
- `@Topic(...)` указывает на именованную конфигурацию темы в `application.conf`
- `@Json` говорит Kora сериализовать событие в JSON перед отправкой в Kafka

По духу это похоже на HTTP-клиенты Kora: вы описываете контракт, а Kora генерирует реализацию.

### Публикация события { #publish-event }

Это самый важный шаг руководства.

В руководстве по HTTP-серверу `createUser()` делегировал работу сервису и сразу записывал данные в репозиторий. Теперь мы изменим только эту часть контроллера. Остальные HTTP-операции останутся
близкими к исходному CRUD-примеру.

Обновите только зависимости конструктора и метод `createUser()`. Остальные конечные точки остаются такими же, как в руководстве по HTTP-серверу, поэтому здесь мы их не повторяем.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/controller/UserController.java"
    @Component
    @HttpController
    public final class UserController {

        private final UserCreatedPublisher userCreatedPublisher;
        private final UserService userService;

        public UserController(UserCreatedPublisher userCreatedPublisher, UserService userService) {
            this.userCreatedPublisher = userCreatedPublisher;
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public HttpResponseEntity<UserAcceptedResponse> createUser(@Json UserRequest request) {
            var userId = UUID.randomUUID().toString();
            var event = new UserCreatedEvent(userId, request.name(), request.email(), LocalDateTime.now());
            this.userCreatedPublisher.send(event);
            return HttpResponseEntity.of(202, HttpHeaders.of(), new UserAcceptedResponse(userId));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/controller/UserController.kt"
    @Component
    @HttpController
    class UserController(
        private val userCreatedPublisher: UserCreatedPublisher,
        private val userService: UserService
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): HttpResponseEntity<UserAcceptedResponse> {
            val userId = UUID.randomUUID().toString()
            val event = UserCreatedEvent(userId, request.name, request.email, LocalDateTime.now())
            userCreatedPublisher.send(event)
            return HttpResponseEntity.of(202, HttpHeaders.of(), UserAcceptedResponse(userId))
        }
    }
    ```

Что изменилось концептуально:

- `createUser()` больше не сохраняет данные напрямую
- контроллер теперь играет роль входной точки команды
- он возвращает `202 Accepted` вместо `201 Created`
- возвращенный идентификатор — это идентификатор, который будет у будущего пользователя после обработки события

Именно поэтому это руководство хорошо вводит в обмен сообщениями. То же бизнес-действие все еще существует, но меняется момент его выполнения.

## Слой сервиса { #service-layer }

Мы все еще хотим, чтобы этот пример ощущался как продолжение руководства по HTTP-серверу, поэтому сохраняем те же слои:

- контроллер
- сервис
- репозиторий

Единственное отличие в том, что создание пользователя теперь входит в систему через Kafka.

Поскольку потребитель получает полностью подготовленное событие с идентификатор и временем, репозиторий сохраняет готовый объект `UserResponse`, а не генерирует идентификатор сам.

И снова мы показываем только те части, которые действительно изменились по сравнению с руководством по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/repository/UserRepository.java"
    public interface UserRepository {

        void save(UserResponse user);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/repository/UserRepository.kt"
    interface UserRepository {

        fun save(user: UserResponse)
    }
    ```

Репозиторий в памяти меняется только в методе `save(...)`, потому что теперь он хранит полностью подготовленный объект пользователя:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/repository/InMemoryUserRepository.java"
    @Component
    public final class InMemoryUserRepository implements UserRepository {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();

        @Override
        public void save(UserResponse user) {
            this.users.put(user.id(), user);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/repository/InMemoryUserRepository.kt"
    @Component
    class InMemoryUserRepository : UserRepository {

        private val users = ConcurrentHashMap<String, UserResponse>()

        override fun save(user: UserResponse) {
            users[user.id] = user
        }
    }
    ```

Сервис также меняется только там, где потребителю Kafka нужна новая входная точка. Все остальное в классе остается таким же, как в руководстве по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/service/UserService.java"
    @Component
    public final class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        public void createUser(UserCreatedEvent event) {
            this.userRepository.save(new UserResponse(event.id(), event.name(), event.email(), event.createdAt()));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/service/UserService.kt"
    @Component
    class UserService(
        private val userRepository: UserRepository
    ) {

        fun createUser(event: UserCreatedEvent) {
            userRepository.save(UserResponse(event.id, event.name, event.email, event.createdAt))
        }
    }
    ```

Это удерживает руководство на знакомой почве. Читатель по-прежнему работает с теми же идеями `UserService` и `UserRepository`, которые уже изучил в руководстве по HTTP-серверу.

## Потребитель { #kafka-consumer }

Подробнее о `@KafkaListener`, стратегиях подписки, десериализации и ошибках смотрите в разделах [стратегии подключения](../documentation/kafka.md#consume-strategy), [десериализации](../documentation/kafka.md#deserialization) и [обработки исключений](../documentation/kafka.md#exception-handling).

Теперь можно подключить другую сторону потока.

Продюсер уже публикует `UserCreatedEvent`. Потребитель будет слушать эту тему и делегировать работу обратно в сервисный слой.

Сначала слушатель Kafka может выглядеть так просто:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KafkaListener("kafka.consumer.user-created")
    public void process(@Json UserCreatedEvent event) {
        this.userService.createUser(event);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KafkaListener("kafka.consumer.user-created")
    fun process(@Json event: UserCreatedEvent) {
        userService.createUser(event)
    }
    ```

Это хорошая первая мысленная модель: Kora десериализует сообщение и передает объект события в ваш метод.

### Обработка событий { #process-events }

В настоящих приложениях часто полезно также получать возможную ошибку десериализации или сопоставления. Именно эта финальная форма используется в руководстве:

Здесь мы снова показываем только сам класс потребителя, потому что именно этот класс вводится на данном шаге.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedConsumer.java"
    @Component
    public final class UserCreatedConsumer {

        private static final Logger logger = LoggerFactory.getLogger(UserCreatedConsumer.class);

        private final UserService userService;

        public UserCreatedConsumer(UserService userService) {
            this.userService = userService;
        }

        @KafkaListener("kafka.consumer.user-created")
        public void process(@Json @Nullable UserCreatedEvent event, @Nullable Exception exception) {
            if (exception != null) {
                logger.warn("Failed to consume user creation event", exception);
                return;
            }
            if (event == null) {
                logger.warn("Received null user creation event without exception");
                return;
            }
            logger.info("Consuming user creation event for user {}", event.id());
            this.userService.createUser(event);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/messaging/kafka/kafka/UserCreatedConsumer.kt"
    @Component
    class UserCreatedConsumer(
        private val userService: UserService
    ) {

        private val logger = LoggerFactory.getLogger(UserCreatedConsumer::class.java)

        @KafkaListener("kafka.consumer.user-created")
        fun process(@Json event: UserCreatedEvent?, exception: Exception?) {
            if (exception != null) {
                logger.warn("Failed to consume user creation event", exception)
                return
            }
            if (event == null) {
                logger.warn("Received null user creation event without exception")
                return
            }
            logger.info("Consuming user creation event for user {}", event.id)
            userService.createUser(event)
        }
    }
    ```

Почему это полезно:

- если десериализация завершится ошибкой, Kora может передать ошибку в ваш слушатель
- бизнес-код может отделить «корректное событие» от «сообщение не удалось прочитать»
- руководство может показать и простую форму, и более защитную форму в промышленном стиле

Это также хорошая симметрия с HTTP-руководствами: контроллер остается входной точкой для HTTP-команды, но теперь потребитель становится входной точкой для асинхронного этапа обработки.

## Конфигурация { #configuration }

Теперь свяжите продюсера и потребителя с одной и той же темой.

Полное описание настроек смотрите в разделах [HTTP-сервер](../documentation/http-server.md), [Kafka](../documentation/kafka.md) и [Журналирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    kafka {
      producer {
        user-created {
          driverProperties {
            "bootstrap.servers": ${?KAFKA_BOOTSTRAP} //(1)!
          }
          telemetry.logging.enabled = true //(2)!
        }

        user-created-topic {
          topic = "user-created-events" //(3)!
        }
      }

      consumer {
        user-created {
          topics = "user-created-events" //(4)!
          pollTimeout = 250ms //(5)!
          driverProperties {
            "bootstrap.servers": ${?KAFKA_BOOTSTRAP} //(6)!
            "group.id": "guide-messaging-kafka-app" //(7)!
            "auto.offset.reset" = "earliest" //(8)!
            "enable.auto.commit" = true //(9)!
          }
          telemetry.logging.enabled = true //(10)!
        }
      }
    }
    ```

    1. Bootstrap-серверы Kafka, которые используют клиенты продюсера или потребителя. Необязательное переопределение через `KAFKA_BOOTSTRAP`.
    2. Включает возможность для этого раздела конфигурации.
    3. Имя темы или канала, которое использует компонент.
    4. Значение для `kafka.consumer.user-created.topics`.
    5. Значение для `kafka.consumer.user-created.pollTimeout`.
    6. Bootstrap-серверы Kafka, которые используют клиенты продюсера или потребителя. Необязательное переопределение через `KAFKA_BOOTSTRAP`.
    7. Значение для `kafka.consumer.user-created.driverProperties.group.id`.
    8. Значение для `kafka.consumer.user-created.driverProperties.auto.offset.reset`.
    9. Значение для `kafka.consumer.user-created.driverProperties.enable.auto.commit`.
    10. Включает возможность для этого раздела конфигурации.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    kafka:
      producer:
        user-created:
          driverProperties:
            "bootstrap.servers": ${?KAFKA_BOOTSTRAP} #(1)!
          telemetry:
            logging:
              enabled: true #(2)!
        user-created-topic:
          topic: "user-created-events" #(3)!
      consumer:
        user-created:
          topics: "user-created-events" #(4)!
          pollTimeout: 250ms #(5)!
          driverProperties:
            "bootstrap.servers": ${?KAFKA_BOOTSTRAP} #(6)!
            "group.id": "guide-messaging-kafka-app" #(7)!
            "auto.offset.reset": "earliest" #(8)!
            "enable.auto.commit": true #(9)!
          telemetry:
            logging:
              enabled: true #(10)!
    ```

    1. Bootstrap-серверы Kafka, которые используют клиенты продюсера или потребителя. Необязательное переопределение через `KAFKA_BOOTSTRAP`.
    2. Включает возможность для этого раздела конфигурации.
    3. Имя темы или канала, которое использует компонент.
    4. Значение для `kafka.consumer.user-created.topics`.
    5. Значение для `kafka.consumer.user-created.pollTimeout`.
    6. Bootstrap-серверы Kafka, которые используют клиенты продюсера или потребителя. Необязательное переопределение через `KAFKA_BOOTSTRAP`.
    7. Значение для `kafka.consumer.user-created.driverProperties.group.id`.
    8. Значение для `kafka.consumer.user-created.driverProperties.auto.offset.reset`.
    9. Значение для `kafka.consumer.user-created.driverProperties.enable.auto.commit`.
    10. Включает возможность для этого раздела конфигурации.

Что делает эта конфигурация:

- определяет одного продюсера с именем `user-created`
- определяет одного потребителя с именем `user-created`
- направляет их обоих в одну тему Kafka
- включает простую телеметрию журналирования, чтобы вы могли видеть поток во время обучения

## Docker Compose { #docker-compose }

Для локальной разработки запустите Kafka через Docker.

Создайте `docker-compose.yml` в каталоге модуля приложения:

```yaml title="docker-compose.yml"
services:
  kafka:
    image: apache/kafka-native:4.1.0
    restart: unless-stopped
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      CLUSTER_ID: "4L6g3nShT-eMCtK--X86sw"
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: "broker,controller"
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@kafka:9093"
      KAFKA_LISTENERS: "PLAINTEXT://:9092,CONTROLLER://:9093"
      KAFKA_ADVERTISED_LISTENERS: "PLAINTEXT://localhost:9092"
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: "PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT"
      KAFKA_INTER_BROKER_LISTENER_NAME: "PLAINTEXT"
      KAFKA_CONTROLLER_LISTENER_NAMES: "CONTROLLER"
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
```

## Запуск приложения { #run-app }

Запустите Kafka:

```bash
docker compose up -d kafka
```

Затем запустите приложение:

```bash
./gradlew run
```

## Проверка приложения { #check-app }

Создайте пользователя:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Вы должны получить примерно такой ответ:

```json
{"id":"9f6f1d43-8e2c-41ce-a7c1-f1d4d92a7982"}
```

Обратите внимание, что произошло:

- HTTP-запрос вернулся сразу
- ответ не содержит всего созданного пользователя
- идентификатор пользователя уже известен
- настоящая запись происходит, когда потребитель Kafka обработает событие

Теперь получите пользователя:

```bash
curl http://localhost:8080/users/9f6f1d43-8e2c-41ce-a7c1-f1d4d92a7982
```

В зависимости от времени может быть короткий промежуток до того, как пользователь станет видимым. В этом и состоит смысл руководства: теперь цепочка создания асинхронная.

## Лучшие практики { #best-practices }

- Держите DTO событий сосредоточенными на бизнес-смысле. `UserCreatedEvent` должен представлять факт, а не форму HTTP-запроса.
- Относитесь к коду потребителя как к еще одной границе приложения. Аккуратно проверяйте данные и пишите журналы.
- По возможности делайте потребителей идемпотентными. В настоящих системах одно и то же событие может быть доставлено больше одного раза.
- Держите HTTP-контракт честным. Возвращать `202 Accepted` лучше, чем делать вид, что запись уже завершилась.
- Переиспользуйте существующие слои сервиса и репозитория, когда это сохраняет проектирование простым. Kafka должна менять поток, а не заставлять делать лишние переписывания.

## Итоги { #summary }

Вы расширили руководство по HTTP-серверу первым событийным рабочим потоком:

- `POST /users` теперь публикует `UserCreatedEvent`
- контроллер возвращает `202 Accepted` с будущим идентификатор пользователя
- потребитель Kafka получает это событие
- потребитель создает пользователя через `UserService`
- остальная часть CRUD API по-прежнему выглядит знакомо

Это делает руководство мягким введением в асинхронный обмен сообщениями. Приложение все еще ощущается как тот же CRUD-сервис, но одна важная операция теперь выполняется через Kafka.

## Ключевые понятия { #key-concepts }

- Kafka позволяет вынести работу из пути HTTP-запроса
- продюсеры публикуют события, потребители обрабатывают их позже
- `202 Accepted` — естественный HTTP-статус для асинхронного создания
- Kora может генерировать продюсеров Kafka из интерфейсов
- слушатели Kafka могут развиваться от простой сигнатуры только с событием к более защитной форме `event + exception`
- событийная архитектура может строиться поверх тех же слоев сервиса и репозитория, которые вы уже знаете

## Устранение неполадок { #troubleshooting }

**`POST /users` возвращает идентификатор, но `GET /users/{id}` все еще возвращает 404:**

Обычно это означает, что событие было опубликовано, но еще не потреблено, или потребитель не смог его обработать.

Проверьте:

- Kafka запущена
- имя темы одинаковое у продюсера и потребителя
- журналы приложения показывают, что потребитель обрабатывает событие

**Потребитель никогда не получает событие:**

Проверьте:

- `kafka.producer.user-created-topic.topic`
- `kafka.consumer.user-created.topics`
- `KAFKA_BOOTSTRAP`

И продюсер, и потребитель должны указывать на одного брокера и одну тему.

**Ошибки десериализации в потребителе:**

Если JSON не удается прочитать корректно, слушатель может получить `exception != null`.

Именно поэтому финальная сигнатура потребителя в этом руководстве принимает оба значения:

- `@Json @Nullable UserCreatedEvent event`
- `@Nullable Exception exception`

Это дает вам место, где можно явно записать в журнал или отреагировать на ошибки сопоставления.

## Что дальше? { #whats-next }

- [Шаблоны отказоотказоустойчивости](resilient.md), чтобы добавить повторы, автоматические выключатели и резервные ответы вокруг операций, которые публикуют или потребляют события.
- [Наблюдаемость](observability.md), чтобы наблюдать за продюсерами, потребителями, поведением, чувствительным к отставанию, и асинхронными отказами.
- [Кэширование](cache.md), когда событийным записям нужны быстрые пути чтения.
- [База данных JDBC](database-jdbc.md) перед руководством по тестированию как черный ящик, если вам нужен сквозной тестовый путь с JDBC.

## Помощь { #help }

Если вы столкнулись с проблемами:

- сравните с [Kora Java Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-messaging-kafka-app) и [Kora Kotlin Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-messaging-kafka-app)
- вернитесь к [HTTP-серверу](http-server.md) как к базовой синхронной версии API
- проверьте [документацию Kafka](../documentation/kafka.md)
- проверьте [документацию JSON](../documentation/json.md) для сопоставления полезной нагрузки событий
