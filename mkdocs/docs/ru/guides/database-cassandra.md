---
search:
  exclude: true
title: Интеграция базы данных Cassandra с Kora
summary: Learn how to integrate Cassandra-compatible storage with Kora and perform CRUD operations
tags: database, cassandra, scylla, cql, crud, persistence
---

# Интеграция базы данных Cassandra с Kora { #cassandra-database-integration-kora }

В этом руководстве рассматривается хранение данных в Cassandra-совместимом хранилище с Kora. Вы узнаете, как интерфейсы репозиториев используют `@Repository` и `@Query`, как записи DAO сопоставляются
со строками CQL, как конфигурация Cassandra создает сеанс в графе приложения и как тот же вид HTTP API может использовать распределенную ширококолоночную базу данных вместо хранения в памяти.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Database Cassandra App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-cassandra-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Database Cassandra App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-cassandra-app).

## Что вы создадите { #youll-build }

Вы превратите пользовательский HTTP API в приложение с хранением данных в Cassandra:

- CQL-схему, которая создает таблицу `users`
- DAO-модель Cassandra с `@EntityCassandra` и явным сопоставлением столбцов
- интерфейс Kora `@Repository` с CQL-запросами для операций создания, чтения, получения списка, обновления и удаления
- сервисную логику, которая сохраняет поведение из HTTP-руководства, но учитывает семантику изменений Cassandra
- HOCON-конфигурацию для точек подключения Cassandra, центра данных, пространства ключей и учетных данных
- тесты со Scylla Testcontainers, которые проверяют хранение данных на Cassandra-совместимой базе данных

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Cassandra-совместимая база данных, например [Apache Cassandra](https://cassandra.apache.org/_/index.html) или [ScyllaDB](https://www.scylladb.com/)
- Docker для интеграционных тестов
- Gradle 7+
- текстовый редактор или среда разработки
- пройденное руководство [HTTP-сервер](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по HTTP-серверу"

    Это руководство предполагает, что вы уже прошли руководство **[HTTP-сервер](http-server.md)** и у вас есть рабочий проект HTTP API с `UserController`, `UserService` и реализацией репозитория в памяти.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь хранение данных в памяти заменяется Cassandra-совместимым хранилищем.

## Обзор { #overview }

Переход от хранения в памяти к [Apache Cassandra](https://cassandra.apache.org/doc/latest/) меняет слой хранения данных, но не меняет публичный контракт HTTP API. Контроллер по-прежнему может
предоставлять `/users`, сервис по-прежнему может возвращать `UserResponse`, а граница репозитория становится местом, где операции приложения переводятся в CQL.

Cassandra не является реляционной базой данных с SQL-соединениями, внешними ключами, последовательностями и счетчиками обновленных строк. Это распределенная ширококолоночная база данных,
спроектированная вокруг секционированных шаблонов доступа, высокой пропускной способности записи, настраиваемой согласованности и горизонтального масштабирования. Поэтому руководству не является
механическим переписыванием JDBC. Оно сохраняет ту же учебную цель в форме CRUD, но адаптирует реализацию к правилам Cassandra.

### Как хранение меняет приложение { #persistence-changes-application }

Репозиторий в памяти полезен при изучении HTTP-контроллеров, но он исчезает при перезапуске, не может совместно использоваться несколькими экземплярами приложения и не проверяет поведение настоящего
хранилища.

Приложение с базой данных добавляет новые задачи:

- записи должны переживать перезапуски приложения
- схема должна быть создана до запуска репозиториев
- запросы должны соответствовать модели доступа базы данных
- конфигурация должна указывать на разные кластеры в локальной, тестовой и развернутой средах
- тесты должны проверять реальное поведение драйвера, запросов и сопоставления

Это руководство вводит полную границу хранения данных: схему таблицы, конфигурацию сеанса Cassandra, CQL репозитория, сгенерированную реализацию репозитория, сопоставление строк и тесты на основе
контейнеров.

### Cassandra как источник истины { #cassandra-source-truth }

В этом руководстве Cassandra становится источником истины для пользовательских данных. Репозиторий больше не хранит пользователей в локальной карте; он читает и записывает строки в таблицу `users`.

Моделирование данных в Cassandra начинается с шаблонов запросов. Таблица обычно проектируется под чтения и записи, которые нужны сервису, а не под нормализованный граф сущностей. В этом руководстве
таблица намеренно остается небольшой:

- `id` является ключом секции
- `name`, `email` и `created_at` являются обычными столбцами
- чтение по идентификатор является прямым чтением секции
- получение списка пользователей допустимо для учебного руководства, но в промышленной системе его нужно проектировать вокруг ограниченного шаблона запроса

Последний пункт важен. `SELECT ... FROM users` удобен в небольшой учебной таблице, но промышленные системы Cassandra обычно избегают неограниченного сканирования таблиц.

### Репозитории Cassandra { #cassandra-repositories }

[CQL](https://cassandra.apache.org/doc/latest/cassandra/developing/cql/) — это язык запросов Cassandra. Он выглядит знакомо, если вы знаете SQL, но следует модели хранения Cassandra. Репозитории
Cassandra в Kora оставляют CQL явным и при этом генерируют шаблонный код драйвера.

Вы объявляете интерфейс репозитория, помечаете методы аннотацией `@Query`, а Kora генерирует реализацию, которая:

- подготавливает CQL-выражения
- связывает именованные параметры с позиционными параметрами драйвера
- выполняет выражения через настроенный сеанс Cassandra
- применяет телеметрию вокруг каждого запроса
- сопоставляет строки с записями Java или классами данных Kotlin

Явный CQL остается видимым при проверке кода, а повторяющийся код драйвера генерируется.

### Сущности и сопоставление строк { #dao-models }

HTTP DTO и строки базы данных должны оставаться раздельными. `UserRequest` и `UserResponse` описывают вход и выход API. `UserDAO` описывает форму строки базы данных.

Поскольку `UserRequest` и `UserResponse` по-прежнему являются HTTP JSON DTO, приложение сохраняет `@Json` на этих классах. Сопоставление Cassandra относится к `UserDAO`; сопоставление JSON относится к
DTO запроса и ответа, которые образуют границу API.

Kora сопоставляет строки Cassandra с типизированными записями Java. `@EntityCassandra` просит Kora сгенерировать преобразователи Cassandra напрямую для DAO-модели, а `@Column` делает имя каждого CQL-столбца
явным. Это полезно, когда в Java используется `createdAt`, а в таблице — `created_at`.

В этом руководстве для `created_at` используется `Instant`, потому что тип Cassandra `timestamp` естественно сопоставляется с мгновением времени.

### Семантика изменений Cassandra { #cassandra-mutation-semantics }

JDBC-обновления часто возвращают число затронутых строк. Записи в Cassandra устроены иначе: `INSERT`, `UPDATE` и `DELETE` являются изменениями и не ведут себя естественно как SQL-операции с
количеством обновленных строк.

Чтобы сохранить поведение HTTP API из предыдущего руководства, сервис проверяет существование через `findById(...)` перед `update` и `delete`. Так API все еще может возвращать `404` для отсутствующих
пользователей, а методы репозитория остаются идиоматичными изменениями Cassandra.

В настоящей системе можно выбрать другой подход:

- принять идемпотентные удаления
- использовать легковесные транзакции для условных записей, когда цена согласованности оправдана
- смоделировать команды так, чтобы клиент уже знал, является ли отсутствие ошибкой

Руководство сохраняет знакомое поведение, чтобы различия хранилища было проще увидеть.

### Конфигурация запуска { #runtime-config }

Kora подключает Cassandra через `CassandraDatabaseModule`. Граф приложения владеет настроенным сеансом, репозитории зависят от него, а тесты переопределяют точки подключения и значения пространства
ключей с помощью Scylla Testcontainers.

Основные настройки:

- точки подключения: куда подключается драйвер
- центр данных: локальный ЦД, который использует политика балансировки нагрузки
- пространство ключей: логическое пространство имен для таблиц
- учетные данные: имя пользователя и пароль, когда включена авторизация
- время ожидания запроса: максимальное время одной попытки запроса

Хранение этих значений вне кода позволяет запускать одно и то же приложение с локальной Scylla, тестовыми контейнерами, подготовительным кластером Cassandra или промышленными кластерами.

### Тестирование хранения { #persistence-testing }

Заглушки не могут доказать, что синтаксис CQL верен, что таблица существует или что сгенерированный преобразователь Cassandra читает нужные столбцы.

Практический путь выглядит так:

1. добавить зависимости Cassandra и Scylla Testcontainers
2. добавить `CassandraDatabaseModule` в приложение Kora
3. определить таблицу `users` в CQL
4. определить Cassandra DAO с `@EntityCassandra`
5. создать репозиторий Cassandra в Kora с CQL-запросами
6. переработать сервис для использования хранения данных в Cassandra
7. проверить поведение репозитория со Scylla Testcontainers

## Зависимости { #dependencies }

Добавьте поддержку Cassandra и зависимости Scylla Testcontainers для проверки.

===! ":fontawesome-brands-java: `Java`"

    Добавьте в блок `dependencies` файла `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:database-cassandra")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в блок `dependencies` файла `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:database-cassandra")
    }
    ```

## Модули { #modules }

Обновите интерфейс Application и подключите модуль Cassandra.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasecassandra/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.databasecassandra;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.database.cassandra.CassandraDatabaseModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            CassandraDatabaseModule,  // <----- Подключили модуль
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/databasecassandra/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasecassandra

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.database.cassandra.CassandraDatabaseModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        CassandraDatabaseModule,  // <----- Подключили модуль
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Сущность БД { #entity-db }

Замените старую модель хранения в памяти на Cassandra DAO-модель, которую используют сопоставления репозитория.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasecassandra/repository/UserDAO.java`:

    ```java
    package ru.tinkoff.kora.guide.databasecassandra.repository;

    import java.time.Instant;
    import ru.tinkoff.kora.database.cassandra.annotation.EntityCassandra;
    import ru.tinkoff.kora.database.common.annotation.Column;
    import ru.tinkoff.kora.database.common.annotation.Table;

    @EntityCassandra
    @Table("users")
    public record UserDAO(
            @Column("id") String id,
            @Column("name") String name,
            @Column("email") String email,
            @Column("created_at") Instant createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/databasecassandra/repository/UserDAO.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasecassandra.repository

    import java.time.Instant
    import ru.tinkoff.kora.database.cassandra.annotation.EntityCassandra
    import ru.tinkoff.kora.database.common.annotation.Column
    import ru.tinkoff.kora.database.common.annotation.Table

    @EntityCassandra
    @Table("users")
    data class UserDAO(
        @field:Column("id") val id: String,
        @field:Column("name") val name: String,
        @field:Column("email") val email: String,
        @field:Column("created_at") val createdAt: Instant,
    )
    ```

`@EntityCassandra` говорит Kora сгенерировать преобразователи строк и наборов результатов Cassandra напрямую для этого DAO. Так генерация преобразователей остается явной и не появляются более медленные поздние раунды
генерации, когда граф репозитория впервые запрашивает преобразователь.

## Репозиторий { #repository }

Удалите старый `InMemoryUserRepository` из руководства по HTTP-серверу и создайте репозиторий Cassandra с CQL-запросами.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasecassandra/repository/UserRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.databasecassandra.repository;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.database.cassandra.CassandraRepository;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;

    @Repository
    public interface UserRepository extends CassandraRepository {

        @Query("SELECT id, name, email, created_at FROM users")
        List<UserDAO> findAll();

        @Query("SELECT id, name, email, created_at FROM users WHERE id = :id")
        @Nullable
        UserDAO findById(String id);

        @Query("""
                INSERT INTO users(id, name, email, created_at)
                VALUES (:user.id, :user.name, :user.email, :user.createdAt)
                """)
        void save(UserDAO user);

        @Query("""
                UPDATE users
                SET name = :user.name, email = :user.email, created_at = :user.createdAt
                WHERE id = :user.id
                """)
        void update(UserDAO user);

        @Query("DELETE FROM users WHERE id = :id")
        void deleteById(String id);
    }
    ```

После компиляции Kora генерирует реализацию репозитория и преобразователи:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-database-cassandra-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasecassandra/repository/$UserRepository_Impl.java
    guides/guide-database-cassandra-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasecassandra/repository/$UserDAO_CassandraRowMapper.java
    guides/guide-database-cassandra-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasecassandra/repository/$UserDAO_ListCassandraResultSetMapper.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-database-cassandra-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasecassandra/repository/$UserRepository_Impl.kt
    guides/kotlin/guide-kotlin-database-cassandra-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasecassandra/repository/$UserDAO_CassandraRowMapper.kt
    guides/kotlin/guide-kotlin-database-cassandra-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasecassandra/repository/$UserDAO_ListCassandraResultSetMapper.kt
    ```

Этот сокращенный фрагмент сгенерированного репозитория показывает, как именованные CQL-параметры становятся параметрами выражения драйвера DataStax:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static final QueryContext QUERY_CONTEXT_3 = new QueryContext(
          "INSERT INTO users(id, name, email, created_at)\n"
        + "VALUES (:user.id, :user.name, :user.email, :user.createdAt)\n",
          "INSERT INTO users(id, name, email, created_at)\n"
        + "VALUES (?, ?, ?, ?)\n",
          "UserRepository.save"
        );

    @Override
    public void save(UserDAO user) {
        var _query = QUERY_CONTEXT_3;
        var _ctxCurrent = Context.current();
        var _telemetry = this._connectionFactory.telemetry().createContext(_ctxCurrent, _query);
        var _session = this._connectionFactory.currentSession();
        var _stmt = _session.prepare(_query.sql()).boundStatementBuilder();
        _stmt.setString(0, user.id());
        _stmt.setString(1, user.name());
        _stmt.setString(2, user.email());
        _stmt.setInstant(3, user.createdAt());
        var _s = _stmt.build();
        try {
            var _rs = _session.execute(_s);
            _telemetry.close(null);
        } catch (Exception _e) {
            _telemetry.close(_e);
            throw _e;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val _queryContext_3: QueryContext = QueryContext(
      "INSERT INTO users(id, name, email, created_at) VALUES (:user.id, :user.name, :user.email, :user.createdAt)",
      "INSERT INTO users(id, name, email, created_at) VALUES (?, ?, ?, ?)",
      "UserRepository.save"
    )

    override fun save(user: UserDAO) {
      val _query = _queryContext_3
      val _ctxCurrent = Context.current()
      val _telemetry = this._cassandraConnectionFactory.telemetry().createContext(_ctxCurrent, _query)
      val _session = this._cassandraConnectionFactory.currentSession()
      var _stmt = _session.prepare(_query.sql()).boundStatementBuilder()
      _stmt.setString(0, user.id)
      _stmt.setString(1, user.name)
      _stmt.setString(2, user.email)
      _stmt.setInstant(3, user.createdAt)
      val _s = _stmt.build()
      try {
        _session.execute(_s)
        _telemetry.close(null)
      } catch (_e: Exception) {
        _telemetry.close(_e)
        throw _e
      }
    }
    ```

Этот сокращенный фрагмент сгенерированного преобразователя строк также показывает, почему явные имена столбцов важны:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var _idx_id = _row.firstIndexOf("id");
    var _idx_name = _row.firstIndexOf("name");
    var _idx_email = _row.firstIndexOf("email");
    var _idx_createdAt = _row.firstIndexOf("created_at");

    String id = _row.getString(_idx_id);
    String name = _row.getString(_idx_name);
    String email = _row.getString(_idx_email);
    Instant createdAt = _row.getInstant(_idx_createdAt);

    return new UserDAO(id, name, email, createdAt);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val _idx_id = _row.columnDefinitions.firstIndexOf("id")
    val _idx_name = _row.columnDefinitions.firstIndexOf("name")
    val _idx_email = _row.columnDefinitions.firstIndexOf("email")
    val _idx_createdAt = _row.columnDefinitions.firstIndexOf("created_at")

    var id: String? = _row.getString(_idx_id)
    if (_row.isNull(_idx_id) || id == null) {
      throw NullPointerException("Required field id is not nullable but row has null")
    }
    var name: String? = _row.getString(_idx_name)
    if (_row.isNull(_idx_name) || name == null) {
      throw NullPointerException("Required field name is not nullable but row has null")
    }
    var email: String? = _row.getString(_idx_email)
    if (_row.isNull(_idx_email) || email == null) {
      throw NullPointerException("Required field email is not nullable but row has null")
    }
    var createdAt: Instant? = _row.getInstant(_idx_createdAt)
    if (_row.isNull(_idx_createdAt) || createdAt == null) {
      throw NullPointerException("Required field created_at is not nullable but row has null")
    }

    val _result = UserDAO(id, name, email, createdAt)
    return _result
    ```

Это лучшее место для отладки связывания CQL и сопоставления строк, потому что здесь видно ровно то, что Kora скомпилировала из `@Repository`, `@Query`, `@EntityCassandra` и `@Column`.

## Переработайте сервис { #refactor-service }

На этом шаге переработайте существующий `UserService` из руководства по HTTP-серверу.

Важные правила:

- Сохраните те же публичные контракты сервиса, которые использует `UserController`.
- Генерируйте идентификаторы в приложении, потому что Cassandra не использует `RETURNING id` в стиле PostgreSQL.
- Проверяйте существование перед обновлением и удалением, если ваш HTTP API должен возвращать `404`.
- Оставьте `UserController` и его HTTP-контракты без изменений.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/ru/tinkoff/kora/guide/databasecassandra/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.guide.databasecassandra.service;

    import java.time.Instant;
    import java.util.Comparator;
    import java.util.List;
    import java.util.Optional;
    import java.util.UUID;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.databasecassandra.dto.UserRequest;
    import ru.tinkoff.kora.guide.databasecassandra.dto.UserResponse;
    import ru.tinkoff.kora.guide.databasecassandra.repository.UserDAO;
    import ru.tinkoff.kora.guide.databasecassandra.repository.UserRepository;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;

    @Component
    public final class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        public UserResponse createUser(UserRequest request) {
            var user = new UserDAO(UUID.randomUUID().toString(), request.name(), request.email(), Instant.now());
            userRepository.save(user);
            return toResponse(user);
        }

        public Optional<UserResponse> getUser(String id) {
            return Optional.ofNullable(userRepository.findById(id)).map(this::toResponse);
        }

        public List<UserResponse> getUsers(int page, int size, String sort) {
            return userRepository.findAll().stream()
                    .map(this::toResponse)
                    .sorted(getComparator(sort))
                    .skip((long) page * size)
                    .limit(size)
                    .toList();
        }

        public UserResponse updateUser(String id, UserRequest request) {
            var existing = userRepository.findById(id);
            if (existing == null) {
                throw HttpServerResponseException.of(404, "User not found");
            }
            var updated = new UserDAO(id, request.name(), request.email(), existing.createdAt());
            userRepository.update(updated);
            return toResponse(updated);
        }

        public void deleteUser(String id) {
            if (userRepository.findById(id) == null) {
                throw HttpServerResponseException.of(404, "User not found");
            }
            userRepository.deleteById(id);
        }

        private UserResponse toResponse(UserDAO user) {
            return new UserResponse(user.id(), user.name(), user.email(), user.createdAt());
        }

        private Comparator<UserResponse> getComparator(String sort) {
            return switch (sort.toLowerCase()) {
                case "name" -> Comparator.comparing(UserResponse::name);
                case "email" -> Comparator.comparing(UserResponse::email);
                case "createdat" -> Comparator.comparing(UserResponse::createdAt);
                default -> Comparator.comparing(UserResponse::name);
            };
        }
    }
    ```

!!! note "Контроллер остается как есть"

    Не переписывайте `UserController` в этом руководстве. Оставьте контроллер из `http-server.md` без изменений, чтобы под капотом была заменена только реализация репозитория.

## Конфигурация { #configuration }

Создайте `src/main/resources/application.conf`:

Полное описание настроек смотрите в разделе [База данных Cassandra](../documentation/database-cassandra.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    cassandra {
      auth {
        login = ${CASSANDRA_USER} //(1)!
        password = ${CASSANDRA_PASS} //(2)!
      }
      basic {
        contactPoints = ${CASSANDRA_CONTACT_POINTS} //(3)!
        dc = ${CASSANDRA_DC} //(4)!
        sessionKeyspace = ${CASSANDRA_KEYSPACE} //(5)!
        request {
          timeout = "5s" //(6)!
        }
      }
      telemetry.logging.enabled = true //(7)!
    }
    ```

    1. Имя пользователя для подключения к Cassandra. Обязательное значение из `CASSANDRA_USER`.
    2. Пароль пользователя базы данных. Обязательное значение из `CASSANDRA_PASS`.
    3. Точки подключения Cassandra, используемые для открытия сеансов. Обязательное значение из `CASSANDRA_CONTACT_POINTS`.
    4. Значение для `cassandra.basic.dc`. Обязательное значение из `CASSANDRA_DC`.
    5. Значение для `cassandra.basic.sessionKeyspace`. Обязательное значение из `CASSANDRA_KEYSPACE`.
    6. Значение для `cassandra.basic.request.timeout`.
    7. Включает логирование телеметрии клиента Cassandra.

=== ":simple-yaml: `YAML`"

    ```yaml
    cassandra:
      auth:
        login: ${CASSANDRA_USER} #(1)!
        password: ${CASSANDRA_PASS} #(2)!
      basic:
        contactPoints: ${CASSANDRA_CONTACT_POINTS} #(3)!
        dc: ${CASSANDRA_DC} #(4)!
        sessionKeyspace: ${CASSANDRA_KEYSPACE} #(5)!
        request:
          timeout: "5s" #(6)!
      telemetry:
        logging:
          enabled: true #(7)!
    ```

    1. Имя пользователя для подключения к Cassandra. Обязательное значение из `CASSANDRA_USER`.
    2. Пароль пользователя базы данных. Обязательное значение из `CASSANDRA_PASS`.
    3. Точки подключения Cassandra, используемые для открытия сеансов. Обязательное значение из `CASSANDRA_CONTACT_POINTS`.
    4. Значение для `cassandra.basic.dc`. Обязательное значение из `CASSANDRA_DC`.
    5. Значение для `cassandra.basic.sessionKeyspace`. Обязательное значение из `CASSANDRA_KEYSPACE`.
    6. Значение для `cassandra.basic.request.timeout`.
    7. Включает логирование телеметрии клиента Cassandra.

Для локальной Scylla типичные значения такие:

```bash
export CASSANDRA_CONTACT_POINTS=127.0.0.1:9042
export CASSANDRA_USER=cassandra
export CASSANDRA_PASS=cassandra
export CASSANDRA_DC=datacenter1
export CASSANDRA_KEYSPACE=guide
```

## Настройка базы данных { #database-setup }

### Docker Compose { #docker-compose }

Создайте файл `docker-compose.yml` в каталоге модуля приложения:

```yaml
services:
  scylla:
    image: scylladb/scylla:2025.3
    command: ["--smp", "1", "--memory", "750M", "--overprovisioned", "1", "--developer-mode", "1"]
    ports:
      - "9042:9042"
```

Запустите базу данных:

```bash
docker compose up -d
```

Создайте пространство ключей и таблицу:

```sql
CREATE KEYSPACE IF NOT EXISTS guide
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS guide.users
(
    id         TEXT,
    name       TEXT,
    email      TEXT,
    created_at TIMESTAMP,
    PRIMARY KEY (id)
);
```

## Запуск приложения { #run-app }

```bash
./gradlew run
```

## Проверка приложения { #check-app }

**Получить всех пользователей:**

```bash
curl http://localhost:8080/users
```

**Получить пользователя по идентификатору:**

```bash
curl http://localhost:8080/users/{id}
```

**Создать нового пользователя:**

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Johnson", "email": "bob@example.com"}'
```

**Обновить пользователя:**

```bash
curl -X PUT http://localhost:8080/users/{id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Smith", "email": "bob.smith@example.com"}'
```

**Удалить пользователя:**

```bash
curl -X DELETE http://localhost:8080/users/{id}
```

## Лучшие практики { #best-practices }

- Проектируйте таблицы Cassandra от шаблонов запросов, а не от нормализованных реляционных моделей.
- Держите CQL в методах репозитория, а бизнес-решения — в сервисном слое.
- Используйте `@EntityCassandra` на DAO-моделях, чтобы Kora явно генерировала преобразователи Cassandra.
- Добавляйте `@Column` к каждому компоненту записи DAO, чтобы сопоставления базы данных оставались явными.
- Избегайте неограниченного сканирования таблиц в промышленной среде; моделируйте конечные точки списков вокруг ограниченных секций или отдельных таблиц чтения.
- По умолчанию относитесь к изменениям Cassandra как к идемпотентным, если вы намеренно не используете условные записи.
- Используйте тесты со Scylla или Cassandra Testcontainers, чтобы проверять CQL, схему и сгенерированные преобразователи.
- Изучайте сгенерированные реализации репозиториев, когда связывание CQL или сопоставление строк неочевидно.

## Итоги { #summary }

Вы заменили репозиторий в памяти из HTTP-руководства репозиторием с хранением в Cassandra, добавили конфигурацию Cassandra, создали CQL-таблицу и проверили хранение данных с помощью Scylla
Testcontainers.

HTTP-контракт остается стабильным, а слой хранения данных становится распределенным и Cassandra-совместимым. Вы также изучили сгенерированный Cassandra-код, чтобы увидеть, как Kora превращает
аннотации репозитория в подготовленные выражения, вызовы телеметрии и преобразователи строк.

## Ключевые понятия { #key-concepts }

- как объявляются репозитории Cassandra в Kora
- как записи DAO используют `@EntityCassandra` и `@Column`
- как конфигурация Cassandra создает сеанс в графе приложения
- чем семантика изменений Cassandra отличается от счетчиков обновлений JDBC
- как сгенерированные реализации репозиториев связывают CQL-параметры и сопоставляют строки
- как Scylla Testcontainers проверяет Cassandra-совместимое хранение данных

## Устранение неполадок { #troubleshooting }

**Проблемы подключения:**

- Убедитесь, что Cassandra или Scylla запущена и доступна из приложения.
- Проверьте `CASSANDRA_CONTACT_POINTS`, `CASSANDRA_USER`, `CASSANDRA_PASS`, `CASSANDRA_DC` и `CASSANDRA_KEYSPACE`.
- Убедитесь, что настроенный центр данных соответствует запущенному кластеру.

**Проблемы схемы:**

- Убедитесь, что пространство ключей существует до запуска приложения.
- Убедитесь, что таблица `users` существует в настроенном пространстве ключей.
- Проверьте, что имена столбцов CQL совпадают с сопоставлениями `@Column` в `UserDAO`.

**Ошибки компиляции:**

- Убедитесь, что добавлена зависимость `ru.tinkoff.kora:database-cassandra`.
- Убедитесь, что обработка аннотаций включена для Kora.
- Используйте `@EntityCassandra` для DAO-моделей, которые возвращают репозитории.

**Ошибки запросов во время выполнения:**

- Проверьте, что запросы соответствуют правилам доступа Cassandra.
- Избегайте шаблонов фильтрации или сортировки, которые Cassandra не может выполнить без подходящей структуры таблиц.
- Изучите сгенерированный `$UserRepository_Impl.java` или `$UserRepository_Impl.kt`, чтобы увидеть точное связывание параметров.

## Что дальше? { #whats-next }

- [Кэширование](cache.md), чтобы уменьшить повторные чтения из Cassandra-совместимого хранилища.
- [Наблюдаемость](observability.md), чтобы отслеживать пути запросов с базой данных с помощью метрик, трассировок, журналов и проб.
- [База данных JDBC](database-jdbc.md), если вы хотите сравнить тот же урок по CRUD-хранению данных с реляционным SQL.
- [Обмен сообщениями с Kafka](messaging-kafka.md), когда записи в базу данных также должны публиковать события.
- [Тестирование с JUnit](testing-junit.md) для компонентных тестов, которые не предполагают JDBC-специфичные руководства по тестированию.

## Помощь { #help }

Если вы столкнулись с проблемами:

- сравните с [Kora Java Database Cassandra App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-cassandra-app) и [Kora Kotlin Database Cassandra App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-cassandra-app)
- проверьте [документацию по базе данных Cassandra](../documentation/database-cassandra.md)
- проверьте [общую документацию по базам данных](../documentation/database-common.md)
- прочитайте [документацию Apache Cassandra](https://cassandra.apache.org/doc/latest/)
- прочитайте [документацию ScyllaDB](https://opensource.docs.scylladb.com/)
