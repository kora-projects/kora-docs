---
description: "Explains Kora SOAP client setup, configuration, usage, generated clients, envelope processors and WS-Security, multipart/MTOM and RPC-style operations, logging, exception handling, testing, and the wsdl2java Gradle plugin. Use when working with SoapClientModule, wsdl2java, jakarta.jws.WebService, SOAPAction, SoapFaultException, SoapEnvelopeProcessorsUtils."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora SOAP client setup, configuration, usage patterns, generated clients, envelope processors and WS-Security authorization, multipart/MTOM and RPC-style operations, logger customization, exception handling, testing, and wsdl2java Gradle plugin integration; key triggers include SoapClientModule, SoapServiceConfig, wsdl2java, jakarta.jws.WebService, SOAPAction, SoapException, SoapFaultException, SoapInvalidHttpResponseException, SoapEnvelopeProcessorsUtils, wssAuth, DefaultSoapClientLoggerFactory."
---

`SOAP` is a protocol for exchanging `XML` messages, often used for integration with external systems over `HTTP` and a `WSDL` contract.
The `soap-client` module creates client implementations for interfaces annotated with `jakarta.jws.WebService` and registers them in the application graph.

Usually, such interfaces and related `JAXB` classes are generated from `WSDL`, for example with `wsdl2java`.
After generation, Kora creates the client implementation and connects it to an `HTTP client`, `XML` mapping, and telemetry.

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:soap-client"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends SoapClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:soap-client")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : SoapClientModule
    ```

**Requires** an [`HTTP client`](http-client.md) implementation (`http-client-jdk`, `http-client-ok` or `http-client-apache`)
and a configuration module ([HOCON](config.md#hocon) or [YAML](config.md#yaml)) to be present in the application.

The `soap-client` artifact already brings the `jakarta` / `JAXB` runtime the client needs, so no extra declarations are required:

- `org.glassfish.jaxb:jaxb-runtime` — `4.0.9`
- `jakarta.xml.ws:jakarta.xml.ws-api` — `4.0.3`
- `jakarta.xml.bind:jakarta.xml.bind-api` — `4.0.5`
- `commons-codec:commons-codec` — `1.22.1`

If another plugin or dependency in the build pins different versions of these artifacts, align them so that exactly one `JAXB` runtime ends up on the classpath.

## Description { #description }

The application is expected to already have interfaces annotated with `jakarta.jws.WebService`.
They can be written manually, but are usually created from `WSDL` by a separate tool, for example a [Gradle plugin](#wsdl2java-plugin).

Based on such interfaces, the annotation processor (bundled in the `annotation-processors` / `symbol-processors` artifact) creates in the same package:

- A client implementation named `$<Interface>_SoapClientImpl` implementing the `@WebService` interface. Its constructor is
  `(HttpClient, SoapClientTelemetryFactory, SoapServiceConfig, Function<SoapEnvelope, SoapEnvelope>)`, where the last argument is the
  optional [request envelope processor](#request-customization) and may be `null`. In `Java` the processor additionally emits a
  three-argument convenience constructor without the processor; both constructors declare `JAXBException`.
- A module named `$<Interface>_SoapClientModule` annotated with `@Module`, which registers two `@DefaultComponent` factories:
    - `SoapServiceConfig` tagged with `@Tag(<Interface>.class)`, read from the `soapClient.<service name>` configuration path.
    - The client itself, injecting `HttpClient`, `SoapClientTelemetryFactory`, the tagged `SoapServiceConfig`
      and an **optional** `Function<SoapEnvelope, SoapEnvelope>` tagged with `@Tag(<Interface>.class)`.

The generated module is registered in the application graph automatically — it does not have to be added to `@KoraApp` by hand.
After that, the configuration and the `SOAP client` become available for dependency injection.

### How it works { #how-it-works }

At runtime the generated client uses the connected `HttpClient` and behaves as follows:

- Sends an `HTTP POST` request with `Content-Type: text/xml` to the address from the `url` configuration parameter.
- Adds the `SOAPAction` `HTTP` header only when `action` is set on the method's `@WebMethod` annotation.
- Applies the `timeout` configuration value as the request timeout.
- Treats `HTTP 200` as a successful response and unmarshals the body into the method's return type.
- Treats `HTTP 500` as a `SOAP Fault` and converts it either to a [typed WSDL fault exception](#exception-handling) or to `SoapFaultException`.
- Raises `SoapInvalidHttpResponseException` for any other `HTTP` status code.
- Parses [`multipart` responses](#multipart) (`XOP` / `MTOM` attachments) automatically.

All generated methods are **synchronous** — the call blocks until the response is read and mapped.

## Configuration { #configuration }

All configurations for `SOAP clients` are created with the `soapClient` prefix.
The main part of the client configuration is placed under the service name from the `@WebService` annotation.

The section name is selected in this order:

1. `name` from `@WebService`
2. `serviceName` from `@WebService`
3. `portName` from `@WebService`
4. interface name

A `SOAP client` named `SimpleService` will have the `soapClient.SimpleService` configuration path.

Basic configuration parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    soapClient {
        SimpleService {
            url = "https://localhost:8090" //(1)!
            timeout = "60s" //(2)!
        }
    }
    ```

    1. Service `URL` where requests will be sent (required, no default).
    2. Maximum request execution time (default: `60s`).

