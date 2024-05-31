Модуль конфигурации отвечает за отображение значений из файлов конфигурации на классы в Kora 
и их последующее использование для настройки приложения.

## HOCON

Поддержка [HOCON](https://github.com/lightbend/config/blob/master/HOCON.md) реализована с помощью [Typesafe Config](https://github.com/lightbend/config).
HOCON — это формат конфиг-файлов, основанный на JSON. Формат менее строгий нежели JSON и обладает слегка другим синтаксисом.

Пример HOCON конфигурации:

```javascript
services {
    foo {
      bar = "SomeValue" //(1)!
      baz = 10 //(2)!
      propRequired = ${REQUIRED_ENV_VALUE} //(3)!
      propOptional = ${?OPTIONAL_ENV_VALUE} //(4)!
      propDefault = 10
      propDefault = ${?NON_DEFAULT_ENV_VALUE} //(5)!
      propReference = ${services.foo.bar}Other${services.foo.baz} //(6)!
      propArray = ["v1", "v2"] //(7)!
      propMap { //(8)!
          "k1" = "v1"
          "k2" = "v2"
      }
    }
}
```

1.  Cтроковое значение конфигурации
2.  Числовое значение конфигурации
3.  Обязательное значение конфигурации которое подставляется из переменной окружения `REQUIRED_ENV_VALUE`
4.  Необязательное значение конфигурации которое подставляется из переменной окружения `OPTIONAL_ENV_VALUE`, если таковой переменной не найдено то значение конфигурации будет опущено
5.  Значение конфигурации со значением по умолчанию, значение по умолчанию указывается в `propDefault = 10` и если будет найдена переменная окружения `NON_DEFAULT_ENV_VALUE` то ее значение заменит значение по умолчанию
6.  Значение конфигурации собранное из подстановок других частей конфигурации и значением `Other` между
7.  Значение конфигурации в виде массива, можно также указывать значение как строка разделенная запятыми
8.  Значение конфигурации в виде словаря ключ и значение

### Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:config-hocon"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends HoconConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:config-hocon")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule
    ```

### Файл

По умолчанию ожидаются файлы конфигурации [reference.conf и application.conf](https://github.com/lightbend/config#note-about-resolving-substitutions-in-referenceconf-and-applicationconf)

Во-первых, все файлы `reference.conf` объединяются, во-вторых, файл `application.conf` накладывается на неразрешенный 
файл `reference.conf`, результат вычисляется и проверяется что все значения переменных доступны.

Предполагается что конфигурация приложения находится в файле `application.conf`, а конфигурации библиотек в `reference.conf`.

Приоритет считывания `application.conf` файла конфигурации:

- Использовать файл из `config.resource` если указан (файл из `resources` директории)
- Использовать файл из `config.file` если указан (файл из файловой системы)
- Использовать файл `application.conf` если имеется (файл из `resources` директории)
- Используется пустой файл конфигурации если все указанное выше отсутствует

## YAML

Поддержка [YAML](https://yaml.org/) реализована с помощью [SnakeYAML](https://github.com/snakeyaml/snakeyaml).

Пример YAML конфигурации:

```yaml
services:
  foo:
    bar: "SomeValue" #(1)!
    baz: 10 #(2)!
    propRequired: ${REQUIRED_ENV_VALUE} #(3)!
    propOptional: ${?OPTIONAL_ENV_VALUE} #(4)!
    propDefault: ${?NON_DEFAULT_ENV_VALUE:10} #(5)!
    propReference: ${services.foo.bar}Other${services.foo.baz} #(6)!
    propArray: ["v1", "v2"] #(7)!
    propMap: #(8)!
      k1: "v1"
      k2: "v2"
```

1.  Cтроковое значение конфигурации
2.  Числовое значение конфигурации
3.  Обязательное значение конфигурации которое подставляется из переменной окружения `REQUIRED_ENV_VALUE`
4.  Необязательное значение конфигурации которое подставляется из переменной окружения `OPTIONAL_ENV_VALUE`, если таковой переменной не найдено то значение конфигурации будет опущено
5.  Значение конфигурации со значением по умолчанию, значение по умолчанию равно `10` и если будет найдена переменная окружения `NON_DEFAULT_ENV_VALUE` то ее значение заменит значение по умолчанию
6.  Значение конфигурации собранное из подстановок других частей конфигурации и значением `Other` между
7.  Значение конфигурации в виде массива, можно также указывать значение как строка разделенная запятыми
8.  Значение конфигурации в виде словаря ключ и значение

### Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:config-yaml"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends YamlConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:config-yaml")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : YamlConfigModule
    ```

### Файл

По умолчанию ожидаются файлы конфигурации `reference.yaml` и `application.yaml`.

Во-первых, все файлы `reference.yaml` объединяются, во-вторых, файл `application.yaml` накладывается на неразрешенный
файл `reference.yaml`, результат вычисляется и проверяется что все значения переменных доступны.

Предполагается что конфигурация приложения находится в файле `application.yaml`, а конфигурации библиотек в `reference.yaml`.

Приоритет считывания `application.yaml` файла конфигурации:

- Использовать файл из `config.resource` если указан (файл из `resources` директории)
- Использовать файл из `config.file` если указан (файл из файловой системы)
- Использовать файл `application.yaml` если имеется (файл из `resources` директории)
- Используется пустой файл конфигурации если все указанное выше отсутствует

## Пользовательские конфигурации

Пользовательская конфигурация предоставляет собой отображение файла конфигурации на пользовательский интерфейс.
Такой пользовательский интерфейс в последствии может быть внедрен как зависимость наравне с другими компонентами.

### В приложении

Для создания пользовательских конфигураций следует использовать аннотацию `@ConfigSource`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        String bar();
        
        int baz();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String

        fun baz(): Int
    }
    ```

Этот пример кода добавит в контейнер экземпляр класса `FooServiceConfig`, который при создании будет ожидать конфигурацию следующего вида:

=== ":material-code-json: `Hocon`"

    ```javascript
    services {
      foo {
        bar = "SomeValue"
        baz = 10
      }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    services:
      foo:
        bar: "SomeValue"
        baz: 10
    ```

После этого класс `FooServiceConfig` уже можно использовать как зависимость в других классах:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final FooServiceConfig config;

        public FooService(FooServiceConfig config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(val config: FooServiceConfig)
    ```

### В библиотеке

Для создания пользовательских конфигураций в рамках пользовательских библиотеках следует использовать аннотацию `@ConfigValueExtractor` 
которая создаст правила обработки файла конфигурации в экземпляр класса конфигурации.

Рассмотрим пример когда есть такой класс конфигурации:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigValueExtractor
    public interface FooLibraryConfig {

        String bar();
        
        int baz();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigValueExtractor
    interface FooLibraryConfig {

        fun bar(): String

        fun baz(): Int
    }
    ```

Для того чтобы библиотека предоставляла конфигурацию, требуется реализовать фабрику в модуле:

=== ":fontawesome-brands-java: `Java`"

    ```java
    public interface FooLibraryModule {

        default FooLibraryConfig config(Config config, ConfigValueExtractor<FooLibraryConfig> extractor) {
            return extractor.extract(config.get("library.foo"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface FooLibraryModule {

        fun config(config: Config, extractor: ConfigValueExtractor<FooLibraryConfig>): FooLibraryConfig {
            return extractor.extract(config["library.foo"])!!
        }
    }
    ```

Фабрика будет ожидать конфигурацию следующего вида:

=== ":material-code-json: `Hocon`"

    ```javascript
    library {
      foo {
        bar = "SomeValue"
        baz = 10
      }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    library:
      foo:
        bar: "SomeValue"
        baz: 10
    ```

Затем подключив модуль `FooLibraryModule` в приложении, конфиг `FooServiceConfig` можно использовать как зависимость в других классах.

### Обязательные значения

По умолчанию все значения объявленные в конфиге считаются **обязательными** (*NotNull*) и должны присутствовать в файле конфигурации.

### Необязательные значения

Если есть необходимость указать значение из файла конфигурации как необязательное, то можно воспользоваться таким форматом:

=== ":fontawesome-brands-java: `Java`"

    Предлагается использовать аннотацию `@Nullable` над сигнатурой метода:

    ```java
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        @Nullable//(1)!
        String bar();

        int baz();
    }
    ```

    1.  Подойдет любая аннотация `@Nullable`, такие как `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использовать [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис и помечать такой параметр как Nullable:

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String?

        fun baz(): Int
    }
    ```

### Значения по умолчанию

Если есть необходимость использовать в классе значения по умолчанию, то можно воспользоваться таким форматом:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        String bar();

        default int baz() {
            return 42;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String

        fun baz(): Int {
            return 42
        }
    }
    ```

## Внедрение конфигурации

Можно внедрять базовый класс `ru.tinkoff.kora.config.common.Config` который предоставляет из себя общую абстракцию над
отображением файла конфигурации. Результирующие отображение конфигурации состоит из нескольких слоев которые представляют из себя:

- Переменные окружения
- Системные переменные
- Файл конфигурации

### Переменные окружения

В случае если требуется внедрить конфигурацию **только** [переменных окружения](https://ru.hexlet.io/courses/cli-basics/lessons/environment-variables/theory_unit), 
то для этого можно использовать аннотацию `@Environment` как тег для класса конфигурации:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(@Environment Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(@Environment val config: Config)
    ```

### Системные переменные

В случае если требуется внедрить конфигурацию **только** [системных переменных](https://www.baeldung.com/java-system-get-property-vs-system-getenv),
то для этого можно использовать аннотацию `@SystemProperties` как тег для класса конфигурации:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(@SystemProperties Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(@SystemProperties val config: Config)
    ```

### Файл конфигурации

В случае если требуется внедрить полную конфигурацию приложения которая состоит **только** из файла конфигурации, 
то для этого можно использовать аннотацию `@ApplicationConfig` как тег для класса конфигурации:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(@ApplicationConfig Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(@ApplicationConfig val config: Config)
    ```

### Результирующая конфигурация

В случае если требуется внедрить полную конфигурацию приложения которая состоит из файла конфигурации,
переменных окружения и системных переменных, то для этого требуется просто внедрить класс конфигурации без тега:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(val config: Config)
    ```

### Рекомендации

???+ warning "Совет"

    **Мы не рекомендуем** использовать напрямую `ru.tinkoff.kora.config.common.Config` как зависимость в компонентах,
    так как при обновлении конфигурации это повлечет обновление всех компонент графа которые используют его у себя,
    рекомендуется всегда создавать [пользовательские конфигурации](#_5).

## Поддерживаемые типы

Экстракторы конфигурации предоставляют обширный список поддерживаемых типов, который охватывает большинство из того,
что вам может понадобиться для указания в пользовательских конфигурациях, либо вы можете расширить поведение собственным `ConfigValueExtractor<T>` компонентом.

??? abstract "Список поддерживаемых типов"

    * boolean / Boolean
    * short / Short
    * int / Integer
    * long / Long
    * double / Double
    * float / Float
    * double[]
    * String
    * BigInteger
    * BigDecimal
    * Period
    * Duration
    * Properties
    * Pattern
    * UUID
    * Properties
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime
    * Enum (любой пользовательский ENUM тип)
    * `List<T>` (где `T` любой из выше перечисленных типов)
    * `Set<T>` (где `T` любой из выше перечисленных типов)
    * `Map<String, T>` (где `T` любой из выше перечисленных типов)
    * `Either<A, B>` (где `A` и `B` любой из выше перечисленных типов)
