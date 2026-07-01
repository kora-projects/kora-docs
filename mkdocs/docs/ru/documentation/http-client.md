---
description: "Explains Kora HTTP clients, OkHttp, AsyncHttpClient, Java native client, declarative client annotations, request and response mapping, interceptors, and authorization. Use when working with @HttpClient, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora HTTP clients, OkHttp, AsyncHttpClient, Java native client, declarative client annotations, request and response mapping, interceptors, and authorization; key triggers include @HttpClient, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith, HttpClientModule, OkHttp."
---

Модуль `HTTP-клиента` описывает исходящие HTTP-вызовы приложения: от выбора транспортной реализации до преобразования запроса,
преобразования ответа, телеметрии и перехватчиков. В Kora можно описывать типизированные клиенты декларативно через `@HttpClient`
и `@HttpRoute` с тонким слоем абстракции, либо использовать общий интерфейс `HttpClient` напрямую, когда запрос нужно собрать в коде.

Декларативный подход подходит для большинства интеграций с внешними службами: контракт метода становится контрактом удаленного вызова,
а Kora во время компиляции создает реализацию без использования `Reflection` во время работы. Императивный подход полезен для низкоуровневых
или динамических сценариев, где путь, заголовки, параметры или тело запроса удобнее собирать вручную.

???+ tip "Совет"

    **Мы советуем** использовать подход, при котором первичен контракт в формате `OpenAPI`,
    а клиенты создаются с помощью генератора.
    Такой подход помогает сохранить согласованность контракта между потребителем и владельцем контракта
    и быстрее обновлять клиент при изменении контракта за счет замены файла описания.
    Подробнее про генератор смотрите в [разделе про генерацию из OpenAPI](openapi-codegen.md).

Если нужен пошаговый разбор перед справочным описанием, смотрите [HTTP-клиент](../guides/http-client.md) и [продвинутый HTTP-клиент](../guides/http-client-advanced.md).

## OkHttp { #okhttp }

Реализация `HTTP`-клиента основана на библиотеке [OkHttp](https://github.com/square/okhttp).
Учитывайте что реализация написана на Kotlin и использует соответствующие зависимости.
Лучше всего подходит для Kotlin сервисов, либо Java сервисов где нужна высокая производительность,
либо требуется поддержка HTTP 3, либо поддержка GZip сжатия, либо другие специфичные HTTP опции.

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:http-client-ok"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:http-client-ok")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OkHttpClientModule
    ```

### Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `OkHttpClientConfig` и `HttpClientConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  Следовать ли по [перенаправлениям в HTTP](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections) (по умолчанию: `true`)
    2.  Максимальная используемая версия `HTTP`-протокола, доступные значения: `HTTP_1_1` / `HTTP_2` / `HTTP_3` (по умолчанию: `HTTP_1_1`)
    3.  Пробовать ли повторно выполнить запрос при ошибке соединения; может влиять на предельное время установления соединения (по умолчанию: `true`)
    4.  Максимальное время на установление соединения (по умолчанию: `5s`)
    5.  Максимальное время на чтение ответа (по умолчанию: `2m`)
    6.  Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
    7.  Адрес прокси (`обязательная`, по умолчанию не указано)
    8.  Порт прокси (`обязательная`, по умолчанию не указано)
    9.  Пользователь для прокси (по умолчанию не указано, необязательно)
    10.  Пароль для прокси (по умолчанию не указано, необязательно)
    11.  Узлы, которые следует исключить из проксирования (по умолчанию не указано, необязательно)
    12.  Включает логирование модуля (по умолчанию: `false`)
    13.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
    14.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
    15.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
    16.  Использовать ли шаблон пути запроса при логировании; если не указано, шаблон используется всегда, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указано, необязательно)
    17.  Включает метрики модуля (по умолчанию: `true`)
    18.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    19.  Настройка тегов для метрик (по умолчанию: `{}`)
    20.  Включает трассировку модуля (по умолчанию: `true`)
    21.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  Следовать ли по [перенаправлениям в HTTP](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections) (по умолчанию: `true`)
    2.  Максимальная используемая версия `HTTP`-протокола, доступные значения: `HTTP_1_1` / `HTTP_2` / `HTTP_3` (по умолчанию: `HTTP_1_1`)
    3.  Пробовать ли повторно выполнить запрос при ошибке соединения; может влиять на предельное время установления соединения (по умолчанию: `true`)
    4.  Максимальное время на установление соединения (по умолчанию: `5s`)
    5.  Максимальное время на чтение ответа (по умолчанию: `2m`)
    6.  Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
    7.  Адрес прокси (`обязательная`, по умолчанию не указано)
    8.  Порт прокси (`обязательная`, по умолчанию не указано)
    9.  Пользователь для прокси (по умолчанию не указано, необязательно)
    10.  Пароль для прокси (по умолчанию не указано, необязательно)
    11.  Узлы, которые следует исключить из проксирования (по умолчанию не указано, необязательно)
    12.  Включает логирование модуля (по умолчанию: `false`)
    13.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
    14.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
    15.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
    16.  Использовать ли шаблон пути запроса при логировании; если не указано, шаблон используется всегда, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указано, необязательно)
    17.  Включает метрики модуля (по умолчанию: `true`)
    18.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    19.  Настройка тегов для метрик (по умолчанию: `{}`)
    20.  Включает трассировку модуля (по умолчанию: `true`)
    21.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#http-client).

