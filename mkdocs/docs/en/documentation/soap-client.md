---
description: "Explains Kora SOAP client setup, configuration, usage, generated clients, request customization and WS-Security, exception handling, testing, and the wsdl2java Gradle plugin. Use when working with SoapClientModule, wsdl2java, JAX-WS, SOAPAction, WebServiceClient, SoapFaultException, SoapEnvelopeProcessors."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora SOAP client setup, configuration, usage patterns, generated clients, envelope processors and WS-Security authorization, body-mapper logging, exception handling, testing, and wsdl2java Gradle plugin integration; key triggers include SoapClientModule, SoapServiceConfig, wsdl2java, JAX-WS, SOAPAction, WebServiceClient, SoapException, SoapFaultException, InvalidHttpResponseSoapException, SoapEnvelopeProcessors, wssAuth."
---

`SOAP` is a protocol for exchanging `XML` messages, often used for integration with external systems over `HTTP` and a `WSDL` contract.
The `soap-client` module creates client implementations for interfaces annotated with `javax.jws.WebService` or `jakarta.jws.WebService` and registers them in the application graph.

Usually, such interfaces and related `JAXB` classes are generated from `WSDL`, for example with `wsdl2java`.
After generation, Kora creates the client implementation and connects it to an `HTTP client`, `XML` mapping, and telemetry.

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:soap-client"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends SoapClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:soap-client")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : SoapClientModule
    ```

**Requires** an [`HTTP client`](http-client.md) implementation (for example `http-client-jdk` or `http-client-ok`)
and a configuration module ([HOCON](config.md#hocon) or [YAML](config.md#yaml)) to be present in the application.

When `SOAP` interfaces and `JAXB` classes are generated with the [`wsdl2java` plugin](#wsdl2java-plugin) in `jakarta` mode,
the required `jakarta.*` / `JAXB` runtime is already provided by the generated sources and the `JDK`.
In that case the transitive `jakarta` / `Glassfish` / `activation` dependencies of `soap-client` can be excluded to avoid version clashes:

===! ":fontawesome-brands-java: `Java`"

    `build.gradle`:
    ```groovy
    implementation("ru.tinkoff.kora:soap-client") {
        exclude group: "jakarta.xml"
        exclude group: "jakarta.jws"
        exclude group: "jakarta.xml.ws"
        exclude group: "jakarta.xml.bind"
        exclude group: "org.glassfish.jaxb"
        exclude group: "com.sun.activation"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:soap-client") {
        exclude(group = "jakarta.xml")
        exclude(group = "jakarta.jws")
        exclude(group = "jakarta.xml.ws")
        exclude(group = "jakarta.xml.bind")
        exclude(group = "org.glassfish.jaxb")
        exclude(group = "com.sun.activation")
    }
    ```

## Description { #description }

The application is expected to already have interfaces annotated with `javax.jws.WebService` or `jakarta.jws.WebService`
(both annotation families are supported). They can be written manually, but are usually created from `WSDL`
by a separate tool, for example a [Gradle plugin](#wsdl2java-plugin).

Based on such interfaces, the annotation processor (bundled in the `annotation-processors` artifact) creates in the same package:

- A client implementation named `$<Interface>_SoapClientImpl`, registered as a `@DefaultComponent` in the application graph.
- A module named `$<Interface>_SoapClientModule` annotated with `@Module`, which registers the `SoapServiceConfig`
  (tagged with `@Tag(<Interface>.class)`) and the client itself.

After that, the configuration and the `SOAP client` become available for dependency injection automatically.

### How it works { #how-it-works }

At runtime the generated client uses the connected `HttpClient` and behaves as follows:

- Sends an `HTTP POST` request with `Content-Type: text/xml` to the address from the `url` configuration parameter.
- Adds the `SOAPAction` `HTTP` header only when `action` is set on the method's `@WebMethod` annotation.
- Applies the `timeout` configuration value as the request timeout.
- Treats `HTTP 200` as a successful response and unmarshals the body into the method's return type.
- Treats `HTTP 500` as a `SOAP Fault` and converts it either to a [typed WSDL fault exception](#exception-handling) or to `SoapFaultException`.
- Raises `InvalidHttpResponseSoapException` for any other `HTTP` status code.
- Parses `multipart` (`XOP` / `MTOM` attachment) responses automatically.
- For every `@WebMethod` it generates a synchronous method and a `<method>Async` method returning `CompletionStage` for [non-blocking calls](#asynchronous).

## Configuration { #configuration }

All configurations for `SOAP clients` are created with the `soapClient` prefix.
The main part of the client configuration is placed under the service name from the `@WebService` annotation.

The section name is selected in this order:

1. `name` from `@WebService`
2. `serviceName` from `@WebService`
3. `portName` from `@WebService`
4. interface name

A `SOAP client` named `SimpleService` will have the `soapClient.SimpleService` configuration path.

Example of the complete configuration described by the `SoapServiceConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    soapClient {
        SimpleService {
            url = "https://localhost:8090" //(1)!
            timeout = "60s" //(2)!
            telemetry {
                logging {
                    enabled = false //(3)!
                }
                metrics {
                    enabled = true //(4)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(5)!
                    tags = { // (6)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(7)!
                    attributes = { // (8)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1. Service `URL` where requests will be sent (required, default: not specified).
    2. Maximum request execution time (default: `60s`).
    3. Enables module logging (default: `false`).
    4. Enables module metrics (default: `true`).
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    6. Additional tags for metrics (default: `{}`).
    7. Enables module tracing (default: `true`).
    8. Additional attributes for tracing (default: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    soapClient:
      SimpleService:
        url: "https://localhost:8090" #(1)!
        timeout: "60s" #(2)!
        telemetry:
          logging:
            enabled: false #(3)!
          metrics:
            enabled: true #(4)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(5)!
            tags: #(6)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(7)!
            attributes: #(8)!
              key1: value1
              key2: value2
    ```

    1. Service `URL` where requests will be sent (required, default: not specified).
    2. Maximum request execution time (default: `60s`).
    3. Enables module logging (default: `false`).
    4. Enables module metrics (default: `true`).
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    6. Additional tags for metrics (default: `{}`).
    7. Enables module tracing (default: `true`).
    8. Additional attributes for tracing (default: `{}`).

Module metrics are described in the [Metrics Reference](metrics.md#soap-client) section.

The configuration is described by the `SoapServiceConfig` interface. The `url` parameter is **required**:
if it is missing from the configuration, the application graph fails to build with a `ConfigValueExtractionException`
(missing value after parse). The `timeout` parameter defaults to `60s`.

The configuration is registered in the graph under `@Tag(<Interface>.class)`, so when a client is
[constructed manually](#request-customization) the `SoapServiceConfig` dependency must be resolved with that same tag.

## Usage { #usage }

After all components are created, the `SOAP client` becomes available for injection.
Below is an example for the `SimpleService` client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final SimpleService service;

        public SomeService(SimpleService service) {
            this.service = service;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(val service: SimpleService) {

    }
    ```

### Invocation { #invocation }

A generated method accepts the request type and returns the typed response.
For the `SimpleService` client with a `test` operation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final SimpleService service;

        public SomeService(SimpleService service) {
            this.service = service;
        }

        public String call() throws Exception {
            var request = new TestRequest();
            request.setVal1("1");
            request.setVal2("2");

            TestResponse response = service.test(request);
            return response.getVal1();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val service: SimpleService) {

        fun call(): String? {
            val request = TestRequest().apply {
                val1 = "1"
                val2 = "2"
            }

            val response = service.test(request)
            return response.val1
        }
    }
    ```

### Asynchronous { #asynchronous }

For every `@WebMethod`, the generator also creates a `<method>Async` method returning `CompletionStage<T>` for non-blocking calls.
The async method is declared on the generated `$<Interface>_SoapClientImpl` class rather than on the `WSDL` interface,
so to use it you cast the injected client to the generated implementation type:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final SimpleService service;

        public SomeService(SimpleService service) {
            this.service = service;
        }

        public CompletionStage<String> callAsync() {
            var request = new TestRequest();
            request.setVal1("1");
            request.setVal2("2");

            return (($SimpleService_SoapClientImpl) service).testAsync(request)
                .thenApply(TestResponse::getVal1);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val service: SimpleService) {

        fun callAsync(): CompletionStage<String?> {
            val request = TestRequest().apply {
                val1 = "1"
                val2 = "2"
            }

            return (service as `$SimpleService_SoapClientImpl`).testAsync(request)
                .thenApply { it.val1 }
        }
    }
    ```

## Request customization { #request-customization }

`SOAP` clients do not use the `@InterceptWith` mechanism of [declarative HTTP clients](http-client.md#interceptors).
Instead, the generated `$<Interface>_SoapClientImpl` provides a **secondary constructor** that accepts a
`Function<SoapEnvelope, SoapEnvelope>` envelope processor. The processor is applied to the request `SOAP` envelope
before it is marshalled and sent — this is the extension point for adding `SOAP` headers (authorization, tracing,
custom elements) or otherwise transforming the outgoing envelope.

The generated implementation has two constructors:

- `(HttpClient, SoapClientTelemetryFactory, SoapServiceConfig)` — used by the generated `@DefaultComponent`; applies `Function.identity()` (no changes).
- `(HttpClient, SoapClientTelemetryFactory, SoapServiceConfig, Function<SoapEnvelope, SoapEnvelope>)` — lets you supply a custom processor.

To use a custom processor, register your own factory that returns the client **interface** type and constructs the
implementation with the processor. Because it provides the same interface type, your factory **overrides** the generated
`@DefaultComponent`. Resolve `SoapServiceConfig` with `@Tag(<Interface>.class)` — the tag under which the generated module registers it:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SoapModule {

        default SimpleService simpleService(HttpClient httpClient,
                                            SoapClientTelemetryFactory telemetryFactory,
                                            @Tag(SimpleService.class) SoapServiceConfig config) {
            var processor = SoapEnvelopeProcessors.wssAuth("username", "password"); //(1)!
            try {
                return new $SimpleService_SoapClientImpl(httpClient, telemetryFactory, config, processor);
            } catch (Exception e) {
                throw new IllegalStateException(e);
            }
        }
    }
    ```

    1. Any `Function<SoapEnvelope, SoapEnvelope>` can be used here; `SoapEnvelopeProcessors.wssAuth` is a built-in one.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SoapModule {

        fun simpleService(httpClient: HttpClient,
                          telemetryFactory: SoapClientTelemetryFactory,
                          @Tag(SimpleService::class) config: SoapServiceConfig): SimpleService {
            val processor = SoapEnvelopeProcessors.wssAuth("username", "password") //(1)!
            return `$SimpleService_SoapClientImpl`(httpClient, telemetryFactory, config, processor)
        }
    }
    ```

    1. Any `Function<SoapEnvelope, SoapEnvelope>` can be used here; `SoapEnvelopeProcessors.wssAuth` is a built-in one.

A custom processor can add arbitrary `SOAP` headers by appending to `envelope.getHeader().getAny()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Function<SoapEnvelope, SoapEnvelope> processor = envelope -> {
        envelope.getHeader().getAny().add(myHeaderElement); // org.w3c.dom.Element or a JAXB object
        return envelope;
    };
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val processor = Function<SoapEnvelope, SoapEnvelope> { envelope ->
        envelope.header.any.add(myHeaderElement) // org.w3c.dom.Element or a JAXB object
        envelope
    }
    ```

### Authorization (WS-Security) { #authorization }

`SoapEnvelopeProcessors.wssAuth(username, password)` is a built-in processor that adds a
[WS-Security](https://en.wikipedia.org/wiki/WS-Security) `UsernameToken` header (`Username` plus a plaintext `Password`)
to every request envelope. Wire it exactly as shown above by passing it as the envelope processor to the client constructor.

## Logging { #logging }

When `telemetry.logging.enabled` is `true`, the client logs the full request and response `SOAP` envelopes (the `XML` bodies).
To mask or transform logged payloads (for example, to hide sensitive data), override the `SoapClientLogger.SoapClientLoggerBodyMapper`
component. `SoapClientModule` provides it as a `@DefaultComponent`, so a user `@Component` implementation replaces it:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MaskingBodyMapper implements SoapClientLogger.SoapClientLoggerBodyMapper {

        @Override
        public String mapRequest(String serviceName, String soapMethod, byte[] requestAsBytes) {
            return "<masked/>";
        }

        @Override
        public String mapResponseSuccess(String serviceName, String soapMethod, byte[] responseAsBytes) {
            return new String(responseAsBytes, StandardCharsets.UTF_8);
        }

        @Override
        public String mapResponseFailure(String serviceName, String soapMethod, byte[] responseAsBytes) {
            return new String(responseAsBytes, StandardCharsets.UTF_8);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MaskingBodyMapper : SoapClientLogger.SoapClientLoggerBodyMapper {

        override fun mapRequest(serviceName: String, soapMethod: String, requestAsBytes: ByteArray): String {
            return "<masked/>"
        }

        override fun mapResponseSuccess(serviceName: String, soapMethod: String, responseAsBytes: ByteArray): String {
            return String(responseAsBytes, StandardCharsets.UTF_8)
        }

        override fun mapResponseFailure(serviceName: String, soapMethod: String, responseAsBytes: ByteArray): String {
            return String(responseAsBytes, StandardCharsets.UTF_8)
        }
    }
    ```

## Exception handling { #exception-handling }

All `SOAP` client failures are unchecked. Transport and `HTTP` errors extend the base `SoapException`
(a `RuntimeException`), so a single `catch (SoapException e)` handles those, or a specific subtype can be caught.
The `XML` marshalling/unmarshalling exceptions extend `RuntimeException` directly (not `SoapException`), so they must
be caught separately.

Main exception types:

- `SoapException` — base unchecked exception (extends `RuntimeException`) for transport and `HTTP` `SOAP` client failures.
- `SoapFaultException` (extends `SoapException`) — the server returned a `SOAP Fault` that does not match a typed `WSDL` fault. `getFault()` returns a `SoapFault` exposing `getFaultcode()` (`QName`), `getFaultstring()`, `getFaultactor()`, and `getDetail()`.
- `InvalidHttpResponseSoapException` (extends `SoapException`) — the server returned an unexpected `HTTP` status code (anything other than `200` or `500`).
- `SoapRequestMarshallingException` (extends `RuntimeException`, **not** `SoapException`) — the request envelope could not be marshalled to `XML`.
- `SoapResponseUnmarshallingException` (extends `RuntimeException`, **not** `SoapException`) — the response `XML` could not be unmarshalled.

When a `WSDL` operation declares faults (`<wsdl:fault>`), the generator emits typed checked exceptions annotated with `@WebFault`,
and the method throws them directly when the returned fault `detail` matches one of them. If the fault does not match any
declared type, `SoapFaultException` is thrown instead.

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        var response = service.test(request);
        // ... use the response
    } catch (MyServiceFault e) {                    //(1)!
        // handle a specific declared WSDL fault
    } catch (SoapFaultException e) {                //(2)!
        SoapFault fault = e.getFault();
        var code = fault.getFaultcode();
        var message = fault.getFaultstring();
    } catch (InvalidHttpResponseSoapException e) {
        // unexpected HTTP status code
    } catch (SoapException e) {
        // any other transport/HTTP SOAP failure
    } catch (SoapRequestMarshallingException | SoapResponseUnmarshallingException e) {
        // XML (un)marshalling failure — extends RuntimeException, not SoapException
    }
    ```

    1. Typed `@WebFault` exception generated from a `<wsdl:fault>`; the concrete class name comes from the `WSDL`.
    2. Any `SOAP Fault` that does not match a declared typed fault.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        val response = service.test(request)
        // ... use the response
    } catch (e: MyServiceFault) {                   //(1)!
        // handle a specific declared WSDL fault
    } catch (e: SoapFaultException) {               //(2)!
        val fault = e.fault
        val code = fault.faultcode
        val message = fault.faultstring
    } catch (e: InvalidHttpResponseSoapException) {
        // unexpected HTTP status code
    } catch (e: SoapException) {
        // any other transport/HTTP SOAP failure
    } catch (e: SoapRequestMarshallingException) {
        // request XML marshalling failure — extends RuntimeException, not SoapException
    } catch (e: SoapResponseUnmarshallingException) {
        // response XML unmarshalling failure — extends RuntimeException, not SoapException
    }
    ```

    1. Typed `@WebFault` exception generated from a `<wsdl:fault>`; the concrete class name comes from the `WSDL`.
    2. Any `SOAP Fault` that does not match a declared typed fault.

### Low-level result model { #result-model }

Internally the request engine `SoapRequestExecutor` returns a `SoapResult`, a sealed interface with two records:
`SoapResult.Success(Object body)` and `SoapResult.Failure(SoapFault fault, String faultMessage)`.
The generated client maps `Success` to the typed response and `Failure` to a typed fault exception or `SoapFaultException`,
so you normally do not work with `SoapResult` directly.

## Testing { #testing }

The client can be tested with [`@KoraAppTest`](junit5.md) by injecting it as a `@TestComponent` and pointing `url` at a mock server.
The example below overrides `SOAP_CLIENT_URL` to the mock server address and invokes `service.test(request)`, checking the typed response:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SimpleServiceTests implements KoraAppTestConfigModifier {

        @TestComponent
        private SimpleService service;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty("SOAP_CLIENT_URL", "http://localhost:8080");
        }

        @Test
        void testCall() throws Exception {
            // the mock server responds with a TestResponse envelope for the request below
            var request = new TestRequest();
            request.setVal1("1");
            request.setVal2("2");

            var response = service.test(request);
            assertEquals("1", response.getVal1());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SimpleServiceTests : KoraAppTestConfigModifier {

        @TestComponent
        lateinit var service: SimpleService

        override fun config(): KoraConfigModification =
            KoraConfigModification.ofSystemProperty("SOAP_CLIENT_URL", "http://localhost:8080")

        @Test
        fun testCall() {
            // the mock server responds with a TestResponse envelope for the request below
            val request = TestRequest().apply {
                val1 = "1"
                val2 = "2"
            }

            val response = service.test(request)
            assertEquals("1", response.val1)
        }
    }
    ```

The request envelope sent to the server and the response envelope it returns look like this on the wire:

```xml
<!-- Request -->
<ns2:Envelope xmlns:ns2="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns3="http://kora.tinkoff.ru/simple/service">
    <ns2:Header/>
    <ns2:Body>
        <ns3:TestRequest>
            <val1>1</val1>
            <val2>2</val2>
        </ns3:TestRequest>
    </ns2:Body>
</ns2:Envelope>

<!-- Response -->
<ns2:Envelope xmlns:ns2="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns3="http://kora.tinkoff.ru/simple/service">
    <ns2:Header/>
    <ns2:Body>
        <ns3:TestResponse>
            <val1>1</val1>
        </ns3:TestResponse>
    </ns2:Body>
</ns2:Envelope>
```

## `wsdl2java` Plugin { #wsdl2java-plugin }

A [Gradle plugin](https://github.com/bjornvester/wsdl2java-gradle-plugin) can be used as one option for creating interfaces annotated with `javax.jws.WebService` or `jakarta.jws.WebService`,
as well as `JAXB` classes based on `WSDL`.

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    Plugin `build.gradle`:
    ```groovy
    plugins {
        id "com.github.bjornvester.wsdl2java" version "2.0.2"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Plugin `build.gradle.kts`:
    ```groovy
    plugins {
        id("com.github.bjornvester.wsdl2java") version ("2.0.2")
    }
    ```

### Usage { #usage-2 }

Suppose there is a `WSDL` where the `SimpleService` service is declared.
Then the plugin configuration for generation with `jakarta` annotations will look like this:

===! ":fontawesome-brands-java: `Java`"

    Plugin setup `build.gradle`:
    ```groovy
    wsdl2java {
        cxfVersion = "4.0.2"
        wsdlDir = layout.projectDirectory.dir("src/main/resources/wsdl")
        useJakarta = true
        markGenerated = true
        verbose = false
        packageName = "ru.tinkoff.kora.generated.soap"
        generatedSourceDir.set(layout.buildDirectory.dir("generated/sources/wsdl2java/java"))
        includesWithOptions = [
            "**/simple-service.wsdl": ["-wsdlLocation", "https://kora.tinkoff.ru/simple/service?wsdl"],
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Plugin setup `build.gradle.kts`:
    ```groovy
    wsdl2java {
        cxfVersion = "4.0.2"
        wsdlDir = layout.projectDirectory.dir("src/main/resources/wsdl")
        useJakarta = true
        markGenerated = true
        verbose = false
        packageName = "ru.tinkoff.kora.generated.soap"
        generatedSourceDir.set(layout.buildDirectory.dir("generated/sources/wsdl2java/java"))
        includesWithOptions.putAll(
            mapOf(
                "**/simple-service.wsdl" to listOf(
                    "-wsdlLocation",
                    "https://kora.tinkoff.ru/simple/service?wsdl"
                )
            )
        )
    }
    ```

The `useJakarta = true` option makes the plugin generate interfaces with `jakarta.jws` annotations.
Set it to `false` (or omit it) to generate `javax.jws` annotations instead — the annotation processor supports both.
