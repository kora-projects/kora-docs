---
description: "Explains Kora Netty customization and transport configuration used by HTTP Async clients, gRPC clients and gRPC servers. Use when working with NettyModule, EventLoopGroup, NettyTransport, Epoll, KQueue, NIO."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Netty customization and transport configuration used by HTTP Async clients, gRPC clients and gRPC servers; key triggers include NettyModule, EventLoopGroup, NettyTransport, Epoll, KQueue, NIO."
---

Netty is a networking library built around non-blocking I/O and the `event loop` model.
In Kora, it is used as a low-level network `transport` mechanism for modules that need to process connections and network events efficiently.

This functionality customizes shared Netty components used by other modules: [HTTP Async client](http-client.md#asynchttpclient), [gRPC client](grpc-client.md), [gRPC server](grpc-server.md).
These settings are useful when an application needs to control the network `transport`, I/O thread count, or native transport selection.
Default values are usually suitable for most services, but you can set them explicitly for high network load or specific environment requirements.

Module itself does not provide any utility on its own,
but only serves to configure [Netty transport and Netty event loop](https://netty.io/4.1/api/io/netty/channel/EventLoop.html) within Kora.

## Connection { #connection }

Usually you do not need to connect this module manually: it is added as a transitive dependency by Kora modules that require Netty.

## Configuration { #configuration }

An example of the configuration described by the `NettyTransportConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    netty {
        transport = "NIO" //(1)!
        threads = 2 //(2)!
    }
    ```

    1. Preferred [transport](https://netty.io/wiki/native-transports.html): `NIO`, `EPOLL` or `KQUEUE` (default: not specified, optional).
    2. Number of `worker event loop` threads (default: number of available CPU cores multiplied by `2`). Server components also create a `boss event loop` with `1` thread, and the `threads` value does not affect it.

=== ":simple-yaml: `YAML`"

    ```yaml
    netty:
      transport: "NIO" #(1)!
      threads: 2 #(2)!
    ```

    1. Preferred [transport](https://netty.io/wiki/native-transports.html): `NIO`, `EPOLL` or `KQUEUE` (default: not specified, optional).
    2. Number of `worker event loop` threads (default: number of available CPU cores multiplied by `2`). Server components also create a `boss event loop` with `1` thread, and the `threads` value does not affect it.

## Transport { #transport }

The `transport` parameter sets the preferred Netty `transport`:

- `NIO` - standard Java NIO `transport`, always available.
- `EPOLL` - Linux `native transport`.
- `KQUEUE` - macOS / BSD `native transport`.

If `transport` is not set, Kora selects the first available transport in this order:

1. `EPOLL`
2. `KQUEUE`
3. `NIO`

If the configured `native transport` is not available at runtime, Kora uses the first available `transport` from the same order.

## Native Transport { #native-transport }

To use `EPOLL` or `KQUEUE`, the corresponding Netty native dependency must be available in the `runtime classpath`:

- [`io.netty:netty-transport-native-epoll`](https://mvnrepository.com/artifact/io.netty/netty-transport-native-epoll) for Linux.
- [`io.netty:netty-transport-native-kqueue`](https://mvnrepository.com/artifact/io.netty/netty-transport-native-kqueue) for macOS / BSD.

When adding a native dependency, choose the `classifier` for the target platform, for example `linux-x86_64`, `osx-x86_64` or `osx-aarch_64`.

???+ tip "Recommendation"

    Usually it is enough to leave `transport` unset and let Kora select it automatically. Add `native transport` intentionally: for example, when you need it for performance or Netty features unavailable in `NIO`.
