---
description: "Explains Kora HTTP clients, the OkHttp, Apache HttpClient and JDK transports, declarative client annotations, request and response mapping, interceptors, authorization and telemetry. Use when working with @HttpClient, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @Mapping, @ResponseCodeMapper, @InterceptWith."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora HTTP clients, the OkHttp / Apache HttpClient / JDK transports, declarative client annotations, request and response mapping, interceptors, authorization and telemetry; key triggers include @HttpClient, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @Mapping, @ResponseCodeMapper, @InterceptWith, HttpClientResponseMapper, HttpClientRequestMapper, HttpClientParameterWriter, HttpClientInterceptor, HttpClientModule, OkHttpClientModule, ApacheHttpClientModule, JdkHttpClientModule."
---

The `HTTP client` module describes outgoing HTTP calls: transport implementation, request mapping, response mapping,
telemetry, and interceptors. In Kora, clients can be described declaratively with `@HttpClient` and `@HttpRoute`,
or used imperatively through the common `HttpClient` interface when a request must be built in code.

The declarative approach is suitable for most integrations with external services: the method contract becomes the remote call contract,
and Kora creates the implementation at compile time without using `Reflection` at runtime. The imperative approach is useful for low-level
or dynamic scenarios where path, headers, query parameters, or body are easier to assemble manually.

All HTTP client calls in Kora are **synchronous and blocking**: `HttpClient.execute()` returns `HttpClientResponse` directly,
and a declarative method returns its result directly. Concurrency is expected to come from virtual threads
rather than from reactive or coroutine return types.

???+ tip "Recommendation"

    **We recommend** using an approach where the `OpenAPI` file is the primary contract
    and clients are created from it using the generator.
    This approach allows you to achieve consistency between the consumer and owner of the contract
    and update the API faster when the contract changes by replacing the contract file.
    For more information about the generator, see the [section on generating from OpenAPI](openapi-codegen.md).

For a step-by-step walkthrough before the reference details, see [HTTP Client](../guides/http-client.md) and [Advanced HTTP Client](../guides/http-client-advanced.md).

## OkHttp { #okhttp }

