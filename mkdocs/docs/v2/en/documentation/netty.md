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

## What it provides { #what-it-provides }

When the module is connected, `NettyCommonModule` contributes the following shared components to the dependency container.
Consumer modules ([HTTP Async client](http-client.md#asynchttpclient), [gRPC client](grpc-client.md), [gRPC server](grpc-server.md)) inject them instead of creating their own Netty threads:

- **`NettyTransportConfig`** - configuration bound to the `netty` section (preferred [transport](#transport) and [worker thread count](#configuration)).
- **Worker `EventLoopGroup`** with tag `@Tag(NettyCommonModule.WorkerLoopGroup.class)` - the shared `event loop` that processes connections and network I/O. Its size is set by the `threads` parameter, and both clients and servers use it.
- **Boss `EventLoopGroup`** with tag `@Tag(NettyCommonModule.BossLoopGroup.class)` - a separate group fixed at `1` thread that only server components (for example [gRPC server](grpc-server.md)) use to accept incoming connections; the `threads` parameter does not affect it.
- **[`NettyChannelFactory`](#channel-factory)** - a factory that creates Netty channels matching the selected [transport](#transport).

Both `event loop` groups are managed by the Kora [lifecycle](container.md#component-lifecycle): they are shut down gracefully after all dependent components are released, so no manual management is required.

Advanced modules that build a custom Netty `transport` can inject these components directly:

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

## Channel factory { #channel-factory }

`NettyChannelFactory` is a shared injectable component that produces Netty [`ChannelFactory`](https://netty.io/4.1/api/io/netty/channel/ChannelFactory.html) instances matching the selected [transport](#transport).
It is an advanced injection point for modules that build their own Netty client or server `bootstrap` and want channels consistent with the chosen `transport`:

- `getClientFactory()` / `getClientFactory(boolean domainSocket)` - a factory for client channels.
- `getServerFactory()` / `getServerFactory(boolean domainSocket)` - a factory for server channels.

The no-argument overloads create standard `TCP` socket channels.
Passing `domainSocket = true` requests a [Unix domain socket](https://en.wikipedia.org/wiki/Unix_domain_socket) channel: this is supported by the `EPOLL` and `KQUEUE` `native transports`, while the `NIO` implementation currently falls back to standard socket channels.

## Thread factory { #thread-factory }

Both the worker and boss `event loop` groups accept an optional [`ThreadFactory`](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ThreadFactory.html).
To customize Netty thread naming or priority, provide a `ThreadFactory` component tagged with `@Tag(NettyCommonModule.class)`; when present, Kora uses it for both groups:

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