#### Конфигуратор { #configurer }

Пример настройки построителя OkHttp клиента, `OkHttpConfigurer` должен быть доступен как компонент:

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

Реализация `HTTP`-клиента основана на библиотеке [Async HTTP Client](https://github.com/AsyncHttpClient/async-http-client).
Подходит для Java сервисов, где преобладают асинхронные вызовы.

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:http-client-async"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends AsyncHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:http-client-async")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : AsyncHttpClientModule
    ```

### Конфигурация { #configuration-2 }

Пример полной конфигурации, описанной в классе `AsyncHttpClientConfig` и `HttpClientConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  Следовать ли по [перенаправлениям в HTTP](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections) (по умолчанию: `true`)
    2.  Максимальное время на установление соединения (по умолчанию: `5s`)
    3.  Максимальное время на чтение ответа (по умолчанию: `2m`)
    4.  Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
    5.  Адрес прокси (`обязательная`, по умолчанию не указано)
    6.  Порт прокси (`обязательная`, по умолчанию не указано)
    7.  Пользователь для прокси (по умолчанию не указано, необязательно)
    8.  Пароль для прокси (по умолчанию не указано, необязательно)
    9.  Узлы, которые следует исключить из проксирования (по умолчанию не указано, необязательно)
    10.  Включает логирование модуля (по умолчанию: `false`)
    11.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
    12.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
    13.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
    14.  Использовать ли шаблон пути запроса при логировании; если не указано, шаблон используется всегда, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указано, необязательно)
    15.  Включает метрики модуля (по умолчанию: `true`)
    16.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    17.  Настройка тегов для метрик (по умолчанию: `{}`)
    18.  Включает трассировку модуля (по умолчанию: `true`)
    19.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  Следовать ли по [перенаправлениям в HTTP](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections) (по умолчанию: `true`)
    2.  Максимальное время на установление соединения (по умолчанию: `5s`)
    3.  Максимальное время на чтение ответа (по умолчанию: `2m`)
    4.  Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
    5.  Адрес прокси (`обязательная`, по умолчанию не указано)
    6.  Порт прокси (`обязательная`, по умолчанию не указано)
    7.  Пользователь для прокси (по умолчанию не указано, необязательно)
    8.  Пароль для прокси (по умолчанию не указано, необязательно)
    9.  Узлы, которые следует исключить из проксирования (по умолчанию не указано, необязательно)
    10.  Включает логирование модуля (по умолчанию: `false`)
    11.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
    12.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
    13.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
    14.  Использовать ли шаблон пути запроса при логировании; если не указано, шаблон используется всегда, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указано, необязательно)
    15.  Включает метрики модуля (по умолчанию: `true`)
    16.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    17.  Настройка тегов для метрик (по умолчанию: `{}`)
    18.  Включает трассировку модуля (по умолчанию: `true`)
    19.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

Можно также настроить [Netty транспорт](netty.md).

## Java клиент { #native-client }

