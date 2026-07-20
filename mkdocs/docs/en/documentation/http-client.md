---
description: "Explains Kora HTTP clients, OkHttp, AsyncHttpClient, Java native client, declarative client annotations, request and response mapping, interceptors, and authorization. Use when working with @HttpClient, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora HTTP clients, OkHttp, AsyncHttpClient, Java native client, declarative client annotations, request and response mapping, interceptors, and authorization; key triggers include @HttpClient, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith, HttpClientModule, OkHttp."
---

The `HTTP client` module describes outgoing HTTP calls: transport implementation, request mapping, response mapping,
telemetry, and interceptors. In Kora, clients can be described declaratively with `@HttpClient` and `@HttpRoute`,
or used imperatively through the common `HttpClient` interface when a request must be built in code.

The declarative approach is suitable for most integrations with external services: the method contract becomes the remote call contract,
and Kora creates the implementation at compile time without using `Reflection` at runtime. The imperative approach is useful for low-level
or dynamic scenarios where path, headers, query parameters, or body are easier to assemble manually.

???+ tip "Recommendation"

    **We recommend** using an approach where the `OpenAPI` file is the primary contract
    and clients are created from it using the generator.
    This approach allows you to achieve consistency between the consumer and owner of the contract
    and update the API faster when the contract changes by replacing the contract file.
    For more information about the generator, see the [section on generating from OpenAPI](openapi-codegen.md).

For a step-by-step walkthrough before the reference details, see [HTTP Client](../guides/http-client.md) and [Advanced HTTP Client](../guides/http-client-advanced.md).

## OkHttp { #okhttp }

HTTP client implementation based on [OkHttp](https://github.com/square/okhttp) library.
Please note that the implementation is written in Kotlin and uses appropriate dependencies.

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:http-client-ok"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends OkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:http-client-ok")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : OkHttpClientModule
    ```

### Configuration { #configuration }

Example of the complete configuration described in the `OkHttpClientConfig`
and `HttpClientConfig` classes (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        ok {
            followRedirects = true //(1)!
            httpVersion = "HTTP_1_1" //(2)!
            retryOnConnectionFailure = true //(3)!
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
        telemetry {
            logging {
                enabled = false //(12)!
                mask = "***" //(13)!
                maskQueries = [ ] //(14)!
                maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(15)!
                pathTemplate = true //(16)!
            }
            metrics {
                enabled = true //(17)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(18)!
                tags = { // (19)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(20)!
                attributes = { // (21)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1. Whether to follow [HTTP redirects](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections) (default: `true`)
    2. Maximum `HTTP` protocol version to use, available values: `HTTP_1_1` / `HTTP_2` / `HTTP_3` (default: `HTTP_1_1`)
    3. Whether to retry a request after a connection failure; this can affect the maximum connection establishment time (default: `true`)
    4. Maximum time to establish a connection (default: `5s`)
    5. Maximum time to read a response (default: `2m`)
    6. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
    7. Proxy host (`required`, default not specified)
    8. Proxy port (`required`, default not specified)
    9. Proxy user (default not specified, optional)
    10. Proxy password (default not specified, optional)
    11. Hosts to exclude from proxying (default not specified, optional)
    12. Enables module logging (default: `false`)
    13. Mask used to hide specified headers and request or response parameters (default: `***`)
    14. List of request parameters to hide (default: `[]`)
    15. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    16. Whether to use the request path template in logging; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional)
    17. Enables module metrics (default: `true`)
    18. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    19. Configures metric tags (default: `{}`)
    20. Enables module tracing (default: `true`)
    21. Configures tracing attributes (default: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      ok:
        followRedirects: true #(1)!
        httpVersion: "HTTP_1_1" #(2)!
        retryOnConnectionFailure: true #(3)!
      connectTimeout: "5s" #(4)!
      readTimeout: "2m" #(5)!
      useEnvProxy: false #(6)!
      proxy:
        host: "localhost" #(7)!
        port: 8090  #(8)!
        user: "user"  #(9)!
        password: "password" #(10)!
        nonProxyHosts: [ "host1", "host2" ] #(11)!
      telemetry:
        logging:
          enabled: false #(12)!
          mask: "***" #(13)!
          maskQueries: [ ] #(14)!
          maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(15)!
          pathTemplate: true #(16)!
        metrics:
          enabled: true #(17)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(18)!
          tags: #(19)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(20)!
          attributes: #(21)!
            key1: value1
            key2: value2
    ```

    1. Whether to follow [HTTP redirects](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections) (default: `true`)
    2. Maximum `HTTP` protocol version to use, available values: `HTTP_1_1` / `HTTP_2` / `HTTP_3` (default: `HTTP_1_1`)
    3. Whether to retry a request after a connection failure; this can affect the maximum connection establishment time (default: `true`)
    4. Maximum time to establish a connection (default: `5s`)
    5. Maximum time to read a response (default: `2m`)
    6. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
    7. Proxy host (`required`, default not specified)
    8. Proxy port (`required`, default not specified)
    9. Proxy user (default not specified, optional)
    10. Proxy password (default not specified, optional)
    11. Hosts to exclude from proxying (default not specified, optional)
    12. Enables module logging (default: `false`)
    13. Mask used to hide specified headers and request or response parameters (default: `***`)
    14. List of request parameters to hide (default: `[]`)
    15. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    16. Whether to use the request path template in logging; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional)
    17. Enables module metrics (default: `true`)
    18. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    19. Configures metric tags (default: `{}`)
    20. Enables module tracing (default: `true`)
    21. Configures tracing attributes (default: `{}`)

