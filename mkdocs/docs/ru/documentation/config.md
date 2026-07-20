---
description: "Explains Kora configuration system for HOCON and YAML, typed config extraction, config injection, config sources, watchers, and supported value types. Use when working with @ConfigSource, @ConfigValueExtractor, @Environment, @SystemProperties, Config, HoconConfigModule, YamlConfigModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora configuration system for HOCON and YAML, typed config extraction, config injection, config sources, watchers, and supported value types; key triggers include @ConfigSource, @ConfigValueExtractor, @Environment, @SystemProperties, Config, HoconConfigModule, YamlConfigModule."
---

Модуль конфигурации читает настройки приложения из файлов `HOCON` или `YAML`, переменных окружения, системных свойств
`Java` и отображает их на типизированные классы в `Kora`. Полученные объекты конфигурации становятся обычными
компонентами графа зависимостей и могут внедряться в сервисы, клиенты, серверы и другие интеграции.

В `Kora` конфигурация приложения обычно описывается интерфейсом с аннотацией `@ConfigSource`: путь в файле указывает на
читаемую секцию, а методы интерфейса описывают обязательные значения, необязательные значения и значения по умолчанию.
Библиотеки и переиспользуемые формы конфигурации используют `@ConfigValueExtractor`, который создает только правило
извлечения, тогда как конкретный путь выбирается в модуле библиотеки.

Для пошагового разбора перед справочным описанием смотрите [Конфигурация HOCON](../guides/config-hocon.md) и [Конфигурация YAML](../guides/config-yaml.md).

## HOCON { #hocon }

