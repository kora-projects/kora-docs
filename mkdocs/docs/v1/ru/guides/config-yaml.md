---
search:
  exclude: true
title: Управление YAML-конфигурацией в Kora
summary: Learn how to bind YAML configuration to type-safe interfaces, separate required and defaulted values, and reuse one config shape across multiple integrations
tags: configuration, yaml, configsource, configvalueextractor
---

# Управление YAML-конфигурацией в Kora { #yaml-configuration-management-kora }

Это руководство знакомит с типобезопасной конфигурацией в Kora и YAML. Оно показывает, как записи конфигурации извлекаются из `application.yaml`, как обязательные значения и значения по умолчанию
выражаются в Java-коде, и как переиспользуемые фрагменты конфигурации можно внедрять в несколько компонентов без дублирования всего блока. Также вы увидите, как переменные окружения и вывод значений
во время выполнения помогают легко проверять итоговую конфигурацию.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Config YAML App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-config-yaml-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Config YAML App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-config-yaml-app).

## Что вы создадите { #youll-build }

Вы соберете небольшое запускаемое приложение Kora, которое:

- связывает `app.name`, `app.version` и `app.environment` через `@ConfigSource`
- считает `APP_VERSION` обязательным значением, а `APP_NAME` переопределением из окружения со значением по умолчанию
- определяет один переиспользуемый `LibConfig` с `endpoint` и `requestTimeout`
- извлекает тот же `LibConfig` для `lib1` и `lib2`
- переиспользует один общий YAML-объект и переопределяет только одно поле для второй библиотеки
- печатает все итоговые значения в `stdout` во время запуска

## Что потребуется { #youll-need }

- JDK 17 или новее
- Gradle 7+
- редактор кода или среда разработки
- пройденное руководство [Создание первого приложения на Kora](getting-started.md)

## Требования { #prerequisites }

!!! note "Требуется: завершить начальное руководство"

    Это руководство предполагает, что вы прошли **[Создание первого приложения на Kora](getting-started.md)** и уже имеете запускаемый проект Kora с плагином `application` и сгенерированным графом приложения.

    Если вы еще не создали такую базовую заготовку, сначала пройдите начальное руководство, потому что этот материал сосредоточен на типизированной конфигурации, а не на первоначальной настройке проекта.

## Обзор { #overview }

Конфигурация — это способ, которым окружения времени выполнения влияют на поведение приложения без изменения кода. Порты, учетные данные, переключатели возможностей, тайм-ауты и адреса внешних
сервисов должны жить вне скомпилированных классов, но коду приложения все равно нужен типобезопасный способ читать эти значения.

Главный урок: конфигурация должна быть явной на границе приложения. Компоненты не должны сами искать переменные окружения или разбирать файлы; они должны получать типизированную конфигурацию из графа.

### YAML и типобезопасное извлечение { #yaml-type-safe-extraction }

