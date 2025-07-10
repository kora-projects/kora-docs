Модуль конфигурации отвечает за отображение значений из файлов конфигурации на классы в Kora 
и их последующее использование для настройки приложения.

## HOCON

Поддержка [HOCON](https://github.com/lightbend/config/blob/master/HOCON.md) реализована с помощью [Typesafe Config](https://github.com/lightbend/config).
HOCON — это формат конфиг-файлов, основанный на JSON. Формат менее строгий нежели JSON и обладает слегка другим синтаксисом.

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
      propArrayAsString = "v1, v2" //(8)!
      propMap = { //(9)!
          "k1" = "v1"
          "k2" = "v2"
      }
      propObject = { //(10)!
          p1 = "v1"
          p2 = "v2"
      }
      propObjects = [ //(11)!
        {
          p1 = "v1"
          p2 = "v2"
        },
        {
          p1 = "v3"
          p2 = "v4"
        }
      ]
    }
}
```

1.  Cтроковое значение конфигурации
2.  Числовое значение конфигурации
3.  Обязательное значение конфигурации которое подставляется из переменной окружения `REQUIRED_ENV_VALUE`
4.  Необязательное значение конфигурации которое подставляется из переменной окружения `OPTIONAL_ENV_VALUE`, если таковой переменной не найдено то значение конфигурации будет опущено
5.  Значение конфигурации со значением по умолчанию, значение по умолчанию указывается в `propDefault = 10` и если будет найдена переменная окружения `NON_DEFAULT_ENV_VALUE` то ее значение заменит значение по умолчанию
6.  Значение конфигурации собранное из подстановок других частей конфигурации и значением `Other` между
7.  Значение конфигурации списка строк, значение задается как массив строк либо также можно задать как строку, где значения разделены запятыми
8.  Значение конфигурации списка строк, значение задается как строка, где значения разделены запятыми либо также можно задать как массив строк
9.  Значение конфигурации в виде словаря ключ и значение
10. Значение конфигурации в виде отображенного класса
11. Значение конфигурации в виде списка отображенных классов

Отображение конфигурации в коде:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("services.foo")
    public interface FooConfig {

        String bar();

        Integer baz();

        String propRequired();

        @Nullable
        String propOptional();

        Integer propDefault();

        String propReference();

        List<String> propArray();

        List<String> propArrayAsString();

        Map<String, String> propMap();

        @ConfigValueExtractor
        public interface ObjectConfig {
            
            String p1();

            String p2();
        }

        ObjectConfig propObject();

        List<ObjectConfig> propObjects();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("services.foo")
    interface FooConfig {

        fun bar(): String

        fun baz(): Int

        fun propRequired(): String

        fun propOptional(): String?

        fun propDefault(): Int

        fun propReference(): String

        fun propArray(): List<String>

        fun propArrayAsString(): List<String>

        fun propMap(): Map<String, String>

        @ConfigValueExtractor
        interface ObjectConfig {
            
            fun p1(): String

            fun p2(): String
        }

        fun propObject(): ObjectConfig

        fun propObjects(): List<ObjectConfig>
    }
    ```

### Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:config-hocon"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends HoconConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
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

===! ":fontawesome-brands-java: `java`"

    Пример указания конфига при запуске в терминале через `java`:
    ```shell
    java -Dconfig.file=path/to/configFile application
    ```

=== ":simple-kotlin: `gradle`"

    Пример указания конфига в `build.gradle`:
    ```groovy
    run {
        jvmArgs += [
            "-Dconfig.file=path/to/configFile",
        ]
    }
    ```

## YAML

