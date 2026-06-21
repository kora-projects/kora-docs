---
description: "Explains Common Kora database model and repository conventions: entities, identifiers, naming, embedded fields, query macros, batch queries, and repository inheritance. Use when working with @Table, @Column, @Id, @Embedded, @Repository, @Query, @Batch, @Mapping."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Common Kora database model and repository conventions: entities, identifiers, naming, embedded fields, query macros, batch queries, and repository inheritance; key triggers include @Table, @Column, @Id, @Embedded, @Repository, @Query, @Batch, @Mapping, Entity, Repository."
---

Основные принципы и механизмы работы модулей баз данных в Kora.
Этот раздел описывает общую модель для `JDBC`, `Cassandra`, `R2DBC` и `Vertx`: сущности, репозитории, параметры запросов, пакетные запросы, количество измененных строк и макросы.
Особенности подключения, транзакций, поддержанных сигнатур и драйверных преобразователей описаны в документации конкретного модуля базы данных.

Этот раздел намеренно не описывает детали конкретных драйверов.
За конфигурацией подключения, транзакциями, типами возвращаемых значений, созданными базой данных идентификаторами,
служебными параметрами методов и точными интерфейсами преобразователей нужно обращаться к документации нужной реализации:
[`JDBC`](database-jdbc.md), [`Cassandra`](database-cassandra.md), [`R2DBC`](database-r2dbc.md) или [`Vertx`](database-vertx.md).

Мы придерживаемся концепции, что самый лучший способ общения с базой данных SQL, это общение на ее родном языке SQL.
Другие инструменты зачастую имеют ограничения на использования специфичных функций определенной базы данных,
либо сложный программный язык построения запросов который требует дополнительное и значительное время на изучение и освоение,
несет в себе кучу не явностей и потенциальных ошибок со стороны разработчика, а также порой имеет низкую производительность.

Если нужен пошаговый разбор перед справочным описанием, смотрите [База данных JDBC](../guides/database-jdbc.md) и [База данных JDBC продвинутая](../guides/database-jdbc-advanced.md).

## Сущность { #entity }

Сущность - представления данных из базы данных в виде класса с полями.

Сущности используемые в качестве возвращаемого значения, должны содержать один публичный
конструктор. Это может быть как конструктор по умолчанию, так и конструктор с параметрами.
Если Kora найдет конструктор с параметрами, то на его основе будет создаваться объект сущности.
В случае же с пустым конструктором поля будут заполняться [через сеттеры](https://docs.oracle.com/cd/E19316-01/819-3669/bnais/index.html).

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val id: String, val name: String)
    ```

### Таблица { #table }

Можно указывать, к какой таблице принадлежит сущность, это понадобится в случае использования [макросов](#macros) при построении запросов.

В случае если таблица не указана, макросы будут использовать имя класса в [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/)

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Table("entities")
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Table("entities")
    data class Entity(val id: String, val name: String)
    ```

### Идентификатор { #identifier }

Так как все манипуляции с данными происходят посредством преобразования сущности в запрос к драйверу,
то нет надобности выделять специально первичный ключ в рамках сущности для работы с сущностью.

Обозначать, что именно является первичным ключом, может пригодиться в рамках использования [макросов](#macros),
для этого можно использовать аннотацию `@Id`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Id String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(@field:Id val id: String, val name: String)
    ```

#### Последовательный { #sequential }

Рассмотрим создание идентификатора как последовательность чисел на примере Postgres,
Kora предлагает использовать механизм базы данных [identity column](https://www.tutorialsteacher.com/postgresql/identity-column).

Пример таблицы для такой сущности будет выглядеть так:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    id   BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
```

Создаваться идентификатор будет на этапе вставки в базу данных,
а получать его в коде приложения подразумевается с помощью конструкции [возвращаемого значения идентификатора для JDBC или R2DBC](database-jdbc.md#generated-identifier) при вставке
либо использовать [специальные конструкции](https://postgrespro.ru/docs/postgresql/9.5/dml-returning) вашей базы данных:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(Long id, String name) {}

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        @Nullable
        Entity findById(long id);

        @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
        long insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val id: Long, val name: String)

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: Long): Entity?

        @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
        fun insert(entity: Entity): Long
    }
    ```

#### Случайный { #random }

Для создания случайного идентификатора предлагается использовать стандартный `UUID` из Java:

Пример таблицы для такой сущности будет выглядеть так:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    id   UUID    NOT NULL,
    name VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
```

