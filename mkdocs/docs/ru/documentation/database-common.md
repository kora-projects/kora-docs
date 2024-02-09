Основные принципы и механизмы работы модулей баз данных в Kora.

Мы придерживаемся концепции, что самый лучший способ написания запросов к SQL базам данных это использование именно SQL языка.
Другие инструменты зачастую имеют ограничения на использования специфичных функций определенной базы данных, 
либо сложный программный язык построения запросов который требует отдельного понимания.

## Сущность

Сущность - представления данных из базы данных в виде класса с полями.

Сущности используемые в качестве возвращаемого значения, должны содержать один публичный
конструктор. Это может быть как конструктор по умолчанию, так и конструктор с параметрами.
Если Kora найдет конструктор с параметрами, то на его основе будет создаваться объект сущности.
В случае же с пустым конструктором поля будут заполняться [через сеттеры](https://docs.oracle.com/cd/E19316-01/819-3669/bnais/index.html).

=== ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val id: String, val name: String)
    ```

### Таблица

Можно указывать к какой таблице принадлежит сущность, это понадобится в случае использования [макросов]() при построении запросов.

В случае если таблица не указана, макросы будут использовать имя класса в [snake_lower_case](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/)

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Table("entities")
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Table("entities")
    data class Entity(val id: String, val name: String)
    ```

### Идентификатор

Так как все манипуляции с данными происходят посредствам преобразования сущности в запрос к драйверу, 
то нет надобности выделять специально первичный ключ в рамках сущности для работы с сущностью.

Обозначать что именно является первичным ключом, может пригодиться в рамках использования [макросов](#_15), 
для этого можно использовать аннотацию `@Id`.

=== ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Id String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(@field:Id val id: String, val name: String)
    ```

#### Последовательный

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
а получать его в коде приложения подразумевается с помощью конструкции [возвращаемого значения идентификатора]() при вставке 
либо использовать [специальные конструкции](https://postgrespro.ru/docs/postgresql/9.5/dml-returning) вашей базы данных:

=== ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(Long id, String name) {}

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT * FROM entities WHERE id = :id")
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

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(id: Long): Entity?

        @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
        fun insert(entity: Entity): Long
    }
    ```

#### Случайный

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

=== ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(UUID id, String name) {}

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT * FROM entities WHERE id = :id")
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

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(id: UUID): Entity?

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity)
    }
    ```

### Именование

По умолчанию имена полей сущностей переводятся в [snake_lower_case](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/) при извлечении
результата.

Если требуется настроить сопоставление конкретных полей из базы данных с сущностью, то можно использовать аннотацию `@Column`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Column("ID") String id, 
                         @Column("NAME") String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(@field:Column("ID") val id: String,
                      @field:Column("NAME") val name: String)
    ```

#### Стратегия именования

Если требуется использовать стратегию именования для всей сущности, то предлагается создать реализацию `NameConverter` и затем использовать ее в аннотации `@NamingStrategy`.
Требуется чтобы реализация `NameConverter` имела конструктор без параметров.

Либо использовать доступные стратегии из Kora:

