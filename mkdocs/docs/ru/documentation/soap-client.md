---
description: "Explains Kora SOAP client setup, configuration, usage, generated clients, request customization and WS-Security, exception handling, testing, and the wsdl2java Gradle plugin. Use when working with SoapClientModule, wsdl2java, JAX-WS, SOAPAction, WebServiceClient, SoapFaultException, SoapEnvelopeProcessors."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora SOAP client setup, configuration, usage patterns, generated clients, envelope processors and WS-Security authorization, body-mapper logging, exception handling, testing, and wsdl2java Gradle plugin integration; key triggers include SoapClientModule, SoapServiceConfig, wsdl2java, JAX-WS, SOAPAction, WebServiceClient, SoapException, SoapFaultException, InvalidHttpResponseSoapException, SoapEnvelopeProcessors, wssAuth."
---

`SOAP` — это протокол обмена сообщениями в формате `XML`, который часто используется для интеграции с внешними системами по `HTTP` и контракту `WSDL`.
Модуль `soap-client` создаёт реализации клиентов для интерфейсов, помеченных аннотацией `javax.jws.WebService` или `jakarta.jws.WebService`, и регистрирует их в графе приложения.

Обычно такие интерфейсы и связанные с ними классы `JAXB` генерируются из `WSDL`, например с помощью `wsdl2java`.
После генерации Kora создаёт реализацию клиента и подключает её к `HTTP-клиенту`, преобразованию `XML` и телеметрии.

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:soap-client"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends SoapClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:soap-client")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : SoapClientModule
    ```

**Требует** наличия в приложении реализации [`HTTP-клиента`](http-client.md) (например `http-client-jdk` или `http-client-ok`)
и модуля конфигурации ([HOCON](config.md#hocon) или [YAML](config.md#yaml)).

Когда интерфейсы `SOAP` и классы `JAXB` генерируются [плагином `wsdl2java`](#wsdl2java-plugin) в режиме `jakarta`,
необходимая среда выполнения `jakarta.*` / `JAXB` уже предоставляется сгенерированными исходниками и `JDK`.
В этом случае транзитивные зависимости `jakarta` / `Glassfish` / `activation` модуля `soap-client` можно исключить, чтобы избежать конфликтов версий:

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

## Описание { #description }

Предполагается, что в приложении уже есть интерфейсы, помеченные аннотацией `javax.jws.WebService` или `jakarta.jws.WebService`
(поддерживаются оба семейства аннотаций). Их можно написать вручную, но обычно они создаются из `WSDL`
отдельным инструментом, например [Gradle-плагином](#wsdl2java-plugin).

На основе таких интерфейсов процессор аннотаций (входящий в артефакт `annotation-processors`) создаёт в том же пакете:

- Реализацию клиента с именем `$<Interface>_SoapClientImpl`, зарегистрированную как `@DefaultComponent` в графе приложения.
- Модуль с именем `$<Interface>_SoapClientModule`, помеченный аннотацией `@Module`, который регистрирует `SoapServiceConfig`
  (с тегом `@Tag(<Interface>.class)`) и сам клиент.

После этого конфигурация и `SOAP-клиент` автоматически становятся доступны для внедрения зависимостей.

### Как это работает { #how-it-works }

Во время работы сгенерированный клиент использует подключённый `HttpClient` и ведёт себя следующим образом:

- Отправляет запрос `HTTP POST` с `Content-Type: text/xml` на адрес из параметра конфигурации `url`.
- Добавляет `HTTP`-заголовок `SOAPAction` только когда в аннотации `@WebMethod` метода задан `action`.
- Применяет значение конфигурации `timeout` как предельное время выполнения запроса.
- Трактует `HTTP 200` как успешный ответ и десериализует тело в тип возвращаемого значения метода.
- Трактует `HTTP 500` как `SOAP Fault` и преобразует его либо в [типизированное исключение ошибки WSDL](#exception-handling), либо в `SoapFaultException`.
- Выбрасывает `InvalidHttpResponseSoapException` для любого другого кода состояния `HTTP`.
- Автоматически разбирает ответы `multipart` (вложения `XOP` / `MTOM`).
- Для каждого `@WebMethod` генерирует синхронный метод и метод `<method>Async`, возвращающий `CompletionStage` для [неблокирующих вызовов](#asynchronous).

## Конфигурация { #configuration }

Все конфигурации `SOAP-клиентов` создаются с префиксом `soapClient`.
Основная часть конфигурации клиента размещается под именем службы из аннотации `@WebService`.

Имя секции выбирается в следующем порядке:

1. `name` из `@WebService`
2. `serviceName` из `@WebService`
3. `portName` из `@WebService`
4. имя интерфейса

У `SOAP-клиента` с именем `SimpleService` путь конфигурации будет `soapClient.SimpleService`.

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

    1. `URL` службы, куда будут отправляться запросы (обязательная, по умолчанию не указано).
    2. Максимальное время выполнения запроса (по умолчанию: `60s`).
    3. Включает логирование модуля (по умолчанию: `false`).
    4. Включает метрики модуля (по умолчанию: `true`).
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

    1. `URL` службы, куда будут отправляться запросы (обязательная, по умолчанию не указано).
    2. Максимальное время выполнения запроса (по умолчанию: `60s`).
    3. Включает логирование модуля (по умолчанию: `false`).
    4. Включает метрики модуля (по умолчанию: `true`).
    5. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    6. Дополнительные теги для метрик (по умолчанию: `{}`).
    7. Включает трассировку модуля (по умолчанию: `true`).
    8. Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#soap-client).

Конфигурация описывается интерфейсом `SoapServiceConfig`. Параметр `url` **обязателен**:
если он отсутствует в конфигурации, граф приложения не собирается и выбрасывается `ConfigValueExtractionException`
(отсутствие значения после разбора). Параметр `timeout` по умолчанию равен `60s`.

Конфигурация регистрируется в графе под `@Tag(<Interface>.class)`, поэтому при
[ручном создании](#request-customization) клиента зависимость `SoapServiceConfig` должна разрешаться с тем же тегом.

## Использование { #usage }

После создания всех компонентов `SOAP-клиент` становится доступен для внедрения.
Ниже приведён пример для клиента `SimpleService`:

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

### Асинхронность { #asynchronous }

Для каждого `@WebMethod` генератор также создаёт метод `<method>Async`, возвращающий `CompletionStage<T>` для неблокирующих вызовов.
Асинхронный метод объявляется в сгенерированном классе `$<Interface>_SoapClientImpl`, а не в интерфейсе `WSDL`,
поэтому для его использования нужно привести внедрённый клиент к типу сгенерированной реализации:

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

## Настройка запроса { #request-customization }

`SOAP`-клиенты не используют механизм `@InterceptWith` из [декларативных HTTP-клиентов](http-client.md#interceptors).
Вместо этого сгенерированный `$<Interface>_SoapClientImpl` предоставляет **дополнительный конструктор**, принимающий обработчик
конверта `Function<SoapEnvelope, SoapEnvelope>`. Обработчик применяется к конверту `SOAP` запроса
перед его сериализацией и отправкой — это точка расширения для добавления заголовков `SOAP` (авторизация, трассировка,
произвольные элементы) или иного преобразования исходящего конверта.

У сгенерированной реализации два конструктора:

- `(HttpClient, SoapClientTelemetryFactory, SoapServiceConfig)` — используется сгенерированным `@DefaultComponent`; применяет `Function.identity()` (без изменений).
- `(HttpClient, SoapClientTelemetryFactory, SoapServiceConfig, Function<SoapEnvelope, SoapEnvelope>)` — позволяет задать собственный обработчик.

Чтобы использовать собственный обработчик, зарегистрируйте свою фабрику, которая возвращает тип **интерфейса** клиента и создаёт
реализацию с обработчиком. Поскольку она предоставляет тот же тип интерфейса, ваша фабрика **переопределяет** сгенерированный
`@DefaultComponent`. Разрешайте `SoapServiceConfig` через `@Tag(<Interface>.class)` — тег, под которым его регистрирует сгенерированный модуль:

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

    1. Здесь можно использовать любую `Function<SoapEnvelope, SoapEnvelope>`; `SoapEnvelopeProcessors.wssAuth` — встроенная.

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

    1. Здесь можно использовать любую `Function<SoapEnvelope, SoapEnvelope>`; `SoapEnvelopeProcessors.wssAuth` — встроенная.

Собственный обработчик может добавлять произвольные заголовки `SOAP`, дописывая их в `envelope.getHeader().getAny()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Function<SoapEnvelope, SoapEnvelope> processor = envelope -> {
        envelope.getHeader().getAny().add(myHeaderElement); // org.w3c.dom.Element или объект JAXB
        return envelope;
    };
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val processor = Function<SoapEnvelope, SoapEnvelope> { envelope ->
        envelope.header.any.add(myHeaderElement) // org.w3c.dom.Element или объект JAXB
        envelope
    }
    ```

### Авторизация (WS-Security) { #authorization }

`SoapEnvelopeProcessors.wssAuth(username, password)` — встроенный обработчик, который добавляет в каждый конверт запроса заголовок
`UsernameToken` стандарта [WS-Security](https://en.wikipedia.org/wiki/WS-Security) (`Username` и `Password` в открытом виде).
Подключите его ровно так, как показано выше, передав его в качестве обработчика конверта в конструктор клиента.

## Логирование { #logging }

Когда `telemetry.logging.enabled` равно `true`, клиент логирует полные конверты `SOAP` запроса и ответа (тела `XML`).
Чтобы замаскировать или преобразовать логируемые данные (например, скрыть чувствительные данные), переопределите компонент `SoapClientLogger.SoapClientLoggerBodyMapper`.
`SoapClientModule` предоставляет его как `@DefaultComponent`, поэтому пользовательская реализация `@Component` заменяет его:

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

## Обработка исключений { #exception-handling }

Все ошибки `SOAP`-клиента являются непроверяемыми (unchecked). Транспортные и `HTTP`-ошибки наследуются от базового `SoapException`
(`RuntimeException`), поэтому их можно обработать одним `catch (SoapException e)` или перехватить конкретный подтип.
Исключения сериализации/десериализации `XML` наследуются напрямую от `RuntimeException` (а не от `SoapException`), поэтому их нужно
перехватывать отдельно.

Основные типы исключений:

- `SoapException` — базовое непроверяемое исключение (наследуется от `RuntimeException`) для транспортных и `HTTP`-ошибок `SOAP`-клиента.
- `SoapFaultException` (наследуется от `SoapException`) — сервер вернул `SOAP Fault`, который не соответствует типизированной ошибке `WSDL`. `getFault()` возвращает `SoapFault`, предоставляющий `getFaultcode()` (`QName`), `getFaultstring()`, `getFaultactor()` и `getDetail()`.
- `InvalidHttpResponseSoapException` (наследуется от `SoapException`) — сервер вернул неожиданный код состояния `HTTP` (любой, кроме `200` или `500`).
- `SoapRequestMarshallingException` (наследуется от `RuntimeException`, а **не** от `SoapException`) — конверт запроса не удалось сериализовать в `XML`.
- `SoapResponseUnmarshallingException` (наследуется от `RuntimeException`, а **не** от `SoapException`) — `XML` ответа не удалось десериализовать.

Когда операция `WSDL` объявляет ошибки (`<wsdl:fault>`), генератор создаёт типизированные проверяемые исключения, помеченные аннотацией `@WebFault`,
и метод выбрасывает их напрямую, когда `detail` возвращённой ошибки соответствует одному из них. Если ошибка не соответствует ни одному
объявленному типу, вместо этого выбрасывается `SoapFaultException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        var response = service.test(request);
        // ... использование ответа
    } catch (MyServiceFault e) {                    //(1)!
        // обработка конкретной объявленной ошибки WSDL
    } catch (SoapFaultException e) {                //(2)!
        SoapFault fault = e.getFault();
        var code = fault.getFaultcode();
        var message = fault.getFaultstring();
    } catch (InvalidHttpResponseSoapException e) {
        // неожиданный код состояния HTTP
    } catch (SoapException e) {
        // любая другая транспортная/HTTP-ошибка SOAP
    } catch (SoapRequestMarshallingException | SoapResponseUnmarshallingException e) {
        // ошибка (де)сериализации XML — наследуется от RuntimeException, а не от SoapException
    }
    ```

    1. Типизированное исключение `@WebFault`, сгенерированное из `<wsdl:fault>`; конкретное имя класса берётся из `WSDL`.
    2. Любой `SOAP Fault`, не соответствующий объявленной типизированной ошибке.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        val response = service.test(request)
        // ... использование ответа
    } catch (e: MyServiceFault) {                   //(1)!
        // обработка конкретной объявленной ошибки WSDL
    } catch (e: SoapFaultException) {               //(2)!
        val fault = e.fault
        val code = fault.faultcode
        val message = fault.faultstring
    } catch (e: InvalidHttpResponseSoapException) {
        // неожиданный код состояния HTTP
    } catch (e: SoapException) {
        // любая другая транспортная/HTTP-ошибка SOAP
    } catch (e: SoapRequestMarshallingException) {
        // ошибка сериализации XML запроса — наследуется от RuntimeException, а не от SoapException
    } catch (e: SoapResponseUnmarshallingException) {
        // ошибка десериализации XML ответа — наследуется от RuntimeException, а не от SoapException
    }
    ```

    1. Типизированное исключение `@WebFault`, сгенерированное из `<wsdl:fault>`; конкретное имя класса берётся из `WSDL`.
    2. Любой `SOAP Fault`, не соответствующий объявленной типизированной ошибке.

