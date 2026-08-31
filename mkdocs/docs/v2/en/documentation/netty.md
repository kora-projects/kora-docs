---
description: "Explains the shared Kora Netty transport: event loop groups, transport selection between NIO, EPOLL, KQUEUE and io_uring, channel factory and thread factories. Use when working with NettyModule, NettyTransportConfig, NettyChannelFactory, NettyEventLoopFactory, EventLoopGroup."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the shared Netty transport and event loop configuration in Kora; key triggers include NettyModule, NettyTransportConfig, NettyChannelFactory, NettyEventLoopFactory, EventLoopGroup, EventLoopWorker, EventLoopBoss, netty config section, Epoll, KQueue, io_uring, NIO."
---

Netty is a networking library built around non-blocking I/O and the `event loop` model.
In Kora it is a low-level network `transport` for modules that have to process connections and network events efficiently.

The module provides no user-facing API of its own.
It exists so that every Netty-based part of an application shares one `event loop` and one `transport` decision,
instead of each of them starting its own I/O threads.
The [Redis cache](cache.md#redis) driver is built on it, and a custom Netty `transport` written inside a service can be built on the very same components.

These settings are useful when an application has to control the network `transport`, the number of I/O threads,
or the choice of a `native transport`.
The defaults suit most services, but they can be set explicitly under high network load or specific environment requirements.

The module configures the [Netty transport and the Netty event loop](https://netty.io/4.2/api/io/netty/channel/EventLoop.html) within Kora.

## Connection { #connection }

Usually the module does not need to be connected manually: Kora modules that require Netty extend `NettyModule` themselves
and bring it as a transitive dependency.
The [Redis cache](cache.md#redis) module is exactly such a case: `LettuceRedisCacheModule` extends `LettuceModule`,
and `LettuceModule` extends `NettyModule`.

Connect it explicitly only when a custom Netty `transport` is built inside the service and should share the `event loop` with everything else:

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:netty-common"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends NettyModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:netty-common")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : NettyModule
    ```

## What it provides { #what-it-provides }

`NettyModule` contributes the following shared components to the dependency container:

- **`NettyTransportConfig`** - configuration bound to the `netty` section: the preferred [transport](#transport) and the [thread count](#configuration) of the `event loop` groups.
- **Worker `EventLoopGroup`** with tag `@Tag(NettyModule.EventLoopWorker.class)` - the shared `event loop` that processes established connections and network I/O. Netty-based clients run on it.
- **Boss `EventLoopGroup`** with tag `@Tag(NettyModule.EventLoopBoss.class)` - a separate `event loop` meant for server `bootstraps` that accept incoming connections, so that accepting a connection is never delayed by I/O work on established ones.
- **[`NettyEventLoopFactory`](#event-loop-factory)** with the same two tags - the factories the groups above are built from.
- **[`NettyChannelFactory`](#channel-factory)** - a factory that creates Netty channels matching the selected [transport](#transport).

Both groups are built from the same [transport](#transport) selection and are sized by the same `threads` parameter,
so worker and boss threads are always of the same kind.

Both `event loop` groups are managed by the Kora [lifecycle](container.md#component-lifecycle):
they are shut down gracefully after every component that depends on them has been released, so no manual management is required.

The `event loop` factories, both groups and `NettyChannelFactory` are registered as [standard components](container.md#default-factory),
so any of them can be replaced by declaring a component of the same type with the same [tag](container.md#tags).

Components that build their own Netty `transport` inject these components directly:

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

## Configuration { #configuration }

An example of the configuration described by the `NettyTransportConfig` interface:

===! ":material-code-json: `Hocon`"

    ```javascript
    netty {
        transport = "NIO" //(1)!
        threads = 2 //(2)!
    }
    ```

    1. Preferred [transport](https://netty.io/wiki/native-transports.html): `NIO`, `EPOLL`, `KQUEUE` or `URING` (optional, when not set the [transport is selected automatically](#transport)).
    2. Number of threads in each `event loop` group (default: the number of processors available to Netty multiplied by `2`). The worker and boss groups are sized by this same value.

=== ":simple-yaml: `YAML`"

    ```yaml
    netty:
      transport: "NIO" #(1)!
      threads: 2 #(2)!
    ```

    1. Preferred [transport](https://netty.io/wiki/native-transports.html): `NIO`, `EPOLL`, `KQUEUE` or `URING` (optional, when not set the [transport is selected automatically](#transport)).
    2. Number of threads in each `event loop` group (default: the number of processors available to Netty multiplied by `2`). The worker and boss groups are sized by this same value.

The default thread count comes from Netty's own `NettyRuntime.availableProcessors()`, which falls back to
`Runtime.availableProcessors()` and can be overridden with the `io.netty.availableProcessors` system property.
Set that property, or `threads` explicitly, when the CPU limit of the container does not match what the JVM reports.

The root-level `netty` section belongs to this module only.
Drivers that embed their own Netty stack configure it under their own section:
the [Cassandra](database-cassandra.md) driver, for example, has a nested `cassandra.advanced.netty` section
that configures the driver's own `event loop` groups and has nothing to do with the shared `transport` described here.

## Transport { #transport }

The `transport` parameter sets the preferred Netty `transport`:

- `NIO` - standard Java NIO `transport`, always available.
- `EPOLL` - Linux `native transport`.
- `KQUEUE` - macOS / BSD `native transport`.
- `URING` - Linux `io_uring` `native transport`.

If `transport` is not set, Kora picks the first `transport` available at runtime, in this order:

1. `URING`
2. `EPOLL`
3. `KQUEUE`
4. `NIO`

Availability of a `native transport` means two things at once: its classes are on the `classpath`,
and Netty reports the platform as supported.
If the configured `native transport` fails either check, Kora falls back to the same order instead of failing to start.
`NIO` is the only value that is always honored exactly as configured, because it has no availability check.

Note that the automatic order prefers `io_uring` over `epoll`:
adding the `io_uring` `native transport` to the `runtime classpath` of a Linux service changes the selected `transport`
even if nothing else in the configuration changed.
Pin `transport` explicitly when the selection has to stay stable across environments.

The same selection is applied to both `event loop` groups and to the [channel factory](#channel-factory),
so channels and the `event loop` they are registered on always come from the same `transport`.

## Native Transport { #native-transport }

The module compiles against the `native transport` classes but does not bring them at runtime,
so to use `EPOLL`, `KQUEUE` or `URING` the corresponding Netty dependency must be present in the `runtime classpath`:

| Transport | Artifact                                                                                                              | Platform      | Classifiers                                       |
|-----------|-----------------------------------------------------------------------------------------------------------------------|---------------|---------------------------------------------------|
| `EPOLL`   | [`io.netty:netty-transport-native-epoll`](https://mvnrepository.com/artifact/io.netty/netty-transport-native-epoll)      | Linux         | `linux-x86_64`, `linux-aarch_64`, `linux-riscv64` |
| `KQUEUE`  | [`io.netty:netty-transport-native-kqueue`](https://mvnrepository.com/artifact/io.netty/netty-transport-native-kqueue)    | macOS / BSD   | `osx-x86_64`, `osx-aarch_64`                      |
| `URING`   | [`io.netty:netty-transport-native-io_uring`](https://mvnrepository.com/artifact/io.netty/netty-transport-native-io_uring) | Linux         | `linux-x86_64`, `linux-aarch_64`, `linux-riscv64` |

The `classifier` must match the target platform, and the version must match the rest of the `io.netty` artifacts on the `classpath`.
Kora 2.0 brings Netty `4.2.17.Final`:

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    runtimeOnly "io.netty:netty-transport-native-epoll:4.2.17.Final:linux-x86_64"
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    runtimeOnly("io.netty:netty-transport-native-epoll:4.2.17.Final:linux-x86_64")
    ```

The native artifact brings the matching `netty-transport-classes-*` artifact transitively, so it does not have to be declared separately.
A service built for several platforms declares one native artifact per platform: they coexist on the `classpath`,
and the availability check picks the one that actually works.

???+ tip "Recommendation"

    Usually it is enough to leave `transport` unset and let Kora select it automatically.
    Add a `native transport` intentionally: for example, when it is required for performance or for Netty features unavailable in `NIO`.

For a [GraalVM native image](graalvm-native.md) the module ships metadata that initializes the `io.netty` classes at run time,
which is what native transports require.

## Channel factory { #channel-factory }

`NettyChannelFactory` is a shared injectable component that produces Netty [`ChannelFactory`](https://netty.io/4.2/api/io/netty/channel/ChannelFactory.html) instances matching the selected [transport](#transport).
It is the injection point for components that build their own Netty client or server `bootstrap` and want channels consistent with the chosen `transport`:

- `build()` / `build(boolean domainSocket)` - a `ChannelFactory<Channel>` for client channels.
- `buildServer()` / `buildServer(boolean domainSocket)` - a `ChannelFactory<ServerChannel>` for server channels.

The no-argument overloads delegate to the `boolean` ones with `domainSocket = false` and create standard `TCP` socket channels.
Passing `domainSocket = true` requests a [Unix domain socket](https://en.wikipedia.org/wiki/Unix_domain_socket) channel:
every `transport`, `NIO` included, provides both a client and a server domain socket channel implementation.

## Event loop factory { #event-loop-factory }

`NettyEventLoopFactory` is a single-method factory that builds an `EventLoopGroup` for the selected [transport](#transport)
with the configured [thread count](#configuration).
Kora registers two of them, tagged `@Tag(NettyModule.EventLoopWorker.class)` and `@Tag(NettyModule.EventLoopBoss.class)`,
and builds the two shared groups from them.

Inject a factory instead of a group when a component needs an isolated `EventLoopGroup` rather than the shared one -
for example when its I/O must not compete with the rest of the application:

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

A group created this way is not managed by the container, so the component that created it is responsible for shutting it down,
as in the example above via the [component lifecycle](container.md#component-lifecycle).

## Thread factory { #thread-factory }

Each `event loop` group is built with a [`ThreadFactory`](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadFactory.html).
By default Kora uses Netty's [`DefaultThreadFactory`](https://netty.io/4.2/api/io/netty/util/concurrent/DefaultThreadFactory.html)
producing daemon threads named after `netty-kora-worker` for the worker group and `netty-kora-boss` for the boss group.

To customize thread naming or priority, provide a `ThreadFactory` component with the [tag](container.md#tags) of the group it belongs to.
The tags are separate, so worker and boss threads can be configured independently,
and providing only one of them leaves the other on the default:

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

Kora's own default thread factories create daemon threads on purpose: the `event loop` groups are released by the container,
and daemon threads must not keep the JVM alive if a shutdown path is skipped.
A custom `ThreadFactory` should keep that property.