Создаваться идентификатор будет на этапе создания объекта в пользовательском коде приложения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(UUID id, String name) {}

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        @Nullable
        Entity findById(UUID id);

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        void insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val id: UUID, val name: String)

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: UUID): Entity?

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity)
    }
    ```

#### Композитный { #composite }

В случае если требуется использовать композитный ключ,
предполагается использовать аннотацию `@Embedded` для создания [вложенных полей](#embedded-fields).

### Именование { #naming }

По умолчанию имена полей сущностей переводятся в [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/) при извлечении
результата.

Если требуется настроить сопоставление конкретных полей из базы данных с сущностью, то можно использовать аннотацию `@Column`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Column("ID") String id,
                         @Column("NAME") String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(@field:Column("ID") val id: String,
                      @field:Column("NAME") val name: String)
    ```

#### Стратегия именования { #naming-strategy }

Если требуется использовать стратегию именования для всей сущности, то предлагается создать реализацию `NameConverter` и затем использовать ее в аннотации `@NamingStrategy`.
Требуется чтобы реализация `NameConverter` имела конструктор без параметров.

Либо использовать доступные стратегии из Kora:

- `NoopNameConverter` - стратегия использует имя поля по умолчанию.
- `SnakeCaseNameConverter` - стратегия использует [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `SnakeCaseUpperNameConverter` - стратегия использует [SNAKE_UPPER_CASE](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `PascalCaseNameConverter` - стратегия использует [PascalCase](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `CamelCaseNameConverter` - стратегия использует [camelCase](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @NamingStrategy(NoopNameConverter.class)
    public record Entity(String id,
                         String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @NamingStrategy(NoopNameConverter::class.java)
    data class Entity(val id: String,
                      val name: String)
    ```

### Обязательные поля { #required-fields }

===! ":fontawesome-brands-java: `Java`"

    По умолчанию все поля объявленные в сущности считаются **обязательными** (*NotNull*).

    ```java
    public record Entity(String id,
                         String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все поля объявленные в сущности которые не используют [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис считаются **обязательными** (*NotNull*).

    ```kotlin
    data class Entity(val id: String,
                      val name: String)
    ```

### Необязательные поля { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    В случае если поле в сущности является необязательным, то есть может отсутствовать то,
    можно использовать аннотацию `@Nullable`, чтобы явно указать необязательное поле сущности.

    ```java
    public record Entity(String id,
                         @Nullable String name) {} //(1)!
    ```

    1.  Подойдет любая аннотация `@Nullable`, такие как `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

    Также можно указывать необязательными параметры конструктора в случае если переопределен канонический конструктор у Record:

    ```java
    public record Entity(String id,
                         String name) {

        public Entity(String id,
                      @Nullable String name) { //(1)!
            this.id = id;
            this.name = name;
        }
    }
    ```

    1.  Подойдет любая аннотация `@Nullable`, такие как `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использовать [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис и помечать такой параметр как Nullable:

    ```kotlin
    data class Entity(val id: String,
                      val name: String?)
    ```

### Вложенные поля { #embedded-fields }

В случае если требуется использовать вложенные поля,
то есть объединить колонки из таблицы в рамках отдельного класса внутри сущности, можно использовать аннотацию `@Embedded`.

Предположим есть SQL таблица где имеется композитный ключ который мы хотим выразить отдельным классом:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    name     VARCHAR NOT NULL,
    surname  VARCHAR NOT NULL,
    info     VARCHAR NOT NULL,
    PRIMARY KEY (name, surname)
)
```

Тогда сущность будет выглядеть так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Id @Embedded UserID id,
                         @Column("info") String info) {

        public record UserID(String name, String surname) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(
        @field:Id @field:Embedded val id: UserID,
        @field:Column("info") val info: String
    ) {

        data class UserID(
            val name: String,
            val surname: String
        )
    }
    ```

Тогда репозиторий для такой сущности будет выглядеть так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("""
                SELECT name, surname, info FROM entities
                WHERE name = :id.name AND surname = :id.surname;
                """)
        @Nullable
        Entity findById(Entity.UserID id);

        @Query("""
            INSERT INTO entities(name, surname, info)
            VALUES (:entity.id.name, :entity.id.surname, :entity.info)
            """)
        void insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query(
            """
            SELECT name, surname, info FROM entities
            WHERE name = :id.name AND surname = :id.surname;
            """
        )
        fun findById(id: Entity.UserID): Entity?

        @Query(
            """
            INSERT INTO entities(name, surname, info)
            VALUES (:entity.id.name, :entity.id.surname, :entity.info)
            """
        )
        fun insert(entity: Entity)
    }
    ```

В случае если бы поля имели общий префикс, его можно было бы указать в аннотации `@Embedded("user_")`:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    user_name     VARCHAR NOT NULL,
    user_surname  VARCHAR NOT NULL,
    info          VARCHAR NOT NULL,
    PRIMARY KEY (user_name, user_surname)
)
```

## Репозиторий { #repository }

Главным инструментом для работы с базами данных в Kora является использование [шаблона проектирование репозиторий](https://gist.github.com/maestrow/594fd9aee859c809b043) при проектировании абстракции доступа к базе данных.
Интерфейс репозитория должен быть проаннотирован `@Repository`.
Запросы для методов репозиториев описываются с помощью `@Query` аннотации.
На этапе компиляции создается реализация, где каждый метод будет выполнять описанный запрос и эффективно производить сборку аргументов запроса и обработку результата.

Предполагается написание `SQL`-запросов разработчиком, поскольку это повышает ответственность разработчика за план запроса,
дает больше понимание и контекста разработчику о том что он делает и как его запрос будет работать.
Для улучшения пользовательского опыта с перечислениями моделей можно использовать [макросы](#macros).

Репозиторий должен являться наследником одной из реализаций, в примерах ниже рассматривается реализация [JDBC](database-jdbc.md)

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository //(1)!
    public interface EntityRepository extends JdbcRepository {

        public record Entity(String id, String name) { }

        @Query("SELECT id, name FROM entities WHERE id = :id") //(2)!
        @Nullable //(3)!
        Entity findById(String id);
    }
    ```

    1. Указывает, что интерфейс является репозиторием.
    2. Указывает, что нужно создать реализацию метода, выполняющую `SQL`-запрос, указанный в аннотации.
    3. Указывает, что возвращаемое значение может отсутствовать, можно также использовать `Optional`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository //(1)!
    interface EntityRepository : JdbcRepository {

        data class Entity(val id: String, val name: String)

        @Query("SELECT id, name FROM entities WHERE id = :id") //(2)!
        fun findById(id: String): Entity?
    }
    ```

    1. Указывает, что интерфейс является репозиторием.
    2. Указывает, что нужно создать реализацию метода, выполняющую `SQL`-запрос, указанный в аннотации.

### Параметры запроса { #query-parameters }

Параметры метода репозитория связываются с именованными параметрами в `@Query`.
Обычный параметр используется по имени метода: `:id`, `:name`, `:status`.
Если параметр является сущностью или `DTO`, можно обращаться к его полям через точку: `:entity.id`, `:entity.name`, `:filter.status`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("""
            SELECT id, name FROM entities
            WHERE id = :id AND name = :filter.name
            """)
        @Nullable
        Entity findById(String id, Filter filter);

        record Filter(String name) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query(
            """
            SELECT id, name FROM entities
            WHERE id = :id AND name = :filter.name
            """
        )
        fun findById(id: String, filter: Filter): Entity?

        data class Filter(val name: String)
    }
    ```

Если параметр встречается в запросе несколько раз, Kora привяжет его ко всем вхождениям.
Если параметр метода не используется в запросе и не является служебным параметром конкретного драйвера, компиляция завершится ошибкой.

### Преобразователи { #mappers }

Для нестандартного представления значения в базе данных используется аннотация `@Mapping`.
Ее можно ставить на поле сущности, параметр метода или метод репозитория:

- на поле сущности - когда нужно изменить чтение или запись конкретной колонки;
- на параметр метода - когда нужно изменить запись конкретного параметра запроса;
- на метод репозитория - когда нужно изменить обработку результата запроса целиком или строки результата.

Нельзя использовать произвольный преобразователь в любом месте: его тип должен соответствовать месту применения.
Преобразователь параметра применяется к параметру запроса, преобразователь колонки - к полю сущности, а преобразователь результата или строки - к методу репозитория.
Точный набор допустимых интерфейсов зависит от драйвера: например, для `JDBC` это `JdbcRowMapper`, `JdbcResultSetMapper`, `JdbcResultColumnMapper` и `JdbcParameterColumnMapper`.
Аналогичные интерфейсы для `Cassandra`, `R2DBC` и `Vertx`, а также особенности их применения, описаны в соответствующих разделах документации конкретной реализации базы данных.
Если преобразователь указан через `@Mapping`, Kora добавит его как зависимость сгенерированного репозитория и будет использовать вместо преобразователя по умолчанию.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Table("entities")
    public record Entity(@Id String id,
                         @Mapping(JsonParameterMapper.class)
                         @Column("payload")
                         String payload) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Table("entities")
    data class Entity(
        @field:Id val id: String,
        @field:Mapping(JsonParameterMapper::class)
        @field:Column("payload")
        val payload: String
    )
    ```

### Пакетный запрос { #batch-query }

Kora поддерживает пакетные запросы с помощью аннотации `@Batch`.

В отличие от последовательного выполнения `SQL`-запросов, пакетная обработка даёт возможность отправить целый набор запросов за один вызов,
уменьшая количество требуемых сетевых обращений и позволяя выполнять часть запросов параллельно на стороне базы данных,
что может увеличить скорость выполнения.

Пример использования:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        void insert(@Batch List<Entity> entity);
    }
    ```

    **Пакетный запрос** не может возвращать произвольные значения, такой метод может возвращать `void`, либо `UpdateCount`,
    либо созданные базой данных идентификаторы для [JDBC](database-jdbc.md#generated-identifier) или [R2DBC](database-r2dbc.md#generated-identifier) драйверов.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(@Batch entity: List<Entity>)
    }
    ```

    **Пакетный запрос** не может возвращать произвольные значения, такой метод может возвращать `Unit`, либо `UpdateCount`,
    либо созданные базой данных идентификаторы для [JDBC](database-jdbc.md#generated-identifier) или [R2DBC](database-r2dbc.md#generated-identifier) драйверов.

`@Batch` ставится на параметр-коллекцию, элементы которой будут по очереди подставляться в один и тот же запрос.
Остальные параметры метода, если они есть, являются общими для всех элементов пакета.
Например, в запросе `INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)` параметр `tenantId` будет одинаковым для всех элементов, а поля `entity` будут взяты из каждого элемента коллекции.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)")
    UpdateCount insert(String tenantId, @Batch List<Entity> entity);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)")
    fun insert(tenantId: String, @Batch entity: List<Entity>): UpdateCount
    ```

В одном методе должен быть не более одного параметра с `@Batch`.
Поддержка созданных базой данных идентификаторов в пакетных запросах зависит от конкретного драйвера и описана в соответствующем разделе.

### Счетчик обновлений { #affected-rows }

Kora не обрабатывает содержимое запроса, результат метода всегда считается производным из строк, которые вернула база данных.
Если необходимо получить в качестве результата количество измененных строк, нужно использовать специальный тип `UpdateCount`.
Для обычного запроса `UpdateCount#value()` содержит количество строк, которое вернул драйвер для выполненного запроса.
Для пакетного запроса значение обычно является суммой результатов по элементам пакета; точное поведение зависит от драйвера базы данных.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        UpdateCount insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): UpdateCount
    }
    ```

### Ручное управление { #manual-query }

В случае если по каким-то причинам не хватает функциональности запросов в аннотации `@Query` или требуется ручное управление соединением,
можно использовать встроенный метод фабрики соединений для создания метода с полностью ручным управлением.

Можно также использовать внутри метода другие методы репозитория, и они будут выполняться в рамках одной транзакции, если это требуется.
Детальнее про транзакции стоит смотреть документацию по конкретной реализации репозитория.

В репозитории можно объявлять обычные методы с реализацией.
Это удобно, когда нужно инкапсулировать более сложную операцию рядом с запросами: например, выполнить несколько методов с `@Query` в одной транзакции,
собрать результат из нескольких запросов или оставить последовательность операций с базой данных внутри репозитория, не вынося ее в сервисный слой.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        UpdateCount insert(Entity entity);

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        UpdateCount updateName(Long id, String name);

        default Entity saveAndRename(Entity entity, String name) {
            return getJdbcConnectionFactory().inTx(() -> {
                insert(entity);
                updateName(entity.id(), name);
                return new Entity(entity.id(), name);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        data class Entity(val id: Long, val name: String)

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        fun insert(entity: Entity): UpdateCount

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        fun updateName(id: Long, name: String): UpdateCount

        fun saveAndRename(entity: Entity, name: String): Entity {
            return jdbcConnectionFactory.inTx<Entity> {
                insert(entity)
                updateName(entity.id, name)
                Entity(entity.id, name)
            }
        }
    }
    ```

### Несколько баз данных { #multiple-databases }

Иногда требуется чтобы в рамках одного приложения был доступ к разным базам данных в разных репозиториях,
это можно решить следующим образом.
Требуется создать отдельный экземпляр базы данных и подключить его в репозиторий,
ниже будет показан пример для [JDBC](database-jdbc.md) базы данных, но принцип аналогичный и для других типов подключений.

Требуется скопировать фабрики создания `JdbcDatabase` и его конфигурации из модуля `JdbcDatabaseModule`
и указать им свой тег, который будет указывать что это соединения для другой базы данных.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule {

        final class OtherDatabase { }

        @Tag(OtherDatabase.class)
        default JdbcDatabaseConfig otherJdbcDataBaseConfig(Config config,
                                                           ConfigValueExtractor<JdbcDatabaseConfig> extractor) {
            var value = config.get("db.other");
            return extractor.extract(value);
        }

        @Tag(OtherDatabase.class)
        default JdbcDatabase otherJdbcDataBase(@Tag(OtherDatabase.class) JdbcDatabaseConfig config,
                                               DataBaseTelemetryFactory telemetryFactory,
                                               @Tag(OtherDatabase.class) @Nullable Executor executor) {
            return new JdbcDatabase(config, telemetryFactory, executor);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule {

        class OtherDatabase

        @Tag(OtherDatabase::class)
        fun otherJdbcDataBaseConfig(
            config: Config,
            extractor: ConfigValueExtractor<JdbcDatabaseConfig?>
        ): JdbcDatabaseConfig {
            val value = config.get("db.other")
            return extractor.extract(value) ?: throw ConfigValueExtractionException.missingValue(value)
        }

        @Tag(OtherDatabase::class)
        fun otherJdbcDataBase(
            @Tag(OtherDatabase::class) config: JdbcDatabaseConfig?,
            telemetryFactory: DataBaseTelemetryFactory?,
            @Tag(OtherDatabase::class) executor: Executor?
        ): JdbcDatabase {
            return JdbcDatabase(config, telemetryFactory, executor)
        }
    }
    ```

А в репозиториях, которые будут использовать эту базу данных теперь требуется указывать тег этого подключения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository(executorTag = @Tag(OtherDatabase.class))
    public interface OtherJdbcRepository extends JdbcRepository {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository(executorTag = Tag(value = [OtherDatabase::class]))
    interface OtherJdbcRepository : JdbcRepository {

    }
    ```

Репозитории с подключением к основной базе данных, не требуют тега.

### Макросы { #macros }

Самой неприятной частью написания `SQL`-запросов может быть перечисление и поддержание колонок и полей сущности в актуальном состоянии.

Чтобы решить эту проблему, можно использовать специальные макрос-конструкции внутри `SQL`-запроса в рамках аннотации `@Query`.
Эти конструкции позволяют оперировать [сущностью](#entity), на которую указывают, раскрывать её в определенные `SQL`-конструкции и легко дополнять `SQL`-запросы.
Макрос является помощником при написании `SQL`-запросов и раскрывается в конструкции, которые пользователь смог бы написать собственными руками.

Синтаксис макроса выглядит следующем образом: `%{return#selects}`

1. Макрос ограничен синтаксической конструкцией `%{` и `}`
2. Первым указывается цель макроса, это может быть как имя любого аргумента метода, так и возвращаемое значение с помощью ключевого слова `return`
3. Затем используется `#` символ для разделения цели и команды макроса
4. Затем указывается команда макроса, которая говорит в какую именно SQL конструкцию раскрывать сущность

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id,
                             @Column("entity_name") String name,
                             String code) {}

        @Query("SELECT %{return#selects} FROM %{return#table}") //(1)!
        List<Entity> findAll();
    }
    ```

    1.  Раскрывается в запрос:
        ```sql
        SELECT id, entity_name, code FROM entities
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long,
                          @field:Column("entity_name") val name: String,
                          val code: String)

        @Query("SELECT %{return#selects} FROM %{return#table}") //(1)!
        fun findAll(): List<Entity>
    }
    ```

    1.  Раскрывается в запрос:
        ```sql
        SELECT id, entity_name, code FROM entities
        ```

#### Команды { #commands }

Доступные команды макросов:

- `table` - конструкция раскрывает значение сущности в [аннотации](#table) `@Table` либо, если таковая отсутствует, переводит имя сущности в [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/)
- `selects` - создает конструкцию перечисления колонок сущности для `SELECT` запроса
- `inserts` - создает конструкцию таблицы, перечисления колонок и соответствующих полей сущности для `INSERT` запроса
- `updates` - создает конструкцию перечисления колонок и соответствующих полей сущности (за исключением `@id` поля) для `UPDATE` запроса
- `where` - создает конструкцию перечисления колонок со значением из сущности для `WHERE` части запроса

#### Перечисление полей { #field-enumeration }

Макрос поддерживает дополнительный синтаксис по перечислению определенных полей в команде,
если вдруг требуется сделать частичное обновление или получение данных.
Для этого после команды используется специальная конструкция: `%{return#updates=name}`

**Только** между полями перечисления и символом перечисления могут содержаться пробелы.

Доступны специальные символы перечисления:

1. `=` - только указанные после символа имя полей сущности будут участвовать в раскрытии команды
2. `-=` - все поля сущности за исключением указанных после символа будут участвовать в раскрытии команды

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id,
                             @Column("entity_name") String name,
                             String code) {}

        @Query("INSERT INTO %{entity#inserts=name,code}") //(1)!
        UpdateCount insert(Entity entity);
    }
    ```

    1.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code)
        VALUES(:entity.name, :entity.code)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long,
                          @field:Column("entity_name") val name: String,
                          val code: String)

        @Query("INSERT INTO %{entity#inserts=name,code}") //(1)!
        fun insert(entity: Entity): UpdateCount
    }
    ```

    1.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code)
        VALUES(:entity.name, :entity.code)
        ```

##### Идентификатор { #identifier-2 }

При перечислении полей в макросе возможно использовать специальное ключевое слово `@id`
для того чтобы ссылаться сразу идентификатор сущности проаннотированный [аннотацией](#identifier) `@Id`.

Это может быть особенно полезно когда идентификатор является [составным ключом](#optional-fields), для перечисления сразу всех колонок.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id,
                             @Column("entity_name") String name,
                             String code) {}

        @Query("INSERT INTO %{entity#inserts-=@id}") //(1)!
        UpdateCount insert(Entity entity);
    }
    ```

    1.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code)
        VALUES(:entity.name, :entity.code)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long,
                          @field:Column("entity_name") val name: String,
                          val code: String)

        @Query("INSERT INTO %{entity#inserts-=@id}") //(1)!
        fun insert(entity: Entity): UpdateCount
    }
    ```

    1.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code)
        VALUES(:entity.name, :entity.code)
        ```

