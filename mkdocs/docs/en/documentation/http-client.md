Module provides a thin layer of abstraction over HTTP client libraries to create HTTP clients
using declarative-style annotations or using client in imperative-style.

???+ warning "Tip"

    **We recommend** using an approach where OpenAPI file is primary contract
    and clients are created from it using a OpenAPI generator. 
    This approach allows you to achieve consistency between the consumer and owner of the contract
    and update API faster in case of new version by just updaing contract file. 
    For more information about the generator, see the [section on generating from OpenAPI](openapi-codegen.md).

## OkHttp

HTTP client implementation based on [OkHttp](https://github.com/square/okhttp) library.
Please note that the implementation is written in Kotlin and uses appropriate dependencies.

### Dependency

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

### Configuration

Example of the complete configuration described in the `OkHttpClientConfig`
and `HttpClientConfig` classes (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        ok {
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
            }
            tracing {
                enabled = true //(18)!
            }
        }
    }
    ```

    1. Whether to follow [redirects in HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections)
    2. Maximum HTTP protocol version used (available values: `HTTP_1_1` / `HTTP_2` / `HTTP_3`)
    3. Maximum time to establish a connection
    4. Maximum time to read a response
    5. Whether to use environment variables to configure the proxy
    6. Proxy address (optional)
    7. Proxy port (optional)
    8. User for the proxy (optional)
    9. Password for the proxy (optional)
    10. Hosts that should be excluded from proxying (optional)
    11. Enables module logging (default `false`)
    12.  Mask that is used to hide specified headers and request/response parameters
    13.  List of request parameters to be hidden
    14.  List of request/response headers that should be hidden
    15.  Whether to always use the request path template when logging. Default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    16. Enables module metrics (default `true`)
    17. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    18. Enables module tracing (default `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      ok:
        followRedirects: true #(1)!
        httpVersion: "HTTP_1_1" #(2)!
      connectTimeout: "5s" #(3)!
      readTimeout: "2m" #(4)!
      useEnvProxy: false #(5)!
      proxy:
        host: "localhost" #(6)!
        port: 8090  #(7)!
        user: "user"  #(8)!
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
        telemetry:
          enabled: true #(18)!
    ```

    1. Whether to follow [redirects in HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections)
    2. Maximum HTTP protocol version used (available values: `HTTP_1_1` / `HTTP_2` / `HTTP_3`)
    3. Maximum time to establish a connection
    4. Maximum time to read a response
    5. Whether to use environment variables to configure the proxy
    6. Proxy address (optional)
    7. Proxy port (optional)
    8. User for the proxy (optional)
    9. Password for the proxy (optional)
    10. Hosts that should be excluded from proxying (optional)
    11. Enables module logging (default `false`)
    12.  Mask that is used to hide specified headers and request/response parameters
    13.  List of request parameters to be hidden
    14.  List of request/response headers that should be hidden
    15.  Whether to always use the request path template when logging. Default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    16. Enables module metrics (default `true`)
    17. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    18. Enables module tracing (default `true`)

#### Configurer

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

## AsyncHttpClient

HTTP client implementation based on the [Async HTTP Client](https://github.com/AsyncHttpClient/async-http-client) library.

### Dependency

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

### Configuration

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
            }
            tracing {
                enabled = true //(17)!
            }
        }
    }
    ```

    1. Whether to follow [redirects in HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections)
    2. Maximum time to establish a connection
    3. Maximum time to read a response
    4. Whether to use environment variables to configure the proxy
    5. Proxy address (optional)
    6. Proxy port (optional)
    7. User for the proxy (optional)
    8. Password for the proxy (optional)
    9. Hosts that should be excluded from proxying (optional)
    10. Enables module logging (default `false`)
    11.  Mask that is used to hide specified headers and request/response parameters
    12.  List of request parameters to be hidden
    13.  List of request/response headers that should be hidden
    14.  Whether to always use the request path template when logging. Default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    15. Enables module metrics (default `true`)
    16. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    17. Enables module tracing (default `true`)

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
        telemetry:
          enabled: true #(17)!
    ```

    1. Whether to follow [redirects in HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections)
    2. Maximum time to establish a connection
    3. Maximum time to read a response
    4. Whether to use environment variables to configure the proxy
    5. Proxy address (optional)
    6. Proxy port (optional)
    7. User for the proxy (optional)
    8. Password for the proxy (optional)
    9. Hosts that should be excluded from proxying (optional)
    10. Enables module logging (default `false`)
    11.  Mask that is used to hide specified headers and request/response parameters
    12.  List of request parameters to be hidden
    13.  List of request/response headers that should be hidden
    14.  Whether to always use the request path template when logging. Default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    15. Enables module metrics (default `true`)
    16. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    17. Enables module tracing (default `true`)

You can also configure [Netty transport](netty.md).

## Native client

Implementation of an HTTP client based on the native client provided in the [JDK](https://openjdk.org/groups/net/httpclient/intro.html).

### Dependency

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

### Configuration

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
        useEnvProxy = false //(4)!
        proxy {
            host = "localhost" //(5)!
            port = 8090 //(6)!
            user = "user" //(7)!
            password = "password" //(8)!
            nonProxyHosts = [ "host1", "host2" ] //(9)!
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
            }
            tracing {
                enabled = true //(17)!
            }
        }
    }
    ```

    1. Number of threads for HTTP client
    2. Which version of HTTP protocol to use (available values: `HTTP_1_1` / `HTTP_2`)
    3. Maximum time to establish a connection
    4. Whether to use environment variables to configure the proxy
    5. Proxy address (optional)
    6. Proxy port (optional)
    7. User for the proxy (optional)
    8. Password for the proxy (optional)
    9. Hosts that should be excluded from proxying (optional)
    10. Enables module logging (default `false`)
    11.  Mask that is used to hide specified headers and request/response parameters
    12.  List of request parameters to be hidden
    13.  List of request/response headers that should be hidden
    14.  Whether to always use the request path template when logging. Default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    15. Enables module metrics (default `true`)
    16. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    17. Enables module tracing (default `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      jdk:
        threads: 2 #(1)!
        httpVersion: "HTTP_1_1" #(2)!
      connectTimeout: "2s" #(3)!
      useEnvProxy: false #(4)!
      proxy:
        host: "localhost" #(5)!
        port: 8090 #(6)!
        user: "user" #(7)!
        password: "password" #(8)!
        nonProxyHosts: [ "host1", "host2" ] #(9)!
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
        telemetry:
          enabled: true #(17)!
    ```

    1. Number of threads for HTTP client
    2. Which version of HTTP protocol to use (available values: `HTTP_1_1` / `HTTP_2`)
    3. Maximum time to establish a connection
    4. Whether to use environment variables to configure the proxy
    5. Proxy address (optional)
    6. Proxy port (optional)
    7. User for the proxy (optional)
    8. Password for the proxy (optional)
    9. Hosts that should be excluded from proxying (optional)
    10. Enables module logging (default `false`)
    11.  Mask that is used to hide specified headers and request/response parameters
    12.  List of request parameters to be hidden
    13.  List of request/response headers that should be hidden
    14.  Whether to always use the request path template when logging. Default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    15. Enables module metrics (default `true`)
    16. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    17. Enables module tracing (default `true`)

## Client declarative

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

#### Client Configuration

The default configuration of a particular implementation of `@HttpClient` uses the following path `httpClient.{lower case class name}` for configuration lookup,
or specified in the `configPath` parameter in the annotation:

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
                }
                tracing {
                    enabled = true //(10)!
                }
            }
        }
    }
    ```

    1. URL of the service where requests will be sent
    2. Maximum request timeout, may spans the entire call: resolving DNS, connecting, writing the request body, server processing, and reading the response body, if call requires redirects or retries all must complete within one timeout period
    3. Enables module logging (default `false`)
    4.  Mask that is used to hide specified headers and request/response parameters
    5.  List of request parameters to be hidden
    6.  List of request/response headers that should be hidden
    7.  Whether to always use the request path template when logging. Default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    8. Enables module metrics (default `true`)
    9. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    10. Enables module tracing (default `true`)

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
          telemetry:
            enabled: true #(10)!
    ```

    1. URL of the service where requests will be sent
    2. Maximum request timeout, may spans the entire call: resolving DNS, connecting, writing the request body, server processing, and reading the response body, if call requires redirects or retries all must complete within one timeout period
    3. Enables module logging (default `false`)
    4.  Mask that is used to hide specified headers and request/response parameters
    5.  List of request parameters to be hidden
    6.  List of request/response headers that should be hidden
    7.  Whether to always use the request path template when logging. Default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    8. Enables module metrics (default `true`)
    9. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    10. Enables module tracing (default `true`)