Kora умеет читать конфигурацию [YAML](https://yaml.org/spec/) через [SnakeYAML](https://github.com/snakeyaml/snakeyaml) и извлекать ее в Java-интерфейсы или записи. Вместо передачи сырых строк и
словарей через приложение, компоненты получают типизированные объекты конфигурации. Это делает обязательные значения явными и позволяет компилятору помогать при использовании конфигурации.

В этом руководстве используются два взаимодополняющих стиля отображения:

- `@ConfigSource("app")` связывает одну фиксированную секцию конфигурации с типобезопасной зависимостью
- `@ConfigValueExtractor` описывает переиспользуемую форму конфигурации, которую можно извлекать из разных путей

Используйте `@ConfigSource`, когда компоненту нужна одна стабильная секция конфигурации приложения. Используйте `@ConfigValueExtractor`, когда одна и та же структура встречается в нескольких местах и
нужен один переиспользуемый извлекатель.

### Обязательные и значения по умолчанию { #required-default }

YAML поддерживает полезные возможности композиции:

- обязательную подстановку из переменной окружения, например `${APP_VERSION}`
- подстановку из переменной окружения со значением по умолчанию, например `${APP_NAME:Task Management App}`
- переиспользование объекта через подстановки Kora из другой YAML-секции

Эти возможности помогают одному файлу конфигурации оставаться читаемым и при этом адаптироваться к локальной разработке, тестам и развернутым окружениям.

Как контракт protobuf в gRPC или контракт кеша в кешировании, тип конфигурации является контрактом границы. Он говорит, какие значения времени выполнения ожидает приложение и какую форму эти значения
должны иметь.

### Конфигурация как зависимость графа { #configuration-graph-dependency }

В Kora конфигурация является частью графа зависимостей. Компонент может запросить типизированный объект конфигурации в конструкторе так же, как репозиторий или клиент. Это делает зависимости от
конфигурации видимыми и тестируемыми. Также это удерживает разбор конфигурации на границе графа, а не размазывает его по коду приложения.

Практический поток:

1. добавить модуль конфигурации YAML
2. определить фиксированный источник конфигурации приложения
3. связать обязательные значения и значения по умолчанию
4. определить переиспользуемый извлекатель значений
5. переиспользовать одну форму конфигурации для настроек нескольких библиотек
6. запустить приложение и посмотреть итоговую конфигурацию

## Зависимости { #dependencies }

Добавьте модуль YAML в существующий проект и оставьте логирование включенным, чтобы поведение при запуске было видно во время обучения.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy title="build.gradle"
    plugins {
        id "application"
    }

    dependencies {
        implementation "ru.tinkoff.kora:config-yaml"
        implementation "ru.tinkoff.kora:logging-logback"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    plugins {
        id("application")
    }

    dependencies {
        implementation("ru.tinkoff.kora:config-yaml")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

Почему это важно:

- `config-yaml` включает загрузку YAML-файла в граф приложения
- `logging-logback` делает запуск и диагностику неполадок видимыми, пока приложение работает

## Модули { #modules }

Начните с минимального графа приложения, который может загрузить YAML-конфигурацию и запустить приложение Kora.

На этом этапе мы еще не добавляем конфигурацию, специфичную для приложения. Мы только подготавливаем граф, чтобы на следующих шагах связать типизированную конфигурацию и напечатать итоговые значения.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/config/yaml/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.config.yaml;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.yaml.YamlConfigModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            YamlConfigModule,  // <----- Подключили модуль
            LogbackModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/config/yaml/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.config.yaml

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.yaml.YamlConfigModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        YamlConfigModule,  // <----- Подключили модуль
        LogbackModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Почему это важно:

- `YamlConfigModule` активирует загрузку конфигурации в формате YAML
- `LogbackModule` подключает базовое логирование для запуска и диагностики
- граф пока остается минимальным: он только умеет стартовать приложение и читать файл конфигурации

Типизированные секции появятся постепенно: сначала секция приложения, затем отдельная форма для библиотек и только после этого явное связывание путей `libs.lib1` и `libs.lib2` с двумя экземплярами одного типа.

Если хотите больше контекста о связывании графа и фабриках, смотрите [документацию по контейнеру](../documentation/container.md).

## Конфигурация приложения { #app-config }

Теперь добавим первый типизированный контракт конфигурации: стабильную секцию приложения с именем `app`.

Это самый простой и самый частый шаблон конфигурации в Kora. Вместо ручного чтения ключей вы один раз объявляете форму и внедряете ее туда, где она нужна.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/config/yaml/AppConfig.java`:

    ```java
    package ru.tinkoff.kora.guide.config.yaml;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("app")
    public interface AppConfig {

        String name();

        String version();

        String environment();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/config/yaml/AppConfig.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.config.yaml

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("app")
    interface AppConfig {
        fun name(): String
        fun version(): String
        fun environment(): String
    }
    ```

Почему это важно:

- `@ConfigSource("app")` делает секцию `app` полноценной зависимостью
- контракт остается рядом с кодом, который его использует
- рефакторинг ключей конфигурации становится безопаснее, потому что структура явно описана в одном месте

## Обязательные значения { #required-values }

Когда `AppConfig` определен, можно решить, какие значения обязательны, а какие могут использовать значения по умолчанию.

Обновите `src/main/resources/application.yaml`:

```yaml title="src/main/resources/application.yaml"
app:
    name: ${APP_NAME:Task Management App}
    version: ${APP_VERSION}
    environment: "development"
```

Что это означает:

- `version: ${APP_VERSION}` является обязательным, поэтому запуск завершается ошибкой, если `APP_VERSION` отсутствует
- `name: ${APP_NAME:Task Management App}` использует `APP_NAME`, когда переменная существует, а иначе возвращается к значению по умолчанию
- `environment` остается обычным статическим значением, потому что в этом руководстве его пока не нужно менять

Это важный шаблон YAML: критически важные значения должны завершать запуск с ошибкой как можно раньше, а косметические или зависящие от окружения значения должны легко переопределяться.

Подробнее о правилах подстановки и поддерживаемых типах значений смотрите в [документации по конфигурации](../documentation/config.md).

## Конфигурация библиотек { #library-config }

Теперь создадим переиспользуемую форму конфигурации для одной библиотеки.

Представим, что абстрактной библиотеке нужны две настройки:

- `endpoint`
- `requestTimeout`

Вместо хранения этих значений как сырых ключей, опишите их один раз как тип.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/config/yaml/LibConfig.java`:

    ```java
    package ru.tinkoff.kora.guide.config.yaml;

    import java.time.Duration;
    import ru.tinkoff.kora.config.common.annotation.ConfigValueExtractor;

    @ConfigValueExtractor
    public interface LibConfig {

        String endpoint();

        Duration requestTimeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/config/yaml/LibConfig.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.config.yaml

    import java.time.Duration
    import ru.tinkoff.kora.config.common.annotation.ConfigValueExtractor

    @ConfigValueExtractor
    interface LibConfig {
        fun endpoint(): String
        fun requestTimeout(): Duration
    }
    ```

Теперь, когда тип `LibConfig` уже объявлен, можно вернуться к графу приложения и явно показать, откуда берутся две библиотечные конфигурации.

`@ConfigValueExtractor` генерирует извлекатель для формы `LibConfig`, а методы графа выбирают конкретные ветки файла конфигурации. Так Kora получает два разных экземпляра одного типа: один для `libs.lib1`, второй для `libs.lib2`.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/ru/tinkoff/kora/guide/config/yaml/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.config.yaml;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.config.common.Config;
    import ru.tinkoff.kora.config.common.extractor.ConfigValueExtractor;
    import ru.tinkoff.kora.config.yaml.YamlConfigModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            YamlConfigModule,  // <----- Подключили модуль
            LogbackModule {

        final class Lib1Tag {
            private Lib1Tag() {}
        }

        final class Lib2Tag {
            private Lib2Tag() {}
        }

        @Tag(Lib1Tag.class)
        default LibConfig lib1Config(Config config, ConfigValueExtractor<LibConfig> extractor) {
            return extractor.extract(config.get("libs.lib1"));
        }

        @Tag(Lib2Tag.class)
        default LibConfig lib2Config(Config config, ConfigValueExtractor<LibConfig> extractor) {
            return extractor.extract(config.get("libs.lib2"));
        }

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/config/yaml/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.config.yaml

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.config.common.Config
    import ru.tinkoff.kora.config.common.extractor.ConfigValueExtractor
    import ru.tinkoff.kora.config.yaml.YamlConfigModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        YamlConfigModule,  // <----- Подключили модуль
        LogbackModule {

        class Lib1Tag private constructor()
        class Lib2Tag private constructor()

        @Tag(Lib1Tag::class)
        fun lib1Config(config: Config, extractor: ConfigValueExtractor<LibConfig>): LibConfig {
            return extractor.extract(config.get("libs.lib1"))
        }

        @Tag(Lib2Tag::class)
        fun lib2Config(config: Config, extractor: ConfigValueExtractor<LibConfig>): LibConfig {
            return extractor.extract(config.get("libs.lib2"))
        }
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Что здесь происходит:

- `Lib1Tag` и `Lib2Tag` различают два экземпляра `LibConfig` в графе
- `config.get("libs.lib1")` и `config.get("libs.lib2")` выбирают разные ветки конфигурации
- `ConfigValueExtractor<LibConfig>` преобразует каждую ветку в типизированный объект

Добавьте первую секцию библиотеки в `application.yaml`:

```yaml title="src/main/resources/application.yaml"
app:
    name: ${APP_NAME:Task Management App}
    version: ${APP_VERSION}
    environment: "development"

libs:
    lib1:
        endpoint: "https://integration.local/api"
        requestTimeout: "5s"
```

На этом этапе `LibConfig` используется только для `lib1`. Граф приложения извлекает его из `libs.lib1`, а Kora напрямую преобразует `"5s"` в `Duration`.

## Файл конфигурации { #config-file }

Теперь представим, что второй библиотеке нужна ровно такая же форма.

Можно продублировать весь блок конфигурации, но YAML вместе с подстановками Kora дает лучший вариант: положить общие скалярные значения в одну секцию и ссылаться на эти значения там, где нужно.

Снова обновите `application.yaml`:

```yaml title="src/main/resources/application.yaml"
app:
    name: ${APP_NAME:Task Management App}
    version: ${APP_VERSION}
    environment: "development"

commonLib:
    endpoint: "https://integration.local/api"
    requestTimeout: "5s"

libs:
    lib1:
        endpoint: ${commonLib.endpoint}
        requestTimeout: ${commonLib.requestTimeout}
    lib2:
        endpoint: "https://integration-2.local/api"
        requestTimeout: ${commonLib.requestTimeout}
```

Что изменилось:

- `commonLib` хранит общие скалярные значения один раз
- `libs.lib1` ссылается на оба общих значения
- `libs.lib2` переопределяет только `endpoint`
- `libs.lib2.requestTimeout` все еще переиспользует общий тайм-аут

В этом и есть выигрыш от сочетания переиспользования YAML с `@ConfigValueExtractor`: одна форма конфигурации, несколько извлеченных экземпляров, минимум дублирования.

## Итоговые значения { #resolved-values }

Последний шаг — доказать, что все внедрилось корректно.

Вместо HTTP-маршрута это руководство использует маленький компонент `@Root`, который печатает все итоговые значения в стандартный вывод во время запуска. Это похоже на проверку через консоль из руководства по
внедрению зависимостей.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/config/yaml/ConfigRunner.java`:

    ```java
    package ru.tinkoff.kora.guide.config.yaml;

    import java.util.LinkedHashMap;
    import java.util.Map;
    import ru.tinkoff.kora.application.graph.Lifecycle;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.common.annotation.Root;

    @Root
    @Component
    public final class ConfigRunner implements Lifecycle {

        private final AppConfig appConfig;
        private final LibConfig lib1Config;
        private final LibConfig lib2Config;

        public ConfigRunner(
            AppConfig appConfig,
            @Tag(Application.Lib1Tag.class) LibConfig lib1Config,
            @Tag(Application.Lib2Tag.class) LibConfig lib2Config
        ) {
            this.appConfig = appConfig;
            this.lib1Config = lib1Config;
            this.lib2Config = lib2Config;
        }

        public Map<String, String> snapshot() {
            Map<String, String> values = new LinkedHashMap<>();
            values.put("name", this.appConfig.name());
            values.put("version", this.appConfig.version());
            values.put("environment", this.appConfig.environment());
            values.put("lib1.endpoint", this.lib1Config.endpoint());
            values.put("lib1.requestTimeout", this.lib1Config.requestTimeout().toString());
            values.put("lib2.endpoint", this.lib2Config.endpoint());
            values.put("lib2.requestTimeout", this.lib2Config.requestTimeout().toString());
            return values;
        }

        @Override
        public void init() {
            System.out.println("Config guide start");
            this.snapshot().forEach((key, value) -> System.out.println(key + "=" + value));
        }

        @Override
        public void release() {
            System.out.println("Application shutdown");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/config/yaml/ConfigRunner.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.config.yaml

    import ru.tinkoff.kora.application.graph.Lifecycle
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.common.annotation.Root

    @Root
    @Component
    class ConfigRunner(
        private val appConfig: AppConfig,
        @Tag(Application.Lib1Tag::class) private val lib1Config: LibConfig,
        @Tag(Application.Lib2Tag::class) private val lib2Config: LibConfig,
    ) : Lifecycle {

        fun snapshot(): Map<String, String> {
            return linkedMapOf(
                "name" to appConfig.name(),
                "version" to appConfig.version(),
                "environment" to appConfig.environment(),
                "lib1.endpoint" to lib1Config.endpoint(),
                "lib1.requestTimeout" to lib1Config.requestTimeout().toString(),
                "lib2.endpoint" to lib2Config.endpoint(),
                "lib2.requestTimeout" to lib2Config.requestTimeout().toString(),
            )
        }

        override fun init() {
            println("Config guide start")
            snapshot().forEach { (key, value) -> println("$key=$value") }
        }

        override fun release() {
            println("Application shutdown")
        }
    }
    ```

Почему это важно:

- `@Root` гарантирует, что запускаемый компонент действительно будет создан при старте приложения
- `Lifecycle` дает естественное место для печати или проверки внедренных значений
- `snapshot()` удерживает вывод во время выполнения и тесты вокруг одного контракта

## Запуск приложения { #run-app }

Используйте стандартную последовательность действий из руководств:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

В запускаемом примере задача `run` внедряет `APP_VERSION` из `koraVersion` в `gradle.properties`, поэтому обычный `./gradlew run` работает из коробки.

Если хотите также переопределить имя приложения, добавьте `APP_NAME` перед запуском:

```bash
APP_NAME="Custom Task App" ./gradlew run
```

## Вывод приложения { #output }

Когда приложение стартует, оно должно напечатать примерно такой вывод:

```text
Config guide start
name=Task Management App
version=1.0.0
environment=development
lib1.endpoint=https://integration.local/api
lib1.requestTimeout=PT5S
lib2.endpoint=https://integration-2.local/api
lib2.requestTimeout=PT5S
```

Если вы передадите `APP_NAME`, напечатанная строка `name=` должна показать переопределение.

## Вторая конфигурация { #config-2 }

Частый следующий шаг — держать отдельные файлы конфигурации для разных окружений, например разработки, стенда или промышленного окружения.

Например, создайте `src/main/resources/application-prod.yaml`:

```yaml
app:
    name: ${APP_NAME:Task Management App}
    version: ${APP_VERSION}
    environment: "production"

commonLib:
    endpoint: "https://integration.local/api"
    requestTimeout: "5s"

libs:
    lib1:
        endpoint: ${commonLib.endpoint}
        requestTimeout: ${commonLib.requestTimeout}
    lib2:
        endpoint: "https://integration-2.local/api"
        requestTimeout: ${commonLib.requestTimeout}
```

Этот файл сохраняет ту же форму, что и `application.yaml`, и меняет только значение окружения. YAML-конфигурация выбирается через свойство Kora `config.resource`, поэтому альтернативный ресурс должен
быть достаточно полным, чтобы приложение могло стартовать самостоятельно.

Запустить приложение с этой конфигурацией можно через системное свойство Kora `config.resource`:

```bash
./gradlew run -Dconfig.resource=application-prod.yaml
```

С таким переопределением вывод при запуске должен напечатать:

```text
environment=production
```

Подробнее о поиске файлов и внешних файлах конфигурации смотрите в [документации по конфигурации](../documentation/config.md).

## Лучшие практики { #best-practices }

- Используйте `@ConfigSource` для стабильной конфигурации уровня приложения, которая принадлежит одной хорошо известной секции.
- Используйте `@ConfigValueExtractor`, когда одна форма конфигурации переиспользуется под несколькими путями.
- Держите обязательные значения явными через `${VAR_NAME}`, а значения по умолчанию явными через `${VAR_NAME:default}`.
- Предпочитайте общие YAML-секции плюс подстановки Kora вместо копирования одинаковых скалярных значений в несколько секций.
- Пока изучаете поведение конфигурации, держите диагностику запуска простой; `System.out.println(...)` достаточно для учебной последовательности действий.

## Итоги { #summary }

Теперь у вас есть рабочее приложение Kora на основе YAML, которое связывает конфигурацию двумя способами. `AppConfig` отображает стабильную секцию `app`, а `LibConfig` дважды извлекается из двух
разных путей с разными метками. Переиспользование YAML делает файл компактным, а одно переопределение меняет только `endpoint` второй библиотеки.

## Ключевые понятия { #key-concepts }

**`@ConfigSource`:**

- отображает одну фиксированную секцию конфигурации на типобезопасный интерфейс
- хорошо подходит для настроек приложения вроде `app.name` и `app.environment`

**Обязательные значения и значения по умолчанию:**

- `${APP_VERSION}` является обязательным и завершает запуск с ошибкой как можно раньше, если значение отсутствует
- `${APP_NAME:Task Management App}` использует значение из окружения, когда оно присутствует, а иначе возвращается к настроенному значению по умолчанию

**`@ConfigValueExtractor` и переиспользование:**

- одну форму конфигурации можно извлекать из нескольких путей
- общая секция вроде `commonLib` может один раз хранить скалярные значения по умолчанию
- подстановки вроде `${commonLib.requestTimeout}` переиспользуют эти скалярные значения в нескольких типизированных секциях конфигурации

## Устранение неполадок { #troubleshooting }

**Приложение падает при старте из-за неразрешенной подстановки:**

`app.version: ${APP_VERSION}` является обязательным. В запускаемом примере задача `run` предоставляет его автоматически из `koraVersion`. Если вы удалите это связывание Gradle, нужно
задать `APP_VERSION` перед запуском.

**`APP_NAME` не меняет имя по умолчанию:**

Используйте форму подстановки со значением по умолчанию:

```yaml
name: ${APP_NAME:Task Management App}
```

**Значения конфигурации библиотеки дублируются между секциями:**

Перенесите общие скалярные значения в секцию вроде `commonLib` и ссылайтесь на них через подстановки вида `${commonLib.requestTimeout}` вместо копирования одного и того же значения в обе библиотеки.

**Сборка зависает или падает неожиданно:**

Остановите демоны Gradle и повторите:

```bash
./gradlew --stop
./gradlew clean classes
```

**`AccessDeniedException` в кеше Gradle на Windows:**

Если кешированные файлы заблокированы другим процессом, повторите запуск со свежим кешем текущего запуска:

```bash
GRADLE_USER_HOME=.gradle-user-home ./gradlew test
```

## Что дальше? { #whats-next }

- [Конфигурация HOCON](config-hocon.md), чтобы сравнить YAML с распространенной для Kora настройкой на основе HOCON.
- [Работа с JSON](json.md), чтобы сделать DTO запросов и ответов явными в небольшом приложении, которое у вас уже есть.
- [Создание HTTP-сервера](http-server.md) после JSON, потому что это руководство опирается на отображение JSON DTO и превращает приложение в более полноценный HTTP API.
- [Изучите основы внедрения зависимостей](dependency-injection-introduction.md), если сгенерированный граф и фабрики конфигурации все еще кажутся неочевидными.

## Помощь { #help }

Если возникли проблемы:

- сравните с [Kora Java Config YAML App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-config-yaml-app) и [Kora Kotlin Config YAML App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-config-yaml-app)
- проверьте [документацию по конфигурации](../documentation/config.md)
- проверьте [документацию по контейнеру](../documentation/container.md)
- прочитайте [спецификацию YAML](https://yaml.org/spec/)
