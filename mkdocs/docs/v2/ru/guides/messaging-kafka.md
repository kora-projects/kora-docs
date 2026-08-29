---
search:
  exclude: true
title: Обмен сообщениями с Kafka
summary: Extend the HTTP Server guide with asynchronous user creation using Kafka producer and consumer components in the same Kora application
description: "Step-by-step event-driven messaging for a Kora 2.0 service with Apache Kafka: the io.koraframework:kafka artifact and KafkaModule, a generated @KafkaPublisher interface with @KafkaPublisher.Topic pointing at a named topic config section, a @KafkaListener consumer with the defensive event-plus-exception signature, @Json event payloads, the kafka.producer and kafka.consumer configuration sections with driverProperties, and a local Kafka broker through Docker Compose."
agent:
  use_when: "Use this file for questions about publishing and consuming Kafka events from a Kora 2.0 service: io.koraframework:kafka, KafkaModule, @KafkaPublisher and its Topic nested annotation, @KafkaListener and its tag attribute, @Json event serialization, the synchronous and Future / CompletionStage / CompletableFuture / suspend / Deferred publisher signatures, the event-plus-Exception listener signature for deserialization failures, kafka.producer.* and kafka.consumer.* config keys (driverProperties, topics, pollTimeout, threads, offset, backoffTimeout, telemetry), returning 202 Accepted from an async create endpoint, and running a local broker."
tags: kafka, messaging, asynchronous, event-driven, producer, consumer
---

# Обмен сообщениями с Kafka { #messaging-kafka }

В этом руководстве рассматривается событийный обмен сообщениями с Kora и Apache Kafka. Вы узнаете, как продюсеры публикуют доменные события, как потребители обрабатывают эти события асинхронно и
как Kora подключает модуль Kafka, JSON-сериализаторы, конфигурацию и слушателей с управляемым жизненным циклом в граф приложения. Вы также увидите, как HTTP-запрос может передать работу в Kafka, пока
потребитель завершает операцию в фоне.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-messaging-kafka-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-messaging-kafka-app).

## Что вы создадите { #youll-build }

Вы превратите существующий пользовательский API в небольшой событийный поток:

- контроллер будет принимать `POST /users`
- он будет генерировать будущий идентификатор пользователя
- он будет публиковать `UserCreatedEvent` в Kafka
- он будет сразу возвращать `202 Accepted`
- потребитель Kafka в том же приложении получит событие
- этот потребитель создаст пользователя через тот же стек сервиса и репозитория

Остальная часть API ведет себя как в руководстве по HTTP-серверу:

- `GET /users/{userId}`
- `GET /users`
- `PUT /users/{userId}`
- `DELETE /users/{userId}`