Реализация `HTTP`-клиента основана на встроенном Java-клиенте, поставляемом в [JDK](https://openjdk.org/groups/net/httpclient/intro.html).
Лучше всего подходит для Java-сервисов, где не требуется максимальная производительность,
и хочется минимизировать количество внешних библиотек.

### Подключение { #dependency-3 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:http-client-jdk"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends JdkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:http-client-jdk")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JdkHttpClientModule
    ```

### Конфигурация { #configuration-3 }

Пример полной конфигурации, описанной в классе `JdkHttpClientConfig` и `HttpClientConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  Количество потоков для `HTTP`-клиента (по умолчанию: количество доступных процессоров, умноженное на `2`)
    2.  Какую версию `HTTP`-протокола использовать, доступные значения: `HTTP_1_1` / `HTTP_2` (по умолчанию: `HTTP_1_1`)
    3.  Максимальное время на установление соединения (по умолчанию: `5s`)
    4.  Максимальное время на чтение ответа (по умолчанию: `2m`)
    5.  Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
    6.  Адрес прокси (`обязательная`, по умолчанию не указано)
    7.  Порт прокси (`обязательная`, по умолчанию не указано)
    8.  Пользователь для прокси (по умолчанию не указано, необязательно)
    9.  Пароль для прокси (по умолчанию не указано, необязательно)
    10.  Узлы, которые следует исключить из проксирования (по умолчанию не указано, необязательно)
    11.  Включает логирование модуля (по умолчанию: `false`)
    12.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
    13.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
    14.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
    15.  Использовать ли шаблон пути запроса при логировании; если не указано, шаблон используется всегда, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указано, необязательно)
    16.  Включает метрики модуля (по умолчанию: `true`)
    17.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    18.  Настройка тегов для метрик (по умолчанию: `{}`)
    19.  Включает трассировку модуля (по умолчанию: `true`)
    20.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  Количество потоков для `HTTP`-клиента (по умолчанию: количество доступных процессоров, умноженное на `2`)
    2.  Какую версию `HTTP`-протокола использовать, доступные значения: `HTTP_1_1` / `HTTP_2` (по умолчанию: `HTTP_1_1`)
    3.  Максимальное время на установление соединения (по умолчанию: `5s`)
    4.  Максимальное время на чтение ответа (по умолчанию: `2m`)
    5.  Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
    6.  Адрес прокси (`обязательная`, по умолчанию не указано)
    7.  Порт прокси (`обязательная`, по умолчанию не указано)
    8.  Пользователь для прокси (по умолчанию не указано, необязательно)
    9.  Пароль для прокси (по умолчанию не указано, необязательно)
    10.  Узлы, которые следует исключить из проксирования (по умолчанию не указано, необязательно)
    11.  Включает логирование модуля (по умолчанию: `false`)
    12.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
    13.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
    14.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
    15.  Использовать ли шаблон пути запроса при логировании; если не указано, шаблон используется всегда, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указано, необязательно)
    16.  Включает метрики модуля (по умолчанию: `true`)
    17.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    18.  Настройка тегов для метрик (по умолчанию: `{}`)
    19.  Включает трассировку модуля (по умолчанию: `true`)
    20.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

## Декларативный клиент { #client-declarative }

Предлагается использовать специальные аннотации для создания декларативного клиента:

* `@HttpClient` — указывает, что интерфейс является декларативным `HTTP`-клиентом
* `@HttpRoute` — указывает [тип HTTP-запроса](https://developer.mozilla.org/ru/docs/Web/HTTP/Methods) и путь запроса

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

### Конфигурация клиента { #client-configuration }

Конфигурация конкретной реализации `@HttpClient` по умолчанию ищется по пути `httpClient.{имя класса в нижнем регистре}`.
Если нужно задать путь явно, используйте параметр `configPath` в аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient(configPath = "httpClient.someClient") //(1)!
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

    1. Путь до конфигурации конкретно этого клиента

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient(configPath = "httpClient.someClient") //(1)!
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

    1. Путь до конфигурации конкретно этого клиента

В `@HttpClient` также можно указать теги для внедряемых компонентов:

* `httpClientTag` — тег для выбора конкретного транспортного `HttpClient`, если в графе есть несколько реализаций с разными `@Tag`
* `telemetryTag` — тег для выбора конкретной фабрики телеметрии клиента

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

Пример конфигурации в случае пути `httpClient.someClient` описанной в классе `DeclarativeHttpClientConfig`:

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

    1.  Базовый `URL` сервиса, куда будут отправляться запросы (`обязательная`, по умолчанию не указано)
    2.  Максимальное время запроса: может включать разрешение `DNS`, подключение, запись тела запроса, обработку сервером и чтение тела ответа. Если вызов требует перенаправления или повторных попыток, все они должны завершиться в течение одного периода (по умолчанию не указано, необязательно)
    3.  Включает логирование модуля (по умолчанию: `false`)
    4.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
    5.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
    6.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
    7.  Использовать ли шаблон пути запроса при логировании; если не указано, шаблон используется всегда, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указано, необязательно)
    8.  Включает метрики модуля (по умолчанию: `true`)
    9.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    10.  Настройка тегов для метрик (по умолчанию: `{}`)
    11.  Включает трассировку модуля (по умолчанию: `true`)
    12.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  Базовый `URL` сервиса, куда будут отправляться запросы (`обязательная`, по умолчанию не указано)
    2.  Максимальное время запроса: может включать разрешение `DNS`, подключение, запись тела запроса, обработку сервером и чтение тела ответа. Если вызов требует перенаправления или повторных попыток, все они должны завершиться в течение одного периода (по умолчанию не указано, необязательно)
    3.  Включает логирование модуля (по умолчанию: `false`)
    4.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
    5.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
    6.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
    7.  Использовать ли шаблон пути запроса при логировании; если не указано, шаблон используется всегда, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указано, необязательно)
    8.  Включает метрики модуля (по умолчанию: `true`)
    9.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    10.  Настройка тегов для метрик (по умолчанию: `{}`)
    11.  Включает трассировку модуля (по умолчанию: `true`)
    12.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

