---
description: "Explains Kora Netty customization and transport configuration used by HTTP Async clients, gRPC clients and gRPC servers. Use when working with NettyModule, EventLoopGroup, NettyTransport, Epoll, KQueue, NIO."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Netty customization and transport configuration used by HTTP Async clients, gRPC clients and gRPC servers; key triggers include NettyModule, EventLoopGroup, NettyTransport, Epoll, KQueue, NIO."
---

Netty — это библиотека для сетевого взаимодействия, построенная вокруг неблокирующего ввода-вывода и модели `event loop`.
В Kora она используется как низкоуровневый механизм сетевого `транспорта` для модулей, которым нужно эффективно обрабатывать соединения и сетевые события.

Функционал настраивает работу общих компонентов Netty, которые используются другими модулями: [асинхронным HTTP-клиентом](http-client.md#asynchttpclient), [gRPC-клиентом](grpc-client.md), [gRPC-сервером](grpc-server.md).
Эти настройки полезны, когда приложению нужно управлять сетевым `транспортом`, количеством потоков обработки ввода-вывода или выбором `платформенного транспорта`.
Обычно значения по умолчанию подходят для большинства сервисов, но при высокой сетевой нагрузке или особых требованиях к окружению их можно задать явно.

Сам модуль не предоставляет отдельный пользовательский `программный интерфейс`,
а служит для настройки [`транспорта Netty` и `цикла событий Netty`](https://netty.io/4.1/api/io/netty/channel/EventLoop.html) в рамках Kora.

## Подключение { #connection }

Обычно модуль не требуется подключать вручную: его добавляют как транзитивную зависимость модули Kora, которым нужен Netty.

## Что предоставляется { #what-it-provides }

При подключении модуля `NettyCommonModule` добавляет в контейнер зависимостей следующие общие компоненты.
Модули-потребители ([асинхронный HTTP-клиент](http-client.md#asynchttpclient), [gRPC-клиент](grpc-client.md), [gRPC-сервер](grpc-server.md)) внедряют их вместо создания собственных потоков Netty:

- **`NettyTransportConfig`** — конфигурация, привязанная к секции `netty` (предпочтительный [транспорт](#transport) и [количество рабочих потоков](#configuration)).
- **Рабочая `EventLoopGroup`** с тегом `@Tag(NettyCommonModule.WorkerLoopGroup.class)` — общий `цикл событий`, который обрабатывает соединения и сетевой ввод-вывод. Его размер задается параметром `threads`, и его используют как клиенты, так и серверы.
- **`EventLoopGroup` для приема соединений (boss)** с тегом `@Tag(NettyCommonModule.BossLoopGroup.class)` — отдельная группа, фиксированная на `1` поток, которую используют только серверные компоненты (например, [gRPC-сервер](grpc-server.md)) для приема входящих соединений; параметр `threads` на нее не влияет.
- **[`NettyChannelFactory`](#channel-factory)** — фабрика, создающая каналы Netty, соответствующие выбранному [транспорту](#transport).

Обе группы `цикла событий` управляются [жизненным циклом](container.md#component-lifecycle) Kora: они корректно останавливаются после освобождения всех зависимых компонентов, поэтому ручное управление не требуется.

Продвинутые модули, которые строят собственный `транспорт` Netty, могут внедрять эти компоненты напрямую:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyNettyTransport {

        public MyNettyTransport(@Tag(NettyCommonModule.WorkerLoopGroup.class) EventLoopGroup workerGroup,
                                NettyChannelFactory channelFactory) {
            // build a client or server bootstrap on the shared event loop
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyNettyTransport(
        @Tag(NettyCommonModule.WorkerLoopGroup::class) workerGroup: EventLoopGroup,
        channelFactory: NettyChannelFactory,
    )
    ```

## Конфигурация { #configuration }

Пример конфигурации, описанной в классе `NettyTransportConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    netty {
        transport = "NIO" //(1)!
        threads = 2 //(2)!
    }
    ```

    1. Предпочитаемый [транспорт](https://netty.io/wiki/native-transports.html): `NIO`, `EPOLL` или `KQUEUE` (по умолчанию не указано, необязательно).
    2. Количество потоков `worker event loop` (по умолчанию: количество доступных ядер процессора, умноженное на `2`). Для серверных компонентов дополнительно создается `boss event loop` с `1` потоком, значение `threads` на него не влияет.

=== ":simple-yaml: `YAML`"

    ```yaml
    netty:
      transport: "NIO" #(1)!
      threads: 2 #(2)!
    ```

    1. Предпочитаемый [транспорт](https://netty.io/wiki/native-transports.html): `NIO`, `EPOLL` или `KQUEUE` (по умолчанию не указано, необязательно).
    2. Количество потоков `worker event loop` (по умолчанию: количество доступных ядер процессора, умноженное на `2`). Для серверных компонентов дополнительно создается `boss event loop` с `1` потоком, значение `threads` на него не влияет.

## Транспорт { #transport }

Параметр `transport` задает предпочтительный `транспорт` Netty:

- `NIO` - стандартный `транспорт` Java NIO, доступен всегда.
- `EPOLL` - `платформенный транспорт` Linux.
- `KQUEUE` - `платформенный транспорт` macOS / BSD.

Если параметр `transport` не задан, Kora выбирает первый доступный транспорт в порядке:

1. `EPOLL`
2. `KQUEUE`
3. `NIO`

Если указанный `платформенный транспорт` недоступен во время выполнения, Kora использует первый доступный `транспорт` из этого же порядка.

## Платформенный транспорт { #native-transport }

Для использования `EPOLL` или `KQUEUE` соответствующая платформенная зависимость Netty должна быть доступна в `пути классов времени выполнения`:

- [`io.netty:netty-transport-native-epoll`](https://mvnrepository.com/artifact/io.netty/netty-transport-native-epoll) для Linux.
- [`io.netty:netty-transport-native-kqueue`](https://mvnrepository.com/artifact/io.netty/netty-transport-native-kqueue) для macOS / BSD.

При подключении платформенной зависимости требуется выбрать `классификатор` под целевую платформу, например `linux-x86_64`, `osx-x86_64` или `osx-aarch_64`.

???+ tip "Совет"

    Обычно достаточно не задавать `transport` явно и оставить автоматический выбор. `Платформенный транспорт` стоит подключать осознанно: например, если он нужен для производительности или возможностей Netty, недоступных в `NIO`.

## Фабрика каналов { #channel-factory }

`NettyChannelFactory` — это общий внедряемый компонент, который создает экземпляры [`ChannelFactory`](https://netty.io/4.1/api/io/netty/channel/ChannelFactory.html) Netty, соответствующие выбранному [транспорту](#transport).
Это продвинутая точка внедрения для модулей, которые строят собственный клиентский или серверный `bootstrap` Netty и хотят получать каналы, согласованные с выбранным `транспортом`:

- `getClientFactory()` / `getClientFactory(boolean domainSocket)` — фабрика клиентских каналов.
- `getServerFactory()` / `getServerFactory(boolean domainSocket)` — фабрика серверных каналов.

Перегрузки без аргументов создают стандартные сокет-каналы `TCP`.
Передача `domainSocket = true` запрашивает канал [Unix domain socket](https://en.wikipedia.org/wiki/Unix_domain_socket): его поддерживают `платформенные транспорты` `EPOLL` и `KQUEUE`, тогда как реализация `NIO` в настоящее время возвращается к стандартным сокет-каналам.

## Фабрика потоков { #thread-factory }

Обе группы `цикла событий` — рабочая и boss — принимают необязательную [`ThreadFactory`](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ThreadFactory.html).
Чтобы настроить именование или приоритет потоков Netty, предоставьте компонент `ThreadFactory` с тегом `@Tag(NettyCommonModule.class)`; при его наличии Kora использует его для обеих групп:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends AsyncHttpClientModule {

        @Tag(NettyCommonModule.class)
        default ThreadFactory nettyThreadFactory() {
            return new DefaultThreadFactory("netty-io");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : AsyncHttpClientModule {

        @Tag(NettyCommonModule::class)
        fun nettyThreadFactory(): ThreadFactory = DefaultThreadFactory("netty-io")
    }
    ```
