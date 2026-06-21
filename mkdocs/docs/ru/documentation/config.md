---
description: "Explains Kora configuration system for HOCON and YAML, typed config extraction, config injection, config sources, watchers, and supported value types. Use when working with @ConfigSource, @ConfigValueExtractor, @Environment, @SystemProperties, Config, HoconConfigModule, YamlConfigModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora configuration system for HOCON and YAML, typed config extraction, config injection, config sources, watchers, and supported value types; key triggers include @ConfigSource, @ConfigValueExtractor, @Environment, @SystemProperties, Config, HoconConfigModule, YamlConfigModule."
---

Модуль конфигурации отвечает за чтение настроек приложения из файлов `HOCON` или `YAML`, переменных окружения,
системных свойств `Java` и их отображение на типизированные классы в `Kora`.
Полученные объекты конфигурации становятся обычными компонентами графа зависимостей и могут внедряться в сервисы,
клиенты, серверы и другие интеграции.

В `Kora` конфигурация обычно описывается интерфейсом с аннотацией `@ConfigSource`: путь в файле указывает,
какую секцию нужно прочитать, а методы интерфейса описывают обязательные, необязательные и значения по умолчанию.
Для библиотек и переиспользуемых форм конфигурации используется `@ConfigValueExtractor`, который создает только
правило извлечения значения, а конкретный путь выбирается в модуле библиотеки.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Конфигурация HOCON](../guides/config-hocon.md) и [Конфигурация YAML](../guides/config-yaml.md).

## HOCON { #hocon }