### Конфигурация метода { #method-configuration }

Для конкретного метода можно отдельно настроить часть параметров. Путь к конфигурации метода определяется путем к клиенту и именем метода:
если путь клиента `httpClient.someClient`, то для метода `hello` итоговый путь будет `httpClient.someClient.hello`.

Конфигурация метода накладывается поверх конфигурации клиента: `requestTimeout` метода заменяет клиентское значение, а настройки телеметрии метода
переопределяют только явно указанные поля.

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

    1.  Максимальное время запроса: может включать разрешение `DNS`, подключение, запись тела запроса, обработку сервером и чтение тела ответа. Если вызов требует перенаправления или повторных попыток, все они должны завершиться в течение одного периода (по умолчанию не указано, необязательно)
    2.  Включает логирование модуля (по умолчанию: `false`)
    3.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
    4.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
    5.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
    6.  Использовать ли шаблон пути запроса при логировании; если не указано, наследуется значение клиента (по умолчанию не указано, необязательно)
    7.  Включает метрики модуля (по умолчанию: `true`)
    8.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    9.  Настройка тегов для метрик (по умолчанию: `{}`)
    10.  Включает трассировку модуля (по умолчанию: `true`)
    11.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  Максимальное время запроса: может включать разрешение `DNS`, подключение, запись тела запроса, обработку сервером и чтение тела ответа. Если вызов требует перенаправления или повторных попыток, все они должны завершиться в течение одного периода (по умолчанию не указано, необязательно)
    2.  Включает логирование модуля (по умолчанию: `false`)
    3.  Маска, которая используется для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`)
    4.  Список параметров запроса, которые следует скрывать (по умолчанию: `[]`)
    5.  Список заголовков запроса или ответа, которые следует скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
    6.  Использовать ли шаблон пути запроса при логировании; если не указано, наследуется значение клиента (по умолчанию не указано, необязательно)
    7.  Включает метрики модуля (по умолчанию: `true`)
    8.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    9.  Настройка тегов для метрик (по умолчанию: `{}`)
    10.  Включает трассировку модуля (по умолчанию: `true`)
    11.  Настройка атрибутов для трассировки (по умолчанию: `{}`)

### Запрос { #request }

Раздел описывает преобразования `HTTP`-запроса у декларативного `HTTP`-клиента.
Предлагается использовать специальные аннотации для указания параметров запроса.

#### Преобразование параметров в строку { #string-parameter-converter }

`StringParameterConverter<T>` преобразует значение параметра в строку перед тем, как Kora подставит его в путь, параметр запроса,
заголовок или куки. Интерфейс состоит из одного метода:

```java
public interface StringParameterConverter<T> {
    String convert(T value);
}
```

Преобразователь ищется как обычный компонент графа по точному типу параметра. Если параметр имеет тип `Map<String, T>`,
то преобразователь ищется для типа значения `T`; если используется `Map<String, List<T>>`, он применяется к каждому элементу списка.

Из коробки доступны преобразователи для `Boolean`, `Short`, `Integer`, `Long`, `Double`, `Float`, `UUID`, `BigDecimal`, `BigInteger`,
`Duration`, `OffsetTime`, `OffsetDateTime`, `LocalTime`, `LocalDate`, `LocalDateTime`, `ZonedDateTime` и `Instant`.
Типы даты и времени записываются в `ISO`-формате. Для собственных типов нужно предоставить компонент `StringParameterConverter<T>`:

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

После этого тип можно использовать в параметрах клиента:

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

#### Параметр пути { #path-parameter }

`@Path` — обозначает значение части пути запроса, сам параметр указывается в `{кавычках}` в пути
и имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.

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

#### Параметр запроса { #query-parameter }

`@Query` — значение параметра запроса, имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.
Поддерживаются одиночные значения, `List<T>`, `Set<T>`, `Collection<T>`, а также `Map<String, T>` и `Map<String, List<T>>`.
Для значений, которые не являются строками, используется доступный `StringParameterConverter<T>`.

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

Можно отправлять параметры запроса в формате ключ и значение, для этого предполагается использовать тип `Map`,
где ключом является имя параметра и обязательно имеет тип `String`.
Если значение `Map` является списком, каждый элемент списка будет отправлен как отдельное значение того же параметра.
Если элемент списка равен `null`, параметр будет отправлен без значения.

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

#### Заголовок { #header }

`@Header` — значение [заголовка запроса](https://developer.mozilla.org/ru/docs/Web/HTTP/Headers), имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.
Поддерживаются одиночные значения, `List<T>`, `Set<T>`, `Collection<T>`, `Map<String, T>` и готовый объект `HttpHeaders`.

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

Можно отправлять заголовки в формате ключ и значение, для этого предполагается использовать тип `HttpHeaders` либо `Map`,
где ключом является имя заголовка и обязательно имеет тип `String`.
Для значений, которые не являются строками, используется доступный `StringParameterConverter<T>`:

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

#### Тело запроса { #request-body }

Для указания тела запроса требуется использовать аргумент метода без специальных аннотации,
по умолчанию поддерживаются такие типы как `byte[]`, `ByteBuffer` или `String`.

##### JSON { #json }

Чтобы указать, что тело является `JSON` и для него требуется автоматически создать и внедрить `JsonWriter`,
используется тег-аннотация `@Json`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record MyBody(String name) { }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        void hello(@Json MyBody body); //(1)!
    }
    ```

    1. Указывает, что тело должно быть записано как `JSON`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class MyBody(val name: String) { }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun hello(@Json body: MyBody) //(1)!
    }
    ```

    1. Указывает, что тело должно быть записано как `JSON`

Требуется подключить модуль [JSON](json.md).

##### Текстовая форма { #text-form }

Можно использовать `FormUrlEncoded` как тип аргумента тела [форма данных](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1).

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

Пример вызова метода с такой формой будет выглядеть так:

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

##### Бинарная форма { #binary-form }

Можно использовать `FormMultipart` как тип аргумента тела [бинарная форма](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2).

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

Пример вызова метода с такой формой будет выглядеть так:

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

##### Самописное { #custom-body }

Если тело требуется записывать отличным от стандартных механизмов способом,
то можно использовать специальный интерфейс `HttpClientRequestMapper` для реализации собственной логики:

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

#### Куки { #cookie }

`@Cookie` — значение [Cookie](https://developer.mozilla.org/ru/docs/Glossary/Cookie), имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.
Поддерживаются одиночные значения, `List<T>`, `Set<T>`, `Collection<T>`, `Map<String, T>` и готовый объект `Cookie`.
Куки добавляются в заголовок `Cookie`; для коллекций каждое значение превращается в отдельное значение куки с тем же именем.

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

#### Обязательные параметры { #required-parameters }

===! ":fontawesome-brands-java: `Java`"

    По умолчанию все аргументы объявленные в методе являются **обязательными** (*NotNull*).

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все аргументы объявленные в методе которые не используют [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис считаются **обязательными** (*NotNull*).

#### Необязательные параметры { #optional-parameters }

===! ":fontawesome-brands-java: `Java`"

    Если аргумент метода является необязательным, то есть может отсутствовать то,
    можно использовать аннотацию `@Nullable`:

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello(@Nullable @Query("queryValue") String queryValue); //(1)!
    }
    ```

    1.  Подойдет любая аннотация `@Nullable`, такие как `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использовать [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис и помечать такой параметр как Nullable:

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(@Query("queryValue") queryValue: String?)
    }
    ```

