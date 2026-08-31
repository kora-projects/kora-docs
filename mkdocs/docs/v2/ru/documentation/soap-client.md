---
description: "Explains Kora SOAP client setup, configuration, usage, generated clients, envelope processors and WS-Security, multipart/MTOM and RPC-style operations, logging, exception handling, testing, and the wsdl2java Gradle plugin. Use when working with SoapClientModule, wsdl2java, jakarta.jws.WebService, SOAPAction, SoapFaultException, SoapEnvelopeProcessorsUtils."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora SOAP client setup, configuration, usage patterns, generated clients, envelope processors and WS-Security authorization, multipart/MTOM and RPC-style operations, logger customization, exception handling, testing, and wsdl2java Gradle plugin integration; key triggers include SoapClientModule, SoapServiceConfig, wsdl2java, jakarta.jws.WebService, SOAPAction, SoapException, SoapFaultException, SoapInvalidHttpResponseException, SoapEnvelopeProcessorsUtils, wssAuth, DefaultSoapClientLoggerFactory."
---

`SOAP` — это протокол обмена сообщениями в формате `XML`, который часто используется для интеграции с внешними системами по `HTTP` и контракту `WSDL`.
Модуль `soap-client` создаёт реализации клиентов для интерфейсов, помеченных аннотацией `jakarta.jws.WebService`, и регистрирует их в графе приложения.

Обычно такие интерфейсы и связанные с ними классы `JAXB` генерируются из `WSDL`, например с помощью `wsdl2java`.
После генерации Kora создаёт реализацию клиента и связывает её с `HTTP-клиентом`, отображением `XML` и телеметрией.

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:soap-client"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends SoapClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:soap-client")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : SoapClientModule
    ```

**Требуется** наличие в приложении реализации [`HTTP-клиента`](http-client.md) (`http-client-jdk`, `http-client-ok` или `http-client-apache`)
и модуля конфигурации ([HOCON](config.md#hocon) либо [YAML](config.md#yaml)).

Артефакт `soap-client` уже приносит нужный клиенту рантайм `jakarta` / `JAXB`, поэтому объявлять его отдельно не требуется:

- `org.glassfish.jaxb:jaxb-runtime` — `4.0.9`
- `jakarta.xml.ws:jakarta.xml.ws-api` — `4.0.3`
- `jakarta.xml.bind:jakarta.xml.bind-api` — `4.0.5`
- `commons-codec:commons-codec` — `1.22.1`

Если другой плагин или зависимость в сборке фиксируют иные версии этих артефактов, версии стоит выровнять, чтобы на classpath оказался ровно один рантайм `JAXB`.

## Описание { #description }

Предполагается, что в приложении уже есть интерфейсы, помеченные аннотацией `jakarta.jws.WebService`.
Их можно написать вручную, но обычно они создаются из `WSDL` отдельным инструментом, например [Gradle-плагином](#wsdl2java-plugin).

На основе таких интерфейсов процессор аннотаций (входящий в артефакт `annotation-processors` / `symbol-processors`) создаёт в том же пакете:

- Реализацию клиента с именем `$<Interface>_SoapClientImpl`, реализующую интерфейс `@WebService`. Её конструктор —
  `(HttpClient, SoapClientTelemetryFactory, SoapServiceConfig, Function<SoapEnvelope, SoapEnvelope>)`, где последний аргумент —
  необязательный [обработчик конверта запроса](#request-customization), он может быть `null`. В `Java` процессор дополнительно
  создаёт конструктор из трёх аргументов без обработчика; оба конструктора объявляют `JAXBException`.
- Модуль с именем `$<Interface>_SoapClientModule`, помеченный аннотацией `@Module`, который регистрирует две фабрики `@DefaultComponent`:
    - `SoapServiceConfig` с тегом `@Tag(<Interface>.class)`, читаемый по пути конфигурации `soapClient.<имя сервиса>`.
    - Сам клиент, которому внедряются `HttpClient`, `SoapClientTelemetryFactory`, конфигурация с тегом
      и **необязательный** `Function<SoapEnvelope, SoapEnvelope>` с тегом `@Tag(<Interface>.class)`.

Сгенерированный модуль регистрируется в графе приложения автоматически — добавлять его в `@KoraApp` вручную не нужно.
После этого конфигурация и `SOAP-клиент` становятся доступны для внедрения зависимостей.

### Как это работает { #how-it-works }

Во время работы сгенерированный клиент использует подключённый `HttpClient` и ведёт себя следующим образом:

- Отправляет запрос `HTTP POST` с `Content-Type: text/xml` на адрес из параметра конфигурации `url`.
- Добавляет `HTTP`-заголовок `SOAPAction` только когда в аннотации `@WebMethod` метода задан `action`.
- Применяет значение конфигурации `timeout` как предельное время выполнения запроса.
- Трактует `HTTP 200` как успешный ответ и десериализует тело в тип возвращаемого значения метода.
- Трактует `HTTP 500` как `SOAP Fault` и преобразует его либо в [типизированное исключение ошибки WSDL](#exception-handling), либо в `SoapFaultException`.
- Выбрасывает `SoapInvalidHttpResponseException` для любого другого кода состояния `HTTP`.
- Автоматически разбирает [ответы `multipart`](#multipart) (вложения `XOP` / `MTOM`).

Все сгенерированные методы **синхронные** — вызов блокируется до тех пор, пока ответ не будет прочитан и отображён.

## Конфигурация { #configuration }

Все конфигурации `SOAP-клиентов` создаются с префиксом `soapClient`.
Основная часть конфигурации клиента размещается под именем службы из аннотации `@WebService`.

Имя секции выбирается в следующем порядке:

1. `name` из `@WebService`
2. `serviceName` из `@WebService`
3. `portName` из `@WebService`
4. имя интерфейса

У `SOAP-клиента` с именем `SimpleService` путь конфигурации будет `soapClient.SimpleService`.

Основные параметры конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    soapClient {
        SimpleService {
            url = "https://localhost:8090" //(1)!
            timeout = "60s" //(2)!
        }
    }
    ```

    1. `URL` службы, куда будут отправляться запросы (обязательный, без значения по умолчанию).
    2. Максимальное время выполнения запроса (по умолчанию: `60s`).

