---
search:
  exclude: true
title: Управление HOCON-конфигурацией в Kora
summary: Learn how to bind HOCON configuration to type-safe interfaces, separate required and optional values, and reuse one config shape across multiple integrations
description: "Step-by-step type-safe HOCON configuration for a Kora 2.0 service: the io.koraframework:config-hocon artifact, HoconConfigModule, @ConfigSource for an application section, @ConfigMapper plus ConfigValueMapper.mapOrThrow for a reusable library shape, @Tag to bind one config type to several paths, required ${VAR} and optional ${?VAR} substitutions, HOCON object reuse and include, config.resource and config.file selection, and the generated config mapper and module sources."
agent:
  use_when: "Use this file for questions about typed HOCON configuration in a Kora 2.0 service: io.koraframework:config-hocon, HoconConfigModule, @ConfigSource, @ConfigMapper, ConfigValueMapper with map and mapOrThrow, Config.get, @Tag for two instances of one config type, required values versus @Nullable and default methods, ${APP_VERSION} and ${?APP_NAME} substitutions, HOCON object reuse and include, -Dconfig.resource and -Dconfig.file, and generated $Type_ConfigValueMapper sources."
tags: configuration, hocon, configsource, configmapper
---

# Управление HOCON-конфигурацией в Kora { #hocon-configuration-management-kora }

Это руководство знакомит с типобезопасной конфигурацией в Kora и HOCON. Оно показывает, как значения конфигурации отображаются из `application.conf` в типизированные интерфейсы, как обязательные и
необязательные значения выражаются в коде на Java и Kotlin, и как один переиспользуемый формат конфигурации можно привязать к нескольким секциям без дублирования целого блока. Также вы увидите, как
переменные окружения и вывод значений во время выполнения помогают легко проверять итоговую конфигурацию.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Config HOCON App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-config-hocon-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Config HOCON App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-config-hocon-app).

## Что вы создадите { #youll-build }

Вы соберете небольшое запускаемое приложение Kora, которое:

- связывает `app.name`, `app.version` и `app.environment` через `@ConfigSource`
- считает `APP_VERSION` обязательным значением, а `APP_NAME` необязательным переопределением
- определяет один переиспользуемый `LibConfig` с `endpoint` и `requestTimeout`
- отображает тот же `LibConfig` для `lib1` и `lib2`
- переиспользует один общий HOCON-объект и переопределяет только одно поле для второй библиотеки
- печатает все итоговые значения в `stdout` во время запуска

## Что потребуется { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Текстовый редактор или IDE
- Пройденное руководство [Создание первого приложения Kora](getting-started.md)

Артефакты Kora 2.0 собраны под Java 25, поэтому JDK, которым компилируется приложение, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Обязательно: пройденное вводное руководство"

    Это руководство предполагает, что вы прошли **[Создание первого приложения Kora](getting-started.md)** и у вас уже есть запускаемый проект Kora с плагином `application` и сгенерированным графом приложения.

    Если такой основы еще нет, сначала пройдите вводное руководство: здесь мы сосредоточены на типизированной конфигурации, а не на начальной настройке проекта.

## Обзор { #overview }

Конфигурация — это способ влиять на поведение приложения из среды выполнения, не меняя код. Порты, учетные данные, переключатели функциональности, таймауты и адреса внешних сервисов должны жить вне
скомпилированных классов, но коду приложения все равно нужен типобезопасный способ их читать.

Главный урок в том, что конфигурация должна быть явной на границе приложения. Компоненты не должны сами искать переменные окружения или разбирать файлы; они должны получать типизированную конфигурацию
из графа.

### HOCON и типобезопасное отображение { #hocon-type-safe-extraction }

