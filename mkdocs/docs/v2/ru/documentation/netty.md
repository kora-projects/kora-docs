---
description: "Explains the shared Kora Netty transport: event loop groups, transport selection between NIO, EPOLL, KQUEUE and io_uring, channel factory and thread factories. Use when working with NettyModule, NettyTransportConfig, NettyChannelFactory, NettyEventLoopFactory, EventLoopGroup."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the shared Netty transport and event loop configuration in Kora; key triggers include NettyModule, NettyTransportConfig, NettyChannelFactory, NettyEventLoopFactory, EventLoopGroup, EventLoopWorker, EventLoopBoss, netty config section, Epoll, KQueue, io_uring, NIO."
---

Netty — это библиотека сетевого взаимодействия, построенная вокруг неблокирующего ввода-вывода и модели `event loop`.
В Kora она используется как низкоуровневый сетевой `транспорт` для модулей, которым требуется эффективно обрабатывать соединения и сетевые события.

Модуль не предоставляет собственного пользовательского `программного интерфейса`.
Он существует для того, чтобы все части приложения, работающие поверх Netty, использовали один `event loop` и одно решение о `транспорте`,
а не поднимали каждый свои потоки ввода-вывода.
Поверх него построен драйвер [кэша Redis](cache.md#redis), и собственный `транспорт` Netty внутри сервиса можно построить на тех же самых компонентах.

Эти настройки полезны, когда приложению требуется управлять сетевым `транспортом`, количеством потоков ввода-вывода
или выбором `платформенного транспорта`.
Значения по умолчанию подходят большинству сервисов, но их можно задать явно при высокой сетевой нагрузке или особых требованиях окружения.

Модуль настраивает [`транспорт Netty` и `цикл событий Netty`](https://netty.io/4.2/api/io/netty/channel/EventLoop.html) в рамках Kora.

## Подключение { #connection }

Обычно модуль не требуется подключать вручную: модули Kora, которым нужен Netty, сами наследуют `NettyModule`
и приносят его как транзитивную зависимость.
Модуль [кэша Redis](cache.md#redis) — как раз такой случай: `LettuceRedisCacheModule` наследует `LettuceModule`,
а `LettuceModule` наследует `NettyModule`.

Подключать модуль явно нужно только тогда, когда внутри сервиса строится собственный `транспорт` Netty,
который должен разделять `event loop` со всем остальным приложением:

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:netty-common"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends NettyModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:netty-common")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : NettyModule
    ```

## Что предоставляется { #what-it-provides }

`NettyModule` добавляет в контейнер зависимостей следующие общие компоненты:

- **`NettyTransportConfig`** — конфигурация, привязанная к секции `netty`: предпочитаемый [транспорт](#transport) и [количество потоков](#configuration) групп `event loop`.
- **Рабочая `EventLoopGroup`** с тегом `@Tag(NettyModule.EventLoopWorker.class)` — общий `event loop`, который обрабатывает установленные соединения и сетевой ввод-вывод. На нем работают клиенты поверх Netty.
- **`EventLoopGroup` приема соединений (boss)** с тегом `@Tag(NettyModule.EventLoopBoss.class)` — отдельный `event loop`, предназначенный для серверных `bootstrap`, принимающих входящие соединения, чтобы прием соединения не задерживался вводом-выводом по уже установленным.
- **[`NettyEventLoopFactory`](#event-loop-factory)** с теми же двумя тегами — фабрики, из которых собираются группы выше.
- **[`NettyChannelFactory`](#channel-factory)** — фабрика, создающая каналы Netty, соответствующие выбранному [транспорту](#transport).

Обе группы собираются из одного и того же выбора [транспорта](#transport) и имеют одинаковый размер, заданный параметром `threads`,
поэтому рабочие и boss-потоки всегда одного вида.

Обе группы `event loop` управляются [жизненным циклом](container.md#component-lifecycle) Kora:
они корректно останавливаются после освобождения всех зависящих от них компонентов, поэтому ручное управление не требуется.

Фабрики `event loop`, обе группы и `NettyChannelFactory` зарегистрированы как [компоненты по умолчанию](container.md#default-factory),
поэтому любой из них можно заменить, объявив компонент того же типа с тем же [тегом](container.md#tags).

Компоненты, которые строят собственный `транспорт` Netty, внедряют эти компоненты напрямую:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyNettyTransport {

        private final Bootstrap bootstrap;

        public MyNettyTransport(@Tag(NettyModule.EventLoopWorker.class) EventLoopGroup workerGroup,
                                NettyChannelFactory channelFactory) {
            this.bootstrap = new Bootstrap()
                .group(workerGroup)
                .channelFactory(channelFactory.build());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyNettyTransport(
        @Tag(NettyModule.EventLoopWorker::class) workerGroup: EventLoopGroup,
        channelFactory: NettyChannelFactory,
    ) {

        private val bootstrap: Bootstrap = Bootstrap()
            .group(workerGroup)
            .channelFactory(channelFactory.build())
    }
    ```

## Конфигурация { #configuration }

Пример конфигурации, описанной в интерфейсе `NettyTransportConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    netty {
        transport = "NIO" //(1)!
        threads = 2 //(2)!
    }
    ```

    1. Предпочитаемый [транспорт](https://netty.io/wiki/native-transports.html): `NIO`, `EPOLL`, `KQUEUE` или `URING` (необязательный, если не указан, [транспорт выбирается автоматически](#transport)).
    2. Количество потоков в каждой группе `event loop` (по умолчанию: количество процессоров, доступных Netty, умноженное на `2`). Рабочая и boss-группы имеют одинаковый размер, заданный этим значением.

=== ":simple-yaml: `YAML`"

    ```yaml
    netty:
      transport: "NIO" #(1)!
      threads: 2 #(2)!
    ```

    1. Предпочитаемый [транспорт](https://netty.io/wiki/native-transports.html): `NIO`, `EPOLL`, `KQUEUE` или `URING` (необязательный, если не указан, [транспорт выбирается автоматически](#transport)).
    2. Количество потоков в каждой группе `event loop` (по умолчанию: количество процессоров, доступных Netty, умноженное на `2`). Рабочая и boss-группы имеют одинаковый размер, заданный этим значением.

Количество потоков по умолчанию берется из `NettyRuntime.availableProcessors()` самой Netty: она опирается на
`Runtime.availableProcessors()`, но это значение можно переопределить системным свойством `io.netty.availableProcessors`.
Задавайте это свойство или `threads` явно, если лимит процессоров контейнера не совпадает с тем, что видит JVM.

Корневая секция `netty` относится только к этому модулю.
Драйверы со встроенным стеком Netty настраивают его в своей собственной секции:
например, у драйвера [Cassandra](database-cassandra.md) есть вложенная секция `cassandra.advanced.netty`,
которая настраивает собственные группы `event loop` драйвера и не имеет отношения к общему `транспорту`, описанному здесь.

## Транспорт { #transport }

Параметр `transport` задает предпочитаемый `транспорт` Netty:

- `NIO` - стандартный `транспорт` Java NIO, доступен всегда.
- `EPOLL` - `платформенный транспорт` Linux.
- `KQUEUE` - `платформенный транспорт` macOS / BSD.
- `URING` - `платформенный транспорт` Linux `io_uring`.

Если параметр `transport` не задан, Kora выбирает первый доступный во время выполнения `транспорт` в порядке:

1. `URING`
2. `EPOLL`
3. `KQUEUE`
4. `NIO`

Доступность `платформенного транспорта` означает сразу две вещи: его классы присутствуют в `пути классов`
и Netty сообщает, что платформа поддерживается.
Если указанный `платформенный транспорт` не проходит любую из этих проверок, Kora переходит к тому же порядку выбора, а не падает при старте.
`NIO` — единственное значение, которое всегда применяется ровно так, как указано, потому что у него нет проверки доступности.

Обратите внимание, что автоматический порядок предпочитает `io_uring` перед `epoll`:
добавление `платформенного транспорта` `io_uring` в `путь классов времени выполнения` Linux-сервиса меняет выбранный `транспорт`,
даже если в конфигурации ничего не менялось.
Задавайте `transport` явно, если выбор должен быть одинаковым во всех окружениях.

Один и тот же выбор применяется к обеим группам `event loop` и к [фабрике каналов](#channel-factory),
поэтому каналы и `event loop`, на котором они регистрируются, всегда относятся к одному `транспорту`.

## Платформенный транспорт { #native-transport }

Модуль компилируется с классами `платформенного транспорта`, но не приносит их во время выполнения,
поэтому для использования `EPOLL`, `KQUEUE` или `URING` соответствующая зависимость Netty должна присутствовать в `пути классов времени выполнения`:

| Транспорт | Артефакт                                                                                                              | Платформа     | Классификаторы                                    |
|-----------|-----------------------------------------------------------------------------------------------------------------------|---------------|---------------------------------------------------|
| `EPOLL`   | [`io.netty:netty-transport-native-epoll`](https://mvnrepository.com/artifact/io.netty/netty-transport-native-epoll)      | Linux         | `linux-x86_64`, `linux-aarch_64`, `linux-riscv64` |
| `KQUEUE`  | [`io.netty:netty-transport-native-kqueue`](https://mvnrepository.com/artifact/io.netty/netty-transport-native-kqueue)    | macOS / BSD   | `osx-x86_64`, `osx-aarch_64`                      |
| `URING`   | [`io.netty:netty-transport-native-io_uring`](https://mvnrepository.com/artifact/io.netty/netty-transport-native-io_uring) | Linux         | `linux-x86_64`, `linux-aarch_64`, `linux-riscv64` |

`Классификатор` должен соответствовать целевой платформе, а версия — остальным артефактам `io.netty` в `пути классов`.
Kora 2.0 приносит Netty `4.2.17.Final`:

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    runtimeOnly "io.netty:netty-transport-native-epoll:4.2.17.Final:linux-x86_64"
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    runtimeOnly("io.netty:netty-transport-native-epoll:4.2.17.Final:linux-x86_64")
    ```

Платформенный артефакт транзитивно приносит соответствующий артефакт `netty-transport-classes-*`, объявлять его отдельно не требуется.
Сервис, собираемый под несколько платформ, объявляет по одному платформенному артефакту на платформу: они сосуществуют в `пути классов`,
а проверка доступности выбирает тот, который реально работает.

???+ tip "Совет"

    Обычно достаточно не задавать `transport` явно и оставить автоматический выбор.
    `Платформенный транспорт` стоит подключать осознанно: например, если он нужен для производительности или для возможностей Netty, недоступных в `NIO`.

Для [нативного образа GraalVM](graalvm-native.md) модуль поставляет метаданные, которые инициализируют классы `io.netty` во время выполнения,
что и требуется платформенным транспортам.

## Фабрика каналов { #channel-factory }

`NettyChannelFactory` — это общий внедряемый компонент, который создает экземпляры [`ChannelFactory`](https://netty.io/4.2/api/io/netty/channel/ChannelFactory.html) Netty, соответствующие выбранному [транспорту](#transport).
Это точка внедрения для компонентов, которые строят собственный клиентский или серверный `bootstrap` Netty и хотят получать каналы, согласованные с выбранным `транспортом`:

- `build()` / `build(boolean domainSocket)` — `ChannelFactory<Channel>` для клиентских каналов.
- `buildServer()` / `buildServer(boolean domainSocket)` — `ChannelFactory<ServerChannel>` для серверных каналов.

Перегрузки без аргументов делегируют вызов перегрузкам с `boolean` при `domainSocket = false` и создают стандартные сокет-каналы `TCP`.
Передача `domainSocket = true` запрашивает канал [Unix domain socket](https://en.wikipedia.org/wiki/Unix_domain_socket):
каждый `транспорт`, включая `NIO`, предоставляет реализацию как клиентского, так и серверного канала домен-сокета.

## Фабрика event loop { #event-loop-factory }

`NettyEventLoopFactory` — фабрика с единственным методом, который собирает `EventLoopGroup` для выбранного [транспорта](#transport)
с заданным [количеством потоков](#configuration).
Kora регистрирует две такие фабрики с тегами `@Tag(NettyModule.EventLoopWorker.class)` и `@Tag(NettyModule.EventLoopBoss.class)`
и собирает из них две общие группы.

Внедряйте фабрику вместо группы, когда компоненту нужна изолированная `EventLoopGroup`, а не общая —
например, когда его ввод-вывод не должен конкурировать с остальным приложением:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyIsolatedTransport implements Lifecycle {

        private final EventLoopGroup eventLoopGroup;

        public MyIsolatedTransport(@Tag(NettyModule.EventLoopWorker.class) NettyEventLoopFactory factory) {
            this.eventLoopGroup = factory.build();
        }

        @Override
        public void init() { }

        @Override
        public void release() throws Exception {
            eventLoopGroup.shutdownGracefully().get();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyIsolatedTransport(
        @Tag(NettyModule.EventLoopWorker::class) factory: NettyEventLoopFactory,
    ) : Lifecycle {

        private val eventLoopGroup: EventLoopGroup = factory.build()

        override fun init() { }

        override fun release() {
            eventLoopGroup.shutdownGracefully().get()
        }
    }
    ```

Созданная так группа не управляется контейнером, поэтому за ее остановку отвечает создавший ее компонент —
как в примере выше, через [жизненный цикл компонента](container.md#component-lifecycle).

## Фабрика потоков { #thread-factory }

Каждая группа `event loop` собирается с [`ThreadFactory`](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadFactory.html).
По умолчанию Kora использует [`DefaultThreadFactory`](https://netty.io/4.2/api/io/netty/util/concurrent/DefaultThreadFactory.html) из Netty,
которая создает потоки-демоны с именами на основе `netty-kora-worker` для рабочей группы и `netty-kora-boss` для boss-группы.

Чтобы настроить именование или приоритет потоков, предоставьте компонент `ThreadFactory` с [тегом](container.md#tags) той группы, к которой он относится.
Теги разные, поэтому рабочие и boss-потоки настраиваются независимо,
а если предоставить только один из них, второй останется на значении по умолчанию:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends LettuceRedisCacheModule {

        @Tag(NettyModule.EventLoopWorker.class)
        default ThreadFactory nettyWorkerThreadFactory() {
            return new DefaultThreadFactory("netty-worker", true);
        }

        @Tag(NettyModule.EventLoopBoss.class)
        default ThreadFactory nettyBossThreadFactory() {
            return new DefaultThreadFactory("netty-boss", true);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : LettuceRedisCacheModule {

        @Tag(NettyModule.EventLoopWorker::class)
        fun nettyWorkerThreadFactory(): ThreadFactory = DefaultThreadFactory("netty-worker", true)

        @Tag(NettyModule.EventLoopBoss::class)
        fun nettyBossThreadFactory(): ThreadFactory = DefaultThreadFactory("netty-boss", true)
    }
    ```

Собственные фабрики потоков Kora намеренно создают потоки-демоны: группы `event loop` освобождаются контейнером,
и потоки-демоны не должны удерживать JVM живой, если путь остановки был пропущен.
Пользовательской `ThreadFactory` стоит сохранить это свойство.