Поддержка [HOCON](https://github.com/lightbend/config/blob/master/HOCON.md) реализована с помощью [Typesafe Config](https://github.com/lightbend/config).
`HOCON` — это формат конфигурационных файлов на основе `JSON`. Он менее строгий, чем `JSON`, и поддерживает подстановки,
значения по умолчанию и удобный синтаксис для вложенных объектов.

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

1. Строковое значение конфигурации
2. Числовое значение конфигурации
3. Обязательное значение конфигурации, подставляемое из переменной окружения `REQUIRED_ENV_VALUE`
4. Необязательное значение конфигурации, подставляемое из переменной окружения `OPTIONAL_ENV_VALUE`; если переменная не найдена, значение конфигурации опускается
5. Значение конфигурации со значением по умолчанию: значение по умолчанию задается как `propDefault = 10`, а `NON_DEFAULT_ENV_VALUE`, если найдено, заменяет его
6. Значение конфигурации, собранное из подстановок других частей конфигурации со значением `Other` между ними
7.  Значение конфигурации в виде списка строк; значение можно задать как массив строк или как строку с разделителем-запятой
8.  Значение конфигурации в виде списка строк; значение можно задать как строку с разделителем-запятой или как массив строк
9.  Значение конфигурации в виде словаря ключ-значение
10. Значение конфигурации в виде отображаемого класса
11. Значение конфигурации в виде списка отображаемых классов

Значения также могут ссылаться на другие ключи конфигурации (само-ссылка / перекрестная ссылка) через `${path}`,
а на переменные окружения — через `${VAR}` (обязательные), `${?VAR}` (необязательные) или через резервный вариант по
умолчанию. Все подстановки разрешаются после слияния каждого слоя, поэтому ссылка может указывать на ключ, определенный
в другом файле или в другом слое конфигурации.

Представление конфигурации в коде:

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

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:config-hocon"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends HoconConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:config-hocon")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule
    ```

### Файл { #file }

По умолчанию ожидаются конфигурационные файлы [`reference.conf` и `application.conf`](https://github.com/lightbend/config#note-about-resolving-substitutions-in-referenceconf-and-applicationconf).

Сначала объединяются все файлы `reference.conf` из classpath, затем поверх неразрешенного `reference.conf` накладывается
`application.conf`, после чего результат разрешается и проверяются обязательные подстановки.

Ожидается, что конфигурация приложения находится в `application.conf`, а конфигурация библиотек — в `reference.conf`.

`HOCON` также поддерживает директиву [`include`](https://github.com/lightbend/config/blob/master/HOCON.md#includes):
файлы, подключенные через `include`, участвуют в том же слиянии и разрешении подстановок, что и основной файл,
и отслеживаются [наблюдателем за конфигурацией](#config-watcher), поэтому изменения во включенном файле также обновляют граф.

Приоритет выбора файла приложения для `HOCON`:

- Использовать файл из `config.resource`, если он указан (файл из каталога `resources`)
- Использовать файл из `config.file`, если он указан (файл из файловой системы)
- Использовать `application.conf`, если он присутствует (файл из каталога `resources`)
- Использовать пустую конфигурацию, если ничего из вышеперечисленного нет

Одновременно можно указать только одно свойство: `config.resource` или `config.file`. Если указаны оба свойства,
приложение не запустится.

===! ":fontawesome-brands-java: `java`"

    Пример указания конфигурации при запуске через `java`:
    ```shell
    java -Dconfig.file=path/to/configFile application
    ```

=== ":simple-kotlin: `gradle`"

    Пример указания конфигурации в `build.gradle`:
    ```groovy
    run {
        jvmArgs += [
                "-Dconfig.file=path/to/configFile"
        ]
    }
    ```

## YAML { #yaml }

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

1. Строковое значение конфигурации
2. Числовое значение конфигурации
3. Обязательное значение конфигурации, подставляемое из переменной окружения `REQUIRED_ENV_VALUE`
4. Необязательное значение конфигурации, подставляемое из переменной окружения `OPTIONAL_ENV_VALUE`; если переменная не найдена, значение конфигурации опускается
5. Значение конфигурации со значением по умолчанию: значение по умолчанию — `10`, а `NON_DEFAULT_ENV_VALUE`, если найдено, заменяет его
6. Значение конфигурации, собранное из подстановок других частей конфигурации со значением `Other` между ними
7.  Значение конфигурации в виде списка строк; значение можно задать как массив строк или как строку с разделителем-запятой
8.  Значение конфигурации в виде списка строк; значение можно задать как строку с разделителем-запятой или как массив строк
9.  Значение конфигурации в виде словаря ключ-значение
10. Значение конфигурации в виде отображаемого класса
11. Значение конфигурации в виде списка отображаемых классов

Представление конфигурации в коде:

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

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:config-yaml"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends YamlConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:config-yaml")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : YamlConfigModule
    ```

### Файл { #file-2 }

По умолчанию ожидаются конфигурационные файлы `reference.yaml` и `application.yaml`.

Сначала объединяются все файлы `reference.yaml` из classpath, затем поверх `reference.yaml` накладывается
`application.yaml`, после чего результат разрешается и проверяются обязательные подстановки.

Ожидается, что конфигурация приложения находится в `application.yaml`, а конфигурация библиотек — в `reference.yaml`.

Приоритет выбора файла приложения для `YAML`:

- Использовать файл из `config.resource`, если он указан (файл из каталога `resources`)
- Использовать файл из `config.file`, если он указан (файл из файловой системы)
- Использовать `application.yaml`, если он присутствует (файл из каталога `resources`)
- Использовать пустую конфигурацию, если ничего из вышеперечисленного нет

Одновременно можно указать только одно свойство: `config.resource` или `config.file`. Если указаны оба свойства,
приложение не запустится.

===! ":fontawesome-brands-java: `java`"

    Пример указания конфигурации при запуске через `java`:
    ```shell
    java -Dconfig.file=path/to/configFile application
    ```

=== ":simple-kotlin: `gradle`"

    Пример указания конфигурации в `build.gradle`:
    ```groovy
    run {
        jvmArgs += [
                "-Dconfig.file=path/to/configFile"
        ]
    }
    ```

