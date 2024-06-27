Functionality customizing Netty components used by other modules like [Vertx](database-vertx.md), [HTTP Async client](http-client.md#asynchttpclient), [gRPC client](grpc-client.md), [gRPC server](grpc-server.md).

Module itself does not provide any utility on its own,
but only serves to configure [Netty transport and Netty event loop](https://netty.io/4.1/api/io/netty/channel/EventLoop.html) within Kora.

## Connection

The module will be transitively provided to dependencies that use it.

## Configuration

An example of the configuration described in the `NettyTransportConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    netty {
        transport = "NIO" //(1)!
        threads = 2 //(2)!
    }
    ```

    1. Preferred [trasnport](https://netty.io/wiki/native-transports.html) if available on the path as a dependency, is selected by default in order of availability: 
        1. `Epoll` 
        2. `KQueue`
        3. `Nio`
    2. Number of threads [Netty event loop](https://netty.io/4.1/api/io/netty/channel/EventLoop.html), defaults to the number of CPU cores multiplied by 2.

=== ":simple-yaml: `YAML`"

    ```yaml
    netty:
      transport: "NIO" #(1)!
      threads: 2 #(2)!
    ```

    1. Preferred [trasnport](https://netty.io/wiki/native-transports.html) if available on the path as a dependency, is selected by default in order of availability: 
        1. `Epoll`
        2. `KQueue`
        3. `Nio`
    2. Number of threads [Netty event loop](https://netty.io/4.1/api/io/netty/channel/EventLoop.html), defaults to the number of CPU cores multiplied by 2.