=== ":simple-yaml: `YAML`"

    ```yaml
    soapClient:
      SimpleService:
        url: "https://localhost:8090" #(1)!
        timeout: "60s" #(2)!
    ```

    1. Service `URL` where requests will be sent (required, no default).
    2. Maximum request execution time (default: `60s`).

??? note "Full Configuration"

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
                        enabled = false //(4)!
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

        1. Service `URL` where requests will be sent (required, no default).
        2. Maximum request execution time (default: `60s`).
        3. Enables module logging (default: `false`).
        4. Enables module metrics (default: `false`).
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
                enabled: false #(4)!
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

        1. Service `URL` where requests will be sent (required, no default).
        2. Maximum request execution time (default: `60s`).
        3. Enables module logging (default: `false`).
        4. Enables module metrics (default: `false`).
        5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
        6. Additional tags for metrics (default: `{}`).
        7. Enables module tracing (default: `true`).
        8. Additional attributes for tracing (default: `{}`).

Module metrics are described in the [Metrics Reference](metrics.md#soap-client) section.

The configuration is described by the `SoapServiceConfig` interface. The `url` parameter is **required**:
if the whole section or the `url` value is missing, the application graph fails to build with a `ConfigValueException`.

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

### Multipart responses { #multipart }

When the server answers with a `multipart/related` body (`MTOM` / `XOP` attachments), the client parses it without any extra configuration:
the `XML` part named by the `start` parameter of `Content-Type` is unmarshalled as the `SOAP` envelope, and `<xop:Include href="cid:…"/>`
references are resolved against the remaining parts. The bytes of a referenced part are taken as they arrived — the part's
`Content-Transfer-Encoding` header is not applied, so the attachment has to be sent in binary form.

The `Content-Type` header of such a response **must** carry both the `boundary` and the `start` parameters, otherwise the response is rejected
with an `IllegalArgumentException`.

A `WSDL` element of type `xsd:base64Binary` is generated as a `byte[]` field, and the attachment content is placed into it:

===! ":fontawesome-brands-java: `Java`"

    ```java
    TestResponse response = service.test(request);
    byte[] content = response.getContent(); //(1)!
    ```

    1. Content of the attachment referenced by `<xop:Include/>` in the response envelope.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = service.test(request)
    val content: ByteArray = response.content //(1)!
    ```

    1. Content of the attachment referenced by `<xop:Include/>` in the response envelope.

### RPC style { #rpc }

Operations of a service bound with `<soap:binding style="rpc"/>` are supported as well.
For such operations `wsdl2java` generates a `void` method whose output parts are `jakarta.xml.ws.Holder` arguments,
and the client fills those holders from the response:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var part1 = new Holder<String>();
    var part2 = new Holder<String>();

    service.test("value", part1, part2); //(1)!

    String first = part1.value;
    String second = part2.value;
    ```

    1. The request element is built from the `IN` parameters; `OUT` parameters are returned through the holders.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val part1 = Holder<String>()
    val part2 = Holder<String>()

    service.test("value", part1, part2) //(1)!

    val first = part1.value
    val second = part2.value
    ```

    1. The request element is built from the `IN` parameters; `OUT` parameters are returned through the holders.

## Request customization { #request-customization }

`SOAP` clients do not use the `@InterceptWith` mechanism of [declarative HTTP clients](http-client.md).
Instead, the generated client accepts a `Function<SoapEnvelope, SoapEnvelope>` envelope processor.
The processor is applied to the request `SOAP` envelope before it is marshalled and sent — this is the extension point for adding
`SOAP` headers (authorization, tracing, custom elements) or otherwise transforming the outgoing envelope.

The generated module declares that processor as an **optional dependency** tagged with `@Tag(<Interface>.class)`.
Registering a component with that type and tag is enough — no other wiring is needed.
In `Kotlin` the type must be imported as `java.util.function.Function`, otherwise it resolves to the single-argument `kotlin.Function`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SoapModule {

        @Tag(SimpleService.class)
        default Function<SoapEnvelope, SoapEnvelope> simpleServiceEnvelopeProcessor() {
            return SoapEnvelopeProcessorsUtils.wssAuth("username", "password"); //(1)!
        }
    }
    ```

    1. Any `Function<SoapEnvelope, SoapEnvelope>` can be used here; `SoapEnvelopeProcessorsUtils.wssAuth` is a built-in one.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SoapModule {

        @Tag(SimpleService::class)
        fun simpleServiceEnvelopeProcessor(): Function<SoapEnvelope, SoapEnvelope> {
            return SoapEnvelopeProcessorsUtils.wssAuth("username", "password") //(1)!
        }
    }
    ```

    1. Any `Function<SoapEnvelope, SoapEnvelope>` can be used here; `SoapEnvelopeProcessorsUtils.wssAuth` is a built-in one.

A custom processor can add arbitrary `SOAP` headers by appending to `envelope.getHeader().getAny()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SoapModule {

        @Tag(SimpleService.class)
        default Function<SoapEnvelope, SoapEnvelope> simpleServiceEnvelopeProcessor() {
            return envelope -> {
                envelope.getHeader().getAny().add(myHeaderElement); //(1)!
                return envelope;
            };
        }
    }
    ```

    1. An `org.w3c.dom.Element` or a `JAXB` object known to the client's `JAXBContext`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SoapModule {

        @Tag(SimpleService::class)
        fun simpleServiceEnvelopeProcessor(): Function<SoapEnvelope, SoapEnvelope> {
            return Function { envelope ->
                envelope.header.any.add(myHeaderElement) //(1)!
                envelope
            }
        }
    }
    ```

    1. An `org.w3c.dom.Element` or a `JAXB` object known to the client's `JAXBContext`.

Because the generated client factory is a `@DefaultComponent`, a factory of your own that returns the client **interface** type
overrides it entirely. That is only needed when the client must be built by hand — the `SoapServiceConfig` dependency then has to be
resolved with `@Tag(<Interface>.class)`, the tag under which the generated module registers it:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SoapModule {

        default SimpleService simpleService(HttpClient httpClient,
                                            SoapClientTelemetryFactory telemetryFactory,
                                            @Tag(SimpleService.class) SoapServiceConfig config) {
            var processor = SoapEnvelopeProcessorsUtils.wssAuth("username", "password");
            try {
                return new $SimpleService_SoapClientImpl(httpClient, telemetryFactory, config, processor);
            } catch (Exception e) {
                throw new IllegalStateException(e);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SoapModule {

        fun simpleService(httpClient: HttpClient,
                          telemetryFactory: SoapClientTelemetryFactory,
                          @Tag(SimpleService::class) config: SoapServiceConfig): SimpleService {
            val processor = SoapEnvelopeProcessorsUtils.wssAuth("username", "password")
            return `$SimpleService_SoapClientImpl`(httpClient, telemetryFactory, config, processor)
        }
    }
    ```

### Authorization { #authorization }

`SoapEnvelopeProcessorsUtils.wssAuth(username, password)` is a built-in processor that adds a
[WS-Security](https://en.wikipedia.org/wiki/WS-Security) `UsernameToken` header (`Username` plus a plaintext `Password`)
to every request envelope. Wire it exactly as shown above by registering it as the tagged envelope processor.

## Logging { #logging }

Client logging is off by default and is enabled with `telemetry.logging.enabled`.
Each client writes into two `SLF4J` loggers named after the canonical name of the `@WebService` interface:

- `<package>.<Interface>.request`
- `<package>.<Interface>.response`

===! ":material-code-json: `Hocon`"

    ```javascript
    soapClient.SimpleService.telemetry.logging.enabled = true

    logging.levels {
        "io.koraframework.example.generated.soap.SimpleService.request" = "TRACE" //(1)!
        "io.koraframework.example.generated.soap.SimpleService.response" = "TRACE"
    }
    ```

    1. `SOAP` envelopes are written only at the `TRACE` level.

=== ":simple-yaml: `YAML`"

    ```yaml
    soapClient:
      SimpleService:
        telemetry:
          logging:
            enabled: true

    logging:
      levels:
        "io.koraframework.example.generated.soap.SimpleService.request": "TRACE" #(1)!
        "io.koraframework.example.generated.soap.SimpleService.response": "TRACE"
    ```

    1. `SOAP` envelopes are written only at the `TRACE` level.

What is written where:

- `SoapService requesting` — every request, with the `clientConfigPath`, `soapService` and `soapMethod` key-values.
  The request `XML` is added as `soapRequestBody` **only** when the request logger is at `TRACE`.
- `SoapService received response` — a successful response, additionally with `soapStatus=success`.
  The response `XML` is added as `soapResponseBody` **only** when the response logger is at `TRACE`.
- `SoapService received 'failure'` — a `SOAP Fault`, with `soapStatus=failure`, `soapFaultCode` and `soapFaultActor`,
  or a transport/mapping error, with `soapStatus=failure` and `exceptionType`. Both are written at `INFO`.

Nothing is written when the corresponding logger is below `INFO`, even if `telemetry.logging.enabled` is `true`.

To mask or transform the logged envelopes (for example, to hide sensitive data), register a `@Component` that extends
`DefaultSoapClientLoggerFactory` and returns a logger overriding `prepareRequestBodyForLog` / `prepareResponseBodyForLog`.
`SoapClientModule` takes such a component as an optional dependency of the telemetry factory and uses it for every client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MaskingSoapClientLoggerFactory extends DefaultSoapClientLoggerFactory {

        @Override
        public DefaultSoapClientLogger create(DefaultSoapClientTelemetry.TelemetryContext context) {
            var requestLog = LoggerFactory.getLogger(context.clientCanonicalName() + ".request");
            var responseLog = LoggerFactory.getLogger(context.clientCanonicalName() + ".response");
            return new MaskingLogger(requestLog, responseLog, context);
        }

        private static final class MaskingLogger extends DefaultSoapClientLoggerFactory.DefaultSoapClientLogger {

            private MaskingLogger(Logger requestLog,
                                  Logger responseLog,
                                  DefaultSoapClientTelemetry.TelemetryContext context) {
                super(requestLog, responseLog, context);
            }

            @Override
            protected String prepareRequestBodyForLog(byte[] requestXml) {
                return "<masked/>";
            }

            @Override
            protected String prepareResponseBodyForLog(byte[] xml) {
                return new String(xml, StandardCharsets.UTF_8);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MaskingSoapClientLoggerFactory : DefaultSoapClientLoggerFactory() {

        override fun create(context: DefaultSoapClientTelemetry.TelemetryContext): DefaultSoapClientLoggerFactory.DefaultSoapClientLogger {
            val requestLog = LoggerFactory.getLogger(context.clientCanonicalName() + ".request")
            val responseLog = LoggerFactory.getLogger(context.clientCanonicalName() + ".response")
            return MaskingLogger(requestLog, responseLog, context)
        }

        private class MaskingLogger(
            requestLog: Logger,
            responseLog: Logger,
            context: DefaultSoapClientTelemetry.TelemetryContext
        ) : DefaultSoapClientLoggerFactory.DefaultSoapClientLogger(requestLog, responseLog, context) {

            override fun prepareRequestBodyForLog(requestXml: ByteArray): String {
                return "<masked/>"
            }

            override fun prepareResponseBodyForLog(xml: ByteArray): String {
                return String(xml, StandardCharsets.UTF_8)
            }
        }
    }
    ```

## Exception handling { #exception-handling }

All `SOAP` client failures are unchecked and extend the base `SoapException` (a `RuntimeException`),
so a single `catch (SoapException e)` handles all of them, or a specific subtype can be caught.

Main exception types:

- `SoapException` — base unchecked exception for `SOAP` client failures; also thrown directly for transport and `I/O` errors of the underlying `HTTP client`.
- `SoapFaultException` — the server returned a `SOAP Fault` that does not match a typed `WSDL` fault. `getFault()` returns a `SoapFault` exposing `getFaultcode()` (`QName`), `getFaultstring()`, `getFaultactor()`, and `getDetail()`.
- `SoapInvalidHttpResponseException` — the server returned an unexpected `HTTP` status code (anything other than `200` or `500`). The message contains the code and up to the first 500 bytes of the response body.
- `SoapRequestMarshallingException` — the request envelope could not be marshalled to `XML`.
- `SoapResponseUnmarshallingException` — the response `XML` could not be unmarshalled.

When a `WSDL` operation declares faults (`<wsdl:fault>`), the generator emits typed checked exceptions annotated with `@WebFault`,
and the method throws them directly when the returned fault `detail` matches one of them. If the fault does not match any
declared type, `SoapFaultException` is thrown instead.

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        var response = service.test(request);
        // ... use the response
    } catch (TestError1Msg e) {                     //(1)!
        // handle a specific declared WSDL fault
    } catch (SoapFaultException e) {                //(2)!
        SoapFault fault = e.getFault();
        var code = fault.getFaultcode();
        var message = fault.getFaultstring();
    } catch (SoapInvalidHttpResponseException e) {
        // unexpected HTTP status code
    } catch (SoapRequestMarshallingException | SoapResponseUnmarshallingException e) {
        // XML (un)marshalling failure
    } catch (SoapException e) {
        // any other transport/HTTP SOAP failure
    }
    ```

    1. Typed `@WebFault` exception generated from a `<wsdl:fault>`; the concrete class name comes from the `WSDL`.
    2. Any `SOAP Fault` that does not match a declared typed fault.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        val response = service.test(request)
        // ... use the response
    } catch (e: TestError1Msg) {                    //(1)!
        // handle a specific declared WSDL fault
    } catch (e: SoapFaultException) {               //(2)!
        val fault = e.fault
        val code = fault.faultcode
        val message = fault.faultstring
    } catch (e: SoapInvalidHttpResponseException) {
        // unexpected HTTP status code
    } catch (e: SoapRequestMarshallingException) {
        // request XML marshalling failure
    } catch (e: SoapResponseUnmarshallingException) {
        // response XML unmarshalling failure
    } catch (e: SoapException) {
        // any other transport/HTTP SOAP failure
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
The example below overrides the `SOAP_CLIENT_URL` environment substitution used by `soapClient.SimpleService.url`,
stubs the response envelope and invokes `service.test(request)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @TestcontainersMockServer(mode = ContainerMode.PER_CLASS)
    @KoraAppTest(Application.class)
    class SimpleServiceTests implements KoraAppTestConfigModifier {

        @ConnectionMockServer
        private MockServerConnection mockserverConnection;

        @TestComponent
        private SimpleService service;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty("SOAP_CLIENT_URL", mockserverConnection.params().uri().toString());
        }

        @Test
        void testCall() throws Exception {
            mockserverConnection.client()
                .when(HttpRequest.request().withMethod("POST").withPath("/"))
                .respond(HttpResponse.response().withBody(new XmlBody("""
                    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                    <ns2:Envelope xmlns:ns2="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns3="http://kora.tinkoff.ru/simple/service">
                        <ns2:Header/>
                        <ns2:Body>
                            <ns3:TestResponse>
                                <val1>1</val1>
                            </ns3:TestResponse>
                        </ns2:Body>
                    </ns2:Envelope>
                    """)));

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
    @TestcontainersMockServer(mode = ContainerMode.PER_CLASS)
    @KoraAppTest(Application::class)
    class SimpleServiceTests : KoraAppTestConfigModifier {

        @ConnectionMockServer
        lateinit var mockserverConnection: MockServerConnection

        @TestComponent
        lateinit var service: SimpleService

        override fun config(): KoraConfigModification =
            KoraConfigModification.ofSystemProperty("SOAP_CLIENT_URL", mockserverConnection.params().uri().toString())

        @Test
        fun testCall() {
            mockserverConnection.client()
                .`when`(request().withMethod("POST").withPath("/"))
                .respond(response().withBody(XmlBody("""
                    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                    <ns2:Envelope xmlns:ns2="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns3="http://kora.tinkoff.ru/simple/service">
                        <ns2:Header/>
                        <ns2:Body>
                            <ns3:TestResponse>
                                <val1>1</val1>
                            </ns3:TestResponse>
                        </ns2:Body>
                    </ns2:Envelope>
                    """.trimIndent())))

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

A [Gradle plugin](https://github.com/bjornvester/wsdl2java-gradle-plugin) can be used as one option for creating interfaces annotated with `jakarta.jws.WebService`,
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
        packageName = "io.koraframework.example.generated.soap"
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
        cxfVersion.set("4.0.2")
        wsdlDir.set(layout.projectDirectory.dir("src/main/resources/wsdl"))
        useJakarta.set(true)
        markGenerated.set(true)
        verbose.set(false)
        packageName.set("io.koraframework.example.generated.soap")
        generatedSourceDir.set(layout.buildDirectory.dir("generated/sources/wsdl2java/java"))
        includesWithOptions.set(
            mapOf(
                "**/simple-service.wsdl" to listOf(
                    "-wsdlLocation",
                    "https://kora.tinkoff.ru/simple/service?wsdl"
                )
            )
        )
    }

    sourceSets.main {
        java.srcDir(layout.buildDirectory.dir("generated/sources/wsdl2java/java")) //(1)!
    }
    ```

    1. The plugin generates `Java` sources; the directory has to be added to the `Java` source set so that `KSP` sees the `@WebService` interfaces.

The `useJakarta = true` option is **required** — the annotation processor only recognises `jakarta.jws.WebService`.
Kora itself is built and tested against `CXF` `4.2.3`, so `cxfVersion` can be raised to that version if the generated code has to match.