- `NoopNameConverter` - стратегия использует имя поля по умолчанию.
- `SnakeCaseNameConverter` - стратегия использует [snake_lower_case](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `SnakeCaseUpperNameConverter` - стратегия использует [SNAKE_UPPER_CASE](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `PascalCaseNameConverter` - стратегия использует [PascalCase](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `CamelCaseNameConverter` - стратегия использует [camelCase](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).

=== ":fontawesome-brands-java: `Java`"

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

### Обязательные поля

=== ":fontawesome-brands-java: `Java`"

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

### Необязательные поля

=== ":fontawesome-brands-java: `Java`"

    В случае если поле в сущности является необязательным, то есть может отсутствовать то,
    можно использовать аннотацию `@Nullable` для соответствия поля в Json и DTO.

    ```java
    public record Entity(String id, 
                         @Nullable String name) {} //(1)!
    ```

    1.  Подойдет любая аннотация `@Nullable`, такие как `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использовать [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис и помечать такой параметр как Nullable:

    ```kotlin
    data class Entity(val id: String,
                      val name: String?)
    ```

### Вложенные поля

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

=== ":fontawesome-brands-java: `Java`"

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
        @field:Column("name") val info: String
    ) {

        data class UserID(
            val name: String,
            val surname: String
        )
    }
    ```

Тогда репозиторий для такой сущности будет выглядеть так:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("""
                SELECT * FROM entities
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
            SELECT * FROM entities
            WHERE name = :id.name AND surname = :id.surname;
            """
        )
        fun findById(id: Entity.CompositeID): Entity?

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

## Репозиторий

Главным инструментом для работы с базами данных с помощью Kora является специализированный класс репозиторий, аннотированный `@Repository`.
Репозитории позволяют создавать с помощью создания код на этапе компиляции реализации контрактов описанных репозиториев которые будут доступны в контейнере.
Запросы в репозиториях описываются с помощью `@Query` аннотации.

Репозиторий должен являться наследником одной из реализаций, в примерах ниже будет расcмотрена реализация [JDBC](#jdbc)

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Repository //(1)!
    public interface EntityRepository extends JdbcRepository {

        public record Entity(String id, String name) { }

        @Query("SELECT * FROM entities WHERE id = :id;") //(2)!
        @Nullable //(3)!
        Entity findById(String id);
    }
    ```

    1. Указывает, что интерфейс является репозиторием.
    2. Указывает, что нужно создать реализацию метода, выполняющую SQL запрос указанный в аннотации.
    3. Указывает, что возвращаемое значение может отстутствовать, можно также использовать `Optional`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository //(1)!
    interface EntityRepository : JdbcRepository {

        data class Entity(val id: String, val name: String)

        @Query("SELECT * FROM entities WHERE id = :id;") //(2)!
        fun findById(id: String): Entity?
    }
    ```

    1. Указывает, что интерфейс является репозиторием.
    2. Указывает, что нужно создать реализацию метода, выполняющую SQL запрос указанный в аннотации.

### Пакетный запрос

Kora поддерживает пакетные запросы (batch-запросы) с помощью аннотации `@Batch`.

В отличие от последовательного выполнения SQL запросов, пакетная обработка даёт возможность отправить целый набор запросов за один вызов, 
уменьшая количество требуемых сетевых подключений и позволяя выполнять какое-то количество запросов параллельно на стороне базы данных, 
что может увеличить скорость выполнения.

Пример использования:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        void insert(@Batch List<Entity> entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(@Batch entity: List<Entity>)
    }
    ```

### Счетчик обновлений

Kora не обрабатывает содержимое запроса, результат метода всегда считается производным из строк, которые вернула база данных.
Если необходимо получить в качестве результата количество обновленных строк нужно использовать специальный тип `UpdateCount`.

=== ":fontawesome-brands-java: `Java`"

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

### Созданные идентификаторы

Если необходимо получить в качестве результата созданные базой данных первичные ключи сущности, 
предлагается использовать аннотацию `@Id` над методом, где тип возвращаемого значения является идентификаторами.
Такой подход работает и для `@Batch` запросов.

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        long insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insert(entity: Entity): Long
    }
    ```

### Макросы

Самой неприятной частью написания SQL запросов может быть перечисление и поддержание в соответствие колонок и полей сущности в актуальном состоянии.

Чтобы решить эту проблему можно использовать специальные макрос конструкции внутри SQL запроса в рамках `@Query` аннотации.
Эти конструкции позволяют оперировать [сущностью](#_1) на которую указывают и раскрывать её в определенные SQL конструкции и легко дополнять SQL запросы.
Макрос является помощником при написании SQL запросов, раскрывается в конструкции которые пользователь смог бы написать собственными руками.

Синтаксис макроса выглядит следующем образом: `%{return#selects}`

1. Макрос ограничен синтаксической конструкцией `%{` и `}`
2. Первым указывается цель макроса, это может быть как имя любого аргумента метода, так и возвращаемое значение с помощью ключевого слова `return`
3. Затем используется `#` символ для разделения цели и команды макроса
4. Затем указывается команда макроса, которая говорит в какую именно SQL конструкцию раскрывать сущность

=== ":fontawesome-brands-java: `Java`"

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

#### Команды

Доступные команды макросов:

- `table` - конструкция раскрывает значение сущности в [аннотации](#_2) `@Table` либо если таковая отсутствует то, переводит имя сущности в [snake_lower_case](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/)
- `selects` - создает конструкцию перечисления колонок сущности для `SELECT` запроса
- `inserts` - создает конструкцию таблицы, перечисления колонок и соответствующих полей сущности для `INSERT` запроса
- `updates` - создает конструкцию перечисления колонок и соответствующих полей сущности (за исключением `@id` поля) для `UPDATE` запроса
- `where` - создает конструкцию перечисления колонок со значением из сущности для `WHERE` части запроса

#### Перечисление полей

Макрос поддерживает дополнительный синтаксис по перечислению определенных полей в команде, 
если вдруг требуется сделать частичное обновление или получение данных.
Для этого после команды используется специальная конструкция: `%{return#updates=name}`

**Только** между полями перечисления и символом перечисления могут содержаться пробелы.

Доступны специальные символы перечисления:

1. `=` - только указанные после символа имя полей сущности будут участвовать в раскрытии команды
2. `-=` - все поля сущности за исключением указанных после символа будут участвовать в раскрытии команды

=== ":fontawesome-brands-java: `Java`"

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

##### Идентификатор

При перечислении полей в макросе возможно использовать специальное ключевое слово `@id` 
для того чтобы ссылаться сразу идентификатор сущности проаннотированный [аннотацией](#_3) `@Id`.

Это может быть особенно полезно когда идентификатор является [составным ключом](#_10), для перечисления сразу всех колонок.

=== ":fontawesome-brands-java: `Java`"

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

#### Пример репозитория

Пример полного репозитория со всеми основными методами для оперирования сущностью.

=== ":fontawesome-brands-java: `Java`"

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
        SELECT id, value1, value2, value3 FROM entities WHERE id = :id
        ```
    2.  Раскрывается в запрос:
        ```sql
        SELECT id, value1, value2, value3 FROM entities
        ```
    3.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3) 
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
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
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
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
        fun findById(id: String?): Entity?

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
        SELECT id, value1, value2, value3 FROM entities WHERE id = :id
        ```
    2.  Раскрывается в запрос:
        ```sql
        SELECT id, value1, value2, value3 FROM entities
        ```
    3.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3) 
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
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
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
        ON CONFLICT (id) DO UPDATE 
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        ```
