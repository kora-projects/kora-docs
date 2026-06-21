---
description: "Explains Kora SOAP client setup, SOAP client configuration, usage patterns, generated clients, and wsdl2java Gradle plugin integration. Use when working with SoapClientModule, @SoapClient, wsdl2java, JAX-WS, SOAPAction, WebServiceClient."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora SOAP client setup, SOAP client configuration, usage patterns, generated clients, and wsdl2java Gradle plugin integration; key triggers include SoapClientModule, @SoapClient, wsdl2java, JAX-WS, SOAPAction, WebServiceClient."
---

`SOAP` — это протокол обмена `XML`-сообщениями, который часто используется для интеграции с внешними системами через `HTTP` и контракт `WSDL`.
Модуль `soap-client` создает клиентские реализации для интерфейсов, размеченных `javax.jws.WebService` или `jakarta.jws.WebService`, и регистрирует их в графе приложения.

Обычно такие интерфейсы и связанные `JAXB`-классы генерируются из `WSDL`, например с помощью `wsdl2java`.
После генерации Kora создает реализацию клиента, подключает к ней `HTTP-клиент`, `XML`-преобразование и телеметрию.

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

**Требуется** подключить реализацию [`HTTP-клиента`](http-client.md), например `http-client-ok`.

## Описание { #description }

Подразумевается, что в приложении уже есть интерфейсы, размеченные `javax.jws.WebService` или `jakarta.jws.WebService`.
Они могут быть написаны вручную, но чаще создаются из `WSDL` отдельным инструментом, например [Gradle-плагином](#wsdl2java-plugin).

На основании таких интерфейсов Kora создает реализации SOAP-клиентов с суффиксом `SoapClientImpl` в том же пакете.
Также создается модуль с суффиксом `SoapClientModule`, который регистрирует конфигурацию и сам клиент в графе приложения.

После этого конфигурация и `SOAP-клиент` становятся доступны для внедрения зависимостей автоматически.

## Конфигурация { #configuration }

Все конфигурации для `SOAP-клиентов` создаются с префиксом `soapClient`.
Основная часть конфигурации клиента находится под именем сервиса из аннотации `@WebService`.

Имя секции выбирается в таком порядке:

1. `name` из `@WebService`
2. `serviceName` из `@WebService`
3. `portName` из `@WebService`
4. имя интерфейса

`SOAP-клиент` с именем `SimpleService` будет иметь конфигурацию с путем `soapClient.SimpleService`.

Пример полной конфигурации, описанной в классе `SoapServiceConfig`:

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

    1.  `URL` сервиса, куда будут отправляться запросы (`обязательная`, по умолчанию не указано).
    2.  Максимальное время выполнения запроса (по умолчанию: `60s`).
    3.  Включает логирование модуля (по умолчанию: `false`).
    4.  Включает метрики модуля (по умолчанию: `true`).
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    6.  Дополнительные теги для метрик (по умолчанию: `{}`).
    7.  Включает трассировку модуля (по умолчанию: `true`).
    8.  Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

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

    1.  `URL` сервиса, куда будут отправляться запросы (`обязательная`, по умолчанию не указано).
    2.  Максимальное время выполнения запроса (по умолчанию: `60s`).
    3.  Включает логирование модуля (по умолчанию: `false`).
    4.  Включает метрики модуля (по умолчанию: `true`).
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    6.  Дополнительные теги для метрик (по умолчанию: `{}`).
    7.  Включает трассировку модуля (по умолчанию: `true`).
    8.  Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#soap-client).

`SOAP-клиент` использует подключенный `HttpClient` и отправляет запросы на адрес из параметра `url`.
Если у метода в `@WebMethod` задан `action`, клиент добавит HTTP-заголовок `SOAPAction`.
Если сервер вернет `SOAP Fault`, клиент преобразует его в исключение.

## Использование { #usage }

После создания всех компонентов `SOAP-клиент` становится доступен для внедрения.
Ниже показан пример для клиента `SimpleService`:

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

## Плагин `wsdl2java` { #wsdl2java-plugin }

[Gradle-плагин](https://github.com/bjornvester/wsdl2java-gradle-plugin) может использоваться как один из вариантов для создания интерфейсов, размеченных `javax.jws.WebService` или `jakarta.jws.WebService`,
а также `JAXB`-классов на основании `WSDL`.

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

Предположим, что есть `WSDL`, где объявлен сервис `SimpleService`.
Тогда настройка плагина для генерации с `jakarta`-аннотациями будет выглядеть так:

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
