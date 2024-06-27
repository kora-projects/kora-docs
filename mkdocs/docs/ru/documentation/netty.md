Функционал настраивающий работу Netty компонент которые используются другими модулями как [Vertx](database-vertx.md), [HTTP Async клиент](http-client.md#asynchttpclient), [gRPC клиент](grpc-client.md), [gRPC сервер](grpc-server.md).

Сам модуль самостоятельно не предоставляет какой-либо пользы, 
а лишь служит для настройки [Netty транспорта и цикла событий Netty](https://netty.io/4.1/api/io/netty/channel/EventLoop.html) в рамках Kora.

## Подключение

Модуль будет транзитивно предоставлен использующими его зависимостям.

## Конфигурация

Пример конфигурации описанной в классе `NettyTransportConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    netty {
        transport = "NIO" //(1)!
        threads = 2 //(2)!
    }
    ```

    1. Предпочитаемый [траснпорт](https://netty.io/wiki/native-transports.html) если доступен на пути как зависимость, по умолчанию выбирается в порядке доступности: 
        1. `Epoll` (надо подключить [зависимость](https://mvnrepository.com/artifact/io.netty/netty-transport-native-epoll))
        2. `KQueue` (надо подключить [зависимость](https://mvnrepository.com/artifact/io.netty/netty-transport-native-kqueue))
        3. `Nio`
    2. Количество потоков [цикла событий Netty](https://netty.io/4.1/api/io/netty/channel/EventLoop.html), по умолчанию равен кол-во ядер процессора умноженных на 2

=== ":simple-yaml: `YAML`"

    ```yaml
    netty:
      transport: "NIO" #(1)!
      threads: 2 #(2)!
    ```

    1. Предпочитаемый [траснпорт](https://netty.io/wiki/native-transports.html) если доступен на пути как зависимость, по умолчанию выбирается в порядке доступности: 
        1. `Epoll` (надо подключить [зависимость](https://mvnrepository.com/artifact/io.netty/netty-transport-native-epoll))
        2. `KQueue` (надо подключить [зависимость](https://mvnrepository.com/artifact/io.netty/netty-transport-native-kqueue))
        3. `Nio`
    2. Количество потоков [цикла событий Netty](https://netty.io/4.1/api/io/netty/channel/EventLoop.html), по умолчанию равен кол-во ядер процессора умноженных на 2
