Модуль для создания и регистрации SOAP сервисов по классам аннотированным `javax.jws.WebService`/`jakarta.jws.WebService`.

## Подключение

===! ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:soap-client"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends SoapClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:soap-client")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : SoapClientModule
    ```

**Требуется** подключить реализацию [HTTP клиента](http-client.md).

## Описание

Подразумевается что у нас есть классы аннотированные `javax.jws.WebService`/`jakarta.jws.WebService`, которые могут быть созданы другими средствами, 
такими как [Gradle Plugin](#плагин-wsdl2java).

На основании таких классов с помощью Kora создаются реализации SOAP клиента с суффиксом Impl в том же пакете и регистрирует их как модуль с конфигурацей.

Затем конфигурация и сам SOAP сервис становятся доступны для внедрения зависимостей автоматически.

## Конфигурация

Все конфигурации для SOAP клиентов создаются с префиксом `soapClient`, 
а основная часть конфигурации клиента находится под именем клиента из WSDL аннотации `@WebService`, 
который соответствует зачастую тегу `<wsdl:binding type="tns:SimpleService">` в конфигурации WSDL.

Сервис SOAP с именем `SimpleService` будет иметь конфигурацию с путем `soapClient.SimpleService`.

Пример полной конфигурации, описанной в классе `SoapServiceConfig` (указаны примеры значений или значения по умолчанию):

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
                }
                tracing {
                    enabled = true //(6)!
                }
            }
        }
    }
    ```

    1.  URL сервиса куда будут отправляться запросы (**обязательный**)
    2.  Максимальное время запроса
    3.  Включает логгирование модуля (по умолчанию `false`)
    4.  Включает метрики модуля (по умолчанию `true`)
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    6.  Включает трассировку модуля (по умолчанию `true`)

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
          telemetry:
            enabled: true #(6)!
    ```

    1.  URL сервиса куда будут отправляться запросы (**обязательный**)
    2.  Максимальное время запроса
    3.  Включает логгирование модуля (по умолчанию `false`)
    4.  Включает метрики модуля (по умолчанию `true`)
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    6.  Включает трассировку модуля (по умолчанию `true`)

## Использование

После создания всех компонент созданный SOAP сервис становится доступен для внедрения, ниже показан пример для `SimpleService` сервиса:

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

## Плагин wsdl2java

[Gradle Plugin](https://github.com/bjornvester/wsdl2java-gradle-plugin) может использоваться как один из вариантов для создания классов аннотированных `javax.jws.WebService`/`jakarta.jws.WebService`
на основании [WSDL](https://coderlessons.com/tutorials/xml-tekhnologii/uznaite-wsdl/wsdl-kratkoe-rukovodstvo).

### Подключение

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

### Использование

Предположим что у нас есть WSDL, где объявлен сервис `SimpleService` то настройка плагина для `jakarta` аннотацией будет выглядить так:

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