=== ":simple-yaml: `YAML`"

    ```yaml
    soapClient:
      SimpleService:
        url: "https://localhost:8090" #(1)!
        timeout: "60s" #(2)!
    ```

    1. `URL` службы, куда будут отправляться запросы (обязательный, без значения по умолчанию).
    2. Максимальное время выполнения запроса (по умолчанию: `60s`).

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной классом `SoapServiceConfig`:

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

        1. `URL` службы, куда будут отправляться запросы (обязательный, без значения по умолчанию).
        2. Максимальное время выполнения запроса (по умолчанию: `60s`).
        3. Включает логгирование модуля (по умолчанию: `false`).
        4. Включает метрики модуля (по умолчанию: `false`).
        5. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
        6. Дополнительные теги для метрик (по умолчанию: `{}`).
        7. Включает трассировку модуля (по умолчанию: `true`).
        8. Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

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

        1. `URL` службы, куда будут отправляться запросы (обязательный, без значения по умолчанию).
        2. Максимальное время выполнения запроса (по умолчанию: `60s`).
        3. Включает логгирование модуля (по умолчанию: `false`).
        4. Включает метрики модуля (по умолчанию: `false`).
        5. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
        6. Дополнительные теги для метрик (по умолчанию: `{}`).
        7. Включает трассировку модуля (по умолчанию: `true`).
        8. Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#soap-client).

Конфигурация описывается интерфейсом `SoapServiceConfig`. Параметр `url` **обязателен**:
если отсутствует вся секция или само значение `url`, граф приложения не соберётся и упадёт с `ConfigValueException`.