Module metrics are described in the [Metrics Reference](metrics.md#http-client) section.

#### Configurer { #configurer }

Example of how to configure OkHttp client builder, `OkHttpConfigurer` must be available as component:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeConfigurer implements OkHttpConfigurer {

        @Override
        public OkHttpClient.Builder configure(OkHttpClient.Builder builder) {
            return builder;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeConfigurer : OkHttpConfigurer {
        fun configure(builder: Builder): Builder {
            return builder
        }
    }
    ```

## AsyncHttpClient { #asynchttpclient }

HTTP client implementation based on the [Async HTTP Client](https://github.com/AsyncHttpClient/async-http-client) library.

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:http-client-async"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends AsyncHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:http-client-async")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : AsyncHttpClientModule
    ```

The `HttpClient` interface implementation is `AsyncHttpClient` and is available for manual implementation.

### Configuration { #configuration-2 }

Example of the complete configuration described in the `AsyncHttpClientConfig` 
and `HttpClientConfig` classes (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        async {
            followRedirects = true //(1)!
        }
        connectTimeout = "5s" //(2)!
        readTimeout = "2m" //(3)!
        useEnvProxy = false //(4)!
        proxy {
            host = "localhost"  //(5)!
            port = 8090  //(6)!
            user = "user"  //(7)!
            password = "password"  //(8)!
            nonProxyHosts = [ "host1", "host2" ]  //(9)!
        }
        telemetry {
            logging {
                enabled = false //(10)!
                mask = "***" //(11)!
                maskQueries = [ ] //(12)!
                maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(13)!
                pathTemplate = true //(14)!
            }
            metrics {
                enabled = true //(15)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(16)!
                tags = { // (17)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(18)!
                attributes = { // (19)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1. Whether to follow [HTTP redirects](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections) (default: `true`)
    2. Maximum time to establish a connection (default: `5s`)
    3. Maximum time to read a response (default: `2m`)
    4. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
    5. Proxy host (`required`, default not specified)
    6. Proxy port (`required`, default not specified)
    7. Proxy user (default not specified, optional)
    8. Proxy password (default not specified, optional)
    9. Hosts to exclude from proxying (default not specified, optional)
    10. Enables module logging (default: `false`)
    11. Mask used to hide specified headers and request or response parameters (default: `***`)
    12. List of request parameters to hide (default: `[]`)
    13. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    14. Whether to use the request path template in logging; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional)
    15. Enables module metrics (default: `true`)
    16. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    17. Configures metric tags (default: `{}`)
    18. Enables module tracing (default: `true`)
    19. Configures tracing attributes (default: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      async:
        followRedirects: true #(1)!
      connectTimeout: "5s" #(2)!
      readTimeout: "2m" #(3)!
      useEnvProxy: false #(4)!
      proxy:
        host: "localhost"  #(5)!
        port: 8090  #(6)!
        user: "user"  #(7)!
        password: "password"  #(8)!
        nonProxyHosts: [ "host1", "host2" ]  #(9)!
      telemetry:
        logging:
          enabled: false #(10)!
          mask: "***" #(11)!
          maskQueries: [ ] #(12)!
          maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(13)!
          pathTemplate: true #(14)!
        metrics:
          enabled: true #(15)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(16)!
          tags: #(17)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(18)!
          attributes: #(19)!
            key1: value1
            key2: value2
    ```

    1. Whether to follow [HTTP redirects](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections) (default: `true`)
    2. Maximum time to establish a connection (default: `5s`)
    3. Maximum time to read a response (default: `2m`)
    4. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
    5. Proxy host (`required`, default not specified)
    6. Proxy port (`required`, default not specified)
    7. Proxy user (default not specified, optional)
    8. Proxy password (default not specified, optional)
    9. Hosts to exclude from proxying (default not specified, optional)
    10. Enables module logging (default: `false`)
    11. Mask used to hide specified headers and request or response parameters (default: `***`)
    12. List of request parameters to hide (default: `[]`)
    13. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    14. Whether to use the request path template in logging; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional)
    15. Enables module metrics (default: `true`)
    16. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    17. Configures metric tags (default: `{}`)
    18. Enables module tracing (default: `true`)
    19. Configures tracing attributes (default: `{}`)

You can also configure [Netty transport](netty.md).

## Native client { #native-client }

Implementation of an HTTP client based on the native client provided in the [JDK](https://openjdk.org/groups/net/httpclient/intro.html).

### Dependency { #dependency-3 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:http-client-jdk"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends JdkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:http-client-jdk")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : JdkHttpClientModule
    ```

The `HttpClient` interface implementation is `JdkHttpClient` and is available for manual implementation.

### Configuration { #configuration-3 }

Example of the complete configuration described in the `JdkHttpClientConfig`
and `HttpClientConfig` classes (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        jdk {
            threads = 2 //(1)!
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
        telemetry {
            logging {
                enabled = false //(11)!
                mask = "***" //(12)!
                maskQueries = [ ] //(13)!
                maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(14)!
                pathTemplate = true //(15)!
            }
            metrics {
                enabled = true //(16)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(17)!
                tags = { // (18)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(19)!
                attributes = { // (20)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1. Number of threads for the `HTTP` client (default: number of available processors multiplied by `2`)
    2. Which `HTTP` protocol version to use, available values: `HTTP_1_1` / `HTTP_2` (default: `HTTP_1_1`)
    3. Maximum time to establish a connection (default: `5s`)
    4. Maximum time to read a response (default: `2m`)
    5. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
    6. Proxy host (`required`, default not specified)
    7. Proxy port (`required`, default not specified)
    8. Proxy user (default not specified, optional)
    9. Proxy password (default not specified, optional)
    10. Hosts to exclude from proxying (default not specified, optional)
    11. Enables module logging (default: `false`)
    12. Mask used to hide specified headers and request or response parameters (default: `***`)
    13. List of request parameters to hide (default: `[]`)
    14. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    15. Whether to use the request path template in logging; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional)
    16. Enables module metrics (default: `true`)
    17. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    18. Configures metric tags (default: `{}`)
    19. Enables module tracing (default: `true`)
    20. Configures tracing attributes (default: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      jdk:
        threads: 2 #(1)!
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
      telemetry:
        logging:
          enabled: false #(11)!
          mask: "***" #(12)!
          maskQueries: [ ] #(13)!
          maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(14)!
          pathTemplate: true #(15)!
        metrics:
          enabled: true #(16)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(17)!
          tags: #(18)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(19)!
          attributes: #(20)!
            key1: value1
            key2: value2
    ```

    1. Number of threads for the `HTTP` client (default: number of available processors multiplied by `2`)
    2. Which `HTTP` protocol version to use, available values: `HTTP_1_1` / `HTTP_2` (default: `HTTP_1_1`)
    3. Maximum time to establish a connection (default: `5s`)
    4. Maximum time to read a response (default: `2m`)
    5. Whether to use `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` and `no_proxy` / `NO_PROXY` environment variables for proxy configuration (default: `false`)
    6. Proxy host (`required`, default not specified)
    7. Proxy port (`required`, default not specified)
    8. Proxy user (default not specified, optional)
    9. Proxy password (default not specified, optional)
    10. Hosts to exclude from proxying (default not specified, optional)
    11. Enables module logging (default: `false`)
    12. Mask used to hide specified headers and request or response parameters (default: `***`)
    13. List of request parameters to hide (default: `[]`)
    14. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    15. Whether to use the request path template in logging; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional)
    16. Enables module metrics (default: `true`)
    17. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    18. Configures metric tags (default: `{}`)
    19. Enables module tracing (default: `true`)
    20. Configures tracing attributes (default: `{}`)

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

### Client Configuration { #client-configuration }

By default, configuration for a particular `@HttpClient` implementation is looked up at `httpClient.{lower case class name}`.
If the path must be specified explicitly, use the `configPath` annotation parameter:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient(configPath = "httpClient.someClient") //(1)!
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

    1. The path to the configuration of this particular client

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient(configPath = "httpClient.someClient") //(1)!
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

    1. The path to the configuration of this particular client

`@HttpClient` can also specify tags for injected components:

* `httpClientTag` — tag used to select a particular transport `HttpClient` when the graph contains several implementations with different `@Tag` values
* `telemetryTag` — tag used to select a particular client telemetry factory

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient(
        configPath = "httpClient.someClient",
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
        configPath = "httpClient.someClient",
        httpClientTag = [CustomTransport::class],
        telemetryTag = [CustomTelemetry::class]
    )
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

Example configuration in the case of the `httpClient.someClient` path described in the `DeclarativeHttpClientConfig` class:

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
                    pathTemplate = true //(7)!
                }
                metrics {
                    enabled = true //(8)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(9)!
                    tags = { // (10)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(11)!
                    attributes = { // (12)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1. Base service `URL` where requests will be sent (`required`, default not specified)
    2. Maximum request time: may include `DNS` resolution, connection, request body write, server processing, and response body read. If the call requires redirects or retries, they must all finish within one period (default not specified, optional)
    3. Enables module logging (default: `false`)
    4. Mask used to hide specified headers and request or response parameters (default: `***`)
    5. List of request parameters to hide (default: `[]`)
    6. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    7. Whether to use the request path template in logging; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional)
    8. Enables module metrics (default: `true`)
    9. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    10. Configures metric tags (default: `{}`)
    11. Enables module tracing (default: `true`)
    12. Configures tracing attributes (default: `{}`)

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
            pathTemplate: true #(7)!
          metrics:
            enabled: true #(8)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(9)!
            tags: #(10)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(11)!
            attributes: #(12)!
              key1: value1
              key2: value2
    ```

    1. Base service `URL` where requests will be sent (`required`, default not specified)
    2. Maximum request time: may include `DNS` resolution, connection, request body write, server processing, and response body read. If the call requires redirects or retries, they must all finish within one period (default not specified, optional)
    3. Enables module logging (default: `false`)
    4. Mask used to hide specified headers and request or response parameters (default: `***`)
    5. List of request parameters to hide (default: `[]`)
    6. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    7. Whether to use the request path template in logging; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional)
    8. Enables module metrics (default: `true`)
    9. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    10. Configures metric tags (default: `{}`)
    11. Enables module tracing (default: `true`)
    12. Configures tracing attributes (default: `{}`)

### Method Configuration { #method-configuration }

For a particular method, some parameters can be configured separately. The method configuration path is determined by the client path and the method name:
if the client path is `httpClient.someClient`, the final path for the `hello` method is `httpClient.someClient.hello`.

Method configuration is applied over client configuration: method `requestTimeout` replaces the client value, and method telemetry settings override
only explicitly specified fields.

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
                        pathTemplate = true //(6)!
                    }
                    metrics {
                        enabled = true //(7)!
                        slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(8)!
                        tags = { // (9)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                    tracing {
                        enabled = true //(10)!
                        attributes = { // (11)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                }
            }
        }
    }
    ```

    1. Maximum request time: may include `DNS` resolution, connection, request body write, server processing, and response body read. If the call requires redirects or retries, they must all finish within one period (default not specified, optional)
    2. Enables module logging (default: `false`)
    3. Mask used to hide specified headers and request or response parameters (default: `***`)
    4. List of request parameters to hide (default: `[]`)
    5. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    6. Whether to use the request path template in logging; when not specified, the client value is inherited (default not specified, optional)
    7. Enables module metrics (default: `true`)
    8. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    9. Configures metric tags (default: `{}`)
    10. Enables module tracing (default: `true`)
    11. Configures tracing attributes (default: `{}`)

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
              pathTemplate: true #(6)!
            metrics:
              enabled: true #(7)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(8)!
              tags: #(9)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(10)!
              attributes: #(11)!
                key1: value1
                key2: value2
    ```

    1. Maximum request time: may include `DNS` resolution, connection, request body write, server processing, and response body read. If the call requires redirects or retries, they must all finish within one period (default not specified, optional)
    2. Enables module logging (default: `false`)
    3. Mask used to hide specified headers and request or response parameters (default: `***`)
    4. List of request parameters to hide (default: `[]`)
    5. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    6. Whether to use the request path template in logging; when not specified, the client value is inherited (default not specified, optional)
    7. Enables module metrics (default: `true`)
    8. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    9. Configures metric tags (default: `{}`)
    10. Enables module tracing (default: `true`)
    11. Configures tracing attributes (default: `{}`)

### Request { #request }

This section describes `HTTP` request transformations for a declarative `HTTP` client.
Use special annotations to specify request parameters.

#### String Parameter Conversion { #string-parameter-converter }

`StringParameterConverter<T>` converts a parameter value to a string before Kora puts it into a path, query parameter,
header, or cookie. The interface has one method:

```java
public interface StringParameterConverter<T> {
    String convert(T value);
}
```

The converter is looked up as a regular graph component by the exact parameter type. If the parameter has type `Map<String, T>`,
the converter is looked up for value type `T`; if `Map<String, List<T>>` is used, it is applied to every list item.

Built-in converters are available for `Boolean`, `Short`, `Integer`, `Long`, `Double`, `Float`, `UUID`, `BigDecimal`, `BigInteger`,
`Duration`, `OffsetTime`, `OffsetDateTime`, `LocalTime`, `LocalDate`, `LocalDateTime`, `ZonedDateTime`, and `Instant`.
Date and time types are written in `ISO` format. For custom types, provide a `StringParameterConverter<T>` component:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserId(long value) {}

    @Module
    public interface UserIdModule {

        default StringParameterConverter<UserId> userIdStringParameterConverter() {
            return value -> Long.toString(value.value());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserId(val value: Long)

    @Module
    interface UserIdModule {

        fun userIdStringParameterConverter(): StringParameterConverter<UserId> {
            return StringParameterConverter { value -> value.value.toString() }
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

#### Path parameter { #path-parameter }

`@Path` - denotes the value of the request path part, the parameter itself is specified in `{quote}` in the path
and the name of the parameter is specified in `value` or is equal to the name of the method argument by default.

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

#### Query parameter { #query-parameter }

`@Query` - query parameter value, the name is specified in `value` or defaults to the method argument name.
Single values, `List<T>`, `Set<T>`, `Collection<T>`, `Map<String, T>`, and `Map<String, List<T>>` are supported.
For non-string values, an available `StringParameterConverter<T>` is used.

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
For non-string values, an available `StringParameterConverter<T>` is used:

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

Specifying the body of a request requires using a method argument without special annotations,
the default supported types are `byte[]`, `ByteBuffer` or `String`.

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

        data class MyBody(val name: String) { }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun hello(@Json body: MyBody) //(1)!
    }
    ```

    1. Specifies that the body should be written as Json

[Json](json.md) module is required.

##### Text form { #text-form }

You can use `FormUrlEncoded` as the body argument type and it will be processed as [form data](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        void hello(FormUrlEncoded body);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun hello(body: FormUrlEncoded): 
    }
    ```

An example of a method call with this form would look like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = httpClient.formEncoded(new FormUrlEncoded(
            new FormUrlEncoded.FormPart("name", "Bob"),
            new FormUrlEncoded.FormPart("password", "12345")
    ));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = httpClient.formEncoded(
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
        void hello(FormMultipart body);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun hello(body: FormMultipart): 
    }
    ```

An example of a method call with this form would look like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = httpClient.formMultipart(new FormMultipart(List.of(
            FormMultipart.data("field1", "some data content"),
            FormMultipart.file("field2", "example1.txt", "text/plain", "some file content".getBytes(StandardCharsets.UTF_8))
    )));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = httpClient.formMultipart(
        FormMultipart(
            listOf<FormMultipart.FormPart>(
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
            public HttpBodyOutput apply(Context ctx, UserBody value) {
                return HttpBody.plaintext(value.id());
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        void hello(@Mapping(UserRequestMapper.class) UserBody body);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class UserBody(val id: String)

        class UserRequestMapper : HttpClientRequestMapper<UserBody> {
            override fun apply(ctx: Context, value: UserBody): HttpBodyOutput {
                return HttpBody.plaintext(value.id)
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun hello(@Mapping(UserRequestMapper::class) body: UserBody)
    }
    ```

**Example: Protobuf Serialization**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface ProtobufClient {

        final class ProtobufRequestMapper implements HttpClientRequestMapper<MyMessage> {

            @Override
            public HttpBodyOutput apply(Context ctx, MyMessage value) {
                byte[] protobufBytes = value.toByteArray();
                return HttpBody.of(protobufBytes, "application/x-protobuf");
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

            override fun apply(Context ctx, MyMessage value): HttpBodyOutput {
                val protobufBytes = value.toByteArray()
                return HttpBody.of(protobufBytes, "application/x-protobuf")
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/message")
        fun sendMessage(@Mapping(ProtobufRequestMapper::class) message: MyMessage)
    }
    ```

#### Cookie { #cookie }

`@Cookie` - [Cookie](https://developer.mozilla.org/en-US/docs/Glossary/Cookie) value, the parameter name is specified in `value` or defaults to the method argument name.
Single values, `List<T>`, `Set<T>`, `Collection<T>`, `Map<String, T>`, and a ready `Cookie` object are supported.
Cookies are added to the `Cookie` header; for collections, every value becomes a separate cookie value with the same name.

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

    1.  Any `@Nullable` annotation will do, such as `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

=== ":simple-kotlin: `Kotlin`"

    It is expected to use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such a parameter as Nullable:

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(@Query("queryValue") queryValue: String?)
    }
    ```

### Response { #response }

The section describes the transformation of an HTTP response from a declarative HTTP client.

#### Response body { #response-body }

By default, you can use the standard response body return value types such as `void`, `byte[]`, `ByteBuffer` or `String`.

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

        data class MyResponse(val name: String) { }

        @Json //(1)!
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(): MyResponse
    }
    ```

    1. Indicates that the response should be read as Json

[Json](json.md) module is required.

##### Response Entity { #response-entity }

If the intention is to read the body and also get the headers and status code of the response,
it is intended to use `HttpResponseEntity`, which is a wrapper over the response body.

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

        data class MyResponse(val name: String) { }

        @Json
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(): HttpResponseEntity<MyResponse>
    }
    ```

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
            
            @Throws(IOException::class, HttpClientDecoderException::class)
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

**Example: Error Handling in Mapper**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface ApiClient {

        record ApiResponse(String status, Object data) {}

        final class SafeResponseMapper implements HttpClientResponseMapper<ApiResponse> {

            private final JsonReader<ApiResponse> jsonReader;

            public SafeResponseMapper(JsonReader<ApiResponse> jsonReader) {
                this.jsonReader = jsonReader;
            }

            @Override
            public ApiResponse apply(HttpClientResponse response) throws IOException {
                int statusCode = response.statusCode();
                byte[] body = response.body();

                if (statusCode >= 400) {
                    // Handle error: log or throw exception
                    throw new HttpClientResponseException(statusCode, body, response.headers());
                }

                if (body == null || body.length == 0) {
                    return null;
                }

                return jsonReader.read(body);
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

        data class ApiResponse(val status: String, val data: Any?)

        class SafeResponseMapper(
            private val jsonReader: JsonReader<ApiResponse>
        ) : HttpClientResponseMapper<ApiResponse> {

            @Throws(IOException::class)
            override fun apply(response: HttpClientResponse): ApiResponse {
                val statusCode = response.statusCode()
                val body = response.body()

                if (statusCode >= 400) {
                    // Handle error: log or throw exception
                    throw HttpClientResponseException(statusCode, body, response.headers())
                }

                if (body == null || body.isEmpty()) {
                    return null
                }

                return jsonReader.read(body)
            }
        }

        @HttpRoute(method = HttpMethod.GET, path = "/api/data")
        @Mapping(SafeResponseMapper::class)
        fun getData(): ApiResponse
    }
    ```

#### Response Error { #response-error }

By default, when neither converter tag nor converter is specified, conversion is applied only for `2xx` HTTP response codes.
For all other codes, `HttpClientResponseException` is thrown. It contains the [HTTP response code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status), response body, and response headers.

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

`HttpClientResponseException` is created after reading the response body into a byte array. If the body could not be read fully,
the read error is added as a `suppressed` exception, and `getBytes()` contains the body that could be collected.

#### Conversion by Code { #conversion-by-code }

If specific conversions are required depending on the [HTTP status code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) of the response, you can use the `@ResponseCodeMapper` annotation to specify a
correspondence between the HTTP status code and the `HttpClientResponseMapper` resolver.

You can also use `ResponseCodeMapper.DEFAULT` to define default behavior for all unlisted HTTP codes.
If `mapper` is specified for a code, that particular `HttpClientResponseMapper` is used.
If `type` is specified, Kora selects a response mapper for that type and then casts the result to the method return type.
This is useful for closed response hierarchies where different HTTP statuses correspond to different result subtypes.

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

        data class UserResponse(val payload: Payload, val error: Error) {
            
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

### Signatures { #signatures }

Available signatures for declarative `HTTP` client methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

## Interceptors { #interceptors }

You can create interceptors to change behavior or create additional behavior using the `HttpClientInterceptor` interface.
Interceptors can be attached to specific methods or the entire `@HttpClient` class using the `@InterceptWith` annotation.

**Method-level interceptor:**

### Root URL { #root-uri-interceptor }

`RootUriInterceptor` is a ready-made interceptor that adds a base `URL` to relative requests.
If the request already contains a scheme (`http://` or `https://`), the interceptor leaves it unchanged.
If the request is relative, `RootUriInterceptor` adds the root address and guarantees one `/` separator between the root and the path.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ClientModule {

        default RootUriInterceptor rootUriInterceptor() {
            return new RootUriInterceptor("https://api.example.com");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ClientModule {

        fun rootUriInterceptor(): RootUriInterceptor {
            return RootUriInterceptor("https://api.example.com")
        }
    }
    ```

After registering the interceptor, connect it to the client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    @InterceptWith(RootUriInterceptor.class)
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        User get(@Path String id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    @InterceptWith(RootUriInterceptor::class)
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        fun get(@Path id: String): User
    }
    ```

For declarative clients, it is usually more convenient to set the base `URL` through `DeclarativeHttpClientConfig.url`.
`RootUriInterceptor` is useful for imperative `HttpClient` or when a shared root address should be added as separate cross-cutting behavior.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        final class MethodInterceptor implements HttpClientInterceptor {

            private final Component1 component1;

            private MethodInterceptor(Component1 component1) {
                this.component1 = component1;
            }

            @Override
            public CompletionStage<HttpClientResponse> processRequest(Context ctx, InterceptChain chain, HttpClientRequest request) throws Exception {
                component1.doSomething();
                return chain.process(ctx, request);
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

        class MethodInterceptor(val component1: Component1) : HttpClientInterceptor {

            @Throws(Exception::class)
            override fun processRequest(
                ctx: Context,
                chain: HttpClientInterceptor.InterceptChain,
                request: HttpClientRequest
            ): CompletionStage<HttpClientResponse> {
                component1.doSomething()
                return chain.process(ctx, request)
            }
        }

        @InterceptWith(MethodInterceptor::class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

**Class-level interceptor:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @InterceptWith(LoggingInterceptor.class) // Applied to all client methods
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        void hello();

        @HttpRoute(method = HttpMethod.POST, path = "/world")
        void world();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @InterceptWith(LoggingInterceptor::class) // Applied to all client methods
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        fun hello()

        @HttpRoute(method = HttpMethod.POST, path = "/world")
        fun world()
    }
    ```

**Interceptor execution order:**

Interceptors are executed in declaration order (left to right). Each interceptor can:
- Modify the request before sending
- Call the next interceptor in the chain (`chain.process()`)
- Modify the response after receiving
- Throw an exception to break the chain

```
Request → Interceptor1 → Interceptor2 → Interceptor3 → HTTP Server
Response ← Interceptor1 ← Interceptor2 ← Interceptor3 ← HTTP Server
```

### Global interceptor { #interceptor-global }

To apply an interceptor to all clients, register it as a component without `@InterceptWith`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class GlobalInterceptor implements HttpClientInterceptor {

        @Override
        public CompletionStage<HttpClientResponse> processRequest(Context ctx, InterceptChain chain, HttpClientRequest request) throws Exception {
            // Applied to all HTTP clients
            return chain.process(ctx, request);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class GlobalInterceptor : HttpClientInterceptor {

        @Throws(Exception::class)
        override fun processRequest(
            ctx: Context,
            chain: HttpClientInterceptor.InterceptChain,
            request: HttpClientRequest
        ): CompletionStage<HttpClientResponse> {
            // Applied to all HTTP clients
            return chain.process(ctx, request)
        }
    }
    ```

If the interceptor must be applied to all client methods, `@InterceptWith` can be placed on the interface:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    @InterceptWith(ClientInterceptor.class)
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    @InterceptWith(ClientInterceptor::class)
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

If interceptors are specified on both the client and the method, both interceptor sets are applied for that call.

### Authorization { #authorization }

Kora provides out-of-the-box interceptors that can be used for [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/) authorization.

#### Basic { #basic }

You need to configure an interceptor and configuration for [Basic](https://swagger.io/docs/specification/authentication/basic-authentication/) authorization:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface BasicAuthModule {
    
        @ConfigSource("openapiAuth.basicAuth")
        public interface BasicAuthConfig {

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

You can also provide your own `HttpClientTokenProvider` implementation in the constructor if rules for getting secrets are different.

Then add interceptor for the entire HTTP client or specific methods.

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

You need to configure an interceptor and configuration for [ApiKey](https://swagger.io/docs/specification/authentication/api-keys/) authorization:

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

Then add interceptor for the entire HTTP client or specific methods.

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
    interface BasicAuthModule {
            
        fun bearerAuther(tokenProvider: HttpClientTokenProvider): BearerAuthHttpClientInterceptor {
            return BearerAuthHttpClientInterceptor(tokenProvider)
        }
    }
    ```

You will need to implement the `Bearer` token provisioning yourself using your custom `HttpClientTokenProvider` implementation,
or use a constructor that accepts a static `Bearer Token`.

```java
public interface HttpClientTokenProvider {
    
    CompletionStage<String> getToken(HttpClientRequest request);
}
```

Then add interceptor for the entire HTTP client or specific methods.

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
Used when the token needs to be refreshed or obtained from an external source (e.g., OAuth2 token endpoint).

**Implementation example:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class MyTokenProvider implements HttpClientTokenProvider {

        private final OAuthClient oauthClient;
        private volatile String cachedToken;
        private volatile long tokenExpiry;

        public MyTokenProvider(OAuthClient oauthClient) {
            this.oauthClient = oauthClient;
        }

        @Override
        public CompletionStage<String> getToken(HttpClientRequest request) {
            if (cachedToken != null && System.currentTimeMillis() < tokenExpiry) {
                return CompletableFuture.completedFuture(cachedToken);
            }
            
            // Get new token
            return oauthClient.refreshToken()
                .thenApply(response -> {
                    this.cachedToken = response.accessToken();
                    this.tokenExpiry = System.currentTimeMillis() + response.expiresIn() * 1000;
                    return this.cachedToken;
                });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyTokenProvider(
        private val oauthClient: OAuthClient
    ) : HttpClientTokenProvider {

        private var cachedToken: String? = null
        private var tokenExpiry: Long = 0

        override fun getToken(request: HttpClientRequest): CompletionStage<String> {
            if (cachedToken != null && System.currentTimeMillis() < tokenExpiry) {
                return CompletableFuture.completedFuture(cachedToken)
            }
            
            // Get new token
            return oauthClient.refreshToken()
                .thenApply { response ->
                    cachedToken = response.accessToken()
                    tokenExpiry = System.currentTimeMillis() + response.expiresIn() * 1000
                    cachedToken!!
                }
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

## Exception handling { #exception-handling }

Various exceptions may occur during HTTP requests. All exceptions inherit from the base `HttpClientException`.

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
    class SomeService {
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
                // Response error: statusCode, body, headers
                int statusCode = e.getStatusCode();
                byte[] body = e.getBody();
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
                // Response error: statusCode, body, headers
                val statusCode = e.statusCode
                val body = e.body
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

#### HttpClientTimeoutException { #timeout-exception }

Thrown when a request exceeds the configured timeout (`requestTimeout` or `connectTimeout`).

**Causes:**
- Server does not respond within `requestTimeout`
- Connection establishment time exceeds `connectTimeout`
- Network delays

**Recommendations:**
- Configure adequate timeouts in configuration
- Implement retry logic for temporary failures
- Use circuit breaker to protect from cascading failures

#### HttpClientConnectionException { #connection-exception }

Thrown when connection to server cannot be established.

**Causes:**
- DNS resolution fails
- Server unavailable (port closed, firewall)
- Connection refused
- SSL/TLS handshake failed

**Recommendations:**
- Check service availability (health check)
- Use fallback to backup service
- Configure retry with exponential backoff

#### HttpClientResponseException { #response-exception }

Thrown when server returns HTTP error status code (4xx or 5xx) and no custom mapper is specified via `@ResponseCodeMapper`.

**Available data:**
- `statusCode` — HTTP status code (400, 404, 500, etc.)
- `body` — response body (may contain error details)
- `headers` — response headers

**Recommendations:**
- Use `@ResponseCodeMapper` for custom status handling
- Log statusCode and body for debugging
- Distinguish client (4xx) and server (5xx) errors

#### HttpClientEncoderException { #encoder-exception }

Thrown when serialization of request body fails.

**Causes:**
- JSON/XML serialization error
- Invalid data in request object
- Missing serializer for type

**Recommendations:**
- Validate data before sending
- Check for Json annotations on classes
- Log original exception in `cause`

#### HttpClientDecoderException { #decoder-exception }

Thrown when deserialization of response body fails.

**Causes:**
- Invalid JSON/XML in server response
- Schema mismatch (server returned unexpected fields)
- Missing deserializer for type

**Recommendations:**
- Check API version compatibility
- Log response body for debugging
- Use `@ResponseCodeMapper` for format error handling

#### HttpClientUnknownException { #unknown-exception }

Thrown when an unknown error occurs that doesn't fit other categories.

**Available data:**
- `cause` — original exception

**Recommendations:**
- Always log `cause` for diagnostics
- Check HTTP client logs at DEBUG/TRACE level
- Report bug if exception is reproducible

## Client imperative { #client-imperative }

The base client represents the `HttpClient` interface and is available for deployment:

```java
public interface HttpClient {
    
    CompletionStage<HttpClientResponse> execute(HttpClientRequest request); //(1)!

    HttpClient with(HttpClientInterceptor interceptor); //(2)!
}
```

1. Method of request execution
2. A method that allows you to add various interceptors manually

You can use `HttpClientRequestBuilder` to build requests manually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    HttpClientRequest request = HttpClientRequest.of("POST", "http://localhost:8090/pets/{petId}")
            .templateParam("petId", "1")
            .queryParam("page", 1)
            .header("token", "12345")
            .body(HttpBody.plaintext("refresh"))
            .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.of("POST", "http://localhost:8090/pets/{petId}")
        .templateParam("petId", "1")
        .queryParam("page", 1)
        .header("token", "12345")
        .body(HttpBody.plaintext("refresh"))
        .build()
    ```

### HttpClientRequestBuilder { #request-builder }

`HttpClientRequestBuilder` allows building HTTP requests manually.

===! ":fontawesome-brands-java: `Java`"

    ```java
    HttpClientRequest request = HttpClientRequest.of("POST", "http://localhost:8090/pets/{petId}")
            .templateParam("petId", "1")
            .queryParam("page", 1)
            .header("token", "12345")
            .body(HttpBody.plaintext("refresh"))
            .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.of("POST", "http://localhost:8090/pets/{petId}")
        .templateParam("petId", "1")
        .queryParam("page", 1)
        .header("token", "12345")
        .body(HttpBody.plaintext("refresh"))
        .build()
    ```

### UriQueryBuilder { #uri-query-builder }

`UriQueryBuilder` helps build URIs with query parameters.

===! ":fontawesome-brands-java: `Java`"

    ```java
    UriQueryBuilder builder = new UriQueryBuilder()
        .path("/api/users")
        .queryParam("page", 1)
        .queryParam("size", 10)
        .queryParam("sort", "name");
    
    String uri = builder.build();
    // /api/users?page=1&size=10&sort=name
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val builder = UriQueryBuilder()
        .path("/api/users")
        .queryParam("page", 1)
        .queryParam("size", 10)
        .queryParam("sort", "name")
    
    val uri = builder.build()
    // /api/users?page=1&size=10&sort=name
    ```

### HttpBodyInput { #http-body-input }

`HttpBodyInput` is an interface that describes HTTP request body as a data stream (Flow.Publisher<ByteBuffer>).
Used for streaming large data without loading into memory.

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `asInputStream()` | `InputStream` | Represents body as InputStream for reading |
| `asBufferStage()` | `CompletionStage<ByteBuffer>` | Asynchronously reads entire body to ByteBuffer |
| `asArrayStage()` | `CompletionStage<byte[]>` | Asynchronously reads entire body to byte[] |

### HttpClientResponse { #http-client-response }

`HttpClientResponse` is an interface that represents HTTP response from server.

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `statusCode()` | `int` | HTTP status code (200, 404, 500, etc.) |
| `body()` | `byte[]` | Response body as byte array |
| `headers()` | `HttpHeaders` | Response headers |
| `cookies()` | `Cookies` | Cookies from response |

### HttpHeaders { #http-headers-imperative }

`HttpHeaders` provides access to request and response headers in the imperative client.

**Reading headers:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    HttpClientRequest request = HttpClientRequest.of("GET", "http://localhost:8090/api/data")
        .build();
    
    httpClient.execute(request).thenAccept(response -> {
        HttpHeaders headers = response.headers();
        String contentType = headers.getFirst("Content-Type");
        List<String> allValues = headers.get("X-Custom-Header");
        boolean hasHeader = headers.contains("Authorization");
    });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.of("GET", "http://localhost:8090/api/data").build()
    
    httpClient.execute(request).thenAccept { response ->
        val headers = response.headers
        val contentType = headers.getFirst("Content-Type")
        val allValues = headers.get("X-Custom-Header")
        val hasHeader = headers.contains("Authorization")
    }
    ```

**Adding headers:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    MutableHttpHeaders headers = new MutableHttpHeaders();
    headers.add("Authorization", "Bearer token123");
    headers.add("X-Custom-Header", "value");
    headers.set("Content-Type", "application/json");
    
    HttpClientRequest request = HttpClientRequest.of("POST", "http://localhost:8090/api/data")
        .headers(headers)
        .body(HttpBody.plaintext("body"))
        .build();
    
    httpClient.execute(request);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val headers = MutableHttpHeaders()
    headers.add("Authorization", "Bearer token123")
    headers.add("X-Custom-Header", "value")
    headers.set("Content-Type", "application/json")
    
    val request = HttpClientRequest.of("POST", "http://localhost:8090/api/data")
        .headers(headers)
        .body(HttpBody.plaintext("body"))
        .build()
    
    httpClient.execute(request)
    ```

### Cookies { #cookies-imperative }

`Cookies` provides access to request and response cookies in the imperative client.

**Reading cookies:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    HttpClientRequest request = HttpClientRequest.of("GET", "http://localhost:8090/api/profile")
        .build();
    
    httpClient.execute(request).thenAccept(response -> {
        Cookies cookies = response.cookies();
        Cookie sessionCookie = cookies.get("SESSIONID");
        if (sessionCookie != null) {
            String value = sessionCookie.value();
            String domain = sessionCookie.domain();
            String path = sessionCookie.path();
        }
    });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.of("GET", "http://localhost:8090/api/profile").build()
    
    httpClient.execute(request).thenAccept { response ->
        val cookies = response.cookies
        val sessionCookie = cookies.get("SESSIONID")
        if (sessionCookie != null) {
            val value = sessionCookie.value()
            val domain = sessionCookie.domain()
            val path = sessionCookie.path()
        }
    }
    ```

## Telemetry { #telemetry }

HTTP Client uses a telemetry contract for logging, metrics, and tracing of requests.
Telemetry configuration (section `telemetry { logging / metrics / tracing }`) is described in the [Configuration](#configuration) section.
Extension points are located in `ru.tinkoff.kora.http.client.common.telemetry`.

For each HTTP request, an `HttpClientTelemetry.HttpClientTelemetryContext` is created, which is closed upon request completion.
The request is described through telemetry handler parameters, including method, URL, response status, and duration.

The default factory `DefaultHttpClientTelemetryFactory` combines three factories:
- `HttpClientLoggerFactory` builds `HttpClientLogger` for logging request start/end;
- `HttpClientMetricsFactory` builds `HttpClientMetrics` for writing request metrics;
- `HttpClientTracerFactory` builds `HttpClientTracer` for distributed tracing.

Metrics and tracing are described in the [Metrics Reference](metrics.md#http-client) section.