### Method Configuration

Using the above HTTP client example, it is possible to configure separately some of the parameters for a particular method, the configuration path
is determined by the path to the client and the method name, in the example above the configuration is `httpClient.someClient`
and method `hello` the final path will be `httpClient.someClient.hello`

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
                    }
                    tracing {
                        enabled = true //(9)!
                    }
                }
            }
        }
    }
    ```

    1. Maximum request timeout, may spans the entire call: resolving DNS, connecting, writing the request body, server processing, and reading the response body, if call requires redirects or retries all must complete within one timeout period
    2. Enables module logging (default `false`)
    3. Mask that is used to hide specified headers and request/response parameters
    4. List of request parameters to be hidden
    5. List of request/response headers that should be hidden
    6. Whether to always use the request path template when logging. Default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    7. Includes module metrics
    8. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    9. Enables module tracing (default `true`)

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
            telemetry:
              enabled: true #(9)!
    ```

    1. Maximum request timeout, may spans the entire call: resolving DNS, connecting, writing the request body, server processing, and reading the response body, if call requires redirects or retries all must complete within one timeout period
    2. Enables module logging (default `false`)
    3. Mask that is used to hide specified headers and request/response parameters
    4. List of request parameters to be hidden
    5. List of request/response headers that should be hidden
    6. Whether to always use the request path template when logging. Default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    7. Includes module metrics
    8. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    9. Enables module tracing (default `true`)