#### Пример репозитория { #repository-example }

Пример полного репозитория со всеми основными методами для оперирования сущностью для [Postgres SQL](https://postgrespro.ru/docs/postgresql):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        record Entity(@Id String id,
                      @Column("value1") int field1,
                      String value2,
                      @Nullable String value3) {}

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        @Nullable
        Entity findById(String id);

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        List<Entity> findAll();

        @Query("INSERT INTO %{entity#inserts}")  //(3)!
        UpdateCount insert(@Batch List<Entity> entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")  //(4)!
        UpdateCount update(@Batch List<Entity> entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (id) DO UPDATE SET %{entity#updates}")  //(5)!
        UpdateCount upsert(@Batch List<Entity> entity);

        @Query("DELETE FROM entities WHERE id = :id")
        UpdateCount deleteById(String id);

        @Query("DELETE FROM entities")
        UpdateCount deleteAll();
    }
    ```

    1.  Раскрывается в запрос:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        WHERE id = :id
        ```
    2.  Раскрывается в запрос:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        ```
    3.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Раскрывается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        WHERE id = :entity.id
        ```
    5.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (id) DO UPDATE
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(
            @field:Id val id: String,
            @field:Column("value1") val field1: Int,
            val value2: String,
            @field:Nullable val value3: String
        )

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        fun findById(id: String): Entity?

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        fun findAll(): List<Entity>

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(@Batch entity: List<Entity>): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}") //(4)!
        fun update(@Batch entity: List<Entity>): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (id) DO UPDATE SET %{entity#updates}") //(5)!
        fun upsert(@Batch entity: List<Entity>): UpdateCount

        @Query("DELETE FROM entities WHERE id = :id")
        fun deleteById(id: String): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```

    1.  Раскрывается в запрос:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        WHERE id = :id
        ```
    2.  Раскрывается в запрос:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        ```
    3.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Раскрывается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        WHERE id = :entity.id
        ```
    5.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (id) DO UPDATE
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        ```

#### Пример композитного { #composite-example }

Пример репозитория с [композитным идентификатором](#composite) и основными методами для оперирования сущностью,
он почти что полностью идентичен предыдущему за исключением `WHERE` условий при поиске и удалении для [Postgres SQL](https://postgrespro.ru/docs/postgresql):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        record Entity(@Id @Embedded  EntityId id,
                      @Column("value1") int field1,
                      String value2,
                      @Nullable String value3) {

            public record EntityId(String code, String type) { }
        }

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE %{id#where}") //(1)!
        @Nullable
        Entity findById(EntityId id);

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        List<Entity> findAll();

        @Query("INSERT INTO %{entity#inserts}")  //(3)!
        UpdateCount insert(@Batch List<Entity> entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")  //(4)!
        UpdateCount update(@Batch List<Entity> entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (code, type) DO UPDATE SET %{entity#updates}")  //(5)!
        UpdateCount upsert(@Batch List<Entity> entity);

        @Query("DELETE FROM entities WHERE %{id#where}")
        UpdateCount deleteById(EntityId id);

        @Query("DELETE FROM entities")
        UpdateCount deleteAll();
    }
    ```

    1.  Раскрывается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        WHERE code = :code AND type = :type
        ```
    2.  Раскрывается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        ```
    3.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3)
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Раскрывается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        WHERE code = :entity.id.code AND type = :entity.id.type
        ```
    5.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3)
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (code, type) DO UPDATE
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(
            @field:Id @field:Embedded val id: EntityId,
            @field:Column("value1") val field1: Int,
            val value2: String,
            val value3: String?
        ) {

            data class EntityId(val code: String, val type: String)
        }

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE %{id#where}") //(1)!
        fun findById(id: EntityId): Entity?

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        fun findAll(): List<Entity>

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(@Batch entity: List<Entity>): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}") //(4)!
        fun update(@Batch entity: List<Entity>): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (code, type) DO UPDATE SET %{entity#updates}") //(5)!
        fun upsert(@Batch entity: List<Entity>): UpdateCount

        @Query("DELETE FROM entities WHERE %{id#where}")
        fun deleteById(id: EntityId): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```

    1.  Раскрывается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        WHERE code = :code AND type = :type
        ```
    2.  Раскрывается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        ```
    3.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3)
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Раскрывается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        WHERE code = :entity.id.code AND type = :entity.id.type
        ```
    5.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3)
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (code, type) DO UPDATE
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        ```