## Пользовательская конфигурация { #custom-configuration }

Пользовательская конфигурация отображает секцию конфигурационного файла на пользовательский тип.
Затем этот тип можно внедрять как зависимость точно так же, как любой другой компонент.

### Конфигурация приложения { #application-config }

Для создания пользовательских конфигураций в приложении используйте аннотацию `@ConfigSource`.
Она генерирует `ConfigValueExtractor` для интерфейса и модуль, который добавляет готовый объект конфигурации в граф
зависимостей. Значение аннотации указывает на путь секции внутри итоговой конфигурации:

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

Этот пример кода добавит экземпляр класса `FooServiceConfig` в контейнер зависимостей, который при создании будет ожидать конфигурацию следующего вида:

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

### Конфигурация библиотеки { #library-config }

Для создания пользовательских конфигураций в библиотеках используйте аннотацию `@ConfigValueExtractor`.
Она создает правило извлечения значения из `ConfigValue<?>`, но не привязывает его к конкретному пути конфигурации.
Путь выбирается в фабричном методе модуля библиотеки, поэтому одну и ту же форму конфигурации можно переиспользовать для разных секций.
`@ConfigValueExtractor` можно использовать на интерфейсе, `record` или классе `Java`, а также на интерфейсе или `data class` `Kotlin`.

У аннотации есть параметр `mapNullAsEmptyObject` (по умолчанию: `true`). Когда он включен, отсутствующая секция
трактуется как пустой объект: обязательные поля по-прежнему приводят к ошибке, а необязательные поля и значения по
умолчанию ведут себя так, как будто присутствовала пустая секция.
Если `mapNullAsEmptyObject = false`, отсутствующая секция трактуется как `null` для всего объекта конфигурации.

Рассмотрим такой класс конфигурации:

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

Чтобы библиотека предоставляла конфигурацию, реализуйте фабрику в модуле:

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

Затем, после подключения `FooLibraryModule` в приложении, `FooLibraryConfig` можно использовать как зависимость в других классах.

### Обязательные значения { #required-values }

По умолчанию все объявленные в конфигурации значения считаются **обязательными** (`NotNull`) и должны присутствовать в
итоговой конфигурации. Если обязательное значение отсутствует или имеет значение `null`, приложение завершится с ошибкой
при создании объекта конфигурации.

### Необязательные значения { #optional-values }

Если требуется указать значение из конфигурационного файла как необязательное, можно использовать такой формат:

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

    1.  Подойдет любая аннотация `@Nullable`, например `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Используйте синтаксис [null-safety `Kotlin`](https://kotlinlang.org/docs/null-safety.html) и пометьте параметр как nullable:

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String?

        fun baz(): Int
    }
    ```

Также поддерживается тип возвращаемого значения `Optional<T>` (отсутствующее значение отображается на `Optional.empty()`),
но значение `@Nullable` (или nullable-тип `Kotlin`) является рекомендуемым стилем.

### Значения по умолчанию { #default-values }

Если требуется задать значение по умолчанию при отображении конфигурации, используйте `default`-метод:

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

### Гибкие имена ключей { #relaxed-key-names }