### Request

The section describes HTTP request transformations at a declarative HTTP client.
It is suggested to use special annotations to specify request parameters.

#### Path parameter

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

#### Query parameter

`@Query` - value of the query parameter, the name of the parameter is specified in `value` or is equal to the name of the method argument by default.

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


It is possible to send query parameters in key and value format, for this purpose it is assumed to use `Map` type,
where the key is the parameter name and must be of type `String`, and the parameter value can be of any type and will be processed through `String.valueOf()`:

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

#### Header

`@Header` - value of [request header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers), parameter name is specified in `value` or defaults to the method argument name.

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

It is possible to send request parameters in key and value format, for this purpose it is supposed to use `HttpHeaders` type or `Map` type,
where the key is the parameter name and must be of type `String`, and the parameter value can be of any type and will be processed through `String.valueOf()`:

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

#### Request body

Specifying the body of a request requires using a method argument without special annotations,
the default supported types are `byte[]`, `ByteBuffer` or `String`.

##### Json

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

##### Text form

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

##### Binary Form

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

##### Custom body

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

#### Cookie

`@Cookie` - [Cookie](https://developer.mozilla.org/en-US/docs/Glossary/Cookie) value, the parameter name is specified in `value` or defaults to the method argument name.

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

#### Required parameters

===! ":fontawesome-brands-java: `Java`"

    By default, all arguments declared in a method are **required** (*NotNull*).

=== ":simple-kotlin: `Kotlin`"

    By default, all arguments declared in a method that do not use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax are considered **required** (*NotNull*).

#### Optional parameters

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

### Response

The section describes the transformation of an HTTP response from a declarative HTTP client.

#### Response body

By default, you can use the standard response body return value types such as `void`, `byte[]`, `ByteBuffer` or `String`.

##### Json

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

##### Response Entity

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

#### Custom response

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

#### Response Error

By default, when no converter tag or converter itself is specified, the conversion will be applied for `2xx` HTTP status codes,
for all others a `HttpClientResponseException` exception will be thrown, which contains [HTTP status code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status), response body and response headers.

#### Conversion by Code

If specific conversions are required depending on the [HTTP status code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) of the response, you can use the `@ResponseCodeMapper` annotation to specify a
correspondence between the HTTP status code and the `HttpClientResponseMapper` resolver.

You can also use `ResponseCodeMapper.DEFAULT` as an indication of the default behavior for all unlisted status codes.

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

### Signatures

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

## Interceptors

You can create interceptors to change behavior or create additional behavior using the `HttpClientInterceptor` class.
Interceptors can be applied to specific methods or to the entire `@HttpClient` class:

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

### Authorization

Kora provides out-of-the-box interceptors that can be used for [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/) authorization.

#### Basic

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

#### ApiKey

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

#### Bearer

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

#### OAuth

Authorization by [OAuth](https://swagger.io/docs/specification/authentication/oauth2/) is similar to [Bearer](#bearer),
you need to implement `HttpClientTokenProvider` yourself and put it in dependency container.

## Client imperative

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
