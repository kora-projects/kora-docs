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

- `EPOLL` - `платформенный транспорт` Linux.
- `KQUEUE` - `платформенный транспорт` macOS / BSD.
- `NIO` - стандартный `транспорт` Java NIO, доступен всегда.

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