Конфигурация регистрируется в графе под тегом `@Tag(<Interface>.class)`, поэтому при [ручном создании клиента](#request-customization)
зависимость `SoapServiceConfig` нужно запрашивать с тем же тегом.

## Использование { #usage }

После создания всех компонентов `SOAP-клиент` становится доступен для внедрения.
Ниже пример для клиента `SimpleService`:

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

### Вызов { #invocation }

Сгенерированный метод принимает тип запроса и возвращает типизированный ответ.
Для клиента `SimpleService` с операцией `test`:

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

### Ответы multipart { #multipart }

Если сервер отвечает телом `multipart/related` (вложения `MTOM` / `XOP`), клиент разбирает его без дополнительной настройки:
`XML`-часть, указанная параметром `start` заголовка `Content-Type`, десериализуется как конверт `SOAP`, а ссылки
`<xop:Include href="cid:…"/>` разрешаются по остальным частям. Байты вложения берутся ровно в том виде, в каком пришли —
заголовок `Content-Transfer-Encoding` части не учитывается, поэтому вложение должно передаваться в бинарном виде.

Заголовок `Content-Type` такого ответа **обязан** содержать одновременно параметры `boundary` и `start`, иначе ответ будет отклонён
с `IllegalArgumentException`.

Элемент `WSDL` типа `xsd:base64Binary` генерируется как поле `byte[]`, куда и помещается содержимое вложения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    TestResponse response = service.test(request);
    byte[] content = response.getContent(); //(1)!
    ```

    1. Содержимое вложения, на которое ссылается `<xop:Include/>` в конверте ответа.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = service.test(request)
    val content: ByteArray = response.content //(1)!
    ```

    1. Содержимое вложения, на которое ссылается `<xop:Include/>` в конверте ответа.

### Стиль RPC { #rpc }

Операции сервиса с привязкой `<soap:binding style="rpc"/>` также поддерживаются.
Для таких операций `wsdl2java` генерирует метод с типом `void`, у которого выходные части передаются аргументами
`jakarta.xml.ws.Holder`, а клиент заполняет эти holder-ы из ответа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var part1 = new Holder<String>();
    var part2 = new Holder<String>();

    service.test("value", part1, part2); //(1)!

    String first = part1.value;
    String second = part2.value;
    ```

    1. Элемент запроса собирается из параметров `IN`; параметры `OUT` возвращаются через holder-ы.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val part1 = Holder<String>()
    val part2 = Holder<String>()

    service.test("value", part1, part2) //(1)!

    val first = part1.value
    val second = part2.value
    ```

    1. Элемент запроса собирается из параметров `IN`; параметры `OUT` возвращаются через holder-ы.

## Настройка запроса { #request-customization }

`SOAP-клиенты` не используют механизм `@InterceptWith` из [декларативных HTTP-клиентов](http-client.md).
Вместо этого сгенерированный клиент принимает обработчик конверта `Function<SoapEnvelope, SoapEnvelope>`.
Обработчик применяется к конверту `SOAP` запроса перед сериализацией и отправкой — это точка расширения для добавления
заголовков `SOAP` (авторизация, трассировка, произвольные элементы) или иного преобразования исходящего конверта.

Сгенерированный модуль объявляет такой обработчик **необязательной зависимостью** с тегом `@Tag(<Interface>.class)`.
Достаточно зарегистрировать компонент этого типа с этим тегом — больше ничего связывать не нужно.
В `Kotlin` тип нужно импортировать как `java.util.function.Function`, иначе он разрешится в `kotlin.Function` с одним параметром типа:

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

    1. Здесь может использоваться любая `Function<SoapEnvelope, SoapEnvelope>`; `SoapEnvelopeProcessorsUtils.wssAuth` — встроенная реализация.

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

    1. Здесь может использоваться любая `Function<SoapEnvelope, SoapEnvelope>`; `SoapEnvelopeProcessorsUtils.wssAuth` — встроенная реализация.

Собственный обработчик может добавлять произвольные заголовки `SOAP`, дописывая их в `envelope.getHeader().getAny()`:

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

    1. `org.w3c.dom.Element` либо объект `JAXB`, известный `JAXBContext` клиента.

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

    1. `org.w3c.dom.Element` либо объект `JAXB`, известный `JAXBContext` клиента.

Поскольку сгенерированная фабрика клиента помечена `@DefaultComponent`, собственная фабрика, возвращающая тип **интерфейса** клиента,
полностью её переопределяет. Это нужно только когда клиент требуется собрать вручную — тогда зависимость `SoapServiceConfig`
следует запрашивать с тегом `@Tag(<Interface>.class)`, под которым её регистрирует сгенерированный модуль:

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

### Авторизация { #authorization }

`SoapEnvelopeProcessorsUtils.wssAuth(username, password)` — встроенный обработчик, добавляющий в каждый конверт запроса заголовок
[WS-Security](https://en.wikipedia.org/wiki/WS-Security) `UsernameToken` (`Username` и `Password` открытым текстом).
Подключается ровно так, как показано выше — регистрацией обработчика конверта с тегом.

## Логирование { #logging }

Логирование клиента выключено по умолчанию и включается параметром `telemetry.logging.enabled`.
Каждый клиент пишет в два логгера `SLF4J`, названных по каноническому имени интерфейса `@WebService`:

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

    1. Конверты `SOAP` пишутся только на уровне `TRACE`.

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

    1. Конверты `SOAP` пишутся только на уровне `TRACE`.

Что и куда пишется:

- `SoapService requesting` — каждый запрос, с ключами `clientConfigPath`, `soapService` и `soapMethod`.
  `XML` запроса добавляется как `soapRequestBody` **только** когда логгер запроса выставлен в `TRACE`.
- `SoapService received response` — успешный ответ, дополнительно с `soapStatus=success`.
  `XML` ответа добавляется как `soapResponseBody` **только** когда логгер ответа выставлен в `TRACE`.
- `SoapService received 'failure'` — `SOAP Fault`, с `soapStatus=failure`, `soapFaultCode` и `soapFaultActor`,
  либо ошибка транспорта или отображения, с `soapStatus=failure` и `exceptionType`. Обе записи пишутся на уровне `INFO`.

Если соответствующий логгер ниже уровня `INFO`, не пишется ничего, даже когда `telemetry.logging.enabled` равно `true`.

Чтобы маскировать или преобразовывать логируемые конверты (например, скрыть чувствительные данные), нужно зарегистрировать `@Component`,
наследующий `DefaultSoapClientLoggerFactory` и возвращающий логгер с переопределёнными `prepareRequestBodyForLog` / `prepareResponseBodyForLog`.
`SoapClientModule` принимает такой компонент как необязательную зависимость фабрики телеметрии и использует его для всех клиентов:

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

## Обработка исключений { #exception-handling }

Все ошибки `SOAP-клиента` являются непроверяемыми и наследуют базовое `SoapException` (`RuntimeException`),
поэтому один `catch (SoapException e)` покрывает их все, либо можно перехватывать конкретный подтип.

Основные типы исключений:

- `SoapException` — базовое непроверяемое исключение ошибок `SOAP-клиента`; также выбрасывается напрямую при ошибках транспорта и `I/O` нижележащего `HTTP-клиента`.
- `SoapFaultException` — сервер вернул `SOAP Fault`, который не соответствует ни одной типизированной ошибке `WSDL`. `getFault()` возвращает `SoapFault` с методами `getFaultcode()` (`QName`), `getFaultstring()`, `getFaultactor()` и `getDetail()`.
- `SoapInvalidHttpResponseException` — сервер вернул неожиданный код состояния `HTTP` (любой, кроме `200` и `500`). В сообщении содержатся код и первые 500 байт тела ответа.
- `SoapRequestMarshallingException` — конверт запроса не удалось сериализовать в `XML`.
- `SoapResponseUnmarshallingException` — `XML` ответа не удалось десериализовать.

Когда операция `WSDL` объявляет ошибки (`<wsdl:fault>`), генератор создаёт типизированные проверяемые исключения с аннотацией `@WebFault`,
и метод выбрасывает их напрямую, если `detail` полученной ошибки соответствует одному из них. Если ошибка не соответствует ни одному
объявленному типу, выбрасывается `SoapFaultException`.

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

    1. Типизированное исключение `@WebFault`, сгенерированное из `<wsdl:fault>`; конкретное имя класса берётся из `WSDL`.
    2. Любой `SOAP Fault`, не соответствующий объявленной типизированной ошибке.

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

    1. Типизированное исключение `@WebFault`, сгенерированное из `<wsdl:fault>`; конкретное имя класса берётся из `WSDL`.
    2. Любой `SOAP Fault`, не соответствующий объявленной типизированной ошибке.

### Низкоуровневая модель результата { #result-model }

Внутри движок выполнения запроса `SoapRequestExecutor` возвращает `SoapResult` — запечатанный интерфейс с двумя записями:
`SoapResult.Success(Object body)` и `SoapResult.Failure(SoapFault fault, String faultMessage)`.
Сгенерированный клиент отображает `Success` в типизированный ответ, а `Failure` — в типизированное исключение ошибки или `SoapFaultException`,
поэтому напрямую с `SoapResult` обычно работать не приходится.

## Тестирование { #testing }

Клиент можно тестировать с помощью [`@KoraAppTest`](junit5.md), внедрив его как `@TestComponent` и направив `url` на mock-сервер.
В примере ниже переопределяется подстановка переменной окружения `SOAP_CLIENT_URL`, используемая в `soapClient.SimpleService.url`,
задаётся заглушка конверта ответа и вызывается `service.test(request)`:

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

Конверт запроса, отправляемый на сервер, и конверт ответа, который он возвращает, в сыром виде выглядят так:

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

## Плагин `wsdl2java` { #wsdl2java-plugin }

Одним из вариантов создания интерфейсов с аннотацией `jakarta.jws.WebService`, а также классов `JAXB` на основе `WSDL`,
является [Gradle-плагин](https://github.com/bjornvester/wsdl2java-gradle-plugin).

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    Плагин `build.gradle`:
    ```groovy
    plugins {
        id "com.github.bjornvester.wsdl2java" version "2.0.2"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Плагин `build.gradle.kts`:
    ```groovy
    plugins {
        id("com.github.bjornvester.wsdl2java") version ("2.0.2")
    }
    ```

### Использование { #usage-2 }

Предположим, есть `WSDL`, в котором объявлена служба `SimpleService`.
Тогда конфигурация плагина для генерации с аннотациями `jakarta` будет выглядеть так:

===! ":fontawesome-brands-java: `Java`"

    Настройка плагина `build.gradle`:
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

    Настройка плагина `build.gradle.kts`:
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

    1. Плагин генерирует исходники на `Java`, поэтому каталог нужно добавить в `Java`-source set, чтобы `KSP` увидел интерфейсы `@WebService`.

Опция `useJakarta = true` **обязательна** — процессор аннотаций распознаёт только `jakarta.jws.WebService`.
Сама Kora собирается и тестируется на `CXF` `4.2.3`, поэтому `cxfVersion` можно поднять до этой версии, если сгенерированный код должен ей соответствовать.