Поддержка [HOCON](https://github.com/lightbend/config/blob/master/HOCON.md) реализована с помощью [Typesafe Config](https://github.com/lightbend/config).
`HOCON` — это формат файлов конфигурации, основанный на `JSON`. Формат менее строгий, чем `JSON`, поддерживает
подстановки, значения по умолчанию и удобный синтаксис для вложенных объектов.

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

1.  Строковое значение конфигурации
2.  Числовое значение конфигурации
3.  Обязательное значение конфигурации, которое подставляется из переменной окружения `REQUIRED_ENV_VALUE`
4.  Необязательное значение конфигурации, которое подставляется из переменной окружения `OPTIONAL_ENV_VALUE`; если такая переменная не найдена, значение конфигурации будет опущено
5.  Значение конфигурации со значением по умолчанию: значение по умолчанию указывается в `propDefault = 10`, а переменная окружения `NON_DEFAULT_ENV_VALUE`, если она найдена, заменит его
6.  Значение конфигурации, собранное из подстановок других частей конфигурации и значения `Other` между ними
7.  Значение конфигурации списка строк, значение задается как массив строк либо также можно задать как строку, где значения разделены запятыми
8.  Значение конфигурации списка строк, значение задается как строка, где значения разделены запятыми либо также можно задать как массив строк
9.  Значение конфигурации в виде словаря ключей и значений
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

По умолчанию ожидаются файлы конфигурации [`reference.conf` и `application.conf`](https://github.com/lightbend/config#note-about-resolving-substitutions-in-referenceconf-and-applicationconf).

Сначала все файлы `reference.conf` из пути классов объединяются, затем файл `application.conf` накладывается поверх
неразрешенного `reference.conf`, после чего результат вычисляется и проверяется, что все обязательные подстановки доступны.

Предполагается, что конфигурация приложения находится в файле `application.conf`, а конфигурация библиотек — в `reference.conf`.

Приоритет выбора файла приложения для `HOCON`:

- Используется файл из `config.resource`, если указан (файл из директории `resources`)
- Используется файл из `config.file`, если указан (файл из файловой системы)
- Используется файл `application.conf`, если он есть (файл из директории `resources`)
- Используется пустая конфигурация, если все указанное выше отсутствует

Одновременно можно указать только одно свойство: `config.resource` или `config.file`. Если указаны оба свойства,
приложение завершится с ошибкой при запуске.

===! ":fontawesome-brands-java: `java`"

    Пример указания конфигурации при запуске в терминале через `java`:
    ```shell
    java -Dconfig.file=path/to/configFile application
    ```

=== ":simple-kotlin: `gradle`"

    Пример указания конфигурации в `build.gradle`:
    ```groovy
    run {
        jvmArgs += [
            "-Dconfig.file=path/to/configFile",
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

1.  Строковое значение конфигурации
2.  Числовое значение конфигурации
3.  Обязательное значение конфигурации, которое подставляется из переменной окружения `REQUIRED_ENV_VALUE`
4.  Необязательное значение конфигурации, которое подставляется из переменной окружения `OPTIONAL_ENV_VALUE`; если такая переменная не найдена, значение конфигурации будет опущено
5.  Значение конфигурации со значением по умолчанию: значение по умолчанию равно `10`, а переменная окружения `NON_DEFAULT_ENV_VALUE`, если она найдена, заменит его
6.  Значение конфигурации, собранное из подстановок других частей конфигурации и значения `Other` между ними
7.  Значение конфигурации списка строк, значение задается как массив строк либо также можно задать как строку, где значения разделены запятыми
8.  Значение конфигурации списка строк, значение задается как строка, где значения разделены запятыми либо также можно задать как массив строк
9.  Значение конфигурации в виде словаря ключей и значений
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

По умолчанию ожидаются файлы конфигурации `reference.yaml` и `application.yaml`.

Сначала все файлы `reference.yaml` из пути классов объединяются, затем файл `application.yaml` накладывается поверх
`reference.yaml`, после чего результат вычисляется и проверяется, что все обязательные подстановки доступны.

Предполагается, что конфигурация приложения находится в файле `application.yaml`, а конфигурация библиотек — в `reference.yaml`.

Приоритет выбора файла приложения для `YAML`:

- Используется файл из `config.resource`, если указан (файл из директории `resources`)
- Используется файл из `config.file`, если указан (файл из файловой системы)
- Используется файл `application.yaml`, если он есть (файл из директории `resources`)
- Используется пустая конфигурация, если все указанное выше отсутствует

Одновременно можно указать только одно свойство: `config.resource` или `config.file`. Если указаны оба свойства,
приложение завершится с ошибкой при запуске.

===! ":fontawesome-brands-java: `java`"

    Пример указания конфигурации при запуске в терминале через `java`:
    ```shell
    java -Dconfig.file=path/to/configFile application
    ```

=== ":simple-kotlin: `gradle`"

    Пример указания конфигурации в `build.gradle`:
    ```groovy
    run {
        jvmArgs += [
            "-Dconfig.file=path/to/configFile",
        ]
    }
    ```

## Пользовательские конфигурации { #custom-configuration }

Пользовательская конфигурация представляет собой отображение секции файла конфигурации на пользовательский тип.
Такой тип затем может быть внедрен как зависимость наравне с другими компонентами.

### В приложении { #application-config }

Для создания пользовательских конфигураций в приложении следует использовать аннотацию `@ConfigSource`.
Она генерирует `ConfigValueExtractor` для интерфейса и модуль, который добавляет готовый объект конфигурации в граф зависимостей.
Значение аннотации указывает путь к секции внутри итоговой конфигурации:

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

### В библиотеке { #library-config }

Для создания пользовательских конфигураций в рамках библиотек следует использовать аннотацию `@ConfigValueExtractor`.
Она создает правило извлечения значения из `ConfigValue<?>`, но не привязывает его к конкретному пути в конфигурации.
Путь выбирается в фабричном методе модуля библиотеки, поэтому одну и ту же форму конфигурации можно переиспользовать для разных секций.
`@ConfigValueExtractor` можно использовать над интерфейсом, `record` или классом в `Java`, а также над интерфейсом
или `data class` в `Kotlin`.

У аннотации есть параметр `mapNullAsEmptyObject` (по умолчанию: `true`). Если он включен, отсутствующая секция
воспринимается как пустой объект: обязательные поля все равно приведут к ошибке, а необязательные поля и значения
по умолчанию будут обработаны как при пустой секции. Если указать `mapNullAsEmptyObject = false`, отсутствующая секция
будет считаться значением `null` для всего объекта конфигурации.

Рассмотрим пример, когда есть такой класс конфигурации:

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

Чтобы библиотека предоставляла конфигурацию, требуется реализовать фабрику в модуле:

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

Затем, подключив модуль `FooLibraryModule` в приложении, конфигурацию `FooLibraryConfig` можно использовать как зависимость в других классах.

### Обязательные значения { #required-values }

По умолчанию все значения, объявленные в конфигурации, считаются **обязательными** (`NotNull`) и должны присутствовать
в итоговой конфигурации. Если обязательное значение отсутствует или имеет значение `null`, приложение завершится с ошибкой
на этапе создания объекта конфигурации.

### Необязательные значения { #optional-values }

Если нужно указать значение из файла конфигурации как необязательное, можно воспользоваться таким форматом:

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

    Предполагается использовать синтаксис [null-безопасности `Kotlin`](https://kotlinlang.ru/docs/null-safety.html)
    и помечать такой параметр как допускающий `null`:

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String?

        fun baz(): Int
    }
    ```

### Значения по умолчанию { #default-values }

Если нужно задать значение по умолчанию в отображении конфигурации, можно воспользоваться `default`-методом:

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

### Рекомендуемое оформление { #recommended-configuration-style }

Обычно удобнее описывать конфигурацию отдельным типом под конкретную интеграцию или подсистему: HTTP-клиент,
подключение к внешнему сервису, обработчик очереди и так далее. В таком типе стоит явно разделять обязательные значения,
необязательные значения и значения, которые приходят из переменных окружения.

В примере ниже:

1. `baseUrl` — обязательное значение из файла конфигурации
2. `clientName` — необязательное значение из переменной окружения `ORDERS_CLIENT_NAME`
3. `token` — обязательное значение из переменной окружения `ORDERS_API_TOKEN`
4. `requestTimeout` — значение по умолчанию `2s`, которое можно переопределить необязательной переменной окружения `ORDERS_REQUEST_TIMEOUT`

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

Такой подход оставляет структуру конфигурации читаемой: обязательные настройки видны в типе конфигурации, секреты можно
передавать через переменные окружения, а безопасные значения по умолчанию остаются прямо в файле конфигурации.

## Внедрение конфигурации { #injecting-configuration }

Можно внедрять базовый класс `ru.tinkoff.kora.config.common.Config`, который представляет дерево конфигурации и дает доступ
к значениям через метод `get(...)`.
Итоговая конфигурация состоит из нескольких слоев:

- Переменные окружения
- Системные свойства `Java`
- Файл конфигурации

Слои объединяются в таком порядке: переменные окружения, затем системные свойства, затем файл конфигурации приложения.
Каждый следующий слой накладывается поверх предыдущего.

### Переменные окружения { #environment-variables }

Если требуется внедрить конфигурацию **только** [переменных окружения](https://ru.hexlet.io/courses/cli-basics/lessons/environment-variables/theory_unit),
для этого можно использовать аннотацию `@Environment` как тег для класса конфигурации:

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

Если требуется внедрить конфигурацию **только** [системных свойств `Java`](https://www.baeldung.com/java-system-get-property-vs-system-getenv),
для этого можно использовать аннотацию `@SystemProperties` как тег для класса конфигурации:

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

### Файл конфигурации { #configuration-file }

Если требуется внедрить конфигурацию приложения, которая состоит **только** из файла конфигурации,
для этого можно использовать аннотацию `@ApplicationConfig` как тег для класса конфигурации:

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

### Результирующая конфигурация { #resulting-configuration }

Если требуется внедрить полную итоговую конфигурацию приложения, которая состоит из файла конфигурации,
переменных окружения и системных свойств, для этого требуется просто внедрить класс конфигурации без тега:

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

### Совет { #recommendations }

???+ warning "Совет"

    **Мы не советуем** использовать напрямую `ru.tinkoff.kora.config.common.Config` как зависимость в компонентах,
    так как при обновлении конфигурации это повлечет обновление всех компонентов графа, которые используют его у себя,
    рекомендуется всегда создавать [пользовательские конфигурации](#custom-configuration).

## Наблюдатель { #config-watcher }

По умолчанию в `Kora` работает наблюдатель за файлом конфигурации, который проверяет изменения файла приложения
и запускает обновление графа зависимостей, если файл изменился.
Проверка выполняется раз в `1000` миллисекунд.

Для `HOCON` наблюдатель также отслеживает файлы, которые были подключены через `include` внутри основного файла
конфигурации. Если изменится такой подключенный файл, конфигурация тоже будет перечитана и граф зависимостей обновится.

Наблюдатель работает только для файловой конфигурации, у которой есть отслеживаемый источник. Если конфигурация пришла
из ресурса внутри архива или была собрана без файла приложения, обновлять на диске будет нечего.

Можно отключить наблюдатель с помощью:

1. Переменной окружения `KORA_CONFIG_WATCHER_ENABLED` (по умолчанию: `true`)
2. Системного свойства `kora.config.watcher.enabled` (по умолчанию: `true`)

## Поддерживаемые типы { #supported-types }

Экстракторы конфигурации предоставляют обширный список поддерживаемых типов, который охватывает большинство значений,
которые могут понадобиться в пользовательских конфигурациях.
Если стандартного преобразования не хватает, поведение можно расширить собственным компонентом `ConfigValueExtractor<T>`.

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
    * Enum (любой пользовательский `enum`; соответствие можно переопределить через `toString()`)
    * `Optional<T>` (где `T` любой из поддерживаемых типов)
    * `List<T>` (где `T` любой из поддерживаемых типов)
    * `Set<T>` (где `T` любой из поддерживаемых типов)
    * `Map<String, V>` либо `Map<K, V>` (где `K` и `V` поддерживаются соответствующими экстракторами)
    * `Either<A, B>` (где `A` и `B` любые из поддерживаемых типов)

### Собственный экстрактор { #custom-extractor }

Если для типа нет стандартного преобразования или требуется особая логика разбора, можно добавить собственный компонент
`ConfigValueExtractor<T>`. Метод `extract(...)` получает значение конфигурации как `ConfigValue<?>` и должен вернуть
готовое значение нужного типа.

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

Если нужно использовать конкретный экстрактор только для одного поля, можно указать его через `@Mapping`:

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

### Длительность { #duration }

`Duration` можно задавать числом или строкой.
Если указано число, оно считается количеством миллисекунд.
Если указана строка, поддерживается формат `java.time.Duration`, например `PT10S`, а также стиль `HOCON`:

- `500ms`
- `10 seconds`
- `2 minutes`
- `1h`
- `1d`

### Период { #period }

`Period` можно задавать числом или строкой.
Если указано число, оно считается количеством дней.
Если указана строка, поддерживаются единицы:

- `d` / `days`
- `w` / `weeks`
- `m` / `mo` / `months`
- `y` / `years`

Например, `7d`, `2 weeks`, `3mo` или `1 year`.

### Размер { #size }

`Size` — специальный тип, который позволяет задавать размер в байтах в удобной человеку системе исчисления:
по стандарту [IEEE 1541—2002](https://ru.ruwiki.ru/wiki/IEEE_1541-2002) (двоичный) или по стандарту
[СИ](https://ru.ruwiki.ru/wiki/%D0%95%D0%B4%D0%B8%D0%BD%D0%B8%D1%86%D1%8B_%D0%B8%D0%B7%D0%BC%D0%B5%D1%80%D0%B5%D0%BD%D0%B8%D1%8F_%D1%91%D0%BC%D0%BA%D0%BE%D1%81%D1%82%D0%B8_%D0%BD%D0%BE%D1%81%D0%B8%D1%82%D0%B5%D0%BB%D0%B5%D0%B9_%D0%B8_%D0%BE%D0%B1%D1%8A%D1%91%D0%BC%D0%B0_%D0%B8%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D0%B8%D0%B8#%D0%91%D0%B0%D0%B9%D1%82) (десятичный).

Примеры значений:

- `1Mb` — 1 мегабайт (`1.000.000` байт)
- `1Mib` — 1 мебибайт (`1.048.576` байт)
- `1024b` — 1024 байт
- `1024` — 1024 байт

Если указано просто число без суффикса, то считается, что указаны байты.