Так что главное изменение в этом руководстве — не вся архитектура приложения. Главное изменение в том, что **создание пользователя становится асинхронным**.

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Docker для локальной Kafka и интеграционных тестов
- текстовый редактор или среда разработки
- пройденное руководство [HTTP-сервер](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательно: сначала пройдите руководство по HTTP-серверу"

    Это руководство предполагает, что вы прошли **[HTTP-сервер](http-server.md)** и у вас уже есть `UserController`, `UserService`, `UserRepository`, `InMemoryUserRepository`, `UserRequest` и `UserResponse`.

    Мы сохраним эту знакомую структуру и разовьем ее, а не начнем с нуля.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь меняется поток создания пользователя при сохранении существующего HTTP API и структуры сервиса.

## Обзор { #overview }

Это руководство меняет одну часть HTTP-приложения с синхронного поведения «запрос-ответ» на событийное. Вместо того чтобы завершать создание пользователя внутри HTTP-запроса, контроллер публикует
событие и быстро возвращает ответ. Потребитель получает это событие позже и выполняет саму запись.

Этот сдвиг мал в коде, но важен архитектурно. Он вводит асинхронную работу, конечную согласованность, сериализацию сообщений, обработку у потребителя и необходимость сохранять бизнес-логику
переиспользуемой, когда триггером служит уже не только HTTP-запрос.

### Что такое событийная архитектура? { #event-driven-architecture }

Событийная архитектура — это стиль проектирования, при котором компоненты общаются, публикуя и потребляя события. Событие — это факт или запрос на работу, на который другие части системы могут
отреагировать, а продюсер при этом их напрямую не вызывает.

В синхронном потоке вызывающая сторона ждет, пока завершится каждый шаг:

1. Приходит HTTP-запрос.
2. Контроллер вызывает сервис.
3. Сервис пишет в репозиторий.
4. Ответ возвращается только после завершения записи.

В событийном потоке часть работы уходит за границу сообщений:

1. Приходит HTTP-запрос.
2. Контроллер публикует `UserCreatedEvent`.
3. Ответ возвращается с принятым или будущим идентификатором.
4. Потребитель получает событие.
5. Потребитель вызывает сервис и репозиторий, чтобы завершить запись.

Это значит, что система становится конечно согласованной. Клиент может получить ответ раньше, чем пользователь станет виден через `GET /users/{id}`. Для асинхронных потоков это нормально, но поведение
API, тесты и раздел про неполадки должны говорить об этом прямо.

### Зачем нужны события { #messaging-needed }

События помогают, когда выполнять всю работу внутри одного запроса становится неудобно:

- дорогая работа не должна блокировать запрос, видимый пользователю
- несколько компонентов должны реагировать на одно и то же бизнес-событие
- продюсеры и потребители должны масштабироваться независимо
- временный сбой потребителя не должен всегда ломать точку входа
- всплески трафика нужно буферизовать, а не сразу давить на нижестоящие системы

События — не замена простым вызовам методов по умолчанию. Они добавляют эксплуатационную сложность: брокеры, топики, сериализацию, повторы, обработку дублей, лаг и порядок. Используйте их, когда
развязка или асинхронность стоят этой сложности.

### Что такое Apache Kafka? { #apache-kafka }

[Apache Kafka](https://kafka.apache.org/documentation/) — распределенная платформа потоковой передачи событий. Она хранит события в именованных топиках, позволяет продюсерам дописывать записи в эти
топики, а потребителям читать записи в своем темпе. Kafka часто используют как надежный хребет событийных систем, потому что она рассчитана на высокую пропускную способность, хранение, повторное
чтение и горизонтальное масштабирование.

На практике Kafka дает приложениям надежное место, куда публиковать факты о случившемся, и позволяет другим компонентам отреагировать на эти факты позже.

#### Основные понятия Kafka { #core-kafka-concepts }

- Топик: именованный поток записей
- Продюсер: код приложения, который пишет записи в топик
- Потребитель: код приложения, который читает записи из топика
- Группа потребителей: группа потребителей, делящих работу по топику
- Брокер: сервер Kafka, который хранит данные топика и обслуживает продюсеров и потребителей
- Ключ и значение записи: данные, отправляемые в Kafka, часто сериализованные из типизированных объектов приложения

Kafka не заменяет базу данных. Основное состояние приложения по-прежнему принадлежит слою базы или репозитория. Kafka — транспорт, переносящий бизнес-события между компонентами и сервисами.

### События в сервисах { #messaging-services }

В микросервисных архитектурах события часто работают как слой координации между независимо развертываемыми компонентами. Вместо того чтобы один сервис знал каждый нижестоящий API и ждал каждый ответ,
он может публиковать события, которые потребляют другие сервисы.

Распространенные шаблоны:

- Publish-subscribe: одно событие может быть потреблено одним или многими подписчиками
- Event sourcing: состояние приложения восстанавливается из сохраненных событий
- CQRS: изменения на стороне записи публикуют события, обновляющие одну или несколько моделей чтения
- Saga: распределенные рабочие процессы координируются последовательностью событий

Это руководство использует минимально полезную версию этой идеи. Продюсер и потребитель живут в одном приложении, чтобы сосредоточиться на модели обмена сообщениями до разделения потока между
несколькими сервисами.

### Kafka и Kora { #kora-kafka }

Модуль Kafka в Kora подключает продюсеров и потребителей в граф приложения. Конфигурация описывает брокеров, топики, группы потребителей и сериализацию. JSON-сериализаторы сохраняют типизированность
полезной нагрузки событий, а потребители с управляемым жизненным циклом стартуют вместе с приложением и обрабатывают записи в фоне.

Важная граница остается той же, что и в руководстве по HTTP:

- контроллер обрабатывает HTTP-вход и публикует событие
- продюсер — исходящий адаптер сообщений
- потребитель — входящий адаптер сообщений
- сервис по-прежнему владеет поведением приложения
- репозиторий по-прежнему владеет хранением

Практический порядок такой:

1. добавить модуль Kafka и зависимости
2. ввести `UserCreatedEvent`
3. публиковать событие из `createUser()`
4. добавить потребителя Kafka для этого события
5. вернуть работу потребителя в сервис и репозиторий
6. настроить Kafka для локальной разработки и тестов

## Зависимости { #dependencies }

Сначала добавьте поддержку Kafka в проект, который вы уже собрали в руководстве по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    Добавьте эти зависимости в `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:kafka")
        implementation("io.koraframework:json-common")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте эти зависимости в `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:kafka")
        implementation("io.koraframework:json-common")
    }
    ```

Поддержка Kafka в Kora приходит из единственного артефакта `kafka`, который приносит с собой клиент Apache Kafka (`4.3.1` в Kora `2.0.0.RC1`). Поддержка JSON важна, потому что мы хотим отправлять
структурированные объекты событий, а не сырые строки, а генератор кода и для продюсера, и для слушателя уже живет в подключенном вами артефакте `annotation-processors` / `symbol-processors`.

## Модули { #modules }

Теперь расширьте приложение поддержкой Kafka.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/messaging/kafka/Application.java"
    package io.koraframework.guide.messaging.kafka;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.kafka.common.KafkaModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowPublicHttpServerModule,
            JsonModule,
            KafkaModule,  // <----- Connected module
            LogbackModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/messaging/kafka/Application.kt"
    package io.koraframework.guide.messaging.kafka

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.kafka.common.KafkaModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule,
        KafkaModule,  // <----- Connected module
        LogbackModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`KafkaModule` наследует `KafkaDeserializersModule` и `KafkaSerializersModule` и добавляет фабрики телеметрии продюсера и потребителя. На этом этапе еще ничего не публикуется и не потребляется. Мы лишь
включаем модуль фреймворка, который сгенерирует нам компоненты продюсера и потребителя.

## События { #events }

В руководстве по HTTP-серверу `createUser()` сразу возвращал созданного пользователя, потому что запись происходила в том же запросе.

Здесь нам нужен другой контракт:

- контроллер принимает запрос
- он генерирует будущий идентификатор
- он публикует событие
- он сразу возвращает этот идентификатор

Значит, нужны два новых DTO:

- `UserCreatedEvent` для Kafka
- `UserAcceptedResponse` для HTTP-ответа

Это не только изменение DTO. Это еще и изменение того, как приложение думает о работе.

В синхронном CRUD-приложении поток запроса обычно выполняет все до возврата HTTP-ответа. Часто это хорошая отправная точка, но она становится куда менее привлекательной, когда создание пользователя
требует еще и других медленных или хрупких операций, например:

- вызова внешних провайдеров идентификации
- подготовки данных на другой платформе
- отправки писем или уведомлений
- обновления поисковых индексов
- отправки данных в аналитические системы
- запуска рабочих процессов в других сервисах

Если все это происходит внутри запроса, эндпоинт становится медленнее и хрупче. Одна медленная нижестоящая интеграция может заставить пользователя ждать гораздо дольше ожидаемого, а сбой в одной
зависимости — сломать весь путь запроса.

Публикация события и его обработка позже могут быть лучшим решением, потому что:

- HTTP-запрос завершается быстро
- долгая работа уходит из потока запроса
- обработка может падать и повторяться независимо
- логика обработки позже может переехать в другое приложение без изменения контракта события

Именно это мы и моделируем в этом руководстве.

Для простоты продюсер и потребитель по-прежнему живут в одном приложении. Концептуально стоит воспринимать это как небольшую симуляцию более крупной событийной системы:

- контроллер принимает команду
- Kafka переносит событие
- потребитель позже выполняет саму работу по созданию

Так что хотя в руководстве и одно приложение, архитектура здесь того же рода, какую команды используют, когда один сервис публикует событие, а другой его потребляет.

Добавьте `UserCreatedEvent`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/messaging/kafka/kafka/UserCreatedEvent.java"
    @Json
    public record UserCreatedEvent(
            String id,
            String name,
            String email,
            LocalDateTime createdAt
    ) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/messaging/kafka/kafka/UserCreatedEvent.kt"
    @Json
    data class UserCreatedEvent(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

Это полезная нагрузка, которую Kafka перенесет от продюсера к потребителю. `@Json` генерирует для нее читатель и писатель на этапе компиляции, и оба — и публикующий клиент, и слушатель — берут их из
графа.

Добавьте `UserAcceptedResponse`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/messaging/kafka/dto/UserAcceptedResponse.java"
    @Json
    public record UserAcceptedResponse(String id) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/messaging/kafka/dto/UserAcceptedResponse.kt"
    @Json
    data class UserAcceptedResponse(val id: String)
    ```

Возврат только будущего идентификатора важен для повествования: он делает асинхронный контракт видимым читателю — пользователь не гарантированно существует в тот самый момент, когда `POST /users`
возвращает ответ.

## Продюсер { #kafka-producer }

Подробности о генерируемых продюсерах Kafka, настройке топиков и обработке ошибок — в разделе [Продюсер](../documentation/kafka.md#producer).

Теперь нам нужен компонент продюсера, способный публиковать `UserCreatedEvent`.

Kora генерирует реализации продюсеров из размеченных интерфейсов, так что мы объявляем только контракт.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/messaging/kafka/kafka/UserCreatedPublisher.java"
    package io.koraframework.guide.messaging.kafka.kafka;

    import io.koraframework.json.common.annotation.Json;
    import io.koraframework.kafka.common.annotation.KafkaPublisher;
    import io.koraframework.kafka.common.annotation.KafkaPublisher.Topic;

    @KafkaPublisher("kafka.producer.user-created")
    public interface UserCreatedPublisher {

        @Topic("kafka.producer.user-created-topic")
        void send(@Json UserCreatedEvent event);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/messaging/kafka/kafka/UserCreatedPublisher.kt"
    package io.koraframework.guide.messaging.kafka.kafka

    import io.koraframework.json.common.annotation.Json
    import io.koraframework.kafka.common.annotation.KafkaPublisher
    import io.koraframework.kafka.common.annotation.KafkaPublisher.Topic

    @KafkaPublisher("kafka.producer.user-created")
    interface UserCreatedPublisher {

        @Topic("kafka.producer.user-created-topic")
        fun send(@Json event: UserCreatedEvent)
    }
    ```

Что здесь происходит:

- `@KafkaPublisher(...)` велит Kora сгенерировать компонент продюсера Kafka, а его значение — путь конфигурации с `driverProperties` этого продюсера
- `@Topic(...)` указывает на **отдельную** именованную секцию конфигурации, содержащую ключ `topic`, а не на само имя топика
- `@Json` велит Kora сериализовать событие в JSON перед отправкой в Kafka

Такое разделение на два пути сделано намеренно: несколько методов публикации могут делить одно соединение продюсера, при этом каждый пишет в свою секцию топика.

По духу это близко к HTTP-клиентам Kora: вы описываете контракт, а Kora генерирует реализацию.

Возврат `void` выше — самая простая форма и правильное значение по умолчанию для этого руководства, потому что он блокирует до подтверждения записи брокером. Когда подтверждение нужно без блокировки,
метод публикации может вместо этого возвращать `Future<RecordMetadata>`, `CompletionStage<RecordMetadata>` или `CompletableFuture<RecordMetadata>`, а в Kotlin быть `suspend fun` или возвращать
`Deferred<RecordMetadata>`. Это не пережитки реактивного прошлого — это поддерживаемый способ совмещать публикацию с другой работой. Полный список — в
[Сигнатурах продюсера](../documentation/kafka.md#signatures-producer).

### Публикация события { #publish-events }

Это самый важный шаг в руководстве.

В руководстве по HTTP-серверу `createUser()` делегировал сервису и сразу писал в репозиторий. Теперь мы изменим только эту часть контроллера. Остальные HTTP-операции по-прежнему близки к исходному
CRUD-примеру.

Обновите только зависимости конструктора и метод `createUser()`. Остальные эндпоинты остаются такими же, как в руководстве по HTTP-серверу, поэтому мы их здесь не повторяем.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/messaging/kafka/controller/UserController.java"
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

    ```kotlin title="src/main/kotlin/io/koraframework/guide/messaging/kafka/controller/UserController.kt"
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

- `createUser()` больше не сохраняет напрямую
- контроллер теперь играет роль точки входа для команды
- он возвращает `202 Accepted` вместо `201 Created`
- возвращаемый идентификатор — это идентификатор, который будущий пользователь получит после обработки события

Именно поэтому это руководство — хорошее введение в обмен сообщениями. То же бизнес-действие никуда не делось, но меняется момент его выполнения.

## Слой сервиса { #service-layer }

Мы по-прежнему хотим, чтобы пример ощущался продолжением руководства по HTTP-серверу, поэтому сохраняем те же слои:

- контроллер
- сервис
- репозиторий

Разница только в том, что создание пользователя теперь входит в систему через Kafka.

Поскольку потребитель получает полностью подготовленное событие с идентификатором и меткой времени, репозиторий сохраняет готовый объект `UserResponse`, а не генерирует идентификатор сам.

И снова мы показываем только те части, которые действительно изменились по сравнению с руководством по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/messaging/kafka/repository/UserRepository.java"
    public interface UserRepository {

        void save(UserResponse user);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/messaging/kafka/repository/UserRepository.kt"
    interface UserRepository {

        fun save(user: UserResponse)
    }
    ```

Репозиторий в памяти меняется только в методе `save(...)`, потому что теперь он хранит полностью подготовленный объект пользователя:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/messaging/kafka/repository/InMemoryUserRepository.java"
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

    ```kotlin title="src/main/kotlin/io/koraframework/guide/messaging/kafka/repository/InMemoryUserRepository.kt"
    @Component
    class InMemoryUserRepository : UserRepository {

        private val users = ConcurrentHashMap<String, UserResponse>()

        override fun save(user: UserResponse) {
            users[user.id] = user
        }
    }
    ```

Сервис тоже меняется только там, где потребителю Kafka нужна новая точка входа. Все остальное в классе остается таким же, как в руководстве по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/messaging/kafka/service/UserService.java"
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

    ```kotlin title="src/main/kotlin/io/koraframework/guide/messaging/kafka/service/UserService.kt"
    @Component
    class UserService(
        private val userRepository: UserRepository
    ) {

        fun createUser(event: UserCreatedEvent) {
            userRepository.save(UserResponse(event.id, event.name, event.email, event.createdAt))
        }
    }
    ```

Это удерживает руководство на земле. Читатель по-прежнему работает с теми же идеями `UserService` и `UserRepository`, которые уже изучил в руководстве по HTTP-серверу.

## Потребитель { #kafka-consumer }

Подробнее о `@KafkaListener`, стратегиях подписки, десериализации и сбоях — в разделах [Стратегия потребления](../documentation/kafka.md#consume-strategy), [Десериализация](../documentation/kafka.md#deserialization) и [Обработка исключений](../documentation/kafka.md#exception-handling).

Теперь можно подключить вторую сторону потока.

Продюсер уже публикует `UserCreatedEvent`. Потребитель будет слушать этот топик и делегировать обратно в слой сервиса.

Поначалу слушатель Kafka может выглядеть вот так просто:

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

### Обработка событий { #events-processing }

Для реальных приложений часто полезно получать и возможную ошибку десериализации или отображения. Это и есть итоговая форма, используемая в руководстве:

Здесь мы снова показываем только сам класс потребителя, потому что именно он вводится на этом шаге.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/messaging/kafka/kafka/UserCreatedConsumer.java"
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

    ```kotlin title="src/main/kotlin/io/koraframework/guide/messaging/kafka/kafka/UserCreatedConsumer.kt"
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

- если десериализация не удалась, Kora может передать ошибку в ваш слушатель
- ваш бизнес-код может отделить «корректное событие» от «сообщение не удалось прочитать»
- руководство может показать и простую форму, и более защищенную промышленную

Обратите внимание на допустимость `null` в обоих языках. Параметр события должен принимать `null`, потому что запись, тело которой не удалось прочитать, приходит вместе с исключением вместо значения. В
Java это `@Nullable`; в Kotlin — `UserCreatedEvent?`. Объявление здесь непустого параметра в Kotlin — ошибка компиляции, а не сюрприз во время выполнения.

Та же допустимость `null` всплывает, если вы когда-нибудь напишете `Deserializer` для Kafka вручную: `JsonReader.read(...)` объявлен как `@Nullable`, поэтому Kotlin видит `T?`, и десериализатор с
непустым возвращаемым типом обязан сузить его через `requireNotNull(...)`. Смотрите [Собственный десериализатор](../documentation/kafka.md#custom-deserializer).

Это еще и приятная симметрия с руководствами по HTTP: контроллер по-прежнему точка входа для HTTP-команды, но теперь потребитель становится точкой входа для асинхронной стадии обработки.

## Конфигурация { #configuration }

Теперь свяжите продюсера и потребителя одним топиком.

Полный справочник по конфигурации смотрите в [HTTP-сервере](../documentation/http-server.md), [Kafka](../documentation/kafka.md) и [Логировании SLF4J](../documentation/logging-slf4j.md).

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

    1. Адреса брокеров Kafka, передаваемые напрямую продюсеру Apache Kafka. Необязательное переопределение из `KAFKA_BOOTSTRAP`.
    2. Логирует каждую опубликованную запись, пока вы изучаете поток.
    3. Секция топика, на которую ссылается `@Topic("kafka.producer.user-created-topic")`.
    4. Топики, на которые подписывается этот слушатель.
    5. Сколько каждый вызов `poll` ждет записи. По умолчанию `5s`.
    6. Адреса брокеров Kafka, передаваемые напрямую потребителю Apache Kafka. Необязательное переопределение из `KAFKA_BOOTSTRAP`.
    7. Группа потребителей, к которой присоединяется этот слушатель.
    8. Начинать с самого раннего смещения, когда у группы нет зафиксированной позиции.
    9. Позволить драйверу фиксировать смещения автоматически.
    10. Логирует каждую потребленную запись, пока вы изучаете поток.

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

    1. Адреса брокеров Kafka, передаваемые напрямую продюсеру Apache Kafka. Необязательное переопределение из `KAFKA_BOOTSTRAP`.
    2. Логирует каждую опубликованную запись, пока вы изучаете поток.
    3. Секция топика, на которую ссылается `@Topic("kafka.producer.user-created-topic")`.
    4. Топики, на которые подписывается этот слушатель.
    5. Сколько каждый вызов `poll` ждет записи. По умолчанию `5s`.
    6. Адреса брокеров Kafka, передаваемые напрямую потребителю Apache Kafka. Необязательное переопределение из `KAFKA_BOOTSTRAP`.
    7. Группа потребителей, к которой присоединяется этот слушатель.
    8. Начинать с самого раннего смещения, когда у группы нет зафиксированной позиции.
    9. Позволить драйверу фиксировать смещения автоматически.
    10. Логирует каждую потребленную запись, пока вы изучаете поток.

Что делает эта конфигурация:

- определяет одного продюсера с именем `user-created`
- определяет отдельную секцию `user-created-topic`, содержащую только имя топика
- определяет одного потребителя с именем `user-created`
- направляет обоих в один и тот же топик Kafka
- включает простую телеметрию логирования, чтобы вы видели поток во время обучения

`driverProperties` — сквозная передача в клиент Apache Kafka, поэтому все, что понимает драйвер, живет там под своим нативным ключом. Все за пределами этого блока принадлежит самой Kora: помимо
`topics` и `pollTimeout`, слушатель принимает еще `threads`, `offset`, `backoffTimeout`, `partitionRefreshInterval`, `shutdownWait` и `allowEmptyRecords`.

## Docker Compose { #docker-compose }

Для локальной разработки запустите Kafka через Docker.

Создайте `docker-compose.yml` в каталоге модуля приложения:

```yaml title="docker-compose.yml"
services:
  kafka:
    image: apache/kafka-native:4.3.1
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

Именно `KAFKA_AUTO_CREATE_TOPICS_ENABLE` позволяет `user-created-events` появиться при первой публикации, так что руководству не нужен отдельный шаг создания топика. В любой реальной среде выключите
это и создавайте топики осознанно.

## Запуск приложения { #run-app }

Запустите Kafka:

```bash
docker compose up -d kafka
```

Затем запустите приложение:

```bash
KAFKA_BOOTSTRAP=localhost:9092 ./gradlew run
```

## Проверка приложения { #check-app }

Создайте пользователя:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Вы должны получить ответ вроде такого:

```json
{
    "id": "9f6f1d43-8e2c-41ce-a7c1-f1d4d92a7982"
}
```

Обратите внимание, что произошло:

- HTTP-запрос вернулся сразу
- в ответе нет всего созданного пользователя
- идентификатор пользователя уже известен
- реальная запись происходит, когда потребитель Kafka обработает событие

Теперь запросите пользователя:

```bash
curl http://localhost:8080/users/9f6f1d43-8e2c-41ce-a7c1-f1d4d92a7982
```

В зависимости от таймингов может пройти короткая пауза, прежде чем пользователь станет виден. Эта пауза и есть смысл руководства: конвейер создания теперь асинхронный.

## Лучшие практики { #best-practices }

- Держите DTO событий сосредоточенными на бизнес-смысле. `UserCreatedEvent` должен представлять факт, а не форму HTTP-запроса.
- Относитесь к коду потребителя как к еще одной границе приложения. Аккуратно проверяйте и логируйте.
- Всегда принимайте допускающее `null` событие плюс `Exception` в слушателях, которые должны переживать плохие полезные нагрузки, вместо того чтобы сбой десериализации застопорил партицию.
- По возможности делайте потребителей идемпотентными. В реальных системах одно и то же событие может быть доставлено более одного раза.
- Держите HTTP-контракт честным. Вернуть `202 Accepted` лучше, чем делать вид, что запись уже завершилась.
- Начинайте с блокирующего `void`-продюсера и переходите к сигнатуре с `CompletionStage` или `suspend` только тогда, когда вызывающей стороне действительно есть чем занять время отправки.
- Переиспользуйте существующие слои сервиса и репозитория, когда это упрощает дизайн. Kafka должна менять поток, а не заставлять переписывать лишнее.

## Итоги { #summary }

Вы расширили руководство по HTTP-серверу первым событийным рабочим процессом:

- `POST /users` теперь публикует `UserCreatedEvent`
- контроллер возвращает `202 Accepted` с будущим идентификатором пользователя
- потребитель Kafka получает это событие
- потребитель создает пользователя через `UserService`
- остальная часть CRUD API по-прежнему выглядит знакомо

Это делает руководство мягким введением в асинхронный обмен сообщениями. Приложение по-прежнему ощущается тем же CRUD-сервисом, но одна важная операция теперь происходит через Kafka.

## Ключевые понятия { #key-concepts }

- Kafka позволяет вынести работу из пути HTTP-запроса
- продюсеры публикуют события, потребители обрабатывают их позже
- `202 Accepted` — естественный HTTP-статус для асинхронного создания
- Kora генерирует продюсеров Kafka из интерфейсов с `@KafkaPublisher`, а значение `@Topic` — это путь конфигурации, а не имя топика
- методы публикации могут быть блокирующими или возвращать `Future`, `CompletionStage`, `CompletableFuture`, а в Kotlin быть `suspend` или возвращать `Deferred`
- слушатели Kafka могут развиваться от простой сигнатуры только с событием до более защищенной формы `событие + исключение`
- событийная архитектура может строиться поверх тех же слоев сервиса и репозитория, которые вы уже знаете

## Устранение неполадок { #troubleshooting }

**`POST /users` возвращает идентификатор, а `GET /users/{id}` по-прежнему отдает 404:**

Обычно это значит, что событие опубликовано, но еще не потреблено, либо потребитель не смог его обработать.

Проверьте:

- Kafka запущена
- имя топика одинаково у продюсера и потребителя
- в логах приложения видно, что потребитель обрабатывает событие

**Потребитель никогда не получает событие:**

Проверьте:

- `kafka.producer.user-created-topic.topic`
- `kafka.consumer.user-created.topics`
- `KAFKA_BOOTSTRAP`

И продюсер, и потребитель должны указывать на один брокер и один топик.

**Сборка графа падает на пути `@Topic`:**

Значение `@Topic` — это путь конфигурации, в секции которого лежит ключ `topic`. Указание на само имя топика или на секцию продюсера не разрешится.

**Ошибки десериализации у потребителя:**

Если JSON не удается прочитать корректно, слушатель может получить `exception != null`.

Именно поэтому итоговая сигнатура потребителя в этом руководстве принимает и то и другое:

- `@Json @Nullable UserCreatedEvent event`
- `@Nullable Exception exception`

Это дает вам место, где явно логировать сбои отображения или реагировать на них.

**Kotlin отвергает сигнатуру слушателя:**

Параметр события обязан допускать `null` (`UserCreatedEvent?`), когда слушатель также объявляет параметр `Exception?`, потому что запись, которую не удалось десериализовать, приходит без значения.

## Что дальше? { #whats-next }

- [Шаблоны отказоустойчивости](resilient.md), чтобы добавить повторы, прерыватели и резервные методы вокруг операций публикации и потребления событий.
- [Наблюдаемость](observability.md), чтобы следить за продюсерами, потребителями, чувствительным к лагу поведением и асинхронными сбоями.
- [Кеширование](cache.md), когда событийным записям нужны быстрые пути чтения.
- [База данных JDBC](database-jdbc.md) перед черноящичным тестированием, если нужен сквозной путь тестов поверх JDBC.

## Помощь { #help }

Если возникнут сложности:

- сравните с [Kora Java Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-messaging-kafka-app) и [Kora Kotlin Messaging Kafka App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-messaging-kafka-app)
- перечитайте [HTTP-сервер](http-server.md) про синхронную базовую линию API
- посмотрите [документацию по Kafka](../documentation/kafka.md)
- посмотрите [документацию по JSON](../documentation/json.md) про отображение полезной нагрузки событий