#### Пример наследования { #inheritance-example }

Также можно создать абстрактный общий репозиторий и потом использовать его в наследовании для [Postgres SQL](https://postgrespro.ru/docs/postgresql):

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface PostgresJdbcCrudRepository<K, V> extends JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table}")
        List<V> findAll();

        @Query("INSERT INTO %{entity#inserts}")
        UpdateCount insert(V entity);

        @Query("INSERT INTO %{entity#inserts}")
        UpdateCount insert(@Batch List<V> entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        UpdateCount update(V entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        UpdateCount update(@Batch List<V> entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#selects = @id}) DO UPDATE SET %{entity#updates}")
        UpdateCount upsert(V entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#selects = @id}) DO UPDATE SET %{entity#updates}")
        UpdateCount upsert(@Batch List<V> entity);

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        UpdateCount delete(V entity);

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        UpdateCount delete(@Batch List<V> entity);
    }

    @Repository
    public interface EntityRepository extends PostgresJdbcCrudRepository<String, Entity> {

        @Table("entities")
        record Entity(@Id String id,
                      @Column("value1") int field1,
                      String value2,
                      @Nullable String value3) {
        }

        @Query("DELETE FROM entities WHERE id = :id")
        UpdateCount deleteById(String id);

        @Query("DELETE FROM entities")
        UpdateCount deleteAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface PostgresJdbcCrudRepository<K, V> : JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table}")
        fun findAll(): List<V>

        @Query("INSERT INTO %{entity#inserts}")
        fun insert(entity: V): UpdateCount

        @Query("INSERT INTO %{entity#inserts}")
        fun insert(@Batch entity: List<V>): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        fun update(entity: V): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        fun update(@Batch entity: List<V>): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#selects = @id}) DO UPDATE SET %{entity#updates}")
        fun upsert(entity: V): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#selects = @id}) DO UPDATE SET %{entity#updates}")
        fun upsert(@Batch entity: List<V>): UpdateCount

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        fun delete(entity: V): UpdateCount

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        fun delete(@Batch entity: List<V>): UpdateCount
    }

    @Repository
    interface EntityRepository : PostgresJdbcCrudRepository<String, Entity> {

        @Table("entities")
        data class Entity(
            @field:Id val id: String,
            @field:Column("value1") val field1: Int,
            val value2: String,
            @field:Nullable val value3: String
        )

        @Query("DELETE FROM entities WHERE id = :id")
        fun deleteById(id: String): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```