### Низкоуровневая модель результата { #result-model }

Внутри движок запросов `SoapRequestExecutor` возвращает `SoapResult` — запечатанный (sealed) интерфейс с двумя record:
`SoapResult.Success(Object body)` и `SoapResult.Failure(SoapFault fault, String faultMessage)`.
Сгенерированный клиент отображает `Success` в типизированный ответ, а `Failure` — в типизированное исключение ошибки или `SoapFaultException`,
поэтому обычно с `SoapResult` напрямую работать не приходится.

## Тестирование { #testing }

Клиент можно протестировать с помощью [`@KoraAppTest`](junit5.md), внедрив его как `@TestComponent` и указав в `url` адрес мок-сервера.
В примере ниже `SOAP_CLIENT_URL` переопределяется на адрес мок-сервера, вызывается `service.test(request)` и проверяется типизированный ответ:

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
            // мок-сервер отвечает конвертом TestResponse на запрос ниже
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
            // мок-сервер отвечает конвертом TestResponse на запрос ниже
            val request = TestRequest().apply {
                val1 = "1"
                val2 = "2"
            }

            val response = service.test(request)
            assertEquals("1", response.val1)
        }
    }
    ```

Конверт запроса, отправляемый на сервер, и конверт ответа, который он возвращает, в передаче по сети выглядят так:

```xml
<!-- Запрос -->
<ns2:Envelope xmlns:ns2="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns3="http://kora.tinkoff.ru/simple/service">
    <ns2:Header/>
    <ns2:Body>
        <ns3:TestRequest>
            <val1>1</val1>
            <val2>2</val2>
        </ns3:TestRequest>
    </ns2:Body>
</ns2:Envelope>

<!-- Ответ -->
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

[Gradle-плагин](https://github.com/bjornvester/wsdl2java-gradle-plugin) можно использовать как один из вариантов для создания интерфейсов, помеченных аннотацией `javax.jws.WebService` или `jakarta.jws.WebService`,
а также классов `JAXB` на основе `WSDL`.

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
        packageName = "ru.tinkoff.kora.generated.soap"
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

Опция `useJakarta = true` заставляет плагин генерировать интерфейсы с аннотациями `jakarta.jws`.
Установите её в `false` (или опустите), чтобы вместо этого генерировать аннотации `javax.jws` — процессор аннотаций поддерживает оба варианта.
