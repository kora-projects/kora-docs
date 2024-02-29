Module provides a thin layer of abstraction over HTTP client libraries to create HTTP clients using annotations
using both declarative-style annotations and imperative-style annotations.

## AsyncHttpClient

HTTP client implementation based on the [Async HTTP Client](https://github.com/AsyncHttpClient/async-http-client) library.

### Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:http-client-async"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends AsyncHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:http-client-async")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : AsyncHttpClientModule
    ```

The `HttpClient` interface implementation is `AsyncHttpClient` and is available for manual implementation.

### Configuration

The configuration is responsible for the general settings of the HTTP client implementation.
An example of the configuration described in `AsyncHttpClientConfig` and `HttpClientConfig` class:

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
    }
    ```

    1. Whether to follow [redirects in HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections)
    2. Maximum time to establish a connection
    3. Maximum time to read a response
    4. Whether to use environment variables to configure the proxy
    5. Proxy address
    6. Proxy port
    7. User for the proxy
    8. Password for the proxy
    9. Hosts that should be excluded from proxying

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
    ```

    1. Whether to follow [redirects in HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections)
    2. Maximum time to establish a connection
    3. Maximum time to read a response
    4. Whether to use environment variables to configure the proxy
    5. Proxy address
    6. Proxy port
    7. User for the proxy
    8. Password for the proxy
    9. Hosts that should be excluded from proxying

## OkHttp

HTTP client implementation based on [OkHttp](https://github.com/square/okhttp) library.
Please note that the implementation is written in Kotlin and uses appropriate dependencies.

### Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:http-client-ok"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends OkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:http-client-ok")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : OkHttpClientModule
    ```

### Configuration

Configuration is responsible for the general settings of the HTTP client implementation.
Example of configuration described in `OkHttpClientConfig` and `HttpClientConfig` classes:

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
    }
    ```

    1. Whether to follow [redirects in HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections)
    2. Maximum HTTP protocol version used (available values: `HTTP_1_1` / `HTTP_2` / `HTTP_3`)
    3. Maximum time to establish a connection
    4. Maximum time to read a response
    5. Whether to use environment variables to configure the proxy
    6. Proxy address
    7. Proxy port
    8. User for the proxy
    9. Password for the proxy
    10. Hosts that should be excluded from proxying

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
    ```

    1. Whether to follow [redirects in HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections)
    2. Maximum HTTP protocol version used (available values: `HTTP_1_1` / `HTTP_2` / `HTTP_3`)
    3. Maximum time to establish a connection
    4. Maximum time to read a response
    5. Whether to use environment variables to configure the proxy
    6. Proxy address
    7. Proxy port
    8. User for the proxy
    9. Password for the proxy
    10. Hosts that should be excluded from proxying

## Native client

