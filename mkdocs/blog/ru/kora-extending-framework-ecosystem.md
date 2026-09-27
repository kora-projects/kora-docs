---
title: Экосистема, которую вы можете построить — почему расширять фреймворк Kora намеренно просто
date: 2026-09-05
description: Как тонкие абстракции и модульная модель фреймворка Kora позволяют командам интегрировать любую Java-библиотеку через тот же граф приложения.
search:
  exclude: true
---

# Экосистема, которую вы можете построить: почему расширять Kora намеренно просто { #ecosystem-you-can-build }

**5 сентября 2026**

Экосистемы фреймворков обычно обсуждаются как инвентаризации.

Сколько интеграций баз данных поставляет фреймворк? У скольких систем обмена сообщениями есть официальные модули? Есть ли стартер для Elasticsearch? Есть ли стартер для NATS? Есть ли стартер для
MinIO? А как насчёт ClickHouse, нового облачного SDK, движка рабочих процессов, клиента фича-флагов, проприетарного внутреннего сервиса или инфраструктурного продукта, появившегося шесть месяцев назад
и ещё не попавшего ни в чью дорожную карту фреймворка?

Такой способ измерения экосистемы понятен, потому что готовые интеграции полезны. Если фреймворк уже поддерживает ровно ту технологию, которая нужна команде, кто-то другой уже решил конфигурацию,
жизненный цикл, внедрение зависимостей, метрики, трассировку, проверки здоровья, поведение завершения, тестирование и, возможно, генерацию кода. Команда может начать с работающей интеграции вместо
того, чтобы строить её.

Но подсчёт интеграций — лишь один способ оценить экосистему, и он может вводить в заблуждение, когда рассматривается как основной показатель зрелости фреймворка.

Часто более важен такой вопрос:

> **Настоящий вопрос не в том, сколько интеграций фреймворк уже поставляет, а в том, насколько дорого добавить ту, которая вам действительно нужна.**

Это различие важно для фреймворка Kora, потому что Kora не пытается выиграть конкурс экосистем, оборачивая каждую Java-библиотеку за специфичным для фреймворка API. Её заявленная философия уже:
использовать контролируемый набор продакшен-ориентированных модулей, держать абстракции тонкими, держать связку приложения явной, позволять заменять компоненты фреймворка и давать командам добавлять
собственные модули через ту же модель приложения, которую использует сама Kora.

Это производит другое определение экосистемы.

В традиционной модели большой экосистемы ценность фреймворка частично в количестве уже доступных адаптеров:

```text
Модель большой экосистемы

Нужна технология X
      ↓
Найти официальный/сообщественный стартер
      ↓
Изучить его абстракцию
      ↓
Изучить его конфигурацию
      ↓
Зависеть от его обслуживания
      ↓
Использовать технологию X через стартер
```

В модели расширяемого фреймворка путь может быть короче:

```text
Модель расширяемого фреймворка

Нужна технология X
      ↓
Использовать нативную Java-библиотеку
      ↓
Раскрыть её через маленький модуль Kora
      ↓
Добавить жизненный цикл/конфигурацию/телеметрию/пробы
      ↓
Использовать её нормально через DI
```

Вторая модель не устраняет интеграции. Сама Kora поставляет интеграции для HTTP, JDBC, Cassandra, Kafka, gRPC, S3 и другой инфраструктуры. Она также предоставляет производственные задачи, такие как
конфигурация, телеметрия, пробы здоровья, отказоустойчивость, планирование, валидация, кеширование и тестирование. Разница в том, что эти интеграции не должны устанавливать правило, что каждая внешняя
технология сначала должна быть переведена в большую специфичную для Kora подсистему, прежде чем код приложения сможет её использовать.

Это центральный аргумент этой статьи.

Маленькая экосистема — серьёзная проблема, когда фреймворк трудно расширять. Она гораздо менее серьезна, когда расширение фреймворка — локальное, типизированное и прозрачное упражнение.

А архитектура Kora необычно хорошо подходит для второй модели.

---

## Размер экосистемы и трение экосистемы — разные вещи { #ecosystem-size-vs-friction }

Представьте два фреймворка.

Фреймворк A поставляет 500 интеграций. Большинство раскрыто через специфичные для фреймворка абстракции, конвенции конфигурации, хуки жизненного цикла, стартер-зависимости и механизмы расширения
рантайма. Интеграция технологии за пределами этого каталога требует понимания нескольких внутренностей фреймворка и воспроизведения конвенций, которые не очевидны из обычного кода приложения.

Фреймворк B поставляет 50 интеграций. Его граф приложения явный, модули — обычные интерфейсы с фабричными методами, конфигурация типизирована, жизненный цикл — маленький интерфейс, пробы — обычные
компоненты, телеметрия строится из обычных Java-контрактов, а приложение может заменять компоненты по умолчанию, просто объявляя другую фабрику.

У какого фреймворка лучше экосистема?

Если нужная вам технология — интеграция номер 327 в фреймворке A, фреймворк A сегодня может быть явно удобнее.

Если нужная вам технология — интеграция номер 501, ответ становится менее очевидным.

Фреймворк с 500 интеграциями, которые трудно понять, не обязательно более расширяем, чем фреймворк с 50 интеграциями, где 51-ю можно написать в нескольких прямолинейных классах.

Это разница между *широтой экосистемы* и *эластичностью экосистемы*.

Широта спрашивает:

```text
Сколько уже присутствует?
```

Эластичность спрашивает:

```text
Насколько дорога следующая отсутствующая вещь?
```

Оба важны, но второе часто недооценивается.

Причина проста: реальные производственные системы в итоге содержат что-то за пределами официального каталога фреймворка.

Это может быть внутренний RPC-клиент. Может быть SDK вендора. Может быть драйвер базы данных, который фреймворк не знает. Может быть устройство безопасности. Может быть новая платформа обмена
сообщениями. Может быть специализированный облачный продукт. Может быть проприетарная библиотека, поддерживаемая другой командой в той же компании.

В этот момент практическое качество фреймворка определяется не размером его существующей экосистемы, а стоимостью пересечения его границы.

---

## Почему большие экосистемы стали такими ценными { #why-large-ecosystems }

Есть историческая причина, по которой Java-разработчики часто приравнивают зрелость фреймворка к количеству интеграций.

Годами интеграция инфраструктуры в корпоративные Java-приложения была по-настоящему дорогой. Библиотеке редко требовалось только конструирование. Ей также нужны были привязка конфигурации, жизненный
цикл соединений, управление потоками, проверки здоровья, участие в транзакциях, метрики, трассировка, политики повторов, обработка завершения, внедрение зависимостей и тестовая инфраструктура.

Стартеры фреймворков упаковывали эти задачи в переиспользуемые единицы.

Экосистема Spring — очевидный пример. Ценность Spring Boot никогда не была только во внедрении зависимостей. Значительная часть его ценности в том, что команды могут добавить зависимость, настроить
несколько свойств и автоматически получить значительный объём инфраструктурного поведения.

Это чрезвычайно полезно.

Но есть компромисс. Чем больше поведения владеет стартер, тем больше разработчики зависят от абстракции стартера, модели конфигурации, условной логики, конвенций рантайма и графика обслуживания.
Собственная документация базовой библиотеки может стать недостаточной, потому что интеграция фреймворка меняет то, как библиотека создаётся или используется.

Это ведёт ко второй экосистеме, наслоенной поверх первой.

Например, вместо изучения только:

```text
NATS Java client
```

разработчикам может понадобиться изучить:

```text
Стартер NATS фреймворка
+
свойства фреймворка
+
обёрточный API фреймворка
+
правила жизненного цикла фреймворка
+
поведение телеметрии фреймворка
+
нативные концепции NATS
```

Этот дополнительный слой может быть оправдан, когда он даёт значительную ценность.

Вопрос в том, обязателен ли он для каждой интеграции.

Дизайн Kora предполагает, что часто нет.

---

## Модель расширения Kora начинается с обычной Java { #extension-model-ordinary-java }

Модель внедрения зависимостей Kora важна здесь, потому что модули — не скрытые дескрипторы плагинов рантайма.

Модуль фундаментально — интерфейс, содержащий фабричные методы.