Kora умеет читать конфигурацию в формате [HOCON](https://github.com/lightbend/config/blob/main/HOCON.md) и отображать ее в интерфейсы Java или Kotlin. Вместо того чтобы протаскивать через приложение
сырые строки и словари, компоненты получают типизированные объекты конфигурации. Это делает обязательные значения явными и позволяет компилятору помогать с использованием конфигурации.

В этом руководстве используются два дополняющих друг друга стиля отображения:

- `@ConfigSource("app")` отображает одну фиксированную секцию конфигурации в типобезопасную зависимость
- `@ConfigMapper` отображает переиспользуемый формат конфигурации, который можно привязать к разным путям

Используйте `@ConfigSource`, когда компоненту нужна одна стабильная секция конфигурации приложения. Используйте `@ConfigMapper`, когда та же структура встречается в нескольких местах и нужно одно
переиспользуемое правило отображения, путь для которого выбирается в фабрике модуля.

Обе аннотации генерируют реализацию `ConfigValueMapper<T>` на этапе компиляции. Разница только в том, кто выбирает путь: `@ConfigSource` зашивает его в сгенерированный модуль, а `@ConfigMapper`
оставляет выбор вам.

### Обязательные и необязательные значения { #required-optional }

HOCON поддерживает полезные средства композиции:

- обязательная подстановка из окружения вида `${APP_VERSION}`
- необязательная подстановка из окружения вида `${?APP_NAME}`
- переиспользование объекта вида `${common-lib}`

Эти возможности позволяют одному файлу конфигурации оставаться читаемым и при этом подстраиваться под локальную разработку, тесты и развернутые окружения.

Со стороны кода правило столь же короткое: каждый метод интерфейса конфигурации — обязательное значение, если он не помечен как допускающий `null` и не имеет реализации `default`. Как protobuf-контракт
в gRPC или контракт кэша в кэшировании, тип конфигурации — это контракт границы. Он говорит, какие значения среды выполнения ожидает приложение и какую форму эти значения должны иметь.

### Конфигурация как зависимость графа { #configuration-graph-dependency }

В Kora конфигурация — часть графа зависимостей. Компонент может запросить типизированный объект конфигурации в конструкторе так же, как запрашивает репозиторий или клиент. Это делает зависимости от
конфигурации видимыми и тестируемыми, а разбор конфигурации остается на границе графа, а не размазывается по коду приложения.

Практический порядок действий:

1. подключить модуль конфигурации HOCON
2. определить фиксированный источник конфигурации приложения
3. связать обязательные и необязательные значения
4. определить переиспользуемый маппер конфигурации
5. переиспользовать один формат конфигурации для настроек нескольких библиотек
6. запустить приложение и изучить итоговую конфигурацию

## Зависимости { #dependencies }

Добавьте модуль HOCON в существующий проект и оставьте логирование включенным, чтобы поведение при запуске было видно во время обучения.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy title="build.gradle"
    plugins {
        id "application"
    }

    dependencies {
        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:logging-logback"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    plugins {
        id("application")
    }

    dependencies {
        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:logging-logback")
    }
    ```

Почему это важно:

- `config-hocon` включает загрузку HOCON-файлов в графе приложения
- `logging-logback` сохраняет видимость логов запуска и диагностики во время работы приложения

Версии берутся из платформы `io.koraframework:kora-bom`, которую проект уже импортирует, поэтому указывать версию здесь не нужно.

## Модули { #modules }

Начните с минимально возможного графа приложения, который умеет загружать HOCON-конфигурацию и запускать приложение Kora.

На этом шаге мы еще не добавляем конфигурацию, специфичную для приложения. Мы только готовим граф, чтобы дальше можно было связать типизированную конфигурацию и вывести итоговые значения.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/config/hocon/Application.java`:

    ```java
    package io.koraframework.guide.config.hocon;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,  // <----- Connected module
            LogbackModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/config/hocon/Application.kt`:

    ```kotlin
    package io.koraframework.guide.config.hocon

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,  // <----- Connected module
        LogbackModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Почему это важно:

- `HoconConfigModule` активирует загрузку конфигурации на основе HOCON
- `LogbackModule` добавляет базовые логи запуска и диагностики
- граф пока остается минимальным: он умеет запустить приложение и прочитать файл конфигурации

`HoconConfigModule` также решает, какой файл читать. Если системные свойства не заданы, он ищет `application.conf` в classpath; `config.resource` и `config.file` переопределяют этот выбор, и первое из
них мы используем в конце руководства.

Типизированные секции вводятся постепенно: сначала секция приложения, затем переиспользуемый формат для библиотеки, и только после этого явное отображение `libs.lib1` и `libs.lib2` в два экземпляра одного типа.

Если нужно больше контекста про связывание графа и фабрики, посмотрите [документацию по контейнеру](../documentation/container.md).

## Конфигурация приложения { #app-config }

Теперь введем первый типизированный контракт конфигурации: стабильную секцию приложения с именем `app`.

Это самый простой и самый частый паттерн конфигурации в Kora. Вместо ручного чтения ключей вы один раз объявляете форму и внедряете ее там, где она нужна.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/config/hocon/AppConfig.java`:

    ```java
    package io.koraframework.guide.config.hocon;

    import io.koraframework.config.common.annotation.ConfigSource;

    @ConfigSource("app")
    public interface AppConfig {

        String name();

        String version();

        String environment();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/config/hocon/AppConfig.kt`:

    ```kotlin
    package io.koraframework.guide.config.hocon

    import io.koraframework.config.common.annotation.ConfigSource

    @ConfigSource("app")
    interface AppConfig {
        fun name(): String
        fun version(): String
        fun environment(): String
    }
    ```

Почему это важно:

- `@ConfigSource("app")` делает секцию `app` полноценной зависимостью
- контракт находится рядом с кодом, который его использует
- рефакторинг ключей конфигурации становится безопаснее, потому что структура явно описана в одном месте

Все три метода возвращают типы, не допускающие `null`, поэтому все три значения обязательны. Сделать одно из них необязательным — это правка кода, а не файла: пометьте его `@Nullable` в Java или
верните nullable-тип в Kotlin. Имена методов сопоставляются нестрого, поэтому `someBarString()` читается также из `some-bar-string` и `some_bar_string`.

## Обязательные значения { #required-values }

Теперь, когда `AppConfig` определен, можно решить, какие значения обязательны, а какие могут опираться на значения по умолчанию.

Обновите `src/main/resources/application.conf`:

```hocon title="src/main/resources/application.conf"
app {
  name = "Task Management App"
  name = ${?APP_NAME}
  version = ${APP_VERSION}
  environment = "development"
}
```

Что это означает:

- `version = ${APP_VERSION}` обязателен, поэтому запуск падает, если `APP_VERSION` отсутствует
- `name = ${?APP_NAME}` необязателен и переопределяет значение по умолчанию только тогда, когда переменная существует
- `environment` остается обычным статическим значением, потому что в этом руководстве его менять не требуется

Это важный паттерн HOCON: критичные значения должны падать сразу, а косметические или зависящие от окружения переопределения оставаться необязательными.

Обратите внимание: две строки `name` — не ошибка. HOCON сохраняет последнее присваивание ключа, а `${?APP_NAME}` не дает ничего, когда переменная не задана, поэтому литерал выше выживает. Именно так в
HOCON записывается значение по умолчанию вместе с необязательным переопределением.

Подробнее о правилах подстановки и поддерживаемых типах значений — в [документации по конфигурации](../documentation/config.md).

## Конфигурация библиотек { #library-config }

Дальше создадим переиспользуемый формат конфигурации для одной библиотеки.

Представим, что некоторой абстрактной библиотеке нужны две настройки:

- `endpoint`
- `requestTimeout`

Вместо того чтобы держать их как сырые ключи, опишем их один раз как тип.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/config/hocon/LibConfig.java`:

    ```java
    package io.koraframework.guide.config.hocon;

    import java.time.Duration;
    import io.koraframework.config.common.annotation.ConfigMapper;

    @ConfigMapper
    public interface LibConfig {

        String endpoint();

        Duration requestTimeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/config/hocon/LibConfig.kt`:

    ```kotlin
    package io.koraframework.guide.config.hocon

    import io.koraframework.config.common.annotation.ConfigMapper
    import java.time.Duration

    @ConfigMapper
    interface LibConfig {
        fun endpoint(): String
        fun requestTimeout(): Duration
    }
    ```

Теперь, когда `LibConfig` существует, вернемся к графу приложения и явно покажем, откуда берутся две конфигурации библиотек.

`@ConfigMapper` генерирует `ConfigValueMapper<LibConfig>` для этой формы, но не привязывает путь, а методы графа выбирают конкретные ветки файла конфигурации. Так Kora получает два разных экземпляра одного типа: один для `libs.lib1` и один для `libs.lib2`.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/io/koraframework/guide/config/hocon/Application.java`:

    ```java
    package io.koraframework.guide.config.hocon;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.config.common.Config;
    import io.koraframework.config.common.mapper.ConfigValueMapper;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,  // <----- Connected module
            LogbackModule {

        final class Lib1Tag {}

        final class Lib2Tag {}

        @Tag(Lib1Tag.class)
        default LibConfig lib1Config(Config config, ConfigValueMapper<LibConfig> mapper) {
            return mapper.mapOrThrow(config.get("libs.lib1"));
        }

        @Tag(Lib2Tag.class)
        default LibConfig lib2Config(Config config, ConfigValueMapper<LibConfig> mapper) {
            return mapper.mapOrThrow(config.get("libs.lib2"));
        }

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/io/koraframework/guide/config/hocon/Application.kt`:

    ```kotlin
    package io.koraframework.guide.config.hocon

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.common.annotation.Tag
    import io.koraframework.config.common.Config
    import io.koraframework.config.common.mapper.ConfigValueMapper
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,  // <----- Connected module
        LogbackModule {

        class Lib1Tag private constructor()
        class Lib2Tag private constructor()

        @Tag(Lib1Tag::class)
        fun lib1Config(config: Config, mapper: ConfigValueMapper<LibConfig>): LibConfig {
            return mapper.mapOrThrow(config.get("libs.lib1"))
        }

        @Tag(Lib2Tag::class)
        fun lib2Config(config: Config, mapper: ConfigValueMapper<LibConfig>): LibConfig {
            return mapper.mapOrThrow(config.get("libs.lib2"))
        }
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Что здесь происходит:

- `Lib1Tag` и `Lib2Tag` различают два экземпляра `LibConfig` в графе
- `config.get("libs.lib1")` и `config.get("libs.lib2")` выбирают разные ветки конфигурации
- `ConfigValueMapper<LibConfig>` превращает каждую ветку в типизированный объект

У `ConfigValueMapper<T>` есть два метода чтения. `map(...)` может вернуть `null`, а `mapOrThrow(...)` превращает этот `null` в `ConfigValueException`. В фабричных методах обычно используют
`mapOrThrow(...)`, потому что отсутствующая секция библиотеки — это ошибка запуска, а не допустимое состояние.

Теперь обе фабрики входят в граф, поэтому обе секции обязаны существовать. Добавьте их в `application.conf`:

```hocon title="src/main/resources/application.conf"
app {
  name = "Task Management App"
  name = ${?APP_NAME}
  version = ${APP_VERSION}
  environment = "development"
}

libs {
  lib1 {
    endpoint = "https://integration.local/api"
    requestTimeout = 5s
  }
  lib2 {
    endpoint = "https://integration-2.local/api"
    requestTimeout = 5s
  }
}
```

На этом шаге приложение запускается, а Kora преобразует `5s` прямо в `Duration`. Но две секции почти одинаковы, и именно это дублирование убирает следующий шаг.

## Файл конфигурации { #config-file }

Обеим библиотекам нужна ровно одна и та же форма, а сейчас общие значения скопированы дважды.

HOCON дает лучший вариант: положить общие значения в один объект и переиспользовать этот объект там, где он нужен.

Снова обновите `application.conf`:

```hocon title="src/main/resources/application.conf"
app {
  name = "Task Management App"
  name = ${?APP_NAME}
  version = ${APP_VERSION}
  environment = "development"
}

common-lib = {
  endpoint = "https://integration.local/api"
  requestTimeout = 5s
}

libs.lib1 = ${common-lib}
libs.lib2 = ${common-lib}
libs.lib2.endpoint = "https://integration-2.local/api"
```

Что изменилось:

- `common-lib` теперь хранит общие значения по умолчанию один раз
- `libs.lib1` переиспользует объект целиком
- `libs.lib2` тоже переиспользует объект целиком
- `libs.lib2.endpoint` переопределяет после этого только одно поле

В последних трех строках важен порядок: `libs.lib2.endpoint` должен идти после `libs.lib2 = ${common-lib}`, иначе присваивание объекта целиком затерло бы его.

В этом и польза от сочетания переиспользования HOCON с `@ConfigMapper`: один формат конфигурации, несколько отображенных экземпляров, минимум дублирования.

## Итоговые значения { #resolved-values }

Последний шаг — убедиться, что все было внедрено правильно.

Вместо HTTP-эндпоинта в этом руководстве используется небольшой `@Root`-компонент, который печатает все итоговые значения в стандартный вывод во время запуска. Это повторяет консольную проверку из
руководства по внедрению зависимостей.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/config/hocon/ConfigRunner.java`:

    ```java
    package io.koraframework.guide.config.hocon;

    import java.util.LinkedHashMap;
    import java.util.Map;
    import io.koraframework.application.graph.Lifecycle;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Root;
    import io.koraframework.common.annotation.Tag;

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

    Создайте `src/main/kotlin/io/koraframework/guide/config/hocon/ConfigRunner.kt`:

    ```kotlin
    package io.koraframework.guide.config.hocon

    import io.koraframework.application.graph.Lifecycle
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Root
    import io.koraframework.common.annotation.Tag

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

- `@Root` гарантирует, что компонент действительно будет создан при запуске приложения
- `Lifecycle` дает естественное место для вывода или проверки внедренных значений
- `snapshot()` удерживает вывод во время выполнения и тесты вокруг одного контракта

Те же маркеры `@Tag`, которые различали две фабрики, теперь выбирают, какой `LibConfig` получит каждый параметр конструктора. Без них граф не смог бы отличить два компонента друг от друга.

## Сгенерированный код конфигурации { #config-code }

Как и все остальное в Kora, отображение конфигурации генерируется на этапе компиляции. После `./gradlew clean classes` посмотрите, что создал обработчик:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-config-hocon-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/config/hocon/AppConfigModule.java
    guides/java/kora-java-guide-config-hocon-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/config/hocon/$AppConfig_ConfigValueMapper.java
    guides/java/kora-java-guide-config-hocon-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/config/hocon/$LibConfig_ConfigValueMapper.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-config-hocon-app/build/generated/ksp/main/kotlin/io/koraframework/guide/config/hocon/AppConfigModule.kt
    guides/kotlin/kora-kotlin-guide-config-hocon-app/build/generated/ksp/main/kotlin/io/koraframework/guide/config/hocon/$AppConfig_ConfigValueMapper.kt
    guides/kotlin/kora-kotlin-guide-config-hocon-app/build/generated/ksp/main/kotlin/io/koraframework/guide/config/hocon/$LibConfig_ConfigValueMapper.kt
    ```

`@ConfigSource` создал целый модуль, и выглядит он ровно так же, как фабрики, написанные вами вручную для `LibConfig`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface AppConfigModule {
      default AppConfig appConfig(Config config, ConfigValueMapper<AppConfig> mapper) {
        return mapper.mapOrThrow(config.get("app"));
      }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    public interface AppConfigModule {
      public fun appConfig(config: Config, mapper: ConfigValueMapper<AppConfig>): AppConfig = mapper.mapOrThrow(config.get("app"))
    }
    ```

В этом и вся разница между двумя аннотациями: `@ConfigSource` пишет этот модуль за вас для фиксированного пути, а `@ConfigMapper` — нет, поэтому для `LibConfig` вы написали две фабрики с тегами.

Сам маппер показывает, где именно проверяются обязательные значения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private String parse_endpoint(ConfigValue.ObjectValue config) {
      var value = config.get(_endpoint_path);
      if (value instanceof ConfigValue.NullValue nullValue) {
        throw ConfigValueException.missingValue(nullValue);
      }
      return value.asString();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private fun parse_endpoint(config: ConfigValue.ObjectValue): String {
      val value = config.get(_endpoint_path)
      if (value is ConfigValue.NullValue) {
        throw ConfigValueException.missingValue(value)
      }
      return value.asString()
    }
    ```

`requestTimeout` обрабатывается иначе: вместо написанной вручную ветки сгенерированный маппер принимает `ConfigValueMapper<Duration>` как зависимость конструктора. Любой поддерживаемый тип значения
попадает в маппер тем же путем — так позже можно добавить собственный тип, не трогая интерфейс конфигурации.

## Запуск приложения { #run-app }

Используйте стандартный порядок из руководств:

```bash
./gradlew clean classes
./gradlew test
```

`app.version` обязателен, поэтому `APP_VERSION` должен присутствовать до запуска приложения:

```bash
APP_VERSION=1.0.0 ./gradlew run
```

В запускаемом Java-примере задача `run` уже подставляет `APP_VERSION` из `koraVersion` в `gradle.properties`, поэтому там обычный `./gradlew run` работает сразу.

Если нужно переопределить еще и имя приложения, добавьте `APP_NAME` перед запуском:

```bash
APP_VERSION=1.0.0 APP_NAME="Custom Task App" ./gradlew run
```

## Вывод приложения { #output }

При запуске приложение печатает:

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

`PT5S` — это запись `Duration.ofSeconds(5)` в формате ISO-8601, что подтверждает: `5s` был отображен в настоящий `Duration`, а не в строку. Если задать `APP_NAME`, выведенная строка `name=` отразит
переопределение:

```text
name=Custom Task App
```

## Вторая конфигурация { #config-2 }

Частый следующий шаг — держать отдельные файлы конфигурации для разных окружений: разработки, тестового стенда или продакшена.

Например, создайте `src/main/resources/application-prod.conf`:

```hocon title="src/main/resources/application-prod.conf"
include "application"

app {
  environment = "production"
}
```

Этот файл переиспользует базовую конфигурацию из `application.conf` через директиву HOCON `include` и переопределяет только те значения, которые отличаются для продакшена. Включенные файлы участвуют в
том же слиянии и разрешении подстановок, что и основной файл, поэтому `${APP_VERSION}` продолжает работать.

Альтернативный файл выбирается системным свойством `config.resource`. Плагин Gradle `application` не передает флаги `-D` из командной строки в процесс приложения, поэтому объявите свойство в задаче
`run`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    run {
        jvmArgs += [
                "-Dconfig.resource=application-prod.conf"
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    tasks.named<JavaExec>("run") {
        jvmArgs("-Dconfig.resource=application-prod.conf")
    }
    ```

Собранный дистрибутив принимает то же свойство через `JAVA_OPTS`:

```bash
JAVA_OPTS="-Dconfig.resource=application-prod.conf" ./bin/application
```

С этим переопределением вывод при запуске печатает:

```text
environment=production
```

Используйте `config.file` вместо `config.resource`, чтобы читать файл с диска, а не из classpath. Одновременно можно задать только одно из двух: если заданы оба, приложение падает при запуске с
`Application config source is ambiguous`.

Подробнее о выборе файла и внешних файлах конфигурации — в [документации по конфигурации](../documentation/config.md).

## Лучшие практики { #best-practices }

- Используйте `@ConfigSource` для стабильной конфигурации уровня приложения, относящейся к одной известной секции.
- Используйте `@ConfigMapper`, когда один формат конфигурации переиспользуется по нескольким путям, и выбирайте путь в фабрике модуля.
- Предпочитайте `mapOrThrow(...)` вместо `map(...)` в фабриках, чтобы отсутствующая секция падала при запуске, а не давала `null`.
- Делайте обязательные значения явными через `${VAR_NAME}`, а необязательные переопределения — через `${?VAR_NAME}`.
- Предпочитайте переиспользование объекта с небольшими переопределениями полей копированию больших блоков конфигурации.
- Держите диагностику при запуске простой, пока изучаете поведение конфигурации; `System.out.println(...)` вполне достаточно для учебных сценариев.

## Итоги { #summary }

Теперь у вас есть рабочее приложение Kora на HOCON, которое связывает конфигурацию двумя способами. `AppConfig` отображает стабильную секцию `app`, а `LibConfig` отображается дважды из двух разных
путей с разными тегами. Переиспользование в HOCON делает файл компактным, а одно переопределение меняет только endpoint второй библиотеки.

## Ключевые понятия { #key-concepts }

**`@ConfigSource`:**

- отображает одну фиксированную секцию конфигурации в типобезопасный интерфейс
- генерирует модуль, который сам вызывает `mapOrThrow(config.get("app"))`
- хорошо подходит для настроек приложения вроде `app.name` и `app.environment`

**Обязательные и необязательные значения:**

- каждый метод интерфейса обязателен, если он не допускает `null` и не имеет реализации `default`
- `${APP_VERSION}` обязателен и падает сразу, когда значение отсутствует
- `${?APP_NAME}` необязателен и переопределяет значение по умолчанию только тогда, когда присутствует

**`@ConfigMapper` и переиспользование:**

- генерирует `ConfigValueMapper<T>` без привязки к пути
- один формат конфигурации можно отобразить из нескольких путей, различая их через `@Tag`
- `${common-lib}` копирует объект целиком в другой путь
- последующее присваивание вида `libs.lib2.endpoint = ...` переопределяет только одно поле

## Устранение неполадок { #troubleshooting }

**Приложение падает при запуске из-за неразрешенной подстановки:**

`app.version = ${APP_VERSION}` обязателен. В запускаемом Java-примере задача `run` подставляет его автоматически из `koraVersion`. В остальных случаях нужно задать `APP_VERSION` перед запуском.

**Запуск падает с `Config expected value, but got null at path: '...'`:**

В итоговой конфигурации отсутствует обязательное значение. Либо добавьте ключ в файл, либо сделайте метод необязательным через `@Nullable` в Java или nullable-тип возврата в Kotlin, либо дайте ему
реализацию `default`.

**`APP_NAME` не переопределяет имя по умолчанию:**

HOCON сохраняет последнее присваивание, поэтому необязательное переопределение должно идти после значения по умолчанию:

```hocon
name = "Task Management App"
name = ${?APP_NAME}
```

**Значения конфигурации библиотек дублируются между секциями:**

Перенесите общие значения в один объект, например `common-lib`, и переиспользуйте его через `${common-lib}` вместо копирования целого блока в обе библиотеки.

**`Application config source is ambiguous`:**

Заданы одновременно `config.resource` и `config.file`. Уберите одно из двух системных свойств.

**Сборка зависает или неожиданно падает:**

Остановите демоны Gradle и повторите:

```bash
./gradlew --stop
./gradlew clean classes
```

**`AccessDeniedException` в кэше Gradle на Windows:**

Если закэшированные файлы заблокированы другим процессом, повторите со свежим кэшем сессии:

```bash
GRADLE_USER_HOME=.gradle-user-home ./gradlew test
```

## Что дальше? { #whats-next }

- [YAML-конфигурация](config-yaml.md), чтобы увидеть ту же модель типизированной конфигурации в другом формате файла.
- [Работа с JSON](json.md), чтобы сделать DTO запросов и ответов явными в том небольшом приложении, которое у вас уже есть.
- [Создание HTTP-сервера](http-server.md) после JSON, так как это руководство опирается на отображение JSON-DTO и превращает приложение в более полноценное HTTP API.
- [Основы внедрения зависимостей](dependency-injection-introduction.md), если сгенерированный граф и фабрики конфигурации все еще кажутся непонятными.

## Помощь { #help }

Если возникли сложности:

- сравните с [Kora Java Config HOCON App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-config-hocon-app) и [Kora Kotlin Config HOCON App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-config-hocon-app)
- посмотрите [документацию по конфигурации](../documentation/config.md)
- посмотрите [документацию по контейнеру](../documentation/container.md)
- посмотрите [пример конфигурации HOCON](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-config-hocon)
- прочитайте [спецификацию HOCON](https://github.com/lightbend/config/blob/master/HOCON.md)