Implementation of an HTTP client based on the native client provided in the [JDK](https://openjdk.org/groups/net/httpclient/intro.html).

### Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:http-client-jdk"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends JdkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:http-client-jdk")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : JdkHttpClientModule
    ```

The `HttpClient` interface implementation is `JdkHttpClient` and is available for manual implementation.

### Configuration

The configuration is responsible for the general settings of the HTTP client implementation.
An example of the configuration described in the `JdkHttpClientConfig` and `HttpClientConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        jdk {
            threads = 10 //(1)!
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
    }
    ```

    1. Number of threads for HTTP client
    2. Which version of HTTP protocol to use (available values: `HTTP_1_1` / `HTTP_2`)
    3. Maximum time to establish a connection
    4. Whether to use environment variables to configure the proxy
    5. Proxy address
    6. Proxy port
    7. User for the proxy
    8. Password for the proxy
    9. Hosts that should be excluded from proxying

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      jdk:
        threads: 10 #(1)!
        httpVersion: "HTTP_1_1" #(2)!
      connectTimeout: "2s" #(3)!
      useEnvProxy: false #(4)!
      proxy:
        host: "localhost" #(5)!
        port: 8090 #(6)!
        user: "user" #(7)!
        password: "password" #(8)!
        nonProxyHosts: [ "host1", "host2" ] #(9)!
    ```

    1. Number of threads for HTTP client
    2. Which version of HTTP protocol to use (available values: `HTTP_1_1` / `HTTP_2`)
    3. Maximum time to establish a connection
    4. Whether to use environment variables to configure the proxy
    5. Proxy address
    6. Proxy port
    7. User for the proxy
    8. Password for the proxy
    9. Hosts that should be excluded from proxying

## Client declarative

It is suggested to use special annotations to create a declarative client:

* `@HttpClient` - indicates that the interface is a declarative HTTP client
* `@HttpRoute` - specifies [HTTP request type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) and request path

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient(configPath = "path.to.config") //(1)!
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

    1. The path to the configuration of this particular client

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient(configPath = "path.to.config") //(1)!
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

    1. The path to the configuration of this particular client

Example configuration in the case of the `path.to.config` path described in the `DeclarativeHttpClientConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    path {
        to {
            config {
                url = "https://localhost:8090" //(1)!
                requestTimeout = "10s" //(2)!
                telemetry {
                    logging {
                        enabled = true //(3)!
                    }
                    metrics {
                        enabled = true //(4)!
                        slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(5)!
                    }
                    telemetry {
                        enabled = true //(6)!
                    }
                }
            }
        }
    }
    ```

    1. URL of the service where requests will be sent
    2. Maximum request time
    3. Enables module logging
    4. Enables module metrics
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    6. Enables module tracing

=== ":simple-yaml: `YAML`"

    ```yaml
    path:
      to:
        config:
          url: "https://localhost:8090" //(1)!
          requestTimeout: "10s" //(2)!
          telemetry:
            logging:
              enabled: true #(3)!
            metrics:
              enabled: true #(4)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(5)!
            telemetry:
              enabled: true #(6)!
    ```

    1. URL of the service where requests will be sent
    2. Maximum request time
    3. Enables module logging
    4. Enables module metrics
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    6. Enables module tracing

### Method Configuration

Using the above HTTP client example, it is possible to configure separately some of the parameters for a particular method, the configuration path
is determined by the path to the client and the method name, in the example above the configuration is `path.to.config`
and method `hello` the final path will be `path.to.config.getHello`

===! ":material-code-json: `Hocon`"

    ```javascript
    path {
        to {
            config {
                hello {
                    requestTimeout = "10s" //(1)!
                    telemetry {
                        logging {
                            enabled = true //(2)!
                        }
                        metrics {
                            enabled = true //(3)!
                            slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(4)!
                        }
                        telemetry {
                            enabled = true //(5)!
                        }
                    }
                }
            }
        }
    }
    ```

    1.  Maximum method query time
    2.  Enables module logging
    3.  Includes module metrics
    4.  Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    5.  Enables module tracing

=== ":simple-yaml: `YAML`"

    ```yaml
    path:
      to:
        config:
          hello:  
            requestTimeout: "10s" #(1)!
            telemetry:
              logging:
                enabled: true #(2)!
              metrics:
                enabled: true #(3)!
                slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(4)!
              telemetry:
                enabled: true #(5)!
    ```

    1.  Maximum method query time
    2.  Enables module logging
    3.  Includes module metrics
    4.  Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    5.  Enables module tracing

### Request

The section describes HTTP request transformations at a declarative HTTP client.
It is suggested to use special annotations to specify request parameters.

#### Path parameter

`@Path` - denotes the value of the request path part, the parameter itself is specified in `{quote}` in the path
and the name of the parameter is specified in `value` or is equal to the name of the method argument by default.

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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
is required to use the `@Json` annotation:

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

    By default, all arguments declared in a method are **required** (*NotNull*).

=== ":simple-kotlin: `Kotlin`"

    By default, all arguments declared in a method that do not use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax are considered **required** (*NotNull*).

#### Optional parameters

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

By default, the conversion will only be applied for `2xx` HTTP status codes,
for all others a `HttpClientResponseException` exception will be thrown, which contains [HTTP status code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status), response body and response headers.

#### Conversion by Code

If specific conversions are required depending on the [HTTP status code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) of the response, you can use the `@ResponseCodeMapper` annotation to specify a
correspondence between the HTTP status code and the `HttpClientResponseMapper` resolver.

You can also use `ResponseCodeMapper.DEFAULT` as an indication of the default behavior for all unlisted status codes.

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)

## Interceptors

You can create interceptors to change behavior or create additional behavior using the `HttpClientInterceptor` class.
Interceptors can be applied to specific methods or to the entire `@HttpClient` class:

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

    ```java
    HttpClientRequest request = HttpClientRequestBuilder.of("POST", "http://localhost:8090/pets/{petId}")
            .templateParam("petId", "1")
            .queryParam("page", 1)
            .header("token", "12345")
            .body(HttpBody.plaintext("refresh"))
            .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequestBuilderImpl("POST", "http://localhost:8090/pets/{petId}")
        .templateParam("petId", "1")
        .queryParam("page", 1)
        .header("token", "12345")
        .body(HttpBody.plaintext("refresh"))
        .build()
    ```