Концептуально:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface MyLibraryModule {

        default MyClient myClient(MyClientConfig config) {
            return new MyClient(config.endpoint());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface MyLibraryModule {

        fun myClient(config: MyClientConfig): MyClient {
            return MyClient(config.endpoint())
        }
    }
    ```

Возвращаемое значение становится компонентом в графе приложения. Параметры метода — зависимости. Kora валидирует этот граф на этапе компиляции и генерирует обычный код запуска.

Этого уже достаточно, чтобы интегрировать многие Java-библиотеки.

Библиотеке не нужно знать о Kora.

Библиотеке не нужен специфичный для Kora интерфейс адаптера.

Библиотеку не нужно обнаруживать динамически.

Приложению не нужен реестр плагинов рантайма.

Интеграционная граница — просто фабрика:

```text
граф Kora
   ↓
фабричный метод
   ↓
объект нативной библиотеки
```

Как только этот объект в графе, другие компоненты внедряют его нормально.

Это звучит почти тривиально, и именно в этом суть.

Механизм расширения фреймворка наиболее здоров, когда простые расширения просты.

---

## `@Module` — механизм композиции, а не мини-фреймворк { #module-composition }

Соблазн при построении интеграций фреймворка — изобрести другой фреймворк внутри фреймворка.

Предположим, команда хочет поддержку NATS. Она могла бы создать большую специфичную для Kora абстракцию:

```text
KoraNatsClient
KoraNatsPublisher
KoraNatsSubscriber
KoraNatsMessage
KoraNatsHeaders
KoraNatsConsumerFactory
KoraNatsConnectionManager
KoraNatsTemplate
KoraNatsProperties
```

Код приложения тогда использовал бы эти типы вместо официального NATS Java API.

Это может быть оправдано, если фреймворк может предоставить значимую семантику, которой не хватает нативной библиотеке. Но делать это по умолчанию создаёт семантический разрыв.

Разработчикам теперь приходится переводить документацию:

```text
документация NATS
        ↓
Как это отображается на KoraNatsTemplate?
        ↓
Что Kora скрывает?
        ↓
Что настраивается?
        ↓
Какая версия базовой библиотеки обёрнута?
```

Модель модулей Kora допускает гораздо меньшую интеграцию:

```text
NatsConfig
NatsModule
NatsTelemetry
NatsReadinessProbe
```

а сам клиент может оставаться:

===! ":fontawesome-brands-java: `Java`"

    ```java
    io.nats.client.Connection
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    io.nats.client.Connection
    ```

Это значит, что каждый пример в официальной NATS Java-документации остаётся полезным.

Если NATS завтра добавит новый API, код приложения часто сможет использовать его немедленно после обновления зависимости. Интеграции фреймворка не обязательно сначала нужна новая абстракция.

Это одно из самых сильных следствий тонких абстракций:

> **Тонкие абстракции сохраняют документацию и экосистему базовой технологии.**

Kora не нужно воссоздавать экосистему NATS, потому что она может компоноваться с ней.

---

## Что на самом деле нужно инфраструктурной интеграции { #infrastructure-integration-needs }

Полезно отделять обязательные ответственности фреймворка от ответственностей нативной библиотеки.

Для типичной клиентской библиотеки нативная библиотека должна владеть доменным поведением:

```text
протоколом
сериализацией
семантикой соединения
семантикой переподключения
запросами
публикацией
подписками
ошибками, специфичными для клиента
настройкой, специфичной для клиента
```

Фреймворку приложения нужно подключить эту библиотеку к жизненному циклу сервиса:

```text
типизированная конфигурация
связка зависимостей
запуск
завершение
телеметрия
здоровье/готовность
тестирование
опциональные обёртки политик
```

Это даёт нам общий конвейер интеграции:

```text
Нативная библиотека
      ↓
Типизированная конфигурация
      ↓
Фабрика клиента
      ↓
Жизненный цикл
      ↓
Модуль Kora
      ↓
Телеметрия
      ↓
Пробы
      ↓
Внедрение в приложение
```

Большинство кастомных интеграций Kora могут остановиться здесь.

Нет необходимости строить универсальную подсистему расширения, если интеграция действительно не требует генерации кода или более глубокого поведения этапа компиляции.

Это различие важно, потому что у Kora действительно есть механизм расширения этапа компиляции для продвинутых случаев. Модули фреймворка могут учить компилятор создавать зависимости, такие как
сгенерированные репозитории, декларативные HTTP-клиенты, мапперы, валидаторы или gRPC-стабы. Но это инструмент уровня системы, а не обычная отправная точка для интеграции Java SDK.

Обычный путь гораздо проще: сначала фабричные методы и компоненты графа; расширение компилятора — только когда генерация создаёт реальную ценность.

---

## Пошаговый разбор: интегрируем библиотеку, которую Kora не поддерживает { #walkthrough }

Чтобы сделать аргумент конкретным, рассмотрим NATS.

Предположим, нашему приложению на Kora нужен официальный NATS Java-клиент. Мы хотим:

- типизированную конфигурацию;
- одно общее NATS-соединение;
- установление соединения при запуске;
- корректное завершение;
- готовность соединения;
- базовую телеметрию вокруг публикации;
- обычное внедрение зависимостей;
- прямой доступ к нативному NATS API.

Важное ограничение: мы не будем изобретать NATS-фреймворк внутри Kora.

Код приложения должен по-прежнему понимать, что использует NATS.

Итоговая форма зависимостей будет выглядеть так:

```text
application.conf
      ↓
NatsConfig
      ↓
NatsModule
      ↓
Соединение NATS
      ├─────────────→ NatsPublisher
      ├─────────────→ NatsReadinessProbe
      └─────────────→ сервисы приложения
                         ↓
                    нативный NATS API
```

Это намеренно скучно.

Это фича.

---

## Шаг 1: Добавьте нативную библиотеку { #step-1-native-library }

Gradle-зависимость принадлежит экосистеме NATS, а не Kora:

```groovy
dependencies {
    implementation "io.nats:jnats:<version>"
}
```

Ничто в этой зависимости не должно меняться из-за того, что приложение использует Kora.

Если команда читает официальный NATS-пример, показывающий:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Connection connection = Nats.connect(options);
    connection.publish("orders.created", payload);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val connection = Nats.connect(options)
    connection.publish("orders.created", payload)
    ```

эти знания остаются напрямую применимыми.

Это первый признак того, что интеграция тонкая.

---

## Шаг 2: Определите типизированную конфигурацию { #step-2-typed-config }

В Kora 2 конфигурация может моделироваться как типизированный интерфейс и привязываться напрямую к пути конфигурации.

Например:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package com.example.nats;

    import io.koraframework.config.common.annotation.ConfigSource;

    import java.time.Duration;
    import java.util.List;

    @ConfigSource("nats")
    public interface NatsConfig {

        List<String> servers();

        default String connectionName() {
            return "orders-service";
        }

        default int maxReconnects() {
            return -1;
        }

        default Duration connectionTimeout() {
            return Duration.ofSeconds(5);
        }

        default boolean readinessEnabled() {
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package com.example.nats

    import io.koraframework.config.common.annotation.ConfigSource
    import java.time.Duration

    @ConfigSource("nats")
    interface NatsConfig {

        fun servers(): List<String>

        fun connectionName(): String {
            return "orders-service"
        }

        fun maxReconnects(): Int {
            return -1
        }

        fun connectionTimeout(): Duration {
            return Duration.ofSeconds(5)
        }

        fun readinessEnabled(): Boolean {
            return true
        }
    }
    ```

Конфигурация HOCON приложения может оставаться столь же прямой:

===! ":material-code-json: Hocon"

    ```hocon
    nats {
      servers = [
        "nats://nats-1:4222",
        "nats://nats-2:4222"
      ]

      connectionName = "orders-service"
      maxReconnects = -1
      connectionTimeout = 5s
      readinessEnabled = true
    }
    ```

=== ":simple-yaml: YAML"

    ```yaml
    nats:
      servers:
        - "nats://nats-1:4222"
        - "nats://nats-2:4222"
      connectionName: "orders-service"
      maxReconnects: -1
      connectionTimeout: 5s
      readinessEnabled: true
    ```

Нет универсального мешка свойств, передаваемого по приложению.

`NatsConfig` — типизированная зависимость графа.

Это важно для кастомных интеграций, потому что конфигурация становится частью архитектуры этапа компиляции. Фабричные методы запрашивают `NatsConfig`; сервисы не ищут снова и снова по сырым деревьям
конфигурации; тесты могут заменять или предоставлять конфигурацию явно.

Теперь у интеграции есть чёткий контракт:

```text
конфигурация
     ↓
NatsConfig
```

---

## Шаг 3: Создайте нативные NATS Options { #step-3-nats-options }

Следующий компонент переводит конфигурацию сервиса в нативный объект NATS `Options`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    package com.example.nats;

    import io.nats.client.Options;
    import io.koraframework.common.annotation.Module;

    @Module
    public interface NatsModule {

        default Options natsOptions(NatsConfig config) {
            var builder = new Options.Builder()
                .servers(config.servers().toArray(String[]::new))
                .connectionName(config.connectionName())
                .maxReconnects(config.maxReconnects())
                .connectionTimeout(config.connectionTimeout());

            return builder.build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package com.example.nats

    import io.nats.client.Options
    import io.koraframework.common.annotation.Module

    @Module
    interface NatsModule {

        fun natsOptions(config: NatsConfig): Options {
            val builder = Options.Builder()
                .servers(config.servers().toTypedArray())
                .connectionName(config.connectionName())
                .maxReconnects(config.maxReconnects())
                .connectionTimeout(config.connectionTimeout())

            return builder.build()
        }
    }
    ```

Обратите внимание, чего мы *не* делаем.

Мы не воспроизводим каждое свойство `Options.Builder` в новой абстракции фреймворка.

Если проекту нужны только четыре опции, раскройте четыре опции.

Если позже понадобятся аутентификация, TLS, настройка переподключения или другая функция NATS, добавляйте их намеренно.

Интеграция остаётся сформированной под приложение, а не пытается зеркалить весь сторонний API.

Это одно из преимуществ локальных интеграций перед универсальными стартерами: они могут быть ровно такого размера, который требует приложение.

---

## Шаг 4: Дайте соединению жизненный цикл { #step-4-lifecycle }

Соединение — не просто значение. Оно владеет ресурсами и должно закрываться.

Модель жизненного цикла Kora делает это явным.

Один вариант — создать маленький компонент, реализующий `Lifecycle`. Другой — вернуть обёрнутый компонент из фабрики модуля. Если нативный клиент — `AutoCloseable`, Kora также может закрывать его
автоматически при освобождении графа.

Для ясности мы можем использовать выделенный держатель:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package com.example.nats;

    import io.nats.client.Connection;
    import io.nats.client.Nats;
    import io.nats.client.Options;
    import io.koraframework.application.graph.Lifecycle;

    public final class NatsConnectionLifecycle implements Lifecycle {

        private final Options options;
        private volatile Connection connection;

        public NatsConnectionLifecycle(Options options) {
            this.options = options;
        }

        @Override
        public void init() throws Exception {
            this.connection = Nats.connect(options);
        }

        @Override
        public void release() throws Exception {
            var current = this.connection;
            if (current != null) {
                current.close();
            }
        }

        public Connection connection() {
            var current = this.connection;
            if (current == null) {
                throw new IllegalStateException("NATS connection is not initialized");
            }
            return current;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package com.example.nats

    import io.nats.client.Connection
    import io.nats.client.Nats
    import io.nats.client.Options
    import io.koraframework.application.graph.Lifecycle

    class NatsConnectionLifecycle(private val options: Options) : Lifecycle {

        @Volatile
        private var connection: Connection? = null

        override fun init() {
            this.connection = Nats.connect(options)
        }

        override fun release() {
            connection?.close()
        }

        fun connection(): Connection {
            return connection
                ?: throw IllegalStateException("NATS connection is not initialized")
        }
    }
    ```

Затем раскройте и жизненный цикл, и соединение через модуль:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface NatsModule {

        default Options natsOptions(NatsConfig config) {
            return new Options.Builder()
                .servers(config.servers().toArray(String[]::new))
                .connectionName(config.connectionName())
                .maxReconnects(config.maxReconnects())
                .connectionTimeout(config.connectionTimeout())
                .build();
        }

        default NatsConnectionLifecycle natsConnectionLifecycle(Options options) {
            return new NatsConnectionLifecycle(options);
        }

        default Connection natsConnection(NatsConnectionLifecycle lifecycle) {
            return lifecycle.connection();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface NatsModule {

        fun natsOptions(config: NatsConfig): Options {
            return Options.Builder()
                .servers(config.servers().toTypedArray())
                .connectionName(config.connectionName())
                .maxReconnects(config.maxReconnects())
                .connectionTimeout(config.connectionTimeout())
                .build()
        }

        fun natsConnectionLifecycle(options: Options): NatsConnectionLifecycle {
            return NatsConnectionLifecycle(options)
        }

        fun natsConnection(lifecycle: NatsConnectionLifecycle): Connection {
            return lifecycle.connection()
        }
    }
    ```

В производственной реализации мы были бы осторожны с точным отношением инициализации графа, чтобы компонент соединения становился доступным после инициализации жизненного цикла. Kora также
предоставляет обёртки жизненного цикла специально для фабрик, возвращающих значение, требующее инициализации и освобождения.

Архитектурный момент не меняется:

```text
создать нативный клиент
      ↓
прикрепить жизненный цикл
      ↓
поместить нативный клиент в граф
```

Фреймворку не нужен скрытый пост-процессор бинов, чтобы обнаружить, что у NATS-соединения есть поведение запуска и завершения.

Жизненный цикл — это код.

---

## Более чистая версия с обёрткой жизненного цикла { #lifecycle-wrapper }

Для объекта библиотеки, который следует внедрять напрямую, механизм обёрток Kora может держать граф ещё меньше.

Концептуально:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default Wrapped<Connection> natsConnection(Options options) {
        var holder = new AtomicReference<Connection>();

        return new LifecycleWrapper<>(
            Nats.connect(options),
            connection -> {
                // опциональный хук инициализации
            },
            connection -> {
                connection.close();
            }
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun natsConnection(options: Options): Wrapped<Connection> {
        val holder = AtomicReference<Connection>()

        return LifecycleWrapper(
            Nats.connect(options),
            { connection ->
                // опциональный хук инициализации
            },
            { connection ->
                connection.close()
            }
        )
    }
    ```

Точную фабрику можно адаптировать к тому, происходит ли установление соединения во время конструирования или при явной инициализации, но полезное свойство `Wrapped<T>` в том, что код приложения может
запрашивать `Connection`, в то время как граф всё ещё знает, что у значения есть поведение жизненного цикла.

Этот паттерн обобщается на многие нативные клиенты:

```text
клиент ClickHouse
клиент Elasticsearch
клиент MinIO
SDK вендора
кастомный пул соединений
встроенный движок
```

Если клиент — просто обычный Java-объект, Kora обычно нуждается только в обычной фабрике плюс семантике жизненного цикла.

---

## Шаг 5: Добавьте маленький издатель уровня приложения { #step-5-publisher }

Приложение могло бы внедрять `Connection` напрямую повсюду:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class OrderEvents {

        private final Connection nats;

        public OrderEvents(Connection nats) {
            this.nats = nats;
        }

        public void created(byte[] payload) {
            nats.publish("orders.created", payload);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class OrderEvents(private val nats: Connection) {

        fun created(payload: ByteArray) {
            nats.publish("orders.created", payload)
        }
    }
    ```

Для многих систем это вполне приемлемо.

Если команда хочет централизованную телеметрию или именование subject'ов, добавьте одну тонкую обёртку уровня приложения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class NatsPublisher {

        private final Connection connection;
        private final NatsTelemetry telemetry;

        public NatsPublisher(Connection connection, NatsTelemetry telemetry) {
            this.connection = connection;
            this.telemetry = telemetry;
        }

        public void publish(String subject, byte[] payload) {
            var context = telemetry.publish(subject, payload.length);
            try {
                connection.publish(subject, payload);
                context.success();
            } catch (RuntimeException e) {
                context.failure(e);
                throw e;
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NatsPublisher(
        private val connection: Connection,
        private val telemetry: NatsTelemetry
    ) {

        fun publish(subject: String, payload: ByteArray) {
            val context = telemetry.publish(subject, payload.size)
            try {
                connection.publish(subject, payload)
                context.success()
            } catch (e: RuntimeException) {
                context.failure(e)
                throw e
            }
        }
    }
    ```

Эта обёртка не пытается заменить NATS-клиент.

Она добавляет одну задачу, которую приложение хочет стандартизировать.

Код приложения, которому нужны низкоуровневые операции NATS, может по-прежнему внедрять `Connection`.

Код приложения, который только публикует события, может внедрять `NatsPublisher`.

Именно так тонкая абстракция выглядит на практике.

---

## Шаг 6: Добавьте телеметрию без перестройки NATS { #step-6-telemetry }

Предположим, мы хотим метрики и трассировку вокруг публикаций приложения.

Определите маленький контракт:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface NatsTelemetry {

        PublishContext publish(String subject, int payloadBytes);

        interface PublishContext {
            void success();
            void failure(Throwable error);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface NatsTelemetry {

        fun publish(subject: String, payloadBytes: Int): PublishContext

        interface PublishContext {
            fun success()
            fun failure(error: Throwable)
        }
    }
    ```

Реализация на базе Micrometer/OpenTelemetry может использовать компоненты телеметрии, уже присутствующие в графе приложения.

Например, концептуально:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class DefaultNatsTelemetry implements NatsTelemetry {

        private final MeterRegistry meterRegistry;

        public DefaultNatsTelemetry(MeterRegistry meterRegistry) {
            this.meterRegistry = meterRegistry;
        }

        @Override
        public PublishContext publish(String subject, int payloadBytes) {
            var start = System.nanoTime();

            return new PublishContext() {
                @Override
                public void success() {
                    meterRegistry.counter(
                        "nats.publish",
                        "subject", subject,
                        "result", "success"
                    ).increment();

                    recordDuration(start, subject);
                }

                @Override
                public void failure(Throwable error) {
                    meterRegistry.counter(
                        "nats.publish",
                        "subject", subject,
                        "result", "failure"
                    ).increment();

                    recordDuration(start, subject);
                }
            };
        }

        private void recordDuration(long start, String subject) {
            var elapsed = System.nanoTime() - start;

            // Запись таймера опущена для краткости.
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class DefaultNatsTelemetry(private val meterRegistry: MeterRegistry) : NatsTelemetry {

        override fun publish(subject: String, payloadBytes: Int): NatsTelemetry.PublishContext {
            val start = System.nanoTime()

            return object : NatsTelemetry.PublishContext {
                override fun success() {
                    meterRegistry.counter(
                        "nats.publish",
                        "subject", subject,
                        "result", "success"
                    ).increment()

                    recordDuration(start, subject)
                }

                override fun failure(error: Throwable) {
                    meterRegistry.counter(
                        "nats.publish",
                        "subject", subject,
                        "result", "failure"
                    ).increment()

                    recordDuration(start, subject)
                }
            }
        }

        private fun recordDuration(start: Long, subject: String) {
            val elapsed = System.nanoTime() - start

            // Запись таймера опущена для краткости.
        }
    }
    ```

В реальной производственной реализации значения subject с высокой кардинальностью должны тщательно рассматриваться. Динамические NATS-subject'ы могут нуждаться в нормализации перед тем, как стать
тегами метрик.

Важный архитектурный момент в том, что телеметрия компонуема.

Нам не пришлось модифицировать рантайм Kora.

Нам не нужен центральный реестр плагинов.

Нам не нужно ждать официальный модуль `kora-nats`.

Мы взяли примитивы телеметрии, уже используемые приложением, и скомпоновали их вокруг нативного клиента.

Именно так концептуально структурированы собственные интеграции Kora: операции рантайма раскрывают логирование, метрики и трассировку через маленькие контракты телеметрии.

---

## Шаг 7: Добавьте готовность { #step-7-readiness }

Производственной интеграции также нужна операционная семантика.

Если этот сервис не может безопасно обрабатывать трафик, когда NATS отключён, NATS-соединение может участвовать в готовности.

Пробы Kora — обычные компоненты графа, реализующие маленькие интерфейсы.

Компонент готовности может выглядеть так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package com.example.nats;

    import io.nats.client.Connection;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.readiness.ReadinessProbe;
    import io.koraframework.common.readiness.ReadinessProbeFailure;

    @Component
    public final class NatsReadinessProbe implements ReadinessProbe {

        private final Connection connection;
        private final NatsConfig config;

        public NatsReadinessProbe(Connection connection, NatsConfig config) {
            this.connection = connection;
            this.config = config;
        }

        @Override
        public ReadinessProbeFailure probe() {
            if (!config.readinessEnabled()) {
                return null;
            }

            if (connection.getStatus() == Connection.Status.CONNECTED) {
                return null;
            }

            return new ReadinessProbeFailure(
                "NATS connection is not connected: " + connection.getStatus()
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package com.example.nats

    import io.nats.client.Connection
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.readiness.ReadinessProbe
    import io.koraframework.common.readiness.ReadinessProbeFailure

    @Component
    class NatsReadinessProbe(
        private val connection: Connection,
        private val config: NatsConfig
    ) : ReadinessProbe {

        override fun probe(): ReadinessProbeFailure? {
            if (!config.readinessEnabled()) {
                return null
            }

            if (connection.status == Connection.Status.CONNECTED) {
                return null
            }

            return ReadinessProbeFailure(
                "NATS connection is not connected: " + connection.status
            )
        }
    }
    ```

Теперь интеграция участвует в той же модели готовности приложения, что и HTTP-сервер, gRPC-сервер, источник данных JDBC и любой другой зарегистрированный компонент готовности.

Опять же, нет специального реестра расширений NATS.

Граф видит обычный `ReadinessProbe`.

Эндпоинт управления агрегирует его с остальными.

Это переиспользование через контракты, а не через скрытые точки расширения.

---

## Должен ли внешний брокер быть зависимостью готовности? { #readiness-dependency }

Этот разбор также раскрывает важное архитектурное преимущество явных интеграций: решения политики остаются видимыми.

Должно ли отключение NATS делать весь сервис неготовым — это не вопрос фреймворка. Это вопрос приложения.

Для одних сервисов NATS обязателен. Без него экземпляр не может выполнять свою работу, поэтому провал готовности может быть уместен.

Для другого сервиса публикация в NATS опциональна или буферизована. Вывод экземпляра из ротации из-за временной недоступности брокера может сделать отключение хуже.

Интеграция не должна молча решать эту политику.

Типизированный флаг конфигурации, такой как:

```text
readinessEnabled
```

делает решение явным.

Это ещё одна выгода от того, чтобы не переусложнять абстракцию. Интеграции фреймворка должны предоставлять механизмы; архитектура сервиса должна выбирать политику.

---

## Шаг 8: Внедряйте нативное соединение нормально { #step-8-inject-connection }

Как только модуль подключён к приложению, любой компонент может запрашивать `Connection`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FraudEvents {

        private final Connection nats;

        public FraudEvents(Connection nats) {
            this.nats = nats;
        }

        public void suspiciousTransaction(byte[] event) {
            nats.publish("fraud.suspicious", event);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FraudEvents(private val nats: Connection) {

        fun suspiciousTransaction(event: ByteArray) {
            nats.publish("fraud.suspicious", event)
        }
    }
    ```

Или он может запрашивать обёртку телеметрии:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class OrderEvents {

        private final NatsPublisher publisher;

        public OrderEvents(NatsPublisher publisher) {
            this.publisher = publisher;
        }

        public void created(byte[] event) {
            publisher.publish("orders.created", event);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class OrderEvents(private val publisher: NatsPublisher) {

        fun created(event: ByteArray) {
            publisher.publish("orders.created", event)
        }
    }
    ```

Больше ничего не меняется.

Приложение остаётся обычной Java с внедрением через конструктор.

---

## Шаг 9: Подключите модуль явно { #step-9-connect-module }

Kora намеренно не ищет внешние зависимости для произвольных модулей во время выполнения.

Это значит, что интеграция подключается явно.

Для локального модуля приложения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application
    ```

компилятор может обнаруживать локальные объявления `@Module` в той же области компиляции.

Если NATS-интеграция переносится в переиспользуемый модуль библиотеки, приложение может явно подключить свой внешний модуль через интерфейс приложения.

Концептуально:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends NatsModule, LogbackModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : NatsModule, LogbackModule
    ```

Итоговая архитектура приложения видна в точке сборки.

Это важно, потому что механизмы расширения имеют тенденцию становиться трудными для рассуждения, когда добавление зависимости молча добавляет поведение рантайма.

Модель Kora предпочитает:

```text
зависимость присутствует
+
модуль явно подключён
=
интеграция активна
```

а не:

```text
зависимость присутствует
=
возможно, активируется какая-то авто-конфигурация рантайма
в зависимости от classpath и конфигурации
```

Эта явность делает кастомные интеграции легче аудируемыми.

---

## Вся интеграция достаточно мала, чтобы её понять { #integration-small-enough }

Соберём части:

```text
NatsConfig
NatsModule
NatsTelemetry
DefaultNatsTelemetry
NatsPublisher
NatsReadinessProbe
```

Это уже продакшен-образная интеграция.

Если обработка жизненного цикла инкапсулирована в модуле, специфичная для приложения поверхность может составлять всего несколько классов.

Переиспользуемая внутренняя библиотека могла бы организовать их так:

```text
company-kora-nats/
├── NatsConfig.java
├── NatsModule.java
├── NatsTelemetry.java
├── DefaultNatsTelemetry.java
└── NatsReadinessProbe.java
```

Приложение использует:

```text
io.nats.client.Connection
```

для фактического API протокола NATS.

Нет фреймворка внутри фреймворка.

Это ключевой результат разбора.

---

## Почему `@Module` так хорошо работает для интеграций { #module-works-well }

Сила `@Module` в том, как мало он предполагает.

Фабричный метод говорит:

```text
Даны эти зависимости графа,
создай этот компонент графа.
```

Этого достаточно, чтобы выразить:

- нативные клиенты;
- пулы соединений;
- SDK;
- сериализаторы;
- реестры;
- исполнители;
- менеджеры;
- фабрики;
- адаптеры;
- объекты политик;
- инфраструктурные сервисы.

Рассмотрим ClickHouse.

Модуль может маппить конфигурацию в нативный клиент:

```text
ClickHouseConfig
      ↓
ClickHouseClient
```

Рассмотрим Elasticsearch:

```text
ElasticsearchConfig
      ↓
транспорт
      ↓
ElasticsearchClient
```

Рассмотрим MinIO:

```text
MinioConfig
      ↓
MinioClient
```

Рассмотрим новый облачный SDK:

```text
CloudConfig
      ↓
провайдер учётных данных
      ↓
SDK-клиент
```

Ни одному из них не требуется, чтобы Kora знала технологию.

Графу нужно знать только зависимости объектов.

---

## Конфигурация — интеграционная граница { #configuration-boundary }

Конфигурация часто там, где сторонние интеграции становятся грязными, потому что фреймворки пытаются поддерживать каждую опцию каждой библиотеки.

Типизированная модель конфигурации Kora поощряет более узкую стратегию.

Определяйте только то, что нужно вашему сервису.

Например:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("search")
    public interface SearchConfig {

        String endpoint();

        Duration timeout();

        default int maxConnections() {
            return 50;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("search")
    interface SearchConfig {

        fun endpoint(): String

        fun timeout(): Duration

        fun maxConnections(): Int {
            return 50
        }
    }
    ```

Затем постройте конфигурацию нативной библиотеки:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default SearchClient searchClient(SearchConfig config) {
        return SearchClient.builder()
            .endpoint(config.endpoint())
            .timeout(config.timeout())
            .maxConnections(config.maxConnections())
            .build();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun searchClient(config: SearchConfig): SearchClient {
        return SearchClient.builder()
            .endpoint(config.endpoint())
            .timeout(config.timeout())
            .maxConnections(config.maxConnections())
            .build()
    }
    ```

У этого несколько преимуществ.

Во-первых, конфигурация приложения остаётся стабильной, даже если нативная библиотека меняет некоторые имена билдера.

Во-вторых, сервис не раскрывает 80 нерелевантных свойств настройки только потому, что у библиотеки их 80.

В-третьих, конфигурация становится частью графа и может заменяться в тестах.

В-четвёртых, обязательные значения статически представлены как обязательные методы, а не недокументированные строки.

В-пятых, код маппинга конфигурации может генерироваться Kora вместо ручного разбора карт.

Поэтому кастомная интеграция получает продакшен-классную историю конфигурации почти бесплатно.

---

## Жизненный цикл — первоклассный контракт { #lifecycle-first-class }

Инфраструктурные библиотеки часто выделяют ресурсы:

- сокеты;
- исполнители;
- пулы соединений;
- файловые дескрипторы;
- фоновые воркеры;
- сетевые каналы;
- нативную память.

Интеграция фреймворка должна гарантировать, что эти ресурсы запускаются и останавливаются вместе с приложением.

Kora делает эту задачу явной через контракты жизненного цикла.

Компонент может реализовывать:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Lifecycle
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    Lifecycle
    ```

с:

```text
init()
release()
```

или фабрика может возвращать значение, обёрнутое жизненным циклом. Компоненты, реализующие `AutoCloseable`, также могут естественно участвовать в очистке.

Это важно для расширяемости, потому что жизненный цикл не привязан к специальному встроенному реестру интеграций.

Ваш кастомный клиент получает то же поведение контейнера, что и предоставляемая фреймворком инфраструктура.

Граф зависимостей также контролирует порядок.

Если:

```text
OrderConsumer
      ↓
Соединение NATS
```

то порядок создания и освобождения следует этим зависимостям.

Автору интеграции не нужно строить ещё один менеджер завершения.

---

## Здоровье и пробы — тоже обычные компоненты { #health-probes-ordinary }

Тот же паттерн появляется в проверках здоровья.

Системы живости и готовности Kora агрегируют компоненты, реализующие интерфейсы проб.

Кастомной инфраструктурной интеграции не нужно регистрировать колбэк в скрытой подсистеме здоровья.

Она может просто раскрыть:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ReadinessProbe
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    ReadinessProbe
    ```

или:

===! ":fontawesome-brands-java: `Java`"

    ```java
    LivenessProbe
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    LivenessProbe
    ```

как компонент.

Это значит, что неподдерживаемая технология может участвовать в операционной готовности ровно как встроенная технология.

Это важное различие между API расширения и моделью композиции.

API расширения обычно спрашивает:

```text
Как мне подключиться к подсистеме X?
```

Модель композиции спрашивает:

```text
Какой обычный контракт представляет эту задачу?
```

Второе имеет тенденцию производить более простые интеграции.

---

## Телеметрии не нужен универсальный адаптер { #telemetry-no-universal-adapter }

Телеметрия — это где интеграции фреймворков часто становятся большими, потому что каждая операция библиотеки может нуждаться в метриках и трассировке.

Но даже здесь не каждой интеграции нужен полный специфичный для фреймворка API.

Есть как минимум три уровня интеграции.

### Уровень 1: используйте нативную телеметрию { #level-1-native-telemetry }

Если Java-библиотека уже испускает метрики OpenTelemetry или Micrometer, просто настройте эти средства и раскройте соответствующие реестры через граф.

### Уровень 2: оберните операции приложения { #level-2-wrap-operations }

Если важны лишь несколько операций, используйте маленькую обёртку, такую как `NatsPublisher`.

```text
приложение
    ↓
маленькая обёртка телеметрии
    ↓
нативный клиент
```

### Уровень 3: постройте переиспользуемый контракт телеметрии Kora { #level-3-reusable-telemetry }

Если интеграция становится широко общей во многих сервисах, определите структурированную фабрику телеметрии, похожую на встроенные контракты телеметрии HTTP, базы данных, Kafka или gRPC Kora.

Важный момент в том, что команды могут эволюционировать от Уровня 1 к Уровню 3 по мере появления реального переиспользования.

Им не нужно строить Уровень 3 в первый же день только для подключения библиотеки.

Это резко снижает начальную стоимость 51-й интеграции.

---

## AOP доступен, когда интеграция действительно в нём нуждается { #aop-when-needed }

Большинству интеграций библиотек AOP не требуется.

Если интеграции нужны сквозные политики вокруг методов приложения, можно использовать модель AOP этапа компиляции Kora.

Примеры могут включать:

- повтор вокруг выбранных вызовов SDK;
- политики circuit breaker;
- границы таймаутов;
- кастомную авторизацию;
- логирование;
- валидацию;
- транзакционно-подобные области.

Но это должно быть решение второго порядка.

Сама интеграция обычно может оставаться обычным модулем.

Это важно, потому что фреймворки иногда затрудняют разработку расширений, требуя кастомных аннотаций и перехватчиков даже для базовой связки.

Более простой путь Kora:

```text
сначала фабрика
AOP только если нужно
```

а не:

```text
всё является плагином расширения
```

---

## Сгенерированный код не делает кастомные интеграции непрозрачными { #generated-code-not-opaque }

Kora активно использует генерацию кода, но это не значит, что интеграции приложения должны становиться компиляторными проектами.

Сгенерированная часть в первую очередь соединяет граф и контракты фреймворка.

Если `NatsPublisher` зависит от `Connection` и `NatsTelemetry`, сгенерированный граф приложения содержит связку, соответствующую этому отношению.

Автор интеграции всё равно пишет обычную Java.

Это создаёт полезное разделение:

```text
Ваша логика интеграции
       ↓
обычные Java-классы и фабрики

Сборка фреймворка
       ↓
сгенерированный код графа
```

Если связка зависимостей неверна, компиляция падает.

Если два соединения неоднозначны, теги могут сделать их явными.

Если требуемый компонент отсутствует, построение графа падает на этапе компиляции.

Нет необходимости отлаживать загрузчик плагинов рантайма, чтобы понять, почему интеграция не активировалась.

---

## Замена компонентов фреймворка — часть расширяемости { #replacing-components }

Расширяемость — не только о добавлении новых технологий.

Это также о замене частей существующих интеграций.

Модель DI Kora поддерживает компоненты по умолчанию, которые код приложения может переопределить компонентом, не являющимся значением по умолчанию, того же типа и тегов.

Это важно, потому что встроенные интеграции неизбежно делают выбор.

Фреймворк может предоставлять логгер по умолчанию, фабрику телеметрии, маппер, компонент HTTP-клиента, исполнитель, сериализатор или реализацию политики.

Закрытая интеграция говорит:

```text
Используйте нашу реализацию или замените весь модуль.
```

Композиционная интеграция говорит:

```text
Этот компонент — значение по умолчанию.
Предоставьте свой, если нужно другое поведение.
```

Это делает кастомизацию локальной.

Например:

```text
фабрика телеметрии Kora по умолчанию
            ↓
приложение поставляет кастомную реализацию
            ↓
граф выбирает компонент приложения
```

Нет форка.

Нет хака с отражением.

Нет хирургии определений бинов.

Нет недокументированного трюка с порядком.

Это свойство особенно важно для организаций, которые стандартизируют инфраструктуру иначе, чем значения по умолчанию фреймворка.

---

## Тонкие абстракции сохраняют знания вендора { #thin-abstractions-vendor }

Предположим, разработчик уже понимает Kafka.

Толстая абстракция фреймворка может уменьшить, сколько этих знаний переносится.

Разработчику теперь нужно знать, какие функции Kafka раскрыты, как назначение партиций отображается в абстракцию фреймворка, где живут настройки потребителя, как скрыты нативные типы, как переводятся
ошибки и меняет ли специфичный для фреймворка слой повторов семантику.

Тонкая абстракция сохраняет больше исходной ментальной модели.

То же самое применимо к:

- JDBC;
- gRPC;
- HTTP;
- NATS;
- Elasticsearch;
- ClickHouse;
- MinIO;
- AWS SDK;
- Google Cloud SDK;
- внутренним клиентам компании.

Это имеет главное следствие для экосистемы:

> Фреймворку не нужно владеть документацией каждой технологии, если он достаточно хорошо сохраняет нативную технологию, чтобы её документация оставалась валидной.

Это другая модель масштабирования.

Вместо построения:

```text
экосистема Kora
    содержащая
    новую документацию для всего
```

вы получаете:

```text
модель композиции Kora
        +
нативная технологическая экосистема
```

Вторая на практике может быть гораздо больше.

---

## Почему это важнее в эпоху ИИ { #ai-era }

Эта архитектура становится ещё ценнее, когда кодинг-агенты участвуют в разработке.

ИИ-агент часто уже имеет значительные знания о мейнстримных Java-библиотеках и протоколах.

Он может знать:

```text
NATS Java
Elasticsearch Java API Client
MinIO Java SDK
JDBC
Kafka
gRPC
OpenTelemetry
Micrometer
```

Если Kora оборачивает каждую технологию за уникальной абстракцией, агенту приходится учить новый слой перевода.

Если интеграция Kora остаётся тонкой, существующие знания переносятся напрямую.

Агенту нужно понять только слой композиции:

```text
Как этот объект помещается в граф Kora?
Как маппится конфигурация?
Как прикрепляется жизненный цикл?
Как раскрывается готовность?
```

Это относительно стабильные концепции Kora.

Специфичная для технологии работа остаётся специфичной для технологии.

Это мощное свойство масштабирования и для людей, и для машин.

---

## Нативная библиотека остаётся запасным люком { #native-library-escape-hatch }

Каждая абстракция в итоге протекает.

Стартер может поддерживать 95% библиотеки и упускать ровно ту продвинутую функцию, которая нужна проекту.

С толстой абстракцией разработчики сталкиваются с несколькими вариантами:

```text
ждать поддержки фреймворка
форкнуть интеграцию
пробираться сквозь абстракцию
перереализовать функцию
```

С тонкой интеграцией запасной люк уже присутствует:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Connection nats
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val nats: Connection
    ```

или:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ElasticsearchClient client
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val client: ElasticsearchClient
    ```

или:

===! ":fontawesome-brands-java: `Java`"

    ```java
    MinioClient client
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val client: MinioClient
    ```

Нативный объект — часть графа.

Продвинутые функции остаются доступными.

Это снижает зависимость от экосистемы.

---

## Внутренние платформы выигрывают ещё больше { #internal-platforms }

Аргумент не ограничен публичными библиотеками с открытым исходным кодом.

У крупных компаний часто есть внутренняя инфраструктура:

- проприетарные RPC-клиенты;
- клиенты авторизации;
- сервисы конфигурации;
- системы фича-флагов;
- внутренние объектные хранилища;
- системы аудита;
- внутренние шины событий;
- SDK наблюдаемости компании;
- движки политик;
- клиенты секретов.

Ни одна публичная экосистема фреймворка не может поставлять официальные интеграции для этого.

Каждой организации в итоге приходится расширять фреймворк.

Внутренняя интеграционная библиотека Kora может выглядеть так:

```text
company-kora/
├── auth/
│   └── CompanyAuthModule
├── audit/
│   └── AuditModule
├── featureflags/
│   └── FeatureFlagsModule
├── messaging/
│   └── CompanyBusModule
└── telemetry/
    └── CompanyTelemetryModule
```

Каждый модуль может раскрывать обычные компоненты через ту же модель графа.

Это превращает расширяемость фреймворка в платформенную инженерию.

Компании не нужно модифицировать саму Kora.

---

## Переиспользуемые интеграции могут развиваться постепенно { #integrations-evolve-gradually }

Распространённая ошибка — относиться к новой интеграции как к публичному проекту фреймворка с самого начала.

Лучший путь инкрементален.

### Стадия 1: локальная фабрика приложения { #stage-1-local-factory }

===! ":fontawesome-brands-java: `Java`"

    ```java
    default Client client(Config config) {
        return new Client(...);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun client(config: Config): Client {
        return Client(...)
    }
    ```

### Стадия 2: локальная типизированная конфигурация { #stage-2-typed-config }

```text
ClientConfig
Фабрика клиента
```

### Стадия 3: жизненный цикл { #stage-3-lifecycle }

```text
запуск
завершение
```

### Стадия 4: операционная интеграция { #stage-4-operational }

```text
готовность
метрики
трассировка
логирование
```

### Стадия 5: переиспользуемый внутренний модуль { #stage-5-reusable-module }

Переместите код в общую библиотеку.

### Стадия 6: расширение этапа компиляции { #stage-6-compile-time }

Только если интеграция выигрывает от генерации кода или синтеза обобщённых типов.

Эта последовательность избегает преждевременной фреймворк-инженерии.

Интеграция растёт только тогда, когда переиспользование её оправдывает.

---

## У Kora есть более глубокий механизм расширения, когда он нужен { #deeper-extension-mechanism }

До сих пор мы намеренно избегали механизма расширения компилятора Kora.

Это правильный выбор по умолчанию для обычной интеграции SDK.

Но некоторые интеграции действительно выигрывают от генерации на этапе компиляции.

Представьте кастомный декларативный клиент:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @MyRpcClient
    public interface BillingClient {
        Invoice getInvoice(String id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @MyRpcClient
    interface BillingClient {
        fun getInvoice(id: String): Invoice
    }
    ```

Если организация хочет, чтобы Kora синтезировала реализацию всякий раз, когда запрашивается `BillingClient`, расширение компилятора может участвовать в разрешении зависимостей и генерировать эту
реализацию.

Kora использует такой механизм внутри для таких вещей, как:

- JSON-читатели и писатели;
- репозитории;
- декларативные HTTP-клиенты;
- gRPC-стабы;
- мапперы конфигурации;
- валидаторы;
- интеграции маппинга.

Это даёт фреймворку два слоя расширяемости:

```text
обычная интеграция
      ↓
@Module + компоненты

продвинутая сгенерированная интеграция
      ↓
расширение этапа компиляции
```

Это разделение здорово.

Большинство команд могут оставаться на первом слое.

Авторы фреймворков и платформенные команды могут использовать второй, когда синтез на этапе компиляции даёт достаточную ценность.

---

## Явные внешние модули предотвращают сюрпризы classpath { #explicit-external-modules }

Одна тонкая, но важная особенность дизайна модулей Kora в том, что внешние модули не активируются автоматически просто потому, что зависимость присутствует.

Их нужно подключить к приложению.

Это снижает распространённую форму неопределённости фреймворка:

```text
Почему добавление этой зависимости изменило поведение запуска?
Какая авто-конфигурация стала активной?
Какое условие совпало?
Какой компонент по умолчанию был зарегистрирован?
```

Явная модель Kora больше похожа на:

```text
Application
   extends
   NatsModule
   HttpServerModule
   JsonModule
```

или эквивалентную композицию через подмодули.

Сборка приложения становится архитектурной документацией.

Для кастомных интеграций это ценно, потому что принятие контролируется исходным кодом, а не побочными эффектами classpath.

---

## Модули масштабируются в многомодульные приложения { #multi-module-applications }

Переиспользуемой интеграции не обязательно жить рядом с конечным приложением.

Kora поддерживает композицию подмодулей для многопроектных сборок.

Это значит, что доменный модуль может владеть и своими компонентами, и инфраструктурными интеграциями, которые ему требуются.

Например:

```text
модуль заказов
├── OrdersService
├── OrdersRepository
├── OrdersEvents
└── OrdersInfrastructure
       ├── JDBC
       └── NATS
```

Затем модуль приложения компонует доменные подмодули.

Концептуально:

```text
Application
├── OrdersModule
├── BillingModule
├── CatalogModule
└── NotificationsModule
```

Это релевантно для дизайна экосистемы, потому что интеграции можно упаковывать с той же гранулярностью, что и архитектуру.

Не каждой технологии нужно становиться глобальной функцией фреймворка.

Интеграция может принадлежать домену, которому она нужна.

---

## Два соединения не требуют нового фреймворка { #two-connections }

Предположим, приложению нужны два кластера NATS.

Толстой интеграции может понадобиться кастомная поддержка нескольких клиентов.

В графе Kora уже есть теги для различения компонентов одного типа.

Концептуально:

```text
@Tag(MainNats)
Connection

@Tag(AuditNats)
Connection
```

Фабрики могут маппить каждое соединение на другой раздел конфигурации.

Тот же паттерн модуля работает для:

```text
основная база данных / реплика базы данных
внутренний / внешний HTTP-клиент
основное / архивное объектное хранилище
региональные SDK-клиенты
```

Это иллюстрирует ещё одно полезное свойство: общие возможности DI решают многие требования интеграции до того, как понадобится специализированная абстракция фреймворка.

---

## Фабричный модуль может параметризовать переиспользуемую инфраструктуру { #parameterized-factory-module }

Kora 2 также поддерживает параметризованные фабричные модули.

Это полезно, когда одна переиспользуемая интеграция должна инстанцироваться несколько раз с разными путями конфигурации или тегами.

Концептуально:

```text
NatsFactoryModule("nats.main")
NatsFactoryModule("nats.audit")
```

Каждый производит отдельный набор компонентов.

Это более масштабируемый паттерн, чем дублирование кода интеграции.

Он также показывает, что модель модулей Kora — не просто список синглтон-фабрик; она может выражать переиспользуемые инфраструктурные шаблоны, оставаясь типо-управляемой и явной.

---

## Тестирование кастомной интеграции прямолинейно { #testing-custom-integration }

Хорошая модель расширения также должна быть тестируемой.

Поскольку кастомная интеграция — просто часть графа приложения, модель компонентного тестирования Kora может запрашивать релевантный срез графа.

Тест может запрашивать:

```text
NatsPublisher
NatsReadinessProbe
```

и заменять `Connection` тестовым компонентом.

Концептуально:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class NatsPublisherTest {

        @TestComponent
        NatsPublisher publisher;

        // предоставить заменяющее соединение
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class NatsPublisherTest {

        @TestComponent
        lateinit var publisher: NatsPublisher

        // предоставить заменяющее соединение
    }
    ```

Важное свойство в том, что тестирование не требует запуска всего приложения только потому, что интеграция живёт в графе DI.

Граф можно нарезать до требуемых компонентов и зависимостей.

Для интеграционных тестов можно использовать реальный NATS-контейнер, а готовность может стать контрактом синхронизации.

Это даёт кастомной интеграции ту же модель тестирования, что и встроенным компонентам.

---

## Кастомные интеграции должны быть скучными { #custom-integrations-boring }

Это, пожалуй, самый сильный критерий дизайна.

Хорошая интеграция Kora должна быть скучной для чтения.

Что-то вроде:

```text
Config
↓
Builder
↓
Client
↓
Lifecycle
↓
Telemetry
↓
Probe
```

Если интеграция обычного Java SDK требует:

```text
кастомного сканера classpath
кастомного реестра отражения
фабрики прокси рантайма
кастомного дескриптора плагина
хука начальной загрузки фреймворка
кастомного процессора аннотаций
динамического кеша метаданных
специализированного объекта контекста
```

что-то, вероятно, пошло не так.

Сложность может быть оправдана для мощных декларативных функций, но она не должна быть платой за вход.

Архитектура Kora держит эту плату за вход низкой.

---

## Количество экосистемы может скрывать качество интеграций { #ecosystem-count-hides-quality }

Представьте фреймворк, рекламирующий поддержку 300 технологий.

Это число ничего не говорит о том, является ли каждая интеграция:

- актуальной;
- хорошо поддерживаемой;
- прозрачной;
- настраиваемой;
- совместимой с последним нативным клиентом;
- наблюдаемой;
- эффективной;
- лёгкой в отладке;
- лёгкой в замене.

Интеграция может существовать и всё же становиться обязательством.

Например, адаптер фреймворка может отставать на две крупные версии от SDK вендора. Документация вендора может описывать API, недоступные через обёртку. Продвинутые опции могут не раскрываться. Баги
могут требовать ожидания мейнтейнера адаптера.

Тонкая интеграция снижает эту поверхность зависимости.

Приложение часто может обновлять нативную библиотеку напрямую, потому что сторона Kora состоит из маленького маппинга конструктора или билдера.

Это делает владение интеграцией дешевле.

---

## Маленькое сообщество всё же может быстро производить полезные расширения { #small-community-extensions }

У фреймворка с меньшим сообществом естественно будет меньше готовых модулей, чем у Spring.

Это реальный недостаток, когда отсутствующая интеграция сложна.

Но серьёзность недостатка зависит от того, насколько трудно создавать модули сообщества.

Если интеграция может начинаться как:

```text
один интерфейс конфигурации
один модуль
одна проба
один адаптер телеметрии
```

то маленькое сообщество всё же может быстро покрывать отсутствующие технологии.

Вклад не требует глубоких знаний скрытых внутренностей контейнера.

Его можно рецензировать, читая обычный код.

Это снижает барьер и для внутренних расширений компании, и для расширений с открытым исходным кодом.

---

## Бремя документации тоже становится меньше { #documentation-burden }

Большие экосистемы интеграций создают проблему масштабирования документации.

Каждой обёртке нужна документация для:

- конфигурации;
- жизненного цикла;
- функций;
- примеров;
- обработки ошибок;
- совместимости версий;
- ограничений;
- продвинутых опций.

Если интеграция сохраняет нативную библиотеку, документация фреймворка может сосредоточиться на границе композиции.

Например:

```text
Как поместить NATS Connection в граф
Как его настроить
Как работает жизненный цикл
Как подключается телеметрия
Как работает готовность
```

Всё остальное может концептуально указывать обратно на официальный NATS API.

Это избегает дублирования целого руководства вендора.

Опять же, тонкие абстракции сохраняют нативную экосистему.

---

## Вот почему JDBC — такая мощная модель { #jdbc-powerful-model }

JDBC остаётся одним из лучших примеров рычага экосистемы.

Фреймворк может предоставлять:

- жизненный цикл источника данных;
- генерацию репозиториев;
- транзакции;
- телеметрию;
- маппинг;

в то время как разработчики приложения всё равно понимают, что базовая технология — JDBC.

Знания о SQL, драйверах, пулах соединений и семантике баз данных переносятся.

Более широкая философия интеграции Kora следует этому паттерну: добавлять ценность фреймворка вокруг технологии, не притворяясь, что технология исчезла.

Тот же принцип можно применять к новым SDK.

---

## Когда толстая абстракция оправдана { #thick-abstraction-justified }

Тонкие абстракции не всегда достаточны.

Иногда фреймворк может дать большую ценность, вводя более сильную абстракцию.

Примеры включают:

- сгенерированные интерфейсы репозиториев;
- декларативные HTTP-клиенты;
- сгенерированные эндпоинты OpenAPI;
- аннотации кеша;
- аннотации отказоустойчивости;
- валидацию;
- межтехнологические контракты телеметрии.

Эти абстракции могут удалять значительный объём повторяющегося кода.

Важный вопрос в том, сжимает ли абстракция реальную сложность.

Полезная абстракция фреймворка должна удовлетворять примерно такому:

```text
удалённая сложность
>
новые специфичные для фреймворка знания
```

Если да, абстракция заслуживает своё место.

Если нет, раскрытие нативной библиотеки часто лучше.

---

## NATS не должен становиться «Kora NATS» { #nats-not-kora-nats }

Вернёмся к нашему примеру.

Что добавила Kora?

```text
типизированную конфигурацию
построение графа
жизненный цикл
композицию телеметрии
готовность
тестируемость
```

Что остаётся NATS?

```text
Connection
Options
publish
subscribe
request/reply
JetStream
поведение переподключения
семантику протокола
subjects
сообщения
```

Это разделение здорово.

Оно даёт нам производственную интеграцию без потери нативной технологии.

Именно поэтому интеграция NATS, ClickHouse, Elasticsearch, MinIO или нового SDK не требует написания «фреймворка внутри фреймворка».

---

## Поверхность интеграции можно визуализировать как тонкий слой { #integration-surface-thin-layer }

Толстый адаптер фреймворка часто выглядит так:

```text
Application
    ↓
DSL фреймворка
    ↓
Доменная абстракция фреймворка
    ↓
Адаптер фреймворка
    ↓
Нативная Java-библиотека
    ↓
Технология
```

Тонкая интеграция в стиле Kora может выглядеть так:

```text
Application
    ↓
Нативный Java API
    ↓
Технология

с боковым слоем для:

Config ─┐
DI ─────┤
Life ───┤──→ нативный клиент
OTel ───┤
Probe ──┘
```

Фреймворк участвует там, где этого требует жизненный цикл приложения.

Ему не нужно владеть концептуальной моделью технологии.

---

## Стоимость расширения — лучшая долгосрочная метрика { #extension-cost-metric }

Технологические портфели меняются непрерывно.

Сегодня команда использует Kafka.

Завтра другая рабочая нагрузка использует NATS.

Один сервис добавляет ClickHouse.

Другой принимает векторную базу данных.

Вендор вводит новый платёжный SDK.

Облачный провайдер выпускает новый управляемый API.

Ни один фреймворк не может предсказать всё это.

Поэтому полнота экосистемы временна.

Стоимость расширения структурна.

Фреймворк может со временем добавлять больше официальных модулей, но более долговечное свойство — можно ли подключать неизвестные будущие технологии без борьбы с фреймворком.

Вот почему стоимость расширения заслуживает быть первоклассным критерием оценки.

---

## Практический чек-лист интеграции для Kora { #integration-checklist }

Добавляя неподдерживаемую библиотеку, команда может задать небольшой набор вопросов.

## 1. Что за нативный объект мы на самом деле хотим внедрить? { #checklist-native-object }

Примеры:

```text
Connection
Client
DataSource
Transport
SDK
Manager
```

Предпочитайте раскрывать нативный объект, если обёртка не добавляет явной ценности.

## 2. Какая конфигурация действительно нужна этому сервису? { #checklist-configuration }

Создайте типизированный контракт конфигурации.

Не зеркалируйте всю нативную библиотеку вслепую.

## 3. Владеет ли объект ресурсами? { #checklist-resources }

Если да, интегрируйте его с жизненным циклом или `AutoCloseable`.

## 4. Что означает готовность? { #checklist-readiness }

Добавляйте пробу, только если внешняя зависимость действительно влияет на способность экземпляра обслуживать рабочую нагрузку.

## 5. Какой телеметрии не хватает? { #checklist-telemetry }

Переиспользуйте нативную телеметрию, когда возможно. Добавляйте маленькую обёртку там, где необходимо.

## 6. Нужны ли интеграции сквозные политики? { #checklist-policies }

Используйте отказоустойчивость или AOP только там, где приложение действительно в них нуждается.

## 7. Нужно ли нам больше одного экземпляра? { #checklist-multiple-instances }

Используйте теги или параметризованный фабричный модуль.

## 8. Должно ли это стать переиспользуемым? { #checklist-reusable }

Начните локально. Извлеките общий модуль, когда нескольким сервисам нужна одна и та же интеграция.

## 9. Требует ли это генерации кода? { #checklist-code-generation }

Если нет, остановитесь на обычных модулях и компонентах.

Этот чек-лист покрывает удивительный объём работы по инфраструктурной интеграции.

---

## Что эта модель не решает { #model-does-not-solve }

Эта архитектура не магия.

Некоторые интеграции действительно трудны.

Интеграция Kafka — не просто конструктор клиента, потому что жизненный цикл потребителя, назначение партиций, повторы, фиксация смещений, противодавление, телеметрия и семантика завершения
значительны.

Интеграция базы данных может требовать транзакций, пулинга, телеметрии запросов, генерации репозиториев и маппинга.

Движок рабочих процессов может требовать регистрации воркеров, управления состоянием и сложной координации рантайма.

Для этих технологий официальный модуль фреймворка может сэкономить много работы.

Аргумент не в том, что экосистемы не важны.

Аргумент в том, что *только размер* экосистемы — слабый предиктор того, насколько болезненными будут отсутствующие интеграции.

Фреймворк, который легко расширять, снижает штраф за пробелы.

---

## Официальные интеграции всё ещё важны { #official-integrations }

Есть несколько причин предпочесть официальный модуль Kora, когда он существует.

Во-первых, он уже интегрирован с конвенциями телеметрии Kora.

Во-вторых, поведение жизненного цикла и готовности уже спроектировано.

В-третьих, конвенции конфигурации согласованы с другими модулями.

В-четвёртых, модуль тестируется против релизов фреймворка.

В-пятых, генерация кода может давать возможности, которые простая фабрика не может.

В-шестых, настройка производительности может быть уже сделана.

Поэтому дерево решений не такое:

```text
Никогда не используйте интеграции фреймворка.
```

А такое:

```text
Официальная интеграция существует и подходит?
        ↓ да
Используйте её.

        ↓ нет
Может ли нативная Java-библиотека + маленький модуль решить это?
        ↓ да
Постройте тонкую интеграцию.

        ↓ нет
Создайте более глубокое переиспользуемое расширение.
```

Это здоровая стратегия экосистемы.

---

## Философия Kora делает это намеренным { #kora-philosophy }

Главная страница Kora 2 явно заявляет, что фреймворк не стремится к широте ради самой широты и не оборачивает каждую возможную технологию за специфичной для фреймворка абстракцией. Она также
подчёркивает, что приложения могут использовать только нужные модули, заменять или настраивать компоненты и добавлять модули через ту же явную модель приложения.

Эта философия важна, потому что расширяемость легче, когда сам фреймворк следует тем же правилам, что ожидаются от пользовательского кода.

Если внутренности фреймворка опираются на скрытые привилегированные механизмы расширения, в то время как приложения получают только упрощённую публичную поверхность, воспроизведение интеграций
качества фреймворка становится трудным.

Kora раскрывает достаточно своей модели композиции, чтобы команды приложений и платформ могли строить интеграции на том же архитектурном языке:

```text
модуль
компонент
конфигурация
жизненный цикл
телеметрия
проба
граф
```

Эта симметрия снижает кривую обучения.

---

## Экосистема — не только то, что поставляется в коробке { #ecosystem-not-only-box }

Это даёт нам более широкое определение.

Экосистема фреймворка состоит как минимум из трёх слоёв.

### Слой 1: встроенные модули фреймворка { #layer-1-built-in-modules }

```text
HTTP
JDBC
Kafka
gRPC
S3
отказоустойчивость
кеш
валидация
телеметрия
...
```

### Слой 2: нативная Java-экосистема { #layer-2-native-ecosystem }

```text
SDK вендоров
драйверы баз данных
клиенты обмена сообщениями
облачные SDK
библиотеки
реализации протоколов
```

### Слой 3: модули, специфичные для организации { #layer-3-organization-modules }

```text
внутренние клиенты
платформенные библиотеки
безопасность
телеметрия компании
общая инфраструктура
```

Фреймворк мощен, когда эти слои легко компонуются.

Kora не обязана дублировать Слой 2, чтобы извлечь из него выгоду.

Это более широкий смысл тонких абстракций.

---

## Самое важное свойство экосистемы может быть скоростью выхода { #escape-velocity }

Здесь есть полезная метафора.

У некоторых фреймворков большое гравитационное поле. В них легко войти, потому что на всё есть стартер, но трудно покинуть абстракции фреймворка, оказавшись внутри.

Другие фреймворки дают меньше начального покрытия, но делают границы легче пересекаемыми.

Для долгоживущих систем способность пересекать эти границы важна.

Командам нужно:

- обновлять нативные библиотеки;
- заменять клиенты;
- принимать новую инфраструктуру;
- мигрировать вендоров;
- настраивать значения по умолчанию;
- отлаживать сбои, специфичные для протокола;
- использовать продвинутые нативные функции.

Тонкая интеграция даёт приложению скорость выхода.

Оно может перемещаться между фреймворком и нативной библиотекой без большого слоя перевода.

---

## Стоимость обслуживания — где модель окупается { #maintenance-cost }

Первая версия интеграции — лишь часть стоимости.

Большая стоимость часто проявляется годами.

Предположим, NATS меняет свой API.

С толстым адаптером:

```text
NATS меняется
     ↓
мейнтейнеры адаптера обновляют обёртку
     ↓
фреймворк выпускает новый адаптер
     ↓
приложение обновляет адаптер
     ↓
приложение адаптируется к изменениям обёртки
```

С тонким модулем:

```text
NATS меняется
     ↓
приложение обновляет зависимость
     ↓
маленький маппинг фабрики меняется, если нужно
```

Разница может быть значительной.

Это особенно ценно для менее популярных интеграций, где адаптеры сообщества могут отставать от релизов вендора.

---

## 51-я интеграция — настоящий тест { #fifty-first-integration }

Качество первых 50 интеграций фреймворка говорит вам, сколько работы уже сделали его мейнтейнеры.

Трудность 51-й говорит вам, сколько работы *вам* придётся сделать, когда дорожная карта разойдётся с их.

Вот почему следующее утверждение — больше, чем риторика:

> **Фреймворк с 500 интеграциями, которые трудно понять, не обязательно более расширяем, чем фреймворк с 50 интеграциями, где 51-ю можно написать в нескольких прямолинейных классах.**

Зрелый фреймворк должен оптимизировать обе стороны.

Поставляйте полезные интеграции.

И делайте отсутствующую неожиданно простой для построения.

---

## Маленькая экосистема может быстро стать локальной экосистемой { #local-ecosystem }

Команды также должны различать размер публичной экосистемы и размер локальной экосистемы.

Компания, принимающая Kora, может создать собственный курируемый слой интеграций.

Через год её внутренняя платформа может включать:

```text
company-kora-postgres
company-kora-nats
company-kora-clickhouse
company-kora-auth
company-kora-featureflags
company-kora-object-storage
company-kora-secrets
company-kora-audit
```

Эти модули кодируют политику компании, а не общую политику фреймворка.

Это часто ценнее, чем иметь публичный стартер для каждой технологии, потому что внутренние модули могут стандартизировать:

- именование;
- теги телеметрии;
- учётные данные;
- значения таймаутов по умолчанию;
- TLS;
- политику готовности;
- безопасность;
- допущения развёртывания.

Простая модель модулей Kora делает такой платформенный слой практичным.

---

## Почему это может быть лучше общих стартеров { #better-than-generic-starters }

Общий стартер должен удовлетворять многие среды.

Поэтому он накапливает опции.

Модуль компании может быть сфокусированным.

Например:

```text
Все NATS-клиенты:
- используют TLS компании
- используют стандартные имена соединений
- экспортируют стандартные метрики
- используют одобренную политику переподключения
- по умолчанию не раскрывают зависимость готовности
```

Переиспользуемый модуль может кодировать эти выборы в обычном фабричном коде.

Это построение экосистемы, адаптированной под организацию.

---

## Внедрение зависимостей на этапе компиляции делает ошибки кастомной интеграции дешёвыми { #compile-time-di-errors }

Есть ещё одна выгода от использования кастомных модулей в Kora.

Если интеграция подключена неверно, валидация графа происходит во время компиляции.

Предположим, `NatsPublisher` требует `NatsTelemetry`, но реализации телеметрии не существует.

Граф приложения не строится.

Предположим, существуют два нетегированных компонента `Connection`.

Граф сообщает о неоднозначности.

Предположим, фабрика модуля требует маппер конфигурации, который нельзя сгенерировать.

Компилятор идентифицирует отсутствующую зависимость.

Это делает разработку кастомной интеграции менее рискованной, потому что структурные ошибки ловятся рано.

Фреймворку не требуется запуск приложения, чтобы раскрыть, связна ли интеграция внутренне.

---

## Сгенерированный код графа делает интеграцию объяснимой { #generated-graph-explainable }

При отладке кастомного модуля сгенерированный код полезен.

Вы можете изучить, как граф конструирует:

```text
NatsConfig
Options
Connection
NatsTelemetry
NatsPublisher
NatsReadinessProbe
```

Это недооценённая функция расширяемости.

Непрозрачные системы расширения рантайма делают кастомные интеграции труднее, потому что связка живёт внутри механизмов фреймворка.

Читаемый сгенерированный код графа превращает сборку приложения в нечто инспектируемое.

Это важно для людей.

Это ещё важнее для ИИ-кодинг-агентов.

---

## Расширяемость и ИИ-нативный дизайн усиливают друг друга { #ai-native-design }

ИИ-агент, которому поручено интегрировать новый SDK в Kora, может следовать относительно механическому процессу:

```text
прочитать документацию SDK
↓
определить билдер клиента
↓
определить типизированную конфигурацию
↓
создать фабрику модуля Kora
↓
прикрепить жизненный цикл
↓
добавить телеметрию/пробу, если требуется
↓
скомпилировать
↓
исправить ошибки графа
```

Скрытого состояния мало.

Агент может изучить сгенерированные исходники при необходимости.

Документация нативного SDK остаётся релевантной.

Это ещё одна причина, почему скромная официальная экосистема менее ограничивает, чем когда-то. Стоимость написания маленького клея упала, в то время как стоимость понимания непрозрачного поведения
фреймворка упала далеко не так сильно.

В среде с поддержкой ИИ проверяемость становится ценнее сырого количества интеграций.

---

## Ревью — новое бутылочное горлышко { #review-bottleneck }

По мере того как генерация кода становится дешевле — будь то процессоры аннотаций или ИИ-агенты — бутылочное горлышко смещается к ревью.

Кастомная интеграция, состоящая из шести прозрачных классов, проверяема.

Плагин фреймворка, включающий сканирование classpath, динамические условия и прокси рантайма, труднее рецензировать, даже если ИИ может его быстро произвести.

Модель расширения Kora хорошо согласуется с этим сдвигом.

Идеальная интеграция не просто легко генерируется.

Она легко проверяется.

Это значит:

```text
маленькая
типизированная
локальная
явная
нативная
тестируемая
```

Эти свойства важнее по мере ускорения производства программного обеспечения.

---

## Вам не нужен стартер для всего { #no-starter-needed }

Фраза «нет стартера» звучит пугающе, только если фреймворк делает обычное конструирование библиотек трудным.

Для многих Java-технологий стартер — в первую очередь удобный пакет вокруг:

```text
new Client(config)
```

плюс жизненный цикл и наблюдаемость.

Если фреймворк уже делает эти задачи легко компонуемыми, отсутствие стартера становится неудобством, а не блокером.

Это применимо не в равной степени к каждой технологии.

Но это применимо к гораздо большему числу технологий, чем иногда подразумевают экосистемы фреймворков.

---

## Более полезное сравнение фреймворков { #useful-framework-comparison }

Вместо сравнения экосистем только по количеству модулей оцените эту матрицу:

| Вопрос                                                | Почему это важно              |
|-------------------------------------------------------|-------------------------------|
| Сколько интеграций уже существует?                    | Немедленное покрытие          |
| Могу ли я использовать нативный Java-клиент напрямую? | Запасной люк                  |
| Сколько специфичного для фреймворка API добавляется?  | Стоимость обучения            |
| Как я привязываю конфигурацию?                        | Шаблонный код интеграции      |
| Как я управляю жизненным циклом?                      | Производственная безопасность |
| Как я добавляю готовность?                            | Операционная интеграция       |
| Как я добавляю метрики/трассировку?                   | Наблюдаемость                 |
| Могу ли я заменять значения по умолчанию?             | Кастомизация                  |
| Могу ли я иметь несколько экземпляров?                | Реальная топология            |
| Могу ли я тестировать срез графа?                     | Стоимость разработки          |
| Являются ли ошибки связки ошибками этапа компиляции?  | Качество обратной связи       |
| Могу ли я упаковать это как внутренний модуль?        | Переиспользование платформы   |
| Нужны ли мне внутренности фреймворка?                 | Барьер расширения             |

Это даёт гораздо более осмысленную картину, чем «У фреймворка A 430 стартеров, у фреймворка B — 70».

---

## Где у Kora ещё есть работа { #kora-work-to-do }

Защита Kora не должна притворяться, что размер экосистемы неважен.

Меньшая экосистема означает:

- меньше примеров copy-paste для необычных технологий;
- меньше готовых конвенций телеметрии;
- меньше проверенных сообществом адаптеров;
- меньше интеграций, поддерживаемых специалистами;
- больше случаев, когда командам приходится писать собственный клей;
- меньше ответов на Stack Overflow и записей в блогах для граничных случаев.

Для сложных технологий это реальная инженерная стоимость.

Ответ Kora — не заставить эту стоимость исчезнуть.

Её ответ — сделать клей как можно более дешёвым и предсказуемым.

Это другая стратегия.

Правильная ли это стратегия, зависит от команды.

Команда, которая хочет каждую возможную технологию предынтегрированной, может предпочесть большую экосистему.

Команда, которая ценит контроль, нативные API, ясность этапа компиляции и способность строить маленькие локальные интеграции, может найти модель Kora более привлекательной.

---

## Лучшая интеграция иногда — отсутствие интеграции { #best-integration-no-integration }

Есть финальный провокационный момент.

Иногда корректная интеграция фреймворка для Java-библиотеки — просто:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface VendorModule {

        default VendorClient vendorClient(VendorConfig config) {
            return VendorClient.builder()
                .endpoint(config.endpoint())
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface VendorModule {

        fun vendorClient(config: VendorConfig): VendorClient {
            return VendorClient.builder()
                .endpoint(config.endpoint())
                .build()
        }
    }
    ```

Этого может быть достаточно.

Если клиент потокобезопасен, не управляет необычным жизненным циклом, экспортирует собственные сигналы OpenTelemetry и не влияет на готовность, добавление большего количества кода фреймворка сделало
бы систему хуже.

Зрелость фреймворка включает знание того, когда не оборачивать.

Философия тонких абстракций Kora делает этот ответ социально приемлемым.

---

## Заключение: экосистема — это то, что вы можете безопасно добавить { #conclusion }

Экосистема фреймворка часто представляется как полка готовых деталей.

Эта полка важна. Kora выигрывает от каждой официальной интеграции, которую поставляет, и всегда будут случаи, когда зрелый встроенный модуль экономит значительные инженерные усилия.

Но полка — не вся мастерская.

Рано или поздно производственной системе нужно что-то за пределами каталога. Появляется новая база данных. Команда принимает NATS. Вендор выпускает новый SDK. Внутренняя платформа раскрывает
проприетарный клиент. У облачного сервиса нет официального модуля фреймворка. В этот момент реальное качество фреймворка раскрывается тем, что происходит дальше.

Должна ли команда понимать скрытые точки расширения рантайма?

Нужно ли ей воспроизводить сложную архитектуру стартера?

Нужно ли ей создавать специфичные для фреймворка зеркала нативного API?

Должна ли она ждать официальной поддержки?

Или она может сделать вот это?

```text
Новая библиотека
   ↓
Config
   ↓
Фабрика клиента
   ↓
Жизненный цикл
   ↓
Модуль Kora
   ↓
Телеметрия
   ↓
Пробы
   ↓
Внедрение в приложение
```

Kora намеренно спроектирована так, чтобы второй путь часто был достаточен.

Её модули — обычные единицы композиции. Конфигурация типизирована. Жизненный цикл явный. Готовность и живость — обычные контракты компонентов. Телеметрия может наслаиваться вокруг нативных операций.
Компоненты фреймворка по умолчанию можно заменять. Теги и фабричные модули обрабатывают несколько экземпляров. Валидация графа на этапе компиляции ловит структурные ошибки рано. Сгенерированный код
остаётся инспектируемым. А когда обычных фабрик больше недостаточно, фреймворк также раскрывает более глубокий механизм расширения этапа компиляции для интеграций, которые действительно выигрывают от
сгенерированных реализаций.

Самое главное, тонкие абстракции сохраняют экосистему базовой технологии.

Разработчик, знающий JDBC, по-прежнему знает JDBC.

Разработчик, знающий Kafka, по-прежнему понимает Kafka.

Разработчик, добавляющий NATS, может продолжать читать документацию NATS.

Команда, принимающая Elasticsearch, ClickHouse, MinIO или новый облачный SDK, не обязательно должна ждать, пока эти технологии будут переведены в новый диалект фреймворка.

Это меняет значение размера экосистемы.

Релевантное сравнение больше не только:

```text
Сколько интеграций поставляется сегодня?
```

Оно становится:

```text
Насколько дорога завтрашняя отсутствующая интеграция?
```

И это ведёт к более долговечному принципу:

> **Настоящий вопрос не в том, сколько интеграций фреймворк уже поставляет, а в том, насколько дорого добавить ту, которая вам действительно нужна.**

Фреймворк с сотнями интеграций может быть ценен, потому что кто-то уже сделал работу.

Но расширяемость — нечто другое.

> **Фреймворк с 500 интеграциями, которые трудно понять, не обязательно более расширяем, чем фреймворк с 50 интеграциями, где 51-ю можно написать в нескольких прямолинейных классах.**

Поэтому меньшую экосистему Kora следует оценивать вместе с архитектурой, которая её окружает. Фреймворку не нужно предсказывать каждую технологию, которую команда когда-либо будет использовать, если
неизвестные технологии могут входить в приложение через маленькую, типизированную и прозрачную границу.

Это экосистема, которую Kora на самом деле предлагает.

Не только интеграции, поставляемые в коробке.

Экосистема, которую вы можете построить.