Ключи конфигурации сопоставляются с гибким именованием. Имя метода сравнивается с ключом в файле не только в его точной
форме, но и в вариантах `kebab-case` и `snake_case`. Это означает, что метод `someBarString()` одинаково разрешается из
`someBarString`, `some-bar-string` или `some_bar_string` в конфигурационном файле, поэтому команды, предпочитающие ключи
в стиле kebab-case или snake_case, могут сохранять свой стиль без переименования методов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigValueExtractor
    public interface BarConfig {

        String someBarString();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigValueExtractor
    interface BarConfig {

        fun someBarString(): String
    }
    ```

Все три написания ключа ниже читаются в `someBarString()`:

===! ":material-code-json: `Hocon`"

    ```javascript
    bar {
      someBarString = "value"        //(1)!
      # some-bar-string = "value"    //(2)!
      # some_bar_string = "value"    //(3)!
    }
    ```

    1. Точное написание имени метода в `camelCase`
    2. Гибкое написание в `kebab-case`
    3. Гибкое написание в `snake_case`

=== ":simple-yaml: `YAML`"

    ```yaml
    bar:
      someBarString: "value"         #(1)!
      # some-bar-string: "value"     #(2)!
      # some_bar_string: "value"     #(3)!
    ```

    1. Точное написание имени метода в `camelCase`
    2. Гибкое написание в `kebab-case`
    3. Гибкое написание в `snake_case`

### Рекомендуемый стиль { #recommended-configuration-style }

Обычно удобнее описывать конфигурацию как отдельный тип для конкретной интеграции или подсистемы:
HTTP-клиента, подключения к внешнему сервису, обработчика очереди и так далее. Такой тип должен четко разделять
обязательные значения, необязательные значения и значения, приходящие из переменных окружения.

В примере ниже:

1. `baseUrl` — обязательное значение из конфигурационного файла
2. `clientName` — необязательное значение из переменной окружения `ORDERS_CLIENT_NAME`
3. `token` — обязательное значение из переменной окружения `ORDERS_API_TOKEN`
4. `requestTimeout` имеет значение по умолчанию `2s` и может быть переопределено необязательной переменной окружения `ORDERS_REQUEST_TIMEOUT`

===! ":fontawesome-brands-java: `Java`"

    ```java
    import java.time.Duration;
    import javax.annotation.Nullable;

    @ConfigSource("clients.orders")
    public interface OrdersClientConfig {

        String baseUrl();

        @Nullable
        String clientName();

        String token();

        Duration requestTimeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import java.time.Duration

    @ConfigSource("clients.orders")
    interface OrdersClientConfig {

        fun baseUrl(): String

        fun clientName(): String?

        fun token(): String

        fun requestTimeout(): Duration
    }
    ```

===! "`HOCON`"

    ```javascript
    clients {
      orders {
        baseUrl = "https://orders.example.com"
        clientName = ${?ORDERS_CLIENT_NAME}
        token = ${ORDERS_API_TOKEN}
        requestTimeout = 2s
        requestTimeout = ${?ORDERS_REQUEST_TIMEOUT}
      }
    }
    ```

=== "`YAML`"

    ```yaml
    clients:
      orders:
        baseUrl: "https://orders.example.com"
        clientName: ${?ORDERS_CLIENT_NAME}
        token: ${ORDERS_API_TOKEN}
        requestTimeout: ${?ORDERS_REQUEST_TIMEOUT:2s}
    ```

Это сохраняет структуру конфигурации читаемой: обязательные настройки видны в типе конфигурации, секреты можно передавать
через переменные окружения, а безопасные значения по умолчанию остаются прямо в конфигурационном файле.

## Внедрение конфигурации { #injecting-configuration }

Можно внедрить базовый класс `ru.tinkoff.kora.config.common.Config`, который представляет дерево конфигурации и дает
доступ к значениям через метод `get(...)`. Итоговая конфигурация состоит из нескольких слоев:

- Переменные окружения
- Системные свойства `Java`
- Конфигурационный файл

Слои объединяются в таком порядке: переменные окружения, затем системные свойства, затем конфигурационный файл
приложения. Каждый следующий слой накладывается на предыдущий.

### Переменные окружения { #environment-variables }

Если требуется внедрить конфигурацию, содержащую **только** [переменные окружения](https://en.wikipedia.org/wiki/Environment_variable),
используйте аннотацию `@Environment` как тег для класса конфигурации:

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

### Системные свойства { #system-variables }

Если требуется внедрить конфигурацию, содержащую **только** [системные свойства `Java`](https://www.baeldung.com/java-system-get-property-vs-system-getenv),
используйте аннотацию `@SystemProperties` как тег для класса конфигурации:

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

### Конфигурационный файл { #configuration-file }

Если требуется внедрить конфигурацию приложения, состоящую **только** из конфигурационного файла,
используйте аннотацию `@ApplicationConfig` как тег для класса конфигурации:

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

### Итоговая конфигурация { #resulting-configuration }

Если требуется внедрить полную итоговую конфигурацию приложения, которая состоит из конфигурационного файла,
переменных окружения и системных свойств, просто внедрите класс конфигурации без тега:

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

### Чтение сырых значений Config { #reading-raw-config-values }

Когда внедряется сырой `Config`, значения читаются через метод `get(...)`, который возвращает узел `ConfigValue<?>`
для запрошенного пути. `ConfigValue<?>` — это sealed-тип с типизированными аксессорами: `asString()`, `asNumber()`,
`asBoolean()`, `asObject()`, `asArray()` и `isNull()`. Если значение имеет неожиданный тип, аксессор выбрасывает
`ConfigValueExtractionException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        public FooService(Config config) {
            ConfigValue<?> value = config.get("services.foo.bar");
            if (!value.isNull()) {
                String bar = value.asString();
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(config: Config) {

        init {
            val value = config["services.foo.bar"]
            if (!value.isNull) {
                val bar = value.asString()
            }
        }
    }
    ```

Как отмечено в разделе [Рекомендации](#recommendations), предпочитайте типизированные [пользовательские конфигурации](#custom-configuration)
чтению сырого `Config`; используйте API сырого чтения только для динамического или обобщенного доступа.

???+ warning "Рекомендация"

    **Мы не рекомендуем** использовать `ru.tinkoff.kora.config.common.Config` напрямую как зависимость в компонентах,
    потому что при обновлении конфигурации будут обновлены и все компоненты графа, которые ее используют.
    Мы рекомендуем всегда создавать [пользовательские конфигурации](#custom-configuration).

## Наблюдатель за конфигурацией { #config-watcher }

По умолчанию в `Kora` есть наблюдатель за конфигурационным файлом, который проверяет файл приложения на изменения и
запускает обновление графа зависимостей при изменении файла. Проверка выполняется каждые `1000` миллисекунд.

Для `HOCON` наблюдатель также отслеживает файлы, подключенные через `include` внутри основного конфигурационного файла.
Если такой включенный файл изменяется, конфигурация перечитывается, и граф зависимостей также обновляется.

Наблюдатель работает только для файловой конфигурации, имеющей отслеживаемый источник. Если конфигурация пришла из
ресурса внутри архива или была собрана без файла приложения, на диске нечего обновлять.

Наблюдатель можно отключить с помощью:

1. Переменной окружения `KORA_CONFIG_WATCHER_ENABLED` (по умолчанию: `true`)
2. Системного свойства `kora.config.watcher.enabled` (по умолчанию: `true`)

## Поддерживаемые типы { #supported-types }

Экстракторы конфигурации предоставляют обширный список поддерживаемых типов, который покрывает большинство значений,
которые могут понадобиться в пользовательских конфигурациях. Если стандартного преобразования недостаточно, поведение
можно расширить пользовательским компонентом `ConfigValueExtractor<T>`.

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
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime
    * ConfigValue.ObjectValue
    * Enum (любой пользовательский `enum`; отображение можно переопределить через `toString()`)
    * `Optional<T>` (где `T` — любой поддерживаемый тип)
    * `List<T>` (где `T` — любой поддерживаемый тип)
    * `Set<T>` (где `T` — любой поддерживаемый тип)
    * `Map<String, V>` или `Map<K, V>` (где `K` и `V` поддерживаются соответствующими экстракторами)
    * `Either<A, B>` (где `A` и `B` — любые поддерживаемые типы)

### Пользовательский экстрактор { #custom-extractor }

Если для типа нет стандартного преобразования или требуется специальная логика разбора, добавьте пользовательский
компонент `ConfigValueExtractor<T>`. Метод `extract(...)` получает значение конфигурации как `ConfigValue<?>`
и должен вернуть готовое значение требуемого типа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class TokenConfigValueExtractor implements ConfigValueExtractor<Token> {

        @Override
        public Token extract(ConfigValue<?> value) {
            if (value instanceof ConfigValue.NullValue) {
                return null;
            }
            return new Token(value.asString());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class TokenConfigValueExtractor : ConfigValueExtractor<Token> {

        override fun extract(value: ConfigValue<*>): Token? {
            if (value is ConfigValue.NullValue) {
                return null
            }
            return Token(value.asString())
        }
    }
    ```

Если конкретный экстрактор должен использоваться только для одного поля, укажите его через `@Mapping`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigValueExtractor
    public interface ApiConfig {

        @Mapping(TokenConfigValueExtractor.class)
        Token token();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigValueExtractor
    interface ApiConfig {

        @Mapping(TokenConfigValueExtractor::class)
        fun token(): Token
    }
    ```

### Duration { #duration }

`Duration` можно задать как число или строку.
Если указано число, оно трактуется как миллисекунды.
Если указана строка, поддерживается формат `java.time.Duration`, например `PT10S`, а также стиль `HOCON`:

- `500ms`
- `10 seconds`
- `2 minutes`
- `1h`
- `1d`

### Period { #period }

`Period` можно задать как число или строку.
Если указано число, оно трактуется как дни.
Если указана строка, поддерживаются такие единицы:

- `d` / `days`
- `w` / `weeks`
- `m` / `mo` / `months`
- `y` / `years`

Например, `7d`, `2 weeks`, `3mo` или `1 year`.

### Size { #size }

`Size` — это специальный тип, который позволяет указывать размеры в байтах в удобной для человека нотации: согласно
стандарту [IEEE 1541-2002](https://en.wikipedia.org/wiki/IEEE_1541-2002) (двоичный) или стандарту
[SI](https://en.wikipedia.org/wiki/Binary_prefix) (десятичный).

Примеры значений:

- `1Mb` — 1 мегабайт (`1.000.000` байт)
- `1Mib` — 1 мебибайт (`1.048.576` байт)
- `1024b` — 1024 байта
- `1024` — 1024 байта

Если указано просто число без суффикса, считается, что указаны байты.

### Either { #either }

`Either<A, B>` позволяет одному полю принимать две альтернативные формы. Экстрактор сначала пробует левый тип `A`, и если
извлечение завершается любым исключением, откатывается к правому типу `B`. Это полезно, когда значение может быть либо
простым скаляром, либо структурированным объектом.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import ru.tinkoff.kora.common.util.Either;

    @ConfigValueExtractor
    public interface EndpointConfig {

        String host();

        int port();
    }

    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        Either<String, EndpointConfig> endpoint();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import ru.tinkoff.kora.common.util.Either

    @ConfigValueExtractor
    interface EndpointConfig {

        fun host(): String

        fun port(): Int
    }

    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun endpoint(): Either<String, EndpointConfig>
    }
    ```

Обе эти формы допустимы для поля `endpoint`:

===! ":material-code-json: `Hocon`"

    ```javascript
    services {
      foo {
        endpoint = "https://example.com"   //(1)!
      }
    }
    ```

    1. Разрешается как левый тип (`String`)

=== ":simple-yaml: `YAML`"

    ```yaml
    services:
      foo:
        endpoint:                          #(1)!
          host: "example.com"
          port: 8080
    ```

    1. Разрешается как правый тип (`EndpointConfig`)

Используйте `isLeft()` / `isRight()`, чтобы проверить, какая сторона была разрешена, и `left()` / `right()`, чтобы прочитать значение.