HTTP client implementation based on the [OkHttp](https://github.com/square/okhttp) library.
The Kora module itself is written in Java, but the OkHttp library is a Kotlin library and brings its own dependencies.
This transport is the one to pick when `HTTP/2` or `HTTP/3`, `GZip` compression, or other OkHttp-specific options are required.

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:http-client-ok"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends OkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:http-client-ok")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : OkHttpClientModule
    ```

The `HttpClient` interface implementation is `OkHttpClient` from the `io.koraframework.http.client.ok` package.

### Configuration { #configuration }

Basic OkHttp client configuration parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        connectTimeout = "5s" //(1)!
        readTimeout = "2m" //(2)!
    }
    ```

    1.  Maximum time to establish a connection (default: `5s`)
    2.  Maximum time to read a response (default: `2m`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      connectTimeout: "5s" #(1)!
      readTimeout: "2m" #(2)!
    ```

    1.  Maximum time to establish a connection (default: `5s`)
    2.  Maximum time to read a response (default: `2m`)

??? note "Full Configuration"

    Example of the complete configuration described in the `OkHttpClientConfig`
    and `HttpClientConfig` classes (default or example values are specified):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpClient {
            ok {
                followRedirects = true //(1)!
                retryOnConnectionFailure = true //(2)!
                httpVersion = "HTTP_1_1" //(3)!
            }
            connectTimeout = "5s" //(4)!
            readTimeout = "2m" //(5)!
            useEnvProxy = false //(6)!
            proxy {
                host = "localhost" //(7)!
                port = 8090 //(8)!
                user = "user" //(9)!
                password = "password" //(10)!
                nonProxyHosts = [ "host1", "host2" ] //(11)!
            }
        }
        ```

        1. Whether to follow [HTTP redirects](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections) (default: `true`)
        2. Whether to retry a request after a connection failure; this can affect the maximum connection establishment time (default: `true`)
        3. Maximum `HTTP` protocol version to use, available values: `HTTP_1_1` / `HTTP_2` / `HTTP_3` (default: `HTTP_1_1`)
        4. Maximum time to establish a connection (default: `5s`)
        5. Maximum time to read a response (default: `2m`)
        6. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
        7. Proxy host (required if the `proxy` section is present, no default)
        8. Proxy port (required if the `proxy` section is present, no default)
        9. Proxy user (optional, no default)
        10. Proxy password (optional, no default)
        11. Hosts to exclude from proxying (optional, no default)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpClient:
          ok:
            followRedirects: true #(1)!
            retryOnConnectionFailure: true #(2)!
            httpVersion: "HTTP_1_1" #(3)!
          connectTimeout: "5s" #(4)!
          readTimeout: "2m" #(5)!
          useEnvProxy: false #(6)!
          proxy:
            host: "localhost" #(7)!
            port: 8090  #(8)!
            user: "user"  #(9)!
            password: "password" #(10)!
            nonProxyHosts: [ "host1", "host2" ] #(11)!
        ```

        1. Whether to follow [HTTP redirects](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections) (default: `true`)
        2. Whether to retry a request after a connection failure; this can affect the maximum connection establishment time (default: `true`)
        3. Maximum `HTTP` protocol version to use, available values: `HTTP_1_1` / `HTTP_2` / `HTTP_3` (default: `HTTP_1_1`)
        4. Maximum time to establish a connection (default: `5s`)
        5. Maximum time to read a response (default: `2m`)
        6. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
        7. Proxy host (required if the `proxy` section is present, no default)
        8. Proxy port (required if the `proxy` section is present, no default)
        9. Proxy user (optional, no default)
        10. Proxy password (optional, no default)
        11. Hosts to exclude from proxying (optional, no default)

Telemetry is **not** configured in the transport section: logging, metrics and tracing are configured per declarative client
under `httpClient.<clientName>.telemetry`, see [Client Configuration](#client-configuration).

Module metrics are described in the [Metrics Reference](metrics.md#http-client) section.

#### Configurer { #configurer }

The transport builder can be customized with a `Configurer<OkHttpClient.Builder>` component.
Kora applies it as the last step, after its own configuration has been applied:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeConfigurer implements Configurer<OkHttpClient.Builder> {

        @Override
        public OkHttpClient.Builder configure(OkHttpClient.Builder builder) {
            return builder.callTimeout(Duration.ofSeconds(30));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeConfigurer : Configurer<OkHttpClient.Builder> {

        override fun configure(builder: OkHttpClient.Builder): OkHttpClient.Builder {
            return builder.callTimeout(Duration.ofSeconds(30))
        }
    }
    ```

`Configurer` lives in `io.koraframework.common` and is the shared customization contract of all Kora transports.

## Apache HttpClient { #apache-httpclient }

HTTP client implementation based on [Apache HttpClient 5](https://hc.apache.org/httpcomponents-client-5.5.x/).
It uses the classic (blocking) API and a pooling connection manager, which fits the synchronous Kora client contract directly.

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:http-client-apache"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends ApacheHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:http-client-apache")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : ApacheHttpClientModule
    ```

The `HttpClient` interface implementation is `ApacheHttpClient` from the `io.koraframework.http.client.apache` package.

### Configuration { #configuration-2 }

Basic Apache HttpClient configuration parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        connectTimeout = "5s" //(1)!
        readTimeout = "2m" //(2)!
    }
    ```

    1.  Maximum time to establish a connection (default: `5s`)
    2.  Maximum time to read a response, mapped to the Apache response timeout (default: `2m`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      connectTimeout: "5s" #(1)!
      readTimeout: "2m" #(2)!
    ```

    1.  Maximum time to establish a connection (default: `5s`)
    2.  Maximum time to read a response, mapped to the Apache response timeout (default: `2m`)

??? note "Full Configuration"

    Example of the complete configuration described in the `ApacheHttpClientConfig`
    and `HttpClientConfig` classes (default or example values are specified):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpClient {
            apache {
                followRedirects = true //(1)!
                maxRedirects = 3 //(2)!
                maxConnections = 1000 //(3)!
            }
            connectTimeout = "5s" //(4)!
            readTimeout = "2m" //(5)!
            useEnvProxy = false //(6)!
            proxy {
                host = "localhost" //(7)!
                port = 8090 //(8)!
                user = "user" //(9)!
                password = "password" //(10)!
                nonProxyHosts = [ "host1", "host2" ] //(11)!
            }
        }
        ```

        1. Whether to follow [HTTP redirects](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections) (default: `true`)
        2. Maximum number of redirects to follow for a single request (default: `3`)
        3. Maximum number of pooled connections, applied both in total and per route (default: number of available processors multiplied by `250`)
        4. Maximum time to establish a connection (default: `5s`)
        5. Maximum time to read a response (default: `2m`)
        6. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
        7. Proxy host (required if the `proxy` section is present, no default)
        8. Proxy port (required if the `proxy` section is present, no default)
        9. Proxy user (optional, no default)
        10. Proxy password (optional, no default)
        11. Hosts to exclude from proxying (optional, no default)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpClient:
          apache:
            followRedirects: true #(1)!
            maxRedirects: 3 #(2)!
            maxConnections: 1000 #(3)!
          connectTimeout: "5s" #(4)!
          readTimeout: "2m" #(5)!
          useEnvProxy: false #(6)!
          proxy:
            host: "localhost" #(7)!
            port: 8090  #(8)!
            user: "user"  #(9)!
            password: "password" #(10)!
            nonProxyHosts: [ "host1", "host2" ] #(11)!
        ```

        1. Whether to follow [HTTP redirects](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections) (default: `true`)
        2. Maximum number of redirects to follow for a single request (default: `3`)
        3. Maximum number of pooled connections, applied both in total and per route (default: number of available processors multiplied by `250`)
        4. Maximum time to establish a connection (default: `5s`)
        5. Maximum time to read a response (default: `2m`)
        6. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
        7. Proxy host (required if the `proxy` section is present, no default)
        8. Proxy port (required if the `proxy` section is present, no default)
        9. Proxy user (optional, no default)
        10. Proxy password (optional, no default)
        11. Hosts to exclude from proxying (optional, no default)

#### Configurer { #configurer-2 }

The Apache transport accepts two configurers: `Configurer<RequestConfig.Builder>` for the default request configuration
and `Configurer<HttpClientBuilder>` for the client itself. Both are optional:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeRequestConfigurer implements Configurer<RequestConfig.Builder> {

        @Override
        public RequestConfig.Builder configure(RequestConfig.Builder builder) {
            return builder.setConnectionRequestTimeout(1, TimeUnit.SECONDS);
        }
    }

    @Component
    public final class SomeClientConfigurer implements Configurer<HttpClientBuilder> {

        @Override
        public HttpClientBuilder configure(HttpClientBuilder builder) {
            return builder.setUserAgent("my-service");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeRequestConfigurer : Configurer<RequestConfig.Builder> {

        override fun configure(builder: RequestConfig.Builder): RequestConfig.Builder {
            return builder.setConnectionRequestTimeout(1, TimeUnit.SECONDS)
        }
    }

    @Component
    class SomeClientConfigurer : Configurer<HttpClientBuilder> {

        override fun configure(builder: HttpClientBuilder): HttpClientBuilder {
            return builder.setUserAgent("my-service")
        }
    }
    ```

## Native client { #native-client }

Implementation of an HTTP client based on the native client provided in the [JDK](https://openjdk.org/groups/net/httpclient/intro.html).
Kora runs it on a virtual thread executor, so the transport needs no thread pool configuration of its own.

### Dependency { #dependency-3 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:http-client-jdk"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends JdkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:http-client-jdk")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : JdkHttpClientModule
    ```

The `HttpClient` interface implementation is `JdkHttpClient` from the `io.koraframework.http.client.jdk` package.

### Configuration { #configuration-3 }

Basic JDK HttpClient configuration parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        connectTimeout = "5s" //(1)!
        readTimeout = "2m" //(2)!
    }
    ```

    1.  Maximum time to establish a connection (default: `5s`)
    2.  Maximum time to read a response (default: `2m`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      connectTimeout: "5s" #(1)!
      readTimeout: "2m" #(2)!
    ```

    1.  Maximum time to establish a connection (default: `5s`)
    2.  Maximum time to read a response (default: `2m`)

??? note "Full Configuration"

    Example of the complete configuration described in the `JdkHttpClientConfig`
    and `HttpClientConfig` classes (default or example values are specified):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpClient {
            jdk {
                followRedirects = true //(1)!
                httpVersion = "HTTP_1_1" //(2)!
            }
            connectTimeout = "5s" //(3)!
            readTimeout = "2m" //(4)!
            useEnvProxy = false //(5)!
            proxy {
                host = "localhost" //(6)!
                port = 8090 //(7)!
                user = "user" //(8)!
                password = "password" //(9)!
                nonProxyHosts = [ "host1", "host2" ] //(10)!
            }
        }
        ```

        1. Whether to follow [HTTP redirects](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections) (default: `true`)
        2. Which `HTTP` protocol version to use, available values: `HTTP_1_1` / `HTTP_2` (default: `HTTP_1_1`)
        3. Maximum time to establish a connection (default: `5s`)
        4. Maximum time to read a response (default: `2m`)
        5. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
        6. Proxy host (required if the `proxy` section is present, no default)
        7. Proxy port (required if the `proxy` section is present, no default)
        8. Proxy user (optional, no default)
        9. Proxy password (optional, no default)
        10. Hosts to exclude from proxying (optional, no default)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpClient:
          jdk:
            followRedirects: true #(1)!
            httpVersion: "HTTP_1_1" #(2)!
          connectTimeout: "5s" #(3)!
          readTimeout: "2m" #(4)!
          useEnvProxy: false #(5)!
          proxy:
            host: "localhost" #(6)!
            port: 8090 #(7)!
            user: "user" #(8)!
            password: "password" #(9)!
            nonProxyHosts: [ "host1", "host2" ] #(10)!
        ```

        1. Whether to follow [HTTP redirects](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections) (default: `true`)
        2. Which `HTTP` protocol version to use, available values: `HTTP_1_1` / `HTTP_2` (default: `HTTP_1_1`)
        3. Maximum time to establish a connection (default: `5s`)
        4. Maximum time to read a response (default: `2m`)
        5. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
        6. Proxy host (required if the `proxy` section is present, no default)
        7. Proxy port (required if the `proxy` section is present, no default)
        8. Proxy user (optional, no default)
        9. Proxy password (optional, no default)
        10. Hosts to exclude from proxying (optional, no default)

#### Configurer { #configurer-3 }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeConfigurer implements Configurer<java.net.http.HttpClient.Builder> {

        @Override
        public java.net.http.HttpClient.Builder configure(java.net.http.HttpClient.Builder builder) {
            return builder.sslContext(SSLContext.getDefault());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeConfigurer : Configurer<java.net.http.HttpClient.Builder> {

        override fun configure(builder: java.net.http.HttpClient.Builder): java.net.http.HttpClient.Builder {
            return builder.sslContext(SSLContext.getDefault())
        }
    }
    ```

## Declarative Client { #client-declarative }

It is suggested to use special annotations to create a declarative client:

* `@HttpClient` - indicates that the interface is a declarative HTTP client
* `@HttpRoute` - specifies [HTTP request type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) and request path

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

`HttpMethod` is a holder of `String` constants (`GET`, `HEAD`, `POST`, `PUT`, `DELETE`, `CONNECT`, `OPTIONS`, `TRACE`, `PATCH`, `QUERY`),
so `method = "GET"` is equally valid.

A client interface may extend other interfaces: routes declared in a supertype are implemented as well,
and an overriding method in the client replaces the inherited route.

### Client Configuration { #client-configuration }

By default, configuration for a particular `@HttpClient` implementation is looked up at `httpClient.{lower case class name}`.
If the path must be specified explicitly, pass it as the annotation value:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient("httpClient.someClient") //(1)!
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

    1. The path to the configuration of this particular client

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient("httpClient.someClient") //(1)!
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

    1. The path to the configuration of this particular client

`@HttpClient` can also specify tags for injected components:

* `httpClientTag` — tag used to select a particular transport `HttpClient` when the graph contains several implementations with different `@Tag` values
* `telemetryTag` — tag used to select a particular `HttpClientTelemetryFactory`

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient(
        value = "httpClient.someClient",
        httpClientTag = CustomTransport.class,
        telemetryTag = CustomTelemetry.class
    )
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient(
        value = "httpClient.someClient",
        httpClientTag = CustomTransport::class,
        telemetryTag = CustomTelemetry::class
    )
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

Basic declarative client configuration parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        someClient {
            url = "https://localhost:8090" //(1)!
            requestTimeout = "10s" //(2)!
        }
    }
    ```

    1.  Base service `URL` where requests will be sent (required, no default)
    2.  Maximum request time (optional, no default)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      someClient:
        url: "https://localhost:8090" #(1)!
        requestTimeout: "10s" #(2)!
    ```

    1.  Base service `URL` where requests will be sent (required, no default)
    2.  Maximum request time (optional, no default)

??? note "Full Configuration"

    Example configuration in the case of the `httpClient.someClient` path described in the `DeclarativeHttpClientConfig`
    and `HttpClientTelemetryConfig` classes:

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpClient {
            someClient {
                url = "https://localhost:8090" //(1)!
                requestTimeout = "10s" //(2)!
                telemetry {
                    logging {
                        enabled = false //(3)!
                        mask = "***" //(4)!
                        maskQueries = [ ] //(5)!
                        maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(6)!
                        pathFull = false //(7)!
                        maxRequestBodyLogSize = "2MiB" //(8)!
                        maxResponseBodyLogSize = "2MiB" //(9)!
                    }
                    metrics {
                        enabled = false //(10)!
                        slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(11)!
                        tags = { // (12)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                    tracing {
                        enabled = true //(13)!
                        pathFull = true //(14)!
                        attributes = { // (15)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                }
            }
        }
        ```

        1. Base service `URL` where requests will be sent (required, no default)
        2. Maximum request time: may include `DNS` resolution, connection, request body write, server processing, and response body read. If the call requires redirects or retries, they must all finish within one period (optional, no default)
        3. Enables module logging (default: `false`)
        4. Mask used to hide specified headers and request or response parameters (default: `***`)
        5. List of request parameters to hide (default: `[]`)
        6. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
        7. Whether to log the full request path instead of the route template; when not specified, the full path is logged only at `TRACE` level and the template otherwise (optional, no default)
        8. Maximum request body size that is still written to the log; a larger body is skipped with a warning (default: `2MiB`)
        9. Maximum response body size that is still written to the log; a larger body is skipped with a warning (default: `2MiB`)
        10. Enables module metrics (default: `false`)
        11. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) buckets in milliseconds for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        12. Configures metric tags (default: `{}`)
        13. Enables module tracing (default: `true`)
        14. Whether the span carries the full `url.full` attribute instead of only `url.path` (default: `true`)
        15. Configures tracing attributes (default: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpClient:
          someClient:
            url: "https://localhost:8090" #(1)!
            requestTimeout: "10s" #(2)!
            telemetry:
              logging:
                enabled: false #(3)!
                mask: "***" #(4)!
                maskQueries: [ ] #(5)!
                maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(6)!
                pathFull: false #(7)!
                maxRequestBodyLogSize: "2MiB" #(8)!
                maxResponseBodyLogSize: "2MiB" #(9)!
              metrics:
                enabled: false #(10)!
                slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(11)!
                tags: #(12)!
                  key1: value1
                  key2: value2
              tracing:
                enabled: true #(13)!
                pathFull: true #(14)!
                attributes: #(15)!
                  key1: value1
                  key2: value2
        ```

        1. Base service `URL` where requests will be sent (required, no default)
        2. Maximum request time: may include `DNS` resolution, connection, request body write, server processing, and response body read. If the call requires redirects or retries, they must all finish within one period (optional, no default)
        3. Enables module logging (default: `false`)
        4. Mask used to hide specified headers and request or response parameters (default: `***`)
        5. List of request parameters to hide (default: `[]`)
        6. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
        7. Whether to log the full request path instead of the route template; when not specified, the full path is logged only at `TRACE` level and the template otherwise (optional, no default)
        8. Maximum request body size that is still written to the log; a larger body is skipped with a warning (default: `2MiB`)
        9. Maximum response body size that is still written to the log; a larger body is skipped with a warning (default: `2MiB`)
        10. Enables module metrics (default: `false`)
        11. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) buckets in milliseconds for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        12. Configures metric tags (default: `{}`)
        13. Enables module tracing (default: `true`)
        14. Whether the span carries the full `url.full` attribute instead of only `url.path` (default: `true`)
        15. Configures tracing attributes (default: `{}`)

???+ warning "Metrics and logging are disabled by default"

    In Kora 2.0 `telemetry.metrics.enabled` and `telemetry.logging.enabled` default to `false`, and `telemetry.tracing.enabled` to `true`.
    Nothing fails and nothing is written to the log when metrics are off — `http.client.request.duration` simply never appears.
    Enable them explicitly per client.

### Method Configuration { #method-configuration }

For a particular method, some parameters can be configured separately. The method configuration path is determined by the client path and the method name:
if the client path is `httpClient.someClient`, the final path for the `hello` method is `httpClient.someClient.hello`.

Method configuration is applied over client configuration: method `requestTimeout` replaces the client value, and method telemetry settings override
only explicitly specified fields.

Basic method configuration parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        someClient {
            hello {
                requestTimeout = "10s" //(1)!
            }
        }
    }
    ```

    1.  Maximum request time (optional, no default)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      someClient:
        hello:
          requestTimeout: "10s" #(1)!
    ```

    1.  Maximum request time (optional, no default)

??? note "Full Configuration"

    Full method configuration example described in the `HttpClientOperationConfig` class.
    Every field is optional: an omitted field inherits the client value.

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpClient {
            someClient {
                hello {
                    requestTimeout = "10s" //(1)!
                    telemetry {
                        logging {
                            enabled = false //(2)!
                            mask = "***" //(3)!
                            maskQueries = [ ] //(4)!
                            maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(5)!
                            pathFull = false //(6)!
                            maxRequestBodyLogSize = "2MiB" //(7)!
                            maxResponseBodyLogSize = "2MiB" //(8)!
                        }
                        metrics {
                            enabled = false //(9)!
                            slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(10)!
                            tags = { // (11)!
                                "key1" = "value1"
                                "key2" = "value2"
                            }
                        }
                        tracing {
                            enabled = true //(12)!
                            pathFull = true //(13)!
                            attributes = { // (14)!
                                "key1" = "value1"
                                "key2" = "value2"
                            }
                        }
                    }
                }
            }
        }
        ```

        1. Maximum request time: may include `DNS` resolution, connection, request body write, server processing, and response body read. If the call requires redirects or retries, they must all finish within one period (optional, inherits the client value)
        2. Enables module logging (optional, inherits the client value)
        3. Mask used to hide specified headers and request or response parameters (optional, inherits the client value)
        4. List of request parameters to hide (optional, inherits the client value)
        5. List of request or response headers to hide (optional, inherits the client value)
        6. Whether to log the full request path instead of the route template (optional, inherits the client value)
        7. Maximum request body size that is still written to the log (optional, inherits the client value)
        8. Maximum response body size that is still written to the log (optional, inherits the client value)
        9. Enables module metrics (optional, inherits the client value)
        10. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) buckets in milliseconds for metrics (optional, inherits the client value)
        11. Configures metric tags (optional, inherits the client value)
        12. Enables module tracing (optional, inherits the client value)
        13. Whether the span carries the full `url.full` attribute instead of only `url.path` (optional, inherits the client value)
        14. Configures tracing attributes (optional, inherits the client value)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpClient:
          someClient:
            hello:
              requestTimeout: "10s" #(1)!
              telemetry:
                logging:
                  enabled: false #(2)!
                  mask: "***" #(3)!
                  maskQueries: [ ] #(4)!
                  maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(5)!
                  pathFull: false #(6)!
                  maxRequestBodyLogSize: "2MiB" #(7)!
                  maxResponseBodyLogSize: "2MiB" #(8)!
                metrics:
                  enabled: false #(9)!
                  slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(10)!
                  tags: #(11)!
                    key1: value1
                    key2: value2
                tracing:
                  enabled: true #(12)!
                  pathFull: true #(13)!
                  attributes: #(14)!
                    key1: value1
                    key2: value2
        ```

        1. Maximum request time: may include `DNS` resolution, connection, request body write, server processing, and response body read. If the call requires redirects or retries, they must all finish within one period (optional, inherits the client value)
        2. Enables module logging (optional, inherits the client value)
        3. Mask used to hide specified headers and request or response parameters (optional, inherits the client value)
        4. List of request parameters to hide (optional, inherits the client value)
        5. List of request or response headers to hide (optional, inherits the client value)
        6. Whether to log the full request path instead of the route template (optional, inherits the client value)
        7. Maximum request body size that is still written to the log (optional, inherits the client value)
        8. Maximum response body size that is still written to the log (optional, inherits the client value)
        9. Enables module metrics (optional, inherits the client value)
        10. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) buckets in milliseconds for metrics (optional, inherits the client value)
        11. Configures metric tags (optional, inherits the client value)
        12. Enables module tracing (optional, inherits the client value)
        13. Whether the span carries the full `url.full` attribute instead of only `url.path` (optional, inherits the client value)
        14. Configures tracing attributes (optional, inherits the client value)

### Request { #request }

This section describes `HTTP` request transformations for a declarative `HTTP` client.
Use special annotations to specify request parameters.

#### Parameter Conversion { #string-parameter-converter }

`HttpClientParameterWriter<T>` converts a parameter value to a string before Kora puts it into a path, query parameter,
header, or cookie. The interface has one method:

```java
public interface HttpClientParameterWriter<T> {
    String convert(T value);
}
```

`String`, `Integer`, `Long`, `Boolean` and Java primitives are written directly and need no writer at all.
For every other type Kora looks up an `HttpClientParameterWriter<T>` component by the exact parameter type.
If the parameter has type `Map<String, T>`, the writer is looked up for value type `T`; if `Map<String, List<T>>` is used,
it is applied to every list item; for `List<T>` / `Set<T>` / `Collection<T>` it is applied to every element.

Built-in writers are available for `Boolean`, `Short`, `Integer`, `Long`, `Double`, `Float`, `UUID`, `BigDecimal`, `BigInteger`,
`Duration`, `OffsetTime`, `OffsetDateTime`, `LocalTime`, `LocalDate`, `LocalDateTime`, `ZonedDateTime`, and `Instant`.
Date and time types are written in `ISO` format. For custom types, provide an `HttpClientParameterWriter<T>` component:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserId(long value) {}

    @Module
    public interface UserIdModule {

        default HttpClientParameterWriter<UserId> userIdParameterWriter() {
            return value -> Long.toString(value.value());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserId(val value: Long)

    @Module
    interface UserIdModule {

        fun userIdParameterWriter(): HttpClientParameterWriter<UserId> {
            return HttpClientParameterWriter { value -> value.value.toString() }
        }
    }
    ```

After that, the type can be used in client parameters:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        User get(@Path("id") UserId id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        fun get(@Path("id") id: UserId): User
    }
    ```

For enums, `EnumHttpClientParameterWriter` from `io.koraframework.http.client.common.request.mapper` builds a writer
from the enum constants and a mapping function; it is also what the [OpenAPI generator](openapi-codegen.md) emits for enum parameters.

??? failure "HttpClientParameterWriter&lt;T&gt; was not found"

    The build fails with `No component found for dependency: HttpClientParameterWriter<T>`.
    Either the type is custom and no writer component exists, or the writer has a `@Tag` that the parameter does not.
    Declare an `HttpClientParameterWriter<T>` component for that exact type.

#### Path parameter { #path-parameter }

`@Path` - denotes the value of the request path part, the parameter itself is specified in `{quote}` in the path
and the name of the parameter is specified in `value` or is equal to the name of the method argument by default.
Path values are URL-encoded, so a space becomes `%20`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/{pathName}")
        void hello(@Path("pathName") String pathValue);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/{pathName}")
        fun hello(@Path("pathName") pathValue: String)
    }
    ```

Every `{name}` placeholder in the path must have a matching `@Path` parameter; otherwise the build fails
with `Path template contains parameters that have no matching @Path method parameter`.

#### Query parameter { #query-parameter }

`@Query` - query parameter value, the name is specified in `value` or defaults to the method argument name.
Single values, `List<T>`, `Set<T>`, `Collection<T>`, `Map<String, T>`, and `Map<String, List<T>>` are supported.
For non-string values, an available `HttpClientParameterWriter<T>` is used.
An empty collection is sent as a parameter without a value.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello(@Query("queryName") String queryValue,
                   @Query("queryNameList") List<String> queryValues);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(@Query("queryName") queryValue: String,
                  @Query("queryNameList") queryValues: List<String>)
    }
    ```

Query parameters can also be sent in key-value format using `Map`, where the key is the parameter name and must be `String`.
If a `Map` value is a list, every item is sent as a separate value of the same parameter.
If a list item is `null`, the parameter is sent without a value.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello(@Query Map<String, String> queryValues);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(@Query queryValues: Map<String, String>)
    }
    ```

#### Header { #header }

`@Header` - value of [request header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers), parameter name is specified in `value` or defaults to the method argument name.
Single values, `List<T>`, `Set<T>`, `Collection<T>`, `Map<String, T>`, and a ready `HttpHeaders` object are supported.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello(@Header("headerName") String headerValue,
                   @Header("headerNameList") List<String> headerValues);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(@Header("headerName") headerValue: String,
                  @Header("headerNameList") headerValues: List<String>)
    }
    ```

Headers can be sent in key-value format using `HttpHeaders` or `Map`, where the key is the header name and must be `String`.
For non-string values, an available `HttpClientParameterWriter<T>` is used:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello(@Header HttpHeaders headers);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(@Header headers: HttpHeaders)
    }
    ```

#### Request body { #request-body }

Specifying the body of a request requires using a method argument without special annotations.
Out of the box `byte[]`, `ByteBuffer`, `String`, `HttpBodyOutput`, `FormUrlEncoded` and `FormMultipart` are supported,
because `HttpClientRequestMapperModule` provides `HttpClientRequestMapper` implementations for exactly those types.

##### Json { #json }

In order to indicate that the body is Json and needs to automatically create such a writer and embed it,
is required to use the special `@Json` tag annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record MyBody(String name) { }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        void hello(@Json MyBody body); //(1)!
    }
    ```

    1. Specifies that the body should be written as Json

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class MyBody(val name: String)

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun hello(@Json body: MyBody) //(1)!
    }
    ```

    1. Specifies that the body should be written as Json

[Json](json.md) module is required, and a `JsonWriter<MyBody>` must exist — usually by annotating the type itself with `@Json`.

##### Text form { #text-form }

You can use `FormUrlEncoded` as the body argument type and it will be processed as [form data](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        HttpResponseEntity<String> formEncoded(FormUrlEncoded body);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun formEncoded(body: FormUrlEncoded): HttpResponseEntity<String>
    }
    ```

An example of a method call with this form would look like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = someClient.formEncoded(new FormUrlEncoded(
            new FormUrlEncoded.FormPart("name", "Bob"),
            new FormUrlEncoded.FormPart("password", "12345")
    ));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = someClient.formEncoded(
        FormUrlEncoded(
            FormUrlEncoded.FormPart("name", "Bob"),
            FormUrlEncoded.FormPart("password", "12345")
        )
    )
    ```

##### Binary Form { #binary-form }

You can use `FormMultipart` as the body argument type and it will be treated as [binary form](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        HttpResponseEntity<String> formMultipart(FormMultipart body);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun formMultipart(body: FormMultipart): HttpResponseEntity<String>
    }
    ```

An example of a method call with this form would look like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = someClient.formMultipart(new FormMultipart(List.of(
            FormMultipart.data("field1", "some data content"),
            FormMultipart.file("field2", "example1.txt", "text/plain", "some file content".getBytes(StandardCharsets.UTF_8))
    )));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = someClient.formMultipart(
        FormMultipart(
            listOf(
                FormMultipart.data("field1", "some data content"),
                FormMultipart.file(
                    "field2",
                    "example1.txt",
                    "text/plain",
                    "some file content".toByteArray(StandardCharsets.UTF_8)
                )
            )
        )
    )
    ```

`FormMultipart.file(String name, String fileName, HttpBodyOutput content)` sends a part as a stream instead of a byte array.

##### Custom body { #custom-body }

If the body needs to be written in a way different from the standard mechanisms,
it is possible to use a special `HttpClientRequestMapper` interface to implement your custom logic:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record UserBody(String id) {}

        final class UserRequestMapper implements HttpClientRequestMapper<UserBody> {

            @Override
            public HttpBodyOutput apply(UserBody value) {
                return HttpBody.plaintext(value.id());
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        HttpResponseEntity<String> hello(@Mapping(UserRequestMapper.class) UserBody body);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class UserBody(val id: String)

        class UserRequestMapper : HttpClientRequestMapper<UserBody> {

            override fun apply(value: UserBody): HttpBodyOutput {
                return HttpBody.plaintext(value.id)
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun hello(@Mapping(UserRequestMapper::class) body: UserBody): HttpResponseEntity<String>
    }
    ```

**Example: Protobuf Serialization**

Note that `HttpBody.of` takes the content type first and the payload second:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface ProtobufClient {

        final class ProtobufRequestMapper implements HttpClientRequestMapper<MyMessage> {

            @Override
            public HttpBodyOutput apply(MyMessage value) {
                byte[] protobufBytes = value.toByteArray();
                return HttpBody.of("application/x-protobuf", protobufBytes);
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/message")
        void sendMessage(@Mapping(ProtobufRequestMapper.class) MyMessage message);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface ProtobufClient {

        class ProtobufRequestMapper : HttpClientRequestMapper<MyMessage> {

            override fun apply(value: MyMessage): HttpBodyOutput {
                val protobufBytes = value.toByteArray()
                return HttpBody.of("application/x-protobuf", protobufBytes)
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/message")
        fun sendMessage(@Mapping(ProtobufRequestMapper::class) message: MyMessage)
    }
    ```

???+ note "When a mapper needs `@Component`"

    A mapper referenced by `@Mapping` that is `final` (Java) or not `open` (Kotlin) **and** has a single public no-argument constructor
    is instantiated by the generated client itself — it must not be a graph component.
    Any other mapper — one with constructor dependencies such as a `JsonReader<T>`, an open class, or one with several constructors —
    is taken from the dependency container and therefore must be declared as `@Component`.
    Decide by the constructor, not by the annotation above the method.

#### Cookie { #cookie }

`@Cookie` - [Cookie](https://developer.mozilla.org/en-US/docs/Glossary/Cookie) value, the parameter name is specified in `value` or defaults to the method argument name.
Single values, `List<T>`, `Set<T>`, `Collection<T>`, `Map<String, T>`, and a ready `Cookie` object are supported.
Every cookie is written as its own `Cookie` header value in `name=value` form.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello(@Cookie("cookieName") String cookieValue);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(@Cookie("cookieName") cookieValue: String)
    }
    ```

#### Required parameters { #required-parameters }

===! ":fontawesome-brands-java: `Java`"

    By default, all arguments declared in a method are **required** (*NotNull*).

=== ":simple-kotlin: `Kotlin`"

    By default, all arguments declared in a method that do not use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax are considered **required** (*NotNull*).

#### Optional parameters { #optional-parameters }

===! ":fontawesome-brands-java: `Java`"

    If a method argument is optional, that is, it may not exist then,
    `@Nullable` annotation can be used:

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello(@Nullable @Query("queryValue") String queryValue); //(1)!
    }
    ```

    1.  Kora is built on [JSpecify](https://jspecify.dev/), so `org.jspecify.annotations.Nullable` is the recommended annotation; any annotation whose simple name is `Nullable` is accepted.

=== ":simple-kotlin: `Kotlin`"

    It is expected to use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such a parameter as Nullable:

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(@Query("queryValue") queryValue: String?)
    }
    ```

A `null` query parameter, header, or cookie is simply omitted from the request.

### Response { #response }

The section describes the transformation of an HTTP response from a declarative HTTP client.

#### Response body { #response-body }

Kora ships `HttpClientResponseMapper` implementations for a limited set of types, all declared in `HttpClientResponseMapperModule`:

| Return type | Requires |
|---|---|
| `void` | nothing, the body is not read |
| `String` | nothing |
| `byte[]` | nothing |
| `ByteBuffer` | nothing |
| `HttpBodyInput` | nothing, the body stays a stream |
| `T` with `@Json` | a `JsonReader<T>` |
| `HttpResponseEntity<T>` | an `HttpClientResponseMapper<T>` for the payload |
| `Either<T, E>` | an `HttpClientResponseMapper` for each of `T` and `E` |

Any other type needs a mapper of its own, see [Custom response](#custom-response).

##### Json { #json-2 }

If the body is to be read as Json, the `@Json` annotation must be used over the method.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record MyResponse(String name) { }

        @Json //(1)!
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        MyResponse hello();
    }
    ```

    1. Indicates that the response should be read as Json

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class MyResponse(val name: String)

        @Json //(1)!
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(): MyResponse
    }
    ```

    1. Indicates that the response should be read as Json

[Json](json.md) module is required.

##### Response Entity { #response-entity }

If the intention is to read the body and also get the headers and status code of the response,
it is intended to use `HttpResponseEntity`, which is a wrapper over the response body and exposes `code()`, `headers()` and `body()`.

Below is an example similar to the Json example along with the `HttpResponseEntity` wrapper:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record MyResponse(String name) { }

        @Json
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        HttpResponseEntity<MyResponse> hello();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class MyResponse(val name: String)

        @Json
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(): HttpResponseEntity<MyResponse>
    }
    ```

Kora builds the entity mapper itself from the payload mapper, so `HttpResponseEntity<Void>` — the usual shape when only the
status code matters — needs an `HttpClientResponseMapper<Void>` in the graph. There is no built-in one, so declare it as a component
and do **not** point at it with `@Mapping`: with `@Mapping` the mapper would have to produce the whole `HttpResponseEntity<Void>`,
while the framework's template factory expects a payload mapper and wraps it into the entity itself.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient("httpClient.userApi")
    public interface UserApiClient {

        @Component
        final class VoidResponseMapper implements HttpClientResponseMapper<Void> {

            @Override
            public Void apply(HttpClientResponse response) throws IOException {
                try (var body = response.body()) {
                    body.asInputStream().readAllBytes();
                }
                return null;
            }
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        HttpResponseEntity<Void> deleteUser(@Path String userId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient("httpClient.userApi")
    interface UserApiClient {

        @Component
        class VoidResponseMapper : HttpClientResponseMapper<Void> {

            override fun apply(response: HttpClientResponse): Void? {
                response.body().use { body ->
                    body.asInputStream().readAllBytes()
                }
                return null
            }
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        fun deleteUser(@Path userId: String): HttpResponseEntity<Void>
    }
    ```

Without that component the build fails with `No component found for dependency: HttpClientResponseMapper<java.lang.Void>`.

##### Either { #either }

`Either<T, E>` describes a call where a non-successful status code is a normal outcome rather than an exception.
Kora maps a `2xx` response with the mapper of `T` into `Either.Left` and any other status code with the mapper of `E` into `Either.Right`,
and never throws `HttpClientResponseException` for such a method.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record Success(String id) {}

        record Error(String message) {}

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        Either<@Json Success, @Json Error> get(@Path String id); //(1)!
    }
    ```

    1. `@Json` is a type-use annotation here, so the success and error payloads can be tagged independently

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class Success(val id: String)

        data class Error(val message: String)

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        fun get(@Path id: String): Either<@Json Success, @Json Error> //(1)!
    }
    ```

    1. `@Json` is a type-use annotation here, so the success and error payloads can be tagged independently

`Either` exposes `isLeft()` / `isRight()` and the nullable accessors `left()` / `right()`.
`HttpResponseEntity<Either<T, E>>` is supported as well when the status code and headers are also required.

#### Custom response { #custom-response }

If you need to read the response in a different way, you can use the special `HttpClientResponseMapper` interface:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record MyResponse(String name) { }

        final class ResponseMapper implements HttpClientResponseMapper<MyResponse> {

            @Override
            public MyResponse apply(HttpClientResponse response) throws IOException, HttpClientDecoderException {
                try (var is = response.body().asInputStream()) {
                    final byte[] bytes = is.readAllBytes();
                    var body = new String(bytes, StandardCharsets.UTF_8);
                    return new MyResponse(body);
                }
            }
        }

        @Mapping(ResponseMapper.class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        MyResponse hello();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class MyResponse(val name: String)

        class ResponseMapper : HttpClientResponseMapper<MyResponse> {

            override fun apply(response: HttpClientResponse): MyResponse {
                response.body().asInputStream().use {
                    val bytes: ByteArray = it.readAllBytes()
                    val body = String(bytes, StandardCharsets.UTF_8)
                    return MyResponse(body)
                }
            }
        }

        @Mapping(ResponseMapper::class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(): MyResponse
    }
    ```

???+ warning "A `@Mapping` mapper handles every status code"

    When a method declares `@Mapping`, Kora stops checking for a successful status code and hands **every** response to that mapper,
    including `4xx` and `5xx`. Throw from the mapper yourself if a non-successful code must remain an error.
    A `@Tag` on the method only picks which `HttpClientResponseMapper` component is injected — the `2xx` check still applies
    and a non-successful code still throws `HttpClientResponseException`.

**Example: Error Handling in Mapper**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface ApiClient {

        record ApiResponse(String status, String data) {}

        @Component
        final class SafeResponseMapper implements HttpClientResponseMapper<ApiResponse> {

            private final JsonReader<ApiResponse> jsonReader;

            public SafeResponseMapper(JsonReader<ApiResponse> jsonReader) {
                this.jsonReader = jsonReader;
            }

            @Override
            public ApiResponse apply(HttpClientResponse response) throws IOException {
                if (response.code() >= 400) {
                    throw HttpClientResponseException.fromResponse(response);
                }

                try (var body = response.body(); var is = body.asInputStream()) {
                    return jsonReader.read(is);
                }
            }
        }

        @HttpRoute(method = HttpMethod.GET, path = "/api/data")
        @Mapping(SafeResponseMapper.class)
        ApiResponse getData();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface ApiClient {

        data class ApiResponse(val status: String, val data: String)

        @Component
        class SafeResponseMapper(
            private val jsonReader: JsonReader<ApiResponse>
        ) : HttpClientResponseMapper<ApiResponse> {

            override fun apply(response: HttpClientResponse): ApiResponse {
                if (response.code() >= 400) {
                    throw HttpClientResponseException.fromResponse(response)
                }

                response.body().use { body ->
                    body.asInputStream().use { return jsonReader.read(it) }
                }
            }
        }

        @HttpRoute(method = HttpMethod.GET, path = "/api/data")
        @Mapping(SafeResponseMapper::class)
        fun getData(): ApiResponse
    }
    ```

This mapper takes a `JsonReader` in its constructor, so it is a graph component and carries `@Component`.

#### Response Error { #response-error }

By default, when neither a `@Mapping` mapper nor `@ResponseCodeMapper` is specified,
conversion is applied only for `2xx` HTTP response codes.
For all other codes, `HttpClientResponseException` is thrown. It contains the [HTTP response code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status), response body, and response headers.

`Either<T, E>` and `HttpResponseEntity<Either<T, E>>` are the exception to this rule: they map every status code and never throw.

#### Client Exceptions { #client-exceptions }

All standard `HTTP` client exceptions inherit from `HttpClientException`, which is a `RuntimeException`.
This lets you catch a specific error type or all client errors with one common type:

```java
try {
    client.getUser("123");
} catch (HttpClientResponseException e) {
    var code = e.getCode();
    var headers = e.getHeaders();
    var body = e.getBytes();
} catch (HttpClientException e) {
    throw e;
}
```

Main exception types:

* `HttpClientResponseException` — response was received, but its code was not handled as successful. Contains `getCode()`, `getHeaders()`, and `getBytes()`.
* `HttpClientTimeoutException` — request, connection, or read timeout expired.
* `HttpClientConnectionException` — error while establishing or maintaining a connection to the remote host.
* `HttpClientEncoderException` — error while converting a user value into a request body.
* `HttpClientDecoderException` — error while converting a response body into a user type.
* `HttpClientUnknownException` — other transport client error that did not match a more specific category.

`HttpClientResponseException` is created by `HttpClientResponseException.fromResponse(response)` after reading the response body.
If the whole body is already buffered it is captured in full; otherwise only the first `4096` bytes are read into `getBytes()`
so that a failing call never has to buffer an arbitrarily large error page.

#### Conversion by Code { #conversion-by-code }

If specific conversions are required depending on the [HTTP status code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) of the response, you can use the `@ResponseCodeMapper` annotation to specify a
correspondence between the HTTP status code and the `HttpClientResponseMapper` resolver.

You can also use `ResponseCodeMapper.DEFAULT` to define default behavior for all unlisted HTTP codes.
If `mapper` is specified for a code, that particular `HttpClientResponseMapper` is used.
If `type` is specified, Kora selects a response mapper for that type and then casts the result to the method return type.
This is useful for closed response hierarchies where different HTTP statuses correspond to different result subtypes.
If neither is specified, Kora asks the graph for an `HttpClientResponseMapper` of the method return type
(`HttpClientResponseMapper<Void>` for a `void` method).
A status code that is not listed and has no `DEFAULT` entry still throws `HttpClientResponseException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record UserResponse(UserResponse.Payload payload, UserResponse.Error error) {

            public record Error(int code, String message) {}

            public record Payload(String message) {}
        }

        @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = ResponseErrorMapper.class)
        @ResponseCodeMapper(code = 200, mapper = ResponseSuccessMapper.class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        UserResponse hello();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class UserResponse(val payload: Payload?, val error: Error?) {

            data class Error(val code: Int, val message: String)

            data class Payload(val message: String)
        }

        @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = ResponseErrorMapper::class)
        @ResponseCodeMapper(code = 200, mapper = ResponseSuccessMapper::class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(): UserResponse
    }
    ```

In the example above, `ResponseSuccessMapper` will be used for status code `200`,
and for all other status codes the `ResponseErrorMapper` will be used.

Example with the `type` parameter:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        sealed interface UserResponse permits Success, Error {}

        record Success(String id) implements UserResponse {}

        record Error(String message) implements UserResponse {}

        @Json
        @ResponseCodeMapper(code = 200, type = Success.class)
        @ResponseCodeMapper(code = 404, type = Error.class)
        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        UserResponse get(@Path String id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        sealed interface UserResponse

        data class Success(val id: String) : UserResponse

        data class Error(val message: String) : UserResponse

        @Json
        @ResponseCodeMapper(code = 200, type = Success::class)
        @ResponseCodeMapper(code = 404, type = Error::class)
        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        fun get(@Path id: String): UserResponse
    }
    ```

If the mapped `type` is not assignable to the method return type, Kora treats the mapper result as an exception and throws it
instead of returning it — that is how an error branch can be modelled as a thrown exception for a specific status code.

### Signatures { #signatures }

Declarative `HTTP` client methods are **blocking**:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `void myMethod()`

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `myMethod(): T`

???+ warning "Asynchronous signatures are not supported"

    In Kotlin a `suspend` client method is a compile-time error: *Suspend methods are not supported by the HTTP client generator*.
    In Java a `CompletionStage<T>` or `Mono<T>` return type only produces the warning *Method has async signature, this might not work correctly* —
    the generated code still performs a blocking call and the type will not be satisfied.

    Run independent calls in parallel with virtual threads instead, for example with `StructuredTaskScope`:

    ```java
    try (var scope = StructuredTaskScope.open(StructuredTaskScope.Joiner.<Object>awaitAllSuccessfulOrThrow())) {
        var profile = scope.fork(() -> profileHttpClient.getProfile(userId));
        var recommendations = scope.fork(() -> recommendationsHttpClient.getForUser(userId));
        scope.join();
        return new Dashboard(profile.get(), recommendations.get());
    }
    ```

## Interceptors { #interceptors }

You can create interceptors to change behavior or create additional behavior using the `HttpClientInterceptor` interface.
Interceptors are attached with the `@InterceptWith` annotation, either to a specific method or to the whole `@HttpClient` interface.

```java
public interface HttpClientInterceptor {

    HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request) throws Exception; //(1)!

    interface InterceptChain {
        HttpClientResponse process(HttpClientRequest request) throws Exception; //(2)!
    }
}
```

1. Called for every request of the intercepted method
2. Passes the request further down the chain and returns the response

The request is immutable, so a modified request is produced with `request.toBuilder()`.

**Method-level interceptor:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @Component
        final class MethodInterceptor implements HttpClientInterceptor {

            private final Component1 component1;

            public MethodInterceptor(Component1 component1) {
                this.component1 = component1;
            }

            @Override
            public HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request) throws Exception {
                component1.doSomething();
                return chain.process(request);
            }
        }

        @InterceptWith(MethodInterceptor.class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @Component
        class MethodInterceptor(val component1: Component1) : HttpClientInterceptor {

            override fun processRequest(
                chain: HttpClientInterceptor.InterceptChain,
                request: HttpClientRequest
            ): HttpClientResponse {
                component1.doSomething()
                return chain.process(request)
            }
        }

        @InterceptWith(MethodInterceptor::class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

An interceptor is taken from the dependency container, so it follows the same rule as a mapper:
it needs `@Component` when it has constructor dependencies.
`@InterceptWith` also accepts a `tag` attribute to pick a tagged interceptor implementation.

**Example: adding a header**

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class RequestIdInterceptor implements HttpClientInterceptor {

        @Override
        public HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request) throws Exception {
            var modified = request.toBuilder()
                    .header("x-request-id", UUID.randomUUID().toString())
                    .build();
            return chain.process(modified);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RequestIdInterceptor : HttpClientInterceptor {

        override fun processRequest(
            chain: HttpClientInterceptor.InterceptChain,
            request: HttpClientRequest
        ): HttpClientResponse {
            val modified = request.toBuilder()
                .header("x-request-id", UUID.randomUUID().toString())
                .build()
            return chain.process(modified)
        }
    }
    ```

**Interceptor execution order:**

Interceptors declared on the client run before interceptors declared on the method,
and within one element they run in declaration order. Each interceptor can:

- Modify the request before sending
- Call the next interceptor in the chain (`chain.process(request)`)
- Modify or inspect the response after receiving
- Throw an exception to break the chain

```
Request  → Client interceptors → Method interceptors → Telemetry → HTTP Server
Response ← Client interceptors ← Method interceptors ← Telemetry ← HTTP Server
```

### Client interceptor { #interceptor-global }

If the interceptor must be applied to all methods of a client, `@InterceptWith` is placed on the interface:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    @InterceptWith(ClientInterceptor.class) //(1)!
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        void hello();

        @HttpRoute(method = HttpMethod.POST, path = "/world")
        void world();
    }
    ```

    1. Applied to every method of this client

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    @InterceptWith(ClientInterceptor::class) //(1)!
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        fun hello()

        @HttpRoute(method = HttpMethod.POST, path = "/world")
        fun world()
    }
    ```

    1. Applied to every method of this client

If interceptors are specified on both the client and the method, both interceptor sets are applied for that call.
There is no application-wide registry of HTTP client interceptors: an interceptor only applies where `@InterceptWith` names it.

### Authorization { #authorization }

Kora provides out-of-the-box interceptors that can be used for [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/) authorization.

#### Basic { #basic }

You need to configure an interceptor and configuration for [Basic](https://swagger.io/docs/specification/authentication/basic-authentication/) authorization:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface BasicAuthModule {

        @ConfigSource("openapiAuth.basicAuth")
        interface BasicAuthConfig {

            String username();

            String password();
        }

        default BasicAuthHttpClientInterceptor basicAuther(BasicAuthConfig config) {
            return new BasicAuthHttpClientInterceptor(config.username(), config.password());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface BasicAuthModule {

        @ConfigSource("openapiAuth.basicAuth")
        interface BasicAuthConfig {

            fun username(): String

            fun password(): String
        }

        fun basicAuther(config: BasicAuthConfig): BasicAuthHttpClientInterceptor {
            return BasicAuthHttpClientInterceptor(config.username(), config.password())
        }
    }
    ```

The two-argument constructor wraps the credentials into a `BasicAuthHttpClientTokenProvider`.
You can also provide your own `HttpClientTokenProvider` implementation in the constructor if rules for getting secrets are different.

Then add the interceptor for the entire HTTP client or specific methods.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @InterceptWith(BasicAuthHttpClientInterceptor.class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @InterceptWith(BasicAuthHttpClientInterceptor::class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

#### ApiKey { #apikey }

You need to configure an interceptor and configuration for [ApiKey](https://swagger.io/docs/specification/authentication/api-keys/) authorization.
`ApiKeyLocation` supports `HEADER`, `QUERY` and `COOKIE`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ApiKeyAuthModule {

        @ConfigSource("openapiAuth.apiKeyAuth")
        interface ApiKeyAuthConfig {

            String apiKey();
        }

        default ApiKeyHttpClientInterceptor apiKeyAuther(ApiKeyAuthConfig config) {
            return new ApiKeyHttpClientInterceptor(ApiKeyLocation.HEADER, "X-API-KEY", config.apiKey());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ApiKeyAuthModule {

        @ConfigSource("openapiAuth.apiKeyAuth")
        interface ApiKeyAuthConfig {

            fun apiKey(): String
        }

        fun apiKeyAuther(config: ApiKeyAuthConfig): ApiKeyHttpClientInterceptor {
            return ApiKeyHttpClientInterceptor(ApiKeyLocation.HEADER, "X-API-KEY", config.apiKey())
        }
    }
    ```

Then add the interceptor for the entire HTTP client or specific methods.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @InterceptWith(ApiKeyHttpClientInterceptor.class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @InterceptWith(ApiKeyHttpClientInterceptor::class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

#### Bearer { #bearer }

You need to configure an interceptor for [Bearer](https://swagger.io/docs/specification/authentication/bearer-authentication/) authorization:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface BearerAuthModule {

        default BearerAuthHttpClientInterceptor bearerAuther(HttpClientTokenProvider tokenProvider) {
            return new BearerAuthHttpClientInterceptor(tokenProvider);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface BearerAuthModule {

        fun bearerAuther(tokenProvider: HttpClientTokenProvider): BearerAuthHttpClientInterceptor {
            return BearerAuthHttpClientInterceptor(tokenProvider)
        }
    }
    ```

You will need to implement the `Bearer` token provisioning yourself using your custom `HttpClientTokenProvider` implementation,
or use the constructor that accepts a static `Bearer Token`.

```java
public interface HttpClientTokenProvider {

    @Nullable
    String getToken(HttpClientRequest request); //(1)!
}
```

1. Returning `null` leaves the request unchanged and no `Authorization` header is added

Then add the interceptor for the entire HTTP client or specific methods.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @InterceptWith(BearerAuthHttpClientInterceptor.class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @InterceptWith(BearerAuthHttpClientInterceptor::class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

#### OAuth { #oauth }

Authorization by [OAuth](https://swagger.io/docs/specification/authentication/oauth2/) is similar to [Bearer](#bearer),
you need to implement `HttpClientTokenProvider` yourself and put it in dependency container.

#### HttpClientTokenProvider { #token-provider }

`HttpClientTokenProvider` — interface for providing authorization tokens dynamically.
Used when the token needs to be refreshed or obtained from an external source (e.g., an OAuth2 token endpoint).
The method is blocking, so the token can simply be fetched inline.

**Implementation example:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyTokenProvider implements HttpClientTokenProvider {

        private final OAuthClient oauthClient;
        private volatile String cachedToken;
        private volatile long tokenExpiry;

        public MyTokenProvider(OAuthClient oauthClient) {
            this.oauthClient = oauthClient;
        }

        @Override
        public String getToken(HttpClientRequest request) {
            if (cachedToken != null && System.currentTimeMillis() < tokenExpiry) {
                return cachedToken;
            }

            var response = oauthClient.refreshToken();
            this.cachedToken = response.accessToken();
            this.tokenExpiry = System.currentTimeMillis() + response.expiresIn() * 1000;
            return this.cachedToken;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyTokenProvider(
        private val oauthClient: OAuthClient
    ) : HttpClientTokenProvider {

        @Volatile
        private var cachedToken: String? = null

        @Volatile
        private var tokenExpiry: Long = 0

        override fun getToken(request: HttpClientRequest): String? {
            val token = cachedToken
            if (token != null && System.currentTimeMillis() < tokenExpiry) {
                return token
            }

            val response = oauthClient.refreshToken()
            cachedToken = response.accessToken()
            tokenExpiry = System.currentTimeMillis() + response.expiresIn() * 1000
            return cachedToken
        }
    }
    ```

**Usage with BearerAuthHttpClientInterceptor:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface AuthModule {

        default BearerAuthHttpClientInterceptor bearerAuthInterceptor(HttpClientTokenProvider tokenProvider) {
            return new BearerAuthHttpClientInterceptor(tokenProvider);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface AuthModule {

        fun bearerAuthInterceptor(tokenProvider: HttpClientTokenProvider): BearerAuthHttpClientInterceptor {
            return BearerAuthHttpClientInterceptor(tokenProvider)
        }
    }
    ```

The [OpenAPI generator](openapi-codegen.md) expects the same interface, tagged with the generated `ApiSecurity` marker class.

## Exception handling { #exception-handling }

Various exceptions may occur during HTTP requests. All exceptions inherit from the base `HttpClientException`,
which is an unchecked `RuntimeException` living in `io.koraframework.http.client.common.exception`.

**Exception hierarchy:**

```
HttpClientException
├── HttpClientTimeoutException
├── HttpClientConnectionException
├── HttpClientResponseException
├── HttpClientEncoderException
├── HttpClientDecoderException
└── HttpClientUnknownException
```

**Handling example:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final SomeClient client;

        public SomeService(SomeClient client) {
            this.client = client;
        }

        public void call() {
            try {
                client.hello();
            } catch (HttpClientTimeoutException e) {
                // Timeout: log, retry
            } catch (HttpClientConnectionException e) {
                // Connection error: check service availability
            } catch (HttpClientResponseException e) {
                // Response error: code, body, headers
                int code = e.getCode();
                byte[] body = e.getBytes();
                var headers = e.getHeaders();
            } catch (HttpClientEncoderException e) {
                // Serialization error: validate data
            } catch (HttpClientDecoderException e) {
                // Deserialization error: log
            } catch (HttpClientUnknownException e) {
                // Unknown error: e.getCause()
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(
        private val client: SomeClient
    ) {
        fun call() {
            try {
                client.hello()
            } catch (e: HttpClientTimeoutException) {
                // Timeout: log, retry
            } catch (e: HttpClientConnectionException) {
                // Connection error: check service availability
            } catch (e: HttpClientResponseException) {
                // Response error: code, body, headers
                val code = e.code
                val body = e.bytes
                val headers = e.headers
            } catch (e: HttpClientEncoderException) {
                // Serialization error: validate data
            } catch (e: HttpClientDecoderException) {
                // Deserialization error: log
            } catch (e: HttpClientUnknownException) {
                // Unknown error: e.cause
            }
        }
    }
    ```

#### Timeout Exception { #timeout-exception }

Thrown when the request exceeds the configured timeout (`requestTimeout`, `connectTimeout` or `readTimeout`).

**Causes:**

- Server doesn't respond within `requestTimeout`
- Connection establishment timeout exceeded (`connectTimeout`)
- Response read timeout exceeded (`readTimeout`)
- Network delays

**Recommendations:**

- Configure appropriate timeouts in settings, per client and per method
- Implement [retry](resilient.md) logic for temporary failures
- Use a [circuit breaker](resilient.md) to protect against cascading failures

#### Connection Exception { #connection-exception }

Thrown when connection to the server cannot be established.

**Causes:**

- DNS resolution failure
- Server unavailable (port closed, firewall)
- Connection refused
- SSL/TLS handshake failed

**Recommendations:**

- Check service availability (health check)
- Use fallback to a backup service
- Configure retry with exponential backoff

#### Response Exception { #response-exception }

Thrown when the server returns an HTTP status code outside `2xx` and the method does not declare its own mapper
via `@Mapping` or `@ResponseCodeMapper`, and does not return `Either`.

**Available data:**

- `getCode()` — HTTP status code (400, 404, 500, etc.)
- `getBytes()` — response body, truncated to `4096` bytes when the body was not fully buffered
- `getHeaders()` — response headers

**Recommendations:**

- Use `@ResponseCodeMapper` for custom status handling
- Use `Either<T, E>` when a non-successful code is a normal outcome
- Log the code and body for debugging
- Distinguish between client (4xx) and server (5xx) errors

#### Request Encoder Exception { #encoder-exception }

Thrown when an error occurs during request body serialization: the `HttpClientRequestMapper` of the body threw.

**Causes:**

- JSON/binary serialization error
- Invalid data in the request object
- The mapper itself failed on the value

**Recommendations:**

- Validate data before sending
- Check that the body type carries `@Json` and has a `JsonWriter`
- Log the original exception in `cause`

#### Response Decoder Exception { #decoder-exception }

Thrown when an error occurs during response body deserialization: the `HttpClientResponseMapper` of the method threw.

**Causes:**

- Invalid JSON in the server response
- Schema mismatch (server returned unexpected fields)
- The stream was closed or truncated

**Recommendations:**

- Check API version compatibility
- Log the response body for debugging
- Use `@ResponseCodeMapper` to handle differently shaped error payloads

#### Unknown Exception { #unknown-exception }

Thrown when an error occurs that doesn't fit other categories, including any checked exception escaping the transport.

**Available data:**

- `getCause()` — original exception

**Recommendations:**

- Always log `cause` for diagnostics
- Check HTTP client logs at DEBUG/TRACE level
- Report a bug if the exception is reproducible

## Client imperative { #client-imperative }

The base client represents the `HttpClient` interface and is available for injection from any transport module:

```java
public interface HttpClient {

    HttpClientResponse execute(HttpClientRequest request) throws HttpClientException; //(1)!

    default HttpClient with(HttpClientInterceptor interceptor); //(2)!
}
```

1. Executes the request and returns the response; the response must be closed
2. Returns a new `HttpClient` view with an extra interceptor applied on top

The response holds an open body stream, so it must be closed — use it inside a `try`-with-resources block:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var request = HttpClientRequest.post("http://localhost:8090/pets/{petId}")
            .pathParam("petId", "1")
            .queryParam("page", 1)
            .header("token", "12345")
            .body(HttpBody.plaintext("refresh"))
            .build();

    try (var response = httpClient.execute(request)) {
        var code = response.code();
        var body = new String(response.body().asInputStream().readAllBytes(), StandardCharsets.UTF_8);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.post("http://localhost:8090/pets/{petId}")
        .pathParam("petId", "1")
        .queryParam("page", 1)
        .header("token", "12345")
        .body(HttpBody.plaintext("refresh"))
        .build()

    httpClient.execute(request).use { response ->
        val code = response.code()
        val body = String(response.body().asInputStream().readAllBytes(), StandardCharsets.UTF_8)
    }
    ```

### HttpClientRequestBuilder { #request-builder }

`HttpClientRequestBuilder` allows building HTTP requests manually. A builder is obtained from one of the
`HttpClientRequest` factory methods — `get`, `head`, `post`, `put`, `delete`, `connect`, `options`, `trace`, `patch`,
or `of(method, uriTemplate)` — and an existing request can be turned back into a builder with `request.toBuilder()`.

| Method | Description |
|---|---|
| `pathParam(String name, String \| int \| long \| UUID value)` | Substitutes a `{name}` placeholder of the URI template |
| `queryParam(String name)` | Adds a query parameter without a value |
| `queryParam(String name, String \| int \| long \| boolean \| UUID \| Collection<?> value)` | Adds a query parameter value |
| `queryParamRemove(String name)` | Removes all values of a query parameter |
| `header(String name, String \| List<String> value)` | Sets a request header |
| `headerRemove(String name)` | Removes a request header |
| `requestTimeout(Duration \| int millis)` | Overrides the request timeout for this request |
| `body(HttpBodyOutput body)` | Sets the request body |
| `build()` | Builds the immutable `HttpClientRequest` |

===! ":fontawesome-brands-java: `Java`"

    ```java
    HttpClientRequest request = HttpClientRequest.of("POST", "http://localhost:8090/pets/{petId}")
            .pathParam("petId", "1")
            .queryParam("page", 1)
            .header("token", "12345")
            .requestTimeout(Duration.ofSeconds(5))
            .body(HttpBody.plaintext("refresh"))
            .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.of("POST", "http://localhost:8090/pets/{petId}")
        .pathParam("petId", "1")
        .queryParam("page", 1)
        .header("token", "12345")
        .requestTimeout(Duration.ofSeconds(5))
        .body(HttpBody.plaintext("refresh"))
        .build()
    ```

The built `HttpClientRequest` exposes `method()`, `uri()`, `uriTemplate()`, `headers()`, `body()` and `requestTimeout()`.
`uriTemplate()` is what telemetry uses as the operation name, which is why templated paths keep metrics and spans low-cardinality.

### UriQueryBuilder { #uri-query-builder }

`UriQueryBuilder` is the low-level helper that the generated declarative clients use to assemble a query string.
It appends parameters in order and takes care of the `?` and `&` separators:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var query = new UriQueryBuilder(true, false); //(1)!
    query.add("page", "1"); //(2)!
    query.add("sort", "name age"); //(3)!
    query.add("debug"); //(4)!

    String uri = "/api/users" + query.build();
    // /api/users?page=1&sort=name+age&debug
    ```

    1. First argument: start the string with `?`; second: start it with `&` because the base path already ends with a query parameter
    2. Adds a `name=value` pair, both parts are URL-encoded
    3. Values are URL-encoded, so the space becomes `+`
    4. Adds a parameter without a value

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val query = UriQueryBuilder(true, false) //(1)!
    query.add("page", "1") //(2)!
    query.add("sort", "name age") //(3)!
    query.add("debug") //(4)!

    val uri = "/api/users" + query.build()
    // /api/users?page=1&sort=name+age&debug
    ```

    1. First argument: start the string with `?`; second: start it with `&` because the base path already ends with a query parameter
    2. Adds a `name=value` pair, both parts are URL-encoded
    3. Values are URL-encoded, so the space becomes `+`
    4. Adds a parameter without a value

`unsafeAdd` variants append already-encoded values as-is. A `null` value is skipped entirely.

### HttpBodyInput { #http-body-input }

`HttpBodyInput` describes the response body. It extends `HttpBody` and is `Closeable`.

| Method | Returns | Description |
|--------|---------|-------------|
| `asInputStream()` | `InputStream` | Reads the body as a stream |
| `getFullContentIfAvailable()` | `ByteBuffer` | Returns the whole body if it is already buffered, otherwise `null` |
| `contentLength()` | `long` | Body length, `-1` when unknown |
| `contentType()` | `String` | Value of the `Content-Type` header, may be `null` |
| `close()` | `void` | Releases the underlying connection resources |

The outgoing counterpart is `HttpBodyOutput`, built with `HttpBody.plaintext(...)`, `HttpBody.json(...)`,
`HttpBody.octetStream(...)`, `HttpBody.of(contentType, content)`, or `HttpBodyOutput.of(contentType, inputStream)`
for streaming a body that is not fully in memory.

### HttpClientResponse { #http-client-response }

`HttpClientResponse` is an interface that represents the HTTP response from the server. It is `Closeable`.

| Method | Returns | Description |
|--------|---------|-------------|
| `code()` | `int` | HTTP status code (200, 404, 500, etc.) |
| `headers()` | `HttpHeaders` | Response headers |
| `body()` | `HttpBodyInput` | Response body |
| `close()` | `void` | Closes the response and releases the connection |

### HttpHeaders { #http-headers-imperative }

`HttpHeaders` provides access to request and response headers. Header names are lower-cased and lookups are case-insensitive.

| Method | Returns | Description |
|--------|---------|-------------|
| `getFirst(String name)` | `String` | First value of the header or `null` |
| `getAll(String name)` | `List<String>` | All values of the header or `null` |
| `has(String name)` | `boolean` | Whether the header is present |
| `names()` | `Set<String>` | All header names |
| `size()` | `int` | Number of headers |
| `isEmpty()` | `boolean` | Whether there are no headers |
| `toMutable()` | `MutableHttpHeaders` | Mutable copy |

**Reading headers:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    var request = HttpClientRequest.get("http://localhost:8090/api/data").build();

    try (var response = httpClient.execute(request)) {
        HttpHeaders headers = response.headers();
        String contentType = headers.getFirst("content-type");
        List<String> allValues = headers.getAll("x-custom-header");
        boolean hasHeader = headers.has("authorization");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.get("http://localhost:8090/api/data").build()

    httpClient.execute(request).use { response ->
        val headers = response.headers()
        val contentType = headers.getFirst("content-type")
        val allValues = headers.getAll("x-custom-header")
        val hasHeader = headers.has("authorization")
    }
    ```

**Building headers:**

`HttpHeaders.of(...)` returns a `MutableHttpHeaders` which supports `set`, `add` and `remove`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    MutableHttpHeaders headers = HttpHeaders.of();
    headers.add("authorization", "Bearer token123");
    headers.add("x-custom-header", "value");
    headers.set("content-type", "application/json");

    var request = HttpClientRequest.post("http://localhost:8090/api/data")
            .header("authorization", headers.getFirst("authorization"))
            .body(HttpBody.json("{}"))
            .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val headers = HttpHeaders.of()
    headers.add("authorization", "Bearer token123")
    headers.add("x-custom-header", "value")
    headers.set("content-type", "application/json")

    val request = HttpClientRequest.post("http://localhost:8090/api/data")
        .header("authorization", headers.getFirst("authorization")!!)
        .body(HttpBody.json("{}"))
        .build()
    ```

A ready `HttpHeaders` object can also be passed straight to a declarative method with `@Header`, see [Header](#header).

### Cookies { #cookies-imperative }

Cookies are ordinary headers: an outgoing cookie is a `Cookie` header, an incoming one is a `Set-Cookie` header.
`Cookie` describes a single cookie and `Cookies` is a utility class that parses and renders them.

**Sending a cookie:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    var request = HttpClientRequest.get("http://localhost:8090/api/profile")
            .header("Cookie", Cookie.of("SESSIONID", "12345").toValue())
            .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.get("http://localhost:8090/api/profile")
        .header("Cookie", Cookie.of("SESSIONID", "12345").toValue())
        .build()
    ```

**Reading cookies from a response:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    try (var response = httpClient.execute(request)) {
        var setCookies = response.headers().getAll("set-cookie");
        if (setCookies != null) {
            for (var header : setCookies) {
                Cookie cookie = Cookies.parseSetCookieHeader(header);
                String name = cookie.name();
                String value = cookie.value();
                String domain = cookie.domain();
                String path = cookie.path();
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    httpClient.execute(request).use { response ->
        val setCookies = response.headers().getAll("set-cookie")
        if (setCookies != null) {
            for (header in setCookies) {
                val cookie = Cookies.parseSetCookieHeader(header)
                val name = cookie.name()
                val value = cookie.value()
                val domain = cookie.domain()
                val path = cookie.path()
            }
        }
    }
    ```

For a declarative client, use the [`@Cookie`](#cookie) parameter annotation instead of building the header by hand.

## Telemetry { #telemetry }

HTTP Client telemetry is installed as an interceptor: `DeclarativeHttpClientConfig` asks the `HttpClientTelemetryFactory`
for an `HttpClientTelemetry` per client method and wraps the transport in a `TelemetryInterceptor`.
Extension points live in `io.koraframework.http.client.common.telemetry`.

For each HTTP request `HttpClientTelemetry.observe(request)` creates an `HttpClientObservation`,
which sees the request via `observeRequest`, the response via `observeResponse`, a failure via `observeError`,
and is always closed with `end()`.

The default factory `DefaultHttpClientTelemetryFactory` combines three optional pieces, each replaceable by declaring
a component of the corresponding type:

- `DefaultHttpClientLoggerFactory` builds the request/response loggers;
- `DefaultHttpClientMetricsFactory` builds the metrics recorder;
- `DefaultHttpClientBodyConverter` turns a captured body into the string that is written to the log.

When logging, metrics and tracing are all disabled for a client, the factory returns a no-op telemetry and no wrapper is installed at all.

**Logging.** Two loggers are created per client method, named after the client class, the method, and the direction:
`com.example.SomeClient.hello.request` and `com.example.SomeClient.hello.response`.
Their level decides how much is written: `INFO` logs the operation only, `DEBUG` adds query parameters and headers,
`TRACE` adds the body. Masked query parameters and headers are replaced with the configured `mask`,
and a body larger than `maxRequestBodyLogSize` / `maxResponseBodyLogSize` is skipped with a warning.
See [Logging](logging-slf4j.md) for the logger configuration itself.

**Metrics.** The default recorder writes the `http.client.request.duration` timer with the SLO buckets from
`telemetry.metrics.slo`, tagged with the HTTP method, status code, route, server address and error type.
See [Metrics Reference](metrics.md#http-client).

**Tracing.** A span named `<METHOD> <path template>` is created per request with the OpenTelemetry HTTP semantic
attributes; `telemetry.tracing.pathFull` decides between the `url.full` and `url.path` attributes.
See [Tracing](tracing.md).