Поддержка [YAML](https://yaml.org/) реализована с помощью [SnakeYAML](https://github.com/snakeyaml/snakeyaml).

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
    propArrayAsString: "v1, v2" #(8)!
    propMap: #(9)!
      k1: "v1"
      k2: "v2"
    propObject: #(10)!
      p1: "v1"
      p2: "v2"
    propObjects: #(11)!
      - p1: "v1"
        p2: "v2"
      - p1: "v1"
        p2: "v2"
```

1.  Cтроковое значение конфигурации
2.  Числовое значение конфигурации
3.  Обязательное значение конфигурации которое подставляется из переменной окружения `REQUIRED_ENV_VALUE`
4.  Необязательное значение конфигурации которое подставляется из переменной окружения `OPTIONAL_ENV_VALUE`, если таковой переменной не найдено то значение конфигурации будет опущено
5.  Значение конфигурации со значением по умолчанию, значение по умолчанию равно `10` и если будет найдена переменная окружения `NON_DEFAULT_ENV_VALUE` то ее значение заменит значение по умолчанию
6.  Значение конфигурации собранное из подстановок других частей конфигурации и значением `Other` между
7.  Значение конфигурации списка строк, значение задается как массив строк либо также можно задать как строку, где значения разделены запятыми
8.  Значение конфигурации списка строк, значение задается как строка, где значения разделены запятыми либо также можно задать как массив строк
9.  Значение конфигурации в виде словаря ключ и значение
10. Значение конфигурации в виде отображенного класса
11. Значение конфигурации в виде списка отображенных классов

Отображение конфигурации в коде:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("services.foo")
    public interface FooConfig {

        String bar();

        Integer baz();

        String propRequired();

        @Nullable
        String propOptional();

        Integer propDefault();

        String propReference();

        List<String> propArray();

        List<String> propArrayAsString();

        Map<String, String> propMap();

        @ConfigValueExtractor
        public interface ObjectConfig {
            
            String p1();

            String p2();
        }

        ObjectConfig propObject();

        List<ObjectConfig> propObjects();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("services.foo")
    interface FooConfig {

        fun bar(): String

        fun baz(): Int

        fun propRequired(): String

        fun propOptional(): String?

        fun propDefault(): Int

        fun propReference(): String

        fun propArray(): List<String>

        fun propArrayAsString(): List<String>

        fun propMap(): Map<String, String>

        @ConfigValueExtractor
        interface ObjectConfig {
            
            fun p1(): String

            fun p2(): String
        }

        fun propObject(): ObjectConfig

        fun propObjects(): List<ObjectConfig>
    }
    ```

### Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:config-yaml"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends YamlConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
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

===! ":fontawesome-brands-java: `java`"

    Пример указания конфига при запуске в терминале через `java`:
    ```shell
    java -Dconfig.file=path/to/configFile application
    ```

=== ":simple-kotlin: `gradle`"

    Пример указания конфига в `build.gradle`:
    ```groovy
    run {
        jvmArgs += [
            "-Dconfig.file=path/to/configFile",
        ]
    }
    ```

## Пользовательские конфигурации

Пользовательская конфигурация предоставляет собой отображение файла конфигурации на пользовательский интерфейс.
Такой пользовательский интерфейс в последствии может быть внедрен как зависимость наравне с другими компонентами.

### В приложении

Для создания пользовательских конфигураций следует использовать аннотацию `@ConfigSource`:

===! ":fontawesome-brands-java: `Java`"

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

===! ":material-code-json: `Hocon`"

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

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

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

===! ":material-code-json: `Hocon`"

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

===! ":fontawesome-brands-java: `Java`"

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

Если есть необходимость использовать задать в отображении значение по умолчанию, то можно воспользоваться `default` модификатором:

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

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

## Наблюдатель

По умолчанию в Kora работает наблюдатель за файлом конфигурации который обновляет его содержимое, 
что влечет в случае изменения файла конфигурации обновление графа зависимостей для компонент которые затронули изменения.

Можно отключить наблюдатель с помощь:

1. Переменной окружения `KORA_CONFIG_WATCHER_ENABLED` 
2. Системного свойства `kora.config.watcher.enabled`

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
    * Size
    * Properties
    * Pattern
    * UUID
    * Properties
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime
    * Enum (любой пользовательский ENUM тип) (Переопределить соответствие можно через переопределение `toString()`)
    * `List<T>` (где `T` любой из выше перечисленных типов)
    * `Set<T>` (где `T` любой из выше перечисленных типов)
    * `Map<K, V>` (где `K` или `V` любой из выше перечисленных типов)
    * `Either<A, B>` (где `A` и `B` любой из выше перечисленных типов)

### Размер

`Size` - специальный тип который позволяет задавать размер байт в удобной человеку системе исчислений по стандарту [IEEE 1541—2002](https://ru.ruwiki.ru/wiki/IEEE_1541-2002) (двоичный), так и в стандарте [СИ](https://ru.ruwiki.ru/wiki/%D0%95%D0%B4%D0%B8%D0%BD%D0%B8%D1%86%D1%8B_%D0%B8%D0%B7%D0%BC%D0%B5%D1%80%D0%B5%D0%BD%D0%B8%D1%8F_%D1%91%D0%BC%D0%BA%D0%BE%D1%81%D1%82%D0%B8_%D0%BD%D0%BE%D1%81%D0%B8%D1%82%D0%B5%D0%BB%D0%B5%D0%B9_%D0%B8_%D0%BE%D0%B1%D1%8A%D1%91%D0%BC%D0%B0_%D0%B8%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D0%B8%D0%B8#%D0%91%D0%B0%D0%B9%D1%82) (десятичный).

Примеры значений:

- `1Mb` - 1 мегабайт (`1.000.000` байт)
- `1Mib` - 1 мегабит (`1.048.576` байт)
- `1024b` - 1024 байт
- `1024` - 1024 байт

Если указано просто число без суффикса, то считается что указаны байты.
