---
description: "Explains the Kora configuration system for HOCON and YAML, typed configuration mapping, configuration injection, config sources, the config watcher, and supported value types. Use when working with @ConfigSource, @ConfigMapper, ConfigValueMapper, @EnvironmentConfig, @SystemPropertiesConfig, @ApplicationConfig, Config, HoconConfigModule, YamlConfigModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the Kora configuration system for HOCON and YAML, typed configuration mapping, configuration injection, config sources, the config watcher, and supported value types; key triggers include @ConfigSource, @ConfigMapper, ConfigValueMapper, @EnvironmentConfig, @SystemPropertiesConfig, @ApplicationConfig, Config, HoconConfigModule, YamlConfigModule."
---

Модуль конфигурации читает настройки приложения из файлов `HOCON` или `YAML`, переменных окружения, системных свойств
`Java` и отображает их на типизированные классы в `Kora`. Полученные объекты конфигурации становятся обычными
компонентами графа зависимостей и могут внедряться в сервисы, клиенты, серверы и другие интеграции.

В `Kora` конфигурация приложения обычно описывается интерфейсом с аннотацией `@ConfigSource`: путь в файле указывает на
читаемую секцию, а методы интерфейса описывают обязательные значения, необязательные значения и значения по умолчанию.
Библиотеки и переиспользуемые формы конфигурации используют `@ConfigMapper`, который создаёт только правило
отображения, тогда как конкретный путь выбирается в модуле библиотеки.

Для пошагового разбора перед справочным описанием смотрите [Конфигурация HOCON](../guides/config-hocon.md) и [Конфигурация YAML](../guides/config-yaml.md).

## HOCON { #hocon }