### Ответ { #response }

Раздел описывает преобразование `HTTP`-ответа от декларативного `HTTP`-клиента.

#### Тело ответа { #response-body }

По умолчанию можно использовать стандартные типы возвращаемых значений тела ответа, такие как `void`, `byte[]`, `ByteBuffer` либо `String`.

##### JSON { #json-2 }

Если предполагается читать тело как `JSON`, то требуется использовать аннотацию `@Json` над методом.

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

    1. Указывает, что ответ должен быть прочитан как `JSON`

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

    1. Указывает, что ответ должен быть прочитан как `JSON`

Требуется подключить модуль [JSON](json.md).

##### Сущность ответа { #response-entity }

Если предполагается читать тело и получить также заголовки и статус код ответа,
то предполагается использовать `HttpResponseEntity`, это обертка над телом ответа.

Ниже показан пример, аналогичный примеру `JSON`, вместе с оберткой `HttpResponseEntity`:

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

##### Самописное { #custom-response }

Если требуется чтение ответа отличным способом, то можно использовать специальный интерфейс `HttpClientResponseMapper`:

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

#### Ошибка ответа { #response-error }

По умолчанию, когда не указан ни тег преобразователя, ни сам преобразователь, преобразование применяется только для `2xx` HTTP-кодов ответа.
Для всех остальных кодов будет выброшено исключение `HttpClientResponseException`, которое содержит [HTTP-код ответа](https://developer.mozilla.org/ru/docs/Web/HTTP/Status), тело ответа и заголовки ответа.

#### Исключения клиента { #client-exceptions }

Все штатные исключения `HTTP`-клиента наследуются от `HttpClientException`, который является `RuntimeException`.
Это позволяет перехватывать как конкретный вид ошибки, так и все ошибки клиента одним общим типом:

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

Основные типы исключений:

* `HttpClientResponseException` — ответ получен, но его код не был обработан как успешный. Содержит `getCode()`, `getHeaders()` и `getBytes()`.
* `HttpClientTimeoutException` — истекло время ожидания запроса, соединения или чтения.
* `HttpClientConnectionException` — ошибка установления или поддержания соединения с удаленным узлом.
* `HttpClientEncoderException` — ошибка преобразования пользовательского значения в тело запроса.
* `HttpClientDecoderException` — ошибка преобразования тела ответа в пользовательский тип.
* `HttpClientUnknownException` — прочая ошибка транспортного клиента, которая не попала в более точную категорию.

`HttpClientResponseException` создается после чтения тела ответа в массив байт. Если тело не удалось прочитать полностью,
ошибка чтения добавляется как `suppressed`-исключение, а в `getBytes()` попадает то тело, которое удалось собрать.

#### Преобразование по коду { #conversion-by-code }

Если требуется особое преобразование в зависимости от [HTTP-кода ответа](https://developer.mozilla.org/ru/docs/Web/HTTP/Status), можно использовать аннотацию `@ResponseCodeMapper` для указания
соответствия HTTP-кода и преобразователя `HttpClientResponseMapper`.

Также можно использовать `ResponseCodeMapper.DEFAULT` как указание поведения по умолчанию для всех неперечисленных HTTP-кодов.
Если для кода указан параметр `mapper`, будет использован конкретный `HttpClientResponseMapper`.
Если указан параметр `type`, Kora подберет преобразователь ответа для этого типа и затем приведет результат к возвращаемому типу метода.
Это удобно для закрытых иерархий ответов, где разные HTTP-статусы соответствуют разным подтипам результата.

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

В примере выше для статуса кода `200` будет использовать `ResponseSuccessMapper`,
а для всех остальных статус кодов будет использован `ResponseErrorMapper`.

Пример с параметром `type`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @Json
        sealed interface UserResponse permits Success, Error {}

        @Json
        record Success(String id) implements UserResponse {}

        @Json
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

        @Json
        sealed interface UserResponse

        @Json
        data class Success(val id: String) : UserResponse

        @Json
        data class Error(val message: String) : UserResponse

        @Json
        @ResponseCodeMapper(code = 200, type = Success::class)
        @ResponseCodeMapper(code = 404, type = Error::class)
        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        fun get(@Path id: String): UserResponse
    }
    ```

### Сигнатуры { #signatures }

Доступные сигнатуры для методов декларативного `HTTP`-клиента из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

## Перехватчики { #interceptors }

Можно создавать перехватчики для изменения поведения либо создания дополнительного поведения используя класс `HttpClientInterceptor`.
Перехватчики можно подключить на определенные методы либо весь `@HttpClient` класс целиком:

### Базовый URL { #root-uri-interceptor }

`RootUriInterceptor` — готовый перехватчик, который добавляет базовый `URL` к относительным запросам.
Если запрос уже содержит схему (`http://` или `https://`), перехватчик оставляет его без изменений.
Если запрос относительный, `RootUriInterceptor` добавляет к нему корневой адрес и гарантирует один разделитель `/` между корнем и путем.

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

После регистрации перехватчика его можно подключить к клиенту:

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

Для декларативных клиентов обычно удобнее задавать базовый `URL` через конфигурацию `DeclarativeHttpClientConfig.url`.
`RootUriInterceptor` полезен для императивного `HttpClient` или для случаев, когда общий корневой адрес нужно добавить как отдельное сквозное поведение.

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

Если перехватчик нужен для всех методов клиента, `@InterceptWith` можно поставить на интерфейс:

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

Если перехватчики указаны и на клиенте, и на методе, для конкретного вызова будут применены оба набора перехватчиков.

### Авторизация { #authorization }

Kora предоставляет готовые перехватчики, которые можно использовать для авторизации с помощью [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/)

#### Basic { #basic }

Требуется сконфигурировать перехватчик и конфигурацию для авторизации [Basic](https://swagger.io/docs/specification/authentication/basic-authentication/):

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

Также в конструктор можно предоставить собственную реализацию `HttpClientTokenProvider` если правила получения секретов другие.

Затем подключить перехватчик для всего `HTTP`-клиента либо определенных методов.

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

Требуется сконфигурировать перехватчик и конфигурацию для авторизации [ApiKey](https://swagger.io/docs/specification/authentication/api-keys/):

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

Затем подключить перехватчик для всего `HTTP`-клиента либо определенных методов.

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

Требуется сконфигурировать перехватчик для авторизации [Bearer](https://swagger.io/docs/specification/authentication/bearer-authentication/):

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

Потребуется самостоятельно реализовать предоставление `Bearer` токена с помощью собственной реализации `HttpClientTokenProvider`,
либо использовать конструктор который принимает статический `Bearer Token`.

```java
public interface HttpClientTokenProvider {

    CompletionStage<String> getToken(HttpClientRequest request);
}
```

Затем подключить перехватчик для всего `HTTP`-клиента либо определенных методов.

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

Авторизация с помощью [OAuth](https://swagger.io/docs/specification/authentication/oauth2/) аналогична [Bearer](#bearer),
требуется самостоятельно реализовать `HttpClientTokenProvider` и подложить его в контейнер зависимостей.

## Клиент императивный { #client-imperative }

Базовый клиент представляет собой интерфейс `HttpClient` и доступен для внедрения:

```java
public interface HttpClient {

    CompletionStage<HttpClientResponse> execute(HttpClientRequest request); //(1)!

    HttpClient with(HttpClientInterceptor interceptor); //(2)!
}
```

1. Метод исполнения запроса
2. Метод позволяющий добавлять различные перехватчики в ручном режиме

Для построения запросов вручную можно использовать `HttpClientRequestBuilder`:

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

`HttpClientRequestBuilder` поддерживает методы под основные `HTTP`-методы (`get`, `post`, `put`, `delete`, `patch` и другие), подстановку параметров пути,
параметры запроса, заголовки, тело запроса и `requestTimeout` для отдельного запроса.

Так как `HttpClientResponse` реализует `Closeable`, при ручном вызове его нужно закрывать после чтения тела:

===! ":fontawesome-brands-java: `Java`"

    ```java
    httpClient.execute(request).thenApply(response -> {
        try (response) {
            if (response.code() >= 400) {
                throw new IllegalStateException("HTTP error: " + response.code());
            }

            try (var is = response.body().asInputStream()) {
                return new String(is.readAllBytes(), StandardCharsets.UTF_8);
            }
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    httpClient.execute(request).thenApply { response ->
        response.use {
            if (response.code() >= 400) {
                throw IllegalStateException("HTTP error: ${response.code()}")
            }

            response.body().asInputStream().use { body ->
                String(body.readAllBytes(), StandardCharsets.UTF_8)
            }
        }
    }
    ```