Поддержка [HOCON](https://github.com/lightbend/config/blob/master/HOCON.md) реализована с помощью [Typesafe Config](https://github.com/lightbend/config).
`HOCON` — это формат файла конфигурации на основе `JSON`. Он менее строгий, чем `JSON`, и поддерживает подстановки,
значения по умолчанию и удобный синтаксис вложенных объектов.

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
4. Необязательное значение конфигурации, подставляемое из переменной окружения `OPTIONAL_ENV_VALUE`; если переменная не найдена, значение конфигурации отсутствует
5. Значение конфигурации со значением по умолчанию: значение по умолчанию задано как `propDefault = 10`, а `NON_DEFAULT_ENV_VALUE`, если найдено, заменяет его
6. Значение конфигурации, собранное из подстановок других частей конфигурации со значением `Other` между ними
7.  Значение конфигурации в виде списка строк; значение можно задать массивом строк либо строкой с разделителем-запятой
8.  Значение конфигурации в виде списка строк; значение можно задать строкой с разделителем-запятой либо массивом строк
9.  Значение конфигурации в виде словаря «ключ-значение»
10. Значение конфигурации в виде отображаемого класса
11. Значение конфигурации в виде списка отображаемых классов

Значения могут ссылаться и на другие ключи конфигурации (внутренние и перекрёстные ссылки) через `${path}`, и на
переменные окружения через `${VAR}` (обязательная подстановка) или `${?VAR}` (необязательная подстановка). Значение по
умолчанию задаётся принятым в `HOCON` способом: ключ присваивается дважды — сначала запасным литеральным значением, затем
необязательной подстановкой, как это сделано для `propDefault` выше. Подстановки внутри файла `HOCON` разрешает
`Typesafe Config` уже после слияния всех слоёв этого файла, поэтому ссылка может указывать на ключ, объявленный в другом
файле `HOCON`, подключённом через `include`.

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

        @ConfigMapper
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

        @ConfigMapper
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
    implementation "io.koraframework:config-hocon"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends HoconConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:config-hocon")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule
    ```

### Файл { #file }

По умолчанию ожидаются файлы конфигурации [`reference.conf` и `application.conf`](https://github.com/lightbend/config#note-about-resolving-substitutions-in-referenceconf-and-applicationconf).

Сначала сливаются все файлы `reference.conf` из classpath, затем поверх неразрешённого `reference.conf` накладывается
`application.conf`, а поверх него — системные свойства `Java`. Только после сборки всего стека результат разрешается и
проверяются обязательные подстановки.

Конфигурация приложения ожидается в `application.conf`, а конфигурация библиотек — в `reference.conf`.

`HOCON` также поддерживает директиву [`include`](https://github.com/lightbend/config/blob/master/HOCON.md#includes):
подключённые через `include` файлы участвуют в том же слиянии и разрешении подстановок, что и основной файл.
Подключения, которые указывают на реальные файлы на диске, дополнительно отслеживаются [наблюдателем за конфигурацией](#config-watcher),
поэтому изменение подключённого файла тоже обновляет граф; подключения ресурсов classpath и `URL` не отслеживаются.

Приоритет выбора файла приложения для `HOCON`:

- Используется файл из `config.resource`, если он указан (файл из директории `resources`)
- Используется файл из `config.file`, если он указан (файл из файловой системы)
- Используется `application.conf`, если он присутствует (файл из директории `resources`)
- Используется пустая конфигурация, если ничего из вышеперечисленного нет

Одновременно можно указать только одно свойство: `config.resource` либо `config.file`. Если указаны оба свойства,
приложение упадёт при старте с ошибкой `Application config source is ambiguous`.

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
        propDefault: ${NON_DEFAULT_ENV_VALUE:10} #(5)!
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
4. Необязательное значение конфигурации, подставляемое из переменной окружения `OPTIONAL_ENV_VALUE`; если переменная не найдена, значение конфигурации отсутствует
5. Значение конфигурации со значением по умолчанию: значение по умолчанию — `10`, а `NON_DEFAULT_ENV_VALUE`, если найдено, заменяет его
6. Значение конфигурации, собранное из подстановок других частей конфигурации со значением `Other` между ними
7.  Значение конфигурации в виде списка строк; значение можно задать массивом строк либо строкой с разделителем-запятой
8.  Значение конфигурации в виде списка строк; значение можно задать строкой с разделителем-запятой либо массивом строк
9.  Значение конфигурации в виде словаря «ключ-значение»
10. Значение конфигурации в виде отображаемого класса
11. Значение конфигурации в виде списка отображаемых классов

У `YAML` нет собственного синтаксиса подстановок, поэтому ссылки разрешает сама `Kora` уже после слияния всех слоёв
конфигурации. Поддерживаются три формы:

- `${path}` — обязательная: ссылка должна разрешиться, иначе приложение упадёт при старте
- `${?path}` — необязательная: неразрешённая ссылка не даёт значения, и ключ ведёт себя так, будто он отсутствует
- `${path:defaultValue}` — неразрешённая ссылка заменяется на `defaultValue`

Те же формы работают и для переменных окружения, и для ссылок на другие ключи конфигурации, потому что переменные
окружения и системные свойства сами являются слоями конфигурации. В одну строку можно встроить несколько ссылок, как это
сделано для `propReference` выше.

???+ warning "Внимание"

    Символ `?` и значение по умолчанию нельзя комбинировать: в `${?path:defaultValue}` весь текст `path:defaultValue`
    воспринимается как имя ссылки, и ключ не получит значения. Используйте `${path:defaultValue}` — эта форма и так
    подставляет запасное значение, когда ссылка не разрешилась.

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

        @ConfigMapper
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

        @ConfigMapper
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
    implementation "io.koraframework:config-yaml"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends YamlConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:config-yaml")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : YamlConfigModule
    ```

### Файл { #file-2 }

По умолчанию ожидаются файлы конфигурации `reference.yaml` и `application.yaml`.

Сначала сливаются все файлы `reference.yaml` из classpath, затем поверх `reference.yaml` накладывается
`application.yaml`, после чего результат разрешается и проверяются обязательные подстановки.

Конфигурация приложения ожидается в `application.yaml`, а конфигурация библиотек — в `reference.yaml`.

Каждый `reference.yaml` должен разрешаться самостоятельно, без файла приложения: он проверяется при старте, и
неразрешимая ссылка роняет приложение с ошибкой `Reference config ... cannot be resolved without external application config`.
Задайте таким ключам литеральное значение по умолчанию, сделайте ссылку необязательной через `${?path}` либо укажите
запасное значение через `${path:defaultValue}`.

Приоритет выбора файла приложения для `YAML`:

- Используется файл из `config.resource`, если он указан (файл из директории `resources`)
- Используется файл из `config.file`, если он указан (файл из файловой системы)
- Используется `application.yaml`, если он присутствует (файл из директории `resources`)
- Используется пустая конфигурация, если ничего из вышеперечисленного нет

Одновременно можно указать только одно свойство: `config.resource` либо `config.file`. Если указаны оба свойства,
приложение упадёт при старте с ошибкой `Application config source is ambiguous`.

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

Пользовательская конфигурация отображает секцию файла конфигурации на пользовательский тип.
Этот тип затем внедряется как зависимость наравне с любым другим компонентом.

И `@ConfigSource`, и `@ConfigMapper` генерируют реализацию `ConfigValueMapper<T>` во время компиляции.
Допустимые формы объявления:

- `Java` — `interface`, `record` либо класс. Класс должен быть неабстрактным и переопределять `equals` и `hashCode`
- `Kotlin` — `interface` либо `data class`

Методы интерфейса конфигурации описывают поля, поэтому они не должны принимать параметры, не должны быть обобщёнными и
обязаны возвращать значение. Всё остальное оформляется методом `default`. Поля, объявленные в родительских интерфейсах,
наследуются в отображение.

### Конфигурация приложения { #application-config }

Для создания пользовательских конфигураций в приложении используется аннотация `@ConfigSource`.
Она генерирует `ConfigValueMapper` для типа и модуль, который добавляет готовый объект конфигурации в граф
зависимостей. Значение аннотации указывает путь к секции внутри итоговой конфигурации:

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

Такой код добавит в контейнер зависимостей экземпляр класса `FooServiceConfig`, который при создании будет ожидать конфигурацию следующего вида:

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

После этого класс `FooServiceConfig` можно использовать как зависимость в других классах:

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

Для создания пользовательских конфигураций в библиотеках используется аннотация `@ConfigMapper`.
Она создаёт правило отображения `ConfigValue<?>` на тип, но не привязывает его к конкретному пути конфигурации.
Путь выбирается в фабричном методе модуля библиотеки, поэтому одну и ту же форму конфигурации можно переиспользовать для разных секций.

У аннотации есть параметр `mapNullAsEmptyObject` (по умолчанию: `true`). Когда он включён, отсутствующая секция
трактуется как пустой объект: обязательные поля всё так же падают, а необязательные поля и значения по умолчанию ведут
себя так, будто пустая секция присутствовала. При `mapNullAsEmptyObject = false` отсутствующая секция отображается в
`null` для всего объекта конфигурации.
Тип, помеченный только `@ConfigSource`, всегда ведёт себя как при `mapNullAsEmptyObject = true`.

Рассмотрим такой класс конфигурации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public interface FooLibraryConfig {

        String bar();

        int baz();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    interface FooLibraryConfig {

        fun bar(): String

        fun baz(): Int
    }
    ```

Чтобы библиотека предоставляла конфигурацию, реализуйте фабрику в модуле:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface FooLibraryModule {

        default FooLibraryConfig fooLibraryConfig(Config config, ConfigValueMapper<FooLibraryConfig> mapper) {
            return mapper.mapOrThrow(config.get("library.foo"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface FooLibraryModule {

        fun fooLibraryConfig(config: Config, mapper: ConfigValueMapper<FooLibraryConfig>): FooLibraryConfig {
            return mapper.mapOrThrow(config.get("library.foo"))
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

После подключения `FooLibraryModule` в приложении `FooLibraryConfig` можно использовать как зависимость в других классах.

У `ConfigValueMapper<T>` два метода чтения: `map(...)` может вернуть `null` — у сгенерированного маппера это
происходит при `mapNullAsEmptyObject = false` и отсутствующей секции, — а `mapOrThrow(...)` превращает такой `null` в
`ConfigValueException`. В фабричных методах обычно используют `mapOrThrow(...)`, потому что отсутствие секции
библиотеки — это ошибка старта, а не допустимое состояние.

Одну и ту же форму можно привязать сразу к нескольким секциям, добавив [тег](container.md#tags) каждому фабричному методу:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface FooLibraryModule {

        final class Lib1Tag {}

        final class Lib2Tag {}

        @Tag(Lib1Tag.class)
        default FooLibraryConfig lib1Config(Config config, ConfigValueMapper<FooLibraryConfig> mapper) {
            return mapper.mapOrThrow(config.get("libs.lib1"));
        }

        @Tag(Lib2Tag.class)
        default FooLibraryConfig lib2Config(Config config, ConfigValueMapper<FooLibraryConfig> mapper) {
            return mapper.mapOrThrow(config.get("libs.lib2"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface FooLibraryModule {

        class Lib1Tag private constructor()

        class Lib2Tag private constructor()

        @Tag(Lib1Tag::class)
        fun lib1Config(config: Config, mapper: ConfigValueMapper<FooLibraryConfig>): FooLibraryConfig {
            return mapper.mapOrThrow(config.get("libs.lib1"))
        }

        @Tag(Lib2Tag::class)
        fun lib2Config(config: Config, mapper: ConfigValueMapper<FooLibraryConfig>): FooLibraryConfig {
            return mapper.mapOrThrow(config.get("libs.lib2"))
        }
    }
    ```

### Обязательные значения { #required-values }

По умолчанию все значения, объявленные в конфигурации, считаются **обязательными** и должны присутствовать в итоговой
конфигурации. Если обязательное значение отсутствует либо равно `null`, приложение упадёт при создании объекта
конфигурации с ошибкой `Config expected value, but got null at path: '...'`.

### Необязательные значения { #optional-values }

Если требуется указать значение из файла конфигурации как необязательное, используется такой формат:

===! ":fontawesome-brands-java: `Java`"

    Рекомендуется использовать аннотацию `@Nullable` над сигнатурой метода:

    ```java
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        @Nullable//(1)!
        String bar();

        int baz();
    }
    ```

    1.  [JSpecify](https://jspecify.dev/) `org.jspecify.annotations.Nullable` — аннотация, на которой построена сама `Kora`.

=== ":simple-kotlin: `Kotlin`"

    Используйте синтаксис [null-safety в `Kotlin`](https://kotlinlang.org/docs/null-safety.html) и пометьте параметр как nullable:

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String?

        fun baz(): Int
    }
    ```

`@Nullable` из `JSpecify` — аннотация *над типом*, поэтому для квалифицированного или обобщённого типа она пишется
непосредственно перед именем типа, а не перед всем объявлением:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        java.time.@Nullable Duration timeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun timeout(): java.time.Duration?
    }
    ```

Также поддерживается возвращаемый тип `Optional<T>` (отсутствующее значение отображается в `Optional.empty()`), но
рекомендуемый стиль — значение с `@Nullable` (или nullable-тип в `Kotlin`).

### Значения по умолчанию { #default-values }

Если требуется задать значение по умолчанию при отображении конфигурации, используйте метод `default`:

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

Значения по умолчанию доступны и для остальных форм объявления, но механизм отличается по языкам: `data class`
в `Kotlin` берёт их из значений по умолчанию у параметров конструктора, а класс в `Java` — из инициализаторов
полей, поэтому ему нужны публичный конструктор без аргументов и методы доступа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public class FooServiceConfig {

        private String bar;
        private int baz = 42;

        public String getBar() {
            return this.bar;
        }

        public void setBar(String bar) {
            this.bar = bar;
        }

        public int getBaz() {
            return this.baz;
        }

        public void setBaz(int baz) {
            this.baz = baz;
        }

        @Override
        public boolean equals(Object o) {
            return o instanceof FooServiceConfig that
                && Objects.equals(this.bar, that.bar)
                && this.baz == that.baz;
        }

        @Override
        public int hashCode() {
            return Objects.hash(this.bar, this.baz);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    data class FooServiceConfig(val bar: String, val baz: Int = 42)
    ```

У `record` в `Java` механизма значений по умолчанию нет: каждый компонент читается как обязательное значение,
если он не помечен `@Nullable`. Когда для record нужны значения по умолчанию, используйте интерфейс с методами
`default`.

### Валидация { #validation }

Тип конфигурации можно дополнительно проверять ограничениями [валидации](validation.md). Пометьте его аннотацией `@Valid`
и расставьте ограничения на полях: сгенерированный маппер вызовет `Validator` сразу после сборки объекта, поэтому
некорректная конфигурация уронит приложение на старте, а не при первом использовании.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        @NotBlank
        String bar();

        @Range(from = 1.0, to = 65535.0)
        int port();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        @NotBlank
        fun bar(): String

        @Range(from = 1.0, to = 65535.0)
        fun port(): Int
    }
    ```

### Гибкие имена ключей { #relaxed-key-names }

Ключи конфигурации сопоставляются по гибким правилам именования. Имя метода сравнивается с ключом в файле не только в
точной форме, но и в вариантах `kebab-case` и `snake_case`. Это значит, что метод `someBarString()` одинаково
разрешается из `someBarString`, `some-bar-string` или `some_bar_string` в файле конфигурации, поэтому команды,
предпочитающие kebab-case или snake_case, могут сохранить свой стиль без переименования методов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public interface BarConfig {

        String someBarString();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
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

Цифры и подряд идущие заглавные буквы также считаются отдельными частями, поэтому `someFieldWithCAPSAnd42Numbers()`
читается ещё и из `some-field-with-caps-and-42-numbers` и `some_field_with_caps_and_42_numbers`.

### Рекомендуемый стиль { #recommended-configuration-style }

Обычно удобнее описывать конфигурацию отдельным типом для конкретной интеграции или подсистемы: HTTP-клиента,
подключения к внешнему сервису, обработчика очереди и так далее. Такой тип должен явно разделять обязательные значения,
необязательные значения и значения, приходящие из переменных окружения.

В примере ниже:

1. `baseUrl` — обязательное значение из файла конфигурации
2. `clientName` — необязательное значение из переменной окружения `ORDERS_CLIENT_NAME`
3. `token` — обязательное значение из переменной окружения `ORDERS_API_TOKEN`
4. `requestTimeout` имеет значение по умолчанию `2s` и может быть переопределён необязательной переменной окружения `ORDERS_REQUEST_TIMEOUT`

===! ":fontawesome-brands-java: `Java`"

    ```java
    import java.time.Duration;
    import org.jspecify.annotations.Nullable;

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

===! ":material-code-json: `Hocon`"

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

=== ":simple-yaml: `YAML`"

    ```yaml
    clients:
      orders:
        baseUrl: "https://orders.example.com"
        clientName: ${?ORDERS_CLIENT_NAME}
        token: ${ORDERS_API_TOKEN}
        requestTimeout: ${ORDERS_REQUEST_TIMEOUT:2s}
    ```

Так структура конфигурации остаётся читаемой: обязательные настройки видны в типе конфигурации, секреты передаются через
переменные окружения, а безопасные значения по умолчанию остаются прямо в файле конфигурации.

## Внедрение конфигурации { #injecting-configuration }

Можно внедрить базовый класс `io.koraframework.config.common.Config`, который представляет дерево конфигурации и даёт
доступ к значениям через метод `get(...)`. Итоговая конфигурация состоит из нескольких слоёв:

- Переменные окружения
- Системные свойства `Java`
- Файл конфигурации

Слои сливаются так, что более ранний слой побеждает более поздний: переменная окружения переопределяет системное
свойство, а системное свойство переопределяет значение из файла конфигурации. Переменные окружения становятся плоскими
ключами с именем самой переменной (`ORDERS_API_TOKEN`), а системные свойства разбиваются по `.` в дерево, поэтому
`-Dservices.foo.bar=value` напрямую переопределяет ключ конфигурации `services.foo.bar`.

После слияния `Kora` разрешает ссылки `${...}` по всему дереву. Значения, пришедшие из переменных окружения, повторно не
разрешаются, поэтому символ `$` внутри секрета безопасен. Разрешение значений, пришедших из системных свойств, можно
отключить переменной окружения `KORA_SYSTEM_PROPERTIES_RESOLVE_ENABLED` либо системным свойством
`kora.system.properties.resolve.enabled` (по умолчанию: `true`).

### Переменные окружения { #environment-variables }

Если требуется внедрить конфигурацию, состоящую **только** из [переменных окружения](https://en.wikipedia.org/wiki/Environment_variable),
используйте аннотацию `@EnvironmentConfig` как тег для класса конфигурации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(@EnvironmentConfig Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(@EnvironmentConfig val config: Config)
    ```

### Системные свойства { #system-variables }

Если требуется внедрить конфигурацию, состоящую **только** из [системных свойств `Java`](https://www.baeldung.com/java-system-get-property-vs-system-getenv),
используйте аннотацию `@SystemPropertiesConfig` как тег для класса конфигурации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(@SystemPropertiesConfig Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(@SystemPropertiesConfig val config: Config)
    ```

### Конфигурационный файл { #configuration-file }

Если требуется внедрить конфигурацию приложения, состоящую **только** из файла конфигурации,
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

Если требуется внедрить полную итоговую конфигурацию приложения, состоящую из файла конфигурации, переменных окружения и
системных свойств, просто внедрите класс конфигурации без тега:

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

### Чтение сырого Config { #reading-raw-config-values }

Когда внедрён сырой `Config`, значения читаются методом `get(...)`, который возвращает узел `ConfigValue<?>` по
запрошенному пути. `ConfigValue<?>` — sealed-тип с типизированными методами доступа: `asString()`, `asNumber()`,
`asBoolean()`, `asObject()`, `asArray()` и `isNull()`. Если значение имеет неожиданный тип, метод доступа бросает
`ConfigValueException`. Отсутствующий путь сам по себе исключения не бросает — он возвращает `ConfigValue.NullValue`.

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
            val value = config.get("services.foo.bar")
            if (!value.isNull) {
                val bar = value.asString()
            }
        }
    }
    ```

Элементы массива адресуются индексом внутри пути, например `config.get("services.foo.propObjects[0].p1")`.

Как отмечено в разделе [Рекомендуемый стиль](#recommended-configuration-style), предпочитайте типизированные
[пользовательские конфигурации](#custom-configuration) чтению сырого `Config`.
Используйте API сырого чтения только для динамического или обобщённого доступа, когда иного выбора нет, и применяйте
`ValueOf<Config>`, чтобы избежать обновления компонента.

???+ warning "Внимание"

    **Не рекомендуется** использовать `io.koraframework.config.common.Config` напрямую как зависимость в компонентах,
    потому что при обновлении конфигурации будут обновлены и все компоненты графа, которые его используют.
    Рекомендуется всегда создавать [пользовательские конфигурации](#custom-configuration).

## Наблюдатель за конфигурацией { #config-watcher }

По умолчанию в `Kora` есть наблюдатель за файлом конфигурации, который проверяет файл приложения на изменения и
запускает обновление графа зависимостей, если файл изменился. Проверка выполняется каждые `1000` миллисекунд на
виртуальном потоке.

Для `HOCON` наблюдатель отслеживает и файлы, подключённые через `include` внутри основного файла конфигурации.
Если такой подключённый файл изменился, конфигурация перечитывается и граф зависимостей также обновляется.

Наблюдатель работает только для файловой конфигурации с отслеживаемым источником. Если конфигурация пришла из ресурса
внутри архива либо была собрана без файла приложения, обновлять на диске нечего.
Подмена символической ссылки, на которую указывает файл конфигурации, тоже считается изменением — именно это делает
видимыми без перезапуска смонтированные секреты и обновления `ConfigMap`.

Отключить наблюдатель можно с помощью:

1. Переменной окружения `KORA_CONFIG_WATCHER_ENABLED` (по умолчанию: `true`)
2. Системного свойства `kora.config.watcher.enabled` (по умолчанию: `true`)

## Поддерживаемые типы { #supported-types }

Мапперы конфигурации предоставляют обширный список поддерживаемых типов, который покрывает большинство значений,
нужных в пользовательских конфигурациях. Если стандартного преобразования недостаточно, поведение расширяется
собственным компонентом `ConfigValueMapper<T>`.

??? abstract "Список поддерживаемых типов"

    * boolean / Boolean
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
    * Duration[]
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
    * `Map<String, V>` или `Map<K, V>` (где `K` и `V` поддерживаются соответствующими мапперами)
    * `Either<A, B>` (где `A` и `B` — любые поддерживаемые типы)

`List<T>` и `Set<T>` принимают и массив, и строку с разделителем-запятой, поэтому `["v1", "v2"]` и `"v1, v2"` дают одно
и то же значение. `Map<K, V>` читается из объекта: ключи берутся как строки и проходят через маппер ключа, значения —
через маппер значения.

### Пользовательский маппер { #custom-extractor }

Если для типа нет стандартного преобразования или требуется особая логика разбора, добавьте собственный компонент
`ConfigValueMapper<T>`. Метод `map(...)` получает значение конфигурации как `ConfigValue<?>` и должен вернуть готовое
значение нужного типа либо `null`, если значение отсутствует.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class TokenConfigValueMapper implements ConfigValueMapper<Token> {

        @Override
        public @Nullable Token map(ConfigValue<?> value) {
            if (value.isNull()) {
                return null;
            }
            return new Token(value.asString());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class TokenConfigValueMapper : ConfigValueMapper<Token> {

        override fun map(value: ConfigValue<*>): Token? {
            if (value.isNull) {
                return null
            }
            return Token(value.asString())
        }
    }
    ```

Зарегистрированный так маппер используется для каждого поля конфигурации типа `Token`.

Если конкретный маппер должен применяться только к одному полю, укажите его через `@Mapping`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public interface ApiConfig {

        @Mapping(TokenConfigValueMapper.class)
        Token token();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    interface ApiConfig {

        @Mapping(TokenConfigValueMapper::class)
        fun token(): Token
    }
    ```

Откуда берётся экземпляр маппера, зависит от его объявления. Если класс `final` (`Java`) / не `open` (`Kotlin`),
имеет публичный конструктор без аргументов и не помечен `@Tag`, `Kora` создаёт его сама для этого поля.
В любом другом случае — есть зависимости конструктора, класс `open` либо рядом с `@Mapping` стоит `@Tag` — маппер
берётся из графа зависимостей и должен быть там зарегистрирован. Маппер, используемый без `@Mapping`, то есть как маппер
типа для всего графа, всегда берётся из графа и обязан быть компонентом.

### Duration { #duration }

`Duration` можно задать числом или строкой.
Если указано число, оно трактуется как миллисекунды.
Если указана строка, поддерживается формат `java.time.Duration`, например `PT10S`, а также стиль `HOCON`:

- `500ms`
- `10 seconds`
- `2 minutes`
- `1h`
- `1d`

Поддерживаемые суффиксы единиц: `ns` / `nanos` / `nanoseconds`, `us` / `micros` / `microseconds`, `ms` / `millis` / `milliseconds`,
`s` / `seconds`, `m` / `minutes`, `h` / `hours`, `d` / `days`. Значение без суффикса читается как миллисекунды.

### Period { #period }

`Period` можно задать числом или строкой.
Если указано число, оно трактуется как дни.
Если указана строка, поддерживаются такие единицы:

- `d` / `days`
- `w` / `weeks`
- `m` / `mo` / `months`
- `y` / `years`

Например, `7d`, `2 weeks`, `3mo` или `1 year`. Значение без суффикса читается как дни.

### Size { #size }

`Size` — специальный тип, который позволяет задавать размеры в байтах в удобной для человека нотации: по стандарту
[IEEE 1541-2002](https://en.wikipedia.org/wiki/IEEE_1541-2002) (двоичной) либо по стандарту
[SI](https://en.wikipedia.org/wiki/Binary_prefix) (десятичной).

Примеры значений:

- `1Mb` - 1 мегабайт (`1.000.000` байт)
- `1Mib` - 1 мебибайт (`1.048.576` байт)
- `1024b` - 1024 байта
- `1024` - 1024 байта

Если указано просто число без суффикса, считается, что указаны байты.
Суффиксы сопоставляются без учёта регистра и покрывают `b`, `kb` / `kib`, `mb` / `mib`, `gb` / `gib`, `tb` / `tib`,
`pb` / `pib`, `eb` / `eib`.

### Either { #either }

`Either<A, B>` позволяет одному полю принимать две альтернативные формы. Маппер сначала пробует левый тип `A`, и если
отображение падает с любым исключением, откатывается к правому типу `B`. Это удобно, когда значение может быть либо
простым скаляром, либо структурированным объектом.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.common.Either;

    @ConfigMapper
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
    import io.koraframework.common.Either

    @ConfigMapper
    interface EndpointConfig {

        fun host(): String

        fun port(): Int
    }

    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun endpoint(): Either<String, EndpointConfig>
    }
    ```

Обе формы ниже допустимы для поля `endpoint`:

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
